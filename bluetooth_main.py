if __name__ == '__main__':
    from utils.bluetooth_helper import BluetoothInstance
    from bluetooth_request_handler import on_message_factory

    BluetoothInstance(on_message_factory('speaker:12345')).run()
