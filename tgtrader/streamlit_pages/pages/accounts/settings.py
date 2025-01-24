# encoding: utf-8

import streamlit as st
from st_keyup import st_keyup
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
from tgtrader.streamlit_pages.dao.t_api_key import TApiKey
from tgtrader.streamlit_pages.dao.t_rss_source import TRssSource
from tgtrader.streamlit_pages.utils.common import get_user_name
from loguru import logger
import arrow


def run():
    manage_api_keys()
    manage_rss_sources()

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
        api_key_name = st.text_input("API Key名称", key="new_api_key_name")
        model_name = st.selectbox("模型名称", ["qwen-plus-latest"])
        api_key = st.text_input("API Key", key="new_api_key")
        
        if st.button("保存"):
            if model_name and api_key and api_key_name:
                try:
                    TApiKey.save_api_key(username=username, model_name=model_name, api_key=api_key, api_key_name=api_key_name)
                    st.success(f"{model_name} 的API Key已保存")
                except Exception as e:
                    st.error(str(e))
            else:
                st.error("请填写模型名称、API Key和API Key名称")
    
    # 显示现有API Keys
    st.subheader("已保存的API Keys")
    
    # 从数据库获取API Keys
    api_keys = TApiKey.get_api_keys(username=username, hide_middle=True)
    
    if api_keys:
        # 使用AgGrid显示数据
        df = pd.DataFrame([
            {"id": key.id, "API Key名称": key.api_key_name, "模型名称": key.model_name, "API Key": key.api_key,
             '创建时间': arrow.get(key.create_time, tzinfo='+08:00').format('YYYY-MM-DD HH:mm:ss')}
            for key in api_keys
        ])
        
        gb = GridOptionsBuilder.from_dataframe(df[["id", "API Key名称", "模型名称", "API Key", "创建时间"]])
        gb.configure_selection('single')
        grid_options = gb.build()
        
        grid_response = AgGrid(
            df[["id", "API Key名称", "模型名称", "API Key", "创建时间"]],
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

def manage_rss_sources():
    """管理RSS源"""
    st.header("RSS源管理")
    
    # 获取当前用户
    username = get_user_name()
    if not username:
        st.error("请先登录")
        return
        
    # 添加新的RSS源
    with st.expander("添加新的RSS源"):
        rss_name = st.text_input("RSS源名称", key="new_rss_name")
        rss_url = st.text_input("RSS URL", key="new_rss_url")
        rss_type = st.selectbox("RSS类型", ["新闻", "博客", "社交媒体", "其他"], key="new_rss_type")
        
        if st.button("保存RSS源"):
            if rss_name and rss_url:
                try:
                    TRssSource.save_rss_source(
                        username=username,
                        rss_name=rss_name,
                        rss_url=rss_url,
                        rss_type=rss_type
                    )
                    st.success(f"RSS源 {rss_name} 已保存")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            else:
                st.error("请填写RSS源名称和URL")
    
    # 显示现有RSS源
    st.subheader("已保存的RSS源")
    
    # 从数据库获取RSS源
    rss_sources = TRssSource.get_rss_sources(username=username)
    
    if rss_sources:
        # 使用AgGrid显示数据
        df = pd.DataFrame([
            {
                "id": source.id,
                "RSS源名称": source.rss_name,
                "RSS URL": source.rss_url,
                "RSS类型": source.rss_type,
                "创建时间": arrow.get(source.create_time, tzinfo='+08:00').format('YYYY-MM-DD HH:mm:ss')
            }
            for source in rss_sources
        ])
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection('single')
        grid_options = gb.build()
        
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            height=200,
            width="100%",
            theme="streamlit"
        )
        
        # 处理选中的RSS源
        selected = grid_response['selected_rows']
        if selected is not None and len(selected) > 0:
            selected_row = selected.iloc[0]
            
            # 创建两列布局
            col1, col2 = st.columns(2)
            
            # 删除按钮放在左列
            with col1:
                if st.button("删除选中的RSS源"):
                    TRssSource.delete_rss_source(selected_row["id"])
                    st.success("RSS源已删除")
                    st.rerun()
            
            # 编辑按钮放在右列
            with col2:
                if st.button("编辑选中的RSS源"):
                    st.session_state.editing_rss = True
                    st.session_state.editing_rss_id = selected_row["id"]
                    st.session_state.editing_rss_name = selected_row["RSS源名称"]
                    st.session_state.editing_rss_url = selected_row["RSS URL"]
                    st.session_state.editing_rss_type = selected_row["RSS类型"]
            
            # 如果处于编辑状态，显示编辑表单
            if st.session_state.get('editing_rss', False):
                with st.form("edit_rss_form"):
                    st.subheader("编辑RSS源")
                    edited_name = st.text_input("RSS源名称", value=st.session_state.editing_rss_name)
                    edited_url = st.text_input("RSS URL", value=st.session_state.editing_rss_url)
                    edited_type = st.selectbox(
                        "RSS类型",
                        ["新闻", "博客", "社交媒体", "其他"],
                        index=["新闻", "博客", "社交媒体", "其他"].index(st.session_state.editing_rss_type)
                    )
                    
                    # 提交和取消按钮
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("保存修改")
                    with col2:
                        cancel = st.form_submit_button("取消")
                    
                    if submit:
                        if edited_name and edited_url:
                            try:
                                TRssSource.update_rss_source(
                                    st.session_state.editing_rss_id,
                                    edited_name,
                                    edited_url,
                                    edited_type
                                )
                                st.success("RSS源更新成功")
                                st.session_state.editing_rss = False
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                        else:
                            st.error("请填写RSS源名称和URL")
                    
                    if cancel:
                        st.session_state.editing_rss = False
                        st.rerun()
    else:
        st.info("当前没有保存任何RSS源")


