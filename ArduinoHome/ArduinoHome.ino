#include <Stepper.h>
#include "functions.h"
#include <OneWire.h>
#include <Servo.h>

ToxObject* objects[69];


const int stepsPerRevolution = 512;
const int MAXSTEPS = 2000;
Stepper stepper(stepsPerRevolution,8,10,9,11);

int motorMode = -1;
int stepsDone = 0;

void setup() {
  stepper.setSpeed(60);
  Serial.begin(57600);
  
  for (int i = 0; i < 42; i++) {
    pinMode(i, OUTPUT);
  }
  for (int i = 42; i < 54; i++) {
    pinMode(i, INPUT);
    setPinAsReadOnly(i);
  }
}

void loop() {  
  if (Serial.available()) {
    handleInput();
  }

 if(stepsDone < MAXSTEPS) {
  if (motorMode == 0) {
    stepper.step(1);
  } else if (motorMode == 1) {
    stepper.step(-1);
  }
  stepsDone++;
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
        int rpin = rand() % n_PINSD;
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
      int total_pins = (n_PINSD + n_PINSA);
      for (int i = 0; i < (total_pins - 1); i++) {
        ToxObject *obj = objects[i];
        if (obj == NULL) {
          Serial.print("NULL");
        } else {
          //p(obj->className);
          Serial.print(obj->className);  
        }
        
        if (i != (total_pins - 2)) {
          Serial.print(", ");
        }
        //delay(10);
      }
      Serial.println("");
      
    }
    break;
    case 7:
    {
      freeObjectPin(pin);
      createCustomObject(pin, "MotorControl");
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

    //Serial.print("Ecco la classe al pin: ");
    //Serial.print(pin);
    
   // p(objects[pin]->className);
    
    //Serial.print("Sto creando una classe: ");
    //Serial.print(className);
    if (object->className.equals("Servo")) {
      Servo servo;
      servo.attach(pin);

      servo.write(0);
      delay(15);

      servo.detach();
    }
}

void freeObjectPin(int pin) {
  ToxObject *old = objects[pin];
  objects[pin] = NULL;
  free(old);
}

int getobit(int num) {
  return num / 1000;
}

int getpin(int num) {
  return num % 100;
}

int *getps() {
   int *p = (int *)malloc(sizeof(int) * (n_PINSD + (n_PINSA - 1)));

   //DIGITAL PINS
   for (int i = 0; i < n_PINSD; i++) {
      if (i == 0 || i == 1 || i == 14 || i == 15 || i == 16 || i == 17 || i == 18 || i == 19 || i == 20 || i == 21) {
        p[i] = 0;
        continue;
      }

      if (objects[i] == NULL) {
        p[i] = digitalRead(i);
      } else {
        ToxObject *object = objects[i];
        
        if (object->className.equals("DallasTemperature")) {
          p[i] = (int)dallas(i,0);
        } 

       
      }
   }
   //FINE DIGITAL PINS


  //ANALOG PINS
  for (int i = 0; i < n_PINSA; i ++) {
    int index = n_PINSD + i;
    uint8_t analogPin = getAnalogPin(i);
    
    if (objects[index] == NULL) {
      p[index] = analogRead(analogPin);
    } else {
      ToxObject *object = objects[index];
      
      if (object->className.equals("DallasTemperature")) {
        uint8_t analogPin = getAnalogPin(i);
        p[index] = (int)dallas(analogPin,0); 
      } 
     
      
    }
  }
  //FINE ANALOG PINS


  
   return p;
}

void sendsts() {
  int* arr = getps();

  if (arr == NULL) { return; }
  Serial.print("{ \"pins_d\" : [ ");
  for (int i = 0; i < n_PINSD; i++) {
    Serial.print(arr[i]);
    if (i != (n_PINSD - 1)) {
      Serial.print(", ");
    }
  }
  Serial.print(" ], \"pins_a\" : [");
  int total_pins = n_PINSD + n_PINSA;
  for (int i = n_PINSD; i < (total_pins - 1); i++) {
    Serial.print(arr[i]);
    if (i != (total_pins - 2)) {
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
  for (int i = 0; i < 10; i++) {
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
        //Serial.print("Sto per accendere la classe: ");
        //Serial.println(object->className);
        if (object == NULL) {
          digitalWrite(pin, HIGH);   
        } else {
          //p(object->className);
          if (object->className.equals("Servo")) {
           
            Servo servo;
            servo.attach(pin);
            float pos;
            
            for (pos = 0; pos < 180; pos+=2.5) {
              servo.write(pos);
              delay(10);
            }

            servo.detach();
          }
          
          else if (object->className.equals("MotorControl")) {
            motorMode = 1;
            stepsDone = 0;
            //Serial.println("Alzo le veneziane");
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
          if (object->className.equals("Servo")) {
            Servo servo;
            servo.attach(pin);
            
            float pos;
            
            for (pos = 180; pos > 1; pos-=2.5) {
              servo.write(pos);
              delay(10);
            }

            servo.detach();
          }
          else if (object->className.equals("MotorControl")) {
            //Serial.println("Chiudo le veneziane");
            motorMode = 0;
            stepsDone = 0;
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

uint8_t getAnalogPin(int pin) {
  if (pin == 0) {
    return A0;
  } else if (pin == 1) {
    return A1;
  } else if (pin == 2) {
    return A2;
  } else if (pin == 3) {
    return A3;
  } else if (pin == 4) {
    return A4;
  } else if (pin == 5) {
    return A5;
  } else if (pin == 6) {
    return A6;
  } else if (pin == 7) {
    return A7;
  } else if (pin == 8) {
    return A8;
  } else if (pin == 9) {
    return A9;
  } else if (pin == 10) {
    return A10;
  } else if (pin == 11) {
    return A11;
  } else if (pin == 12) {
    return A12;
  } else if (pin == 13) {
    return A13;
  } else if (pin == 14) {
    return A14;
  } else if (pin == 15) {
    return A15;
  }
}




