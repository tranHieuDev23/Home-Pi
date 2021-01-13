from threading import Thread
from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, advertise_service, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE
import json
import os

BLUETOOTH_READ_BUFFER = 1024


class BluetoothInstance(Thread):
    def __init__(self, on_message):
        super().__init__()
        self.on_message = on_message

    def __handle_client(self, client_sock, on_message):
        try:
            while True:
                message_bytes = client_sock.recv(BLUETOOTH_READ_BUFFER)
                message_str = message_bytes.decode('utf-8').strip()
                message_json = dict()
                try:
                    message_json = json.loads(message_str)
                except:
                    print('Malformed JSON message: %s' % message_str)
                    continue
                print('Received JSON message: %s' % str(message_json))
                on_message(client_sock, message_json)
        except Exception as e:
            print('Exception while reading from client socket: ' + str(e))
            return

    def run(self):
        def bluetooth_loop(on_message):
            os.system('sudo hciconfig hciX piscan')
            while True:
                server_sock = BluetoothSocket(RFCOMM)
                server_sock.bind(("", PORT_ANY))
                server_sock.listen(1)
                port = server_sock.getsockname()[1]
                uuid = "00001101-0000-1000-8000-00805F9B34FB"
                advertise_service(server_sock, "Home Pi Speaker Config",
                                  service_id=uuid,
                                  service_classes=[uuid, SERIAL_PORT_CLASS],
                                  profiles=[SERIAL_PORT_PROFILE])
                print("Waiting for connection on RFCOMM channel %d" % port)
                client_sock, client_info = server_sock.accept()
                print("Bluetooth connected to", client_info)
                self.__handle_client(client_sock, on_message)
                try:
                    client_sock.close()
                except Exception as e:
                    print('Exception while closing client socket: ' + str(e))
                server_sock.close()
                print('Bluetooth disconnected from', client_info)

        bluetooth_loop(self.on_message)
