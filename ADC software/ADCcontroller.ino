#include <Wire.h>

String inputString = "";
bool stringComplete = false;
String outputString = "";

const int adc_address[5] = {0x1D, 0x1E, 0x35, 0x2D, 0x2E};
const int adc_channel[8] = {0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27};
const int adc_limit_high[8] = {0x2A,0x2C,0x2E,0x30,0x32,0x34,0x36,0x38};
const int adc_limit_low[8] = {0x2B,0x2D,0x2F,0x31,0x33,0x35,0x37,0x39};

const int adc_config = B00000001; // Turn on ADC
const int adv_adc_config = B00000011; // Mode select 1 (8 channels), external VRef
const int conv_rate = B00000001; // Continuous conversion mode

signed int adc_data[40];
// 8*n + i | n - 0:4 | i - 0:7 

long int count = 0;

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
    String temp[2] = {"b1\n", "dreq\n"};
    if(outputString == temp[0]) {
      char ser_output[4] = {'b','1','c','\n'};
      Serial.write(ser_output);
    }
    else if(outputString == temp[1]) {
      String temp_output;
      char ser_output_2[5] = {'b','e','g','d','\n'};
      Serial.write(ser_output_2);
      for (int i = 0; i < 40; i++){
        temp_output = String(adc_data[i]);
        switch(temp_output.length()){
          case 4:
            ser_output_2[0] = temp_output[0];
            ser_output_2[1] = temp_output[1];
            ser_output_2[2] = temp_output[2];
            ser_output_2[3] = temp_output[3];
            ser_output_2[4] = '\n';
            break;
          case 3:
            ser_output_2[0] = '0';
            ser_output_2[1] = temp_output[0];
            ser_output_2[2] = temp_output[1];
            ser_output_2[3] = temp_output[2];
            ser_output_2[4] = '\n';
            break;
          case 2:
            ser_output_2[0] = '0';
            ser_output_2[1] = '0';
            ser_output_2[2] = temp_output[0];
            ser_output_2[3] = temp_output[1];
            ser_output_2[4] = '\n';
            break;
          case 1:
            ser_output_2[0] = '0';
            ser_output_2[1] = '0';
            ser_output_2[2] = '0';
            ser_output_2[3] = temp_output[0];
            ser_output_2[4] = '\n';
            break;
          default:
            ser_output_2[0] = 'e';
            ser_output_2[1] = 'r';
            ser_output_2[2] = 'r';
            ser_output_2[3] = '2';
            ser_output_2[4] = '\n';
            break;
        }
        Serial.write(ser_output_2);
      }
      ser_output_2[0] = 'e';
      ser_output_2[1] = 'n';
      ser_output_2[2] = 'd';
      ser_output_2[3] = 'd';
      ser_output_2[4] = '\n';
      Serial.write(ser_output_2);
    }
    inputString = "";
    stringComplete = false;
  }
  if(count == 500000) {
    ADC_getdata();
    count = 0;
  }
  count++;
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
     int highByte_read = Wire.read();
     int lowByte_read = Wire.read() & 240;
     adc_data[8*i+j] = (highByte_read << 4) | (lowByte_read >> 4);
     //Serial.print(18000/(3.3/(3.3*adc_data[8*i+j]/4095)-1));
     //Serial.write('\n');
    }
  }
}
