"""
Dependency Injection

Provides FastAPI dependencies for database sessions.

Author: LinkedIn AI Studio
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db() -> Session:
    """
    Dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()