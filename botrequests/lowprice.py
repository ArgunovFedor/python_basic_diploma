from typing import List

from botrequests.get_hotels_handler import get_hotels_handler
from models.lowprice_result_model import LowPriceResultModel
from models.request_param_model import RequestParamModel


def get_lowprice_hotels(request_param_model: RequestParamModel = None, meta_date: List = None) -> List[LowPriceResultModel]:
    return get_hotels_handler(request_param_model=request_param_model, meta_date=meta_date,
                              result_model=LowPriceResultModel)




