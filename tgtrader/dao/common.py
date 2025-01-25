# encoding: utf-8
from peewee import Model, SqliteDatabase
from tgtrader.utils.db_path_utils import get_common_data_database

# 设置数据库路径
db = get_common_data_database()

class BaseModel(Model):
    class Meta:
        database = db
