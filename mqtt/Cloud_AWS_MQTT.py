import time  # Import time library
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import mysql.connector
import json
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishTimeoutException

myMQTTClient = AWSIoTMQTTClient("MyCloudComputer")
myMQTTClient.configureEndpoint(
    "a27eliy2xg4c5e-ats.iot.us-east-1.amazonaws.com", 8883)
myMQTTClient.configureCredentials(
    r"D:\Users\User\Programming\Swinburne Project\IOT\mqtt\AmazonRootCA1.pem",
    r"D:\Users\User\Programming\Swinburne Project\IOT\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-private.pem.key",
    r"D:\Users\User\Programming\Swinburne Project\IOT\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-certificate.pem.crt"
)
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)
myMQTTClient.configureConnectDisconnectTimeout(10)
myMQTTClient.configureMQTTOperationTimeout(5)


database = mysql.connector.connect(
    host="database.ckozhfjjzal0.us-east-1.rds.amazonaws.com",
    user="admin",
    password="aRHnjDuknZhPZc4",
    database="parking"
)

myMQTTClient.connect()


def sendData(client, userdata, message):
    payload = message.payload.decode('utf-8')
    data = json.loads(payload)

    if "request" in data and data["request"] == "control_data":
        print("Sending data to RPI")
        cursor = database.cursor(dictionary=True)
        cursor.execute("SELECT * FROM variables")
        result = cursor.fetchall()
        database.commit()
        response_data = {}
        for row in result:
            response_data[row["name"]] = row["value"]

        print(response_data)
        try:
            myMQTTClient.publish("rpi/get_response",
                                 json.dumps(response_data), 1)
            myMQTTClient.publish("rpi/get_request", json.dumps(payload), 0)
        except publishTimeoutException:
            print("Publish timed out, retrying...")
            time.sleep(1)

        return


def saveData(client, userdata, message):
    print("Saving data to database")
    payload = message.payload.decode('utf-8')
    data = json.loads(payload)

    if "sql" in data:
        cursor = database.cursor()
        cursor.execute(data["sql"])
        database.commit()
        return
    
    elif "type" in data and "status" in data and "rfidTag" in data and "distance" in data and "slotID" in data:
        cursor = database.cursor()
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchall()
        print(result)

        exist = False

        for row in result:
            if row["rfid_tag"] == data["rfidTag"]:
                cursor.execute(f"INSERT INTO access_logs (user_id, event_type, timestamp) VALUES ({row['id']}, 'enter', NOW())")
                exist = True
                database.commit()

        if not exist:
            cursor.execute(f"INSERT INTO system_alarms (type, description, timestamp) VALUES ('{data['type']}', 'error at private gate', NOW())")
            database.commit()
            response = {
                "status": "error",
                "message": "RFID not found"
            }
            myMQTTClient.publish("rpi/post_response", json.dumps(response), 1)
            return
        elif exist:
            response = {
                "status": "success",
                "message": "RFID found"
            }
            myMQTTClient.publish("rpi/post_response", json.dumps(response), 1)
            return

        return


myMQTTClient.subscribe("rpi/get_request", 1, sendData)
myMQTTClient.subscribe("rpi/post_request", 1, saveData)


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrupted by user, disconnecting...")
    myMQTTClient.disconnect()
    print("Disconnected")
