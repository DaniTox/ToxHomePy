#include "functions.h"

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < 8; i++) {
    pinMode(i, INPUT);
    setPinAsReadOnly(i);
  }
  for (int i = 8; i < 14; i++) {
    pinMode(i, OUTPUT);
  }

}

void loop() {  
  if (Serial.available()) {
    handleInput();
  }
}


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
  
  int opbit = getobit(number);
  if (opbit < 0) {
    Serial.println("opbit < 0");
    return;
  }

  int pin = getpin(number);
  if (pin < 0) {
    Serial.println(ERRIN);
    return;
  }


  switch (opbit) {
    case 0:
      {
        int rpin = rand() % PINS_N;
        digitalWrite(rpin, HIGH);
      }
      break;
    case 1:
      if (!isReadOnly(pin)) {
        digitalWrite(pin, HIGH);  
      } else {
        Serial.print("Read-Only pin. Non procedo... ");
      }
      Serial.print("OK: ");
      Serial.println(number);
      break;
    case 2:
      if (!isReadOnly(pin)) {
        digitalWrite(pin, LOW);
      } else {
        Serial.print("Read-Only pin. Non procedo...");
      }
      Serial.print("OK: ");
      Serial.println(number);
      break;
    case 9:
      //int* arr = getps();    <-- Memory management is hard :(
      //sendsts(arr);          <-- Memory management is hard :(
      sendsts();
      //serialFlush();
      break;
  }
  
}

int getobit(int num) {
  return num / 1000;
}

int getpin(int num) {
  return num % 100;
}

int *getps() {
   int *p = (int *)malloc(sizeof(int) * PINS_N);
   for (int i = 0; i < PINS_N; i++) {
      if (i == 0 || i == 1) {
        p[i] = 0;
        continue;
      }
      p[i] = digitalRead(i);
   }
   return p;
}

void sendsts() {
  int* arr = getps();
  //delay(100);
  if (arr == NULL) { return; }
  Serial.print("{ \"pins_d\" : [ ");
  for (int i = 0; i < PINS_N; i++) {
    Serial.print(arr[i]);
    if (i != (PINS_N - 1)) {
      Serial.print(", ");
    }
  }
  Serial.print(" ], \"pins_a\" : [");
  for (int i = 0; i < 5; i++) {
    Serial.print(analogRead(analog_pins[i]));
    if (i != 4) {
      Serial.print(", ");
    }
  }
  Serial.print(" ] }\n");
  free(arr);
}

void setPinAsReadOnly(int pin) {
  readOnlyPins[pinsIndex] = pin;
  pinsIndex++;
}

bool isReadOnly(int pin) {
  for (int i = 0; i < 7; i++) {
    if (readOnlyPins[i] == pin) {
      return true;
    }
  }
  return false;
}

void serialFlush(){
  while(Serial.available() > 0) {
    char t = Serial.read();
  }
}
