# encoding: utf-8
import os
from peewee import Model
from loguru import logger
from tgtrader.utils.duckdb_peewee import DuckDBDatabase


default_path = os.path.join(os.getcwd(), 'data', 'akshare_data.db')
db_path: str = os.getenv('DATA_PATH', default_path)
main_db: DuckDBDatabase = DuckDBDatabase(db_path)
logger.info(f"akshare main_db: {db_path}")

class BaseModel(Model):
    """
    Base model class for all database models.
    """
    class Meta:
        """
        Meta class for BaseModel.
        """
        primary_key = False
        database = main_db