# encoding: utf-8

from typing import List
import streamlit as st

from tgtrader.data import DataGetter
from tgtrader.common import SecurityType

  
class StockDropdownSelectItem:
    def __init__(self, symbol_type:str, code:str, name:str, weight:float):
        self.symbol_type = symbol_type
        self.code = code
        self.name = name
        self.weight = weight
        
    def __eq__(self, other):
        # 通过 symbol_type 和 code 确定唯一性
        if not isinstance(other, StockDropdownSelectItem):
            return False
        return self.symbol_type == other.symbol_type and self.code == other.code
        
    def __hash__(self):
        # 通过 symbol_type 和 code 确定唯一性
        return hash((self.symbol_type, self.code))
    
def build_stock_dropdown_list(src_page:str, data_getter: DataGetter) -> list[StockDropdownSelectItem]:
    # 选择证券类型
    security_type_selectbox = st.selectbox(
        "证券类型", 
        options=["ETF", "股票"],
        key="build_stock_dropdown_list_security_type_selectbox"
    )

    @st.cache_data
    def get_symbols(security_type):
        return data_getter.get_all_symbols(security_type)
  
    # 根据当前选择的类型过滤显示选项
    if security_type_selectbox == "ETF":
        etf_df = get_symbols(SecurityType.ETF)
        etf_options = [f"{row['code']}|{row['name']}|{SecurityType.ETF.value}" for _, row in etf_df.iterrows()]
        display_options = etf_options
    else:
        stock_df = get_symbols(SecurityType.Stocks)
        stock_options = [f"{row['code']}|{row['name']}|{SecurityType.Stocks.value}" for _, row in stock_df.iterrows()]
        display_options = stock_options
    
    # 保持已选择的选项
    symbol_multiselect = st.multiselect(
        f"选择{security_type_selectbox}",
        options=display_options,
        format_func=lambda x: '|'.join(x.split('|')[:-1]),
        key=f"build_stock_dropdown_list_symbol_multiselect_{src_page}"
    )

    # 将symbol_multiselect转换为BuildStockDropdownSelectItem列表
    symbol_multiselect = [StockDropdownSelectItem(symbol.split('|')[2], symbol.split('|')[0], symbol.split('|')[1], 0.0) for symbol in symbol_multiselect]

    return symbol_multiselect
