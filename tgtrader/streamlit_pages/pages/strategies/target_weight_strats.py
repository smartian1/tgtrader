# encoding: utf-8

import streamlit as st
import json
from datetime import datetime

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.strategies.bt.target_weight_strategy import TargetWeightStrategy, TargetWeightStrategyConfig
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem, build_stock_dropdown_list
from tgtrader.streamlit_pages.pages.component.weight_editor import weight_editor
from tgtrader.streamlit_pages.pages.component.backtest_params import build_backtest_params
from tgtrader.streamlit_pages.pages.component.backtest_results import display_backtest_results

def run():
    st.title('目标权重策略')
    
    # 1. 标的选择
    data_getter = DataGetter()
    default_symbols: list[StockDropdownSelectItem] = []
    # 计算每个标的的等权重
    if default_symbols:
        default_weight = 100.0 / len(default_symbols)
    else:
        default_weight = None
        
    symbol_multiselect: list[StockDropdownSelectItem] = build_stock_dropdown_list(src_page='target_weight_strats', data_getter=data_getter)

    # 2. 已选择标的表格
    if symbol_multiselect:
        edited_df, cash_weight, weights_valid = weight_editor(
            src_page='target_weight_strats',
            symbol_multiselect=symbol_multiselect,
            show_weights=True
        )
    
    # 3. 回测参数
    rebalance_period_enum, initial_capital, start_date, end_date = build_backtest_params()
    
    if None in (rebalance_period_enum, initial_capital, start_date, end_date):
        st.error('请确保所有参数都已填写')
        return
    
    # 6. 回测按钮
    strategy = None
    if 'strategy' not in st.session_state:
        st.session_state.strategy = None
    if 'symbols' not in st.session_state:
        st.session_state.symbols = None
    if 'weights' not in st.session_state:
        st.session_state.weights = None
    if 'strategy_params' not in st.session_state:
        st.session_state.strategy_params = None

    col1, col2 = st.columns(2)
    if col1.button('开始回测', type='primary'):
        if not symbol_multiselect:
            st.error('请选择至少一个标的')
            return
            
        if not weights_valid:
            st.error('请确保权重之和为100%')
            return
            
        progress_bar = st.progress(0)
        
        # 从编辑的DataFrame中准备权重字典
        weights = {
            row['代码']: row['权重(%)'] / 100 
            for _, row in edited_df.iterrows()
        }

        progress_bar.progress(25, text='正在处理权重数据...')
        
        # 根据选择分离ETF和股票代码
        etf_symbols = []
        stock_symbols = []
        
        for symbol in symbol_multiselect:
            code, _, security_type = symbol.split('|')
            if security_type == 'ETF':
                etf_symbols.append(code)
            else:
                stock_symbols.append(code)
                
        # 构建包含非空列表的symbols字典
        symbols = {}
        if etf_symbols:
            symbols[SecurityType.ETF] = etf_symbols
        if stock_symbols:
            symbols[SecurityType.Stocks] = stock_symbols

        # 如果权重中包含现金，则删除
        if 'CASH' in weights:
            del weights['CASH']

        progress_bar.progress(30, text='正在运行策略...')

        # 创建策略实例
        strategy = TargetWeightStrategy(
            symbols=symbols,
            weights=weights,
            rebalance_period=rebalance_period_enum,
            integer_positions=True
        )

        # 运行回测
        # 将日期转换为字符串格式
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        strategy.backtest(start_date, end_date)

        progress_bar.progress(100, text='回测完成!')
        
        # 保存策略相关数据到session_state
        st.session_state.strategy = strategy
        # 将 SecurityType 枚举转换为字符串以确保 JSON 序列化
        st.session_state.symbols = symbols

        st.session_state.weights = weights
        st.session_state.strategy_params = {
            'rebalance_period': rebalance_period_enum,
            'initial_capital': initial_capital,
            'start_date': start_date,
            'end_date': end_date
        }

        # 显示回测结果
        display_backtest_results(strategy)

    # 修改保存策略按钮的逻辑
    if st.session_state.get('strategy') is not None and col2.button('保存策略'):
        try:
            # 从session_state获取保存的数据
            symbols = st.session_state.symbols
            weights = st.session_state.weights
            params = st.session_state.strategy_params

            # 准备策略配置
            strategy_config = TargetWeightStrategyConfig(
                symbols=symbols,
                rebalance_period=params['rebalance_period'],
                initial_capital=params['initial_capital'],
                start_date=params['start_date'],
                end_date=params['end_date'],
                strategy_cls=TargetWeightStrategy.__name__,
                target_weights_dict=weights
            )
            
            # 将策略配置转换为JSON并保存
            config_json = strategy_config.to_json()
            
            print(config_json)
            
        except Exception as e:
            st.error(f'保存策略时发生错误: {str(e)}')
            