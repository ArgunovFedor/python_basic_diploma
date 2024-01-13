import functools

from decouple import config

import re
from typing import Callable, List

from loguru import logger
from telebot import types, TeleBot
from telebot.types import InputMediaPhoto
from telegram_bot_calendar import DetailedTelegramCalendar

from botrequests.bestdeal import get_bestdeal_hotels
from botrequests.highprice import get_highprice_hotels
from botrequests.lowprice import get_lowprice_hotels
from data.user_data import UserData
from exceptions.api_exception import ApiException
from infastructure.calendar_list_step import StepList
from infastructure.meta_date_options import MetaDateOptions
from models.request_param_model import RequestParamModel

token = config('TOKEN')
bot = TeleBot(token)

logger.level(name='HISTORY', no=1, color=None, icon=None)
logger.add('debug.log', filter=lambda record: record['level'].name == 'DEBUG',
           retention='10 days')
logger.add('info.log', filter=lambda record: record['level'].name == 'INFO',
           retention='10 days')
logger.add('error.log', filter=lambda record: record['level'].name == 'ERROR', rotation='5 MB',
           retention='10 days')
logger.add('history.log', filter=lambda record: record['level'].name == 'HISTORY',
           format='{time:DD:MM:YYYY HH:mm:ss}%{message}',
           level='HISTORY', retention="10 days")


@logger.catch
def user_data_decorator(func: Callable):
    user_data = UserData()
    # мы сохраняем данные запроса пользователя
    # для этого логгируем результат этой функции
    last_step_func_name = 'result_handler'

    def wrapped(*args, **kwargs):
        # есть несколько методов и параметры этих методов порой друг от друга отличаются
        # поэтому message может быть в args или kwargs, если message отсутствует, то мы пропускаем этот метод
        if len(args) > 0:
            message = args[0]
        elif 'message' in kwargs.keys():
            message = kwargs['message']
        else:
            return func(*args, **kwargs)
        if hasattr(message.from_user, 'is_bot') and message.from_user.is_bot is True:
            current_user_id = str(message.chat.id)
        else:
            current_user_id = str(message.from_user.id)

        if current_user_id not in user_data.users.values():
            logger.log('INFO', ''.join(['В систему зашёл новый пользователь с ID:', str(current_user_id)]))
            user_data.create_user(current_user_id)
        else:
            logger.log('INFO',
                       ' '.join(['Пользователь c ID:', str(current_user_id), 'вызвал функцию:', func.__name__,
                                 'с текстом', message.text]))
        result = func(*args, **kwargs)

        if result is not None and func.__name__ == last_step_func_name:
            # записываем результат запроса в лог в файл history
            logger.log('HISTORY', '🧐'.join([str(message.from_user.id), '😎'.join(
                ['*'.join(
                    ['Название:' + hotel.name, 'Адрес:' + hotel.address, 'Цена:' + hotel.price, 'URL:' + hotel.url]) for
                    hotel in result])]))

        return result

    return wrapped


@logger.catch
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


@logger.catch
@user_data_decorator
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def callback_worker(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {StepList().step_list[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        request_param: RequestParamModel = DetailedTelegramCalendar.request_param
        request_param.check_in = result
        bot.edit_message_text(f'Выбрана дата: {result}', call.message.chat.id, call.message.message_id,
                              reply_markup=None)
        get_check_out(message=call.message, request_param=DetailedTelegramCalendar.request_param)


@logger.catch
@user_data_decorator
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def callback_worker(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {StepList().step_list[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        request_param: RequestParamModel = DetailedTelegramCalendar.request_param
        request_param.check_out = result
        bot.edit_message_text(f'Выбрана дата: {result}', call.message.chat.id, call.message.message_id,
                              reply_markup=None)
        call.message.chat, call.message.from_user = call.message.from_user, call.message.chat
        result_handler(message=call.message, request_param=request_param)



@logger.catch
@user_data_decorator
@bot.callback_query_handler(func=lambda call: call.data in ['/highprice', '/bestdeal', '/history', '/lowprice'])
def callback_worker(call):
    initial_step(message=call.message, command=call.data, from_user_id=call.from_user.id, is_from_call=True)


@logger.catch
@user_data_decorator
def initial_step(message, command: str, from_user_id: int, is_from_call=False):
    if command == "/highprice":
        choose_chain(message=message, command=command, from_user_id=from_user_id, is_from_call=is_from_call,
                     text='Дорогие отели 👌')
    elif command == "/bestdeal":
        choose_chain(message=message, command=command, from_user_id=from_user_id, is_from_call=is_from_call,
                     text='С фильтром 👌', is_detailed_survey=True)
    elif command == "/lowprice":
        choose_chain(message=message, command=command, from_user_id=from_user_id, is_from_call=is_from_call,
                     text='Дешевые отели 👌')
    else:
        get_history(message=message, is_from_call=is_from_call)


@logger.catch
@user_data_decorator
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


@logger.catch
@user_data_decorator
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


@logger.catch
@user_data_decorator
def get_city(message, request_param: RequestParamModel = None):
    request_param.city = message.text
    request_param.previous_step = get_city, message.text
    if request_param.is_detailed_survey:
        bot.send_message(message.from_user.id, 'Введите диапазон цен через дефис рублях. Например, 0-10000:')
        bot.register_next_step_handler(message, get_range_price, request_param)
    else:
        bot.send_message(message.from_user.id, 'Количество отелей, которые необходимо вывести в результате:')
        bot.register_next_step_handler(message, get_hotels_count, request_param)


@logger.catch
@validator_with_regex(r'\d+-\d+$', 'К сожалению, вы ввели неправильный диапазон цифр. Попробуйте заново')
@user_data_decorator
def get_range_price(message, request_param: RequestParamModel = None):
    request_param.previous_step = get_range_price, message.text
    request_param.price_range = message.text.split('-')
    bot.send_message(message.from_user.id,
                     'Максимальное расстояние от центра км. Например, 3:')
    bot.register_next_step_handler(message, range_of_distance, request_param)


@logger.catch
@validator_with_regex(r'\b\d+$', 'К сожалению, вы ввели неправильное число. Попробуйте заново')
@user_data_decorator
def range_of_distance(message, request_param: RequestParamModel = None):
    request_param.previous_step = range_of_distance, message.text
    request_param.max_distance = int(message.text)
    bot.send_message(message.from_user.id, 'Количество отелей, которые необходимо вывести в результате:')
    bot.register_next_step_handler(message, get_hotels_count, request_param)


@logger.catch
@validator_with_regex(r'\b\d+$', 'К сожалению, вы ввели неправильный диапазон цифр. Попробуйте заново')
@user_data_decorator
def get_hotels_count(message, request_param: RequestParamModel = None):
    request_param.previous_step = get_hotels_count, message.text
    request_param.hotels_count = message.text
    bot.send_message(message.from_user.id, 'Необходимость загрузки и вывода фотографий для каждого отеля (“Да/Нет”):')
    bot.register_next_step_handler(message, get_with_photos, request_param)


@logger.catch
@user_data_decorator
def get_with_photos(message, request_param: RequestParamModel = None):
    request_param.previous_step = get_with_photos, message.text
    if message.text.lower() == 'да':
        request_param.is_with_photos = True
        bot.send_message(message.from_user.id, 'Введите количество фотографий:')
        bot.register_next_step_handler(message, get_photos_count, request_param)
    else:
        request_param.is_with_photos = False
        get_check_in(message, request_param)


@logger.catch
@validator_with_regex(r'\b\d+$', 'Введите число. Попробуйте заново')
@user_data_decorator
def get_photos_count(message, request_param: RequestParamModel):
    request_param.previous_step = get_photos_count, message.text
    request_param.photos_count = message.text
    get_check_in(message, request_param)


@logger.catch
@user_data_decorator
def get_check_in(message, request_param: RequestParamModel):
    request_param.previous_step = get_check_in, message.text
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale='ru').build()
    DetailedTelegramCalendar.request_param = request_param
    bot.send_message(message.from_user.id,
                     'Выберите дату заезда:',
                     reply_markup=calendar)


@logger.catch
@user_data_decorator
def get_check_out(message, request_param: RequestParamModel):
    request_param.previous_step = get_check_out, message.text
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru').build()
    DetailedTelegramCalendar.request_param = request_param
    bot.send_message(message.chat.id,
                     'Выберите дату выезда:',
                      reply_markup=calendar)


@logger.catch
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
            if hotel.photos_urls is not None:
                bot.send_media_group(message.from_user.id,
                                     [InputMediaPhoto(photo_url) for photo_url in hotel.photos_urls])
            bot.send_message(message.from_user.id, hotel, disable_web_page_preview=True)
        return result
    except ApiException as exception:
        error_code, description = exception.args[0].split(':')
        if error_code == 'EMPTY':
            bot.send_message(message.from_user.id, description)
        elif error_code == 'SEARCH':
            bot.send_message(message.from_user.id, description)
    except Exception as exception:
        error_code, description = exception.args[0].split(':')
        logger.log('ERROR', ' '.join([error_code, description]))
        bot.send_message(message.from_user.id, 'Извините, но произошла внутренняя ошибка')
    finally:
        start(message)


@bot.message_handler(content_types=['text'])
@logger.catch
@user_data_decorator
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


@logger.catch
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