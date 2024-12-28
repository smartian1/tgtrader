# encoding: utf-8
from peewee import Model, SqliteDatabase, CharField, Proxy

from loguru import logger

# 创建 Proxy 实例
database_proxy = Proxy()

class BaseModel(Model):
    def __init__(self, *args, database=None, **kwargs):
        # 如果数据库参数为空，抛出异常
        if database is None:
            raise ValueError("'database' 参数不能为空")
        
        # 初始化模型
        super().__init__(*args, **kwargs)
        
        # 通过 Proxy 绑定数据库
        self._bind_database(database)

    def _bind_database(self, database):
        """绑定数据库，避免每个实例都暴露 Proxy"""
        database_proxy.initialize(database)
        self._meta.database = database_proxy  # 设置当前实例的数据库
        
        # 确保表已经初始化（创建）
        self._init_table()

    def _init_table(self):
        """表初始化，确保表在指定数据库中创建"""
        if not self._meta.database.get_tables():
            self._meta.database.create_tables([self.__class__], safe=True)

    class Meta:
        primary_key = False
        database = database_proxy  # 使用 Proxy 来动态指定数据库