from datetime import datetime
import os
import time
from typing import List
from loguru import logger
from peewee import *
from tgtrader.dao.common import BaseModel, db


class TLLMTemplate(BaseModel):
    id = AutoField()
    username = TextField(verbose_name='用户名')
    name = TextField(verbose_name='模版名称')
    content = TextField(verbose_name='模板内容')
    create_time = BigIntegerField(verbose_name='创建时间', default=int(time.time() * 1000))
    update_time = BigIntegerField(verbose_name='更新时间', default=int(time.time() * 1000))

    class Meta:
        table_name = 't_llm_template' 
        indexes = (
            (('username', 'name'), True),
        )

    @classmethod
    def init_table(cls):
        # 初始化表
        cls.create_table(fail_silently=True)

    @classmethod
    def save_template(cls, username: str, name: str, content: str, is_check_exist: bool = True):
        template = cls.get_or_none(username=username, name=name)
        if not template:
            TLLMTemplate.create(username=username, name=name, content=content)
        else:
            if is_check_exist:
                raise Exception(f"模板已存在，请修改模板名称或内容")
            else:
                template.content = content
                template.update_time = int(time.time() * 1000)
                template.save()

    @classmethod
    def get_all_template(cls):
        news_parser = """请根据以下财经新闻内容进行结构化分析：
标题：{{title}}
发布时间：{{pub_time}}
内容：{{description}}


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
  ],
  "related_company": [
    {
      "company": "公司1",
      "sentiment": 数值(-1~1)
    },
    {
      "company": "公司2",
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
7. 相关公司规则：
- 从新闻内容中提取公司名称或股票代码，作为个股的标识
- 如果新闻涉及某个上市公司并提供了具体的财务数据、股价波动等信息，应根据这些细节生成对应的分析。
- 如果新闻中未提及关联具体公司，related_company返回空列表
8. 输出控制：
- 必须严格返回标准JSON格式
- 禁用注释/附加说明
- 行业数量限制：2-3个核心相关行业
- 指数数量限制：1-3个核心相关指数
    """
        
        return {
            "新闻解析": news_parser,
        }

    @classmethod
    def get_user_templates(cls, username: str) -> List['TLLMTemplate']:
        return cls.select().where(cls.username == username)

TLLMTemplate.init_table()
