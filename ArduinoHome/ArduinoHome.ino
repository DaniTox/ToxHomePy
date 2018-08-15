#include "functions.h"

void setup() {
  Serial.begin(9600);
}

void loop() {  
  if (Serial.available()) {
    handleInput();
  }
  //while(Serial.available())
    //Serial.read();
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
      digitalWrite(pin, HIGH);
      break;
    case 2:
      digitalWrite(pin, LOW);
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


void serialFlush(){
  while(Serial.available() > 0) {
    char t = Serial.read();
  }
}
