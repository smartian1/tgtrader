# encoding utf-8

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Callable
import futu as ft
from futu import RET_OK
from tgtrader.gateway.futu.defs import AccountInfo, TradeEnv, \
    AccoutStatus, TradeAccType, SimAccountType, AccountCashInfo, \
        CurrencyType, AccountRiskLevel, AccountRiskStatus, DtStatus, \
            TradeMarket, PositionInfo, PositionSide, \
                OrderInfo, OrderType, OrderStatus, TimeInForce, TrailType, \
                    TradeSize
from loguru import logger

@dataclass
class FutuTradeGateway:
    host: str = "127.0.0.1"
    port: int = 11111
    conn: ft.OpenSecTradeContext = None

    
    def __post_init__(self):
        self.conn = ft.OpenSecTradeContext(filter_trdmarket=ft.TrdMarket.HK,host=self.host, port=self.port)
        logger.info("富途期权交易网关已初始化")
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("富途期权交易网关已关闭")

    def __enter__(self):
        """上下文管理器进入方法，确保连接已建立
        
        Returns:
            FutuTradeGateway: 当前实例
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出方法，确保关闭连接
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        self.close()

    def get_account_list(self, trd_env: TradeEnv=None) -> List[AccountInfo]:
        """获取账户列表
        
        Returns:
            List[AccountInfo]: 账户列表
        """
        ret, data = self.conn.get_acc_list()
        if ret != RET_OK:
            raise Exception(f"获取账户列表失败: {data}")
        
        result = []
        for _, row in data.iterrows():
            acc_status = AccoutStatus(row['acc_status'])
            if acc_status != AccoutStatus.ACTIVE:
                continue

            if trd_env and trd_env != TradeEnv(row['trd_env']):
                continue

            result.append(AccountInfo(
                acc_id=row['acc_id'],
                trd_env=TradeEnv(row['trd_env']),
                acc_type=TradeAccType(row['acc_type']),
                uni_card_num=row['uni_card_num'],
                card_num=row['card_num'],
                security_firm=row['security_firm'],
                sim_acc_type=SimAccountType(row['sim_acc_type']),
                trdmarket_authlist=[TradeMarket(x) for x in row['trdmarket_auth']],
                acc_status=AccoutStatus(row['acc_status'])
            ))
        
        return result

    def unlock_trade(self, pwd: str, is_unlock: bool) -> bool:
        """解锁交易密码
        
        Args:
            pwd: 解锁密码
            is_unlock: 是否解锁
        """
        ret, data = self.conn.unlock_trade(password=pwd, is_unlock=is_unlock)
        if ret != RET_OK:
            raise Exception(f"解锁交易密码失败: {data}")

        return True

    def get_account_cash_info_list(self, acc_id: int) -> AccountInfo:
        """查询账户资金信息
        
        Args:
            acc_id: 账户ID
        """
        ret, data = self.conn.accinfo_query(acc_id=acc_id, refresh_cache=False, currency=ft.Currency.HKD)
    
        if ret != RET_OK:
            raise Exception(f"获取账户资金信息失败: {data}")
        
        result = []
        for _, row in data.iterrows():
            result.append(AccountCashInfo(
                power=row['power'],
                max_power_short=row['max_power_short'],
                net_cash_power=row['net_cash_power'],
                total_assets=row['total_assets'],
                securities_assets=row['securities_assets'],
                funds_assets=row['fund_assets'],
                bonds_assets=row['bond_assets'],
                cash=row['cash'],
                market_val=row['market_val'],
                long_mv=row['long_mv'],
                short_mv=row['short_mv'],
                pending_asset=row['pending_asset'],
                interest_charged_amount=row['interest_charged_amount'],
                frozen_cash=row['frozen_cash'],
                avl_withdrawal_cash=row['avl_withdrawal_cash'],
                max_withdrawal=row['max_withdrawal'],
                currency=CurrencyType(row['currency']),
                available_funds=row['available_funds'],
                unrealized_pl=row['unrealized_pl'],
                realized_pl=row['realized_pl'],
                risk_level=AccountRiskLevel(row['risk_level']),
                risk_status=AccountRiskStatus(row['risk_status']),
                initial_margin=row['initial_margin'],
                margin_call_margin=row['margin_call_margin'],
                maintenance_margin=row['maintenance_margin'],
                hk_cash=row['hk_cash'],
                hk_avl_withdrawal_cash=row['hk_avl_withdrawal_cash'],
                hkd_net_cash_power=row['hkd_net_cash_power'],
                hkd_assets=row['hkd_assets'],
                us_cash=row['us_cash'],
                us_avl_withdrawal_cash=row['us_avl_withdrawal_cash'],
                usd_net_cash_power=row['usd_net_cash_power'],
                usd_assets=row['usd_assets'],
                cn_cash=row['cn_cash'],
                cn_avl_withdrawal_cash=row['cn_avl_withdrawal_cash'],
                cnh_net_cash_power=row['cnh_net_cash_power'],
                cnh_assets=row['cnh_assets'],
                is_pdt=row['is_pdt'],
                pdt_seq=row['pdt_seq'],
                beginning_dtbp=row['beginning_dtbp'],
                remaining_dtbp=row['remaining_dtbp'],
                dt_call_amount=row['dt_call_amount'],
                dt_status=DtStatus(row['dt_status'])
            ))
        
        return result

    def get_position_list(self, acc_id: int) -> List[PositionInfo]:
        """查询账户持仓
        
        Args:
            acc_id: 账户ID
        """
        ret, data = self.conn.position_list_query(acc_id=acc_id, refresh_cache=False)
    
        if ret != RET_OK:
            raise Exception(f"获取账户持仓失败: {data}")
        
        result = []
        for _, row in data.iterrows():
            result.append(PositionInfo(
                position_side=PositionSide(row['position_side']),
                code=row['code'],
                stock_name=row['stock_name'],
                position_market=TradeMarket(row['position_market']),
                qty=row['qty'],
                can_sell_qty=row['can_sell_qty'],
                currency=CurrencyType(row['currency']),
                nominal_price=row['nominal_price'],
                cost_price=row['cost_price'],
                cost_price_valid=row['cost_price_valid'],
                market_val=row['market_val'],
                pl_ratio=row['pl_ratio'],
                pl_ratio_valid=row['pl_ratio_valid'],
                pl_val=row['pl_val'],
                pl_val_valid=row['pl_val_valid'],
                today_pl_val=row['today_pl_val'],
                today_trd_val=row['today_trd_val'],
                today_buy_qty=row['today_buy_qty'],
                today_buy_val=row['today_buy_val'],
                today_sell_qty=row['today_sell_qty'],
                today_sell_val=row['today_sell_val'],
                unrealized_pl=row['unrealized_pl'],
                realized_pl=row['realized_pl']
            ))
        
        return result

    def get_history_order_list(self, acc_id: int) -> List[OrderInfo]:
        """查询账户订单
        
        Args:
            acc_id: 账户ID
        """
        ret, data = self.conn.history_order_list_query(acc_id=acc_id)
    
        if ret != RET_OK:
            raise Exception(f"获取账户订单失败: {data}")
        
        result = []
        for _, row in data.iterrows():
            result.append(OrderInfo(
                trd_side=TradeSize(row['trd_side']),
                order_type=OrderType(row['order_type']),
                order_status=OrderStatus(row['order_status']),
                order_id=str(row['order_id']),
                code=row['code'],
                stock_name=row['stock_name'],
                order_market=TradeMarket(row['order_market']),
                qty=float(row['qty']),
                price=float(row['price']),
                currency=CurrencyType(row['currency']),
                create_time=row['create_time'],
                updated_time=row['updated_time'],
                dealt_qty=float(row['dealt_qty']),
                dealt_avg_price=float(row['dealt_avg_price']),
                last_err_msg=row['last_err_msg'],
                remark=row.get('remark', ''),
                time_in_force=TimeInForce(row.get('time_in_force', 'DAY')),
                fill_outside_rth=bool(row.get('fill_outside_rth', False)),
                aux_price=float(row.get('aux_price', 0.0)) if row.get('aux_price') != 'N/A' else 0.0,
                trail_type=TrailType(row.get('trail_type', 'N/A')),
                trail_value=float(row.get('trail_value', 0.0)) if row.get('trail_value') != 'N/A' else 0.0,
                trail_spread=float(row.get('trail_spread', 0.0)) if row.get('trail_spread') != 'N/A' else 0.0
            ))
        
        return result

    def query_orders_not_finished(self, acc_id: int) -> List[OrderInfo]:
        ret, data = self.conn.order_list_query(acc_id=acc_id)
    
        if ret != RET_OK:
            raise Exception(f"获取账户订单失败: {data}")
        
        result = []
        for _, row in data.iterrows():
            result.append(OrderInfo(
                trd_side=TradeSize(row['trd_side']),
                order_type=OrderType(row['order_type']),
                order_status=OrderStatus(row['order_status']),
                order_id=str(row['order_id']),
                code=row['code'],
                stock_name=row['stock_name'],
                order_market=TradeMarket(row['order_market']),
                qty=float(row['qty']),
                price=float(row['price']),
                currency=CurrencyType(row['currency']),
                create_time=row['create_time'],
                updated_time=row['updated_time'],
                dealt_qty=float(row['dealt_qty']),
                dealt_avg_price=float(row['dealt_avg_price']),
                last_err_msg=row['last_err_msg'],
                remark=row.get('remark', ''),
                time_in_force=TimeInForce(row.get('time_in_force', 'DAY')),
                fill_outside_rth=bool(row.get('fill_outside_rth', False)),
                aux_price=float(row.get('aux_price', 0.0)) if row.get('aux_price') != 'N/A' else 0.0,
                trail_type=TrailType(row.get('trail_type', 'N/A')),
                trail_value=float(row.get('trail_value', 0.0)) if row.get('trail_value') != 'N/A' else 0.0,
                trail_spread=float(row.get('trail_spread', 0.0)) if row.get('trail_spread') != 'N/A' else 0.0
            ))
        
        return result

    def place_order(self, acc_id: int,
                    code: str,
                    qty: float,
                    price: float,
                    trd_side: ft.TrdSide,
                    order_type: OrderType = ft.OrderType.NORMAL
                    ) -> OrderInfo:
        """下单
        
        Args:
            acc_id: 账户ID
            code: 证券代码
            qty: 下单数量
            price: 下单价格
            trd_side: 交易方向
            order_type: 订单类型
        """

        ret, data = self.conn.place_order(acc_id=acc_id,
                                          code=code,
                                          qty=qty,
                                          price=price,
                                          trd_side=trd_side,
                                          order_type=order_type)

        if ret != RET_OK:
            raise Exception(f"下单失败: {data}")
        
        result = []
        for _, row in data.iterrows():
            result.append(OrderInfo(
                trd_side=TrdSide(row['trd_side']),
                order_type=OrderType(row['order_type']),
                order_status=OrderStatus(row['order_status']),
                order_id=str(row['order_id']),
                code=row['code'],
                stock_name=row['stock_name'],
                order_market=TradeMarket(row['order_market']),
                qty=float(row['qty']),
                price=float(row['price']),
                currency=CurrencyType(row['currency']),
                create_time=row['create_time'],
                updated_time=row['updated_time'],
                dealt_qty=float(row['dealt_qty']),
                dealt_avg_price=float(row['dealt_avg_price']),
                last_err_msg=row['last_err_msg'],
                remark=row.get('remark', ''),
                time_in_force=TimeInForce(row.get('time_in_force', 'DAY')),
                fill_outside_rth=bool(row.get('fill_outside_rth', False)),
                aux_price=float(row.get('aux_price', 0.0)) if row.get('aux_price') != 'N/A' else 0.0,
                trail_type=TrailType(row.get('trail_type', 'N/A')),
                trail_value=float(row.get('trail_value', 0.0)) if row.get('trail_value') != 'N/A' else 0.0,
                trail_spread=float(row.get('trail_spread', 0.0)) if row.get('trail_spread') != 'N/A' else 0.0
            ))
        
        return result