# encoding: utf-8
from loguru import logger
from peewee import *
from datetime import datetime
import random
import time
from tgtrader.streamlit_pages.dao.common import BaseModel, db
from tgtrader.streamlit_pages.utils.common import hash, verify
from cryptography.fernet import Fernet

class User(BaseModel):
    id = AutoField()
    username = CharField(unique=True)
    password = CharField()
    key = CharField()
    # User role field, defaults to 'normal'. Can be 'normal' or 'admin'
    role = CharField(default='normal')
    create_time = BigIntegerField(default=lambda: int(datetime.now().timestamp()))
    update_time = BigIntegerField(default=lambda: int(datetime.now().timestamp()))

    class Meta:
        table_name = 't_user'

    def save(self, *args, **kwargs):
        self.update_time = int(datetime.now().timestamp())
        return super(User, self).save(*args, **kwargs)

    @staticmethod
    def hash_password(password: str) -> str:
        return hash(password)

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        try:
            return verify(password, self.password)
        except Exception as e:
            logger.error(f"verify password error: {str(e)}")
            return False

    @classmethod
    def init_table(cls):
        with db:
            if User.table_exists():
                User.delete().execute()  # Delete all records if table exists
            else:
                db.create_tables([User])  # Create table if it doesn't exist

    @classmethod
    def get_user_by_username(cls, username: str):
        with db:
            user = cls.get_or_none(cls.username == username)
            return user

    @classmethod
    def create_user(cls, username: str, password: str, role: str = 'normal'):
        """Create a new user"""
        with db:
            # Check if user already exists
            if cls.get_user_by_username(username):
                raise Exception(f"user {username} already exists")
            
            # Hash the password
            hashed_password = cls.hash_password(password)
            
            # 生成符合 Fernet 要求的密钥
            # 使用 Fernet.generate_key() 生成一个有效的密钥
            key = Fernet.generate_key().decode()

            ts = int(time.time() * 1000)
            
            return cls.create(
                username=username,
                password=hashed_password,
                key=key,
                role=role,
                create_time=ts,
                update_time=ts
            )