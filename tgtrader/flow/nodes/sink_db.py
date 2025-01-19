# encoding: utf-8

from typing import Callable, Dict, Any, List
import pandas as pd
from peewee import Model
from tgtrader.flow.flow import FlowNode
from tgtrader.utils.duckdb_peewee import DuckDBDatabase

class SinkDBNode(FlowNode):
    """数据库写入节点，将数据写入到DuckDB数据库中.
    
    Attributes:
        config (Dict): 配置信息，包含表名、字段配置等
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化数据库写入节点.
        
        Args:
            config: 节点配置信息
        """
        super().__init__(config)
        # 初始化数据库连接
        self.db = DuckDBDatabase('user_db.db')
        self.db.connect()

    def _create_dynamic_model(self, table_name: str, field_config: List[Dict]) -> type:
        """动态创建Peewee模型类.
        
        Args:
            table_name: 表名
            field_config: 字段配置列表
        
        Returns:
            type: 动态创建的Model类
        """
        # 导入所需的字段类型
        from peewee import CharField, FloatField, IntegerField
        
        # 字段类型映射
        field_type_mapping = {
            'string': CharField,
            'float': FloatField,
            'int': IntegerField
        }
        
        # 创建字段字典
        fields = {
            'Meta': type('Meta', (), {
                'database': self.db,
                'table_name': table_name
            })
        }
        
        # 根据配置添加字段
        for field in field_config:
            field_type = field_type_mapping.get(field['field_type'])
            if field_type:
                fields[field['field_name']] = field_type(
                    primary_key=field.get('is_primary_key', False)
                )
        
        # 动态创建模型类
        return type(f'Dynamic{table_name}', (Model,), fields)

    def execute(self, input_data: dict, process_callback: Callable = None) -> None:
        """执行数据库写入操作.
        
        Args:
            input_data: 包含DataFrame的输入数据字典
            process_callback: 处理回调函数
            
        Returns:
            None
        """
        try:
            df = input_data.get('df')
            if df is None or not isinstance(df, pd.DataFrame):
                raise ValueError("输入数据必须包含DataFrame")
            
            content = self.config.get('content', {})
            table_name = content.get('table_name')
            field_config = content.get('field_config', [])
            is_create_table = content.get('is_create_table', False)
            
            if not table_name or not field_config:
                raise ValueError("配置信息不完整")
            
            # 创建动态模型
            model_class = self._create_dynamic_model(table_name, field_config)
            
            # 如果需要创建表
            if is_create_table:
                self.db.create_tables([model_class])
            
            # 准备数据
            records = []
            field_mapping = {
                field['field_name']: field['input_field_mapping']
                for field in field_config
            }
            
            # 转换数据
            for _, row in df.iterrows():
                record = {}
                for db_field, df_field in field_mapping.items():
                    record[db_field] = row[df_field]
                records.append(record)
            
            # 批量插入数据
            with self.db.atomic():
                model_class.insert_many(records).execute()
                
            # 调用回调函数
            if process_callback:
                process_callback(f"成功写入 {len(records)} 条数据到表 {table_name}")
                
        except Exception as e:
            if process_callback:
                process_callback(f"数据库写入失败: {str(e)}")
            raise
        finally:
            self.db.close()
