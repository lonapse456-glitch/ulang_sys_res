#include <ArduinoJson.h>
#include <Adafruit_MLX90614.h>
#include <Wire.h>
#include <math.h>

#define TCS3472_ADDR 0x29
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// Define your relay pins
const int aeratorRelayPin = 3; 
const int ledRelayPin = 2;

const int mtrPWMA = 5;
const int mtrAIN2 = 6;
const int mtrAIN1 = 7;
const int mtrSTBY = 4;
const int mtrSpeed = 255;

const int trigPIN = 10;
const int echoPIN = 9;

bool conveyor_moving = false;
unsigned long motor_start_millis = 0;
const unsigned long conveyor_timer = 10000;

void setup() {
  Serial.begin(9600);
  
  pinMode(aeratorRelayPin, OUTPUT);
  pinMode(ledRelayPin, OUTPUT);

  digitalWrite(aeratorRelayPin, LOW);
  digitalWrite(ledRelayPin, LOW); // Default to OFF

  pinMode(mtrPWMA, OUTPUT);
  pinMode(mtrAIN1, OUTPUT);
  pinMode(mtrAIN2, OUTPUT);
  pinMode(mtrSTBY, OUTPUT);

  // Enable motor driver
  digitalWrite(mtrSTBY, HIGH);

  pinMode(trigPIN, OUTPUT);
  pinMode(echoPIN, INPUT);

  digitalWrite(trigPIN, LOW);
  
  mlx.begin();

  Wire.begin();

  delay(100);

  Wire.beginTransmission(TCS3472_ADDR);

  if (Wire.endTransmission() != 0) {
    Serial.println("ERROR: TCS3472 NOT detected!");
    while (1);
  }

  Wire.beginTransmission(TCS3472_ADDR);
  Wire.write(0x80);
  Wire.write(0x03);
  Wire.endTransmission();

  delay(100);
}

void loop() {
  unsigned long current_millis = millis();

  if (conveyor_moving) {
    if (current_millis - motor_start_millis >= conveyor_timer) {
      // Time is up: Stop the motor (Coast)
      digitalWrite(mtrAIN1, LOW);
      digitalWrite(mtrAIN2, LOW);
      analogWrite(mtrPWMA, 0);
      conveyor_moving = false; // Reset the state
    }
  }
  // ==========================================
  // 1. NON-BLOCKING SERIAL LISTENER
  // ==========================================
  if (Serial.available() > 0) {
    // Read the incoming string until the newline character
    String incomingJson = Serial.readStringUntil('\n');
    
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, incomingJson);

    if (!error) {
      String command = doc["command"];
      
      // -- HARDWARE ACTUATORS --
      if (command == "aerator_on") {
        // -- Turn Aerator Relay On --
        digitalWrite(aeratorRelayPin, HIGH);
        // -- Turn the conveyor belt forward --
        digitalWrite(mtrAIN1, HIGH);
        digitalWrite(mtrAIN2, LOW);
        analogWrite(mtrPWMA, mtrSpeed);
        conveyor_moving = true;

      } else if (command == "aerator_off") {
        // -- Turn Aerator Relay Off --
        digitalWrite(aeratorRelayPin, HIGH);
        // -- Turn the conveyor belt reverse --
        digitalWrite(mtrAIN1, LOW);
        digitalWrite(mtrAIN2, HIGH);
        analogWrite(mtrPWMA, mtrSpeed);
        conveyor_moving = false;

      } else if (command == "led_on") {
        digitalWrite(ledRelayPin, HIGH);
        
      } else if (command == "led_off") {
        digitalWrite(ledRelayPin, LOW);
      }
      // -- SENSOR PING-PONG RESPONSE --
      else if (command == "get_sensors") {
        float currentTemp = mlx.readObjectTempC(); 
        uint16_t currentLight = read16(0x14);// Placeholder until your TCS34725 is added
        float wtrLvl = measureDistance();

        StaticJsonDocument<200> outDoc;
        outDoc["temp"] = currentTemp;
        outDoc["light"] = currentLight;
        outDoc["wtrlvl"] = wtrLvl;

        // Send the JSON string to the Pi, followed by a newline (\n)
        serializeJson(outDoc, Serial);
        Serial.println(); 
      }
    }
  }
}

uint16_t read16(uint8_t reg) {
  Wire.beginTransmission(TCS3472_ADDR);
  Wire.write(0x80 | reg);
  Wire.endTransmission();
  Wire.requestFrom((uint8_t)TCS3472_ADDR, (uint8_t)2);

  if (Wire.available() >= 2) {
    uint8_t lowByte = Wire.read();
    uint8_t highByte = Wire.read();
    return ((uint16_t)highByte << 8) | lowByte;
  }
  return 0;
}

float measureDistance() {
  // Send ultrasonic pulse
  digitalWrite(trigPIN, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPIN, LOW);

  // Measure echo time
  long duration = pulseIn(echoPIN, HIGH);

  // Calculate distance in centimeters
  float distance = duration * 0.0343 / 2;

  delay(10);
  return distance;
}