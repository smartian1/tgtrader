# encoding: utf-8

import time
from tgtrader.streamlit_pages.dao.t_flow import FlowCfg
from tgtrader.streamlit_pages.dao.t_flow_node import FlowNodeCfg
import json
from typing import Callable, List
from tgtrader.flow.flow import Flow
from loguru import logger

class FlowConfigService:
    def __init__(self):
        pass
    
    @classmethod
    def save_node(cls, flow_id, node_id, node_type, node_cfg):
        """
        根据flow_id和node_id，查询是否有is_draft=1的记录，如果有，则更新，否则插入
        如果是插入，并且之前已经有相同flow_id和node_id的记录，则version+1
        """

        # 查询是否有草稿状态的记录
        existing_draft = FlowNodeCfg.select().where(
            (FlowNodeCfg.flow_id == flow_id) & 
            (FlowNodeCfg.node_id == node_id) & 
            (FlowNodeCfg.is_draft == 1)
        ).first()

        current_timestamp = int(time.time() * 1000)

        if existing_draft:
            # 如果有草稿状态的记录，直接更新
            existing_draft.node_type = node_type.value
            existing_draft.node_cfg = json.dumps(node_cfg)
            existing_draft.update_time = current_timestamp
            existing_draft.save()
        else:
            # 查询该flow_id和node_id的最大版本号
            max_version_record = FlowNodeCfg.select(
                FlowNodeCfg.version
            ).where(
                (FlowNodeCfg.flow_id == flow_id) & 
                (FlowNodeCfg.node_id == node_id)
            ).order_by(
                FlowNodeCfg.version.desc()
            ).first()

            # 确定新的版本号
            new_version = max_version_record.version + 1 if max_version_record else 1

            # 创建新的草稿记录
            FlowNodeCfg.create(
                flow_id=flow_id,
                node_id=node_id,
                node_type=node_type.value,
                node_cfg=json.dumps(node_cfg),
                version=new_version,
                is_draft=1,
                create_time=current_timestamp,
                update_time=current_timestamp
            )

    @classmethod
    def save_flow(cls, username, flow_id, flow_type, flow_name, node_list, edge_list):
        """
        新增：
            1. t_flow表新增一条记录
            2. t_flow的node_list里所有记录，将is_draft=1的记录，更新为is_draft=0
        修改：
            1. t_flow表，更新flow_id=flow_id的记录
            2. t_flow的node_list里所有记录，将is_draft=1的记录，更新为is_draft=0
        """
        current_timestamp = int(time.time() * 1000)

        # 检查是否已存在相同flow_id的记录
        existing_flow = FlowCfg.get_or_none(FlowCfg.flow_id == flow_id)

        if existing_flow:
            # 更新已存在的流程记录
            existing_flow.flow_type = flow_type
            existing_flow.flow_name = flow_name
            existing_flow.node_list = json.dumps(node_list)
            existing_flow.edge_list = json.dumps(edge_list)
            existing_flow.update_time = current_timestamp
            existing_flow.username = username
            existing_flow.save()
        else:
            # 检查是否存在相同flow_name的记录
            existing_flow_name = FlowCfg.select().where(
                (FlowCfg.username == username) & 
                (FlowCfg.flow_name == flow_name)
            ).first()

            if existing_flow_name:
                raise Exception(f"流程名称已存在，请修改流程名称")

            # 创建新的流程记录
            FlowCfg.create(
                username=username,
                flow_id=flow_id,
                flow_type=flow_type,
                flow_name=flow_name,
                node_list=json.dumps(node_list),
                edge_list=json.dumps(edge_list),
                create_time=current_timestamp,
                update_time=current_timestamp
            )

        # 更新节点记录的草稿状态
        for node in node_list:
            node_id = node['id']
            draft_nodes = FlowNodeCfg.select().where(
                (FlowNodeCfg.flow_id == flow_id) & 
                (FlowNodeCfg.node_id == node_id) & 
                (FlowNodeCfg.is_draft == 1)
            )
            
            for node in draft_nodes:
                node.is_draft = 0
                node.save()

    @classmethod
    def get_node_info(cls, flow_id, node_id) -> FlowNodeCfg:
        node_info = FlowNodeCfg.select().where(
            (FlowNodeCfg.flow_id == flow_id) &
            (FlowNodeCfg.node_id == node_id)
        ).order_by(FlowNodeCfg.version.desc()).first()
        return node_info
    
    @classmethod
    def get_flow_info(cls, flow_id) -> FlowCfg:
        flow_info = FlowCfg.get_or_none(FlowCfg.flow_id == flow_id)
        if not flow_info:
            return None
        flow_info.node_list = json.loads(flow_info.node_list)
        flow_info.edge_list = json.loads(flow_info.edge_list)
        return flow_info

    @classmethod
    def get_all_user_flow_info(cls, username, flow_type):
        flow_info = FlowCfg.select().where(
            (FlowCfg.username == username) & 
            (FlowCfg.flow_type == flow_type)
        ).order_by(FlowCfg.create_time.desc())
        return flow_info

    @classmethod
    def get_user_flow_info_by_flow_name(cls, username, flow_name):
        if not flow_name:
            return None

        flow_info = FlowCfg.select().where(
            (FlowCfg.username == username) & 
            (FlowCfg.flow_name == flow_name)
        ).first()
        return flow_info

    @classmethod
    def delete_node_draft(cls, user_name, flow_id):
        """删除用户某个flow下所有is_draft=1的节点配置
        
        Args:
            user_name (str): 用户名
            flow_id (str): 流程id
        """
        # 获取flow信息
        flow_info = cls.get_flow_info(flow_id)
        if not flow_info or flow_info.username != user_name:
            return
        
        # 删除所有草稿状态的节点配置
        draft_nodes = FlowNodeCfg.delete().where(
            (FlowNodeCfg.flow_id == flow_id) &
            (FlowNodeCfg.is_draft == 1)
        ).execute()


    @staticmethod
    def __default_run_flow_callback(message, message_type):
        if message_type == "info":
            logger.info(message)
        elif message_type == "warning":
            logger.warning(message)
        elif message_type == "error":
            logger.error(message)
        else:
            logger.info(message)

    @classmethod
    def run_flow(cls, user: str, flow_id, info_callback: Callable=__default_run_flow_callback):
        """
        info_callback: 
            Args: 
                message: 消息
                message_type: 消息类型，可选值：info, warning, error
        
        process_callback: 
            Args: 
                data: 处理后的数据
        """
        if info_callback:
            info_callback("开始运行流程", message_type="info")

        flow_info = FlowConfigService.get_flow_info(flow_id)

        if not flow_info:
            info_callback("未找到flow信息, 请先保存流程", message_type="error")
            return

        try:
            flow = Flow(flow_id, user=user)

            node_list = cls.__convert_node_list(flow_id, flow_info.node_list)
            edge_list = cls.__convert_edge_list(flow_info.edge_list)
            flow.build_flow(node_list, edge_list)

            flow.execute_flow(info_callback)
        except Exception as e:
            info_callback(f"流程构建失败: {e}", message_type="error")
            logger.exception(e)
            return

    @classmethod
    def __convert_node_list(cls, flow_id, node_list: List[dict]) -> list:
        ret_list = []
        for node in node_list:
            node_id = node['id']
            node_label = node['data']['content']

            node_info = FlowNodeCfg.select().where(
                (FlowNodeCfg.flow_id == flow_id) &
                (FlowNodeCfg.node_id == node_id)
            ).order_by(FlowNodeCfg.version.desc()).first()

            if not node_info:
                raise Exception(f"未找到节点{node_id}的配置信息")
            
            node_type = node_info.node_type
            node_cfg = node_info.node_cfg

            ret_list.append({
                "id": node_id,
                "node_label": node_label,
                "node_type": node_type,
                "config": node_cfg
            })

        return ret_list

    @classmethod
    def __convert_edge_list(cls, edge_list: List[dict]) -> list:
        ret_list = []
        for edge in edge_list:
            ret_list.append({
                "source": edge['source'],
                "target": edge['target'],
                "edge_name": edge['label']
            })
        return ret_list

