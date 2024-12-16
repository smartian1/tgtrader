# encoding: utf-8
from peewee import *
from datetime import datetime
import bcrypt
from .common import BaseModel, db

class User(BaseModel):
    id = AutoField()
    username = CharField(unique=True)
    password = CharField()
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
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        return bcrypt.checkpw(password.encode(), self.password.encode())

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
            print(f"当前数据库路径: {db.database}")
            print(f"查询表名: {cls._meta.table_name}")
            try:
                user = cls.get_or_none(cls.username == username)
                print(f"查询结果: username=={username}, user={user}")
                return user
            except Exception as e:
                print(f"查询出错: {str(e)}")
                raise

    @classmethod
    def create_user(cls, username: str, password: str, role: str = 'normal'):
        """Create a new user"""
        with db:
            # Check if user already exists
            if cls.get_user_by_username(username):
                raise Exception(f"用户 {username} 已存在")
            
            # Hash the password and create user
            hashed_password = cls.hash_password(password)
            return cls.create(
                username=username,
                password=hashed_password,
                role=role
            )