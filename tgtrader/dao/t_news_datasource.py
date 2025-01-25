# encoding: utf-8
from datetime import datetime
from tgtrader.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey


class TNewsDataSource(BaseModel):
    # 主键自增id
    id = AutoField()
    # 用户名
    username = TextField()
    # 表名
    table_name = TextField()
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_news_datasource'
        indexes = (
            (('username', 'table_name'), True),
        )

    @classmethod
    def init_table(cls):
        with db:
            if not TNewsDataSource.table_exists():
                db.create_tables([TNewsDataSource])

TNewsDataSource.init_table()
