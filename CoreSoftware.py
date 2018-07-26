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
sys.dont_write_bytecode = True

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
        if len(objects) > 0:
            for obj in objects:
                self.currentIDs.append(obj["id"])

        # self.FILE_NAME = ".currentIDs.json"
        # self.currentIDs = self.getIDsFromStorage()

    def setIDasUsed(self, id):
        print(traceback.format_exc())
        if id not in self.currentIDs:
            self.currentIDs.append(id)
    
    def setIDasFree(self, id):
        try:
            self.currentIDs.remove(id)
        except:
            raise Exception("Non ho potuto settare l'id come free")
            sys.exit(1)

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

        self.customVariables = {}

        self.messages = {}
        self.handlers = {}

        idCreator = ToxIDCreator.shared()
        self.id = idCreator.createUniqueID()
        if self.id == None or self.id == 0:
            raise Exception("Creato ID NULL o 0(zero) nell'init di un oggetto")
        self.pin = None 

        ToxMain.shared().addRealObject(self)

    def generateHandlers(self):
        allHandlers = self.handlers
        keys = list(allHandlers.keys())
        if len(keys) <= 0:
            return
        for key in keys:
            if type(allHandlers[key]) == dict:
                for hand in allHandlers[key]:
                    handler = ToxHandler.createFromDict(hand)
                    self.handlers[key].append(handler)
                    self.handlers[key].remove(hand)
                
        print(self.handlers)


    def createDict(self): 
        myDict = {}
        variables = self.__dict__.keys()
        for var in variables:
            if var == "messages": #or var == "handlers"
                continue
            if var == "handlers" and len(self.__dict__["handlers"]) > 0:
                print("I'M IN")
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


    def addHandlerForKey(self, key, handler):
        self.handlers[key].append(handler)

    def executeMessage(self, message):
        func = self.messages[message]
        if func != None:
            func()

    def removeAllHandlers(self):
        for key in self.handlers:
            del self.handlers[key][:]

    def removeHandlersForKey(self, key):
        del self.handlers[key][:]

    def removeMe(self):
        ToxMain.shared().removeRealObjectForID(self.id)



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
        self.id = None
        #TODO: create an unique ID

    @staticmethod
    def createFromDict(dictObj):
        if "function" not in dictObj:
            raise Exception("Non ho trovato la chiave 'function' nel dict handler")
        realFunc = ToxFunction()
        realFunc.objectId = dictObj["function"]["objectId"]
        realFunc.functionName = dictObj["function"]["functionName"]

        realHandler = ToxHandler()
        realHandler.function = realFunc
        if "id" not in dictObj["id"]:
            raise Exception("Non ho trovato l'ID handler")
        realHandler.id = dictObj["id"]
        if "args" in dictObj:
            realHandler.args = dictObj["args"]
        return realHandler


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
        #self.generateObjectsHandlers()
        

        

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
        if "messages" in dictObj:
            newObj.messages = dictObj["messages"]
        newObj.handlers = dictObj["handlers"]
        newObj.generateHandlers()
        #print(newObj.createJSON())
        
        #TESTING ONLY. DA ELIMINARE
        # func = getattr(newObj, "printStr")
        # func()
        #####

        return newObj
        #return the obj

    def addRealObject(self, obj):
        self.realObjects.append(obj)
        ToxIDCreator.shared().setIDasUsed(obj.id)
        #self.saveRealObjectsToDisk()

    def commitObjects(self):
        self.saveRealObjectsToDisk()

    def saveRealObjectsToDisk(self):
        ToxConverter().saveObjectsToJSON(self.realObjects)

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

    def removeRealObjectForID(self, id):
        for index, obj in enumerate(self.realObjects):
            if obj.id == id:
                del self.realObjects[index]
                ToxIDCreator.shared().setIDasFree(id)
                break

        self.saveRealObjectsToDisk()





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



class ToxSocketServer:
    def __init__(self, port = 8080):
        self.host = ''
        self.port = port

    def activate_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
        data = conn.recv(4096)
        
        request = json.loads(data)
        #print(str(data))
        requestType = request["request-type"]

        if requestType == "create_new_object":
            if "name" in request and "description" in request and "className" in request:
                objClass = globals()[request["className"]]
                newObject = objClass()
                newObject.name = request["name"]
                newObject.description = request["description"]
                if "pin" in request:
                    newObject.pin = request["pin"]
                if "variables" in request:
                    newObject.customVariables = request["variables"]
                ToxMain.shared().commitObjects()
                print("Nuovo oggetto creato con successo!")
                odic = newObject.createDict()
                odic["code"] = "OK"
                #print(str(odic))
                ojson = str(json.dumps(odic))
                #print(ojson)
                conn.send(ojson)
                # for obj in ToxMain.shared().realObjects:
                #     print(obj.createDict())
            else:
                print("Errore nella creazione oggetto. Qualche valore mancante")
                conn.send("Errore nella creazione oggetto. Qualche valore mancante") 
            
        
        elif requestType == "modify_handler_actions":
            all_handlers = request["handlers"]
            handlers_key = request["handlers-obj-key"]
            obj_id_of_object_receiver = request["objID-receiver"]
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
        elif requestType == "show_objects":
            arr = list()
            realobjs = ToxMain.shared().realObjects
            for obj in realobjs:
                arr.append(obj.createDict())
            json_str = json.dumps(arr)
            conn.send(json_str)
        elif requestType == "remove_object":
            objectID = request["object_id"]
            obj = ToxMain.shared().getRealObjectFromID(objectID)
            if obj != None:
                obj.removeMe()
                conn.send("Oggetto rimosso con successo")
            else:
                conn.send("Non esiste nessun oggetto con quell'ID")
        elif requestType == "show_ids":
            ids = ToxIDCreator.shared().currentIDs
            conn.send(str(ids))
        elif requestType == "remove_handler":
            handlerIDToRemove = request["handlerID"]
            objectIDOfHandler = request["obj_id"]
            #TODO: call the toxHandlerOrganizer and tell him to remove the handler

        #conn.send("Scemotto! Hide and Seek\n")
        conn.close()


    def _wait_for_connections(self):
        while True:
            self.socket.listen(5)

            conn, addr = self.socket.accept()
            print("Server <-- " + addr[0])

            start_new_thread(self._handle_request, (conn,))
