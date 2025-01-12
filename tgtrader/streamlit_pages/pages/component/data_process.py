# encoding: utf-8
import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout
from tgtrader.streamlit_pages.pages.component.data_flow_component import data_source_db_config, python_code_config, sql_config, sink_db_config
import streamlit_shadcn_ui as ui

node_type_dict = {
    "data_source_db": "数据源(DB)",
    "processor_python_code": "处理节点(python代码)",
    "processor_sql": "处理节点(sql)",
    "sink_db": "存储(DB)"
}


def build_flow_page(support_node_type_list: list):
    """
    新建：
    1. 在内存里构建一个FlowCfg实例
    2. 编辑节点时，将节点信息存储进数据库，is_draft=1； 更新FlowCfg的信息（内存中）
    3. 保存流程时，将FlowCfg实例存储进数据库，节点的is_draft改为0

    编辑：
    1. 流程配置读取到FlowCfg实例
    2. 编辑节点时，节点信息存储进数据库（新增一条记录），is_draft=1；更新FlowCfg的信息（内存中）
    3. 保存流程时，更新FlowCfg在数据库中的信息，节点is_draft改为0

    """

    
    flow_options = ['', "新建流程"] + ["流程1", "流程2", "流程3"] 
    selected_flow = st.selectbox('选择流程', flow_options)
    
    if selected_flow == '':
        return
    if selected_flow == "新建流程":
        new_state = streamlit_flow('new_flow', 
                    StreamlitFlowState([], []), # Start with an empty state, or with some pre-initialized state
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

        flow_name = st.text_input('输入流程名称')
        
        ui.button(text="点击保存流程", key="styled_btn_save_flow",
                    className="bg-orange-500 text-white w-full h-14 py-3")
    else:
        new_state = streamlit_flow('edit_flow',
                                   StreamlitFlowState([], []),
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
                                   get_node_on_click=True
                                   )
        ui.button(text="点击保存流程", key="styled_btn_save_flow", 
                    className="bg-orange-500 text-white w-full h-14 py-3")
    
    col1, col2 = st.columns(2)
    with col1:
        btn_flow = ui.button(text="运行所有节点", key="styled_btn_run_all",
                             className="bg-orange-500 text-white w-full h-14 py-3")
    with col2:
        btn_save = ui.button(text="运行到选择的节点", key="styled_btn_run_to_node",
                             className="bg-orange-500 text-white w-full h-14 py-3")

    
    if new_state.selected_id and 'edge' not in new_state.selected_id:
        support_node_type_name = [node_type_dict[node_type] for node_type in support_node_type_list]

        node_type = st.selectbox("选择节点类型", support_node_type_name)
        if node_type == node_type_dict["data_source_db"]:
            data_source_db_config(src_page="data_process")
        elif node_type == node_type_dict["processor_python_code"]:
            python_code_config(src_page="data_process")
        elif node_type == node_type_dict["processor_sql"]:
            sql_config(src_page="data_process")
        elif node_type == node_type_dict["sink_db"]:
            sink_db_config(src_page="data_process")

