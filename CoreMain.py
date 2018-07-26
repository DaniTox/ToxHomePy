from CoreSoftware import *




##  TESTING TOXSERIAL

####    SECTION 0   ####
# serialObj = ToxSerial.shared()
# serialObj.start()

# while True:
    
#     updateObj = ToxSerialUpdate()

#     msg = ToxMessage(updateObj.updateObjs)
#     msg.id = 1
#     serialObj.addToQueue(msg)

#     serialObj.printQueueLen()
#     time.sleep(0.15)


####    SECTION 0.1     #####
# converter = ToxConverter()
# print(converter.getObjectsFromJSON())



####    SECTION 1   #####
# object1 = DigitalOutputDevice()

# handler = ToxHandler()

# function = ToxFunction()
# function.objectId = 17
# function.functionName = "asd"

# handler.function = function
# handler.args = None

# object1.addHandlerForKey("activate", handler)
# object1.executeMessage("activate")


####    SECTION 2   #####

# timer = Timer()
# timer.duration = 2

# completion = ToxHandler()

# function = ToxFunction()
# function.functionName = "asd"
# function.objectId = 17

# completion.function = function
# timer.addHandlerForKey("activate", completion)


# obj1 = DigitalOutputDevice()
# completion2 = ToxHandler()

# func2 = ToxFunction()
# func2.objectId = timer.id
# func2.functionName = "startTimer"
# completion2.function = func2
# completion2.args = None

# obj1.addHandlerForKey("activate", completion2)

# obj1.executeMessage("activate")

# asd = ToxIDCreator.shared()
# print(asd.currentIDs)
#####################



####    SECTION 3   ####
#       HTTP SERVER     #

# server = HTTPServer(('', 8080), ToxServer)
# server.allow_reuse_address = True
# server.serve_forever()




##  SECTION 4   ####
##  SOCKET SERVER   ##

# server = ToxSocketServer()
# try:
#     server.activate_server()
# except KeyboardInterrupt:
#     print("\nRicevuto segnale di chiusura. Esco...")



##   SECTION 5  ###
#      BOOT      #
ToxBoot().boot()
