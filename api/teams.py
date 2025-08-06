"""
Team endpoints for the API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db_session, User, Team, TeamMember
from .auth import get_current_user_or_api_key as get_current_user
from teams.team_manager import TeamManager

logger = logging.getLogger(__name__)

# Router setup
teams_router = APIRouter()


# Pydantic models
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TeamMemberAdd(BaseModel):
    email: str
    role: str = Field("member", pattern="^(admin|member|viewer)$")


class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    member_count: int
    transcript_count: int
    your_role: Optional[str] = None


class TeamDetailResponse(TeamResponse):
    members: List[dict]
    recent_activity: List[dict]


class TeamListResponse(BaseModel):
    teams: List[TeamResponse]
    total: int


# Endpoints
@teams_router.get("/", response_model=TeamListResponse)
async def list_teams(
    current_user: User = Depends(get_current_user),
    include_all: bool = Query(False, description="Include teams you're not a member of")
):
    """List teams (user's teams or all teams based on parameter)"""
    db = next(get_db_session())
    
    if include_all:
        # Get all teams (for discovery)
        teams = db.query(Team).all()
    else:
        # Get user's teams
        team_ids = [m.team_id for m in current_user.team_memberships]
        teams = db.query(Team).filter(Team.id.in_(team_ids)).all() if team_ids else []
    
    # Convert to response
    team_list = []
    for team in teams:
        # Get user's role in team
        member = db.query(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == current_user.id
        ).first()
        
        team_list.append(TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_by=team.created_by,
            created_at=team.created_at,
            member_count=len(team.members),
            transcript_count=len(team.transcripts),
            your_role=member.role if member else None
        ))
    
    return TeamListResponse(
        teams=team_list,
        total=len(teams)
    )


@teams_router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new team"""
    db = next(get_db_session())
    team_manager = TeamManager(db)
    
    # Create team
    new_team = team_manager.create_team(
        name=team.name,
        description=team.description,
        created_by=current_user.id
    )
    
    logger.info(f"Created team {new_team.id} by user {current_user.id}")
    
    return TeamResponse(
        id=new_team.id,
        name=new_team.name,
        description=new_team.description,
        created_by=new_team.created_by,
        created_at=new_team.created_at,
        member_count=1,  # Creator is automatically added
        transcript_count=0,
        your_role="admin"  # Creator is admin
    )


@teams_router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get team details"""
    db = next(get_db_session())
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check if user is member
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    # Get members list
    members = []
    for team_member in team.members:
        members.append({
            "id": team_member.user.id,
            "username": team_member.user.username,
            "email": team_member.user.email,
            "role": team_member.role,
            "joined_at": team_member.joined_at.isoformat()
        })
    
    # Get recent activity (simplified)
    recent_activity = []
    for transcript in team.transcripts[:5]:  # Last 5 transcripts
        recent_activity.append({
            "type": "transcript_created",
            "transcript_id": transcript.id,
            "title": transcript.title,
            "user": transcript.user.username,
            "timestamp": transcript.created_at.isoformat()
        })
    
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_by=team.created_by,
        created_at=team.created_at,
        member_count=len(team.members),
        transcript_count=len(team.transcripts),
        your_role=member.role,
        members=members,
        recent_activity=recent_activity
    )


@teams_router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    update: TeamUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update team details"""
    db = next(get_db_session())
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check if user is admin
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.role == "admin"
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can update team details"
        )
    
    # Update team
    if update.name is not None:
        team.name = update.name
    if update.description is not None:
        team.description = update.description
    
    db.commit()
    db.refresh(team)
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_by=team.created_by,
        created_at=team.created_at,
        member_count=len(team.members),
        transcript_count=len(team.transcripts),
        your_role=member.role
    )


@teams_router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a team"""
    db = next(get_db_session())
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check if user is creator
    if team.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team creator can delete the team"
        )
    
    # Delete team (cascades to members and transcripts)
    db.delete(team)
    db.commit()
    
    logger.info(f"Deleted team {team_id} by user {current_user.id}")


@teams_router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user)
):
    """Add a member to team"""
    db = next(get_db_session())
    team_manager = TeamManager(db)
    
    # Check if user is admin
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.role == "admin"
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can add members"
        )
    
    # Find user by email
    new_user = db.query(User).filter(User.email == member_data.email).first()
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Add member
    try:
        team_manager.add_member(
            team_id=team_id,
            user_id=new_user.id,
            role=member_data.role,
            added_by=current_user.id
        )
        
        return {"message": f"Successfully added {new_user.username} to team"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@teams_router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove a member from team"""
    db = next(get_db_session())
    team_manager = TeamManager(db)
    
    # Check if user is admin or removing themselves
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    if member.role != "admin" and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can remove other members"
        )
    
    # Remove member
    try:
        team_manager.remove_member(team_id=team_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@teams_router.put("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: int,
    user_id: int,
    role: str = Query(..., pattern="^(admin|member|viewer)$"),
    current_user: User = Depends(get_current_user)
):
    """Update a member's role"""
    db = next(get_db_session())
    team_manager = TeamManager(db)
    
    # Check if user is admin
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.role == "admin"
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team admins can update member roles"
        )
    
    # Update role
    try:
        team_manager.update_member_role(
            team_id=team_id,
            user_id=user_id,
            new_role=role
        )
        
        return {"message": f"Successfully updated role to {role}"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )