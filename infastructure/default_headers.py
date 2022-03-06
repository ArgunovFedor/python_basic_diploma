import os

from infastructure.singleton import Singleton

rad_api_host = os.environ.get('x-rapidapi-host')
rad_api_key = os.environ.get('x-rapidapi-key')


class DefaultHeaders(Singleton):
    def __init__(self):
        self.__get_headers = {
            'x-rapidapi-host': rad_api_host,
            'x-rapidapi-key': rad_api_key
        }

    @property
    def get_headers(self):
        return self.__get_headers
