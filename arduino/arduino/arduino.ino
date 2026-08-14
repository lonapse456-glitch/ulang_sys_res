#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Define your relay pins
const int aeratorRelayPin = 7; 
const int ledRelayPin = 11;

#define ONE_WIRE_BUS 13

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  // 115200 baud rate is fast and stable for USB communication
  Serial.begin(115200);
  sensors.begin();
  pinMode(aeratorRelayPin, OUTPUT);
  pinMode(ledRelayPin, OUTPUT);
  digitalWrite(aeratorRelayPin, LOW);
  digitalWrite(aeratorRelayPin, LOW); // Default to OFF
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
        digitalWrite(aeratorRelayPin, HIGH);
      } else if (command == "aerator_off") {
        digitalWrite(aeratorRelayPin, LOW);
      }
      if (command == "led_on") {
        digitalWrite(ledRelayPin, HIGH);
      } else if (command == "led_off") {
        digitalWrite(ledRelayPin, LOW);
      }
    }
  }

  // ==========================================
  // 2. SEND SENSOR READINGS TO RASPBERRY PI
  // ==========================================
  // In your real code, replace these with analogRead() or sensor library calls
  
  sensors.requestTemperatures();

  float currentTemp = sensors.getTempCByIndex(0);
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