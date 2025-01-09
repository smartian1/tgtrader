# encoding: utf-8
import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout
import json
from streamlit_ace import st_ace

node_type_dict = {
    "data_source_db": "数据源(DB)",
    "python_code": "处理节点(python代码)",
    "sql": "处理节点(sql)",
    "storage_db": "存储(DB)"
}

def run():
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
    
    
    if new_state.selected_id and 'edge' not in new_state.selected_id:
        node_type = st.selectbox("选择节点类型", list(node_type_dict.values()))
        if node_type == node_type_dict["data_source_db"]:
            data_source_config()
        elif node_type == node_type_dict["python_code"]:
            python_code_config()
        elif node_type == node_type_dict["sql"]:
            sql_config()
        elif node_type == node_type_dict["storage_db"]:
            storage_config()


def data_source_config():
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.selectbox("数据源", ["Akshare"])
    with col2:  
        table_name = st.selectbox("表名", get_table_names(data_source))

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=True,
                       placeholder="请输入sql语句",
                       show_gutter=True,
                       )
        

def python_code_config():
    python_code = st_ace(language='python', theme='dracula',
                       height=300, auto_update=True,
                       placeholder="请输入python代码",
                       show_gutter=True,
                       )


def sql_config():
    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=True,
                       placeholder="请输入sql语句",
                       show_gutter=True,
                       )


def storage_config():
    create_table = st.checkbox("是否新建表")
    if create_table:
        columns = st.text_area("表字段和类型", placeholder="请输入表字段和类型",
                               show_gutter=True,
                               )
    # 其他存储配置
    
def get_table_names(data_source):
    if data_source == "Akshare":
        return ["stock_zh_a_spot_em", "stock_zh_a_spot_em_detail_sina"]
    return []
