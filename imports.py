import classes
from Main import ToxMain
import ToxSerial
import ToxIDCreator
import ToxIDCreator


object1 = DigitalOutputDevice()

handler = ToxHandler()

function = ToxFunction()
function.objectId = 17
function.functionName = "asd"

handler.function = function
handler.args = None

object1.addHandlerForKey("activate", handler)
object1.executeMessage("activate")