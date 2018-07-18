import classes
import ToxConverter

class ToxMain:
    def __init__(self):
        toxSaver = ToxConverter.ToxConverter()
        self.objects = toxSaver.getObjectsFromJSON()
        self.realObjects = [] 

        #TODO: creare gli oggetti da questo dizionario
        for objD in self.objects:
            realObj = self.createObectFromDict(objD)
            self.realObjects.append(realObj)

    def createObectFromDict(self, dictObj):
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
        return newObj
        #return the obj


    def getObjectFromID(self, id):
        for obj in self.objects:
            if obj.id == id:
                return obj
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


main = ToxMain()