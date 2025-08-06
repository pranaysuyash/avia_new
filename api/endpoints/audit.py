#!/usr/bin/env python3
"""
Audit API Endpoints
Access and manage audit logs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
import csv
import io

from database.models import User
from database.connection import get_db
from api.auth_routes_enhanced import get_current_user
from api.dependencies import require_role
from services.audit_logging_service import audit_service, AuditEventType
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])

# Request/Response Models

class AuditLogQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None
    event_types: Optional[List[str]] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class AuditLogResponse(BaseModel):
    id: int
    timestamp: str
    event_type: str
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str
    details: Optional[Dict[str, Any]]
    error_message: Optional[str]

class AuditLogsResponse(BaseModel):
    total: int
    logs: List[AuditLogResponse]

# Endpoints

@router.get("/logs", response_model=AuditLogsResponse)
@require_role("admin")
async def get_audit_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends()
):
    """Get audit logs with filters"""
    # Log access to audit logs
    audit_service.log_data_access(
        user_id=current_user.id,
        username=current_user.username,
        action="View audit logs",
        resource_type="audit_logs",
        resource_id="all"
    )
    
    # Parse event types
    event_types = [event_type] if event_type else None
    
    # Query logs
    result = audit_service.query_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        event_types=event_types,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        limit=limit,
        offset=offset
    )
    
    return result

@router.get("/logs/user/{user_id}")
@require_role("admin")
async def get_user_audit_logs(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends()
):
    """Get audit logs for specific user"""
    # Log access
    audit_service.log_data_access(
        user_id=current_user.id,
        username=current_user.username,
        action="View user audit logs",
        resource_type="audit_logs",
        resource_id=f"user_{user_id}"
    )
    
    logs = audit_service.get_user_activity(
        user_id=user_id,
        days=days,
        limit=limit
    )
    
    return logs

@router.get("/logs/security")
@require_role("admin")
async def get_security_events(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends()
):
    """Get recent security events"""
    # Log access
    audit_service.log_data_access(
        user_id=current_user.id,
        username=current_user.username,
        action="View security events",
        resource_type="audit_logs",
        resource_id="security"
    )
    
    events = audit_service.get_security_events(
        days=days,
        limit=limit
    )
    
    return events

@router.get("/logs/compliance-report")
@require_role("admin")
async def get_compliance_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user_id: Optional[int] = Query(None),
    current_user: User = Depends()
):
    """Generate compliance report"""
    # Log access
    audit_service.log_data_access(
        user_id=current_user.id,
        username=current_user.username,
        action="Generate compliance report",
        resource_type="audit_logs",
        resource_id="compliance_report",
        details={
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'target_user_id': user_id
        }
    )
    
    report = audit_service.get_compliance_report(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    return report

@router.get("/logs/export")
@require_role("admin")
async def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    current_user: User = Depends()
):
    """Export audit logs in CSV or JSON format"""
    # Log export
    audit_service.log_event(
        event_type=AuditEventType.DATA_EXPORT,
        action="Export audit logs",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="audit_logs",
        resource_id="export",
        details={
            'format': format,
            'filters': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'user_id': user_id,
                'event_type': event_type
            }
        }
    )
    
    # Get logs
    event_types = [event_type] if event_type else None
    
    result = audit_service.query_logs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        event_types=event_types,
        limit=10000  # Higher limit for exports
    )
    
    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                'timestamp', 'event_type', 'username', 'action',
                'result', 'resource_type', 'resource_id', 'ip_address'
            ]
        )
        writer.writeheader()
        
        for log in result['logs']:
            writer.writerow({
                'timestamp': log['timestamp'],
                'event_type': log['event_type'],
                'username': log['username'] or '',
                'action': log['action'],
                'result': log['result'],
                'resource_type': log['resource_type'] or '',
                'resource_id': log['resource_id'] or '',
                'ip_address': log['ip_address'] or ''
            })
        
        content = output.getvalue()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    
    else:  # JSON
        return Response(
            content=json.dumps(result, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )

@router.get("/event-types")
async def get_event_types(
    current_user: User = Depends(get_current_user)
):
    """Get available audit event types"""
    # Only admins get full list, others get limited list
    if current_user.role == "admin":
        event_types = [e.value for e in AuditEventType]
    else:
        # Limited list for regular users
        event_types = [
            AuditEventType.LOGIN.value,
            AuditEventType.LOGOUT.value,
            AuditEventType.TRANSCRIPT_CREATE.value,
            AuditEventType.TRANSCRIPT_UPDATE.value,
            AuditEventType.DATA_EXPORT.value
        ]
    
    return {
        "event_types": event_types,
        "categories": {
            "authentication": [
                e.value for e in AuditEventType
                if e.value.startswith(('login', 'logout', 'password'))
            ],
            "user_management": [
                e.value for e in AuditEventType
                if e.value.startswith('user_')
            ],
            "data_access": [
                e.value for e in AuditEventType
                if e.value.startswith('data_')
            ],
            "transcription": [
                e.value for e in AuditEventType
                if e.value.startswith('transcript_')
            ],
            "system": [
                e.value for e in AuditEventType
                if e.value.startswith(('config_', 'backup_', 'system_'))
            ]
        }
    }

@router.post("/cleanup")
@require_role("admin")
async def cleanup_old_logs(
    retention_days: int = Query(90, ge=30, le=365),
    current_user: User = Depends()
):
    """Clean up old audit logs"""
    # Log cleanup action
    audit_service.log_event(
        event_type=AuditEventType.SYSTEM_ERROR,
        action="Initiate audit log cleanup",
        user_id=current_user.id,
        username=current_user.username,
        details={'retention_days': retention_days}
    )
    
    # Perform cleanup
    audit_service.cleanup_old_logs(retention_days)
    
    return {
        "message": f"Cleanup initiated for logs older than {retention_days} days",
        "retention_days": retention_days
    }

@router.get("/my-activity")
async def get_my_activity(
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """Get current user's activity logs"""
    # Regular users can view their own activity
    logs = audit_service.get_user_activity(
        user_id=current_user.id,
        days=days,
        limit=limit
    )
    
    # Filter out sensitive information for non-admin users
    if current_user.role != "admin":
        for log in logs.get('logs', []):
            # Remove IP addresses and detailed error messages
            log.pop('ip_address', None)
            log.pop('error_message', None)
            # Simplify details
            if log.get('details'):
                log['details'] = {
                    k: v for k, v in log['details'].items()
                    if k in ['resource_name', 'action_type']
                }
    
    return logs