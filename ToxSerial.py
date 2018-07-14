import serial
from enum import Enum
import time
import json
from thread import *
from collections import deque

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
    def sendSerial(self, message): #ToxSerialMessage
        if message.isResponseRequested == False:
            #send serial
            return

        #send serial
        #var = read response
        #response = ToxSerialResponse(var)
        #response.senderMessage = message
        #return response

    
class TestSerial:
    # def __init__(self):
    #     self.ser = serial.Serial('/dev/cu.usbmodem14141', 9600)
    #     time.sleep(2.5)
    #     self.serialActivated = True

    def __init__(self):
        self.queue = deque()

    def start(self):
        self.ser = serial.Serial("/dev/cu.usbmodem14141", 9600, timeout=0)
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
                    msg.handler(None)
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
        

          

asd = TestSerial()
asd.start()

def test(message):
    if message != None:
        asd.ser.write(message)
    else:
        asd.ser.write("A")
    time.sleep(0.1)
    line = asd.ser.readline()
    asd.ser.flushInput()
    asd.ser.flushOutput()
    print(line) 



while True:
    
    msg = ToxMessage(test)
    msg.args = ("B")
    msg.id = 1
    asd.addToQueue(msg)

    # msg2 = ToxMessage(test)
    # msg2.args = ("A")
    # asd.addToQueue(msg2)

    asd.printQueueLen()
    time.sleep(0.15)
    # if value == "0":
    #     msg = ToxMessage(test)
    #     msg.args = ("B")
    #     asd.addToQueue(msg)

    # elif value == "1":
    #     asd.printQueue()
    # else:
    #     print("Error input")
