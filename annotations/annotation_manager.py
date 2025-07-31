"""
Annotation manager for handling transcript annotations and comments
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from database.models import Annotation, User, Transcript, TranscriptVersion
import re
from collections import defaultdict


class AnnotationManager:
    """Manages annotations for transcripts"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_annotation(
        self,
        transcript_id: int,
        user_id: int,
        content: str,
        position_start: Optional[int] = None,
        position_end: Optional[int] = None,
        highlighted_text: Optional[str] = None,
        parent_id: Optional[int] = None,
        notification_manager=None  # Optional notification manager
    ) -> Annotation:
        """Create a new annotation"""
        # Validate transcript exists and user has access
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        if not transcript:
            raise ValueError("Transcript not found")
        
        # Create annotation
        annotation = Annotation(
            transcript_id=transcript_id,
            user_id=user_id,
            content=content,
            position_start=position_start,
            position_end=position_end,
            highlighted_text=highlighted_text,
            parent_id=parent_id
        )
        
        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)
        
        # Load relationships
        annotation = self.session.query(Annotation).options(
            joinedload(Annotation.user),
            joinedload(Annotation.replies)
        ).filter_by(id=annotation.id).first()
        
        # Handle notifications if manager provided
        if notification_manager:
            # Process mentions
            notification_manager.process_mentions(
                text=content,
                from_user_id=user_id,
                annotation_id=annotation.id,
                transcript_id=transcript_id
            )
            
            # Notify about reply if this is a reply
            if parent_id:
                parent_annotation = self.get_annotation(parent_id)
                if parent_annotation and parent_annotation.user_id != user_id:
                    notification_manager.notify_annotation_reply(
                        original_author_id=parent_annotation.user_id,
                        reply_author_id=user_id,
                        reply_content=content,
                        annotation_id=annotation.id,
                        transcript_id=transcript_id
                    )
            else:
                # Notify interested users about new annotation
                related_users = notification_manager.get_related_users(transcript_id)
                notification_manager.notify_new_annotation(
                    transcript_id=transcript_id,
                    annotator_id=user_id,
                    annotation_content=content,
                    notify_users=related_users
                )
        
        return annotation
    
    def get_annotation(self, annotation_id: int) -> Optional[Annotation]:
        """Get a single annotation with all details"""
        return self.session.query(Annotation).options(
            joinedload(Annotation.user),
            joinedload(Annotation.replies).joinedload(Annotation.user),
            joinedload(Annotation.parent)
        ).filter_by(id=annotation_id).first()
    
    def get_transcript_annotations(
        self,
        transcript_id: int,
        include_replies: bool = True,
        only_unresolved: bool = False
    ) -> List[Annotation]:
        """Get all annotations for a transcript"""
        query = self.session.query(Annotation).options(
            joinedload(Annotation.user),
            joinedload(Annotation.replies).joinedload(Annotation.user)
        ).filter_by(transcript_id=transcript_id)
        
        # Filter top-level annotations only if not including replies
        if not include_replies:
            query = query.filter(Annotation.parent_id.is_(None))
        
        # Filter unresolved if requested
        if only_unresolved:
            query = query.filter_by(is_resolved=False)
        
        # Order by position or creation time
        query = query.order_by(
            Annotation.position_start.asc().nullsfirst(),
            Annotation.created_at.asc()
        )
        
        return query.all()
    
    def get_annotations_by_position(
        self,
        transcript_id: int,
        position: int
    ) -> List[Annotation]:
        """Get annotations that include a specific position"""
        return self.session.query(Annotation).options(
            joinedload(Annotation.user)
        ).filter(
            and_(
                Annotation.transcript_id == transcript_id,
                Annotation.position_start <= position,
                Annotation.position_end >= position
            )
        ).all()
    
    def update_annotation(
        self,
        annotation_id: int,
        user_id: int,
        content: Optional[str] = None,
        is_resolved: Optional[bool] = None
    ) -> Annotation:
        """Update an annotation"""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            raise ValueError("Annotation not found")
        
        # Check permission (only author can edit)
        if annotation.user_id != user_id:
            raise PermissionError("Only the author can edit this annotation")
        
        # Update fields
        if content is not None:
            annotation.content = content
        if is_resolved is not None:
            annotation.is_resolved = is_resolved
        
        self.session.commit()
        self.session.refresh(annotation)
        
        return annotation
    
    def delete_annotation(self, annotation_id: int, user_id: int) -> bool:
        """Delete an annotation"""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            raise ValueError("Annotation not found")
        
        # Check permission
        if annotation.user_id != user_id:
            raise PermissionError("Only the author can delete this annotation")
        
        # Delete annotation and all replies
        self.session.delete(annotation)
        self.session.commit()
        
        return True
    
    def resolve_annotation(self, annotation_id: int, user_id: int) -> Annotation:
        """Mark an annotation as resolved"""
        return self.update_annotation(annotation_id, user_id, is_resolved=True)
    
    def unresolve_annotation(self, annotation_id: int, user_id: int) -> Annotation:
        """Mark an annotation as unresolved"""
        return self.update_annotation(annotation_id, user_id, is_resolved=False)
    
    def get_user_annotations(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Annotation]:
        """Get all annotations by a user"""
        return self.session.query(Annotation).options(
            joinedload(Annotation.transcript),
            joinedload(Annotation.parent)
        ).filter_by(
            user_id=user_id
        ).order_by(
            desc(Annotation.created_at)
        ).limit(limit).offset(offset).all()
    
    def search_annotations(
        self,
        transcript_id: int,
        query: str,
        user_id: Optional[int] = None
    ) -> List[Annotation]:
        """Search annotations by content"""
        search_query = self.session.query(Annotation).options(
            joinedload(Annotation.user)
        ).filter(
            and_(
                Annotation.transcript_id == transcript_id,
                Annotation.content.ilike(f'%{query}%')
            )
        )
        
        if user_id:
            search_query = search_query.filter_by(user_id=user_id)
        
        return search_query.all()
    
    def get_annotation_stats(self, transcript_id: int) -> Dict[str, Any]:
        """Get statistics about annotations on a transcript"""
        annotations = self.get_transcript_annotations(transcript_id)
        
        # Count by user
        user_counts = defaultdict(int)
        resolved_count = 0
        reply_count = 0
        
        for ann in annotations:
            user_counts[ann.user.username] += 1
            if ann.is_resolved:
                resolved_count += 1
            if ann.parent_id:
                reply_count += 1
        
        return {
            'total_annotations': len(annotations),
            'resolved_count': resolved_count,
            'unresolved_count': len(annotations) - resolved_count,
            'reply_count': reply_count,
            'unique_users': len(user_counts),
            'user_counts': dict(user_counts),
            'top_contributor': max(user_counts.items(), key=lambda x: x[1])[0] if user_counts else None
        }
    
    def create_mention_notification(
        self,
        annotation: Annotation,
        mentioned_usernames: List[str]
    ) -> None:
        """Create notifications for @mentions in annotations"""
        # Extract @mentions from content
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, annotation.content)
        
        for username in mentions:
            user = self.session.query(User).filter_by(username=username).first()
            if user and user.id != annotation.user_id:
                # Here you would create a notification
                # For now, we'll just print (implement notification system later)
                print(f"Notification: {annotation.user.username} mentioned you in an annotation")
    
    def get_thread_context(self, annotation_id: int) -> List[Annotation]:
        """Get the full thread context for an annotation"""
        annotation = self.get_annotation(annotation_id)
        if not annotation:
            return []
        
        # If it's a reply, get the parent thread
        if annotation.parent_id:
            parent = self.get_annotation(annotation.parent_id)
            thread = [parent] + parent.replies if parent else []
        else:
            # It's a parent, get all replies
            thread = [annotation] + annotation.replies
        
        return thread
    
    def export_annotations(
        self,
        transcript_id: int,
        format: str = 'markdown'
    ) -> str:
        """Export annotations in various formats"""
        annotations = self.get_transcript_annotations(transcript_id)
        
        if format == 'markdown':
            output = "# Transcript Annotations\n\n"
            for ann in annotations:
                if not ann.parent_id:  # Top-level only
                    output += f"## {ann.user.username} - {ann.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    if ann.highlighted_text:
                        output += f"> {ann.highlighted_text}\n\n"
                    output += f"{ann.content}\n"
                    if ann.is_resolved:
                        output += "**[RESOLVED]**\n"
                    
                    # Add replies
                    for reply in ann.replies:
                        output += f"\n### Reply by {reply.user.username}\n"
                        output += f"{reply.content}\n"
                    output += "\n---\n\n"
        
        elif format == 'json':
            import json
            data = []
            for ann in annotations:
                if not ann.parent_id:
                    ann_data = {
                        'id': ann.id,
                        'user': ann.user.username,
                        'content': ann.content,
                        'highlighted_text': ann.highlighted_text,
                        'position': [ann.position_start, ann.position_end],
                        'resolved': ann.is_resolved,
                        'created_at': ann.created_at.isoformat(),
                        'replies': [
                            {
                                'user': reply.user.username,
                                'content': reply.content,
                                'created_at': reply.created_at.isoformat()
                            }
                            for reply in ann.replies
                        ]
                    }
                    data.append(ann_data)
            output = json.dumps(data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return output
    
    def merge_annotations_with_transcript(
        self,
        transcript_id: int,
        transcript_content: str
    ) -> str:
        """Merge annotations inline with transcript content"""
        annotations = self.get_transcript_annotations(transcript_id)
        
        # Group annotations by position
        position_annotations = defaultdict(list)
        for ann in annotations:
            if ann.position_start is not None and not ann.parent_id:
                position_annotations[ann.position_start].append(ann)
        
        # Sort positions in reverse order to insert from end to beginning
        positions = sorted(position_annotations.keys(), reverse=True)
        
        # Insert annotations
        result = transcript_content
        for pos in positions:
            anns = position_annotations[pos]
            annotation_text = ""
            for ann in anns:
                annotation_text += f"\n[NOTE by {ann.user.username}: {ann.content}]"
                if ann.replies:
                    for reply in ann.replies:
                        annotation_text += f"\n  [REPLY by {reply.user.username}: {reply.content}]"
            
            # Insert at position
            if pos <= len(result):
                result = result[:pos] + annotation_text + result[pos:]
        
        return result