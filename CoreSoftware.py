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
import pyowm
from datetime import datetime
import platform

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


####    CLASSES APPARECCHIATURE     ###

class Object(ToxSerializeableObjectBase):
    def __init__(self, autoID = True):
        ToxSerializeableObjectBase.__init__(self)
        self.name = ""
        self.description = ""
        #self.color = ObjectColors.BLACK
        #self.type = ObjectType.NONE
        #self.className = None
        

        self.customVariables = {
            "name" : ToxVariable("String", ""),
            "description" : ToxVariable("String", "")#,
            # "pin" : ToxVariable("Int", None),
            # "location" : ToxVariable("String", "")
        }
        
        self.messages = {}
        self.serializedMessages = {}

        self.handlers = {}
        self.serializedHandlers = {}

        self.className = "Object"

        self.liveProperty = ""

        self.id = None
        if autoID == True:
            self.id = ToxIDCreator.shared().createUniqueID()
            if self.id == None or self.id == 0:
                raise Exception("Creato ID NULL o 0(zero) nell'init di un oggetto")
        #self.pin = None 

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
                if self.serializedHandlers[key] == None:
                    continue          
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

    # def createDict(self): 
    #     myDict = {}
    #     variables = self.__dict__.keys()
    #     for var in variables:
    #         if var == "serializedHandlers" or var == "serializedMessages":
    #             continue
    #         if var == "messages": #or var == "handlers"
    #             #print(str(self.__dict__["messages"]))
    #             myDict[var] = self.__dict__["messages"].keys()
    #             continue
    #         if var == "handlers" and len(self.__dict__["handlers"]) > 0:
    #             keyValueHandlers = self.__dict__["handlers"]
    #             allKeys = list(keyValueHandlers.keys())

    #             newDict = {}
    #             for key in allKeys:
    #                 arrHandlers = keyValueHandlers[key]
    #                 arrHandlerForKey = list()
    #                 for hand in arrHandlers:
    #                     if type(hand) != dict:
    #                         hd = {
    #                         "function" : {
    #                             "objectId" : hand.function.objectId,
    #                             "functionName" : hand.function.functionName
    #                             }
    #                         }
    #                         if "args" in hand.__dict__:
    #                             hd["args"] = hand.args
    #                         if "id" in hand.__dict__:
    #                             hd["id"] = hand.id
    #                         arrHandlerForKey.append(hd)
    #                     else:
    #                         arrHandlerForKey.append(hand)
    #                 newDict[key] = arrHandlerForKey
    #             myDict[var] = newDict
    #             continue
    #         if var == "customVariables":
    #             variables = {}
    #             if len(self.customVariables.keys()) <= 0:
    #                 myDict[var] = {}
    #                 continue
    #             for key in self.customVariables:
    #                 variables[key] = self.customVariables[key].createDict()
    #             myDict[var] = variables
    #             continue
    #         myDict[var] = self.__dict__[var]
        
    #     return myDict

    def generateDict(self, saving = False):
        tempDict = ToxSerializeableObjectBase.generateDict(self)
        if "messages" in tempDict:
            tempDict["messages"] = list(tempDict["messages"].keys())
        if "serializedHandlers" in tempDict:
            del tempDict["serializedHandlers"]
        if "serializedMessages" in tempDict:
            del tempDict["serializedMessages"]
        
        keys = tempDict["handlers"].keys()
        for key in keys:
            if tempDict["handlers"][key] == None:
                tempDict["handlers"][key] = list()
        #print("\n\n\n" + str(tempDict))
        # if saving == False:
        #     keys = tempDict["handlers"].keys()
        #     for key in keys:
        #         if tempDict["handlers"][key] == None:
        #             tempDict["handlers"][key] = list()
        # if "handlers" in tempDict and saving == False:
        #     keys = tempDict["handlers"].keys()
        #     for key in keys:
        #         if tempDict["handlers"][key] == None:
        #             tempDict["handlers"][key] = list()
        return tempDict

    def createJSON(self):
        return json.dumps(self.generateDict())

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
                # raise Exception("ogetto ottenuto is NULL")
                print("Oggetto ottenuto is NULL")
                return
                # sys.exit(1)
            try:
                realObject.executeMessage(funcName)
            except RuntimeError:
                pass
            #function = getattr(realObject, funcName)
            # if args != None:
            #     function(args)
            # else:
            #     funcion()
            # function
            # function()

    def addHandlerForKey(self, key, handler):
        self.handlers[key].append(handler)
        ToxIDCreator.shared().setHandlerIDasUsed(handler.id)
        ToxMain.shared().commitObjects()#save

    def executeMessage(self, message):
        func = self.messages[message]
        if func != None:
            #func()
            start_new_thread(func, ())
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
        self.sendDeleteMessageToArduino()

    def sendDeleteMessageToArduino(self):
        if self.get("pin") == None:
            return
        pin = self.get("pin")
        
        message = ToxSerialMessage.create(SerialMessageType.DELETE, pin)
        ToxSerial.shared().addToQueue(message)

    # def checkIntegrityTypes(self, oldToxValue, newRawValue):
    #     oldType = oldValue.valueType
    #     newType = type(newRawValue)

    #     if oldType == "Int":
    #         if newType == int:
    #             return 0
    #         elif newType == float:

    #     elif oldType == "Float":
    #         pass
    #     else:
    #         pass    



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
            oldValue = self.customVariables[key]
            oldType = oldValue.valueType

            if oldType == "Int":
                if type(value) is int:
                   self.customVariables[key].value = value
                elif type(value) is float:
                    self.customVariables[key].value = int(value)
                elif type(value) is str or type(value) is unicode:
                    try:
                        newValue = int(value)
                        self.customVariables[key].value = newValue
                    except:
                        return 2
            elif oldType == "Float":
                if type(value) is int:
                   self.customVariables[key].value = float(value)
                elif type(value) is float:
                    self.customVariables[key].value = round(value)
                elif type(value) is str or type(value) is unicode:
                    try:
                        newValue = float(value)
                        self.customVariables[key].value = newValue
                    except:
                        return 2
            elif oldType == "String":
                if type(value) is int:
                   self.customVariables[key].value = str(value)
                elif type(value) is float:
                    self.customVariables[key].value = str(value)
                elif type(value) is str or type(value) is unicode:
                    self.customVariables[key].value = value
            else:
                return 3

        if key in self.__dict__:
            self.__dict__[key] = value
        return 0

    def get(self, key, retTox_v = False):
        cvars = self.customVariables
        if key not in cvars:
            return None
        if cvars == None:
            return None
        if retTox_v == False:
            return cvars[key].value
        else:
            return cvars[key]
        
    def getToxValueForKey(self, key): #same as get() but more understandable
        return self.get(key, retTox_v=True)

    def update(self, value):
        pass

class VirtualObject(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.isVirtual = True

class ConcreteObject(Object):
    def __init__(self, autoID = True):
        Object.__init__(self, autoID)
        self.isVirtual = False
        
        self.customVariables["pin"] = ToxVariable("Int", None)
        self.customVariables["location"] = ToxVariable("String", "")


# NB:
# È ESTREMAMAMENTE SCONSIGLIATO aggiungere handler agli oggetti FISICI. La soluzione è la ToxAxtion
# Una ToxAction serve per eseguire un'azione di un oggetto fisico oltre che azioni degli oggetti virtuali.
# Un esempio: se devo far si che la luce si accenda e si spenga per 3 volte \n
# non posso mettere tutta la logica negli handler degli oggetti fisici perchè \n
# questo farebbe si che se io volessi eseguire un'altra azione, per esempio accendere la luce normalmente \n
# eseguendo il suo messaggio, partirebbe la logica dell'accensione e spegnimento per tre volte \n
# che ho scritto prima.
# Per ovviare a questo, si crea una tox action che esegue i controlli con la NumericalCondition e si accende \n
# e spegne la luce come conseguenza dei messaggi inviati dagli oggetti virtuali.
# Gli Handler degli oggetti fisici possono essere usati (con cautela) se si vuole simulare un impianto in parallelo \n
# così se si vuole accendere le luci del balcone (composto da 3 lampade per esempio), non si devono aggiungere \n
# 3 handler per tre luci diverse ma si aggiunge a una lampada e quest'ultima eseguirà i suoi handler dove \n
# manderà dei messaggi alle altre luci.

class ToxAction(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
        self.className = "ToxAction"
        # self.isAction = True

        self.actionObjectsIDs = list()

        self.customVariables["isActive"] = ToxVariable("Int", 1)

        self.messages = {
            "Esegui azione" : self.execute,
            "Azione conclusa" : self.finish,
            "Attiva": self.activate,
            "Disattiva" : self.deactivate
        }

        self.handlers = {
            "Azione da eseguire" : list(),
            "Azione conclusa" : list()
        }

    def activate(self):
        self.setValueForKey(1, "isActive")
        print("ToxAction è stata settata to Attiva")

    def deactivate(self):
        self.setValueForKey(0, "isActive")
        print("ToxAction è stata settata to Disattiva")

    def removeObjIDfromMyList(self, objID):
        if objID == None:
            return 1
        try:
            self.actionObjectsIDs.remove(objID)
            ToxMain.shared().keepActionsIntegrity()
            ToxMain.shared().commitObjects()
            return 0
        except ValueError:
            return 2
        

    def addObjIDtoMyList(self, objID):
        if objID == None:
            return 1
        if objID in self.actionObjectsIDs:
            return 0
        self.actionObjectsIDs.append(objID)
        ToxMain.shared().commitObjects()
        return 0
           
    
    def execute(self):
        isActive = self.get("isActive")
        if isActive == 1 or isActive == None:
            print("ToxAction è abilitata. Eseguo...")
            self.executeHandlers("Azione da eseguire")
        elif isActive == 0:
            print("ToxAction disabilitata. Non eseguo...")
        

    def finish(self):
        self.executeHandlers("Azione conclusa")

    @staticmethod
    def class_():
        return "ToxAction"


class Timer(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
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

        self.liveProperty = "Sto contando i secondi..."

        t = threading.Timer(duration, self.activate)
        t.start()

    def activate(self):
        print("Timer: sto dicendo agli oggetti di eseguire le azioni che hai richiesto...")
        self.executeHandlers("Azione da svolgere")
        self.liveProperty = "In Riposo"

    @staticmethod
    def class_():
        return "Timer"

    

class WeatherChecker(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
        self.className = "WeatherChecker"
        
        self.customVariables["location_temperatura"] = ToxVariable("String", None)

        self.messages = {
            "Controlla il tempo" : self.checkWeather,
            "Sereno" : self.sereno,
            "Pioggia" : self.pioggia
        }

        self.handlers = {
            "Temporali" : list(),
            "Pioviggino" : list(),
            "Pioggia" : list(),
            "Neve" : list(),
            "Nebbia": list(),
            "Nuvoloso" : list(),
            "Sereno" : list(),
            "Qualsiasi" : list()
        }

    def sereno(self):
        self.executeHandlers("Sereno")

    def pioggia(self):
        self.executeHandlers("Pioggia")

    def fetchWeatherFromAPI(self, isLive = False):
        if isLive == False:
            print(self.name + ": Controllo il tempo...")

        customLocation = self.customVariables["location_temperatura"].value
        if customLocation == None:
            customLocation = "brescia"

        owm = pyowm.OWM('9626593728b889faec6aa8925aca3399')
        try:
            observation = owm.weather_at_place(customLocation)
        except pyowm.exceptions.api_response_error.NotFoundError:
            print("Il pyowm modulo dice che non ha trovato la città che richiedi.")
            #self.executeHandlers("Qualsiasi")
            return
        w = observation.get_weather()
        
        if isLive == False:
            print(str(w._status))
        return w._weather_code

    def getWeatherName(self, code):
        weatherDict = {
            "2" : "Temporali",
            "3" : "Pioviggino",
            "5" : "Pioggia",
            "6" : "Neve",
            "7" : "Nebbia",
            "8" : "Nuvoloso",
        }
        return weatherDict[code]

    def checkWeather(self):
        code = self.fetchWeatherFromAPI()
        groupCode = str(code)[0]
        
        if groupCode not in ("0", "1", "2", "3", "4", "5", "6", "7", "8"):
            print("Codice tempo atmosferico non è nell'elenco dei codici autorizzati")
            return

        if code == 800:
            self.executeHandlers("Sereno")
        else:
            self.executeHandlers(self.getWeatherName(str(groupCode)))
        self.executeHandlers("Qualsiasi")


    def live(self):
        code = self.fetchWeatherFromAPI(isLive=True)
        groupCode = str(code)[0]

        if code == 800:
            self.liveProperty = "Sereno"
        else:
            self.liveProperty = self.getWeatherName(groupCode)

    @staticmethod
    def class_():
        return "WeatherChecker"

class TimeCondition(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
        self.className = "TimeCondition"

        self.customVariables["condizione"] = ToxVariable("String", None)

        self.messages = {
            "Controlla la condizione" : self.checkCondition
        }

        self.handlers = {
            "Condizione verificata" : list(),
            "Condizione non verificata" : list()
        }

    def checkCondition(self):
        if condizione == None:
            return
        condizione = self.get("condizione")
        if type(condizione) is not str:
            condizione = str(condizione)

        operator = condizione[0]
        orario_cond = condizione[1:]
        ore_cond = orario_cond.split(":")[0]
        min_cond = orario_cond.split(":")[1]

        curr_time = datetime.now().time()
        condition_time =  time(int(ore_cond), int(min_cond))

        if operator == ">":
            if curr_time > condition_time:
                self.executeHandlers("Condizione verificata")
            else:
                self.executeHandlers("Condizione non verificata")
        elif operator == "<":
            if curr_time < condtion_time:
                self.executeHandlers("Condizione verificata")
            else:
                self.executeHandlers("Condizione non verificata")
        elif operator == "=":
            if curr_time == condition_time:
                self.executeHandlers("Condizione verificata")
            else:
                self.executeHandlers("Condizione non verificata")
        else:
            return

        @staticmethod
        def class_():
            return "TimeCondition"
        
class Tapparelle(ConcreteObject):
    def __init__(self, autoID = True):
        ConcreteObject.__init__(self, autoID)
        self.className = "Tapparelle"

        self.isOpen = False

        self.handlers = {
            "Aperte" : list(),
            "Chiuse" : list()
        }

        self.messages = {
            "Apri" : self.open,
            "Chiudi" : self.close
        }

    def open(self):
        if self.isOpen != None:
            pin = self.get("pin")
            if pin != None:
                messsage = ToxSerialMessage.create(SerialMessageType.ACCENSIONE, pin)
                ToxSerial.shared().addToQueue(messsage)
            self.executeHandlers("Aperte")
            self.isOpen = True 

    def close(self):
        if self.isOpen != None:
            pin = self.get("pin")
            if pin != None:
                message = ToxSerialMessage.create(SerialMessageType.SPEGNIMENTO, pin)
                ToxSerial.shared().addToQueue(message)
            self.executeHandlers("Chiuse")
    
    def live(self):
        self.liveProperty = "Aperte" if self.isOpen else "Chiuse"

    def setValueForKey(self, value, key):
        if key == "pin":
            message = ToxSerialMessage.create(SerialMessageType.MOTOR, value)
            ToxSerial.shared().addToQueue(message)
        return ConcreteObject.setValueForKey(self, value, key)

    @staticmethod
    def class_():
        return "Tapparelle"

class Repeater(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
        self.className = "Repeater"
        self.isRepeatableObject = True
        self.isRepeatableObjectReady = True

        self.customVariables["secondi"] = ToxVariable("Int", None)

        self.handlers = {
            "Azione da ripetere": list()
        }

    def performActions(self):
        secondi = self.get("secondi")
        if type(secondi) is not int:
            secondi = int(secondi)
        if secondi == None:
            return
        if secondi < 1:
            print("Tempo di secondi troppo basso. Deve essere almeno di 1 secondo")
            return
        
        secondi = float(secondi)

        t = threading.Timer(secondi, self.executeHandlers, ["Azione da ripetere"])
        t.start()

    def repeaterAction(self):
        self.isRepeatableObjectReady = False
        self.performActions()

    def executeHandlers(self, message):
        VirtualObject.executeHandlers(self, message)
        self.isRepeatableObjectReady = True

    @staticmethod
    def class_():
        return "Repeater"

class RealTemperature(ConcreteObject):
    def __init__(self, autoID = True):
        ConcreteObject.__init__(self, autoID)
        self.className = "RealTemperature"

        self.customVariables["condizione"] = ToxVariable("String", None)
        self.customVariables["temperatura"] = ToxVariable("Int", None)

        self.handlers = {
            "Condizione verificata" : list(),
            "Codizione non verificata" : list()
        }


    def setValueForKey(self, value, key):
        if key == "pin" and value != None:
            message = ToxSerialMessage.create(SerialMessageType.DALLAS_TEMPERATURE, value)
            ToxSerial.shared().addToQueue(message)
        return ConcreteObject.setValueForKey(self, value, key)

    @staticmethod
    def class_():
        return "RealTemperature"

    def update(self, value):
        if value == None:
            return  
        self.setValueForKey(value, "temperatura")

    def live(self):
        self.liveProperty = str(self.get("temperatura")) + "° C" 

class InternetTemperature(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
        self.className = "InternetTemperature"

        self.customVariables["condizione"] = ToxVariable("String", None)
        self.customVariables["location_temperatura"] = ToxVariable("String", None)

        self.messages = {
            "Controlla la temperatura" : self.checkTemperature
        }

        self.handlers = {
            "Condizione verificata" : list(),
            "Condizione non verificata" : list()
        }

    def fetchTemperatureFromAPI(self):
        customLocation = self.customVariables["location_temperatura"].value
        if customLocation == None:
            customLocation = "brescia"

        owm = pyowm.OWM('9626593728b889faec6aa8925aca3399')
        try:
            observation = owm.weather_at_place(customLocation)
        except:
            print("Internet Temperature: non ho potuto ottenere la città richiesta")
            return

        w = observation.get_weather()
        curr_temperature = int(w.get_temperature('celsius')["temp"])
        return curr_temperature

    def checkTemperature(self):
        logic_condition = self.customVariables["condizione"].value
        if logic_condition == None:
            return
        if len(logic_condition) < 2:
            print("Condizione non valida...")
            return
        
        curr_temperature = self.fetchTemperatureFromAPI()
        print(self.name + ".curr_temperature: " + str(curr_temperature))

        operator = logic_condition[0]
        try:
            condition_temperature = int(logic_condition[1:])
        except ValueError:
            print("InternetTemerature: Condizione non valida. Ritorno...")
            return
        if operator == ">":
            if curr_temperature > condition_temperature:
                self.executeHandlers("Condizione verificata")
            else:
                self.executeHandlers("Condizione non verificata")
        elif operator == "<":
            if curr_temperature < condition_temperature:
                self.executeHandlers("Condizione verificata")
            else:
                self.executeHandlers("Condizione non verificata")
        elif operator == "=":
            if curr_temperature == condition_temperature:
                self.executeHandlers("Condizione verificata")
            else:
                self.executeHandlers("Condizione non verificata")
        else:
            return

    def live(self):
        self.liveProperty = str(self.fetchTemperatureFromAPI()) + "° C"   
    
    @staticmethod
    def class_():
        return "InternetTemperature"

class NumericalCondition(VirtualObject):
    def __init__(self, autoID = True):
        VirtualObject.__init__(self, autoID)
        self.className = "NumericalCondition"

        self.customVariables["variabile"] = ToxVariable("Int", 0)
        self.customVariables["condizione"] = ToxVariable("String", None)

        self.messages = {
            "Controllo condizione" : self.eseguiAzioni,
            "Azzera" : self.azzera
        }

        self.handlers = {
            "Condizione verificata" : list()
        }

    def azzera(self):
        self.setValueForKey(0, "variabile")

    def eseguiAzioni(self):
        current_var_value = self.customVariables["variabile"].value
        if current_var_value == None:
            return

        logic_condition = self.customVariables["condizione"].value
        if logic_condition == None:
            return

        operator = logic_condition[0]
        try:
            condition_number = int(logic_condition[1:])
        except ValueError:
            print("Valore della condizione non valido. Annullo...")
            return
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

class Porta(ConcreteObject):
    def __init__(self, autoID = True):
        ConcreteObject.__init__(self, autoID)
        self.className = "Porta"

        self.isOpen = False

        self.messages = {
            "Apri" : self.open,
            "Chiudi" : self.close
        }

        self.handlers = {
            "Porta aperta" : list(),
            "Porta chiusa" : list()
        }

    def open(self):
        if self.get("pin") == None:
            return

        pin = self.get("pin")
        if self.isOpen == False:
            message = ToxSerialMessage.create(SerialMessageType.ACCENSIONE, pin)
            ToxSerial.shared().addToQueue(message)
            self.isOpen = True
            self.executeHandlers("Porta aperta")
    
    def close(self):
        if self.get("pin") == None:
            return
        pin = self.get("pin")
        if self.isOpen == True:
            message = ToxSerialMessage.create(SerialMessageType.SPEGNIMENTO, pin)
            ToxSerial.shared().addToQueue(message)
            self.isOpen = False
            self.executeHandlers("Porta chiusa")

    def live(self):
        self.liveProperty = "Aperta" if self.isOpen == True else "Chiusa"
    
    def setValueForKey(self, value, key):
        if key == "pin":
            message = ToxSerialMessage.create(SerialMessageType.SERVO, value)
            ToxSerial.shared().addToQueue(message)
        return ConcreteObject.setValueForKey(self, value, key)

    @staticmethod
    def class_():
        return "Porta"

class Lampada(ConcreteObject):
    def __init__(self, autoID = True):
        ConcreteObject.__init__(self, autoID)
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

    def update(self, value):
        if value == None:
            return
        elif value == 0:
            self.isOn = False
        elif value == 1:
            self.isOn = True
        else:
            # print("Lampada: Non accetto questo dato")
            return    

    def activate(self):
        #print(str(self.generateDict()))
        if self.isOn == False:
            # self.isOn = True
            #attiva il pin
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.ACCENSIONE, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Accensione")
    
    def deactivate(self):
        #if self.isOn == True:
            # self.isOn = False
            #disattiva il pin
        pin = self.customVariables["pin"].value
        if pin != None:
            msg = ToxSerialMessage.create(SerialMessageType.SPEGNIMENTO, pin)
            ToxSerial.shared().addToQueue(msg)
        if self.isOn == True:    
            self.executeHandlers("Spegnimento")

    def live(self):
        self.liveProperty = "Accesa" if self.isOn == True else "Spenta"

    @staticmethod
    def class_():
        return "Lampada"
        
class Ventola(ConcreteObject):
    def __init__(self, autoID = True):
        ConcreteObject.__init__(self, autoID)
        self.className = "Ventola"

        self.handlers = {
            "Accesa" : list(),
            "Spenta" : list()
        }

        self.messages = {
            "Accendi" : self.accendi,
            "Spegni" : self.spegni
        }

        self.isOn = False
    
    
    def update(self, value):
        if value == None:
            return
        elif value == 0:
            self.isOn = False
        elif value == 1:
            self.isOn = True
        else:
            return 


    def accendi(self):
        if self.isOn == False:
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.ACCENSIONE, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Accesa")

    def spegni(self):
        if self.isOn == True:
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.SPEGNIMENTO, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Spenta")


    def live(self):
        self.liveProperty = "Sta girando" if self.isOn else "Ferma"

    @staticmethod
    def class_():
        return "Ventola"


class Buzzer(ConcreteObject):
    def __init__(self, autoID=True):
        ConcreteObject.__init__(self, autoID)
        self.className = "Buzzer"

        self.handlers = {
            "Attivato" : list(),
            "Disattivato" : list()
        }

        self.messages = {
            "Attiva" : self.activate,
            "Disattiva" : self.deactivate
        }

        self.isOn = False

    def update(self, value):
        if value == None:
            return
        elif value == 0:
            self.isOn = False
        elif value == 1:
            self.isOn = True
        else:
            return 

    def activate(self):
        if self.isOn == False:
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.ACCENSIONE, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Attivato")

    def deactivate(self):
        if self.isOn == True:
            pin = self.customVariables["pin"].value
            if pin != None:
                msg = ToxSerialMessage.create(SerialMessageType.SPEGNIMENTO, pin)
                ToxSerial.shared().addToQueue(msg)
            self.executeHandlers("Disattivato")
    
    def live(self):
        self.liveProperty = "Sta suonando..." if self.isOn else "Spento"

    @staticmethod
    def class_():
        return "Buzzer"


class IRSensor(ConcreteObject):
    def __init__(self, autoID = True):
        ConcreteObject.__init__(self, autoID)
        self.className = "IRSensor"
        self.customVariables["Allarme Attiva"] = ToxVariable("Int", 0)
        self.hasBeenAlerted = False

        self.handlers = {
            "Rilevato movimento" : list(),
            "Rilevato intruso" : list(),
            "Allarme spenta" : list(),
            "Allarme accesa" : list()
        }

        self.messages = {
            "Attiva Allarme" : self.activateAlarm,
            "Disattiva Allarme" : self.deactivateAlarm
        }

    def activateAlarm(self):
        self.customVariables["Allarme Attiva"] = ToxVariable("Int", 1)
        self.executeHandlers("Allarme accesa")

    def deactivateAlarm(self):
        self.customVariables["Allarme Attiva"] = ToxVariable("Int", 0)
        self.executeHandlers("Allarme spenta")

    def update(self, value):
        if value == None:
            return

        if value == 1:
            if self.hasBeenAlerted == True: #cioè è già acceso da prima
                return
            if self.get("Allarme Attiva") == 1:
                self.executeHandlers("Rilevato intruso")
            else:
                self.executeHandlers("Rilevato movimento")
            self.hasBeenAlerted = True
        elif value == 0:
            if self.hasBeenAlerted == False:
                return
            self.hasBeenAlerted = False
    
    def live(self):
        alarmState = "[Allarme attiva] - " if self.get("Allarme Attiva") == 1 else "[Allarme disattiva] - "
        rilevamento = "Nessun movimento" if self.hasBeenAlerted == False else "Movimento rilevato..."
        self.liveProperty = alarmState + rilevamento

    @staticmethod
    def class_():
        return "IRSensor"

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
        arguments = sys.argv
        if len(arguments) > 1:
            if arguments[1] == "-t":
                ToxMain.shared().isTesting = True
                print("[+] Attivata la modalità testing.")

        arraySerializedObjects = ToxConverter.shared().getObjectsFromJSON()
        ToxMain.shared().createRealObjects(arraySerializedObjects)
        ToxIDCreator.shared().getUsedIDs()

        start_new_thread(ToxMain.shared().checkRepeatableObjectsAndExecuteThem, ())
       # ToxMain.shared().checkRepeatableObjectsAndExecuteThem()
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
        if ToxMain.shared().isTesting == True:
            return
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
            #newObj = obj.createDict()
            newObj = obj.generateDict(saving = True)
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

        self.realObjects = [] 
        self.repeatableObjects = []

        self.classes = [
            Timer.class_(),
            WeatherChecker.class_(),
            Lampada.class_(),
            InternetTemperature.class_(),
            RealTemperature.class_(),
            NumericalCondition.class_(),
            IRSensor.class_(),
            Buzzer.class_(),
            Porta.class_(),
            TimeCondition.class_(),
            Repeater.class_(),
            Tapparelle.class_(),
            Ventola.class_()
        ]
        self.isTesting = False
        #self.generateObjectsHandlers()
        
    def createRealObjects(self, fromArray):
        for objD in fromArray:
            realObj = self.createObectFromDict(objD)

    def createObectFromDict(self, dictObj):
        className = dictObj["className"]
        objClass = globals()[className]
        newObj = objClass(autoID = False)
        
        newObj.id = dictObj["id"]

        newObj.serializedHandlers = dictObj["handlers"]
        newObj.generateHandlers()

        if "actionObjectsIDs" in dictObj:
            objectsList = dictObj["actionObjectsIDs"]
            newObj.actionObjectsIDs = objectsList

        customSerializedVariables = dictObj["customVariables"]
        for key in customSerializedVariables.keys():
            serVar = customSerializedVariables[key]
            newObj.setValueForKey(serVar["value"], key)
            
            #newObj.customVariables[key] = ToxVariable(serVar["valueType"], serVar["value"])
            #if key in ("name", "description"):
            #    newObj.setValueForKey(serVar["value"], key)

        return newObj

    def createRepeatableObjectsList(self):
        for obj in self.realObjects:
            try:
                if obj.isRepeatableObject == True:
                    if obj not in self.repeatableObjects:
                        self.repeatableObjects.append(obj)
            except AttributeError:
                pass
        start_new_thread(self.performRepeatableQueue, ())

    def performRepeatableQueue(self):
        for obj in self.repeatableObjects:
            try:
                if obj.isRepeatableObjectReady:
                    obj.repeaterAction()
            except:
                pass

    def checkRepeatableObjectsAndExecuteThem(self):
        while True:
            self.createRepeatableObjectsList()
            time.sleep(0.1)


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
            if obj.get("pin") == pin:
                return obj  
            # if isinstance(obj, ConcreteObject) and obj.get("pin") == pin:
            #     return obj
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
            print(str(status))
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
                if obj in self.repeatableObjects:
                    self.repeatableObjects.remove(obj)
                break

        self.saveRealObjectsToDisk()

    def isObjectNameUnique(self, name):
        for obj in self.realObjects:
            if obj.name == name:
                return False
        return True

    def getRealActions(self):
        actions = list()
        for obj in self.realObjects:
            if isinstance(obj, ToxAction):
                actions.append(obj)
        return actions

    def keepActionsIntegrity(self):
        actions = self.getRealActions()
        if actions == None or len(actions) < 1:
            return
        for action in actions:
            actionObjectsIDs = action.actionObjectsIDs
            for objID in actionObjectsIDs:
                realObject = self.getRealObjectFromID(objID)
                if realObject == None:
                    action.removeObjIDfromMyList(objID)


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
        if (platform.system() == "Linux"):
            self.ser = serial.Serial("/dev/ttyACM0", 74880, timeout=3, write_timeout=3)
        else:
            self.ser = serial.Serial("/dev/cu.usbmodem14231", 74880, timeout=3, write_timeout=3)
        
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
    def create(type_, pin):
        id = random.randint(1, 999999)

        prefix = ""
        suffix = ""
        if type_ < 10:
            prefix = "0"
        prefix += str(type_)
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
    DALLAS_TEMPERATURE = 3
    DELETE = 4
    SERVO = 5
    MOTOR = 7

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
            #print(str(request))
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
                "response_message" : "Nessun request-body nella tua richiesta"
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
                        "response_message": "Il nome dell'oggetto non è unique"
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
                
                if "actionID" in requestBody and requestBody["actionID"] != None:
                    actionID = requestBody["actionID"]
                    realAction = ToxMain.shared().getRealObjectFromID(actionID)
                    if realAction == None:
                        self.send_err(conn, "Action non trovata con questo ID.")
                        return

                    result = realAction.addObjIDtoMyList(newObject.id)
                    if result != 0:
                        self.send_err(conn, "Errore mentre cercavo di aggiungere l'oggetto alla ToxAction.")
                        return

                ToxMain.shared().commitObjects()
                print("Nuovo oggetto creato con successo!")
                
                newDict = {
                    "code" : "OK",
                    "response_message" : "Oggetto creato con successo!"
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
                    "response_message" : "Manca l'id_object_owner"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            if "key" not in handler:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "key non trovata nella richiesta che mi hai mandato"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            if "function" not in handler:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Manca la function"
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
                    "response_message" : "Non ho trovato nessun oggetto con l'ID che mi hai dato"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            handlerFunction = handler["function"]

            if "objectId" not in handlerFunction:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "ObjectID della funzione non inviato"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            idObjectFunction = handlerFunction["objectId"]

            
            if "functionName" not in handlerFunction:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Non ho trovato nessuna functionName nella tua richiesta"
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
                "response_message" : "Handler aggiunto con successo"
            }
            conn.send(json.dumps(returnDict))


        elif requestType == "show_objects":
            arr = list()
            realobjs = ToxMain.shared().realObjects
            # print("realObjs.count = " + str(len(realobjs)))
            for obj in realobjs:
                if isinstance(obj, ToxAction):
                    continue
                objDict = obj.generateDict(saving = False)
                #objDict["handlers"] = {}
                keys = objDict["handlers"].keys()
                for key in keys:                    
                    objDict["handlers"][key] = list()
                arr.append(objDict)
            returnDict = {
                "code" : "OK",
                "response_objects" : arr
            }
            #print(str(arr))
            json_str = json.dumps(returnDict)
            conn.send(json_str)
            print("Oggetti fetchati con successo!")
        elif requestType == "remove_object":
            if "object_id" not in requestBody:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "non ho trovato 'object_id' nella tua richiesta"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            objectID = requestBody["object_id"]
            obj = ToxMain.shared().getRealObjectFromID(objectID)

            if obj == None:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Oggetto con quell'ID == NULL"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            obj.removeMe()
            returnDict = {
                "code" : "OK",
                "response_message" : "Oggetto rimosso con successo!"
            }
            conn.send(json.dumps(returnDict))
            print("Oggetto rimosso con successo!")
        elif requestType == "show_ids":
            ids = ToxIDCreator.shared().currentIDs
            conn.send(str(ids))
        elif requestType == "remove_handler":
            if "handlerID" not in requestBody:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Nella tua richiesta non hai inserito l'id dell'handler da rimuovere"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return

            if "obj_id" not in requestBody:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Nella tua richiesta non hai inserito l'id dell'oggetto"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            handlerIDToRemove = requestBody["handlerID"]
            objectIDOfHandler = requestBody["obj_id"]

            realObject = ToxMain.shared().getRealObjectFromID(objectIDOfHandler)
            if realObject == None:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Nessun oggetto con questo ID"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            
            if handlerIDToRemove not in ToxIDCreator.shared().usedHandlersIDs:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Nessun handler trovato con questo ID nella lista degli handler usati."
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            realObject.removeHandlerWithID(handlerIDToRemove)
            returnDict = {
                "code" : "OK",
                "response_message" : "Handler rimosso con successo"
            }
            conn.send(json.dumps(returnDict))
            print("Handler rimosso con successo!")
        elif requestType == "show_ids_h":
            ids = ToxIDCreator.shared().usedHandlersIDs
            conn.send(str(ids))
        elif requestType == "show_objects_classes":
            classes = ToxMain.shared().classes
            if classes == None:
                returnDict = {
                    "code" : "NO",
                    "response_message": "Nessuna classe"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            returnDict = {
                "code" : "OK",
                "response_objects": classes
            }
            conn.send(json.dumps(returnDict))
            print("Classi fetchate con successo!")
        elif requestType == "execute_message":
            objID = requestBody["objID"]
            messageName = requestBody["messageName"]
            realObject = ToxMain.shared().getRealObjectFromID(objID)
            if realObject == None:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Oggetto non trovato con questo ID"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            if realObject.executeMessage(messageName) != 0:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Funzione nel messaggio == NULL"
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            else:
                returnDict = {
                    "code" : "OK",
                    "response_message" : "Funzione eseguita con successo"
                }
                conn.send(json.dumps(returnDict))
                print("Messaggio eseguito con successo!")
        elif requestType == "change_properties":
            properties = requestBody["properties"]
            objID = requestBody["objID"]
            realObject = ToxMain.shared().getRealObjectFromID(objID)
            if realObject == None:
                returnDict = {
                    "code" : "NO",
                    "response_message" : "Oggetto non trovato con questo ID"
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
                    "response_message" : "Valore ritornato mentre cambiavo le properties: " + str(retCode)
                }
                conn.send(json.dumps(returnDict))
                conn.close()
                return
            returnDict = {
                "code" : "OK",
                "response_message" : "Properties modificate con successo!"
            }
            print("Server response: " + str(returnDict))
            conn.send(json.dumps(returnDict))
            print("Properties modificate con successo!")
        elif requestType == "get_handlers":
            if "obj_id" not in requestBody:
                self.send_err(conn, "Nella tua richiesta manca l'objID")
                return
            objID = requestBody["obj_id"]

            realObject = ToxMain.shared().getRealObjectFromID(objID)
            if realObject == None:
                self.send_err(conn, "Nessun oggetto con questo ID")
                return

            objectDict = realObject.generateDict()
            if objectDict == None:
                self.send_err(conn, "Errore mentre generavo il dict dell'oggetto.")
                return

            requiredDict = objectDict["handlers"]
            #print(str(requiredDict))

            returnDict = {
                "code" : "OK",
                "response_objects" : requiredDict
            }
            conn.send(json.dumps(returnDict))
            print("Handlers fetchati con successo!")
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
            print("Properties[2] modificate con successo")
        elif requestType == "show_actions":
            all_objects = ToxMain.shared().realObjects
            actions = list()
            for obj in all_objects:
                if isinstance(obj, ToxAction):
                    actions.append(obj.generateDict())
            returnDict = {
                "code" : "OK",
                "response_objects" : actions
            }
            conn.send(json.dumps(returnDict))
            print("Azioni fetchate con successo!")
        elif requestType == "remove_object_from_action":
            if "action_id" not in requestBody:
                self.send_err(conn, "Non ho trovato l'ID Action nella tua richiesta")
                return
            if "obj_id" not in requestBody:
                self.send_err(conn, "Non ho trovato l'ID dell'oggetto nella tua richiesta")
                return

            objID = requestBody["obj_id"]
            actionID = requestBody["action_id"]
            realAction = ToxMain.shared().getRealObjectFromID(actionID)
            if realAction == None:
                self.send_err(conn, "Non ho trovato nessuna azione con questo ID")
                return
            
            result = realAction.removeObjIDfromMyList(objID)

            if result != 0:
                self.send_err(conn, "Errore " + str(result) + " mentre eliminavo l'ID dalla liste dell'azione")
                return
            else:
                self.send_msg(conn, "Oggetto rimosso dall'azione correttamente")
                
        elif requestType == "show_objects_of_action":
            if "action_id" not in requestBody:
                self.send_err(conn, "Non c'è l'action_id nella tua richiesta")
                return
            actionID = requestBody["action_id"]
            realAction = ToxMain.shared().getRealObjectFromID(actionID)
            if realAction == None:
                self.send_err(conn, "Non ho trovato nessun'azione con questo ID")
                return
            
            idsList = realAction.actionObjectsIDs
            actionObjects = list()
            for idObject in idsList:
                realObject = ToxMain.shared().getRealObjectFromID(idObject)
                if realObject != None:
                    actionObjects.append(realObject.generateDict())
            
            returnDict = {
                "code" : "OK",
                "response_objects" : actionObjects
            }
            conn.send(json.dumps(returnDict))
            
        elif requestType == "add_existing_object_to_action":
            if "actionID" not in requestBody:
                self.send_err(conn, "Non ho trovato l'actionID nella tua richiesta")
                return
            if "obj_id" not in requestBody:
                self.send_err(conn, "Non ho trovato l'obj_id nella tua richiesta")
                return

            actionID = requestBody["actionID"]
            objID = requestBody["obj_id"]

            realAction = ToxMain.shared().getRealObjectFromID(actionID)
            if realAction == None:
                self.send_err(conn, "Non ho trovato nessuna azione con questo ID")
                return
            
            if objID in realAction.actionObjectsIDs:
                self.send_err(conn, "Oggetto già presente nella lista dell'azione")
                return
            else:
                realAction.actionObjectsIDs.append(objID)
                self.send_msg(conn, "Oggetto aggiunto all'azione correttamente")
        elif requestType == "add_some_existing_objects_to_action":
            if "actionID" not in requestBody:
                self.send_err(conn, "Non ho trovato l'actionID nella tua richiesta")
                return
            
            if "objects_ids" not in requestBody:
                self.send_err(conn, "Non mi hai dato la lista di oggetti da aggiungere")
                return

            actionID = requestBody["actionID"]
            objectsIDs = requestBody["objects_ids"]

            if type(objectsIDs) is not list:
                self.send_err(conn, "Bastardo! Hai provato a mandarmi un input corrotto come objects_ids per hackerarmi. Invece ti ho inculato bene")
                return

            realAction = ToxMain.shared().getRealObjectFromID(actionID)
            if realAction == None:
                self.send_err(conn, "Non ho trovato nessuna azione con questo ID")
                return

            for objID in objectsIDs:
                if objID not in realAction.actionObjectsIDs:
                    realAction.actionObjectsIDs.append(objID)

            ToxMain.shared().commitObjects()
            self.send_msg(conn, "Oggetti aggiunti all'azione correttamente")
        elif requestType == "show_live_objects":
            realObjects = ToxMain.shared().realObjects
            liveObjects = list()
            for obj in realObjects:
                try:
                    obj.live()
                    liveObjects.append(obj.generateDict())
                except:
                    pass
            
            returnDict = {
                "code" : "OK",
                "response_objects" : liveObjects
            }
            conn.send(json.dumps(returnDict))
        #conn.send("Scemotto! Hide and Seek\n")
        conn.close()

    def send_err(self, conn, msg):
        returnDict = {
            "code" : "NO",
            "response_message" : msg
        }
        conn.send(json.dumps(returnDict))
        conn.close()

    def send_msg(self, conn, msg):
        returnDict = {
            "code" : "OK",
            "response_message" : msg
        }
        conn.send(json.dumps(returnDict))

    def _wait_for_connections(self):
        while True:
            self.socket.listen(5)

            conn, addr = self.socket.accept()
            # print("Server <-- " + addr[0])

            start_new_thread(self._handle_request, (conn,))
