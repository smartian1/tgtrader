# encoding: utf-8
import streamlit as st
from ..dao.t_user import User, db

class AccountService:
    @classmethod
    def verify_user(cls, username, password):
        """Verify user credentials from database and return user info"""
        try:
            with db:
                user = User.get_or_none(User.username == username)
                if user and user.verify_password(password):
                    return {
                        'id': user.id,
                        'username': user.username,
                        'role': user.role
                    }
                return None
                
        except Exception as e:
            st.error(f'数据库错误：{str(e)}')
            return None
