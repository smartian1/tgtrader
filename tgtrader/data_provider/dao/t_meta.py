# encoding: utf-8
from peewee import *
from tgtrader.data_provider.dao.common import BaseModel, main_db

class T_Meta(BaseModel):
    # 数据类型
    data_type = CharField()
    # 数据来源
    source = CharField()
    # 起始时间
    start_time = CharField()
    # 结束时间
    end_time = CharField()
    # 表名
    table_name = CharField()
    # 创建时间
    create_time = BigIntegerField()
    # 更新时间
    update_time = BigIntegerField()

    class Meta:
        primary_key = CompositeKey('data_type', 'source')
        table_name = 't_meta'

    @classmethod
    def init_table(cls):
        # 初始化表
        with main_db:
            table_exists = T_Meta.table_exists()
            if not table_exists:
                main_db.create_tables([T_Meta])  # 如果表不存在，创建表

