# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from typing import Callable
from tgtrader.common import DataSource
from tgtrader.utils.duckdb_query import DuckDBQuery

class SourceDBNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        if process_callback:
            process_callback(f"【节点: {self.node_label}】开始执行数据源查询", message_type="info")

        try:
            data_source = DataSource(self.config["data_source"].lower())
            sql = self.config["content"]

            duckdb_query = DuckDBQuery(data_source)
            df = duckdb_query.fetch_df(sql)
        except Exception as e:
            if process_callback:
                process_callback(f"【节点: {self.node_label}】数据源: {data_source}, 查询SQL: {sql}, 查询失败: {e}", message_type="error")
            raise e

        if process_callback:
            process_callback(f"【节点: {self.node_label}】数据源: {data_source}, 查询SQL: {sql}, 查询结果数量: {len(df)}", message_type="info")

        return df
