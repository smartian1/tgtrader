# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from typing import Callable
from tgtrader.utils.duckdb_query_df import DuckDBQueryDF

class SQLProcessorNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        """执行SQL处理节点的处理逻辑。
        
        Args:
            input_data: 包含输入数据的字典，通常包含多个DataFrame
            process_callback: 可选的处理过程回调函数
        
        Returns:
            处理后的DataFrame结果
        
        Raises:
            Exception: 如果SQL执行失败
        """
        if process_callback:
            process_callback(f"【节点: {self.node_label}】开始执行SQL处理", message_type="info")

        try:
            # 获取SQL语句
            sql = self.config.get('content')
            if not sql:
                raise ValueError("未提供SQL语句")

            # 创建DuckDB查询对象，使用第一个输入数据源
            if not input_data:
                raise ValueError("未提供输入数据")
            
            # 使用DuckDBQueryDF创建查询对象并注册所有DataFrame
            with DuckDBQueryDF(input_data) as dq:
                df = dq.query(sql)

            if process_callback:
                process_callback(f"【节点: {self.node_label}】SQL处理成功, 结果行数: {len(df)}", message_type="info")

            return df

        except Exception as e:
            if process_callback:
                process_callback(f"【节点: {self.node_label}】SQL处理失败: {str(e)}", message_type="error")
            raise
