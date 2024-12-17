# encoding: utf-8

import streamlit as st
import pandas as pd
import numpy as np

from tgtrader.data import DataGetter
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
                '代码': symbol.split()[0],
                '名称': symbol.split()[1],
                '权重(%)': 0.0
            } for symbol in symbol_multiselect
        ])
        
        # 使用st.data_editor让用户编辑权重
        edited_df = st.data_editor(
            selected_df,
            column_config={
                '权重(%)': st.column_config.NumberColumn(
                    min_value=0,
                    max_value=100,
                    step=0.1,
                    format="%.1f %%"
                )
            },
            disabled=['代码', '名称'],
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
            index=1  # 默认选择'周'
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
    
    # 5. 手续费
    fee_rate = st.slider(
        '手续费率(%)',
        min_value=0.0,
        max_value=0.5,
        value=0.05,
        step=0.01,
        format='%.2f'
    )
    
    # 6. 回测按钮
    if st.button('开始回测', type='primary'):
        if not selected_symbols:
            st.error('请选择至少一个标的')
            return
            
        if not validate_weights(edited_df['权重(%)']):
            st.error('请确保权重之和为100%')
            return
            
        # TODO: 执行回测逻辑
        st.info('回测进行中...')
        
        # 这里添加回测逻辑
        # backtest_params = {
        #     'symbols': edited_df['代码'].tolist(),
        #     'weights': edited_df['权重(%)'].tolist(),
        #     'rebalance_period': rebalance_period,
        #     'initial_capital': initial_capital,
        #     'fee_rate': fee_rate / 100
        # }

