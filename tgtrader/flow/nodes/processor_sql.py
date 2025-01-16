# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from tgtrader.common import DataSource
from tgtrader.utils.duckdb_query import DuckDBQuery
from typing import Callable

class SQLProcessorNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        data_source = DataSource(self.config["data_source"])
        sql = self.config["sql"]

        duckdb_query = DuckDBQuery(data_source)
        df = duckdb_query.fetch_df(sql)

        if process_callback:
            process_callback(df)

        return df

