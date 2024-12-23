# encoding: utf-8

import streamlit as st
import json
from datetime import datetime

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.strategies.bt.risk_parity_strategy import RiskParityStrategy, RiskParityStrategyConfig
from tgtrader.strategy import StrategyRegistry
from tgtrader.strategy_config import StrategyConfig
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem, build_stock_dropdown_list
from tgtrader.streamlit_pages.pages.component.weight_editor import weight_editor
from tgtrader.streamlit_pages.pages.component.backtest_params import build_backtest_params
from tgtrader.streamlit_pages.pages.component.backtest_results import display_backtest_results
from tgtrader.streamlit_pages.service.user_strategy import UserStrategyService
from loguru import logger
import inspect

def run(strategy_id: int = None):
    # 每个策略类都需要获取当前模块名，用于保存策略
    current_frame = inspect.currentframe()
    module = inspect.getmodule(current_frame)
    module_name = module.__name__

    st.title('风险平价策略')

    strategy_config = None
    if strategy_id is not None:
        # 获取策略对象
        strategy_obj = UserStrategyService.get_strategy(strategy_id)
        if strategy_obj is None:
            st.error('策略不存在!')
            return
        
        strategy_dict = json.loads(strategy_obj.strategy)
        strategy_config = StrategyConfig.from_dict(strategy_dict)

    # 1. 标的选择
    data_getter = DataGetter()
    
    symbol_multiselect: list[StockDropdownSelectItem] = build_stock_dropdown_list(src_page='risk_parity_strats', 
                                                                                  data_getter=data_getter, 
                                                                                  strategy_config=strategy_config)

    # 2. 已选择标的表格
    if symbol_multiselect:
        edited_df, cash_weight, weights_valid = weight_editor(
            src_page='risk_parity_strats',
            symbol_multiselect=symbol_multiselect,
            show_weights=False,
            strategy_config=strategy_config
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
         
        progress_bar = st.progress(0)
        
        # 根据选择分离ETF和股票代码
        etf_symbols = []
        stock_symbols = []
        
        for symbol in symbol_multiselect:
            if SecurityType(symbol.symbol_type) == SecurityType.ETF:
                etf_symbols.append(symbol.code)
            elif SecurityType(symbol.symbol_type) == SecurityType.Stocks:
                stock_symbols.append(symbol.code)
            else:
                st.error(f'未知标的类型: {symbol.symbol_type}')
                return
                
        # 构建包含非空列表的symbols字典
        symbols = {}
        if etf_symbols:
            symbols[SecurityType.ETF] = etf_symbols
        if stock_symbols:
            symbols[SecurityType.Stocks] = stock_symbols

        progress_bar.progress(30, text='正在运行策略...')

        # 创建策略实例
        strategy = RiskParityStrategy(
            symbols=symbols,
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

        st.session_state.strategy_params = {
            'rebalance_period': rebalance_period_enum,
            'initial_capital': initial_capital,
            'start_date': start_date,
            'end_date': end_date
        }

        # 显示回测结果
        display_backtest_results(strategy)

    # 显示策略名称输入框和保存按钮
    if st.session_state.get('strategy') is not None:
        strategy_name = col2.text_input('请输入策略名称:', key='strategy_name_input_risk_parity')
        
        if col2.button('保存策略'):
            try:
                # 检查是否选择了标的
                if not symbol_multiselect:
                    st.error('请选择至少一个标的')
                    return
                    
                # 检查是否输入了策略名称
                if not strategy_name:
                    st.error('请输入策略名称')
                    return
                
                if st.session_state.strategy is None:
                    st.error('请先回测')
                    return
                
                # 从session_state获取保存的数据
                symbols = st.session_state.symbols
                params = st.session_state.strategy_params

                # 准备策略配置
                strategy_config = RiskParityStrategyConfig(
                    symbols=symbols,
                    rebalance_period=params['rebalance_period'],
                    initial_capital=params['initial_capital'],
                    start_date=params['start_date'],
                    end_date=params['end_date'],
                    strategy_cls=StrategyRegistry.get_pkg_name(RiskParityStrategy),
                    strategy_name=strategy_name,
                    module_name=module_name
                )
                
                # 保存策略
                UserStrategyService.create_strategy(user_id=st.session_state['user_info']['id'], strategy_config=strategy_config)

                # 清空策略
                st.session_state.strategy = None

                st.success('策略保存成功!')

            except Exception as e:
                st.error(f'保存策略时发生错误: {str(e)}')