# encoding: utf-8
from peewee import Model, SqliteDatabase

# 设置数据库路径
db_path = './data/streamlit_data.db'
print(f"正在连接数据库: {db_path}")
db = SqliteDatabase(db_path, pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64,
    'foreign_keys': 1,
    'ignore_check_constraints': 0,
    'synchronous': 0
})

class BaseModel(Model):
    class Meta:
        database = db
