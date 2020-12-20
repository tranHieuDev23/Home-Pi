from .device import DeviceType
from .mqtt_device import MqttDevice
import json


class MqttLight(MqttDevice):
    def __init__(self, id, name, location):
        super().__init__(id, name, DeviceType.LIGHT, location)
        self.__status_topic = None
        self.__command_topic = None

    def set_status_topic(self, topic):
        if (self.__status_topic is not None):
            self.__mqtt_client.unsubscribe(self.__status_topic)
        self.__status_topic = topic
        self.__mqtt_client.subscribe(topic)

    def set_command_topic(self, topic):
        self.__command_topic = topic

    def is_on(self):
        return self.get_field('isOn')

    def handle_command(self, command):
        if (self.__command_topic is None):
            return
        json_command = dict()
        json_command['on'] = command['on']
        json_str = json.dumps(json_command)
        self.__mqtt_client.publish(self.__command_topic, json_str)

    def on_message(self, client, userdata, msg):
        super().on_message(client, userdata, msg)
        json_message = json.loads(msg.payload)
        isOn = json_message['isOn']
        self.__set_field('isOn', isOn)
