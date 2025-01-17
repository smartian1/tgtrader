# encoding: utf-8
import os
from tgtrader.utils.duckdb_peewee import DuckDBDatabase

def get_user_data_db_path(user: str) -> str:
    default_path = os.path.join(os.getcwd(), 'data', f'{user}_data.db')
    db_path: str = os.getenv('DATA_PATH', default_path)
    return db_path

def get_user_data_database(user: str) -> DuckDBDatabase:
    db_path = get_user_data_db_path(user)
    return DuckDBDatabase(db_path)
