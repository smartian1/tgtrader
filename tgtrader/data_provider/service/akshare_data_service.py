# encoding: utf-8
from typing import List, Optional
import pandas as pd
from tqdm import tqdm
from loguru import logger
import time

from tgtrader.data_provider.dao.akshare.common import main_db
from tgtrader.data_provider.dao.akshare.t_kdata import T_KData
from tgtrader.data_provider.dao.akshare.t_meta import T_Meta
from tgtrader.common import SecurityType, Period, PriceAdjust
from tgtrader.data_provider.service.data_service import DataService

class AkshareDataService(DataService):
    """Akshare数据服务实现类"""

    @classmethod
    def init_data(cls):
        """初始化数据"""
        with main_db:
            main_db.create_tables([T_Meta, T_KData])

    def batch_save_kdata(self,
                        data: Optional[pd.DataFrame] = None,
                        adjust: Optional[PriceAdjust] = None,
                        source: str = 'akshare',
                        batch_size: int = 1000) -> int:
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
            
            with main_db:
                # 使用tqdm显示进度
                for i in tqdm(range(0, len(data_list), batch_size), 
                            desc="Saving kdata"):
                    batch = data_list[i:i + batch_size]
                    rows = T_KData.insert_many(batch).on_conflict(
                        conflict_target=[T_KData.code, T_KData.date, T_KData.source],
                        action='UPDATE',
                        update={
                            T_KData.open: T_KData.open,
                            T_KData.high: T_KData.high,
                            T_KData.low: T_KData.low,
                            T_KData.close: T_KData.close,
                            T_KData.volume: T_KData.volume,
                            T_KData.adjust_type: T_KData.adjust_type,
                            T_KData.update_time: T_KData.update_time
                        }
                    ).execute()
                    total_count += len(batch)
                    
            logger.info(f"Successfully saved {total_count} kdata records")
            return total_count
            
        except Exception as e:
            logger.error(f"Error in batch saving kdata: {str(e)}")
            raise

    def update_meta_info(self, 
                        meta_name: str,
                        security_type: SecurityType,
                        period: Period,
                        start_time: str,
                        end_time: str,
                        source: str = 'akshare',
                        table_name: str = 't_kdata') -> bool:
        """更新元数据信息"""
        try:
            meta_name = meta_name
            
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

            current_time = int(time.time() * 1000)
            meta_data = {
                'meta_name': meta_name,
                'security_type': security_type.value,
                'period': period.value,
                'source': source,
                'start_time': merged_start,
                'end_time': merged_end,
                'table_name': table_name,
                'create_time': current_time,
                'update_time': current_time
            }
            
            # 插入或更新元信息
            T_Meta.insert(**meta_data).on_conflict(
                conflict_target=[T_Meta.meta_name],
                action='UPDATE',
                update={
                    T_Meta.start_time: meta_data['start_time'],
                    T_Meta.end_time: meta_data['end_time'],
                    T_Meta.update_time: meta_data['update_time']
                }
            ).execute()
            
            logger.info(
                f"Successfully updated meta information for {meta_name}, "
                f"security_type: {security_type.value}, "
                f"period: {period.value}, "
                f"source: {source}, "
                f"start_time: {merged_start}, "
                f"end_time: {merged_end}, "
                f"table_name: {table_name}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error updating meta info: {str(e)}")
            return False