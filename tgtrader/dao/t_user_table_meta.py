from datetime import datetime
import os
import time
from typing import List
from loguru import logger
from peewee import *
import json
import copy
from tgtrader.dao.common import BaseModel, db

class UserTableMeta(BaseModel):
    """
    用户数据元信息.
    """
    
    user = TextField(verbose_name='用户')
    db_name = TextField(verbose_name='数据库名')
    table_name = TextField(verbose_name='表名')
    db_path = TextField(verbose_name='数据库路径')
    columns_info = TextField(verbose_name='列信息')
    version = IntegerField(verbose_name='版本')
    create_time = BigIntegerField(verbose_name='创建时间')
    update_time = BigIntegerField(verbose_name='更新时间')

    class Meta:
        table_name = 't_user_table_meta' 
        primary_key = CompositeKey('user', 'db_name', 'table_name', 'version')
    
    @classmethod
    def init_table(cls):
        # 初始化表
        with db:
            table_exists = cls.table_exists()
            if not table_exists:
                db.create_tables([cls])  # 如果表不存在，创建表

    @classmethod
    def get_all_db_names(cls, user: str):
        data = cls.select(cls.db_name).where(cls.user == user).distinct().execute()
        return [item.db_name for item in data]

    @classmethod
    def get_all_table_names(cls, user: str, db_name: str):
        data = cls.select(cls.table_name).where(cls.user == user, cls.db_name == db_name).distinct().execute()
        return [item.table_name for item in data]
    
    @classmethod
    def get_table_meta(cls, user: str, db_name: str, table_name: str) -> 'UserTableMeta':
        ret = cls.select().where(cls.user == user, cls.db_name == db_name, cls.table_name == table_name).order_by(cls.version.desc()).first()
        if ret:
            ret.columns_info = json.loads(ret.columns_info)
        
        return ret

    @classmethod
    def get_table_columns_info(cls, user: str, db_name: str, table_name: str) -> List[dict]:
        """
        样例：
        [
            {
                "field_name": "code",
                "field_type": "string",
                "description": "code",
                "is_primary_key": true
            }
        ]
        """
        table_info = cls.select().where(cls.user == user, cls.db_name == db_name, cls.table_name == table_name).order_by(cls.version.desc()).first()
        if table_info:
            return json.loads(table_info.columns_info)
        else:
            return []

    @classmethod
    def update_table_meta(cls, user: str, db_name: str, table_name: str, db_path: str, columns_info: List[dict]) -> None:
        """
        更新表的元数据信息，创建新版本记录.

        Args:
            user (str): 用户名
            db_name (str): 数据库名
            table_name (str): 表名
            columns_info (List[dict]): 列信息列表

        Returns:
            None
        """

        columns_info = copy.deepcopy(columns_info)

        for info in columns_info:
            if 'input_field_mapping' in info:
                del info['input_field_mapping']

        # 获取当前最大版本号和最新记录
        latest_record = (cls
            .select()
            .where(
                cls.user == user,
                cls.db_name == db_name,
                cls.table_name == table_name
            )
            .order_by(cls.version.desc())
            .first())
        
        current_max_version = latest_record.version if latest_record else 0
        
        # 创建新版本记录
        current_time = int(time.time())
        new_record = cls.create(
            user=user,
            db_name=db_name,
            table_name=table_name,
            db_path=db_path,
            columns_info=json.dumps(columns_info),
            version=current_max_version + 1,
            create_time=current_time,
            update_time=current_time
        )
        logger.info(f"Created new version {current_max_version + 1} for table {table_name}")

UserTableMeta.init_table()
