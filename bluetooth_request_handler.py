import json
from utils.wifi_helper import discover_wifi, wifi_connect, is_wifi_connected


def on_message_factory(device_id):
    def __get_base_response(success):
        response = dict()
        response['success'] = success
        return response

    def __get_failure_response_str():
        return json.dumps(__get_base_response(False))

    def __get_device_id(client_sock):
        response = __get_base_response(True)
        response['deviceId'] = device_id
        client_sock.send(json.dumps(response))

    def __get_wifi_status(client_sock):
        response = __get_base_response(True)
        response['connected'] = is_wifi_connected()
        client_sock.send(json.dumps(response))

    def __scan_wifi(client_sock):
        response = __get_base_response(True)
        response['networks'] = discover_wifi()
        client_sock.send(json.dumps(response))

    def __connect_wifi(client_sock, message_json):
        if ('ssid' not in message_json or 'psk' not in message_json):
            client_sock.send(__get_failure_response_str())
            return
        ssid = message_json['ssid']
        psk = message_json['psk']
        ip_address = wifi_connect(ssid, psk)
        if (ip_address is None):
            client_sock.send(__get_failure_response_str())
            return
        response = __get_base_response(True)
        client_sock.send(json.dumps(response))

    def __connect_user(client_sock, message_json):
        response = __get_base_response(True)
        client_sock.send(json.dumps(response))

    def on_message(client_sock, message_json):
        if ('action' not in message_json):
            client_sock.send(json.dumps(__get_failure_response_str()))
            return
        action = message_json['action']
        if (action == 'getId'):
            __get_device_id(client_sock)
            return
        if (action == 'wifiStatus'):
            __get_wifi_status(client_sock)
            return
        if (action == 'scanWifi'):
            __scan_wifi(client_sock)
            return
        if (action == 'connectWifi'):
            __connect_wifi(client_sock, message_json)
            return
        if (action == 'register'):
            __connect_user(client_sock, message_json)
            return
        client_sock.send(json.dumps(__get_failure_response_str()))

    return on_message
