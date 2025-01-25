# encoding: utf-8
import os
from peewee import SqliteDatabase
from tgtrader.utils.duckdb_peewee import DuckDBDatabase

def get_user_data_db_path(user: str) -> str:
    default_path = os.path.join(os.getcwd(), 'data', f'{user}_data.db')
    db_path: str = os.getenv('DATA_PATH', default_path)
    return db_path

def get_user_data_database(user: str) -> DuckDBDatabase:
    db_path = get_user_data_db_path(user)
    return DuckDBDatabase(db_path)

def get_common_data_db_path() -> str:
    default_path = os.path.join(os.getcwd(), 'data', 'common.sqlite')
    db_path: str = os.getenv('DATA_PATH', default_path)
    return db_path

def get_common_data_database() -> DuckDBDatabase:
    db_path = get_common_data_db_path()
    db = SqliteDatabase(db_path, pragmas={
        'journal_mode': 'wal',
        'cache_size': -1024 * 64,
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 0
    })
    return db

