from time import sleep
from .device import Device
import paho.mqtt.client as mqtt


class MqttDevice(Device):
    def __init__(self, id, name, type, location):
        super().__init__(id, name, type, location)
        self.__mqtt_client = mqtt.Client()
        self.__broker = None
        self.__port = None
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.on_message

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

    def on_connect(self, client, userdata, flags, rc):
        print('[MqttDevice] Connected to broker')

    def on_message(self, client, userdata, msg):
        print('[MqttDevice] Received message from broker: %s' % msg.payload)
