# encoding utf-8

import streamlit as st
from typing import Dict, List, Optional
from tgtrader.gateway.futu.futu_trade_gateway import FutuTradeGateway
from tgtrader.gateway.futu.defs import TradeEnv, AccountInfo, AccountCashInfo, PositionInfo, OrderInfo
from loguru import logger

def account_info_component():
    """
    富途账户信息组件，包含账户选择、资金信息、持仓信息和订单信息展示。
    
    布局如下：
    1. 上方：账号选择下拉框、密码输入框、查询按钮
    2. 左侧：账户资金信息和持仓信息
    3. 右侧：未完成订单和历史订单
    """
    # 初始化会话状态
    if 'gateway' not in st.session_state:
        st.session_state.gateway = None
    if 'account_list' not in st.session_state:
        st.session_state.account_list = []
    if 'selected_account' not in st.session_state:
        st.session_state.selected_account = None
    
    # 上方控件区域
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # 获取账号列表
        if not st.session_state.account_list:
            try:
                with FutuTradeGateway() as gateway:
                    st.session_state.account_list = gateway.get_account_list(TradeEnv.REAL)
            except Exception as e:
                logger.error(f"Failed to get account list: {str(e)}")
                st.error("获取账号列表失败")
                st.session_state.account_list = []
        
        account_options = [f"{acc.security_firm}-{acc.acc_id}" for acc in st.session_state.account_list]
        selected_account = st.selectbox(
            "选择账号",
            options=account_options if account_options else ["暂无账号"],
            key="futu_account_select"
        )
        if account_options:
            st.session_state.selected_account = next(
                (acc for acc in st.session_state.account_list 
                 if f"{acc.security_firm}-{acc.acc_id}" == selected_account),
                None
            )
    
    with col2:
        password = st.text_input(
            "交易密码",
            type="password",
            key="futu_account_password"
        )
    
    with col3:
        if st.button("查询", key="futu_query_button"):
            if not st.session_state.selected_account:
                st.error("请先选择账号")
                return
                
            if not password:
                st.error("请输入交易密码")
                return
                
            try:
                # 初始化富途交易网关
                gateway = FutuTradeGateway(
                    host="127.0.0.1",
                    port=11111
                )
                
                # 解锁交易
                gateway.unlock_trade(password, True)
                st.session_state.gateway = gateway
                logger.info("Successfully unlocked Futu trade gateway")
                
            except Exception as e:
                logger.error(f"Failed to initialize gateway: {str(e)}")
                st.error(f"初始化失败: {str(e)}")
                return
    
    # 主体内容区域
    left_col, right_col = st.columns([1, 1])
    
    # 左侧：账户信息
    with left_col:
        if st.session_state.gateway and st.session_state.selected_account:
            try:
                # 账户资金信息
                st.subheader("账户资金信息")
                cash_info = st.session_state.gateway.get_account_cash_info_list(
                    st.session_state.selected_account.acc_id
                )
                
                # 显示资金信息
                account_info = {
                    "总资产": f"{cash_info.total_assets:.2f}",
                    "证券资产净值": f"{cash_info.securities_assets:.2f}",
                    "证券市值": f"{cash_info.market_val:.2f}",
                    "现金总值": f"{cash_info.cash:.2f}",
                    "可提总值": f"{cash_info.avl_withdrawal_cash:.2f}"
                }
                for key, value in account_info.items():
                    st.text(f"{key}: {value}")
                
                # 账户持仓信息
                st.subheader("账户持仓")
                positions = st.session_state.gateway.get_position_list(
                    st.session_state.selected_account.acc_id
                )
                
                if positions:
                    for pos in positions:
                        st.write(f"""
                        {pos.code} - {pos.stock_name}  
                        数量: {pos.qty} | 可用: {pos.can_sell_qty}  
                        成本价: {pos.cost_price:.3f} | 当前价: {pos.current_price:.3f}  
                        市值: {pos.market_val:.2f} | 盈亏: {pos.pl_val:.2f}
                        """)
                else:
                    st.info("暂无持仓")
                    
            except Exception as e:
                logger.error(f"Failed to get account details: {str(e)}")
                st.error(f"获取账户详情失败: {str(e)}")
    
    # 右侧：订单信息
    with right_col:
        if st.session_state.gateway and st.session_state.selected_account:
            try:
                # 未完成订单
                st.subheader("未完成订单")
                orders = st.session_state.gateway.get_order_list(
                    st.session_state.selected_account.acc_id,
                    status_filter_list=["SUBMITTED", "WAITING", "SUBMITTING"]
                )
                
                if orders:
                    for order in orders:
                        st.write(f"""
                        {order.code} - {order.stock_name}  
                        方向: {order.trd_side.name} | 价格: {order.price:.3f}  
                        数量: {order.qty} | 状态: {order.order_status.name}
                        """)
                else:
                    st.info("暂无未完成订单")
                
                # 历史订单
                st.subheader("历史订单")
                history_orders = st.session_state.gateway.get_order_list(
                    st.session_state.selected_account.acc_id,
                    status_filter_list=["FILLED", "CANCELLED", "FAILED"]
                )
                
                if history_orders:
                    for order in history_orders:
                        st.write(f"""
                        {order.code} - {order.stock_name}  
                        方向: {order.trd_side.name} | 价格: {order.price:.3f}  
                        数量: {order.qty} | 状态: {order.order_status.name}
                        """)
                else:
                    st.info("暂无历史订单")
                    
            except Exception as e:
                logger.error(f"Failed to get order details: {str(e)}")
                st.error(f"获取订单详情失败: {str(e)}")