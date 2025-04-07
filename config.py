import os
from urllib.parse import urlparse

class Config:
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')  # Fallback to SQLite
    
    # For Render PostgreSQL
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Verify we have a database URL
    if not DATABASE_URL:
        raise ValueError("No DATABASE_URL set in environment variables")
