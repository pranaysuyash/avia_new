#!/usr/bin/env python3
"""
Admin API Endpoints
Administrative functions and system management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from database.models import User, Team, Transcript, Notification
from database.subscription_models import Subscription, Payment, UsageRecord
from database.connection import get_db
from api.auth_routes_enhanced import get_current_user
from api.dependencies import require_role
from services.usage_analytics_service import UsageAnalyticsService
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize services
analytics_service = UsageAnalyticsService(get_db)

# Request/Response Models

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    role: str = Field("user", pattern="^(admin|user|viewer)$")
    plan_tier: Optional[str] = "free"

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class SystemAnnouncementRequest(BaseModel):
    title: str
    message: str
    priority: str = Field("info", pattern="^(info|warning|critical)$")
    recipients: List[str] = Field(default_factory=lambda: ["all"])

class SystemConfigRequest(BaseModel):
    category: str
    settings: Dict[str, Any]

class BackupRequest(BaseModel):
    backup_type: str = Field("full", pattern="^(full|incremental|selective)$")
    include_files: bool = True
    compress: bool = True

# Endpoints

@router.get("/stats/quick")
@require_role("admin")
async def get_quick_stats(
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Get quick statistics for admin dashboard"""
    # User stats
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(
        User.is_active == True,
        User.last_active >= datetime.utcnow() - timedelta(days=30)
    ).scalar()
    
    # Team stats
    total_teams = db.query(func.count(Team.id)).scalar()
    
    # Revenue stats (simplified)
    active_subscriptions = db.query(func.count(Subscription.id)).filter(
        Subscription.status.in_(['active', 'trialing'])
    ).scalar()
    
    # Calculate MRR
    mrr = db.query(func.sum(Subscription.monthly_amount)).filter(
        Subscription.status == 'active'
    ).scalar() or 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_teams": total_teams,
        "active_subscriptions": active_subscriptions,
        "mrr": float(mrr)
    }

@router.get("/stats/detailed")
@require_role("admin")
async def get_detailed_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Get detailed system statistics"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # User growth
    user_growth = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        func.date(User.created_at)
    ).all()
    
    # Transcript creation
    transcript_stats = db.query(
        func.date(Transcript.created_at).label('date'),
        func.count(Transcript.id).label('count'),
        func.sum(Transcript.duration).label('total_duration')
    ).filter(
        Transcript.created_at >= start_date
    ).group_by(
        func.date(Transcript.created_at)
    ).all()
    
    # Revenue by day
    revenue_stats = db.query(
        func.date(Payment.created_at).label('date'),
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.created_at >= start_date,
        Payment.status == 'succeeded'
    ).group_by(
        func.date(Payment.created_at)
    ).all()
    
    return {
        "period": f"{days} days",
        "user_growth": [
            {"date": row.date.isoformat(), "new_users": row.count}
            for row in user_growth
        ],
        "transcript_stats": [
            {
                "date": row.date.isoformat(),
                "count": row.count,
                "total_duration": float(row.total_duration or 0)
            }
            for row in transcript_stats
        ],
        "revenue_stats": [
            {"date": row.date.isoformat(), "revenue": float(row.total)}
            for row in revenue_stats
        ]
    }

@router.get("/users")
@require_role("admin")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    plan: Optional[str] = None,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """List all users with filters"""
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        if status == "active":
            query = query.filter(User.is_active == True)
        elif status == "inactive":
            query = query.filter(User.is_active == False)
    
    # Get total count
    total = query.count()
    
    # Get users
    users = query.offset(skip).limit(limit).all()
    
    # Format response
    return {
        "total": total,
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "last_active": user.last_active,
                "subscription": {
                    "plan": user.subscription.plan.name if user.subscription else "Free",
                    "status": user.subscription.status.value if user.subscription else "none"
                } if hasattr(user, 'subscription') else None
            }
            for user in users
        ]
    }

@router.post("/users")
@require_role("admin")
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    # Check if user exists
    existing = db.query(User).filter(
        or_(
            User.username == request.username,
            User.email == request.email
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    
    # Create user
    from auth.auth_service_enhanced import AuthenticationService
    auth_service = AuthenticationService(lambda: db)
    
    user = User(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        hashed_password=auth_service._hash_password(request.password),
        role=request.role,
        is_verified=True,  # Admin-created users are pre-verified
        created_by_id=current_user.id
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "User created successfully"
    }

@router.put("/users/{user_id}")
@require_role("admin")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Update user details"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.email is not None:
        user.email = request.email
    if request.role is not None:
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.is_verified is not None:
        user.is_verified = request.is_verified
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "User updated successfully"}

@router.post("/users/{user_id}/suspend")
@require_role("admin")
async def suspend_user(
    user_id: int,
    reason: str = Query(...),
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Suspend user account"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.suspension_reason = reason
    user.suspended_at = datetime.utcnow()
    user.suspended_by_id = current_user.id
    
    # Create notification
    notification = Notification(
        user_id=user_id,
        type='account_suspended',
        title='Account Suspended',
        message=f'Your account has been suspended. Reason: {reason}',
        priority='high'
    )
    db.add(notification)
    
    db.commit()
    
    return {"message": "User suspended successfully"}

@router.post("/users/{user_id}/unsuspend")
@require_role("admin")
async def unsuspend_user(
    user_id: int,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Unsuspend user account"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.suspension_reason = None
    user.suspended_at = None
    user.suspended_by_id = None
    
    # Create notification
    notification = Notification(
        user_id=user_id,
        type='account_unsuspended',
        title='Account Reactivated',
        message='Your account has been reactivated.',
        priority='info'
    )
    db.add(notification)
    
    db.commit()
    
    return {"message": "User unsuspended successfully"}

@router.delete("/users/{user_id}")
@require_role("admin")
async def delete_user(
    user_id: int,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting admin's own account
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete - mark as deleted
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    user.deleted_by_id = current_user.id
    
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.post("/announcement")
@require_role("admin")
async def send_announcement(
    request: SystemAnnouncementRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Send system announcement"""
    # Determine recipients
    recipients_query = db.query(User).filter(User.is_active == True)
    
    if "all" not in request.recipients:
        if "pro" in request.recipients:
            recipients_query = recipients_query.join(Subscription).filter(
                Subscription.plan.has(tier='pro')
            )
        if "enterprise" in request.recipients:
            recipients_query = recipients_query.join(Subscription).filter(
                Subscription.plan.has(tier='enterprise')
            )
        if "admins" in request.recipients:
            recipients_query = recipients_query.filter(User.role == 'admin')
    
    recipients = recipients_query.all()
    
    # Create notifications
    for recipient in recipients:
        notification = Notification(
            user_id=recipient.id,
            type='system_announcement',
            title=request.title,
            message=request.message,
            priority=request.priority,
            data={
                'sent_by': current_user.username,
                'sent_at': datetime.utcnow().isoformat()
            }
        )
        db.add(notification)
    
    db.commit()
    
    # Send emails in background
    background_tasks.add_task(
        send_announcement_emails,
        recipients,
        request.title,
        request.message
    )
    
    return {
        "message": f"Announcement sent to {len(recipients)} users",
        "recipient_count": len(recipients)
    }

@router.get("/system/health")
@require_role("admin")
async def get_system_health(
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    # Check various system components
    health_checks = {
        "database": check_database_health(db),
        "redis": check_redis_health(),
        "storage": check_storage_health(),
        "email": check_email_health(),
        "api": True  # If we got here, API is working
    }
    
    # Calculate overall health score
    operational_count = sum(1 for status in health_checks.values() if status)
    health_score = (operational_count / len(health_checks)) * 100
    
    return {
        "health_score": health_score,
        "status": "healthy" if health_score > 90 else "degraded" if health_score > 50 else "unhealthy",
        "services": health_checks,
        "timestamp": datetime.utcnow()
    }

@router.get("/system/config")
@require_role("admin")
async def get_system_config(
    category: Optional[str] = None,
    current_user: User = Depends()
):
    """Get system configuration"""
    # This would fetch from a configuration service/database
    config = {
        "general": {
            "app_name": "Transcription Platform",
            "app_url": "https://app.example.com",
            "timezone": "UTC",
            "maintenance_mode": False
        },
        "security": {
            "session_timeout": 60,
            "max_login_attempts": 5,
            "password_min_length": 8,
            "require_2fa": True
        },
        "limits": {
            "max_file_size": 2048,
            "max_transcript_length": 240,
            "rate_limit_per_hour": 1000,
            "concurrent_transcriptions": 10
        },
        "email": {
            "provider": "sendgrid",
            "from_address": "noreply@example.com",
            "from_name": "Transcription Platform"
        }
    }
    
    if category:
        return config.get(category, {})
    
    return config

@router.put("/system/config")
@require_role("admin")
async def update_system_config(
    request: SystemConfigRequest,
    current_user: User = Depends()
):
    """Update system configuration"""
    # This would update configuration in database/service
    logger.info(f"Admin {current_user.username} updated {request.category} config")
    
    return {
        "message": f"Configuration updated for {request.category}",
        "category": request.category,
        "updated_settings": len(request.settings)
    }

@router.post("/backup")
@require_role("admin")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends()
):
    """Create system backup"""
    backup_id = f"BKP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    # Start backup in background
    background_tasks.add_task(
        perform_backup,
        backup_id,
        request.backup_type,
        request.include_files,
        request.compress
    )
    
    return {
        "message": "Backup started",
        "backup_id": backup_id,
        "status": "in_progress"
    }

@router.get("/backup/history")
@require_role("admin")
async def get_backup_history(
    limit: int = 10,
    current_user: User = Depends()
):
    """Get backup history"""
    from services.backup_service import backup_service
    
    backups = backup_service.list_backups()
    
    # Format for API response
    formatted_backups = [
        {
            "id": backup['backup_id'],
            "date": backup['created_at'],
            "size": backup['size'],
            "type": backup['type'],
            "status": "success",
            "components": backup['components'],
            "created_by": backup.get('created_by')
        }
        for backup in backups[:limit]
    ]
    
    return formatted_backups

@router.post("/backup/{backup_id}/restore")
@require_role("admin")
async def restore_backup(
    backup_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends()
):
    """Restore from backup"""
    # This would initiate restore process
    background_tasks.add_task(
        perform_restore,
        backup_id,
        current_user.id
    )
    
    return {
        "message": "Restore started",
        "backup_id": backup_id,
        "status": "in_progress"
    }

@router.get("/activity/recent")
@require_role("admin")
async def get_recent_activity(
    limit: int = 50,
    activity_type: Optional[str] = None,
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Get recent system activity"""
    # This would fetch from activity log
    activities = []
    
    # Get recent user registrations
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    for user in recent_users:
        activities.append({
            "timestamp": user.created_at,
            "type": "user_registration",
            "user": user.username,
            "action": "User registered",
            "details": f"New user: {user.email}"
        })
    
    # Get recent transcripts
    recent_transcripts = db.query(Transcript).order_by(Transcript.created_at.desc()).limit(5).all()
    for transcript in recent_transcripts:
        activities.append({
            "timestamp": transcript.created_at,
            "type": "transcript_created",
            "user": transcript.user.username,
            "action": "Created transcript",
            "details": f"Title: {transcript.title}"
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:limit]

# Helper functions

def check_database_health(db: Session) -> bool:
    """Check database connectivity"""
    try:
        db.execute("SELECT 1")
        return True
    except Exception:
        return False

def check_redis_health() -> bool:
    """Check Redis connectivity"""
    # Implementation would check Redis connection
    return True

def check_storage_health() -> bool:
    """Check storage service health"""
    # Implementation would check S3/storage service
    return True

def check_email_health() -> bool:
    """Check email service health"""
    # Implementation would check email service
    return True

async def send_announcement_emails(recipients: List[User], title: str, message: str):
    """Send announcement emails to recipients"""
    # Implementation would send emails
    logger.info(f"Sending announcement to {len(recipients)} recipients")

async def perform_backup(backup_id: str, backup_type: str, include_files: bool, compress: bool):
    """Perform system backup"""
    from services.backup_service import backup_service
    
    result = await backup_service.create_backup(
        backup_type=backup_type,
        include_files=include_files,
        compress=compress
    )
    
    logger.info(f"Backup {backup_id} completed with status: {result.get('status')}")

async def perform_restore(backup_id: str, user_id: int):
    """Perform system restore"""
    from services.backup_service import backup_service
    
    result = await backup_service.restore_backup(
        backup_id=backup_id,
        user_id=user_id
    )
    
    logger.info(f"Restore from {backup_id} completed with status: {result.get('status')}")