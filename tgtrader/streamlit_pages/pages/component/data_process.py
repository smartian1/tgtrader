# encoding: utf-8
from dataclasses import dataclass, field
import time
import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout
from tgtrader.streamlit_pages.pages.component.data_flow_component import data_source_db_config, python_code_config, sql_config, sink_db_config
import streamlit_shadcn_ui as ui
import enum
import json
from loguru import logger
import arrow
from tgtrader.streamlit_pages.pages.component.widget import display_hint_message
from tgtrader.streamlit_pages.service.flow_config_service import FlowConfigService
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_ace import st_ace
from functools import partial

class NodeType(enum.Enum):
    DATA_SOURCE_DB = "数据源(DB)"
    PROCESSOR_PYTHON_CODE = "处理节点(python代码)"
    PROCESSOR_SQL = "处理节点(sql)"
    SINK_DB = "存储(DB)"

    def get_node_type_by_value(value: str) -> 'NodeType':
        for node_type in NodeType:
            if node_type.value == value:
                return node_type
        raise ValueError(f"未找到匹配的节点类型: {value}")


class FlowType(enum.Enum):
    FACTOR_PROCESS = "facotr_process"


def get_support_node_type_list(flow_type: FlowType):
    if flow_type == FlowType.FACTOR_PROCESS:
        return [NodeType.DATA_SOURCE_DB, NodeType.PROCESSOR_PYTHON_CODE, NodeType.PROCESSOR_SQL, NodeType.SINK_DB]
    else:
        return []

def get_user_name():
    return st.session_state.user_info['username']

def get_selected_node_content(flow_data, sel_node_id):
    for node in flow_data['nodes']:
        if node['id'] == sel_node_id:
            return node['data']['content']
    return ''

def create_select_flow_component(flow_type: FlowType) -> tuple[str, str]:
    """
    返回值： 旧值、新值
    """
    username = get_user_name()
    all_user_flow_info = FlowConfigService.get_all_user_flow_info(username, flow_type.value)
    flow_options = ["新建流程"] + [flow_info.flow_name for flow_info in all_user_flow_info]
    selected_flow = st.selectbox('选择流程', flow_options, key='select_box_flow_id')

    if 'last_selected_flow_name' not in st.session_state:
        st.session_state.last_selected_flow_name = None
    
    old_select_flow_name = st.session_state.last_selected_flow_name
    new_select_flow_name = selected_flow

    st.session_state.last_selected_flow_name = new_select_flow_name

    return old_select_flow_name, new_select_flow_name

def create_flow_component(is_new_flow: bool, flow_type: FlowType, flow_id: str = None):
    nodes = []
    edges = []
    flow_name = ''

    flow_id_input_key = f"flow_id_input_{flow_type.value}_{is_new_flow}" if not flow_id else f"flow_id_input_{flow_id}"

    if not flow_id and not st.session_state.get(flow_id_input_key):
        # 如果是新建flow，且没有保存过（保存就会重新调用create_flow_component）
        flow_id = arrow.now(tz='+08:00').format('YYYYMMDDHHmmssSSS')
    else:
        # 如果是编辑之前的flow，或者是新建flow且保存过
        flow_id = flow_id if flow_id else st.session_state.get(
            flow_id_input_key)

    if not is_new_flow:
        flow_info = FlowConfigService.get_flow_info(flow_id)
        if not flow_info:
            display_hint_message("未找到flow信息", message_type="error")
            return
        
        nodes = flow_info.node_list
        nodes = [StreamlitFlowNode.from_dict(node) for node in nodes]

        edges = flow_info.edge_list
        edges = [StreamlitFlowEdge.from_dict(edge) for edge in edges]

        flow_name = flow_info.flow_name

    flow_component = streamlit_flow(f"{flow_id_input_key}_flow_component",
                                    StreamlitFlowState(nodes, edges),
                                    fit_view=True,
                                    show_controls=True,
                                    allow_new_edges=True,
                                    animate_new_edges=True,
                                    layout=TreeLayout("right"),
                                    enable_pane_menu=True,
                                    enable_edge_menu=True,
                                    enable_node_menu=True,
                                    height=600,
                                    show_minimap=True,
                                    get_node_on_click=True,
                                    )

    flow_id = st.text_input('流程id', key=flow_id_input_key,
                            value=flow_id, disabled=True)

    flow_name = st.text_input('输入流程名称', value=flow_name)

    click_save_btn = ui.button(text="点击保存流程", key="styled_btn_save_flow",
                               className="bg-orange-500 text-white w-full h-14 py-3")

    if click_save_btn:
        if flow_name == '':
            display_hint_message("请输入流程名称", message_type="error")
        else:
            if not __check_edge_label_exist(flow_component.asdict()['edges']):
                st.error("请为每条边设置label")
                return None, None, None
            
            FlowConfigService.save_flow(
                username=get_user_name(),
                flow_id=flow_id,
                flow_type=flow_type.value,
                flow_name=flow_name,
                node_list=flow_component.asdict()['nodes'],
                edge_list=flow_component.asdict()['edges']
            )
            display_hint_message("保存成功", message_type="success")

    return flow_component, click_save_btn, flow_id

def __check_edge_label_exist(edge_list):
    for edge in edge_list:
        if edge['label'].strip() == '':
            return False
    return True

def build_flow_page(flow_type: FlowType):
    """
    新建：
    1. 在内存里构建一个FlowCfg实例
    2. 编辑节点时，将节点信息存储进数据库，is_draft=1； 更新FlowCfg的信息（内存中）
    3. 保存流程时，将FlowCfg实例存储进数据库，节点的is_draft改为0
    4. 如果flow没有保存，那么不会记录该flow的数据

    编辑：
    1. 流程配置读取到FlowCfg实例
    2. 编辑节点时，节点信息存储进数据库（新增一条记录），is_draft=1；更新FlowCfg的信息（内存中）
    3. 保存流程时，更新FlowCfg在数据库中的信息，节点is_draft改为0
    4. 如果flow没有保存，则下次选中该flow时，将其关联的is_draft=1的节点，删除

    """

    FlowConfigService.init_tables()

    old_select_flow_name, new_select_flow_name = create_select_flow_component(flow_type)

    if old_select_flow_name != new_select_flow_name:
        # 如果新的flow是从另一个flow切过来的，则需要删除新的flow，关联的is_draft=1的节点，因为这些节点是上一次编辑且未保存的
        selected_flow_info = FlowConfigService.get_user_flow_info_by_flow_name(
            get_user_name(), new_select_flow_name)
        
        if selected_flow_info:
            FlowConfigService.delete_node_draft(get_user_name(), selected_flow_info.flow_id)


    if new_select_flow_name == '':
        return
    
    flow_id = None
    if new_select_flow_name == "新建流程":
        flow_component, is_save_flow_btn_clicked, flow_id = create_flow_component(
            is_new_flow=True, flow_type=flow_type)
    else:
        select_flow_id = FlowConfigService.get_user_flow_info_by_flow_name(get_user_name(), new_select_flow_name).flow_id
        flow_component, is_save_flow_btn_clicked, flow_id = create_flow_component(
            is_new_flow=False, flow_type=flow_type, flow_id=select_flow_id)

    col1, col2 = st.columns(2)
    with col1:
        btn_run_all = ui.button(text="运行所有节点", key="styled_btn_run_all",
                                className="bg-orange-500 text-white w-full h-14 py-3")
    with col2:
        btn_run_select = ui.button(text="运行到选择的节点", key="styled_btn_run_to_node",
                                   className="bg-orange-500 text-white w-full h-14 py-3")
    
    if btn_run_all:
        run_all(flow_id)

    support_node_type_list = get_support_node_type_list(flow_type)
    if flow_component and flow_component.selected_id and 'edge' not in flow_component.selected_id:
        support_node_type_name = [
            node_type.value for node_type in support_node_type_list]

        st.title(get_selected_node_content(
            flow_component.asdict(), flow_component.selected_id))
        
        node_info = FlowConfigService.get_node_info(flow_id, flow_component.selected_id)

        if node_info:
            cfg = json.loads(node_info.node_cfg)
        else:
            cfg = {}

        if node_info:
            node_type = NodeType.get_node_type_by_value(node_info.node_type)
            idx = support_node_type_name.index(node_type.value)
        else:
            idx = 0

        node_type = st.selectbox("选择节点类型", support_node_type_name, index=idx)
        if node_type == NodeType.DATA_SOURCE_DB.value:
            ret = data_source_db_config(node_id=flow_component.selected_id,
                src_page="data_process", node_cfg=cfg)
        elif node_type == NodeType.PROCESSOR_PYTHON_CODE.value:
            ret = python_code_config(node_id=flow_component.selected_id, src_page="data_process", node_cfg=cfg)
        elif node_type == NodeType.PROCESSOR_SQL.value:
            ret = sql_config(node_id=flow_component.selected_id, src_page="data_process", node_cfg=cfg)
        elif node_type == NodeType.SINK_DB.value:
            ret = sink_db_config(node_id=flow_component.selected_id, src_page="data_process", node_cfg=cfg)

        if ret and not is_save_flow_btn_clicked and not btn_run_all and not btn_run_select:
            # 如果is_save_flow_btn_clicked为True，则不保存节点信息，否则会多出来一条is_draft=1的记录
            FlowConfigService.save_node(
                flow_id=flow_id,
                node_id=flow_component.selected_id,
                node_type=NodeType.get_node_type_by_value(node_type),
                node_cfg=ret
            )

def run_all(flow_id):
    log_placeholder = st.empty()
    st.session_state['run_log'] = ''
    FlowConfigService.run_flow(user=get_user_name(), flow_id=flow_id, info_callback=partial(run_flow_log_callback, log_placeholder=log_placeholder))

def run_flow_log_callback(message: str, message_type: str, log_placeholder) -> None:
    """
    记录流程运行日志并更新日志显示区域
    
    Args:
        message (str): 日志消息内容
        message_type (str): 日志类型（info, warning, error等）
        log_placeholder: Streamlit日志占位符
    """
    timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
    log_prefix = f"[{timestamp}] [{message_type.upper()}] "
    
    old_log = st.session_state['run_log']
    new_log = old_log + log_prefix + message + '\n'
    st.session_state['run_log'] = new_log

    log_placeholder.text_area("运行日志", value=new_log, height=200, disabled=True)
