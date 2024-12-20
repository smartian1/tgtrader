# encoding: utf-8

import enum

class PriceAdjust(enum.Enum):
    NO = "NO"
    HFQ = "hfq"
    QFQ = "qfq"

class Period(enum.Enum):
    Day = "1d"
    Week = "1w"
    Month = "1m"
    Year = "1y"

class SecurityType(enum.Enum):
    Stocks = 'stocks'
    ETF = 'etf'
    Fund = 'fund'
    Futures = 'futures'

class RebalancePeriod(enum.Enum):
    """调仓周期"""
    Daily = 'daily'
    Weekly = 'weekly'
    Monthly = 'monthly'
    Quarterly = 'quarterly'

class DataProvider:
    def __init__(self):
        pass

    def get_data(self,
                 symbol_list: list[str],
                 start_date: str,
                 end_date: str,
                 security_type: SecurityType,
                 period: Period = Period.Day,
                 adjust: str = "hfq",
                 fields: list[str] = ["open", "high", "low", "close", "volume"]):
        raise NotImplementedError

    def standardize_symbol(self, symbol: str):
        raise NotImplementedError
