# encoding: utf-8
from peewee import *
from tgtrader.data_provider.dao.common import BaseModel

class T_KData(BaseModel):
    # 主键自增id
    id = AutoField()
    # 股票代码
    code = CharField(max_length=64)
    # 日期
    date = CharField(max_length=64)
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
    adjust_type = CharField(max_length=64, constraints=[Check('adjust_type IN ("qfq", "hfq", "nfq")')])

    class Meta:
        table_name = 't_kdata'

    def init_table(self):
        with T_KData.Meta.database as db:
            if T_KData.table_exists():
                T_KData.delete().execute()  # 如果表存在，删除所有记录
            else:
                db.create_tables([T_KData])  # 如果表不存在，创建表
