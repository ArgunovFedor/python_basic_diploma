import requests
import json
from exceptions.api_exception import ApiException
from infastructure.hotels_urls_options import HotelsUrlsOptions


def get_destinationIds_list(
        querystring: dict,
        headers: dict,
        url: str = HotelsUrlsOptions().hotels_urls['locations']) -> list:
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(response.text)
    if len(response['suggestions'][0]['entities']) != 0:
        return [(ent['destinationId'], ent['caption'], ent['name']) for ent in response['suggestions'][0]['entities']]
    raise ApiException('SEARCH: Город не отмечен на карте как отдельный субъект')