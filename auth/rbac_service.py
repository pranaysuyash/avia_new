#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Service
Implements granular permissions for resources and actions
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.models import User, UserRole, Team, TeamMember, TeamRole, Transcript, SharedLink, SharePermission

logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions"""
    # Transcript permissions
    TRANSCRIPT_CREATE = "transcript:create"
    TRANSCRIPT_READ = "transcript:read"
    TRANSCRIPT_UPDATE = "transcript:update"
    TRANSCRIPT_DELETE = "transcript:delete"
    TRANSCRIPT_SHARE = "transcript:share"
    TRANSCRIPT_EXPORT = "transcript:export"
    
    # Team permissions
    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_INVITE = "team:invite"
    TEAM_REMOVE_MEMBER = "team:remove_member"
    
    # User management permissions
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"
    
    # API permissions
    API_KEY_CREATE = "api:key:create"
    API_KEY_READ = "api:key:read"
    API_KEY_DELETE = "api:key:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_STATS = "system:stats"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_CONFIG = "system:config"
    
    # Feature permissions
    FEATURE_ADVANCED_ANALYSIS = "feature:advanced_analysis"
    FEATURE_BATCH_PROCESSING = "feature:batch_processing"
    FEATURE_CUSTOM_MODELS = "feature:custom_models"
    FEATURE_UNLIMITED_STORAGE = "feature:unlimited_storage"

class ResourceType(Enum):
    """Resource types in the system"""
    TRANSCRIPT = "transcript"
    TEAM = "team"
    USER = "user"
    API_KEY = "api_key"
    SYSTEM = "system"

class RolePermissions:
    """Define permissions for each role"""
    
    # System-wide role permissions
    SYSTEM_ROLES = {
        UserRole.ADMIN: {
            # Admins have all permissions
            Permission.TRANSCRIPT_CREATE,
            Permission.TRANSCRIPT_READ,
            Permission.TRANSCRIPT_UPDATE,
            Permission.TRANSCRIPT_DELETE,
            Permission.TRANSCRIPT_SHARE,
            Permission.TRANSCRIPT_EXPORT,
            Permission.TEAM_CREATE,
            Permission.TEAM_READ,
            Permission.TEAM_UPDATE,
            Permission.TEAM_DELETE,
            Permission.TEAM_INVITE,
            Permission.TEAM_REMOVE_MEMBER,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.USER_MANAGE_ROLES,
            Permission.API_KEY_CREATE,
            Permission.API_KEY_READ,
            Permission.API_KEY_DELETE,
            Permission.SYSTEM_ADMIN,
            Permission.SYSTEM_STATS,
            Permission.SYSTEM_LOGS,
            Permission.SYSTEM_CONFIG,
            Permission.FEATURE_ADVANCED_ANALYSIS,
            Permission.FEATURE_BATCH_PROCESSING,
            Permission.FEATURE_CUSTOM_MODELS,
            Permission.FEATURE_UNLIMITED_STORAGE,
        },
        UserRole.USER: {
            # Regular users
            Permission.TRANSCRIPT_CREATE,
            Permission.TRANSCRIPT_READ,  # Own transcripts
            Permission.TRANSCRIPT_UPDATE,  # Own transcripts
            Permission.TRANSCRIPT_DELETE,  # Own transcripts
            Permission.TRANSCRIPT_SHARE,
            Permission.TRANSCRIPT_EXPORT,
            Permission.TEAM_CREATE,
            Permission.TEAM_READ,  # Teams they belong to
            Permission.API_KEY_CREATE,
            Permission.API_KEY_READ,  # Own keys
            Permission.API_KEY_DELETE,  # Own keys
            Permission.FEATURE_ADVANCED_ANALYSIS,  # Based on subscription
        },
        UserRole.VIEWER: {
            # View-only users
            Permission.TRANSCRIPT_READ,  # Shared transcripts
            Permission.TRANSCRIPT_EXPORT,  # If allowed
            Permission.TEAM_READ,  # Teams they belong to
        }
    }
    
    # Team-specific role permissions
    TEAM_ROLES = {
        TeamRole.OWNER: {
            # Team owners have full control
            Permission.TRANSCRIPT_CREATE,
            Permission.TRANSCRIPT_READ,
            Permission.TRANSCRIPT_UPDATE,
            Permission.TRANSCRIPT_DELETE,
            Permission.TRANSCRIPT_SHARE,
            Permission.TRANSCRIPT_EXPORT,
            Permission.TEAM_READ,
            Permission.TEAM_UPDATE,
            Permission.TEAM_DELETE,
            Permission.TEAM_INVITE,
            Permission.TEAM_REMOVE_MEMBER,
        },
        TeamRole.ADMIN: {
            # Team admins can manage content and members
            Permission.TRANSCRIPT_CREATE,
            Permission.TRANSCRIPT_READ,
            Permission.TRANSCRIPT_UPDATE,
            Permission.TRANSCRIPT_DELETE,
            Permission.TRANSCRIPT_SHARE,
            Permission.TRANSCRIPT_EXPORT,
            Permission.TEAM_READ,
            Permission.TEAM_UPDATE,
            Permission.TEAM_INVITE,
            Permission.TEAM_REMOVE_MEMBER,
        },
        TeamRole.MEMBER: {
            # Team members can work with content
            Permission.TRANSCRIPT_CREATE,
            Permission.TRANSCRIPT_READ,
            Permission.TRANSCRIPT_UPDATE,
            Permission.TRANSCRIPT_SHARE,
            Permission.TRANSCRIPT_EXPORT,
            Permission.TEAM_READ,
        },
        TeamRole.VIEWER: {
            # Team viewers have read-only access
            Permission.TRANSCRIPT_READ,
            Permission.TRANSCRIPT_EXPORT,
            Permission.TEAM_READ,
        }
    }

class RBACService:
    """Role-Based Access Control Service"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for a user"""
        permissions = set()
        
        # Add system role permissions
        if user.role in RolePermissions.SYSTEM_ROLES:
            permissions.update(RolePermissions.SYSTEM_ROLES[user.role])
        
        # Add subscription-based permissions
        permissions.update(self._get_subscription_permissions(user))
        
        return permissions
    
    def get_user_team_permissions(self, user: User, team_id: int) -> Set[Permission]:
        """Get user's permissions within a specific team"""
        db = self._get_db()
        try:
            # Get team membership
            membership = db.query(TeamMember).filter(
                and_(
                    TeamMember.user_id == user.id,
                    TeamMember.team_id == team_id
                )
            ).first()
            
            if not membership:
                return set()
            
            # Get team role permissions
            if membership.role in RolePermissions.TEAM_ROLES:
                return RolePermissions.TEAM_ROLES[membership.role]
            
            return set()
            
        finally:
            db.close()
    
    def check_permission(self, user: User, permission: Permission,
                        resource_type: Optional[ResourceType] = None,
                        resource_id: Optional[int] = None) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user: User object
            permission: Permission to check
            resource_type: Type of resource (for context-specific checks)
            resource_id: ID of specific resource
        
        Returns:
            bool: True if user has permission
        """
        # System admins have all permissions
        if user.role == UserRole.ADMIN:
            return True
        
        # Check system-wide permissions
        user_permissions = self.get_user_permissions(user)
        if permission in user_permissions:
            # For resource-specific permissions, need additional checks
            if resource_type and resource_id:
                return self._check_resource_permission(
                    user, permission, resource_type, resource_id
                )
            return True
        
        # Check team-based permissions if resource is team-scoped
        if resource_type and resource_id:
            return self._check_resource_permission(
                user, permission, resource_type, resource_id
            )
        
        return False
    
    def _check_resource_permission(self, user: User, permission: Permission,
                                 resource_type: ResourceType, resource_id: int) -> bool:
        """Check permission for a specific resource"""
        db = self._get_db()
        try:
            if resource_type == ResourceType.TRANSCRIPT:
                return self._check_transcript_permission(db, user, permission, resource_id)
            elif resource_type == ResourceType.TEAM:
                return self._check_team_permission(db, user, permission, resource_id)
            elif resource_type == ResourceType.USER:
                return self._check_user_permission(db, user, permission, resource_id)
            elif resource_type == ResourceType.API_KEY:
                return self._check_api_key_permission(db, user, permission, resource_id)
            
            return False
            
        finally:
            db.close()
    
    def _check_transcript_permission(self, db: Session, user: User,
                                   permission: Permission, transcript_id: int) -> bool:
        """Check permission for a specific transcript"""
        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            return False
        
        # Owner has full permissions
        if transcript.user_id == user.id:
            return permission in {
                Permission.TRANSCRIPT_READ,
                Permission.TRANSCRIPT_UPDATE,
                Permission.TRANSCRIPT_DELETE,
                Permission.TRANSCRIPT_SHARE,
                Permission.TRANSCRIPT_EXPORT
            }
        
        # Check team permissions if transcript belongs to a team
        if transcript.team_id:
            team_permissions = self.get_user_team_permissions(user, transcript.team_id)
            if permission in team_permissions:
                return True
        
        # Check shared links
        if permission in {Permission.TRANSCRIPT_READ, Permission.TRANSCRIPT_EXPORT}:
            # Check if user has access via shared link
            shared_link = db.query(SharedLink).filter(
                and_(
                    SharedLink.transcript_id == transcript_id,
                    SharedLink.is_active == True
                )
            ).first()
            
            if shared_link:
                if permission == Permission.TRANSCRIPT_READ:
                    return shared_link.permission in {SharePermission.VIEW, SharePermission.COMMENT, SharePermission.EDIT}
                elif permission == Permission.TRANSCRIPT_EXPORT:
                    return shared_link.permission in {SharePermission.EDIT}
        
        return False
    
    def _check_team_permission(self, db: Session, user: User,
                             permission: Permission, team_id: int) -> bool:
        """Check permission for a specific team"""
        # Get team
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            return False
        
        # Owner has full permissions
        if team.owner_id == user.id:
            return True
        
        # Check team membership
        team_permissions = self.get_user_team_permissions(user, team_id)
        return permission in team_permissions
    
    def _check_user_permission(self, db: Session, user: User,
                             permission: Permission, target_user_id: int) -> bool:
        """Check permission for user management"""
        # Users can read and update their own profile
        if target_user_id == user.id:
            return permission in {Permission.USER_READ, Permission.USER_UPDATE}
        
        # Only admins can manage other users
        return user.role == UserRole.ADMIN
    
    def _check_api_key_permission(self, db: Session, user: User,
                                permission: Permission, api_key_id: int) -> bool:
        """Check permission for API key management"""
        from database.models import APIKey
        
        # Get API key
        api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not api_key:
            return False
        
        # Users can manage their own API keys
        if api_key.user_id == user.id:
            return permission in {Permission.API_KEY_READ, Permission.API_KEY_DELETE}
        
        # Only admins can manage other users' API keys
        return user.role == UserRole.ADMIN
    
    def _get_subscription_permissions(self, user: User) -> Set[Permission]:
        """Get permissions based on user's subscription tier"""
        # This would integrate with your subscription system
        # For now, return basic permissions
        permissions = set()
        
        # Example subscription tiers
        subscription_tier = getattr(user, 'subscription_tier', 'free')
        
        if subscription_tier == 'pro':
            permissions.update({
                Permission.FEATURE_ADVANCED_ANALYSIS,
                Permission.FEATURE_BATCH_PROCESSING,
            })
        elif subscription_tier == 'enterprise':
            permissions.update({
                Permission.FEATURE_ADVANCED_ANALYSIS,
                Permission.FEATURE_BATCH_PROCESSING,
                Permission.FEATURE_CUSTOM_MODELS,
                Permission.FEATURE_UNLIMITED_STORAGE,
            })
        
        return permissions
    
    def get_user_accessible_transcripts(self, user: User, db: Session) -> List[int]:
        """Get all transcript IDs accessible to a user"""
        accessible_ids = set()
        
        # Own transcripts
        own_transcripts = db.query(Transcript.id).filter(
            Transcript.user_id == user.id
        ).all()
        accessible_ids.update([t[0] for t in own_transcripts])
        
        # Team transcripts
        team_memberships = db.query(TeamMember.team_id).filter(
            TeamMember.user_id == user.id
        ).all()
        
        if team_memberships:
            team_ids = [tm[0] for tm in team_memberships]
            team_transcripts = db.query(Transcript.id).filter(
                Transcript.team_id.in_(team_ids)
            ).all()
            accessible_ids.update([t[0] for t in team_transcripts])
        
        # Shared transcripts (via links)
        # This would need to check active shared links
        
        return list(accessible_ids)
    
    def filter_by_permission(self, user: User, items: List[Any],
                           permission: Permission,
                           resource_type: ResourceType,
                           id_field: str = 'id') -> List[Any]:
        """Filter a list of items by permission"""
        return [
            item for item in items
            if self.check_permission(
                user, permission, resource_type,
                getattr(item, id_field)
            )
        ]
    
    def require_permission(self, permission: Permission,
                         resource_type: Optional[ResourceType] = None,
                         resource_id_param: Optional[str] = None):
        """
        Decorator to require permission for a function
        
        Args:
            permission: Required permission
            resource_type: Type of resource being accessed
            resource_id_param: Parameter name containing resource ID
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user from kwargs (assumes it's passed as 'current_user')
                user = kwargs.get('current_user')
                if not user:
                    raise PermissionError("Authentication required")
                
                # Extract resource ID if specified
                resource_id = None
                if resource_id_param:
                    resource_id = kwargs.get(resource_id_param)
                
                # Check permission
                if not self.check_permission(user, permission, resource_type, resource_id):
                    raise PermissionError(f"Permission denied: {permission.value}")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_role_permissions_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """Get a matrix of all roles and their permissions for UI display"""
        matrix = {
            "system_roles": {},
            "team_roles": {}
        }
        
        # System roles
        for role, permissions in RolePermissions.SYSTEM_ROLES.items():
            matrix["system_roles"][role.value] = [p.value for p in permissions]
        
        # Team roles
        for role, permissions in RolePermissions.TEAM_ROLES.items():
            matrix["team_roles"][role.value] = [p.value for p in permissions]
        
        return matrix


# Global RBAC instance (initialize with your DB session factory)
rbac_service = None

def init_rbac(db_session_factory):
    """Initialize RBAC service"""
    global rbac_service
    rbac_service = RBACService(db_session_factory)
    return rbac_service