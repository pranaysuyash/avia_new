"""
WebSocket integration with application features
"""

from typing import Optional, Dict, Any
import logging

from websocket.server import websocket_manager
from websocket.events import (
    Event, EventType,
    TranscriptUpdatedEvent,
    AnnotationAddedEvent,
    ProcessingProgressEvent,
    NotificationEvent
)

logger = logging.getLogger(__name__)


class WebSocketIntegration:
    """Integration layer for WebSocket events with application features"""
    
    @staticmethod
    async def notify_transcript_update(
        transcript_id: int,
        user_id: int,
        changes: Dict[str, Any]
    ):
        """Notify about transcript updates"""
        event = TranscriptUpdatedEvent(
            transcript_id=transcript_id,
            user_id=user_id,
            changes=changes
        )
        
        # Broadcast through WebSocket manager
        await websocket_manager.broadcast_event(
            event,
            target={"room_id": f"transcript_{transcript_id}", "exclude_user": user_id}
        )
    
    @staticmethod
    async def notify_annotation_added(
        transcript_id: int,
        annotation_id: int,
        user_id: int,
        start_pos: int,
        end_pos: int,
        text: str,
        annotation_type: str
    ):
        """Notify about new annotation"""
        event = AnnotationAddedEvent(
            transcript_id=transcript_id,
            annotation_id=annotation_id,
            user_id=user_id,
            start_pos=start_pos,
            end_pos=end_pos,
            text=text,
            annotation_type=annotation_type
        )
        
        # Broadcast to transcript room
        await websocket_manager.broadcast_event(
            event,
            target={"room_id": f"transcript_{transcript_id}", "exclude_user": user_id}
        )
    
    @staticmethod
    async def notify_processing_progress(
        job_id: str,
        user_id: int,
        progress: int,
        status: str,
        message: str = ""
    ):
        """Notify about processing progress"""
        event = ProcessingProgressEvent(
            job_id=job_id,
            progress=progress,
            status=status,
            message=message
        )
        
        # Send to specific user
        await websocket_manager.broadcast_event(
            event,
            target={"user_id": user_id}
        )
    
    @staticmethod
    async def notify_new_notification(
        notification_id: int,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        action_url: Optional[str] = None
    ):
        """Send real-time notification"""
        event = NotificationEvent(
            notification_id=notification_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url
        )
        
        # Send to specific user
        await websocket_manager.broadcast_event(
            event,
            target={"user_id": user_id}
        )
    
    @staticmethod
    async def notify_team_update(
        team_id: int,
        event_type: EventType,
        data: Dict[str, Any]
    ):
        """Notify team members about updates"""
        event = Event(
            type=event_type,
            data={**data, "team_id": team_id}
        )
        
        # Broadcast to team room
        await websocket_manager.broadcast_event(
            event,
            target={"room_id": f"team_{team_id}"}
        )
    
    @staticmethod
    async def broadcast_system_announcement(
        title: str,
        message: str,
        severity: str = "info"
    ):
        """Broadcast system-wide announcement"""
        event = Event(
            type=EventType.SYSTEM_ANNOUNCEMENT,
            data={
                "title": title,
                "message": message,
                "severity": severity
            }
        )
        
        # Broadcast to all users
        await websocket_manager.broadcast_event(event)


# Usage Examples:

async def example_transcript_update():
    """Example: Notify when transcript is updated"""
    await WebSocketIntegration.notify_transcript_update(
        transcript_id=123,
        user_id=456,
        changes={
            "title": "Updated Title",
            "content": "Partial content update at position 100"
        }
    )


async def example_annotation():
    """Example: Notify when annotation is added"""
    await WebSocketIntegration.notify_annotation_added(
        transcript_id=123,
        annotation_id=789,
        user_id=456,
        start_pos=100,
        end_pos=150,
        text="Important note about this section",
        annotation_type="note"
    )


async def example_processing():
    """Example: Send processing progress updates"""
    job_id = "job_123"
    user_id = 456
    
    # Start
    await WebSocketIntegration.notify_processing_progress(
        job_id=job_id,
        user_id=user_id,
        progress=0,
        status="started",
        message="Processing started"
    )
    
    # Progress
    for progress in [25, 50, 75]:
        await WebSocketIntegration.notify_processing_progress(
            job_id=job_id,
            user_id=user_id,
            progress=progress,
            status="processing",
            message=f"Processing... {progress}%"
        )
    
    # Complete
    await WebSocketIntegration.notify_processing_progress(
        job_id=job_id,
        user_id=user_id,
        progress=100,
        status="completed",
        message="Processing completed successfully"
    )


async def example_notification():
    """Example: Send real-time notification"""
    await WebSocketIntegration.notify_new_notification(
        notification_id=999,
        user_id=456,
        title="Transcript Shared",
        message="John Doe shared 'Meeting Notes' with you",
        notification_type="info",
        action_url="/transcript/123"
    )


# Integration with existing features:

def integrate_with_transcripts():
    """How to integrate WebSocket with transcript operations"""
    
    # In transcripts.py or transcript routes:
    """
    @transcripts_router.put("/{transcript_id}")
    async def update_transcript(transcript_id: int, ...):
        # ... update logic ...
        
        # Notify via WebSocket
        await WebSocketIntegration.notify_transcript_update(
            transcript_id=transcript_id,
            user_id=current_user.id,
            changes={"title": new_title, "content": "updated"}
        )
        
        return updated_transcript
    """


def integrate_with_annotations():
    """How to integrate WebSocket with annotations"""
    
    # In annotation_manager.py:
    """
    def add_annotation(self, ...):
        # ... add annotation logic ...
        
        # Notify via WebSocket (in async context)
        asyncio.create_task(
            WebSocketIntegration.notify_annotation_added(
                transcript_id=transcript_id,
                annotation_id=annotation.id,
                user_id=user_id,
                start_pos=start_pos,
                end_pos=end_pos,
                text=text,
                annotation_type=annotation_type
            )
        )
        
        return annotation
    """


def integrate_with_processing():
    """How to integrate WebSocket with media processing"""
    
    # In media processing:
    """
    async def process_media_file(job_id: str, ...):
        # Notify start
        await WebSocketIntegration.notify_processing_progress(
            job_id=job_id,
            user_id=user_id,
            progress=0,
            status="started"
        )
        
        # ... processing logic with progress updates ...
        
        # Notify completion
        await WebSocketIntegration.notify_processing_progress(
            job_id=job_id,
            user_id=user_id,
            progress=100,
            status="completed"
        )
    """