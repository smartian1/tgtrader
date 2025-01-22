# encoding: utf-8
import streamlit as st
import bcrypt
from cryptography.fernet import Fernet


def get_user_name():
    return st.session_state.user_info['username']

def hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify(password: str, pwd_saved: str) -> bool:
    return bcrypt.checkpw(password.encode(), pwd_saved.encode())

def encrypt(data: str, key: str) -> str:
    cipher = Fernet(key)
    return cipher.encrypt(data.encode()).decode()

def decrypt(data: str, key: str) -> str:
    cipher = Fernet(key)
    return cipher.decrypt(data.encode()).decode()

