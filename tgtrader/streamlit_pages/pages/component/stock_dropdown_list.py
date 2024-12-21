# encoding: utf-8

from typing import List
import streamlit as st

from tgtrader.data import DataGetter
from tgtrader.common import SecurityType
from tgtrader.strategy_config import StrategyConfig

  
class StockDropdownSelectItem:
    def __init__(self, symbol_type:str, code:str, name:str):
        self.symbol_type = symbol_type
        self.code = code
        self.name = name
        
    def __eq__(self, other):
        # 通过 symbol_type 和 code 确定唯一性
        if not isinstance(other, StockDropdownSelectItem):
            return False
        return self.symbol_type == other.symbol_type and self.code == other.code
        
    def __hash__(self):
        # 通过 symbol_type 和 code 确定唯一性
        return hash((self.symbol_type, self.code))
    
def build_stock_dropdown_list(src_page:str, data_getter: DataGetter, strategy_config: StrategyConfig = None) -> list[StockDropdownSelectItem]:
    # 从策略配置中获取默认的证券类型
    default_security_type = None
    if strategy_config is not None and strategy_config.symbols:
        # 获取第一个有标的的证券类型
        for security_type in strategy_config.symbols.keys():
            if security_type == SecurityType.ETF:
                default_security_type = "ETF"
            else:
                default_security_type = "股票"
            break

    # 选择证券类型
    security_type_selectbox = st.selectbox(
        "证券类型", 
        options=["ETF", "股票"],
        index=0 if default_security_type is None else ["ETF", "股票"].index(default_security_type),
        key=f"build_stock_dropdown_list_security_type_selectbox_{src_page}"
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

    # 如果有策略配置，获取已选择的标的
    default_values = []
    if strategy_config is not None and strategy_config.symbols:
        for security_type, symbols in strategy_config.symbols.items():
            if (security_type == SecurityType.ETF and security_type_selectbox == "ETF") or \
               (security_type == SecurityType.Stocks and security_type_selectbox == "股票"):
                df = get_symbols(security_type)
                for symbol in symbols:
                    row = df[df['code'] == symbol].iloc[0]
                    default_values.append(f"{row['code']}|{row['name']}|{security_type.value}")
    
    # 保持已选择的选项
    symbol_multiselect = st.multiselect(
        f"选择{security_type_selectbox}",
        options=display_options,
        default=default_values,
        format_func=lambda x: '|'.join(x.split('|')[:-1]),
        key=f"build_stock_dropdown_list_symbol_multiselect_{src_page}"
    )

    # 将symbol_multiselect转换为BuildStockDropdownSelectItem列表
    symbol_multiselect = [StockDropdownSelectItem(symbol.split('|')[2], symbol.split('|')[0], symbol.split('|')[1]) for symbol in symbol_multiselect]

    return symbol_multiselect
