#include <ArduinoJson.h>

// Define your relay pins
const int aeratorRelayPin = 2; 

void setup() {
  // 115200 baud rate is fast and stable for USB communication
  Serial.begin(115200);
  
  pinMode(aeratorRelayPin, OUTPUT);
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