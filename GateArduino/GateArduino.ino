#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <ArduinoJson.h>
#include <Servo.h>

// Private Gate
#define SS_RFID_1 10
#define RST_RFID_1 9
#define GATE_LED_ENTER_1 4
#define INFRARED_END_ENTER_1 A0

#define INFRARED_START_EXIT_1 A1
#define GATE_LED_EXIT_1 5
#define INFRARED_END_EXIT_1 A2

// Public Gate
#define ServoPin 2
#define GATE_INFRARED_FRONT A4
#define GATE_END_BACK A5

Servo servo;
StaticJsonDocument<200> outgoing;
int public_always_open_gate, public_always_close_gate, public_manual, public_max_car_number, public_current_car_number, public_code;
int private_always_open_gate, private_always_close_gate, private_manual, private_max_car_number, private_current_car_number, private_code;


const int BUFFER_SIZE = 512;
char buffer[BUFFER_SIZE];

MFRC522 rfid(SS_RFID_1, RST_RFID_1);

void handleRFID();
void handleGateDetection();
void sendSerialData(const char *type, int status, const char *rfidTag, int distance, int slotID);

void setup()
{
	Serial.begin(9600);
	SPI.begin();
	rfid.PCD_Init();
	servo.attach(ServoPin);

	pinMode(GATE_LED_ENTER_1, OUTPUT);
	pinMode(GATE_LED_EXIT_1, OUTPUT);

	pinMode(INFRARED_END_ENTER_1, INPUT);
	pinMode(INFRARED_START_EXIT_1, INPUT);
	pinMode(INFRARED_END_EXIT_1, INPUT);
}

void loop()
{
	receiveData();
	handleRFID();
	handleGateDetection();
	handlePublicGate();
	delay(100);
}

void handleRFID()
{
	// detect card
	if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial())
	{
		// send data to the Raspberry Pi
		String rfidTag = getRfidTag();
		sendSerialData("Gate", 1, rfidTag.c_str(), 0, 1);

		// waiting for the server response
		int status = 100;
		while (true) {
			receiveData();
			if (private_code == 10) {
				digitalWrite(GATE_LED_ENTER_1, HIGH);
				break;
			} else if (private_code == 11) {
				digitalWrite(GATE_LED_ENTER_1, LOW);
				status = 0;
				break;
			}
		}

		if (status == 0) {
			return;
		}

		unsigned long startTime = millis();
		bool carDetected = false;

		while (millis() - startTime < 10000)
		{
			if (analogRead(INFRARED_END_ENTER_1) < 512)
			{
				carDetected = true;
				break;
			}
			delay(100);
		}

		if (carDetected)
		{
			digitalWrite(GATE_LED_ENTER_1, LOW);
		}
		else
		{
			while (analogRead(INFRARED_END_ENTER_1) > 512)
			{
				digitalWrite(GATE_LED_ENTER_1, HIGH);
				delay(500);
				digitalWrite(GATE_LED_ENTER_1, LOW);
				delay(500);
			}
			digitalWrite(GATE_LED_ENTER_1, LOW);
		}

		rfid.PICC_HaltA();
		rfid.PCD_StopCrypto1();
	}
}

void handleGateDetection()
{
	if (analogRead(INFRARED_START_EXIT_1) < 512)
	{
		int distance = analogRead(INFRARED_START_EXIT_1);
		sendSerialData("Gate", 2, "", distance, 1);
		digitalWrite(GATE_LED_EXIT_1, HIGH);

		unsigned long startTime = millis();
		bool carDetected = false;

		while (millis() - startTime < 10000)
		{
			if (analogRead(INFRARED_END_EXIT_1) < 512)
			{
				carDetected = true;
				break;
			}
			delay(100);
		}

		if (carDetected)
		{
			digitalWrite(GATE_LED_EXIT_1, LOW);
		}
		else
		{
			sendSerialData("Gate", 0, "", distance, 1);
			while (analogRead(INFRARED_END_EXIT_1) > 512)
			{
				digitalWrite(GATE_LED_EXIT_1, HIGH);
				delay(500);
				digitalWrite(GATE_LED_EXIT_1, LOW);
				delay(500);
			}
			digitalWrite(GATE_LED_EXIT_1, LOW);
		}
	}
}

String getRfidTag()
{
	String rfidTag = "";
	for (byte i = 0; i < rfid.uid.size; i++)
	{
		rfidTag += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "") + String(rfid.uid.uidByte[i], HEX);
	}
	rfidTag.toUpperCase();
	return rfidTag;
}

void sendSerialData(const char *type, int status, const char *rfidTag, int distance, int slotID)
{
	outgoing["type"] = type;
	outgoing["status"] = status;
	outgoing["rfidTag"] = rfidTag;
	outgoing["distance"] = distance;
	outgoing["slotID"] = slotID;

	// String jsonString;
	// serializeJson(outgoing, jsonString);
	// Serial.println(jsonString);
	serializeJson(outgoing, Serial);
	Serial.print('\n');
}

void receiveData()
{
	if (Serial.available() > 0)
	{
		memset(buffer, 0, BUFFER_SIZE);

		if (Serial.readBytesUntil('\n', buffer, BUFFER_SIZE) > 0)
		{
			Serial.println(buffer);
			StaticJsonDocument<200> jsonDoc;
			DeserializationError error = deserializeJson(jsonDoc, buffer);

			if (!error)
			{
				public_always_open_gate = jsonDoc["public_always_open_gate"];
				public_always_close_gate = jsonDoc["public_always_close_gate"];
				public_max_car_number = jsonDoc["public_max_car_number"];
				public_current_car_number = jsonDoc["public_current_car_number"];
				public_code = jsonDoc["public_code"];

				private_always_open_gate = jsonDoc["private_always_open_gate"];
				private_always_close_gate = jsonDoc["private_always_close_gate"];
				private_max_car_number = jsonDoc["private_max_car_number"];
				private_current_car_number = jsonDoc["private_current_car_number"];
				private_code = jsonDoc["private_code"];

				outgoing["public_always_open_gate"] = public_always_open_gate;
				outgoing["public_always_close_gate"] = public_always_close_gate;
				outgoing["public_max_car_number"] = public_max_car_number;
				outgoing["public_current_car_number"] = public_current_car_number;
				outgoing["public_code"] = public_code;

				outgoing["private_always_open_gate"] = private_always_open_gate;
				outgoing["private_always_close_gate"] = private_always_close_gate;
				outgoing["private_max_car_number"] = private_max_car_number;
				outgoing["private_current_car_number"] = private_current_car_number;
				outgoing["private_code"] = private_code;

				serializeJson(outgoing, Serial);
				Serial.print('\n');
			}
			else
			{
				Serial.println("Error");
			}
		}
	}
}

void handlePublicGate()
{
	if (public_always_open_gate == 1)
	{
		servo.write(90);
	}

	else if (public_always_close_gate == 1)
	{
		servo.write(0);
	}
}