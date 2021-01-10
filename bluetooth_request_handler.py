import json
from utils.wifi_helper import discover_ssid, wifi_connect


def on_message_factory(device_id):
    def __get_base_response(reqId, success):
        response = dict()
        response['reqId'] = reqId
        response['success'] = success
        return response

    def __get_failure_response_str(reqId):
        return json.dumps(__get_base_response(reqId, False))

    def __get_device_id(client_sock, reqId):
        response = __get_base_response(reqId, True)
        response['deviceId'] = device_id
        client_sock.send(json.dumps(response))

    def __list_wifi(client_sock, reqId):
        response = __get_base_response(reqId, True)
        response['ssids'] = discover_ssid()
        client_sock.send(json.dumps(response))

    def __connect_wifi(client_sock, reqId, message_json):
        if ('ssid' not in message_json or 'psk' not in message_json):
            client_sock.send(__get_failure_response_str())
        ssid = message_json['ssid']
        psk = message_json['psk']
        ip_address = wifi_connect(ssid, psk)
        if (ip_address is None):
            client_sock.send(__get_failure_response_str())
            return
        response = __get_base_response(reqId, True)
        response['ipAddress'] = ip_address
        client_sock.send(json.dumps(response))

    def __connect_user(client_sock, reqId, message_json):
        response = __get_base_response(reqId, True)
        client_sock.send(json.dumps(response))

    def on_message(client_sock, message_json):
        if ('reqId' not in message_json):
            return
        reqId = message_json['reqId']
        if ('action' not in message_json):
            client_sock.send(json.dumps(__get_failure_response_str(reqId)))
            return
        action = message_json['action']
        if (action == 'getId'):
            __get_device_id(client_sock, reqId)
            return
        if (action == 'listWifi'):
            __list_wifi(client_sock, reqId)
            return
        if (action == 'connectWifi'):
            __connect_wifi(client_sock, reqId)
            return
        if (action == 'connectUser'):
            __connect_user(client_sock, reqId)
            return
        client_sock.send(json.dumps(__get_failure_response_str(reqId)))

    return on_message
