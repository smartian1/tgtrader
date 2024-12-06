# encoding: utf-8

import akshare as ak
import pandas as pd
from loguru import logger
from tqdm import tqdm

from tgtrader.common import Period, DataProvider, PriceAdjust, SecurityType

class AkshareDataProvider(DataProvider):
    def __init__(self):
        # 字段名映射：标准英文名到akshare中文列名的映射
        self.field_map = {
            "date": "日期",
            "open": "开盘",
            "high": "最高",
            "low": "最低",
            "close": "收盘",
            "volume": "成交量",
            "amount": "成交额"
        }
        
        # Period枚举到akshare的period字符串的映射
        self.period_map = {
            Period.Day: "daily",
            Period.Week: "weekly",
            Period.Month: "monthly"
        }
        
        # 复权参数映射
        self.adjust_map = {
            PriceAdjust.HFQ: "hfq",
            PriceAdjust.QFQ: "qfq",
            PriceAdjust.NO: ""
        }

    def get_data(self, 
                 symbol_list: list[str], 
                 start_date: str, 
                 end_date: str, 
                 period: Period = Period.Day, 
                 adjust: PriceAdjust = PriceAdjust.HFQ, 
                 fields: list[str] = ["open", "high", "low", "close", "volume"],
                 security_type: SecurityType = SecurityType.ETF):
        """获取证券数据，支持ETF和股票
        
        Args:
            symbol_list: 证券代码列表
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            period: 周期，默认为日线数据
            adjust: 复权方式，默认为后复权
            fields: 需要的字段列表
            security_type: 证券类型，默认为ETF
            
        Returns:
            DataFrame with MultiIndex(code, date)
        """
        fields = ["date"] + fields
        
        try:
            if security_type == SecurityType.ETF:
                return self._get_etf_data(symbol_list, start_date, end_date, 
                                        period, adjust, fields)
            elif security_type == SecurityType.Stocks:
                return self._get_stock_data(symbol_list, start_date, end_date, 
                                          period, adjust, fields)
            else:
                logger.error(f"Unsupported security type: {security_type}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()

    def _get_etf_data(self, symbol_list, start_date, end_date, period, adjust, fields):
        """获取ETF数据"""
        all_dfs = []
        
        for symbol in tqdm(symbol_list, desc="Fetching ETF data"):
            try:
                df = ak.fund_etf_hist_em(
                    symbol=symbol,
                    period=self.period_map[period],
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust=self.adjust_map[adjust]
                )
                
                if df is None or df.empty:
                    logger.warning(f"No data found for ETF: {symbol}")
                    continue
                    
                # 重命名列并选择所需字段
                df = df.rename(columns={v: k for k, v in self.field_map.items()})
                df = df[fields]
                df['code'] = symbol
                all_dfs.append(df)
                
            except Exception as e:
                logger.error(f"Error fetching ETF {symbol}: {str(e)}")
                continue
        
        return self._process_combined_data(all_dfs)

    def _get_stock_data(self, symbol_list, start_date, end_date, period, adjust, fields):
        """获取股票数据"""
        all_dfs = []
        
        for symbol in tqdm(symbol_list, desc="Fetching stock data"):
            try:
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period=self.period_map[period],
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust=self.adjust_map[adjust]
                )
                
                if df is None or df.empty:
                    logger.warning(f"No data found for stock: {symbol}")
                    continue
                    
                df = df.rename(columns={v: k for k, v in self.field_map.items()})
                df = df[fields]
                df['code'] = symbol
                all_dfs.append(df)
                
            except Exception as e:
                logger.error(f"Error fetching stock {symbol}: {str(e)}")
                continue
        
        return self._process_combined_data(all_dfs)

    def _process_combined_data(self, all_dfs):
        """处理合并后的数据"""
        if not all_dfs:
            return pd.DataFrame()
            
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        if combined_df.empty:
            return pd.DataFrame()

        combined_df['date'] = pd.to_datetime(combined_df['date'])
        combined_df = combined_df.set_index(['code', 'date'])
        
        return combined_df

    def standardize_symbol(self, symbol: str):
        """标准化证券代码格式"""
        return symbol