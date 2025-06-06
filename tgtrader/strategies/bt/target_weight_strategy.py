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
class TargetWeightStrategyConfig(StrategyConfig):
    target_weights_dict: Dict[str, Any] = Field(default_factory=dict, description="目标权重")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        dict_config = super().to_dict()
        dict_config['target_weights_dict'] = self.target_weights_dict

        return dict_config

    def from_dict(self, data: dict) -> None:
        """从字典格式加载数据"""
        super().from_dict(data)
        if 'target_weights' in data:
            if isinstance(data['target_weights'], pd.DataFrame):
                self.target_weights_dict = data['target_weights'].to_dict()
            else:
                self.target_weights_dict = data['target_weights']

@strategy_def(name="目标权重策略")
class TargetWeightStrategy(BtStrategy):
    def __init__(self, 
                 symbols: Dict[SecurityType, list[str]], 
                 target_weights_dict: dict[str, float],
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily, 
                 data_getter: DataGetter = DEFAULT_DATA_PROVIDER, 
                 integer_positions: bool = True, 
                 commissions = lambda q, p: 0.0,
                 backtest_field: str = 'close',
                 initial_capital: float = 1000000.0):
        super().__init__(name="TargetWeightStrategy", 
                         symbols=symbols, 
                         rebalance_period=rebalance_period, 
                         data_getter=data_getter, 
                         integer_positions=integer_positions, 
                         commissions=commissions,
                         backtest_field=backtest_field,
                         initial_capital=initial_capital)
        self.target_weights_dict = target_weights_dict

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
            bt.algos.WeighSpecified(**self.target_weights_dict),
            bt.algos.Rebalance()]
        
        return self.algos