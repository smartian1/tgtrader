# encoding: utf-8

from tgtrader.common import DataSource
from tgtrader.utils.duckdb_peewee import DuckDBDatabase
import pandas as pd
from typing import Optional

from tgtrader.data_provider.dao.akshare.common import main_db as akshare_db

class DuckDBQuery:
    def __init__(self, db: Optional[DuckDBDatabase|DataSource|str] = None):
        if isinstance(db, str):
            db = DataSource(db.lower())
        
        if isinstance(db, DataSource):
            if db == DataSource.Akshare:
                self.db = akshare_db
            else:
                raise ValueError(f"不支持的数据源: {db}")
        elif isinstance(db, DuckDBDatabase):
            self.db = db
        else:
            raise ValueError(f"不支持的数据源: {db}")

    def fetch_df(self, sql: str) -> pd.DataFrame:
        with self.db:
            cursor = self.db.execute_sql(sql)
            # 获取列名
            columns = [desc[0] for desc in cursor.description]

            # 获取查询结果
            rows = cursor.fetchall()

            # 将结果转换成 DataFrame
            df = pd.DataFrame(rows, columns=columns)
            return df
