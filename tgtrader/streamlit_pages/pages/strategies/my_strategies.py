from functools import partial
import importlib
import streamlit as st
import pandas as pd
import json
from tgtrader.strategies.bt.strategy_bt import BtStrategy
from tgtrader.strategy import StrategyRegistry
from tgtrader.streamlit_pages.pages.component.backtest_results import display_backtest_results
from tgtrader.streamlit_pages.service.user_strategy import UserStrategyService
from tgtrader.strategy_config import StrategyConfig, StrategyConfigRegistry
from loguru import logger
from datetime import datetime, timezone, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder

def run():
    st.title('我的策略')

    if 'user_info' not in st.session_state:
        st.error('请先登录!')
        return

    user_id = st.session_state['user_info']['id']

    try:
        strategies = UserStrategyService.get_user_strategies(user_id)

        if not strategies:
            st.info('暂无策略')
            return

        df = pd.DataFrame(strategies)
        strategy_configs = []
        for _, row in df.iterrows():
            strategy_dict = row['strategy']
            if isinstance(strategy_dict, str):
                strategy_dict = json.loads(strategy_dict)

            # logger.debug(f"Strategy dict: {strategy_dict}")
            strategy_config = StrategyConfig.from_dict(strategy_dict)

            strategy_name = strategy_config.strategy_name

            strategy_cls = strategy_config.strategy_cls

            strategy_type = StrategyRegistry.get_name(strategy_cls.split('.')[-1])

            module_name = strategy_config.module_name

            symbols_str = ", ".join([f"{code}_{security_type.value}" for security_type, codes in strategy_config.symbols.items() for code in codes])

            create_time = datetime.fromtimestamp(int(row['create_time']), tz=timezone.utc).astimezone(timezone(timedelta(hours=8)))
            update_time = datetime.fromtimestamp(int(row['update_time']), tz=timezone.utc).astimezone(timezone(timedelta(hours=8)))

            common_params = {'symbols', 'strategy_cls', 'rebalance_period', 'initial_capital', 'start_date', 'end_date', 'strategy_name'}
            other_params = {k: v for k, v in strategy_dict.items() if k not in common_params}


            strategy_configs.append({
                'id': row['id'],
                '策略名称': strategy_name,
                '策略类型': strategy_type,
                '交易标的': symbols_str,
                '调仓周期': strategy_config.rebalance_period.value,
                '初始资金': strategy_config.initial_capital,
                '开始日期': strategy_config.start_date,
                '结束日期': strategy_config.end_date,
                '其他参数': str(other_params),
                '模块名': module_name,
                '创建时间': create_time.strftime('%Y-%m-%d %H:%M:%S'),
                '更新时间': update_time.strftime('%Y-%m-%d %H:%M:%S'),
            })

        display_df = pd.DataFrame(strategy_configs)

        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_default_column(resizable=True, filterable=True, sortable=True)
        gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_selection(selection_mode="single")
        gridOptions = gb.build()

        grid_response = AgGrid(
            display_df,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            theme='streamlit',
            custom_css={
                ".ag-cell-focus": {"border": "none !important"},
                ".ag-row-hover": {"background-color": "#f5f5f5 !important"}
            }
        )

        selected = grid_response['selected_rows']

        if selected is not None:
            strategy_id_selected = selected.iloc[0]['id']  # Get the id of the selected strategy
            if 'selected_strategy_id' in st.session_state:
                old_strategy_id = st.session_state['selected_strategy_id']
                if old_strategy_id != strategy_id_selected:
                    if 'confirm_view' in st.session_state:
                        del st.session_state['confirm_view']
                    if 'confirm_delete' in st.session_state:
                        del st.session_state['confirm_delete']
            st.session_state['selected_strategy_id'] = strategy_id_selected

            module_name_selected = selected.iloc[0]['模块名']
            col1, col2 = st.columns(2, gap='small')

            with col1:
                if st.button('查看', use_container_width=True, key=f"view_{strategy_id_selected}"):
                    
                    if 'confirm_delete' in st.session_state:
                        del st.session_state['confirm_delete']

                    st.session_state['confirm_view'] = {
                        'strategy_id': strategy_id_selected,
                        'module_name': module_name_selected
                    }

            with col2:
                if st.button('删除', use_container_width=True, key=f"delete_{strategy_id_selected}"):
                    if 'confirm_view' in st.session_state:
                        del st.session_state['confirm_view']
                    
                    st.session_state['confirm_delete'] = strategy_id_selected # Store the strategy ID

        if 'confirm_delete' in st.session_state:
            st.warning(f'确定要删除策略: {st.session_state["confirm_delete"]} 吗?', icon="⚠️")
            col3, col4 = st.columns(2)
            with col3:
                if st.button('确认删除', key="confirm_delete_button"):
                    try:
                        UserStrategyService.delete_strategy(user_id, st.session_state['confirm_delete'])
                        st.success(f'策略 {st.session_state["confirm_delete"]} 已删除')
                        logger.warning(f"Deleted strategy: {st.session_state['confirm_delete']}")
                        del st.session_state['confirm_delete']
                        st.rerun()
                    except Exception as e:
                        logger.exception(e)
                        st.error(f'删除策略失败: {str(e)}')
            with col4:
                if st.button('取消', key="cancel_delete_button"):
                    del st.session_state['confirm_delete']
                    st.rerun()
        elif 'confirm_view' in st.session_state:
            view_strategy(st.session_state['confirm_view']['strategy_id'])
        else:
            st.info('请选择一行以执行操作')

    except Exception as e:
        logger.exception(e)
        st.error(f'获取策略列表失败: {str(e)}')

def view_strategy(strategy_id):
    try:
        user_id = st.session_state['user_info']['id']

        # 获取策略对象
        strategy_obj = UserStrategyService.get_strategy(user_id, strategy_id)
        if strategy_obj is None:
            st.error('策略不存在!')
            return
            
        # 将策略配置字符串解析为字典
        strategy_dict = json.loads(strategy_obj.strategy)
        strategy_config = StrategyConfig.from_dict(strategy_dict)
        
        # 获取策略类名和模块名
        strategy_cls_name = strategy_config.strategy_cls

        # 导入策略模块
        module_name = '.'.join(strategy_cls_name.split('.')[0:-1])
        cls_name = strategy_cls_name.split('.')[-1]

        module = importlib.import_module(module_name)
        strategy_cls = getattr(module, cls_name)

        # 检查策略类是否是 BtStrategy 的子类
        if issubclass(strategy_cls, BtStrategy):
            # 获取基本参数
            base_params = {
                'symbols': strategy_config.symbols,
                'rebalance_period': strategy_config.rebalance_period,
                'integer_positions': True,
                'commissions': lambda q, p: 0.0,
                'backtest_field': 'close',
                'initial_capital': strategy_config.initial_capital
            }

            filter_params = [
                'start_date',
                'end_date',
                'strategy_cls',
                'strategy_name',
                'module_name'
            ]
            
            # 获取额外参数
            other_params = {k: v for k, v in strategy_config.__dict__.items() 
                          if k not in base_params and not k.startswith('_') and k not in filter_params}
            
            # 合并所有参数并创建策略实例
            strategy = strategy_cls(**base_params, **other_params)
        
        # 运行回测
        with st.spinner('运行中...'):
            end_date = datetime.now().strftime('%Y-%m-%d')
            strategy.backtest(strategy_config.start_date, end_date)
            
            display_backtest_results(strategy, strategy_config.end_date)
        
    except Exception as e:
        logger.exception(e)
        st.error(f'查看策略失败: {str(e)}')