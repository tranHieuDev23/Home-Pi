from home_control.device_database import DeviceDatabase
from os import path, mkdir
from whoosh.index import create_in, open_dir
from whoosh.fields import *
from whoosh.query import *
from threading import Thread

DEVICE_INDEX_DIR = 'device_index'


class DeviceManager:
    def __init__(self):
        self.__database = DeviceDatabase()
        self.__database.initialize()
        self.devices = self.__database.get_all_devices()

        if (not path.isdir(DEVICE_INDEX_DIR)):
            mkdir(DEVICE_INDEX_DIR)
            schema = Schema(
                id=TEXT(stored=True),
                name=TEXT(stored=True),
                type=TEXT(stored=True),
                location_name=TEXT(stored=True),
                location_type=TEXT(stored=True)
            )
            self.index = create_in(DEVICE_INDEX_DIR, schema)
        else:
            self.index = open_dir(DEVICE_INDEX_DIR)

        self.device_processes = []

    def add_device(self, device):
        self.__database.add_device(device)
        self.devices.append(device)
        writer = self.index.writer()
        writer.add_document(
            id=device.get_id(),
            name=device.get_name(),
            type=device.get_type().name,
            location_name=device.get_location().name,
            location_type=device.get_location().type.name
        )
        writer.commit()
        new_process = Thread(target=device.loop_forever)
        new_process.daemon = True
        new_process.start()
        self.device_processes.append(new_process)

    def remove_device(self, device):
        self.__database.delete_device(device)
        device_id = self.__get_device_id(device)
        if (device_id == None):
            return

        self.devices = self.devices[:device_id] + self.devices[device_id + 1:]

        writer = self.index.writer()
        writer.delete_by_term('id', device.get_id())
        writer.commit()

        self.device_processes = self.device_processes[:device_id] + \
            self.device_processes[device_id + 1:]

    def search_device(self, query):
        parsed_query = self.__parse_query(query)
        results = []
        with self.index.searcher() as searcher:
            doc_results = searcher.search(parsed_query)
            results = [self.__get_device(item['id']) for item in doc_results]
        return results

    def __parse_query(self, query):
        terms = []
        if ('id' in query):
            terms.append(Term('id', query['id']))
        if ('name' in query):
            terms.append(Term('name', query['name']))
        if ('type' in query):
            terms.append(Term('type', query['type']))
        if ('location_name' in query):
            terms.append(Term('location_name', query['location_name']))
        if ('location_type' in query):
            terms.append(Term('location_type', query['location_type']))
        parsed_query = And(terms)
        return parsed_query

    def __get_device(self, id):
        for item in self.devices:
            if (item.get_id() == id):
                return item
        return None

    def __get_device_id(self, device):
        for i in range(len(self.devices)):
            item = self.devices[i]
            if (item.get_id() == device.get_id()):
                return i
        return None
