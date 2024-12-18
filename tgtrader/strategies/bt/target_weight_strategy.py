# encoding: utf-8


"""
TargetWeightStrategy
"""
from tgtrader import bt
from tgtrader.bt.core import Algo
from tgtrader.data import DataGetter
from tgtrader.strategies.bt.strategy_bt import BtStrategy
from tgtrader.strategy import RebalancePeriod
from tgtrader.data import DataGetter, DEFAULT_DATA_PROVIDER
from tgtrader.common import SecurityType
from typing import Dict

class TargetWeightStrategy(BtStrategy):
    def __init__(self, 
                 symbols: Dict[SecurityType, list[str]], 
                 weights: dict[str, float],
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily, 
                 data_getter: DataGetter = DEFAULT_DATA_PROVIDER, 
                 integer_positions: bool = True, 
                 commissions = lambda q, p: 0.0,
                 backtest_field: str = 'close'):
        super().__init__(name="TargetWeightStrategy", 
                         symbols=symbols, 
                         rebalance_period=rebalance_period, 
                         data_getter=data_getter, 
                         integer_positions=integer_positions, 
                         commissions=commissions,
                         backtest_field=backtest_field)
        self.weights = weights

    def _get_algos(self) -> list[Algo]:
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
            bt.algos.WeighSpecified(**self.weights),
            bt.algos.Rebalance()]
        
        return self.algos