from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import Config

# Database URL
DATABASE_URL = Config.DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Base class for declarative models
Base = declarative_base()

# SessionLocal is the factory for creating new session objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize the database and create all tables.
    This should be called when starting the application.
    """
    Base.metadata.create_all(bind=engine)
    
