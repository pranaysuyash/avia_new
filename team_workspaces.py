#!/usr/bin/env python3
"""
Team Workspaces and Collaboration Features (Task 50)
Enterprise-grade team management, workspaces, and collaboration with RBAC
"""

import streamlit as st
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import secrets
from enum import Enum

logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions"""
    # Content permissions
    CONTENT_VIEW = "content:view"
    CONTENT_CREATE = "content:create"
    CONTENT_EDIT = "content:edit"
    CONTENT_DELETE = "content:delete"
    CONTENT_SHARE = "content:share"
    
    # Workspace permissions
    WORKSPACE_VIEW = "workspace:view"
    WORKSPACE_CREATE = "workspace:create"
    WORKSPACE_EDIT = "workspace:edit"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_MANAGE = "workspace:manage"
    
    # Team permissions
    TEAM_VIEW = "team:view"
    TEAM_INVITE = "team:invite"
    TEAM_MANAGE = "team:manage"
    TEAM_ADMIN = "team:admin"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_BILLING = "system:billing"
    SYSTEM_ANALYTICS = "system:analytics"
    
    # API permissions
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"

class Role(Enum):
    """User roles with permission sets"""
    VIEWER = "viewer"
    MEMBER = "member"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"
    SYSTEM_ADMIN = "system_admin"

@dataclass
class Team:
    """Team data model"""
    team_id: str
    name: str
    description: str
    owner_id: str
    created_at: str
    updated_at: str
    is_active: bool
    settings: Dict[str, Any]
    subscription_tier: str  # 'free', 'pro', 'enterprise'
    member_limit: int
    storage_limit: int  # in bytes
    usage_stats: Dict[str, Any]

@dataclass
class Workspace:
    """Workspace data model"""
    workspace_id: str
    team_id: str
    name: str
    description: str
    created_by: str
    created_at: str
    updated_at: str
    is_active: bool
    settings: Dict[str, Any]
    content_count: int
    storage_used: int  # in bytes

@dataclass
class TeamMember:
    """Team member data model"""
    member_id: str
    team_id: str
    user_id: str
    username: str
    email: str
    role: str
    permissions: List[str]
    invited_by: str
    joined_at: str
    last_active: Optional[str]
    is_active: bool

@dataclass
class Invitation:
    """Team invitation data model"""
    invitation_id: str
    team_id: str
    email: str
    role: str
    invited_by: str
    created_at: str
    expires_at: str
    accepted_at: Optional[str]
    status: str  # 'pending', 'accepted', 'declined', 'expired'
    token: str

@dataclass
class ContentItem:
    """Content item in workspace"""
    content_id: str
    workspace_id: str
    team_id: str
    created_by: str
    title: str
    content_type: str  # 'transcription', 'analysis', 'export'
    file_path: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    is_shared: bool
    permissions: Dict[str, List[str]]  # user_id -> permissions
    tags: List[str]
    size: int  # in bytes

class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
    
    def _initialize_role_permissions(self) -> Dict[Role, List[Permission]]:
        """Initialize role-permission mappings"""
        return {
            Role.VIEWER: [
                Permission.CONTENT_VIEW,
                Permission.WORKSPACE_VIEW,
                Permission.TEAM_VIEW,
                Permission.API_READ
            ],
            Role.MEMBER: [
                Permission.CONTENT_VIEW,
                Permission.CONTENT_CREATE,
                Permission.CONTENT_SHARE,
                Permission.WORKSPACE_VIEW,
                Permission.TEAM_VIEW,
                Permission.API_READ
            ],
            Role.EDITOR: [
                Permission.CONTENT_VIEW,
                Permission.CONTENT_CREATE,
                Permission.CONTENT_EDIT,
                Permission.CONTENT_SHARE,
                Permission.WORKSPACE_VIEW,
                Permission.WORKSPACE_CREATE,
                Permission.TEAM_VIEW,
                Permission.TEAM_INVITE,
                Permission.API_READ,
                Permission.API_WRITE
            ],
            Role.ADMIN: [
                Permission.CONTENT_VIEW,
                Permission.CONTENT_CREATE,
                Permission.CONTENT_EDIT,
                Permission.CONTENT_DELETE,
                Permission.CONTENT_SHARE,
                Permission.WORKSPACE_VIEW,
                Permission.WORKSPACE_CREATE,
                Permission.WORKSPACE_EDIT,
                Permission.WORKSPACE_DELETE,
                Permission.TEAM_VIEW,
                Permission.TEAM_INVITE,
                Permission.TEAM_MANAGE,
                Permission.API_READ,
                Permission.API_WRITE
            ],
            Role.OWNER: [
                # Owners have all permissions except system admin
                Permission.CONTENT_VIEW,
                Permission.CONTENT_CREATE,
                Permission.CONTENT_EDIT,
                Permission.CONTENT_DELETE,
                Permission.CONTENT_SHARE,
                Permission.WORKSPACE_VIEW,
                Permission.WORKSPACE_CREATE,
                Permission.WORKSPACE_EDIT,
                Permission.WORKSPACE_DELETE,
                Permission.WORKSPACE_MANAGE,
                Permission.TEAM_VIEW,
                Permission.TEAM_INVITE,
                Permission.TEAM_MANAGE,
                Permission.TEAM_ADMIN,
                Permission.SYSTEM_BILLING,
                Permission.SYSTEM_ANALYTICS,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.API_ADMIN
            ],
            Role.SYSTEM_ADMIN: [
                # System admins have all permissions
                *list(Permission)
            ]
        }
    
    def get_user_permissions(self, role: str) -> List[str]:
        """Get permissions for a user role"""
        try:
            role_enum = Role(role)
            permissions = self.role_permissions.get(role_enum, [])
            return [p.value for p in permissions]
        except ValueError:
            return []
    
    def has_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        user_permissions = self.get_user_permissions(user_role)
        return required_permission in user_permissions
    
    def can_access_content(self, user_role: str, content_permissions: Dict[str, List[str]], 
                          user_id: str, action: str) -> bool:
        """Check if user can access specific content"""
        # Check role-based permissions first
        if self.has_permission(user_role, action):
            return True
        
        # Check content-specific permissions
        user_content_permissions = content_permissions.get(user_id, [])
        return action in user_content_permissions

class TeamWorkspaceDatabase:
    """Database manager for teams and workspaces"""
    
    def __init__(self, db_path: str = "team_workspaces.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Teams table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS teams (
                        team_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        owner_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        settings TEXT DEFAULT '{}',
                        subscription_tier TEXT DEFAULT 'free',
                        member_limit INTEGER DEFAULT 5,
                        storage_limit INTEGER DEFAULT 1073741824,
                        usage_stats TEXT DEFAULT '{}'
                    )
                """)
                
                # Workspaces table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workspaces (
                        workspace_id TEXT PRIMARY KEY,
                        team_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        settings TEXT DEFAULT '{}',
                        content_count INTEGER DEFAULT 0,
                        storage_used INTEGER DEFAULT 0,
                        FOREIGN KEY (team_id) REFERENCES teams (team_id)
                    )
                """)
                
                # Team members table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS team_members (
                        member_id TEXT PRIMARY KEY,
                        team_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        role TEXT NOT NULL,
                        permissions TEXT DEFAULT '[]',
                        invited_by TEXT NOT NULL,
                        joined_at TEXT NOT NULL,
                        last_active TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (team_id) REFERENCES teams (team_id),
                        UNIQUE(team_id, user_id)
                    )
                """)
                
                # Invitations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS invitations (
                        invitation_id TEXT PRIMARY KEY,
                        team_id TEXT NOT NULL,
                        email TEXT NOT NULL,
                        role TEXT NOT NULL,
                        invited_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        accepted_at TEXT,
                        status TEXT DEFAULT 'pending',
                        token TEXT NOT NULL,
                        FOREIGN KEY (team_id) REFERENCES teams (team_id)
                    )
                """)
                
                # Content items table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_items (
                        content_id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        team_id TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        file_path TEXT,
                        metadata TEXT DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_shared BOOLEAN DEFAULT 0,
                        permissions TEXT DEFAULT '{}',
                        tags TEXT DEFAULT '[]',
                        size INTEGER DEFAULT 0,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces (workspace_id),
                        FOREIGN KEY (team_id) REFERENCES teams (team_id)
                    )
                """)
                
                # Activity log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team_id TEXT,
                        workspace_id TEXT,
                        user_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        target_type TEXT,
                        target_id TEXT,
                        details TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing team workspace database: {e}")
            raise
    
    def create_team(self, team: Team) -> bool:
        """Create a new team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO teams (
                        team_id, name, description, owner_id, created_at, updated_at,
                        is_active, settings, subscription_tier, member_limit, 
                        storage_limit, usage_stats
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    team.team_id, team.name, team.description, team.owner_id,
                    team.created_at, team.updated_at, team.is_active,
                    json.dumps(team.settings), team.subscription_tier,
                    team.member_limit, team.storage_limit, json.dumps(team.usage_stats)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            return False
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_team(row)
                return None
        except Exception as e:
            logger.error(f"Error getting team: {e}")
            return None
    
    def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.* FROM teams t
                    JOIN team_members tm ON t.team_id = tm.team_id
                    WHERE tm.user_id = ? AND tm.is_active = 1 AND t.is_active = 1
                """, (user_id,))
                rows = cursor.fetchall()
                
                return [self._row_to_team(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user teams: {e}")
            return []
    
    def create_workspace(self, workspace: Workspace) -> bool:
        """Create a new workspace"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO workspaces (
                        workspace_id, team_id, name, description, created_by,
                        created_at, updated_at, is_active, settings,
                        content_count, storage_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workspace.workspace_id, workspace.team_id, workspace.name,
                    workspace.description, workspace.created_by, workspace.created_at,
                    workspace.updated_at, workspace.is_active, json.dumps(workspace.settings),
                    workspace.content_count, workspace.storage_used
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            return False
    
    def get_team_workspaces(self, team_id: str) -> List[Workspace]:
        """Get all workspaces for a team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM workspaces WHERE team_id = ? AND is_active = 1",
                    (team_id,)
                )
                rows = cursor.fetchall()
                
                return [self._row_to_workspace(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting team workspaces: {e}")
            return []
    
    def add_team_member(self, member: TeamMember) -> bool:
        """Add member to team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO team_members (
                        member_id, team_id, user_id, username, email, role,
                        permissions, invited_by, joined_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    member.member_id, member.team_id, member.user_id, member.username,
                    member.email, member.role, json.dumps(member.permissions),
                    member.invited_by, member.joined_at, member.is_active
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            return False
    
    def get_team_members(self, team_id: str) -> List[TeamMember]:
        """Get all members of a team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM team_members WHERE team_id = ? AND is_active = 1",
                    (team_id,)
                )
                rows = cursor.fetchall()
                
                return [self._row_to_team_member(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting team members: {e}")
            return []
    
    def create_invitation(self, invitation: Invitation) -> bool:
        """Create team invitation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO invitations (
                        invitation_id, team_id, email, role, invited_by,
                        created_at, expires_at, status, token
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invitation.invitation_id, invitation.team_id, invitation.email,
                    invitation.role, invitation.invited_by, invitation.created_at,
                    invitation.expires_at, invitation.status, invitation.token
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating invitation: {e}")
            return False
    
    def get_pending_invitations(self, team_id: str) -> List[Invitation]:
        """Get pending invitations for a team"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM invitations WHERE team_id = ? AND status = 'pending'",
                    (team_id,)
                )
                rows = cursor.fetchall()
                
                return [self._row_to_invitation(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting pending invitations: {e}")
            return []
    
    def log_activity(self, team_id: Optional[str], workspace_id: Optional[str], 
                    user_id: str, action: str, target_type: Optional[str] = None,
                    target_id: Optional[str] = None, details: str = ""):
        """Log team/workspace activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO activity_log (
                        team_id, workspace_id, user_id, action, target_type,
                        target_id, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    team_id, workspace_id, user_id, action, target_type,
                    target_id, details, datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def _row_to_team(self, row) -> Team:
        """Convert database row to Team object"""
        return Team(
            team_id=row[0],
            name=row[1],
            description=row[2],
            owner_id=row[3],
            created_at=row[4],
            updated_at=row[5],
            is_active=bool(row[6]),
            settings=json.loads(row[7]) if row[7] else {},
            subscription_tier=row[8],
            member_limit=row[9],
            storage_limit=row[10],
            usage_stats=json.loads(row[11]) if row[11] else {}
        )
    
    def _row_to_workspace(self, row) -> Workspace:
        """Convert database row to Workspace object"""
        return Workspace(
            workspace_id=row[0],
            team_id=row[1],
            name=row[2],
            description=row[3],
            created_by=row[4],
            created_at=row[5],
            updated_at=row[6],
            is_active=bool(row[7]),
            settings=json.loads(row[8]) if row[8] else {},
            content_count=row[9],
            storage_used=row[10]
        )
    
    def _row_to_team_member(self, row) -> TeamMember:
        """Convert database row to TeamMember object"""
        return TeamMember(
            member_id=row[0],
            team_id=row[1],
            user_id=row[2],
            username=row[3],
            email=row[4],
            role=row[5],
            permissions=json.loads(row[6]) if row[6] else [],
            invited_by=row[7],
            joined_at=row[8],
            last_active=row[9],
            is_active=bool(row[10])
        )
    
    def _row_to_invitation(self, row) -> Invitation:
        """Convert database row to Invitation object"""
        return Invitation(
            invitation_id=row[0],
            team_id=row[1],
            email=row[2],
            role=row[3],
            invited_by=row[4],
            created_at=row[5],
            expires_at=row[6],
            accepted_at=row[7],
            status=row[8],
            token=row[9]
        )

class TeamWorkspaceManager:
    """Main team workspace management system"""
    
    def __init__(self):
        self.db = TeamWorkspaceDatabase()
        self.rbac = RBACManager()
    
    def create_team(self, owner_id: str, name: str, description: str = "", 
                   subscription_tier: str = "free") -> Tuple[bool, str, Optional[Team]]:
        """Create a new team"""
        try:
            # Validate input
            if not name or len(name.strip()) < 2:
                return False, "Team name must be at least 2 characters", None
            
            # Set limits based on subscription tier
            tier_limits = {
                'free': {'members': 5, 'storage': 1024**3},  # 1GB
                'pro': {'members': 25, 'storage': 10 * 1024**3},  # 10GB
                'enterprise': {'members': 100, 'storage': 100 * 1024**3}  # 100GB
            }
            
            limits = tier_limits.get(subscription_tier, tier_limits['free'])
            
            # Create team
            team_id = f"team_{secrets.token_urlsafe(16)}"
            team = Team(
                team_id=team_id,
                name=name.strip(),
                description=description.strip(),
                owner_id=owner_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                is_active=True,
                settings={},
                subscription_tier=subscription_tier,
                member_limit=limits['members'],
                storage_limit=limits['storage'],
                usage_stats={'members': 1, 'workspaces': 0, 'storage_used': 0}
            )
            
            if self.db.create_team(team):
                # Add owner as team member
                owner_member = TeamMember(
                    member_id=f"member_{secrets.token_urlsafe(16)}",
                    team_id=team_id,
                    user_id=owner_id,
                    username="Owner",  # Would get from user database
                    email="owner@example.com",  # Would get from user database
                    role=Role.OWNER.value,
                    permissions=self.rbac.get_user_permissions(Role.OWNER.value),
                    invited_by=owner_id,
                    joined_at=datetime.now().isoformat(),
                    last_active=None,
                    is_active=True
                )
                
                if self.db.add_team_member(owner_member):
                    # Log activity
                    self.db.log_activity(team_id, None, owner_id, "TEAM_CREATED", 
                                       "team", team_id, f"Created team: {name}")
                    
                    return True, "Team created successfully", team
                else:
                    return False, "Failed to add owner to team", None
            else:
                return False, "Failed to create team", None
                
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            return False, "Team creation failed due to system error", None
    
    def create_workspace(self, team_id: str, creator_id: str, name: str, 
                        description: str = "") -> Tuple[bool, str, Optional[Workspace]]:
        """Create a new workspace"""
        try:
            # Validate input
            if not name or len(name.strip()) < 2:
                return False, "Workspace name must be at least 2 characters", None
            
            # Check if user has permission
            if not self._user_can_create_workspace(creator_id, team_id):
                return False, "Insufficient permissions to create workspace", None
            
            # Create workspace
            workspace_id = f"workspace_{secrets.token_urlsafe(16)}"
            workspace = Workspace(
                workspace_id=workspace_id,
                team_id=team_id,
                name=name.strip(),
                description=description.strip(),
                created_by=creator_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                is_active=True,
                settings={},
                content_count=0,
                storage_used=0
            )
            
            if self.db.create_workspace(workspace):
                # Log activity
                self.db.log_activity(team_id, workspace_id, creator_id, 
                                   "WORKSPACE_CREATED", "workspace", workspace_id,
                                   f"Created workspace: {name}")
                
                return True, "Workspace created successfully", workspace
            else:
                return False, "Failed to create workspace", None
                
        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            return False, "Workspace creation failed due to system error", None
    
    def invite_user(self, team_id: str, inviter_id: str, email: str, 
                   role: str) -> Tuple[bool, str]:
        """Invite user to team"""
        try:
            # Validate role
            try:
                Role(role)
            except ValueError:
                return False, "Invalid role specified"
            
            # Check if inviter has permission
            if not self._user_can_invite(inviter_id, team_id):
                return False, "Insufficient permissions to invite users"
            
            # Check team member limit
            team = self.db.get_team(team_id)
            if not team:
                return False, "Team not found"
            
            current_members = len(self.db.get_team_members(team_id))
            if current_members >= team.member_limit:
                return False, f"Team member limit ({team.member_limit}) reached"
            
            # Check if user already invited or member
            existing_invitations = self.db.get_pending_invitations(team_id)
            if any(inv.email == email for inv in existing_invitations):
                return False, "User already has pending invitation"
            
            existing_members = self.db.get_team_members(team_id)
            if any(member.email == email for member in existing_members):
                return False, "User is already a team member"
            
            # Create invitation
            invitation_id = f"invite_{secrets.token_urlsafe(16)}"
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(days=7)).isoformat()
            
            invitation = Invitation(
                invitation_id=invitation_id,
                team_id=team_id,
                email=email,
                role=role,
                invited_by=inviter_id,
                created_at=datetime.now().isoformat(),
                expires_at=expires_at,
                accepted_at=None,
                status="pending",
                token=token
            )
            
            if self.db.create_invitation(invitation):
                # Log activity
                self.db.log_activity(team_id, None, inviter_id, "USER_INVITED",
                                   "invitation", invitation_id,
                                   f"Invited {email} as {role}")
                
                return True, f"Invitation sent to {email}"
            else:
                return False, "Failed to create invitation"
                
        except Exception as e:
            logger.error(f"Error inviting user: {e}")
            return False, "Invitation failed due to system error"
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user's team and workspace context"""
        try:
            teams = self.db.get_user_teams(user_id)
            context = {
                'teams': [],
                'workspaces': [],
                'permissions': set(),
                'current_team': None,
                'current_workspace': None
            }
            
            for team in teams:
                # Get user's role in team
                members = self.db.get_team_members(team.team_id)
                user_member = next((m for m in members if m.user_id == user_id), None)
                
                if user_member:
                    team_data = {
                        'team': team,
                        'role': user_member.role,
                        'permissions': user_member.permissions,
                        'workspaces': self.db.get_team_workspaces(team.team_id)
                    }
                    context['teams'].append(team_data)
                    context['permissions'].update(user_member.permissions)
                    context['workspaces'].extend(team_data['workspaces'])
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {'teams': [], 'workspaces': [], 'permissions': set()}
    
    def _user_can_create_workspace(self, user_id: str, team_id: str) -> bool:
        """Check if user can create workspace in team"""
        try:
            members = self.db.get_team_members(team_id)
            user_member = next((m for m in members if m.user_id == user_id), None)
            
            if not user_member:
                return False
            
            return self.rbac.has_permission(user_member.role, Permission.WORKSPACE_CREATE.value)
            
        except Exception as e:
            logger.error(f"Error checking workspace creation permission: {e}")
            return False
    
    def _user_can_invite(self, user_id: str, team_id: str) -> bool:
        """Check if user can invite others to team"""
        try:
            members = self.db.get_team_members(team_id)
            user_member = next((m for m in members if m.user_id == user_id), None)
            
            if not user_member:
                return False
            
            return self.rbac.has_permission(user_member.role, Permission.TEAM_INVITE.value)
            
        except Exception as e:
            logger.error(f"Error checking invitation permission: {e}")
            return False

class TeamWorkspaceUI:
    """Streamlit UI for team workspaces and collaboration"""
    
    def __init__(self):
        self.manager = TeamWorkspaceManager()
    
    def render_team_selector(self, user_id: str) -> Optional[str]:
        """Render team selection interface"""
        context = self.manager.get_user_context(user_id)
        
        if not context['teams']:
            st.info("You're not a member of any teams yet.")
            if st.button("Create Your First Team"):
                return "create_team"
            return None
        
        # Team selection
        team_options = {f"{team['team'].name} ({team['role']})": team['team'].team_id 
                       for team in context['teams']}
        
        selected_team_display = st.selectbox(
            "Select Team",
            options=list(team_options.keys()),
            key="team_selector"
        )
        
        if selected_team_display:
            return team_options[selected_team_display]
        
        return None
    
    def render_workspace_selector(self, team_id: str, user_id: str) -> Optional[str]:
        """Render workspace selection interface"""
        workspaces = self.manager.db.get_team_workspaces(team_id)
        
        if not workspaces:
            st.info("No workspaces in this team yet.")
            if st.button("Create First Workspace"):
                return "create_workspace"
            return None
        
        # Workspace selection
        workspace_options = {ws.name: ws.workspace_id for ws in workspaces}
        
        selected_workspace_name = st.selectbox(
            "Select Workspace",
            options=list(workspace_options.keys()),
            key="workspace_selector"
        )
        
        if selected_workspace_name:
            return workspace_options[selected_workspace_name]
        
        return None
    
    def render_team_creation(self, user_id: str):
        """Render team creation interface"""
        st.subheader("Create New Team")
        
        with st.form("create_team_form"):
            name = st.text_input("Team Name", max_chars=100)
            description = st.text_area("Description (Optional)", max_chars=500)
            
            subscription_tier = st.selectbox(
                "Subscription Tier",
                options=["free", "pro", "enterprise"],
                format_func=lambda x: {
                    "free": "Free (5 members, 1GB storage)",
                    "pro": "Pro (25 members, 10GB storage)",
                    "enterprise": "Enterprise (100 members, 100GB storage)"
                }[x]
            )
            
            submitted = st.form_submit_button("Create Team")
            
            if submitted:
                if not name or len(name.strip()) < 2:
                    st.error("Team name must be at least 2 characters")
                    return
                
                success, message, team = self.manager.create_team(
                    user_id, name, description, subscription_tier
                )
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    def render_workspace_creation(self, team_id: str, user_id: str):
        """Render workspace creation interface"""
        st.subheader("Create New Workspace")
        
        with st.form("create_workspace_form"):
            name = st.text_input("Workspace Name", max_chars=100)
            description = st.text_area("Description (Optional)", max_chars=500)
            
            submitted = st.form_submit_button("Create Workspace")
            
            if submitted:
                if not name or len(name.strip()) < 2:
                    st.error("Workspace name must be at least 2 characters")
                    return
                
                success, message, workspace = self.manager.create_workspace(
                    team_id, user_id, name, description
                )
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    def render_team_management(self, team_id: str, user_id: str):
        """Render team management interface"""
        team = self.manager.db.get_team(team_id)
        if not team:
            st.error("Team not found")
            return
        
        st.subheader(f"Team: {team.name}")
        
        # Team info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Members", team.usage_stats.get('members', 0))
        
        with col2:
            st.metric("Workspaces", len(self.manager.db.get_team_workspaces(team_id)))
        
        with col3:
            storage_used_mb = team.usage_stats.get('storage_used', 0) / (1024 * 1024)
            storage_limit_mb = team.storage_limit / (1024 * 1024)
            st.metric("Storage", f"{storage_used_mb:.1f}MB / {storage_limit_mb:.0f}MB")
        
        # Team members
        st.subheader("Team Members")
        members = self.manager.db.get_team_members(team_id)
        
        if members:
            member_data = []
            for member in members:
                member_data.append({
                    "Username": member.username,
                    "Email": member.email,
                    "Role": member.role.title(),
                    "Joined": member.joined_at[:10],
                    "Status": "Active" if member.is_active else "Inactive"
                })
            
            st.dataframe(member_data, use_container_width=True)
        else:
            st.info("No team members found")
        
        # Invite new member
        if self.manager._user_can_invite(user_id, team_id):
            st.subheader("Invite New Member")
            
            with st.form("invite_member_form"):
                email = st.text_input("Email Address")
                role = st.selectbox(
                    "Role",
                    options=[Role.VIEWER.value, Role.MEMBER.value, Role.EDITOR.value, Role.ADMIN.value],
                    format_func=lambda x: x.title()
                )
                
                submitted = st.form_submit_button("Send Invitation")
                
                if submitted:
                    if not email or "@" not in email:
                        st.error("Please enter a valid email address")
                        return
                    
                    success, message = self.manager.invite_user(team_id, user_id, email, role)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Pending invitations
        invitations = self.manager.db.get_pending_invitations(team_id)
        if invitations:
            st.subheader("Pending Invitations")
            
            invitation_data = []
            for inv in invitations:
                invitation_data.append({
                    "Email": inv.email,
                    "Role": inv.role.title(),
                    "Invited": inv.created_at[:10],
                    "Expires": inv.expires_at[:10],
                    "Status": inv.status.title()
                })
            
            st.dataframe(invitation_data, use_container_width=True)
    
    def render_workspace_content(self, workspace_id: str, user_id: str):
        """Render workspace content and collaboration features"""
        # This would integrate with existing content management
        st.subheader("Workspace Content")
        st.info("Content management integration would go here")
        
        # Placeholder for content items
        st.write("Recent Content:")
        st.write("- Transcription_2024_01_15.json")
        st.write("- Meeting_Analysis_Q1.pdf")
        st.write("- Project_Summary.docx")
        
        # Collaboration features
        st.subheader("Collaboration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Share Content"):
                st.info("Content sharing dialog would open here")
        
        with col2:
            if st.button("Real-time Collaboration"):
                st.info("Real-time collaboration features would activate here")

def main():
    """Main function for testing team workspaces"""
    st.set_page_config(
        page_title="Team Workspaces & Collaboration",
        page_icon="👥",
        layout="wide"
    )
    
    st.title("👥 Team Workspaces & Collaboration")
    st.markdown("---")
    
    # Initialize UI
    ui = TeamWorkspaceUI()
    
    # Mock user ID (in real app, get from authentication)
    if 'user_id' not in st.session_state:
        st.session_state.user_id = f"user_{secrets.token_urlsafe(8)}"
    
    user_id = st.session_state.user_id
    
    # Navigation
    tab1, tab2, tab3, tab4 = st.tabs(["Teams", "Workspaces", "Management", "Content"])
    
    with tab1:
        st.header("Your Teams")
        
        # Team selection or creation
        selected_team = ui.render_team_selector(user_id)
        
        if selected_team == "create_team":
            ui.render_team_creation(user_id)
        elif selected_team:
            st.session_state.current_team = selected_team
            st.success(f"Selected team: {selected_team}")
    
    with tab2:
        st.header("Workspaces")
        
        if 'current_team' in st.session_state:
            team_id = st.session_state.current_team
            
            # Workspace selection or creation
            selected_workspace = ui.render_workspace_selector(team_id, user_id)
            
            if selected_workspace == "create_workspace":
                ui.render_workspace_creation(team_id, user_id)
            elif selected_workspace:
                st.session_state.current_workspace = selected_workspace
                st.success(f"Selected workspace: {selected_workspace}")
        else:
            st.info("Please select a team first")
    
    with tab3:
        st.header("Team Management")
        
        if 'current_team' in st.session_state:
            ui.render_team_management(st.session_state.current_team, user_id)
        else:
            st.info("Please select a team first")
    
    with tab4:
        st.header("Workspace Content")
        
        if 'current_workspace' in st.session_state:
            ui.render_workspace_content(st.session_state.current_workspace, user_id)
        else:
            st.info("Please select a workspace first")
    
    # Debug info
    with st.expander("Debug Info"):
        st.write("Session State:", st.session_state)
        st.write("User ID:", user_id)

if __name__ == "__main__":
    main()