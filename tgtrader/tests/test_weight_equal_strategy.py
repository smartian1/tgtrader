import unittest
import pandas as pd
import numpy as np
from tgtrader.strategy.strategies.bt.weight_equal_strategy import WeightEqualStrategy
from tgtrader.strategy.strategy_base import RebalancePeriod
from tgtrader.data import DataGetter
from tgtrader import bt


class MockDataGetter(DataGetter):
    def get_data(self, symbols: list[str], start_date: str = None, end_date: str = None) -> pd.DataFrame:
        dates = pd.date_range(start='2023-01-01', end='2023-01-10')
        data = {}
        for symbol in symbols:
            data[symbol] = np.random.randn(len(dates)) + 100
        return pd.DataFrame(data, index=dates)


class TestWeightEqualStrategy(unittest.TestCase):
    def setUp(self):
        self.symbols = ['AAPL', 'GOOGL', 'MSFT']
        self.mock_data_getter = MockDataGetter()

    def test_initialization(self):
        """Test proper initialization of WeightEqualStrategy"""
        strategy = WeightEqualStrategy(
            symbols=self.symbols,
            data_getter=self.mock_data_getter
        )
        
        self.assertEqual(strategy.name, "WeightEqualStrategy")
        self.assertEqual(strategy.symbols, self.symbols)
        self.assertEqual(strategy.rebalance_period, RebalancePeriod.Daily)
        self.assertFalse(strategy.integer_positions)

    def test_algo_generation_daily(self):
        """Test algo generation with daily rebalancing"""
        strategy = WeightEqualStrategy(
            symbols=self.symbols,
            rebalance_period=RebalancePeriod.Daily,
            data_getter=self.mock_data_getter
        )
        
        algos = strategy.get_algos()
        self.assertEqual(len(algos), 4)
        self.assertIsInstance(algos[0], bt.algos.RunDaily)
        self.assertIsInstance(algos[1], bt.algos.SelectAll)
        self.assertIsInstance(algos[2], bt.algos.WeighEqually)
        self.assertIsInstance(algos[3], bt.algos.Rebalance)

    def test_algo_generation_weekly(self):
        """Test algo generation with weekly rebalancing"""
        strategy = WeightEqualStrategy(
            symbols=self.symbols,
            rebalance_period=RebalancePeriod.Weekly,
            data_getter=self.mock_data_getter
        )
        
        algos = strategy.get_algos()
        self.assertEqual(len(algos), 4)
        self.assertIsInstance(algos[0], bt.algos.RunWeekly)

    def test_algo_generation_monthly(self):
        """Test algo generation with monthly rebalancing"""
        strategy = WeightEqualStrategy(
            symbols=self.symbols,
            rebalance_period=RebalancePeriod.Monthly,
            data_getter=self.mock_data_getter
        )
        
        algos = strategy.get_algos()
        self.assertEqual(len(algos), 4)
        self.assertIsInstance(algos[0], bt.algos.RunMonthly)

    def test_invalid_rebalance_period(self):
        """Test that invalid rebalance period raises ValueError"""
        with self.assertRaises(ValueError):
            strategy = WeightEqualStrategy(
                symbols=self.symbols,
                rebalance_period="Invalid",
                data_getter=self.mock_data_getter
            )
            strategy.get_algos()

    def test_strategy_with_commission(self):
        """Test strategy initialization with commission function"""
        def commission_func(q, p):
            return 0.001 * abs(q) * p

        strategy = WeightEqualStrategy(
            symbols=self.symbols,
            data_getter=self.mock_data_getter,
            commissions=commission_func
        )
        
        self.assertEqual(strategy.commissions, commission_func)


if __name__ == '__main__':
    unittest.main() 