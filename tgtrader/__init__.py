"""
tgtrader - TianGong Quantitative Investment Research Analysis Client
"""

import warnings

warnings.filterwarnings('ignore', message='为了支持更多特性，请将 Pandas 升级到 2.2.0 及以上版本！')


from .common import *
from .data import *


from .strategy.strategy_base import *
from .strategy.strategies.bt.strategy_bt import *
from .strategy.strategies.bt.weight_equal_strategy import WeightEqualStrategy as WeightEqualStrategyBt

__version__ = "0.1.0"
