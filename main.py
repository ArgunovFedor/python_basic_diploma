import functools
from decouple import config

import re
from typing import Callable, List

from loguru import logger
from telebot import types, TeleBot

from botrequests.bestdeal import get_bestdeal_hotels
from botrequests.highprice import get_highprice_hotels
from botrequests.lowprice import get_lowprice_hotels
from data.user_data import UserData
from exceptions.api_exception import ApiException
from infastructure.meta_date_options import MetaDateOptions
from models.hotel_result_model import HotelResultModel
from models.request_param_model import RequestParamModel

token = config('TOKEN')
bot = TeleBot(token, parse_mode=None)

logger.level(name='HISTORY', no=1, color=None, icon=None)
logger.add("debug.log", filter=lambda record: record["level"].name == "DEBUG",
           retention="10 days")
logger.add("info.log", filter=lambda record: record["level"].name == "INFO",
           retention="10 days")
logger.add("error.log", filter=lambda record: record["level"].name == "ERROR", rotation='5 MB',
           retention="10 days")
logger.add("history.log", filter=lambda record: record["level"].name == "HISTORY", format='{time:DD:MM:YYYY HH:mm:ss}%{message}',
           level='HISTORY', retention="10 days")


def user_data_decorator(func: Callable):
    user_data = UserData(dict())

    def wrapped(*args, **kwargs):
        result: List[HotelResultModel] = func(*args, **kwargs)
        message = args[0]
        if message.from_user.id not in user_data.users.keys():
            user_data.create_user(message)
        if result is not None:
            logger.log('HISTORY', '🧐'.join([str(message.from_user.id), '😎'.join(
                ['*'.join(['Название:' + hotel.name, 'Адрес:' + hotel.address, 'Цена:' + hotel.price, 'URL:' + hotel.url]) for hotel in result])]))

        return result

    return wrapped


def validator_with_regex(pattern: str, error_message: str):
    def validator_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = args[0]
            request_param: RequestParamModel = args[1]
            is_acceptable = re.match(pattern, message.text)
            if is_acceptable is None:
                logger.error('VALIDATION. Ошибка валидации')
                bot.send_message(message.from_user.id, error_message)
                message.text = request_param.previous_step[1]
                return request_param.previous_step[0](message, request_param)
            else:
                result = func(*args, **kwargs)
                return result

        return wrapper

    return validator_decorator


@bot.callback_query_handler(func=lambda call: call.data in ['/highprice', '/bestdeal', '/history', '/lowprice'])
def callback_worker(call):
    initial_step(message=call.message, command=call.data, from_user_id=call.from_user.id, is_from_call=True)


def initial_step(message, command: str, from_user_id: int, is_from_call=False):
    if command == "/highprice":
        choose_chain(message=message, command=command, from_user_id=from_user_id, is_from_call=is_from_call,
                     text='Дорогие отели 👌')
    elif command == "/bestdeal":
        choose_chain(message=message, command=command, from_user_id=from_user_id, is_from_call=is_from_call,
                     text='С фильтром 👌', is_detailed_survey=True)
    elif command == "/lowprice":
        choose_chain(message=message, command=command, from_user_id=from_user_id, is_from_call=is_from_call, text='Дешевые отели 👌')
    else:
        get_history(message=message, is_from_call=is_from_call)


def get_history(message, is_from_call: bool = False, text: str = 'История 👌'):
    try:
        # Удаляет клавиатуру выбора
        if is_from_call:
            bot.edit_message_text(text=text, message_id=message.message_id, chat_id=message.chat.id,
                                  reply_markup=None)
        with open('history.log', mode='r', encoding='utf-8') as file:
            data = file.readlines()
            counter = 0
            for string in data:
                time, message_with_id = string.split('%')
                user_id, items = message_with_id.split('🧐')
                items = [item.replace('*', '\n') for item in items.split('😎')]
                if int(user_id) == message.chat.id:
                    counter += 1
                    bot.send_message(message.chat.id, ' '.join([str(counter), 'запрос:']))
                    bot.send_message(message.chat.id, 'Время: ' + time)
                    bot.send_message(message.chat.id, '\n'.join(items), disable_web_page_preview=True)
        return True
    finally:
        bot.send_message(message.chat.id, '/help')


def choose_chain(message: types.Message, from_user_id: int, command: str, is_from_call: bool, text,
                 is_detailed_survey: bool = False):
    # Удаляет клавиатуру выбора
    if is_from_call:
        bot.edit_message_text(text=text, message_id=message.message_id, chat_id=message.chat.id,
                              reply_markup=None)
    bot.send_message(from_user_id, 'Введите город, где будет проводиться поиск:')
    request_param = RequestParamModel(is_detailed_survey=is_detailed_survey, command=command)
    request_param.previous_step = choose_chain, message.text
    bot.register_next_step_handler(message, get_city, request_param)


def get_city(message, request_param: RequestParamModel = None):
    request_param.city = message.text
    request_param.previous_step = get_city, message.text
    if request_param.is_detailed_survey:
        bot.send_message(message.from_user.id, 'Введите диапазон цен через дефис рублях. Например, 0-10000:')
        bot.register_next_step_handler(message, get_range_price, request_param)
    else:
        bot.send_message(message.from_user.id, 'Количество отелей, которые необходимо вывести в результате:')
        bot.register_next_step_handler(message, get_hotels_count, request_param)


@validator_with_regex(r'\d+-\d+$', 'К сожалению, вы ввели неправильный диапазон цифр. Попробуйте заново')
def get_range_price(message, request_param: RequestParamModel = None):
    request_param.previous_step = get_range_price, message.text
    request_param.price_range = message.text.split('-')
    bot.send_message(message.from_user.id,
                     'Максимальное расстояние от центра км. Например, 3:')
    bot.register_next_step_handler(message, range_of_distance, request_param)


@validator_with_regex(r'\b\d+$', 'К сожалению, вы ввели неправильное число. Попробуйте заново')
def range_of_distance(message, request_param: RequestParamModel = None):
    request_param.previous_step = range_of_distance, message.text
    request_param.max_distance = int(message.text)
    bot.send_message(message.from_user.id, 'Количество отелей, которые необходимо вывести в результате:')
    bot.register_next_step_handler(message, get_hotels_count, request_param)


@validator_with_regex(r'\b\d+$', 'К сожалению, вы ввели неправильный диапазон цифр. Попробуйте заново')
def get_hotels_count(message, request_param: RequestParamModel = None):
    request_param.previous_step = get_hotels_count, message.text
    request_param.hotels_count = message.text
    bot.send_message(message.from_user.id, 'Необходимость загрузки и вывода фотографий для каждого отеля (“Да/Нет”):')
    bot.register_next_step_handler(message, get_with_photos, request_param)


def get_with_photos(message, request_param: RequestParamModel = None):
    request_param.previous_step = get_with_photos, message.text
    if message.text.lower() == 'да':
        request_param.is_with_photos = True
        bot.send_message(message.from_user.id, 'Введите количество фотографий:')
        bot.register_next_step_handler(message, get_photos_count, request_param)
    else:
        request_param.is_with_photos = False
        result_handler(message, request_param)


@validator_with_regex(r'\b\d+$', 'Введите число. Попробуйте заново')
def get_photos_count(message, request_param: RequestParamModel):
    request_param.previous_step = get_photos_count, message.text
    request_param.photos_count = message.text
    result_handler(message, request_param)


@user_data_decorator
def result_handler(message, request_param: RequestParamModel = None) -> List:
    try:
        bot.send_message(message.from_user.id, 'Это может занять какое-то время. Пожалуйста подождите немного 👌')
        if request_param.command == '/lowprice':
            result = get_lowprice_hotels(request_param_model=request_param, meta_date=MetaDateOptions().meta_date)
        elif request_param.command == '/highprice':
            result = get_highprice_hotels(request_param_model=request_param, meta_date=MetaDateOptions().meta_date)
        elif request_param.command == '/bestdeal':
            result = get_bestdeal_hotels(request_param_model=request_param, meta_date=MetaDateOptions().meta_date)
        for hotel in result:
            bot.send_message(message.from_user.id, hotel, disable_web_page_preview=True)
            if hotel.photos_urls is not None:
                for photos_url in hotel.photos_urls:
                    bot.send_photo(message.from_user.id, photos_url)
        return result
    except ApiException as exception:
        error_code, description = exception.args[0].split(':')
        if error_code == 'EMPTY':
            bot.send_message(message.from_user.id, description)
        elif error_code == 'SEARCH':
            bot.send_message(message.from_user.id, description)
    except Exception:
        bot.send_message(message.from_user.id, 'Извините, но произошла внутренняя ошибка')
    finally:
        start(message)


@bot.message_handler(content_types=['text'])
@logger.catch
def start(message):
    if message.text == '/hello_world':
        bot.send_message(message.from_user.id, "Привет мир")
    elif message.text in ['/highprice', '/bestdeal', '/lowprice']:
        initial_step(message=message, command=message.text, from_user_id=message.from_user.id)
    elif message.text == '/history':
        get_history(message=message)
    else:
        keyboard = generate_main_keyboard()
        bot.send_message(message.from_user.id, text='Выберите одно 👇:', reply_markup=keyboard)


def generate_main_keyboard():
    # клавиатура
    keyboard = types.InlineKeyboardMarkup(row_width=2)  # наша клавиатура
    key_low_price = types.InlineKeyboardButton(text='Дешевые отели', callback_data='/lowprice')
    keyboard.add(key_low_price)  # добавляем кнопку в клавиатуру
    key_hight_price = types.InlineKeyboardButton(text='Дорогие отели', callback_data='/highprice')
    keyboard.add(key_hight_price)
    key_best_deal = types.InlineKeyboardButton(text='С фильтром', callback_data='/bestdeal')
    keyboard.add(key_best_deal)
    key_history = types.InlineKeyboardButton(text='История', callback_data='/history')
    keyboard.add(key_history)
    return keyboard


bot.polling(none_stop=True, interval=0)
