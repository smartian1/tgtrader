# encoding: utf-8

from tgtrader.flow.flow import FlowNode
from typing import Callable

class SinkDBNode(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        pass
