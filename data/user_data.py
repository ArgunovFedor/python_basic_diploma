class UserData:
    """
    Базовый класс UserData

    Args:
        user_dict (dict): словарь, хранящий данные пользователей
    """
    def __init__(self, user_dict: dict = None):
        self.__users = user_dict

    @property
    def users(self):
        return self.__users

    @users.setter
    def users(self, data):
        self.__users = data

    def create_user(self, message) -> None:
        self.__users[message.from_user.id] = [message.text]

    def update_user(self, message) -> None:
        self.__users[message.from_user.id].append(message.text)

    def get_user_value_by_id(self, id: int) -> dict:
        return self.__users[id]

    def delete_user(self, id: int) -> None:
        self.__users.pop(id)