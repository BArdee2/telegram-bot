import os
from urllib.parse import urlparse

class Config:
    # Get Telegram bot token from environment variables
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Admin user IDs (comma separated in env)
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    
    # Database configuration (Render PostgreSQL)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Payment settings
    PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'stripe')
    MIN_WITHDRAWAL = float(os.getenv('MIN_WITHDRAWAL', '10.00'))
    CURRENCY = os.getenv('CURRENCY', 'USD')
    
    # Task settings
    MAX_TASKS_PER_USER = int(os.getenv('MAX_TASKS_PER_USER', '5'))
