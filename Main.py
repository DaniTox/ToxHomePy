import classes
import ToxConverter

class ToxMain:

    __instance = None

    @staticmethod
    def shared():
        if ToxMain.__instance == None:
            ToxMain()
        return ToxMain.__instance

    def __init__(self):
        # toxSaver = ToxConverter()
        self.objects = ToxConverter.getObjectsFromJSON()
        self.realObjects = [] 

        #TODO: creare gli oggetti da questo dizionario
        for objD in self.objects:
            realObj = self.createObectFromDict(objD)
            self.realObjects.append(realObj)

        if ToxMain.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ToxMain.__instance = self

    def createObectFromDict(self, dictObj):
        # import classes
        className = dictObj["className"]
        objClass = getattr(classes, className)
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

    def updateObjetctsStatus(self, status):
        for index, value in enumerate(status):
            obj = self.getObjectFromPin(index,self.objects)
            if obj != None:
                obj.update(value)


#main = ToxMain()

