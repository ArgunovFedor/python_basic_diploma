import json
from infastructure.singleton import Singleton


class HotelsUrlsOptions(Singleton):
    def __init__(self):
        with open('appsettings.json', 'r') as file:
            self.__hotels_urls = json.loads(file.read())['hotels_urls']

    @property
    def hotels_urls(self):
        return self.__hotels_urls