import datetime
from typing import List

import requests
import json

from infastructure.default_headers import DefaultHeaders
from infastructure.hotels_urls_options import HotelsUrlsOptions
from botrequests.search import get_destinationIds_list
from models.lowprice_result_model import LowPriceResultModel
from models.request_param_model import RequestParamModel


def get_lowprice_hotels(requestParamModel: RequestParamModel=None, meta_date: List=None) -> List[LowPriceResultModel]:
    url = HotelsUrlsOptions().hotels_urls['properties_list']
    querystring = {"query": requestParamModel.city, "locale": meta_date['hcomLocale'], "currency": "RUB"}
    destinationIds_list = get_destinationIds_list(querystring, DefaultHeaders().get_headers)
    # 1 - это hotels
    check_in = datetime.date.today()
    check_out = check_in + datetime.timedelta(days=6)
    querystring = {
        "destinationId": destinationIds_list[0],
        "pageNumber": "1",
        "pageSize": requestParamModel.hotels_count,
        "checkIn": check_in.strftime('%Y-%m-%d'),
        "checkOut": check_out.strftime('%Y-%m-%d'),
        "adults1": "1",
        "sortOrder": "PRICE",
        "locale": meta_date['hcomLocale'],
        "currency": meta_date['currency']}
    response = requests.request("GET", url, headers=DefaultHeaders().get_headers, params=querystring)
    hotels_dict = json.loads(response.text)
    result_list = list()
    # если указано с фотографией, то доп фотографии должны вывести
    for hotel in hotels_dict['data']['body']['searchResults']['results']:
        # готовим ответ
        hotel_result = LowPriceResultModel()
        hotel_result.hotel_id = hotel['id']
        hotel_result.name = hotel['name']
        hotel_result.address = hotel['address']
        hotel_result.price = hotel['ratePlan']['price']['current']
        hotel_result.distance = hotel['landmarks'][0]['distance']
        # делаем запрос за коллекцией фотографий

        if requestParamModel.is_with_photos:
            get_photos_urls(hotel, hotel_result, requestParamModel)
        # добавляем в основной результирующий лист
        result_list.append(hotel_result)
    return result_list


def get_photos_urls(hotel, hotel_result, requestParamModel=None):
    url_photo = HotelsUrlsOptions().hotels_urls['properties_get_hotel_photos']
    querystring = {"id": hotel['id']}
    response = requests.request("GET", url_photo, headers=DefaultHeaders().get_headers, params=querystring)
    photos_dict = json.loads(response.text)
    hotel_result.photos_urls = [image['baseUrl'].format(size='w') for image in
                                photos_dict['hotelImages'][:int(requestParamModel.photos_count)]]
