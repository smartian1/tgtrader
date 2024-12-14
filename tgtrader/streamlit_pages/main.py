# encoding: utf-8

import streamlit as st


def logout():
    pass

login_page = st.Page('login.py', title='登录', icon=':material/login:')

target_weights_page = st.Page('pages/strategies/target_weight_strats.py', title='目标权重策略', icon=':material/target:')
risk_parity_page = st.Page('pages/strategies/risk_parity_strats.py', title='风险平价策略', icon=':material/balance:')
strategy_pages = {
    '策略列表': [target_weights_page, risk_parity_page],
}

strategy_compare_page = st.Page('pages/strategies/strategy_compare.py', title='策略对比', icon=':material/compare_arrows:')
strategy_composite_page = st.Page('pages/strategies/strategy_composite.py', title='策略组合', icon=':material/apps:')
my_strategies_page = st.Page('pages/strategies/my_strategies.py', title='我的策略', icon=':material/person:')
strategy_pages['策略分析'] = [strategy_compare_page, strategy_composite_page, my_strategies_page]

account_info_page = st.Page('pages/accounts/account_info.py', title='账户信息', icon=':material/person:')
account_settings_page = st.Page('pages/accounts/settings.py', title='账户设置', icon=':material/settings:')
data_init_page = st.Page('pages/accounts/data_init.py', title='数据初始化', icon=':material/restart_alt:')
logout_page = st.Page(logout, title='退出登录', icon=':material/logout:')
strategy_pages['账户管理'] = [account_info_page, account_settings_page, data_init_page, logout_page]

pg = st.navigation(strategy_pages)

pg.run()
