import json


class Controller:
    def __init__(self, private_always_open_gate, private_always_close_gate, private_current_car_number, private_max_car_number, private_switch_on_light, private_switch_off_light, private_message, private_code,
                public_always_open_gate, public_always_close_gate, public_current_car_number, public_max_car_number, public_switch_on_light, public_switch_off_light, public_message, public_code
                ):
        self.private_always_open_gate = private_always_open_gate
        self.private_always_close_gate = private_always_close_gate
        self.private_current_car_number = private_current_car_number
        self.private_max_car_number = private_max_car_number
        self.private_switch_on_light = private_switch_on_light
        self.private_switch_off_light = private_switch_off_light
        
        self.private_message = private_message
        self.private_code = private_code

        self.public_always_open_gate = public_always_open_gate
        self.public_always_close_gate = public_always_close_gate
        self.public_current_car_number = public_current_car_number
        self.public_max_car_number = public_max_car_number
        self.public_switch_on_light = public_switch_on_light
        self.public_switch_off_light = public_switch_off_light
        
        self.public_message = public_message
        self.public_code = public_code

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
