import json
import os
import random

class ToxIDCreator:
    def __init__(self):
        self.FILE_NAME = ".currentIDs.json"
        self.currentIDs = self.getIDsFromStorage()

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
        id = 0
        while id in self.currentIDs and id == 0:
            id = random.randint(0, 9999)
        return id

    def isIDUnique(self, id):
        if id in self.currentIDs:
            return False
        else:
            return True
    