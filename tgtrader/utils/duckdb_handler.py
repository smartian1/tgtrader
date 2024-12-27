# encoding: utf-8

from loguru import logger
import duckdb
from typing import Any, List, Optional, Tuple, Union


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
