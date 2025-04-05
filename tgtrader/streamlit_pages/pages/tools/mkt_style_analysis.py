# encoding utf-8

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from tgtrader.data import DataGetter, SecurityType
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem, build_stock_dropdown_list
from tgtrader.data_provider.index_data_query import IndexDataQuery
from loguru import logger

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


def create_monthly_returns_heatmap(factor_df: pd.DataFrame, factor_column: str, color: str):
    """
    创建因子月度收益率热力图
    
    Args:
        factor_df: 因子数据DataFrame
        factor_column: 因子数据列名
        color: 热力图颜色
        
    Returns:
        热力图Figure对象
    """
    if factor_df.empty:
        return None
    
    # 确保日期列是datetime类型
    factor_df['data_time'] = pd.to_datetime(factor_df['data_time'])
    
    # 设置日期为索引
    df = factor_df.set_index('data_time')
    
    # 计算每个月的收益率
    df['year'] = df.index.year
    df['month'] = df.index.month
    
    # 按年月分组计算月度收益率
    # 将每个月的第一个点设为0
    def calculate_monthly_return(group):
        # 将组内第一个点设为0
        group_values = group[factor_column].copy()
        if not group_values.empty:
            group_values.iloc[0] = 0
        # 计算累计收益率
        return (1 + group_values).prod() - 1
    
    monthly_returns = df.groupby(['year', 'month']).apply(calculate_monthly_return) * 100
    
    # 创建透视表，行为年，列为月
    pivot_table = monthly_returns.reset_index().pivot(index='year', columns='month', values=0)
    
    # 对年份进行排序，使其从上到下依次增大
    pivot_table = pivot_table.sort_index(ascending=True)
    
    # 创建热力图
    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=[f"{i}月" for i in range(1, 13)],
        y=pivot_table.index,
        # 设置纵轴方向，使年份从上到下依次增大
        yaxis="y",
        colorscale=[[0, 'rgba(0, 128, 0, 0.8)'], [0.5, 'rgba(255, 255, 255, 0.8)'], [1, 'rgba(255, 0, 0, 0.8)']],
        zmid=0,  # 将0设为中间值，正收益为绿色，负收益为红色
        text=[[f"{val:.2f}%" if not pd.isna(val) else "" for val in row] for row in pivot_table.values],
        texttemplate="%{text}",  # 直接在热力图上显示文本
        hoverinfo='text',
        showscale=True,
        colorbar=dict(
            title="月度收益率(%)",
            thickness=10,  # 减小颜色条的宽度
            len=0.8,  # 减小颜色条的长度
            titleside="right",  # 标题放在右侧
            ticks="outside"
        ),
    ))
    
    # 更新布局
    fig.update_layout(
        title="月度收益率热力图",
        xaxis_title="月份",
        yaxis_title="年份",
        height=400,
        width=500,  # 增加宽度
        margin=dict(l=40, r=20, t=50, b=30),  # 保持边距紧凑
        xaxis=dict(side='top'),  # 将x轴标签放在顶部
        yaxis=dict(autorange='reversed')  # 将y轴反转，使年份从上到下依次增大
    )
    
    return fig


def create_common_chart_layout(fig: go.Figure, title: str, xaxis_title: str, yaxis_title: str, 
                              height: int = 400, width: int = 800) -> go.Figure:
    """
    为图表创建通用布局
    
    Args:
        fig: Plotly图表对象
        title: 图表标题
        xaxis_title: x轴标题
        yaxis_title: y轴标题
        height: 图表高度
        width: 图表宽度
        
    Returns:
        更新布局后的图表对象
    """
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=height,
        width=width,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="closest"
    )
    
    # 添加网格线
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    
    return fig


def display_chart_with_heatmap(fig: go.Figure, factor_df: pd.DataFrame = None, 
                              factor_column: str = None, color: str = None, 
                              description: str = None):
    """
    显示图表和热力图的通用函数
    
    Args:
        fig: 主图表对象
        factor_df: 因子数据框（用于热力图）
        factor_column: 因子数据列名
        color: 热力图颜色
        description: 显示的描述信息
    """
    # 创建两列布局
    col1, col2 = st.columns([1.5, 1])
    
    # 左侧显示主图表
    with col1:
        st.plotly_chart(fig)
    
    # 右侧显示热力图（如果提供了必要参数）
    with col2:
        if factor_df is not None and factor_column is not None and color is not None:
            heatmap_fig = create_monthly_returns_heatmap(factor_df, factor_column, color)
            if heatmap_fig is not None:
                st.plotly_chart(heatmap_fig)
    
    # 显示描述信息（如果有）
    if description:
        st.info(description)


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
        returns_df = returns_df.copy()

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
    
    # 使用通用函数设置图表布局
    create_common_chart_layout(
        fig=fig,
        title=factor_name,
        xaxis_title="时间",
        yaxis_title="累计收益率(%)"
    )
    
    # 使用通用函数显示图表和热力图
    display_chart_with_heatmap(
        fig=fig,
        factor_df=factor_df,
        factor_column=factor_column,
        color=color,
        description=factor_description
    )
    
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
    
    # 使用通用函数设置图表布局
    create_common_chart_layout(
        fig=fig,
        title="标的价格走势（标准化）",
        xaxis_title="日期",
        yaxis_title="价格（起始=100）",
        height=500
    )
    
    # 只显示图表，不显示热力图和描述
    st.plotly_chart(fig)


def process_factor_data(factor_data: Dict[str, pd.DataFrame], target_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    处理因子数据，将其重新索引到目标索引
    
    Args:
        factor_data: 因子数据字典
        target_index: 目标索引
        
    Returns:
        处理后的因子数据框
    """
    factor_returns = pd.DataFrame(index=target_index)
    
    # 遍历FACTOR_CONFIG中的所有因子
    for factor_key, config in FACTOR_CONFIG.items():
        factor_name = config['name']
        if factor_key in factor_data and not factor_data[factor_key].empty:
            factor_series = factor_data[factor_key].set_index('data_time')[factor_name]
            factor_series.index = pd.to_datetime(factor_series.index)
            factor_series = factor_series.reindex(target_index, method='ffill')
            factor_returns[factor_name] = factor_series
    
    return factor_returns


@st.cache_data(ttl=3600, hash_funcs={pd.DataFrame: lambda _: None}, show_spinner=False)  # 缓存1小时，使用自定义哈希函数
def calculate_factor_correlation(returns_df: Optional[pd.DataFrame], factor_data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    计算标的收益率与因子之间的相关性，如果没有标的数据，则计算因子之间的相关性
    
    Args:
        returns_df: 收益率数据，可以为None
        factor_data: 因子数据字典
        
    Returns:
        相关性矩阵
    """
    # 创建因子收益率数据框
    # 如果没有标的数据，使用因子数据的索引
    if returns_df is None or returns_df.empty:
        # 获取所有因子数据的公共日期索引
        common_index = None
        for factor_name, df in factor_data.items():
            # 确保数据框不为空并且有数据
            if df is not None and not df.empty:
                # 如果数据框有data_time列，先设置索引
                if 'data_time' in df.columns:
                    df_indexed = df.set_index('data_time')
                else:
                    df_indexed = df
                
                if common_index is None:
                    common_index = df_indexed.index
                else:
                    common_index = common_index.intersection(df_indexed.index)
        
        if common_index is None or len(common_index) == 0:
            logger.warning("No common dates found in factor data")
            return None
            
        # 使用公共日期索引创建因子收益率数据框
        target_index = common_index  # 设置target_index为公共索引
        logger.info(f"Calculating correlation between factors only (no symbols)")
    else:
        # 获取要使用的索引
        target_index = returns_df.index
        logger.info(f"Calculating correlation for {len(returns_df.columns)} symbols with factors")
    
    # 使用通用函数处理因子数据
    factor_returns = process_factor_data(factor_data, target_index)

    # 合并标的收益率和因子收益率
    if returns_df is not None and not returns_df.empty:
        combined_returns = pd.concat([returns_df, factor_returns], axis=1).dropna()
    else:
        # 如果没有标的数据，只使用因子收益率
        combined_returns = factor_returns.dropna()

    # 计算相关性矩阵
    if combined_returns.empty:
        logger.warning("Combined returns DataFrame is empty, cannot calculate correlation")
        return None

    corr_matrix = combined_returns.corr()
    logger.info("Successfully calculated factor correlation matrix")
    
    return corr_matrix


@st.cache_data(ttl=3600, hash_funcs={pd.DataFrame: lambda _: None}, show_spinner=False)
def calculate_factor_regression(returns_df: pd.DataFrame, factor_data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    计算标的收益率与因子收益率的线性回归指标
    
    Args:
        returns_df: 标的收益率数据
        factor_data: 因子数据字典
        
    Returns:
        回归指标数据框
    """
    if returns_df is None or returns_df.empty:
        logger.warning("Returns DataFrame is empty, cannot calculate regression")
        return None
    
    # 使用通用函数处理因子数据
    factor_returns = process_factor_data(factor_data, returns_df.index)
    
    # 合并数据并删除缺失值
    combined_data = pd.concat([returns_df, factor_returns], axis=1).dropna()
    
    if combined_data.empty:
        logger.warning("Combined data is empty, cannot calculate regression")
        return None
    
    # 创建结果数据框
    results = []
    
    # 对每个标的进行回归分析
    for symbol in returns_df.columns:
        # 准备数据
        y = combined_data[symbol].values.reshape(-1, 1)  # 标的收益率
        X = combined_data[factor_returns.columns].values  # 因子收益率
        
        # 创建并拟合模型
        model = LinearRegression()
        model.fit(X, y)
        
        # 预测值
        y_pred = model.predict(X)
        
        # 计算指标
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        
        # 提取系数
        coefficients = {}
        for i, factor_name in enumerate(factor_returns.columns):
            coefficients[f"{factor_name}_系数"] = model.coef_[0][i]
        
        # 添加截距
        coefficients["截距"] = model.intercept_[0]
        
        # 添加评估指标
        coefficients["R²"] = r2
        coefficients["RMSE"] = rmse
        
        # 添加到结果列表
        result = {"标的": symbol, **coefficients}
        results.append(result)
    
    # 创建结果数据框
    regression_df = pd.DataFrame(results)
    
    logger.info("Successfully calculated factor regression")
    return regression_df


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
        # 计算并显示相关性矩阵
        # 清除缓存的计算结果，确保重新计算
        calculate_factor_correlation.clear()
        corr_matrix = calculate_factor_correlation(returns_df, factor_data)

        # 将相关性矩阵保存到session_state
        st.session_state.corr_matrix = corr_matrix
        
        if corr_matrix is not None:
            # 根据是否有标的数据显示不同的标题
            if returns_df is not None and not returns_df.empty:
                st.subheader('标的与因子相关性')
            else:
                st.subheader('因子之间的相关性')
            
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
        
        # 如果有标的数据，计算并显示因子回归分析
        if returns_df is not None and not returns_df.empty:
            # 计算因子回归
            calculate_factor_regression.clear()  # 清除缓存
            regression_df = calculate_factor_regression(returns_df, factor_data)
            
            if regression_df is not None:
                st.subheader('因子回归分析')
                st.markdown('以下表格展示了各标的收益率与因子收益率的线性回归结果，用于分析因子对标的收益率的解释性。')
                
                # 重命名标的列，添加名称
                if symbol_to_name:
                    regression_df['标的名称'] = regression_df['标的'].apply(lambda x: symbol_to_name.get(x, x))
                    regression_df['标的'] = regression_df['标的'].apply(lambda x: f"{x} ({symbol_to_name.get(x, x)})")
                
                # 显示回归结果表格
                st.dataframe(regression_df.style.format({
                    'R²': '{:.4f}',
                    'RMSE': '{:.4f}',
                    '截距': '{:.4f}',
                    'SMB规模因子_系数': '{:.4f}',
                    'HML价值因子_系数': '{:.4f}',
                    'MOM动量因子_系数': '{:.4f}',
                    'RMW盈利因子_系数': '{:.4f}',
                    'CMA投资因子_系数': '{:.4f}'
                }))
                
                # 创建汇总表格，每行是一个标的，每列是各因子的解释
                st.markdown('### 标的因子影响汇总表')
                
                # 定义因子影响判断函数
                def get_factor_impact(coef):
                    """根据系数判断因子影响大小和方向"""
                    if coef > 0.5:
                        return "强正相关"
                    elif coef > 0.2:
                        return "中正相关"
                    elif coef > 0:
                        return "弱正相关"
                    elif coef > -0.2:
                        return "弱负相关"
                    elif coef > -0.5:
                        return "中负相关"
                    else:
                        return "强负相关"
                
                def get_r2_impact(r2):
                    """根据R²判断模型解释力"""
                    if r2 > 0.6:
                        return "解释力强"
                    elif r2 > 0.3:
                        return "解释力中"
                    else:
                        return "解释力弱"
                
                # 准备汇总表格数据
                summary_data = []
                
                # 处理每个标的
                for _, row in regression_df.iterrows():
                    symbol = row['标的']
                    
                    # 创建每个标的的数据行
                    symbol_data = {
                        '标的': symbol,
                        'R²': f"{row['R²']:.4f} ({get_r2_impact(row['R²'])})",
                        'RMSE': f"{row['RMSE']:.4f} ({'误差大' if row['RMSE'] > 0.02 else '误差小'})",
                        '截距': f"{row['截距']:.4f} ({'有超额收益' if row['截距'] > 0.001 else '无显著超额收益' if row['截距'] > -0.001 else '有负超额收益'})"
                    }
                    
                    # 添加各因子的影响解释
                    factor_explanations = {
                        'SMB规模因子': {
                            '强正相关': '强烈偏好小市值',
                            '中正相关': '中度偏好小市值',
                            '弱正相关': '轻微偏好小市值',
                            '弱负相关': '轻微偏好大市值',
                            '中负相关': '中度偏好大市值',
                            '强负相关': '强烈偏好大市值'
                        },
                        'HML价值因子': {
                            '强正相关': '强烈偏好价值股',
                            '中正相关': '中度偏好价值股',
                            '弱正相关': '轻微偏好价值股',
                            '弱负相关': '轻微偏好成长股',
                            '中负相关': '中度偏好成长股',
                            '强负相关': '强烈偏好成长股'
                        },
                        'MOM动量因子': {
                            '强正相关': '强烈追涨特征',
                            '中正相关': '中度追涨特征',
                            '弱正相关': '轻微追涨特征',
                            '弱负相关': '轻微逆势特征',
                            '中负相关': '中度逆势特征',
                            '强负相关': '强烈逆势特征'
                        },
                        'RMW盈利因子': {
                            '强正相关': '强烈偏好高盈利',
                            '中正相关': '中度偏好高盈利',
                            '弱正相关': '轻微偏好高盈利',
                            '弱负相关': '轻微偏好低盈利',
                            '中负相关': '中度偏好低盈利',
                            '强负相关': '强烈偏好低盈利'
                        },
                        'CMA投资因子': {
                            '强正相关': '强烈偏好保守投资',
                            '中正相关': '中度偏好保守投资',
                            '弱正相关': '轻微偏好保守投资',
                            '弱负相关': '轻微偏好激进投资',
                            '中负相关': '中度偏好激进投资',
                            '强负相关': '强烈偏好激进投资'
                        }
                    }
                    
                    # 添加各因子解释
                    for factor in ['SMB规模因子', 'HML价值因子', 'MOM动量因子', 'RMW盈利因子', 'CMA投资因子']:
                        coef_col = f"{factor}_系数"
                        if coef_col in row:
                            impact = get_factor_impact(row[coef_col])
                            explanation = factor_explanations[factor][impact] if factor in factor_explanations and impact in factor_explanations[factor] else impact
                            symbol_data[factor] = f"{row[coef_col]:.4f} ({explanation})"
                    
                    # 添加到汇总数据
                    summary_data.append(symbol_data)
                
                # 显示汇总表格
                st.dataframe(pd.DataFrame(summary_data))
                

if __name__ == "__main__":
    run()
