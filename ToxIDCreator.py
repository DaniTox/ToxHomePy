import json
import os
import random

class ToxIDCreator:
    def __init__:
        self.currentIDs = self.getIDsFromStorage()
        self.FILE_NAME = ".currentIDs.json"

    def getIDsFromStorage(self):
        if os.path.isFile(self.FILE_NAME):
            with open(self.FILE_NAME) as f:
                data = json.load(f)
            if data != None:
                return data
        else:
            return {}

    def createUniqueID(self):
        id = 0
        while id in self.currentIDs and id == 0:
            id = random.randint(0, 9999)
        return id

    def isIDUnique(self, id):
        if id in self.currentIDs:
            return False
        else:
            return True
    