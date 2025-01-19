# encoding: utf-8

from dataclasses import dataclass
from peewee import *
from enum import Enum
from tgtrader.utils.duckdb_peewee import DuckDBDatabase
from typing import List, Dict
from loguru import logger


class DBType(Enum):
    SQLITE = "sqlite"
    DUCKDB = "duckdb"

@dataclass
class DBWrapper:
    database: Database = None
    db_path: str = None
    db_type: DBType = None

    def __post_init__(self):
        if not self.db_path:
            raise ValueError("db_path is required")
        
        if not self.db_type:
            raise ValueError("db_type is required")
        
        if self.db_type == DBType.SQLITE:
            self.database = SqliteDatabase(self.db_path)
        elif self.db_type == DBType.DUCKDB:
            self.database = DuckDBDatabase(self.db_path)
        else:
            raise NotImplementedError(f"Unsupported database type: {self.db_type}")

    def is_table_exists(self, table_name: str) -> bool:
        return self.database.table_exists(table_name)
    
    def create_table(self, table_name: str, field_config: List[Dict]) -> None:
        """
        Args:
            table_name: 表名
            field_config: 字段配置列表
        """
        model = self._create_dynamic_model(table_name, field_config)
        model.create_table()

    def _create_dynamic_model(self, table_name: str, field_config: List[Dict]) -> type:
        """动态创建Peewee模型类.
        
        Args:
            table_name: 表名
            field_config: 字段配置列表，样例：
                field_config = [
                    {'field_name': 'code', 'field_type': 'string', 'is_primary_key': True, 'comment': '股票代码'},
                    {'field_name': 'date', 'field_type': 'string', 'is_primary_key': True, 'comment': '交易日期'},
                    {'field_name': 'price', 'field_type': 'float', 'comment': '股票价格'},
                ]
        
        Returns:
            type: 动态创建的Model类
        """
        # 字段类型映射
        field_type_mapping = {
            'string': CharField,
            'float': FloatField,
            'int': IntegerField,
            'bool': BooleanField,
            'datetime': DateTimeField
        }
        
        # 创建字段字典
        fields = {}
        # 记录主键字段
        primary_keys = []

        try:
            # 根据配置添加字段
            for field in field_config:
                field_name = field.get('field_name')
                field_type = field.get('field_type')
                
                # 必须提供字段名和类型
                if not field_name or not field_type:
                    raise ValueError(f"字段配置错误，必须提供 'field_name' 和 'field_type'")

                peewee_field = field_type_mapping.get(field_type.lower())
                if peewee_field:
                    # 创建字段时添加comment参数
                    fields[field_name] = peewee_field(
                        null=field.get('is_nullable', True),
                    )
                    # 如果是主键字段，添加到主键列表
                    if field.get('is_primary_key', False):
                        primary_keys.append(field_name)
                else:
                    raise ValueError(f"不支持的字段类型：{field_type}")

            # 动态创建Meta类，设置复合主键
            Meta = type('Meta', (), {
                'database': self.database, 
                'table_name': table_name,
                'primary_key': CompositeKey(*primary_keys) if len(primary_keys) > 1 else None
            })
            
            # 如果只有一个主键，直接在字段上设置
            if len(primary_keys) == 1:
                primary_field = next(f for f in field_config if f['field_name'] == primary_keys[0])
                fields[primary_keys[0]] = field_type_mapping[
                    primary_field['field_type'].lower()
                ](
                    primary_key=True, 
                    null=False,
                )
            
            # 动态创建模型类并返回
            dynamic_model = type(f'Dynamic{table_name}', (Model,), {**fields, 'Meta': Meta})
            
            return dynamic_model
        except Exception as e:
            logger.exception(e)
            raise e
