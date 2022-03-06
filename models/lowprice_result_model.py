from models.hotel_result_model import HotelResultModel


class LowPriceResultModel(HotelResultModel):
    def __str__(self):
        return 'Название отеля: {name}\n' \
               'Адрес: {address}\n' \
               'Как далеко расположен от центра: {distance}\n' \
               'Цена: {price}'.format(
            name=self.name,
            address=self.address,
            price=self.price,
            distance=self.distance
        )
