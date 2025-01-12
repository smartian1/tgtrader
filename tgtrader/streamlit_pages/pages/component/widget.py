# encoding: utf-8
import streamlit as st
import time

def display_hint_message(message: str, message_type: str = 'info', auto_disappear: bool = False, duration: float = 1.0):
    """
    在Streamlit应用中显示提示信息
    
    参数:
    - message: 要显示的提示信息文本
    - message_type: 提示信息类型，可选值包括 'info', 'success', 'warning', 'error'
    - auto_disappear: 是否自动消失
    - duration: 消息显示的持续时间（秒）
    """
    # 创建一个占位符
    placeholder = st.empty()
    
    # 根据消息类型选择不同的Streamlit提示方法
    if message_type == 'info':
        placeholder.info(message)
    elif message_type == 'success':
        placeholder.success(message)
    elif message_type == 'warning':
        placeholder.warning(message)
    elif message_type == 'error':
        placeholder.error(message)
    else:
        # 默认使用info类型
        placeholder.info(message)
    
    # 如果设置了自动消失，则在指定时间后清空
    if auto_disappear:
        time.sleep(duration)
        placeholder.empty()

