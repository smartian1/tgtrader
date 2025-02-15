# encoding: utf-8

import futu as ft
from dataclasses import dataclass
from loguru import logger
from futu import *
from tgtrader.gateway.futu.defs import SecurityType, \
    OptionType, IndexOptionType, StockPriceSnapshot, \
    FutuOptionAreaType
import time
from typing import List, Callable
from dataclasses import field
from loguru import logger


@dataclass
class FutuStockGateway:
    """
    富途股票网关
    """
    host: str = "127.0.0.1"
    port: int = 11111
    conn: ft.OpenQuoteContext = None

    def __post_init__(self):
        self.conn = ft.OpenQuoteContext(host=self.host, port=self.port)

    def get_stock_snapshot(self, code_list: List[str]) -> List[StockPriceSnapshot]:
        """获取标的实时报价数据
        
        Args:
            code_list: List[str], 标的代码列表，例如 ['HK.00700', 'HK.09988']
            
        Returns:
            List[StockPriceSnapshot]: 股票实时报价数据对象列表，与输入的code_list顺序一致
                
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        if not self.conn:
            raise Exception("行情接口未连接")

        # 富途API限制每次最多查询1000个股票
        MAX_CODES_PER_BATCH = 1000
        result = []

        try:
            # 将code_list按MAX_CODES_PER_BATCH大小分批处理
            for i in range(0, len(code_list), MAX_CODES_PER_BATCH):
                batch_codes = code_list[i:i + MAX_CODES_PER_BATCH]

                # 获取实时报价
                ret, data = self.conn.get_market_snapshot(batch_codes)
                if ret != RET_OK:
                    raise Exception(f"获取实时报价失败: {data}")

                if len(data) == 0:
                    logger.warning(f"未获取到{batch_codes}的报价数据")
                    continue

                # 处理每个股票的数据
                for _, quote in data.iterrows():
                    try:
                        snapshot = StockPriceSnapshot(
                            code=str(quote['code']),
                            name=str(quote['name']),
                            last_price=float(quote['last_price']),
                            open_price=float(quote['open_price']),
                            high_price=float(quote['high_price']),
                            low_price=float(quote['low_price']),
                            prev_close_price=float(quote['prev_close_price']),
                            volume=int(quote['volume']),
                            turnover=float(quote['turnover']),
                            turnover_rate=float(quote.get('turnover_rate', 0)),
                            amplitude=float(quote.get('amplitude', 0)),
                            suspension=bool(quote.get('suspension', False)),
                            update_time=str(quote.get('update_time', '')),
                            bid_price=float(quote['bid_price'] if quote['bid_price'] != 'N/A' else 0),
                            ask_price=float(quote['ask_price'] if quote['ask_price'] != 'N/A' else 0),
                            bid_vol=int(quote['bid_vol'] if quote['bid_vol'] != 'N/A' else 0),
                            ask_vol=int(quote['ask_vol'] if quote['ask_vol'] != 'N/A' else 0)
                        )
                        result.append(snapshot)
                    except Exception as e:
                        logger.warning(
                            f"处理股票{quote.get('code', 'unknown')}数据异常: {str(e)}")
                        continue

                # 如果不是最后一批，加入适当延时避免频率限制
                if i + MAX_CODES_PER_BATCH < len(code_list):
                    time.sleep(0.5)  # 500ms延时

            return result

        except Exception as e:
            logger.error(f"获取实时报价异常: {str(e)}")
            raise e
