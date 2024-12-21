import streamlit as st
import pandas as pd
import json
from tgtrader.strategy import StrategyRegistry
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

            strategy_type = StrategyRegistry.get_display_name(strategy_config.strategy_cls)

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
            strategy_id_to_delete = selected.iloc[0]['id']  # Get the id of the selected strategy
            col1, col2 = st.columns(2, gap='small')

            with col1:
                if st.button('查看', use_container_width=True, key=f"view_{strategy_id_to_delete}"):
                    
                    if 'confirm_delete' in st.session_state:
                        del st.session_state['confirm_delete']

                    view_strategy(strategy_id_to_delete)

            with col2:
                if st.button('删除', use_container_width=True, key=f"delete_{strategy_id_to_delete}"):
                    st.session_state['confirm_delete'] = strategy_id_to_delete # Store the strategy ID

        if 'confirm_delete' in st.session_state:
            st.warning(f'确定要删除策略: {st.session_state["confirm_delete"]} 吗?', icon="⚠️")
            col3, col4 = st.columns(2)
            with col3:
                if st.button('确认删除', key="confirm_delete_button"):
                    try:
                        UserStrategyService.delete_strategy(st.session_state['confirm_delete'])
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

        else:
            st.info('请选择一行以执行操作')

    except Exception as e:
        logger.exception(e)
        st.error(f'获取策略列表失败: {str(e)}')

def view_strategy(strategy_id):
    st.write(f'查看策略: {strategy_id}')
    # 在这里添加更多的查看逻辑，例如显示策略详细信息

# def delete_strategy(strategy_id): # Removed the separate delete_strategy function
#     confirm = st.warning('确定要删除这个策略吗?', icon="⚠️")
#     if st.button('确认删除'):
#         try:
#             # 调用删除 API
#             UserStrategyService.delete_strategy(strategy_id)
#             # 显示删除成功提示
#             st.success(f'策略 {strategy_id} 已删除')
#             st.rerun()
#         except Exception as e:
#             logger.exception(e)
#             st.error(f'删除策略失败: {str(e)}')