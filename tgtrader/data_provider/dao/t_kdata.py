# encoding: utf-8
from peewee import *
from tgtrader.data_provider.dao.common import BaseModel, main_db

class T_KData(BaseModel):
    # 股票代码
    code = CharField(max_length=64)
    # 日期
    date = CharField()
    # 开盘价
    open = FloatField()
    # 收盘价
    close = FloatField()
    # 最高价
    high = FloatField()
    # 最低价
    low = FloatField()
    # 成交量
    volume = FloatField()
    # 复权方式
    adjust_type = CharField(max_length=64)
    # 创建时间
    create_time = BigIntegerField()
    # 更新时间
    update_time = BigIntegerField()

    class Meta:
        primary_key = CompositeKey('code', 'date')
        table_name = 't_kdata'

    @classmethod
    def init_table(cls):
        # 初始化表
        with main_db:
            table_exists = T_KData.table_exists()
            if not table_exists:
                main_db.create_tables([T_KData])  # 如果表不存在，创建表
