# encoding: utf-8

import logging
from typing import Callable, Dict, Any, Optional
from tgtrader.flow.flow import FlowNode

class PythonProcessorNode(FlowNode):
    """Python处理器节点，用于执行自定义Python函数处理输入数据。
    
    该节点接收Python代码作为配置并在输入数据上执行。
    代码应定义一个以DataFrame为输入的函数。
    """
    
    def execute(self, input_data: Dict[str, Any], process_callback: Optional[Callable] = None) -> Any:
        """在输入数据上执行配置的Python代码。
        
        Args:
            input_data: 包含输入数据的字典，通常包含一个用于DataFrame的'df'键
            process_callback: 可选的处理过程回调函数
            
        Returns:
            执行配置的Python函数后的结果
            
        Raises:
            ValueError: 如果代码执行失败或缺少必需的输入
        """
        try:
            # 获取Python代码
            code = self.config.get('content')
            if not code:
                logging.error("No Python code provided in configuration")
                raise ValueError("Missing Python code in configuration")
                
            # 创建本地命名空间执行代码
            local_vars = {}
            exec(code, globals(), local_vars)

            # 检查是否定义了计算函数
            if 'calc' not in local_vars:
                logging.error("Python code did not define required 'calc' function")
                raise ValueError("Python code must define a 'calc' function")
            
            # 执行计算函数
            result = local_vars['calc'](**input_data)

            # 如果提供了回调函数则调用
            if process_callback:
                process_callback(f"【节点: {self.node_label}】Python代码执行成功, 结果:\n {result}", 'info')
                
            return result
            
        except Exception as e:
            logging.error(f"执行Python处理器节点时发生错误: {str(e)}")
            raise ValueError(f"Failed to execute Python code: {str(e)}")
