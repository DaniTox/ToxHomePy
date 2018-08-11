#include "functions.h"

void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    handleInput();
  }
}



