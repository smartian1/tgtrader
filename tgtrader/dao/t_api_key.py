# encoding: utf-8
from datetime import datetime
from tgtrader.dao.common import BaseModel, db
from peewee import AutoField, IntegerField, BigIntegerField, TextField, CompositeKey
from typing import List
import time
from tgtrader.dao.t_user import User
from tgtrader.streamlit_pages.utils.common import encrypt, decrypt
from peewee import *
from loguru import logger


class TApiKey(BaseModel):
    # 主键自增id
    id = AutoField()
    # api key名称
    api_key_name = TextField()
    # 用户名
    username = TextField()
    # 模型名称
    model_name = TextField()
    # api key
    api_key = TextField()
    # 创建时间
    create_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))
    # 更新时间
    update_time = BigIntegerField(
        default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_api_key'
        indexes = (
            (('username', 'model_name', 'api_key'), True),
            (('username', 'api_key_name'), True),
        )

    @classmethod
    def init_table(cls):
        with db:
            if not TApiKey.table_exists():
                db.create_tables([TApiKey])

    @classmethod
    def get_api_keys(cls, username: str, hide_middle: bool = True) -> List['TApiKey']:
        with db:
            # 获取用户的API Keys并解密
            api_keys = list(cls.select().where(cls.username == username).order_by(cls.create_time.desc()))
            for api_key in api_keys:
                # 解密API Key
                try:
                    decrypted_key = cls.decrypt(username, api_key.api_key)
                except Exception as e:
                    decrypted_key = '解析失败，请删除后重新增加'
                    logger.exception(e)

                # 如果需要隐藏中间部分，只显示前后4个字符
                if hide_middle:
                    if len(decrypted_key) > 8:
                        api_key.api_key = f"{decrypted_key[:4]}{'*' * (len(decrypted_key) - 8)}{decrypted_key[-4:]}"
                    else:
                        api_key.api_key = decrypted_key[0] + '*' * (len(decrypted_key) - 1)
                else:
                    api_key.api_key = decrypted_key
            
            return api_keys

    @classmethod
    def save_api_key(cls, username: str, model_name: str, api_key: str, api_key_name: str):
        try:
            api_key = cls.encrypt(username, api_key)
            ts = int(time.time() * 1000)
            with db:
                cls.create(username=username, model_name=model_name, api_key=api_key, api_key_name=api_key_name,
                        create_time=ts, update_time=ts)
        except IntegrityError:
            raise Exception(f"API Key已存在")

    @classmethod
    def delete_api_key(cls, _id: int):
        with db:
            cls.delete().where(cls.id == _id).execute()

    @classmethod
    def encrypt(cls, username: str, api_key: str) -> str:
        user = User.get_user_by_username(username)
        if not user:
            raise Exception(f"user {username} not found")
        return encrypt(api_key, user.key)

    @classmethod
    def decrypt(cls, username: str, encrypted_key: str) -> str:
        user = User.get_user_by_username(username)
        if not user:
            raise Exception(f"user {username} not found")
        return decrypt(encrypted_key, user.key)

    @classmethod
    def get_model_config(cls, model_id: int) -> 'TApiKey':
        with db:
            model_config = cls.select().where(cls.id == model_id).first()
            if model_config:
                username = model_config.username
                model_config.api_key = cls.decrypt(username, model_config.api_key)
            return model_config

TApiKey.init_table()
