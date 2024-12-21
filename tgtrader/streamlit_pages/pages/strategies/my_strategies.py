# encoding: utf-8

import streamlit as st
import pandas as pd
import json
from tgtrader.strategy import StrategyRegistry
from tgtrader.streamlit_pages.service.user_strategy import UserStrategyService
from tgtrader.strategy_config import StrategyConfig, StrategyConfigRegistry
from loguru import logger
from datetime import datetime, timezone, timedelta

def run():
    st.title('我的策略')
    
    # 从session state获取用户信息
    if 'user_info' not in st.session_state:
        st.error('请先登录!')
        return
        
    user_id = st.session_state['user_info']['id']
    
    try:
        # 获取用户的策略列表
        strategies = UserStrategyService.get_user_strategies(user_id)
        
        if not strategies:
            st.info('暂无策略')
            return
            
        # 将策略列表转换为DataFrame
        df = pd.DataFrame(strategies)
        
        # 解析策略配置并添加到DataFrame
        strategy_configs = []
        for _, row in df.iterrows():
            # 检查strategy字段的类型并相应处理
            strategy_dict = row['strategy']
            if isinstance(strategy_dict, str):
                strategy_dict = json.loads(strategy_dict)
            
            logger.debug(f"Strategy dict: {strategy_dict}")
            strategy_config = StrategyConfig.from_dict(strategy_dict)
            
            # 处理交易标的显示
            symbols_str = []
            for security_type, codes in strategy_config.symbols.items():
                for code in codes:
                    symbols_str.append(f"{code}_{security_type.value}")
            symbols_str = ", ".join(symbols_str)
            
            # 尝试将时间戳转换为datetime对象
            create_time = datetime.fromtimestamp(int(row['create_time']), tz=timezone.utc)
            update_time = datetime.fromtimestamp(int(row['update_time']), tz=timezone.utc)
            beijing_tz = timezone(timedelta(hours=8))
            create_time = create_time.astimezone(beijing_tz)
            update_time = update_time.astimezone(beijing_tz)
            
            # 获取其他参数
            common_params = {'symbols', 'strategy_cls', 'rebalance_period', 'initial_capital', 'start_date', 'end_date'}
            other_params = {k: v for k, v in strategy_dict.items() if k not in common_params}

            # 获取策略显示名称
            strategy_name = StrategyRegistry.get_display_name(strategy_dict.get('strategy_cls', '未知策略'))
            
            strategy_configs.append({
                'id': row['id'],
                'strategy_type': strategy_name,
                'symbols': symbols_str,
                'rebalance_period': strategy_config.rebalance_period.value,
                'initial_capital': strategy_config.initial_capital,
                'start_date': strategy_config.start_date,
                'end_date': strategy_config.end_date,
                'other_params': str(other_params),
                'create_time': create_time.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        display_df = pd.DataFrame(strategy_configs)
        
        # 显示策略表格,设置宽度为100%
        st.dataframe(
            display_df,
            column_config={
                'id': '策略ID',
                'strategy_type': '策略类型',
                'symbols': '交易标的',
                'rebalance_period': '调仓周期',
                'initial_capital': '初始资金',
                'start_date': '开始日期',
                'end_date': '结束日期',
                'other_params': '其他参数',
                'create_time': '创建时间',
                'update_time': '更新时间'
            },
            hide_index=True
        )
                
    except Exception as e:
        logger.exception(e)
        st.error(f'获取策略列表失败: {str(e)}')
