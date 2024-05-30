import time
import json
from datetime import datetime
import mysql.connector
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishTimeoutException

# Print startup message
print("Starting up private parking script...")

# MySQL Configuration
database = mysql.connector.connect(
    host="database.ckozhfjjzal0.us-east-1.amazonaws.rds.com",
    user="admin",
    password="aRHnjDuknZhPZc4",
    database="parking"
)

endpoint = "a27eliy2xg4c5e-ats.iot.us-east-1.amazonaws.com"
cert_filepath = r"/home/pi/PrivateParking/mqtt/44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-certificate.pem.crt"
pri_key_filepath =  r"/home/pi/PrivateParking/mqtt/44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-private.pem.key"
ca_filepath = r"/home/pi/PrivateParking/mqtt/AmazonRootCA1.pem"
client_id = "ParkingSlot"

# AWS IoT MQTT Client Setup
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=endpoint,
    cert_filepath=cert_filepath,
    pri_key_filepath=pri_key_filepath,
    client_bootstrap=client_bootstrap,
    ca_filepath=ca_filepath,
    client_id=client_id,
    clean_session=False,
    keep_alive_secs=6
)

# Connect to AWS IoT Core
print(f"Connecting to {endpoint} with client ID '{client_id}'...")
connected_future = mqtt_connection.connect()
connected_future.result()
print("Connected!")

# Callback Functions
def sendData(topic, payload, dup, qos, retain, **kwargs):
    payload = payload.decode('utf-8')
    data = json.loads(payload)

    if "request" in data and data["request"] == "control_data":
        print("Sending data to RPI")
        cursor = database.cursor(dictionary=True)
        cursor.execute("SELECT * FROM variables")
        result = cursor.fetchall()
        database.commit()
        response_data = {row["name"]: row["value"] for row in result}
        
        print(response_data)
        try:
            mqtt_connection.publish(
                topic="rpi/get_private_parking", payload=json.dumps(response_data), qos=mqtt.QoS.AT_LEAST_ONCE)
        except publishTimeoutException:
            print("Publish timed out, retrying...")
            time.sleep(1)


current_parking_status = {}

def saveData(topic, payload, dup, qos, retain, **kwargs):
    print("Saving data to database")
    payload = payload.decode('utf-8')
    data = json.loads(payload)

    try:
        if "sql" in data:
            cursor = database.cursor()
            cursor.execute(data["sql"])
            database.commit()
            cursor.close()
            print("Executed SQL command successfully")
            return

        elif "type" in data and "status" in data and "distance" in data and "slotID" in data:
            slot_id = data["slotID"]
            status = data["status"]
            current_status = current_parking_status.get(slot_id, None)

            if status == 0 and current_status == 1:
                print(f"Ending parking session for slot_id: {slot_id}")
                end_parking_session(slot_id)
            elif status == 1 and current_status != 1:
                print(f"Starting parking session for slot_id: {slot_id}")
                start_parking_session(slot_id)
            elif status == 2:
                print(f"Logging system alarm for slot_id: {slot_id}")
                log_system_alarm(slot_id, "Error at parking slot", "Parking sensor error detected")

            current_parking_status[slot_id] = status
            print(f"Updating public carpark
