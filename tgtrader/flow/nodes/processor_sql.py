# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from tgtrader.common import DataSource
from tgtrader.utils.duckdb_query import DuckDBQuery


class SQLProcessorNode(FlowNode):
    def execute(self, input_data: dict):
        data_source = DataSource(self.config["data_source"])
        sql = self.config["sql"]

        duckdb_query = DuckDBQuery(data_source)
        df = duckdb_query.fetch_df(sql)

        return df

