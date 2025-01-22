# encoding: utf-8

import streamlit as st
from st_keyup import st_keyup
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
from tgtrader.streamlit_pages.dao.t_api_key import TApiKey
from tgtrader.streamlit_pages.utils.common import get_user_name
from loguru import logger
import arrow


def run():
    manage_api_keys()

def manage_api_keys():
    """管理大模型API Key"""
    st.header("大模型API Key管理")
    
    # 获取当前用户
    username = get_user_name()
    if not username:
        st.error("请先登录")
        return
        
    # 添加新的API Key
    with st.expander("添加新的API Key"):
        model_name = st.selectbox("模型名称", ["通义千问-Turbo-2024-11-01"])
        api_key = st.text_input("API Key", key="new_api_key")
        
        if st.button("保存"):
            if model_name and api_key:
                # 保存到数据库
                TApiKey.save_api_key(username=username, model_name=model_name, api_key=api_key)
                st.success(f"{model_name} 的API Key已保存")
            else:
                st.error("请填写模型名称和API Key")
    
    # 显示现有API Keys
    st.subheader("已保存的API Keys")
    
    # 从数据库获取API Keys
    api_keys = TApiKey.get_api_keys(username=username, hide_middle=True)
    
    if api_keys:
        # 使用AgGrid显示数据
        df = pd.DataFrame([
            {"id": key.id, "模型名称": key.model_name, "API Key": key.api_key,
             '创建时间': arrow.get(key.create_time, tzinfo='+08:00').format('YYYY-MM-DD HH:mm:ss')}
            for key in api_keys
        ])
        
        gb = GridOptionsBuilder.from_dataframe(df[["id", "模型名称", "API Key", "创建时间"]])
        gb.configure_selection('single')
        grid_options = gb.build()
        
        grid_response = AgGrid(
            df[["id", "模型名称", "API Key", "创建时间"]],
            gridOptions=grid_options,
            height=200,
            width="100%",
            theme="streamlit"
        )
        # 删除选中的API Key
        selected = grid_response['selected_rows']
        if selected is not None and len(selected) > 0:
            if st.button("删除选中的API Key"):
                id_to_delete = selected.iloc[0]["id"]
                # 从数据库中删除
                TApiKey.delete_api_key(id_to_delete)
                st.success(f"API Key已删除")
                st.rerun()
    else:
        st.info("当前没有保存任何API Key")


