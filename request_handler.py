import device_helpers


def get_request_handler(device_id):
    device_handler = device_helpers.DeviceRequestHandler(device_id)

    @device_handler.command('action.devices.commands.OnOff')
    def onoff(on):
        pass

    @device_handler.command('com.example.commands.BlinkLight')
    def blink(speed, number):
        pass

    return device_handler
