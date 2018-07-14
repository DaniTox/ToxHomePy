import json
import time
from enum import Enum
import inspect
import ToxIDCreator

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
        self.id = ToxIDCreator().createUniqueID()
        self.priority = 0
        self.pins = None 
        self.onActivationActionsObjects = None
        self.onDeactivationActionsObjects = None
        self.status = 0

#subclasses have to override these 2 functions adding the actions to perform and then calling the super functions
    def activate(self):  #private func
        for obj in self.onActivationActionsObjects:
            obj.activate()

    def deactivate(self): #private func
        for obj in self.onDeactivationActionsObjects:
            obj.deactivate()
####################################
    def setStatus(self, code):
        if self.status == code:
            return
        else:
            if code > self.status:
                self.activate()
            elif code < self.status:
                self.deactivate()

    def createDict(self): 
        myDict = {}
        variables = self.__dict__.keys()
        for var in variables:
            myDict[var] = self.__dict__[var]
        
        return myDict

    def createJSON(self):
        return json.dumps(self.createDict())

    def setID(self, customID):
        self.id = customID

    def printMyProperties(self):
        print(self.__dict__)



class Luce(Object):
    def __init__(self):
        Object.__init__(self)
        
        #Old properties
        self.priority = 1
        self.type = ObjectType.LUCE

        #New properties
        self.isOn = False


    def switchOn(self):
        self.isOn = True
    
    def switchOff(self):
        self.isOn = False

    def switch(self):
        self.isOn = not self.isOn


class Ventola(Object):
    def __init__(self):
        Object.__init__(self)
        self.type = ObjectType.VENTOLA

        self.isOn = False

    def activate(self):
        self.isOn = True


    def disable(self):
        self.isOn = False

#call a method in a class that will connect to the arduino telling him to stop/activate the fan

class DoorLock(Object):
    def __init__(self):
        Object.__init__(self)

        #Old
        self.type = ObjectType.DOOR_LOCK

        #New
        self.isOpen = False


    def open(self):
        self.isOpen = True

    def close(self):
        self.isOpen = False


class PIRSensor(Object):
    def __init__(self):
        Object.__init__(self)

        self.type = ObjectType.PIR
        self.priority = 100
        

class LightSensor(Object):
    def __init__(self):
        Object.__init__(self)

        

class Timer(Object):
    def __init__(self):
        Object.__init__(self)
        self.timerDuration = 0

    def performAction(self):
        self.activate()

    def fireTimer(self):
        self.activate()