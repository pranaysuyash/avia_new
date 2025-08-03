#!/usr/bin/env python3
"""
Team Management API Endpoints with RBAC
Handles team creation, membership, and permissions
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from datetime import datetime
import logging

from database.models import Team, TeamMember, TeamRole, User, Transcript
from database.connection import get_db
from auth.rbac_service import Permission, ResourceType
from api.middleware.rbac_middleware import require_permission, require_team_permission
from api.auth_routes_enhanced import get_current_user_flexible
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["teams"])

# Request/Response Models

class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_members: int = Field(10, ge=2, le=100)
    storage_quota_mb: int = Field(5000, ge=100, le=100000)

class TeamUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=2, le=100)
    storage_quota_mb: Optional[int] = Field(None, ge=100, le=100000)
    is_active: Optional[bool] = None

class TeamInviteRequest(BaseModel):
    email: str = Field(..., description="Email of user to invite")
    role: TeamRole = Field(TeamRole.MEMBER, description="Role to assign")

class TeamMemberUpdateRequest(BaseModel):
    role: TeamRole = Field(..., description="New role for member")

class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_active: bool
    max_members: int
    storage_quota_mb: int
    storage_used_mb: float
    member_count: int
    transcript_count: int
    created_at: datetime
    updated_at: datetime
    owner: Dict[str, Any]
    user_role: Optional[str]

class TeamMemberResponse(BaseModel):
    id: int
    user: Dict[str, Any]
    role: str
    joined_at: datetime
    invited_by: Optional[Dict[str, Any]]

# Endpoints

@router.post("/", response_model=TeamResponse)
@require_permission(Permission.TEAM_CREATE)
async def create_team(
    request: TeamCreateRequest,
    current_user: User = Depends()
):
    """Create new team"""
    db = next(get_db())
    
    # Check if user already owns too many teams (limit to 5)
    owned_teams_count = db.query(func.count(Team.id)).filter(
        Team.owner_id == current_user.id
    ).scalar()
    
    if owned_teams_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only own up to 5 teams"
        )
    
    # Create team
    team = Team(
        name=request.name,
        description=request.description,
        owner_id=current_user.id,
        max_members=request.max_members,
        storage_quota_mb=request.storage_quota_mb
    )
    
    db.add(team)
    db.commit()
    db.refresh(team)
    
    # Add owner as team member
    team_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER,
        invited_by_id=current_user.id
    )
    
    db.add(team_member)
    db.commit()
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        is_active=team.is_active,
        max_members=team.max_members,
        storage_quota_mb=team.storage_quota_mb,
        storage_used_mb=team.storage_used_mb,
        member_count=1,
        transcript_count=0,
        created_at=team.created_at,
        updated_at=team.updated_at,
        owner={
            "id": current_user.id,
            "username": current_user.username,
            "full_name": current_user.full_name
        },
        user_role=TeamRole.OWNER.value
    )

@router.get("/", response_model=List[TeamResponse])
@require_permission(Permission.TEAM_READ)
async def list_teams(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends()
):
    """List user's teams"""
    db = next(get_db())
    
    # Get teams where user is a member
    teams_query = db.query(Team).join(TeamMember).filter(
        TeamMember.user_id == current_user.id
    )
    
    teams = teams_query.offset(skip).limit(limit).all()
    
    results = []
    for team in teams:
        # Get member count
        member_count = db.query(func.count(TeamMember.id)).filter(
            TeamMember.team_id == team.id
        ).scalar()
        
        # Get transcript count
        transcript_count = db.query(func.count(Transcript.id)).filter(
            Transcript.team_id == team.id
        ).scalar()
        
        # Get user's role
        user_membership = db.query(TeamMember).filter(
            and_(
                TeamMember.team_id == team.id,
                TeamMember.user_id == current_user.id
            )
        ).first()
        
        results.append(TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            is_active=team.is_active,
            max_members=team.max_members,
            storage_quota_mb=team.storage_quota_mb,
            storage_used_mb=team.storage_used_mb,
            member_count=member_count,
            transcript_count=transcript_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
            owner={
                "id": team.owner.id,
                "username": team.owner.username,
                "full_name": team.owner.full_name
            },
            user_role=user_membership.role.value if user_membership else None
        ))
    
    return results

@router.get("/{team_id}", response_model=TeamResponse)
@require_permission(Permission.TEAM_READ, ResourceType.TEAM, "team_id")
async def get_team(
    team_id: int,
    current_user: User = Depends()
):
    """Get team details"""
    db = next(get_db())
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Get counts
    member_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.team_id == team.id
    ).scalar()
    
    transcript_count = db.query(func.count(Transcript.id)).filter(
        Transcript.team_id == team.id
    ).scalar()
    
    # Get user's role
    user_membership = db.query(TeamMember).filter(
        and_(
            TeamMember.team_id == team.id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        is_active=team.is_active,
        max_members=team.max_members,
        storage_quota_mb=team.storage_quota_mb,
        storage_used_mb=team.storage_used_mb,
        member_count=member_count,
        transcript_count=transcript_count,
        created_at=team.created_at,
        updated_at=team.updated_at,
        owner={
            "id": team.owner.id,
            "username": team.owner.username,
            "full_name": team.owner.full_name
        },
        user_role=user_membership.role.value if user_membership else None
    )

@router.put("/{team_id}", response_model=TeamResponse)
@require_permission(Permission.TEAM_UPDATE, ResourceType.TEAM, "team_id")
async def update_team(
    team_id: int,
    request: TeamUpdateRequest,
    current_user: User = Depends()
):
    """Update team settings"""
    db = next(get_db())
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Update fields
    if request.name is not None:
        team.name = request.name
    if request.description is not None:
        team.description = request.description
    if request.max_members is not None:
        # Check current member count
        member_count = db.query(func.count(TeamMember.id)).filter(
            TeamMember.team_id == team.id
        ).scalar()
        
        if request.max_members < member_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce max members below current count ({member_count})"
            )
        
        team.max_members = request.max_members
    if request.storage_quota_mb is not None:
        team.storage_quota_mb = request.storage_quota_mb
    if request.is_active is not None:
        team.is_active = request.is_active
    
    team.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(team)
    
    # Get updated counts
    member_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.team_id == team.id
    ).scalar()
    
    transcript_count = db.query(func.count(Transcript.id)).filter(
        Transcript.team_id == team.id
    ).scalar()
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        owner_id=team.owner_id,
        is_active=team.is_active,
        max_members=team.max_members,
        storage_quota_mb=team.storage_quota_mb,
        storage_used_mb=team.storage_used_mb,
        member_count=member_count,
        transcript_count=transcript_count,
        created_at=team.created_at,
        updated_at=team.updated_at,
        owner={
            "id": team.owner.id,
            "username": team.owner.username,
            "full_name": team.owner.full_name
        },
        user_role=TeamRole.OWNER.value if team.owner_id == current_user.id else TeamRole.ADMIN.value
    )

@router.delete("/{team_id}")
@require_permission(Permission.TEAM_DELETE, ResourceType.TEAM, "team_id")
async def delete_team(
    team_id: int,
    current_user: User = Depends()
):
    """Delete team (owner only)"""
    db = next(get_db())
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Only owner can delete
    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can delete the team"
        )
    
    # Check if team has transcripts
    transcript_count = db.query(func.count(Transcript.id)).filter(
        Transcript.team_id == team.id
    ).scalar()
    
    if transcript_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete team with {transcript_count} transcripts. Please delete or transfer them first."
        )
    
    db.delete(team)
    db.commit()
    
    return {"message": "Team deleted successfully"}

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
@require_team_permission(Permission.TEAM_READ)
async def list_team_members(
    team_id: int,
    current_user: User = Depends()
):
    """List team members"""
    db = next(get_db())
    
    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id
    ).all()
    
    results = []
    for member in members:
        results.append(TeamMemberResponse(
            id=member.id,
            user={
                "id": member.user.id,
                "username": member.user.username,
                "email": member.user.email,
                "full_name": member.user.full_name
            },
            role=member.role.value,
            joined_at=member.joined_at,
            invited_by={
                "id": member.invited_by.id,
                "username": member.invited_by.username,
                "full_name": member.invited_by.full_name
            } if member.invited_by else None
        ))
    
    return results

@router.post("/{team_id}/invite", response_model=Dict[str, Any])
@require_team_permission(Permission.TEAM_INVITE)
async def invite_team_member(
    team_id: int,
    request: TeamInviteRequest,
    current_user: User = Depends()
):
    """Invite user to team"""
    db = next(get_db())
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check member limit
    member_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.team_id == team_id
    ).scalar()
    
    if member_count >= team.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team has reached maximum members limit ({team.max_members})"
        )
    
    # Find user by email
    invited_user = db.query(User).filter(User.email == request.email).first()
    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this email"
        )
    
    # Check if already member
    existing_member = db.query(TeamMember).filter(
        and_(
            TeamMember.team_id == team_id,
            TeamMember.user_id == invited_user.id
        )
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a team member"
        )
    
    # Add member
    new_member = TeamMember(
        team_id=team_id,
        user_id=invited_user.id,
        role=request.role,
        invited_by_id=current_user.id
    )
    
    db.add(new_member)
    db.commit()
    
    # TODO: Send invitation email
    
    return {
        "message": f"User {invited_user.username} invited to team",
        "member": {
            "id": new_member.id,
            "user_id": invited_user.id,
            "username": invited_user.username,
            "role": request.role.value
        }
    }

@router.put("/{team_id}/members/{member_id}", response_model=TeamMemberResponse)
@require_team_permission(Permission.TEAM_INVITE)  # Admin+ can manage roles
async def update_team_member(
    team_id: int,
    member_id: int,
    request: TeamMemberUpdateRequest,
    current_user: User = Depends()
):
    """Update team member role"""
    db = next(get_db())
    
    # Get member
    member = db.query(TeamMember).filter(
        and_(
            TeamMember.id == member_id,
            TeamMember.team_id == team_id
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    # Cannot change owner role
    if member.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner role. Transfer ownership instead."
        )
    
    # Cannot promote to owner
    if request.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot promote to owner. Transfer ownership instead."
        )
    
    member.role = request.role
    db.commit()
    db.refresh(member)
    
    return TeamMemberResponse(
        id=member.id,
        user={
            "id": member.user.id,
            "username": member.user.username,
            "email": member.user.email,
            "full_name": member.user.full_name
        },
        role=member.role.value,
        joined_at=member.joined_at,
        invited_by={
            "id": member.invited_by.id,
            "username": member.invited_by.username,
            "full_name": member.invited_by.full_name
        } if member.invited_by else None
    )

@router.delete("/{team_id}/members/{member_id}")
@require_team_permission(Permission.TEAM_REMOVE_MEMBER)
async def remove_team_member(
    team_id: int,
    member_id: int,
    current_user: User = Depends()
):
    """Remove team member"""
    db = next(get_db())
    
    # Get member
    member = db.query(TeamMember).filter(
        and_(
            TeamMember.id == member_id,
            TeamMember.team_id == team_id
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    # Cannot remove owner
    if member.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove team owner"
        )
    
    # Members can remove themselves
    if member.user_id != current_user.id:
        # Otherwise need admin+ permissions (already checked by decorator)
        pass
    
    db.delete(member)
    db.commit()
    
    return {"message": "Team member removed successfully"}