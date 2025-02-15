# encoding: utf-8

import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from tgtrader.gateway.futu.futu_option_gateway import FutuOptionGateway
from tgtrader.gateway.futu.defs import OptionType
from tgtrader.gateway.futu.futu_stock_gateway import FutuStockGateway

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
            option_gateway = FutuOptionGateway()
            expiry_dates = option_gateway.get_option_expiration_date(stock_code)
            st.session_state.expiry_dates = [date.strike_time for date in expiry_dates]
        except Exception as e:
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
            # 初始化FUTU期权网关
            option_gateway = FutuOptionGateway()
            
            # 获取期权链数据
            option_chain = option_gateway.get_option_chain(stock_code, expiry_date)
            
            if option_chain:
                # 批量获取期权快照数据
                option_codes = [item.code for item in option_chain]
                snapshots = option_gateway.get_option_snapshot(option_codes)
                
                # 创建快照数据字典以便快速查找
                snapshot_dict = {snapshot.code: snapshot for snapshot in snapshots}
                
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
                            'implied_volatility': snapshot.option_implied_volatility if snapshot.option_implied_volatility else 0.0,
                            'delta': snapshot.option_delta if snapshot.option_delta else 0.0,
                            'gamma': snapshot.option_gamma if snapshot.option_gamma else 0.0,
                            'theta': snapshot.option_theta if snapshot.option_theta else 0.0,
                            'vega': snapshot.option_vega if snapshot.option_vega else 0.0,
                            'rho': snapshot.option_rho if snapshot.option_rho else 0.0
                        })
                
                df = pd.DataFrame(chain_data)

                # 获取股票最新价格
                stock_gateway = FutuStockGateway()
                stock_snapshot = stock_gateway.get_stock_snapshot([stock_code])
                stock_price = None
                if stock_snapshot:
                    stock_price = stock_snapshot[0].last_price
                
                # 分离看涨和看跌期权
                call_options = df[df['type'] == OptionType.CALL].sort_values('strike_price', ascending=True).reset_index(drop=True)
                put_options = df[df['type'] == OptionType.PUT].sort_values('strike_price', ascending=True).reset_index(drop=True)
                
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
                    'gamma': 'Gamma',
                    'theta': 'Theta',
                    'vega': 'Vega',
                    'rho': 'Rho'
                }
                
                # 准备看涨期权数据
                call_display = call_options[[
                    'rho', 'vega', 'theta', 'gamma', 'delta', 'implied_volatility',
                    'ask_price', 'ask_vol', 'bid_price', 'bid_vol',
                    'volume', 'open_interest',
                    'last_price', 'strike_price'
                ]].copy()
                call_display.columns = [columns_map[col] for col in call_display.columns]
                
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
                    '未平仓量', '成交量',
                    '隐波', 'Delta', 'Gamma', 'Theta', 'Vega', 'Rho',
                ]
                
                # 设置序号从1开始
                call_display.index = range(1, len(call_display) + 1)
                put_display.index = range(1, len(put_display) + 1)
                
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
                    st.dataframe(
                        call_display.style
                        .apply(lambda x: highlight_options(x, stock_price, 'call'), axis=1)
                        .format({
                            '买量': '{:,.0f}',
                            '卖量': '{:,.0f}',
                            '持仓量': '{:,.0f}',
                            '成交量': '{:,.0f}',
                            '隐波': '{:.2%}',
                            'Delta': '{:.4f}',
                            'Gamma': '{:.4f}',
                            'Theta': '{:.4f}',
                            'Vega': '{:.4f}',
                            'Rho': '{:.4f}',
                            '卖价': '{:.3f}',
                            '买价': '{:.3f}',
                            '最新价': '{:.3f}',
                            '行权价': '{:.1f}'
                        }),
                        use_container_width=True,
                        height=600
                    )
                
                with col_put:
                    st.subheader("看跌期权")
                    st.dataframe(
                        put_display.style
                        .apply(lambda x: highlight_options(x, stock_price, 'put'), axis=1)
                        .format({
                            '买量': '{:,.0f}',
                            '卖量': '{:,.0f}',
                            '持仓量': '{:,.0f}',
                            '成交量': '{:,.0f}',
                            '隐波': '{:.2%}',
                            'Delta': '{:.4f}',
                            'Gamma': '{:.4f}',
                            'Theta': '{:.4f}',
                            'Vega': '{:.4f}',
                            'Rho': '{:.4f}',
                            '卖价': '{:.3f}',
                            '买价': '{:.3f}',
                            '最新价': '{:.3f}',
                            '行权价': '{:.1f}'
                        }),
                        use_container_width=True,
                        height=600
                    )
            else:
                st.warning("未找到相关期权数据")
                
        except Exception as e:
            st.error(f"获取期权数据失败: {str(e)}")
    
    elif query_button and not stock_code:
        st.warning("请输入股票代码")

