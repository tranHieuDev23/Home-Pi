from enum import Enum


class DeviceType(Enum):
    LIGHT = 1
    THERMOSTAT = 2


class Device:
    def __init__(self, id, name, type, location):
        self.__id = id
        self.__name = name
        self.__type = type
        self.__location = location
        self.__fields = dict()

    def get_id(self):
        return self.__id

    def get_name(self):
        return self.__name

    def get_type(self):
        return self.__type

    def get_location(self):
        return self.__location

    def get_field(self, field):
        if (field not in self.__fields):
            return None
        return self.__fields[field]

    def set_field(self, field, value):
        self.__fields[field] = value

    def handle_command(self, command):
        pass
