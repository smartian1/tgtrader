# encoding: utf-8
from peewee import *
from tqdm import tqdm
from loguru import logger
from tgtrader.common import DataSource
from tgtrader.data_provider.dao.akshare.common import main_db
from tgtrader.data_provider.dao.models.common import register_model
from tgtrader.data_provider.dao.models.t_kdata_model import T_KData_Model


@register_model(DataSource.Akshare, 't_kdata')
class T_KData(T_KData_Model):

    @classmethod
    def init_table(cls):
        # 初始化表
        with main_db:
            table_exists = T_KData.table_exists()
            if not table_exists:
                main_db.create_tables([T_KData])  # 如果表不存在，创建表

    @classmethod
    def batch_insert_many(cls, data_list: list, batch_size: int = 1000) -> int:
        """批量插入数据，自动分批、显示进度

        Args:
            data_list: 要插入的数据列表
            batch_size: 每批数据量，默认1000条

        Returns:
            int: 成功插入的记录数
        """
        if not data_list:
            logger.warning("No data to insert")
            return 0

        total_count = 0
        
        try:
            with main_db:
                # 使用tqdm显示进度
                for i in tqdm(range(0, len(data_list), batch_size), 
                            desc="Inserting data"):
                    batch = data_list[i:i + batch_size]
                    rows = cls.insert_many(batch).on_conflict(
                        conflict_target=[cls.code, cls.date, cls.source],
                        action='UPDATE',
                        update={
                            cls.open: cls.open,
                            cls.high: cls.high,
                            cls.low: cls.low,
                            cls.close: cls.close,
                            cls.volume: cls.volume,
                            cls.adjust_type: cls.adjust_type,
                            cls.update_time: cls.update_time
                        }
                    ).execute()
                    total_count += len(batch)
                    
            logger.info(f"Successfully inserted/updated {total_count} records")
            return total_count
            
        except Exception as e:
            logger.error(f"Error in batch insert: {str(e)}")
            raise
