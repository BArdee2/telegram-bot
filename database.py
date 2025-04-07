from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
import os

# Remove any mysql.connector imports

Base = declarative_base()

# Handle Render's PostgreSQL SSL requirement
def get_engine():
    if Config.DATABASE_URL and "render.com" in Config.DATABASE_URL:
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
