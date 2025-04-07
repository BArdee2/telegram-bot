from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import os

# Create the declarative base
Base = declarative_base()

# Database engine setup
def get_engine():
    if not Config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured")
    
    if "render.com" in Config.DATABASE_URL:
        return create_engine(
            Config.DATABASE_URL,
            connect_args={
                "sslmode": "require",
                "sslrootcert": os.path.join(os.path.dirname(__file__), "cert.pem")
            }
        )
    return create_engine(Config.DATABASE_URL)

engine = get_engine()

# Use SessionLocal to make it clear this is a factory, not an instance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Delayed import to avoid circular import
    from models import User, Task, UserTask, Transaction
    Base.metadata.create_all(bind=engine)

# Dependency for fastapi or manual db use
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
