# encoding: utf-8

from tgtrader.flow.flow import register_node
from tgtrader.flow.base import FlowNode
from typing import Callable
from tgtrader.utils.duckdb_query_df import DuckDBQueryDF
import json
from tgtrader.utils.llm_utils import LLMUtils


@register_node("处理节点(llm)")
class ProcessorLLM(FlowNode):
    def execute(self, input_data: dict, process_callback: Callable=None):
        """执行LLM处理节点的处理逻辑。
        
        Args:
            input_data: 包含输入数据的字典，通常包含多个DataFrame
            process_callback: 可选的处理过程回调函数
        
        Returns:
            处理后的LLM结果, dataframe格式
        
        Raises:
            Exception: 如果LLM执行失败
        """
        def callback(message: str, message_type: str):
            if process_callback:
                message = f"【节点: {self.node_label}】{message}"
                process_callback(message, message_type)
            else:
                logger.info(message)


        if process_callback:
            process_callback(f"【节点: {self.node_label}】开始执行LLM处理", message_type="info")

        try:
            config = self.config.get('content')
            if not config:
                raise ValueError("未提供LLM配置")
            
            if not input_data:
                raise ValueError("未提供输入数据")
            
            llm_utils = LLMUtils(config.get("model_id"), config.get("api_key"), config.get("prompt_template"))

            df = llm_utils.run(input_data, callback)

            return df

        except Exception as e:
            if process_callback:
                process_callback(f"【节点: {self.node_label}】SQL处理失败: {str(e)}", message_type="error")
            raise
