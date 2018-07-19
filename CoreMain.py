from CoreSoftware import *

serialObj = ToxSerial.shared()
serialObj.start()

while True:
    
    updateObj = ToxSerialUpdate()

    msg = ToxMessage(updateObj.updateObjs)
    msg.id = 1
    serialObj.addToQueue(msg)

    serialObj.printQueueLen()
    time.sleep(0.15)