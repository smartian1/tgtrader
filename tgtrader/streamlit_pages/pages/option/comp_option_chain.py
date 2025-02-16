# encoding: utf-8
from dataclasses import dataclass
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from tgtrader.gateway.futu.defs import OptionType
from loguru import logger
import numpy as np
import pandas as pd
import enum

class OptionTradeDirection(enum.Enum):
    BUY = '买入'
    SELL = '卖出'

class OptionType(enum.Enum):
    CALL = '看涨'
    PUT = '看跌'

@dataclass
class OptionTrade:
    direction: OptionTradeDirection
    quantity: int
    timestamp: str
    option_type: OptionType
    price: float

def display_option_chain(call_options, put_options, stock_price=None):
    """
    显示期权链数据
    Args:
        call_options: DataFrame containing call options
        put_options: DataFrame containing put options
        stock_price: Current stock price

    Returns:
        List of option trades, each containing the following information:

        - direction (str): 买入/卖出
        - quantity (int): Number of contracts
        - timestamp (str): Timestamp when the trade was executed
        - option_type (str): 看涨/看跌
        - price (float): Execution price
    """
    # 准备数据
    call_display = _prepare_option_display_data(call_options, stock_price, 'call')
    put_display = _prepare_option_display_data(put_options, stock_price, 'put')

    # 创建两列布局显示数据
    col_call, col_put = st.columns(2)

    with col_call:
        _display_option_table(call_display, "看涨期权", stock_price, 'call')

    with col_put:
        _display_option_table(put_display, "看跌期权", stock_price, 'put')

    # 显示交易列表
    _show_trade_list()

    if 'option_trades' in st.session_state:
        return [
            OptionTrade(
                direction=OptionTradeDirection(trade['direction']),
                quantity=trade['quantity'],
                timestamp=trade['timestamp'],
                option_type=OptionType(trade['option_type']),
                price=trade['price']
            )
            for trade in st.session_state.option_trades
        ]
    else:
        return []


def _create_grid_options(df, stock_price=None, option_type='call'):
    """
    创建AG Grid的配置选项
    Args:
        df: DataFrame containing the option data
        stock_price: Current stock price for highlighting
        option_type: 'call' or 'put' to determine highlighting logic
    Returns:
        Grid options for AG Grid
    """
    gb = GridOptionsBuilder.from_dataframe(df)

    # 配置基础列宽
    column_widths = {
        "序号": 70,
        "行权价": 80,
        "最新价": 80,
        "买价": 70,
        "买量": 70,
        "卖价": 70,
        "卖量": 70,
        "成交量": 80,
        "未平仓数": 80,
        "内在价值": 100,
        "隐波": 80,
        "Delta": 80,
        "Gamma": 80,
        "Theta": 80,
        "Vega": 80,
        "Rho": 80
    }

    # 设置列宽和固定列
    for col, width in column_widths.items():
        if col in df.columns:
            pin_side = 'right' if (option_type == 'call' and col == '序号') else \
                'left' if (option_type == 'put' and col == '序号') else None
            gb.configure_column(col, width=width, pinned=pin_side)

    # 配置默认列属性
    gb.configure_default_column(
        resizable=True,
        sorteable=False,
        filterable=False,
        type=["numericColumn", "numberColumnFilter"],
        cellStyle={'text-align': 'right'}
    )
    gb.configure_selection(selection_mode="single")

    # 添加条件样式
    if stock_price:
        highlight_condition = f"params.data['行权价'] < {stock_price}" if option_type == 'call' \
            else f"params.data['行权价'] > {stock_price}"

        js_code = f"""
        function(params) {{
            if ({highlight_condition}) {{
                return {{'backgroundColor': '#e6ffe6'}}; // 浅绿色
            }} else if (params.data['行权价'] {'>' if option_type == 'call' else '<'} {stock_price}) {{
                return {{'backgroundColor': '#ffe6e6'}}; // 浅红色
            }}
            return {{'backgroundColor': '#ffffff'}}; // 相等时白色
        }}
        """
        gb.configure_grid_options(getRowStyle=JsCode(js_code))

    return gb.build()


def _display_option_table(df, title, stock_price=None, option_type='call'):
    """
    显示期权数据表格
    Args:
        df: DataFrame containing the option data
        title: Table title
        stock_price: Current stock price for highlighting
        option_type: 'call' or 'put' to determine highlighting logic
    """
    st.subheader(title)

    grid_options = _create_grid_options(df, stock_price, option_type)
    grid_response = AgGrid(df,
                           gridOptions=grid_options,
                           height=500,
                           width='100%',
                           allow_unsafe_jscode=True,
                           fit_columns_on_grid_load=False,
                           key=f"option_grid_{option_type}")

    selected = grid_response['selected_rows']

    # 显示选中行的期权信息和交易操作界面
    if selected is not None and len(selected) > 0:
        selected_option = selected.iloc[0]

        # 根据选中的code，从df里查询当前最新信息并更新
        selected_option = df[df['期权代码'] == selected_option['期权代码']]

        if selected_option is not None and len(selected_option) > 0:
            selected_option = selected_option.iloc[0]
            _show_selected_option(selected_option, option_type)


def _show_trade_list():
    """显示交易列表"""
    if 'option_trades' not in st.session_state:
        st.session_state.option_trades = []
    
    if st.session_state.option_trades:
        st.markdown("### 交易列表")

        # 准备表格数据
        trades_data = []
        valid_trades = []  # 用于存储有效的交易
        for trade in st.session_state.option_trades:
            try:
                trades_data.append({
                    '期权代码': trade['option_info']['期权代码'],
                    '类型': trade['option_type'],
                    '行权价': trade['option_info']['行权价'],
                    '方向': trade['direction'],
                    '数量': trade['quantity'],
                    '价格': trade['price'],
                    '隐波': f"{trade['option_info'].get('隐波', 0):.2%}",
                    'Delta': f"{trade['option_info'].get('Delta', 0):.4f}",
                    'Gamma': f"{trade['option_info'].get('Gamma', 0):.4f}",
                    'Theta': f"{trade['option_info'].get('Theta', 0):.4f}",
                    'Vega': f"{trade['option_info'].get('Vega', 0):.4f}"
                })
                valid_trades.append(trade)
            except (KeyError, TypeError, IndexError):
                # 如果交易数据无效，跳过这条记录
                continue
        
        # 更新session_state中的交易列表，只保留有效的交易
        st.session_state.option_trades = valid_trades
        
        if not trades_data:
            return
        
        df = pd.DataFrame(trades_data)
        
        # 设置列的编辑属性
        column_config = {
            '期权代码': st.column_config.TextColumn(disabled=True),
            '类型': st.column_config.TextColumn(disabled=True),
            '行权价': st.column_config.NumberColumn(disabled=True),
            '方向': st.column_config.SelectboxColumn(
                options=['买入', '卖出'],
                required=True
            ),
            '数量': st.column_config.NumberColumn(
                min_value=1,
                step=1,
                required=True
            ),
            '价格': st.column_config.NumberColumn(
                min_value=0.001,
                step=0.001,
                format="%.3f",
                required=True
            ),
            '隐波': st.column_config.TextColumn(disabled=True),
            'Delta': st.column_config.TextColumn(disabled=True),
            'Gamma': st.column_config.TextColumn(disabled=True),
            'Theta': st.column_config.TextColumn(disabled=True),
            'Vega': st.column_config.TextColumn(disabled=True)
        }
        
        # 使用data_editor显示和编辑数据
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            height=300,
            use_container_width=True,
            disabled=["adding_rows", "column_order", "filters"],
            num_rows="dynamic"
        )
        
        # 检查数据是否有更改
        if not edited_df.equals(df):
            # 更新交易列表中的数据
            for i, row in edited_df.iterrows():
                if i < len(st.session_state.option_trades):
                    st.session_state.option_trades[i]['direction'] = row['方向']
                    st.session_state.option_trades[i]['quantity'] = row['数量']
                    st.session_state.option_trades[i]['price'] = row['价格']
        
        # 处理删除操作
        if len(edited_df) != len(trades_data):
            remaining_options = edited_df['期权代码'].tolist()
            st.session_state.option_trades = [
                trade for trade in st.session_state.option_trades 
                if trade['option_info']['期权代码'] in remaining_options
            ]


def _show_selected_option(selected, option_type='call'):
    with st.container():
        st.markdown(f"### 序号{selected['序号']}【{selected['期权代码']}】")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"行权价: {selected['行权价']}")
            st.write(f"最新价: {selected['最新价']}")
            st.write(f"买价: {selected['买价']}")
            st.write(f"卖价: {selected['卖价']}")
        with col2:
            st.write(f"成交量: {selected['成交量']}")
            st.write(f"未平仓: {selected['未平仓数']}")
            if '隐波' in selected:
                st.write(f"隐含波动率: {selected['隐波']:.2%}")
        with col3:
            if 'Delta' in selected:
                st.write(f"Delta: {selected['Delta']:.4f}")
            if 'Gamma' in selected:
                st.write(f"Gamma: {selected['Gamma']:.4f}")
            if 'Theta' in selected:
                st.write(f"Theta: {selected['Theta']:.4f}")
            if 'Vega' in selected:
                st.write(f"Vega: {selected['Vega']:.4f}")
            if 'Rho' in selected:
                st.write(f"Rho: {selected['Rho']:.4f}")

        # 交易操作界面
        col3, col4, col5 = st.columns([1, 1, 1])
        with col3:
            direction = st.selectbox(
                "交易方向",
                options=["买入", "卖出"],
                key=f"direction_{option_type}"
            )
        with col4:
            quantity = st.number_input(
                "数量",
                min_value=1,
                value=1,
                step=1,
                key=f"quantity_{option_type}"
            )
        with col5:
            # 价格来源选择
            price_source = st.radio(
                "价格来源",
                options=["立即成交", "最新价"],
                key=f"price_source_{option_type}",
                horizontal=True
            )
            
            if price_source == "立即成交":
                # 根据方向自动选择买一/卖一价
                entered_price = selected["卖价"] if direction == "买入" else selected["买价"]
                st.write(f"使用{'卖' if direction == '买入' else '买'}一价: {entered_price}")
            else:
                # 允许用户手动输入价格，默认显示最新价
                entered_price = st.number_input(
                    "价格",
                    value=selected["最新价"],
                    key=f"price_{option_type}"
                )

        if st.button("添加", key=f"add_button_{option_type}"):
            # 添加新交易到列表
            new_trade = {
                'option_info': selected,
                'direction': direction,
                'quantity': quantity,
                'timestamp': pd.Timestamp.now(),
                'option_type': '看涨' if option_type == 'call' else '看跌',
                'price': entered_price
            }

            # 校验数量和价格
            if new_trade['quantity'] <= 0:
                st.warning("数量必须大于0")
                return
            if new_trade['price'] <= 0:
                st.warning("价格必须大于0")
                return
            if (new_trade['price'] > (selected["卖价"] if selected["卖价"] > 0 else selected["最新价"]) * 2 and direction == "买入"):
                st.warning("价格超过卖一价或最新价2倍，请检查")
                return
            if (new_trade['price'] < (selected["买价"] if selected["买价"] > 0 else selected["最新价"]) * 0.5 and direction == "卖出"):
                st.warning("价格低于买一价或最新价0.5倍，请检查")
                return

            if 'option_trades' not in st.session_state:
                st.session_state.option_trades = []
            # 检查同一个code的，不能重复添加
            if not any(trade['option_info']['期权代码'] == selected['期权代码'] for trade in st.session_state.option_trades):
                st.session_state.option_trades.append(new_trade)
                st.success(f"已添加{direction} {quantity}张 行权价{selected['行权价']}的{'看涨' if option_type == 'call' else '看跌'}期权, 价格: {entered_price}")
            else:
                st.warning(f"已存在该期权的交易记录，不能重复添加")


def _prepare_option_display_data(options_df, stock_price=None, option_type='call'):
    """
    准备期权显示数据
    Args:
        options_df: DataFrame containing raw option data，包含以下字段：
            - code: 期权代码
            - name: 期权名称
            - type: 期权类型（CALL/PUT）
            - strike_price: 行权价
            - last_price: 最新价
            - bid_price: 买入价
            - ask_price: 卖出价
            - bid_vol: 买入量
            - ask_vol: 卖出量
            - volume: 成交量
            - open_interest: 未平仓数
            - implied_volatility: 隐含波动率
            - delta: Delta值
            - gamma: Gamma值
            - theta: Theta值
            - vega: Vega值
            - rho: Rho值
        stock_price: Current stock price for intrinsic value calculation
        option_type: 'call' or 'put' to determine column order
    Returns:
        DataFrame formatted for display
    """
    display_df = options_df[[
        'strike_price', 'last_price', 'bid_price', 'bid_vol',
        'ask_price', 'ask_vol', 'open_interest', 'volume',
        'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho', 'code'
    ]].copy()

    # 计算内在价值
    if stock_price:
        is_call = options_df['type'].iloc[0] == 'CALL'
        display_df['intrinsic_value'] = display_df['strike_price'].apply(
            lambda x: round(max(stock_price - x if is_call else x - stock_price, 0), 3))
    else:
        display_df['intrinsic_value'] = 0.0

    # 设置序号
    display_df.index = range(1, len(display_df) + 1)
    display_df['序号'] = display_df.index

    # 重命名列
    chinese_columns = {
        'strike_price': '行权价',
        'last_price': '最新价',
        'bid_price': '买价',
        'bid_vol': '买量',
        'ask_price': '卖价',
        'ask_vol': '卖量',
        'open_interest': '未平仓数',
        'volume': '成交量',
        'implied_volatility': '隐波',
        'intrinsic_value': '内在价值',
        'delta': 'Delta',
        'gamma': 'Gamma',
        'theta': 'Theta',
        'vega': 'Vega',
        'rho': 'Rho',
        'code': '期权代码'
    }
    display_df.rename(columns=chinese_columns, inplace=True)

    # 定义基础列顺序
    base_columns = ['序号', '行权价', '最新价', '内在价值', '买价', '买量',
                    '卖价', '卖量', '未平仓数', '成交量', '隐波',
                    'Delta', 'Gamma', 'Theta', 'Vega', 'Rho', '期权代码']

    # 如果是看涨期权，反转除序号外的列顺序
    if option_type == 'call':
        reversed_columns = base_columns[1:][::-1]  # 反转除序号外的所有列
        col_order = ['序号'] + reversed_columns
    else:
        col_order = base_columns

    return display_df[col_order]
