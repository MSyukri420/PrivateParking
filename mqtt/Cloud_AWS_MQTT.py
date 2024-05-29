import time
import json
from datetime import datetime
import mysql.connector
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishTimeoutException

# MySQL Configuration
database = mysql.connector.connect(
    host="database.ckozhfjjzal0.us-east-1.rds.amazonaws.com",
    user="admin",
    password="aRHnjDuknZhPZc4",
    database="parking"
)

endpoint = "a27eliy2xg4c5e-ats.iot.us-east-1.amazonaws.com"
cert_filepath = r"C:\Users\Syukri\Desktop\Github Repo\RPi-clone\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-certificate.pem.crt"
pri_key_filepath =  r"C:\Users\Syukri\Desktop\Github Repo\RPi-clone\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-private.pem.key"
ca_filepath = r"C:\Users\Syukri\Desktop\Github Repo\RPi-clone\mqtt\AmazonRootCA1.pem"
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
                topic="rpi/get_response", payload=json.dumps(response_data), qos=mqtt.QoS.AT_LEAST_ONCE)
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
                end_parking_session(slot_id)
            elif status == 1 and current_status != 1:
                start_parking_session(slot_id)
            elif status == 2:
                log_system_alarm(slot_id, "Error at parking slot", "Parking sensor error detected")

            current_parking_status[slot_id] = status
            update_public_carpark_slot(slot_id, status)
    except Exception as e:
        print(f"Error processing data: {e}")

def start_parking_session(slot_id):
    try:
        cursor = database.cursor()
        cursor.execute(
            'INSERT INTO parking_sessions (slot_id, start_time, status) VALUES (%s, %s, %s)',
            (slot_id, datetime.now(), 'active')
        )
        cursor.execute(
            'UPDATE public_carpark_slot SET status = 1 WHERE id = %s',
            (slot_id,)
        )
        database.commit()
        cursor.close()
    except Exception as e:
        print(f"Error starting parking session: {e}")

def end_parking_session(slot_id):
    try:
        cursor = database.cursor()
        cursor.execute(
            'UPDATE parking_sessions SET end_time = %s, status = %s WHERE slot_id = %s AND end_time IS NULL',
            (datetime.now(), 'completed', slot_id)
        )
        cursor.execute(
            'UPDATE public_carpark_slot SET status = 0 WHERE id = %s',
            (slot_id,)
        )
        database.commit()
        cursor.close()
    except Exception as e:
        print(f"Error ending parking session: {e}")

def log_system_alarm(slot_id, alarm_type, description):
    try:
        cursor = database.cursor()
        cursor.execute(
            'INSERT INTO system_alarms (type, description, timestamp) VALUES (%s, %s, %s)',
            (alarm_type, description, datetime.now())
        )
        database.commit()
        cursor.close()
    except Exception as e:
        print(f"Error logging system alarm: {e}")

def update_public_carpark_slot(slot_id, status):
    try:
        cursor = database.cursor()
        cursor.execute(
            'UPDATE public_carpark_slot SET status = %s WHERE id = %s',
            (status, slot_id)
        )
        database.commit()
        cursor.close()
    except Exception as e:
        print(f"Error updating public carpark slot: {e}")

# MQTT Subscriptions
print("Subscribing to topic 'rpi/get_request'...")
subscribe_future, packet_id = mqtt_connection.subscribe(
    topic="rpi/get_request",
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=sendData
)

# Wait for the subscribe to succeed
subscribe_result = subscribe_future.result()
print("Subscribed with {}".format(str(subscribe_result['qos'])))

print("Subscribing to topic 'rpi/post_request'...")
subscribe_future, packet_id = mqtt_connection.subscribe(
    topic="rpi/post_request",
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=saveData
)

# Wait for the subscribe to succeed
subscribe_result = subscribe_future.result()
print("Subscribed with {}".format(str(subscribe_result['qos'])))

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrupted by user, disconnecting...")
    mqtt_connection.disconnect().result()
    print("Disconnected")
