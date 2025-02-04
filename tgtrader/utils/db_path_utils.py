# encoding: utf-8
import os
from peewee import SqliteDatabase
from tgtrader.utils.duckdb_peewee import DuckDBDatabase

def ensure_dir_exists(path: str) -> None:
    """
    确保目录存在，如果不存在则创建。

    Args:
        path: 目录路径
    """
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_user_data_db_path(user: str) -> str:
    """
    获取用户数据库路径。

    Args:
        user: 用户名

    Returns:
        str: 数据库文件路径
    """
    default_path = os.path.join(os.getcwd(), 'data', f'{user}_data.db')
    db_path: str = os.getenv('DATA_PATH', default_path)
    ensure_dir_exists(db_path)
    return db_path

def get_user_data_database(user: str) -> DuckDBDatabase:
    """
    获取用户数据库连接。

    Args:
        user: 用户名

    Returns:
        DuckDBDatabase: 数据库连接对象
    """
    db_path = get_user_data_db_path(user)
    return DuckDBDatabase(db_path)

def get_common_data_db_path() -> str:
    """
    获取公共数据库路径。

    Returns:
        str: 数据库文件路径
    """
    default_path = os.path.join(os.getcwd(), 'data', 'common.sqlite')
    db_path: str = os.getenv('DATA_PATH', default_path)
    ensure_dir_exists(db_path)
    return db_path

def get_common_data_database() -> SqliteDatabase:
    """
    获取公共数据库连接。

    Returns:
        SqliteDatabase: 数据库连接对象
    """
    db_path = get_common_data_db_path()
    db = SqliteDatabase(db_path, pragmas={
        'journal_mode': 'wal',
        'cache_size': -1024 * 64,
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 0
    })
    return db

