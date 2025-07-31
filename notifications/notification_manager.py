"""
Notification manager for handling user notifications
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_, func
from database.models import Notification, User, Transcript, Annotation, SharedLink, Team, TeamRole
import re


class NotificationManager:
    """Manages user notifications"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        from_user_id: Optional[int] = None,
        link: Optional[str] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            from_user_id=from_user_id,
            link=link,
            related_id=related_id,
            related_type=related_type
        )
        
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        
        return notification
    
    def get_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: Optional[int] = None,
        notification_type: Optional[str] = None
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = self.session.query(Notification).options(
            joinedload(Notification.from_user)
        ).filter(
            Notification.user_id == user_id,
            Notification.is_archived == False
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        query = query.order_by(desc(Notification.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        return self.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_archived == False
        ).count()
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = self.session.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.session.commit()
            return True
        
        return False
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = self.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_archived == False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        self.session.commit()
        return count
    
    def archive_notification(self, notification_id: int, user_id: int) -> bool:
        """Archive a notification"""
        notification = self.session.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_archived = True
            self.session.commit()
            return True
        
        return False
    
    def delete_old_notifications(self, days: int = 30) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        count = self.session.query(Notification).filter(
            Notification.created_at < cutoff_date,
            Notification.is_read == True
        ).delete()
        
        self.session.commit()
        return count
    
    # Specific notification creators
    
    def notify_mention(
        self,
        mentioned_user_id: int,
        from_user_id: int,
        content: str,
        annotation_id: int,
        transcript_id: int
    ) -> Notification:
        """Create a mention notification"""
        from_user = self.session.query(User).filter_by(id=from_user_id).first()
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        
        return self.create_notification(
            user_id=mentioned_user_id,
            notification_type='mention',
            title=f"{from_user.username} mentioned you",
            message=f"You were mentioned in an annotation on '{transcript.title}': {content[:100]}...",
            from_user_id=from_user_id,
            link=f"/transcript/{transcript_id}#annotation_{annotation_id}",
            related_id=annotation_id,
            related_type='annotation'
        )
    
    def notify_annotation_reply(
        self,
        original_author_id: int,
        reply_author_id: int,
        reply_content: str,
        annotation_id: int,
        transcript_id: int
    ) -> Notification:
        """Create a reply notification"""
        reply_author = self.session.query(User).filter_by(id=reply_author_id).first()
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        
        return self.create_notification(
            user_id=original_author_id,
            notification_type='annotation_reply',
            title=f"{reply_author.username} replied to your annotation",
            message=f"New reply on '{transcript.title}': {reply_content[:100]}...",
            from_user_id=reply_author_id,
            link=f"/transcript/{transcript_id}#annotation_{annotation_id}",
            related_id=annotation_id,
            related_type='annotation'
        )
    
    def notify_transcript_edit(
        self,
        transcript_id: int,
        editor_id: int,
        change_summary: str,
        notify_users: List[int]
    ) -> List[Notification]:
        """Notify users about transcript edits"""
        editor = self.session.query(User).filter_by(id=editor_id).first()
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        
        notifications = []
        for user_id in notify_users:
            if user_id != editor_id:  # Don't notify the editor
                notification = self.create_notification(
                    user_id=user_id,
                    notification_type='transcript_edit',
                    title=f"{editor.username} edited '{transcript.title}'",
                    message=f"Changes: {change_summary}",
                    from_user_id=editor_id,
                    link=f"/transcript/{transcript_id}",
                    related_id=transcript_id,
                    related_type='transcript'
                )
                notifications.append(notification)
        
        return notifications
    
    def notify_share_access(
        self,
        shared_with_user_id: int,
        sharer_id: int,
        transcript_id: int,
        permission: str
    ) -> Notification:
        """Notify user about shared transcript"""
        sharer = self.session.query(User).filter_by(id=sharer_id).first()
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        
        return self.create_notification(
            user_id=shared_with_user_id,
            notification_type='share_access',
            title=f"{sharer.username} shared a transcript with you",
            message=f"You now have {permission} access to '{transcript.title}'",
            from_user_id=sharer_id,
            link=f"/transcript/{transcript_id}",
            related_id=transcript_id,
            related_type='transcript'
        )
    
    def notify_new_annotation(
        self,
        transcript_id: int,
        annotator_id: int,
        annotation_content: str,
        notify_users: List[int]
    ) -> List[Notification]:
        """Notify users about new annotations"""
        annotator = self.session.query(User).filter_by(id=annotator_id).first()
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        
        notifications = []
        for user_id in notify_users:
            if user_id != annotator_id:
                notification = self.create_notification(
                    user_id=user_id,
                    notification_type='new_annotation',
                    title=f"New annotation on '{transcript.title}'",
                    message=f"{annotator.username}: {annotation_content[:100]}...",
                    from_user_id=annotator_id,
                    link=f"/transcript/{transcript_id}",
                    related_id=transcript_id,
                    related_type='transcript'
                )
                notifications.append(notification)
        
        return notifications
    
    def notify_team_invitation(
        self,
        invited_user_id: int,
        inviter_id: int,
        team_id: int,
        team_name: str,
        role: str
    ) -> Notification:
        """Notify user about team invitation"""
        inviter = self.session.query(User).filter_by(id=inviter_id).first()
        
        return self.create_notification(
            user_id=invited_user_id,
            notification_type='team_invitation',
            title=f"Team invitation from {inviter.username}",
            message=f"You've been invited to join '{team_name}' as a {role}",
            from_user_id=inviter_id,
            link=f"/teams/{team_id}",
            related_id=team_id,
            related_type='team'
        )
    
    def notify_team_role_change(
        self,
        user_id: int,
        changer_id: int,
        team_id: int,
        team_name: str,
        old_role: str,
        new_role: str
    ) -> Notification:
        """Notify user about role change in team"""
        changer = self.session.query(User).filter_by(id=changer_id).first()
        
        return self.create_notification(
            user_id=user_id,
            notification_type='team_role_change',
            title=f"Role changed in {team_name}",
            message=f"{changer.username} changed your role from {old_role} to {new_role}",
            from_user_id=changer_id,
            link=f"/teams/{team_id}",
            related_id=team_id,
            related_type='team'
        )
    
    def notify_team_removal(
        self,
        user_id: int,
        remover_id: int,
        team_name: str
    ) -> Notification:
        """Notify user about being removed from team"""
        remover = self.session.query(User).filter_by(id=remover_id).first()
        
        return self.create_notification(
            user_id=user_id,
            notification_type='team_removal',
            title=f"Removed from {team_name}",
            message=f"You were removed from '{team_name}' by {remover.username}",
            from_user_id=remover_id,
            related_type='team'
        )
    
    def notify_team_members(
        self,
        team_id: int,
        notification_type: str,
        title: str,
        message: str,
        from_user_id: Optional[int] = None,
        exclude_user_ids: Optional[List[int]] = None
    ) -> List[Notification]:
        """Send notification to all team members"""
        from database.models import TeamMember
        
        # Get all team members
        members = self.session.query(TeamMember).filter_by(team_id=team_id).all()
        notifications = []
        
        exclude_ids = exclude_user_ids or []
        if from_user_id:
            exclude_ids.append(from_user_id)
        
        for member in members:
            if member.user_id not in exclude_ids:
                if self.should_notify(member.user_id, notification_type):
                    notification = self.create_notification(
                        user_id=member.user_id,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                        from_user_id=from_user_id,
                        link=f"/teams/{team_id}",
                        related_id=team_id,
                        related_type='team'
                    )
                    notifications.append(notification)
        
        return notifications
    
    def get_notification_preferences(self, user_id: int) -> Dict[str, bool]:
        """Get user's notification preferences"""
        # This would typically be stored in a UserPreferences table
        # For now, return default preferences
        return {
            'mention': True,
            'annotation_reply': True,
            'transcript_edit': True,
            'share_access': True,
            'new_annotation': False,  # Might be too noisy
            'team_invitation': True,
            'team_role_change': True,
            'team_removal': True,
            'team_announcement': True,
            'email_notifications': False  # Email notifications deferred
        }
    
    def should_notify(self, user_id: int, notification_type: str) -> bool:
        """Check if user wants this type of notification"""
        preferences = self.get_notification_preferences(user_id)
        return preferences.get(notification_type, True)
    
    def get_related_users(self, transcript_id: int) -> List[int]:
        """Get users who should be notified about changes to a transcript"""
        users = set()
        
        # Owner of the transcript
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        if transcript:
            users.add(transcript.user_id)
        
        # Users who have annotated
        annotations = self.session.query(Annotation).filter_by(
            transcript_id=transcript_id
        ).distinct(Annotation.user_id).all()
        for ann in annotations:
            users.add(ann.user_id)
        
        # Users with share access
        shares = self.session.query(SharedLink).filter_by(
            transcript_id=transcript_id,
            created_by_user_id=transcript.user_id  # Only notify about owner's shares
        ).all()
        # In a full implementation, we'd track who accessed shares
        
        return list(users)
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text"""
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, text)
    
    def process_mentions(
        self,
        text: str,
        from_user_id: int,
        annotation_id: int,
        transcript_id: int
    ) -> List[Notification]:
        """Process @mentions in text and create notifications"""
        mentioned_usernames = self.extract_mentions(text)
        notifications = []
        
        for username in mentioned_usernames:
            user = self.session.query(User).filter_by(username=username).first()
            if user and user.id != from_user_id:
                if self.should_notify(user.id, 'mention'):
                    notification = self.notify_mention(
                        mentioned_user_id=user.id,
                        from_user_id=from_user_id,
                        content=text,
                        annotation_id=annotation_id,
                        transcript_id=transcript_id
                    )
                    notifications.append(notification)
        
        return notifications
    
    def get_user_notifications(
        self,
        user_id: int,
        include_read: bool = True,
        include_archived: bool = False,
        limit: Optional[int] = None
    ) -> List[Notification]:
        """Get notifications for user with filtering options"""
        query = self.session.query(Notification).options(
            joinedload(Notification.from_user)
        ).filter(Notification.user_id == user_id)
        
        if not include_read:
            query = query.filter(Notification.is_read == False)
        
        if not include_archived:
            query = query.filter(Notification.is_archived == False)
        
        query = query.order_by(desc(Notification.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a single notification as read"""
        notification = self.session.query(Notification).filter_by(id=notification_id).first()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.session.commit()
            return True
        return False
    
    def mark_notification_unread(self, notification_id: int) -> bool:
        """Mark a single notification as unread"""
        notification = self.session.query(Notification).filter_by(id=notification_id).first()
        if notification:
            notification.is_read = False
            notification.read_at = None
            self.session.commit()
            return True
        return False
    
    def archive_notification(self, notification_id: int) -> bool:
        """Archive a single notification"""
        notification = self.session.query(Notification).filter_by(id=notification_id).first()
        if notification:
            notification.is_archived = True
            self.session.commit()
            return True
        return False
    
    def unarchive_notification(self, notification_id: int) -> bool:
        """Unarchive a single notification"""
        notification = self.session.query(Notification).filter_by(id=notification_id).first()
        if notification:
            notification.is_archived = False
            self.session.commit()
            return True
        return False
    
    def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        count = self.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        self.session.commit()
        return count
    
    def archive_all_read(self, user_id: int) -> int:
        """Archive all read notifications for a user"""
        count = self.session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == True,
            Notification.is_archived == False
        ).update({
            'is_archived': True
        })
        self.session.commit()
        return count
    
    def get_user_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        # Get all notifications for user
        all_notifications = self.session.query(Notification).filter_by(user_id=user_id).all()
        
        # Calculate stats
        total = len(all_notifications)
        unread = sum(1 for n in all_notifications if not n.is_read)
        
        # This week and month
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        this_week = sum(1 for n in all_notifications if n.created_at >= week_ago)
        this_month = sum(1 for n in all_notifications if n.created_at >= month_ago)
        
        # By type
        by_type = {}
        for notification in all_notifications:
            by_type[notification.type] = by_type.get(notification.type, 0) + 1
        
        return {
            'total': total,
            'unread': unread,
            'this_week': this_week,
            'this_month': this_month,
            'by_type': by_type
        }