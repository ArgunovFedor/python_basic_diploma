import json
from infastructure.singleton import Singleton


class StepList(Singleton):
    def __init__(self):
        with open('appsettings.json', 'r', encoding='utf-8') as file:
            self.__step_list = json.loads(file.read())['list_step']

    @property
    def step_list(self):
        return self.__step_list
