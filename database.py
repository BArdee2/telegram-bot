from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import os

Base = declarative_base()

def get_engine():
    if not Config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured")
    
    # For Render PostgreSQL
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
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
