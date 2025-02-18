# encoding: utf-8

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple


class SecurityType(Enum):
    """富途证券类型枚举"""
    NONE = "NONE"  # 未知
    BOND = "BOND"  # 债券
    BWRT = "BWRT"  # 一揽子权证
    STOCK = "STOCK"  # 正股
    ETF = "ETF"  # 信托,基金
    WARRANT = "WARRANT"  # 窝轮
    IDX = "IDX"  # 指数
    PLATE = "PLATE"  # 板块
    DRVT = "DRVT"  # 期权
    PLATESET = "PLATESET"  # 板块集
    FUTURE = "FUTURE"  # 期货

    
class OptionType(Enum):
    """富途期权类型枚举"""
    NONE = "NONE"  # 未知类型
    CALL = "CALL"  # 认购期权
    PUT = "PUT"  # 认沽期权

class OptionCondType(Enum):
    """富途期权条件类型枚举

    描述期权的条件类型，包括全部、价内和价外
    """
    ALL = "ALL"  # 所有期权
    WITHIN = "WITHIN"  # 价内期权
    OUTSIDE = "OUTSIDE"  # 价外期权


class IndexOptionType(Enum):
    """富途指数期权类型枚举

    描述不同类型的指数期权
    """
    NONE = "N/A"  # 未知类型
    NORMAL = "NORMAL"  # 普通的指数期权
    SMALL = "SMALL"  # 小型指数期权

class PriceType(Enum):
    """富途价格类型枚举

    描述期权和界内证的价格相对关系的枚举类型
    """
    UNKNOWN = "UNKNOWN"  # 未知价格类型
    OUTSIDE = "OUTSIDE"  # 价外，界内证表示界外
    WITH_IN = "WITH_IN"  # 价内，界内证表示界内


class SecurityStatus(Enum):
    """富途证券状态枚举

    描述证券在不同交易阶段和状态的枚举类型
    """
    NONE = "NONE"  # 未知状态
    NORMAL = "NORMAL"  # 正常状态
    LISTING = "LISTING"  # 待上市
    PURCHASING = "PURCHASING"  # 申购中
    SUBSCRIBING = "SUBSCRIBING"  # 认购中
    BEFORE_DRAK_TRADE_OPENING = "BEFORE_DRAK_TRADE_OPENING"  # 暗盘开盘前
    DRAK_TRADING = "DRAK_TRADING"  # 暗盘交易中
    DRAK_TRADE_END = "DRAK_TRADE_END"  # 暗盘已收盘
    TO_BE_OPEN = "TO_BE_OPEN"  # 待开盘
    SUSPENDED = "SUSPENDED"  # 停牌
    CALLED = "CALLED"  # 已收回
    EXPIRED_LAST_TRADING_DATE = "EXPIRED_LAST_TRADING_DATE"  # 已过最后交易日
    EXPIRED = "EXPIRED"  # 已过期
    DELISTED = "DELISTED"  # 已退市
    CHANGE_TO_TEMPORARY_CODE = "CHANGE_TO_TEMPORARY_CODE"  # 公司行动中，交易关闭，转至临时代码交易
    TEMPORARY_CODE_TRADE_END = "TEMPORARY_CODE_TRADE_END"  # 临时买卖结束，交易关闭
    CHANGED_PLATE_TRADE_END = "CHANGED_PLATE_TRADE_END"  # 已转板，旧代码交易关闭
    CHANGED_CODE_TRADE_END = "CHANGED_CODE_TRADE_END"  # 已换代码，旧代码交易关闭
    RECOVERABLE_CIRCUIT_BREAKER = "RECOVERABLE_CIRCUIT_BREAKER"  # 可恢复性熔断
    UN_RECOVERABLE_CIRCUIT_BREAKER = "UN_RECOVERABLE_CIRCUIT_BREAKER"  # 不可恢复性熔断
    AFTER_COMBINATION = "AFTER_COMBINATION"  # 盘后撮合
    AFTER_TRANSATION = "AFTER_TRANSATION"  # 盘后交易

class AssetClass(Enum):
    """富途资产类别枚举

    描述不同类型的金融资产类别
    """
    UNKNOWN = "UNKNOWN"  # 未知资产类别
    STOCK = "STOCK"  # 股票
    BOND = "BOND"  # 债券
    COMMODITY = "COMMODITY"  # 商品
    CURRENCY_MARKET = "CURRENCY_MARKET"  # 货币市场
    FUTURE = "FUTURE"  # 期货
    SWAP = "SWAP"  # 掉期（互换）

class WrtType(Enum):
    """富途窝轮类型枚举

    描述不同类型的窝轮（权证）
    """
    NONE = "NONE"  # 未知
    CALL = "CALL"  # 认购窝轮
    PUT = "PUT"  # 认沽窝轮
    BULL = "BULL"  # 牛证
    BEAR = "BEAR"  # 熊证
    INLINE = "INLINE"  # 界内证

class FutuOptionAreaType(Enum):
    """富途期权区域类型枚举

    描述期权的行权时间和方式的枚举类型
    """
    NONE = "NONE"  # 未知
    AMERICAN = "AMERICAN"  # 美式
    EUROPEAN = "EUROPEAN"  # 欧式
    BERMUDA = "BERMUDA"  # 百慕大

class DarkStatus(Enum):
    """富途暗盘交易状态枚举

    描述股票在暗盘交易阶段的不同状态
    """
    NONE = "NONE"  # 无暗盘交易
    TRADING = "TRADING"  # 暗盘交易中
    END = "END"  # 暗盘交易结束

class OptionExpirationCycle(Enum):
    """富途期权到期周期枚举

    描述期权的不同到期周期类型
    """
    NONE = 'N/A'  # 未知
    WEEK = "WEEK"  # 周期权
    MONTH = "MONTH"  # 月期权
    ENDOFMONTH = 'END_OF_MONTH'
    QUARTERLY = 'QUARTERLY'


@dataclass
class StockPriceSnapshot:
    """富途股票快照数据类

    包含股票的详细市场信息和各项财务指标
    """
    code: str  # 股票代码
    name: str  # 股票名称
    update_time: Optional[str] = None  # 当前价更新时间
    last_price: Optional[float] = None  # 最新价格
    open_price: Optional[float] = None  # 今日开盘价
    high_price: Optional[float] = None  # 最高价格
    low_price: Optional[float] = None  # 最低价格
    prev_close_price: Optional[float] = None  # 昨收盘价格
    volume: Optional[int] = None  # 成交数量
    turnover: Optional[float] = None  # 成交金额
    turnover_rate: Optional[float] = None  # 换手率
    suspension: Optional[bool] = None  # 是否停牌
    listing_date: Optional[str] = None  # 上市日期
    equity_valid: Optional[bool] = None  # 是否正股
    issued_shares: Optional[int] = None  # 总股本
    total_market_val: Optional[float] = None  # 总市值
    net_asset: Optional[int] = None  # 资产净值
    net_profit: Optional[int] = None  # 净利润
    earning_per_share: Optional[float] = None  # 每股盈利
    outstanding_shares: Optional[int] = None  # 流通股本
    net_asset_per_share: Optional[float] = None  # 每股净资产
    circular_market_val: Optional[float] = None  # 流通市值
    ey_ratio: Optional[float] = None  # 收益率
    pe_ratio: Optional[float] = None  # 市盈率
    pb_ratio: Optional[float] = None  # 市净率
    pe_ttm_ratio: Optional[float] = None  # 市盈率 TTM
    dividend_ttm: Optional[float] = None  # 股息 TTM，派息
    dividend_ratio_ttm: Optional[float] = None  # 股息率 TTM
    dividend_lfy: Optional[float] = None  # 股息 LFY，上一年度派息
    dividend_lfy_ratio: Optional[float] = None  # 股息率 LFY
    stock_owner: Optional[str] = None  # 窝轮所属正股的代码或期权的标的股代码
    wrt_valid: Optional[bool] = None  # 是否是窝轮
    wrt_conversion_ratio: Optional[float] = None  # 换股比率
    wrt_type: Optional[WrtType] = None  # 窝轮类型
    wrt_strike_price: Optional[float] = None  # 行使价格
    wrt_maturity_date: Optional[str] = None  # 格式化窝轮到期时间
    wrt_end_trade: Optional[str] = None  # 格式化窝轮最后交易时间
    wrt_leverage: Optional[float] = None  # 杠杆比率
    wrt_ipop: Optional[float] = None  # 价内/价外
    wrt_break_even_point: Optional[float] = None  # 打和点
    wrt_conversion_price: Optional[float] = None  # 换股价
    wrt_price_recovery_ratio: Optional[float] = None  # 正股距收回价
    wrt_score: Optional[float] = None  # 窝轮综合评分
    wrt_recovery_price: Optional[float] = None  # 窝轮收回价
    wrt_street_vol: Optional[float] = None  # 窝轮街货量
    wrt_issue_vol: Optional[float] = None  # 窝轮发行量
    wrt_street_ratio: Optional[float] = None  # 窝轮街货占比
    wrt_delta: Optional[float] = None  # 窝轮对冲值
    wrt_implied_volatility: Optional[float] = None  # 窝轮引伸波幅
    wrt_premium: Optional[float] = None  # 窝轮溢价
    wrt_upper_strike_price: Optional[float] = None  # 上限价
    wrt_lower_strike_price: Optional[float] = None  # 下限价
    wrt_inline_price_status: Optional[PriceType] = None  # 界内界外
    wrt_issuer_code: Optional[str] = None  # 发行人代码
    option_valid: Optional[bool] = None  # 是否是期权
    option_type: Optional[OptionType] = None  # 期权类型
    strike_time: Optional[str] = None  # 期权行权日
    option_strike_price: Optional[float] = None  # 行权价
    option_contract_size: Optional[float] = None  # 每份合约数
    option_open_interest: Optional[int] = None  # 总未平仓合约数
    option_implied_volatility: Optional[float] = None  # 隐含波动率
    option_premium: Optional[float] = None  # 溢价
    option_delta: Optional[float] = None  # 希腊值 Delta
    option_gamma: Optional[float] = None  # 希腊值 Gamma
    option_vega: Optional[float] = None  # 希腊值 Vega
    option_theta: Optional[float] = None  # 希腊值 Theta
    option_rho: Optional[float] = None  # 希腊值 Rho
    index_option_type: Optional[IndexOptionType] = None  # 指数期权类型
    option_net_open_interest: Optional[int] = None  # 净未平仓合约数
    option_expiry_date_distance: Optional[int] = None  # 距离到期日天数
    option_contract_nominal_value: Optional[float] = None  # 合约名义金额
    option_owner_lot_multiplier: Optional[float] = None  # 相等正股手数
    option_area_type: Optional[FutuOptionAreaType] = None  # 期权类型（按行权时间）
    option_contract_multiplier: Optional[float] = None  # 合约乘数
    plate_valid: Optional[bool] = None  # 是否为板块类型
    plate_raise_count: Optional[int] = None  # 板块类型上涨支数
    plate_fall_count: Optional[int] = None  # 板块类型下跌支数
    plate_equal_count: Optional[int] = None  # 板块类型平盘支数
    index_valid: Optional[bool] = None  # 是否有指数类型
    index_raise_count: Optional[int] = None  # 指数类型上涨支数
    index_fall_count: Optional[int] = None  # 指数类型下跌支数
    index_equal_count: Optional[int] = None  # 指数类型平盘支数
    lot_size: Optional[int] = None  # 每手股数，股票期权表示每份合约的股数，期货表示合约乘数
    price_spread: Optional[float] = None  # 当前向上的摆盘价差
    ask_price: Optional[float] = None  # 卖价
    bid_price: Optional[float] = None  # 买价
    ask_vol: Optional[float] = None  # 卖量
    bid_vol: Optional[float] = None  # 买量
    sec_status: Optional[SecurityStatus] = None  # 股票状态
    amplitude: Optional[float] = None  # 振幅
    avg_price: Optional[float] = None  # 平均价
    bid_ask_ratio: Optional[float] = None  # 委比
    volume_ratio: Optional[float] = None  # 量比
    highest52weeks_price: Optional[float] = None  # 52 周最高价
    lowest52weeks_price: Optional[float] = None  # 52 周最低价
    highest_history_price: Optional[float] = None  # 历史最高价
    lowest_history_price: Optional[float] = None  # 历史最低价
    pre_price: Optional[float] = None  # 盘前价格
    pre_high_price: Optional[float] = None  # 盘前最高价
    pre_low_price: Optional[float] = None  # 盘前最低价
    pre_volume: Optional[int] = None  # 盘前成交量
    pre_turnover: Optional[float] = None  # 盘前成交额
    pre_change_val: Optional[float] = None  # 盘前涨跌额
    pre_change_rate: Optional[float] = None  # 盘前涨跌幅
    pre_amplitude: Optional[float] = None  # 盘前振幅
    after_price: Optional[float] = None  # 盘后价格
    after_high_price: Optional[float] = None  # 盘后最高价
    after_low_price: Optional[float] = None  # 盘后最低价
    after_volume: Optional[int] = None  # 盘后成交量
    after_turnover: Optional[float] = None  # 盘后成交额
    after_change_val: Optional[float] = None  # 盘后涨跌额
    after_change_rate: Optional[float] = None  # 盘后涨跌幅
    after_amplitude: Optional[float] = None  # 盘后振幅
    future_valid: Optional[bool] = None  # 是否期货
    future_last_settle_price: Optional[float] = None  # 昨结
    future_position: Optional[float] = None  # 持仓量
    future_position_change: Optional[float] = None  # 日增仓
    future_main_contract: Optional[bool] = None  # 是否主连合约
    future_last_trade_time: Optional[str] = None  # 最后交易时间
    trust_valid: Optional[bool] = None  # 是否基金
    trust_dividend_yield: Optional[float] = None  # 股息率
    trust_aum: Optional[float] = None  # 资产规模
    trust_outstanding_units: Optional[int] = None  # 总发行量
    trust_netAssetValue: Optional[float] = None  # 单位净值
    trust_premium: Optional[float] = None  # 溢价
    trust_assetClass: Optional[AssetClass] = None  # 资产类别

@dataclass
class StockQuote:
    """股票报价数据类

    包含股票的详细市场和交易信息，涵盖实时价格、成交量、期权相关指标等。
    """
    code: str  # 股票代码
    name: str  # 股票名称
    data_date: Optional[str] = None  # 日期
    data_time: Optional[str] = None  # 当前价更新时间
    last_price: Optional[float] = None  # 最新价格
    open_price: Optional[float] = None  # 今日开盘价
    high_price: Optional[float] = None  # 最高价格
    low_price: Optional[float] = None  # 最低价格
    prev_close_price: Optional[float] = None  # 昨收盘价格
    volume: Optional[int] = None  # 成交数量
    turnover: Optional[float] = None  # 成交金额
    turnover_rate: Optional[float] = None  # 换手率
    amplitude: Optional[int] = None  # 振幅
    suspension: Optional[bool] = None  # 是否停牌
    listing_date: Optional[str] = None  # 上市日期
    price_spread: Optional[float] = None  # 当前向上的价差
    dark_status: Optional[DarkStatus] = None  # 暗盘交易状态
    sec_status: Optional[SecurityStatus] = None  # 股票状态
    strike_price: Optional[float] = None  # 行权价
    contract_size: Optional[float] = None  # 每份合约数
    open_interest: Optional[int] = None  # 未平仓合约数
    implied_volatility: Optional[float] = None  # 隐含波动率
    premium: Optional[float] = None  # 溢价
    delta: Optional[float] = None  # 希腊值 Delta
    gamma: Optional[float] = None  # 希腊值 Gamma
    vega: Optional[float] = None  # 希腊值 Vega
    theta: Optional[float] = None  # 希腊值 Theta
    rho: Optional[float] = None  # 希腊值 Rho
    index_option_type: Optional[IndexOptionType] = None  # 指数期权类型
    net_open_interest: Optional[int] = None  # 净未平仓合约数
    expiry_date_distance: Optional[int] = None  # 距离到期日天数
    contract_nominal_value: Optional[float] = None  # 合约名义金额
    owner_lot_multiplier: Optional[float] = None  # 相等正股手数
    option_area_type: Optional[FutuOptionAreaType] = None  # 期权类型（按行权时间）
    contract_multiplier: Optional[float] = None  # 合约乘数
    pre_price: Optional[float] = None  # 盘前价格
    pre_high_price: Optional[float] = None  # 盘前最高价
    pre_low_price: Optional[float] = None  # 盘前最低价
    pre_volume: Optional[int] = None  # 盘前成交量
    pre_turnover: Optional[float] = None  # 盘前成交额
    pre_change_val: Optional[float] = None  # 盘前涨跌额
    pre_change_rate: Optional[float] = None  # 盘前涨跌幅
    pre_amplitude: Optional[float] = None  # 盘前振幅
    after_price: Optional[float] = None  # 盘后价格
    after_high_price: Optional[float] = None  # 盘后最高价
    after_low_price: Optional[float] = None  # 盘后最低价
    after_volume: Optional[int] = None  # 盘后成交量
    after_turnover: Optional[float] = None  # 盘后成交额
    after_change_val: Optional[float] = None  # 盘后涨跌额
    after_change_rate: Optional[float] = None  # 盘后涨跌幅
    after_amplitude: Optional[float] = None  # 盘后振幅
    last_settle_price: Optional[float] = None  # 昨结
    position: Optional[float] = None  # 持仓量
    position_change: Optional[float] = None  # 日增仓

@dataclass
class StockOrderBook:
    """股票订单簿数据类

    包含股票的详细订单簿数据，涵盖买盘和卖盘的委托价格、委托数量、委托订单数和委托订单明细。
    """
    code: str  # 股票代码
    name: str  # 股票名称
    svr_recv_time_bid: Optional[str] = None  # 富途服务器从交易所收到买盘数据的时间
    svr_recv_time_ask: Optional[str] = None  # 富途服务器从交易所收到卖盘数据的时间
    bid_orders: Optional[List[Tuple[float, int, int, List]]] = None  # 买盘订单列表，包含(委托价格，委托数量，委托订单数，委托订单明细)
    ask_orders: Optional[List[Tuple[float, int, int, List]]] = None  # 卖盘订单列表，包含(委托价格，委托数量，委托订单数，委托订单明细)


@dataclass
class OptionExpirationDate:
    """期权到期日信息数据类

    包含期权的到期日相关详细信息。

    Attributes:
        strike_time (str): 期权链行权日
        option_expiry_date_distance (int): 距离到期日天数
        expiration_cycle (ExpirationCycle): 交割周期
    """
    strike_time: str  # 期权链行权日
    option_expiry_date_distance: int  # 距离到期日天数
    expiration_cycle: OptionExpirationCycle  # 交割周期


@dataclass
class OptionChainItem:
    """期权链条目数据类"""
    code: str
    name: str
    lot_size: int
    stock_type: SecurityType
    option_type: OptionType
    stock_owner: str
    strike_time: str
    strike_price: float
    suspension: bool
    stock_id: int
    index_option_type: Optional[IndexOptionType] = None

class TradeEnv(Enum):
    """交易环境"""
    SIMULATE = 'SIMULATE'  # 模拟环境
    REAL = 'REAL'  # 真实环境

class TradeAccType(Enum):
    """交易账户类型"""
    NONE = 'NONE'  # 未知类型
    CASH = 'CASH'  # 现金账户
    MARGIN = 'MARGIN'  # 保证金账户

class SimAccountType(Enum):
    """模拟账户类型"""
    NONE = 'N/A'  # 未知类型
    STOCK = 'STOCK'  # 股票模拟账户
    OPTION = 'OPTION'  # 期权模拟账户
    FUTURES = 'FUTURES'  # 期货模拟账户

class TradeMarket(Enum):
    """交易市场"""
    NONE = 'NONE'  # 未知市场
    HK = 'HK'  # 香港市场
    US = 'US'  # 美国市场
    CNA = 'CNA'  # A股市场
    HKCC = 'HKCC'  # 香港 A 股通市场
    FUTURES = 'FUTURES'  # 期货市场
    FUTURES_SIMULATE_US = 'FUTURES_SIMULATE_US'  # 美国期货模拟市场
    FUTURES_SIMULATE_HK = 'FUTURES_SIMULATE_HK'  # 香港期货模拟市场
    FUTURES_SIMULATE_SG = 'FUTURES_SIMULATE_SG'  # 新加坡期货模拟市场
    FUTURES_SIMULATE_JP = 'FUTURES_SIMULATE_JP'  # 日本期货模拟市场
    HKFUND = 'HKFUND'  # 香港基金市场
    USFUND = 'USFUND'  # 美国基金市场
    SG = 'SG'  # 新加坡市场
    JP = 'JP'  # 日本市场
    AU = 'AU'  # 澳大利亚市场
    MY = 'MY'  # 马来西亚市场
    CA = 'CA'  # 加拿大市场

class AccoutStatus(Enum):
    """账户状态"""
    ACTIVE = 'ACTIVE'  # 生效账户
    DISABLED = 'DISABLED'  # 失效账户

@dataclass
class AccountInfo:
    """交易业务账户信息"""
    acc_id: int  # 交易业务账户
    trd_env: TradeEnv  # 交易环境
    acc_type: TradeAccType  # 账户类型
    uni_card_num: str  # 综合账户卡号，同移动端内的展示
    card_num: str  # 业务账户卡号
    security_firm: str  # 所属券商
    sim_acc_type: SimAccountType  # 模拟账户类型
    trdmarket_authlist: List[TradeMarket]  # 交易市场权限
    acc_status: AccoutStatus  # 账户状态

class CurrencyType(Enum):
    """货币类型"""
    NONE = 'NONE'  # 未知货币
    HKD = 'HKD'  # 港元
    USD = 'USD'  # 美元
    CNH = 'CNH'  # 离岸人民币
    JPY = 'JPY'  # 日元
    SGD = 'SGD'  # 新元
    AUD = 'AUD'  # 澳元
    CAD = 'CAD'  # 加拿大元
    MYR = 'MYR'  # 马来西亚林吉特

class AccountRiskLevel(Enum):
    """客户风险等级"""
    NONE = 'N/A'  # 未知
    SAFE = 'SAFE'  # 安全
    WARNING = 'WARNING'  # 预警
    DANGER = 'DANGER'  # 危险
    ABSOLUTE_SAFE = 'ABSOLUTE_SAFE'  # 绝对安全
    OPT_DANGER = 'OPT_DANGER'  # 危险

class AccountRiskStatus(Enum):
    """客户风险状态"""
    NONE = 'NONE'  # 未知
    LEVEL1 = 'LEVEL1'  # 非常安全
    LEVEL2 = 'LEVEL2'  # 安全
    LEVEL3 = 'LEVEL3'  # 较安全
    LEVEL4 = 'LEVEL4'  # 较低风险
    LEVEL5 = 'LEVEL5'  # 中等风险
    LEVEL6 = 'LEVEL6'  # 偏高风险
    LEVEL7 = 'LEVEL7'  # 预警
    LEVEL8 = 'LEVEL8'  # 危险
    LEVEL9 = 'LEVEL9'  # 危险

class DtStatus(Enum):
    """动态调整状态"""
    NONE = 'N/A'  # 未知
    UNLIMITED = 'UNLIMITED'  # 无限次
    EM_CALL = 'EM_CALL'  # EM-Call
    DT_CALL = 'DT_CALL'  # DT-Call


@dataclass
class AccountCashInfo:
    """资金信息"""
    power: float  # 最大购买力
    max_power_short: float  # 卖空购买力
    net_cash_power: float  # 现金购买力
    total_assets: float  # 总资产净值
    securities_assets: float  # 证券资产净值
    funds_assets: float  # 基金资产净值
    bonds_assets: float  # 债券资产净值
    cash: float  # 现金
    market_val: float  # 证券市值
    long_mv: float  # 多头市值
    short_mv: float  # 空头市值
    pending_asset: float  # 在途资产
    interest_charged_amount: float  # 计息金额
    frozen_cash: float  # 冻结资金
    avl_withdrawal_cash: float  # 现金可提
    max_withdrawal: float  # 最大可提
    currency: CurrencyType  # 计价货币
    available_funds: float  # 可用资金
    unrealized_pl: float  # 未实现盈亏
    realized_pl: float  # 已实现盈亏
    risk_level: AccountRiskLevel  # 风控状态
    risk_status: AccountRiskStatus  # 风险状态
    initial_margin: float  # 初始保证金
    margin_call_margin: float  # Margin Call 保证金
    maintenance_margin: float  # 维持保证金
    hk_cash: float  # 港元现金
    hk_avl_withdrawal_cash: float  # 港元可提
    hkd_net_cash_power: float  # 港元现金购买力
    hkd_assets: float  # 港股资产净值
    us_cash: float  # 美元现金
    us_avl_withdrawal_cash: float  # 美元可提
    usd_net_cash_power: float  # 美元现金购买力
    usd_assets: float  # 美股资产净值
    cn_cash: float  # 人民币现金
    cn_avl_withdrawal_cash: float  # 人民币可提
    cnh_net_cash_power: float  # 人民币现金购买力
    cnh_assets: float  # A股资产净值
    is_pdt: bool  # 是否为 PDT 账户
    pdt_seq: str  # 剩余日内交易次数
    beginning_dtbp: float  # 初始日内交易购买力
    remaining_dtbp: float  # 剩余日内交易购买力
    dt_call_amount: float  # 日内交易待缴金额
    dt_status: DtStatus  # 日内交易限制情况


class PositionSide(Enum):
    """持仓方向枚举"""
    NONE = "N/A"  # 未知
    LONG = "LONG"  # 多仓
    SHORT = "SHORT"  # 空仓


@dataclass
class PositionInfo:
    """持仓信息数据类
    
    包含股票、期货等金融产品的持仓详细信息，包括持仓数量、成本、盈亏等数据
    """
    position_side: PositionSide  # 持仓方向
    code: str  # 股票代码
    stock_name: str  # 股票名称
    position_market: TradeMarket  # 持仓所属市场
    qty: float  # 持有数量
    can_sell_qty: float  # 可用数量
    currency: CurrencyType  # 交易货币
    nominal_price: float  # 市价
    cost_price: float  # 摊薄成本价（证券账户）或平均开仓价（期货账户）
    cost_price_valid: bool  # 成本价是否有效
    market_val: float  # 市值
    pl_ratio: float  # 盈亏比例
    pl_ratio_valid: bool  # 盈亏比例是否有效
    pl_val: float  # 盈亏金额
    pl_val_valid: bool  # 盈亏金额是否有效
    today_pl_val: float  # 今日盈亏金额
    today_trd_val: float  # 今日交易金额
    today_buy_qty: float  # 今日买入总量
    today_buy_val: float  # 今日买入总额
    today_sell_qty: float  # 今日卖出总量
    today_sell_val: float  # 今日卖出总额
    unrealized_pl: float  # 未实现盈亏
    realized_pl: float  # 已实现盈亏

class TradeSize(Enum):
    """交易方向枚举
    
    描述交易订单的买卖方向
    """
    NONE = "N/A"  # 未知方向
    BUY = "BUY"  # 买入
    SELL = "SELL"  # 卖出
    SELL_SHORT = "SELL_SHORT"  # 卖空
    BUY_BACK = "BUY_BACK"  # 买回

    def get_numeric_value(self) -> int:
        TrdSide_Unknown = 0
        TrdSide_Buy = 1
        TrdSide_Sell = 2
        TrdSide_SellShort = 3
        TrdSide_BuyBack = 4

        if self == TradeSize.NONE:
            return TrdSide_Unknown
        elif self == TradeSize.BUY:
            return TrdSide_Buy
        elif self == TradeSize.SELL:
            return TrdSide_Sell
        elif self == TradeSize.SELL_SHORT:
            return TrdSide_SellShort
        elif self == TradeSize.BUY_BACK:
            return TrdSide_BuyBack
        else:
            raise ValueError(f"Invalid TrdSide value: {self}")



class OrderType(Enum):
    """订单类型枚举
    
    描述不同类型的交易订单，包括限价单、市价单等
    """
    NONE = "N/A"  # 未知类型
    NORMAL = "NORMAL"  # 限价单
    MARKET = "MARKET"  # 市价单
    ABSOLUTE_LIMIT = "ABSOLUTE_LIMIT"  # 绝对限价订单
    AUCTION = "AUCTION"  # 竞价市价单
    AUCTION_LIMIT = "AUCTION_LIMIT"  # 竞价限价单
    SPECIAL_LIMIT = "SPECIAL_LIMIT"  # 特别限价单
    SPECIAL_LIMIT_ALL = "SPECIAL_LIMIT_ALL"  # 特别限价且要求全部成交订单
    STOP = "STOP"  # 止损市价单
    STOP_LIMIT = "STOP_LIMIT"  # 止损限价单
    MARKET_IF_TOUCHED = "MARKET_IF_TOUCHED"  # 触及市价单（止盈）
    LIMIT_IF_TOUCHED = "LIMIT_IF_TOUCHED"  # 触及限价单（止盈）
    TRAILING_STOP = "TRAILING_STOP"  # 跟踪止损市价单
    TRAILING_STOP_LIMIT = "TRAILING_STOP_LIMIT"  # 跟踪止损限价单
    TWAP_LIMIT = "TWAP_LIMIT"  # 时间加权限价算法单（港股和美股）
    TWAP = "TWAP"  # 时间加权市价算法单（仅美股）
    VWAP_LIMIT = "VWAP_LIMIT"  # 成交量加权限价算法单（港股和美股）
    VWAP = "VWAP"  # 成交量加权市价算法单（仅美股）

    def get_numeric_value(self) -> int:
        OrderType_Unknown = 0
        OrderType_Normal = 1
        OrderType_Market = 2
        OrderType_AbsoluteLimit = 5
        OrderType_Auction = 6
        OrderType_AuctionLimit = 7
        OrderType_SpecialLimit = 8
        OrderType_SpecialLimit_All = 9
        OrderType_Stop = 10
        OrderType_StopLimit = 11
        OrderType_MarketifTouched = 12
        OrderType_LimitifTouched = 13
        OrderType_TrailingStop = 14
        OrderType_TrailingStopLimit = 15
        OrderType_TWAP = 16
        OrderType_TWAPLimit = 17
        OrderType_VWAP = 18
        OrderType_VWAPLimit = 19

        if self == OrderType.NONE:
            return OrderType_Unknown
        elif self == OrderType.NORMAL:
            return OrderType_Normal
        elif self == OrderType.MARKET:
            return OrderType_Market
        elif self == OrderType.ABSOLUTE_LIMIT:
            return OrderType_AbsoluteLimit
        elif self == OrderType.AUCTION:
            return OrderType_Auction
        elif self == OrderType.AUCTION_LIMIT:
            return OrderType_AuctionLimit
        elif self == OrderType.SPECIAL_LIMIT:
            return OrderType_SpecialLimit
        elif self == OrderType.SPECIAL_LIMIT_ALL:
            return OrderType_SpecialLimit_All
        elif self == OrderType.STOP:
            return OrderType_Stop
        elif self == OrderType.STOP_LIMIT:
            return OrderType_StopLimit
        elif self == OrderType.MARKET_IF_TOUCHED:
            return OrderType_MarketifTouched
        elif self == OrderType.LIMIT_IF_TOUCHED:
            return OrderType_LimitifTouched
        elif self == OrderType.TRAILING_STOP:
            return OrderType_TrailingStop
        elif self == OrderType.TRAILING_STOP_LIMIT:
            return OrderType_TrailingStopLimit
        elif self == OrderType.TWAP_LIMIT:
            return OrderType_TWAPLimit
        elif self == OrderType.TWAP:
            return OrderType_TWAP
        elif self == OrderType.VWAP_LIMIT:
            return OrderType_VWAPLimit
        elif self == OrderType.VWAP:
            return OrderType_VWAP
        else:
            raise ValueError(f"Invalid OrderType value: {self}")


class OrderStatus(Enum):
    """订单状态枚举
    
    描述订单在不同阶段的状态
    """
    NONE = "N/A"  # 未知状态
    WAITING_SUBMIT = "WAITING_SUBMIT"  # 待提交
    SUBMITTING = "SUBMITTING"  # 提交中
    SUBMITTED = "SUBMITTED"  # 已提交，等待成交
    FILLED_PART = "FILLED_PART"  # 部分成交
    FILLED_ALL = "FILLED_ALL"  # 全部已成交
    CANCELLED_PART = "CANCELLED_PART"  # 部分成交，剩余部分已撤单
    CANCELLED_ALL = "CANCELLED_ALL"  # 全部已撤单，无成交
    FAILED = "FAILED"  # 下单失败，服务拒绝
    DISABLED = "DISABLED"  # 已失效
    DELETED = "DELETED"  # 已删除，无成交的订单才能删除


class TimeInForce(Enum):
    """订单有效期限枚举
    
    描述订单的有效期限类型
    """
    DAY = "DAY"  # 当日有效
    GTC = "GTC"  # 撤单前有效


class TrailType(Enum):
    """跟踪类型枚举
    
    描述跟踪止损订单的跟踪方式
    """
    NONE = "N/A"  # 未知
    RATIO = "RATIO"  # 比例
    AMOUNT = "AMOUNT"  # 金额


@dataclass
class OrderInfo:
    """历史订单信息数据类
    
    包含历史订单的详细信息，包括订单类型、状态、价格、数量等数据
    """
    trd_side: TradeSize  # 交易方向
    order_type: OrderType  # 订单类型
    order_status: OrderStatus  # 订单状态
    order_id: str  # 订单号
    code: str  # 股票代码
    stock_name: str  # 股票名称
    order_market: TradeMarket  # 订单标的所属市场
    qty: float  # 订单数量
    price: float  # 订单价格
    currency: CurrencyType  # 交易货币
    create_time: str  # 创建时间
    updated_time: str  # 最后更新时间
    dealt_qty: float  # 成交数量
    dealt_avg_price: float  # 成交均价
    last_err_msg: str  # 最后的错误描述
    remark: str  # 下单时备注的标识
    time_in_force: TimeInForce  # 有效期限
    fill_outside_rth: bool  # 是否允许盘前盘后（用于港股盘前竞价与美股盘前盘后）
    aux_price: float  # 触发价格
    trail_type: TrailType  # 跟踪类型
    trail_value: float  # 跟踪金额/百分比
    trail_spread: float  # 指定价差
