import classes
import ToxConverter

class ToxMain:
    def __init__(self):
        toxSaver = ToxConverter()
        self.objects = toxSaver.getObjectsFromJSON()

    def getObjectFromID(self, id):
        for obj in self.objects:
            if obj.id == id:
                return obj
        return None