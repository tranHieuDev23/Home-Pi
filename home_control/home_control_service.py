import requests
import json

TOKEN_FILE = 'token.txt'
HOME_CONTROL_API = 'https://1ecea3c289c9.ngrok.io'


def __get_token__():
    try:
        with open(TOKEN_FILE) as token_file:
            token = token_file.readline()
            token = token.strip()
            if (token.endswith('\n')):
                token = token[:-1]
            return token
    except Exception as e:
        print('Exception happened while reading token file: %s' % str(e))
        return None


def set_token(token):
    try:
        with open(TOKEN_FILE, 'w') as token_file:
            token_file.write(token)
    except Exception as e:
        print('Exception happened while writting token file: %s' % str(e))


def __send_request__(endpoint, request_json):
    token = __get_token__()
    if (token is None):
        return None
    request_json['token'] = token
    response = requests.post(HOME_CONTROL_API + endpoint, json=request_json)
    if (response.status_code != 200):
        return None
    try:
        response_json = json.loads(response.content.strip())
        if ('newToken' in response_json):
            new_token = response_json['newToken']
            set_token(new_token)
        return response_json
    except Exception as e:
        print('Exception happened while parsing response: %s' % str(e))
        return None


def validate_token():
    return __send_request__('/api/home-control/validate-commander', dict()) is not None


def issue_command(device_name, command, params=dict()):
    request_json = dict()
    request_json['device_name'] = device_name
    request_json['command'] = command
    request_json['params'] = params
    response_json = __send_request__(
        '/api/home-control/issue-command', request_json)
    if (response_json is None):
        return False
    return True


def get_status(device_name):
    request_json = dict()
    request_json['device_name'] = device_name
    response_json = __send_request__(
        '/api/home-control/get-status', request_json)
    if (response_json is None or 'status' not in response_json):
        return None
    return response_json['status']
