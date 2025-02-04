# 欢迎页面

import streamlit as st

def run():
    st.markdown("""
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

github: https://github.com/smartian1/tgtrader

gitee: https://gitee.com/smartian123/tgtrader   

## 安装

```sh
pip install tgtrader

如果网络不通，可以使用国内镜像源
pip install tgtrader -i https://mirrors.aliyun.com/pypi/simple/
```



## 更新日志

**v1.2.0**

- 数据流支持使用AI大模型解读财经新闻
- 支持任务调度，定时执行数据加工流，用于实时解析财经新闻



**v1.1.0**

- 支持画布拖拽构建数据加工流程，无需写代码



**v1.0.1**

- 增加数据初始化、数据查询页面

- 增加知识库页面，显示jupyter notebook


**v1.0.0**

可视化策略回测

- 支持在**本地运行可视化页面**, 仅需两行代码

- 已支持的**内置策略**: 目标权重策略, 风险平价策略 (策略不断扩充中)

- **我的策略**: 将回测策略及参数保存到个人空间

- **策略详情**: 查看策略详情, 并支持查看策略回测和模拟阶段绩效


## 客户端使用说明

```sh
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

4. 定时任务启动(刷新财经新闻)
  python -m tgtrader.tasks.task_scheduler
```

#### 


    """)