# encoding: utf-8

from dataclasses import dataclass
from peewee import *
from enum import Enum
from tgtrader.utils.duckdb_peewee import DuckDBDatabase
from typing import List, Dict
from loguru import logger
import pandas as pd
import uuid
from tqdm import tqdm
from typing import Callable
import json


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
    
    def get_columns(self, table_name: str) -> List['ColumnMetadata']:
        """获取表的字段信息。

        Args:
            table_name (str): 表名

        Returns:
            List['ColumnMetadata']: 包含字段信息的列表。每个元素包含字段的名称、类型等元数据信息。

        Raises:
            Exception: 获取表字段信息失败时抛出
        """
        try:
            table_info = self.database.get_columns(table_name)
            return table_info
        except Exception as e:
            logger.error(f"Failed to get table columns for {table_name}: {str(e)}")
            raise e

    def create_table(self, table_name: str, field_config: List[Dict], is_add_create_and_update_time: bool = True) -> None:
        """
        Args:
            table_name: 表名
            field_config: 字段配置列表
        """
        model = self.create_dynamic_model(table_name, field_config, is_add_create_and_update_time)
        model.create_table()

    def add_column(self, table_name: str, field_config: List[Dict]) -> None:
        """向已存在的表中添加新字段。
        
        Args:
            table_name: 表名
            field_config: 新增字段配置列表，样例：
                [
                    {'field_name': 'new_field', 'field_type': 'string', 'comment': '新字段'},
                ]
                
        Raises:
            ValueError: 当字段已存在或配置无效时抛出
            Exception: 添加字段失败时抛出
        """
        # 获取已有字段
        existing_fields = self.get_columns(table_name)
        existing_field_names = [field.name for field in existing_fields]
        
        # 字段类型映射
        field_type_mapping = {
            'string': 'VARCHAR',
            'float': 'FLOAT',
            'int': 'INTEGER',
            'bool': 'BOOLEAN',
            'datetime': 'DATETIME'
        }
        
        try:
            for field in field_config:
                field_name = field.get('field_name')
                field_type = field.get('field_type')
                
                # 验证字段配置
                if not field_name or not field_type:
                    raise ValueError("字段配置错误，必须提供 'field_name' 和 'field_type'")
                
                # 检查字段是否已存在
                if field_name in existing_field_names:
                    raise ValueError(f"字段 '{field_name}' 已存在")
                
                # 获取对应的SQL字段类型
                sql_field_type = field_type_mapping.get(field_type.lower())
                if not sql_field_type:
                    raise ValueError(f"不支持的字段类型：{field_type}")
                
                # 构建ALTER TABLE语句
                is_nullable = field.get('is_nullable', True)
                null_constraint = "" if is_nullable else "NOT NULL"
                
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {sql_field_type} {null_constraint}"
                logger.info(f"alter_sql: {alter_sql}")

                # 执行SQL
                self.database.execute_sql(alter_sql)
                logger.info(f"Successfully added column {field_name} to table {table_name}")
                
        except Exception as e:
            logger.error(f"Failed to add column to table {table_name}: {str(e)}")
            raise e
        
    def get_primary_keys(self, table_name: str) -> List[str]:
        return self.database.get_primary_keys(table_name)

    def insert_data(self, table_name: str, df: pd.DataFrame, batch_size: int = 10000, progress_percent_callback: Callable = None) -> None:
        """将DataFrame数据插入到指定表中，如果记录已存在则更新非主键字段。

        Args:
            table_name (str): 要插入数据的表名
            df (pd.DataFrame): 包含要插入数据的DataFrame

        Raises:
            ValueError: 当DataFrame中缺少必需的主键列时抛出
            Exception: 插入数据失败时抛出

        Notes:
            - DataFrame必须包含表的所有主键字段
            - 使用ON CONFLICT方式处理重复数据
            - 支持单一主键和组合主键
            - 更新时排除create_time字段
        """
        try:
            # 获取表的主键字段列表
            primary_keys = self.get_primary_keys(table_name)
            if not primary_keys:
                raise ValueError(f"表 {table_name} 未定义主键")

            # 验证DataFrame是否包含所有主键字段
            missing_keys = [pk for pk in primary_keys if pk not in df.columns]
            if missing_keys:
                raise ValueError(f"DataFrame缺少必需的主键列: {missing_keys}")

            # 获取所有表字段
            table_fields = self.get_columns(table_name)
            field_names = [field.name for field in table_fields]

            # 过滤出DataFrame中存在的列
            valid_columns = [col for col in df.columns if col in field_names]
            df = df[valid_columns]

            # 构建UPDATE部分的字段（排除主键字段和create_time字段）
            update_fields = [col for col in valid_columns if col not in primary_keys and col != 'create_time']
            
            if self.db_type == DBType.DUCKDB:
                # DuckDB的UPSERT语法
                update_clause = ", ".join([f"{field} = excluded.{field}" for field in update_fields])
                
                # 将DataFrame转换为记录列表
                records = df.to_dict('records')
                # 如果字段是list, dict等, 则转换为json字符串
                for record in records:
                    for key, value in record.items():
                        if isinstance(value, list) or isinstance(value, dict):
                            record[key] = json.dumps(value)
                
                with self.database.atomic():
                    total_records = len(records)
                    for i in tqdm(range(0, total_records, batch_size), desc=f"插入数据到 {table_name}"):
                        batch_df = pd.DataFrame(records[i:i + batch_size])
                        
                        # 创建一个唯一的临时表名
                        temp_table = f"temp_{table_name}_{uuid.uuid4().hex}"
                        
                        try:
                            # 直接从connection创建临时表
                            conn = self.database.connection()
                            conn.register(temp_table, batch_df)
                            
                            # 执行UPSERT操作
                            insert_sql = f"""
                                INSERT INTO {table_name} ({', '.join(valid_columns)})
                                SELECT {', '.join(valid_columns)} FROM {temp_table}
                                ON CONFLICT ({', '.join(primary_keys)})
                                DO UPDATE SET {update_clause}
                            """
                            self.database.execute_sql(insert_sql)
                            
                            # 调用百分比回调
                            if progress_percent_callback:
                                progress_percent = min(100, int((i + batch_size) / total_records * 100))
                                progress_percent_callback(progress_percent)
                        finally:
                            # 清理临时表
                            self.database.execute_sql(f"DROP VIEW IF EXISTS {temp_table}")

            elif self.db_type == DBType.SQLITE:
                # SQLite的UPSERT语法
                update_clause = ", ".join([f"{field} = excluded.{field}" for field in update_fields])
                
                # 将DataFrame转换为字典列表
                records = df.to_dict('records')
                
                # 构建INSERT语句
                placeholders = ", ".join(["?" for _ in valid_columns])
                sql = f"""
                    INSERT INTO {table_name} ({', '.join(valid_columns)})
                    VALUES ({placeholders})
                    ON CONFLICT ({', '.join(primary_keys)})
                    DO UPDATE SET {update_clause}
                """
                
                # 批量执行UPSERT操作
                with self.database.atomic():
                    total_records = len(records)
                    for i in tqdm(range(0, total_records), desc=f"插入数据到 {table_name}"):
                        batch_records = records[i:i + batch_size]
                        
                        # 批量插入，而不是逐条插入
                        batch_values = [
                            tuple(record[col] for col in valid_columns) 
                            for record in batch_records
                        ]
                        
                        # 使用executemany提高性能
                        cursor = self.database.connection().cursor()
                        cursor.executemany(sql, batch_values)
                        
                        # 调用百分比回调
                        if progress_percent_callback:
                            progress_percent = min(100, int((i + batch_size) / total_records * 100))
                            progress_percent_callback(progress_percent)

            logger.info(f"Successfully inserted/updated {len(df)} records into table {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to insert data into table {table_name}: {str(e)}")
            raise e

    def create_dynamic_model(self, table_name: str, field_config: List[Dict], is_add_create_and_update_time: bool = True) -> type:
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
            
            if is_add_create_and_update_time:
                # 如果没有create_time和update_time字段，则添加
                if 'create_time' not in fields:
                    fields['create_time'] = BigIntegerField(null=True, default=int(pd.Timestamp.now().timestamp() * 1000))
                
                if 'update_time' not in fields:
                    fields['update_time'] = BigIntegerField(null=True, default=int(pd.Timestamp.now().timestamp() * 1000))

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

@dataclass
class DynamicTableWrapper:
    table_name: str
    field_config: List[Dict]
    db_path: str
    db_type: DBType
    
    def __post_init__(self):
        self.db_wrapper = DBWrapper(db_path=self.db_path, db_type=self.db_type)
        self.model = self.db_wrapper.create_dynamic_model(self.table_name, self.field_config, is_add_create_and_update_time=True)
    
    def get_model(self):
        return self.model

    def query(self, limit_cnt: int = 10, order_by: str = None, **kwargs) -> List[Dict]:
        """查询数据表中的记录。

        Args:
            limit_cnt (int, optional): 限制返回的记录数量. Defaults to 10.
            order_by (str, optional): 排序字段名，可以包含排序方向，例如: "field_name DESC" 或 "field_name ASC". Defaults to None.
            **kwargs: 查询条件，支持字段名作为关键字参数.

        Returns:
            List[Dict]: 查询结果列表，每个元素为一条记录的字典表示.

        Raises:
            Exception: 查询执行失败时抛出
        """
        try:
            with self.db_wrapper.database.atomic():
                query = self.model.select()
                
                # 添加查询条件
                if kwargs:
                    query = query.where(**kwargs)
                
                # 处理排序
                if order_by:
                    # 解析排序字段和方向
                    order_parts = order_by.split()
                    field_name = order_parts[0]
                    direction = order_parts[1].upper() if len(order_parts) > 1 else 'ASC'
                    
                    # 获取字段对象
                    field = getattr(self.model, field_name)
                    
                    # 应用排序
                    if direction.upper() == 'DESC':
                        query = query.order_by(field.desc())
                    else:
                        query = query.order_by(field.asc())
                
                # 应用限制
                if limit_cnt:
                    query = query.limit(limit_cnt)
                
                return list(query.dicts())
                
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            raise e
