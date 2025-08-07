"""
GraphQL Resolvers
Implements business logic for GraphQL queries, mutations, and subscriptions
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from api.database import get_db, User as UserModel, Transcript as TranscriptModel
from api.graphql.types import (
    User, Transcript, TranscriptionJob, SystemMetrics, 
    CacheStats, BackupInfo, RateLimitInfo, NotificationMessage
)
from api.graphql.subscription_manager import subscription_manager, SubscriptionEvent
from services.transcription_service import transcription_service
from services.transcription_service_cached import CachedTranscriptionService
from services.backup_service import backup_service
from services.automated_backup_scheduler import automated_backup_scheduler
from services.rate_limiting_service import rate_limiting_service, RateLimitScope
from api.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class UserResolver:
    """Resolvers for user-related queries and mutations"""
    
    @staticmethod
    async def get_user(user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            db = next(get_db())
            user_model = db.query(UserModel).filter(UserModel.id == user_id).first()
            
            if not user_model:
                return None
            
            return User(
                id=user_model.id,
                username=user_model.username,
                email=user_model.email,
                full_name=user_model.full_name,
                role=user_model.role,
                is_active=user_model.is_active,
                created_at=user_model.created_at,
                updated_at=user_model.updated_at,
                last_login=user_model.last_login,
                subscription_tier=getattr(user_model, 'subscription_tier', None)
            )
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    @staticmethod
    async def get_users(limit: int = 50, offset: int = 0) -> List[User]:
        """Get list of users"""
        try:
            db = next(get_db())
            user_models = db.query(UserModel).offset(offset).limit(limit).all()
            
            users = []
            for user_model in user_models:
                users.append(User(
                    id=user_model.id,
                    username=user_model.username,
                    email=user_model.email,
                    full_name=user_model.full_name,
                    role=user_model.role,
                    is_active=user_model.is_active,
                    created_at=user_model.created_at,
                    updated_at=user_model.updated_at,
                    last_login=user_model.last_login,
                    subscription_tier=getattr(user_model, 'subscription_tier', None)
                ))
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    @staticmethod
    async def get_current_user(context) -> Optional[User]:
        """Get current authenticated user from context"""
        try:
            # Extract user from GraphQL context (set by auth middleware)
            if hasattr(context, 'user') and context.user:
                return await UserResolver.get_user(context.user.id)
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None


class TranscriptResolver:
    """Resolvers for transcript-related queries and mutations"""
    
    @staticmethod
    async def get_transcript(transcript_id: str) -> Optional[Transcript]:
        """Get transcript by ID"""
        try:
            db = next(get_db())
            transcript_model = db.query(TranscriptModel).filter(
                TranscriptModel.id == transcript_id
            ).first()
            
            if not transcript_model:
                return None
            
            # Convert segments from JSON if available
            segments = []
            if hasattr(transcript_model, 'segments') and transcript_model.segments:
                # Parse segments JSON and convert to GraphQL types
                import json
                segment_data = json.loads(transcript_model.segments)
                # Implementation would convert to TranscriptSegment objects
                segments = []  # Placeholder
            
            return Transcript(
                id=transcript_model.id,
                user_id=transcript_model.user_id,
                title=transcript_model.title,
                content=transcript_model.content,
                language=transcript_model.language,
                duration=transcript_model.duration,
                segments=segments,
                file_url=getattr(transcript_model, 'file_url', None),
                file_size=getattr(transcript_model, 'file_size', None),
                created_at=transcript_model.created_at,
                updated_at=transcript_model.updated_at,
                tags=getattr(transcript_model, 'tags', []) or []
            )
            
        except Exception as e:
            logger.error(f"Error getting transcript {transcript_id}: {e}")
            return None
    
    @staticmethod
    async def get_transcripts(
        user_id: Optional[int] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Transcript]:
        """Get list of transcripts"""
        try:
            db = next(get_db())
            query = db.query(TranscriptModel)
            
            if user_id:
                query = query.filter(TranscriptModel.user_id == user_id)
            
            transcript_models = query.offset(offset).limit(limit).all()
            
            transcripts = []
            for model in transcript_models:
                transcript = await TranscriptResolver.get_transcript(model.id)
                if transcript:
                    transcripts.append(transcript)
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error getting transcripts: {e}")
            return []
    
    @staticmethod
    async def search_transcripts(query: str, limit: int = 20) -> List[Transcript]:
        """Search transcripts by content"""
        try:
            db = next(get_db())
            # Simple text search - in production would use full-text search
            transcript_models = db.query(TranscriptModel).filter(
                TranscriptModel.content.ilike(f"%{query}%")
            ).limit(limit).all()
            
            transcripts = []
            for model in transcript_models:
                transcript = await TranscriptResolver.get_transcript(model.id)
                if transcript:
                    transcripts.append(transcript)
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    @staticmethod
    async def update_transcript(
        transcript_id: str, 
        content: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[Transcript]:
        """Update transcript"""
        try:
            db = next(get_db())
            transcript_model = db.query(TranscriptModel).filter(
                TranscriptModel.id == transcript_id
            ).first()
            
            if not transcript_model:
                return None
            
            # Update fields
            if content is not None:
                transcript_model.content = content
            if title is not None:
                transcript_model.title = title
                
            transcript_model.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Publish update event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="transcript_updated",
                data={
                    "id": transcript_id,
                    "user_id": transcript_model.user_id,
                    "title": title,
                    "updated_at": transcript_model.updated_at.isoformat()
                },
                user_id=transcript_model.user_id
            ))
            
            return await TranscriptResolver.get_transcript(transcript_id)
            
        except Exception as e:
            logger.error(f"Error updating transcript {transcript_id}: {e}")
            db.rollback()
            return None
    
    @staticmethod
    async def delete_transcript(transcript_id: str) -> bool:
        """Delete transcript"""
        try:
            db = next(get_db())
            transcript_model = db.query(TranscriptModel).filter(
                TranscriptModel.id == transcript_id
            ).first()
            
            if not transcript_model:
                return False
            
            user_id = transcript_model.user_id
            db.delete(transcript_model)
            db.commit()
            
            # Publish deletion event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="transcript_deleted",
                data={
                    "id": transcript_id,
                    "user_id": user_id
                },
                user_id=user_id
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting transcript {transcript_id}: {e}")
            db.rollback()
            return False


class TranscriptionJobResolver:
    """Resolvers for transcription job queries and mutations"""
    
    @staticmethod
    async def get_job(job_id: str) -> Optional[TranscriptionJob]:
        """Get transcription job by ID"""
        # Implementation would query job from database or cache
        # For now, return placeholder
        return TranscriptionJob(
            id=job_id,
            user_id=1,
            status="processing",
            progress=45.0,
            file_url="https://example.com/audio.mp3",
            created_at=datetime.utcnow()
        )
    
    @staticmethod
    async def get_jobs(
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[TranscriptionJob]:
        """Get list of transcription jobs"""
        # Implementation would query jobs from database
        # For now, return empty list
        return []
    
    @staticmethod
    async def start_transcription(
        context, 
        file_url: str, 
        language: Optional[str] = None
    ) -> TranscriptionJob:
        """Start a new transcription job"""
        try:
            # Create job (implementation would use actual transcription service)
            job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            user_id = context.user.id if hasattr(context, 'user') else None
            
            job = TranscriptionJob(
                id=job_id,
                user_id=user_id or 1,
                status="pending",
                progress=0.0,
                file_url=file_url,
                language=language,
                created_at=datetime.utcnow()
            )
            
            # Publish job created event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="transcription_job",
                data={
                    "id": job_id,
                    "user_id": user_id or 1,
                    "status": "pending",
                    "progress": 0,
                    "file_url": file_url,
                    "language": language,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                user_id=user_id
            ))
            
            return job
            
        except Exception as e:
            logger.error(f"Error starting transcription: {e}")
            raise
    
    @staticmethod
    async def cancel_transcription(job_id: str) -> TranscriptionJob:
        """Cancel a transcription job"""
        try:
            # Implementation would cancel actual job
            job = TranscriptionJob(
                id=job_id,
                user_id=1,
                status="cancelled",
                progress=0.0,
                file_url="placeholder",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Publish job cancelled event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="transcription_job",
                data={
                    "id": job_id,
                    "status": "cancelled",
                    "updated_at": datetime.utcnow().isoformat()
                }
            ))
            
            return job
            
        except Exception as e:
            logger.error(f"Error cancelling transcription {job_id}: {e}")
            raise


class SystemResolver:
    """Resolvers for system-related queries and mutations"""
    
    @staticmethod
    async def get_system_metrics() -> SystemMetrics:
        """Get current system metrics"""
        try:
            # Implementation would get real metrics
            # For now, return placeholder
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_usage=45.2,
                memory_usage=68.7,
                disk_usage=32.1,
                active_connections=127,
                request_rate=89.5,
                error_rate=0.02,
                cache_hit_rate=0.85,
                uptime_seconds=3600 * 24 * 7  # 1 week
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            raise
    
    @staticmethod
    async def get_cache_stats() -> CacheStats:
        """Get cache statistics"""
        try:
            if redis_cache.is_connected():
                # Get actual Redis stats
                db = next(get_db())
                from services.transcription_service_cached import CachedTranscriptionService
                cached_service = CachedTranscriptionService(db)
                stats = cached_service.get_cache_stats()
                
                return CacheStats(
                    connected=stats["connected"],
                    uptime_seconds=stats["uptime_seconds"],
                    memory_used=stats["memory"]["used_bytes"],
                    memory_peak=stats["memory"]["peak_bytes"],
                    hit_rate=stats["stats"]["hit_rate"],
                    total_requests=stats["stats"]["total_requests"],
                    hits=stats["stats"]["hits"],
                    misses=stats["stats"]["misses"],
                    total_keys=stats["keyspace"]["total_keys"]
                )
            else:
                # Return disconnected state
                return CacheStats(
                    connected=False,
                    uptime_seconds=0,
                    memory_used=0,
                    memory_peak=0,
                    hit_rate=0.0,
                    total_requests=0,
                    hits=0,
                    misses=0,
                    total_keys=0
                )
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            raise
    
    @staticmethod
    async def get_backup_info(backup_id: Optional[str] = None) -> List[BackupInfo]:
        """Get backup information"""
        try:
            backups = backup_service.list_backups()
            
            backup_infos = []
            for backup in backups:
                if backup_id and backup["backup_id"] != backup_id:
                    continue
                
                backup_infos.append(BackupInfo(
                    backup_id=backup["backup_id"],
                    status="completed",  # Assume completed for listed backups
                    progress=100.0,
                    size=backup.get("size"),
                    components=backup.get("components", []),
                    created_at=datetime.fromisoformat(backup["created_at"]),
                    location=backup.get("location")
                ))
            
            return backup_infos
            
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return []
    
    @staticmethod
    async def get_rate_limit_info(identifier: str, scope: str) -> RateLimitInfo:
        """Get rate limiting information"""
        try:
            scope_enum = RateLimitScope(scope)
            info = await rate_limiting_service.get_rate_limit_info(identifier, scope_enum)
            
            return RateLimitInfo(
                identifier=identifier,
                scope=scope,
                current_usage=info.get("current_tokens", 0),
                limit=info.get("capacity", 0),
                remaining=info.get("current_tokens", 0),
                reset_time=datetime.utcnow(),  # Placeholder
                algorithm=info.get("algorithm"),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            raise
    
    @staticmethod
    async def create_backup(backup_type: str = "manual") -> BackupInfo:
        """Create a system backup"""
        try:
            # Create backup using automated scheduler for comprehensive backup
            backup_result = await automated_backup_scheduler.create_comprehensive_backup(backup_type)
            
            backup_info = BackupInfo(
                backup_id=backup_result["backup_id"],
                status=backup_result["status"],
                progress=100.0 if backup_result["status"] == "completed" else 0.0,
                size=backup_result.get("total_size"),
                components=list(backup_result.get("components", {}).keys()),
                created_at=datetime.fromisoformat(backup_result["start_time"])
            )
            
            # Publish backup event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="backup_info",
                data={
                    "backup_id": backup_info.backup_id,
                    "status": backup_info.status,
                    "progress": backup_info.progress,
                    "created_at": backup_info.created_at.isoformat()
                }
            ))
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    @staticmethod
    async def invalidate_cache(cache_keys: Optional[List[str]] = None) -> bool:
        """Invalidate cache entries"""
        try:
            if redis_cache.is_connected():
                if cache_keys:
                    # Invalidate specific keys
                    for key in cache_keys:
                        await redis_cache.delete(key)
                else:
                    # Clear all cache
                    await redis_cache.clear_all()
                
                # Publish cache update event
                await subscription_manager.publish_event(SubscriptionEvent(
                    event_type="cache_invalidated",
                    data={
                        "keys": cache_keys or ["all"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ))
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    @staticmethod
    async def reset_rate_limit(identifier: str, scope: str) -> bool:
        """Reset rate limiting for identifier"""
        try:
            scope_enum = RateLimitScope(scope)
            await rate_limiting_service.reset_rate_limit(identifier, scope_enum)
            
            # Publish rate limit reset event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="rate_limit_reset",
                data={
                    "identifier": identifier,
                    "scope": scope,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False


class NotificationResolver:
    """Resolvers for notification-related operations"""
    
    @staticmethod
    async def send_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        priority: str = "medium"
    ) -> NotificationMessage:
        """Send notification to user"""
        try:
            notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            notification = NotificationMessage(
                id=notification_id,
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                priority=priority,
                read=False,
                created_at=datetime.utcnow()
            )
            
            # Publish notification event
            await subscription_manager.publish_event(SubscriptionEvent(
                event_type="notification",
                data={
                    "id": notification_id,
                    "user_id": user_id,
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "priority": priority,
                    "read": False,
                    "created_at": datetime.utcnow().isoformat()
                },
                user_id=user_id
            ))
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            raise