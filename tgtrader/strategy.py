# encoding: utf-8
from abc import abstractmethod
import enum
from typing import Dict, Optional

import pandas as pd

from tgtrader.common import Period, PriceAdjust, SecurityType
from tgtrader.data import DataGetter

# 调仓周期
class RebalancePeriod(enum.Enum):
    Daily = 1
    Weekly = 2
    Monthly = 3
    Quarterly = 4
    Yearly = 5


# 策略
class StrategyDef:
    def __init__(self, 
                 name: str, 
                 symbols: Dict[SecurityType, list[str]],
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily,
                 data_getter: DataGetter = None):
        self.data_getter = data_getter
        self.name: str = name
        self.symbols: Dict[SecurityType, list[str]] = symbols
        self.rebalance_period: RebalancePeriod = rebalance_period
        self.backtest_result = None


    def backtest(self, start_date: str, end_date: str):
        # 遍历每个证券类型，获取数据
        dfs = []
        for security_type, symbols in self.symbols.items():
            df = self.data_getter.get_data(symbols,
                                         start_date,
                                         end_date,
                                         period=Period.Day,
                                         adjust=PriceAdjust.HFQ,
                                         security_type=security_type)
            dfs.append(df)
        
        # 合并所有数据
        df = pd.concat(dfs) if len(dfs) > 0 else pd.DataFrame()

        self.backtest_result = self._run(df)
    
    @abstractmethod
    def _run(self, df: pd.DataFrame):
        raise NotImplementedError

    @abstractmethod
    def get_result(self) -> pd.DataFrame:
        raise NotImplementedError
    
    @abstractmethod
    def plot_result(self):
        raise NotImplementedError


