# encoding: utf-8

import streamlit as st
from tgtrader.streamlit_pages.pages.welcome import run as welcome_run
from tgtrader.streamlit_pages.login import run as login_run
from tgtrader.streamlit_pages.pages.strategies.target_weight_strats import run as target_weight_strats_run
from tgtrader.streamlit_pages.pages.strategies.risk_parity_strats import run as risk_parity_strats_run
from tgtrader.streamlit_pages.pages.strategies.strategy_composite import run as strategy_composite_run
from tgtrader.streamlit_pages.pages.strategies.my_strategies import run as my_strategies_run
from tgtrader.streamlit_pages.pages.strategies.strategy_compare import run as strategy_compare_run
from tgtrader.streamlit_pages.pages.accounts.account_info import run as account_info_run
from tgtrader.streamlit_pages.pages.accounts.settings import run as settings_run

def logout():
    st.header("Log out")
    st.button("Log out")

def run():
    # Check if user is logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_page = st.Page(login_run, title='登录', icon=':material/login:')
        pg = st.navigation([login_page])
    else:
        strategy_pages = {}


        welcome_page = st.Page(welcome_run, title='欢迎', icon=':material/home:', default=True, url_path='welcome')
        strategy_pages['欢迎'] = [welcome_page]

        target_weights_page = st.Page(target_weight_strats_run, title='目标权重策略', icon=':material/target:', url_path='strategies_target_weights')
        risk_parity_page = st.Page(risk_parity_strats_run, title='风险平价策略', icon=':material/balance:', url_path='strategies_risk_parity')
        strategy_pages['策略列表'] = [target_weights_page, risk_parity_page]

        strategy_compare_page = st.Page(strategy_compare_run, title='策略对比', icon=':material/compare_arrows:', url_path='strategies_compare')
        strategy_composite_page = st.Page(strategy_composite_run, title='策略组合', icon=':material/apps:', url_path='strategies_composite')
        my_strategies_page = st.Page(my_strategies_run, title='我的策略', icon=':material/person:', url_path='strategies_my')
        strategy_pages['策略分析'] = [strategy_compare_page, strategy_composite_page, my_strategies_page]

        account_info_page = st.Page(account_info_run, title='账户信息', icon=':material/person:', url_path='accounts_info')
        account_settings_page = st.Page(settings_run, title='账户设置', icon=':material/settings:', url_path='accounts_settings')
        logout_page = st.Page(logout, title='退出登录', icon=':material/logout:')
        strategy_pages['账户管理'] = [account_info_page, account_settings_page, logout_page]

        pg = st.navigation(strategy_pages)

    pg.run()
