#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <ArduinoJson.h>

#define MEASURE_DELAY 25

// PIN DEFINITIONS
const int pin_relay_aerator = 3; 
const int pin_relay_led = 2;
const int pin_echo = 9;
const int pin_trig = 10;
const int pin_mtr_pwma = 5;
const int pin_mtr_ai2 = 6;
const int pin_mtr_ai1 = 7;
const int pin_mtr_stby = 4;

// OBJECTS
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

void setup() {
  Serial.begin(115200);

  pinMode(pin_relay_aerator, OUTPUT);
  pinMode(pin_relay_led, OUTPUT);
  pinMode(pin_mtr_pwma, OUTPUT);
  pinMode(pin_mtr_ai1, OUTPUT);
  pinMode(pin_mtr_ai2, OUTPUT);
  pinMode(pin_mtr_stby, OUTPUT);
  pinMode(pin_trig, OUTPUT);
  pinMode(pin_echo, INPUT_PULLUP);

  digitalWrite(pin_relay_aerator, LOW);
  digitalWrite(pin_relay_led, LOW);
  digitalWrite(pin_trig, LOW);

  delayMicroseconds(500);
}

void loop() {
  float wtrTemp;
  int wtrLvl = measureDistance();
  int luxIntensity;

  if (Serial.available() > 0) {
    // READ RECEIVED STRINGS VIA SERIAL
    String rpi_cmd = Serial.readStringUntil('\n');
    
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, rpi_cmd);

    if (!error) {
      // PARSE COMMANDS FROM RASPBERRY PI
      String command = doc["command"];
      if (command == "aerator_on") {
        digitalWrite(pin_relay_aerator, HIGH);
      } else if (command == "aerator_off") {
        digitalWrite(pin_relay_aerator, LOW);
      }
      if (command == "led_on") {
        digitalWrite(pin_relay_led, HIGH);
      } else if (command == "led_off") {
        digitalWrite(pin_relay_led, LOW);
      }
    }
  }

  StaticJsonDocument<200> outDoc;

  if (!mlx.begin()) {
    outDoc["temp"] = "!!";
    while (1);
  } else {
    wtrTemp = mlx.readObjectTempC();
    outDoc["temp"] = wtrTemp;
  }

  //outDoc["light"] = currentLight;
  outDoc["level"] = wtrLvl;
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