# encoding: utf-8

import streamlit as st

from tgtrader.data import DataGetter
from tgtrader.common import SecurityType

# 获取证券列表数据，使用st.cache_data缓存结果
  
    
def build_stock_dropdown_list(data_getter: DataGetter, default_symbols: list[str] = None):
    # 选择证券类型
    security_type_selectbox = st.selectbox(
        "证券类型", 
        options=["ETF", "股票"],
        key="build_stock_dropdown_list_security_type_selectbox"
    )

    @st.cache_data
    def get_symbols(security_type):
        return data_getter.get_all_symbols(security_type)
  
    # 根据类型获取证券列表
    security_type_enum = SecurityType.ETF if security_type_selectbox == "ETF" else SecurityType.Stocks
    
    df = get_symbols(security_type_enum)
    
    # 格式化显示选项
    options = [f"{row['code']}|{row['name']}|{security_type_selectbox}" 
              for _, row in df.iterrows()]
    
    # 找出默认选中项
    default = []
    if default_symbols:
        default = [opt for opt in options if opt.split('|')[0] in default_symbols]
    
    # 返回下拉多选框控件
    symbol_multiselect = st.multiselect(
        f"选择{security_type_selectbox}",
        options=options,
        default=default,
        format_func=lambda x: '|'.join(x.split('|')[:-1]),
        key="build_stock_dropdown_list_symbol_multiselect"
    )
    return security_type_selectbox, symbol_multiselect
