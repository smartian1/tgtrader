# encoding: utf-8

from typing import Callable, Dict, Any, List
import pandas as pd
from peewee import Model
from tgtrader.flow.flow import FlowNode
import os
from tgtrader.utils.db_wrapper import DBWrapper, DBType


class SinkDBNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable = None) -> None:
        """执行数据库写入操作.
        
        Args:
            input_data: 包含DataFrame的输入数据字典
            process_callback: 处理回调函数
            
        Returns:
            None
        """
        try:
            content = self.config.get('content', None)
            if not content:
                if process_callback:
                    process_callback("config里未提供content", message_type="error")
                raise ValueError("config里未提供content")
            
            is_create_table = content['is_create_table']
            table_name = content['table_name']
            field_config = content['field_config']

            if any([is_create_table is None, table_name is None, field_config is None]):
                if process_callback:
                    process_callback("config里未提供is_create_table, table_name, field_config", message_type="error")
                raise ValueError("config里未提供is_create_table, table_name, field_config")
            
            default_path = os.path.join(os.getcwd(), 'data', 'user_data.db')
            db_path: str = os.getenv('DATA_PATH', default_path)

            db = DBWrapper(db_path=db_path, db_type=DBType.DUCKDB)

            if is_create_table:
                # 检查表是否存在
                if db.is_table_exists(table_name):
                    if process_callback:
                        process_callback(f"表{table_name}已存在", message_type="error")
                    raise ValueError(f"表{table_name}已存在")

                # 创建表
                db.create_table(table_name, field_config)

            else:
                # 检查表是否存在
                if not db.is_table_exists(table_name):
                    if process_callback:
                        process_callback(f"表{table_name}不存在", message_type="error")
                    raise ValueError(f"表{table_name}不存在")
            
            # data进行处理
            columns_mapping = dict()
            for field in field_config:
                input_field_mapping = field.get('input_field_mapping', None)
                field_name = field.get('field_name', None)
                if input_field_mapping:
                    columns_mapping[input_field_mapping] = field_name

            # 导入数据
            for _, df in input_data.items():
                reserved_columns = columns_mapping.keys()
                df = df[reserved_columns]
                df.rename(columns=columns_mapping, inplace=True)

                if 'create_time' not in df.columns:
                    df['create_time'] = pd.Timestamp.now().timestamp() * 1000
                if 'update_time' not in df.columns:
                    df['update_time'] = pd.Timestamp.now().timestamp() * 1000

                db.insert_data(table_name, df)
            
                
        except Exception as e:
            if process_callback:
                process_callback(f"数据库写入失败: {str(e)}")
            raise
