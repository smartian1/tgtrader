# encoding: utf-8
from peewee import *
from datetime import datetime
import bcrypt
from .common import BaseModel

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
