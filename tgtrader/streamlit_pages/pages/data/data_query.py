# encoding: utf-8
from typing import List
import arrow
import pandas as pd
import streamlit as st
import re

from tgtrader.data_provider.dao.models.t_sql_history_model import SqlHistoryModel
from tgtrader.utils.duckdb_query import DuckDBQuery
from tgtrader.streamlit_pages.pages.component.data_meta import build_db_meta_info

def add_limit_if_missing(sql: str, limit: int = 100) -> str:
    """
    检查SQL语句是否包含LIMIT子句，如果没有则添加.

    Args:
        sql (str): 原始SQL语句
        limit (int, optional): 限制返回的行数. Defaults to 100.

    Returns:
        str: 处理后的SQL语句
    """
    # 移除SQL末尾的分号和空白字符
    sql = sql.strip().rstrip(';')
    
    # 使用正则表达式检查是否已有LIMIT子句（不区分大小写）
    if not re.search(r'\bLIMIT\s+\d+\b', sql, re.IGNORECASE):
        sql = f"{sql} LIMIT {limit}"
    
    return sql

def split_sql_statements(sql_text: str) -> List[str]:
    """
    将多个SQL语句分割成单独的语句列表.

    Args:
        sql_text (str): 包含一个或多个SQL语句的文本，语句之间用分号分隔

    Returns:
        List[str]: SQL语句列表，每个元素为一个独立的SQL语句
    """
    # 移除空白SQL语句
    statements = [stmt.strip() for stmt in sql_text.split(';')]
    return [stmt for stmt in statements if stmt]

def run() -> None:
    """
    运行数据查询页面的主函数.
    """
    st.title('数据查询')

    # 数据源选择
    data_source = st.selectbox(
        '数据源',
        options=['AKshare'],  # 可以后续添加更多数据源
        index=0
    )

    sql = st.text_area("请输入sql语句(可输入多条语句，用分号分隔)。表字段信息请参考“数据初始化”页面", height=200)
    
    col1, col2, col3 = st.columns([1, 1, 7])

    with col1:
        btn_query = st.button("查询")
    
    with col2:
        btn_save = st.button("保存")

    with col3:
        btn_clear = st.button("清除")

    if btn_query:
        sql_statements = split_sql_statements(sql)
        db_query = DuckDBQuery(data_source)
        
        # 逐个执行SQL语句并显示结果
        for i, stmt in enumerate(sql_statements, 1):
            try:
                # 添加LIMIT检查
                processed_stmt = add_limit_if_missing(stmt)
                
                st.markdown(f"**SQL语句 {i}:**")
                st.code(processed_stmt, language="sql")
                df = db_query.fetch_df(processed_stmt)
                st.dataframe(df)
                
                # 如果SQL被修改，显示提示信息
                if processed_stmt != stmt:
                    st.info("已自动添加 LIMIT 100 限制")
                
                st.markdown("---")  # 添加分隔线
            except Exception as e:
                st.error(f"执行SQL语句 {i} 时出错: {str(e)}")
    
    if btn_save:
        if len(sql.strip()) <= 0:
            st.error("SQL语句不能为空")
            return
        
        SqlHistoryModel.save_sql_history(st.session_state.user_info['username'], sql, data_source)
        
    # 显示历史查询记录
    st.markdown("### 历史查询记录")
    history_records = SqlHistoryModel.get_sql_history(st.session_state.user_info['username'])
    if history_records:
        # 将历史记录转换为DataFrame，列： 查询时间，sql
        history_df = pd.DataFrame(
            [(arrow.get(record.create_time, tzinfo='+08:00').format('YYYY-MM-DD HH:mm:ss'), record.sql_content) for record in history_records],
            columns=['查询时间', 'SQL语句']
        )
        
        # 显示历史记录表格
        st.dataframe(history_df, use_container_width=True)

    build_db_meta_info(src_page='data_query')