# encoding: utf-8
from loguru import logger
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
            user = cls.get_or_none(cls.username == username)
            return user

    @classmethod
    def create_user(cls, username: str, password: str, role: str = 'normal'):
        """Create a new user"""
        with db:
            # Check if user already exists
            if cls.get_user_by_username(username):
                raise Exception(f"user {username} already exists")
            
            # Hash the password and create user
            hashed_password = cls.hash_password(password)
            return cls.create(
                username=username,
                password=hashed_password,
                role=role
            )