# encoding utf-8

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from typing import Dict, List, Tuple, Any, Optional
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import dendrogram, fcluster

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem, build_stock_dropdown_list
from tgtrader.streamlit_pages.utils.corr_calc import (
    get_price_data,
    calculate_correlation,
    find_positive_correlated_pairs,
    find_negative_correlated_pairs,
    find_low_correlated_pairs,
    prepare_dendrogram_data,
    prepare_distance_matrix
)
from tgtrader.streamlit_pages.utils.cluster_calc import (
    perform_hierarchical_clustering,
    get_clusters
)
from typing import Dict, List, Tuple


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


def run():
    """
    相关性分析页面
    1. 选标的（ETF或股票）
    2. 选时间段
    3. 计算相关性矩阵
    """
    st.title('相关性分析')
    
    # 1. 标的选择
    data_getter = DataGetter()
    
    symbol_multiselect: list[StockDropdownSelectItem] = build_stock_dropdown_list(
        src_page='corr_analysis', 
        data_getter=data_getter
    )
    
    # 2. 时间段选择
    col1, col2 = st.columns(2)
    
    # 默认开始日期为一年前
    default_start_date = datetime.now() - timedelta(days=365)
    default_end_date = datetime.now()
    
    start_date = col1.date_input(
        "开始日期",
        value=default_start_date,
        key="corr_analysis_start_date"
    )
    
    end_date = col2.date_input(
        "结束日期",
        value=default_end_date,
        key="corr_analysis_end_date"
    )
    
    # 3. 计算相关性矩阵
    if st.button('计算相关性', type='primary'):
        if not symbol_multiselect:
            st.error('请选择至少两个标的')
            return
            
        if len(symbol_multiselect) < 2:
            st.error('请选择至少两个标的进行相关性分析')
            return
            
        if start_date >= end_date:
            st.error('开始日期必须早于结束日期')
            return
        
        with st.spinner('正在计算相关性...'):
            # 准备证券类型字典和代码到名称的映射
            symbols_dict, symbol_to_name = prepare_symbols_dict(symbol_multiselect)
            
            # 获取价格数据并计算收益率
            pivot_df, returns_df, normalized_prices = get_price_data(
                data_getter=data_getter,
                symbols_dict=symbols_dict,
                start_date=start_date,
                end_date=end_date
            )
            
            if pivot_df is None or returns_df is None or normalized_prices is None:
                st.error('无法获取所选标的的价格数据')
                return
            
            # 计算相关性矩阵
            corr_matrix = calculate_correlation(returns_df, symbol_to_name)
            
            # 显示相关性矩阵
            st.subheader('相关性矩阵')
            st.dataframe(corr_matrix.style.background_gradient(cmap='coolwarm', axis=None, vmin=-1, vmax=1))
            
            # 添加相关系数文本标签
            annotations = []
            for i, index in enumerate(corr_matrix.index):
                for j, column in enumerate(corr_matrix.columns):
                    annotations.append(
                        dict(
                            x=j,
                            y=i,
                            text=str(round(corr_matrix.iloc[i, j], 2)),
                            showarrow=False,
                            font=dict(color="black" if abs(corr_matrix.iloc[i, j]) < 0.7 else "white")
                        )
                    )
            
            # 显示收益率时间序列
            st.subheader('收益率时间序列')
            
            # 为每个标的创建一个时间序列图
            fig_returns = go.Figure()
            
            for col in returns_df.columns:
                fig_returns.add_trace(
                    go.Scatter(
                        x=returns_df.index,
                        y=returns_df[col],
                        mode='lines',
                        name=f"{col} ({symbol_to_name.get(col, '')})"
                    )
                )
            
            fig_returns.update_layout(
                height=500,
                width=800,
                title="每日收益率时间序列",
                xaxis_title="日期",
                yaxis_title="收益率",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_returns)
            
            # 显示价格时间序列
            st.subheader('价格时间序列')
            
            # 为每个标的创建一个价格时间序列图
            fig_prices = go.Figure()
            
            # 将价格标准化为起始日期的100
            for col in normalized_prices.columns:
                fig_prices.add_trace(
                    go.Scatter(
                        x=normalized_prices.index,
                        y=normalized_prices[col],
                        mode='lines',
                        name=f"{col} ({symbol_to_name.get(col, '')})"
                    )
                )
            
            fig_prices.update_layout(
                height=500,
                width=800,
                title="标准化价格时间序列 (起始=100)",
                xaxis_title="日期",
                yaxis_title="标准化价格",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_prices)
            
            # 分析结果
            st.subheader('相关性分析结果')
            
            # 使用工具模块中的函数获取相关性对
            positive_corr_pairs = find_positive_correlated_pairs(corr_matrix, threshold=0.7)
            negative_corr_pairs = find_negative_correlated_pairs(corr_matrix, threshold=-0.7)
            low_corr_pairs = find_low_correlated_pairs(corr_matrix, threshold=0.3)
            
            # 创建三个表格
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("#### 高度正相关的标的对")
                if positive_corr_pairs:
                    # 创建DataFrame以表格形式显示
                    df_positive = pd.DataFrame(
                        [(p[0], p[1], f"{p[2]:.4f}") for p in positive_corr_pairs],
                        columns=["标的1", "标的2", "相关系数"]
                    )
                    st.dataframe(df_positive, use_container_width=True)
                else:
                    st.write("没有发现高度正相关的标的对（相关系数 > 0.7）")
            
            with col2:
                st.write("#### 高度负相关的标的对")
                if negative_corr_pairs:
                    # 创建DataFrame以表格形式显示
                    df_negative = pd.DataFrame(
                        [(p[0], p[1], f"{p[2]:.4f}") for p in negative_corr_pairs],
                        columns=["标的1", "标的2", "相关系数"]
                    )
                    st.dataframe(df_negative, use_container_width=True)
                else:
                    st.write("没有发现高度负相关的标的对（相关系数 < -0.7）")
            
            with col3:
                st.write("#### 低相关的标的对")
                if low_corr_pairs:
                    # 创建DataFrame以表格形式显示
                    df_low = pd.DataFrame(
                        [(p[0], p[1], f"{p[2]:.4f}") for p in low_corr_pairs],
                        columns=["标的1", "标的2", "相关系数"]
                    )
                    st.dataframe(df_low, use_container_width=True)
                else:
                    st.write("没有发现低相关的标的对（相关系数绝对值 < 0.3）")
            
            
            # 层次聚类分析
            st.subheader('层次聚类分析')
            
            # 调用聚类分析函数
            perform_cluster_analysis(corr_matrix)


@st.fragment
def perform_cluster_analysis(corr_matrix: pd.DataFrame) -> None:
    """
    执行层次聚类分析并展示结果
    
    Args:
        corr_matrix: 相关性矩阵
        
    Returns:
        None
    """
    # 聚类方法选择
    clustering_methods = {
        'average': '平均连接 (Average)',
        'ward': 'Ward方法 (Ward)',
        'complete': '完全连接 (Complete)',
        'single': '单连接 (Single)',
    }
    
    # 聚类方法的详细解释
    clustering_methods_explanations = {
        'complete': """
        **完全连接法 (Complete Linkage)**
        
        计算两个聚类中所有点对之间的最大距离。
        
        特点：
        - 倾向于创建紧凑、大小相似的聚类
        - 对异常值敏感
        - 适合发现相似大小的聚类
        
        适用场景：当您希望聚类大小相对均匀，且数据中没有太多异常值时
        
        **股票量化应用举例：**
        在股票分类中，完全连接法适合将市场分割为规模相近的板块。例如，可以将沪深300成分股按照相关性分为大小相近的几个行业板块，每个板块内部股票的相关性较高，不同板块之间相关性较低。这种方法有助于构建多元化的投资组合，在不同板块间分散风险。
        """,
        
        'single': """
        **单连接法 (Single Linkage)**
        
        计算两个聚类中所有点对之间的最小距离。
        
        特点：
        - 可以处理非椭圆形状的聚类
        - 容易受到噪声和异常值的影响
        - 可能产生"链式效应"，形成细长的聚类
        
        适用场景：当您的数据可能形成不规则形状的聚类，或者您想检测异常值时
        
        **股票量化应用举例：**
        单连接法适合发现市场中的异常股票或特殊关联。例如，在分析ETF与其成分股的关系时，可以识别出那些与大多数成分股行为不同的"异常股"。这些异常股可能代表了套利机会或风险信号。此外，单连接法也适合发现跨行业的关联链，如发现从原材料到终端产品的产业链关系。
        """,
        
        'average': """
        **平均连接法 (Average Linkage)**
        
        计算两个聚类中所有点对之间距离的平均值。
        
        特点：
        - 比单连接和完全连接更稳健
        - 不太容易受到异常值的影响
        - 通常产生更自然的聚类结构
        
        适用场景：当您希望得到一个平衡的聚类结果，既不像单连接那样敏感，也不像完全连接那样严格时
        
        **股票量化应用举例：**
        平均连接法是量化投资中最常用的聚类方法之一。它能够平衡地识别市场结构，适合构建风险平价投资组合。例如，可以将股票市场按照平均相关性分为周期性板块、防御性板块、成长板块等，然后在每个板块中选择代表性股票构建投资组合。这种方法既考虑了板块内部的相似性，也保持了不同板块之间的差异性，有助于在不同市场环境下保持稳定表现。
        """,
        
        'ward': """
        **Ward方法 (Ward's Method)**
        
        基于最小化聚类内方差的原则进行聚类。
        
        特点：
        - 倾向于创建大小相等的聚类
        - 对异常值不太敏感
        - 通常产生紧凑且球形的聚类
        
        适用场景：当您希望得到紧凑、大小相似的聚类，且数据分布相对均匀时
        
        **股票量化应用举例：**
        Ward方法特别适合构建因子投资组合。例如，在多因子选股模型中，可以使用Ward方法将股票按照估值、动量、质量等多维因子特征进行聚类，形成具有相似因子暴露的股票组合。由于Ward方法倾向于创建方差最小的聚类，这有助于构建因子纯度高、内部相关性强的投资组合，减少组合内部的特异性风险。在风格轮动策略中，Ward方法也有助于清晰地区分不同投资风格的股票组合。
        """
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 创建一个包含问号的标题
        st.markdown("<div style='display: flex; align-items: center;'><span>聚类方法</span> <span title='点击查看聚类方法说明' style='cursor: help; margin-left: 5px;'>❓</span></div>", unsafe_allow_html=True)
        
        selected_method = st.selectbox(
            label="选择聚类方法",
            options=list(clustering_methods.keys()),
            format_func=lambda x: clustering_methods[x],
            index=0,
            key="clustering_method",
            label_visibility="collapsed"
        )
        
        # 显示所选聚类方法的解释
        with st.expander("查看聚类方法说明"):
            st.markdown(clustering_methods_explanations[selected_method])
    
    with col2:
        num_clusters = st.slider(
            "聚类数量",
            min_value=2,
            max_value=min(10, len(corr_matrix)),
            value=3,
            key="num_clusters"
        )
    
    try:
        # 执行层次聚类
        with st.spinner('正在计算层次聚类...'):
            # 打印调试信息
            # st.write(f"相关性矩阵维度: {corr_matrix.shape}")
            
            # 执行层次聚类
            linkage_matrix, labels = perform_hierarchical_clustering(
                corr_matrix=corr_matrix,
                method=selected_method,
                optimal_ordering=True
            )
            
            # 打印调试信息
            # st.write(f"链接矩阵维度: {linkage_matrix.shape}, 标签数量: {len(labels)}")
            
            # 创建树状图
            dendrogram_fig = create_dendrogram_figure(
                linkage_matrix=linkage_matrix,
                labels=labels,
                title=f"层次聚类树状图 (方法: {clustering_methods[selected_method]})",
                height=600,
                width=800,
                num_clusters=num_clusters,
                criterion='maxclust'
            )
            
            # 显示树状图
            st.plotly_chart(dendrogram_fig)
            
            # 获取聚类结果
            clusters = get_clusters(
                linkage_matrix=linkage_matrix,
                labels=labels,
                num_clusters=num_clusters,
                criterion='maxclust'  # 添加聚类标准参数
            )
            
            # 显示聚类结果
            st.subheader(f"聚类结果 (分为 {num_clusters} 组)")
            
            # 创建聚类结果表格
            cluster_data = []
            for cluster_id, cluster_items in clusters.items():
                for item in cluster_items:
                    cluster_data.append({
                        "聚类ID": int(cluster_id),
                        "标的": item
                    })
            
            cluster_df = pd.DataFrame(cluster_data)
            cluster_df.sort_values(by="聚类ID", inplace=True)
            st.dataframe(cluster_df, use_container_width=False)
    except Exception as e:
        st.error(f"层次聚类过程中出错: {str(e)}")
        st.write("请尝试选择不同的聚类方法或检查数据")


def create_dendrogram_figure(
    linkage_matrix: np.ndarray, 
    labels: List[str], 
    title: str = "层次聚类树状图",
    height: int = 600,
    width: int = 900,
    color_threshold: Optional[float] = None,
    num_clusters: int = 5,
    criterion: str = 'maxclust'
) -> Any:
    """
    创建层次聚类树状图
    
    Args:
        linkage_matrix: 聚类结果的链接矩阵
        labels: 聚类标签列表
        title: 图表标题
        height: 图表高度
        width: 图表宽度
        color_threshold: 颜色阈值，用于确定何时更改树枝的颜色
        num_clusters: 聚类数量，默认为5
        criterion: 聚类标准，可选值包括：
                  'maxclust': 指定簇的数量
                  'distance': 指定距离阈值
                  'inconsistent': 指定不一致性系数阈值
                  'monocrit': 指定单调性准则
                  'maxclust_monocrit': 指定簇的数量，使用单调性准则
        
    Returns:
        fig: Plotly图表对象
    """
    try:
        # 生成聚类数据
        sorted_matrix, sorted_labels, color_map, boundaries, actual_num_clusters = prepare_dendrogram_data(
            linkage_matrix, labels, num_clusters, criterion
        )
        
        # 创建热图，使用离散的颜色刻度
        fig = px.imshow(
            sorted_matrix,
            x=sorted_labels,
            y=sorted_labels,
            color_continuous_scale='viridis_r',  # 反转颜色，使相似度高的显示为深色
            title=f"{title} (聚类视图，分为 {actual_num_clusters} 组)"
        )
        
        # 添加聚类边界
        # 添加水平和垂直线来标识聚类边界
        for b in boundaries[1:]:  # 跳过第一个边界，它通常是 -0.5
            fig.add_shape(
                type="line",
                x0=b, y0=-0.5,
                x1=b, y1=len(labels)-0.5,
                line=dict(color="white", width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=-0.5, y0=b,
                x1=len(labels)-0.5, y1=b,
                line=dict(color="white", width=2),
                layer="below"
            )
        
        # 更新布局
        fig.update_layout(
            height=height,
            width=width,
            xaxis=dict(side="top"),
            coloraxis_showscale=False,
            margin=dict(t=120, r=20, l=20, b=20),  
            title=dict(
                text=f"{title} (聚类视图，分为 {actual_num_clusters} 组)",
                y=0.98,  
                x=0.5,
                xanchor='center',
                yanchor='top'
            )
        )

        return fig
            
    except Exception as e:
        print(f"Error creating cluster heatmap: {str(e)}")
        # 如果上述方法失败，使用备用方法
    
        # 备用方法：创建一个简单的热图
        try:
            # 使用corr_calc中的函数准备距离矩阵
            dist_full, display_labels = prepare_distance_matrix(linkage_matrix, labels)
            
            if dist_full is not None and display_labels is not None:
                # 创建热图
                fig = px.imshow(
                    dist_full,
                    x=display_labels,
                    y=display_labels,
                    color_continuous_scale='viridis_r',
                    title=f"{title} (距离矩阵)"
                )
                
                fig.update_layout(
                    height=height,
                    width=width,
                    margin=dict(t=120, r=20, l=20, b=20),  
                    title=dict(
                        text=f"{title} (距离矩阵)",
                        y=0.98,  
                        x=0.5,
                        xanchor='center',
                        yanchor='top'
                    )
                )
                
                return fig
        except Exception as e:
            print(f"Error creating distance matrix visualization: {str(e)}")
        
        # 如果所有方法都失败，返回一个简单的错误信息图表
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"无法创建树状图: {str(e)}",
            showarrow=False,
            font=dict(size=14)
        )
        
        fig.update_layout(
            title="无法创建树状图",
            height=height,
            width=width,
            margin=dict(t=120, r=20, l=20, b=20),  
            title_y=0.98  
        )
        
        return fig
