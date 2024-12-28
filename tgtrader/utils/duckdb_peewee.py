# encoding: utf-8
from loguru import logger
import duckdb
from typing import List, Optional, Tuple
from peewee import *


class DuckDBCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = None
        self.description = None  # 初始化 description 属性
        self.rowcount = 0  # 初始化 rowcount 属性

    def execute(self, sql, params=None):
        if params:
            self.result = self.connection.execute(sql, params)
        else:
            self.result = self.connection.execute(sql)
        # 获取描述信息
        if self.result:
            self.description = self.result.description
            self.rowcount = self.result.rowcount if hasattr(self.result, 'rowcount') else 0
        else:
            self.description = None
            self.rowcount = 0
        return self.result

    def fetchone(self):
        if self.result is not None:
            return self.result.fetchone()
        return None

    def fetchall(self):
        if self.result is not None:
            return self.result.fetchall()
        return []

    def close(self):
        """关闭游标"""
        if self.result:
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

    def close(self):
        try:
            if not self.is_closed():
                self.connection().close()
        except duckdb.Error as e:
            logger.error(f"Failed to close DuckDB connection: {e}")
            raise DatabaseError(e)

    def execute_sql(self, sql, params=None):
        try:
            cursor = self.cursor()
            cursor.execute(sql, params)
            return cursor
        except duckdb.Error as e:
            logger.error(f"SQL execution failed: {e}")
            raise DatabaseError(e)

    def last_insert_id(self, cursor, query_type=None):
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
            rows = cursor.fetchall()
            return [row[0] for row in rows]
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
            logger.error(
                f"Failed to retrieve columns for table '{table}': {e}")
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
            logger.error(
                f"Failed to retrieve primary keys for table '{table}': {e}")
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
            logger.error(
                f"Failed to retrieve indexes for table '{table}': {e}")
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
    
    # def conflict_statement(self, on_conflict, query):
    #     """
    #     Generate the ON CONFLICT clause for DuckDB.

    #     DuckDB supports the following syntax:
    #     ON CONFLICT (column_list) DO UPDATE SET column1 = excluded.column1, ...

    #     :param on_conflict: An OnConflict object specifying conflict resolution.
    #     :param query: The query object (if needed for additional context).
    #     :return: A string containing the ON CONFLICT clause.
    #     """
    #     if not on_conflict:
    #         return ''

    #     conflict_target = on_conflict.conflict_target
    #     update_dict = on_conflict.update

    #     if not conflict_target:
    #         logger.error(
    #             "ON CONFLICT clause requires at least one column to specify conflict target."
    #         )
    #         raise ValueError("ON CONFLICT requires at least one column.")

    #     conflict_clause = f"ON CONFLICT ({', '.join([col._name for col in conflict_target])})"

    #     if update_dict:
    #         set_clause = ', '.join(
    #             [f"{col._name} = excluded.{col._name}" for col in update_dict.keys()]
    #         )
    #         conflict_clause += f" DO UPDATE SET {set_clause}"
    #     else:
    #         conflict_clause += " DO NOTHING"

    #     return conflict_clause


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

    # def insert_with_conflict(self, table, data, on_conflict=None):
    #     """
    #     Insert data into a table with optional conflict resolution.

    #     :param table: The table name.
    #     :param data: A dictionary of column-value pairs to insert.
    #     :param on_conflict: A dictionary specifying conflict resolution.
    #                         Example:
    #                         {
    #                             'columns': ['valid_from'],
    #                             'update': {'value': 'excluded.value'}
    #                         }
    #     :return: Result of the insert operation.
    #     """
    #     columns = ', '.join(data.keys())
    #     placeholders = ', '.join(['?'] * len(data))
    #     sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    #     conflict_clause = self.conflict_statement(on_conflict, None)
    #     if conflict_clause:
    #         sql += f" {conflict_clause}"

    #     params = tuple(data.values())

    #     try:
    #         self.execute_sql(sql, params)
    #         return True
    #     except DatabaseError as e:
    #         logger.error(f"Failed to insert data into '{table}': {e}")
    #         return False
