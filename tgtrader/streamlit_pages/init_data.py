# encoding: utf-8

import os
import sys
from getpass import getpass

from loguru import logger
from tgtrader.streamlit_pages.service.account_service import AccountService
from tgtrader.streamlit_pages.service.user_strategy import UserStrategyService

def init_db():
    # Ensure data directory exists
    data_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Initialize user service
        account_service = AccountService()
        
        # Initialize strategy service
        user_strategy_service = UserStrategyService()
        
        # Initialize tables
        # user_strategy_service.init_table()  # Initialize strategy table first
        account_service.init_table()        # Then initialize user table
        
        # Check if admin account exists
        existing_admin = account_service.get_user_by_username("admin")
        if existing_admin:
            print("Admin account already exists, no need to recreate")
            return
            
        # Get admin password and confirm
        while True:
            print("Please enter admin password:")
            admin_password = getpass()
            
            if not admin_password:
                print("Error: Password cannot be empty")
                continue
                
            print("Please enter password again to confirm:")
            confirm_password = getpass()
            
            if admin_password != confirm_password:
                print("Error: Passwords do not match, please try again")
                continue
            
            break
            
        # Create admin account
        account_service.create_user("admin", admin_password)
        print("Admin account created successfully!")
        print("Strategy table initialized successfully!")
        
    except Exception as e:
        logger.exception(f"Initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()

