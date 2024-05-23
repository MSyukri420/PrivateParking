import json


class PublicController:
    def __init__(self, always_open_gate, always_close_gate, message, current_car_number, max_car_number, switch_on_light, switch_off_light, code, isManual):
        self.isManual = isManual
        self.always_open_gate = always_open_gate
        self.always_close_gate = always_close_gate
        self.current_car_number = current_car_number
        self.max_car_number = max_car_number
        self.switch_on_light = switch_on_light
        self.switch_off_light = switch_off_light
        
        self.message = message
        self.code = code

    # default constructor
    def __init__(self):
        self.isManual = 0
        self.always_open_gate = 0
        self.always_close_gate = 0
        self.current_car_number = 0
        self.max_car_number = 0
        self.switch_on_light = 0
        self.switch_off_light = 0
        
        self.message = ""
        self.code = 0

    def toJson(self):
        return json.loads(json.dumps(self.__dict__))
