# encoding: utf-8


"""
WeightEqualStrategy
"""
from tgtrader import bt
from tgtrader.bt.core import Algo
from tgtrader.data import DataGetter
from tgtrader.strategy.strategies.bt.strategy_bt import BtStrategy
from tgtrader.strategy.strategy_base import DEFAULT_DATA_GETTER, RebalancePeriod



class WeightEqualStrategy(BtStrategy):
    def __init__(self, 
                 symbols: list[str], 
                 rebalance_period: RebalancePeriod = RebalancePeriod.Daily, 
                 data_getter: DataGetter = DEFAULT_DATA_GETTER, 
                 integer_positions: bool = False, 
                 commissions: lambda q, p: float = 0.0):
        super().__init__(name="WeightEqualStrategy", 
                         symbols=symbols, 
                         rebalance_period=rebalance_period, 
                         data_getter=data_getter, 
                         integer_positions=integer_positions, 
                         commissions=commissions)

    def get_algos(self) -> list[Algo]:
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