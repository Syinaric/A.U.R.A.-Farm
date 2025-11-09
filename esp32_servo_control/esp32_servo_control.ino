/*
 * ESP32 Robot Arm Control
 * Receives servo commands from Python via Serial
 * 
 * Hardware:
 * - Base: GPIO 5 (D5) - MG996R 180°
 * - Shoulder: GPIO 18 (D18) - MG996R 180°
 * - Elbow: GPIO 22 (D22) - MG996R 180°
 * - Wrist: GPIO 19 (D19) - 9g servo 180°
 * 
 * Required library: ESP32Servo
 */

#include <ESP32Servo.h>
#include <ArduinoJson.h>

// Servo GPIO pins
#define SERVO_BASE_PIN 5      // D5
#define SERVO_SHOULDER_PIN 18 // D18
#define SERVO_ELBOW_PIN 22    // D22
#define SERVO_WRIST_PIN 19    // D19

// Create servo objects
Servo servo_base;
Servo servo_shoulder;
Servo servo_elbow;
Servo servo_wrist;

// MG996R servo specifications
#define SERVO_MIN_PULSE 500   // 0.5ms in microseconds
#define SERVO_MAX_PULSE 2500  // 2.5ms in microseconds

// JSON buffer size
#define JSON_BUFFER_SIZE 256

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("==========================================");
  Serial.println("ESP32 Robot Arm Control");
  Serial.println("==========================================");
  Serial.println("\nInitializing servos...");
  Serial.println("Base: GPIO 5 (D5) - MG996R");
  Serial.println("Shoulder: GPIO 18 (D18) - MG996R");
  Serial.println("Elbow: GPIO 22 (D22) - MG996R");
  Serial.println("Wrist: GPIO 19 (D19) - 9g servo");
  
  // Attach servos to pins
  servo_base.attach(SERVO_BASE_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  servo_shoulder.attach(SERVO_SHOULDER_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  servo_elbow.attach(SERVO_ELBOW_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  servo_wrist.attach(SERVO_WRIST_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  
  // Set all servos to center position (90°)
  servo_base.writeMicroseconds(1500);
  servo_shoulder.writeMicroseconds(1500);
  servo_elbow.writeMicroseconds(1500);
  servo_wrist.writeMicroseconds(1500);
  
  Serial.println("\nServos initialized. Ready to receive commands.");
  Serial.println("Waiting for commands from Python...");
  Serial.println("Command format: {\"op\":\"servos\",\"base\":1500,\"shoulder\":1500,\"elbow\":1500,\"wrist\":1500}");
}

void loop() {
  // Check for incoming serial data
  if (Serial.available() > 0) {
    String jsonString = Serial.readStringUntil('\n');
    jsonString.trim();
    
    if (jsonString.length() > 0) {
      processCommand(jsonString);
    }
  }
  
  // Small delay to prevent overwhelming the processor
  delay(10);
}

void processCommand(String jsonString) {
  // Parse JSON command
  StaticJsonDocument<JSON_BUFFER_SIZE> doc;
  DeserializationError error = deserializeJson(doc, jsonString);
  
  if (error) {
    Serial.print("ERROR: Invalid JSON - ");
    Serial.println(error.c_str());
    return;
  }
  
  // Check command operation
  const char* op = doc["op"];
  
  if (strcmp(op, "servos") == 0) {
    // Set all servos
    int base_us = doc["base"] | 1500;
    int shoulder_us = doc["shoulder"] | 1500;
    int elbow_us = doc["elbow"] | 1500;
    int wrist_us = doc["wrist"] | 1500;
    
    // Clamp values to valid range (900-2100)
    base_us = constrain(base_us, 900, 2100);
    shoulder_us = constrain(shoulder_us, 900, 2100);
    elbow_us = constrain(elbow_us, 900, 2100);
    wrist_us = constrain(wrist_us, 900, 2100);
    
    // Set servo positions
    servo_base.writeMicroseconds(base_us);
    servo_shoulder.writeMicroseconds(shoulder_us);
    servo_elbow.writeMicroseconds(elbow_us);
    servo_wrist.writeMicroseconds(wrist_us);
    
    // Send confirmation
    Serial.print("OK: servos set to ");
    Serial.print(base_us);
    Serial.print(",");
    Serial.print(shoulder_us);
    Serial.print(",");
    Serial.print(elbow_us);
    Serial.print(",");
    Serial.println(wrist_us);
    
  } else if (strcmp(op, "test") == 0) {
    // Test command
    Serial.println("OK: ESP32 is responding");
    
  } else {
    Serial.print("ERROR: Unknown operation - ");
    Serial.println(op);
  }
}

