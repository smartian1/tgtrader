from datetime import datetime
import os
import time
from typing import List
from loguru import logger
from peewee import *
from tgtrader.utils.db_path_utils import get_common_data_database


main_db = get_common_data_database()

class SqlHistoryModel(Model):
    """
    SQL历史记录表模型.
    
    Attributes:
        user (ForeignKeyField): 关联的用户
        sql_content (TextField): SQL内容
        data_source (CharField): 数据源
        create_time (DateTimeField): 创建时间
        update_time (DateTimeField): 更新时间
    """
    
    user = TextField(verbose_name='用户')
    sql_content = TextField(verbose_name='SQL内容')
    data_source = CharField(max_length=50, verbose_name='数据源')
    create_time = BigIntegerField(verbose_name='创建时间')
    update_time = BigIntegerField(verbose_name='更新时间')

    class Meta:
        table_name = 't_sql_history' 
        database = main_db
        primary_key = CompositeKey('user', 'sql_content')
    
    @classmethod
    def init_table(cls):
        # 初始化表
        with main_db:
            table_exists = cls.table_exists()
            if not table_exists:
                main_db.create_tables([cls])  # 如果表不存在，创建表

    @classmethod
    def save_sql_history(cls, user: str, sql: str, data_source: str) -> None:
        ts = int(time.time() * 1000 )
        with main_db:
            cls.create(user=user, sql_content=sql, data_source=data_source, create_time=ts, update_time=ts)

    @classmethod
    def get_sql_history(cls, user: str) -> List['SqlHistoryModel']:
        return cls.select().where(cls.user == user).order_by(cls.create_time.desc())

SqlHistoryModel.init_table()
