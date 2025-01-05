import os
from typing import Dict
import streamlit as st


def run() -> None:
    """
    Run the knowledge base page.
    
    Displays a two-level dropdown to select articles by category and shows the selected article's HTML content.
    """
    # 文章分类和对应的文章映射
    article_categories: Dict[str, Dict[str, str]] = {
        "技术文章": {
            "DuckDB + Pandas，数据分析黄金搭档，效率提升 10 倍！": "duckdb_pandas_compare.html"
        }
    }
    
    # 创建分类下拉选择框
    selected_category = st.selectbox(
        "选择文章分类",
        options=list(article_categories.keys())
    )
    
    # 创建文章下拉选择框
    selected_article = st.selectbox(
        "选择要查看的文章",
        options=list(article_categories[selected_category].keys())
    )
    
    # 获取选中文章对应的html文件名
    html_file = article_categories[selected_category][selected_article]
    
    # 读取并显示html内容
    file_path = os.path.join(os.path.dirname(__file__), html_file)
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    st.components.v1.html(html_content, height=600, scrolling=True)