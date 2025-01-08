# encoding: utf-8
import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout
import json
from streamlit_ace import st_ace
from streamlit_autorefresh import st_autorefresh

def run():
    refresh_cnt = st_autorefresh(interval=1000)

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
        node_type = st.selectbox("选择节点类型", ["数据源", "python代码", "sql", "存储"])
        if node_type == "数据源":
            data_source_config(refresh_cnt)
        elif node_type == "python代码":
            python_code_config()
        elif node_type == "sql":
            sql_config()
        elif node_type == "存储":
            storage_config()

# 新增各节点类型的配置方法


def data_source_config(refresh_cnt):
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.selectbox("数据源", ["Akshare"])
    with col2:  
        table_name = st.selectbox("表名", get_table_names(data_source))

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=True)

    btn = st.button("保存")

    if refresh_cnt % 10 == 0 or btn:
        st.write(sql_query)
        st.success("自动保存成功")
        

def python_code_config():
    # 配置 Python 代码节点
    code = st.text_area("代码输入框")
    # 在此处处理代码输入

def sql_config():
    # 配置 SQL 节点
    sql_query = st.text_area("SQL 输入框")
    # 在此处处理 SQL 查询

def storage_config():
    # 配置存储节点
    create_table = st.checkbox("是否新建表")
    if create_table:
        columns = st.text_area("表字段和类型")
        # 在此处处理表字段和类型
    # 其他存储配置
    
def get_table_names(data_source):
    if data_source == "Akshare":
        return ["stock_zh_a_spot_em", "stock_zh_a_spot_em_detail_sina"]
    return []
