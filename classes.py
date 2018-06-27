import json
import time
from enum import Enum
import inspect

class ObjectType(Enum):
    NONE = 0
    LUCE = 1
    VENTOLA = 2
    PIR = 3
    PUR = 4 #sensore ultrasuoni
    DOOR_LOCK = 5
    LIGHT_SENSOR = 6



class Object:
    def __init__(self):
        self.name = ""
        self.type = ObjectType.NONE
        self.id = 0
        self.priority = 0
        self.pins = None 


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

        

