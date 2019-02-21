#include <Wire.h>

String inputString = "";
bool stringComplete = false;
String outputString = "";

const int adc_address[5] = {0x1D, 0x1E, 0x35, 0x2D, 0x2E};
const int adc_channel[8] = {0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27};
const int adc_limit_high[8] = {0x2A,0x2C,0x2E,0x30,0x32,0x34,0x36,0x38};
const int adc_limit_low[8] = {0x2B,0x2D,0x2F,0x31,0x33,0x35,0x37,0x39};

const int adc_config = B00001001; // Turn on ADC, clear interrupt
const int adv_adc_config = B00000011; // Mode select 1 (8 channels), external VRef
const int conv_rate = B00000001; // Continuous conversion mode

unsigned int adc_data[40];
// 8*n + i | n - 0:4 | i - 0:7 

void setup() {
  Wire.begin();
  Serial.begin(9600, SERIAL_8N1);
  int busy_reg = 1;
  while (busy_reg == 1) {
    delay(33);
    busy_reg = 0;
    for (int i = 0; i < 5; i++) {
      Wire.beginTransmission(adc_address[i]);
      Wire.write(0x0C);
      Wire.requestFrom(adc_address[i],1);
      int temp = Wire.read();
      if (temp & B00000010) {
        busy_reg = 1;
      }
      Wire.endTransmission();
    }
  }
  for (int i = 0; i < 5; i++) {
    Wire.beginTransmission(adc_address[i]);
    Wire.write(0x0B);
    Wire.write(adv_adc_config);
    Wire.endTransmission();
    Wire.beginTransmission(adc_address[i]);
    Wire.write(0x07);
    Wire.write(conv_rate);
    Wire.endTransmission();
    for(int j = 0; j < 8; j++) {
      Wire.beginTransmission(adc_address[i]);
      Wire.write(adc_limit_high[j]);
      Wire.write(0xFA);
      Wire.endTransmission();
      
      Wire.beginTransmission(adc_address[i]);
      Wire.write(adc_limit_low[j]);
      Wire.write(0xB0);
      Wire.endTransmission();
    }
    
    Wire.beginTransmission(adc_address[i]);
    Wire.write(0x00);
    Wire.write(adc_config);
    Wire.endTransmission();
  }
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
  ADC_getdata();
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

void ADC_getdata() {
  for (int i = 0; i < 5; i++) {
    for(int j = 0; j < 8; j++) {
     Wire.beginTransmission(adc_address[i]);
     Wire.write(adc_channel[j]);
     Wire.endTransmission();
     Wire.requestFrom(adc_address[i],2);
     int highByte_read = Wire.read() & 15;
     int lowByte_read = Wire.read();
     adc_data[8*i+j] = (highByte_read << 8) | lowByte_read;
     Serial.print(adc_data[8*i+j]);
     Serial.write('\n');
    }
    delay(1000);
  }
}
