# encoding: utf-8
import streamlit as st
from tgtrader.streamlit_pages.dao.t_user import User
from loguru import logger

class AccountService:
    @classmethod
    def get_user_by_username(cls, username):
        try:
            user = User.get_user_by_username(username)
            return user
        except Exception as e:
            logger.exception(e)
            raise Exception(f'query user error: {str(e)}')

    @classmethod
    def verify_user(cls, username: str, password: str):
        """Verify user credentials and return user info"""
        try:
            user = cls.get_user_by_username(username)
            if user and user.verify_password(password):
                return {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            return None
                
        except Exception as e:
            logger.exception(e)
            raise Exception(f'verify user error: {str(e)}')

    @classmethod
    def create_user(cls, username: str, password: str, role: str = 'admin'):
        """Create a new user"""
        try:
            user = User.create_user(username, password, role)
            return {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        except Exception as e:
            logger.exception(e)
            raise Exception(f"create user error: {str(e)}")

    @classmethod
    def init_table(cls):
        """Initialize database tables"""
        User.init_table()

