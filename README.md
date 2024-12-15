# tgtrader天工量化投研分析客户端

- 提供开箱即用的分析工具
- 对于小白，可以直接使用可视化分析工具，零代码开启量化分析
- 对于有一定经验的开发者，结合使用sdk开发，更加灵活

## 安装

```bash
pip install tgtrader

如果网络不通，可以使用国内镜像源
pip install tgtrader -i https://mirrors.aliyun.com/pypi/simple/
```

## 更新日志

v0.1.0
- 支持获取国内ETF数据、股票数据（使用AKShare获取数据）

## 客户端使用说明

## SDK使用说明

### 获取数据

```python
from tgtrader.data import DataGetter
from tgtrader.common import PriceAdjust, Period, SecurityType

symbols = [
    '511260',  # 十年国债ETF
    '159915',  # 创业板ETF
    '510500',  # 500ETF
    '159919',  # 沪深300ETF
    '510880',  # 红利ETF
    '518880',  # 黄金ETF
    '513100',  # 纳指ETF
]


data_getter = DataGetter()
df = data_getter.get_data(symbols, 
                            "2010-01-01", 
                            "2024-11-30", 
                            period=Period.Day, 
                            fields=["open","close","high","low","volume"], 
                            security_type=SecurityType.ETF,
                            adjust=PriceAdjust.HFQ)
df
``` 

| 参数 | 类型 | 说明 | 示例值 |
|------|------|------|---------|
| symbols | List[str] | 证券代码列表 | ['511260', '159915'] |
| start_date | str | 开始日期，格式为YYYY-MM-DD | '2010-01-01' |
| end_date | str | 结束日期，格式为YYYY-MM-DD | '2024-11-30' |
| period | Period | 数据周期，可选值：Day(日线)、Week(周线)、Month(月线) | Period.Day |
| fields | List[str] | 需要获取的字段，可选值：open、close、high、low、volume | ['open', 'close'] |
| security_type | SecurityType | 证券类型，可选值：ETF、Stock | SecurityType.ETF |
| adjust | PriceAdjust | 价格复权方式，可选值：None(不复权)、QFQ(前复权)、HFQ(后复权) | PriceAdjust.HFQ |


![get_data](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/get_data.png)

## 微信公众号： 天工量化
**关注即可获取**：
1. tgtrader的最佳实践：如何用好tgtrader以提高投研效率
2. 研报复现：各大券商研报复现，源码公开
3. 策略分享：基于tg量化工具集，实现各类策略
4. 实盘跟踪：已上线的实盘策略持续跟进
