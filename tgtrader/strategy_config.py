# encoding: utf-8

from abc import abstractmethod
import json
from typing import Any, Dict, List, Optional, Type
from loguru import logger
from pydantic import BaseModel, Field
from tgtrader.common import SecurityType, RebalancePeriod

def serialize_enum(enum_value):
    if enum_value is None:
        return None
    return enum_value.value


class StrategyConfig(BaseModel):
    # 标的列表
    symbols: Dict[SecurityType, list[str]] = Field(default_factory=dict, description="策略标的列表", serializer=serialize_enum)

    # 回测参数
    rebalance_period: RebalancePeriod = Field(default=RebalancePeriod.Daily, description="回测周期", serializer=serialize_enum)
    initial_capital: float = Field(default=1000000, description="初始资金")
    start_date: str = Field(default="2020-01-01", description="开始日期")
    end_date: str = Field(default="2024-01-01", description="结束日期")

    # 策略类
    strategy_cls: str = Field(default=None, description="策略类名")

    # 策略名称
    strategy_name: str = Field(default="", description="策略名称")

    # 模块名
    module_name: str = Field(default="", description="模块名")

    @abstractmethod
    def to_dict(self) -> dict:
        # Convert enum keys to their string values
        serialized_symbols = {key.value: value for key, value in self.symbols.items()}
        return {
            "symbols": serialized_symbols,
            "rebalance_period": self.rebalance_period.value,
            "initial_capital": self.initial_capital,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "strategy_cls": self.strategy_cls,
            "strategy_name": self.strategy_name,
            "module_name": self.module_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        """反序列化方法，从字典创建 StrategyConfig 对象."""
        # logger.debug(f"Loading strategy config from dict: {data}")
        
        strategy_cls_name = data.get("strategy_cls")
        
        if strategy_cls_name:
            strategy_config_cls = StrategyConfigRegistry.get(f"{strategy_cls_name.split('.')[-1]}Config")
            if strategy_config_cls is None:
                raise ValueError(f"找不到策略config类: {strategy_cls_name}Config")
        else:
            strategy_config_cls = cls  # 如果没有指定策略类，使用当前类
        
        # 处理 symbols 数据
        symbols_data = data.get("symbols", {})
        symbols = {}
        for key, value in symbols_data.items():
            try:
                security_type = SecurityType(key)
                symbols[security_type] = value
            except ValueError:
                logger.warning(f"Warning: Invalid SecurityType '{key}' encountered during deserialization.")
                continue

        # 处理其他字段
        rebalance_period = RebalancePeriod(data.get("rebalance_period"))
        initial_capital = data.get("initial_capital")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        strategy_name = data.get("strategy_name")
        module_name = data.get("module_name")

        # 准备额外参数
        other_params = data.copy()
        other_params.pop("symbols", None)
        other_params.pop("rebalance_period", None)
        other_params.pop("initial_capital", None)
        other_params.pop("start_date", None)
        other_params.pop("end_date", None)
        other_params.pop("strategy_cls", None)
        other_params.pop("strategy_name", None)
        other_params.pop("module_name", None)

        # 创建并返回策略配置对象
        return strategy_config_cls(
            symbols=symbols,
            rebalance_period=rebalance_period,
            initial_capital=initial_capital,
            start_date=start_date,
            end_date=end_date,
            strategy_cls=strategy_cls_name,
            strategy_name=strategy_name,
            module_name=module_name,
            **other_params,
        )

    def to_json(self) -> str:
        dict_config = self.to_dict()
        return json.dumps(dict_config)


class StrategyConfigRegistry:
    """Strategy registry for storing strategy class mappings"""
    _strategies: Dict[str, Type['StrategyConfig']] = {}
    _strategy_names: Dict[str, str] = {}  # 存储策略显示名称

    @classmethod
    def register(cls, name: str, strategy_cls: Type['StrategyConfig'], display_name: str = None) -> None:
        """Register a strategy class with given name"""
        if name in cls._strategies:
            raise ValueError(f"Strategy {name} already registered")
        cls._strategies[name] = strategy_cls
        cls._strategy_names[name] = display_name or name
    
    @classmethod
    def get(cls, name: str) -> Optional[Type['StrategyConfig']]:
        """Get strategy class by name"""
        return cls._strategies.get(name)
    
    @classmethod
    def get_display_name(cls, class_name: str) -> str:
        """获取策略显示名称"""
        return cls._strategy_names.get(class_name, class_name)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """List all registered strategy names"""
        return list(cls._strategies.keys())

def strategy_config_def(cls: Type[StrategyConfig]) -> Type[StrategyConfig]:
    """Decorator to register strategy definitions"""
    StrategyConfigRegistry.register(cls.__name__, cls)
    return cls
