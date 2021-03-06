import json
from utils.wifi_helper import discover_wifi, wifi_connect, is_wifi_connected
from home_control.home_control_service import validate_token, set_token


def on_message_factory(device_id):
    def __send_message(client_sock, message_str):
        client_sock.send(message_str + '\n')

    def __get_base_response(success):
        response = dict()
        response['success'] = success
        return response

    def __get_failure_response_str():
        return json.dumps(__get_base_response(False))

    def __get_device_id(client_sock):
        response = __get_base_response(True)
        response['deviceId'] = device_id
        __send_message(client_sock, json.dumps(response))

    def __get_wifi_status(client_sock):
        response = __get_base_response(True)
        response['connected'] = is_wifi_connected()
        __send_message(client_sock, json.dumps(response))

    def __scan_wifi(client_sock):
        response = __get_base_response(True)
        response['networks'] = discover_wifi()
        __send_message(client_sock, json.dumps(response))

    def __connect_wifi(client_sock, message_json):
        if ('ssid' not in message_json or 'psk' not in message_json):
            __send_message(client_sock, __get_failure_response_str())
            return
        ssid = message_json['ssid']
        psk = message_json['psk']
        ip_address = wifi_connect(ssid, psk)
        if (ip_address is None):
            __send_message(client_sock, __get_failure_response_str())
            return
        response = __get_base_response(True)
        __send_message(client_sock, json.dumps(response))

    def __connect_user(client_sock, message_json):
        if ('token' not in message_json):
            __send_message(client_sock, __get_failure_response_str())
            return
        token = message_json['token']
        set_token(token)
        is_valid_token = validate_token()
        response = __get_base_response(is_valid_token)
        __send_message(client_sock, json.dumps(response))

    def on_message(client_sock, message_json):
        if ('action' not in message_json):
            __send_message(client_sock, json.dumps(
                __get_failure_response_str()))
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
        __send_message(client_sock, json.dumps(__get_failure_response_str()))

    return on_message
