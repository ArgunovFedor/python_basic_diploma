from typing import List

from botrequests.get_hotels_handler import get_hotels_handler
from exceptions.api_exception import ApiException
from models.bestdeal_result_model import BestDealResultModel
from models.request_param_model import RequestParamModel


def get_bestdeal_hotels(request_param_model: RequestParamModel = None, meta_date: List = None) -> List[BestDealResultModel]:
    request_param_model.sort_order = 'DISTANCE_FROM_LANDMARK'
    result = [hotel for hotel in get_hotels_handler(request_param_model=request_param_model, meta_date=meta_date,
                              result_model=BestDealResultModel)
              if request_param_model.is_acceptable_distance(hotel)]
    if len(result) == 0:
        raise ApiException('EMPTY:По установленным фильтрам, к сожалению, отелей не найдено')
    return result





