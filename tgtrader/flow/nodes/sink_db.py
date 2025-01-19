# encoding: utf-8

from typing import Callable, Dict, Any, List
import pandas as pd
from peewee import Model
from tgtrader.flow.flow import FlowNode
import os
from tgtrader.utils.db_wrapper import DBWrapper, DBType
from tgtrader.data_provider.dao.models.t_user_table_meta import UserTableMeta
from loguru import logger


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
            
            default_path = os.path.join(os.getcwd(), 'data', f'{self.user}_data.db')
            db_path: str = os.getenv('DATA_PATH', default_path)
            db_name = "flow_sinkdb"

            db_wrapper = DBWrapper(db_path=db_path, db_type=DBType.DUCKDB)

            if is_create_table:
                # 检查表是否存在
                if not db_wrapper.is_table_exists(table_name):
                    db_wrapper.create_table(table_name, field_config)
                    
            else:
                # 检查表是否存在
                if not db_wrapper.is_table_exists(table_name):
                    if process_callback:
                        process_callback(f"表{table_name}不存在", message_type="error")
                    raise ValueError(f"表{table_name}不存在")

            # 对比field_config和meta_info
            meta_info = UserTableMeta.get_table_columns_info(self.user, f"flow_sinkdb", table_name)
            if meta_info != field_config:
                # 是否有新增字段
                old_columns = db_wrapper.get_columns(table_name)
                old_columns = [column.name for column in old_columns]

                add_columns = []
                for new_field in field_config:
                    if new_field['field_name'] not in old_columns:
                        add_columns.append(new_field)
                
                if add_columns:
                    logger.warning(f"新增字段: {add_columns}")
                    db_wrapper.add_column(table_name, add_columns)

                UserTableMeta.update_table_meta(self.user, db_name, table_name, db_path, field_config)

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

                db_wrapper.insert_data(table_name, df)
            
                
        except Exception as e:
            if process_callback:
                process_callback(f"数据库写入失败: {str(e)}", message_type="error")
            raise
