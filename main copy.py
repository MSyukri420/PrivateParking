import time
import json
from SerialInterface import SerialInterface
from PublicController import PublicController
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from Database import Database
from model.GateOpenLog import GateOpenLog
from model.GateCloseLog import GateCloseLog

localDatabase = Database.get_instance()
controller = PublicController()
data_received = False
iface = SerialInterface()


def retrieveData(client, userdata, message):
    global controller, localDatabase, data_received
    payload = message.payload.decode('utf-8')
    data = json.loads(payload)
    print(data)

    if "public_always_open_gate" in data:
        controller.always_open_gate = data["public_always_open_gate"]
    elif "public_always_close_gate" in data:
        controller.always_close_gate = data["public_always_close_gate"]
    elif "public_current_car_number" in data:
        controller.current_car_number = data["public_current_car_number"]
    elif "public_max_car_number" in data:
        controller.max_car_number = data["public_max_car_number"]
    elif "public_switch_on_light" in data:
        controller.switch_on_light = data["public_switch_on_light"]
    elif "public_switch_off_light" in data:
        controller.switch_off_light = data["value"]
    elif "public_manual_light" in data:
        controller.automation_light_status = data["value"]

    data_received = True
    iface.write_msg(controller.toJson())



myMQTTClient = AWSIoTMQTTClient("rpi_public")
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

myMQTTClient.connect()
myMQTTClient.publish("rpi/get_request", {"request": "control_data"}, 1)
myMQTTClient.subscribe("rpi/get_response", 1, retrieveData)

if __name__ == "__main__":
    while data_received:
        response = iface.read_msg()
        print(f"Response: {response}")

        # if iface.receive_confirmation():
        #     # print(controller.toJson())
        #     # print("Received confirmation")
        #     iface.write_msg(controller.toJson())

        if response is None:
            continue

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
                response = iface.read_msg()
                print(f"Response: {response}")
                print("Waiting at entry...")
                time.sleep(0.5)

                max_car_number = localDatabase.query("SELECT * FROM variables WHERE name = 'max_car_number' LIMIT 1")["value"]
                current_car_number = localDatabase.query("SELECT * FROM variables WHERE name = 'current_car_number' LIMIT 1")["value"]

                if current_car_number >= max_car_number:
                    print("Carpark is full")
                    controller.message = "Carpark is full"
                    iface.write_msg(controller.toJson())
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
                iface.write_msg(controller.toJson())

            elif is_processing_carplate == 3:
                print("Error in detecting carplate")
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_processing_carplate'", False)
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_entering'", False)
                controller.message = "Error in detecting carplate"
                iface.write_msg(controller.toJson())

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
                iface.write_msg(controller.toJson())
                controller.message = ""

            elif is_processing_carplate == 3:
                print("Error in detecting carplate")
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_processing_carplate'", False)
                localDatabase.query(
                    "UPDATE variables SET value = 0 WHERE name = 'is_exiting'", False)
                iface.write_msg(controller.toJson())
        # time.sleep(1)

    iface.close()
