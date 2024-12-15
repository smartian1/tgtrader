# encoding: utf-8

import os
import sys
from getpass import getpass
from tgtrader.streamlit_pages.service.account_service import AccountService

def init_db():
    # 确保data目录存在
    data_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # 初始化用户服务
        account_service = AccountService()
        
        # 初始化表结构
        account_service.init_table()
        
        # 检查管理员账户是否已存在
        existing_admin = account_service.get_user_by_username("admin")
        if existing_admin:
            print("管理员账户已存在，无需重新创建")
            return
            
        # 获取管理员密码并确认
        while True:
            print("请输入管理员密码:")
            admin_password = getpass()
            
            if not admin_password:
                print("错误: 密码不能为空")
                continue
                
            print("请再次输入密码确认:")
            confirm_password = getpass()
            
            if admin_password != confirm_password:
                print("错误: 两次输入的密码不一致，请重新输入")
                continue
            
            break
            
        # 创建管理员账户
        account_service.create_user("admin", admin_password)
        print("管理员账户创建成功!")
        
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()

