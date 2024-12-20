# 欢迎页面

import streamlit as st

def run():
    st.markdown("""
# tgtrader天工量化投研分析客户端

- 提供开箱即用的分析工具
- 对于小白，可以直接使用可视化分析工具，零代码开启量化分析
- 对于有一定经验的开发者，结合使用sdk开发，更加灵活
                
# 源码地址
- github: https://github.com/smartian1/tgtrader
- gitee: https://gitee.com/smartian123/tgtrader                

## 更新日志

v0.1.0
- 支持获取国内ETF数据、股票数据（使用AKShare获取数据）

## 客户端使用说明

## 微信公众号： 天工量化
**关注即可获取**：
1. tgtrader的最佳实践：如何用好tgtrader以提高投研效率
2. 研报复现：各大券商研报复现，源码公开
3. 策略分享：基于tg量化工具集，实现各类策略
4. 实盘跟踪：已上线的实盘策略持续跟进

    """)