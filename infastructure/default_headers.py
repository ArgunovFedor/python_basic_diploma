from decouple import config

from infastructure.singleton import Singleton

rad_api_host = config('x-rapidapi-host')
rad_api_key = config('x-rapidapi-key')


class DefaultHeaders(Singleton):
    def __init__(self):
        self.__get_headers = {
            'x-rapidapi-host': rad_api_host,
            'x-rapidapi-key': rad_api_key
        }

    @property
    def get_headers(self):
        return self.__get_headers
