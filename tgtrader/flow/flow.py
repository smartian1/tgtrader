# encoding: utf-8
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class NodeType(Enum):
    SOURCE_DB = "数据源(DB)"
    PROCESSOR_SQL = "处理节点(sql)"
    PROCESSOR_PYTHON = "处理节点(python代码)"
    SINK_DB = "存储(DB)"

@dataclass
class FlowNode:
    """流程节点基类"""
    node_id: str
    config: dict = field(default_factory=dict)
    
    def is_source_node(self) -> bool:
        raise NotImplementedError("Subclass must implement is_source_node method")

    def is_processor_node(self) -> bool:
        raise NotImplementedError("Subclass must implement is_processor_node method")
    
    def is_sink_node(self) -> bool:
        raise NotImplementedError("Subclass must implement is_sink_node method")
    
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

    @classmethod
    def create_node(cls, node_id: str, node_type: str, config: dict) -> 'FlowNode':
        """根据节点类型创建对应的节点实例
        
        Args:
            node_id: 节点唯一标识
            node_type: 节点类型
            config: 节点配置信息
        
        Returns:
            FlowNode: 创建的节点实例
        """
        from tgtrader.flow.nodes import SourceDBNode, SQLProcessorNode, PythonProcessorNode, SinkDBNode
        # 根据节点类型创建不同的节点
        if NodeType(node_type) == NodeType.SOURCE_DB:
            return SourceDBNode(node_id=node_id, config=config)
        elif NodeType(node_type) == NodeType.PROCESSOR_SQL:
            return SQLProcessorNode(node_id=node_id, config=config)
        elif NodeType(node_type) == NodeType.PROCESSOR_PYTHON:
            return PythonProcessorNode(node_id=node_id, config=config)
        elif NodeType(node_type) == NodeType.SINK_DB:
            return SinkDBNode(node_id=node_id, config=config)
        else:
            raise ValueError(f"未知的节点类型: {node_type}")

    def execute(self, input_data: dict) -> dict:
        """执行节点逻辑
        input_data: 前面节点的输入数据
        key是前一节点与当前节点之间边的名称，value是前一节点的输出数据
        {
            "df1": df1,
            "df2": df2,
        }
        """
        raise NotImplementedError("Subclass must implement execute method")
    
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

@dataclass
class Flow:
    """流程控制类"""
    flow_id: str
    node_map: Dict[str, FlowNode] = field(default_factory=dict)
    
    def build_flow(self, node_list: List[dict], edge_list: List[dict]) -> None:
        """根据节点列表和边列表构建流程
        
        Args:
            node_list: 节点配置列表，每个节点包含 node_id 和 config
                node结构：
                {
                    "id": "node_id",
                    "node_type": "数据源(DB)",
                    "config": {
                    }
                }
            edge_list: 边配置列表，每个边包含 from_node_id 和 to_node_id
                edge结构：
                {
                    "source": "from_node_id",
                    "target": "to_node_id",
                    "edge_name": "edge_name"
                }
        """
        
        # 首先创建所有节点
        for node_config in node_list:
            node = FlowNode.create_node(
                node_id=node_config['id'],
                node_type=node_config['node_type'],
                config=node_config.get('config', {})
            )
            self.node_map[node.node_id] = node
            
        # 根据边列表连接节点
        for edge in edge_list:
            from_node = self.node_map[edge['source']]
            to_node = self.node_map[edge['target']]
            from_node.add_next_node(to_node, edge['edge_name'])
            
    
    def execute_flow(self, input_data: dict) -> List[dict]:
        """执行整个流程
        
        Args:
            input_data: 初始输入数据
            
        Returns:
            List[dict]: 所有节点的执行结果列表
        
        计算逻辑：
        1. 起始节点：没有输入边，且当前节点是数据源类型(is_source_node==True)
        2. 从起始节点开始，执行节点逻辑，并获取输出数据
        3. 同一个节点可能有多个输出节点
        4. 同一个节点，可能有多个输入节点
        5. 边的名字，是前一节点输出给下一节点的数据的key
        """
        pass