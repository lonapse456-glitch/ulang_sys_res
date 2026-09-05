#include <ArduinoJson.h>
#include "TB6612FNG_XCR.h"

// Define your relay pins
#define PIN_RLY_AERATOR 2
#define PIN_MTR_PWMA 5
// #define PIN_MTR_PWMA 11
#define PIN_MTR_AI1 3
#define PIN_MTR_AI2 6
#define PIN_MTR_STBY 4

TB6612FNG_XCR conveyor_mtr;

void setup() {
  // 115200 baud rate is fast and stable for USB communication
  Serial.begin(115200);
  
  pinMode(PIN_RLY_AERATOR, OUTPUT);
  digitalWrite(PIN_RLY_AERATOR, LOW); // Default to OFF

  pinMode(PIN_MTR_PWMA, OUTPUT);
  pinMode(PIN_MTR_AI1, OUTPUT);
  pinMode(PIN_MTR_AI2, OUTPUT);
  pinMode(PIN_MTR_STBY, OUTPUT);

  // conveyor_mtr.attach(PIN_MTR_PWMA, PIN_MTR_AI1, PIN_MTR_AI2, "Conveyor");
  // conveyor_mtr.setStandbyPin(PIN_MTR_STBY);
}

void loop() {
  // ==========================================
  // 1. LISTEN FOR COMMANDS FROM RASPBERRY PI
  // ==========================================
  if (Serial.available() > 0) {
    // Read the incoming string until the newline character
    String incomingJson = Serial.readStringUntil('\n');
    
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, incomingJson);

    if (!error) {
      // Parse the Kivy command and actuate relays
      String command = doc["command"];
      if (command == "aerator_on") {
        //Serial.println("Conveyor_deploying...");
        digitalWrite(PIN_RLY_AERATOR, HIGH);
        digitalWrite(PIN_MTR_AI1, HIGH);
        digitalWrite(PIN_MTR_AI2, LOW);
        analogWrite(PIN_MTR_PWMA, 255);
        delay(10000);
        digitalWrite(PIN_MTR_AI1, LOW);
        analogWrite(PIN_MTR_PWMA, 0);
        // conveyor_mtr.manual(1, 0, 255, 10000);
        // conveyor_mtr.invert(false);
      } else if (command == "aerator_off") {
        //Serial.println("Conveyor_retreating...");
        digitalWrite(PIN_RLY_AERATOR, LOW);
        digitalWrite(PIN_MTR_AI1, LOW);
        digitalWrite(PIN_MTR_AI2, HIGH);
        analogWrite(PIN_MTR_PWMA, 255);
        delay(10000);
        digitalWrite(PIN_MTR_AI2, LOW);
        analogWrite(PIN_MTR_PWMA, 0);
        // conveyor_mtr.manual(1, 0, 255, 10000);
        // conveyor_mtr.invert(true);
      }
    }
  }

  // ==========================================
  // 2. SEND SENSOR READINGS TO RASPBERRY PI
  // ==========================================
  // In your real code, replace these with analogRead() or sensor library calls
  float currentTemp = 28.5; 
  int currentLight = 400;

  StaticJsonDocument<200> outDoc;
  outDoc["temp"] = currentTemp;
  outDoc["light"] = currentLight;

  // Send the JSON string to the Pi, followed by a newline (\n)
  serializeJson(outDoc, Serial);
  Serial.println(); 
  
  // A small delay to prevent flooding the Serial line
  delay(1000); 
}