import serial
from enum import Enum
import time
import json
from thread import *
from collections import deque
import ToxMain

class ToxSerialMessageType(Enum):
    SPEGNIMENTO = 0
    ACCENSIONE = 1
    GET_VALUE = 2


class ToxSerialMessage:
    def __init__(self, pin, msgType): #msgType : ToxSerialMessageType
        self.pin = pin
        offstr = ""
        delis = "<"
        delir = ">"

        if msgType == 0:
            offstr = ""


        if msgType == 2:
            self.isResponseRequested = True
        else:
            self.isResponseRequested = False
        self.message = ""
        if self.pin > 9:
            pass




class ToxSerialResponse:
    def __init__(self, responseMsg):
        self.senderMessage = None #ToxSerialMessage
        self.responseMsg = responseMsg


    
class ToxSerial:

    def __init__(self):
        self.queue = deque()

    def start(self):
        # self.ser = serial.Serial("/dev/cu.usbmodem14141", 9600, timeout=0)
        self.ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0)
        time.sleep(2.5)
        start_new_thread(self.performQueue, ())


    def addToQueue(self, message):
        if message.id == 0:
            self.queue.append(message)
            return

        found = False
        for msg in self.queue:
            if msg.id == message.id:    
                found = True
                break
        if found:
            return
        else:
            self.queue.append(message)

    def removeFromQueue(self):
        self.queue.popleft()

    def performQueue(self):
        while True:
            time.sleep(0.1)
            if len(self.queue) >= 1:
                msg = self.queue[0]
                args = msg.args
                if args != None:
                    msg.handler(args)
                else:
                    msg.handler()
                self.queue.popleft()
    
    def printQueue(self):
        print(self.queue)
    
    def printQueueLen(self):
        print("Blocchi all'interno della queue: " + str(len(self.queue)))



class ToxMessage:
    def __init__(self, handler):
        self.handler = handler
        self.args = None
        self.message = None
        self.id = 0
        

          

class ToxSerialUpdate:
    def __init__(self):
        self.toxMain = ToxMain.ToxMain()

    def updateObjs(self):
        asd.ser.write("B")
        time.sleep(0.1)
        line = asd.ser.readline()
        asd.ser.flushInput()
        asd.ser.flushOutput()
        print(line)
        self.toxMain.updateObjetctsStatus(line)



asd = ToxSerial()
asd.start()


while True:
    
    updateObj = ToxSerialUpdate()

    msg = ToxMessage(updateObj.updateObjs)
    msg.id = 1
    asd.addToQueue(msg)

    asd.printQueueLen()
    time.sleep(0.15)
