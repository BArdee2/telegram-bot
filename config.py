import os

class Config:
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/database_name')
    MIN_WITHDRAWAL = float(os.getenv('MIN_WITHDRAWAL', '10.00'))
