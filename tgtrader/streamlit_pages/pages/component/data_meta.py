# encoding: utf-8
from tgtrader.common import DataSource
from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
from typing import Tuple, List
from tgtrader.utils.model_inspector import FieldInfo
import streamlit as st
import pandas as pd


def __get_data_service(data_source: str):
    if DataSource(data_source.lower()) == DataSource.Akshare:
        return AkshareDataService
    return None


def __get_table_names(data_source):
    data_service = __get_data_service(data_source)
    return data_service.get_table_names()

def __get_db_model_info_by_table_name(data_source: str, table_name: str) -> Tuple[str, List[FieldInfo]]:
    if DataSource(data_source.lower()) == DataSource.Akshare:
        data_service = AkshareDataService()
    else:
        raise NotImplementedError(f'数据源 {data_source} 不支持')
    
    meta_info = data_service.get_metadata_by_table_name(table_name)
    if meta_info:
        table_name, fields = data_service.get_db_model_info_by_table_name(table_name)
        return table_name, fields
    else:
        return None, None
    
def build_db_meta_info(src_page: str):
    st.markdown("### 数据元数据")
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.selectbox("数据源", ["Akshare"], key=f"data_meta_build_data_source_{src_page}")
    with col2:
        table_name = st.selectbox("表名", __get_table_names(data_source), key=f"data_meta_build_table_name_{src_page}")
    
    table_name, fields = __get_db_model_info_by_table_name(data_source, table_name)
    field_data = {
        '字段名': [field.name for field in fields],
        '类型': [str(field.field_type) for field in fields],
        '说明': [field.comment for field in fields]
    }
    df = pd.DataFrame(field_data)
    st.table(df)
