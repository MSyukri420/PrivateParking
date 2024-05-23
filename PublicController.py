import json


class PublicController:
    def __init__(self, public_always_open_gate, public_always_close_gate, public_current_car_number, public_max_car_number, public_switch_on_light, public_switch_off_light, message, code):
        self.public_always_open_gate = public_always_open_gate
        self.public_always_close_gate = public_always_close_gate
        self.public_current_car_number = public_current_car_number
        self.public_max_car_number = public_max_car_number
        self.public_switch_on_light = public_switch_on_light
        self.public_switch_off_light = public_switch_off_light
        
        self.public_message = message
        self.public_code = code

    # default constructor
    def __init__(self):
        self.public_always_open_gate = 0
        self.public_always_close_gate = 0
        self.public_current_car_number = 0
        self.public_max_car_number = 0
        self.public_switch_on_light = 0
        self.public_switch_off_light = 0
        
        self.public_message = ""
        self.public_code = 0

    def toJson(self):
        return json.loads(json.dumps(self.__dict__))
