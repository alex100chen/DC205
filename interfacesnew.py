# Contains methods for communicating with instruments

import serial
#import serial.tools.list_ports
import visa

termchar = '\n'

def openComPort(self, thisport='COM3', baud=115200):
    com = serial.Serial(thisport, baud)
    com.timeout = 5
    if not com.is_open:
        com.open()
    return com

def comWrite(comPort, string):
    bstring = str.encode(string + termchar)
    comPort.write(bstring)

def comRead(comPort):
    rtrnstring = bytes.decode(comPort.read_until(terminator=b'\n', size=128))
    return rtrnstring

def comQuery(comPort, string):
    bstring = str.encode(string + termchar)
    comPort.write(bstring)
    rtrnstring = bytes.decode(comPort.read_until(terminator=b'\n', size=128))
    return rtrnstring