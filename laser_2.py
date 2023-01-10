import serial
import binascii
import time
from enum import Enum, auto
import threading
from argparse import ArgumentParser

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

    def getRegisterType(self, data):
        h = data[0:2]
        l = data[2:4]
        for item in Register:
            if h == item.high and l == item.low:
                return item
        return None 

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

class result_callback():
    def on_distance(self, distance):
        pass
    def on_error(self, error):
        pass

class Laser:

    HEAD = 'AA'
    ADDRESS = '00'
    STATUS = Status.HEAD
    PACKET = Packet.NORMAL
    register = ''
    count = ''
    payload = ''
    is_running = True

    def __init__(self, port, baudrate = 19200):
        self.device = serial.Serial()
        self.device.port = port
        self.device.baudrate = baudrate
        self.callback = result_callback()

    def open(self):
        try:
            self.device.open()
            if self.device.is_open:
                self.device.setDTR(False)
                time.sleep(0.2) #Sleep 200ms to wait device ready
                self.device.write(binascii.a2b_hex('55')) #Auto baudrate by TX single 0x55
                time.sleep(0.3)

                count = self.device.in_waiting
                if  count > 0:
                    binascii.b2a_hex(self.device.read(count)).decode('utf-8')
                    # print(str(count) + " " + str(self.device.read(count)))
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

    def receive(self):
        while(self.is_running):
            # count = self.device.in_waiting
            # print('count: ' + str(count))
            if self.device.inWaiting():
                # print(binascii.b2a_hex(self.device.read(1)).decode('utf-8'))
                self.parse_packet(binascii.b2a_hex(self.device.read(1)).decode('utf-8'))
            # else:
            #     exit()
            time.sleep(0.01)
        print("stop receive")


    def auto_measurement(self):
        data = self.HEAD
        data += self.ADDRESS
        data += Register.INIT.getRegister()
        data += '0001' 
        data += '0004'
        data += str(int(self.ADDRESS) + int(Register.INIT.getRegister()) + int('0001') + int('0004'))
        self.device.write(binascii.a2b_hex(data))
        time.sleep(1)
        self.is_running = True
        t = threading.Thread(target = self.receive)
        t.start()
        # while True:
        #     # count = self.device.in_waiting
        #     # print('count: ' + str(count))
        #     if self.device.inWaiting():
        #         # print(binascii.b2a_hex(self.device.read(1)).decode('utf-8'))
        #         self.parse_packet(binascii.b2a_hex(self.device.read(1)).decode('utf-8'))
        #     # else:
        #     #     exit()
        #     time.sleep(0.01)

    def stop_auto_mode(self):
        self.device.write(binascii.a2b_hex('58'))

    def parse_packet(self, data):
        # print('data: ' + data)
        # print(self.STATUS)
        # match self.STATUS:
        if self.STATUS == Status.HEAD:
            if data == 'aa':
                self.PACKET = Packet.NORMAL
                self.STATUS = Status.RW
            elif data == 'ee':
                self.PACKET = Packet.ERROR
                self.STATUS = Status.RW
                
        elif self.STATUS == Status.RW:
            self.STATUS = Status.REGISTER
        elif self.STATUS == Status.REGISTER:
            self.STATUS = Status.REGISTER2
            self.register += data
        elif self.STATUS == Status.REGISTER2:
            self.STATUS = Status.COUNT
            self.register += data
        elif self.STATUS == Status.COUNT:
            self.STATUS = Status.COUNT2
            self.count = ''
            self.count += data
        elif self.STATUS == Status.COUNT2:
            self.STATUS = Status.PAYLOAD
            self.count += data
            self.payload = ''
                # print("payload count: " + self.count)
                # print(int(self.count))
        elif self.STATUS == Status.PAYLOAD:
            self.payload += data
            if len(self.payload) >= int(self.count) * 4:
                # print('payload: ' + self.payload)
                self.STATUS = Status.CHECKSUM
        elif self.STATUS == Status.CHECKSUM:
            self.STATUS = Status.HEAD
            # checksum = int(self.ADDRESS) + int(self.register) + int(self.count) + int(self.payload)
            # if checksum == int(data, 16):
            self.parse_payload(self.register, self.payload)
            # else:
            #     print("checksum is worng! " + data + " with " + str(checksum))
            self.reset()
    
    def reset(self):
        self.register = ''
        self.count = ''
        self.payload = ''

    def parse_payload(self, register, data):
        if self.PACKET == Packet.NORMAL:
            self.get_distance(data)
        elif self.PACKET == Packet.ERROR:
            self.get_error(data)

    def get_distance(self, data):
        distance = data[0:8]
        self.callback.on_distance(int(distance, 16))

    def get_error(self, data):
        pass

# class result(result_callback):
#     def on_distance(self, distance):
#         print('distance: ' + str(distance))

#     def on_error(self, error):
#         print('error: ' + error)


# if __name__ == '__main__':
#     args = parser.parse_args()
#     laser = Laser(args.port)
#     laser.callback = result()
#     try:
#         if laser.open():
#             laser.auto_measurement()
#     except KeyboardInterrupt:
#         print("stop auto mode")
#         laser.stop_auto_mode()
    


    
 