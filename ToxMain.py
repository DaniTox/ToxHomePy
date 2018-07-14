import classes
import ToxConverter

while True:
    name = input("Name: ")
    desc = input("Description: ")
    pin = raw_input("Pin: ")

    obj = Luce()
    obj.name = name
    obj.description = desc
    obj.pins = pin

    tox = ToxConverter()
    tox.saveToFile(obj.createDict(),JSON_SAVER_FILENAME)