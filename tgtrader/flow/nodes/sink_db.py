# encoding: utf-8

from typing import Callable, Dict, Any, List
import pandas as pd
from peewee import Model
from tgtrader.flow.flow import FlowNode, register_node
import os
from tgtrader.utils.db_wrapper import DBWrapper, DBType
from loguru import logger
from tgtrader.utils.db_path_utils import get_user_data_db_path
from tgtrader.streamlit_pages.dao.t_user_table_meta import UserTableMeta


# DuckDB 保留关键字列表
DUCKDB_RESERVED_KEYWORDS = {
    'add', 'all', 'alter', 'and', 'any', 'as', 'asc', 'between', 'by', 'case', 
    'cast', 'check', 'column', 'commit', 'copy', 'create', 'cross', 'current', 
    'default', 'delete', 'desc', 'distinct', 'drop', 'else', 'end', 'escape', 
    'except', 'exists', 'extract', 'false', 'filter', 'following', 'foreign', 
    'from', 'full', 'group', 'having', 'if', 'in', 'inner', 'insert', 'intersect', 
    'into', 'is', 'join', 'left', 'like', 'limit', 'natural', 'not', 'null', 
    'offset', 'on', 'or', 'order', 'outer', 'over', 'primary', 'references', 
    'right', 'rollback', 'select', 'set', 'table', 'then', 'true', 'union', 
    'unique', 'update', 'using', 'values', 'when', 'where', 'window', 'with'
}


@register_node("存储(DB)")
class SinkDBNode(FlowNode):
    @staticmethod
    def _validate_field_names(field_config: List[Dict[str, Any]]) -> None:
        """验证字段名是否使用了DuckDB保留关键字.
        
        Args:
            field_config: 字段配置列表
            
        Raises:
            ValueError: 当字段名使用了保留关键字时抛出
        """
        invalid_fields = []
        for field in field_config:
            field_name = field.get('field_name', '').lower()
            if field_name in DUCKDB_RESERVED_KEYWORDS:
                invalid_fields.append(field_name)
        
        if invalid_fields:
            raise ValueError(f"以下字段名是DuckDB保留关键字，不能使用: {', '.join(invalid_fields)}")

    def execute(self, input_data: dict, process_callback: Callable = None) -> None:
        """执行数据库写入操作.
        
        Args:
            input_data: 包含DataFrame的输入数据字典
            process_callback: 处理回调函数
            
        Returns:
            None
        """
        
        last_progress = -1
        def percent_callback(progress: int):
            nonlocal last_progress
            if process_callback and progress != last_progress:
                process_callback(f"【节点: {self.node_label}】进度: {progress}%", message_type="info")
                last_progress = progress

        try:
            content = self.config.get('content', None)
            if not content:
                if process_callback:
                    process_callback(f"【节点: {self.node_label}】config里未提供content", message_type="error")
                raise ValueError("config里未提供content")
            
            is_create_table = content['is_create_table']
            table_name = content['table_name']
            field_config = content['field_config']

            if any([is_create_table is None, table_name is None, field_config is None]):
                if process_callback:
                    process_callback(f"【节点: {self.node_label}】config里未提供is_create_table, table_name, field_config", message_type="error")
                raise ValueError("config里未提供is_create_table, table_name, field_config")
            
            # 验证字段名
            try:
                self._validate_field_names(field_config)
            except ValueError as e:
                if process_callback:
                    process_callback(f"【节点: {self.node_label}】字段名验证失败: {str(e)}", message_type="error")
                raise
            
            db_path = get_user_data_db_path(self.user)
            db_name = "flow_sinkdb"

            # 添加初始进度回调
            if process_callback:
                process_callback(f"【节点: {self.node_label}】准备连接数据库", message_type="info")

            db_wrapper = DBWrapper(db_path=db_path, db_type=DBType.DUCKDB)

            if is_create_table:
                # 检查表是否存在
                if not db_wrapper.is_table_exists(table_name):
                    if process_callback:
                        process_callback(f"【节点: {self.node_label}】创建新表", message_type="info")
                    db_wrapper.create_table(table_name, field_config)
                    
            else:
                # 检查表是否存在
                if not db_wrapper.is_table_exists(table_name):
                    if process_callback:
                        process_callback(f"【节点: {self.node_label}】表{table_name}不存在", message_type="error")
                    raise ValueError(f"表{table_name}不存在")

            # 对比field_config和meta_info
            if process_callback:
                process_callback(f"【节点: {self.node_label}】检查表结构", message_type="info")

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
                    if process_callback:
                        process_callback(f"【节点: {self.node_label}】发现新字段: {add_columns}", message_type="warning")
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
            total_records = 0
            total_dfs = len(input_data)
            for idx, (_, df) in enumerate(input_data.items(), 1):
                if process_callback:
                    process_callback(f"【节点: {self.node_label}】处理数据集 {idx}/{total_dfs}", message_type="info")

                reserved_columns = columns_mapping.keys()

                # df的列，与reserved_columns求交集
                df_columns = df.columns
                reserved_columns = [col for col in reserved_columns if col in df_columns]

                df = df[reserved_columns]
                df.rename(columns=columns_mapping, inplace=True)

                if 'create_time' not in df.columns:
                    df['create_time'] = pd.Timestamp.now().timestamp() * 1000
                if 'update_time' not in df.columns:
                    df['update_time'] = pd.Timestamp.now().timestamp() * 1000

                if process_callback:
                    process_callback(f"【节点: {self.node_label}】开始写入数据集 {idx}", message_type="info")

                db_wrapper.insert_data(
                    table_name, df, progress_percent_callback=percent_callback)
                
                total_records += len(df)

            if process_callback:
                process_callback(f"【节点: {self.node_label}】数据写入完成", message_type="success")
                
        except Exception as e:
            if process_callback:
                process_callback(f"【节点: {self.node_label}】数据库写入失败: {str(e)}", message_type="error")
            raise
