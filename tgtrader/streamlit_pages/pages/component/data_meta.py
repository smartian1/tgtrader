# encoding: utf-8
from tgtrader.common import DataSource
from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
from typing import Tuple, List
from tgtrader.utils.model_inspector import FieldInfo
import streamlit as st
import pandas as pd
from tgtrader.streamlit_pages.dao.t_user_table_meta import UserTableMeta
from loguru import logger


def __get_data_service(data_source: str):
    if DataSource(data_source.lower()) == DataSource.Akshare:
        return AkshareDataService
        
    return None


def __get_table_names(data_source):
    if data_source == '用户自定义数据':
        user = st.session_state.user_info['username']
        db_name = 'flow_sinkdb'
        return UserTableMeta.get_all_table_names(user=user, db_name=db_name)

    else:
        data_service = __get_data_service(data_source)
        return data_service.get_table_names()

def __get_db_model_info_by_table_name(data_source: str, table_name: str) -> Tuple[str, List[FieldInfo]]:
    if data_source == '用户自定义数据':
        user = st.session_state.user_info['username']
        db_name = 'flow_sinkdb'
        columns_info = UserTableMeta.get_table_columns_info(user=user, db_name=db_name, table_name=table_name)
        ret = [
            FieldInfo(name=info['field_name'], field_type=info['field_type'], comment=info['description'])
            for info in columns_info
        ]
        return table_name, ret

    elif DataSource(data_source.lower()) == DataSource.Akshare:
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
    st.markdown("### 表字段信息查询")
    col1, col2 = st.columns(2)
    with col1:
        data_source = st.selectbox("数据源", ["Akshare", "用户自定义数据"], key=f"data_meta_build_data_source_{src_page}")
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
