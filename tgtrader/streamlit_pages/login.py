import streamlit as st
from .service.account_service import AccountService

def login_page():
    """Display the login page"""
    st.title('登录系统')
    
    # 创建登录表单
    with st.form("login_form"):
        username = st.text_input('用户名')
        password = st.text_input('密码', type='password')
        submit = st.form_submit_button('登录')
        
        if submit:
            user_info = AccountService.verify_user(username, password)
            if user_info:
                st.success('登录成功！')
                # 设置session state表示用户已登录
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = user_info
            else:
                st.error('用户名或密码错误！')

def main():
    # 检查用户是否已登录
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        
    if not st.session_state['logged_in']:
        login_page()
    else:
        # 显示已登录状态
        user_info = st.session_state['user_info']
        st.write(f'欢迎回来, {user_info["username"]}!')
        st.write(f'用户角色: {user_info["role"]}')
        
        if st.button('退出登录'):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

main()