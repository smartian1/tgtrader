import streamlit as st
import pandas as pd
from tgtrader.strategy import RebalancePeriod

def build_backtest_params(default_rebalance_period='日'):
    """构建回测参数UI组件
    
    Args:
        default_rebalance_period (str): 默认调仓周期，可选值：'日'、'周'、'月'
        
    Returns:
        tuple: (调仓周期枚举值, 初始资金, 开始日期, 结束日期)
    """
    # 调仓周期和初始资金
    col1, col2 = st.columns(2)
    with col1:
        rebalance_period = st.selectbox(
            '调仓周期',
            options=['日', '周', '月'],
            index=['日', '周', '月'].index(default_rebalance_period)
        )
    
    with col2:
        initial_capital = st.number_input(
            '初始资金',
            min_value=100000,
            max_value=10000000,
            value=1000000,
            step=100000,
            format='%d'
        )

    # 回测区间
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            '开始日期',
            value=pd.Timestamp.now() - pd.DateOffset(years=3),
            min_value=pd.Timestamp('2010-01-01'),
            max_value=pd.Timestamp.now()
        )
    
    with col2:
        end_date = st.date_input(
            '结束日期', 
            value=pd.Timestamp.now(),
            min_value=pd.Timestamp('2010-01-01'),
            max_value=pd.Timestamp.now()
        )

    if start_date >= end_date:
        st.error('开始日期必须早于结束日期')
        return None, None, None, None

    # 转换调仓周期为枚举值
    period_map = {
        '日': RebalancePeriod.Daily,
        '周': RebalancePeriod.Weekly, 
        '月': RebalancePeriod.Monthly
    }
    rebalance_period_enum = period_map[rebalance_period]

    return rebalance_period_enum, initial_capital, start_date, end_date 