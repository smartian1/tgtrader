import streamlit as st
import pandas as pd

def validate_weights(weights, cash_weight=0.0):
    """验证权重之和是否为100%"""
    return abs(sum(weights) + cash_weight - 100.0) < 0.01

def weight_editor(symbol_multiselect, show_weights=True):
    """
    创建并显示权重编辑器组件
    """
    if not symbol_multiselect:
        return None, False
        
    # 使用session_state保存权重状态
    if 'weights_df' not in st.session_state:
        # 创建DataFrame时确保数据类型，并设置默认等权重
        cash_weight = st.session_state.get('cash_weight', 0.0)
        equal_weight = (100.0 - cash_weight) / len(symbol_multiselect) if symbol_multiselect else 0.0
        st.session_state.weights_df = pd.DataFrame([
            {
                '代码': str(symbol.split('|')[0]), 
                '名称': str(symbol.split('|')[1]),
                '权重(%)': equal_weight
            } for symbol in symbol_multiselect
        ])
    
    # 检查是否需要更新DataFrame（当选择的标的发生变化时）
    current_symbols = {symbol.split('|')[0] for symbol in symbol_multiselect}
    saved_symbols = set(st.session_state.weights_df['代码'])
    
    if current_symbols != saved_symbols:
        # 标的列表发生变化，需要更新DataFrame
        new_df = pd.DataFrame([
            {
                '代码': symbol.split('|')[0],
                '名称': symbol.split('|')[1],
                '权重(%)': 0.0
            } for symbol in symbol_multiselect
        ])
        # 保留已有标的的权重
        for idx, row in new_df.iterrows():
            if row['代码'] in saved_symbols:
                new_df.loc[idx, '权重(%)'] = st.session_state.weights_df[
                    st.session_state.weights_df['代码'] == row['代码']
                ]['权重(%)'].values[0]
        st.session_state.weights_df = new_df
    
    if show_weights:
        # 使用滑动条选择现金比例
        if 'cash_weight' not in st.session_state:
            st.session_state.cash_weight = 0.0
        
        cash_weight = st.slider('现金比例', 0.0, 100.0, st.session_state.cash_weight, 0.1, format='%.1f%%',
                               key='cash_weight')
        
        # 在表格上方添加等权按钮和说明
        st.markdown("""
        **权重设置说明：**
        1. 点击"等权"按钮：系统会自动将扣除现金后的剩余权重平均分配给所有标的
        2. 手动调整：您也可以直接在表格中修改各个标的的权重百分比
        """)
        
        col1, col2 = st.columns([4, 1])
        with col2:
            equal_weight_button = st.button('等权')
        
        # 如果点击等权按钮，计算除现金外的等权重
        if equal_weight_button:
            remaining_weight = 100.0 - cash_weight
            equal_weight = remaining_weight / len(st.session_state.weights_df) if len(st.session_state.weights_df) > 0 else 0.0
            st.session_state.weights_df['权重(%)'] = equal_weight
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
            display_df = st.session_state.weights_df
        else:
            column_config = {}
            display_df = st.session_state.weights_df[['代码', '名称']]
            
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            hide_index=True,
            key='weights_editor'
        )
    
    # 更新session state中的DataFrame
    if show_weights:
        st.session_state.weights_df = edited_df
        
        # 验证权重之和（包含现金）
        total_weight = edited_df['权重(%)'].sum()
        is_valid = validate_weights(edited_df['权重(%)'], cash_weight)
        if not is_valid:
            st.warning(f'当前权重之和为 {total_weight + cash_weight:.1f}%，请调整为100%')
    else:
        is_valid = True
    
    return edited_df, is_valid