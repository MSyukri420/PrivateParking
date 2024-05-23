import json


class PrivateController:
    def __init__(self, private_always_open_gate, private_always_close_gate, private_current_car_number, private_max_car_number, private_switch_on_light, private_switch_off_light, message, code):
        self.private_always_open_gate = private_always_open_gate
        self.private_always_close_gate = private_always_close_gate
        self.private_current_car_number = private_current_car_number
        self.private_max_car_number = private_max_car_number
        self.private_switch_on_light = private_switch_on_light
        self.private_switch_off_light = private_switch_off_light
        
        self.private_message = message
        self.private_code = code

    # default constructor
    def __init__(self):
        self.private_always_open_gate = 0
        self.private_always_close_gate = 0
        self.private_current_car_number = 0
        self.private_max_car_number = 0
        self.private_switch_on_light = 0
        self.private_switch_off_light = 0
        
        self.private_message = ""
        self.private_code = 0

    def toJson(self):
        return json.loads(json.dumps(self.__dict__))
