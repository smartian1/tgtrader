# encoding: utf-8

import streamlit as st
import pandas as pd
import numpy as np

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.strategies.bt.target_weight_strategy import TargetWeightStrategy
from tgtrader.strategy import RebalancePeriod
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import build_stock_dropdown_list

def validate_weights(weights):
    """验证权重之和是否为100%"""
    return abs(sum(weights) - 100.0) < 0.01

def run():
    st.title('目标权重策略')
    
    # 1. 标的选择
    data_getter = DataGetter()
    security_type_selectbox, symbol_multiselect = build_stock_dropdown_list(data_getter)

    # 2. 已选择标的表格
    if symbol_multiselect:
        # 创建DataFrame来存储选择的标的和权重
        selected_df = pd.DataFrame([
            {
                '代码': symbol.split('|')[0],
                '名称': symbol.split('|')[1],
                '权重(%)': 0.0
            } for symbol in symbol_multiselect
        ])
        
        # 添加现金行
        cash_row = pd.DataFrame([{
            '代码': 'CASH',
            '名称': '现金',
            '权重(%)': 100.0 - selected_df['权重(%)'].sum()
        }])
        display_df = pd.concat([selected_df, cash_row], ignore_index=True)
        
        # 使用st.data_editor让用户编辑权重
        edited_df = st.data_editor(
            display_df,
            column_config={
                '权重(%)': st.column_config.NumberColumn(
                    min_value=0,
                    max_value=100,
                    step=0.1,
                    format="%.1f %%"
                )
            },
            # disabled=['代码', '名称', '权重(%)'],  # 现金权重也设为只读
            hide_index=True
        )
        
        # 验证权重之和
        total_weight = edited_df['权重(%)'].sum()
        if not validate_weights(edited_df['权重(%)']):
            st.warning(f'当前权重之和为 {total_weight:.1f}%，请调整为100%')
    
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
    
    # 6. 回测按钮
    if st.button('开始回测', type='primary'):
        if not symbol_multiselect:
            st.error('请选择至少一个标的')
            return
            
        if not validate_weights(edited_df['权重(%)']):
            st.error('请确保权重之和为100%')
            return
            
        st.info('回测进行中...')
        
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

        # debug
        st.write("Debug parameters:")
        st.write(f"Symbols: {symbols}")
        st.write(f"Weights: {weights}")
        st.write(f"Rebalance period: {rebalance_period_enum}")

        # Create strategy instance
        strategy = TargetWeightStrategy(
            symbols=symbols,
            weights=weights,
            rebalance_period=rebalance_period_enum,
            integer_positions=True
        )

        # Run backtest
        result = strategy.run()

