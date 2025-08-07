"""
GraphQL Schema Definition with Subscriptions
Provides comprehensive GraphQL API with real-time subscription support
"""

import strawberry
from typing import List, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import json
from enum import Enum

from api.graphql.types import (
    User,
    Transcript,
    TranscriptionJob,
    CacheStats,
    BackupInfo,
    RateLimitInfo,
    SystemMetrics,
    NotificationMessage
)
from api.graphql.resolvers import (
    UserResolver,
    TranscriptResolver,
    TranscriptionJobResolver,
    SystemResolver,
    NotificationResolver
)
from api.graphql.subscription_manager import subscription_manager


@strawberry.enum
class SubscriptionType(Enum):
    TRANSCRIPTION_STATUS = "transcription_status"
    SYSTEM_METRICS = "system_metrics"
    USER_NOTIFICATIONS = "user_notifications"
    CACHE_UPDATES = "cache_updates"
    BACKUP_STATUS = "backup_status"
    RATE_LIMIT_ALERTS = "rate_limit_alerts"


@strawberry.type
class Query:
    """GraphQL Query root"""
    
    # User queries
    @strawberry.field
    async def user(self, info, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await UserResolver.get_user(user_id)
    
    @strawberry.field
    async def users(self, info, limit: int = 50, offset: int = 0) -> List[User]:
        """Get list of users"""
        return await UserResolver.get_users(limit, offset)
    
    @strawberry.field
    async def current_user(self, info) -> Optional[User]:
        """Get current authenticated user"""
        return await UserResolver.get_current_user(info.context)
    
    # Transcript queries
    @strawberry.field
    async def transcript(self, info, transcript_id: str) -> Optional[Transcript]:
        """Get transcript by ID"""
        return await TranscriptResolver.get_transcript(transcript_id)
    
    @strawberry.field
    async def transcripts(
        self, 
        info, 
        user_id: Optional[int] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> List[Transcript]:
        """Get list of transcripts"""
        return await TranscriptResolver.get_transcripts(user_id, limit, offset)
    
    @strawberry.field
    async def search_transcripts(
        self, 
        info, 
        query: str, 
        limit: int = 20
    ) -> List[Transcript]:
        """Search transcripts by content"""
        return await TranscriptResolver.search_transcripts(query, limit)
    
    # Transcription job queries
    @strawberry.field
    async def transcription_job(self, info, job_id: str) -> Optional[TranscriptionJob]:
        """Get transcription job by ID"""
        return await TranscriptionJobResolver.get_job(job_id)
    
    @strawberry.field
    async def transcription_jobs(
        self, 
        info, 
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[TranscriptionJob]:
        """Get list of transcription jobs"""
        return await TranscriptionJobResolver.get_jobs(user_id, status, limit)
    
    # System queries
    @strawberry.field
    async def system_metrics(self, info) -> SystemMetrics:
        """Get current system metrics"""
        return await SystemResolver.get_system_metrics()
    
    @strawberry.field
    async def cache_stats(self, info) -> CacheStats:
        """Get cache statistics"""
        return await SystemResolver.get_cache_stats()
    
    @strawberry.field
    async def backup_info(self, info, backup_id: Optional[str] = None) -> List[BackupInfo]:
        """Get backup information"""
        return await SystemResolver.get_backup_info(backup_id)
    
    @strawberry.field
    async def rate_limit_info(self, info, identifier: str, scope: str) -> RateLimitInfo:
        """Get rate limiting information"""
        return await SystemResolver.get_rate_limit_info(identifier, scope)


@strawberry.type
class Mutation:
    """GraphQL Mutation root"""
    
    # Transcription mutations
    @strawberry.mutation
    async def start_transcription(
        self, 
        info, 
        file_url: str, 
        language: Optional[str] = None
    ) -> TranscriptionJob:
        """Start a new transcription job"""
        return await TranscriptionJobResolver.start_transcription(
            info.context, file_url, language
        )
    
    @strawberry.mutation
    async def cancel_transcription(self, info, job_id: str) -> TranscriptionJob:
        """Cancel a transcription job"""
        return await TranscriptionJobResolver.cancel_transcription(job_id)
    
    @strawberry.mutation
    async def update_transcript(
        self, 
        info, 
        transcript_id: str, 
        content: Optional[str] = None,
        title: Optional[str] = None
    ) -> Transcript:
        """Update transcript content"""
        return await TranscriptResolver.update_transcript(
            transcript_id, content, title
        )
    
    @strawberry.mutation
    async def delete_transcript(self, info, transcript_id: str) -> bool:
        """Delete a transcript"""
        return await TranscriptResolver.delete_transcript(transcript_id)
    
    # System mutations
    @strawberry.mutation
    async def create_backup(self, info, backup_type: str = "manual") -> BackupInfo:
        """Create a system backup"""
        return await SystemResolver.create_backup(backup_type)
    
    @strawberry.mutation
    async def invalidate_cache(self, info, cache_keys: Optional[List[str]] = None) -> bool:
        """Invalidate cache entries"""
        return await SystemResolver.invalidate_cache(cache_keys)
    
    @strawberry.mutation
    async def reset_rate_limit(
        self, 
        info, 
        identifier: str, 
        scope: str
    ) -> bool:
        """Reset rate limiting for identifier"""
        return await SystemResolver.reset_rate_limit(identifier, scope)


@strawberry.type
class Subscription:
    """GraphQL Subscription root for real-time updates"""
    
    @strawberry.subscription
    async def transcription_status(
        self, 
        info, 
        job_ids: Optional[List[str]] = None,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[TranscriptionJob, None]:
        """Subscribe to transcription job status updates"""
        
        async def get_updates():
            subscription_id = await subscription_manager.subscribe(
                subscription_type=SubscriptionType.TRANSCRIPTION_STATUS,
                user_id=user_id,
                filters={"job_ids": job_ids} if job_ids else None
            )
            
            try:
                async for update in subscription_manager.get_updates(subscription_id):
                    if update.get("type") == "transcription_job":
                        job_data = update.get("data")
                        if job_data:
                            yield TranscriptionJob(
                                id=job_data["id"],
                                user_id=job_data["user_id"],
                                status=job_data["status"],
                                progress=job_data.get("progress", 0),
                                file_url=job_data["file_url"],
                                language=job_data.get("language"),
                                created_at=job_data["created_at"],
                                updated_at=job_data["updated_at"],
                                error_message=job_data.get("error_message")
                            )
            finally:
                await subscription_manager.unsubscribe(subscription_id)
        
        async for update in get_updates():
            yield update
    
    @strawberry.subscription
    async def system_metrics(
        self, 
        info, 
        interval_seconds: int = 30
    ) -> AsyncGenerator[SystemMetrics, None]:
        """Subscribe to system metrics updates"""
        
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.SYSTEM_METRICS,
            user_id=None,  # System-wide metrics
            filters={"interval": interval_seconds}
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "system_metrics":
                    metrics_data = update.get("data")
                    if metrics_data:
                        yield SystemMetrics(
                            timestamp=metrics_data["timestamp"],
                            cpu_usage=metrics_data["cpu_usage"],
                            memory_usage=metrics_data["memory_usage"],
                            disk_usage=metrics_data["disk_usage"],
                            active_connections=metrics_data["active_connections"],
                            request_rate=metrics_data["request_rate"],
                            error_rate=metrics_data["error_rate"]
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    @strawberry.subscription
    async def user_notifications(
        self, 
        info, 
        user_id: int
    ) -> AsyncGenerator[NotificationMessage, None]:
        """Subscribe to user-specific notifications"""
        
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.USER_NOTIFICATIONS,
            user_id=user_id
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "notification":
                    notification_data = update.get("data")
                    if notification_data:
                        yield NotificationMessage(
                            id=notification_data["id"],
                            user_id=notification_data["user_id"],
                            title=notification_data["title"],
                            message=notification_data["message"],
                            type=notification_data["type"],
                            priority=notification_data["priority"],
                            read=notification_data["read"],
                            created_at=notification_data["created_at"]
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    @strawberry.subscription
    async def cache_updates(self, info) -> AsyncGenerator[CacheStats, None]:
        """Subscribe to cache statistics updates"""
        
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.CACHE_UPDATES,
            user_id=None
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "cache_stats":
                    cache_data = update.get("data")
                    if cache_data:
                        yield CacheStats(
                            connected=cache_data["connected"],
                            uptime_seconds=cache_data["uptime_seconds"],
                            memory_used=cache_data["memory"]["used_bytes"],
                            memory_peak=cache_data["memory"]["peak_bytes"],
                            hit_rate=cache_data["stats"]["hit_rate"],
                            total_requests=cache_data["stats"]["total_requests"],
                            hits=cache_data["stats"]["hits"],
                            misses=cache_data["stats"]["misses"],
                            total_keys=cache_data["keyspace"]["total_keys"]
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    @strawberry.subscription
    async def backup_status(self, info) -> AsyncGenerator[BackupInfo, None]:
        """Subscribe to backup status updates"""
        
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.BACKUP_STATUS,
            user_id=None
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "backup_info":
                    backup_data = update.get("data")
                    if backup_data:
                        yield BackupInfo(
                            backup_id=backup_data["backup_id"],
                            status=backup_data["status"],
                            progress=backup_data.get("progress", 0),
                            size=backup_data.get("size"),
                            components=backup_data.get("components", []),
                            created_at=backup_data["created_at"],
                            completed_at=backup_data.get("completed_at"),
                            error_message=backup_data.get("error_message")
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    @strawberry.subscription
    async def rate_limit_alerts(self, info) -> AsyncGenerator[RateLimitInfo, None]:
        """Subscribe to rate limiting alerts and violations"""
        
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.RATE_LIMIT_ALERTS,
            user_id=None
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "rate_limit_alert":
                    alert_data = update.get("data")
                    if alert_data:
                        yield RateLimitInfo(
                            identifier=alert_data["identifier"],
                            scope=alert_data["scope"],
                            endpoint=alert_data.get("endpoint"),
                            current_usage=alert_data["current_usage"],
                            limit=alert_data["limit"],
                            reset_time=alert_data["reset_time"],
                            violation_type=alert_data.get("violation_type"),
                            timestamp=alert_data["timestamp"]
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)


# Create the GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)