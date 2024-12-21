import streamlit as st
import pandas as pd
import json
from tgtrader.strategy import StrategyRegistry
from tgtrader.streamlit_pages.service.user_strategy import UserStrategyService
from tgtrader.strategy_config import StrategyConfig, StrategyConfigRegistry
from loguru import logger
from datetime import datetime, timezone, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

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
                'id': row['id'],  # 保留id用于操作
                '策略类型': strategy_name,
                '交易标的': symbols_str,
                '调仓周期': strategy_config.rebalance_period.value,
                '初始资金': strategy_config.initial_capital,
                '开始日期': strategy_config.start_date,
                '结束日期': strategy_config.end_date,
                '其他参数': str(other_params),
                '创建时间': create_time.strftime('%Y-%m-%d %H:%M:%S'),
                '更新时间': update_time.strftime('%Y-%m-%d %H:%M:%S'),
                '操作': ''  # 操作列
            })

        display_df = pd.DataFrame(strategy_configs)

        jsfnc = """
        class BtnCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                <span>
                    <button id='view-button'
                        class='btn-simple'
                        style='margin-right: 3px;
                        color: #1f77b4;
                        background-color: transparent;
                        border: 1px solid #1f77b4;
                        border-radius: 3px;
                        padding: 1px 6px;
                        font-size: 12px;'>查看</button>
                    <button id='delete-button'
                        class='btn-simple'
                        style='color: #d62728;
                        background-color: transparent;
                        border: 1px solid #d62728;
                        border-radius: 3px;
                        padding: 1px 6px;
                        font-size: 12px;'>删除</button>
                </span>
                `;
                this.viewButton = this.eGui.querySelector('#view-button');
                this.deleteButton = this.eGui.querySelector('#delete-button');

                this.viewClickHandler = this.viewClickHandler.bind(this);
                this.deleteClickHandler = this.deleteClickHandler.bind(this);

                this.viewButton.addEventListener('click', this.viewClickHandler);
                this.deleteButton.addEventListener('click', this.deleteClickHandler);
            }

            getGui() {
                return this.eGui;
            }

            refresh() {
                return true;
            }

            destroy() {
                if (this.viewButton) {
                    this.viewButton.removeEventListener('click', this.viewClickHandler);
                }
                if (this.deleteButton) {
                    this.deleteButton.removeEventListener('click', this.deleteClickHandler);
                }
            }

            viewClickHandler(event) {
                const strategy = this.params.data;
                window.parent.postMessage({action: 'view', id: strategy.id}, '*');
            }

            deleteClickHandler(event) {
                if (confirm('确定要删除这个策略吗?') == true) {
                    const strategy = this.params.data;
                    window.parent.postMessage({action: 'delete', id: strategy.id}, '*');
                }
            }
        };
        """
        BtnCellRenderer = JsCode(jsfnc)

        # 配置AgGrid选项
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_default_column(resizable=True, filterable=True, sortable=True)
        gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=10)

        # 添加操作列配置
        gb.configure_column(
            "操作",
            cellRenderer=BtnCellRenderer,
            cellRendererParams={
                "color": "red",
                "background_color": "black",
            }
        )

        gridOptions = gb.build()

        # 使用AgGrid显示表格
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

        # 检查URL参数
        query_params = st.query_params
        if 'action' in query_params and 'id' in query_params:
            action = query_params['action'][0]
            strategy_id = query_params['id'][0]
            if action == 'view':
                view_strategy(strategy_id)
            elif action == 'delete':
                delete_strategy(strategy_id)

        # 监听消息事件
        if 'message' in st.session_state:
            message = st.session_state['message']
            if message['action'] == 'view':
                view_strategy(message['id'])
            elif message['action'] == 'delete':
                delete_strategy(message['id'])
            # 清除消息状态
            del st.session_state['message']

    except Exception as e:
        logger.exception(e)
        st.error(f'获取策略列表失败: {str(e)}')

def view_strategy(strategy_id):
    st.write(f'查看策略: {strategy_id}')

def delete_strategy(strategy_id):
    st.write(f'删除策略: {strategy_id}')
