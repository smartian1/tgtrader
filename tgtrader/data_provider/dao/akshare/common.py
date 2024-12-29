# encoding: utf-8
from peewee import Model, SqliteDatabase, CharField, Proxy

from loguru import logger

from tgtrader.utils.duckdb_peewee import DuckDBDatabase


db_path = './data/main_data.db'
main_db = DuckDBDatabase(db_path)


class BaseModel(Model):
    class Meta:
        primary_key = False
        database = main_db