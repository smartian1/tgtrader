# encoding: utf-8

# 设置数据库路径
from tgtrader.utils.duckdb_handler import DuckDBDatabase


akshare_db_path = './data/akshare_data.db'
akshare_db = DuckDBDatabase(akshare_db_path)
