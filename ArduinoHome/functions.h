void handleInput();
void handleNumber(int);

int getobit(int);
int getpin(int);

const char startOfNumberDelimiter = '<';
const char endOfNumberDelimiter   = '>';

const char* ERRIN = "{ \"error\" : \"Struttura messaggio non valida\" }";

void handleInput() {
    static long receivedNumber = 0;
    byte c = Serial.read();

    switch (c) {
      case endOfNumberDelimiter:
        handleNumber(receivedNumber);
        break;
      case startOfNumberDelimiter:
        receivedNumber = 0;
        break;

      case '0' ... '9':
        receivedNumber *= 10;
        receivedNumber += c - '0';
        break;
    }
}

void handleNumber(int number) {
  if (number < 10000) {
    Serial.println(ERRIN);
    return;
  }
  
  int opbit = getobit(number);
  if (opbit <= 0) {
    Serial.println(ERRIN);
    return;
  } else {
    Serial.print("Numero Funzione: ");
    Serial.println(opbit);
  }

  int pin = getpin(number);
  if (pin <= 0) {
    Serial.println(ERRIN);
    return;
  } else {
    Serial.print("Numero Pin: ");
    Serial.println(pin);
  }
  
  
}

int getobit(int num) {
  return num / 1000;
}

int getpin(int num) {
  return num % 100;;
}

