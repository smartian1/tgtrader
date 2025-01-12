# encoding: utf-8
from datetime import datetime
from tgtrader.streamlit_pages.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey


class FlowNodeCfg(BaseModel):
    # 主键自增id
    id = AutoField()
    # flow_id
    flow_id = TextField()
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
    desc = TextField(null=True, default="")
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_flow_node'
        indexes = (
            # 创建 node_id 和 version 的联合唯一索引
            (('flow_id', 'node_id', 'version'), True),
        )

    def save(self, *args, **kwargs):
        # 更新时间戳
        self.update_time = int(datetime.now().timestamp())
        return super(FlowNodeCfg, self).save(*args, **kwargs)

    @classmethod
    def init_table(cls):
        with db:
            if not FlowNodeCfg.table_exists():
                db.create_tables([FlowNodeCfg])
