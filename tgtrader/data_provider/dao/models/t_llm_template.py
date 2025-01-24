from datetime import datetime
import os
import time
from typing import List
from loguru import logger
from peewee import *
from tgtrader.utils.db_path_utils import get_common_data_database


main_db = get_common_data_database()

class TLLMTemplate(Model):
    name = TextField(verbose_name='模版名称', primary_key=True)
    content = TextField(verbose_name='模板内容')
    create_time = BigIntegerField(verbose_name='创建时间', default=int(time.time() * 1000))
    update_time = BigIntegerField(verbose_name='更新时间', default=int(time.time() * 1000))

    class Meta:
        table_name = 't_llm_template' 
        database = main_db

    @classmethod
    def init_table(cls):
        # 初始化表
        cls.create_table(fail_silently=True)
        cls.init_data()
    
    @classmethod
    def init_data(cls):
        data = [
            {
                'name': '财经新闻结构化分析',
                'content': """请根据以下财经新闻内容进行结构化分析：
标题：财联社1月24日电，离岸人民币兑美元日内涨超400个基点，一度涨破7.24，最高触及7.2396，现报7.2430。
发布时间：2025-01-23 12:25:05
内容：财联社1月24日电，离岸人民币兑美元日内涨超400个基点，一度涨破7.24，最高触及7.2396，现报7.2430。

请按JSON格式返回：
{{
  "country": "中国", 
  "markets": "市场类型",
  "tags": ["标签1", "标签2"],
  "sentiment": 数值(-1~1),
  "related_industries": [
    {
      "industry": "申万一级行业1",
      "sentiment": 数值(-1~1)
    },
    {
      "industry": "申万一级行业2",
      "sentiment": 数值(-1~1)
    }
  ],
  "related_indexes": [
    {
      "index": "指数1",
      "sentiment": 数值(-1~1)
    },
    {
      "index": "指数2",
      "sentiment": 数值(-1~1)
    }
  ]
}}

1. 处理规则：
- 国家识别规则：
- 优先采用政策主体国
- 次选事件发生地
- 最后考虑相关公司总部所在地
2. 市场类型选择：
- 必须从以下具体市场中选择：
- 股票市场：[A股、港股、美股、纳斯达克、纽交所、伦敦证交所、东京证交所等]
- 债券市场：[中国银行间债市、美国国债市场、欧洲债券市场等]
- 外汇市场：[人民币外汇市场、美元外汇市场等]
- 商品期货：[上海期货交易所、芝加哥商品交易所等]
- 金融衍生品：[中国金融期货交易所、芝加哥期权交易所等]
- 多选时按影响程度排序
- 需明确标注具体市场名称（如"A股"而非"股票市场"）
3. 标签生成规则：
- 每个标签必须有≥2个独立内容片段支撑
- 标签应体现核心事件要素（如"政策调控"、"技术创新"）
- 优先使用名词性短语，保持客观中性
4. 行业处理规范：
- 必须严格使用申万一级行业标准名称（如"电力设备"而非"新能源"）
- 行业情绪值必须与文中具体事件直接相关
- 相关行业需按影响程度排序
5. 情感评分标准：
- 整体情绪(overall)反映市场综合预期(-1=极度悲观，1=极度乐观)
- 行业情绪值需体现事件对特定行业的非对称影响
- 评分需考虑文中量化指标（如政策力度、财务数据）
6. 相关指数规则：
- 必须明确标注具体指数名称（如"上证指数"、"纳斯达克指数"）
- 优先选择与事件直接相关的市场指数
- 指数数量限制：1-3个核心相关指数
7. 输出控制：
- 必须严格返回标准JSON格式
- 禁用注释/附加说明
- 行业数量限制：2-3个核心相关行业
- 指数数量限制：1-3个核心相关指数
    """
            },
            {
                "name": "test",
                "content": "test"
            }
        ]
        for item in data:
            # 检查记录是否已存在，避免重复插入
            existing = cls.select().where(
                cls.name == item.get('name')
            ).first()
            
            if not existing:
                cls.create(**item)

    @classmethod
    def get_all_templates(cls) -> List['TLLMTemplate']:
        return cls.select()

TLLMTemplate.init_table()
