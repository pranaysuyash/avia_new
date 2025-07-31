"""
Event handlers for WebSocket events
"""

import logging
from typing import Dict, Any

from .events import Event, EventType, EventHandler
from database import get_db_session, Transcript, User, Notification

logger = logging.getLogger(__name__)


class TranscriptEventHandler(EventHandler):
    """Handle transcript-related events"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle transcript events"""
        data = event.data
        transcript_id = data.get("transcript_id")
        
        if not transcript_id:
            logger.error("Transcript ID missing in event")
            return
        
        # Get transcript to find team/collaborators
        db = next(get_db_session())
        transcript = db.query(Transcript).filter_by(id=transcript_id).first()
        
        if not transcript:
            logger.error(f"Transcript {transcript_id} not found")
            return
        
        # Determine who should receive the update
        target_users = set()
        
        # Add transcript owner
        target_users.add(transcript.user_id)
        
        # Add team members if transcript belongs to a team
        if transcript.team_id:
            team_members = db.query(User).join(User.team_memberships).filter_by(
                team_id=transcript.team_id
            ).all()
            target_users.update([member.id for member in team_members])
        
        # Add users with share access
        for share in transcript.shares:
            if share.shared_with_id:
                target_users.add(share.shared_with_id)
        
        # Remove the user who made the change
        target_users.discard(user_id)
        
        # Broadcast to relevant users
        await connection_manager.broadcast_to_users(event, list(target_users))
        
        logger.info(f"Broadcasted transcript update for {transcript_id} to {len(target_users)} users")


class NotificationEventHandler(EventHandler):
    """Handle notification events"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle notification events"""
        data = event.data
        target_user_id = data.get("user_id", user_id)
        
        # Send notification to specific user
        await connection_manager.send_personal_message(event, target_user_id)
        
        logger.info(f"Sent notification to user {target_user_id}")


class CollaborationEventHandler(EventHandler):
    """Handle collaboration events like annotations"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle collaboration events"""
        data = event.data
        transcript_id = data.get("transcript_id")
        
        if not transcript_id:
            logger.error("Transcript ID missing in collaboration event")
            return
        
        # Create room ID for transcript collaboration
        room_id = f"transcript_{transcript_id}"
        
        # Broadcast to all users in the transcript room
        await connection_manager.broadcast_to_room(
            event,
            room_id,
            exclude_user=user_id
        )
        
        # Also handle typing indicators
        if event.type == EventType.USER_TYPING:
            # Set a timeout to clear typing indicator
            import asyncio
            await asyncio.sleep(3)
            
            stop_typing_event = Event(
                type=EventType.USER_STOPPED_TYPING,
                data={"user_id": user_id, "transcript_id": transcript_id},
                user_id=user_id
            )
            
            await connection_manager.broadcast_to_room(
                stop_typing_event,
                room_id,
                exclude_user=user_id
            )


class ProcessingEventHandler(EventHandler):
    """Handle processing progress events"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle processing events"""
        data = event.data
        job_id = data.get("job_id")
        
        if not job_id:
            logger.error("Job ID missing in processing event")
            return
        
        # For processing events, we typically want to send to the user who initiated
        # In a real implementation, we'd look up the job owner
        target_user_id = data.get("user_id", user_id)
        
        # Send progress update to job owner
        await connection_manager.send_personal_message(event, target_user_id)
        
        # If processing completed, might trigger additional events
        if event.type == EventType.PROCESSING_COMPLETED:
            # Could trigger notification
            notification_event = Event(
                type=EventType.NOTIFICATION_NEW,
                data={
                    "title": "Processing Complete",
                    "message": f"Your transcription job {job_id} has completed",
                    "type": "success",
                    "action_url": f"/transcript/{data.get('transcript_id')}"
                },
                user_id=target_user_id
            )
            
            await connection_manager.send_personal_message(notification_event, target_user_id)


class TeamEventHandler(EventHandler):
    """Handle team-related events"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle team events"""
        data = event.data
        team_id = data.get("team_id")
        
        if not team_id:
            logger.error("Team ID missing in team event")
            return
        
        # Get team members
        db = next(get_db_session())
        team_members = db.query(User).join(User.team_memberships).filter_by(
            team_id=team_id
        ).all()
        
        target_users = [member.id for member in team_members if member.id != user_id]
        
        # Broadcast to team members
        await connection_manager.broadcast_to_users(event, target_users)
        
        logger.info(f"Broadcasted team event for team {team_id} to {len(target_users)} users")


class SystemEventHandler(EventHandler):
    """Handle system-wide events"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle system events"""
        # System events typically go to all users
        if event.type == EventType.SYSTEM_ANNOUNCEMENT:
            await connection_manager.broadcast_all(event)
        
        elif event.type == EventType.SYSTEM_MAINTENANCE:
            # Could target specific users or all
            await connection_manager.broadcast_all(event)
        
        logger.info(f"Broadcasted system event: {event.type.value}")