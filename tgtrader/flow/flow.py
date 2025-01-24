# encoding: utf-8
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Type
from collections import deque
import json
import importlib
import pkgutil
import os
from tgtrader.flow.base import FlowNode


# 节点类型注册表
_node_registry: Dict[str, Type[FlowNode]] = {}


def register_node(node_type: str):
    """节点类型注册装饰器
    
    Args:
        node_type: 节点类型名称
        
    Returns:
        装饰器函数
    """
    def decorator(cls):
        _node_registry[node_type.lower()] = cls
        return cls
    return decorator


def create_node(node_id: str, node_label: str, node_type: str, config: dict, user: str = 'admin') -> FlowNode:
    """根据节点类型创建对应的节点实例
    
    Args:
        node_id: 节点唯一标识
        node_label: 节点名称
        node_type: 节点类型
        config: 节点配置信息
        user: 用户标识
    
    Returns:
        FlowNode: 创建的节点实例
        
    Raises:
        ValueError: 当指定的节点类型未注册时抛出
    """
    node_type = node_type.lower()
    if node_type not in _node_registry:
        raise ValueError(f"未知的节点类型: {node_type}")
        
    node_class = _node_registry[node_type]
    return node_class(node_id=node_id, node_label=node_label, config=config, user=user)


def _initialize_node_registry():
    """初始化节点注册表，自动导入所有节点模块
    
    通过遍历nodes目录下的所有.py文件，自动导入所有节点模块，
    使得@register_node装饰器能够正确注册所有节点类型。
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    nodes_dir = os.path.join(current_dir, 'nodes')
    
    # 遍历nodes目录下的所有模块
    for module_info in pkgutil.iter_modules([nodes_dir]):
        if not module_info.name.startswith('__'):
            # 导入模块，这会触发@register_node装饰器的执行
            importlib.import_module(f'tgtrader.flow.nodes.{module_info.name}')


@dataclass
class Flow:
    """流程控制类"""
    flow_id: str
    node_map: Dict[str, FlowNode] = field(default_factory=dict)
    user: str = 'admin'

    def build_flow(self, node_list: List[dict], edge_list: List[dict]) -> None:
        """根据节点列表和边列表构建流程
        
        Args:
            node_list: 节点配置列表，每个节点包含 node_id 和 config
                node结构：
                {
                    "id": "node_id",
                    "node_type": "数据源(DB)",
                    "node_label": "节点名称",
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
            node = create_node(
                node_id=node_config['id'],
                node_label=node_config['node_label'],
                node_type=node_config['node_type'],
                config=json.loads(node_config.get('config', '{}')),
                user=self.user
            )
            self.node_map[node.node_id] = node

        # 2. 根据边列表连接节点
        for edge in edge_list:
            from_node = self.node_map[edge['source']]
            to_node = self.node_map[edge['target']]
            from_node.add_next_node(to_node, edge['edge_name'])

    def execute_flow(self, process_callback: Callable=None) -> Dict[str, dict]:
        """执行整个流程
        
        Args:
            process_callback: 可选的处理过程回调函数
        
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
            result = node.execute(input_data=None, process_callback=process_callback)
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
                    child_result = child_node.execute(child_input, process_callback)
                    aggregator[child_node.node_id] = child_result
                    queue.append(child_node)

        # -------------------------
        # 5. 返回所有节点的执行结果
        # -------------------------
        return aggregator


# 在模块导入时初始化节点注册表
_initialize_node_registry()
