# encoding: utf-8
from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
from loguru import logger

from tgtrader.common import SecurityType, Period, PriceAdjust

class DataService(ABC):
    """数据服务接口类，定义数据存储和查询的标准接口"""
    
    @abstractmethod
    def batch_save_kdata(self, 
                        data: Optional[pd.DataFrame] = None,
                        adjust: Optional[PriceAdjust] = None,
                        source: str = 'akshare',
                        batch_size: int = 1000) -> int:
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
                        meta_name: str,
                        security_type: SecurityType,
                        period: Period,
                        start_time: str,
                        end_time: str,
                        source: str,
                        table_name: str) -> bool:
        """更新元数据信息

        Args:
            meta_name: 元数据名称
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
