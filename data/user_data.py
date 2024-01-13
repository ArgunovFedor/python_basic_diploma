import os

from loguru import logger

from infastructure.singleton import Singleton

@logger.catch
def init_dict_from_history_log():
    """
    Метод смотрит логи истории и из него берет id пользователей.
    Если новый пользователь не сделал хотя бы одного успешного запроса, то его не сохраняем в логах истории.
    :return:
    """
    new_dict = dict()
    if os.path.isfile('history.log'):
        with open('history.log', mode='r', encoding='utf-8') as file:
            data = file.readlines()
            for string in data:
                time, message_with_id = string.split('%')
                user_id, items = message_with_id.split('🧐')
                new_dict[user_id] = str(user_id)
    return new_dict


class UserData(Singleton):
    """
    Базовый класс UserData

    Args:
        user_dict (dict): словарь, хранящий данные пользователей
    """

    def __init__(self):
        self.__users = init_dict_from_history_log()

    @property
    def users(self):
        return self.__users

    @users.setter
    def users(self, data):
        self.__users = data

    def create_user(self, id: int) -> None:
        self.__users[id] = id

    def get_user_value_by_id(self, id: int) -> dict:
        return self.__users[id]

    def delete_user(self, id: int) -> None:
        self.__users.pop(id)
