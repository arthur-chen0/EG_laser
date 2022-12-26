import serial
import binascii
import time
from enum import Enum, auto
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-p","--port", help="serial port path", required=True)

class Register(Enum):
    STATUS = ('00', '00')
    ADDRESS = ('00', '10')
    OFFSET = ('00', '12')
    INIT = ('00', '20')
    RESULT = ('00', '22')
    VERSION = ('00', '0C')
    SERIAL_NUM = ('00', '0E')
    DIODE = ('01', 'BE')

    def __init__(self, high, low):
        self.high = high
        self.low = low
    
    def getRegister(self):
        return self.high + self.low

class Status(Enum):
    HEAD = auto()
    RW = auto()
    REGISTER = auto()
    REGISTER2 = auto()
    COUNT = auto()
    COUNT2 = auto()
    PAYLOAD = auto()
    CHECKSUM = auto()

class Packet(Enum):
    NORMAL = auto()
    ERROR = auto()

class Laser:

    HEAD = 'AA'
    ADDRESS = '00'
    STATUS = Status.HEAD
    PACKET = Packet.NORMAL
    count = ''
    payload = ''

    def __init__(self, port, baudrate = 19200):
        self.device = serial.Serial()
        self.device.port = port
        self.device.baudrate = baudrate

    def open(self):
        try:
            self.device.open()
            if self.device.is_open:
                self.device.setDTR(True)
                time.sleep(0.1) #Sleep 100ms to wait device ready
                self.device.write(binascii.a2b_hex('55')) #Auto baudrate by TX single 0x55
                time.sleep(0.1)

                count = self.device.in_waiting
                if  count > 0:
                    self.ADDRESS = binascii.b2a_hex(self.device.read(count)).decode('utf-8')
                    # print(self.ADDRESS)
                    return True
                else :
                    print("Error occur : Can't get the module address!")
                    exit()
            else:
                raise Exception("Serial port doesn't open!")

        except Exception as ex:
            print("open port " + self.device.port + " error: " + str(ex))
            exit()

    def auto_measurement(self):
        data = self.HEAD
        data += self.ADDRESS
        data += Register.INIT.getRegister()
        data += '0001' 
        data += '0004'
        data += str(int(self.ADDRESS) + int(Register.INIT.getRegister()) + int('0001') + int('0004'))
        self.device.write(binascii.a2b_hex(data))
        time.sleep(1)
        while True:
            # count = self.device.in_waiting
            # print('count: ' + str(count))
            if self.device.in_waiting:
                # print(binascii.b2a_hex(self.device.read(1)).decode('utf-8'))
                self.parse_packet(binascii.b2a_hex(self.device.read(1)).decode('utf-8'))
            # else:
            #     exit()
            time.sleep(0.1)

    def stop_auto_mode(self):
        self.device.write(binascii.a2b_hex('58'))

    def parse_packet(self, data):
        # print('data: ' + data)
        # print(self.STATUS)
        match self.STATUS:
            case Status.HEAD:
                if data == 'aa':
                    self.PACKET = Packet.NORMAL
                elif data == 'ee':
                    self.PACKET = Packet.ERROR
                self.STATUS = Status.RW
            case Status.RW:
                self.STATUS = Status.REGISTER
            case Status.REGISTER:
                self.STATUS = Status.REGISTER2
            case Status.REGISTER2:
                self.STATUS = Status.COUNT
            case Status.COUNT:
                self.STATUS = Status.COUNT2
                self.count = ''
                self.count += data
            case Status.COUNT2:
                self.STATUS = Status.PAYLOAD
                self.count += data
                self.payload = ''
                # print("payload count: " + self.count)
                # print(int(self.count))
            case Status.PAYLOAD:
                self.payload += data
                if len(self.payload) >= int(self.count) * 4:
                    # print('payload: ' + self.payload)
                    self.STATUS = Status.CHECKSUM
            case Status.CHECKSUM:
                if self.PACKET == Packet.NORMAL:
                    self.get_distance(self.payload)
                self.STATUS = Status.HEAD

    def get_distance(self, data):
        distance = data[0:8]
        print("distance: ")
        print(int(distance, 16))


if __name__ == '__main__':
    args = parser.parse_args()
    laser = Laser(args.port)
    if laser.open():
        laser.auto_measurement()


    
 