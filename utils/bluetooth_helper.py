from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, advertise_service, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE
import json
import os

BLUETOOTH_READ_BUFFER = 1024


def __handle_client(client_sock, on_message):
    try:
        while True:
            message_bytes = client_sock.recv(BLUETOOTH_READ_BUFFER)
            message_str = message_bytes.decode('uft-8').strip()
            message_json = dict()
            try:
                message_json = json.loads(message_str)
            except:
                print('Malformed JSON message: %s' % message_str)
                continue
            print('Received JSON message: %s' % str(message_json))
            on_message(client_sock, message_json)
    except:
        return


def bluetooth_loop(on_message):
    os.system('sudo hciconfig hciX piscan')
    while True:
        server_sock = BluetoothSocket(RFCOMM)
        server_sock.bind(("", PORT_ANY))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]
        uuid = "815425a5-bfac-47bf-9321-c5ff980b5e11"
        advertise_service(server_sock, "RPi Wifi config",
                          service_id=uuid,
                          service_classes=[uuid, SERIAL_PORT_CLASS],
                          profiles=[SERIAL_PORT_PROFILE])
        print("Waiting for connection on RFCOMM channel %d" % port)
        client_sock, client_info = server_sock.accept()
        print("Bluetooth connected to", client_info)
        __handle_client(client_sock, on_message)
        client_sock.close()
        server_sock.close()
        print('Bluetooth disconnected from', client_info)
