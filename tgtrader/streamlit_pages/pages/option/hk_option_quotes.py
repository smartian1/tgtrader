import streamlit as st
import pandas as pd
from tgtrader.gateway.futu.futu_option_gateway import FutuOptionGateway
from tgtrader.gateway.futu.defs import OptionType
from tgtrader.gateway.futu.futu_stock_gateway import FutuStockGateway
from tgtrader.gateway.futu.common import check_futu_gateway_avalable
from loguru import logger
from tgtrader.streamlit_pages.pages.option.comp_option_chain import clear_option_trader, build_option_chain_page
from tgtrader.streamlit_pages.pages.option.futu_account_info import account_info_component
from tgtrader.streamlit_pages.pages.option.submit_option_order import submit_option_order

def get_option_expiration_date(stock_code: str):
    with FutuOptionGateway() as option_gateway:
        expiry_dates = option_gateway.get_option_expiration_date(
            stock_code)

    return expiry_dates

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

    if not check_futu_gateway_avalable():
        st.error("富途网关未启动, 请先启动Futu OpenD. 下载地址: https://openapi.futunn.com/futu-api-doc/opend/opend-cmd.html")
        return

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

            if not expiry_dates:
                st.error("获取期权数据失败, 请检查股票代码是否正确")
                return

            st.session_state.expiry_dates = [
                date.strike_time for date in expiry_dates if date.option_expiry_date_distance > 0]

            # 是否选择了新的股票,如果是,需要清空相关信息
            if 'stock_code' in st.session_state and stock_code != st.session_state.stock_code:
                clear_option_trader()

            st.session_state.stock_code = stock_code
            
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
            stock_price = get_stock_price(stock_code)

            # 显示股票最新价
            if stock_price:
                st.metric(label=f"{stock_code} 最新价",
                          value=f"{stock_price:.3f}")

            # 显示期权链数据
            build_option_chain_page(stock_code, expiry_date, stock_price)

            # 提交订单
            submit_option_order()
            
            # 账户信息
            account_info_component()

        except Exception as e:
            logger.exception(e)
            st.error(f"获取期权数据失败: {str(e)}")

    elif query_button and not stock_code:
        st.warning("请输入股票代码")

