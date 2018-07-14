import ToxConverter
import ToxSerial

class MainLogic:
    def __init__(self):
        conv = ToxConverter()
        self.objects = conv.getObjectsFromJSON()

    def startLogic(self):
        while True:
            for obj in self.objects:
                