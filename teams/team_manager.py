"""
Team management system for workspace collaboration
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from database.models import Team, TeamMember, TeamRole, User, Transcript, Project, Notification
import logging

logger = logging.getLogger(__name__)


class TeamManager:
    """Manages team workspaces, membership, and permissions"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_team(
        self,
        name: str,
        description: str,
        owner_id: int,
        max_members: int = 10,
        storage_quota_mb: int = 5000
    ) -> Team:
        """Create a new team workspace"""
        # Validate team name uniqueness for the user
        existing = self.session.query(Team).filter(
            Team.name == name,
            Team.owner_id == owner_id
        ).first()
        
        if existing:
            raise ValueError(f"Team with name '{name}' already exists for this user")
        
        # Create team
        team = Team(
            name=name,
            description=description,
            owner_id=owner_id,
            max_members=max_members,
            storage_quota_mb=storage_quota_mb
        )
        
        self.session.add(team)
        self.session.flush()  # Get the team ID
        
        # Add owner as team member with OWNER role
        owner_membership = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role=TeamRole.OWNER,
            invited_by_id=owner_id
        )
        
        self.session.add(owner_membership)
        self.session.commit()
        self.session.refresh(team)
        
        logger.info(f"Created team '{name}' (ID: {team.id}) for user {owner_id}")
        return team
    
    def get_user_teams(self, user_id: int) -> List[Team]:
        """Get all teams a user is a member of"""
        teams = self.session.query(Team).join(TeamMember).filter(
            TeamMember.user_id == user_id,
            Team.is_active == True
        ).options(
            joinedload(Team.owner),
            joinedload(Team.members).joinedload(TeamMember.user)
        ).order_by(Team.name).all()
        
        return teams
    
    def get_owned_teams(self, user_id: int) -> List[Team]:
        """Get teams owned by a user"""
        teams = self.session.query(Team).filter(
            Team.owner_id == user_id,
            Team.is_active == True
        ).options(
            joinedload(Team.members).joinedload(TeamMember.user)
        ).order_by(Team.name).all()
        
        return teams
    
    def get_team(self, team_id: int, user_id: Optional[int] = None) -> Optional[Team]:
        """Get a team with member verification"""
        query = self.session.query(Team).options(
            joinedload(Team.owner),
            joinedload(Team.members).joinedload(TeamMember.user),
            joinedload(Team.projects)
        ).filter(Team.id == team_id, Team.is_active == True)
        
        team = query.first()
        
        if team and user_id:
            # Verify user is a member
            if not self.is_team_member(team_id, user_id):
                return None
        
        return team
    
    def is_team_member(self, team_id: int, user_id: int) -> bool:
        """Check if user is a member of the team"""
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        return membership is not None
    
    def get_user_role_in_team(self, team_id: int, user_id: int) -> Optional[TeamRole]:
        """Get user's role in a team"""
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        return membership.role if membership else None
    
    def can_user_perform_action(
        self,
        team_id: int,
        user_id: int,
        action: str
    ) -> bool:
        """Check if user can perform a specific action in the team"""
        role = self.get_user_role_in_team(team_id, user_id)
        if not role:
            return False
        
        # Define permission matrix
        permissions = {
            TeamRole.OWNER: {
                'invite_members', 'remove_members', 'change_roles', 'delete_team',
                'edit_team', 'create_projects', 'delete_projects', 'view_analytics',
                'manage_storage', 'view_transcripts', 'edit_transcripts', 'create_transcripts'
            },
            TeamRole.ADMIN: {
                'invite_members', 'remove_members', 'create_projects', 'edit_team',
                'view_analytics', 'view_transcripts', 'edit_transcripts', 'create_transcripts'
            },
            TeamRole.MEMBER: {
                'view_transcripts', 'edit_transcripts', 'create_transcripts',
                'create_projects'
            },
            TeamRole.VIEWER: {
                'view_transcripts'
            }
        }
        
        return action in permissions.get(role, set())
    
    def invite_member(
        self,
        team_id: int,
        inviter_id: int,
        email: str,
        role: TeamRole = TeamRole.MEMBER,
        notification_manager=None
    ) -> Tuple[bool, str, Optional[TeamMember]]:
        """Invite a user to join the team"""
        # Check if inviter has permission
        if not self.can_user_perform_action(team_id, inviter_id, 'invite_members'):
            return False, "You don't have permission to invite members", None
        
        # Get team and check limits
        team = self.get_team(team_id)
        if not team:
            return False, "Team not found", None
        
        current_member_count = len(team.members)
        if current_member_count >= team.max_members:
            return False, f"Team has reached maximum member limit ({team.max_members})", None
        
        # Find user by email
        user = self.session.query(User).filter_by(email=email).first()
        if not user:
            return False, f"No user found with email {email}", None
        
        # Check if already a member
        if self.is_team_member(team_id, user.id):
            return False, f"{user.username} is already a member of this team", None
        
        # Create membership
        membership = TeamMember(
            team_id=team_id,
            user_id=user.id,
            role=role,
            invited_by_id=inviter_id
        )
        
        self.session.add(membership)
        self.session.commit()
        self.session.refresh(membership)
        
        # Send notification if manager provided
        if notification_manager:
            inviter = self.session.query(User).filter_by(id=inviter_id).first()
            notification_manager.notify_team_invitation(
                invited_user_id=user.id,
                inviter_id=inviter_id,
                team_id=team_id,
                team_name=team.name,
                role=role.value
            )
        
        logger.info(f"User {user.username} invited to team {team.name} by {inviter_id}")
        return True, f"{user.username} successfully added to the team", membership
    
    def remove_member(
        self,
        team_id: int,
        remover_id: int,
        member_user_id: int
    ) -> Tuple[bool, str]:
        """Remove a member from the team"""
        # Check permissions
        if not self.can_user_perform_action(team_id, remover_id, 'remove_members'):
            return False, "You don't have permission to remove members"
        
        # Can't remove the owner
        team = self.get_team(team_id)
        if team and team.owner_id == member_user_id:
            return False, "Cannot remove the team owner"
        
        # Can't remove yourself (use leave_team instead)
        if remover_id == member_user_id:
            return False, "Use leave team function to remove yourself"
        
        # Find and remove membership
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == member_user_id
        ).first()
        
        if not membership:
            return False, "User is not a member of this team"
        
        user = membership.user
        self.session.delete(membership)
        self.session.commit()
        
        logger.info(f"User {user.username} removed from team {team_id} by {remover_id}")
        return True, f"{user.username} removed from the team"
    
    def leave_team(self, team_id: int, user_id: int) -> Tuple[bool, str]:
        """Allow a user to leave a team"""
        # Owner cannot leave (must transfer ownership first)
        team = self.get_team(team_id)
        if team and team.owner_id == user_id:
            return False, "Team owner cannot leave. Transfer ownership first."
        
        # Find and remove membership
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        if not membership:
            return False, "You are not a member of this team"
        
        self.session.delete(membership)
        self.session.commit()
        
        logger.info(f"User {user_id} left team {team_id}")
        return True, "Successfully left the team"
    
    def change_member_role(
        self,
        team_id: int,
        changer_id: int,
        member_user_id: int,
        new_role: TeamRole
    ) -> Tuple[bool, str]:
        """Change a member's role in the team"""
        # Check permissions
        if not self.can_user_perform_action(team_id, changer_id, 'change_roles'):
            return False, "You don't have permission to change roles"
        
        # Can't change owner role
        team = self.get_team(team_id)
        if team and team.owner_id == member_user_id:
            return False, "Cannot change the team owner's role"
        
        # Find membership
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == member_user_id
        ).first()
        
        if not membership:
            return False, "User is not a member of this team"
        
        old_role = membership.role
        membership.role = new_role
        self.session.commit()
        
        logger.info(f"User {member_user_id} role changed from {old_role.value} to {new_role.value} in team {team_id}")
        return True, f"Role changed from {old_role.value} to {new_role.value}"
    
    def update_team(
        self,
        team_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        max_members: Optional[int] = None,
        storage_quota_mb: Optional[int] = None
    ) -> Tuple[bool, str, Optional[Team]]:
        """Update team settings"""
        # Check permissions
        if not self.can_user_perform_action(team_id, user_id, 'edit_team'):
            return False, "You don't have permission to edit team settings", None
        
        team = self.get_team(team_id)
        if not team:
            return False, "Team not found", None
        
        # Update fields
        if name is not None:
            # Check name uniqueness for the owner
            existing = self.session.query(Team).filter(
                Team.name == name,
                Team.owner_id == team.owner_id,
                Team.id != team_id
            ).first()
            
            if existing:
                return False, f"Team name '{name}' already exists", None
            
            team.name = name
        
        if description is not None:
            team.description = description
        
        if max_members is not None:
            current_member_count = len(team.members)
            if max_members < current_member_count:
                return False, f"Cannot reduce limit below current member count ({current_member_count})", None
            team.max_members = max_members
        
        if storage_quota_mb is not None:
            if storage_quota_mb < team.storage_used_mb:
                return False, f"Cannot reduce quota below current usage ({team.storage_used_mb:.1f} MB)", None
            team.storage_quota_mb = storage_quota_mb
        
        team.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(team)
        
        logger.info(f"Team {team_id} updated by user {user_id}")
        return True, "Team settings updated successfully", team
    
    def delete_team(self, team_id: int, user_id: int) -> Tuple[bool, str]:
        """Delete a team (only owner can do this)"""
        team = self.get_team(team_id)
        if not team:
            return False, "Team not found"
        
        if team.owner_id != user_id:
            return False, "Only the team owner can delete the team"
        
        # Archive instead of hard delete to preserve data integrity
        team.is_active = False
        team.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"Team {team_id} deleted by owner {user_id}")
        return True, "Team deleted successfully"
    
    def get_team_analytics(self, team_id: int, user_id: int) -> Dict[str, Any]:
        """Get team analytics and statistics"""
        if not self.can_user_perform_action(team_id, user_id, 'view_analytics'):
            return {}
        
        team = self.get_team(team_id)
        if not team:
            return {}
        
        # Basic stats
        member_count = len(team.members)
        transcript_count = self.session.query(Transcript).filter_by(team_id=team_id).count()
        project_count = len(team.projects)
        
        # Recent activity
        recent_transcripts = self.session.query(Transcript).filter_by(
            team_id=team_id
        ).order_by(desc(Transcript.created_at)).limit(5).all()
        
        # Storage usage
        storage_used = team.storage_used_mb
        storage_quota = team.storage_quota_mb
        storage_percentage = (storage_used / storage_quota * 100) if storage_quota > 0 else 0
        
        # Member activity
        member_activity = []
        for member in team.members:
            user_transcript_count = self.session.query(Transcript).filter(
                Transcript.team_id == team_id,
                Transcript.user_id == member.user_id
            ).count()
            
            member_activity.append({
                'user': member.user.username,
                'role': member.role.value,
                'joined_at': member.joined_at,
                'transcript_count': user_transcript_count
            })
        
        return {
            'team_name': team.name,
            'member_count': member_count,
            'transcript_count': transcript_count,
            'project_count': project_count,
            'storage_used_mb': storage_used,
            'storage_quota_mb': storage_quota,
            'storage_percentage': storage_percentage,
            'recent_transcripts': [
                {
                    'title': t.title,
                    'created_at': t.created_at,
                    'author': t.user.username
                }
                for t in recent_transcripts
            ],
            'member_activity': member_activity
        }
    
    def create_project(
        self,
        team_id: int,
        user_id: int,
        name: str,
        description: str = ""
    ) -> Tuple[bool, str, Optional[Project]]:
        """Create a new project within a team"""
        if not self.can_user_perform_action(team_id, user_id, 'create_projects'):
            return False, "You don't have permission to create projects", None
        
        # Check if project name exists in team
        existing = self.session.query(Project).filter(
            Project.team_id == team_id,
            Project.name == name,
            Project.is_archived == False
        ).first()
        
        if existing:
            return False, f"Project '{name}' already exists in this team", None
        
        project = Project(
            team_id=team_id,
            name=name,
            description=description,
            created_by_id=user_id
        )
        
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        
        logger.info(f"Project '{name}' created in team {team_id} by user {user_id}")
        return True, "Project created successfully", project
    
    def get_team_projects(self, team_id: int, user_id: int) -> List[Project]:
        """Get all projects in a team"""
        if not self.is_team_member(team_id, user_id):
            return []
        
        projects = self.session.query(Project).filter(
            Project.team_id == team_id,
            Project.is_archived == False
        ).options(
            joinedload(Project.created_by)
        ).order_by(Project.name).all()
        
        return projects
    
    def get_team_transcripts(
        self,
        team_id: int,
        user_id: int,
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Transcript]:
        """Get transcripts in a team, optionally filtered by project"""
        if not self.can_user_perform_action(team_id, user_id, 'view_transcripts'):
            return []
        
        query = self.session.query(Transcript).filter_by(team_id=team_id)
        
        if project_id:
            # Note: This would require a project_id field in Transcript model
            # For now, we'll just get all team transcripts
            pass
        
        transcripts = query.options(
            joinedload(Transcript.user)
        ).order_by(desc(Transcript.created_at)).limit(limit).all()
        
        return transcripts