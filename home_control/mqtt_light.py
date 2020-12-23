from .device import DeviceType
from .mqtt_device import MqttDevice


class MqttLight(MqttDevice):
    def __init__(self, id, name, location):
        super().__init__(id, name, DeviceType.LIGHT, location)

    def is_on(self):
        return self.get_field('isOn')

    def handle_command(self, command):
        command_json = dict()
        command_json['on'] = command['on']
        self.send_command(command_json)

    def on_status_message(self, status_json):
        isOn = status_json['isOn']
        self.__set_field('isOn', isOn)
