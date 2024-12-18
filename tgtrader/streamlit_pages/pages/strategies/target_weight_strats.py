# encoding: utf-8

import streamlit as st
import pandas as pd
import numpy as np

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.strategies.bt.target_weight_strategy import TargetWeightStrategy
from tgtrader.strategy import RebalancePeriod
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import build_stock_dropdown_list
from tgtrader.streamlit_pages.pages.component.weight_editor import weight_editor

def run():
    st.title('目标权重策略')
    
    # 1. 标的选择
    data_getter = DataGetter()
    # default_symbols = ['513100', '511260', '159915', '510500', '159919', '510880', '518800']
    default_symbols = []
    # 计算每个标的的等权重
    if default_symbols:
        default_weight = 100.0 / len(default_symbols)
    else:
        default_weight = None
    security_type_selectbox, symbol_multiselect = build_stock_dropdown_list(data_getter, default_symbols=default_symbols)

    # 2. 已选择标的表格
    if symbol_multiselect:
        edited_df, weights_valid = weight_editor(
            symbol_multiselect,
            show_weights=True
        )
    
    # 3. 调仓周期
    col1, col2 = st.columns(2)
    with col1:
        rebalance_period = st.selectbox(
            '调仓周期',
            options=['日', '周', '月'],
            index=0  # 默认选择'周'
        )
    
    # 4. 初始资金
    with col2:
        initial_capital = st.number_input(
            '初始资金',
            min_value=100000,
            max_value=10000000,
            value=1000000,
            step=100000,
            format='%d'
        )

    # 5. 回测区间
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            '开始日期',
            value=pd.Timestamp.now() - pd.DateOffset(years=1),
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
    
    # 6. 回测按钮
    if st.button('开始回测', type='primary'):
        if not symbol_multiselect:
            st.error('请选择至少一个标的')
            return
            
        if not weights_valid:
            st.error('请确保权重之和为100%')
            return
            
        progress_bar = st.progress(0)
        
        # Convert rebalance period to enum
        period_map = {
            '日': RebalancePeriod.Daily,
            '周': RebalancePeriod.Weekly, 
            '月': RebalancePeriod.Monthly
        }
        rebalance_period_enum = period_map[rebalance_period]

        # Prepare weights dict from edited dataframe
        weights = {
            row['代码']: row['权重(%)'] / 100 
            for _, row in edited_df.iterrows()
        }

        progress_bar.progress(25, text='正在处理权重数据...')

        # Separate ETF and stock symbols based on selection
        etf_symbols = []
        stock_symbols = []
        
        for symbol in symbol_multiselect:
            code, _, security_type = symbol.split('|')
            if security_type == 'ETF':
                etf_symbols.append(code)
            else:
                stock_symbols.append(code)
                
        # Build symbols dict with non-empty lists only
        symbols = {}
        if etf_symbols:
            symbols[SecurityType.ETF] = etf_symbols
        if stock_symbols:
            symbols[SecurityType.Stocks] = stock_symbols

        # Remove cash from weights if present
        if 'CASH' in weights:
            del weights['CASH']

        progress_bar.progress(30, text='正在运行策略...')

        # Create strategy instance
        strategy = TargetWeightStrategy(
            symbols=symbols,
            weights=weights,
            rebalance_period=rebalance_period_enum,
            integer_positions=True
        )

        # Run backtest
        # Convert dates to string format
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        strategy.backtest(start_date, end_date)

        progress_bar.progress(100, text='回测完成!')

        st.write(strategy.performance_stats())
