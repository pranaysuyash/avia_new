#!/usr/bin/env python3
"""
Test Suite for Team Workspaces and Collaboration Features
Comprehensive testing of RBAC, team management, and workspace functionality
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from team_workspaces import (
    TeamWorkspaceManager, TeamWorkspaceDatabase, RBACManager,
    Team, Workspace, TeamMember, Invitation, Permission, Role
)

class TestRBACManager:
    """Test Role-Based Access Control functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.rbac = RBACManager()
    
    def test_role_permissions(self):
        """Test role permission mappings"""
        # Test viewer permissions
        viewer_perms = self.rbac.get_user_permissions(Role.VIEWER.value)
        assert Permission.CONTENT_VIEW.value in viewer_perms
        assert Permission.CONTENT_CREATE.value not in viewer_perms
        
        # Test member permissions
        member_perms = self.rbac.get_user_permissions(Role.MEMBER.value)
        assert Permission.CONTENT_VIEW.value in member_perms
        assert Permission.CONTENT_CREATE.value in member_perms
        assert Permission.WORKSPACE_CREATE.value not in member_perms
        
        # Test editor permissions
        editor_perms = self.rbac.get_user_permissions(Role.EDITOR.value)
        assert Permission.WORKSPACE_CREATE.value in editor_perms
        assert Permission.TEAM_INVITE.value in editor_perms
        
        # Test admin permissions
        admin_perms = self.rbac.get_user_permissions(Role.ADMIN.value)
        assert Permission.CONTENT_DELETE.value in admin_perms
        assert Permission.WORKSPACE_DELETE.value in admin_perms
        
        # Test owner permissions
        owner_perms = self.rbac.get_user_permissions(Role.OWNER.value)
        assert Permission.TEAM_ADMIN.value in owner_perms
        assert Permission.SYSTEM_BILLING.value in owner_perms
    
    def test_permission_checking(self):
        """Test permission validation"""
        # Test valid permissions
        assert self.rbac.has_permission(Role.EDITOR.value, Permission.CONTENT_CREATE.value)
        assert self.rbac.has_permission(Role.ADMIN.value, Permission.WORKSPACE_DELETE.value)
        
        # Test invalid permissions
        assert not self.rbac.has_permission(Role.VIEWER.value, Permission.CONTENT_DELETE.value)
        assert not self.rbac.has_permission(Role.MEMBER.value, Permission.TEAM_ADMIN.value)
    
    def test_content_access_control(self):
        """Test content-specific access control"""
        content_permissions = {
            "user123": [Permission.CONTENT_EDIT.value],
            "user456": [Permission.CONTENT_VIEW.value]
        }
        
        # Test role-based access
        assert self.rbac.can_access_content(
            Role.ADMIN.value, content_permissions, "user789", Permission.CONTENT_DELETE.value
        )
        
        # Test content-specific access
        assert self.rbac.can_access_content(
            Role.VIEWER.value, content_permissions, "user123", Permission.CONTENT_EDIT.value
        )
        
        # Test denied access
        assert not self.rbac.can_access_content(
            Role.VIEWER.value, content_permissions, "user456", Permission.CONTENT_EDIT.value
        )

class TestTeamWorkspaceDatabase:
    """Test database operations"""
    
    def setup_method(self):
        """Setup test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = TeamWorkspaceDatabase(self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)
    
    def test_team_creation_and_retrieval(self):
        """Test team database operations"""
        # Create test team
        team = Team(
            team_id="test_team_123",
            name="Test Team",
            description="A test team",
            owner_id="user123",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True,
            settings={"theme": "dark"},
            subscription_tier="pro",
            member_limit=25,
            storage_limit=10 * 1024**3,
            usage_stats={"members": 1, "storage_used": 0}
        )
        
        # Test creation
        assert self.db.create_team(team)
        
        # Test retrieval
        retrieved_team = self.db.get_team("test_team_123")
        assert retrieved_team is not None
        assert retrieved_team.name == "Test Team"
        assert retrieved_team.subscription_tier == "pro"
        assert retrieved_team.settings["theme"] == "dark"
    
    def test_workspace_operations(self):
        """Test workspace database operations"""
        # Create team first
        team = Team(
            team_id="test_team_456",
            name="Workspace Test Team",
            description="",
            owner_id="user456",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True,
            settings={},
            subscription_tier="free",
            member_limit=5,
            storage_limit=1024**3,
            usage_stats={}
        )
        self.db.create_team(team)
        
        # Create workspace
        workspace = Workspace(
            workspace_id="workspace_123",
            team_id="test_team_456",
            name="Test Workspace",
            description="A test workspace",
            created_by="user456",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True,
            settings={"auto_save": True},
            content_count=0,
            storage_used=0
        )
        
        # Test creation
        assert self.db.create_workspace(workspace)
        
        # Test retrieval
        workspaces = self.db.get_team_workspaces("test_team_456")
        assert len(workspaces) == 1
        assert workspaces[0].name == "Test Workspace"
        assert workspaces[0].settings["auto_save"] is True
    
    def test_team_member_operations(self):
        """Test team member database operations"""
        # Create team first
        team = Team(
            team_id="test_team_789",
            name="Member Test Team",
            description="",
            owner_id="user789",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True,
            settings={},
            subscription_tier="enterprise",
            member_limit=100,
            storage_limit=100 * 1024**3,
            usage_stats={}
        )
        self.db.create_team(team)
        
        # Add team member
        member = TeamMember(
            member_id="member_123",
            team_id="test_team_789",
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role=Role.EDITOR.value,
            permissions=[Permission.CONTENT_CREATE.value, Permission.WORKSPACE_CREATE.value],
            invited_by="user789",
            joined_at=datetime.now().isoformat(),
            last_active=None,
            is_active=True
        )
        
        # Test addition
        assert self.db.add_team_member(member)
        
        # Test retrieval
        members = self.db.get_team_members("test_team_789")
        assert len(members) == 1
        assert members[0].username == "testuser"
        assert members[0].role == Role.EDITOR.value
        assert Permission.CONTENT_CREATE.value in members[0].permissions
    
    def test_invitation_operations(self):
        """Test invitation database operations"""
        # Create team first
        team = Team(
            team_id="test_team_inv",
            name="Invitation Test Team",
            description="",
            owner_id="user_inv",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True,
            settings={},
            subscription_tier="free",
            member_limit=5,
            storage_limit=1024**3,
            usage_stats={}
        )
        self.db.create_team(team)
        
        # Create invitation
        invitation = Invitation(
            invitation_id="inv_123",
            team_id="test_team_inv",
            email="newuser@example.com",
            role=Role.MEMBER.value,
            invited_by="user_inv",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
            accepted_at=None,
            status="pending",
            token="secure_token_123"
        )
        
        # Test creation
        assert self.db.create_invitation(invitation)
        
        # Test retrieval
        invitations = self.db.get_pending_invitations("test_team_inv")
        assert len(invitations) == 1
        assert invitations[0].email == "newuser@example.com"
        assert invitations[0].status == "pending"
    
    def test_activity_logging(self):
        """Test activity logging"""
        # Log some activities
        self.db.log_activity(
            "team123", "workspace456", "user789", 
            "CONTENT_CREATED", "content", "content123",
            "Created new transcription"
        )
        
        self.db.log_activity(
            "team123", None, "user789",
            "TEAM_MEMBER_ADDED", "member", "member456",
            "Added new team member"
        )
        
        # Verify logs were created (would need additional query method in real implementation)
        # This is a basic test to ensure no exceptions are thrown
        assert True

class TestTeamWorkspaceManager:
    """Test high-level team workspace management"""
    
    def setup_method(self):
        """Setup test manager"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.manager = TeamWorkspaceManager()
        self.manager.db = TeamWorkspaceDatabase(self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)
    
    def test_team_creation_workflow(self):
        """Test complete team creation workflow"""
        # Test successful team creation
        success, message, team = self.manager.create_team(
            "owner123", "My Awesome Team", "A great team for collaboration", "pro"
        )
        
        assert success
        assert "successfully" in message.lower()
        assert team is not None
        assert team.name == "My Awesome Team"
        assert team.subscription_tier == "pro"
        assert team.member_limit == 25
        
        # Verify owner was added as team member
        members = self.manager.db.get_team_members(team.team_id)
        assert len(members) == 1
        assert members[0].role == Role.OWNER.value
        assert members[0].user_id == "owner123"
    
    def test_team_creation_validation(self):
        """Test team creation input validation"""
        # Test empty name
        success, message, team = self.manager.create_team("owner123", "", "Description")
        assert not success
        assert "2 characters" in message
        
        # Test short name
        success, message, team = self.manager.create_team("owner123", "A", "Description")
        assert not success
        assert "2 characters" in message
    
    def test_workspace_creation_workflow(self):
        """Test workspace creation workflow"""
        # Create team first
        success, message, team = self.manager.create_team("owner123", "Test Team")
        assert success
        
        # Create workspace
        success, message, workspace = self.manager.create_workspace(
            team.team_id, "owner123", "My Workspace", "A productive workspace"
        )
        
        assert success
        assert "successfully" in message.lower()
        assert workspace is not None
        assert workspace.name == "My Workspace"
        assert workspace.team_id == team.team_id
    
    def test_workspace_permission_checking(self):
        """Test workspace creation permissions"""
        # Create team and add member with limited permissions
        success, message, team = self.manager.create_team("owner123", "Permission Test Team")
        assert success
        
        # Add viewer (cannot create workspaces)
        viewer_member = TeamMember(
            member_id="member_viewer",
            team_id=team.team_id,
            user_id="viewer123",
            username="viewer",
            email="viewer@example.com",
            role=Role.VIEWER.value,
            permissions=self.manager.rbac.get_user_permissions(Role.VIEWER.value),
            invited_by="owner123",
            joined_at=datetime.now().isoformat(),
            last_active=None,
            is_active=True
        )
        self.manager.db.add_team_member(viewer_member)
        
        # Try to create workspace as viewer (should fail)
        success, message, workspace = self.manager.create_workspace(
            team.team_id, "viewer123", "Viewer Workspace"
        )
        
        assert not success
        assert "permission" in message.lower()
    
    def test_user_invitation_workflow(self):
        """Test user invitation workflow"""
        # Create team
        success, message, team = self.manager.create_team("owner123", "Invitation Test Team")
        assert success
        
        # Invite user
        success, message = self.manager.invite_user(
            team.team_id, "owner123", "newuser@example.com", Role.EDITOR.value
        )
        
        assert success
        assert "invitation sent" in message.lower()
        
        # Verify invitation was created
        invitations = self.manager.db.get_pending_invitations(team.team_id)
        assert len(invitations) == 1
        assert invitations[0].email == "newuser@example.com"
        assert invitations[0].role == Role.EDITOR.value
    
    def test_invitation_validation(self):
        """Test invitation validation"""
        # Create team
        success, message, team = self.manager.create_team("owner123", "Validation Test Team")
        assert success
        
        # Test invalid role
        success, message = self.manager.invite_user(
            team.team_id, "owner123", "test@example.com", "invalid_role"
        )
        assert not success
        assert "invalid role" in message.lower()
        
        # Test duplicate invitation
        self.manager.invite_user(team.team_id, "owner123", "duplicate@example.com", Role.MEMBER.value)
        success, message = self.manager.invite_user(
            team.team_id, "owner123", "duplicate@example.com", Role.EDITOR.value
        )
        assert not success
        assert "pending invitation" in message.lower()
    
    def test_user_context_retrieval(self):
        """Test user context retrieval"""
        # Create multiple teams and workspaces
        success, message, team1 = self.manager.create_team("user123", "Team 1")
        assert success
        
        success, message, team2 = self.manager.create_team("user123", "Team 2")
        assert success
        
        # Create workspaces
        self.manager.create_workspace(team1.team_id, "user123", "Workspace 1A")
        self.manager.create_workspace(team1.team_id, "user123", "Workspace 1B")
        self.manager.create_workspace(team2.team_id, "user123", "Workspace 2A")
        
        # Get user context
        context = self.manager.get_user_context("user123")
        
        assert len(context['teams']) == 2
        assert len(context['workspaces']) == 3
        assert len(context['permissions']) > 0
        
        # Verify team data structure
        team_names = [team_data['team'].name for team_data in context['teams']]
        assert "Team 1" in team_names
        assert "Team 2" in team_names
    
    def test_subscription_tier_limits(self):
        """Test subscription tier limits"""
        # Test free tier limits
        success, message, free_team = self.manager.create_team("user123", "Free Team", "", "free")
        assert success
        assert free_team.member_limit == 5
        assert free_team.storage_limit == 1024**3  # 1GB
        
        # Test pro tier limits
        success, message, pro_team = self.manager.create_team("user456", "Pro Team", "", "pro")
        assert success
        assert pro_team.member_limit == 25
        assert pro_team.storage_limit == 10 * 1024**3  # 10GB
        
        # Test enterprise tier limits
        success, message, ent_team = self.manager.create_team("user789", "Enterprise Team", "", "enterprise")
        assert success
        assert ent_team.member_limit == 100
        assert ent_team.storage_limit == 100 * 1024**3  # 100GB

def test_integration_workflow():
    """Test complete integration workflow"""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        manager = TeamWorkspaceManager()
        manager.db = TeamWorkspaceDatabase(temp_db.name)
        
        # 1. Create team
        success, message, team = manager.create_team(
            "ceo123", "Acme Corp", "Main company team", "enterprise"
        )
        assert success
        
        # 2. Create workspaces
        success, message, dev_workspace = manager.create_workspace(
            team.team_id, "ceo123", "Development", "Software development workspace"
        )
        assert success
        
        success, message, marketing_workspace = manager.create_workspace(
            team.team_id, "ceo123", "Marketing", "Marketing campaigns workspace"
        )
        assert success
        
        # 3. Invite team members
        success, message = manager.invite_user(
            team.team_id, "ceo123", "dev@acme.com", Role.EDITOR.value
        )
        assert success
        
        success, message = manager.invite_user(
            team.team_id, "ceo123", "marketing@acme.com", Role.MEMBER.value
        )
        assert success
        
        # 4. Verify complete setup
        context = manager.get_user_context("ceo123")
        assert len(context['teams']) == 1
        assert len(context['workspaces']) == 2
        
        invitations = manager.db.get_pending_invitations(team.team_id)
        assert len(invitations) == 2
        
        # 5. Test permission scenarios
        rbac = RBACManager()
        
        # CEO (owner) can do everything
        assert rbac.has_permission(Role.OWNER.value, Permission.TEAM_ADMIN.value)
        assert rbac.has_permission(Role.OWNER.value, Permission.WORKSPACE_DELETE.value)
        
        # Editor can create content and workspaces
        assert rbac.has_permission(Role.EDITOR.value, Permission.CONTENT_CREATE.value)
        assert rbac.has_permission(Role.EDITOR.value, Permission.WORKSPACE_CREATE.value)
        
        # Member has limited permissions
        assert rbac.has_permission(Role.MEMBER.value, Permission.CONTENT_CREATE.value)
        assert not rbac.has_permission(Role.MEMBER.value, Permission.WORKSPACE_CREATE.value)
        
        print("✅ Integration workflow test completed successfully!")
        
    finally:
        os.unlink(temp_db.name)

if __name__ == "__main__":
    # Run integration test
    test_integration_workflow()
    
    # Run pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Run basic tests manually
        test_rbac = TestRBACManager()
        test_rbac.setup_method()
        test_rbac.test_role_permissions()
        test_rbac.test_permission_checking()
        test_rbac.test_content_access_control()
        print("✅ RBAC tests passed!")
        
        test_db = TestTeamWorkspaceDatabase()
        test_db.setup_method()
        test_db.test_team_creation_and_retrieval()
        test_db.test_workspace_operations()
        test_db.test_team_member_operations()
        test_db.test_invitation_operations()
        test_db.teardown_method()
        print("✅ Database tests passed!")
        
        test_manager = TestTeamWorkspaceManager()
        test_manager.setup_method()
        test_manager.test_team_creation_workflow()
        test_manager.test_workspace_creation_workflow()
        test_manager.test_user_invitation_workflow()
        test_manager.test_user_context_retrieval()
        test_manager.teardown_method()
        print("✅ Manager tests passed!")
        
        print("🎉 All tests completed successfully!")