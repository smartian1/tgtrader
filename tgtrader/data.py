# encoding: utf-8
from tgtrader.common import Period, DataProvider, PriceAdjust, SecurityType
from tgtrader.data_provider.data_provider_akshare import AkshareDataProvider

    
DEFAULT_DATA_PROVIDER = AkshareDataProvider()

class DataGetter:
    def __init__(self):
        pass

    def get_data(self, 
                 symbol_list: list[str], 
                 start_date: str, 
                 end_date: str, 
                 period: Period = Period.Day,
                 adjust: PriceAdjust = PriceAdjust.HFQ,
                 fields: list[str] = ["open", "high", "low", "close", "volume"],
                 security_type: SecurityType = SecurityType.Stocks,
                 provider: DataProvider = DEFAULT_DATA_PROVIDER):
        """
        获取股票数据
        
        参数:
        - symbol_list: 股票代码列表
        - start_date: 开始日期，格式为"YYYY-MM-DD"
        - end_date: 结束日期，格式为"YYYY-MM-DD" 
        - period: 周期，默认为日线数据
        - adjust: 复权方式，默认为"hfq"(后复权)
        - fields: 需要获取的字段列表，默认为["open", "high", "low", "close", "volume"]
        - provider: 数据提供者，默认为AkshareDataProvider，可选其他provider，或者自定义provider
        
        返回格式:
        - 返回DataFrame，复合索引为(code, date)，列为字段名
            例如:
                                 open    high    low     close   volume
            code        date      
            510300     2023-01-01  4.80    4.90    4.75    4.85    1500000
                       2023-01-02  4.85    4.92    4.80    4.88    1600000
            510500     2023-01-01  7.20    7.30    7.15    7.23    2000000
                       2023-01-02  7.23    7.28    7.20    7.25    1800000
        """
        
        # 标准化symbol，因为不同数据提供者的symbol格式可能不一样
        symbol_list = [provider.standardize_symbol(symbol) for symbol in symbol_list]

        return provider.get_data(symbol_list, start_date, end_date, period, adjust, fields, security_type)
