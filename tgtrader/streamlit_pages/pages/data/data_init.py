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
    
    if meta_type in [MetaType.Stocks1dHfqKdata, MetaType.ETF1dHfqKdata]:
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
    status_text = st.empty()

    for i, (start_time, end_time) in enumerate(fetch_time_ranges):
        progress = i / len(fetch_time_ranges)
        progress_bar.progress(progress)
        status_text.text(f"更新数据： {start_time} 至 {end_time}...")
        
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
    status_text.text("更新完成!")
    time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()

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
    
    # 1. 先插入自定义的 CSS，给一个名叫 "my-card" 的类增加边框样式
    st.markdown(
        """
        <style>
        .my-card {
            /* 边框：1 像素实线 + 浅灰色 */
            border: 1px solid #E2E2E2;
            /* 圆角可自由调 */
            border-radius: 0.5rem;
            /* 内边距让内容不至于贴到边框上 */
            padding: 1rem;
            /* 背景色（可按需修改） */
            background-color: #F9F9F9;
            /* 让这块和其它组件之间有点间距 */
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.subheader(title)

        col1, col2 = st.columns(2)
        with col1:
            st.text(f"起始时间：{meta_info.start_time if meta_info else 'N/A'}")
            st.text(f"结束时间：{meta_info.end_time if meta_info else 'N/A'}")

        with col2:
            st.text(
                f"更新时间：{arrow.get(meta_info.update_time, tzinfo='UTC').to('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss') if meta_info else 'N/A'}"
            )
            st.text(f"数据量：{meta_info.total_count if meta_info else 'N/A'}")

        # 添加时间段选择组件
        col3, col4 = st.columns(2)
        with col3:
            # 如果meta有值，使用meta的结束时间，否则使用2017-01-01
            default_start = (
                datetime.strptime(meta_info.end_time, '%Y-%m-%d').date() 
                if meta_info and meta_info.end_time
                else datetime.strptime('2017-01-01', '%Y-%m-%d').date()
            )
            start_date = st.date_input("选择起始时间", 
                                     value=default_start,
                                     key=f"{data_source}_{meta_type}_start_date")
        with col4:
            # 结束时间默认为今天
            end_date = st.date_input("选择结束时间",
                                   value=datetime.now().date(),
                                   key=f"{data_source}_{meta_type}_end_date")

        btn = st.button("更新", key=f"{data_source}_{meta_type}_update")
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

    # ETF历史行情更新区域 
    create_card(data_source, 
                meta_type=MetaType.ETF1dHfqKdata, 
                title='ETF历史行情(日)', 
                security_type=SecurityType.ETF)
