# encoding: utf-8

from abc import ABC, abstractmethod
import enum
from typing import Optional

import pandas as pd

from tgtrader.data_provider.dao.models.t_meta_model import T_Meta_Model


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

class DataSource(enum.Enum):
    """数据源"""
    Akshare = 'akshare'
    Tushare = 'tushare'


class MetaType(enum.Enum):
    """元数据类型"""
    Stocks1dHfqKdata = 'stocks_1d_hfq_kdata'

class DataProvider:
    def __init__(self):
        pass

    @classmethod
    def get_provider(cls, data_source: DataSource) -> 'DataProvider':
        """获取数据提供者"""
        if data_source == DataSource.Akshare:
            from tgtrader.data_provider.data_provider_akshare import AkshareDataProvider
            return AkshareDataProvider()
        else:
            raise NotImplementedError(f'数据源 {data_source} 不支持')

    def get_price(self,
                 symbol_list: list[str],
                 start_date: str,
                 end_date: str,
                 security_type: SecurityType,
                 period: Period = Period.Day,
                 adjust: str = "hfq",
                 fields: list[str] = ["open", "high", "low", "close", "volume"],
                 multi_thread_cnt: int = -1):
        raise NotImplementedError
    
    def get_all_symbols(self, security_type: SecurityType):
        raise NotImplementedError

    def standardize_symbol(self, symbol: str):
        raise NotImplementedError

    @abstractmethod
    def save_price_data(
            self,
            data: pd.DataFrame,
            security_type: SecurityType,
            period: Period,
            adjust: PriceAdjust
    ):
        raise NotImplementedError


class DataDbService(ABC):
    """数据服务接口类，定义数据存储和查询的标准接口"""
    @classmethod
    def init_database(cls):
        """初始化数据库"""
        raise NotImplementedError

    @classmethod
    def get_data_service(cls, data_source: DataSource) -> 'DataDbService':
        """获取数据服务"""
        if data_source == DataSource.Akshare:
            from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
            return AkshareDataService()
        else:
            raise NotImplementedError(f'数据源 {data_source} 不支持')

    @abstractmethod
    def batch_save_kdata(self,
                         data: Optional[pd.DataFrame] = None,
                         adjust: Optional[PriceAdjust] = None,
                         source: str = 'akshare',
                         batch_size: int = 100000) -> int:
        """批量保存K线数据

        Args:
            data: DataFrame with MultiIndex(code, date)，原始K线数据
            data_list: 已处理的数据字典列表，与data二选一
            adjust: 复权方式，仅在传入data时需要
            source: 数据来源
            batch_size: 每批处理的数据量，默认1000条

        Returns:
            int: 成功保存的记录数
        """
        raise NotImplementedError

    @abstractmethod
    def update_meta_info(self,
                         meta_type: MetaType,
                         security_type: SecurityType,
                         period: Period,
                         start_time: str,
                         end_time: str,
                         source: str,
                         table_name: str) -> bool:
        """更新元数据信息

        Args:
            meta_type: 元数据类型
            security_type: 证券类型
            period: 周期
            start_time: 开始时间 YYYY-MM-DD
            end_time: 结束时间 YYYY-MM-DD
            source: 数据来源
            table_name: 表名
        Returns:
            bool: 是否更新成功
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self, meta_type: MetaType) -> Optional[T_Meta_Model]:
        """获取元数据"""
        raise NotImplementedError
