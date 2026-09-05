#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <ArduinoJson.h>
#include "TCS34725.h"
#include "TB6612FNG_XCR.h"

#define MEASURE_DELAY 25

// PIN DEFINITIONS
const int pin_relay_aerator = 3; 
const int pin_relay_led = 2;
const int pin_echo = 9;
const int pin_trig = 10;
const int pin_mtr_pwma = 5;
const int pin_mtr_ai2 = 6;
const int pin_mtr_ai1 = 3;
const int pin_mtr_stby = 4;

// OBJECTS
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
TCS34725 tcs;
TB6612FNG_XCR conveyor_mtr;

void setup() {
  Serial.begin(115200);
  Serial.println("Controller Initializing");

  pinMode(pin_relay_aerator, OUTPUT);
  pinMode(pin_relay_led, OUTPUT);
  pinMode(pin_mtr_pwma, OUTPUT);
  pinMode(pin_mtr_ai1, OUTPUT);
  pinMode(pin_mtr_ai2, OUTPUT);
  pinMode(pin_mtr_stby, OUTPUT);
  pinMode(pin_trig, OUTPUT);
  pinMode(pin_echo, INPUT);

  tcs.integrationTime(33); // ms
  tcs.gain(TCS34725::Gain::X01);

  conveyor_mtr.attach(pin_mtr_pwma, pin_mtr_ai1, pin_mtr_ai2, "Conveyor");
  conveyor_mtr.setStandbyPin(pin_mtr_stby);

  digitalWrite(pin_relay_aerator, LOW);
  digitalWrite(pin_relay_led, LOW);
  digitalWrite(pin_trig, LOW);

  Serial.println("Controller Initialization Done!");
  delayMicroseconds(500);
}

void loop() {
  float wtrTemp;
  int wtrLvl = measureDistance();
  float luxIntensity;
  float lightTemp;

  StaticJsonDocument<200> doc;

  if (Serial.available() > 0) {
    // READ RECEIVED STRINGS VIA SERIAL
    String rpi_cmd = Serial.readStringUntil('\n');
    DeserializationError error = deserializeJson(doc, rpi_cmd);

    if (!error) {
      // PARSE COMMANDS FROM RASPBERRY PI
      String command = doc["command"];
      if (command == "aerator_on") {
        digitalWrite(pin_relay_aerator, HIGH);
        conveyor_mtr.manual(1, 0, 255, 10000);
      } else if (command == "aerator_off") {
        digitalWrite(pin_relay_aerator, LOW);
        conveyor_mtr.manual(0, 1, 255, 10000);
      }
      if (command == "led_on") {
        digitalWrite(pin_relay_led, HIGH);
      } else if (command == "led_off") {
        digitalWrite(pin_relay_led, LOW);
      }
    }
  }

  if (!mlx.begin()) {
    while (1);
  } else {
    wtrTemp = mlx.readObjectTempC();
  }

  if (tcs.available()) {
    luxIntensity = tcs.lux();
    lightTemp = tcs.colorTemperature();
    Serial.println(luxIntensity);
    Serial.println(lightTemp);
  } else {
    Serial.println("Light Sensor Unavailable!");
  }

  StaticJsonDocument<200> outDoc;

  //outDoc["light"] = currentLight;
  outDoc["level"] = wtrLvl;
  outDoc["temp"] = wtrTemp;
  outDoc["light"] = luxIntensity;
  outDoc["light_temp"] = lightTemp;
  Serial.println(wtrLvl);
  serializeJson(outDoc, Serial);
  Serial.println(); 
  
  delay(1000); 
}

int measureDistance() {    
  digitalWrite(pin_trig, LOW); // Set the trigger pin to low for 2uS 
  delayMicroseconds(2);   
  digitalWrite(pin_trig, HIGH); // Send a 10uS high to trigger ranging 
  delayMicroseconds(20); 
  
  digitalWrite(pin_trig,  LOW); // Send pin low again 
  int distance = pulseIn(pin_trig, pin_echo, 26000); //  Read in times pulse 
  distance = distance/58; //Convert the pulse duration  to distance
  //You can add other math functions to  calibrate it well

  delay(50);
  return distance;
}