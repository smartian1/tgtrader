# encoding: utf-8


"""
WeightEqualStrategy
"""
from tgtrader import bt
from tgtrader.bt.core import Algo
from tgtrader.data import DataGetter
from tgtrader.strategy.strategies.bt.strategy_bt import BtStrategy
from tgtrader.strategy.strategy_base import RebalancePeriod
from tgtrader.data import DataGetter, DEFAULT_DATA_PROVIDER


class WeightEqualStrategy(BtStrategy):
    def __init__(self, 
                 symbols: list[str], 
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily, 
                 data_getter: DataGetter = DEFAULT_DATA_PROVIDER, 
                 integer_positions: bool = True, 
                 commissions = lambda q, p: 0.0,
                 backtest_field: str = 'close'):
        super().__init__(name="WeightEqualStrategy", 
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
            bt.algos.WeighEqually(),
            bt.algos.Rebalance()]
        
        return self.algos