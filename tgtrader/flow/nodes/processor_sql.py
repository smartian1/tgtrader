# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from tgtrader.common import DataSource
from tgtrader.utils.duckdb_query import DuckDBQuery
from typing import Callable

class SQLProcessorNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        pass

