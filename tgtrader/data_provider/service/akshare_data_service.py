# encoding: utf-8
from typing import List, Optional
import pandas as pd
from tqdm import tqdm
from loguru import logger
import time
from peewee import SQL

from tgtrader.data_provider.dao.akshare.common import main_db
from tgtrader.data_provider.dao.akshare.t_kdata import T_KData
from tgtrader.data_provider.dao.akshare.t_etf_kdata import T_ETF_KData
from tgtrader.data_provider.dao.akshare.t_meta import T_Meta
from tgtrader.common import DataSource, MetaType, SecurityType, Period, PriceAdjust
from tgtrader.common import DataDbService
from tgtrader.data_provider.dao.models.common import ModelRegister
from tgtrader.data_provider.dao.models.t_meta_model import T_Meta_Model


class AkshareDataService(DataDbService):
    """Akshare数据服务实现类"""
    
    @classmethod
    def init_database(cls):
        """初始化数据"""
        with main_db:
            main_db.create_tables([T_Meta, T_KData, T_ETF_KData])

    def batch_save_kdata(self,
                        data: Optional[pd.DataFrame] = None,
                        security_type: SecurityType = SecurityType.Stocks,
                        adjust: Optional[PriceAdjust] = None,
                        source: str = 'akshare',
                        batch_size: int = 100000) -> int:
        """批量保存K线数据"""
        try:
            # 如果传入DataFrame，转换为data_list
            if data is not None:
                if data.empty:
                    logger.warning("Empty DataFrame provided")
                    return 0
                    
                # 重置索引,将MultiIndex转换为普通列
                df = data.reset_index()
                
                # 准备数据列表
                current_time = int(time.time() * 1000)
                data_list = []
                
                for _, row in df.iterrows():
                    kdata = {
                        'code': row['code'],
                        'date': row['date'].strftime('%Y-%m-%d'),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume']),
                        'adjust_type': adjust.value,
                        'source': source,
                        'create_time': current_time,
                        'update_time': current_time
                    }
                    data_list.append(kdata)
            
            if not data_list:
                logger.warning("No data to save")
                return 0

            total_count = 0

            if security_type == SecurityType.STOCK:
                db_model_cls = T_KData
            elif security_type == SecurityType.ETF:
                db_model_cls = T_ETF_KData
            else:
                raise ValueError(f"Unsupported security type: {security_type}")
            
            with main_db:
                # 使用tqdm显示进度
                for i in tqdm(range(0, len(data_list), batch_size), 
                            desc="Saving kdata"):
                    batch = data_list[i:i + batch_size]
                    rows = db_model_cls.insert_many(batch).on_conflict(
                        conflict_target=[db_model_cls.code, db_model_cls.date, db_model_cls.source],
                        action='UPDATE',
                        update={
                            db_model_cls.open: SQL('EXCLUDED.open'),
                            db_model_cls.high: SQL('EXCLUDED.high'),
                            db_model_cls.low: SQL('EXCLUDED.low'),
                            db_model_cls.close: SQL('EXCLUDED.close'),
                            db_model_cls.volume: SQL('EXCLUDED.volume'),
                            db_model_cls.adjust_type: SQL('EXCLUDED.adjust_type'),
                            db_model_cls.update_time: SQL('EXCLUDED.update_time')
                        }
                    ).execute()
                    total_count += len(batch)
                    
            logger.info(f"Successfully saved {total_count} kdata records")
            return total_count
            
        except Exception as e:
            logger.error(f"Error in batch saving kdata: {str(e)}")
            raise

    def update_meta_info(self, 
                        meta_type: MetaType,
                        security_type: SecurityType,
                        period: Period,
                        start_time: str,
                        end_time: str,
                        source: str = 'akshare',
                        table_name: str = 't_kdata') -> bool:
        """更新元数据信息"""
        try:
            meta_name = meta_type.value

            with main_db:
                # 查询现有的元信息记录
                existing_meta = T_Meta.select().where(
                    T_Meta.meta_name == meta_name
                ).first()
                
                # 合并时间范围
                if existing_meta:
                    merged_start = min(existing_meta.start_time, start_time)
                    merged_end = max(existing_meta.end_time, end_time)
                else:
                    merged_start = start_time
                    merged_end = end_time

                # 获取总数据量
                total_count = ModelRegister.get_model(DataSource.Akshare, table_name).select().count()

                current_time = int(time.time() * 1000)
                meta_data = {
                    'meta_name': meta_name,
                    'security_type': security_type.value,
                    'period': period.value,
                    'source': source,
                    'start_time': merged_start,
                    'end_time': merged_end,
                    'table_name': table_name,
                    'total_count': total_count,
                    'create_time': current_time,
                    'update_time': current_time
                }
                
                # 插入或更新元信息
                T_Meta.insert(**meta_data).on_conflict(
                    conflict_target=[T_Meta.meta_name],
                    action='UPDATE',
                    update={
                        T_Meta.start_time: SQL('EXCLUDED.start_time'),
                        T_Meta.end_time: SQL('EXCLUDED.end_time'),
                        T_Meta.total_count: SQL('EXCLUDED.total_count'),
                        T_Meta.update_time: SQL('EXCLUDED.update_time')
                    }
                ).execute()
                
                logger.info(
                    f"Successfully updated meta information for {meta_name}, "
                    f"security_type: {security_type.value}, "
                    f"period: {period.value}, "
                    f"source: {source}, "
                    f"start_time: {merged_start}, "
                    f"end_time: {merged_end}, "
                    f"table_name: {table_name}, "
                    f"total_count: {total_count}"
                )
                return True
            
        except Exception as e:
            logger.error(f"Error updating meta info: {str(e)}")
            return False
        
    def get_metadata(self, meta_type: MetaType) -> Optional[T_Meta_Model]:
        with main_db:
            meta_name = meta_type.value
            meta_info = T_Meta.select().where(
                T_Meta.meta_name == meta_name
            ).first()
            return meta_info
