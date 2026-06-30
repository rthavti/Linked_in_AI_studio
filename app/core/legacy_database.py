"""
Database Configuration

Sets up SQLAlchemy engine and session for the application.

Author: LinkedIn AI Studio
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

DATABASE_URL = "sqlite:///linkedin_ai.db"
engine = create_engine(settings.DATABASE_URL)


#engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()