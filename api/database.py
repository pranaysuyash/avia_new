"""
Database configuration and models for FastAPI
Integrates with existing SQLAlchemy models from database.models
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
from contextlib import contextmanager

# Import existing models
from database.models import (
    Base, User, UserRole, Session as UserSession, APIKey,
    Transcript, SharedLink, SharePermission, ShareAccessLog,
    Annotation, TranscriptVersion, Team, TeamRole, TeamMember,
    Project, Notification
)

# Import upload models
from api.models.upload import UploadSession, UploadPart

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transcription_app.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings for concurrent access
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    Ensures proper cleanup of database connections
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions outside of FastAPI requests
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Export all models and utilities
__all__ = [
    # Database utilities
    'get_db',
    'get_db_context',
    'SessionLocal',
    'engine',
    # Models
    'Base',
    'User',
    'UserRole',
    'UserSession',
    'APIKey',
    'Transcript',
    'SharedLink',
    'SharePermission',
    'ShareAccessLog',
    'Annotation',
    'TranscriptVersion',
    'Team',
    'TeamRole',
    'TeamMember',
    'Project',
    'Notification'
]