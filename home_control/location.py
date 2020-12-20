from enum import Enum


class LocationType(Enum):
    LIVING_ROOM = 1
    KITCHEN = 2
    BATHROOM = 3
    BEDROOM = 4


class Location:
    def __init__(self, name, type):
        self.name = name
        self.type = type
