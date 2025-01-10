# encoding: utf-8
import pandas as pd
from tgtrader.common import DataSource
from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
import streamlit as st
from streamlit_ace import st_ace
from .data_meta import build_db_meta_info

def data_source_db_config(src_page: str):
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.selectbox("数据源", ["Akshare"], key=f"data_source_config_{src_page}")

    placeholder = """
输入：该节点必须为起始节点，不能有其他输入

示例：
select * from t_kdata where date>='2024-01-01'
    """

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, 
                       auto_update=False,
                       placeholder=placeholder,
                       show_gutter=True,
                       key=f"{src_page}_sql_query"
                       )
    
    build_db_meta_info(src_page=f"{src_page}_data_source_config")

    return {
        'type': 'data_source_db',
        'content': sql_query
    }



def python_code_config(src_page: str):
    placeholder = """
连接到该节点的前方边的名字，就是传入到该节点的入参名，可以直接对其进行操作

支持的输入：
1. SQL语句
2. Python代码

输出：
必须是DataFrame

示例：
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()
    """

    python_code = st_ace(language='python', theme='dracula',
                         height=300, auto_update=False,
                         placeholder=placeholder,
                         show_gutter=True,
                         key=f"{src_page}_python_code_config"
                         )
    
    return {
        'type': 'processor_python_code',
        'content': python_code
    }


def sql_config(src_page: str):
    placeholder = """
支持的输入：
1. SQL语句
2. Python代码

示例：
select * from df where code='000001'
    """

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=False,
                       placeholder=placeholder,
                       show_gutter=True,
                       key=f"{src_page}_sql_config"
                       )
    
    return {
        'type': 'processor_sql',
        'content': sql_query
    }


def sink_db_config(src_page: str):
    is_create_table = st.checkbox("是否新建表", key=f"{src_page}_storage_config_create_table")
    col1, col2 = st.columns([1, 5])
    if is_create_table:
        with col1:
            st.text_input("表名", placeholder="请输入新建表名", key=f"{src_page}_storage_config_table_name")
        # 字段配置表格 - 新建表可以完全自定义
        field_config_df = pd.DataFrame({
            "字段名": ['sample_field'],
            "类型": ['varchar(10)'],
            "描述": ['示例字段'],
            "是否主键": [False],
            "映射字段": ['sample_field']
        })
        st.data_editor(field_config_df,
                      key=f"{src_page}_storage_config_field_config_new",
                      num_rows="dynamic",
                       column_config={
                          "字段名": st.column_config.TextColumn(
                              "字段名",
                              required=True
                          ),
                           "类型": st.column_config.SelectboxColumn(
                              "类型",
                              options=[
                                  "varchar", "float", "int"],
                              required=True
                          ),
                           "描述": st.column_config.TextColumn(
                              "描述",
                              required=True
                          ),
                           "是否主键": st.column_config.CheckboxColumn(
                              "是否主键",
                              disabled=False,
                          )
                       })
    else:
        with col1:
            st.selectbox("表名", options=['factor_table'], key=f"{src_page}_storage_config_table_name")
        # 字段配置表格 - 已有表主键不可修改
        field_config_df = pd.DataFrame({
            "字段名": ["trade_date", "code", "factor_value"],
            "类型": ["date", "varchar(10)", "float"],
            "描述": ["交易日期", "股票代码", "因子值"],
            "是否主键": [True, True, False],
            "映射字段": ["trade_date", "code", "value"]
        })
        st.data_editor(field_config_df,
                      key=f"{src_page}_storage_config_field_config_existing",
                      num_rows="dynamic",
                      column_config={
                          "字段名": st.column_config.TextColumn(
                              "字段名",
                              required=True
                          ),
                          "类型": st.column_config.SelectboxColumn(
                              "类型",
                              options=["date", "varchar(10)", "float", "int", "text", "boolean"],
                              required=True
                          ),
                          "描述": st.column_config.TextColumn(
                              "描述",
                              required=True
                          ),
                          "是否主键": st.column_config.CheckboxColumn(
                              "是否主键",
                              disabled=True,
                              help="已有表的主键不可修改"
                          )
                      })


    btn_save =st.button("保存配置", key=f"{src_page}_storage_config_save")

    if btn_save:
        return {
            'type': 'sink_db',
            'content': {
                'is_create_table': is_create_table,
            }
        }
    else:
        return None
