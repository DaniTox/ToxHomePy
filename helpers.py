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


class ToxConverter(JSONSaver):

    def getObjectsFromJson(self):
        j = self.getFromFile(JSON_SAVER_FILENAME)
        return j["Objects"]


