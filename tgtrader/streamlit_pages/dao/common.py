# encoding: utf-8
from peewee import Model, SqliteDatabase

# 设置数据库路径
db_path = './data/data.db'
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db
