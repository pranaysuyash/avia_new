"""
Team Management Router
Handles team creation, membership, and collaboration features
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Import database and auth utilities
from api.database import get_db, User, Team, TeamMember, TeamRole
from api.auth import get_current_active_user, get_user_by_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["teams"])

# ===========================
# Pydantic Models
# ===========================

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class TeamMemberInvite(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")

# ===========================
# Team Management Endpoints
# ===========================

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
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
    
    logger.info(f"User {current_user.id} created team {db_team.id}")
    
    return {
        "id": db_team.id,
        "name": db_team.name,
        "description": db_team.description,
        "owner_id": db_team.owner_id,
        "created_at": db_team.created_at,
        "member_count": 1
    }

@router.get("", response_model=List[Dict[str, Any]])
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
            "member_count": member_count,
            "created_at": team.created_at
        })
    
    return teams

@router.get("/{team_id}")
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get team details"""
    # Check membership
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    team = membership.team
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "created_at": team.created_at,
        "your_role": membership.role.value,
        "members": [
            {
                "id": m.user.id,
                "email": m.user.email,
                "name": m.user.full_name or m.user.username,
                "role": m.role.value,
                "joined_at": m.joined_at
            }
            for m in members
        ]
    }

@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can invite members"
        )
    
    # Find user by email
    invited_user = get_user_by_email(db, invite.email)
    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. They must register first."
        )
    
    # Check if already a member
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == invited_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a team member"
        )
    
    # Add member
    new_member = TeamMember(
        team_id=team_id,
        user_id=invited_user.id,
        role=TeamRole[invite.role.upper()],
        invited_by_id=current_user.id
    )
    db.add(new_member)
    db.commit()
    
    logger.info(f"User {current_user.id} added {invited_user.id} to team {team_id}")
    
    return {
        "message": "Member added successfully",
        "user_id": invited_user.id,
        "email": invited_user.email,
        "role": invite.role
    }

@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a member from team"""
    # Check if user is admin or owner
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can remove members"
        )
    
    # Can't remove the owner
    team = db.query(Team).filter(Team.id == team_id).first()
    if team.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the team owner"
        )
    
    # Remove member
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}