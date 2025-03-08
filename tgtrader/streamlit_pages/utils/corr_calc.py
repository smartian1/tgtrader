# encoding: utf-8

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from scipy.cluster.hierarchy import fcluster
from scipy.spatial.distance import squareform
from streamlit import logger

from tgtrader.common import SecurityType
from tgtrader.data import DataGetter
from tgtrader.streamlit_pages.pages.component.stock_dropdown_list import StockDropdownSelectItem



def get_price_data(data_getter: DataGetter, 
                  symbols_dict: Dict[SecurityType, List[str]], 
                  start_date: datetime, 
                  end_date: datetime) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    获取价格数据并计算收益率
    
    Args:
        data_getter: 数据获取器
        symbols_dict: 证券类型到代码列表的字典
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        pivot_df: 价格数据透视表
        returns_df: 收益率数据
        normalized_prices: 标准化价格数据
    """
    # 获取每种类型的价格数据
    dfs = []
    
    for security_type, symbols in symbols_dict.items():
        # 将日期转换为字符串格式
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 获取价格数据
        price_df = data_getter.get_price(
            symbol_list=symbols,
            start_date=start_date_str,
            end_date=end_date_str,
            security_type=security_type,
            fields=["close"]
        )
        
        if not price_df.empty:
            dfs.append(price_df)
    
    if not dfs:
        return None, None, None
        
    # 合并所有价格数据
    combined_df = pd.concat(dfs)
    
    # 数据透视，将多级索引转换为单级索引的DataFrame
    # 结果格式: 行为日期，列为标的代码
    pivot_df = combined_df.unstack(level=0)
    pivot_df.columns = pivot_df.columns.droplevel(0)  # 删除'close'级别
    
    # 计算每日收益率
    returns_df = pivot_df.pct_change().dropna()
    
    # 将价格标准化为起始日期的100
    normalized_prices = pivot_df / pivot_df.iloc[0] * 100
    
    return pivot_df, returns_df, normalized_prices


def calculate_correlation(returns_df: pd.DataFrame, symbol_to_name: Dict[str, str]) -> pd.DataFrame:
    """
    计算相关性矩阵
    
    Args:
        returns_df: 收益率数据
        symbol_to_name: 代码到名称的映射
        
    Returns:
        corr_matrix: 相关性矩阵
    """
    # 计算相关性矩阵
    corr_matrix = returns_df.corr()
    
    # 重命名列和索引，使用标的名称而不是代码
    corr_matrix.columns = [f"{col} ({symbol_to_name.get(col, '')})" for col in corr_matrix.columns]
    corr_matrix.index = [f"{idx} ({symbol_to_name.get(idx, '')})" for idx in corr_matrix.index]
    
    return corr_matrix


def find_positive_correlated_pairs(corr_matrix, threshold=0.7):
    """
    找出正相关性最高的标的对
    
    Args:
        corr_matrix: 相关性矩阵
        threshold: 高度正相关的阈值，默认为0.7
        
    Returns:
        正相关性最高的标的对列表，每个元素为(标的1, 标的2, 相关系数)的元组
    """
    positive_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            if corr_value > threshold:
                positive_corr_pairs.append((
                    corr_matrix.columns[i],
                    corr_matrix.columns[j],
                    corr_value
                ))
    
    # 按相关系数降序排序
    positive_corr_pairs.sort(key=lambda x: x[2], reverse=True)
    
    return positive_corr_pairs


def find_negative_correlated_pairs(corr_matrix, threshold=-0.7):
    """
    找出负相关性最高的标的对
    
    Args:
        corr_matrix: 相关性矩阵
        threshold: 高度负相关的阈值，默认为-0.7
        
    Returns:
        负相关性最高的标的对列表，每个元素为(标的1, 标的2, 相关系数)的元组
    """
    negative_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            if corr_value < threshold:
                negative_corr_pairs.append((
                    corr_matrix.columns[i],
                    corr_matrix.columns[j],
                    corr_value
                ))
    
    # 按相关系数升序排序（负相关越强，值越小）
    negative_corr_pairs.sort(key=lambda x: x[2])
    
    return negative_corr_pairs


def find_low_correlated_pairs(corr_matrix, threshold=0.3):
    """
    找出相关性最低的标的对
    
    Args:
        corr_matrix: 相关性矩阵
        threshold: 低相关的阈值，默认为0.3
        
    Returns:
        相关性最低的标的对列表，每个元素为(标的1, 标的2, 相关系数)的元组
    """
    low_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) < threshold:
                low_corr_pairs.append((
                    corr_matrix.columns[i],
                    corr_matrix.columns[j],
                    corr_value
                ))
    
    # 按相关系数绝对值升序排序（相关性越低，绝对值越小）
    low_corr_pairs.sort(key=lambda x: abs(x[2]))
    
    return low_corr_pairs


def prepare_dendrogram_data(
    linkage_matrix: np.ndarray, 
    labels: List[str], 
    num_clusters: int = 5,
    criterion: str = 'maxclust'
) -> Tuple[np.ndarray, List[str], Dict[int, float], List[float], int]:
    """
    准备层次聚类树状图所需的数据
    
    Args:
        linkage_matrix: 聚类结果的链接矩阵
        labels: 聚类标签列表
        num_clusters: 聚类数量，默认为5
        criterion: 聚类标准，可选值包括：
                  'maxclust': 指定簇的数量
                  'distance': 指定距离阈值
                  'inconsistent': 指定不一致性系数阈值
                  'monocrit': 指定单调性准则
                  'maxclust_monocrit': 指定簇的数量，使用单调性准则
        
    Returns:
        sorted_matrix: 按聚类排序后的矩阵
        sorted_labels: 按聚类排序后的标签
        color_map: 聚类ID到颜色值的映射
        boundaries: 聚类边界位置列表
        actual_num_clusters: 实际聚类数量
    """
    # 生成聚类组，使用传入的聚类数量
    cluster_assignments = fcluster(linkage_matrix, num_clusters, criterion=criterion)

    # 按聚类结果排序标签
    idx_order = np.argsort(cluster_assignments)
    sorted_labels = [labels[i] for i in idx_order]
    
    # 为每个聚类分配一个序号
    cluster_to_id = {}
    for i, cluster_id in enumerate(cluster_assignments[idx_order]):
        if cluster_id not in cluster_to_id:
            cluster_to_id[cluster_id] = len(cluster_to_id)
    
    # 创建热图矩阵 - 使用离散的颜色值而不是连续值
    sorted_matrix = np.zeros((len(labels), len(labels)))
    
    # 获取实际的聚类数量
    unique_clusters = np.unique(cluster_assignments)
    actual_num_clusters = len(unique_clusters)
    
    # 创建一个颜色映射字典，为每个聚类分配一个唯一的颜色值
    color_map = {}
    for i, cluster_id in enumerate(unique_clusters):
        # 使用离散的颜色值，确保每个聚类有明显不同的颜色
        color_map[cluster_id] = i / (actual_num_clusters - 1) if actual_num_clusters > 1 else 0.5
    
    for i in range(len(labels)):
        for j in range(len(labels)):
            cluster_i = cluster_assignments[idx_order[i]]
            cluster_j = cluster_assignments[idx_order[j]]
            
            if cluster_i == cluster_j:
                # 同一聚类内部显示为相同颜色
                sorted_matrix[i, j] = color_map[cluster_i]
            else:
                # 不同聚类之间使用固定值，以便在视觉上区分
                # 使用一个与所有聚类颜色都不同的值
                sorted_matrix[i, j] = 1.0
    
    # 找到每个聚类的边界
    boundaries = []
    prev_cluster = None
    for i, cluster_id in enumerate(cluster_assignments[idx_order]):
        if prev_cluster != cluster_id:
            boundaries.append(i - 0.5)
            prev_cluster = cluster_id
    
    return sorted_matrix, sorted_labels, color_map, boundaries, actual_num_clusters


def prepare_distance_matrix(linkage_matrix: np.ndarray, labels: List[str]) -> Tuple[np.ndarray, List[str]]:
    """
    从linkage矩阵准备距离矩阵用于可视化
    
    Args:
        linkage_matrix: 聚类结果的链接矩阵
        labels: 聚类标签列表
        
    Returns:
        dist_full: 完整距离矩阵
        display_labels: 用于显示的标签
    """
    try:
        # 尝试转换为condensed距离矩阵
        condensed_dist = squareform(linkage_matrix)
        
        # 确保矩阵大小匹配
        n = int((1 + np.sqrt(1 + 8 * len(condensed_dist))) / 2)
        if n > len(labels):
            padded_labels = labels + [f"Item {i+1}" for i in range(len(labels), n)]
            display_labels = padded_labels
        else:
            display_labels = labels[:n]
        
        # 转换为完整距离矩阵
        dist_full = squareform(condensed_dist)
        
        return dist_full, display_labels
    except Exception as e:
        print(f"Error preparing distance matrix: {str(e)}")
        return None, None