# encoding utf-8

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
from loguru import logger

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem, build_stock_dropdown_list
from tgtrader.data_provider.index_data_query import IndexDataQuery

# 因子配置字典
# 所有因子相关的配置都集中在这里，后续只需要修改这个字典即可
FACTOR_CONFIG = {
    'smb': {
        'name': 'SMB规模因子',
        'color': '#1eb5a6',
        'description': "SMB因子（规模因子）：Small Minus Big，表示小市值股票相对于大市值股票的超额收益。正值表示小市值股票表现优于大市值股票，负值表示大市值股票表现优于小市值股票。"
    },
    'hml': {
        'name': 'HML价值因子',
        'color': '#ff6b78',
        'description': "HML因子（价值因子）：High Minus Low，表示高账面市值比股票相对于低账面市值比股票的超额收益。正值表示价值股表现优于成长股，负值表示成长股表现优于价值股。"
    },
    'rmw': {
        'name': 'RMW盈利因子',
        'color': '#4b9afa',
        'description': "RMW因子（盈利因子）：Robust Minus Weak，表示高盈利能力股票相对于低盈利能力股票的超额收益。正值表示高盈利能力股票表现优于低盈利能力股票，负值表示低盈利能力股票表现优于高盈利能力股票。"
    },
    'cma': {
        'name': 'CMA投资因子',
        'color': '#9c27b0',
        'description': "CMA因子（投资因子）：Conservative Minus Aggressive，表示低投资企业相对于高投资企业的超额收益。正值表示低投资企业表现优于高投资企业，负值表示高投资企业表现优于低投资企业。"
    }
    # 如果需要添加新因子，只需在这里添加新的配置项
    # 'new_factor': {
    #     'name': '新因子名称',
    #     'color': '#hex颜色代码',
    #     'description': '因子描述'
    # }
}


def prepare_symbols_dict(symbol_multiselect: list[StockDropdownSelectItem]) -> Tuple[Dict[SecurityType, List[str]], Dict[str, str]]:
    """
    根据选择的标的，准备证券类型字典和代码到名称的映射
    
    Args:
        symbol_multiselect: 选择的标的列表
        
    Returns:
        symbols_dict: 证券类型到代码列表的字典
        symbol_to_name: 代码到名称的映射
    """
    # 根据选择分离ETF和股票代码
    etf_symbols = []
    stock_symbols = []
    
    for symbol in symbol_multiselect:
        if SecurityType(symbol.symbol_type) == SecurityType.ETF:
            etf_symbols.append(symbol.code)
        elif SecurityType(symbol.symbol_type) == SecurityType.Stocks:
            stock_symbols.append(symbol.code)
    
    # 获取所有标的的收盘价数据
    symbols_dict = {}
    
    if etf_symbols:
        symbols_dict[SecurityType.ETF] = etf_symbols
        
    if stock_symbols:
        symbols_dict[SecurityType.Stocks] = stock_symbols
    
    # 创建标的代码到名称的映射
    symbol_to_name = {item.code: item.name for item in symbol_multiselect}
    
    return symbols_dict, symbol_to_name


@st.cache_data(ttl=3600)  # 缓存1小时
def _get_price_data_cached(symbol: str, security_type_value: int,
                         start_date_str: str, end_date_str: str) -> Optional[pd.DataFrame]:
    """
    获取单个标的的价格数据（可缓存版本）
    
    Args:
        symbol: 标的代码
        security_type_value: 证券类型的枚举值
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串
        
    Returns:
        单个标的的价格数据
    """
    # 创建新的DataGetter实例（避免使用不可哈希的对象作为参数）
    data_getter = DataGetter()
    security_type = SecurityType(security_type_value)
    
    # 记录日志
    logger.info(f"Fetching price data for single symbol {symbol} ({security_type}) from {start_date_str} to {end_date_str}")
    
    try:
        df = data_getter.get_price(
            symbol_list=[symbol],
            start_date=start_date_str,
            end_date=end_date_str,
            security_type=security_type,
            fields=["open", "high", "low", "close", "volume"]
        )
        
        if df.empty:
            logger.warning(f"No data found for symbol {symbol}")
            return None
            
        # 处理数据格式
        if isinstance(df.index, pd.MultiIndex) and 'code' in df.index.names and 'date' in df.index.names:
            # 已经是多级索引，提取单个标的的数据
            symbol_df = df.xs(symbol, level='code')['close']
        else:
            # 如果 date 和 code 是普通列
            df['date'] = pd.to_datetime(df['date'])
            symbol_df = df.set_index('date')['close']
        
        logger.info(f"Successfully fetched price data for symbol {symbol}")
        return symbol_df
        
    except Exception as e:
        st.error(f"获取{symbol}数据失败: {str(e)}")
        logger.error(f"获取{symbol}数据失败: {str(e)}")
        return None


def get_single_symbol_price_data(data_getter: DataGetter, symbol: str, security_type: SecurityType,
                            start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
    """
    获取单个标的的价格数据（包装函数）
    
    Args:
        data_getter: 数据获取器
        symbol: 标的代码
        security_type: 证券类型
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        单个标的的价格数据
    """
    # 格式化日期
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # 调用可缓存的函数
    return _get_price_data_cached(
        symbol=symbol,
        security_type_value=security_type.value,  # 使用枚举的值而不是枚举对象
        start_date_str=start_date_str,
        end_date_str=end_date_str
    )


def get_price_data(data_getter: DataGetter, symbols_dict: Dict[SecurityType, List[str]], 
                  start_date: datetime, end_date: datetime) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    获取多个标的的价格数据并计算收益率，使用单个标的缓存数据
    
    Args:
        data_getter: 数据获取器
        symbols_dict: 证券类型字典
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        pivot_df: 透视后的价格数据
        returns_df: 收益率数据
        normalized_prices: 标准化后的价格数据
    """
    # 记录日志
    logger.info(f"Fetching price data for multiple symbols from {start_date} to {end_date}")
    
    all_symbol_data = {}
    
    # 逐个获取每个标的的数据，利用单个标的缓存
    for security_type, symbols in symbols_dict.items():
        for symbol in symbols:
            symbol_data = get_single_symbol_price_data(
                data_getter=data_getter,
                symbol=symbol,
                security_type=security_type,
                start_date=start_date,
                end_date=end_date
            )
            
            if symbol_data is not None:
                all_symbol_data[symbol] = symbol_data
    
    if not all_symbol_data:
        logger.warning("No data found for any symbol")
        return None, None, None
    
    # 将所有标的数据合并为一个DataFrame
    pivot_df = pd.DataFrame(all_symbol_data)
    
    # 检查数据是否为空
    if pivot_df.empty:
        logger.warning("Combined DataFrame is empty")
        return None, None, None
    
    # 计算每日收益率
    returns_df = pivot_df.pct_change().dropna()
    
    # 标准化价格（起始日为100）
    normalized_prices = pivot_df.div(pivot_df.iloc[0]).mul(100)
    
    logger.info(f"Successfully processed price data for {len(pivot_df.columns)} symbols")
    return pivot_df, returns_df, normalized_prices


@st.cache_data(ttl=3600)  # 缓存1小时
def _get_factor_data_cached(start_date_str: str, end_date_str: str, factor_name: str) -> pd.DataFrame:
    """
    获取单个因子数据（可缓存版本）
    
    Args:
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串
        factor_name: 因子名称
        
    Returns:
        因子数据 DataFrame
    """
    # 创建新的查询实例
    index_query = IndexDataQuery()
    
    try:
        factor_df = index_query.get_index_data(factor_name, start_date_str, end_date_str)
        logger.info(f"Successfully fetched {factor_name} factor data")
        return factor_df
    except Exception as e:
        logger.error(f"获取{factor_name}因子数据失败: {str(e)}")
        return pd.DataFrame()


def get_factor_data(start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
    """
    获取因子数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        因子数据字典
    """
    # 记录日志
    logger.info(f"Fetching factor data from {start_date} to {end_date}")
    
    # 格式化日期
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # 从配置中获取因子名称
    factor_display_names = {factor_key: config['name'] for factor_key, config in FACTOR_CONFIG.items()}
    
    # 获取所有因子数据
    factor_data = {}
    
    for factor_key, config in FACTOR_CONFIG.items():
        # 使用可缓存的函数获取因子数据
        factor_df = _get_factor_data_cached(start_date_str, end_date_str, factor_key)
        
        if not factor_df.empty:
            factor_df = factor_df.rename(columns={'value': config['name']})
        else:
            st.error(f"获取{config['name']}数据失败")
        
        factor_data[factor_key] = factor_df
    
    logger.info("Successfully fetched factor data")
    return factor_data


def display_single_factor_chart(factor_df: pd.DataFrame, factor_name: str, factor_column: str, color: str, 
                          factor_description: str, returns_df: Optional[pd.DataFrame] = None, 
                          symbol_to_name: Optional[Dict[str, str]] = None):
    """
    显示单个因子的走势图
    
    Args:
        factor_df: 因子数据DataFrame
        factor_name: 因子名称
        factor_column: 因子数据列名
        color: 因子线条颜色
        factor_description: 因子描述
        returns_df: 对照标的收益率数据（包含所有标的）
        symbol_to_name: 代码到名称的映射
    """
    if factor_df.empty:
        st.warning(f"没有可用的{factor_name}数据")
        return
    
    # 创建图表
    fig = go.Figure()
    
    # 计算累计收益率
    factor_data = factor_df[factor_column]
    factor_data.iloc[0] = 0
    cumulative_returns = (1 + factor_data).cumprod()
    
    # 添加因子数据
    fig.add_trace(
        go.Scatter(
            x=factor_df['data_time'],
            y=cumulative_returns * 100,  # 转换为百分比
            mode='lines',
            name=factor_name,
            line=dict(color=color)
        )
    )
    
    # 如果有对照标的数据，添加所有标的到图表中
    if returns_df is not None and not returns_df.empty and symbol_to_name is not None:
        # 为不同的标的设置不同的颜色
        colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # 遍历所有标的
        for i, col in enumerate(returns_df.columns):
            # 确保日期格式一致
            returns_data = returns_df[col]
            returns_data.index = pd.to_datetime(returns_data.index)
            
            # 计算对照标的的累计收益率
            returns_data.iloc[0] = 0
            compare_cumulative_returns = (1 + returns_data).cumprod()
            
            # 获取标的名称
            symbol_name = f"{col} ({symbol_to_name.get(col, '')})" if symbol_to_name.get(col, '') else col
            
            # 添加对照标的数据，使用不同的颜色
            fig.add_trace(
                go.Scatter(
                    x=compare_cumulative_returns.index,
                    y=compare_cumulative_returns * 100,  # 转换为百分比
                    mode='lines',
                    name=symbol_name,
                    line=dict(color=colors[i % len(colors)], dash='dot', width=1)
                )
            )
    
    # 添加带有问号的标题，用于显示解释信息
    title_with_help = f"{factor_name}"
    
    # 更新布局
    fig.update_layout(
        title=title_with_help,
        xaxis_title="时间",
        yaxis_title="累计收益率(%)",
        height=400,
        width=800,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # 添加悬停提示
        hovermode="closest"
    )
    
    # 添加网格线
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    
    # 显示图表
    st.plotly_chart(fig)
    
    # 显示因子解释
    st.info(factor_description)
    
def display_factor_charts(factor_data: Dict[str, pd.DataFrame], returns_df: Optional[pd.DataFrame] = None, 
                         symbol_to_name: Optional[Dict[str, str]] = None):
    """
    显示所有因子走势图
    
    Args:
        factor_data: 因子数据字典
        returns_df: 对照标的收益率数据
        symbol_to_name: 代码到名称的映射
    """
    # 检查是否有数据
    if all(df.empty for df in factor_data.values()):
        st.warning("没有可用的因子数据")
        return
    
    # 从配置中获取因子描述
    factor_descriptions = {factor_key: config['description'] for factor_key, config in FACTOR_CONFIG.items()}
    
    # 从配置中获取因子颜色
    factor_colors = {factor_key: config['color'] for factor_key, config in FACTOR_CONFIG.items()}
    
    # 从配置中获取因子名称
    factor_names = {factor_key: config['name'] for factor_key, config in FACTOR_CONFIG.items()}
    
    # 遍历所有因子并显示图表
    for factor_key in FACTOR_CONFIG.keys():
        if factor_key in factor_data and not factor_data[factor_key].empty:
            display_single_factor_chart(
                factor_df=factor_data[factor_key],
                factor_name=factor_names[factor_key],
                factor_column=factor_names[factor_key],
                color=factor_colors[factor_key],
                factor_description=factor_descriptions[factor_key],
                returns_df=returns_df,
                symbol_to_name=symbol_to_name
            )


def display_price_chart(normalized_prices: pd.DataFrame, symbol_to_name: Dict[str, str]):
    """
    显示价格走势图
    
    Args:
        normalized_prices: 标准化后的价格数据
        symbol_to_name: 代码到名称的映射
    """
    if normalized_prices is None or normalized_prices.empty:
        st.warning("没有可用的价格数据")
        return
    
    # 创建图表
    fig = go.Figure()
    
    # 为每个标的添加一条线
    for col in normalized_prices.columns:
        fig.add_trace(
            go.Scatter(
                x=normalized_prices.index,
                y=normalized_prices[col],
                mode='lines',
                name=f"{col} ({symbol_to_name.get(col, '')})"
            )
        )
    
    # 更新布局
    fig.update_layout(
        title="标的价格走势（标准化）",
        xaxis_title="日期",
        yaxis_title="价格（起始=100）",
        height=500,
        width=800,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 添加网格线
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    
    # 显示图表
    st.plotly_chart(fig)
    
    # 显示因子解释
    st.info(factor_description)


@st.cache_data(ttl=3600, hash_funcs={pd.DataFrame: lambda _: None}, show_spinner=False)  # 缓存1小时，使用自定义哈希函数
def calculate_factor_correlation(returns_df: pd.DataFrame, factor_data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    计算标的收益率与因子之间的相关性
    
    Args:
        returns_df: 收益率数据
        factor_data: 因子数据字典
        
    Returns:
        相关性矩阵
    """
    if returns_df is None or returns_df.empty:
        return None
    
    # 记录日志
    logger.info(f"Calculating correlation for {len(returns_df.columns)} symbols with factors")
    
    # 创建因子收益率数据框
    factor_returns = pd.DataFrame(index=returns_df.index)
    
    # 添加SMB因子数据
    if not factor_data['smb'].empty:
        smb_data = factor_data['smb'].set_index('data_time')['SMB规模因子']
        # 将日期转换为相同格式
        smb_data.index = pd.to_datetime(smb_data.index)
        # 重采样到与收益率数据相同的频率
        smb_data = smb_data.reindex(returns_df.index, method='ffill')
        factor_returns['SMB规模因子'] = smb_data
    
    # 添加HML因子数据
    if not factor_data['hml'].empty:
        hml_data = factor_data['hml'].set_index('data_time')['HML价值因子']
        hml_data.index = pd.to_datetime(hml_data.index)
        hml_data = hml_data.reindex(returns_df.index, method='ffill')
        factor_returns['HML价值因子'] = hml_data
    
    # 添加RMW因子数据
    if not factor_data['rmw'].empty:
        rmw_data = factor_data['rmw'].set_index('data_time')['RMW盈利因子']
        rmw_data.index = pd.to_datetime(rmw_data.index)
        rmw_data = rmw_data.reindex(returns_df.index, method='ffill')
        factor_returns['RMW盈利因子'] = rmw_data
    
    # 添加CMA因子数据
    if 'cma' in factor_data and not factor_data['cma'].empty:
        cma_data = factor_data['cma'].set_index('data_time')['CMA投资因子']
        cma_data.index = pd.to_datetime(cma_data.index)
        cma_data = cma_data.reindex(returns_df.index, method='ffill')
        factor_returns['CMA投资因子'] = cma_data
    
    # 合并标的收益率和因子收益率
    combined_returns = pd.concat([returns_df, factor_returns], axis=1).dropna()
    
    # 计算相关性矩阵
    if combined_returns.empty:
        logger.warning("Combined returns DataFrame is empty, cannot calculate correlation")
        return None
    
    corr_matrix = combined_returns.corr()
    logger.info("Successfully calculated factor correlation matrix")
    
    return corr_matrix


def run():
    """
    市场风格分析页面
    1. 选标的（ETF或股票）
    2. 选时间段
    3. 分析市场风格因子
    """
    st.title('市场风格分析')
    
    # 初始化session_state
    if 'added_symbols' not in st.session_state:
        st.session_state.added_symbols = []
    if 'factor_data' not in st.session_state:
        st.session_state.factor_data = None
    if 'corr_matrix' not in st.session_state:
        st.session_state.corr_matrix = None
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime.now() - timedelta(days=365)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime.now()
    
    # 1. 标的选择
    data_getter = DataGetter()
    
    # 使用组件选择标的
    symbol_multiselect: list[StockDropdownSelectItem] = build_stock_dropdown_list(
        src_page='mkt_style_analysis', 
        data_getter=data_getter,
        title='选择对照标的',
        with_border=True
    )
    
    add_button = st.button('分析', type='primary')
    
    # 2. 时间段选择
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # 默认开始日期为一年前
    default_start_date = st.session_state.start_date
    default_end_date = st.session_state.end_date
    
    # 快速选择时间范围
    time_range_options = {
        "选择时间范围": None,
        "最近1个月": timedelta(days=30),
        "最近3个月": timedelta(days=90),
        "最近1年": timedelta(days=365),
        "最近2年": timedelta(days=365*2),
        "最近3年": timedelta(days=365*3),
        "最近5年": timedelta(days=365*5),
        "最近10年": timedelta(days=365*10)
    }
    
    time_range = col3.selectbox(
        "快速选择",
        options=list(time_range_options.keys()),
        key="mkt_style_analysis_time_range"
    )
    
    # 如果选择了时间范围，自动计算开始日期
    if time_range != "选择时间范围" and time_range_options[time_range] is not None:
        new_start_date = datetime.now() - time_range_options[time_range]
        st.session_state.start_date = new_start_date.date()
        default_start_date = st.session_state.start_date
        # 结束日期设置为今天
        st.session_state.end_date = datetime.now().date()
        default_end_date = st.session_state.end_date
    
    start_date = col1.date_input(
        "开始日期",
        value=default_start_date,
        key="mkt_style_analysis_start_date"
    )
    
    end_date = col2.date_input(
        "结束日期",
        value=default_end_date,
        key="mkt_style_analysis_end_date"
    )
    
    # 更新session_state中的日期
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    
    # 3. 处理添加标的
    if add_button:
        if start_date >= end_date:
            st.error('开始日期必须早于结束日期')
        else:
            # 清除之前的标的和相关数据
            st.session_state.added_symbols = []
            
            # 添加新选择的标的
            for symbol in symbol_multiselect:
                if symbol not in st.session_state.added_symbols:
                    st.session_state.added_symbols.append(symbol)
            
            # 清除缓存的相关性数据
            if 'corr_matrix' in st.session_state:
                del st.session_state.corr_matrix
            
            st.success(f'已添加 {len(symbol_multiselect)} 个对照标的')
    
    # 4. 显示图表和分析结果
    # 始终显示图表，无论是否有对照标的
    with st.spinner('正在分析市场风格...'):
        # 获取因子数据（第一次加载或日期变化时更新）
        factor_data = get_factor_data(start_date, end_date)

        st.session_state.factor_data = factor_data
        
        # 如果有添加的标的，准备对照标的数据
        returns_df = None
        symbol_to_name = None
        
        if st.session_state.added_symbols:
            # 准备证券类型字典和代码到名称的映射
            symbols_dict, symbol_to_name = prepare_symbols_dict(st.session_state.added_symbols)

            # 获取价格数据并计算收益率
            pivot_df, returns_df, normalized_prices = get_price_data(
                data_getter=data_getter,
                symbols_dict=symbols_dict,
                start_date=start_date,
                end_date=end_date
            )

        # 显示所有因子图表
        st.subheader('市场风格因子走势')
        display_factor_charts(factor_data, returns_df, symbol_to_name)
        
        # 如果有添加的标的，显示相关性矩阵
        if returns_df is not None:
            # 计算并显示相关性矩阵
            # 清除缓存的计算结果，确保重新计算
            calculate_factor_correlation.clear()
            corr_matrix = calculate_factor_correlation(returns_df, factor_data)
            
            # 将相关性矩阵保存到session_state
            st.session_state.corr_matrix = corr_matrix
            
            if corr_matrix is not None:
                st.subheader('标的与因子相关性')
                
                # 重命名索引和列，添加标的名称
                if symbol_to_name:
                    # 创建新的列名和索引名
                    new_columns = []
                    for col in corr_matrix.columns:
                        # 如果是标的代码，添加名称；如果是因子，保持不变
                        if col in symbol_to_name:
                            new_columns.append(f"{col} ({symbol_to_name[col]})")
                        else:
                            new_columns.append(col)
                    
                    # 设置新的列名和索引名
                    corr_matrix.columns = new_columns
                    
                    # 对于索引，只修改标的代码的部分
                    new_index = []
                    for idx in corr_matrix.index:
                        if idx in symbol_to_name:
                            new_index.append(f"{idx} ({symbol_to_name[idx]})")
                        else:
                            new_index.append(idx)
                    corr_matrix.index = new_index
                
                # 显示带颜色渐变的相关性矩阵
                st.dataframe(corr_matrix.style.background_gradient(cmap='coolwarm', axis=None, vmin=-1, vmax=1))


if __name__ == "__main__":
    run()
