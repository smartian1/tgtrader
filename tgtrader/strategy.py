# encoding: utf-8
from abc import abstractmethod
import enum
from typing import Dict, List, Optional, Type, Union
from dataclasses import dataclass

import pandas as pd
import ffn

from tgtrader.common import Period, PriceAdjust, SecurityType, RebalancePeriod
from tgtrader.data import DataGetter
from tgtrader.strategy_config import StrategyConfig


@dataclass
class PerformanceStats:
    """Performance statistics for a trading strategy"""
    # 基础信息
    start: str                      # 回测开始日期
    end: str                        # 回测结束日期
    rf: float                       # 无风险利率

    # 总体收益指标
    total_return: float             # 总收益
    cagr: float                     # 年化收益率
    max_drawdown: float             # 最大回撤
    avg_drawdown: float             # 平均回撤
    avg_drawdown_days: int          # 平均回撤天数
    calmar: float                   # calmar比率

    # 期间收益
    mtd: float                      # 当月收益
    three_month: float              # 3个月收益
    six_month: float                # 6个月收益
    ytd: float                      # 年初至今收益
    one_year: float                 # 1年收益
    three_year: float               # 3年年化收益
    five_year: float                # 5年年化收益
    ten_year: float                 # 10年年化收益
    incep: float                    # 成立以来年化收益

    # 日度指标
    daily_sharpe: float             # 日度夏普比率
    daily_sortino: float            # 日度索提诺比率
    daily_mean: float               # 日度平均收益（年化）
    daily_vol: float                # 日度波动率（年化）
    daily_skew: float               # 日度偏度
    daily_kurt: float               # 日度峰度
    best_day: float                 # 最佳单日收益
    worst_day: float                # 最差单日收益

    # 月度指标
    monthly_sharpe: float           # 月度夏普比率
    monthly_sortino: float          # 月度索提诺比率
    monthly_mean: float             # 月度平均收益（年化）
    monthly_vol: float              # 月度波动率（年化）
    monthly_skew: float             # 月度偏度
    monthly_kurt: float             # 月度峰度
    best_month: float               # 最佳月度收益
    worst_month: float              # 最差月度收益
    avg_up_month: float             # 上涨月均值
    avg_down_month: float           # 下跌月均值

    # 年度指标
    yearly_sharpe: float            # 年度夏普比率
    yearly_sortino: float           # 年度索提诺比率
    yearly_mean: float              # 年度平均收益
    yearly_vol: float               # 年度波动率
    yearly_skew: float              # 年度偏度
    yearly_kurt: float              # 年度峰度
    best_year: float                # 最佳年度收益
    worst_year: float               # 最差年度收益
    win_year_perc: float           # 年度胜率
    twelve_month_win_perc: float   # 12个月胜率

    @classmethod
    def from_ffn_stats(cls, stats: pd.Series) -> 'PerformanceStats':
        """从ffn.GroupStats.stats创建PerformanceStats实例"""
        
        return cls(
            # 基础信息
            start=str(stats.loc['start'] if 'start' in stats.index else ''),
            end=str(stats.loc['end'] if 'end' in stats.index else ''),
            rf=float(stats.loc['rf'] if 'rf' in stats.index else 0.0),
            
            # 总体收益指标
            total_return=float(stats.loc['total_return'] if 'total_return' in stats.index else 0.0),
            cagr=float(stats.loc['cagr'] if 'cagr' in stats.index else 0.0),
            max_drawdown=float(stats.loc['max_drawdown'] if 'max_drawdown' in stats.index else 0.0),
            avg_drawdown=float(stats.loc['avg_drawdown'] if 'avg_drawdown' in stats.index else 0.0),
            avg_drawdown_days=int(stats.loc['avg_drawdown_days'] if 'avg_drawdown_days' in stats.index else 0),
            calmar=float(stats.loc['calmar'] if 'calmar' in stats.index else 0.0),
            
            # 期间收益
            mtd=float(stats.loc['mtd'] if 'mtd' in stats.index else 0.0),
            three_month=float(stats.loc['three_month'] if 'three_month' in stats.index else 0.0),
            six_month=float(stats.loc['six_month'] if 'six_month' in stats.index else 0.0),
            ytd=float(stats.loc['ytd'] if 'ytd' in stats.index else 0.0),
            one_year=float(stats.loc['one_year'] if 'one_year' in stats.index else 0.0),
            three_year=float(stats.loc['three_year'] if 'three_year' in stats.index else 0.0),
            five_year=float(stats.loc['five_year'] if 'five_year' in stats.index else 0.0),
            ten_year=float(stats.loc['ten_year'] if 'ten_year' in stats.index else 0.0),
            incep=float(stats.loc['incep'] if 'incep' in stats.index else 0.0),
            
            # 日度指标
            daily_sharpe=float(stats.loc['daily_sharpe'] if 'daily_sharpe' in stats.index else 0.0),
            daily_sortino=float(stats.loc['daily_sortino'] if 'daily_sortino' in stats.index else 0.0),
            daily_mean=float(stats.loc['daily_mean'] if 'daily_mean' in stats.index else 0.0),
            daily_vol=float(stats.loc['daily_vol'] if 'daily_vol' in stats.index else 0.0),
            daily_skew=float(stats.loc['daily_skew'] if 'daily_skew' in stats.index else 0.0),
            daily_kurt=float(stats.loc['daily_kurt'] if 'daily_kurt' in stats.index else 0.0),
            best_day=float(stats.loc['best_day'] if 'best_day' in stats.index else 0.0),
            worst_day=float(stats.loc['worst_day'] if 'worst_day' in stats.index else 0.0),
            
            # 月度指标
            monthly_sharpe=float(stats.loc['monthly_sharpe'] if 'monthly_sharpe' in stats.index else 0.0),
            monthly_sortino=float(stats.loc['monthly_sortino'] if 'monthly_sortino' in stats.index else 0.0),
            monthly_mean=float(stats.loc['monthly_mean'] if 'monthly_mean' in stats.index else 0.0),
            monthly_vol=float(stats.loc['monthly_vol'] if 'monthly_vol' in stats.index else 0.0),
            monthly_skew=float(stats.loc['monthly_skew'] if 'monthly_skew' in stats.index else 0.0),
            monthly_kurt=float(stats.loc['monthly_kurt'] if 'monthly_kurt' in stats.index else 0.0),
            best_month=float(stats.loc['best_month'] if 'best_month' in stats.index else 0.0),
            worst_month=float(stats.loc['worst_month'] if 'worst_month' in stats.index else 0.0),
            avg_up_month=float(stats.loc['avg_up_month'] if 'avg_up_month' in stats.index else 0.0),
            avg_down_month=float(stats.loc['avg_down_month'] if 'avg_down_month' in stats.index else 0.0),
            
            # 年度指标
            yearly_sharpe=float(stats.loc['yearly_sharpe'] if 'yearly_sharpe' in stats.index else 0.0),
            yearly_sortino=float(stats.loc['yearly_sortino'] if 'yearly_sortino' in stats.index else 0.0),
            yearly_mean=float(stats.loc['yearly_mean'] if 'yearly_mean' in stats.index else 0.0),
            yearly_vol=float(stats.loc['yearly_vol'] if 'yearly_vol' in stats.index else 0.0),
            yearly_skew=float(stats.loc['yearly_skew'] if 'yearly_skew' in stats.index else 0.0),
            yearly_kurt=float(stats.loc['yearly_kurt'] if 'yearly_kurt' in stats.index else 0.0),
            best_year=float(stats.loc['best_year'] if 'best_year' in stats.index else 0.0),
            worst_year=float(stats.loc['worst_year'] if 'worst_year' in stats.index else 0.0),
            win_year_perc=float(stats.loc['win_year_perc'] if 'win_year_perc' in stats.index else 0.0),
            twelve_month_win_perc=float(stats.loc['twelve_month_win_perc'] if 'twelve_month_win_perc' in stats.index else 0.0)
        )

    def to_dataframe(self) -> pd.DataFrame:
        """将统计数据转换为DataFrame格式，并按类别分组"""
        data = self.__dict__
        
        # 定义指标分组
        groups = {
            'Basic_Info': ['start', 'end', 'rf'],
            'Overall_Returns': ['total_return', 'cagr', 'max_drawdown', 'avg_drawdown',
                        'avg_drawdown_days', 'calmar'],
            'Period_Returns': ['mtd', 'three_month', 'six_month', 'ytd', 'one_year',
                        'three_year', 'five_year', 'ten_year', 'incep'],
            'Daily_Metrics': ['daily_sharpe', 'daily_sortino', 'daily_mean', 'daily_vol',
                        'daily_skew', 'daily_kurt', 'best_day', 'worst_day'],
            'Monthly_Metrics': ['monthly_sharpe', 'monthly_sortino', 'monthly_mean', 'monthly_vol',
                        'monthly_skew', 'monthly_kurt', 'best_month', 'worst_month',
                        'avg_up_month', 'avg_down_month'],
            'Yearly_Metrics': ['yearly_sharpe', 'yearly_sortino', 'yearly_mean', 'yearly_vol',
                        'yearly_skew', 'yearly_kurt', 'best_year', 'worst_year',
                        'win_year_perc', 'twelve_month_win_perc']
        }   
        
        # 创建有序的DataFrame
        ordered_data = []
        for group_name, metrics in groups.items():
            # 添加组标题
            ordered_data.append((group_name, pd.NA))
            # 添加该组的指标
            for metric in metrics:
                ordered_data.append((metric, data[metric]))
                
        df = pd.DataFrame(ordered_data, columns=['指标', '值'])
        return df.set_index('指标')


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
        self.backtest_result: ffn.GroupStats = None


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

        # 按code分组，按date排序，用前值填充，去除nan
        df = df.sort_values(['code', 'date']).groupby('code').fillna(method='ffill').dropna()

        self.backtest_result = self._run(df)
    
    @abstractmethod
    def _run(self, df: pd.DataFrame):
        raise NotImplementedError
    
    @abstractmethod
    def get_prices(self) -> pd.DataFrame:
        return self.backtest_result.prices

    @abstractmethod
    def performance_stats(self) -> PerformanceStats:
        """返回策略的性能统计指标"""
        return PerformanceStats.from_ffn_stats(self.backtest_result.stats)
    
    @abstractmethod
    def plot_result(self):
        self.backtest_result.plot()

    @classmethod
    def from_config(cls, config: 'StrategyConfig'):
        raise NotImplementedError


class StrategyCompare:
    def __init__(self, strategies: List[StrategyDef]):
        self.strategies: Dict[str, StrategyDef] = {strategy.name: strategy for strategy in strategies}
        self.result_dict: Dict[str, pd.DataFrame] = {}

    def run(self, start_date: str, end_date: str):
        for name, strategy in self.strategies.items():
            strategy.backtest(start_date, end_date)
            self.result_dict[name] = strategy.performance_stats()

    def performance_stats(self) -> pd.DataFrame:
        """返回所有策略的性能统计指标比较"""
        result_list = []
        for name, strategy in self.strategies.items():
            stats = strategy.performance_stats().to_dataframe()
            stats.columns = [name]
            result_list.append(stats)
        return pd.concat(result_list, axis=1)


class StrategyRegistry:
    """策略注册表，用于存储策略类映射"""
    _strategies_pkg_names: Dict[str, str] = {}  # 存储策略包名
    _strategies_names: Dict[str, str] = {}  # 存储策略名称

    @classmethod
    def register(cls, name: str, strategy_cls: Type['StrategyDef'], pkg_name: str = None) -> None:
        """注册策略类
        
        Args:
            name: 策略名称
            strategy_cls: 策略类
        """
        if strategy_cls.__name__ in cls._strategies_pkg_names:
            raise ValueError(f"策略 {strategy_cls.__name__} 已经注册")
        cls._strategies_pkg_names[strategy_cls.__name__] = pkg_name
        cls._strategies_names[strategy_cls.__name__] = name
    
    @classmethod
    def get_pkg_name(cls, strategy_cls: Union[Type['StrategyDef'], str]) -> str:
        """获取策略包名"""
        if isinstance(strategy_cls, str):
            return cls._strategies_pkg_names.get(strategy_cls, strategy_cls)
        else:
            return cls._strategies_pkg_names.get(strategy_cls.__name__, strategy_cls.__name__)
    
    @classmethod
    def get_name(cls, strategy_cls: Union[Type['StrategyDef'], str]) -> str:
        """获取策略名称"""
        if isinstance(strategy_cls, str):
            return cls._strategies_names.get(strategy_cls, strategy_cls)
        else:
            return cls._strategies_names.get(strategy_cls.__name__, strategy_cls.__name__)
    

def strategy_def(name: str = None):
    """策略定义装饰器
    
    Args:
        name: 策略显示名称，如果不传则使用类名
    """
    def decorator(cls: Type[StrategyDef]) -> Type[StrategyDef]:
        # 获取类的完整包名
        pkg_name = f"{cls.__module__}.{cls.__name__}"
        StrategyRegistry.register(name, cls, pkg_name)
        return cls
    return decorator

