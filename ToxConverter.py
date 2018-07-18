# coding=utf-8

import json
import os

JSON_SAVER_FILENAME = "apparecchiature.json"

class JSONSaver:
    def saveToFile(self, data, fileName):
        os.remove(fileName)
        with open(fileName, "w") as outfile:
            json.dump(data, outfile)

    def getFromFile(self, fileName):
        with open(fileName) as f:
            data = json.load(f)
        return data


# class ToxConverter(JSONSaver):

    # def getObjectsFromJSON(self):
    #     j = self.getFromFile(JSON_SAVER_FILENAME)
    #     return j["Objects"]

    # def saveToFile(self, data, fileName):
    #     if isinstance(data, Object):
    #         newData = data.createDict()
    #     JSONSaver.saveToFile(self, newData, fileName)

jsonSaver = JSONSaver()

def getObjectsFromJSON():
    j = jsonSaver.getFromFile(JSON_SAVER_FILENAME)
    return j["Objects"]

def saveToFile(data, fileName):
        if isinstance(data, Object):
            newData = data.createDict()
        jsonSaver.saveToFile(newData, fileName)