# encoding: utf-8
from datetime import datetime
from tgtrader.streamlit_pages.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey


class UserFlowCfg(BaseModel):
    # 主键自增id
    id = AutoField()
    # 用户id
    user_id = IntegerField()
    # 流程id
    flow_id = IntegerField()
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_user_flow'
        primary_key = CompositeKey('user_id', 'flow_id')

    def save(self, *args, **kwargs):
        # 更新时间戳
        self.update_time = int(datetime.now().timestamp())
        return super(UserFlowCfg, self).save(*args, **kwargs)

    @classmethod
    def init_table(cls):
        # 初始化表
        with db:
            if UserFlowCfg.table_exists():
                UserFlowCfg.delete().execute()
            else:
                db.create_tables([UserFlowCfg])

