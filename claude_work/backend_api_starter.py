"""
Backend API Starter - FastAPI Implementation
This file provides a starting point for the backend API implementation
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import secrets
import uuid

# Import our database models and auth utilities
from api.database import get_db, User, Transcript, Team, TeamMember, TeamRole
from api.auth import (
    authenticate_user, create_user, create_access_token, create_refresh_token,
    get_current_active_user, get_current_admin_user, get_user_by_email,
    create_api_key
)

# Initialize FastAPI app
app = FastAPI(
    title="Transcription Platform API",
    description="Enterprise-grade audio/video transcription platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# Pydantic Models
# ===========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TranscriptionCreate(BaseModel):
    title: str
    language: str = "auto"
    method: str = "basic"
    team_id: Optional[int] = None

class TranscriptionResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: datetime
    duration: Optional[float]
    text: Optional[str]
    entities: Optional[Dict[str, List[str]]]
    confidence: Optional[float]

class TeamCreate(BaseModel):
    name: str
    description: Optional[str]

class TeamMemberInvite(BaseModel):
    email: EmailStr
    role: str = "member"


# ===========================
# Authentication Endpoints
# ===========================

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate username from email if not provided
    username = user.email.split('@')[0]
    
    # Create user
    db_user = create_user(
        db=db,
        email=user.email,
        password=user.password,
        username=username,
        full_name=user.name
    )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.full_name,
            "role": db_user.role.value,
            "created_at": db_user.created_at
        }
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email and password"""
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role.value,
            "created_at": user.created_at
        }
    }

@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout current user"""
    # In production, you would invalidate the token here
    # For now, the client should discard the token
    return {"message": "Successfully logged out"}

# ===========================
# User Endpoints
# ===========================

@app.get("/api/users/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name or current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at
    )

@app.put("/api/users/profile", response_model=UserResponse)
async def update_profile(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if name:
        current_user.full_name = name
        db.commit()
        db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name or current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at
    )

# ===========================
# Transcription Endpoints
# ===========================

@app.post("/api/transcriptions/upload", response_model=TranscriptionResponse)
async def upload_transcription(
    file: UploadFile = File(...),
    title: str = None,
    language: str = "auto",
    method: str = "basic",
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a file for transcription"""
    # Validate file
    if not file.filename.endswith(('.mp3', '.wav', '.mp4', '.mov', '.m4a')):
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    # Create transcription record
    transcript = Transcript(
        user_id=current_user.id,
        team_id=team_id,
        title=title or file.filename,
        content="",  # Will be filled after processing
        file_name=file.filename,
        file_size=0,  # Will be updated
        language=language,
        model_used=method,
        entities={}
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    # In production, you would:
    # 1. Save the file to storage
    # 2. Queue the transcription job
    # 3. Update the transcript when processing completes
    
    return TranscriptionResponse(
        id=str(transcript.id),
        title=transcript.title,
        status="processing",
        created_at=transcript.created_at,
        duration=None,
        text=None,
        entities=None,
        confidence=None
    )

@app.get("/api/transcriptions", response_model=List[TranscriptionResponse])
async def list_transcriptions(
    skip: int = 0,
    limit: int = 20,
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's transcriptions"""
    query = db.query(Transcript).filter(Transcript.user_id == current_user.id)
    
    if team_id:
        query = query.filter(Transcript.team_id == team_id)
    
    transcriptions = query.offset(skip).limit(limit).all()
    
    return [
        TranscriptionResponse(
            id=str(t.id),
            title=t.title,
            status="completed" if t.content else "processing",
            created_at=t.created_at,
            duration=t.duration,
            text=t.content[:100] + "..." if t.content else None,
            entities=t.entities,
            confidence=t.confidence
        )
        for t in transcriptions
    ]

@app.get("/api/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific transcription"""
    transcript = db.query(Transcript).filter(
        Transcript.id == transcription_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return TranscriptionResponse(
        id=str(transcript.id),
        title=transcript.title,
        status="completed" if transcript.content else "processing",
        created_at=transcript.created_at,
        duration=transcript.duration,
        text=transcript.content,
        entities=transcript.entities,
        confidence=transcript.confidence
    )

# ===========================
# Team Endpoints
# ===========================

@app.post("/api/teams", response_model=Dict[str, Any])
async def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    # Create team
    db_team = Team(
        name=team.name,
        description=team.description,
        owner_id=current_user.id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # Add owner as team member
    owner_member = TeamMember(
        team_id=db_team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER,
        invited_by_id=current_user.id
    )
    db.add(owner_member)
    db.commit()
    
    return {
        "id": db_team.id,
        "name": db_team.name,
        "description": db_team.description,
        "owner_id": db_team.owner_id,
        "created_at": db_team.created_at
    }

@app.get("/api/teams")
async def list_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's teams"""
    # Get teams where user is a member
    team_memberships = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()
    
    teams = []
    for membership in team_memberships:
        team = membership.team
        member_count = db.query(TeamMember).filter(
            TeamMember.team_id == team.id
        ).count()
        
        teams.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "role": membership.role.value,
            "member_count": member_count
        })
    
    return teams

@app.post("/api/teams/{team_id}/members")
async def invite_team_member(
    team_id: int,
    invite: TeamMemberInvite,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invite a member to team"""
    # Check if user is admin or owner of the team
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Find user by email
    invited_user = get_user_by_email(db, invite.email)
    if not invited_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a member
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == invited_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a team member")
    
    # Add member
    new_member = TeamMember(
        team_id=team_id,
        user_id=invited_user.id,
        role=TeamRole[invite.role.upper()],
        invited_by_id=current_user.id
    )
    db.add(new_member)
    db.commit()
    
    return {"message": "Member added successfully", "user_id": invited_user.id}

# ===========================
# Health Check
# ===========================

@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

# ===========================
# WebSocket for Real-time
# ===========================

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/collaboration/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time collaboration"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle different message types
            if data["type"] == "cursor":
                await manager.broadcast({
                    "type": "cursor",
                    "userId": data["userId"],
                    "position": data["position"]
                }, session_id)
            elif data["type"] == "content":
                await manager.broadcast({
                    "type": "content",
                    "userId": data["userId"],
                    "change": data["change"]
                }, session_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

# ===========================
# Run the application
# ===========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)