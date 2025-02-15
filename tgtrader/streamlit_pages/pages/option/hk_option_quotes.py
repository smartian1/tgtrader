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

            # 分离看涨和看跌期权
            call_options = df[df['type'] == OptionType.CALL].sort_values(
                'strike_price', ascending=True).reset_index(drop=True)
            put_options = df[df['type'] == OptionType.PUT].sort_values(
                'strike_price', ascending=True).reset_index(drop=True)

            # 设置列名映射
            columns_map = {
                'volume': '成交量',
                'last_price': '最新价',
                'bid_price': '买价',
                'ask_price': '卖价',
                'ask_vol': '卖量',
                'bid_vol': '买量',
                'strike_price': '行权价',
                'code': '合约',
                'open_interest': '未平仓数',
                'implied_volatility': '隐波',
                'delta': 'Delta',
                'theta': 'Theta',
                'vega': 'Vega',
                'rho': 'Rho',
                'gamma': 'Gamma'
            }

            # 准备看涨期权数据
            call_display = call_options[[
                'rho', 'vega', 'theta', 'gamma', 'delta', 'implied_volatility',
                'volume', 'open_interest',
                'ask_vol', 'ask_price', 'bid_vol', 'bid_price',
                'last_price', 'strike_price'
            ]].copy()
            call_display.columns = [columns_map[col]
                                    for col in call_display.columns]

            # 准备看跌期权数据
            put_display = put_options[[
                'strike_price', 'last_price',
                'bid_price', 'bid_vol', 'ask_price', 'ask_vol',
                'open_interest', 'volume',
                'implied_volatility', 'delta', 'gamma', 'theta', 'vega', 'rho',
            ]].copy()
            put_display.columns = [
                '行权价', '最新价',
                '买价', '买量', '卖价', '卖量',
                '未平仓数', '成交量',
                '隐波', 'Delta', 'Gamma', 'Theta', 'Vega', 'Rho',
            ]

            # 设置序号从1开始
            call_display.index = range(1, len(call_display) + 1)
            put_display.index = range(1, len(put_display) + 1)

            # 添加序号列
            call_display['序号'] = call_display.index
            put_display['序号'] = put_display.index
            
            # 重新排列put_display的列，让序号在最前
            put_cols = put_display.columns.tolist()
            put_cols.remove('序号')
            put_display = put_display[['序号'] + put_cols]

            # 创建两列布局
            col_call, col_put = st.columns(2)

            # 定义样式函数
            def highlight_options(row, stock_price, option_type):
                if stock_price is None:
                    return [''] * len(row)
                strike = row['行权价']
                if option_type == 'call':
                    return ['background-color: #e6ffe6' if strike < stock_price else 'background-color: #ffe6e6' for _ in row]
                else:  # put
                    return ['background-color: #e6ffe6' if strike > stock_price else 'background-color: #ffe6e6' for _ in row]

            with col_call:
                st.subheader("看涨期权")
                # Display data using AgGrid
                gb = GridOptionsBuilder.from_dataframe(call_display)
                
                # 配置列宽和固定列
                gb.configure_column("序号", width=60, pinned='right')
                gb.configure_column("行权价", width=80)
                gb.configure_column("Rho", width=70)
                gb.configure_column("Vega", width=70)
                gb.configure_column("Theta", width=70)
                gb.configure_column("Gamma", width=70)
                gb.configure_column("Delta", width=70)
                gb.configure_column("隐波", width=70)
                gb.configure_column("卖价", width=30)
                gb.configure_column("卖量", width=30)
                gb.configure_column("买价", width=30)
                gb.configure_column("买量", width=30)
                gb.configure_column("成交量", width=80)
                gb.configure_column("未平仓数", width=50)
                gb.configure_column("最新价", width=80)
                
                # 配置列对齐方式
                gb.configure_default_column(
                    resizable=True,
                    sorteable=True,
                    filterable=True,
                    type=["numericColumn", "numberColumnFilter"],
                    cellStyle={'text-align': 'right'}
                )
                
                # 为整行添加条件样式
                if stock_price:
                    gb.configure_grid_options(
                        getRowStyle=JsCode(f"""
                        function(params) {{
                            if (params.data['行权价'] < {stock_price}) {{
                                return {{'backgroundColor': '#e6ffe6'}}; // 浅绿色
                            }} else if (params.data['行权价'] > {stock_price}) {{
                                return {{'backgroundColor': '#ffe6e6'}}; // 浅红色
                            }}
                            return {{'backgroundColor': '#ffffff'}}; // 相等时白色
                        }}
                        """))
                
                grid_options = gb.build()
                AgGrid(call_display, 
                        gridOptions=grid_options,
                        height=600,
                        width='100%',
                        allow_unsafe_jscode=True,  # 允许使用JsCode
                        fit_columns_on_grid_load=False)  # 禁用自动适应列宽

            with col_put:
                st.subheader("看跌期权")
                # Display data using AgGrid
                gb = GridOptionsBuilder.from_dataframe(put_display)
                
                # 配置列宽和固定列
                gb.configure_column("序号", width=60, pinned='left')
                gb.configure_column("行权价", width=60)
                gb.configure_column("最新价", width=60)
                gb.configure_column("买价", width=30)
                gb.configure_column("买量", width=30)
                gb.configure_column("卖价", width=30)
                gb.configure_column("卖量", width=30)
                gb.configure_column("未平仓数", width=50)
                gb.configure_column("成交量", width=80)
                gb.configure_column("隐波", width=70)
                gb.configure_column("Delta", width=70)
                gb.configure_column("Gamma", width=70)
                gb.configure_column("Theta", width=70)
                gb.configure_column("Vega", width=70)
                gb.configure_column("Rho", width=70)
                
                # 配置列对齐方式
                gb.configure_default_column(
                    resizable=True,
                    sorteable=True,
                    filterable=True,
                    type=["numericColumn", "numberColumnFilter"],
                    cellStyle={'text-align': 'right'}
                )
                
                # 为整行添加条件样式
                if stock_price:
                    gb.configure_grid_options(
                        getRowStyle=JsCode(f"""
                        function(params) {{
                            if (params.data['行权价'] > {stock_price}) {{
                                return {{'backgroundColor': '#e6ffe6'}}; // 浅绿色
                            }} else if (params.data['行权价'] < {stock_price}) {{
                                return {{'backgroundColor': '#ffe6e6'}}; // 浅红色
                            }}
                            return {{'backgroundColor': '#ffffff'}}; // 相等时白色
                        }}
                        """))
                
                grid_options = gb.build()
                AgGrid(put_display, 
                        gridOptions=grid_options,
                        height=600,
                        width='100%',
                        allow_unsafe_jscode=True,  # 允许使用JsCode
                        fit_columns_on_grid_load=False)  # 禁用自动适应列宽

        except Exception as e:
            logger.exception(e)
            st.error(f"获取期权数据失败: {str(e)}")

    elif query_button and not stock_code:
        st.warning("请输入股票代码")
