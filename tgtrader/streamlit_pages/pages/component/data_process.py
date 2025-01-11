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
    new_state = streamlit_flow('fully_interactive_flow', 
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

