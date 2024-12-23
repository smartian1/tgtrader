# encoding: utf-8


"""
TargetWeightStrategy
"""
import pandas as pd
from tgtrader import bt
from tgtrader.bt.core import Algo
from tgtrader.data import DataGetter
from tgtrader.strategies.bt.strategy_bt import BtStrategy
from tgtrader.strategy import RebalancePeriod, strategy_def
from tgtrader.data import DataGetter, DEFAULT_DATA_PROVIDER
from tgtrader.common import SecurityType
from typing import Dict, Any
import json
from pydantic import Field
from tgtrader.strategy_config import StrategyConfig, strategy_config_def

@strategy_config_def
class RiskParityStrategyConfig(StrategyConfig):
    def to_dict(self) -> dict:
        return super().to_dict()

    def from_dict(self, data: dict) -> None:
        """从字典格式加载数据"""
        super().from_dict(data)


@strategy_def(name="风险平价策略")
class RiskParityStrategy(BtStrategy):
    def __init__(self, 
                 symbols: Dict[SecurityType, list[str]], 
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily, 
                 data_getter: DataGetter = DEFAULT_DATA_PROVIDER, 
                 integer_positions: bool = True, 
                 commissions = lambda q, p: 0.0,
                 backtest_field: str = 'close'):
        super().__init__(name="RiskParityStrategy", 
                         symbols=symbols, 
                         rebalance_period=rebalance_period, 
                         data_getter=data_getter, 
                         integer_positions=integer_positions, 
                         commissions=commissions,
                         backtest_field=backtest_field)

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
            bt.algos.WeighInvVol(),
            bt.algos.Rebalance()]
        
        return self.algos