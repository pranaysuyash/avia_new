"""
GraphQL Type Definitions
Defines all GraphQL types used in the schema
"""

import strawberry
from typing import List, Optional
from datetime import datetime
from enum import Enum


@strawberry.enum
class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


@strawberry.enum
class TranscriptionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@strawberry.enum
class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@strawberry.enum
class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@strawberry.type
class User:
    """User type definition"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    subscription_tier: Optional[str] = None


@strawberry.type
class TranscriptSegment:
    """Transcript segment with timing information"""
    id: int
    start: float
    end: float
    text: str
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    words: Optional[List[str]] = None


@strawberry.type
class Transcript:
    """Transcript type definition"""
    id: str
    user_id: int
    title: Optional[str] = None
    content: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: List[TranscriptSegment]
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = strawberry.field(default_factory=list)
    summary: Optional[str] = None
    key_topics: List[str] = strawberry.field(default_factory=list)


@strawberry.type
class TranscriptionJob:
    """Transcription job status and progress"""
    id: str
    user_id: int
    status: TranscriptionStatus
    progress: float  # 0-100
    file_url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    language: Optional[str] = None
    model: Optional[str] = None
    options: Optional[str] = None  # JSON string of options
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_transcript_id: Optional[str] = None
    estimated_completion: Optional[datetime] = None


@strawberry.type
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_usage: float  # Percentage
    memory_usage: float  # Percentage
    disk_usage: float  # Percentage
    active_connections: int
    request_rate: float  # Requests per second
    error_rate: float  # Percentage
    cache_hit_rate: Optional[float] = None
    database_connections: Optional[int] = None
    queue_size: Optional[int] = None
    uptime_seconds: Optional[int] = None


@strawberry.type
class CacheStats:
    """Cache performance statistics"""
    connected: bool
    uptime_seconds: int
    memory_used: int  # Bytes
    memory_peak: int  # Bytes
    hit_rate: float  # Percentage
    total_requests: int
    hits: int
    misses: int
    total_keys: int
    evicted_keys: Optional[int] = None
    expired_keys: Optional[int] = None
    ops_per_second: Optional[float] = None


@strawberry.type
class BackupInfo:
    """Backup status and information"""
    backup_id: str
    status: str
    progress: float  # 0-100
    size: Optional[int] = None  # Bytes
    components: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None
    location: Optional[str] = None
    s3_location: Optional[str] = None
    error_message: Optional[str] = None
    retention_days: Optional[int] = None


@strawberry.type
class RateLimitInfo:
    """Rate limiting information and alerts"""
    identifier: str
    scope: str
    endpoint: Optional[str] = None
    current_usage: int
    limit: int
    remaining: int
    reset_time: datetime
    window_seconds: Optional[int] = None
    algorithm: Optional[str] = None
    violation_type: Optional[str] = None
    timestamp: datetime


@strawberry.type
class NotificationMessage:
    """User notification message"""
    id: str
    user_id: int
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    read: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    metadata: Optional[str] = None  # JSON string for additional data


@strawberry.type
class CollaborationSession:
    """Real-time collaboration session"""
    id: str
    transcript_id: str
    host_user_id: int
    active_users: List[int]
    created_at: datetime
    last_activity: datetime
    is_active: bool
    permissions: Optional[str] = None  # JSON string


@strawberry.type
class RealtimeEdit:
    """Real-time edit operation for collaboration"""
    id: str
    session_id: str
    user_id: int
    operation_type: str  # insert, delete, replace
    position: int
    length: Optional[int] = None
    content: Optional[str] = None
    timestamp: datetime


@strawberry.type
class AnalyticsEvent:
    """Analytics event for tracking user activity"""
    id: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    event_type: str
    event_name: str
    properties: Optional[str] = None  # JSON string
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@strawberry.type
class APIUsage:
    """API usage statistics"""
    user_id: Optional[int] = None
    api_key: Optional[str] = None
    endpoint: str
    method: str
    status_code: int
    response_time: float  # Milliseconds
    timestamp: datetime
    request_size: Optional[int] = None
    response_size: Optional[int] = None


@strawberry.type
class WebhookEvent:
    """Webhook event for external integrations"""
    id: str
    webhook_url: str
    event_type: str
    payload: str  # JSON string
    status: str  # pending, sent, failed
    attempts: int
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    created_at: datetime


@strawberry.input
class TranscriptionJobInput:
    """Input type for creating transcription jobs"""
    file_url: str
    language: Optional[str] = None
    model: Optional[str] = None
    webhook_url: Optional[str] = None
    options: Optional[str] = None  # JSON string


@strawberry.input
class TranscriptUpdateInput:
    """Input type for updating transcripts"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None


@strawberry.input
class UserUpdateInput:
    """Input type for updating user information"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None


@strawberry.input
class NotificationInput:
    """Input type for creating notifications"""
    user_id: int
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    expires_at: Optional[datetime] = None


@strawberry.input
class CollaborationSessionInput:
    """Input type for creating collaboration sessions"""
    transcript_id: str
    permissions: Optional[str] = None  # JSON string


@strawberry.input
class SystemSettingsInput:
    """Input type for system settings"""
    max_file_size: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None
    default_language: Optional[str] = None
    backup_retention_days: Optional[int] = None
    rate_limit_enabled: Optional[bool] = None