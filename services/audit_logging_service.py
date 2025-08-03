#!/usr/bin/env python3
"""
Audit Logging Service
Comprehensive logging of all system activities for compliance and security
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func, and_, or_
import os
from enum import Enum

logger = logging.getLogger(__name__)

# Audit log database model
Base = declarative_base()

class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # User Management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_REACTIVATE = "user_reactivate"
    
    # Access Control
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_CHANGE = "role_change"
    
    # Data Access
    DATA_VIEW = "data_view"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"
    
    # Transcription
    TRANSCRIPT_CREATE = "transcript_create"
    TRANSCRIPT_UPDATE = "transcript_update"
    TRANSCRIPT_DELETE = "transcript_delete"
    TRANSCRIPT_SHARE = "transcript_share"
    
    # Team Management
    TEAM_CREATE = "team_create"
    TEAM_UPDATE = "team_update"
    TEAM_DELETE = "team_delete"
    TEAM_MEMBER_ADD = "team_member_add"
    TEAM_MEMBER_REMOVE = "team_member_remove"
    
    # Subscription
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    
    # System
    CONFIG_CHANGE = "config_change"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    SYSTEM_ERROR = "system_error"
    API_ERROR = "api_error"

class AuditLog(Base):
    """Audit log entry"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    result = Column(String(20), nullable=False)  # success, failure, error
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_session', 'session_id'),
    )

class AuditLoggingService:
    """Service for comprehensive audit logging"""
    
    def __init__(self, database_url: Optional[str] = None):
        # Use separate database for audit logs if configured
        if not database_url:
            database_url = os.getenv('AUDIT_DATABASE_URL', os.getenv('DATABASE_URL'))
        
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        result: str = "success",
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            db = self.SessionLocal()
            
            audit_log = AuditLog(
                event_type=event_type.value if isinstance(event_type, AuditEventType) else event_type,
                action=action,
                result=result,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                details=details,
                error_message=error_message,
                session_id=session_id,
                request_id=request_id
            )
            
            db.add(audit_log)
            db.commit()
            
            # Log critical events
            if result == "failure" or event_type in [
                AuditEventType.LOGIN_FAILED,
                AuditEventType.USER_DELETE,
                AuditEventType.SYSTEM_ERROR
            ]:
                logger.warning(
                    f"Audit Event: {event_type} - {action} - {result} "
                    f"(User: {username or user_id}, Resource: {resource_type}:{resource_id})"
                )
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def log_authentication(
        self,
        event_type: AuditEventType,
        user_id: Optional[int],
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication events"""
        self.log_event(
            event_type=event_type,
            action=f"User {event_type.value}",
            result="success" if success else "failure",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
    
    def log_data_access(
        self,
        user_id: int,
        username: str,
        action: str,
        resource_type: str,
        resource_id: Any,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log data access events"""
        self.log_event(
            event_type=AuditEventType.DATA_VIEW,
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
    
    def log_configuration_change(
        self,
        user_id: int,
        username: str,
        config_type: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None
    ):
        """Log configuration changes"""
        self.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            action=f"Updated {config_type} configuration",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={
                'config_type': config_type,
                'old_value': old_value,
                'new_value': new_value
            }
        )
    
    def query_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        event_types: Optional[List[str]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
        db = self.SessionLocal()
        try:
            query = db.query(AuditLog)
            
            # Apply filters
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if event_types:
                query = query.filter(AuditLog.event_type.in_(event_types))
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if resource_id:
                query = query.filter(AuditLog.resource_id == str(resource_id))
            
            if result:
                query = query.filter(AuditLog.result == result)
            
            # Order by timestamp descending
            query = query.order_by(AuditLog.timestamp.desc())
            
            # Apply pagination
            total = query.count()
            logs = query.offset(offset).limit(limit).all()
            
            # Convert to dict
            return {
                'total': total,
                'logs': [
                    {
                        'id': log.id,
                        'timestamp': log.timestamp.isoformat(),
                        'event_type': log.event_type,
                        'user_id': log.user_id,
                        'username': log.username,
                        'ip_address': log.ip_address,
                        'resource_type': log.resource_type,
                        'resource_id': log.resource_id,
                        'action': log.action,
                        'result': log.result,
                        'details': log.details,
                        'error_message': log.error_message
                    }
                    for log in logs
                ]
            }
            
        finally:
            db.close()
    
    def get_user_activity(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return self.query_logs(
            start_date=start_date,
            user_id=user_id,
            limit=limit
        )
    
    def get_security_events(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent security-related events"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        security_events = [
            AuditEventType.LOGIN_FAILED.value,
            AuditEventType.USER_SUSPEND.value,
            AuditEventType.PERMISSION_REVOKE.value,
            AuditEventType.SYSTEM_ERROR.value,
            AuditEventType.API_ERROR.value
        ]
        
        return self.query_logs(
            start_date=start_date,
            event_types=security_events,
            limit=limit
        )
    
    def get_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate compliance report for audit purposes"""
        db = self.SessionLocal()
        try:
            # Base query
            query = db.query(AuditLog).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            # Get event type distribution
            event_distribution = db.query(
                AuditLog.event_type,
                func.count(AuditLog.id).label('count')
            ).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            ).group_by(AuditLog.event_type).all()
            
            # Get result distribution
            result_distribution = db.query(
                AuditLog.result,
                func.count(AuditLog.id).label('count')
            ).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            ).group_by(AuditLog.result).all()
            
            # Get top users by activity
            top_users = db.query(
                AuditLog.username,
                func.count(AuditLog.id).label('count')
            ).filter(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                    AuditLog.username.isnot(None)
                )
            ).group_by(AuditLog.username).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10).all()
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_events': query.count(),
                    'unique_users': db.query(
                        func.count(func.distinct(AuditLog.user_id))
                    ).filter(
                        and_(
                            AuditLog.timestamp >= start_date,
                            AuditLog.timestamp <= end_date
                        )
                    ).scalar()
                },
                'event_distribution': [
                    {'event_type': e[0], 'count': e[1]}
                    for e in event_distribution
                ],
                'result_distribution': [
                    {'result': r[0], 'count': r[1]}
                    for r in result_distribution
                ],
                'top_users': [
                    {'username': u[0], 'activity_count': u[1]}
                    for u in top_users
                ]
            }
            
        finally:
            db.close()
    
    def cleanup_old_logs(self, retention_days: int = 90):
        """Clean up old audit logs"""
        db = self.SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old logs
            deleted = db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted} old audit logs")
            
            # Log the cleanup action
            self.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                action="Audit log cleanup",
                details={
                    'retention_days': retention_days,
                    'deleted_count': deleted
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            db.rollback()
        finally:
            db.close()

# Global instance
audit_service = AuditLoggingService()

def get_audit_service() -> AuditLoggingService:
    """Get audit service instance"""
    return audit_service