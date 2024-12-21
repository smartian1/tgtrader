# encoding: utf-8

from abc import abstractmethod
import json
from typing import Any, Dict, Type
from pydantic import BaseModel, Field
from tgtrader.common import SecurityType
from tgtrader.strategy import RebalancePeriod

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
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        """反序列化方法，从字典创建 StrategyConfig 对象."""
        symbols_data = data.get("symbols", {})
        symbols = {}
        for key, value in symbols_data.items():
            try:
                security_type = SecurityType(key)
                symbols[security_type] = value
            except ValueError:
                # Handle invalid SecurityType string (optional: log a warning, raise an error, etc.)
                print(f"Warning: Invalid SecurityType '{key}' encountered during deserialization.")
                continue  # Or raise ValueError

        return cls(
            symbols=symbols,
            rebalance_period=RebalancePeriod(data.get("rebalance_period")),
            initial_capital=data.get("initial_capital"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            strategy_cls=data.get("strategy_cls"),
        )

    def to_json(self) -> str:
        dict_config = self.to_dict()
        return json.dumps(dict_config)
