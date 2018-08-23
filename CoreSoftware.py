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
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
import socket
import traceback
from weather import Weather, Unit
import types

class ToxSerializeableObjectBase:
    def __init__(self):
        pass

    def generateDict(self):
        newDict = {}
        myKeys = list(self.__dict__.keys())
        for key in myKeys:
            value = self.__dict__[key]
            if ToxUtility.isPrimitive(value):
                newDict[key] = value
            elif isinstance(value, ToxSerializeableObjectBase):
                newDict[key] = value.generateDict()
            elif isinstance(value, dict):
                newDict[key] = ToxUtility.getDict(value)
            elif isinstance(value, list):
                newDict[key] = ToxUtility.getList(value)
            else:
                newDict[key] = "ToxConversionError"
        return newDict

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

class ToxUtility:

    @staticmethod
    def isPrimitive(obj):
        primitives = (int, str, float, long, types.NoneType, unicode, basestring)
        return isinstance(obj, primitives)

    @staticmethod
    def getList(objList):
        newList = list()
        for obj in objList:
            if ToxUtility.isPrimitive(obj):
                newList.append(obj)
            elif isinstance(obj, list):
                newList.append(ToxUtility.getList(obj))
            elif isinstance(obj, dict):
                newList.append(ToxUtility.getDict(obj))
            elif isinstance(obj, ToxSerializeableObjectBase):
                newList.append(obj.generateDict())
            else:
                newList.append("ToxConversionObjectError")
            return newList


    @staticmethod
    def getDict(objDict):
        newDict = {}
        keys = objDict.keys()
        for key in keys:
            value = objDict[key]    
            if ToxUtility.isPrimitive(value):
                newDict[key] = value
            elif isinstance(value, list):
                newDict[key] = ToxUtility.getList(value)
            elif isinstance(value, dict):
                newDict[key] = ToxUtility.getDict(value)
            elif isinstance(value, ToxSerializeableObjectBase):
                newDict[key] = value.generateDict()
            else:
                newDict[key] = "ToxConversionObjectError"
        return newDict


class Object(ToxSerializeableObjectBase):
    def __init__(self, autoID = True):
        ToxSerializeableObjectBase.__init__(self)
        self.name = ""
        self.description = ""
        self.color = ObjectColors.BLACK
        self.type = ObjectType.NONE
        #self.className = None

        self.customVariables = {
            "name" : ToxVariable("String", ""),
            "description" : ToxVariable("String", ""),
            "pin" : ToxVariable("Int", None),
            "location" : ToxVariable("String", "")
        }

        self.messages = {}
        self.serializedMessages = {}

        self.handlers = {}
        self.serializedHandlers = {}

        self.className = "Object"

        self.id = None
        if autoID == True:
            self.id = ToxIDCreator.shared().createUniqueID()
            if self.id == None or self.id == 0:
                raise Exception("Creato ID NULL o 0(zero) nell'init di un oggetto")
        self.pin = None 

        ToxMain.shared().addRealObject(self)

    @staticmethod
    def class_():
        return "Object"

    def generateHandlers(self):
        keys = self.handlers.keys()
        if len(keys) <= 0:
            return

        for key in keys:
            if key in self.serializedHandlers:
                self.handlers[key] = [] #Free all handlers            
                for serializedHanlder in self.serializedHandlers[key]:
                    newHandler = ToxHandler.createFromDict(serializedHanlder)
                    newHandler.id_object_owner = self.id
                    self.handlers[key].append(newHandler)

    def removeHandlerWithID(self, id):
        keys = self.handlers.keys()
        for key in keys:
            for handler in self.handlers[key]:
                if handler.id == id:
                    self.handlers[key].remove(handler)
                    ToxIDCreator.shared().setHandlerIDasFree(handler.id)
                    ToxMain.shared().commitObjects()

    def createDict(self): 
        myDict = {}
        variables = self.__dict__.keys()
        for var in variables:
            if var == "serializedHandlers" or var == "serializedMessages":
                continue
            if var == "messages": #or var == "handlers"
                #print(str(self.__dict__["messages"]))
                myDict[var] = self.__dict__["messages"].keys()
                continue
            if var == "handlers" and len(self.__dict__["handlers"]) > 0:
                keyValueHandlers = self.__dict__["handlers"]
                allKeys = list(keyValueHandlers.keys())

                newDict = {}
                for key in allKeys:
                    arrHandlers = keyValueHandlers[key]
                    arrHandlerForKey = list()
                    for hand in arrHandlers:
                        if type(hand) != dict:
                            hd = {
                            "function" : {
                                "objectId" : hand.function.objectId,
                                "functionName" : hand.function.functionName
                                }
                            }
                            if "args" in hand.__dict__:
                                hd["args"] = hand.args
                            if "id" in hand.__dict__:
                                hd["id"] = hand.id
                            arrHandlerForKey.append(hd)
                        else:
                            arrHandlerForKey.append(hand)
                    newDict[key] = arrHandlerForKey
                myDict[var] = newDict
                continue
            if var == "customVariables":
                variables = {}
                if len(self.customVariables.keys()) <= 0:
                    myDict[var] = {}
                    continue
                for key in self.customVariables:
                    variables[key] = self.customVariables[key].createDict()
                myDict[var] = variables
                continue
            myDict[var] = self.__dict__[var]
        
        return myDict

    def createJSON(self):
        return json.dumps(self.createDict())

    def setID(self, customID):
        self.id = customID

    def printMyProperties(self):
        print("ID: " + str(self.id) + str(self.__dict__))

    def executeHandlers(self, message):
        handlers = self.handlers[message] 
        if handlers == None:
            raise Exception("handlers == NULL")
            return
        for handl in handlers:
            toxFunc = handl.function
            objID = toxFunc.objectId
            funcName = toxFunc.functionName
            #args = toxFunc.args
            print("ExecuteHandlers(" + message + "): " + str(objID) + "-->" + str(funcName))
            realObject = ToxMain.shared().getRealObjectFromID(objID)
            # objecs = ToxMain.shared().realObjects
                
            if realObject == None:
                raise Exception("ogetto ottenuto is NULL")
                sys.exit(1)

            realObject.executeMessage(funcName)
            #function = getattr(realObject, funcName)
            # if args != None:
            #     function(args)
            # else:
            #     funcion()
            # function
            # function()

    def addHandlerForKey(self, key, handler):
        self.handlers[key].append(handler)
        ToxMain.shared().commitObjects()#save

    def executeMessage(self, message):
        func = self.messages[message]
        if func != None:
            func()
            print("Eseguito il messaggio: " + message)
            return 0
        print("Errore nell'eseguire il messaggio: " + message)
        return 1

    def removeAllHandlers(self):
        for key in self.handlers:
            del self.handlers[key][:]

    def removeHandlersForKey(self, key):
        del self.handlers[key][:]

    def removeMe(self):
        ToxMain.shared().removeRealObjectForID(self.id)
        ToxMain.shared().commitObjects()

    def setValueForKey(self, value, key):
        # if key not in self.__dict__:
        #     return 1
        # if value == None:
        #     return 1
        if key not in self.customVariables:
            return 1

        if self.customVariables[key] == None:
            if value is str:
                realValue = ToxVariable("String", value)
            elif value is int:
                realValue = ToxVariable("Int", value)
            else:
                realValue = ToxVariable("Float", value)
            self.customVariables[key] = realValue
        else:
            self.customVariables[key].value = value
        
        if key in self.__dict__:
            self.__dict__[key] = value
        return 0

    def update(self, value):
        pass


class Timer(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.className = "Timer"

        self.customVariables["durata"] = ToxVariable("Float", 5)
        
        self.messages = {
            "activate": self.activate,
            "fire": self.startTimer
        }

        self.handlers = {
            "Azione da svolgere" : list()
        }

    def startTimer(self):
        print("Inizio a contare...")
        if "durata" in self.customVariables:
            duration = self.customVariables["durata"].value
        else:
            duration = 0.0
        duration = float(duration)
        t = threading.Timer(duration, self.activate)
        t.start()

    def activate(self):
        print("Timer: sto dicendo agli oggetti di eseguire le azioni che hai richiesto...")
        self.executeHandlers("Azione da svolgere")

    @staticmethod
    def class_():
        return "Timer"

    

class WeatherChecker(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.className = "WeatherChecker"

        self.customVariables["location_temperatura"] = ToxVariable("String", None)

        self.messages = {
            "Controlla il tempo" : self.checkWeather
        }

        self.handlers = {
            "Parzialmente nuvoloso" : list(),
            "Soleggiato" : list(),
            "Neve" : list(),
            "Nuvoloso": list()
        }

    def checkWeather(self):
        print(self.name + ": Controllo il tempo...")

        customLocation = self.customVariables["location_temperatura"].value
        if customLocation == None:
            customLocation = "brescia"

        weather = Weather(unit=Unit.CELSIUS)
        location = weather.lookup_by_location(customLocation)
        condition = location.condition

        code = int(condition.code)

        if code in (29, 30, 44):
            self.executeHandlers("Parzialmente nuvoloso")
        elif code in (26, 27, 28):
            self.executeHandlers("Nuvoloso")
        elif code in (16, 41):
            self.executeHandlers("Neve")
        elif code in (31, 32, 33, 34):
            self.executeHandlers("Soleggiato")
        else:
            print(self.name + ": Codice non corrisponde a niente")

    @staticmethod
    def class_():
        return "WeatherChecker"


class InternetTemperature(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.className = "InternetTemperature"

        self.customVariables["condizione"] = ToxVariable("String", None)
        self.customVariables["location_temperatura"] = ToxVariable("String", None)

        self.messages = {
            "Controlla la temperatura" : self.checkTemperature
        }

        self.handlers = {
            "Condizione verificata" : list()
        }

    def checkTemperature(self):
        logic_condition = self.customVariables["condizione"].value
        if logic_condition == None:
            return
        if len(logic_condition) < 2:
            print("Condizione non valida...")
            return
        
        customLocation = self.customVariables["location_temperatura"].value
        if customLocation == None:
            customLocation = "brescia"

        weather = Weather(unit=Unit.CELSIUS)
        location = weather.lookup_by_location(customLocation)
        weather_condition = location.condition
        curr_temperature = weather_condition.temp

        print(self.name + ".curr_temperature: " + str(curr_temperature))

        operator = logic_condition[0]
        condition_temperature = logic_condition[1:]
        if operator == ">":
            if curr_temperature > condition_temperature:
                self.executeHandlers("Condizione verificata")
        elif operator == "<":
            if curr_temperature < condition_temperature:
                self.executeHandlers("Condizione verificata")
        elif operator == "=":
            if curr_temperature == condition_temperature:
                self.executeHandlers("Condizione verificata")
        else:
            return
        
    @staticmethod
    def class_():
        return "InternetTemperature"

class NumericalCondition(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.className = "NumericalCondition"

        self.customVariables["variabile"] = ToxVariable("Int", 0)
        self.customVariables["condizione"] = ToxVariable("String", None)

        self.messages = {
            "Controllo condizione" : self.eseguiAzioni
        }

        self.handlers = {
            "Condizione verificata" : list()
        }

    def eseguiAzioni(self):
        current_var_value = self.customVariables["variabile"].value
        if current_var_value == None:
            return

        logic_condition = self.customVariables["condizione"].value
        if logic_condition == None:
            return

        operator = logic_condition[0]
        condition_number = int(logic_condition[1:])
        # if operator == ">":
        #     if current_var_value > condition_number:
        #         self.addValue()
        #         self.executeHandlers("Condizione verificata")
        if operator == "<":
            if current_var_value < condition_number:
                self.addValue()
                self.executeHandlers("Condizione verificata")
            else:
                self.customVariables["variabile"] = ToxVariable("Int", 0)
            
        # elif operator == "=":
        #     if current_var_value == condition_number:
        #         self.addValue()
        #         self.executeHandlers("Condizione verificata")
        else:
            return

    def addValue(self):
        curr_value = self.customVariables["variabile"].value
        if curr_value == None:
            return
        new_value = curr_value + 1
        self.setValueForKey(new_value, "variabile")

    @staticmethod
    def class_():
        return "NumericalCondition"

class Lampada(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.className = "Lampada"

        #self.customVariables["isOn"] = ToxVariable("Int", 0)
        self.isOn = False

        self.messages = {
            "activate": self.activate,
            "deactivate": self.deactivate
        }

        self.handlers = {
            "Accensione" : list(),
            "Spegnimento" : list()
        }

    def activate(self):
        print(str(self.generateDict()))
        if self.isOn == False:
            self.isOn = True
            #attiva il pin
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.ACCENSIONE, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Accensione")
    
    def deactivate(self):
        if self.isOn == True:
            self.isOn = False
            #disattiva il pin
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.SPEGNIMENTO, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Spegnimento")

    @staticmethod
    def class_():
        return "Lampada"
        

class ToxHandler(ToxSerializeableObjectBase):
    def __init__(self, autoID = True):
        ToxSerializeableObjectBase.__init__(self)
        self.function = None #ToxFunction
        self.args = None
        self.id_object_owner = None
        if autoID == True:
            self.id = ToxIDCreator.shared().generateUniqueIDforHandlers()
        else:
            self.id = None

    # def getDict(self):
    #     newDict = {
    #         "id" : self.id,
    #         "args" : self.args,
    #         "id_object_owner" : self.id_object_owner,
    #         "function" : self.function.getFunctionDict()
    #     }
    #     return newDict
        

    @staticmethod
    def createFromDict(dictObj):
        if "function" not in dictObj:
            raise Exception("Non ho trovato la chiave 'function' nel dict handler")
        realFunc = ToxFunction()
        realFunc.objectId = dictObj["function"]["objectId"]
        realFunc.functionName = dictObj["function"]["functionName"]

        if "id" in dictObj and dictObj["id"] != None:
            realHandler = ToxHandler(autoID = False)
            realHandler.id = dictObj["id"]
        else:
            realHandler = ToxHandler(autoID = True)
        ToxIDCreator.shared().setHandlerIDasUsed(realHandler.id)

        realHandler.function = realFunc
        # if "id" not in dictObj:
        #     #TODO: MAKE SURE TO HAVE AN ID. SALTATO QUESTO CHECK PER TESTING
        #     raise Exception("Non ho trovato l'ID handler")
        
        if "args" in dictObj:
            realHandler.args = dictObj["args"]
        return realHandler


class ToxFunction(ToxSerializeableObjectBase):
    def __init__(self):
        ToxSerializeableObjectBase.__init__(self)
        self.objectId = None
        self.functionName = None
    
    # def getDict(self):
    #     # newDict = {
    #     #     "objectId" : self.objectId,
    #     #     "functioName" : self.functionName
    #     # }
    #     return self.__dict__


class ToxVariable(ToxSerializeableObjectBase):
    def __init__(self, valueType, value):
        ToxSerializeableObjectBase.__init__(self)
        self.valueType = valueType
        self.value = value

    @staticmethod
    def createFromDict(dictObj):
        return ToxVariable(dictObj["valueType"], dictObj["value"])

    def createDict(self):
        dictObj = {
            "valueType" : self.valueType,
            "value" : self.value
        }
        return dictObj

class ToxBoot:
    @staticmethod
    def boot():
        arraySerializedObjects = ToxConverter.shared().getObjectsFromJSON()
        ToxMain.shared().createRealObjects(arraySerializedObjects)
        ToxIDCreator.shared().getUsedIDs()

        server = ToxSocketServer()
        try:
            start_new_thread(server.activate_server, ())
            start_new_thread(ToxSerial.shared().start, ())
            #start_new_thread(ToxSerialQueueUpdater.shared().start, ())
           # server.activate_server()
        except KeyboardInterrupt:
            print("\nRicevuto segnale di chiusura. Esco...")


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
        self.usedHandlersIDs = []
        
    def generateUniqueIDforHandlers(self):
        id = random.randint(0, 9999)
        while id in self.usedHandlersIDs:
            id = random.randint(0, 9999)
        return id
        
    def setHandlerIDasUsed(self, id):
        if id not in self.usedHandlersIDs and id != None:
            self.usedHandlersIDs.append(id)
    
    def setHandlerIDasFree(self, id):
        try:
            self.usedHandlersIDs.remove(id)
        except:
            raise Exception("Non ho potuto settare l'id handler come free")
            sys.exit(1)

    def getUsedIDs(self):
        objects = ToxConverter.shared().getObjectsFromJSON()
        if len(objects) > 0:
            for obj in objects:
                self.currentIDs.append(obj["id"])

    def setIDasUsed(self, id):
        #print(traceback.format_exc())
        if id not in self.currentIDs and id != None:
            self.currentIDs.append(id)
    
    def setIDasFree(self, id):
        try:
            self.currentIDs.remove(id)
        except:
            raise Exception("Non ho potuto settare l'id object come free")
            sys.exit(1)

    # def getIDsFromStorage(self):
    #     if os.path.isfile(self.FILE_NAME):
    #         with open(self.FILE_NAME) as f:
    #             data = json.load(f)
    #             if data != None:
    #                 return data
    #         return []
    #     else:
    #         return []

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


###     ToxConverter    ###

JSON_SAVER_FILENAME = "apparecchiature.json"

class JSONSaver:
    def saveToFile(self, data, fileName):
        os.remove(fileName)
        with open(fileName, "w") as outfile:
            json.dump(data, outfile, sort_keys=True, indent=2, separators=(',', ': '))

    def getFromFile(self, fileName):
        with open(fileName) as f:
            try:
                data = json.load(f)
                if type(data) != dict:
                    return {"Objects" : []}
                return data
            except:
                newDict = { "Objects" : []}
                return newDict
        


class ToxConverter(JSONSaver):
    __instance = None

    __objects = None

    @staticmethod
    def shared():
        if ToxConverter.__instance == None:
            ToxConverter()
        return ToxConverter.__instance

    def __init__(self):
        if ToxConverter.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ToxConverter.__instance = self
            
    def saveObjectsToJSON(self, objects):
        finalDict = {}
        serializedObjects = list()
        for obj in objects:
            newObj = obj.createDict()
            serializedObjects.append(newObj)
        finalDict["Objects"] = serializedObjects

        # jsonData = json.dumps(finalDict)
        # print(jsonData)
        JSONSaver.saveToFile(self, finalDict, JSON_SAVER_FILENAME)
        

    def getObjectsFromJSON(self):
        if self.__objects == None:
            j = self.getFromFile(JSON_SAVER_FILENAME)
            self.__objects = j["Objects"]
            return self.__objects
        else:
            return self.__objects

    def saveToFile(self, data, fileName):
        if isinstance(data, Object):
            newData = data.createDict()
            JSONSaver.saveToFile(self, newData, fileName)
        else:
            raise Exception("i dati che ho ottenuto non sono degli Oggetti")







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

        #self.objects = ToxConverter().getObjectsFromJSON()
        self.realObjects = [] 

        self.classes = [
            Object.class_(),
            Timer.class_(),
            WeatherChecker.class_(),
            Lampada.class_(),
            InternetTemperature.class_(),
            NumericalCondition.class_()
        ]
        
        #self.generateObjectsHandlers()
        
    def createRealObjects(self, fromArray):
        for objD in fromArray:
            realObj = self.createObectFromDict(objD)

    def createObectFromDict(self, dictObj):
        className = dictObj["className"]
        #objClass = getattr(CoreSoftware, className)
        objClass = globals()[className]
        newObj = objClass(autoID = False)
        newObj.name = dictObj["name"]
        newObj.description = dictObj["description"]
        #newObj.color = dictObj["color"]
        #newObj.type = dictObj["type"]
        newObj.pin = dictObj["pin"]
        newObj.id = dictObj["id"]
        # if "messages" in dictObj:
        #     newObj.messages = dictObj["messages"]
        newObj.serializedHandlers = dictObj["handlers"]
        newObj.generateHandlers()

        customSerializedVariables = dictObj["customVariables"]
        for key in customSerializedVariables.keys():
            serVar = customSerializedVariables[key]
            newObj.customVariables[key] = ToxVariable(serVar["valueType"], serVar["value"])
        return newObj


    def addRealObject(self, obj):
        self.realObjects.append(obj)
        ToxIDCreator.shared().setIDasUsed(obj.id)
        #self.saveRealObjectsToDisk()

    def commitObjects(self):
        self.saveRealObjectsToDisk()

    def saveRealObjectsToDisk(self):
        ToxConverter.shared().saveObjectsToJSON(self.realObjects)

    def generateObjectsHandlers(self):
        for obj in self.realObjects:
            obj.generateHandlers()

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

    def updateObjectsStatus(self, status):
        try:
            statusDict = json.loads(status)
        except:
            print("ToxMain.updateObjectsStatus: errore nel caricare il json dal response dell'Arduino")
            return
        
        allPins = statusDict["pins_d"]
        allPins.extend(statusDict["pins_a"])
        for pin_n, status in enumerate(allPins):
            realObj = self.getRealObjectFromPin(pin_n)
            if realObj == None:
                continue
            else:
                pass
                #print("Eseguito update del pin: " + str(pin_n) + " con stato: " + str(status))
            realObj.update(status)

            

    def removeRealObjectForID(self, id):
        for index, obj in enumerate(self.realObjects):
            if obj.id == id:
                del self.realObjects[index]
                ToxIDCreator.shared().setIDasFree(id)
                break

        self.saveRealObjectsToDisk()

    def isObjectNameUnique(self, name):
        for obj in self.realObjects:
            if obj.name == name:
                return False
        return True



###     ToxSerial   ###


# class ToxSerialMessageType(Enum):
#     SPEGNIMENTO = 0
#     ACCENSIONE = 1
#     GET_VALUE = 2


# class ToxSerialMessage:
#     def __init__(self, pin, msgType): #msgType : ToxSerialMessageType
#         self.pin = pin
#         offstr = ""
#         delis = "<"
#         delir = ">"

#         if msgType == 0:
#             offstr = ""


#         if msgType == 2:
#             self.isResponseRequested = True
#         else:
#             self.isResponseRequested = False
#         self.message = ""
#         if self.pin > 9:
#             pass


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
        self.ser = serial.Serial("/dev/cu.usbmodem142301", 9600, timeout=3, write_timeout=3)
        # self.ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0)
        time.sleep(2.5)
        start_new_thread(ToxSerialQueueUpdater.shared().start, ())
        start_new_thread(self.performQueue, ())


    def addToQueue(self, message):
        # if message.id == 0:
        #     self.queue.append(message)
        #     return
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
        num = 0
        while True:
            time.sleep(0.1)
            num = num + 1
            #print(str(num))
            if len(self.queue) >= 1:
                msg = self.queue[0]
                if msg.id == 0:
                    self.ser.write("<09000>")
                    time.sleep(0.2)
                    response = self.ser.read(self.ser.inWaiting())#self.ser.readline()
                    #print(response)
                    ToxMain.shared().updateObjectsStatus(response)
                else:
                    # if msg.type == 0:
                    #     st_code = "<010"
                    # elif msg.type == 1:
                    #     st_code = "<020"
                    # fn_code = ">"
                    # if msg.pin > 9:
                    #     md_code = str(msg.pin)
                    # else:
                    #     md_code = "0" + str(msg.pin)
                    # code = st_code + md_code + fn_code
                    if msg.ser_str == None:
                        return
                    code = msg.ser_str
                    print("code to serial: " + code)
                    self.ser.write(code)
                    time.sleep(0.1)
                    response = self.ser.readline()
                    print(response)
                    
                self.queue.popleft()
    
    def printQueue(self):
        print(self.queue)
    
    def printQueueLen(self):
        print("Blocchi all'interno della queue: " + str(len(self.queue)))



class ToxSerialMessage:
    def __init__(self, id):
        self.id = id
        self.pin = None
        self.type = None

        self.ser_str = None

    @staticmethod
    def create(type, pin):
        id = random.randint(1, 999999)

        prefix = ""
        suffix = ""
        if type < 10:
            prefix = "0"
        prefix += str(type)
        middle = str(0) #middle number is unused at this moment
        if pin < 10:
            suffix = "0"
        suffix += str(pin)

        me = ToxSerialMessage(id)
        me.ser_str = "<" + prefix + middle + suffix + ">"

        return me
        
class SerialMessageType(Enum):
    ACCENSIONE = 1
    SPEGNIMENTO = 2

class ToxSerialQueueUpdater:
    __instance = None

    updateTime = 0.2

    @staticmethod
    def shared():
        if ToxSerialQueueUpdater.__instance == None:
            ToxSerialQueueUpdater()
        return ToxSerialQueueUpdater.__instance

    def __init__(self):
        if ToxSerialQueueUpdater.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ToxSerialQueueUpdater.__instance = self

    def start(self):
        while True:
            msg = ToxSerialMessage(0)
            ToxSerial.shared().addToQueue(msg)
            time.sleep(self.updateTime)

    
        
# class ToxSerialUpdate:
    
#     def updateObjs(self):
#         serialObject = ToxSerial.shared()
#         serialObject.ser.write("B")
#         time.sleep(0.1)
#         line = serialObject.ser.readline()
#         serialObject.ser.flushInput()
#         serialObject.ser.flushOutput()
#         print(line)
#         ToxMain.shared().updateObjectsStatus(line)



class ToxSocketServer:
    def __init__(self, port = 8080):
        self.host = ''
        self.port = port

    def activate_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)

        try:
            self.socket.bind((self.host, self.port))
        except Exception as e:
            print ("Error: Could not aquite port:",self.port,"\n")
            print(str(e))
            self.shutdown()
            sys.exit(1)

        self._wait_for_connections()
    
    def shutdown(self):
        try:
            s.socket.shutdown(socket.SHUT_RDWR)
            s.close()
        except Exception as e:
            print("Errore nello spegnimento del server. Forse era già spento")


    def _handle_request(self, conn):
        data = conn.recv(8192)
        try:
            request = json.loads(data)
            print(str(request))
        except ValueError:
            print("Nessun messaggio")
            conn.close()
            return
        except:
            print("Qualche errore con la richiesta dal client")
            conn.close()
            return
        #print(str(data))
        requestType = request["request-type"]
        if "request-body" in request:
            requestBody = request["request-body"]
        else:
            returnDict = {
                "code" : "NO",
                "response" : "Nessun request-body nella tua richiesta"
            }
            conn.send(json.dumps(returnDict))
            conn.close()
            return

        if requestType == "create_new_object":
            if "name" in requestBody and "description" in requestBody and "className" in requestBody:
                objClass = globals()[requestBody["className"]]
                if ToxMain.shared().isObjectNameUnique(requestBody["name"]) == False:
                    returnDict = {
                        "code" : "NO",
                        "response": "Il nome dell'oggetto non è unique"
                    }
                    print("Nome non unique")
                    conn.send(json.dumps(returnDict))
                    conn.close()
                    return
                newObject = objClass()
                #newObject.name = requestBody["name"]
                newObject.setValueForKey(requestBody["name"], "name")

                newObject.description = requestBody["description"]
                newObject.setValueForKey(requestBody["description"], "description")

                if "pin" in requestBody:
                    newObject.setValueForKey(requestBody["pin"], "pin")
                    #newObject.pin = requestBody["pin"]
                # if "variables" in request:
                #     newObject.customVariables = request["variables"]
                ToxMain.shared().commitObjects()
                print("Nuovo oggetto creato con successo!")
                odic = newObject.createDict()
                newDict = {
                    "code" : "OK",
                    "response" : "Oggetto creato con successo!"
                }
                
                ojson = str(json.dumps(newDict))
                
                conn.send(ojson)
                
            else:
                print("Errore nella creazione oggetto. Qualche valore mancante")
                conn.send("Errore nella creazione oggetto. Qualche valore mancante") 
            
        
        elif requestType == "modify_handler_actions":
            all_handlers = requestBody["handlers"]
            handlers_key = requestBody["handlers-obj-key"]
            obj_id_of_object_receiver = requestBody["objID-receiver"]
            real_object_receiver = ToxMain.shared().getRealObjectFromID(obj_id_of_object_receiver)
            if real_object_receiver == None:
                raise Exception("Ottento un oggetto NULL durante la modifica degli handlers nel ToxServer")
            real_object_receiver.removeHandlersForKey(handlers_key)

            for handler in all_handlers:
                print("HANDLER: " + str(handler))
                if "function" not in handler:
                    raise Exception("'function' non è nell'handler")
                    sys.exit(1)
                tox_func = handler["function"]
                if "objectId" not in tox_func:
                    raise Exception("'objectId' non è nella func")
                    sys.exit(1)
                objID = tox_func["objectId"]
                if "functionName" not in tox_func:
                    raise Exception("'functionName' non è nella func")
                    sys.exit(1)
                func_name = tox_func["functionName"]

                newToxHandler = ToxHandler()
                newToxHandler.args = None
                newToxFunction = ToxFunction()
                newToxFunction.functionName = func_name
                newToxFunction.objectId = objID

                newToxHandler.function = newToxFunction

                real_object_receiver.addHandlerForKey(handlers_key, newToxHandler)
                conn.send("Handlers changed correctly")
                print("added handler successfully")
        elif requestType == "add_handler":
            handler = requestBody
            if "id_object_owner" not in handler:
                returnDict = {
                    "code" : "NO",
                    "response" : "Manca l'id_object_owner"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            if "key" not in handler:
                returnDict = {
                    "code" : "NO",
                    "response" : "key non trovata nella richiesta che mi hai mandato"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            if "function" not in handler:
                returnDict = {
                    "code" : "NO",
                    "response" : "Manca la function"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            key = handler["key"]
            id_obj_owner = handler["id_object_owner"]
            objOwner = ToxMain.shared().getRealObjectFromID(id_obj_owner)

            if objOwner == None:
                returnDict = {
                    "code" : "NO",
                    "response" : "Non ho trovato nessun oggetto con l'ID che mi hai dato"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            handlerFunction = handler["function"]

            if "objectId" not in handlerFunction:
                returnDict = {
                    "code" : "NO",
                    "response" : "ObjectID della funzione non inviato"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            idObjectFunction = handlerFunction["objectId"]

            
            if "functionName" not in handlerFunction:
                returnDict = {
                    "code" : "NO",
                    "response" : "Non ho trovato nessuna functionName nella tua richiesta"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            functionName = handlerFunction["functionName"]

            realFunction = ToxFunction()
            realFunction.functionName = functionName
            realFunction.objectId = idObjectFunction

            realHandler = ToxHandler()
            realHandler.function = realFunction
            realHandler.id_object_owner = objOwner.id
            realHandler.args = None

            objOwner.addHandlerForKey(key, realHandler) 

            returnDict = {
                "code" : "OK",
                "response" : "Handler aggiunto con successo"
            }
            conn.send(json.dumps(returnDict))


        elif requestType == "show_objects":
            arr = list()
            realobjs = ToxMain.shared().realObjects
            print("realObjs.count = " + str(len(realobjs)))
            for obj in realobjs:
                arr.append(obj.createDict())
            returnDict = {
                "code" : "OK",
                "response" : arr
            }
            json_str = json.dumps(returnDict)
            conn.send(json_str)
        elif requestType == "remove_object":
            if "object_id" not in requestBody:
                returnDict = {
                    "code" : "NO",
                    "response" : "non ho trovato 'object_id' nella tua richiesta"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            objectID = requestBody["object_id"]
            obj = ToxMain.shared().getRealObjectFromID(objectID)

            if obj == None:
                returnDict = {
                    "code" : "NO",
                    "response" : "Oggetto con quell'ID == NULL"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            obj.removeMe()
            returnDict = {
                "code" : "OK",
                "response" : "Oggetto rimosso con successo!"
            }
            conn.send(json.dumps(returnDict))
        elif requestType == "show_ids":
            ids = ToxIDCreator.shared().currentIDs
            conn.send(str(ids))
        elif requestType == "remove_handler":
            handlerIDToRemove = requestBody["handlerID"]
            objectIDOfHandler = requestBody["obj_id"]
            realObject = ToxMain.shared().getRealObjectFromID(objectIDOfHandler)
            if realObject == None:
                returnDict = {
                    "code" : "NO",
                    "response" : "Nessun oggetto con questo ID"
                }
                conn.send(json.dumps(returnDict))
                return
            if handlerIDToRemove not in ToxIDCreator.shared().usedHandlersIDs and handlerIDToRemove != None:
                returnDict = {
                    "code" : "NO",
                    "response" : "Nessun handler trovato con questo ID nella lista degli handler usati. Oppure ID == NULL"
                }
                conn.send(json.dumps(returnDict))
                return
            realObject.removeHandlerWithID(handlerIDToRemove)
            returnDict = {
                "code" : "OK",
                "response" : "Handler rimosso con successo"
            }
            conn.send(json.dumps(returnDict))
            
        elif requestType == "show_ids_h":
            ids = ToxIDCreator.shared().usedHandlersIDs
            conn.send(str(ids))
        elif requestType == "show_objects_classes":
            classes = ToxMain.shared().classes
            if classes == None:
                returnDict = {
                    "code" : "NO",
                    "response": "Nessuna classe"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            returnDict = {
                "code" : "OK",
                "response": classes
            }
            conn.send(json.dumps(returnDict))
        elif requestType == "execute_message":
            objID = requestBody["objID"]
            messageName = requestBody["messageName"]
            realObject = ToxMain.shared().getRealObjectFromID(objID)
            if realObject == None:
                returnDict = {
                    "code" : "NO",
                    "response" : "Oggetto non trovato con questo ID"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            if realObject.executeMessage(messageName) != 0:
                returnDict = {
                    "code" : "NO",
                    "response" : "Funzione nel messaggio == NULL"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            else:
                returnDict = {
                    "code" : "OK",
                    "response" : "Funzione eseguita con successo"
                }
                conn.send(json.dumps(returnDict))
        elif requestType == "change_properties":
            properties = requestBody["properties"]
            objID = requestBody["objID"]
            realObject = ToxMain.shared().getRealObjectFromID(objID)
            if realObject == None:
                returnDict = {
                    "code" : "NO",
                    "response" : "Oggetto non trovato con questo ID"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            retCode = 0
            for key in properties:
                isSuccess = realObject.setValueForKey(properties[key], key)
                if isSuccess != 0:
                    retCode = isSuccess
                    break
            if retCode != 0:
                returnDict = {
                    "code" : "NO",
                    "response" : "Valore ritornato mentre cambiavo le properties: " + str(retCode)
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            returnDict = {
                "code" : "OK",
                "response" : "Properties modificate con successo!"
            }
            print("Server response: " + str(returnDict))
            conn.send(json.dumps(returnDict))
        elif requestType == "get_handlers":
            if "obj_id" not in requestBody:
                self.send_err(conn, "Nella tua richiesta manca l'objID")
                return
            objID = requestBody["obj_id"]

            realObject = ToxMain.shared().getRealObjectFromID(objID)
            if realObject == None:
                self.send_err(conn, "Nessun oggetto con questo ID")
                return

            #TODO: Finire la funzione...

        elif requestType == "change_properties_values":
            if "obj_id" not in requestBody:
                self.send_err(conn, "Nella tua richiesta manca l'objID")
                return
            if "properties" not in requestBody:
                self.send_err(conn, "Nella tua richiesta mancano le properties")
                return
            objID = requestBody["obj_id"]
            properties = requestBody["properties"]

            realObj = ToxMain.shared().getRealObjectFromID(objID)
            if realObj == None:
                self.send_err(conn, "Nessun oggetto con questo ID")
                return
            
            keys = properties.keys()
            success = 0
            for key in keys:
                # if key == "name" and realObj.customVariables["name"].value == properties[key]:
                #     continue
                if realObj.customVariables[key].value == properties[key]:
                    continue
                if properties[key] in ("$null", -1, -1.0):
                    success = realObj.setValueForKey(None, key)
                else:
                    success = realObj.setValueForKey(properties[key], key)
                if success != 0:
                    err = "Non ho trovato una key che mi hai passato in questo oggetto. Codice errore: " + str(success) + "  key, value: " + str(key) + ", " + str(properties[key])
                    self.send_err(conn, err)
                    return
            ToxMain.shared().commitObjects()
            self.send_msg(conn, "Properties modificate con successo!")
            

        #conn.send("Scemotto! Hide and Seek\n")
        conn.close()

    def send_err(self, conn, msg):
        returnDict = {
            "code" : "NO",
            "response" : msg
        }
        conn.send(json.dumps(returnDict))
        conn.close()

    def send_msg(self, conn, msg):
        returnDict = {
            "code" : "OK",
            "response" : msg
        }
        conn.send(json.dumps(returnDict))

    def _wait_for_connections(self):
        while True:
            self.socket.listen(5)

            conn, addr = self.socket.accept()
            print("Server <-- " + addr[0])

            start_new_thread(self._handle_request, (conn,))
