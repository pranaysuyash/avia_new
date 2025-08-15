"""
Enhanced GraphQL Schema with Medical Transcription Support
Comprehensive API schema including medical data, analytics, and real-time subscriptions
"""

import strawberry
from typing import List, Optional, AsyncGenerator
from datetime import datetime
import asyncio

# Import existing types
from api.graphql.types import (
    User, Transcript, TranscriptionJob, CacheStats, BackupInfo,
    RateLimitInfo, SystemMetrics, NotificationMessage
)
from api.graphql.resolvers import (
    UserResolver, TranscriptResolver, TranscriptionJobResolver,
    SystemResolver, NotificationResolver
)

# Import medical types and resolvers
from api.graphql.medical_types import (
    MedicalTranscript, MedicalTranscriptionJob, MedicalSearchResult,
    MedicalAnalytics, MedicalTranscriptionInput, MedicalSearchInput,
    MedicalAnalyticsInput, HIPAAComplianceLevel, MedicalEntityType,
    ProcessingStatus, CareQualityStatus, RecommendationPriority
)
from api.graphql.medical_resolvers import MedicalTranscriptResolver, MedicalJobResolver

# Import subscription manager
from api.graphql.subscription_manager import subscription_manager


@strawberry.enum
class SubscriptionType:
    TRANSCRIPTION_STATUS = "transcription_status"
    MEDICAL_TRANSCRIPTION_STATUS = "medical_transcription_status"
    SYSTEM_METRICS = "system_metrics"
    USER_NOTIFICATIONS = "user_notifications"
    CACHE_UPDATES = "cache_updates"
    BACKUP_STATUS = "backup_status"
    RATE_LIMIT_ALERTS = "rate_limit_alerts"
    MEDICAL_ANALYTICS = "medical_analytics"
    HIPAA_ALERTS = "hipaa_alerts"


@strawberry.type
class Query:
    """Enhanced GraphQL Query root with medical support"""
    
    # ==================
    # User Queries
    # ==================
    
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
    
    # ==================
    # Standard Transcript Queries
    # ==================
    
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
    
    # ==================
    # Medical Transcript Queries
    # ==================
    
    @strawberry.field
    async def medical_transcript(self, info, transcript_id: str) -> Optional[MedicalTranscript]:
        """Get medical transcript with comprehensive analysis"""
        return await MedicalTranscriptResolver.get_medical_transcript(transcript_id, info.context)
    
    @strawberry.field
    async def medical_transcripts(
        self,
        info,
        user_id: Optional[int] = None,
        patient_ids: Optional[List[str]] = None,
        provider_ids: Optional[List[str]] = None,
        compliance_level: Optional[HIPAAComplianceLevel] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MedicalTranscript]:
        """Get list of medical transcripts with filtering"""
        return await MedicalTranscriptResolver.get_medical_transcripts(
            user_id, patient_ids, provider_ids, compliance_level, limit, offset
        )
    
    @strawberry.field
    async def search_medical_transcripts(
        self,
        info,
        search_input: MedicalSearchInput
    ) -> List[MedicalSearchResult]:
        """Advanced search for medical transcripts"""
        return await MedicalTranscriptResolver.search_medical_transcripts(search_input)
    
    @strawberry.field
    async def medical_analytics(
        self,
        info,
        analytics_input: Optional[MedicalAnalyticsInput] = None
    ) -> MedicalAnalytics:
        """Get comprehensive medical analytics"""
        if not analytics_input:
            analytics_input = MedicalAnalyticsInput()
        return await MedicalTranscriptResolver.get_medical_analytics(analytics_input)
    
    # ==================
    # Job Queries
    # ==================
    
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
    
    @strawberry.field
    async def medical_transcription_job(self, info, job_id: str) -> Optional[MedicalTranscriptionJob]:
        """Get medical transcription job by ID"""
        return await MedicalJobResolver.get_medical_job(job_id)
    
    @strawberry.field
    async def medical_transcription_jobs(
        self,
        info,
        user_id: Optional[int] = None,
        status: Optional[ProcessingStatus] = None,
        limit: int = 50
    ) -> List[MedicalTranscriptionJob]:
        """Get list of medical transcription jobs"""
        return await MedicalJobResolver.get_medical_jobs(user_id, status, limit)
    
    # ==================
    # System Queries
    # ==================
    
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
    """Enhanced GraphQL Mutation root with medical support"""
    
    # ==================
    # Standard Transcription Mutations
    # ==================
    
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
    
    # ==================
    # Medical Transcription Mutations
    # ==================
    
    @strawberry.mutation
    async def start_medical_transcription(
        self,
        info,
        transcription_input: MedicalTranscriptionInput
    ) -> MedicalTranscriptionJob:
        """Start a new medical transcription job with comprehensive analysis"""
        user_id = info.context.get("user_id")  # Get from auth context
        return await MedicalTranscriptResolver.create_medical_transcription(
            transcription_input, user_id
        )
    
    @strawberry.mutation
    async def update_medical_transcript(
        self,
        info,
        transcript_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        patient_id: Optional[str] = None,
        provider_id: Optional[str] = None
    ) -> Optional[MedicalTranscript]:
        """Update medical transcript"""
        return await MedicalTranscriptResolver.update_medical_transcript(
            transcript_id, content, title, patient_id, provider_id
        )
    
    @strawberry.mutation
    async def delete_medical_transcript(self, info, transcript_id: str) -> bool:
        """Delete a medical transcript"""
        return await MedicalTranscriptResolver.delete_medical_transcript(transcript_id)
    
    @strawberry.mutation
    async def cancel_medical_transcription(self, info, job_id: str) -> Optional[MedicalTranscriptionJob]:
        """Cancel a medical transcription job"""
        return await MedicalJobResolver.cancel_medical_job(job_id)
    
    # ==================
    # System Mutations
    # ==================
    
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
    """Enhanced GraphQL Subscription root with medical support"""
    
    # ==================
    # Standard Transcription Subscriptions
    # ==================
    
    @strawberry.subscription
    async def transcription_status(
        self, 
        info, 
        job_ids: Optional[List[str]] = None,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[TranscriptionJob, None]:
        """Subscribe to transcription job status updates"""
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
    
    # ==================
    # Medical Transcription Subscriptions
    # ==================
    
    @strawberry.subscription
    async def medical_transcription_status(
        self,
        info,
        job_ids: Optional[List[str]] = None,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[MedicalTranscriptionJob, None]:
        """Subscribe to medical transcription job status updates"""
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.MEDICAL_TRANSCRIPTION_STATUS,
            user_id=user_id,
            filters={"job_ids": job_ids} if job_ids else None
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "medical_transcription_job":
                    job_data = update.get("data")
                    if job_data:
                        yield MedicalTranscriptionJob(
                            id=job_data["id"],
                            user_id=job_data["user_id"],
                            transcript_id=job_data.get("transcript_id"),
                            status=ProcessingStatus(job_data["status"]),
                            progress=job_data.get("progress", 0),
                            file_url=job_data["file_url"],
                            language=job_data.get("language"),
                            compliance_level=HIPAAComplianceLevel(job_data.get("compliance_level", "standard")),
                            created_at=job_data["created_at"],
                            updated_at=job_data["updated_at"],
                            started_at=job_data.get("started_at"),
                            completed_at=job_data.get("completed_at"),
                            error_message=job_data.get("error_message")
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    @strawberry.subscription
    async def medical_analytics_updates(
        self,
        info,
        update_interval: int = 300  # 5 minutes
    ) -> AsyncGenerator[MedicalAnalytics, None]:
        """Subscribe to medical analytics updates"""
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.MEDICAL_ANALYTICS,
            user_id=None,  # System-wide analytics
            filters={"interval": update_interval}
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "medical_analytics":
                    analytics_data = update.get("data")
                    if analytics_data:
                        yield MedicalAnalytics(
                            total_transcripts=analytics_data["total_transcripts"],
                            total_patients=analytics_data["total_patients"],
                            total_providers=analytics_data["total_providers"],
                            average_engagement_score=analytics_data["average_engagement_score"],
                            common_diagnoses=analytics_data["common_diagnoses"],
                            common_medications=analytics_data["common_medications"],
                            common_procedures=analytics_data["common_procedures"],
                            phi_detection_rate=analytics_data["phi_detection_rate"],
                            compliance_rate=analytics_data["compliance_rate"],
                            quality_indicators=analytics_data.get("quality_indicators", [])
                        )
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    @strawberry.subscription
    async def hipaa_compliance_alerts(
        self,
        info,
        severity_threshold: str = "medium"
    ) -> AsyncGenerator[str, None]:
        """Subscribe to HIPAA compliance alerts"""
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.HIPAA_ALERTS,
            user_id=None,
            filters={"severity_threshold": severity_threshold}
        )
        
        try:
            async for update in subscription_manager.get_updates(subscription_id):
                if update.get("type") == "hipaa_alert":
                    alert_data = update.get("data")
                    if alert_data:
                        yield f"HIPAA Alert: {alert_data['message']} (Severity: {alert_data['severity']})"
        finally:
            await subscription_manager.unsubscribe(subscription_id)
    
    # ==================
    # System Subscriptions
    # ==================
    
    @strawberry.subscription
    async def system_metrics(
        self, 
        info, 
        interval_seconds: int = 30
    ) -> AsyncGenerator[SystemMetrics, None]:
        """Subscribe to system metrics updates"""
        subscription_id = await subscription_manager.subscribe(
            subscription_type=SubscriptionType.SYSTEM_METRICS,
            user_id=None,
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


# Create the enhanced GraphQL schema
enhanced_schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)