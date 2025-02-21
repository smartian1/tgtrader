# encoding: utf-8

import streamlit as st
from loguru import logger

from tgtrader.gateway.futu.futu_trade_gateway import FutuTradeGateway
from tgtrader.streamlit_pages.pages.option.comp_option_chain import get_option_trader
from tgtrader.streamlit_pages.pages.option.futu_account_info import get_account_and_password

@st.fragment
def submit_option_order():
    btn_submit_order = st.button("提交订单")

    if btn_submit_order:
        option_traders: list[OptionTrade] = get_option_trader()
        account_info, password = get_account_and_password()
        
        if not account_info or not password:
            st.warning("请先选择账号和密码")
            return

        with FutuTradeGateway() as gateway:
            gateway.unlock_trade(password, is_unlock=True)

            for order in option_traders:
                try:
                    order_info = gateway.place_order(account_info.acc_id, 
                                            code=order.code, 
                                            qty=order.quantity, 
                                            price=order.price, 
                                            trd_side=order.convert_direction())
                    logger.info(f"下单信息：acc_id={account_info.acc_id}, code={order.code}, qty={order.quantity}, price={order.price}, trd_side={order.convert_direction()}")
                except Exception as e:
                    logger.exception(e)

            gateway.unlock_trade(password, is_unlock=False)

        st.success("下单成功, 请点击账户查询，查看订单状态")