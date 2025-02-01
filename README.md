# tgtrader天工量化投研分析客户端

- 提供开箱即用的分析工具
- 对于小白，可以直接使用可视化分析工具，零代码开启量化分析
- 对于有一定经验的开发者，结合使用sdk开发，更加灵活

## 微信公众号： 天工量化
**关注即可获取**：
1. tgtrader的最佳实践：如何用好tgtrader以提高投研效率
2. 研报复现：各大券商研报复现，源码公开
3. 策略分享：基于tg量化工具集，实现各类策略
4. 实盘跟踪：已上线的实盘策略持续跟进


## 源码地址
>github: https://github.com/smartian1/tgtrader
gitee: https://gitee.com/smartian123/tgtrader   


## 安装

```bash
pip install tgtrader

如果网络不通，可以使用国内镜像源
pip install tgtrader -i https://mirrors.aliyun.com/pypi/simple/
```

![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/preview.png)



## 更新日志
**v1.2.0**
- 数据流支持使用AI大模型解析财经新闻
- 支持任务调度，定时执行数据加工流
  
**v1.1.0**
- 支持画布拖拽构建数据加工流程

**v1.0.1**
- 增加数据初始化、数据查询页面
- 增加知识库页面，显示jupyter notebook
  
**v1.0.0**

可视化策略回测
- 支持在**本地运行可视化页面**, 仅需两行代码
- 已支持的**内置策略**: 目标权重策略, 风险平价策略 (策略不断扩充中)
- **我的策略**: 将回测策略及参数保存到个人空间
- **策略详情**: 查看策略详情, 并支持查看策略回测和模拟阶段绩效

SDK功能
- 支持获取国内ETF数据、股票数据（使用AKShare获取数据）
- 支持自定义策略类

## 客户端使用说明
```bash
创建虚拟环境(建议)
python -m venv venv_tgtrader

激活虚拟环境
1. windows
.\venv_tgtrader\Scripts\activate
2. mac/linux
source venv_tgtrader/bin/activate

安装tgtrader
pip install tgtrader

初始化数据
python -m tgtrader.streamlit_pages.init_data

启动客户端
1. 创建一个python文件(要与初始化数据时目录保持一致)，例如：tgtrader_cli.py
2. 在文件中添加以下代码：

from tgtrader.streamlit_pages.main import run
run()

3. 运行
   streamlit run tgtrader_cli.py
```

### 一、数据模块
#### 1.1 数据下载
点击“数据初始化”，进入下载页面。选择需要更新的数据以及时间段，进行更新。

**数据下载了有什么用**：
1. 可在数据查询页面用sql进行查询，进行探索性分析
2. 后续因子计算，直接用本地数据进行计算，提升效率
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/data_init.png)

#### 1.2 数据查询
tgtrader底层使用duckdb存储数据，使用duckdb sql即可进行查询

**为什么用duckdb**：
1. duckdb sql**与标准sql基本一致**，使用sql进行数据分析效率更高，更加灵活
2. duckdb**性能非常高**，同样的功能，duckdb比pandas性能要高数倍
3. 可以**与pandas完美结合**，可以用sql对dataframe进行查询，效率翻倍提升
4. 在量化交易中，需要频繁的对行情数据做**时间序列和截面的计算**，duckdb对此有比较好的支持。使用窗口函数，可以非常方便的进行各种时间和截面的计算
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/data_query.png)

#### 1.3 数据加工
可以在画布上拖拽来构建可视化的数据加工流程：
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/flow_intro_13.png)

### 二、策略模块
#### 2.1 已支持的内置策略
| 策略名称 | 策略说明 | 适用场景 |
|---------|---------|----------|
| 目标权重策略 | 根据预设的目标权重定期调仓，是最基础的资产配置策略 | 适用于有明确资产配置目标的场景，如60/40策略、风险等级配置等 |
| 风险平价策略 | 通过计算资产的风险贡献，使各资产的风险贡献相等，实现风险的平衡配置 | 适用于追求风险平衡、稳健收益的场景，特别是在市场波动较大时期 |

##### 2.1.1 目标权重策略
![目标权重策略](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/target_weight_strategy.png)
![目标权重策略](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/target_weight_strategy_result.png)

##### 2.1.2 风险平价策略
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/risk_parity_strategy.png)

#### 2.2 我的策略
策略回测完成之后，可以保存到“我的策略”
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/save_strategy.png)

进入“我的策略”，可以查看保存的策略列表
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/my_strategies.png)

选中某个策略，并点击“查看”，可以查看策略的收益绩效。蓝色部分是回测收益曲线，红色部分是回测之后时间段的收益曲线。通过观察红线，可以了解策略仍然有效
![alt text](https://raw.githubusercontent.com/smartian1/tgtrader/main/tgtrader/images/my_strategies_backtest.png)

## SDK使用说明

### 一、数据模块

#### 1.1 获取外部数据

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
df = data_getter.get_price(symbols, 
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


#### 1.2 查询本地数据库

```python
from tgtrader.utils.duckdb_query import DuckDBQuery
from tgtrader.common import DataSource

# 设置读取数据库文件的db_query
data_source = DataSource.Akshare
db_query = DuckDBQuery(data_source)

# fetch_df：输入sql，输出dataframe
df = db_query.fetch_df("select * from t_kdata limit 10")

# fetch_all: 输入sql，输出list[dict]
data = db_query.fetch_all("select * from t_kdata limit 10")

```

#### 1.3 使用sql，对dataframe进行分析

```python
from tgtrader.utils.duckdb_query_df import DuckDBQueryDF

# 将dataframe传入到DuckDBQueryDF实例，构建一个查询器
duckdb_df_query = DuckDBQueryDF(df)

# 可用sql对df进行分析了，例如计算20日SMA
sql = """
  SELECT
    code,
    date,
    open,
    low,
    high,
    close,
    volume,
    -- 计算 20 日 SMA
    AVG(close) OVER (PARTITION BY code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20
  FROM df
"""

df_duck = duckdb_df_query.query(sql)

```