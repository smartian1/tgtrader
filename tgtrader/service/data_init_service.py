# encoding: utf-8

from pathlib import Path
from datetime import datetime
from ..dao.common import db
from ..dao.t_user import User

def init_user_data():
    """Initialize the t_user table with default admin user"""
    # Create tables if not exists
    with db:
        db.create_tables([User])
        
        # Default admin user data
        admin_user = {
            'username': 'admin',
            'password': User.hash_password('admin123'),
            'role': 'admin'
        }
        
        # Insert or update admin user
        User.insert(**admin_user).on_conflict(
            conflict_target=[User.username],
            update={
                User.password: User.password,
                User.role: User.role,
                User.update_time: int(datetime.now().timestamp())
            }
        ).execute()
