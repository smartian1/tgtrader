import streamlit as st
import pandas as pd
from tgtrader.gateway.futu.futu_option_gateway import FutuOptionGateway
from tgtrader.gateway.futu.defs import OptionType
from tgtrader.gateway.futu.futu_stock_gateway import FutuStockGateway
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import JsCode
from loguru import logger

def get_option_expiration_date(stock_code: str):
    with FutuOptionGateway() as option_gateway:
        expiry_dates = option_gateway.get_option_expiration_date(
            stock_code)

    return expiry_dates

def get_option_chain(stock_code: str, expiry_date: str):
    # 初始化FUTU期权网关
    with FutuOptionGateway() as option_gateway:
        # 获取期权链数据
        option_chain = option_gateway.get_option_chain(
            stock_code, expiry_date)

        if option_chain:
            # 批量获取期权快照数据
            option_codes = [item.code for item in option_chain]
            snapshots = option_gateway.get_option_snapshot(
                option_codes)

            # 创建快照数据字典以便快速查找
            snapshot_dict = {
                snapshot.code: snapshot for snapshot in snapshots}

            # 将期权链数据转换为DataFrame
            chain_data = []
            for item in option_chain:
                snapshot = snapshot_dict.get(item.code)
                if snapshot:
                    chain_data.append({
                        'code': item.code,
                        'name': item.name,
                        'type': item.option_type,
                        'strike_price': item.strike_price,
                        'last_price': snapshot.last_price if snapshot.last_price else 0.0,
                        'bid_price': snapshot.bid_price if snapshot.bid_price else 0.0,
                        'ask_price': snapshot.ask_price if snapshot.ask_price else 0.0,
                        'ask_vol': snapshot.ask_vol if snapshot.ask_vol else 0.0,
                        'bid_vol': snapshot.bid_vol if snapshot.bid_vol else 0.0,
                        'volume': snapshot.volume if snapshot.volume else 0,
                        'open_interest': snapshot.option_open_interest if snapshot.option_open_interest else 0,
                        'implied_volatility': round(snapshot.option_implied_volatility, 4) if snapshot.option_implied_volatility else 0.0000,
                        'delta': round(snapshot.option_delta, 4) if snapshot.option_delta else 0.0000,
                        'gamma': round(snapshot.option_gamma, 4) if snapshot.option_gamma else 0.0000,
                        'theta': round(snapshot.option_theta, 4) if snapshot.option_theta else 0.0000,
                        'vega': round(snapshot.option_vega, 4) if snapshot.option_vega else 0.0000,
                        'rho': round(snapshot.option_rho, 4) if snapshot.option_rho else 0.0000
                    })

        df = pd.DataFrame(chain_data)

        return df

def get_stock_price(stock_code: str):
    # 获取股票最新价格
    with FutuStockGateway() as stock_gateway:
        stock_snapshot = stock_gateway.get_stock_snapshot([stock_code])
        stock_price = None
        if stock_snapshot:
            stock_price = stock_snapshot[0].last_price

    return stock_price

def create_grid_options(df, stock_price=None, option_type='call'):
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
        "序号": 60,
        "行权价": 80,
        "最新价": 80,
        "买价": 30,
        "买量": 30,
        "卖价": 30,
        "卖量": 30,
        "成交量": 80,
        "未平仓数": 50,
        "内在价值": 100,
        "隐波": 70,
        "Delta": 70,
        "Gamma": 70,
        "Theta": 70,
        "Vega": 70,
        "Rho": 70
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
        sorteable=True,
        filterable=True,
        type=["numericColumn", "numberColumnFilter"],
        cellStyle={'text-align': 'right'}
    )
    
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

def display_option_table(df, title, stock_price=None, option_type='call'):
    """
    显示期权数据表格
    Args:
        df: DataFrame containing the option data
        title: Table title
        stock_price: Current stock price for highlighting
        option_type: 'call' or 'put' to determine highlighting logic
    """
    st.subheader(title)
    grid_options = create_grid_options(df, stock_price, option_type)
    AgGrid(df,
           gridOptions=grid_options,
           height=600,
           width='100%',
           allow_unsafe_jscode=True,
           fit_columns_on_grid_load=False)

def prepare_option_display_data(options_df, stock_price=None, option_type='call'):
    """
    准备期权显示数据
    Args:
        options_df: DataFrame containing raw option data
        stock_price: Current stock price for intrinsic value calculation
        option_type: 'call' or 'put' to determine column order
    Returns:
        DataFrame formatted for display
    """
    display_df = options_df[[
        'strike_price', 'last_price', 'bid_price', 'bid_vol',
        'ask_price', 'ask_vol', 'open_interest', 'volume',
        'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho'
    ]].copy()
    
    # 计算内在价值
    if stock_price:
        is_call = options_df['type'].iloc[0] == OptionType.CALL
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
        'rho': 'Rho'
    }
    display_df.rename(columns=chinese_columns, inplace=True)
    
    # 定义基础列顺序
    base_columns = ['序号', '行权价', '最新价', '内在价值', '买价', '买量', 
                    '卖价', '卖量', '未平仓数', '成交量', '隐波',
                    'Delta', 'Gamma', 'Theta', 'Vega', 'Rho']
    
    # 如果是看涨期权，反转除序号外的列顺序
    if option_type == 'call':
        reversed_columns = base_columns[1:][::-1]  # 反转除序号外的所有列
        col_order = ['序号'] + reversed_columns
    else:
        col_order = base_columns
    
    return display_df[col_order]

def display_option_chain(call_options, put_options, stock_price=None):
    """
    显示期权链数据
    Args:
        call_options: DataFrame containing call options
        put_options: DataFrame containing put options
        stock_price: Current stock price
    """
    # 准备数据
    call_display = prepare_option_display_data(call_options, stock_price, 'call')
    put_display = prepare_option_display_data(put_options, stock_price, 'put')
    
    # 创建两列布局显示数据
    col_call, col_put = st.columns(2)
    
    with col_call:
        display_option_table(call_display, "看涨期权", stock_price, 'call')
    
    with col_put:
        display_option_table(put_display, "看跌期权", stock_price, 'put')

def run():
    """
    期权报价页面
    Option quotes page implementation
    """

    # 调整页面样式
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            margin: 0;
        }
        div[data-testid="stDateInput"] > div {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    # 创建上方的查询区域，使用更紧凑的布局
    col1, col2, col3 = st.columns([3, 1, 3])

    with col1:
        # 股票代码输入框
        stock_code = st.text_input("股票代码",
                                   value="",  # 清空默认值
                                   label_visibility="visible",
                                   placeholder="请输入",
                                   help="输入港股代码，如：HK.00700")
        if stock_code and not stock_code.startswith("HK."):
            stock_code = f"HK.{stock_code}"

    with col2:
        # 查询按钮，调整垂直对齐
        st.write("")  # 添加空行以对齐
        st.write("")  # 添加空行以对齐
        query_button = st.button("查询")

    # 初始化session state
    if 'expiry_dates' not in st.session_state:
        st.session_state.expiry_dates = []

    # 如果点击查询按钮且有股票代码，获取到期日列表
    if query_button and stock_code:
        try:
            expiry_dates = get_option_expiration_date(stock_code)
            st.session_state.expiry_dates = [
                date.strike_time for date in expiry_dates]
        except Exception as e:
            logger.exception(e)
            st.error(f"获取期权到期日失败: {str(e)}")
            st.session_state.expiry_dates = []

    with col3:
        # 到期日选择
        expiry_date = st.selectbox("到期日",
                                   options=st.session_state.expiry_dates,
                                   index=0 if st.session_state.expiry_dates else None,
                                   label_visibility="visible",
                                   help="选择期权到期日")

    # 如果选择了到期日且有股票代码，获取期权链数据
    if stock_code and expiry_date:
        try:
            df = get_option_chain(stock_code, expiry_date)

            if df is None or df.empty:
                st.warning("未找到相关期权数据")
                return

            stock_price = get_stock_price(stock_code)

            # 显示股票最新价
            if stock_price:
                st.metric(label=f"{stock_code} 最新价", value=f"{stock_price:.3f}")

            # 分离看涨和看跌期权
            call_options = df[df['type'] == OptionType.CALL].sort_values(
                'strike_price', ascending=True).reset_index(drop=True)
            put_options = df[df['type'] == OptionType.PUT].sort_values(
                'strike_price', ascending=True).reset_index(drop=True)

            # 显示期权链数据
            display_option_chain(call_options, put_options, stock_price)

        except Exception as e:
            logger.exception(e)
            st.error(f"获取期权数据失败: {str(e)}")

    elif query_button and not stock_code:
        st.warning("请输入股票代码")
