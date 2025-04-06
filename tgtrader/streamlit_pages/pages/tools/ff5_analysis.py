# encoding utf-8

import streamlit as st
import statsmodels.api as sm
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from tgtrader.data import DataGetter, SecurityType
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem, build_stock_dropdown_list
from tgtrader.data_provider.index_data_query import IndexDataQuery
from loguru import logger
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge

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


def _get_price_data_cached_inner(symbol: str, security_type_value: int,
                         start_date_str: str, end_date_str: str) -> Optional[pd.DataFrame]:
    """
    获取单个标的的价格数据（内部实现）
    
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

@st.cache_data(ttl=3600)  # 缓存1小时
def _get_price_data_cached(symbol: str, security_type_value: int,
                         start_date_str: str, end_date_str: str) -> Optional[pd.DataFrame]:
    """
    获取单个标的的价格数据（可缓存版本）
    
    只有在成功获取数据时才会将结果添加到缓存中
    
    Args:
        symbol: 标的代码
        security_type_value: 证券类型的枚举值
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串
        
    Returns:
        单个标的的价格数据
    """
    # 调用内部函数获取数据
    result = _get_price_data_cached_inner(symbol, security_type_value, start_date_str, end_date_str)
    
    # 如果结果为None，抛出异常以避免缓存
    if result is None:
        # 使用st.cache_data的特性，抛出异常会阻止缓存
        raise Exception(f"获取{symbol}数据失败，不缓存结果")
    
    return result


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
def _get_factor_data_cached_inner(start_date_str: str, end_date_str: str, factor_name: str) -> pd.DataFrame:
    """
    获取单个因子数据（内部实现）
    
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

def _get_factor_data_cached(start_date_str: str, end_date_str: str, factor_name: str) -> pd.DataFrame:
    """
    获取单个因子数据（可缓存版本）
    
    只有在成功获取数据时才会将结果添加到缓存中
    
    Args:
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串
        factor_name: 因子名称
        
    Returns:
        因子数据 DataFrame
    """
    # 调用内部函数获取数据
    result = _get_factor_data_cached_inner(start_date_str, end_date_str, factor_name)
    
    # 如果结果为空 DataFrame，抛出异常以避免缓存
    if result.empty:
        # 使用st.cache_data的特性，抛出异常会阻止缓存
        raise Exception(f"获取{factor_name}因子数据失败，不缓存结果")
    
    return result


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
        title="因子月度收益率热力图",
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

    factor_df = factor_df.copy()
    
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


def display_correlation_matrix(corr_matrix: pd.DataFrame, symbol_to_name: Optional[Dict[str, str]] = None, 
                           returns_df: Optional[pd.DataFrame] = None):
    """
    显示相关性矩阵
    
    Args:
        corr_matrix: 相关性矩阵DataFrame
        symbol_to_name: 代码到名称的映射
        returns_df: 收益率数据，用于判断是否有标的数据
    """
    if corr_matrix is None:
        return
        
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


def filter_high_correlation_factors(factors_df: pd.DataFrame, correlation_threshold: float = 0.7) -> Tuple[pd.DataFrame, Dict[str, str], pd.DataFrame]:
    """
    移除高相关性因子，优先保留具有重要经济意义的因子，其次保留方差大或VIF值低的因子
    
    Args:
        factors_df: 因子数据框
        correlation_threshold: 相关性阈值，当相关性绝对值超过此阈值时进行处理
        
    Returns:
        过滤后的因子数据框、过滤信息字典和过滤后的相关性矩阵的元组 (filtered_factors_df, filter_info, filtered_correlation_matrix)
    """
    if factors_df.empty or factors_df.shape[1] < 2:
        return factors_df, {}, factors_df.corr().abs() if not factors_df.empty else pd.DataFrame()
    
    # 定义具有重要经济意义的因子列表（按重要性排序）
    important_factors = ['smb', 'rmw', 'hml', 'cma']  # 小市值、盈利、价值、投资因子
    
    # 计算相关性矩阵的绝对值
    correlation_matrix = factors_df.corr().abs()
    
    # 计算每个因子的方差
    factor_variance = factors_df.var()
    
    # 尝试计算VIF值（如果数据充足）
    vif_values = {}
    try:
        # 添加常数项
        X = sm.add_constant(factors_df)
        vif_data = pd.DataFrame()
        vif_data["feature"] = X.columns
        
        # 计算每个因子的VIF
        for i in range(1, len(X.columns)):
            vif_values[X.columns[i]] = variance_inflation_factor(X.values, i)
        
        logger.debug(f"VIF值: {vif_values}")
    except Exception as e:
        logger.warning(f"计算VIF值时出错: {e}")
    
    # 创建一个列表来存储要保留的因子
    filtered_factors = list(factors_df.columns)
    
    # 创建一个字典来记录过滤信息
    filter_info = {}
    
    # 获取上三角矩阵的索引，不包括对角线
    upper_triangle = np.triu(correlation_matrix.values, k=1)
    
    # 找出相关性超过阈值的因子对
    high_correlation_indices = np.where(upper_triangle > correlation_threshold)
    
    # 将索引转换为因子名称对
    high_correlation_pairs = [(correlation_matrix.index[i], correlation_matrix.columns[j]) 
                              for i, j in zip(*high_correlation_indices)]
    
    # 按相关性从高到低排序
    high_correlation_pairs.sort(key=lambda pair: correlation_matrix.loc[pair[0], pair[1]], reverse=True)
    
    # 处理每一对高相关性因子
    for factor1, factor2 in high_correlation_pairs:
        # 如果其中一个因子已经被移除，则跳过
        if factor1 not in filtered_factors or factor2 not in filtered_factors:
            continue
        
        # 决定移除哪个因子
        remove_factor = None
        keep_factor = None
        reason = ""
        
        # 第一优先级：根据因子的经济意义重要性决定
        factor1_importance = -1
        factor2_importance = -1
        
        # 检查因子是否在重要因子列表中，并获取其重要性排名
        for factor in [factor1.lower(), factor2.lower()]:
            for i, important_factor in enumerate(important_factors):
                if factor == important_factor or factor.startswith(important_factor):
                    if factor == factor1.lower():
                        factor1_importance = i
                    else:
                        factor2_importance = i
                    break
        
        # 如果两个因子都在重要因子列表中，根据重要性排名决定
        if factor1_importance >= 0 and factor2_importance >= 0:
            if factor1_importance < factor2_importance:  # 排名越小越重要
                remove_factor = factor2
                keep_factor = factor1
                reason = f"经济意义更重要({important_factors[factor1_importance]} > {important_factors[factor2_importance]})"
            else:
                remove_factor = factor1
                keep_factor = factor2
                reason = f"经济意义更重要({important_factors[factor2_importance]} > {important_factors[factor1_importance]})"
        
        # 如果只有一个因子在重要因子列表中，保留该因子
        elif factor1_importance >= 0:
            remove_factor = factor2
            keep_factor = factor1
            reason = f"保留经济意义重要因子({important_factors[factor1_importance]})"
        elif factor2_importance >= 0:
            remove_factor = factor1
            keep_factor = factor2
            reason = f"保留经济意义重要因子({important_factors[factor2_importance]})"
        
        # 第二优先级：使用VIF值做决策（如果可用且上一步没有决定）
        elif vif_values and factor1 in vif_values and factor2 in vif_values:
            if vif_values[factor1] > vif_values[factor2]:
                remove_factor = factor1
                keep_factor = factor2
                reason = f"VIF值较高({vif_values[factor1]:.2f} > {vif_values[factor2]:.2f})"
            else:
                remove_factor = factor2
                keep_factor = factor1
                reason = f"VIF值较高({vif_values[factor2]:.2f} > {vif_values[factor1]:.2f})"
        
        # 第三优先级：根据方差决定（如果前两步没有决定）
        else:
            # 移除方差较小的因子（保留信息量更大的因子）
            if factor_variance[factor1] >= factor_variance[factor2]:
                remove_factor = factor2
                keep_factor = factor1
                reason = f"方差较小({factor_variance[factor2]:.6f} < {factor_variance[factor1]:.6f})"
            else:
                remove_factor = factor1
                keep_factor = factor2
                reason = f"方差较小({factor_variance[factor1]:.6f} < {factor_variance[factor2]:.6f})"
        
        logger.debug(f"移除因子: {remove_factor}，保留因子: {keep_factor}，原因: {reason}，相关性: {correlation_matrix.loc[factor1, factor2]:.4f}")
        
        # 移除选定的因子
        if remove_factor in filtered_factors:
            filtered_factors.remove(remove_factor)
            filter_info[remove_factor] = f"由于与{keep_factor}高相关({correlation_matrix.loc[factor1, factor2]:.4f})被移除，{reason}"
    
    # 创建过滤后的因子数据框
    filtered_factors_df = factors_df[filtered_factors].copy()
    
    # 计算过滤后的相关性矩阵
    filtered_correlation_matrix = filtered_factors_df.corr().abs()
    logger.debug(f"过滤后因子相关性矩阵:\n{filtered_correlation_matrix}")
    
    return filtered_factors_df, filter_info, filtered_correlation_matrix


def calculate_factor_regression(returns_df: pd.DataFrame, factor_data: Dict[str, pd.DataFrame], maxlags: int = 5, 
                               correlation_threshold: float = 0.7) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    计算因子回归分析，通过移除高相关性因子来处理共线性问题，然后使用处理后的因子进行OLS回归
    
    Args:
        returns_df: 收益率数据框
        factor_data: 因子数据字典，键为因子名称，值为因子数据框
        maxlags: HAC标准误的最大滞后期数，用于处理时间序列中的自相关和异方差
        correlation_threshold: 相关性阈值，当因子间绝对相关性超过此阈值时，移除其中一个因子
        
    Returns:
        回归分析结果数据框和处理后的因子相关性矩阵的元组 (regression_df, filtered_correlation_matrix)
    """
    # 检查输入数据有效性
    if returns_df is None or returns_df.empty or not factor_data:
        logger.warning("收益率数据或因子数据为空，无法进行回归分析")
        return None, None

    # 处理因子数据，确保时间索引一致
    common_index = returns_df.index
    all_factors = process_factor_data(factor_data, common_index)

    if all_factors.empty or all_factors.shape[1] < 1:
        logger.warning("处理后的因子数据为空，无法进行回归分析")
        return None, None
    
    # 1. 计算原始因子相关性矩阵（用于显示原始相关性）
    correlation_matrix = all_factors.corr().abs()
    logger.debug(f"原始因子相关性矩阵:\n{correlation_matrix}")
    
    # 2. 使用过滤高相关性因子的方法处理共线性
    filtered_factors, filter_info, filtered_correlation_matrix = filter_high_correlation_factors(all_factors, correlation_threshold)
    logger.info(f"共线性处理后保留的因子数量: {filtered_factors.shape[1]}/{all_factors.shape[1]}")
    
    # 3. 对每个标的进行回归分析
    regression_results = []
    for symbol in returns_df.columns:
        symbol_returns = returns_df[[symbol]]
        # 合并收益率和过滤后的因子数据
        merged_data = pd.merge(symbol_returns, filtered_factors, left_index=True, right_index=True, how='inner')
        merged_data = merged_data.dropna()
        
        # 检查数据量是否足够
        if len(merged_data) < 10:  # 至少需要10个观测值
            logger.warning(f"对{symbol}进行回归分析的有效数据不足。只有{len(merged_data)}个观测值。")
            continue

        # 准备回归变量
        y = merged_data[symbol].values  # 回归因变量（收益率）
        X_df = merged_data.drop(columns=[symbol])  # 自变量（因子）
        
        # 添加常数项
        X = sm.add_constant(X_df.values)
        X_cols_with_const = ['const'] + X_df.columns.tolist()  # 用于结果索引
        
        try:
            # 4. 使用OLS + HAC标准误进行回归
            ols_model = sm.OLS(y, X)
            ols_fit = ols_model.fit(cov_type='HAC', cov_kwds={'maxlags': maxlags})

            # 5. 收集回归结果
            reg_res = {
                '标的': symbol,
                'R²': ols_fit.rsquared,
                'Adj. R²': ols_fit.rsquared_adj,
                '样本数': ols_fit.nobs
            }
            
            # 添加系数信息
            for i, name in enumerate(X_cols_with_const):
                # 格式化: 系数 (t值, p值)
                coef = ols_fit.params[i]
                tval = ols_fit.tvalues[i]
                pval = ols_fit.pvalues[i]
                reg_res[f'{name}_系数'] = f"{coef:.4f} (t={tval:.2f}, p={pval:.3f})"
            
            # 添加共线性处理信息
            if filter_info:
                reg_res['共线性处理'] = f'移除高相关因子(阈值={correlation_threshold})'
                # 添加过滤信息
                reg_res['过滤信息'] = ', '.join([f"{factor}: {info}" for factor, info in filter_info.items()])
            else:
                reg_res['共线性处理'] = '无'

            regression_results.append(reg_res)
        except Exception as e:
            logger.error(f"对{symbol}进行回归分析时出错: {e}")
            # 跳过当前符号，继续处理下一个
            continue

    # 6. 创建回归结果数据框
    regression_df = pd.DataFrame(regression_results) if regression_results else None

    return regression_df, filtered_correlation_matrix


def display_factor_regression_analysis(regression_results: Optional[pd.DataFrame], filtered_correlation_matrix: Optional[pd.DataFrame], symbol_to_name: Optional[Dict[str, str]], factor_code_to_display: Dict[str, str]):
    """
    显示因子回归分析结果表格和处理后的因子相关性矩阵

    Args:
        regression_results: 回归分析结果DataFrame
        filtered_correlation_matrix: 处理后的因子相关性矩阵
        symbol_to_name: 代码到名称的映射
        factor_code_to_display: 因子代码 (列名后缀) 到中文显示名称的映射
    """

    # 定义一个函数来处理系数显示，添加显著性标记
    def format_coef_with_significance(coef_str):
        if not isinstance(coef_str, str) or '(' not in coef_str:
            return coef_str
        try:
            # 先移除可能已存在的星号，再解析p值
            p_val_str = coef_str.split('p=')[1].split(')')[0].replace('*','').strip()
            p_val = float(p_val_str)
            
            # 检查是否是z值或t值
            if 'z=' in coef_str:
                stat_type = 'z'
            else:
                stat_type = 't'
                
            # 提取系数值和统计量部分，保留t值或z值
            coef_and_stat = coef_str.split('p=')[0].strip()
            if coef_and_stat.endswith(','):
                coef_and_stat = coef_and_stat[:-1]  # 移除末尾的逗号

            # 根据p值添加星号
            if p_val < 0.01:
                return f"{coef_and_stat} p={p_val:.3f} ***)" 
            elif p_val < 0.05:
                return f"{coef_and_stat} p={p_val:.3f} **)"
            elif p_val < 0.1:
                return f"{coef_and_stat} p={p_val:.3f} *)"
            return f"{coef_and_stat} p={p_val:.3f})" 
        except:
            return coef_str # 解析失败返回原值

    # --- 显示处理后的因子相关性矩阵 ---
    if filtered_correlation_matrix is not None and not filtered_correlation_matrix.empty:
        st.markdown("### 处理后的因子相关性矩阵")
        
        # 将因子代码转换为显示名称
        display_matrix = filtered_correlation_matrix.copy()
        display_matrix.index = [factor_code_to_display.get(col, col.capitalize()) for col in display_matrix.index]
        display_matrix.columns = [factor_code_to_display.get(col, col.capitalize()) for col in display_matrix.columns]
        
        # 创建相关性热力图
        fig = px.imshow(
            display_matrix,
            text_auto=True,
            color_continuous_scale='RdBu_r',
            zmin=0, zmax=1,
            aspect="auto"
        )
        fig.update_layout(
            title="因子相关性热力图 (去除共线性后)",
            height=500,
            width=700
        )
        st.plotly_chart(fig)
        
        st.markdown('''
        ### 相关性矩阵说明
        
        上图显示了**处理共线性后保留的因子**之间的相关性矩阵。该矩阵的特点：
        
        - **相关性值范围**：0（无相关）至1（完全相关），这里显示的是绝对值
        - **颜色含义**：颜色越深，表示相关性越强
        - **共线性处理效果**：经过处理，所有因子间的相关性绝对值均低于设定的阈值，有效降低了多重共线性问题
        
        这些低相关性的因子能更好地捕捉不同的市场风格特征，提高回归结果的可靠性和解释性。
        ''')
    
    # --- 显示回归分析结果 ---
    if regression_results is not None and not regression_results.empty:
        st.markdown("### 回归分析结果")
        st.markdown("""
        ### 结果解读指南
        
        **系数值与显著性**：
        - **系数值**：表示因子每变动一个单位，标的收益率预期变动的百分比
        - **t值**：表示系数估计的统计显著性，绝对值越大越显著
        - **p值与星号**：表示显著性级别：
            * p < 0.01 (***): 非常显著
            * p < 0.05 (**): 显著
            * p < 0.1 (*): 弱显著
        
        **模型评估**：
        - **R²**：模型解释力，范围为0-1，越高表示因子对收益率的解释力越强
        - **Adj. R²**：调整后的R²，考虑了因子数量，更适合模型比较
        """)
        
        # 检查是否有共线性处理信息
        collinearity_method = None
        if '共线性处理' in regression_results.columns:
            collinearity_methods = regression_results['共线性处理'].unique()
            if len(collinearity_methods) > 0 and collinearity_methods[0] != '无':
                collinearity_method = collinearity_methods[0]
        
        method_description = '''
        **方法说明**：普通最小二乘法(OLS)结合Newey-West修正，适用于存在自相关和异方差的时间序列数据。'''
        
        # 根据共线性处理方法添加相应的说明
        if collinearity_method and '移除高相关因子' in collinearity_method:
            method_description += f'并通过移除相关性高的因子来处理共线性问题，这样可以：\n\n'
            method_description += '- 保持因子原始含义，便于解释\n'
            method_description += '- 提高系数估计的稳定性\n'
            method_description += '- 使模型更简洁高效'

        '''
        **结果解读**：关注各因子的系数、显著性(p值和星号)和解读。R²表示模型整体解释力度。'''
        
        st.markdown(method_description)

        display_df = regression_results.copy()
        
        # 合并标的和标的名称为一列
        if symbol_to_name:
            display_df['标的'] = display_df['标的'].apply(lambda x: f"{x} ({symbol_to_name.get(x, '')})") 
        
        # 调整列顺序，非系数列
        base_cols = ['标的']
        # 更新列名：将'正交化信息'改为'过滤信息'
        if '正交化信息' in display_df.columns and '过滤信息' not in display_df.columns:
            display_df.rename(columns={'正交化信息': '过滤信息'}, inplace=True)
        other_cols = [col for col in display_df.columns if col not in base_cols and not col.endswith('_系数')]
        
        # 按照指定顺序排列因子列：SMB、RMW、HML、CMA
        factor_order = ['smb', 'rmw', 'hml', 'cma']
        coef_cols = []
        for factor in factor_order:
            factor_col = f"{factor}_系数"
            if factor_col in display_df.columns:
                coef_cols.append(factor_col)
        
        # 添加其他可能存在的因子列（如截距项）
        other_coef_cols = [col for col in display_df.columns if col.endswith('_系数') and col not in coef_cols]
        coef_cols = other_coef_cols + coef_cols  # 其他因子放在前面
        
        # 应用最终列顺序
        display_df = display_df[base_cols + other_cols + coef_cols]

        # 存储最终列顺序的列表
        final_cols_order = []
        processed_interpret_cols = set() # 跟踪已添加的解读列

        # 创建OLS显示DataFrame
        ols_display_df = display_df.copy()

        # 遍历调整后的列
        for col in display_df.columns:
            if col.endswith('_系数'):
                base_factor_code = col.replace('_系数', '')
                display_name = factor_code_to_display.get(base_factor_code, base_factor_code.capitalize())
                
                # 1. 格式化系数列 (添加星号和p值)
                formatted_coefs = ols_display_df[col].apply(format_coef_with_significance)
                
                # 2. 获取解读文本
                interpretations = formatted_coefs.apply(
                    lambda x: interpret_coefficient(x, display_name)
                )
                
                # 3. 合并系数和解读到同一个单元格，增加换行符使显示更清晰
                ols_display_df[col] = formatted_coefs.astype(str) + "\n\n" + "解读：\n" + interpretations.astype(str)
            elif col == 'R²' or col == 'Adj. R²':
                # 为 R² 和 Adj. R² 添加解读
                r_squared_values = ols_display_df[col].astype(float)
                interpretations = r_squared_values.apply(interpret_r_squared)
                ols_display_df[col] = r_squared_values.apply(lambda x: f"{x:.4f}") + "\n\n" + "解读：\n" + interpretations
            
            final_cols_order.append(col)

        # 应用最终的列顺序
        ols_display_df = ols_display_df[final_cols_order]

        # 直接显示 DataFrame，不应用格式化
        # 由于我们已经将所有列转换为字符串，不需要再应用格式化
        
        # 直接显示 DataFrame，不应用格式化
        st.dataframe(ols_display_df)

    else:
        st.markdown("### 回归分析结果")
        st.info("没有足够的有效数据进行回归分析。")

    st.markdown("---") # 分隔线


def display_factor_impact_summary(regression_df: pd.DataFrame, symbol_to_name: Optional[Dict[str, str]] = None):
    """
    显示因子影响汇总表
    """
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
    
    # 因子解释字典
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


def interpret_r_squared(r_squared_val):
    """
    解读R平方和调整后R平方的值

    Args:
        r_squared_val (float): R平方或调整后R平方的值

    Returns:
        str: 解读文本，说明模型拟合程度
    """
    if not isinstance(r_squared_val, (float, int)):
        try:
            r_squared_val = float(r_squared_val)
        except:
            return "无法解读"
    
    if r_squared_val >= 0.7:
        return "模型拟合度很高，因子能很好地解释收益率变化"
    elif r_squared_val >= 0.5:
        return "模型拟合度较高，因子能较好地解释收益率变化"
    elif r_squared_val >= 0.3:
        return "模型拟合度中等，因子能部分解释收益率变化"
    elif r_squared_val >= 0.1:
        return "模型拟合度较低，因子对收益率的解释力有限"
    else:
        return "模型拟合度很低，因子几乎不能解释收益率变化"

def interpret_coefficient(coef_str, factor_display_name):
    """
    根据系数信息字符串生成解读文本。

    Args:
        coef_str (str): 包含系数、t/z值和p值的字符串, e.g., "0.12 (t=2.1, p=0.04)"
        factor_display_name (str): 因子的中文显示名称, e.g., "市值"

    Returns:
        str: 解读文本, e.g., "影响显著 (**)，正相关"
    """
    if not isinstance(coef_str, str):
        return "无法解析"
    
    # 调试信息
    # print(f"解析系数字符串: {coef_str}, 因子: {factor_display_name}")
    
    try:
        # 处理可能的格式: "0.123 (t=1.23, p=0.045)"
        # 或者: "0.123 (z=1.23, p=0.045)"
        # 或者其他可能的格式
        
        # 1. 提取系数值 (数字部分)
        if '(' in coef_str:
            coef_part = coef_str.split('(')[0].strip()
        else:
            coef_part = coef_str.strip()
            
        try:
            coef_val = float(coef_part)
        except ValueError:
            # 如果无法转换为浮点数，尝试其他方法提取
            import re
            number_match = re.search(r"[-+]?\d*\.\d+|\d+", coef_part)
            if number_match:
                coef_val = float(number_match.group())
            else:
                return "系数解析失败"
        
        # 2. 提取p值
        if 'p=' not in coef_str:
            return f"{'正相关' if coef_val > 0 else '负相关'} (无显著性信息)"
            
        # 尝试不同的方式提取p值
        try:
            # 方法1: 直接分割
            p_val_str = coef_str.split('p=')[1]
            if ')' in p_val_str:
                p_val_str = p_val_str.split(')')[0]
            
            # 移除可能的星号和空格
            p_val_str = p_val_str.replace('*', '').strip()
            
            # 如果有逗号，取逗号前的部分
            if ',' in p_val_str:
                p_val_str = p_val_str.split(',')[0].strip()
                
            p_val = float(p_val_str)
        except:
            # 方法2: 使用正则表达式
            import re
            p_match = re.search(r"p\s*=\s*([-+]?\d*\.\d+|\d+)", coef_str)
            if p_match:
                p_val = float(p_match.group(1))
            else:
                return f"{'正相关' if coef_val > 0 else '负相关'} (p值解析失败)"

        # 3. 确定显著性
        if p_val < 0.01:
            significance = "非常显著 (***)"
        elif p_val < 0.05:
            significance = "显著 (**)"
        elif p_val < 0.1:
            significance = "弱显著 (*)"
        else:
            significance = "不显著"

        # 4. 确定方向 (仅当显著时)
        direction = ""
        if significance != "不显著":
            if coef_val > 0:
                direction = "，正相关"
            elif coef_val < 0:
                direction = "，负相关"

        # 5. 特殊处理截距
        if factor_display_name == '截距' or factor_display_name.lower() == 'const' or factor_display_name.lower() == 'intercept':
            # 对于截距，显著性通常表示是否存在Alpha (超额收益)
            if significance != "不显著":
                return f"{significance} (存在Alpha)"
            else:
                return f"{significance} (无Alpha)"
        else:
            return f"{significance}{direction}"

    except Exception as e:
        # 记录详细的错误信息以便调试
        # import traceback
        # print(f"解析系数错误: {coef_str}, 因子: {factor_display_name}")
        # print(f"错误: {str(e)}")
        # print(traceback.format_exc())
        return "解析错误"


def display_factor_regression_section(returns_df: Optional[pd.DataFrame], factor_data: Dict[str, pd.DataFrame], symbol_to_name: Optional[Dict[str, str]]):
    """
    显示因子回归分析部分
    
    Args:
        returns_df: 收益率数据框，可以为None
        factor_data: 因子数据字典
        symbol_to_name: 代码到名称的映射
    """
    st.subheader('因子回归分析')

    # 添加总体解释
    st.markdown("""
    ### 分析方法与目的
    
    因子回归分析采用线性回归模型，量化评估各风格因子对标的收益率的影响程度。该分析可以帮助：
    - 识别标的对不同市场风格的敏感度
    - 发现标的收益率的主要驱动因素
    - 对比不同标的的风格特征
    
    ### 模型说明
    
    我们使用 **OLS + Newey-West HAC** 回归方法，该方法特别适用于时间序列数据，可以处理：
    - 自相关：当前收益率与过去收益率的相关性
    - 异方差：收益率波动幅度的变化
    
    ### 共线性处理
    
    为确保结果可靠，我们使用了移除高相关性因子的方法处理共线性问题，这样可以：
    - 保持因子原始含义，便于解释
    - 提高系数估计的稳定性
    - 使模型更简洁高效

    """)
    
    # 如果有标的数据，计算并显示因子回归分析
    if returns_df is not None and not returns_df.empty:
        # 共线性处理选项
        with st.expander("共线性处理参数设置", expanded=False):
            st.markdown("""
            ### 共线性问题与处理方法
            
            共线性是指因子之间存在高相关性，会导致以下问题：
            - 回归系数估计不稳定，标准误差增大
            - 系数符号可能与经济学预期相反
            - 难以区分各因子的独立贡献
            
            本分析通过**移除高相关性因子**的方法处理共线性，保留信息量更大、独立性更强的因子。
            """)
            
            correlation_threshold = st.slider(
                "相关性阈值", 
                min_value=0.5, 
                max_value=1.0, 
                value=1.0, 
                step=0.05,
                help="当因子间的相关性绝对值超过该阈值时，将移除其中一个因子（保留方差大、VIF值低的因子）"
            )
            
            st.markdown("""
            **阈值选择指南**:
            - **0.5-0.6**: 严格控制共线性，移除较多因子，模型更简洁但可能丢失信息
            - **0.7-0.8**: 推荐设置，平衡因子保留和共线性控制
            - **>0.8**: 仅移除高度相关的因子，保留更多因子信息但可能存在轻微共线性
            
            **因子选择标准**：当两个因子相关性高时，系统会：
            1. 优先考虑VIF值（方差膨胀因子）：保留VIF值低的因子
            2. 其次考虑方差大小：保留方差大（信息量大）的因子
            """)
            
        # 计算因子回归
        regression_results, filtered_correlation_matrix = calculate_factor_regression(
            returns_df, 
            factor_data, 
            correlation_threshold=correlation_threshold
        )

        # 使用新函数显示因子回归分析结果
        display_factor_regression_analysis(regression_results, filtered_correlation_matrix, symbol_to_name, factor_code_to_display={'smb': '市值', 'hml': '价值', 'rmw': '盈利', 'cma': '投资'})


def run():
    """
    FF5风格分析页面
    1. 选标的（ETF或股票）
    2. 选时间段
    3. 分析市场风格因子
    """
    st.title('FF5风格分析')
    
    # 初始化session_state
    if 'added_symbols' not in st.session_state:
        st.session_state.added_symbols = []
    if 'factor_data' not in st.session_state:
        st.session_state.factor_data = None
    if 'corr_matrix' not in st.session_state:
        st.session_state.corr_matrix = None
    if 'start_date' not in st.session_state:
        st.session_state.start_date = (datetime.now() - timedelta(days=365)).date() # 确保是date类型
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime.now().date() # 确保是date类型
    
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
    
    # 快速选择时间范围
    time_range_options = {
        "选择时间范围": None,
        "最近1个月": timedelta(days=30),
        "最近3个月": timedelta(days=90),
        "最近1年": timedelta(days=365),
        "最近2年": timedelta(days=365*2),
        "最近3年": timedelta(days=365*3),
        "最近5年": timedelta(days=365*5),
        "最近10年": timedelta(days=365*10),
        "最近20年": timedelta(days=365*20)
    }
    
    # 使用 on_change 回调
    time_range = col3.selectbox(
        "快速选择",
        options=list(time_range_options.keys()),
        key="mkt_style_analysis_time_range",
        on_change=update_dates_from_selectbox # 绑定回调函数
    )
    
    # 直接从 session_state 获取日期值
    start_date = col1.date_input(
        "开始日期",
        value=st.session_state.start_date, # 直接使用 session_state
        key="mkt_style_analysis_start_date"
    )
    
    end_date = col2.date_input(
        "结束日期",
        value=st.session_state.end_date, # 直接使用 session_state
        key="mkt_style_analysis_end_date"
    )
    
    # 更新session_state中的日期 (这部分仍然需要，以捕获 date_input 的手动更改)
    # 只有当 date_input 的值发生变化时才更新 session_state，避免覆盖回调设置的值
    if st.session_state.start_date != start_date:
        st.session_state.start_date = start_date
    if st.session_state.end_date != end_date:
        st.session_state.end_date = end_date
        
    # 确保 start_date 和 end_date 是 datetime.date 类型，以便后续使用
    current_start_date = st.session_state.start_date
    current_end_date = st.session_state.end_date
    
    # 3. 处理添加标的
    if add_button:
        if current_start_date >= current_end_date:
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
        factor_data = get_factor_data(current_start_date, current_end_date) # 使用当前日期

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
                start_date=current_start_date, # 使用当前日期
                end_date=current_end_date # 使用当前日期
            )

        # 显示所有因子图表
        st.subheader('FF5因子走势')
        display_factor_charts(factor_data, returns_df, symbol_to_name)
        
        # 如果有添加的标的，显示相关性矩阵
        # 计算并显示相关性矩阵
        corr_matrix = calculate_factor_correlation(returns_df, factor_data)

        # 将相关性矩阵保存到session_state
        st.session_state.corr_matrix = corr_matrix
        
        # 使用新函数显示相关性矩阵
        display_correlation_matrix(corr_matrix, symbol_to_name, returns_df)
        
        # 显示因子回归分析部分
        display_factor_regression_section(returns_df, factor_data, symbol_to_name)

# 定义时间范围选择的回调函数
def update_dates_from_selectbox():
    """根据快速选择下拉框更新session_state中的日期"""
    time_range = st.session_state.mkt_style_analysis_time_range
    
    time_range_options = {
        "选择时间范围": None,
        "最近1个月": timedelta(days=30),
        "最近3个月": timedelta(days=90),
        "最近1年": timedelta(days=365),
        "最近2年": timedelta(days=365*2),
        "最近3年": timedelta(days=365*3),
        "最近5年": timedelta(days=365*5),
        "最近10年": timedelta(days=365*10),
        "最近20年": timedelta(days=365*20)
    }

    if time_range != "选择时间范围" and time_range_options[time_range] is not None:
        new_start_date = datetime.now() - time_range_options[time_range]
        st.session_state.start_date = new_start_date.date()
        st.session_state.end_date = datetime.now().date()
        # 注意：这里不需要再手动设置selectbox的值，让它自然保持选择状态
