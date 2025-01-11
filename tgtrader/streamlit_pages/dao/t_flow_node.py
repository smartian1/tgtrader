# encoding: utf-8
from datetime import datetime
from tgtrader.streamlit_pages.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey


class FlowNodeCfg(BaseModel):
    # 主键自增id
    id = AutoField()
    # 节点id
    node_id = TextField()
    # 节点类型
    node_type = TextField()
    # 节点配置JSON
    node_cfg = TextField()
    # 版本号
    version = IntegerField(default=1)
    # 是否草稿
    is_draft = IntegerField(default=1)
    # 描述信息
    desc = TextField(null=True)
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_flow_node_cfg'
        primary_key = CompositeKey('node_id', 'version')

    def save(self, *args, **kwargs):
        # 更新时间戳
        self.update_time = int(datetime.now().timestamp())
        return super(FlowNodeCfg, self).save(*args, **kwargs)

    @classmethod
    def init_table(cls):
        # 初始化表
        with db:
            if FlowNodeCfg.table_exists():
                FlowNodeCfg.delete().execute()
            else:
                db.create_tables([FlowNodeCfg])
