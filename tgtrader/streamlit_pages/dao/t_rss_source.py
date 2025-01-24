# encoding: utf-8
import time
from datetime import datetime
from tgtrader.streamlit_pages.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey
from typing import List
from peewee import *
import re
from urllib.parse import urlparse
import requests
from loguru import logger


class TRssSource(BaseModel):
    # 主键自增id
    id = AutoField()
    # 用户名
    username = TextField()
    # rss源名称
    rss_name = TextField()
    # rss源url
    rss_url = TextField()
    # rss类型
    rss_type = TextField()
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(time.time() * 1000))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(time.time() * 1000))

    MAX_NAME_LENGTH = 50
    MIN_NAME_LENGTH = 2

    class Meta:
        table_name = 't_rss_source'
        indexes = (
            (('username', 'rss_name'), True),
            (('username', 'rss_url'), True),
        )

    @classmethod
    def validate_rss_name(cls, rss_name: str) -> None:
        """验证RSS源名称"""
        if not rss_name:
            raise ValueError("RSS源名称不能为空")
        if len(rss_name) < cls.MIN_NAME_LENGTH:
            raise ValueError(f"RSS源名称长度不能小于{cls.MIN_NAME_LENGTH}个字符")
        if len(rss_name) > cls.MAX_NAME_LENGTH:
            raise ValueError(f"RSS源名称长度不能超过{cls.MAX_NAME_LENGTH}个字符")
        # 检查是否包含特殊字符
        if re.search(r'[<>"\']', rss_name):
            raise ValueError("RSS源名称不能包含特殊字符 < > ' \"")

    @classmethod
    def validate_rss_url(cls, rss_url: str) -> None:
        """验证RSS URL"""
        if not rss_url:
            raise ValueError("RSS URL不能为空")
        
        # 验证URL格式
        try:
            result = urlparse(rss_url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("无效的URL格式")
            if result.scheme not in ['http', 'https']:
                raise ValueError("URL必须以http或https开头")
        except Exception as e:
            raise ValueError(f"无效的URL格式: {str(e)}")

    @classmethod
    def validate_rss_type(cls, rss_type: str) -> None:
        """验证RSS类型"""
        if not rss_type:
            raise ValueError("RSS类型不能为空")

    @classmethod
    def validate_all(cls, rss_name: str, rss_url: str, rss_type: str) -> None:
        """验证所有字段"""
        cls.validate_rss_name(rss_name)
        cls.validate_rss_url(rss_url)
        cls.validate_rss_type(rss_type)

    @classmethod
    def init_table(cls):
        with db:
            if not TRssSource.table_exists():
                db.create_tables([TRssSource])

    @classmethod
    def get_rss_sources(cls, username: str) -> List['TRssSource']:
        with db:
            return list(cls.select().where(cls.username == username))

    @classmethod
    def save_rss_source(cls, username: str, rss_name: str, rss_url: str, rss_type: str):
        try:
            # 验证所有字段
            cls.validate_all(rss_name, rss_url, rss_type)
            
            with db:
                cls.create(
                    username=username,
                    rss_name=rss_name,
                    rss_url=rss_url,
                    rss_type=rss_type
                )
        except ValueError as e:
            raise Exception(str(e))
        except IntegrityError:
            raise Exception(f"RSS源已存在，请修改RSS源名称或URL")
        except Exception as e:
            raise Exception(f"保存RSS源失败: {str(e)}")
    
    @classmethod
    def delete_rss_source(cls, _id: int):
        with db:
            cls.delete().where(cls.id == _id).execute()

    @classmethod
    def update_rss_source(cls, _id: int, rss_name: str, rss_url: str, rss_type: str):
        try:
            # 验证所有字段
            cls.validate_all(rss_name, rss_url, rss_type)
            
            with db:
                cls.update(
                    rss_name=rss_name,
                    rss_url=rss_url,
                    rss_type=rss_type,
                    update_time=int(time.time() * 1000)
                ).where(cls.id == _id).execute()
        except ValueError as e:
            raise Exception(str(e))
        except IntegrityError:
            raise Exception(f"RSS源已存在，请修改RSS源名称或URL")
        except Exception as e:
            raise Exception(f"更新RSS源失败: {str(e)}")

TRssSource.init_table()
