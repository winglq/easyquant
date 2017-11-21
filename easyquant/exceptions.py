class EasyQuantException(Exception):
    pass


class NoHistoryData(EasyQuantException):
    pass


class LessDaysThanExpected(EasyQuantException):
    pass


class StockValueZero(EasyQuantException):
    pass
