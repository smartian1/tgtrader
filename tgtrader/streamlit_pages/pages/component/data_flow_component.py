# encoding: utf-8
import pandas as pd
from tgtrader.common import DataSource
from tgtrader.data_provider.service.akshare_data_service import AkshareDataService
import streamlit as st
from streamlit_ace import st_ace
from .data_meta import build_db_meta_info
from loguru import logger


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
连接到该节点的前方边的名字，就是传入到该节点的入参名，可以直接对其进行操作

支持的输入：
1. SQL语句
2. Python代码

输出：
必须是DataFrame

示例：
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()
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

    return True, ""


def sink_db_config(node_id: str, src_page: str, node_cfg: dict):
    """数据库存储节点配置"""
    try:
        node_cfg = node_cfg.get('content', {})
        # 初始化配置
        if node_cfg:
            is_create_table = node_cfg.get('is_create_table', False)
            table_name = node_cfg.get('table_name', '')
            field_config = pd.DataFrame(node_cfg['field_config'])
        else:
            is_create_table = True
            table_name = ''
            field_config = None

        # 表创建选项
        is_create_table = st.checkbox(
            "是否新建表(保存时就会创建新表)",
            key=f"{src_page}_storage_config_create_table",
            value=is_create_table
        )

        # 表名输入
        col1, col2 = st.columns([1, 5])
        with col1:
            if is_create_table:
                table_name = st.text_input(
                    "表名",
                    placeholder="请输入新建表名",
                    key=f"{src_page}_storage_config_table_name_{node_id}",
                    value=table_name
                )
            else:
                table_name = st.selectbox(
                    "表名",
                    options=['factor_table'],
                    key=f"{src_page}_storage_config_table_name_{node_id}"
                )

        # 字段配置
        data_editor_df = create_field_config_editor(
            node_id, src_page, is_create_table, field_config)

        # 保存按钮
        btn_save = st.button("保存配置", key=f"{src_page}_storage_config_save")

        if btn_save:
            # 验证配置
            is_valid, error_msg = validate_table_config(
                table_name, data_editor_df)
            if not is_valid:
                st.error(error_msg)
                ret = None
            else:
                ret = {
                    'type': 'sink_db',
                    'content': {
                        'is_create_table': is_create_table,
                        'table_name': table_name,
                        'field_config': data_editor_df.to_dict(orient='records')
                    }
                }
        else:
            ret = None

        # 构建元数据信息
        build_db_meta_info(src_page=f"{src_page}_storage_config_{node_id}")

        return ret
    except Exception as e:
        logger.exception(e)
        st.error(f"配置保存失败: {str(e)}")
        return None
