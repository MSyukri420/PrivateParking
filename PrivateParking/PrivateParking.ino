#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>
#include <ArduinoJson.h>
#include <HCSR04.h>

// Pin Definitions
#define PARKING_LED_1 2
#define PARKING_LED_2 3
#define PARKING_LED_3 4

#define TRIG_PARKING_1 8
#define ECHO_PARKING_1 9
#define TRIG_PARKING_2 10
#define ECHO_PARKING_2 11
#define TRIG_PARKING_3 12
#define ECHO_PARKING_3 13

#define INFRARED_1 A5
#define INFRARED_2 A4
#define INFRARED_3 A3

#define NUM_PARKING_SLOTS 3
#define ERROR_DURATION 3000 

HCSR04 slot_1_ultrasonic(TRIG_PARKING_1, ECHO_PARKING_1);
HCSR04 slot_2_ultrasonic(TRIG_PARKING_2, ECHO_PARKING_2);
HCSR04 slot_3_ultrasonic(TRIG_PARKING_3, ECHO_PARKING_3);

enum ParkingState {
    PARKING_EMPTY,
    PARKING_OCCUPIED,
    PARKING_ERROR
};

struct ParkingSlot {
    HCSR04& ultrasonicPin;
    int ledPin;
    int irPin;
    ParkingState currentState;
    ParkingState previousState;
    unsigned long lastTriggerTime;
    unsigned long errorStartTime; 
    bool errorDataSent; 
};

ParkingSlot parkingSlots[NUM_PARKING_SLOTS] = {
    {slot_1_ultrasonic, PARKING_LED_1, INFRARED_1, PARKING_EMPTY, PARKING_EMPTY, 0, 0, false},
    {slot_2_ultrasonic, PARKING_LED_2, INFRARED_2, PARKING_EMPTY, PARKING_EMPTY, 0, 0, false},
    {slot_3_ultrasonic, PARKING_LED_3, INFRARED_3, PARKING_EMPTY, PARKING_EMPTY, 0, 0, false}
};

void setup() {
    Serial.begin(9600);
    Serial.println("Setup Complete");
    for (int i = 0; i < NUM_PARKING_SLOTS; i++) {
        pinMode(parkingSlots[i].ledPin, OUTPUT);
        pinMode(parkingSlots[i].irPin, INPUT);
         sendSerialData("Parking", PARKING_EMPTY, 0, i + 1);
    }
}

void loop() {
    for (int i = 0; i < NUM_PARKING_SLOTS; i++) {
        handleParkingDetection(parkingSlots[i], i + 1);
    }
    delay(100);
}

void handleParkingDetection(ParkingSlot &slot, int slotID) {
    int ultrasonicValue = getAverageDistance(slot.ultrasonicPin, 10);
    int infraredValue = analogRead(slot.irPin);
    bool irDetected = infraredValue < 512;
    bool ultraDetected = ultrasonicValue < 10;

    // Determine current state based on sensor readings
    if (irDetected && ultraDetected) {
        slot.currentState = PARKING_OCCUPIED;
        slot.errorStartTime = 0;  
        slot.errorDataSent = false;  
    } else if (irDetected || ultraDetected) {
        if (slot.currentState != PARKING_ERROR) {
            slot.errorStartTime = millis();  
        }
        slot.currentState = PARKING_ERROR;
    } else {
        slot.currentState = PARKING_EMPTY;
        slot.errorStartTime = 0;  
        slot.errorDataSent = false; 
    }

    // Handle state transitions and LED behavior
    if (slot.currentState != slot.previousState) {
        handleStateTransition(slot, slotID, ultrasonicValue);
        slot.previousState = slot.currentState;  // Update the previous state
    }

    // Handle PARKING_ERROR state and blinking LED
    if (slot.currentState == PARKING_ERROR) {
        handleErrorState(slot, slotID, ultrasonicValue);
    }
}

void handleStateTransition(ParkingSlot &slot, int slotID, int distance) {
    switch (slot.currentState) {
        case PARKING_EMPTY:
            digitalWrite(slot.ledPin, LOW); 
            sendSerialData("Parking", PARKING_EMPTY, distance, slotID);
            break;
        case PARKING_OCCUPIED:
            digitalWrite(slot.ledPin, HIGH);  
            sendSerialData("Parking", PARKING_OCCUPIED, distance, slotID);
            break;
        case PARKING_ERROR:
            slot.errorDataSent = false;  // Reset error data sent flag
            break;
    }
}

void handleErrorState(ParkingSlot &slot, int slotID, int distance) {
    unsigned long currentTime = millis();
    if (currentTime - slot.errorStartTime >= ERROR_DURATION) {
        if (!slot.errorDataSent) {
            sendSerialData("Parking", PARKING_ERROR, distance, slotID);
            slot.errorDataSent = true;  // Set error data sent flag
        }
        // Blink LED
        digitalWrite(slot.ledPin, HIGH);
        delay(200);
        digitalWrite(slot.ledPin, LOW);
        delay(200);
    }
}

void sendSerialData(String type, int status, int distance, int slotID) {
    // Create a JSON object
    StaticJsonDocument<200> jsonDoc;
    jsonDoc["type"] = type;
    jsonDoc["status"] = status;
    jsonDoc["distance"] = distance;
    jsonDoc["slotID"] = slotID;

    String jsonString;
    serializeJson(jsonDoc, jsonString);
    Serial.println(jsonString);
}

int getAverageDistance(HCSR04& ultrasonicPin, int numReadings) {
    long sum = 0;
    for (int i = 0; i < numReadings; i++) {
        sum += ultrasonicPin.dist();
        delay(100); 
    }
    return sum / numReadings;
}
