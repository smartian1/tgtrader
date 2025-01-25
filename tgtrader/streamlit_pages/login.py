import streamlit as st
from tgtrader.service.account_service import AccountService

def login_page():
    """Display the login page"""
    st.title('登录系统')
    
    # Add debug information
    # st.write("Debug: Session State:", st.session_state)
    
    # 创建登录表单
    login_form = st.form(key="login_form")
    with login_form:
        username = st.text_input('用户名', key='username_input')
        password = st.text_input('密码', type='password', key='password_input')
        submit_button = st.form_submit_button('登录')
    
    # Form submission handling
    if submit_button:
        user_info = AccountService.verify_user(username, password)
        if user_info:
            st.success('登录成功！')
            st.session_state['logged_in'] = True
            st.session_state['user_info'] = user_info
            st.rerun()
        else:
            st.error('用户名或密码错误！')

def run():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
    
    if not st.session_state['logged_in']:
        login_page()
