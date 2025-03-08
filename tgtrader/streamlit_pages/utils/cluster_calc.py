# encoding: utf-8

import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from typing import Dict, List, Tuple, Any, Optional

def perform_hierarchical_clustering(
    corr_matrix: pd.DataFrame, 
    method: str = 'complete', 
    optimal_ordering: bool = True
) -> Tuple[np.ndarray, List[str]]:
    """
    对相关性矩阵执行层次聚类
    
    Args:
        corr_matrix: 相关性矩阵
        method: 聚类方法，可选值包括 'single', 'complete', 'average', 'weighted', 'centroid', 'median', 'ward'
        optimal_ordering: 是否进行最优排序以使树状图更易读
        
    Returns:
        linkage_matrix: 聚类结果的链接矩阵
        labels: 聚类标签列表
    """
    # 获取标签
    labels = list(corr_matrix.columns)
    
    # 确保相关性矩阵是对称的
    corr_np = corr_matrix.values
    
    # 将相关系数转换为距离矩阵 (1 - 相关系数的绝对值)
    # 相关性越高，距离越小
    dist_matrix = 1 - np.abs(corr_np)
    
    # 确保对角线为0（自身与自身的距离为0）
    np.fill_diagonal(dist_matrix, 0)
    
    # 将方阵转换为压缩的距离向量（上三角矩阵的扁平表示）
    try:
        condensed_dist = squareform(dist_matrix)
    except ValueError as e:
        # 如果squareform失败，可能是因为矩阵不是对称的或有其他问题
        # 尝试手动提取上三角矩阵
        n = len(dist_matrix)
        condensed_dist = np.zeros(n * (n - 1) // 2)
        k = 0
        for i in range(n):
            for j in range(i + 1, n):
                condensed_dist[k] = dist_matrix[i, j]
                k += 1
    
    # 执行层次聚类
    linkage_matrix = linkage(
        condensed_dist,
        method=method,
        optimal_ordering=optimal_ordering
    )
    
    return linkage_matrix, labels

def get_clusters(
    linkage_matrix: np.ndarray, 
    labels: List[str], 
    num_clusters: int = 3,
    criterion: str = 'maxclust'
) -> Dict[int, List[str]]:
    """
    根据层次聚类结果获取聚类分组
    
    Args:
        linkage_matrix: 聚类结果的链接矩阵
        labels: 聚类标签列表
        num_clusters: 聚类数量
        criterion: 聚类标准，可选值包括：
                  'maxclust': 指定簇的数量
                  'distance': 指定距离阈值
                  'inconsistent': 指定不一致性系数阈值
                  'monocrit': 指定单调性准则
                  'maxclust_monocrit': 指定簇的数量，使用单调性准则
        
    Returns:
        clusters: 聚类结果字典，键为聚类ID，值为该聚类中的标签列表
    """
    # 获取聚类分配
    cluster_assignments = fcluster(linkage_matrix, num_clusters, criterion=criterion)
    
    # 创建聚类结果字典
    clusters = {}
    for i, cluster_id in enumerate(cluster_assignments):
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(labels[i])
    
    return clusters