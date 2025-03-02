# encoding: utf-8
from loguru import logger
import duckdb
from typing import List, Optional, Tuple
from peewee import *


class DuckDBCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = None
        self.description = None
        self.rowcount = 0

    def execute(self, sql, params=None):
        if params:
            self.result = self.connection.execute(sql, params)
        else:
            self.result = self.connection.execute(sql)
        self.description = self.result.description if self.result else None
        self.rowcount = self.result.rowcount if self.result else 0
        return self.result

    def fetchone(self):
        return self.result.fetchone() if self.result else None

    def fetchall(self):
        return self.result.fetchall() if self.result else []

    def close(self):
        self.result = None
        self.description = None
        self.rowcount = 0


class DuckDBDatabase(Database):

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

    def __enter__(self):
        if self.is_closed():
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_closed():
            self.close()
    
    def cursor(self):
        return DuckDBCursor(self.connection())


    def _connect(self):
        try:
            conn = duckdb.connect(self.database)
            # Optionally retrieve and set server_version dynamically
            version_info = conn.execute("SELECT version()").fetchone()
            if version_info:
                version_str = version_info[0][1:]
                self.server_version = tuple(
                    map(int, version_str.split('.')[:3]))
            return conn
        except duckdb.Error as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise DatabaseError(e)

    def _close(self, conn):
        try:
            if not self.is_closed():
                conn.close()
        except duckdb.Error as e:
            raise e


    def execute_sql(self, sql, params=None):
        try:
            cursor = self.cursor()
            cursor.execute(sql, params)
            return cursor
        except duckdb.Error as e:
            raise e

    def last_insert_id(self, cursor, query_type=None):
        # DuckDB doesn't support last_insert_id() natively, so we return None
        return None

    def _begin(self):
        try:
            self.connection().execute('BEGIN')
        except duckdb.Error as e:
            raise e

    def _commit(self):
        try:
            self.connection().commit()
        except duckdb.Error as e:
            raise e

    def _rollback(self):
        try:
            self.connection().rollback()
        except duckdb.Error as e:
            raise e

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
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise e

    def get_columns(self, table_name):
        """
        获取指定表的列信息。

        Args:
            table_name (str): 要查询的表名

        Returns:
            List[ColumnMetadata]: 表的列元数据信息
        """
        from collections import namedtuple
        
        ColumnMetadata = namedtuple('ColumnMetadata', [
            'name', 'data_type', 'null', 'primary_key', 'table', 'default'
        ])
        
        cursor = self.execute_sql(
            'PRAGMA table_info(%s)' % table_name)
        # 需要先调用fetchall()来获取结果
        rows = cursor.fetchall()
        
        columns = []
        for row in rows:
            column = ColumnMetadata(
                name=row[1],  # 列名
                data_type=row[2],  # 数据类型 
                null=row[3] == 0,  # null属性 (0表示NOT NULL, 1表示可为NULL)
                primary_key=row[5] == 1,  # 是否为主键
                table=table_name,  # 表名
                default=None  # DuckDB PRAGMA table_info 不直接返回默认值
            )
            columns.append(column)
        
        return columns

    def get_primary_keys(self, table, schema=None):
        columns = self.get_columns(table)
        return [column.name for column in columns if column.primary_key]    

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
            raise e

    def get_foreign_keys(self, table, schema=None):
        """
        DuckDB does not enforce foreign key constraints.

        :param table: The table name.
        :param schema: The schema name. Defaults to 'main'.
        :return: An empty list.
        """
        return []

    def conflict_statement(self, on_conflict, query):
        action = on_conflict._action.lower() if on_conflict._action else ''
        if action and action not in ('nothing', 'update'):
            return SQL('INSERT OR %s' % on_conflict._action.upper())

    def conflict_update(self, oc, query):
        action = oc._action.lower() if oc._action else ''
        if action and action not in ('nothing', 'update', ''):
            return

        if action == 'nothing':
            return SQL('ON CONFLICT DO NOTHING')
        elif not oc._update and not oc._preserve:
            raise ValueError('If you are not performing any updates (or '
                             'preserving any INSERTed values), then the '
                             'conflict resolution action should be set to '
                             '"NOTHING".')
        elif oc._conflict_constraint:
            raise ValueError('SQLite does not support specifying named '
                             'constraints for conflict resolution.')
        elif not oc._conflict_target:
            raise ValueError('SQLite requires that a conflict target be '
                             'specified when doing an upsert.')

        return self._build_on_conflict_update(oc, query)

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
