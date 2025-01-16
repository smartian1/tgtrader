# encoding: utf-8
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque


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
        # 在此处做实际的子类导入，以免循环引用
        from tgtrader.flow.nodes import SourceDBNode, SQLProcessorNode, PythonProcessorNode, SinkDBNode

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
        
        input_data: 
            来自所有父节点的输出数据，结构类似：
            {
                "某条边edge_name1": parent_node_output_dict,
                "某条边edge_name2": parent_node_output_dict,
                ...
            }
        
        Returns:
            dict: 本节点的输出结果字典，供后续节点使用
        """
        # 这里是基类默认实现，子类应重写实际逻辑
        # 示例：简单地把所有父节点输出合并，并标记本节点id
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
        # 1. 创建所有节点
        for node_config in node_list:
            node = FlowNode.create_node(
                node_id=node_config['id'],
                node_type=node_config['node_type'],
                config=node_config.get('config', {})
            )
            self.node_map[node.node_id] = node

        # 2. 根据边列表连接节点
        for edge in edge_list:
            from_node = self.node_map[edge['source']]
            to_node = self.node_map[edge['target']]
            from_node.add_next_node(to_node, edge['edge_name'])

    def execute_flow(self, input_data: dict=None) -> Dict[str, dict]:
        """
        执行整个流程
        
        Args:
            input_data: 初始输入数据，一般只会被源节点（is_source_node() == True）的执行用到。
        
        Returns:
            Dict[str, dict]: 返回每个节点的执行结果，key 为 node_id，value 为该节点的输出数据
        """
        # -------------------------
        # 1. 统计每个节点的入度
        # -------------------------
        in_degree = {node_id: 0 for node_id in self.node_map}
        # 依赖 build_flow 中的信息，统计当前图中每个节点的入度
        for node_id, node in self.node_map.items():
            for child_info in node.next_nodes:
                child_node = child_info["node"]
                in_degree[child_node.node_id] += 1

        # -------------------------
        # 2. 找到所有 "起始节点"
        #    通常是 is_source_node == True 或者 in_degree == 0
        # -------------------------
        start_nodes = []
        for node_id, node in self.node_map.items():
            if in_degree[node_id] == 0:
                start_nodes.append(node)

        # -------------------------
        # 3. 准备一个队列做拓扑执行，并构建存储节点输出的 aggregator
        # -------------------------
        queue = deque()
        aggregator: Dict[str, dict] = {}  # 用于存储每个节点的执行结果

        # 先把起始节点放进队列，并执行它们
        for node in start_nodes:
            # 对于源节点，我们通常把全局的 input_data 传给它执行
            # 对于非源但 in_degree=0 的节点，也可以传入一个空字典，或者同样传入 input_data
            node_input = input_data
            result = node.execute(node_input)
            aggregator[node.node_id] = result
            queue.append(node)

        # -------------------------
        # 4. BFS/拓扑序执行
        # -------------------------
        while queue:
            parent_node = queue.popleft()
            parent_output = aggregator[parent_node.node_id]

            # 遍历所有子节点，将父节点输出分发给子节点
            for child_info in parent_node.next_nodes:
                edge_name = child_info["edge_name"]
                child_node = child_info["node"]

                # 如果子节点还没在 aggregator 中初始化，就先放个空壳
                if child_node.node_id not in aggregator:
                    aggregator[child_node.node_id] = {}

                # 将父节点的输出放到子节点的输入容器中，key=边名称
                # 注意：不同父节点通过不同的 edge_name 合并到同一个 dict 中
                aggregator[child_node.node_id][edge_name] = parent_output

                # 减少子节点的入度
                in_degree[child_node.node_id] -= 1

                # 当子节点入度归零，说明子节点所有父节点的输出都收集完了
                if in_degree[child_node.node_id] == 0:
                    # 此时可以执行子节点
                    child_input = aggregator[child_node.node_id]
                    child_result = child_node.execute(child_input)
                    aggregator[child_node.node_id] = child_result
                    queue.append(child_node)

        # -------------------------
        # 5. 返回所有节点的执行结果
        # -------------------------
        return aggregator
