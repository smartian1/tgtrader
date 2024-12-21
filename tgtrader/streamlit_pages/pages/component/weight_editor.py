import streamlit as st
import pandas as pd
from tgtrader.strategy_config import StrategyConfig
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem

def validate_weights(weights, cash_weight=0.0):
    """验证权重之和是否为100%"""
    return abs(sum(weights) + cash_weight - 100.0) < 0.01

def weight_editor(src_page:str, 
                  symbol_multiselect: list[StockDropdownSelectItem], 
                  show_weights=True, 
                  strategy_config: StrategyConfig = None):
    """创建并显示权重编辑器组件"""
    if not symbol_multiselect:
        return None, False
        
    # 创建新的DataFrame
    new_df = pd.DataFrame([
        {
            '类型': symbol.symbol_type,
            '代码': symbol.code,
            '名称': symbol.name,
            '权重(%)': 0.0
        } for symbol in symbol_multiselect
    ])

    # 如果有策略配置，使用配置中的权重
    if strategy_config is not None and strategy_config.target_weights_dict:
        print(strategy_config.target_weights_dict)
        for index, row in new_df.iterrows():
            symbol_key = f"{row['代码']}"
            if symbol_key in strategy_config.target_weights_dict:
                new_df.at[index, '权重(%)'] = strategy_config.target_weights_dict[symbol_key] * 100
    # 否则使用之前保存的权重
    elif f'{src_page}_symbol_multiselect' in st.session_state:
        old_df = st.session_state[f'{src_page}_symbol_multiselect']
        # 遍历，更新权重
        for index, row in new_df.iterrows():
            old_row = old_df[(old_df['类型'] == row['类型']) & (old_df['代码'] == row['代码'])]
            if not old_row.empty:
                new_df.at[index, '权重(%)'] = old_row['权重(%)'].values[0]
    
    if show_weights:
        cash_weight = st.slider('现金比例', 
                              min_value=0, 
                              max_value=100, 
                              step=1, 
                              format='%d%%',
                              key=f'cash_weight_{src_page}')
        
        # 在表格上方添加等权按钮和说明
        st.markdown("""
        **权重设置说明：**
        1. 点击"等权"按钮：系统会自动将扣除现金后的剩余权重平均分配给所有标的
        2. 手动调整：您也可以直接在表格中修改各个标的的权重百分比
        """)
        
        col1, col2 = st.columns([4, 1])
        with col2:
            equal_weight_button = st.button('等权重')
        
        # 如果点击等权按钮，计算除现金外的等权重
        if equal_weight_button:
            remaining_weight = 100.0 - cash_weight
            equal_weight = remaining_weight / len(new_df) if len(new_df) > 0 else 0.0
            new_df['权重(%)'] = equal_weight
    else:
        cash_weight = 0.0
        col1, col2 = st.columns([0.95, 0.05])

    # 使用st.data_editor让用户编辑权重
    with col1:
        if show_weights:
            column_config = {
                '权重(%)': st.column_config.NumberColumn(
                    min_value=0,
                    max_value=100,
                    step=0.1,
                    format="%.1f %%"
                )
            }
            display_df = new_df
        else:
            column_config = {}
            display_df = new_df[['类型', '代码', '名称']]
            
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            hide_index=True,
            key='weights_editor',
        )
    
    # 更新session state中的DataFrame
    if show_weights:
        # 验证权重之和（包含现金）
        total_weight = edited_df['权重(%)'].sum()
        is_valid = validate_weights(edited_df['权重(%)'], cash_weight)
        if not is_valid:
            st.warning(f'当前权重之和为 {total_weight + cash_weight:.1f}%，请调整为100%')
        
        st.session_state[f'{src_page}_symbol_multiselect'] = edited_df
    else:
        is_valid = True
    
    return edited_df, cash_weight, is_valid