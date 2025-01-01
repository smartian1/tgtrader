# encoding: utf-8
from peewee import *

class T_Meta_Model(Model):
    # 元数据名称
    meta_name = CharField()
    # 数据类型
    security_type = CharField()
    # 时间周期
    period = CharField()
    # 数据来源
    source = CharField()
    # 起始时间
    start_time = CharField()
    # 结束时间
    end_time = CharField()
    # 表名
    table_name = CharField()
    # 总数据量
    total_count = IntegerField()
    # 创建时间
    create_time = BigIntegerField()
    # 更新时间
    update_time = BigIntegerField()

    class Meta:
        primary_key = CompositeKey('meta_name')
        table_name = 't_meta'
