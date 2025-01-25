# encoding: utf-8
from peewee import Model, SqliteDatabase
from tgtrader.utils.db_path_utils import get_common_data_database
import time

# 设置数据库路径
db = get_common_data_database()

class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def create_or_update(cls, *args, **kwargs):
        instance = cls.get_or_none(**kwargs)
        if instance:
            instance.update_time = int(time.time() * 1000)
            instance.save()
        else:
            cls.create(**kwargs)
