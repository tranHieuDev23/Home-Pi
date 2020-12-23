from time import sleep
from .device import Device
import paho.mqtt.client as mqtt
import json


class MqttDevice(Device):
    def __init__(self, id, name, type, location):
        super().__init__(id, name, type, location)
        self.__mqtt_client = mqtt.Client()
        self.__broker = None
        self.__port = None
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.__on_message
        self.__status_topic = None
        self.__command_topic = None

    def get_status_topic(self):
        return self.__status_topic

    def get_command_topic(self):
        return self.__command_topic

    def set_status_topic(self, topic):
        if (self.__status_topic is not None):
            self.__mqtt_client.unsubscribe(self.__status_topic)
        self.__status_topic = topic
        if (topic is not None):
            self.__mqtt_client.subscribe(topic)

    def set_command_topic(self, topic):
        self.__command_topic = topic

    def connect(self, broker, port):
        self.__broker = broker
        self.__port = port
        if (broker is not None and port is not None):
            self.__mqtt_client.connect(broker, port)

    def loop_forever(self):
        while True:
            if (self.__broker is None or self.__port is None):
                sleep(0.5)
                continue
            if (not self.__mqtt_client.is_connected()):
                self.__mqtt_client.reconnect()
                if (not self.__mqtt_client.is_connected()):
                    sleep(1)
                    continue
            self.__mqtt_client.loop(timeout=10)

    def send_command(self, command_json):
        if (self.__command_topic is None):
            return
        command_str = json.dumps(command_json)
        self.__mqtt_client.publish(self.__command_topic, command_str)

    def on_connect(self, client, userdata, flags, rc):
        print('[MqttDevice] %s connected to broker' % self.__name)

    def on_status_message(self, status_json):
        raise NotImplementedError()

    def __on_message(self, client, userdata, msg):
        print('[MqttDevice] Received message from broker: %s' % msg.payload)
        if (msg.topic == self.__status_topic):
            payload_json = json.loads(msg.payload)
            self.on_status_message(payload_json)
