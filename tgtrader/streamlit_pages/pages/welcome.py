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
v0.2.0
- 支持在**本地运行可视化页面**, 仅需两行代码
- 已支持的**内置策略**: 目标权重策略, 风险平价策略 (策略不断扩充中)
- **我的策略**: 将回测策略及参数保存到个人空间
- **策略详情**: 查看策略详情, 并支持查看策略回测和模拟阶段绩效

v0.1.0
- 支持获取国内ETF数据、股票数据（使用AKShare获取数据）

## 客户端使用说明
### 已支持的内置策略
| 策略名称 | 策略说明 | 适用场景 |
|---------|---------|----------|
| 目标权重策略 | 根据预设的目标权重定期调仓，是最基础的资产配置策略 | 适用于有明确资产配置目标的场景，如60/40策略、风险等级配置等 |
| 风险平价策略 | 通过计算资产的风险贡献，使各资产的风险贡献相等，实现风险的平衡配置 | 适用于追求风险平衡、稳健收益的场景，特别是在市场波动较大时期 |

#### 目标权重策略
![目标权重策略](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/target_weight_strategy.png)
![目标权重策略](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/target_weight_strategy_result.png)

#### 我的策略
策略回测完成之后，可以保存到“我的策略”
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/save_strategy.png)

进入“我的策略”，可以查看保存的策略列表
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/my_strategies.png)

选中某个策略，并点击“查看”，可以查看策略的收益绩效。蓝色部分是回测收益曲线，红色部分是回测之后时间段的收益曲线。通过观察红线，可以了解策略仍然有效
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/my_strategies_backtest.png)
                

## 微信公众号： 天工量化
**关注即可获取**：
1. tgtrader的最佳实践：如何用好tgtrader以提高投研效率
2. 研报复现：各大券商研报复现，源码公开
3. 策略分享：基于tg量化工具集，实现各类策略
4. 实盘跟踪：已上线的实盘策略持续跟进

    """)