#!/usr/bin/env python3
"""
Database Models for Audio/Video Transcription App
Handles user authentication, transcripts, sharing, and collaboration
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
import os
from typing import Optional

Base = declarative_base()

class UserRole(enum.Enum):
    """User roles in the system"""
    USER = "user"
    ADMIN = "admin"
    VIEWER = "viewer"

class SharePermission(enum.Enum):
    """Permissions for shared content"""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"

class TeamRole(enum.Enum):
    """Roles within a team"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class User(Base):
    """User model for authentication and profile"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100), unique=True)
    reset_token = Column(String(100), unique=True)
    reset_token_expires = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="user", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", foreign_keys="TeamMember.user_id", back_populates="user", cascade="all, delete-orphan")
    owned_teams = relationship("Team", back_populates="owner")

class Session(Base):
    """User session management"""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class Transcript(Base):
    """Transcript storage with ownership"""
    __tablename__ = 'transcripts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    duration = Column(Float)
    language = Column(String(10), default='en')
    confidence = Column(Float)
    word_count = Column(Integer)
    entities = Column(JSON)
    summary = Column(Text)
    model_used = Column(String(50))
    processing_time = Column(Float)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transcripts")
    team = relationship("Team", back_populates="transcripts")
    shared_links = relationship("SharedLink", back_populates="transcript", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="transcript", cascade="all, delete-orphan")
    versions = relationship("TranscriptVersion", back_populates="transcript", cascade="all, delete-orphan")

class SharedLink(Base):
    """Shareable links for transcripts"""
    __tablename__ = 'shared_links'
    
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'), nullable=False)
    share_token = Column(String(100), unique=True, nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW)
    password_hash = Column(String(255))  # Optional password protection
    expires_at = Column(DateTime)
    max_views = Column(Integer)  # Optional view limit
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="shared_links")
    created_by = relationship("User")
    access_logs = relationship("ShareAccessLog", back_populates="shared_link", cascade="all, delete-orphan")

class ShareAccessLog(Base):
    """Log access to shared links"""
    __tablename__ = 'share_access_logs'
    
    id = Column(Integer, primary_key=True)
    shared_link_id = Column(Integer, ForeignKey('shared_links.id'), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    accessed_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    shared_link = relationship("SharedLink", back_populates="access_logs")

class Annotation(Base):
    """Comments and annotations on transcripts"""
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('annotations.id'), nullable=True)  # For replies
    content = Column(Text, nullable=False)
    position_start = Column(Integer)  # Character position in transcript
    position_end = Column(Integer)
    highlighted_text = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    transcript = relationship("Transcript", back_populates="annotations")
    user = relationship("User", back_populates="annotations")
    parent = relationship("Annotation", remote_side=[id], backref="replies")

class TranscriptVersion(Base):
    """Version history for transcripts"""
    __tablename__ = 'transcript_versions'
    
    id = Column(Integer, primary_key=True)
    transcript_id = Column(Integer, ForeignKey('transcripts.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    entities = Column(JSON)
    summary = Column(Text)
    changed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    change_summary = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    transcript = relationship("Transcript", back_populates="versions")
    changed_by = relationship("User")

class Team(Base):
    """Team workspace for collaboration"""
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, default=10)
    storage_quota_mb = Column(Integer, default=5000)  # 5GB default
    storage_used_mb = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="team")
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    """Team membership and roles"""
    __tablename__ = 'team_members'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)
    joined_at = Column(DateTime, server_default=func.now())
    invited_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="team_memberships")
    invited_by = relationship("User", foreign_keys=[invited_by_id])

class Project(Base):
    """Projects within teams for organizing transcripts"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="projects")
    created_by = relationship("User")

class Notification(Base):
    """User notifications for changes and mentions"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(50), nullable=False)  # mention, annotation_reply, transcript_edit, share_access
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500))  # Link to the relevant content
    related_id = Column(Integer)  # ID of related entity (transcript, annotation, etc.)
    related_type = Column(String(50))  # Type of related entity
    from_user_id = Column(Integer, ForeignKey('users.id'))
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    read_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="notifications")
    from_user = relationship("User", foreign_keys=[from_user_id])

# Database initialization
def init_db(database_url: Optional[str] = None):
    """Initialize database with all tables"""
    if not database_url:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///transcription_app.db')
    
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    return Session()

def get_db_session(database_url: Optional[str] = None):
    """Get a database session"""
    if not database_url:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///transcription_app.db')
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()