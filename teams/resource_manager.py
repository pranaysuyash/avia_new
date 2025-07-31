"""
Shared resource library system for team workspaces
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_
from database.models import Team, TeamMember, TeamRole, User, Transcript, Project, Annotation
import logging

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages shared resources within team workspaces"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_team_resources(
        self,
        team_id: int,
        user_id: int,
        resource_type: str = "all", 
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Transcript]:
        """Get team resources with filtering"""
        # Check if user has access to team
        if not self._is_team_member(team_id, user_id):
            return []
        
        query = self.session.query(Transcript).filter_by(team_id=team_id)
        
        # Filter by project if specified
        if project_id:
            # Note: This would require adding project_id to Transcript model
            # For now, we'll return all team transcripts
            pass
        
        # Filter by resource type
        if resource_type != "all":
            # Could filter by file type, duration, etc.
            pass
        
        transcripts = query.options(
            joinedload(Transcript.user),
            joinedload(Transcript.annotations)
        ).order_by(desc(Transcript.created_at)).limit(limit).all()
        
        return transcripts
    
    def share_transcript_with_team(
        self,
        transcript_id: int,
        team_id: int,
        user_id: int,
        notification_manager=None
    ) -> Tuple[bool, str]:
        """Share a personal transcript with a team"""
        # Get transcript
        transcript = self.session.query(Transcript).filter_by(
            id=transcript_id,
            user_id=user_id
        ).first()
        
        if not transcript:
            return False, "Transcript not found or you don't have permission"
        
        # Check if user is team member
        if not self._is_team_member(team_id, user_id):
            return False, "You are not a member of this team"
        
        # Check if already shared with team
        if transcript.team_id == team_id:
            return False, "Transcript is already shared with this team"
        
        # Share transcript
        transcript.team_id = team_id
        self.session.commit()
        
        # Notify team members if notification manager provided
        if notification_manager:
            team = self.session.query(Team).filter_by(id=team_id).first()
            user = self.session.query(User).filter_by(id=user_id).first()
            
            notification_manager.notify_team_members(
                team_id=team_id,
                notification_type='team_announcement',
                title=f"New resource shared in {team.name}",
                message=f"{user.username} shared '{transcript.title}' with the team",
                from_user_id=user_id
            )
        
        logger.info(f"Transcript {transcript_id} shared with team {team_id} by user {user_id}")
        return True, "Transcript shared with team successfully"
    
    def unshare_transcript_from_team(
        self,
        transcript_id: int,
        user_id: int
    ) -> Tuple[bool, str]:
        """Remove transcript from team sharing"""
        transcript = self.session.query(Transcript).filter_by(
            id=transcript_id,
            user_id=user_id
        ).first()
        
        if not transcript:
            return False, "Transcript not found or you don't have permission"
        
        if not transcript.team_id:
            return False, "Transcript is not shared with any team"
        
        transcript.team_id = None
        self.session.commit()
        
        logger.info(f"Transcript {transcript_id} unshared from team by user {user_id}")
        return True, "Transcript removed from team"
    
    def create_team_project(
        self,
        team_id: int,
        user_id: int,
        name: str,
        description: str = "",
        notification_manager=None
    ) -> Tuple[bool, str, Optional[Project]]:
        """Create a new project within a team"""
        # Check permissions
        if not self._can_create_projects(team_id, user_id):
            return False, "You don't have permission to create projects", None
        
        # Check if project name exists
        existing = self.session.query(Project).filter(
            Project.team_id == team_id,
            Project.name == name,
            Project.is_archived == False
        ).first()
        
        if existing:
            return False, f"Project '{name}' already exists in this team", None
        
        # Create project
        project = Project(
            team_id=team_id,
            name=name,
            description=description,
            created_by_id=user_id
        )
        
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        
        # Notify team members
        if notification_manager:
            team = self.session.query(Team).filter_by(id=team_id).first()
            user = self.session.query(User).filter_by(id=user_id).first()
            
            notification_manager.notify_team_members(
                team_id=team_id,
                notification_type='team_announcement',
                title=f"New project created in {team.name}",
                message=f"{user.username} created project '{name}'",
                from_user_id=user_id
            )
        
        logger.info(f"Project '{name}' created in team {team_id} by user {user_id}")
        return True, "Project created successfully", project
    
    def get_team_projects(
        self,
        team_id: int,
        user_id: int,
        include_archived: bool = False
    ) -> List[Project]:
        """Get all projects in a team"""
        if not self._is_team_member(team_id, user_id):
            return []
        
        query = self.session.query(Project).filter_by(team_id=team_id)
        
        if not include_archived:
            query = query.filter_by(is_archived=False)
        
        projects = query.options(
            joinedload(Project.created_by)
        ).order_by(Project.name).all()
        
        return projects
    
    def archive_project(
        self,
        project_id: int,
        user_id: int
    ) -> Tuple[bool, str]:
        """Archive a project"""
        project = self.session.query(Project).filter_by(id=project_id).first()
        
        if not project:
            return False, "Project not found"
        
        # Check permissions (owner or team admin/owner)
        if not self._can_manage_project(project.team_id, user_id, project.created_by_id):
            return False, "You don't have permission to archive this project"
        
        project.is_archived = True
        project.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"Project {project_id} archived by user {user_id}")
        return True, "Project archived successfully"
    
    def get_resource_statistics(
        self,
        team_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Get resource statistics for a team"""
        if not self._is_team_member(team_id, user_id):
            return {}
        
        # Basic counts
        transcript_count = self.session.query(Transcript).filter_by(team_id=team_id).count()
        project_count = self.session.query(Project).filter(
            Project.team_id == team_id,
            Project.is_archived == False
        ).count()
        
        # Storage usage
        transcripts = self.session.query(Transcript).filter_by(team_id=team_id).all()
        total_size_mb = sum(t.file_size or 0 for t in transcripts) / (1024 * 1024)
        total_duration = sum(t.duration or 0 for t in transcripts)
        
        # Recent activity
        recent_transcripts = self.session.query(Transcript).filter_by(
            team_id=team_id
        ).order_by(desc(Transcript.created_at)).limit(5).all()
        
        # Most active contributors
        contributor_stats = self.session.query(
            User.username,
            func.count(Transcript.id).label('transcript_count')
        ).join(Transcript).filter(
            Transcript.team_id == team_id
        ).group_by(User.id).order_by(desc('transcript_count')).limit(5).all()
        
        # Annotation activity
        annotation_count = self.session.query(Annotation).join(Transcript).filter(
            Transcript.team_id == team_id
        ).count()
        
        return {
            'transcript_count': transcript_count,
            'project_count': project_count,
            'total_size_mb': total_size_mb,
            'total_duration_hours': total_duration / 3600 if total_duration else 0,
            'annotation_count': annotation_count,
            'recent_transcripts': [
                {
                    'title': t.title,
                    'author': t.user.username,
                    'created_at': t.created_at
                }
                for t in recent_transcripts
            ],
            'top_contributors': [
                {
                    'username': username,
                    'transcript_count': count
                }
                for username, count in contributor_stats
            ]
        }
    
    def search_team_resources(
        self,
        team_id: int,
        user_id: int,
        query: str,
        resource_type: str = "all",
        limit: int = 20
    ) -> List[Transcript]:
        """Search resources within a team"""
        if not self._is_team_member(team_id, user_id):
            return []
        
        # Basic text search in title and content
        search_query = self.session.query(Transcript).filter(
            Transcript.team_id == team_id,
            or_(
                Transcript.title.ilike(f"%{query}%"),
                Transcript.content.ilike(f"%{query}%"),
                Transcript.summary.ilike(f"%{query}%")
            )
        )
        
        transcripts = search_query.options(
            joinedload(Transcript.user)
        ).order_by(desc(Transcript.created_at)).limit(limit).all()
        
        return transcripts
    
    def get_resource_access_log(
        self,
        transcript_id: int,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get access log for a resource (basic implementation)"""
        transcript = self.session.query(Transcript).filter_by(id=transcript_id).first()
        
        if not transcript or not transcript.team_id:
            return []
        
        if not self._is_team_member(transcript.team_id, user_id):
            return []
        
        # In a full implementation, this would track actual access events
        # For now, return annotation events as a proxy for activity
        annotations = self.session.query(Annotation).filter_by(
            transcript_id=transcript_id
        ).options(joinedload(Annotation.user)).order_by(
            desc(Annotation.created_at)
        ).limit(limit).all()
        
        access_log = []
        for ann in annotations:
            access_log.append({
                'user': ann.user.username,
                'action': 'annotation',
                'timestamp': ann.created_at,
                'details': f"Added annotation: {ann.content[:50]}..."
            })
        
        return access_log
    
    def _is_team_member(self, team_id: int, user_id: int) -> bool:
        """Check if user is a team member"""
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        return membership is not None
    
    def _can_create_projects(self, team_id: int, user_id: int) -> bool:
        """Check if user can create projects in team"""
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        if not membership:
            return False
        
        # All members except viewers can create projects
        return membership.role != TeamRole.VIEWER
    
    def _can_manage_project(self, team_id: int, user_id: int, project_creator_id: int) -> bool:
        """Check if user can manage a project"""
        membership = self.session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()
        
        if not membership:
            return False
        
        # Project creator, team admins, or team owner can manage
        if user_id == project_creator_id:
            return True
        
        return membership.role in [TeamRole.OWNER, TeamRole.ADMIN]
    
    def get_user_team_contributions(
        self,
        team_id: int,
        user_id: int,
        target_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get contribution statistics for a user in a team"""
        if not self._is_team_member(team_id, user_id):
            return {}
        
        target_id = target_user_id or user_id
        
        # Transcript contributions
        transcript_count = self.session.query(Transcript).filter(
            Transcript.team_id == team_id,
            Transcript.user_id == target_id
        ).count()
        
        # Annotation contributions
        annotation_count = self.session.query(Annotation).join(Transcript).filter(
            Transcript.team_id == team_id,
            Annotation.user_id == target_id
        ).count()
        
        # Project contributions
        project_count = self.session.query(Project).filter(
            Project.team_id == team_id,
            Project.created_by_id == target_id,
            Project.is_archived == False
        ).count()
        
        # Recent activity
        recent_transcripts = self.session.query(Transcript).filter(
            Transcript.team_id == team_id,
            Transcript.user_id == target_id
        ).order_by(desc(Transcript.created_at)).limit(5).all()
        
        return {
            'transcript_count': transcript_count,
            'annotation_count': annotation_count,
            'project_count': project_count,
            'recent_transcripts': [
                {
                    'title': t.title,
                    'created_at': t.created_at
                }
                for t in recent_transcripts
            ]
        }