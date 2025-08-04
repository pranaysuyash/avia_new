"""
Notification API wrapper for easy integration
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from database.models import User
from database_config import get_db

# Global notification manager instance
notification_manager = EnhancedNotificationManager()

async def notify_processing_complete(
    user_id: str,
    file_name: str,
    transcript_id: str,
    duration: int,
    language: str = "Unknown",
    speaker_count: int = 0,
    processing_time: float = 0.0,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Dict[str, Any]:
    """
    Send notification when audio/video processing is complete
    
    Args:
        user_id: User ID to notify
        file_name: Name of the processed file
        transcript_id: ID of the generated transcript
        duration: Duration of the audio/video in seconds
        language: Detected language
        speaker_count: Number of speakers detected
        processing_time: Time taken to process in seconds
        priority: Notification priority
    
    Returns:
        Dict with results for each channel
    """
    # Get user details
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    user_name = user.full_name if user else "User"
    db.close()
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.PROCESSING_COMPLETE,
        priority=priority,
        data={
            "user_name": user_name,
            "file_name": file_name,
            "duration": duration,
            "language": language,
            "speaker_count": speaker_count,
            "processing_time": processing_time,
            "transcript_url": f"/transcript/{transcript_id}",
            "transcript_id": transcript_id,
            "timestamp": datetime.utcnow().isoformat(),
            "download_url": f"/api/download/{transcript_id}",
            "short_url": f"/t/{transcript_id}"  # Short URL for SMS
        }
    )
    
    return await notification_manager.send_notification(request)

async def notify_processing_failed(
    user_id: str,
    file_name: str,
    error_message: str,
    priority: NotificationPriority = NotificationPriority.HIGH
) -> Dict[str, Any]:
    """
    Send notification when processing fails
    
    Args:
        user_id: User ID to notify
        file_name: Name of the file that failed
        error_message: Error details
        priority: Notification priority
    
    Returns:
        Dict with results for each channel
    """
    # Get user details
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    user_name = user.full_name if user else "User"
    db.close()
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.PROCESSING_FAILED,
        priority=priority,
        data={
            "user_name": user_name,
            "file_name": file_name,
            "error_message": error_message,
            "support_url": "/support",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return await notification_manager.send_notification(request)

async def notify_usage_limit_warning(
    user_id: str,
    usage_percentage: float,
    current_usage: float,
    limit: float,
    unit: str = "minutes",
    priority: NotificationPriority = NotificationPriority.HIGH
) -> Dict[str, Any]:
    """
    Send notification about approaching usage limits
    
    Args:
        user_id: User ID to notify
        usage_percentage: Current usage as percentage of limit
        current_usage: Current usage amount
        limit: Usage limit
        unit: Unit of measurement (minutes, files, etc.)
        priority: Notification priority
    
    Returns:
        Dict with results for each channel
    """
    # Get user details
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    user_name = user.full_name if user else "User"
    db.close()
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.USAGE_LIMIT_WARNING,
        priority=priority,
        data={
            "user_name": user_name,
            "usage_percentage": int(usage_percentage),
            "current_usage": int(current_usage),
            "limit": int(limit),
            "unit": unit,
            "upgrade_url": "/pricing",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return await notification_manager.send_notification(request)

async def notify_batch_complete(
    user_id: str,
    total_files: int,
    successful_files: int,
    failed_files: int,
    batch_id: str,
    total_duration: str = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Dict[str, Any]:
    """
    Send notification when batch processing is complete
    
    Args:
        user_id: User ID to notify
        total_files: Total number of files in batch
        successful_files: Number of successfully processed files
        failed_files: Number of failed files
        batch_id: Batch identifier
        total_duration: Human-readable duration (e.g., "2 hours 15 minutes")
        priority: Notification priority
    
    Returns:
        Dict with results for each channel
    """
    # Get user details
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    user_name = user.full_name if user else "User"
    db.close()
    
    # Calculate duration if not provided
    if not total_duration:
        total_duration = "Unknown"
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.BATCH_COMPLETE,
        priority=priority,
        data={
            "user_name": user_name,
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_duration": total_duration,
            "batch_results_url": f"/batch/results/{batch_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return await notification_manager.send_notification(request)

async def notify_system_update(
    user_id: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.LOW,
    channels: Optional[List[NotificationChannel]] = None
) -> Dict[str, Any]:
    """
    Send system update notification
    
    Args:
        user_id: User ID to notify
        message: Update message
        priority: Notification priority
        channels: Specific channels to use (default: in-app only)
    
    Returns:
        Dict with results for each channel
    """
    if channels is None:
        channels = [NotificationChannel.IN_APP]
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.SYSTEM_UPDATE,
        priority=priority,
        channels=channels,
        data={
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return await notification_manager.send_notification(request)

async def notify_transcript_ready(
    user_id: str,
    transcript_id: str,
    file_name: str,
    export_formats: List[str] = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Dict[str, Any]:
    """
    Send notification when transcript is ready for download
    
    Args:
        user_id: User ID to notify
        transcript_id: Transcript identifier
        file_name: Original file name
        export_formats: Available export formats
        priority: Notification priority
    
    Returns:
        Dict with results for each channel
    """
    if export_formats is None:
        export_formats = ["TXT", "PDF", "DOCX", "SRT"]
    
    # Get user details
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    user_name = user.full_name if user else "User"
    db.close()
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.TRANSCRIPT_READY,
        priority=priority,
        data={
            "user_name": user_name,
            "transcript_id": transcript_id,
            "file_name": file_name,
            "export_formats": ", ".join(export_formats),
            "transcript_url": f"/transcript/{transcript_id}",
            "download_url": f"/api/download/{transcript_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return await notification_manager.send_notification(request)

async def notify_export_ready(
    user_id: str,
    export_id: str,
    file_name: str,
    export_format: str,
    file_size: int = 0,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Dict[str, Any]:
    """
    Send notification when export is ready for download
    
    Args:
        user_id: User ID to notify
        export_id: Export identifier
        file_name: Exported file name
        export_format: Format of the export
        file_size: Size of the export file in bytes
        priority: Notification priority
    
    Returns:
        Dict with results for each channel
    """
    # Get user details
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    user_name = user.full_name if user else "User"
    db.close()
    
    # Format file size
    if file_size > 0:
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
    else:
        size_str = "Unknown size"
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.EXPORT_READY,
        priority=priority,
        data={
            "user_name": user_name,
            "export_id": export_id,
            "file_name": file_name,
            "export_format": export_format,
            "file_size": size_str,
            "download_url": f"/api/export/download/{export_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return await notification_manager.send_notification(request)

# Convenience functions for specific channels

async def send_email(
    user_id: str,
    notification_type: NotificationType,
    data: Dict[str, Any],
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Dict[str, Any]:
    """Send email notification only"""
    request = NotificationRequest(
        user_id=str(user_id),
        type=notification_type,
        priority=priority,
        channels=[NotificationChannel.EMAIL],
        data=data
    )
    return await notification_manager.send_notification(request)

async def send_sms(
    user_id: str,
    notification_type: NotificationType,
    data: Dict[str, Any],
    priority: NotificationPriority = NotificationPriority.HIGH
) -> Dict[str, Any]:
    """Send SMS notification only"""
    request = NotificationRequest(
        user_id=str(user_id),
        type=notification_type,
        priority=priority,
        channels=[NotificationChannel.SMS],
        data=data
    )
    return await notification_manager.send_notification(request)

async def send_in_app(
    user_id: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM
) -> Dict[str, Any]:
    """Send simple in-app notification"""
    data = {
        "title": title,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if action_url:
        data["action_url"] = action_url
    
    request = NotificationRequest(
        user_id=str(user_id),
        type=NotificationType.SYSTEM_UPDATE,  # Generic type for custom messages
        priority=priority,
        channels=[NotificationChannel.IN_APP],
        data=data
    )
    return await notification_manager.send_notification(request)

# Utility functions

async def get_user_notifications(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user's in-app notifications"""
    return await notification_manager.get_user_notifications(str(user_id), limit=limit)

async def mark_notification_read(user_id: str, notification_id: str) -> bool:
    """Mark a notification as read"""
    return await notification_manager.mark_notification_read(str(user_id), notification_id)

async def update_user_preferences(user_id: str, preferences: Dict[NotificationChannel, bool]) -> bool:
    """Update user's notification preferences"""
    return await notification_manager.update_user_preferences(str(user_id), preferences)

# Synchronous wrappers for easier integration

def notify_processing_complete_sync(*args, **kwargs):
    """Synchronous wrapper for notify_processing_complete"""
    return asyncio.run(notify_processing_complete(*args, **kwargs))

def notify_processing_failed_sync(*args, **kwargs):
    """Synchronous wrapper for notify_processing_failed"""
    return asyncio.run(notify_processing_failed(*args, **kwargs))

def notify_batch_complete_sync(*args, **kwargs):
    """Synchronous wrapper for notify_batch_complete"""
    return asyncio.run(notify_batch_complete(*args, **kwargs))

def send_in_app_sync(*args, **kwargs):
    """Synchronous wrapper for send_in_app"""
    return asyncio.run(send_in_app(*args, **kwargs))