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
    "status": None,
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

request = {
    "request": "control_data"
}

myMQTTClient.connect()
myMQTTClient.publish("rpi/get_request", json.dumps(request), 1)
myMQTTClient.subscribe("rpi/get_response", 1, retrieveData)
myMQTTClient.subscribe("rpi/post_response", 1, handleResponseData)

if __name__ == "__main__":
    while True:
        response = iface.read_msg()
        if response is None:
            continue

        print(f"Response: {response}")
        time.sleep(0.1)

    # iface.close()
