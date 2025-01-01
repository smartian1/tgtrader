from peewee import *
from tgtrader.data_provider.dao.akshare.common import main_db

class T_KData_Model(Model):
    # 股票代码
    code = CharField()
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
    adjust_type = CharField()
    # 来源
    source = CharField()
    # 创建时间
    create_time = BigIntegerField()
    # 更新时间
    update_time = BigIntegerField()

    class Meta:
        primary_key = CompositeKey('code', 'date', 'source')
        table_name = 't_kdata'
