# encoding: utf-8

import streamlit as st
from datetime import datetime

from tgtrader.common import DataDbService, DataSource, MetaType, SecurityType


def init_database(data_source: str):
    if data_source == 'AKshare':
        data_service = DataDbService.get_data_service(DataSource.Akshare)
    else:
        raise NotImplementedError(f'数据源 {data_source} 不支持')

    data_service.init_database()

def get_meta_info(data_source: str, 
                  meta_type: MetaType):
    if data_source == 'AKshare':
        data_service = DataDbService.get_data_service(DataSource.Akshare)
    else:
        raise NotImplementedError(f'数据源 {data_source} 不支持')

    meta_info = data_service.get_metadata(meta_type=meta_type)
    
    return meta_info

def update_data(data_source: str, meta_type: MetaType):
    if data_source == 'AKshare':
        data_service = DataDbService.get_data_service(DataSource.Akshare)
    else:
        raise NotImplementedError(f'数据源 {data_source} 不支持')

    data_service.update_data(meta_type)


def create_card(data_source: str, meta_type: MetaType, title: str):
    meta_info = get_meta_info(data_source, meta_type)

    with st.container():
        st.subheader(title)

    col1, col2 = st.columns(2)

    with col1:
        # 起始时间
        st.text(f"起始时间：{meta_info.start_time if meta_info else 'N/A'}")
        # 结束时间 
        st.text(f"结束时间：{meta_info.end_time if meta_info else 'N/A'}")
        
        
    with col2:
        # 更新时间
        st.text(f"更新时间：{meta_info.update_time if meta_info else 'N/A'}")
        # 数据量
        st.text(f"数据量：{meta_info.total_count if meta_info else 'N/A'}")
        
    # 更新按钮
    btn = st.button('更新', key=f'{data_source}_{meta_type}_update')
    if btn:
        data_service.update_data(meta_type)

def run():
    st.title('数据初始化')

    # 数据源选择
    data_source = st.selectbox(
        '数据源',
        options=['AKshare'],  # 可以后续添加更多数据源
        index=0
    )

    if data_source:
        init_database(data_source)

    st.markdown("""
        <style>
            div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    # 股票历史行情更新区域
    create_card(data_source, MetaType.Stocks1dHfqKdata, '股票历史行情(日)')

    # # ETF历史行情更新区域 
    # with st.container():
    #     st.subheader('ETF历史行情(日)')
        
    #     create_card(data_source, MetaType.Stocks1dHfqKdata)
