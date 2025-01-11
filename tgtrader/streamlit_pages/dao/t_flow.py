# encoding: utf-8
from datetime import datetime
from tgtrader.streamlit_pages.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey


class FlowCfg(BaseModel):
    # 主键自增id
    id = AutoField()
    # 流程id
    flow_id = TextField()
    # 流程名称
    flow_name = TextField()
    # 节点列表
    node_list = TextField()
    # 边列表
    edge_list = TextField()
    # 是否草稿
    is_draft = IntegerField(default=1)
    # 描述信息
    desc = TextField(null=True)
    # 版本号
    version = IntegerField(default=1)
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_flow'
        primary_key = CompositeKey('flow_id', 'version')

    def save(self, *args, **kwargs):
        # 更新时间戳
        self.update_time = int(datetime.now().timestamp())
        return super(FlowCfg, self).save(*args, **kwargs)

    @classmethod
    def init_table(cls):
        # 初始化表
        with db:
            if FlowCfg.table_exists():
                FlowCfg.delete().execute()
            else:
                db.create_tables([FlowCfg])
