# encoding: utf-8

import streamlit as st
from tgtrader.streamlit_pages.pages.welcome import run as welcome_run
from tgtrader.streamlit_pages.login import run as login_run
from tgtrader.streamlit_pages.pages.strategies.target_weight_strats import run as target_weight_strats_run
from tgtrader.streamlit_pages.pages.strategies.risk_parity_strats import run as risk_parity_strats_run
from tgtrader.streamlit_pages.pages.strategies.my_strategies import run as my_strategies_run
from tgtrader.streamlit_pages.pages.accounts.settings import run as settings_run
from tgtrader.streamlit_pages.pages.data.data_init import run as data_init_run


def logout():
    # Clear session state
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.rerun()

def run():
    # Check if user is logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_page = st.Page(login_run, title='登录', icon=':material/login:')
        pg = st.navigation([login_page])
    else:
        strategy_pages = {}


        welcome_page = st.Page(welcome_run, title='欢迎', icon=':material/home:', default=True, url_path='welcome')
        strategy_pages['欢迎'] = [welcome_page]

        data_init_page = st.Page(
            data_init_run, title='数据初始化', icon=':material/database:', url_path='data_init')
        strategy_pages['数据'] = [data_init_page]

        target_weights_page = st.Page(target_weight_strats_run, title='目标权重策略', icon=':material/target:', url_path='strategies_target_weights')
        risk_parity_page = st.Page(risk_parity_strats_run, title='风险平价策略', icon=':material/balance:', url_path='strategies_risk_parity')
        strategy_pages['策略列表'] = [target_weights_page, risk_parity_page]

        my_strategies_page = st.Page(my_strategies_run, title='我的策略', icon=':material/person:', url_path='strategies_my')
        strategy_pages['策略分析'] = [my_strategies_page]

        account_settings_page = st.Page(settings_run, title='设置', icon=':material/settings:', url_path='accounts_settings')
        logout_page = st.Page(logout, title='退出', icon=':material/logout:')
        strategy_pages['账户管理'] = [account_settings_page, logout_page]

        pg = st.navigation(strategy_pages)

    pg.run()
