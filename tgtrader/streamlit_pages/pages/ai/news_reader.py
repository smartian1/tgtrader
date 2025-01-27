# encoding: utf-8

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import plotly.graph_objects as go
from datetime import datetime
import random
from tgtrader.streamlit_pages.utils.common import get_user_name
from tgtrader.dao.t_news_datasource import TNewsDataSource
from tgtrader.utils.db_wrapper import DBWrapper, DBType, DynamicTableWrapper
from tgtrader.dao.t_user_table_meta import UserTableMeta
from tgtrader.utils.defs import USER_TABLE_DB_NAME
from loguru import logger
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode


def get_dynamic_table_wrapper():
    table_name = TNewsDataSource.select().where(TNewsDataSource.username == get_user_name()).first().table_name
    if not table_name:
        st.error("请先配置新闻数据源表")
        return
    user_table_meta = UserTableMeta.get_table_meta(get_user_name(), USER_TABLE_DB_NAME, table_name)
    if not user_table_meta:
        st.error("请先配置新闻数据源表")
        return
    db_path = user_table_meta.db_path
    field_config = user_table_meta.columns_info

    dynamic_table_wrapper = DynamicTableWrapper(table_name=table_name, db_path=db_path, db_type=DBType.DUCKDB, field_config=field_config)
    return dynamic_table_wrapper

def get_news_list(limit_cnt=50):
    """
    获取新闻列表，过滤掉国家为空或null的新闻

    Args:
        limit_cnt (int, optional): 获取新闻的数量限制. Defaults to 50.

    Returns:
        list: 过滤后的新闻列表
    """
    table_wrapper = get_dynamic_table_wrapper()
    model = table_wrapper.get_model()
    query = model.select() \
        .where((model.country != "") & model.country.is_null(False)) \
        .limit(limit_cnt) \
        .order_by(model.create_time.desc())

    news_list = list(query.dicts())

    json_columns = ['tags', 'markets', 'related_industries', 'related_indexes', 'related_company']
    
    for news in news_list:
        for column in json_columns:
            if news[column]:
                try:
                    news[column] = json.loads(news[column])
                except json.JSONDecodeError:
                    pass
        
        # 将情绪值从0-1转换为-100到100的范围
        news['sentiment'] = int(float(news['sentiment']) * 100)

    return news_list



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
            gap: 4px;
            margin: 0;
            padding: 0;
        }
        .tag {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 16px;
            font-size: 14px;
            color: #333;
            white-space: nowrap;
            margin: 2px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 淡雅的颜色调色板
    pastel_colors = [
        '#90EE90',  # 浅绿色
        '#87CEFA',  # 浅天蓝色
        '#FFA07A',  # 浅鲑鱼色
        '#20B2AA',  # 浅海洋绿
        '#00CED1',  # 深绿松石色
        '#1E90FF',  # 道奇蓝
        '#FF7F50',  # 珊瑚色
        '#3CB371'   # 中海洋绿
    ]
    
    # 生成标签HTML
    tags_html = '<div class="tag-container">'
    for tag in tags:
        color = random.choice(pastel_colors)
        tags_html += f'<div class="tag" style="background-color: {color};">{tag}</div>'
    tags_html += '</div>'
    
    st.markdown(tags_html, unsafe_allow_html=True)

def render_sentiment_gauge(sentiment: int, title: str) -> None:
    """
    渲染情绪分析仪表盘
    
    Args:
        sentiment: 情绪值 (0-1)
        title: 仪表盘标题
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sentiment,
        title={
            'text': title, 
            'font': {'size': 16},
        },
        number={'font': {'size': 30}},  # 调整中间数字的大小
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ],
        }
    ))
    fig.update_layout(
        height=125,  # 保持高度
        margin=dict(l=10, r=10, t=40, b=0),  # 增加顶部边距，减少底部边距
        font={'size': 12}
    )
    st.plotly_chart(fig, use_container_width=True)

def render_impact_analysis(data: Dict[str, Any]) -> None:
    """
    渲染影响分析部分
    
    Args:
        data: 新闻数据字典
    """
    # 创建三列布局
    col1, col2, col3 = st.columns(3)
    
    def format_value(value: float) -> str:
        """格式化数值，添加颜色"""
        color = '#FF6B6B' if value >= 0 else '#90EE90'  # 正值红色，负值绿色
        return f'<span style="color: {color}">{value}</span>'
    
    with col1:
        st.subheader("🏭 行业影响")
        for industry in data['related_industries']:
            st.markdown(
                f"**{industry['industry']}**  \n{format_value(float(industry['sentiment']))}",
                unsafe_allow_html=True
            )
    
    with col2:
        st.subheader("📊 指数影响")
        for index in data['related_indexes']:
            st.markdown(
                f"**{index['index']}**  \n{format_value(float(index['sentiment']))}",
                unsafe_allow_html=True
            )
    
    with col3:
        st.subheader("🏢 公司影响")
        for company in data['related_company']:
            st.markdown(
                f"**{company['company']}**  \n{format_value(float(company['sentiment']))}",
                unsafe_allow_html=True
            )

def render_html_content(html_content: str) -> None:
    """
    渲染包含图片的HTML内容，支持多图片显示
    
    Args:
        html_content: 包含HTML标签的文本内容
    """
    current_pos = 0
    while True:
        # 查找下一个图片标签
        img_start = html_content.find('<img', current_pos)
        if img_start == -1:
            # 没有更多图片，显示剩余文本
            remaining_text = html_content[current_pos:].replace('<br />', '\n')
            if remaining_text.strip():
                st.markdown(remaining_text)
            break
        
        # 显示图片前的文本
        text_before_img = html_content[current_pos:img_start].replace('<br />', '\n')
        if text_before_img.strip():
            st.markdown(text_before_img)
        
        # 提取图片URL
        src_start = html_content.find('src="', img_start) + 5
        src_end = html_content.find('"', src_start)
        img_url = html_content[src_start:src_end]
        
        # 显示图片
        st.image(img_url, use_container_width=True)
        
        # 更新位置到图片标签结束
        img_end = html_content.find('>', src_end) + 1
        current_pos = img_end

def render_news_details(data: Dict[str, Any]) -> None:
    """
    渲染新闻详情部分，包括标题、时间、基本信息和图片
    
    Args:
        data: 新闻数据字典，包含标题、时间、国家、市场、标签、描述等信息
    """
    st.caption(f"发布时间: {data['pub_time']}")
    
    # 基本信息
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**国家/地区:** {data['country']}")
        st.markdown(f"**相关市场:** {', '.join(data['markets'])}")
    with col2:
        st.markdown("**标签:**")
        render_tags(data['tags'])
    
    # 渲染整体情绪仪表盘
    st.markdown("### 📈 整体情绪分析")
    render_sentiment_gauge(data['sentiment'], "新闻整体情绪倾向")
    
    # 渲染影响分析
    st.markdown("### 🎯 影响分析")
    render_impact_analysis(data)
    
    # 新闻正文
    st.markdown("### 新闻内容")
    render_html_content(data['description'])

def get_sentiment_color(sentiment: int) -> str:
    """
    根据情绪值返回对应的颜色
    
    Args:
        sentiment: 情绪值 (0-100)
    
    Returns:
        str: 对应的颜色代码
    """
    if sentiment >= 70:
        return '#90EE90'  # 绿色
    elif sentiment >= 30:
        return '#FFD700'  # 黄色
    else:
        return '#FF6B6B'  # 红色

def render_news_list(news_list: list) -> int:
    """
    使用AgGrid渲染新闻列表，返回选中的新闻索引
    
    Args:
        news_list: 新闻列表
    
    Returns:
        int: 选中的新闻索引
    """
    st.header("📋 新闻列表")

    # 初始化 session state
    if 'selected_news_index' not in st.session_state:
        st.session_state.selected_news_index = 0

    # 转换数据为DataFrame格式
    df = pd.DataFrame([{
        '标题': news['title'],
        '时间': news['pub_time'],
        '情绪': news['sentiment'],
        '标签': ', '.join(news['tags'])[:50] + '...' if len(news['tags']) > 50 else ', '.join(news['tags']),
        'index': i  # 添加索引列用于追踪选择
    } for i, news in enumerate(news_list)])

    # 配置情绪列的样式 - 使用中心对齐的水平进度条
    cellrenderer_jscode = JsCode("""
    class SentimentBarRenderer {
        init(params) {
            this.eGui = document.createElement('div');
            this.eGui.style.width = '100%';
            this.eGui.style.height = '20px';
            this.eGui.style.display = 'flex';
            this.eGui.style.alignItems = 'center';
            
            const barContainer = document.createElement('div');
            barContainer.style.width = '80%';
            barContainer.style.height = '12px';
            barContainer.style.backgroundColor = '#f0f0f0';
            barContainer.style.borderRadius = '6px';
            barContainer.style.overflow = 'hidden';
            barContainer.style.position = 'relative';
            
            // 添加中心线
            const centerLine = document.createElement('div');
            centerLine.style.position = 'absolute';
            centerLine.style.left = '50%';
            centerLine.style.width = '1px';
            centerLine.style.height = '100%';
            centerLine.style.backgroundColor = '#999';
            barContainer.appendChild(centerLine);
            
            const bar = document.createElement('div');
            const value = params.value || 0;  // 值范围为-100到100
            
            // 设置bar的位置和宽度
            if (value >= 0) {
                bar.style.left = '50%';
                bar.style.width = (value/2) + '%';  // 除以2是因为50%是总宽度的一半
                bar.style.backgroundColor = '#FF6B6B';  // 正值用红色
            } else {
                bar.style.right = '50%';
                bar.style.width = (Math.abs(value)/2) + '%';  // 除以2是因为50%是总宽度的一半
                bar.style.backgroundColor = '#90EE90';  // 负值用绿色
            }
            
            bar.style.height = '100%';
            bar.style.position = 'absolute';
            bar.style.transition = 'all 0.3s';
            
            const text = document.createElement('span');
            text.style.marginLeft = '5px';
            text.style.fontSize = '12px';
            text.innerText = value;
            
            barContainer.appendChild(bar);
            this.eGui.appendChild(barContainer);
            this.eGui.appendChild(text);
        }
        
        getGui() {
            return this.eGui;
        }
        
        refresh(params) {
            return false;
        }
    }
    """)

    # 配置AgGrid选项
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode='single', use_checkbox=False)
    gb.configure_column('标题', minWidth=200)
    gb.configure_column('时间', minWidth=100)
    
    # 配置情绪列
    gb.configure_column('情绪', 
                       minWidth=120,
                       cellRenderer=cellrenderer_jscode)
    
    gb.configure_column('标签', minWidth=150)
    gb.configure_column('index', hide=True)

    # 添加分页设置
    gb.configure_pagination(enabled=True, 
                          paginationAutoPageSize=False, 
                          paginationPageSize=50)

    grid_options = gb.build()

    df = df.sort_values(by='时间', ascending=False)

    # 显示AgGrid表格
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=1000,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        allow_unsafe_jscode=True
    )

    # 处理选择
    selected = grid_response['selected_rows']
    if selected is not None and len(selected) > 0:
        st.session_state.selected_news_index = selected.iloc[0]['index']
    
    return st.session_state.selected_news_index

def run():
    """
    主函数，渲染整个新闻分析页面
    """
    st.title("📊 新闻监控分析")
    
    # 示例数据 - 多条新闻
    sample_news_list = get_news_list(limit_cnt=1000)
    
    # 创建左右两栏布局
    left_col, right_col = st.columns([1, 1])
    
    # 左侧新闻列表
    with left_col:
        selected_index = render_news_list(sample_news_list)
    
    # 右侧新闻详情和分析
    with right_col:
        if selected_index is not None and selected_index < len(sample_news_list):
            selected_news = sample_news_list[selected_index]
            
            # 渲染新闻详情
            render_news_details(selected_news)
