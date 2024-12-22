import streamlit as st
import pandas as pd
import altair as alt  # Streamlit recommends Altair for interactive charts
from typing import Dict, Any, Optional

from tgtrader.strategy import PerformanceStats, StrategyDef

def plot_returns_chart(prices: pd.DataFrame, backtest_end_date: Optional[str] = None):
    """绘制策略收益率曲线，若提供backtest_end_date，则分割回测与非回测部分并加粗非回测部分的线条"""
    
    print(prices.iloc[0])
    print(prices.iloc[-1])
    print(backtest_end_date)

    # 确保日期列为datetime类型
    plot_df = prices.reset_index()
    plot_df.columns = ['date', 'returns']
    plot_df['date'] = pd.to_datetime(plot_df['date'])
    
    if backtest_end_date:
        backtest_end = pd.to_datetime(backtest_end_date)
        # 分割数据为回测和非回测部分
        backtest_df = plot_df[plot_df['date'] <= backtest_end]
        non_backtest_df = plot_df[plot_df['date'] > backtest_end]
        
        # 最小和最大收益率，用于y轴范围
        min_return = plot_df['returns'].min()
        max_return = plot_df['returns'].max()
        y_padding = (max_return - min_return) * 0.05
        
        # 创建回测部分的线
        backtest_line = alt.Chart(backtest_df).mark_line(color='blue').encode(
            x=alt.X('date:T', title='日期'),
            y=alt.Y('returns:Q', 
                    title='累计收益率',
                    scale=alt.Scale(
                        domain=[min_return - y_padding, max_return + y_padding]
                    ))
        )
        
        # 创建非回测部分的线，线条更粗
        non_backtest_line = alt.Chart(non_backtest_df).mark_line(color='red', strokeWidth=3).encode(
            x='date:T',
            y='returns:Q'
        )
        
        # 创建分割竖线
        rule = alt.Chart(pd.DataFrame({'date': [backtest_end]})).mark_rule(color='green').encode(
            x='date:T'
        )
        
        # 合并所有图层
        chart = (backtest_line + non_backtest_line + rule).properties(
            height=500
        )
    else:
        # 如果没有提供backtest_end_date，则绘制普通的线图
        min_return = plot_df['returns'].min()
        max_return = plot_df['returns'].max()
        y_padding = (max_return - min_return) * 0.05
        
        chart = alt.Chart(plot_df).mark_line().encode(
            x=alt.X('date:T', title='日期'),
            y=alt.Y('returns:Q', 
                    title='累计收益率',
                    scale=alt.Scale(
                        domain=[min_return - y_padding, max_return + y_padding]
                    )),
            tooltip=['date:T', 'returns:Q']
        ).properties(
            height=500
        )
    
    return chart

def format_percentage(value: float) -> str:
    """将小数转换为百分比格式"""
    return f"{value * 100:.2f}%"

def format_ratio(value: float) -> str:
    """格式化比率数值"""
    return f"{value:.2f}"

def display_statistics(stats: PerformanceStats):
    """显示回测统计信息"""
    
    # 收益指标
    returns_metrics = {
        "总收益率": format_percentage(stats.total_return),
        "年化收益率": format_percentage(stats.cagr), 
        "最大回撤": format_percentage(stats.max_drawdown),
        "平均回撤": format_percentage(stats.avg_drawdown),
        "平均回撤天数": str(stats.avg_drawdown_days),
        "Calmar比率": format_ratio(stats.calmar)
    }
    
    # 风险指标
    risk_metrics = {
        "日度夏普比率": format_ratio(stats.daily_sharpe),
        "日度索提诺比率": format_ratio(stats.daily_sortino),
        "日度波动率": format_percentage(stats.daily_vol),
        "月度夏普比率": format_ratio(stats.monthly_sharpe),
        "月度索提诺比率": format_ratio(stats.monthly_sortino),
        "月度波动率": format_percentage(stats.monthly_vol)
    }
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 显示收益指标
    with col1:
        st.subheader("收益指标")
        returns_df = pd.DataFrame.from_dict(returns_metrics, orient='index', columns=['值'])
        st.dataframe(returns_df, use_container_width=True)
    
    # 显示风险指标
    with col2:
        st.subheader("风险指标")
        risk_df = pd.DataFrame.from_dict(risk_metrics, orient='index', columns=['值'])
        st.dataframe(risk_df, use_container_width=True)

def display_backtest_results(strategy: StrategyDef, backtest_end_date: Optional[str] = None):
    """显示回测结果的主函数"""
    st.header("回测结果")
    
    # 绘制收益率曲线
    chart = plot_returns_chart(strategy.get_prices(), backtest_end_date)
    st.altair_chart(chart, use_container_width=True)
    
    display_statistics(strategy.performance_stats())
