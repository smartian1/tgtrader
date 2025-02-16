# encoding: utf-8
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from tgtrader.gateway.futu.defs import OptionType
from loguru import logger


def display_option_chain(call_options, put_options, stock_price=None):
    """
    显示期权链数据
    Args:
        call_options: DataFrame containing call options
        put_options: DataFrame containing put options
        stock_price: Current stock price
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
                           height=600,
                           width='100%',
                           allow_unsafe_jscode=True,
                           fit_columns_on_grid_load=False,
                           key=f"option_grid_{option_type}")

    selected = grid_response['selected_rows']
    return selected


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
