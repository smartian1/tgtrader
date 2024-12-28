import os
import duckdb
import pandas as pd
from loguru import logger
from tgtrader.common import DataProvider, SecurityType, Period, PriceAdjust
from typing import List
from tgtrader.utils.duckdb_handler import DuckDBHandler


class DataProviderDuckDB(DataProvider):
    def __init__(self, db_path: str):
        """初始化DuckDB数据提供者

        Args:
            directory_path: 存储DuckDB数据库文件的目录路径
        """
        super().__init__()
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)

    def init_db(self, db_name: str):
        """初始化数据库，检查数据库文件是否存在，若不存在则创建，并创建元信息表"""
        db_file_path = os.path.join(self.db_path, f"{db_name}.db")

        # 如果数据库文件不存在，则创建
        if not os.path.exists(db_file_path):
            try:
                # 创建数据库连接
                conn = duckdb.connect(db_file_path)
                cursor = conn.cursor()
    
                # 创建元信息表
                create_table_query = """
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    create_time TEXT,
                    update_time TEXT
                );
                """
                cursor.execute(create_table_query)

                # 提交事务并关闭连接
                conn.commit()
                conn.close()
                logger.info(f"Database and metadata table created at {db_file_path}")

            except Exception as e:
                logger.error(f"Error initializing database: {str(e)}")

        else:
            logger.info(f"Database already exists at {db_file_path}")

    def _get_db_path(self, security_type: SecurityType, period: Period) -> str:
        """根据参数生成数据库文件路径（不包含adjust）"""
        filename = f"kdata_{security_type.value}_{period.value}.db"
        return os.path.join(self.db_path, filename)

    def get_price(
        self,
        symbol_list: List[str],
        start_date: str,
        end_date: str,
        security_type: SecurityType,
        period: Period = Period.Day,
        adjust: PriceAdjust = PriceAdjust.HFQ,
        fields: List[str] = ["open", "high", "low", "close", "volume"]
    ) -> pd.DataFrame:
        """获取行情数据"""
        db_path = self._get_db_path(security_type, period, adjust)
        fields_str = ", ".join(fields)
        symbols_str = ", ".join([f"'{s}'" for s in symbol_list])

        table_name = f"k_data_{adjust.value}"

        query = f"""
            SELECT code, date, {fields_str}
            FROM {table_name}
            WHERE code IN ({symbols_str})
            AND date BETWEEN ? AND ?
            ORDER BY code, date
        """

        params = (start_date, end_date)

        try:
            with DuckDBHandler(db_path) as db:
                records = db.select_many(query, params)
                if not records:
                    logger.warning(
                        f"No data found for query: {query} with params {params}")
                    return pd.DataFrame()

                # 将结果转换为 DataFrame
                df = pd.DataFrame(records, columns=['code', 'date'] + fields)
                df.set_index(['code', 'date'], inplace=True)
                return df

        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()

    def save_data(
        self,
        data: pd.DataFrame,
        security_type: SecurityType,
        period: Period,
        adjust: PriceAdjust
    ):
        """保存行情数据"""
        if data.empty:
            logger.warning("No data to save")
            return

        db_path = self._get_db_path(security_type, period, adjust)
        table_name = f"k_data_{adjust.value}"

        try:
            # 重置索引，确保code和date为列
            df = data.reset_index()

            # 获取所有列名
            columns = df.columns.tolist()

            # 构建INSERT语句的列部分
            insert_columns = ", ".join(columns)

            # 构建SELECT部分
            select_columns = ", ".join(columns)

            # 构建ON CONFLICT更新部分，排除主键
            update_columns = ", ".join(
                [f"{col} = EXCLUDED.{col}" for col in columns if col not in ['code', 'date']])

            # 注册临时表
            with DuckDBHandler(db_path) as db:
                db.conn.register('temp_df', df)

                # 执行 UPSERT 操作
                upsert_query = f"""
                    INSERT INTO {table_name} ({insert_columns})
                    SELECT {select_columns}
                    FROM temp_df
                    ON CONFLICT (code, date) 
                    DO UPDATE SET 
                        {update_columns}
                """
                db.insert(upsert_query)

                logger.info(f"Saved {len(df)} records to {db_path}")


        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")

    def standardize_symbol(self, symbol: str) -> str:
        """标准化证券代码格式"""
        return symbol
