# encoding: utf-8
import enum
from typing import Dict, Optional

import pandas as pd

from tgtrader import bt
from tgtrader.bt.core import Algo
from tgtrader.common import Period, PriceAdjust, SecurityType
from tgtrader.data import DataGetter

DEFAULT_DATA_GETTER = DataGetter()

# 调仓周期
class RebalancePeriod(enum.Enum):
    Daily = 1
    Weekly = 2
    Monthly = 3
    Quarterly = 4
    Yearly = 5


# 模型
class Model:
    def __init__(self):
        self.name: str = ""
    
    def run(self, 
            df: pd.DataFrame,
            ):
        raise NotImplementedError
    
    def get_result(self):
        raise NotImplementedError
    
    def plot_result(self):
        raise NotImplementedError

# 策略
class StrategyDef:
    def __init__(self, data_getter: DataGetter = DEFAULT_DATA_GETTER):
        self.data_getter = data_getter
        self.name: str = ""
        self.symbols: Dict[SecurityType, list[str]] = {}
        self.rebalance_period: RebalancePeriod = RebalancePeriod.Daily
        self.model: Optional[Model] = None
    
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
        self.model.run(df)


"""
以下是具体的模型的实现
"""
class ModelBt(Model):
    def __init__(self):
        super().__init__()
        self.name = "ModelBt"
        self.rebalance_period: RebalancePeriod = RebalancePeriod.Daily
        self.algos: list[Algo] = []
        self.run_result = None
    
    def run(self, 
            df: pd.DataFrame,
            ):
        s = bt.Strategy(self.name, self.algos)
        t = bt.Backtest(s, df)
        self.run_result = t.run()


class WeightEqualModel(ModelBt):
    def __init__(self):
        super().__init__()
        self.name = "WeightEqualModel"

        if self.rebalance_period == RebalancePeriod.Daily:
            period_run_algo = bt.algos.RunDaily()
        elif self.rebalance_period == RebalancePeriod.Weekly:
            period_run_algo = bt.algos.RunWeekly()
        elif self.rebalance_period == RebalancePeriod.Monthly:
            period_run_algo = bt.algos.RunMonthly()
        else:
            raise ValueError(f"Unsupported rebalance period: {self.rebalance_period}")

        self.algos = [
            period_run_algo,
            bt.algos.SelectAll(),
            bt.algos.WeighEqually(),
            bt.algos.Rebalance()]

"""
以下是具体的策略的实现
"""
class WeightEqualStrategy(StrategyDef):
    def __init__(self,
                 symbols: list[str],
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily,
                 data_getter: DataGetter = DEFAULT_DATA_GETTER):
        super().__init__(data_getter)
        self.name = "WeightEqualStrategy"
        self.symbols = symbols
        self.rebalance_period = rebalance_period
