import json
from infastructure.singleton import Singleton


class MetaDateOptions(Singleton):
    def __init__(self):
        with open('appsettings.json', 'r') as file:
            self.__meta_date = json.loads(file.read())['meta_data'][0]

    @property
    def meta_date(self):
        return self.__meta_date