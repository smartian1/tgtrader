# encoding: utf-8

import enum

import pandas as pd

class PriceAdjust(enum.Enum):
    NO = "nfq"
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

    def init_db(self):
        """
        初始化数据库以及表（即使是外部数据源，如果需要保存到本地，也需要初始化）
        """
        raise NotImplementedError

    def get_price(self,
                 symbol_list: list[str],
                 start_date: str,
                 end_date: str,
                 security_type: SecurityType,
                 period: Period = Period.Day,
                 adjust: str = "hfq",
                 fields: list[str] = ["open", "high", "low", "close", "volume"]):
        raise NotImplementedError
    
    def get_all_symbols(self, security_type: SecurityType):
        raise NotImplementedError

    def standardize_symbol(self, symbol: str):
        raise NotImplementedError

    def save_data(self, 
                  data: pd.DataFrame,
                  security_type: SecurityType,
                  period: Period,
                  adjust: PriceAdjust):
        raise NotImplementedError
