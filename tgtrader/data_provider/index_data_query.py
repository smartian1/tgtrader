# encoding: utf-8

import requests
import pandas as pd
from loguru import logger

class IndexDataQuery:
    """
    指数数据查询类，用于从API获取指数数据
    """
    def __init__(self):
        """
        初始化指数数据查询类
        """
        self.base_url = "https://1312195675-46i1pku1mn.ap-guangzhou.tencentscf.com"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def get_index_data(self, code: str, start_time: str, end_time: str) -> pd.DataFrame:
        """
        获取指数数据
        
        Args:
            code: 指数代码，例如 "smb"
            start_time: 开始时间，格式为 "YYYY-MM-DD"
            end_time: 结束时间，格式为 "YYYY-MM-DD"
            
        Returns:
            包含指数数据的DataFrame，列包括：code, name, data_time, value, create_time, update_time, id
        """
        try:
            # 构建请求数据
            payload = {
                "code": code,
                "start_time": start_time,
                "end_time": end_time
            }
            
            # 发送请求
            logger.info(f"Fetching index data for code={code}, start_time={start_time}, end_time={end_time}")
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应数据
            data = response.json()

            if not data:
                logger.warning(f"No data returned for code={code}")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 转换时间列
            if 'data_time' in df.columns:
                df['data_time'] = pd.to_datetime(df['data_time'])
            
            # 转换时间戳列
            for col in ['create_time', 'update_time']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col].astype(float), unit='ms')
            
            logger.info(f"Successfully fetched {len(df)} records for code={code}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse response data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
