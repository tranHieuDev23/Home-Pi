from home_control.location import Location, LocationType
from home_control.device import DeviceType
import sqlite3
from .mqtt_light import MqttLight


class MqttDeviceFactory:
    def __init__(self):
        pass

    def create_device(self, id, name, type, location):
        if (type == DeviceType.LIGHT.name):
            return self.create_light(id, name, location)

    def create_light(self, id, name, location):
        return MqttLight(id, name, location)


class DeviceDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('device_database.db')
        self.factory = MqttDeviceFactory()

    def initialize(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS devices(
                id text,
                name text,
                type text,
                location_name text,
                location_type text,
                status_topic text,
                command_topic text
            );
        ''')
        self.conn.commit()

    def get_all_devices(self):
        results = []
        cursor = self.conn.execute('''
            SELECT * FROM devices;
        ''')
        for row in cursor:
            id = row[0]
            name = row[1]
            type = row[2]
            location_name = row[3]
            location_type = row[4]
            status_topic = row[5]
            command_topic = row[6]
            location = Location(location_name, LocationType[location_type])
            device = self.factory.create_device(id, name, type, location)
            device.set_status_topic(status_topic)
            device.set_command_topic(command_topic)
            results.append(device)
        return results

    def add_device(self, device):
        self.conn.execute('''
            INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?);
        ''', (
            device.get_id(),
            device.get_name(),
            device.get_type().name,
            device.get_location().name,
            device.get_location().type.name,
            device.get_status_topic(),
            device.get_command_topic()
        ))
        self.conn.commit()

    def delete_device(self, device):
        self.conn.execute('''
            DELETE FROM devices WHERE id = ?;
        ''', (device.get_id(),))
        self.conn.commit()
