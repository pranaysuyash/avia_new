"""
Upload Models
Database models for tracking upload sessions and multipart uploads
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

from database.base import Base


class UploadStatus(str, enum.Enum):
    """Upload status enum"""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    EXPIRED = "expired"


class UploadSession(Base):
    """Model for tracking upload sessions"""
    __tablename__ = "upload_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File information
    file_key = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Upload status
    status = Column(Enum(UploadStatus), default=UploadStatus.PENDING, nullable=False)
    
    # Multipart upload info
    is_multipart = Column(Boolean, default=False)
    part_size = Column(Integer, nullable=True)
    total_parts = Column(Integer, nullable=True)
    
    # Verification data
    verified_size = Column(Integer, nullable=True)
    s3_etag = Column(String, nullable=True)
    
    # File metadata
    file_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="upload_sessions")
    parts = relationship("UploadPart", back_populates="upload_session", cascade="all, delete-orphan")
    
    def is_expired(self) -> bool:
        """Check if upload session has expired"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "file_key": self.file_key,
            "filename": self.filename,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "status": self.status.value,
            "is_multipart": self.is_multipart,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class UploadPart(Base):
    """Model for tracking multipart upload parts"""
    __tablename__ = "upload_parts"
    
    id = Column(Integer, primary_key=True)
    upload_session_id = Column(String, ForeignKey("upload_sessions.id"), nullable=False)
    
    # Part information
    part_number = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    etag = Column(String, nullable=True)
    
    # Status
    status = Column(Enum(UploadStatus), default=UploadStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    upload_session = relationship("UploadSession", back_populates="parts")
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "part_number": self.part_number,
            "size": self.size,
            "etag": self.etag,
            "status": self.status.value,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }