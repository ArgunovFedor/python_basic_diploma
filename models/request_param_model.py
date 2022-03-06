from collections import Callable


class RequestParamModel:
    def __init__(self, city: str = None, command: str = None, is_detailed_survey: bool = False):
        self.__is_detailed_survey = is_detailed_survey
        self.__price_range = None
        self.__range_of_distance = None
        self.__photos_count = 0
        self.__is_with_photos = False
        self.__hotels_count = 0
        self.__city = city
        self.__command = command
        self.__previous_step = None

    @property
    def previous_step(self):
        return self.__previous_step

    @previous_step.setter
    def previous_step(self, func: Callable):
        self.__previous_step = func

    @property
    def command(self):
        return self.__command

    @command.setter
    def command(self, command):
        self.__command = command

    @property
    def city(self):
        return self.__city

    @city.setter
    def city(self, city):
        self.__city = city

    @property
    def hotels_count(self):
        return self.__hotels_count

    @hotels_count.setter
    def hotels_count(self, hotels_count):
        self.__hotels_count = hotels_count

    @property
    def is_with_photos(self):
        return self.__is_with_photos

    @is_with_photos.setter
    def is_with_photos(self, is_with_photos):
        self.__is_with_photos = is_with_photos

    @property
    def photos_count(self):
        return self.__photos_count

    @photos_count.setter
    def photos_count(self, photos_count):
        self.__photos_count = photos_count

    @property
    def is_detailed_survey(self):
        return self.__is_detailed_survey

    @is_detailed_survey.setter
    def is_detailed_survey(self, is_detailed_survey):
        self.__is_detailed_survey = is_detailed_survey

    @property
    def price_range(self):
        return self.__price_range

    @price_range.setter
    def price_range(self, price_range):
        self.__price_range = price_range

    @property
    def range_of_distance(self):
        return self.__range_of_distance

    @range_of_distance.setter
    def range_of_distance(self, range_of_distance):
        self.__range_of_distance = range_of_distance
