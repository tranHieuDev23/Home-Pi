from home_control.device_manager import DeviceManager
from home_control.mqtt_light import MqttLight
from home_control.location import Location, LocationType

manager = DeviceManager()
light = MqttLight(str(len(manager.devices)), "Desk light", Location(
    "My bed room", LocationType.BEDROOM))
manager.add_device(light)

print(manager.search_device({
    'name': 'light'
}))
