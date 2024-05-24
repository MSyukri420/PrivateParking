import time
import json
from SerialInterface import SerialInterface
from Controller import Controller
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from Database import Database

localDatabase = Database.get_instance()
controller = Controller()
data_received = False
iface = SerialInterface()

post_response_data = {
    "type": None,
    "message": None
}

def retrieveData(client, userdata, message):
    print("New message received")
    global controller, localDatabase, data_received
    payload = message.payload.decode('utf-8')
    data = json.loads(payload)
    print(data)

    if "public_always_open_gate" in data:
        controller.public_always_open_gate = data["public_always_open_gate"]
    if "public_always_close_gate" in data:
        controller.public_always_close_gate = data["public_always_close_gate"]
    if "public_current_car_number" in data:
        controller.public_current_car_number = data["public_current_car_number"]
    if "public_max_car_number" in data:
        controller.public_max_car_number = data["public_max_car_number"]

    if "private_always_open_gate" in data:
        controller.private_always_open_gate = data["private_always_open_gate"]
    if "private_always_close_gate" in data:
        controller.private_always_close_gate = data["private_always_close_gate"]
    if "private_current_car_number" in data:
        controller.private_current_car_number = data["private_current_car_number"]
    if "private_max_car_number" in data:
        controller.private_max_car_number = data["private_max_car_number"]

    data_received = True
    # combine 2 object class into 1 object
    print(controller.toJson())
    iface.write_msg(controller.toJson())
    # response = iface.read_msg()
    # i = 5
    # while response is None or response.startswith("Error") or response.startswith("InvalidInput") and i > 0:
    #     print(f"Response: {response}")
    #     iface.write_msg(controller.toJson())
    #     response = iface.read_msg()
    #     i -= 1

def handleResponseData(client, userdata, message):
    print("Response received")
    payload = message.payload.decode('utf-8')
    data = json.loads(payload)

    if "status" in data and "message" in data:
        post_response_data["status"] = data["status"]
        post_response_data["message"] = data["message"]

myMQTTClient = AWSIoTMQTTClient("rpi_public")
myMQTTClient.configureEndpoint(
    "a27eliy2xg4c5e-ats.iot.us-east-1.amazonaws.com", 8883)
# myMQTTClient.configureCredentials(
#     r"D:\Users\User\Programming\Swinburne Project\IOT\mqtt\AmazonRootCA1.pem",
#     r"D:\Users\User\Programming\Swinburne Project\IOT\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-private.pem.key",
#     r"D:\Users\User\Programming\Swinburne Project\IOT\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-certificate.pem.crt"
# )
myMQTTClient.configureCredentials(
    r"/home/pi/RPi/mqtt/AmazonRootCA1.pem",
    r"/home/pi/RPi/mqtt/44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-private.pem.key",
    r"/home/pi/RPi/mqtt/44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-certificate.pem.crt"
)
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)
myMQTTClient.configureConnectDisconnectTimeout(10)
myMQTTClient.configureMQTTOperationTimeout(5)

myMQTTClient.connect()
myMQTTClient.publish("rpi/get_request", json.dumps({"request": "control_data"}), 1)
myMQTTClient.subscribe("rpi/get_response", 1, retrieveData)
myMQTTClient.subscribe("rpi/post_response", 1, handleResponseData)

if __name__ == "__main__":
    while True:
        if not data_received:
            # localData = localDatabase.query("SELECT * from variables", False)
            # if localData is not None:
            #     data_received = True
            print("Waiting for data...")
            time.sleep(1)
            continue

        response = iface.read_msg()

        if response is None:
            continue

        print(f"Response: {response}")
        time.sleep(0.1)

        if "type" in response and "status" in response and "rfidTag" in response and "distance" in response and "slotID" in response:
            myMQTTClient.publish("rpi/post_request", json.dumps(response), 1)
            while post_response_data["status"] is None and post_response_data["message"] is None:
                print("Waiting for response...")
                time.sleep(1)
            print(post_response_data)

            if post_response_data["status"] == "success" and post_response_data["message"] == "RFID found":
                controller.code = 10
                iface.write_msg(controller.toJson())
            elif post_response_data["status"] == "error" and post_response_data["message"] == "RFID not found":
                controller.code = 11
                iface.write_msg(controller.toJson())

            post_response_data["status"] = None
            post_response_data["message"] = None

        # Automation based on sensors
        if response.startswith("Entry sensor activated"):
            print("Python Entry sensor activated")
            # waiting for camera to detect license plate
            localDatabase.query("UPDATE variables SET value = 1 WHERE name = 'is_entering'", False)
            is_processing_carplate = localDatabase.query("SELECT * FROM variables WHERE name = 'is_processing_carplate' LIMIT 1")["value"]

            # 0 represent ideal state
            # 1 represent processing
            # 2 represent completed
            # 3 represent error
            while is_processing_carplate == 0 or is_processing_carplate == 1:
                # response = iface.read_msg()
                print(f"Response: {response}")
                print("Waiting at entry...")
                time.sleep(0.5)

                max_car_number = localDatabase.query("SELECT * FROM variables WHERE name = 'max_car_number' LIMIT 1")["value"]
                current_car_number = localDatabase.query("SELECT * FROM variables WHERE name = 'current_car_number' LIMIT 1")["value"]

                if current_car_number >= max_car_number:
                    print("Carpark is full")
                    controller.message = "Carpark is full"
                    # iface.write_msg(controller.toJson())
                    break

                is_processing_carplate = localDatabase.query(
                    "SELECT * FROM variables WHERE name = 'is_processing_carplate' LIMIT 1")["value"]
                if is_processing_carplate == 2 or is_processing_carplate == 3:
                    break

            if is_processing_carplate == 2:
                print("Carplate detected")
                localDatabase.query("UPDATE variables SET value = 0 WHERE name = 'is_processing_carplate'", False)
                localDatabase.query("UPDATE variables SET value = 0 WHERE name = 'is_entering'", False)
                localDatabase.query("UPDATE variables SET value = value + 1 WHERE name = 'current_car_number'", False)
                controller.current_car_number = localDatabase.query(
                    "SELECT * FROM variables WHERE name = 'current_car_number' LIMIT 1")["value"]
                # controller.car_plate = database.query("SELECT * FROM car_entry_exit_log ORDER BY id DESC LIMIT 1")["carplate"]
                controller.code = 12
                print(controller.toJson())
                # iface.write_msg(controller.toJson())

            elif is_processing_carplate == 3:
                print("Error in detecting carplate")
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_processing_carplate'", False)
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_entering'", False)
                controller.message = "Error in detecting carplate"
                # iface.write_msg(controller.toJson())

        elif response.startswith("Exit sensor activated"):
            print("Exit sensor activated")
            localDatabase.query(
                "UPDATE variables SET value = 1 WHERE name = 'is_exiting'", False)
            is_processing_carplate = localDatabase.query(
                "SELECT * FROM variables WHERE name = 'is_processing_carplate' LIMIT 1")["value"]

            while is_processing_carplate == 0 or is_processing_carplate == 1:
                print("Waiting at exit...")
                time.sleep(0.5)

                max_car_number = localDatabase.query(
                    "SELECT * FROM variables WHERE name = 'max_car_number' LIMIT 1")["value"]
                current_car_number = localDatabase.query(
                    "SELECT * FROM variables WHERE name = 'current_car_number' LIMIT 1")["value"]

                time.sleep(8)
                localDatabase.query(
                    "UPDATE variables SET value = 2 WHERE name = 'is_processing_carplate'", False)
                is_processing_carplate = localDatabase.query(
                    "SELECT * FROM variables WHERE name = 'is_processing_carplate' LIMIT 1")["value"]

                if is_processing_carplate == 2 or is_processing_carplate == 3:
                    break

            if is_processing_carplate == 2:
                print("Carplate detected")
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_processing_carplate'", False)
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_exiting'", False)
                localDatabase.query(
                    "UPDATE variables SET value = value - 1 WHERE name = 'current_car_number'", False)
                controller.current_car_number = localDatabase.query(
                    "SELECT * FROM variables WHERE name = 'current_car_number' LIMIT 1")["value"]
                # controller.car_plate = database.query("SELECT * FROM car_entry_exit_log ORDER BY id DESC LIMIT 1")["carplate"]
                controller.code = 12
                print(controller.toJson())
                # iface.write_msg(controller.toJson())
                controller.message = ""

            elif is_processing_carplate == 3:
                print("Error in detecting carplate")
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_processing_carplate'", False)
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_exiting'", False)
                # iface.write_msg(controller.toJson())
        # time.sleep(1)

    # iface.close()
