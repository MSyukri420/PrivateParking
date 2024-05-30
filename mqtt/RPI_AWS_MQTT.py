import time  #Import time library
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json

myMQTTClient = AWSIoTMQTTClient("pi")
myMQTTClient.configureEndpoint("a27eliy2xg4c5e-ats.iot.us-east-1.amazonaws.com", 8883)
myMQTTClient.configureCredentials(
    r"\home\pi\PrivateParking\mqtt\AmazonRootCA1.pem",
    r"\home\pi\PrivateParking\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-private.pem.key",
    r"\home\pi\PrivateParking\mqtt\44bdbb017ed61e3180473d7562a7219625694010abfe0315ab96632a7fe8402b-certificate.pem.crt"
)
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)
myMQTTClient.configureConnectDisconnectTimeout(10)
myMQTTClient.configureMQTTOperationTimeout(50)

myMQTTClient.connect()

while True:
    time.sleep(2)
    payload = {"request": "control_data"}
    print(payload)
    myMQTTClient.publish("rpi/get_request", json.dumps(payload), 0)

    sql = {
        "sql": "UPDATE variables SET value = value + 1 WHERE name = 'public_max_car_number';"
    }
    print(sql)
    myMQTTClient.publish("rpi/post_request", json.dumps(sql), 0)
