# encoding: utf-8

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import plotly.graph_objects as go
from datetime import datetime
import random

def get_tag_color(tag: str) -> str:
    """
    根据标签内容返回固定的颜色
    
    Args:
        tag: 标签文本
    
    Returns:
        str: 颜色代码
    """
    # 为常见标签定义固定颜色
    color_map = {
        'AI': '#007bff',  # 蓝色
        '股价上涨': '#28a745',  # 绿色
        '股价下跌': '#dc3545',  # 红色
        '中概股普涨': '#28a745',  # 绿色
        '指数上升': '#28a745',  # 绿色
        '指数下跌': '#dc3545',  # 红色
        '科技': '#17a2b8',  # 青色
        '金融': '#6f42c1',  # 紫色
        '能源': '#fd7e14',  # 橙色
        '医疗': '#20c997',  # 青绿色
    }
    
    return color_map.get(tag, '#6c757d')  # 默认返回灰色

def render_tags(tags: List[str]) -> None:
    """
    渲染彩色标签
    
    Args:
        tags: 标签列表
    """
    # CSS样式
    st.markdown("""
        <style>
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 4px;
        }
        .tag {
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 14px;
            color: white;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 生成标签HTML
    tags_html = '<div class="tag-container">'
    for tag in tags:
        color = get_tag_color(tag)
        tags_html += f'<span class="tag" style="background-color: {color}">{tag}</span>'
    tags_html += '</div>'
    
    st.markdown(tags_html, unsafe_allow_html=True)

def render_sentiment_gauge(sentiment: float, title: str) -> None:
    """
    渲染情感分析仪表盘
    
    Args:
        sentiment: 情感值 (0-1)
        title: 仪表盘标题
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sentiment * 100,
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ],
        }
    ))
    fig.update_layout(height=200)
    st.plotly_chart(fig, use_container_width=True)

def render_impact_analysis(data: Dict[str, Any]) -> None:
    """
    渲染影响分析部分
    
    Args:
        data: 新闻数据字典
    """
    # 创建三列布局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🏭 行业影响")
        for industry in data['related_industries']:
            st.metric(
                label=industry['industry'],
                value=f"{industry['sentiment']:.2%}"
            )
    
    with col2:
        st.subheader("📊 指数影响")
        for index in data['related_indexes']:
            st.metric(
                label=index['index'],
                value=f"{index['sentiment']:.2%}"
            )
    
    with col3:
        st.subheader("🏢 公司影响")
        for company in data['related_company']:
            st.metric(
                label=company['company'],
                value=f"{company['sentiment']:.2%}"
            )

def render_news_details(data: Dict[str, Any]) -> None:
    """
    渲染新闻详情部分
    
    Args:
        data: 新闻数据字典
    """
    st.header("📰 新闻详情")
    
    # 新闻标题和时间
    st.subheader(data['title'])
    st.caption(f"发布时间: {data['pub_time']}")
    
    # 基本信息
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**国家/地区:** {data['country']}")
        st.markdown(f"**相关市场:** {', '.join(data['markets'])}")
    with col2:
        st.markdown("**标签:**")
        render_tags(data['tags'])
        st.markdown(f"**整体情感:** {data['sentiment']:.2%}")
    
    # 新闻正文
    st.markdown("### 新闻内容")
    st.markdown(data['description'])

def render_news_list(news_list: List[Dict[str, Any]]) -> int:
    """
    渲染新闻列表，返回选中的新闻索引
    
    Args:
        news_list: 新闻列表
    
    Returns:
        int: 选中的新闻索引
    """
    st.header("📋 新闻列表")
    
    selected_index = 0
    for i, news in enumerate(news_list):
        # 创建可点击的新闻卡片
        with st.container():
            if st.button(
                f"📰 {news['title']}\n\n"
                f"📅 {news['pub_time']}\n"
                f"🌍 {news['country']} | 💹 情感: {news['sentiment']:.2%}",
                key=f"news_{i}",
                use_container_width=True
            ):
                selected_index = i
            # 显示标签
            render_tags(news['tags'])
            st.markdown("---")
    
    return selected_index

def run():
    """
    主函数，渲染整个新闻分析页面
    """
    st.title("📊 新闻监控分析系统")
    
    # 示例数据 - 多条新闻
    sample_news_list = [
        {
            'title': "纳斯达克中国金龙指数收涨3.72% 热门中概股普涨",
            'description': "【纳斯达克中国金龙指数收涨3.72% 热门中概股普涨】财联社1月25日电，纳斯达克中国金龙指数收涨3.72%，本周累计上涨2.8%，热门中概股普涨，金山云涨超13%，爱奇艺涨超11%，京东、好未来涨超5%，百度、名创优品涨超4%，蔚来、小鹏汽车涨超3%。",
            'pub_time': "2025-01-25 05:00:56",
            'country': "中国",
            'markets': ['纳斯达克'],
            'tags': ['中概股普涨', '指数上升'],
            'related_industries': [
                {'industry': '信息技术', 'sentiment': 0.8},
                {'industry': '可选消费', 'sentiment': 0.75}
            ],
            'sentiment': 0.85,
            'related_indexes': [
                {'index': '纳斯达克中国金龙指数', 'sentiment': 0.85}
            ],
            'related_company': [
                {'company': '金山云', 'sentiment': 0.9},
                {'company': '爱奇艺', 'sentiment': 0.85}
            ]
        },
        {
            'title': "ChatGPT发布重大更新 OpenAI股价大涨",
            'description': "OpenAI今日发布ChatGPT重大更新，新增多模态分析能力，股价应声大涨15%。",
            'pub_time': "2025-01-25 04:30:00",
            'country': "美国",
            'markets': ['纳斯达克', '纽约证券交易所'],
            'tags': ['AI', '股价上涨'],
            'related_industries': [
                {'industry': '人工智能', 'sentiment': 0.95},
                {'industry': '科技', 'sentiment': 0.9}
            ],
            'sentiment': 0.9,
            'related_indexes': [
                {'index': '纳斯达克100', 'sentiment': 0.8}
            ],
            'related_company': [
                {'company': 'OpenAI', 'sentiment': 0.95},
                {'company': 'Microsoft', 'sentiment': 0.85}
            ]
        }
    ]

    
    
    # 创建左右两栏布局
    left_col, right_col = st.columns([1, 2])
    
    # 左侧新闻列表
    with left_col:
        selected_index = render_news_list(sample_news_list)
    
    # 右侧新闻详情和分析
    with right_col:
        selected_news = sample_news_list[selected_index]
        
        # 渲染新闻详情
        render_news_details(selected_news)
        
        # 渲染整体情感仪表盘
        st.markdown("### 📈 整体情感分析")
        render_sentiment_gauge(selected_news['sentiment'], "新闻整体情感倾向")
        
        # 渲染影响分析
        st.markdown("### 🎯 影响分析")
        render_impact_analysis(selected_news)
