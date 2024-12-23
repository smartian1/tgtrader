# encoding: utf-8


from abc import abstractmethod
from typing import Dict
import pandas as pd
from tgtrader import bt
from tgtrader.bt.core import Algo
from tgtrader.common import SecurityType, RebalancePeriod
from tgtrader.data import DEFAULT_DATA_PROVIDER, DataGetter
from tgtrader.strategy import StrategyDef



"""
以下是具体的策略的实现
"""
class BtStrategy(StrategyDef):
    def __init__(self,
                 name: str,
                 symbols: Dict[SecurityType, list[str]],
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily,
                 data_getter: DataGetter = DEFAULT_DATA_PROVIDER,
                 integer_positions: bool = True,
                 commissions = lambda q, p: 0.0,
                 backtest_field: str = 'close',
                 initial_capital: float = 1000000.0):
        super().__init__(name, symbols, rebalance_period, data_getter, initial_capital)
        self.integer_positions = integer_positions
        self.commissions = commissions
        self.backtest_field = backtest_field

    def _run(self, df: pd.DataFrame):
        df = df[[self.backtest_field]]
        df = pd.pivot_table(df, index='date', columns='code', values=self.backtest_field)

        df = df.fillna(method='ffill')

        s = bt.Strategy(self.name, self._get_algos())
        t = bt.Backtest(s, df, integer_positions=self.integer_positions, commissions=self.commissions, progress_bar=True)
        ret = bt.run(t)

        return ret

    @abstractmethod
    def _get_algos(self) -> list[Algo]:
        raise NotImplementedError


class BtTreeStrategy(BtStrategy):
    def __init__(self, 
                 name: str,
                 symbols: Dict[SecurityType, list[str]],
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily,
                 data_getter: DataGetter = DEFAULT_DATA_PROVIDER,
                 integer_positions: bool = True,
                 commissions = lambda q, p: 0.0,
                 backtest_field: str = 'close',
                 initial_capital: float = 1000000.0):
        super().__init__(name, symbols, rebalance_period, data_getter, initial_capital, integer_positions, commissions, backtest_field)
        self.strategies: list[BtStrategy] = []

    def add_strategy(self, strategy: BtStrategy):
        self.strategies.append(strategy)

    def _run(self, df: pd.DataFrame):
        df = df[self.backtest_field]
        df = pd.pivot_table(df, index='date', columns='code', values=self.backtest_field)

        df = df.fillna(method='ffill')
    
        strats_list = []
        for strategy in self.strategies:
            strats = bt.Strategy(strategy.name, strategy.get_algos())
            strats_list.append(strats)

        s = bt.Strategy(self.name, self.get_algos(), children=strats_list)
        t = bt.Backtest(s, df, integer_positions=self.integer_positions, commissions=self.commissions, progress_bar=True)
        ret = bt.run(t)

        return ret
