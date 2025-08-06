"""
Collaboration API Endpoints
FastAPI endpoints for real-time collaboration features
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
import uuid

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota
from database.connection import get_db
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# Import database models
from database.models import Base, User, Team, TeamMember
from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/collaboration")

# Database models for collaboration
class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_id = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    timestamp_start = Column(String)  # Time in transcript
    timestamp_end = Column(String)
    parent_id = Column(String, ForeignKey("comments.id"))
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])

class Annotation(Base):
    __tablename__ = "annotations"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_id = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # highlight, note, tag, etc.
    text = Column(Text)
    data = Column(JSON)  # Additional annotation data
    timestamp_start = Column(String)
    timestamp_end = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="annotations")

class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_id = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    active = Column(Boolean, default=True)
    participants = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

# Pydantic models
class CommentCreate(BaseModel):
    transcript_id: str
    text: str
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    parent_id: Optional[str] = None

class CommentUpdate(BaseModel):
    text: Optional[str] = None
    resolved: Optional[bool] = None

class CommentResponse(BaseModel):
    id: str
    transcript_id: str
    user_id: int
    user_name: str
    text: str
    timestamp_start: Optional[str]
    timestamp_end: Optional[str]
    parent_id: Optional[str]
    resolved: bool
    created_at: datetime
    updated_at: datetime
    replies: List['CommentResponse'] = []

class AnnotationCreate(BaseModel):
    transcript_id: str
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None

class AnnotationResponse(BaseModel):
    id: str
    transcript_id: str
    user_id: str
    user_name: str
    type: str
    text: Optional[str]
    data: Optional[Dict[str, Any]]
    timestamp_start: Optional[str]
    timestamp_end: Optional[str]
    created_at: datetime
    updated_at: datetime

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, transcript_id: str):
        await websocket.accept()
        if transcript_id not in self.active_connections:
            self.active_connections[transcript_id] = []
        self.active_connections[transcript_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, transcript_id: str):
        if transcript_id in self.active_connections:
            self.active_connections[transcript_id].remove(websocket)
            if not self.active_connections[transcript_id]:
                del self.active_connections[transcript_id]
    
    async def broadcast(self, message: dict, transcript_id: str, exclude: Optional[WebSocket] = None):
        if transcript_id in self.active_connections:
            for connection in self.active_connections[transcript_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

manager = ConnectionManager()

# REST endpoints for comments
@router.post("/comments", response_model=CommentResponse)
@require_quota('api_calls', 1, 'real_time_collab')  # Require real-time collaboration feature
async def create_comment(
    comment: CommentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new comment on a transcript"""
    try:
        # Create comment
        db_comment = Comment(
            transcript_id=comment.transcript_id,
            user_id=current_user['id'],
            text=comment.text,
            timestamp_start=comment.timestamp_start,
            timestamp_end=comment.timestamp_end,
            parent_id=comment.parent_id
        )
        
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        
        # Get user info
        user = db.query(User).filter(User.id == current_user['id']).first()
        
        # Broadcast to WebSocket connections
        await manager.broadcast(
            {
                "type": "comment_added",
                "comment": {
                    "id": db_comment.id,
                    "user_name": user.name if user else "Unknown",
                    "text": db_comment.text,
                    "timestamp": db_comment.created_at.isoformat()
                }
            },
            comment.transcript_id
        )
        
        return CommentResponse(
            id=db_comment.id,
            transcript_id=db_comment.transcript_id,
            user_id=db_comment.user_id,
            user_name=user.name if user else "Unknown",
            text=db_comment.text,
            timestamp_start=db_comment.timestamp_start,
            timestamp_end=db_comment.timestamp_end,
            parent_id=db_comment.parent_id,
            resolved=db_comment.resolved,
            created_at=db_comment.created_at,
            updated_at=db_comment.updated_at,
            replies=[]
        )
        
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comments/{transcript_id}", response_model=List[CommentResponse])
@require_quota('api_calls', 1, 'real_time_collab')
async def get_transcript_comments(
    transcript_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all comments for a transcript"""
    try:
        # Get comments with user info
        comments = db.query(Comment, User).join(User).filter(
            Comment.transcript_id == transcript_id,
            Comment.parent_id == None  # Only top-level comments
        ).all()
        
        result = []
        for comment, user in comments:
            # Get replies
            replies = db.query(Comment, User).join(User).filter(
                Comment.parent_id == comment.id
            ).all()
            
            comment_response = CommentResponse(
                id=comment.id,
                transcript_id=comment.transcript_id,
                user_id=comment.user_id,
                user_name=user.name,
                text=comment.text,
                timestamp_start=comment.timestamp_start,
                timestamp_end=comment.timestamp_end,
                parent_id=comment.parent_id,
                resolved=comment.resolved,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                replies=[
                    CommentResponse(
                        id=reply.id,
                        transcript_id=reply.transcript_id,
                        user_id=reply.user_id,
                        user_name=reply_user.name,
                        text=reply.text,
                        timestamp_start=reply.timestamp_start,
                        timestamp_end=reply.timestamp_end,
                        parent_id=reply.parent_id,
                        resolved=reply.resolved,
                        created_at=reply.created_at,
                        updated_at=reply.updated_at,
                        replies=[]
                    )
                    for reply, reply_user in replies
                ]
            )
            result.append(comment_response)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting comments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comments/{comment_id}", response_model=CommentResponse)
@require_quota('api_calls', 1, 'real_time_collab')
async def update_comment(
    comment_id: str,
    update: CommentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a comment"""
    try:
        # Get comment
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check permission
        if comment.user_id != current_user['id'] and current_user['role'] != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update fields
        if update.text is not None:
            comment.text = update.text
        if update.resolved is not None:
            comment.resolved = update.resolved
        
        comment.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(comment)
        
        # Broadcast update
        await manager.broadcast(
            {
                "type": "comment_updated",
                "comment_id": comment_id,
                "updates": update.dict(exclude_unset=True)
            },
            comment.transcript_id
        )
        
        user = db.query(User).filter(User.id == comment.user_id).first()
        
        return CommentResponse(
            id=comment.id,
            transcript_id=comment.transcript_id,
            user_id=comment.user_id,
            user_name=user.name if user else "Unknown",
            text=comment.text,
            timestamp_start=comment.timestamp_start,
            timestamp_end=comment.timestamp_end,
            parent_id=comment.parent_id,
            resolved=comment.resolved,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=[]
        )
        
    except Exception as e:
        logger.error(f"Error updating comment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/comments/{comment_id}")
@require_quota('api_calls', 1, 'real_time_collab')
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comment"""
    try:
        # Get comment
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check permission
        if comment.user_id != current_user['id'] and current_user['role'] != 'admin':
            raise HTTPException(status_code=403, detail="Not authorized")
        
        transcript_id = comment.transcript_id
        
        # Delete replies first
        db.query(Comment).filter(Comment.parent_id == comment_id).delete()
        
        # Delete comment
        db.delete(comment)
        db.commit()
        
        # Broadcast deletion
        await manager.broadcast(
            {
                "type": "comment_deleted",
                "comment_id": comment_id
            },
            transcript_id
        )
        
        return {"message": "Comment deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# REST endpoints for annotations
@router.post("/annotations", response_model=AnnotationResponse)
@require_quota('api_calls', 1, 'real_time_collab')
async def create_annotation(
    annotation: AnnotationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new annotation"""
    try:
        # Create annotation
        db_annotation = Annotation(
            transcript_id=annotation.transcript_id,
            user_id=current_user['id'],
            type=annotation.type,
            text=annotation.text,
            data=annotation.data,
            timestamp_start=annotation.timestamp_start,
            timestamp_end=annotation.timestamp_end
        )
        
        db.add(db_annotation)
        db.commit()
        db.refresh(db_annotation)
        
        # Get user info
        user = db.query(User).filter(User.id == current_user['id']).first()
        
        # Broadcast to WebSocket connections
        await manager.broadcast(
            {
                "type": "annotation_added",
                "annotation": {
                    "id": db_annotation.id,
                    "type": db_annotation.type,
                    "user_name": user.name if user else "Unknown",
                    "timestamp": db_annotation.created_at.isoformat()
                }
            },
            annotation.transcript_id
        )
        
        return AnnotationResponse(
            id=db_annotation.id,
            transcript_id=db_annotation.transcript_id,
            user_id=db_annotation.user_id,
            user_name=user.name if user else "Unknown",
            type=db_annotation.type,
            text=db_annotation.text,
            data=db_annotation.data,
            timestamp_start=db_annotation.timestamp_start,
            timestamp_end=db_annotation.timestamp_end,
            created_at=db_annotation.created_at,
            updated_at=db_annotation.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating annotation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/annotations/{transcript_id}", response_model=List[AnnotationResponse])
@require_quota('api_calls', 1, 'real_time_collab')
async def get_transcript_annotations(
    transcript_id: str,
    annotation_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all annotations for a transcript"""
    try:
        # Build query
        query = db.query(Annotation, User).join(User).filter(
            Annotation.transcript_id == transcript_id
        )
        
        if annotation_type:
            query = query.filter(Annotation.type == annotation_type)
        
        annotations = query.all()
        
        return [
            AnnotationResponse(
                id=annotation.id,
                transcript_id=annotation.transcript_id,
                user_id=annotation.user_id,
                user_name=user.name,
                type=annotation.type,
                text=annotation.text,
                data=annotation.data,
                timestamp_start=annotation.timestamp_start,
                timestamp_end=annotation.timestamp_end,
                created_at=annotation.created_at,
                updated_at=annotation.updated_at
            )
            for annotation, user in annotations
        ]
        
    except Exception as e:
        logger.error(f"Error getting annotations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/{transcript_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    transcript_id: str,
    token: str
):
    """WebSocket endpoint for real-time collaboration"""
    try:
        # Verify token
        # TODO: Implement proper WebSocket authentication
        
        await manager.connect(websocket, transcript_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                
                # Handle different message types
                if data['type'] == 'cursor_position':
                    # Broadcast cursor position to other users
                    await manager.broadcast(
                        {
                            "type": "cursor_update",
                            "user_id": data.get('user_id'),
                            "position": data.get('position')
                        },
                        transcript_id,
                        exclude=websocket
                    )
                
                elif data['type'] == 'selection_change':
                    # Broadcast selection change
                    await manager.broadcast(
                        {
                            "type": "selection_update",
                            "user_id": data.get('user_id'),
                            "selection": data.get('selection')
                        },
                        transcript_id,
                        exclude=websocket
                    )
                
                elif data['type'] == 'presence_update':
                    # Update user presence
                    await manager.broadcast(
                        {
                            "type": "presence_update",
                            "user_id": data.get('user_id'),
                            "status": data.get('status')
                        },
                        transcript_id
                    )
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, transcript_id)
            # Notify others about disconnection
            await manager.broadcast(
                {
                    "type": "user_disconnected",
                    "user_id": data.get('user_id', 'unknown')
                },
                transcript_id
            )
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

# Session management endpoints
@router.post("/sessions")
@require_quota('api_calls', 1, 'real_time_collab')
async def create_collaboration_session(
    transcript_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new collaboration session"""
    try:
        # Check if active session exists
        existing = db.query(CollaborationSession).filter(
            and_(
                CollaborationSession.transcript_id == transcript_id,
                CollaborationSession.active == True
            )
        ).first()
        
        if existing:
            return {
                "session_id": existing.id,
                "message": "Active session already exists"
            }
        
        # Create new session
        session = CollaborationSession(
            transcript_id=transcript_id,
            created_by=current_user['id'],
            participants=[current_user['id']]
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "session_id": session.id,
            "transcript_id": session.transcript_id,
            "created_at": session.created_at
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{transcript_id}/active")
@require_quota('api_calls', 1, 'real_time_collab')
async def get_active_session(
    transcript_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active collaboration session for a transcript"""
    try:
        session = db.query(CollaborationSession).filter(
            and_(
                CollaborationSession.transcript_id == transcript_id,
                CollaborationSession.active == True
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="No active session")
        
        return {
            "session_id": session.id,
            "transcript_id": session.transcript_id,
            "participants": session.participants,
            "created_at": session.created_at,
            "created_by": session.created_by
        }
        
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))