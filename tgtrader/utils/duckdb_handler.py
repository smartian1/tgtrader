# encoding: utf-8

from loguru import logger
import duckdb
from typing import Any, List, Optional, Tuple, Union


"""
peewee 的 Database 类不支持 DuckDB，需要自己实现一个
"""
import peewee
import duckdb

import duckdb
from peewee import Database, fn, CharField, AutoField, BigIntegerField, BooleanField, DoubleField, SmallIntegerField, UUIDField, TextField, IntegerField, FloatField, TimestampField, DatabaseError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

import duckdb
import logging

# Configure the logger
logger = logging.getLogger(__name__)

# Assuming the base Database class and field types are defined elsewhere
# from your_module import Database, AutoField, BigIntegerField, BooleanField, DoubleField,
# SmallIntegerField, UUIDField, TextField, IntegerField, FloatField, TimestampField, CharField, DatabaseError, fn

class DuckDBDatabase(Database):
    field_types = {
        'BIGAUTO': AutoField,
        'BIGINT': BigIntegerField,
        'BOOL': BooleanField,
        'DOUBLE': DoubleField,
        'SMALLINT': SmallIntegerField,
        'UUID': UUIDField,
        'TEXT': TextField,
        'INTEGER': IntegerField,
        'FLOAT': FloatField,
        'TIMESTAMP': TimestampField,
        'CHAR': CharField,  # Corrected to 'CHAR' to avoid duplicate 'TEXT' key
        # Add other necessary field types as needed
    }

    operations = {
        'LIKE': 'ILIKE',  # DuckDB uses ILIKE for case-insensitive LIKE operations
        'ILIKE': 'ILIKE'
    }

    index_schema_prefix = True
    limit_max = -1
    server_version = None
    truncate_table = False

    def __init__(self, database, *args, **kwargs):
        super(DuckDBDatabase, self).__init__(database, *args, **kwargs)
        self._functions = {}
        self._extensions = set()

    def init(self, database, timeout=5, **kwargs):
        self._timeout = timeout
        super(DuckDBDatabase, self).init(database, **kwargs)

    def _connect(self):
        try:
            conn = duckdb.connect(self.database)
            # Optionally retrieve and set server_version dynamically
            version_info = conn.execute("SELECT version()").fetchone()
            if version_info:
                # Example version string: 'DuckDB 0.3.2'
                version_str = version_info[0].split()[1]  # Extract '0.3.2'
                self.server_version = tuple(map(int, version_str.split('.')[:3]))
            return conn
        except duckdb.Error as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise DatabaseError(e)

    def close(self):
        try:
            if not self.is_closed():
                self.connection().close()
        except duckdb.Error as e:
            logger.error(f"Failed to close DuckDB connection: {e}")
            raise DatabaseError(e)

    def execute_sql(self, sql, params=None):
        try:
            if params:
                return self.connection().execute(sql, params).fetchall()
            else:
                return self.connection().execute(sql).fetchall()
        except duckdb.Error as e:
            logger.error(f"SQL execution failed: {e}")
            raise DatabaseError(e)

    def last_insert_id(self):
        # DuckDB doesn't support last_insert_id() natively, so we return None
        return None

    def _begin(self):
        try:
            self.connection().execute('BEGIN')
        except duckdb.Error as e:
            logger.error(f"Failed to begin transaction: {e}")
            raise DatabaseError(e)

    def _commit(self):
        try:
            self.connection().commit()
        except duckdb.Error as e:
            logger.error(f"Failed to commit transaction: {e}")
            raise DatabaseError(e)

    def _rollback(self):
        try:
            self.connection().rollback()
        except duckdb.Error as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise DatabaseError(e)

    def register_function(self, fn, name=None, num_params=-1, deterministic=None):
        name = name or fn.__name__
        self._functions[name] = (fn, num_params, deterministic)
        if not self.is_closed():
            self._load_functions(self.connection())

    def _load_functions(self, conn):
        for name, (fn, n_params, deterministic) in self._functions.items():
            try:
                conn.create_function(name, n_params, fn)
            except duckdb.Error as e:
                logger.error(f"Failed to load function '{name}': {e}")
                raise DatabaseError(e)

    def load_extension(self, extension):
        self._extensions.add(extension)
        if not self.is_closed():
            conn = self.connection()
            try:
                conn.load_extension(extension)
            except duckdb.Error as e:
                logger.error(f"Failed to load extension '{extension}': {e}")
                raise DatabaseError(e)

    def get_tables(self, schema=None):
        """
        Retrieve a list of table names from the specified schema.

        :param schema: The schema to search within. Defaults to 'main'.
        :return: A list of table names.
        """
        try:
            cursor = self.execute_sql(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = ?",
                (schema or 'main',)
            )
            return [row[0] for row in cursor]
        except DatabaseError as e:
            logger.error(f"Failed to retrieve tables: {e}")
            return []

    def get_columns(self, table, schema=None):
        """
        Fetch column information from DuckDB system catalog.

        :param table: The table name.
        :param schema: The schema name. Defaults to 'main'.
        :return: A list of tuples containing column names and data types.
        """
        try:
            cursor = self.execute_sql(
                'SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ? AND table_schema = ?',
                (table, schema or 'main')
            )
            return [(row[0], row[1]) for row in cursor]
        except DatabaseError as e:
            logger.error(f"Failed to retrieve columns for table '{table}': {e}")
            return []

    def get_primary_keys(self, table, schema=None):
        """
        Approximate retrieval of primary keys since DuckDB doesn't enforce them.

        :param table: The table name.
        :param schema: The schema name. Defaults to 'main'.
        :return: A list of column names acting as primary keys.
        """
        try:
            cursor = self.execute_sql(
                'SELECT column_name FROM information_schema.key_column_usage WHERE table_name = ? AND table_schema = ?',
                (table, schema or 'main')
            )
            return [row[0] for row in cursor]
        except DatabaseError as e:
            logger.error(f"Failed to retrieve primary keys for table '{table}': {e}")
            return []

    def get_indexes(self, table, schema=None):
        """
        Retrieve index information from DuckDB system catalogs.

        :param table: The table name.
        :param schema: The schema name. Defaults to 'main'.
        :return: A list of index names.
        """
        try:
            cursor = self.execute_sql(
                'SELECT index_name FROM information_schema.statistics WHERE table_name = ? AND table_schema = ?',
                (table, schema or 'main')
            )
            return [row[0] for row in cursor]
        except DatabaseError as e:
            logger.error(f"Failed to retrieve indexes for table '{table}': {e}")
            return []

    def get_foreign_keys(self, table, schema=None):
        """
        DuckDB does not enforce foreign key constraints.

        :param table: The table name.
        :param schema: The schema name. Defaults to 'main'.
        :return: An empty list.
        """
        return []

    def conflict_statement(self, on_conflict, query):
        """
        Generate the ON CONFLICT clause for DuckDB.

        DuckDB supports the following syntax:
        ON CONFLICT (column_list) DO UPDATE SET column1 = excluded.column1, ...

        :param on_conflict: A dictionary specifying conflict resolution.
                            Example:
                            {
                                'columns': ['valid_from'],
                                'update': {'value': 'excluded.value'}
                            }
        :param query: The query object (if needed for additional context).
        :return: A string containing the ON CONFLICT clause.
        """
        if not on_conflict:
            return ''

        conflict_columns = on_conflict.get('columns', [])
        update_dict = on_conflict.get('update', {})

        if not conflict_columns:
            logger.error("ON CONFLICT clause requires at least one column to specify conflict target.")
            raise ValueError("ON CONFLICT requires at least one column.")

        conflict_clause = f"ON CONFLICT ({', '.join(conflict_columns)})"

        if update_dict:
            set_clause = ', '.join([f"{col} = excluded.{col}" for col in update_dict.keys()])
            conflict_clause += f" DO UPDATE SET {set_clause}"
        else:
            conflict_clause += " DO NOTHING"

        return conflict_clause

    def truncate_date(self, date_part, date_field):
        """
        Truncate the date to the specified part.

        :param date_part: The part to truncate to (e.g., 'month', 'year').
        :param date_field: The date field.
        :return: Truncated date expression.
        """
        return fn.date_trunc(date_part, date_field)

    def extract_date(self, date_part, date_field):
        """
        Extract a specific part from the date.

        :param date_part: The part to extract (e.g., 'year', 'month').
        :param date_field: The date field.
        :return: Extracted date part.
        """
        return fn.date_part(date_part, date_field)

    def to_timestamp(self, date_field):
        """
        Convert a date field to a Unix timestamp.

        :param date_field: The date field.
        :return: Unix timestamp as integer.
        """
        return fn.strftime('%s', date_field).cast('INTEGER')

    def from_timestamp(self, timestamp_field):
        """
        Convert a Unix timestamp to a datetime.

        :param timestamp_field: The Unix timestamp.
        :return: Datetime object.
        """
        return fn.to_timestamp(timestamp_field)

    def rows_affected(self, cursor):
        """
        Return the number of rows affected by the query.

        :param cursor: The cursor object.
        :return: Number of rows affected or None.
        """
        return cursor.rowcount if hasattr(cursor, 'rowcount') else None

    def insert_with_conflict(self, table, data, on_conflict=None):
        """
        Insert data into a table with optional conflict resolution.

        :param table: The table name.
        :param data: A dictionary of column-value pairs to insert.
        :param on_conflict: A dictionary specifying conflict resolution.
                            Example:
                            {
                                'columns': ['valid_from'],
                                'update': {'value': 'excluded.value'}
                            }
        :return: Result of the insert operation.
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        conflict_clause = self.conflict_statement(on_conflict, None)
        if conflict_clause:
            sql += f" {conflict_clause}"

        params = tuple(data.values())

        try:
            self.execute_sql(sql, params)
            return True
        except DatabaseError as e:
            logger.error(f"Failed to insert data into '{table}': {e}")
            return False



"""
不使用peewee, 直接操作duckdb
"""
class DuckDBHandler:
    """
    DuckDB 操作类，支持基本的 CRUD 操作，并使用上下文管理器自动管理连接。
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化 DuckDBHandler。

        :param db_path: 数据库文件路径。如果为 None，则使用内存数据库。
        """
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """
        进入上下文管理器时建立数据库连接。
        """
        self.conn = duckdb.connect(database=self.db_path, read_only=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器时关闭数据库连接。
        如果在上下文中发生异常，事务将被回滚；否则，提交事务。
        """
        if self.conn:
            if exc_type is None:
                try:
                    self.conn.commit()
                except Exception as e:
                    logger.error(f"提交事务时出错: {e}")
            else:
                try:
                    self.conn.rollback()
                except Exception as e:
                    logger.error(f"回滚事务时出错: {e}")
            self.conn.close()

    def select_one(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Tuple]:
        """
        执行查询并返回单个结果。

        :param query: SQL 查询语句。
        :param params: 查询参数。
        :return: 单个结果元组或 None。
        """
        try:
            result = self.conn.execute(query, params or ()).fetchone()
            return result
        except Exception as e:
            logger.exception(e)

    def select_many(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Tuple]:
        """
        执行查询并返回所有结果。

        :param query: SQL 查询语句。
        :param params: 查询参数。
        :return: 结果元组列表。
        """
        try:
            result = self.conn.execute(query, params or ()).fetchall()
            return result
        except Exception as e:
            logger.exception(e)

    def insert(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> bool:
        """
        执行单条插入操作。

        :param query: SQL 插入语句。
        :param params: 插入参数。
        :return: 成功与否。
        """
        try:
            self.conn.execute(query, params or ())
        except Exception as e:
            logger.exception(e)

    def insert_batch(self, query: str, params_list: List[Tuple[Any, ...]]) -> bool:
        """
        执行批量插入操作。

        :param query: SQL 插入语句。
        :param params_list: 插入参数列表。
        :return: 成功与否。
        """
        try:
            self.conn.executemany(query, params_list)
        except Exception as e:
            logger.exception(e)

    def update(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> bool:
        """
        执行更新操作。

        :param query: SQL 更新语句。
        :param params: 更新参数。
        :return: 成功与否。
        """
        try:
            self.conn.execute(query, params or ())
        except Exception as e:
            logger.exception(e)

    def delete(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> bool:
        """
        执行删除操作。

        :param query: SQL 删除语句。
        :param params: 删除参数。
        :return: 成功与否。
        """
        try:
            self.conn.execute(query, params or ())
        except Exception as e:
            logger.exception(e)
