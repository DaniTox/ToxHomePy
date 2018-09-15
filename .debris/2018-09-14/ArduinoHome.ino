#include "functions.h"
#include <OneWire.h>
#include <Servo.h>

ToxObject* objects[14];

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
      writeHighPin(pin);
      printNumberReceived(number);
      break;
    case 2:
      writeLowPin(pin);
      printNumberReceived(number);
      break;
    case 3:
    {
      freeObjectPin(pin);
      createCustomObject(pin, "DallasTemperature");
    }
    break;
    case 4:
    {
      freeObjectPin(pin);
      createCustomObject(pin, "ProvaClassName");
    }
    break;
    case 5:
    {
      freeObjectPin(pin);
      createCustomObject(pin, "Servo");
    }
    break;
    case 6:
    {
      for (int i = 0; i < 14; i++) {
        ToxObject *obj = objects[i];
        int z = (unsigned int)obj;
        Serial.print("0x"); Serial.print(z, HEX); Serial.print(" - ");
        Serial.println(obj->className);
      }
    }
    break; 
    case 9:  
      sendsts();
      break;
  }
  
}

void createCustomObject(int pin, char *className) {
    ToxObject *object = (ToxObject *)malloc(sizeof(ToxObject));
    object->className = className;
    objects[pin] = object;
}

void freeObjectPin(int pin) {
  ToxObject *old = objects[pin];
  free(old);
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
      if (objects[i] == NULL) {
        p[i] = digitalRead(i);
      } else {
        ToxObject *object = objects[i];
        if (strcmp(object->className, "DallasTemperature ")) {
          p[i] = (int)dallas(i,0);
        } 
      }
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

int16_t dallas(int x, byte start) {
  OneWire ds(x);
  byte i;
  byte data[2];
  int16_t result;

  do {
    ds.reset();
    ds.write(0xCC);
    ds.write(0xBE);
    for (i = 0; i < 2; i++) data[i] = ds.read();
    result = (data[1]<<8) |data[0];
    result>>=4; if (data[1]&128) result|=61440;
    if (data[0]&8) ++result;
    ds.reset();
    ds.write(0xCC);
    ds.write(0x44, 1);
    if (start) delay(1000);
    
  } while (start--);

  
  return result;
}

void writeHighPin(int pin) {
  if (!isReadOnly(pin)) {
        ToxObject *object = objects[pin];
        if (object == NULL) {
          digitalWrite(pin, HIGH);   
        } else {
          if (strcmp(object->className, "Servo ")) {
            Servo servo;
            servo.attach(pin);
            int pos;
            for (pos = 0; pos < 180; pos++) {
              servo.write(pos);
            }
            servo.detach();
          }
        }
        
      } else {
        Serial.print("Read-Only pin. Non procedo... ");
      }
}

void writeLowPin(int pin) {
  if (!isReadOnly(pin)) {
        ToxObject *object = objects[pin];
        if (object == NULL) {
          digitalWrite(pin, LOW);
        } else {
          if (strcmp(object->className, "Servo ")) {
            Servo servo;
            servo.attach(pin);
            int pos;
            for (pos = 180; pos > 1; pos--) {
              servo.write(pos);
            }
            servo.detach();
          }
        }
        
      } else {
        Serial.print("Read-Only pin. Non procedo...");
      }
}

void printNumberReceived(int number) {
  Serial.print("OK: ");
  Serial.println(number);
}






