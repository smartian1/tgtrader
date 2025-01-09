# encoding: utf-8
from tgtrader.common import DataSource
from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
import streamlit as st
from streamlit_ace import st_ace
from .data_meta import build_db_meta_info

def data_source_config(src_page: str):
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.selectbox("数据源", ["Akshare"], key=f"data_source_config_{src_page}")

    placeholder = """
输入：该节点必须为起始节点，不能有其他输入

示例：
select * from t_kdata where date>='2024-01-01'
    """

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=True,
                       placeholder=placeholder,
                       show_gutter=True,
                       key=f"{src_page}_sql_query"
                       )
    
    build_db_meta_info(src_page=f"{src_page}_data_source_config")



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
                         height=300, auto_update=True,
                         placeholder=placeholder,
                         show_gutter=True,
                         key=f"{src_page}_python_code_config"
                         )


def sql_config(src_page: str):
    placeholder = """
支持的输入：
1. SQL语句
2. Python代码

示例：
select * from df where code='000001'
    """

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=True,
                       placeholder=placeholder,
                       show_gutter=True,
                       key=f"{src_page}_sql_config"
                       )


def storage_config(src_page: str):
    create_table = st.checkbox("是否新建表", key=f"{src_page}_storage_config_create_table")
    if create_table:
        columns = st.text_area("表字段和类型", placeholder="请输入表字段和类型",
                               show_gutter=True,
                               key=f"{src_page}_storage_config_columns"
                               )
    # 其他存储配置


