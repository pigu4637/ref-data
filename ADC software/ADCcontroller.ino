#include <Wire.h>

String inputString = "";
bool stringComplete = false;
String outputString = "";


void setup() {
  Wire.begin();
  Serial.begin(9600, SERIAL_8N1);
}

void loop() {
  if (stringComplete) {
    outputString = inputString;
    String temp = "b1\n";
    if(outputString == temp) {
      char ser_output[4] = {'b','1','c','\n'};
      Serial.write(ser_output);
    }
    inputString = "";
    stringComplete = false;
  }
}

void serialEvent() {
  while(Serial.available()){
    char inputByte = (char)Serial.read();
    inputString += inputByte;
    if(inputByte == '\n') {
      stringComplete = true;
    }
  }
}
