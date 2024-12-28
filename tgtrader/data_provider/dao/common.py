# encoding: utf-8
from peewee import Model


class BaseModel(Model):
    class Meta:
        database = None

    def __init__(self, *args, **kwargs):
        db = kwargs.pop('database', None)
        if db:
            self.Meta.database = db
        else:
            raise ValueError("'database'参数不能为空")
        super().__init__(*args, **kwargs)