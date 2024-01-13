import json
import typing
from typing import List

import requests

from botrequests.search import get_destinationIds_list
from infastructure.default_headers import DefaultHeaders
from infastructure.hotels_urls_options import HotelsUrlsOptions
from models.hotel_result_model import HotelResultModel
from models.request_param_model import RequestParamModel


def get_hotels_handler(request_param_model: RequestParamModel = None, meta_date: List = None,
                       result_model: typing.Annotated = None) -> List[HotelResultModel]:
    url = HotelsUrlsOptions().hotels_urls['properties_list']
    querystring = {'query': request_param_model.city, 'locale': meta_date['hcomLocale'], "currency": "RUB"}
    destination_ids_list = get_destinationIds_list(querystring, DefaultHeaders().get_headers)
    # 1 - это hotels
    check_in = request_param_model.check_in.strftime('%Y-%m-%d')
    check_out = request_param_model.check_out.strftime('%Y-%m-%d')
    querystring = {
        'destinationId': destination_ids_list[0],
        'pageNumber': '1',
        'pageSize': request_param_model.hotels_count,
        'checkIn': check_in,
        'checkOut': check_out,
        'adults1': '1',
        'sortOrder': request_param_model.sort_order,
        'locale': meta_date['hcomLocale'],
        'currency': meta_date['currency']}
    if request_param_model.price_range is not None:
        querystring['priceMin'] = request_param_model.get_min_price()
        querystring['priceMax'] = request_param_model.get_max_price()
    if request_param_model.sort_order == 'DISTANCE_FROM_LANDMARK':
        # добавляем метку города
        querystring['landmarkIds'] = destination_ids_list[0]
    response = requests.request("GET", url, headers=DefaultHeaders().get_headers, params=querystring)
    hotels_dict = json.loads(response.text)
    result_list = list()
    # если указано с фотографией, то доп фотографии должны вывести
    for hotel in hotels_dict['data']['body']['searchResults']['results']:
        # готовим ответ
        hotel_result = result_model()
        hotel_result.hotel_id = hotel['id']
        hotel_result.name = hotel['name']
        hotel_result.address = hotel['address']
        hotel_result.price = hotel['ratePlan']['price']['current']
        hotel_result.distance = hotel['landmarks'][0]['distance']
        # делаем запрос за коллекцией фотографий
        if request_param_model.is_with_photos:
            get_photos_urls(hotel, hotel_result, request_param_model)
        # добавляем в основной результирующий лист
        result_list.append(hotel_result)
    return result_list


def get_photos_urls(hotel: List = None, hotel_result: List = None,
                    request_param_model: HotelResultModel = None) -> None:
    url_photo = HotelsUrlsOptions().hotels_urls['properties_get_hotel_photos']
    querystring = {"id": hotel['id']}
    response = requests.request("GET", url_photo, headers=DefaultHeaders().get_headers, params=querystring)
    photos_dict = json.loads(response.text)
    hotel_result.photos_urls = [image['baseUrl'].format(size='w') for image in
                                photos_dict['hotelImages'][:int(request_param_model.photos_count)]]
