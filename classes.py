# coding=utf-8
import json
import time
from enum import Enum
import inspect
from ToxIDCreator import ToxIDCreator
import threading

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

        idCreator = ToxIDCreator()
        self.id = idCreator.createUniqueID()
        self.pin = None 

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


#TODO: Fix this function and find a way to use it because i don't know why i wrote it
    # def executeHandlers(self, message):
    #     handlers = self.handlers[message] 
    #     if handlers == None:
    #         return
    #     for handl in handlers:
    #         handValues = handl.split(".")
    #         objID = handValues[0]
    #         funcName = handValues[1]

    #         toxMain = ToxMain()
    #         obj = toxMain.getObjectFromID(objID)
    #         func = obj.messages[funcName]
    #         func()

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
        #IMPORTANT: DALL'APP VERRANNO CHIAMATI QUESTI MESSAGGI TRAMITE LA FUNC executeMessage(). È l'unico modo per comunicare con l'app esterna
        self.messages = { 
            "activate": self.activate,
            "deactivate": self.deactivate
        }

        self.handlers = {
            "activate" : [],
            "deactivate" : []
        }

    def activate(self):
        if self.isOn == True:
            return
        #activate the pin
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
        self.messages = {
            "activate": self.activate
        }

        self.handlers = {
            "activate" : []
        }

    def activate(self):
        for handler in self.handlers["activate"]:
            if handler != None:
                handler.function()



class ToxHandler:
    def ___init__(self):
        self.function = None
        self.args = None




class Timer(MonoOutputDevice):
    def __init__(self):
        MonoOutputDevice.__init__(self)
        self.duration = 5
        self.messages = {
            "activate": self.activate,
            "fire": self.startTimer
        }

    def startTimer(self):
        t = threading.Timer(self.duration, self.activate)
        t.start()



def printT():
    print("Done...")

timer = Timer()
timer.duration = 2

completion = ToxHandler()
completion.function = printT
timer.addHandlerForKey("activate", completion)

obj1 = DigitalOutputDevice()
completion2 = ToxHandler()
completion2.function = timer.messages["fire"]
completion2.args = None
obj1.addHandlerForKey("activate", completion2)

obj1.executeMessage("activate")

