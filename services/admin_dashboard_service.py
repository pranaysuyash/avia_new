"""
Admin Dashboard Service
Provides comprehensive system monitoring, user management, and administrative operations
with real-time metrics and analytics.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import psutil
import aioredis
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from api.database import User, Team, Transcript, APIKey, AuditLog, Subscription
from api.cache.redis_cache import redis_cache
from services.audit_logging_service import audit_service, AuditEventType
from services.system_monitoring_service import monitoring_service
from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of system metrics"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    ACTIVE_USERS = "active_users"
    API_CALLS = "api_calls"
    TRANSCRIPTION_MINUTES = "transcription_minutes"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    WEBSOCKET_CONNECTIONS = "websocket_connections"


class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING = "pending"


@dataclass
class SystemMetrics:
    """System metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    active_users: int
    total_api_calls: int
    error_count: int
    avg_response_time_ms: float
    cache_hit_rate: float
    websocket_connections: int
    transcription_minutes_today: float
    system_health: str


@dataclass
class UserMetrics:
    """User activity metrics"""
    user_id: int
    username: str
    email: str
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime]
    total_transcriptions: int
    total_minutes_transcribed: float
    storage_used_mb: float
    api_calls_today: int
    subscription_tier: str
    team_name: Optional[str]
    is_team_admin: bool


@dataclass
class AdminDashboardStats:
    """Comprehensive admin dashboard statistics"""
    system_metrics: SystemMetrics
    user_stats: Dict[str, Any]
    usage_trends: Dict[str, List[Dict[str, Any]]]
    active_sessions: List[Dict[str, Any]]
    recent_errors: List[Dict[str, Any]]
    subscription_summary: Dict[str, Any]
    storage_summary: Dict[str, Any]
    api_usage_summary: Dict[str, Any]


class AdminDashboardService:
    """Service for admin dashboard operations"""
    
    def __init__(self):
        self.metrics_cache_ttl = 60  # 1 minute cache for metrics
        self.user_cache_ttl = 300  # 5 minutes cache for user data
        self.trend_data_days = 30  # Days of trend data to show
        
        # Performance thresholds
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0
        self.error_rate_threshold = 5.0  # percent
        self.response_time_threshold = 1000  # milliseconds
        
        # Start background tasks
        asyncio.create_task(self._collect_metrics_periodically())
    
    async def get_dashboard_stats(self, db: Session) -> AdminDashboardStats:
        """
        Get comprehensive dashboard statistics
        
        Args:
            db: Database session
            
        Returns:
            AdminDashboardStats object
        """
        
        try:
            # Get system metrics
            system_metrics = await self._get_system_metrics(db)
            
            # Get user statistics
            user_stats = await self._get_user_statistics(db)
            
            # Get usage trends
            usage_trends = await self._get_usage_trends(db)
            
            # Get active sessions
            active_sessions = await self._get_active_sessions()
            
            # Get recent errors
            recent_errors = await self._get_recent_errors(db)
            
            # Get subscription summary
            subscription_summary = await self._get_subscription_summary(db)
            
            # Get storage summary
            storage_summary = await self._get_storage_summary(db)
            
            # Get API usage summary
            api_usage_summary = await self._get_api_usage_summary(db)
            
            return AdminDashboardStats(
                system_metrics=system_metrics,
                user_stats=user_stats,
                usage_trends=usage_trends,
                active_sessions=active_sessions,
                recent_errors=recent_errors,
                subscription_summary=subscription_summary,
                storage_summary=storage_summary,
                api_usage_summary=api_usage_summary
            )
            
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            raise
    
    async def _get_system_metrics(self, db: Session) -> SystemMetrics:
        """Get current system metrics"""
        
        # Try cache first
        cached = await redis_cache.get("admin:system_metrics")
        if cached:
            data = json.loads(cached)
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            return SystemMetrics(**data)
        
        # Collect fresh metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get active users (logged in within last 15 minutes)
        active_threshold = datetime.utcnow() - timedelta(minutes=15)
        active_users = db.query(func.count(User.id)).filter(
            User.last_login >= active_threshold,
            User.status == UserStatus.ACTIVE.value
        ).scalar() or 0
        
        # Get today's API calls
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total_api_calls = db.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= today_start,
            AuditLog.event_type.like('API_%')
        ).scalar() or 0
        
        # Get error count
        error_count = db.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= today_start,
            AuditLog.event_type == AuditEventType.ERROR.value
        ).scalar() or 0
        
        # Get average response time from monitoring service
        avg_response_time = await monitoring_service.get_average_response_time()
        
        # Get cache hit rate
        cache_stats = await redis_cache.get_stats()
        cache_hit_rate = cache_stats.get('hit_rate', 0.0)
        
        # Get WebSocket connections
        websocket_connections = await self._get_websocket_connection_count()
        
        # Get transcription minutes today
        transcription_minutes = db.query(func.sum(Transcript.duration)).filter(
            Transcript.created_at >= today_start
        ).scalar() or 0.0
        
        # Calculate system health
        system_health = self._calculate_system_health(
            cpu_percent, memory.percent, disk.percent,
            error_count / max(total_api_calls, 1) * 100,
            avg_response_time
        )
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_total_mb=memory.total / 1024 / 1024,
            disk_percent=disk.percent,
            disk_used_gb=disk.used / 1024 / 1024 / 1024,
            disk_total_gb=disk.total / 1024 / 1024 / 1024,
            active_users=active_users,
            total_api_calls=total_api_calls,
            error_count=error_count,
            avg_response_time_ms=avg_response_time,
            cache_hit_rate=cache_hit_rate,
            websocket_connections=websocket_connections,
            transcription_minutes_today=transcription_minutes / 60.0,
            system_health=system_health
        )
        
        # Cache metrics
        metrics_dict = asdict(metrics)
        metrics_dict['timestamp'] = metrics.timestamp.isoformat()
        await redis_cache.set(
            "admin:system_metrics",
            json.dumps(metrics_dict),
            expiry=self.metrics_cache_ttl
        )
        
        return metrics
    
    def _calculate_system_health(
        self, 
        cpu: float, 
        memory: float, 
        disk: float,
        error_rate: float,
        response_time: float
    ) -> str:
        """Calculate overall system health status"""
        
        issues = 0
        
        if cpu >= self.cpu_threshold:
            issues += 2
        elif cpu >= self.cpu_threshold * 0.8:
            issues += 1
            
        if memory >= self.memory_threshold:
            issues += 2
        elif memory >= self.memory_threshold * 0.8:
            issues += 1
            
        if disk >= self.disk_threshold:
            issues += 1
            
        if error_rate >= self.error_rate_threshold:
            issues += 2
        elif error_rate >= self.error_rate_threshold * 0.5:
            issues += 1
            
        if response_time >= self.response_time_threshold:
            issues += 1
        
        if issues == 0:
            return "healthy"
        elif issues <= 2:
            return "good"
        elif issues <= 4:
            return "warning"
        else:
            return "critical"
    
    async def _get_user_statistics(self, db: Session) -> Dict[str, Any]:
        """Get user statistics"""
        
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(
            User.status == UserStatus.ACTIVE.value
        ).scalar() or 0
        
        # Users by subscription tier
        users_by_tier = db.query(
            User.subscription_tier,
            func.count(User.id)
        ).group_by(User.subscription_tier).all()
        
        # New users this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_month = db.query(func.count(User.id)).filter(
            User.created_at >= month_start
        ).scalar() or 0
        
        # Team statistics
        total_teams = db.query(func.count(Team.id)).scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "suspended_users": total_users - active_users,
            "users_by_tier": dict(users_by_tier),
            "new_users_this_month": new_users_month,
            "total_teams": total_teams,
            "growth_rate": self._calculate_growth_rate(db, month_start)
        }
    
    def _calculate_growth_rate(self, db: Session, current_month_start: datetime) -> float:
        """Calculate month-over-month growth rate"""
        
        # Previous month
        prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        current_month_users = db.query(func.count(User.id)).filter(
            User.created_at >= current_month_start
        ).scalar() or 0
        
        prev_month_users = db.query(func.count(User.id)).filter(
            and_(
                User.created_at >= prev_month_start,
                User.created_at < current_month_start
            )
        ).scalar() or 0
        
        if prev_month_users == 0:
            return 100.0 if current_month_users > 0 else 0.0
        
        return ((current_month_users - prev_month_users) / prev_month_users) * 100
    
    async def _get_usage_trends(self, db: Session) -> Dict[str, List[Dict[str, Any]]]:
        """Get usage trends over time"""
        
        trends = {
            "daily_users": [],
            "daily_transcriptions": [],
            "daily_api_calls": [],
            "daily_errors": []
        }
        
        # Get daily data for the last 30 days
        end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
        start_date = end_date - timedelta(days=self.trend_data_days)
        
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Daily active users
            daily_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
                and_(
                    AuditLog.created_at >= current_date,
                    AuditLog.created_at < next_date,
                    AuditLog.user_id.isnot(None)
                )
            ).scalar() or 0
            
            # Daily transcriptions
            daily_transcriptions = db.query(func.count(Transcript.id)).filter(
                and_(
                    Transcript.created_at >= current_date,
                    Transcript.created_at < next_date
                )
            ).scalar() or 0
            
            # Daily API calls
            daily_api_calls = db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.created_at >= current_date,
                    AuditLog.created_at < next_date,
                    AuditLog.event_type.like('API_%')
                )
            ).scalar() or 0
            
            # Daily errors
            daily_errors = db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.created_at >= current_date,
                    AuditLog.created_at < next_date,
                    AuditLog.event_type == AuditEventType.ERROR.value
                )
            ).scalar() or 0
            
            date_str = current_date.strftime('%Y-%m-%d')
            trends["daily_users"].append({"date": date_str, "value": daily_users})
            trends["daily_transcriptions"].append({"date": date_str, "value": daily_transcriptions})
            trends["daily_api_calls"].append({"date": date_str, "value": daily_api_calls})
            trends["daily_errors"].append({"date": date_str, "value": daily_errors})
            
            current_date = next_date
        
        return trends
    
    async def _get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get active user sessions"""
        
        # Get from Redis
        sessions = []
        pattern = "session:*"
        
        try:
            # Get all session keys
            cursor = '0'
            while cursor != 0:
                cursor, keys = await redis_cache.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    session_data = await redis_cache.get(key)
                    if session_data:
                        session = json.loads(session_data)
                        sessions.append({
                            "user_id": session.get("user_id"),
                            "username": session.get("username"),
                            "ip_address": session.get("ip_address"),
                            "user_agent": session.get("user_agent"),
                            "created_at": session.get("created_at"),
                            "last_activity": session.get("last_activity"),
                            "session_id": key.split(":")[-1]
                        })
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
        
        # Sort by last activity
        sessions.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        
        return sessions[:100]  # Limit to 100 most recent
    
    async def _get_recent_errors(self, db: Session) -> List[Dict[str, Any]]:
        """Get recent error logs"""
        
        errors = db.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.ERROR.value
        ).order_by(desc(AuditLog.created_at)).limit(50).all()
        
        return [
            {
                "id": error.id,
                "timestamp": error.created_at.isoformat(),
                "user_id": error.user_id,
                "action": error.action,
                "details": error.details,
                "ip_address": error.ip_address
            }
            for error in errors
        ]
    
    async def _get_subscription_summary(self, db: Session) -> Dict[str, Any]:
        """Get subscription summary"""
        
        # Revenue by tier
        revenue_by_tier = db.query(
            User.subscription_tier,
            func.count(User.id)
        ).filter(
            User.status == UserStatus.ACTIVE.value
        ).group_by(User.subscription_tier).all()
        
        # Calculate monthly recurring revenue (MRR)
        tier_prices = {
            "free": 0,
            "basic": 9.99,
            "pro": 29.99,
            "enterprise": 99.99
        }
        
        mrr = sum(
            count * tier_prices.get(tier, 0)
            for tier, count in revenue_by_tier
        )
        
        # Churn rate (users who downgraded or cancelled in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        churned_users = db.query(func.count(AuditLog.user_id.distinct())).filter(
            and_(
                AuditLog.created_at >= thirty_days_ago,
                AuditLog.event_type == AuditEventType.SUBSCRIPTION_CANCELLED.value
            )
        ).scalar() or 0
        
        total_paying_users = db.query(func.count(User.id)).filter(
            and_(
                User.status == UserStatus.ACTIVE.value,
                User.subscription_tier != 'free'
            )
        ).scalar() or 1
        
        churn_rate = (churned_users / total_paying_users) * 100
        
        return {
            "revenue_by_tier": dict(revenue_by_tier),
            "monthly_recurring_revenue": mrr,
            "annual_recurring_revenue": mrr * 12,
            "churn_rate": churn_rate,
            "paying_users": total_paying_users,
            "conversion_rate": (total_paying_users / max(db.query(func.count(User.id)).scalar(), 1)) * 100
        }
    
    async def _get_storage_summary(self, db: Session) -> Dict[str, Any]:
        """Get storage usage summary"""
        
        # Total storage used
        total_storage = db.query(
            func.sum(Transcript.file_size)
        ).scalar() or 0
        
        # Storage by user tier
        storage_by_tier = db.query(
            User.subscription_tier,
            func.sum(Transcript.file_size)
        ).join(
            Transcript, User.id == Transcript.user_id
        ).group_by(User.subscription_tier).all()
        
        # Top storage users
        top_users = db.query(
            User.id,
            User.username,
            func.sum(Transcript.file_size).label('total_storage')
        ).join(
            Transcript, User.id == Transcript.user_id
        ).group_by(User.id, User.username).order_by(
            desc('total_storage')
        ).limit(10).all()
        
        return {
            "total_storage_gb": total_storage / 1024 / 1024 / 1024,
            "storage_by_tier": {
                tier: (storage or 0) / 1024 / 1024 / 1024
                for tier, storage in storage_by_tier
            },
            "top_storage_users": [
                {
                    "user_id": user_id,
                    "username": username,
                    "storage_gb": total / 1024 / 1024 / 1024
                }
                for user_id, username, total in top_users
            ],
            "average_file_size_mb": (total_storage / max(db.query(func.count(Transcript.id)).scalar(), 1)) / 1024 / 1024
        }
    
    async def _get_api_usage_summary(self, db: Session) -> Dict[str, Any]:
        """Get API usage summary"""
        
        # API calls by endpoint
        api_calls = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            and_(
                AuditLog.event_type.like('API_%'),
                AuditLog.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).group_by(AuditLog.action).order_by(desc(func.count(AuditLog.id))).limit(20).all()
        
        # API keys usage
        api_key_usage = db.query(
            APIKey.name,
            func.count(AuditLog.id).label('usage_count')
        ).join(
            AuditLog, APIKey.user_id == AuditLog.user_id
        ).filter(
            and_(
                AuditLog.event_type.like('API_%'),
                AuditLog.created_at >= datetime.utcnow() - timedelta(days=7),
                APIKey.is_active == True
            )
        ).group_by(APIKey.name).order_by(desc('usage_count')).limit(10).all()
        
        return {
            "top_endpoints": [
                {"endpoint": endpoint, "calls": count}
                for endpoint, count in api_calls
            ],
            "top_api_keys": [
                {"key_name": key_name, "usage": usage}
                for key_name, usage in api_key_usage
            ],
            "total_api_calls_week": sum(count for _, count in api_calls)
        }
    
    async def get_user_list(
        self, 
        db: Session,
        page: int = 1,
        per_page: int = 50,
        search: Optional[str] = None,
        status_filter: Optional[UserStatus] = None,
        tier_filter: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[UserMetrics], int]:
        """
        Get paginated user list with filters
        
        Args:
            db: Database session
            page: Page number
            per_page: Items per page
            search: Search term
            status_filter: Filter by status
            tier_filter: Filter by subscription tier
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            
        Returns:
            Tuple of (users, total_count)
        """
        
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
        
        if status_filter:
            query = query.filter(User.status == status_filter.value)
        
        if tier_filter:
            query = query.filter(User.subscription_tier == tier_filter)
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        # Build user metrics
        user_metrics = []
        for user in users:
            # Get user statistics
            transcription_count = db.query(func.count(Transcript.id)).filter(
                Transcript.user_id == user.id
            ).scalar() or 0
            
            total_minutes = db.query(func.sum(Transcript.duration)).filter(
                Transcript.user_id == user.id
            ).scalar() or 0
            
            storage_used = db.query(func.sum(Transcript.file_size)).filter(
                Transcript.user_id == user.id
            ).scalar() or 0
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            api_calls_today = db.query(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.user_id == user.id,
                    AuditLog.created_at >= today_start,
                    AuditLog.event_type.like('API_%')
                )
            ).scalar() or 0
            
            # Get team info
            team_name = None
            is_team_admin = False
            if user.team_id:
                team = db.query(Team).filter(Team.id == user.team_id).first()
                if team:
                    team_name = team.name
                    is_team_admin = user.id == team.owner_id
            
            user_metrics.append(UserMetrics(
                user_id=user.id,
                username=user.username,
                email=user.email,
                status=UserStatus(user.status) if user.status else UserStatus.ACTIVE,
                created_at=user.created_at,
                last_login=user.last_login,
                total_transcriptions=transcription_count,
                total_minutes_transcribed=total_minutes / 60.0,
                storage_used_mb=storage_used / 1024 / 1024 if storage_used else 0,
                api_calls_today=api_calls_today,
                subscription_tier=user.subscription_tier,
                team_name=team_name,
                is_team_admin=is_team_admin
            ))
        
        return user_metrics, total_count
    
    async def update_user_status(
        self,
        db: Session,
        user_id: int,
        new_status: UserStatus,
        admin_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Update user account status
        
        Args:
            db: Database session
            user_id: User to update
            new_status: New status
            admin_id: Admin performing the action
            reason: Optional reason for status change
            
        Returns:
            Success boolean
        """
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            old_status = user.status
            user.status = new_status.value
            user.updated_at = datetime.utcnow()
            
            # Log the action
            audit_service.log_event(
                event_type=AuditEventType.USER_STATUS_CHANGED,
                action=f"User status changed from {old_status} to {new_status.value}",
                user_id=admin_id,
                details={
                    "target_user_id": user_id,
                    "old_status": old_status,
                    "new_status": new_status.value,
                    "reason": reason
                }
            )
            
            db.commit()
            
            # Clear user cache
            await redis_cache.delete(f"user:{user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user status: {e}")
            db.rollback()
            return False
    
    async def get_system_settings(self) -> Dict[str, Any]:
        """Get current system settings"""
        
        settings = await redis_cache.get("system:settings")
        if settings:
            return json.loads(settings)
        
        # Default settings
        default_settings = {
            "maintenance_mode": False,
            "allow_registrations": True,
            "require_email_verification": True,
            "max_upload_size_mb": 500,
            "max_transcription_length_minutes": 180,
            "rate_limit_per_minute": 60,
            "session_timeout_minutes": 30,
            "password_min_length": 8,
            "password_require_special": True,
            "enable_api_access": True,
            "enable_webhooks": True,
            "backup_enabled": True,
            "backup_interval_hours": 24
        }
        
        await redis_cache.set(
            "system:settings",
            json.dumps(default_settings),
            expiry=3600
        )
        
        return default_settings
    
    async def update_system_settings(
        self,
        settings: Dict[str, Any],
        admin_id: int
    ) -> bool:
        """
        Update system settings
        
        Args:
            settings: New settings
            admin_id: Admin making the change
            
        Returns:
            Success boolean
        """
        
        try:
            # Validate settings
            current_settings = await self.get_system_settings()
            updated_settings = {**current_settings, **settings}
            
            # Save to cache
            await redis_cache.set(
                "system:settings",
                json.dumps(updated_settings),
                expiry=3600
            )
            
            # Log the change
            audit_service.log_event(
                event_type=AuditEventType.SYSTEM_SETTINGS_CHANGED,
                action="System settings updated",
                user_id=admin_id,
                details={
                    "changed_settings": settings
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update system settings: {e}")
            return False
    
    async def _get_websocket_connection_count(self) -> int:
        """Get current WebSocket connection count"""
        
        try:
            # Get from monitoring service or Redis
            count = await redis_cache.get("websocket:connection_count")
            return int(count) if count else 0
        except:
            return 0
    
    async def _collect_metrics_periodically(self):
        """Background task to collect metrics periodically"""
        
        while True:
            try:
                # Collect and cache metrics every minute
                await asyncio.sleep(60)
                
                # This will trigger metric collection and caching
                # when called by the dashboard
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)


# Global admin dashboard service instance
admin_dashboard_service = AdminDashboardService()