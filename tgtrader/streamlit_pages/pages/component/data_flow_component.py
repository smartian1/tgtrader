# encoding: utf-8
import pandas as pd
from tgtrader.common import DataSource
from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
import streamlit as st
from streamlit_ace import st_ace
from .data_meta import build_db_meta_info
from loguru import logger
from tgtrader.data_provider.dao.models.t_user_table_meta import UserTableMeta
from tgtrader.utils.db_wrapper import DBWrapper, DBType
from tgtrader.utils.db_path_utils import get_user_data_db_path

def get_user_name():
    return st.session_state.user_info['username']

def data_source_db_config(node_id: str, src_page: str, node_cfg: dict):
    col1, col2 = st.columns(2)
    with col1:
        options = ["Akshare"]
        default_value = node_cfg.get(
            'data_source', 'Akshare') if node_cfg else 'Akshare'
        default_index = options.index(default_value)
        data_source = st.selectbox("数据源", options,
                                   key=f"data_source_config_{node_id}_{src_page}",
                                   index=default_index)

    placeholder = """
输入：该节点必须为起始节点，不能有其他输入

示例：
select * from t_kdata where date>='2024-01-01'
    """

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300,
                       auto_update=False,
                       placeholder=placeholder,
                       show_gutter=True,
                       key=f"{src_page}_sql_query_{node_id}",
                       value=node_cfg.get('content', '') if node_cfg else ''
                       )

    build_db_meta_info(src_page=f"{src_page}_data_source_config_{node_id}")

    return {
        'type': 'data_source_db',
        'data_source': data_source,
        'content': sql_query
    }


def python_code_config(node_id: str, src_page: str, node_cfg: dict):
    placeholder = """
要定义一个函数，函数名必须为calc，函数参数为前方节点连到该节点的边的名字

输出：
任意类型

示例：
def calc(df):
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    return df
"""

    python_code = st_ace(language='python', theme='dracula',
                         height=300, auto_update=False,
                         placeholder=placeholder,
                         show_gutter=True,
                         key=f"{src_page}_python_code_config_{node_id}",
                         value=node_cfg.get('content', '') if node_cfg else ''
                         )

    return {
        'type': 'processor_python_code',
        'content': python_code
    }


def sql_config(node_id: str, src_page: str, node_cfg: dict):
    placeholder = """
支持的输入：
1. SQL语句
2. Python代码

示例：
select * from df where code='000001'
    """

    sql_query = st_ace(language='sql', theme='dracula',
                       height=300, auto_update=False,
                       placeholder=placeholder,
                       show_gutter=True,
                       key=f"{src_page}_sql_config_{node_id}",
                       value=node_cfg.get('content', '') if node_cfg else ''
                       )

    return {
        'type': 'processor_sql',
        'content': sql_query
    }


# 添加字段名映射
FIELD_NAME_MAPPING = {
    'field_name': '字段名',
    'field_type': '类型',
    'description': '描述', 
    'is_primary_key': '是否主键',
    'input_field_mapping': '映射前节点输入字段'
}

def cn_to_en_field_names(df: pd.DataFrame) -> pd.DataFrame:
    """将DataFrame的中文字段名转换为英文字段名
    
    Args:
        df: 包含中文字段名的DataFrame
        
    Returns:
        包含英文字段名的DataFrame
    """
    reverse_mapping = {v: k for k, v in FIELD_NAME_MAPPING.items()}
    return df.rename(columns=reverse_mapping)

def en_to_cn_field_names(df: pd.DataFrame) -> pd.DataFrame:
    """将DataFrame的英文字段名转换为中文字段名
    
    Args:
        df: 包含英文字段名的DataFrame
        
    Returns:
        包含中文字段名的DataFrame
    """
    return df.rename(columns=FIELD_NAME_MAPPING)

def get_empty_field_config():
    """获取空字段配置"""
    return pd.DataFrame({
        "字段名": pd.Series([], dtype='str'),
        "类型": pd.Series([], dtype='str'),
        "描述": pd.Series([], dtype='str'),
        "是否主键": pd.Series([], dtype='bool'),
        "映射前节点输入字段": pd.Series([], dtype='str')
    })

def create_field_config_editor(node_id: str, src_page: str, is_create_table: bool, field_config: pd.DataFrame):
    """创建字段配置编辑器"""
    if field_config is None or field_config.empty:
        field_config = get_empty_field_config()

    if is_create_table:
        field_config_df = field_config
        disabled_primary_key = False
    else:
        field_config_df = field_config
        disabled_primary_key = True

    return st.data_editor(
        field_config_df,
        key=f"{src_page}_storage_config_field_config_{'new' if is_create_table else 'existing'}_{node_id}",
        num_rows="dynamic",
        column_config={
            "字段名": st.column_config.TextColumn("字段名", required=True),
            "类型": st.column_config.SelectboxColumn(
                "类型",
                options=["string", "float", "int"],
                required=True
            ),
            "描述": st.column_config.TextColumn("描述", required=True),
            "是否主键": st.column_config.CheckboxColumn(
                "是否主键",
                disabled=disabled_primary_key,
                help="已有表的主键不可修改" if disabled_primary_key else None
            )
        }
    )


def validate_table_config(table_name: str, field_config_df: pd.DataFrame) -> tuple[bool, str]:
    """验证表配置的合法性"""
    if not table_name:
        return False, "表名不能为空"

    if field_config_df.empty:
        return False, "字段配置不能为空"

    # 检查必填字段
    required_fields = ["字段名", "类型", "描述"]
    for field in required_fields:
        if field_config_df[field].isnull().any():
            return False, f"{field}不能为空"

    # 检查主键
    if not field_config_df["是否主键"].any():
        return False, "至少需要一个主键字段"

    # 检查字段名唯一性
    if field_config_df["字段名"].duplicated().any():
        return False, "字段名不能重复"
    
    # 检查主键字段是否有映射字段
    primary_key_rows = field_config_df[field_config_df["是否主键"] == True]
    for _, row in primary_key_rows.iterrows():
        if not pd.notna(row.get('映射前节点输入字段', None)):
            return False, "主键字段必须有映射字段"

    return True, ""


def sink_db_config(node_id: str, src_page: str, node_cfg: dict):
    """数据库存储节点配置
    
    Args:
        node_id: 节点ID
        src_page: 源页面
        node_cfg: 节点配置
        
    Returns:
        节点配置字典或None（配置无效时）
    """

    try:
        db_path = get_user_data_db_path(get_user_name())
        db_name = "flow_sinkdb"
        db_wrapper = DBWrapper(db_path=db_path, db_type=DBType.DUCKDB)

        node_cfg = node_cfg.get('content', {})
        # 初始化配置
        if node_cfg:
            is_create_table = node_cfg.get('is_create_table', False)
            table_name = node_cfg.get('table_name', '')

            # 检查表是否已经存在
            if db_wrapper.is_table_exists(table_name):
                is_create_table = False
        else:
            is_create_table = True
            table_name = ''
            node_cfg = {}

        # 表创建选项
        is_create_table = st.checkbox(
            "是否新建表(保存时就会创建新表)",
            key=f"{src_page}_storage_config_create_table",
            value=is_create_table
        )

        # 表名输入
        col1, col2 = st.columns([1, 5])
        user = get_user_name()
        db_name = 'flow_sinkdb'
        with col1:
            if is_create_table:
                table_name = st.text_input(
                    "表名",
                    placeholder="请输入新建表名",
                    key=f"{src_page}_storage_config_table_name_{node_id}",
                    value=table_name
                )
            else:
                table_names = [''] + UserTableMeta.get_all_table_names(user=user, db_name=db_name)
                
                idx = table_names.index(table_name) if table_name in table_names else 0
                table_name = st.selectbox(
                    "表名",
                    options=table_names,
                    key=f"{src_page}_storage_config_table_name_{node_id}",
                    index=idx
                )
                
            if table_name:
                # 实际的列信息
                real_table_columns = []
                if db_wrapper.is_table_exists(table_name):
                    real_table_columns = db_wrapper.get_columns(table_name)

                real_table_columns_dict = {
                    column.name: {
                        'field_name': column.name,
                        'field_type': column.data_type,
                        'is_primary_key': column.primary_key,
                        'description': '',
                        'input_field_mapping': ''
                    }
                    for column in real_table_columns if column.name not in ['create_time', 'update_time']
                }

                # 读取保存的元信息
                columns_meta_info = UserTableMeta.get_table_columns_info(user=user, db_name=db_name, table_name=table_name)
                columns_meta_info_dict = {
                    column['field_name']: {
                        'field_name': column['field_name'],
                        'field_type': column['field_type'],
                        'is_primary_key': column['is_primary_key'],
                        'description': column['description'],
                        'input_field_mapping': ''
                    }
                    for column in columns_meta_info
                }

                # 传入的配置信息
                field_config = node_cfg.get('field_config', [])
                field_config_dict = {
                    info['field_name']: info
                    for info in field_config
                }
                
                if not real_table_columns and not columns_meta_info:
                    # 情况1：real_table_columns和columns_meta_info都不存在, 使用传入的配置
                    pass
                elif real_table_columns and not columns_meta_info:
                    # 情况2：real_table_columns存在，columns_meta_info不存在，补充新增字段
                    new_columns = set(real_table_columns_dict.keys()) - set(field_config_dict.keys())
                    for column in new_columns:
                        field_config.append(real_table_columns_dict[column])
                elif not real_table_columns and columns_meta_info:
                    # 情况3：real_table_columns不存在，columns_meta_info存在, 使用传入的配置
                    pass
                elif real_table_columns and columns_meta_info:
                    # 情况4：real_table_columns和columns_meta_info都存在，合并三部分信息
                    new_columns = set(real_table_columns_dict.keys()) - set(field_config_dict.keys())
                    # 新增的字段，使用meta_info里的信息进行补充
                    for column in new_columns:
                        if column in columns_meta_info_dict:
                            field_config.append(columns_meta_info_dict[column])
                        else:
                            field_config.append(real_table_columns_dict[column])

                # 将保存的英文字段名转换为中文显示
                field_config = pd.DataFrame(field_config)
                field_config = en_to_cn_field_names(field_config)
            else:
                field_config = pd.DataFrame()

        # 字段配置
        data_editor_df = create_field_config_editor(
            node_id, src_page, is_create_table, field_config)

        # 保存按钮
        btn_save = st.button("保存配置", key=f"{src_page}_storage_config_save")

        if btn_save:
            # logger.debug(f"is_create_table: {is_create_table}, table_name: {table_name}, data_editor_df: {data_editor_df}")

            if is_create_table and table_name:
                if db_wrapper.is_table_exists(table_name):
                    st.error(f"表名已存在，请更换表名")
                    ret = None
                else:
                    ret = save_table_config(table_name, data_editor_df, is_create_table)
            else:
                ret = save_table_config(table_name, data_editor_df, is_create_table)

        else:
            ret = None

        # 构建元数据信息
        build_db_meta_info(src_page=f"{src_page}_storage_config_{node_id}")
        return ret
    except Exception as e:
        logger.exception(e)
        st.error(f"配置保存失败: {str(e)}")
        return None

def save_table_config(table_name: str, data_editor_df: pd.DataFrame, is_create_table: bool):
    # 验证配置
    is_valid, error_msg = validate_table_config(
        table_name, data_editor_df)
    if not is_valid:
        st.error(error_msg)
    else:
        # 保存时转换为英文字段名
        data_editor_df_en = cn_to_en_field_names(data_editor_df)
        ret = {
            'type': 'sink_db',
            'content': {
                'is_create_table': is_create_table,
                'table_name': table_name,
                'field_config': data_editor_df_en.to_dict(orient='records')
            }
        }
        st.success(f"保存成功，表名：{table_name}")
    
        return ret