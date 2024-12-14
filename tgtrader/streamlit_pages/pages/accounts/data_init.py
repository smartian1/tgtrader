# encoding: utf-8

import streamlit as st
from streamlit_pages.dao.t_user import User
from streamlit_pages.service.data_init_service import init_user_data

def get_user_count():
    try:
        return User.select().count()
    except:
        return 0

# 创建表格数据
data = {
    "数据项": ["用户信息"],
    "数据量": [get_user_count()],
}

# 创建表格
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.write("数据项")
    for item in data["数据项"]:
        st.write(item)

with col2:
    st.write("数据量") 
    for count in data["数据量"]:
        st.write(count)

with col3:
    st.write("重置")
    if st.button("重置", key="reset_user"):
        init_user_data()
        st.experimental_rerun()
