# coding=utf-8
import json
import os
import random
import threading
import inspect
from enum import Enum
import time
import serial
from thread import *
from collections import deque
import sys

class ToxIDCreator:
    __instance = None

    @staticmethod
    def shared():
        if ToxIDCreator.__instance == None:
            ToxIDCreator()
        return ToxIDCreator.__instance

    def __init__(self):
        
        if ToxIDCreator.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ToxIDCreator.__instance = self

        self.currentIDs = []
        objects = ToxConverter().getObjectsFromJSON()
        for obj in objects:
            self.currentIDs.append(obj["id"])

        # self.FILE_NAME = ".currentIDs.json"
        # self.currentIDs = self.getIDsFromStorage()

    def setIDasUsed(self, id):
        if id not in self.currentIDs:
            self.currentIDs.append(id)
    
    def setIDasFree(self, id):
        try:
            self.currentIDs.remove(id)
        except:
            pass

    def getIDsFromStorage(self):
        if os.path.isfile(self.FILE_NAME):
            with open(self.FILE_NAME) as f:
                data = json.load(f)
                if data != None:
                    return data
            return []
        else:
            return []

    def createUniqueID(self):
        id = random.randint(0, 9999)
        while id in self.currentIDs:
            id = random.randint(0, 9999)
        return id

    def isIDUnique(self, id):
        if id in self.currentIDs:
            return False
        else:
            return True




####    CLASSES APPARECCHIATURE     ###

class ObjectType(Enum):
    NONE = 0
    LUCE = 1
    VENTOLA = 2
    PIR = 3
    PUR = 4 #sensore ultrasuoni
    DOOR_LOCK = 5
    LIGHT_SENSOR = 6

class ObjectColors(Enum):
    BLACK = 0
    RED = 1
    BLUE = 2
    PURPLE = 3
    ORANGE = 4
    GREEN = 5
    WHITE = 6
    GRAY = 7


class Object:
    def __init__(self):
        self.name = ""
        self.description = ""
        self.color = ObjectColors.BLACK
        self.type = ObjectType.NONE
        self.className = None


        idCreator = ToxIDCreator.shared()
        self.id = idCreator.createUniqueID()
        if self.id == None or self.id == 0:
            raise Exception("Creato ID NULL o 0(zero) nell'init di un oggetto")
        self.pin = None 

        ToxMain.shared().addRealObject(self)

    def createDict(self): 
        myDict = {}
        variables = self.__dict__.keys()
        for var in variables:
            if var == "messages": #or var == "handlers"
                continue
            myDict[var] = self.__dict__[var]
        
        return myDict

    def createJSON(self):
        return json.dumps(self.createDict())

    def setID(self, customID):
        self.id = customID

    def printMyProperties(self):
        print(self.__dict__)

    def executeHandlers(self, message):
        handlers = self.handlers[message] 
        if handlers == None:
            return
        for handl in handlers:
            toxFunc = handl.function
            objID = toxFunc.objectId
            funcName = toxFunc.functionName
            #args = toxFunc.args

            realObject = ToxMain.shared().getRealObjectFromID(objID)
            objecs = ToxMain.shared().realObjects
                
            if realObject == None:
                raise Exception("ogetto ottenuto is NULL")
                sys.exit(1)
            function = getattr(realObject, funcName)
            # if args != None:
            #     function(args)
            # else:
            #     funcion()
            function()
            # handValues = handl.split(".")
            # objID = handValues[0]
            # funcName = handValues[1]

            # toxMain = ToxMain()
            # obj = toxMain.getObjectFromID(objID)
            # func = obj.messages[funcName]
            # func()

    def addHandlerForKey(self, key, handler):
        self.handlers[key].append(handler)

    def executeMessage(self, message):
        func = self.messages[message]
        if func != None:
            func()



class DigitalOutputDevice(Object):
    def __init__(self):
        Object.__init__(self)
        self.isOn = False
        self.className = "DigitalOutputDevice"
        #IMPORTANT: DALL'APP VERRANNO CHIAMATI QUESTI MESSAGGI TRAMITE LA FUNC executeMessage(). È l'unico modo per comunicare con l'app esterna
        
        # myID = self.id
        # myFunc = 
        
        self.messages = { 
            "activate": self.activate,
            "deactivate": self.deactivate
        }

        self.handlers = {
            "activate" : [],
            "deactivate" : []
        }

    #TESTING ONLY. DA ELIMINARE
    def printStr(self):
        print("Prova messaggio da handler")

    def activate(self):
        if self.isOn == True:
            return
        #activate the pin


        self.executeHandlers("activate")

        return
        for handler in self.handlers["activate"]:
            if handler != None:
                func = handler.function
                if handler.args != None:
                    func(handler.args)
                else:
                    func()
        

    def deactivate(self):
        if self.isOn == False:
            return
        #deactivate the pin
        for handler in self.handlers["deactivate"]:
            if handler != None:
                func = handler.function
                args = handler.args
                func(args)

    def update(self, value):
        if isinstance(self, DigitalOutputDevice):
            if value > 0:
                self.activate()
            elif value <= 0:
                self.deactivate() 
        #perform some update in pins and execute functions/messages if needed
    

        

class MonoOutputDevice(Object):
    def __init__(self):
        Object.__init__(self)
        self.className = "MonoOutputDevice"
        self.messages = {
            "activate": self.activate
        }

        self.handlers = {
            "activate" : []
        }

    def activate(self):
        self.executeHandlers("activate")
        # for handler in self.handlers["activate"]:
        #     if handler != None:
                #print(type(handler))
                #handler.function()
                # self.executeHandlers("activate")

    #TESTING ONLY. DA ELIMINARE
    def asd(self):
        print("Asdddddd")


class ToxHandler:
    def ___init__(self):
        self.function = None #ToxFunction
        self.args = None

class ToxFunction:
    def __init__(self):
        self.objectId = None
        self.functionName = None


class Timer(MonoOutputDevice):
    def __init__(self):
        MonoOutputDevice.__init__(self)
        self.className = "Timer"
        self.duration = 5
        self.messages = {
            "activate": self.activate,
            "fire": self.startTimer
        }

    def startTimer(self):
        t = threading.Timer(self.duration, self.activate)
        t.start()





###     ToxConverter    ###

JSON_SAVER_FILENAME = "apparecchiature.json"

class JSONSaver:
    def saveToFile(self, data, fileName):
        os.remove(fileName)
        with open(fileName, "w") as outfile:
            json.dump(data, outfile)

    def getFromFile(self, fileName):
        with open(fileName) as f:
            data = json.load(f)
        return data


class ToxConverter(JSONSaver):

    def getObjectsFromJSON(self):
        j = self.getFromFile(JSON_SAVER_FILENAME)
        return j["Objects"]

    def saveToFile(self, data, fileName):
        if isinstance(data, Object):
            newData = data.createDict()
        JSONSaver.saveToFile(self, newData, fileName)







### ToxMain ###

class ToxMain:

    __instance = None

    @staticmethod
    def shared():
        if ToxMain.__instance == None:
            ToxMain()
        return ToxMain.__instance

    def __init__(self):
        if ToxMain.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ToxMain.__instance = self


        self.objects = ToxConverter().getObjectsFromJSON()
        self.realObjects = [] 

        for objD in self.objects:
            realObj = self.createObectFromDict(objD)
            #self.realObjects.append(realObj)

        

    def createObectFromDict(self, dictObj):
        className = dictObj["className"]
        #objClass = getattr(CoreSoftware, className)
        objClass = globals()[className]
        newObj = objClass()
        newObj.name = dictObj["name"]
        newObj.description = dictObj["description"]
        #newObj.color = dictObj["color"]
        #newObj.type = dictObj["type"]
        newObj.pin = dictObj["pin"]
        newObj.id = dictObj["id"]
        newObj.messages = dictObj["messages"]
        newObj.handlers = dictObj["handlers"]
        print(newObj.createJSON())
        
        #TESTING ONLY. DA ELIMINARE
        # func = getattr(newObj, "printStr")
        # func()
        #####

        return newObj
        #return the obj

    def addRealObject(self, obj):
        self.realObjects.append(obj)
        ToxIDCreator.shared().setIDasUsed(obj.id)

    def generateObjectsHandlers(self):
        pass

    def getObjectFromID(self, id):
        for obj in self.objects:
            if obj["id"] == id:
                newObj = self.createObectFromDict(obj)
                return newObj
        return None

    def getObjectFromPin(self, pin, objects):
        for obj in objects:
            if obj.pin == pin:
                return obj
        return None


    def getRealObjectFromPin(self, pin):
        for obj in self.realObjects:
            if obj.pin == pin:
                return obj
        return None

    def getRealObjectFromID(self, id):
        for obj in self.realObjects:
            if obj.id == id:
                return obj
        return None

    # def updateObjetctsStatus(self, status):
    #     for index, value in enumerate(status):
    #         obj = self.getObjectFromPin(index,self.objects)
    #         if obj != None:
    #             obj.update(value)

    def updateObjectsStatus(self, status):
        for index, value in enumerate(status):
            obj = self.getRealObjectFromPin(index)
            if obj != None:
                obj.update(value)





###     ToxSerial   ###


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

    __instance = None

    @staticmethod
    def shared():
        if ToxSerial.__instance == None:
            ToxSerial()
        return ToxSerial.__instance

    def __init__(self):
        self.queue = deque()
        if ToxSerial.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ToxSerial.__instance = self

    def start(self):
        self.ser = serial.Serial("/dev/cu.usbmodem14141", 9600, timeout=0)
        # self.ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0)
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
    
    def updateObjs(self):
        serialObject = ToxSerial.shared()
        serialObject.ser.write("B")
        time.sleep(0.1)
        line = serialObject.ser.readline()
        serialObject.ser.flushInput()
        serialObject.ser.flushOutput()
        print(line)
        ToxMain.shared().updateObjectsStatus(line)
