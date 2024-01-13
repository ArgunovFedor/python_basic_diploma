from typing import List

from botrequests.get_hotels_handler import get_hotels_handler
from models.highprice_result_model import HighPriceResultModel
from models.request_param_model import RequestParamModel


def get_highprice_hotels(request_param_model: RequestParamModel = None, meta_date: List = None) -> List[HighPriceResultModel]:
    request_param_model.sort_order = 'PRICE_HIGHEST_FIRST'
    return get_hotels_handler(request_param_model=request_param_model, meta_date=meta_date,
                              result_model=HighPriceResultModel)



