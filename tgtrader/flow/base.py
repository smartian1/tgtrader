from dataclasses import dataclass, field
from typing import Dict, List, Callable


@dataclass
class FlowNode:
    """流程节点基类"""
    node_id: str
    node_label: str
    config: dict = field(default_factory=dict)
    user: str = 'admin'

    # 保存后续节点及其对应的边名称
    """
    [
        {
            "edge_name": "df1",
            "node": FlowNodeObject1
        },
        {
            "edge_name": "df2",
            "node": FlowNodeObject2
        },
    ]
    """
    next_nodes: List[Dict[str, 'FlowNode']] = field(default_factory=list)

    def execute(self, input_data: dict, process_callback: Callable=None) -> dict:
        """执行节点逻辑
        
        Args:
            input_data: 来自所有父节点的输出数据，结构类似：
                {
                    "某条边edge_name1": parent_node_output_dict,
                    "某条边edge_name2": parent_node_output_dict,
                    ...
                }
            process_callback: 可选的处理过程回调函数
        
        Returns:
            dict: 本节点的输出结果字典，供后续节点使用
        """
        # 这里是基类默认实现，子类应重写实际逻辑
        raise NotImplementedError("subclass should implement this method")

    def add_next_node(self, node: 'FlowNode', edge_name: str) -> None:
        """添加后续节点
        
        Args:
            node: 要添加的后续节点
            edge_name: 边名称
        """
        self.next_nodes.append({
            "edge_name": edge_name,
            "node": node
        }) 