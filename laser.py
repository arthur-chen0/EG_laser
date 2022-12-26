import serial
import binascii
import time
from enum import Enum
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

class Laser:

    HEAD = 'AA'
    ADDRESS = '00'

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
                self.write(binascii.a2b_hex('55')) #Auto baudrate by TX single 0x55
                time.sleep(0.1)

                count = self.device.in_waiting
                if  count > 0:
                    self.ADDRESS = self.device.read(count)
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

    def stop_auto_mode(self):
        self.device.write(binascii.a2b_hex('58'))

if __name__ == '__main__':
    args = parser.parse_args()
    laser = Laser(args.port)
    if laser.open():
        laser.auto_measurement()


    
 