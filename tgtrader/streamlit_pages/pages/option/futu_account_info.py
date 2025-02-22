# encoding utf-8

import streamlit as st
from typing import Dict, List, Optional, Tuple
from tgtrader.gateway.futu.futu_trade_gateway import FutuTradeGateway
from tgtrader.gateway.futu.defs import TradeEnv, AccountInfo, AccountCashInfo, PositionInfo, OrderInfo, OrderStatus
from loguru import logger
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode, ColumnsAutoSizeMode, DataReturnMode

def fetch_account_data(acc_id: str) -> Tuple[List[PositionInfo], Optional[AccountCashInfo], List[OrderInfo], List[OrderInfo]]:
    """从富途网关获取账户相关数据.

    获取账户的持仓、资金、未完成订单和历史订单信息.

    Args:
        acc_id: 账户ID

    Returns:
        包含以下信息的元组:
            - List[PositionInfo]: 持仓列表
            - Optional[AccountCashInfo]: 账户资金信息，如果获取失败则为None
            - List[OrderInfo]: 未完成订单列表
            - List[OrderInfo]: 历史订单列表

    Raises:
        Exception: 当网关连接失败或数据获取出错时抛出
    """
    with FutuTradeGateway() as gateway:
        positions = gateway.get_position_list(acc_id)
        cash_info_list = gateway.get_account_cash_info_list(acc_id)
        not_finished_orders = gateway.query_orders_not_finished(acc_id)
        history_orders = gateway.get_history_order_list(acc_id)
        
    cash_info = cash_info_list[0] if cash_info_list else None
    st.session_state.positions = positions
    st.session_state.cash_info = cash_info
    st.session_state.not_finished_orders = not_finished_orders
    st.session_state.history_orders = history_orders

def calculate_pl_values(positions: List[PositionInfo]) -> Tuple[float, float]:
    """计算总盈亏和今日盈亏.

    遍历持仓列表，累计计算总盈亏和今日盈亏.

    Args:
        positions: 持仓列表

    Returns:
        Tuple[float, float]: 包含以下信息的元组:
            - float: 总盈亏
            - float: 今日盈亏
    """
    total_pl_val = sum(pos.pl_val for pos in positions)
    today_pl_val = sum(pos.today_pl_val for pos in positions)
    return total_pl_val, today_pl_val

def display_account_info(cash_info: AccountCashInfo, total_pl_val: float, today_pl_val: float) -> None:
    """显示账户资金信息.

    将账户资金信息以表格形式展示，包括总资产、证券资产、现金等信息.

    Args:
        cash_info: 账户现金信息对象
        total_pl_val: 总盈亏金额
        today_pl_val: 今日盈亏金额
    """
    st.subheader("账户资金信息")
    account_info = {
        "项目": [
            "总资产",
            "证券资产净值",
            "证券市值",
            "现金总值",
            "可提总值",
            "总盈亏",
            "今日总盈亏"
        ],
        "金额": [
            f"{cash_info.total_assets:.2f}",
            f"{cash_info.securities_assets:.2f}",
            f"{cash_info.market_val:.2f}",
            f"{cash_info.cash:.2f}",
            f"{cash_info.avl_withdrawal_cash:.2f}",
            f"{total_pl_val:.2f}",
            f"{today_pl_val:.2f}"
        ]
    }
    df = pd.DataFrame(account_info)
    st.dataframe(df, hide_index=True, use_container_width=True)

def display_positions(positions: List[PositionInfo]) -> None:
    """显示账户持仓信息.

    将持仓信息以表格形式展示，包括股票代码、名称、数量、成本等信息.

    Args:
        positions: 持仓列表
    """
    st.subheader("账户持仓")
    if not positions:
        st.info("暂无持仓")
        return
    
    positions_data = {
        "代码": [pos.code for pos in positions],
        "名称": [pos.stock_name for pos in positions],
        "数量": [pos.qty for pos in positions],
        "可用": [pos.can_sell_qty for pos in positions],
        "成本价": [f"{pos.cost_price:.3f}" for pos in positions],
        "当前价": [f"{pos.nominal_price:.3f}" for pos in positions],
        "市值": [f"{pos.market_val:.2f}" for pos in positions],
        "盈亏": [f"{pos.pl_val:.2f}" for pos in positions],
        "今日盈亏": [f"{pos.today_pl_val:.2f}" for pos in positions],
    }
    
    df = pd.DataFrame(positions_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

def display_order_list(orders: List[OrderInfo], title: str) -> None:
    """显示订单列表.

    将订单信息以表格形式展示，包括股票代码、名称、交易方向、价格等信息.

    Args:
        orders: 订单列表
        title: 显示的标题
        show_time: 是否显示订单时间，默认为False
    """
    st.subheader(title)
    if not orders:
        st.info(f"暂无{title}")
        return

    orders_data = {
        "代码": [order.code for order in orders],
        "名称": [order.stock_name for order in orders],
        "方向": [order.trd_side.name for order in orders],
        "价格": [f"{order.price:.3f}" for order in orders],
        "数量": [order.qty for order in orders],
        "状态": [order.order_status.name for order in orders],
        "时间": [order.create_time for order in orders],
    }
    
    df = pd.DataFrame(orders_data)
    st.dataframe(df, hide_index=True, use_container_width=True)

def display_account_component() -> None:
    """显示账户信息组件的主函数.

    负责整体页面布局和数据展示的协调:
    1. 第一行显示账户资金信息和持仓信息(1:2布局)
    2. 第二行显示未完成订单
    3. 第三行显示历史订单

    """
    try:
        if not st.session_state.selected_account:
            return
        
        positions = st.session_state.positions if 'positions' in st.session_state else []
        cash_info = st.session_state.cash_info if 'cash_info' in st.session_state else None
        not_finished_orders = st.session_state.not_finished_orders if 'not_finished_orders' in st.session_state else []
        history_orders = st.session_state.history_orders if 'history_orders' in st.session_state else []

        # 第一行：账户资金信息和持仓信息 (1:2)
        account_col, positions_col = st.columns([1, 3])
        
        with account_col:
            if cash_info:
                total_pl_val, today_pl_val = calculate_pl_values(positions)
                display_account_info(cash_info, total_pl_val, today_pl_val)
            else:
                st.error("获取账户资金信息失败")
        
        with positions_col:
            display_positions(positions)
        
        # 第二行：未完成订单
        display_not_finished_order_list(not_finished_orders, st.session_state.selected_account.acc_id)
        
        # 第三行：历史订单
        display_order_list(history_orders, "历史订单")
            
    except Exception as e:
        logger.exception("Failed to display account information")
        st.error(f"获取账户详情失败: {str(e)}")
    finally:
        st.session_state.query_account = False

def display_left_column(positions: List[PositionInfo], cash_info: Optional[AccountCashInfo]) -> None:
    """显示左侧栏内容，包括账户信息和持仓信息.
    
    Args:
        positions: 持仓列表
        cash_info: 账户现金信息
    """
    try:
        if not cash_info:
            st.error("获取账户资金信息失败")
            return

        total_pl_val, today_pl_val = calculate_pl_values(positions)
        display_account_info(cash_info, total_pl_val, today_pl_val)
        display_positions(positions)
    except Exception as e:
        logger.exception(e)
        st.error(f"获取账户详情失败: {str(e)}")

def display_right_column(not_finished_orders: List[OrderInfo], history_orders: List[OrderInfo]) -> None:
    """显示右侧栏内容，包括未完成订单和历史订单.
    
    Args:
        not_finished_orders: 未完成订单列表
        history_orders: 历史订单列表
    """
    try:
        display_order_list(not_finished_orders, "未完成订单")
        display_order_list(history_orders, "历史订单", show_time=True)
    except Exception as e:
        logger.error(f"Failed to get order details: {str(e)}")
        st.error(f"获取订单详情失败: {str(e)}")

def display_not_finished_order_list(orders: List[OrderInfo], acc_id: str) -> None:
    """显示未完成订单列表.

    使用AgGrid显示未完成订单，并提供撤单功能.

    Args:
        orders: 未完成订单列表
        acc_id: 账户ID
    """
    st.subheader("未完成订单")
    if not orders:
        st.info("暂无未完成订单")
        return

    # 转换数据为DataFrame格式
    df = pd.DataFrame([{
        "代码": order.code,
        "名称": order.stock_name,
        "方向": order.trd_side.name,
        "价格": f"{order.price:.3f}",
        "数量": order.qty,
        "状态": order.order_status.name,
        "order_id": order.order_id,  # 用于撤单操作
        "时间": order.create_time
    } for order in orders])

    df = df.sort_values(by='时间', ascending=False)

    # 配置AgGrid选项
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode='single', use_checkbox=False)
    gb.configure_column('代码', minWidth=100)
    gb.configure_column('名称', minWidth=100)
    gb.configure_column('方向', minWidth=80)
    gb.configure_column('价格', minWidth=80)
    gb.configure_column('数量', minWidth=80)
    gb.configure_column('状态', minWidth=100)
    gb.configure_column('order_id', hide=True)  # 隐藏order_id列
    gb.configure_column('时间', minWidth=160)

    grid_options = gb.build()

    # 显示AgGrid表格
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=400,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme='streamlit'
    )

    # 处理选择和撤单
    selected = grid_response['selected_rows']
    if selected is not None and len(selected) > 0:
        selected_order = selected.iloc[0]
        logger.debug(f"Selected order: {selected_order}")
        
        # 显示撤单按钮
        if st.button("撤销所选订单"):
            try:
                order_status = selected_order['状态']
                if OrderStatus(order_status) not in [OrderStatus.WAITING_SUBMIT, 
                                        OrderStatus.SUBMITTED,
                                        OrderStatus.FILLED_PART]:
                    st.warning("当前状态不可撤单")
                    return

                cancel_order(selected_order['order_id'], 
                selected_order['数量'], 
                selected_order['价格'])

                st.success("撤单成功, 点击查询按钮刷新订单信息")

            except Exception as e:
                st.error(f"撤单失败: {str(e)}")
                logger.exception(f"Cancel order failed: {str(e)}")

def cancel_order(order_id, qty, price):
    if 'selected_account' not in st.session_state or not st.session_state.selected_account:
        st.warning("请先选择账户")
        return
    
    if 'password' not in st.session_state or not st.session_state.password:
        st.warning("请先输入密码")
        return

    order_info = OrderInfo(
        order_id=order_id,
        price=price,
        qty=qty,
    )
    
    acc_id = st.session_state.selected_account.acc_id
    with FutuTradeGateway() as gateway:
        gateway.unlock_trade(st.session_state.password, is_unlock=True)
        gateway.cancel_order(acc_id, order_info)
        gateway.unlock_trade(st.session_state.password, is_unlock=False)
        logger.info(f"取消订单: {order_info}, acc_id: {acc_id}")

@st.fragment
def account_info_component():
    """
    富途账户信息组件，包含账号选择、资金信息、持仓信息和订单信息展示.
    
    布局如下：
    1. 上方：账号选择下拉框、密码输入框、查询按钮
    2. 左侧：账户资金信息和持仓信息
    3. 右侧：未完成订单和历史订单
    """
    # 初始化会话状态
    if 'account_list' not in st.session_state:
        st.session_state.account_list = []
    if 'selected_account' not in st.session_state:
        st.session_state.selected_account = None
    if 'password' not in st.session_state:
        st.session_state.password = None
    
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
        st.session_state.password = password
    
    with col3:
        if st.button("查询", key="futu_query_button"):
            if not st.session_state.selected_account:
                st.error("请先选择账号")
                return
                
            if not password:
                st.error("请输入交易密码")
                return

            fetch_account_data(
                st.session_state.selected_account.acc_id
            )
    
    if not password:
        return
        
    display_account_component()

def get_account_and_password() -> tuple[AccountInfo, str]:
    account_info = st.session_state.selected_account if 'selected_account' in st.session_state else None
    pwd = st.session_state.password if 'password' in st.session_state else None

    return account_info, pwd