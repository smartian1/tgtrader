# encoding: utf-8

from tgtrader.common import DataSource
from peewee import Model
from typing import Dict, Tuple, Type, Callable
from functools import wraps


def register_model(data_source: DataSource, table_name: str) -> Callable[[Type[Model]], Type[Model]]:
    """
    装饰器用于注册Model类到ModelRegister
    
    Args:
        data_source: 数据源
        table_name: 表名
        
    Returns:
        装饰后的Model类
    """
    def decorator(cls: Type[Model]) -> Type[Model]:
        ModelRegister.register_model(data_source, table_name, cls)
        return cls
    return decorator


class ModelRegister:
    # 初始化register_map
    register_map: Dict[Tuple[DataSource, str], Model] = {}

    @classmethod
    def register_model(cls,
                      data_source: DataSource,
                      table_name: str,
                      model: Model):
        cls.register_map[(data_source, table_name)] = model

    @classmethod
    def get_model(cls, data_source: DataSource, table_name: str) -> Model:
        return cls.register_map[(data_source, table_name)]

