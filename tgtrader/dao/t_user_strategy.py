# encoding: utf-8
from loguru import logger
from peewee import *
from datetime import datetime
from tgtrader.dao.common import BaseModel, db

class UserStrategy(BaseModel):
    # 主键自增id
    id = AutoField()
    # 用户id
    user_id = IntegerField()
    # 策略配置JSON
    strategy = TextField()
    # 创建时间
    create_time = BigIntegerField(default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_user_strategy'

    def save(self, *args, **kwargs):
        # 更新时间戳
        self.update_time = int(datetime.now().timestamp())
        return super(UserStrategy, self).save(*args, **kwargs)

    @classmethod
    def init_table(cls):
        # 初始化表
        with db:
            if not UserStrategy.table_exists():
                db.create_tables([UserStrategy])  # 如果表不存在，创建表

    @classmethod
    def get_user_strategies(cls, user_id: int):
        """获取用户的所有策略，按更新时间倒序排列"""
        with db:
            return list(cls.select().where(cls.user_id == user_id).order_by(cls.update_time.desc()))
        
    @classmethod
    def get_strategy(cls, user_id: int, strategy_id: int):
        """获取策略"""
        with db:
            return cls.get(cls.id == strategy_id, cls.user_id == user_id)

    @classmethod
    def create_strategy(cls, user_id: int, strategy: str):
        """创建新的策略"""
        with db:
            return cls.create(
                user_id=user_id,
                strategy=strategy
            )

    @classmethod
    def update_strategy(cls, user_id: int, strategy_id: int, strategy: str):
        """更新策略"""
        with db:
            query = cls.update(
                strategy=strategy,
                update_time=int(datetime.now().timestamp())
            ).where(cls.id == strategy_id, cls.user_id == user_id)
            return query.execute()

    @classmethod
    def delete_strategy(cls, user_id: int, strategy_id: int):
        """删除策略"""
        with db:
            return cls.delete().where(cls.id == strategy_id, cls.user_id == user_id).execute()


UserStrategy.init_table()
