# encoding: utf-8

import futu as ft
from dataclasses import dataclass
from loguru import logger
from futu import *
from tgtrader.gateway.futu.defs import SecurityType, \
    OptionType, IndexOptionType, StockPriceSnapshot, \
        StockQuote, StockOrderBook, OptionChainItem, \
            OptionExpirationDate, OptionExpirationCycle, \
                FutuOptionAreaType
import time
from typing import List, Callable
from dataclasses import field
from loguru import logger


@dataclass
class FutuOptionGateway:
    """
    富途期权网关
    """
    host: str = "127.0.0.1"
    port: int = 11111
    conn: ft.OpenQuoteContext = None
    quote_subscribe_list: List[str] = field(default_factory=list)
    order_subscribe_list: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.conn = ft.OpenQuoteContext(host=self.host, port=self.port)

    def get_option_expiration_date(self, code: str) -> list:
        """
        获取期权到期日
        """
        ret, data = self.conn.get_option_expiration_date(code)
        if ret != RET_OK:
            raise Exception(f"获取期权到期日失败: {data}")
        
        ret = []
        for _, row in data.iterrows():
            ret.append(OptionExpirationDate(
                strike_time=row['strike_time'],
                option_expiry_date_distance=row['option_expiry_date_distance'],
                expiration_cycle=OptionExpirationCycle(row['expiration_cycle'])
            ))
        return ret
    
    def get_option_chain(self, code: str, date: str) -> List[OptionChainItem]:
        """获取期权链数据
        
        Args:
            code: 标的代码，例如 'HK.00700' 为腾讯控股
            date: 期权到期日，格式为 'YYYY-MM-DD'
            
        Returns:
            List[OptionChainItem]: 期权链数据列表
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        # 检查API连接状态
        if not self.conn:
            raise Exception("行情接口未连接")
        
        try:
            # 获取期权链基础数据
            ret, data = self.conn.get_option_chain(code, start=date, end=date)
            if ret != RET_OK:
                raise Exception(f"获取期权链失败: {data}")
            
            result = []
            for _, row in data.iterrows():
                # 转换期权类型
                opt_type = (OptionType.CALL if row['option_type'] == 'CALL' 
                           else OptionType.PUT)
                
                # 创建期权链项
                item = OptionChainItem(
                    code=row['code'],  # 期权代码
                    name=row['name'],  # 期权名称
                    lot_size=int(row['lot_size']),  # 每手数量
                    stock_type=SecurityType(row['stock_type']),  # 证券类型
                    option_type=OptionType(row['option_type']),  # 期权类型（认购/认沽）
                    stock_owner=row['stock_owner'],  # 标的代码
                    strike_time=row['strike_time'],  # 到期日
                    strike_price=float(row['strike_price']),  # 行权价
                    suspension=bool(row.get('suspension', False)),  # 是否停牌
                    stock_id=int(row.get('stock_id', 0)),  # 股票ID
                    index_option_type=IndexOptionType(row.get('index_option_type', 'NONE'))  # 指数期权类型，暂不支持
                )
                result.append(item)
            
            return result
        
        except Exception as e:
            logger.error(f"获取期权链异常: {str(e)}")
            raise e

    
    def get_option_snapshot(self, code_list: List[str]) -> List[StockPriceSnapshot]:
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
            
        # 富途API限制每次最多查询400个股票
        MAX_CODES_PER_BATCH = 400
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
                            bid_price=float(quote['bid_price']),
                            ask_price=float(quote['ask_price']),
                            bid_vol=int(quote['bid_vol']),
                            ask_vol=int(quote['ask_vol']),
                            option_valid=bool(quote.get('option_valid', False)),
                            option_type=OptionType(quote.get('option_type', 'NONE')),
                            strike_time=str(quote.get('strike_time', '')),
                            option_strike_price=float(quote.get('option_strike_price', 0)),
                            option_contract_size=float(quote.get('option_contract_size', 0)),
                            option_open_interest=int(quote.get('option_open_interest', 0)),
                            option_implied_volatility=float(quote.get('option_implied_volatility', 0)),
                            option_premium=float(quote.get('option_premium', 0)),
                            option_delta=float(quote.get('option_delta', 0)),
                            option_gamma=float(quote.get('option_gamma', 0)),
                            option_vega=float(quote.get('option_vega', 0)),
                            option_theta=float(quote.get('option_theta', 0)),
                            option_rho=float(quote.get('option_rho', 0)),
                            index_option_type=IndexOptionType(quote.get('index_option_type', 'NONE')),
                            option_net_open_interest=int(quote.get('option_net_open_interest', 0)),
                            option_expiry_date_distance=int(quote.get('option_expiry_date_distance', 0)),
                            option_contract_nominal_value=float(quote.get('option_contract_nominal_value', 0)),
                            option_owner_lot_multiplier=float(quote.get('option_owner_lot_multiplier', 0)),
                            option_area_type=FutuOptionAreaType(quote.get('option_area_type', 'NONE')),
                            option_contract_multiplier=float(quote.get('option_contract_multiplier', 0))
                        )
                        result.append(snapshot)
                    except Exception as e:
                        logger.warning(f"处理股票{quote.get('code', 'unknown')}数据异常: {str(e)}")
                        continue
                
                # 如果不是最后一批，加入适当延时避免频率限制
                if i + MAX_CODES_PER_BATCH < len(code_list):
                    time.sleep(0.5)  # 500ms延时
            
            return result
            
        except Exception as e:
            logger.error(f"获取实时报价异常: {str(e)}")
            raise e
    
    def subscribe_option_quote(self, code_list: List[str], call_back: Callable):
        """获取期权实时报价数据
        
        Args:
            code_list: 期权代码列表，例如 ['HK.09988C2.500']
            
        Returns:
            List[StockPriceSnapshot]: 期权实时报价数据对象列表，与输入的code_list顺序一致
                
        Raises:
            Exception: 当API调用失败或行情接口未连接时抛出异常
        """
        # 检查API连接状态
        if not self.conn:
            raise Exception("行情接口未连接")

        class QuoteHandler(StockQuoteHandlerBase):
            def on_recv_rsp(self, rsp_pb):
                ret_code, data = super(QuoteHandler, self).on_recv_rsp(rsp_pb)
                if ret_code != RET_OK:
                    logger.error("行情回调失败: %s" % data)
                    return RET_ERROR, data
                
                result = []
                for _, quote in data.iterrows():
                    try:
                        snapshot = StockQuote(
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
                            suspension=bool(quote.get('suspension', False)),
                            strike_price=float(
                                quote.get('option_strike_price', 0)),
                            contract_size=float(
                                quote.get('option_contract_size', 0)),
                            open_interest=int(
                                quote.get('option_open_interest', 0)),
                            implied_volatility=float(
                                quote.get('option_implied_volatility', 0)),
                            premium=float(quote.get('option_premium', 0)),
                            delta=float(quote.get('option_delta', 0)),
                            gamma=float(quote.get('option_gamma', 0)),
                            vega=float(quote.get('option_vega', 0)),
                            theta=float(quote.get('option_theta', 0)),
                            rho=float(quote.get('option_rho', 0)),
                            index_option_type=IndexOptionType(
                                quote.get('index_option_type', 'NONE')),
                            net_open_interest=int(
                                quote.get('option_net_open_interest', 0)),
                            expiry_date_distance=int(
                                quote.get('option_expiry_date_distance', 0)),
                            contract_nominal_value=float(
                                quote.get('option_contract_nominal_value', 0)),
                            owner_lot_multiplier=float(
                                quote.get('option_owner_lot_multiplier', 0)),
                            option_area_type=FutuOptionAreaType(
                                quote.get('option_area_type', 'NONE')),
                            contract_multiplier=float(
                                quote.get('option_contract_multiplier', 0)),
                            data_time=str(quote.get('data_time', '')),
                            data_date=str(quote.get('data_date', ''))
                        )
                        result.append(snapshot)
                    except Exception as e:
                        logger.warning(
                            f"处理期权{quote.get('code', 'unknown')}数据异常: {str(e)}")
                        continue

                call_back(result)

                return RET_OK, data
        
        self.conn.set_handler(QuoteHandler())

        # 检查是否已经订阅过这些期权代码
        new_codes = [
            code for code in code_list if code not in self.quote_subscribe_list]

        # 如果没有新的代码需要订阅，直接返回
        if not new_codes:
            logger.info("所有期权代码已经订阅过，无需重复订阅")
            return

        # 订阅新的期权代码
        ret, data = self.conn.subscribe(
            new_codes, [SubType.QUOTE], subscribe_push=True)
        if ret != RET_OK:
            raise Exception(f"订阅期权实时报价失败: {data}")

        # 更新已订阅列表
        self.quote_subscribe_list.extend(new_codes)
    
    def subscribe_order_book(self, code_list: List[str], call_back: Callable):
        """获取标的实时订单簿数据
        
        Args:
            code: str, 标的代码，例如 'HK.00700'
            
        Returns:
            StockOrderBook: 股票订单簿数据对象，包含买卖盘的详细信息
                
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        if not self.conn:
            raise Exception("行情接口未连接")
        
        class OrderBookHandler(OrderBookHandlerBase):
            def on_recv_rsp(self, rsp_pb):
                ret_code, data = super(OrderBookHandler, self).on_recv_rsp(rsp_pb)
                if ret_code != RET_OK:
                    logger.error("订单簿回调失败: %s" % data)
                    return RET_ERROR, data
                
                order_book = StockOrderBook(
                    code=data['code'],
                    name=data['name'],
                    svr_recv_time_bid=data['svr_recv_time_bid'],
                    svr_recv_time_ask=data['svr_recv_time_ask'],
                    bid_orders=data['Bid'],
                    ask_orders=data['Ask']
                )

                call_back(order_book)
                return RET_OK, data
            
        self.conn.set_handler(OrderBookHandler())

        # 检查是否已经订阅过这些期权代码
        new_codes = [
            code for code in code_list if code not in self.order_subscribe_list]

        # 如果没有新的代码需要订阅，直接返回
        if not new_codes:
            logger.info("所有期权代码已经订阅过，无需重复订阅")
            return

        # 订阅新的期权代码
        ret, data = self.conn.subscribe(
            new_codes, [SubType.ORDER_BOOK], subscribe_push=True)
        if ret != RET_OK:
            raise Exception(f"订阅订单簿失败: {data}")

        # 更新已订阅列表
        self.order_subscribe_list.extend(new_codes)
            