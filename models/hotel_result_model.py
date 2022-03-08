from typing import List, Dict

from infastructure.hotels_urls_options import HotelsUrlsOptions


class HotelResultModel:
    def __init__(self):
        self.__photos_urls = None
        self.__price = None
        self.__address = None
        self.__name = None
        self.__hotel_id = None
        self.__distance = None
        self.__url = None

    @property
    def url(self):
        return HotelsUrlsOptions().hotels_urls['url_path_to_the_hotel_page'].format(id=self.__hotel_id)


    @property
    def hotel_id(self):
        return self.__hotel_id

    @hotel_id.setter
    def hotel_id(self, hotel_id: str):
        self.__hotel_id = hotel_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    @property
    def address(self):
        return self.__address

    @address.setter
    def address(self, address: Dict):
        self.__address = '{countryName}, {locality}, {streetAddress}'.format(
            countryName=address['countryName'],
            locality=address['locality'],
            streetAddress=address['streetAddress']
        )

    @property
    def price(self):
        return self.__price

    @price.setter
    def price(self, price: str):
        self.__price = price

    @property
    def photos_urls(self):
        return self.__photos_urls

    @photos_urls.setter
    def photos_urls(self, photos_urls: List):
        self.__photos_urls = photos_urls

    @property
    def distance(self):
        return self.__distance

    @distance.setter
    def distance(self, distance: str):
        self.__distance = distance
