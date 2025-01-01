# encoding: utf-8

import time
import arrow
from loguru import logger
import pandas as pd
import streamlit as st
from datetime import datetime

from tgtrader.common import DataDbService, DataProvider, DataSource, MetaType, Period, PriceAdjust, SecurityType
from tgtrader.data_provider.dao.models.t_meta_model import T_Meta_Model


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

def update_data(data_source: str, 
                meta_type: MetaType, 
                security_type: SecurityType,
                meta_info: T_Meta_Model):
    if data_source == 'AKshare':
        data_provider = DataProvider.get_provider(DataSource.Akshare)
    else:
        raise NotImplementedError(f'数据源 {data_source} 不支持')
    
    if meta_type == MetaType.Stocks1dHfqKdata:
        update_price_data(security_type,
                          Period.Day,
                          PriceAdjust.HFQ,
                          data_provider,
                          meta_info)
    else:
        raise NotImplementedError(f'元数据类型 {meta_type} 不支持')

def update_price_data(security_type: SecurityType,
                      period: Period,
                      adjust: PriceAdjust,
                      data_provider: DataProvider,
                      meta_info: T_Meta_Model):
    all_symbols = data_provider.get_all_symbols(security_type)
    all_symbols = list(all_symbols['code'])

    fetch_time_ranges = __get_fetch_time_range(meta_info)

    progress_bar = st.progress(0)
    for i, (start_time, end_time) in enumerate(fetch_time_ranges):
        progress_bar.progress(i / len(fetch_time_ranges))
        df = data_provider.get_price(all_symbols,
                                     start_time,
                                     end_time,
                                     security_type,
                                     period,    
                                     adjust,
                                     multi_thread_cnt=5)
        data_provider.save_price_data(df, 
                                      security_type,
                                      period,
                                      adjust)
        time.sleep(0.1)
        
    progress_bar.progress(1.0)
    progress_bar.empty()

    st.rerun()


def __get_fetch_time_range(meta_info: T_Meta_Model):
    all_start_time = arrow.get('2017-01-01', tzinfo='+08:00').timestamp()
    all_end_time = arrow.now(tz="+08:00").timestamp()

    if meta_info is None:
        return __get_fetch_time_range_by_month(all_start_time, all_end_time)
    else:
        if meta_info.end_time < arrow.now(tz="+08:00").format('YYYY-MM-DD'):
            return __get_fetch_time_range_by_month(arrow.get(meta_info.end_time, tzinfo='+08:00').timestamp(), 
                                                   all_end_time)
        else:
            return []

def __get_fetch_time_range_by_month(start_time: int, end_time: int) -> list:
    """按年拆分时间范围

    Args:
        start_time: 开始时间戳
        end_time: 结束时间戳

    Returns:
        list: [(start_time, end_time), ...] 按年拆分的时间范围列表
    """
    # 转换为arrow对象
    start_date = arrow.get(start_time)
    end_date = arrow.get(end_time)

    # 初始化结果列表
    time_ranges = []

    # 当前处理的时间
    current_date = start_date

    # 按年拆分时间范围
    while current_date <= end_date:
        # 获取当年第一天和最后一天
        year_start = current_date.floor('year')
        year_end = current_date.ceil('year')

        if year_start < current_date:
            year_start = current_date
        
        if year_end > end_date:
            year_end = end_date
        
        # 添加时间范围元组
        time_ranges.append((
            year_start.format('YYYY-MM-DD'),
            year_end.format('YYYY-MM-DD')
        ))

        # 移动到下一年第一天
        current_date = year_end.shift(days=1).floor('day')


    return time_ranges


def create_card(data_source: str, meta_type: MetaType, title: str, security_type: SecurityType):
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
        st.text(
            f"更新时间：{arrow.get(meta_info.update_time, tzinfo='UTC').to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss') if meta_info else 'N/A'}")
        # 数据量
        st.text(f"数据量：{meta_info.total_count if meta_info else 'N/A'}")
        
    # 更新按钮
    btn = st.button('更新', key=f'{data_source}_{meta_type}_update')
    if btn:
        update_data(data_source, meta_type, security_type, meta_info)

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
    create_card(data_source, 
                meta_type=MetaType.Stocks1dHfqKdata, 
                title='股票历史行情(日)', 
                security_type=SecurityType.Stocks)

    # # ETF历史行情更新区域 
    # with st.container():
    #     st.subheader('ETF历史行情(日)')
        
    #     create_card(data_source, MetaType.Stocks1dHfqKdata)
