#!/usr/bin/env python3
"""
Test suite for team management system
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from database.models import init_db, User, Team, TeamMember, TeamRole, Transcript, Project
from teams.team_manager import TeamManager
from teams.resource_manager import ResourceManager
from notifications.notification_manager import NotificationManager


@pytest.fixture
def db_session():
    """Create a temporary database session for testing"""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db_url = f"sqlite:///{temp_db.name}"
    session = init_db(db_url)
    
    yield session
    
    # Cleanup
    session.close()
    os.unlink(temp_db.name)


@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing"""
    # Create test users
    user1 = User(
        email="owner@example.com",
        username="teamowner",
        password_hash="hashed_password",
        full_name="Team Owner"
    )
    
    user2 = User(
        email="admin@example.com", 
        username="teamadmin",
        password_hash="hashed_password",
        full_name="Team Admin"
    )
    
    user3 = User(
        email="member@example.com",
        username="teammember", 
        password_hash="hashed_password",
        full_name="Team Member"
    )
    
    user4 = User(
        email="viewer@example.com",
        username="teamviewer",
        password_hash="hashed_password", 
        full_name="Team Viewer"
    )
    
    db_session.add_all([user1, user2, user3, user4])
    db_session.commit()
    
    return user1, user2, user3, user4


def test_team_creation(db_session, sample_users):
    """Test team creation functionality"""
    owner, _, _, _ = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team
    team = team_manager.create_team(
        name="Test Team",
        description="A test team",
        owner_id=owner.id,
        max_members=5,
        storage_quota_mb=1000
    )
    
    assert team is not None
    assert team.name == "Test Team"
    assert team.description == "A test team"
    assert team.owner_id == owner.id
    assert team.max_members == 5
    assert team.storage_quota_mb == 1000
    
    # Check owner membership was created
    membership = db_session.query(TeamMember).filter_by(
        team_id=team.id,
        user_id=owner.id
    ).first()
    
    assert membership is not None
    assert membership.role == TeamRole.OWNER


def test_member_invitation(db_session, sample_users):
    """Test member invitation functionality"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team
    team = team_manager.create_team(
        name="Invitation Test Team",
        description="Testing invitations",
        owner_id=owner.id
    )
    
    # Invite admin
    success, message, membership = team_manager.invite_member(
        team_id=team.id,
        inviter_id=owner.id,
        email="admin@example.com",
        role=TeamRole.ADMIN
    )
    
    assert success is True
    assert "successfully added" in message
    assert membership is not None
    assert membership.role == TeamRole.ADMIN
    
    # Invite member
    success, message, _ = team_manager.invite_member(
        team_id=team.id,
        inviter_id=owner.id,
        email="member@example.com",
        role=TeamRole.MEMBER
    )
    
    assert success is True
    
    # Try to invite same user again (should fail)
    success, message, _ = team_manager.invite_member(
        team_id=team.id,
        inviter_id=owner.id,
        email="member@example.com",
        role=TeamRole.MEMBER
    )
    
    assert success is False
    assert "already a member" in message


def test_role_management(db_session, sample_users):
    """Test role change functionality"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team with members
    team = team_manager.create_team(
        name="Role Test Team",
        description="Testing roles",
        owner_id=owner.id
    )
    
    # Add member
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    
    # Change member to admin
    success, message = team_manager.change_member_role(
        team_id=team.id,
        changer_id=owner.id,
        member_user_id=member.id,
        new_role=TeamRole.ADMIN
    )
    
    assert success is True
    assert "Role changed" in message
    
    # Verify role change
    role = team_manager.get_user_role_in_team(team.id, member.id)
    assert role == TeamRole.ADMIN


def test_permissions(db_session, sample_users):
    """Test permission system"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team with all roles
    team = team_manager.create_team(
        name="Permission Test Team",
        description="Testing permissions",
        owner_id=owner.id
    )
    
    team_manager.invite_member(team.id, owner.id, "admin@example.com", TeamRole.ADMIN)
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    team_manager.invite_member(team.id, owner.id, "viewer@example.com", TeamRole.VIEWER)
    
    # Test owner permissions
    assert team_manager.can_user_perform_action(team.id, owner.id, 'delete_team') is True
    assert team_manager.can_user_perform_action(team.id, owner.id, 'invite_members') is True
    assert team_manager.can_user_perform_action(team.id, owner.id, 'view_transcripts') is True
    
    # Test admin permissions
    assert team_manager.can_user_perform_action(team.id, admin.id, 'delete_team') is False
    assert team_manager.can_user_perform_action(team.id, admin.id, 'invite_members') is True
    assert team_manager.can_user_perform_action(team.id, admin.id, 'view_transcripts') is True
    
    # Test member permissions
    assert team_manager.can_user_perform_action(team.id, member.id, 'invite_members') is False
    assert team_manager.can_user_perform_action(team.id, member.id, 'view_transcripts') is True
    assert team_manager.can_user_perform_action(team.id, member.id, 'create_transcripts') is True
    
    # Test viewer permissions
    assert team_manager.can_user_perform_action(team.id, viewer.id, 'invite_members') is False
    assert team_manager.can_user_perform_action(team.id, viewer.id, 'view_transcripts') is True
    assert team_manager.can_user_perform_action(team.id, viewer.id, 'create_transcripts') is False


def test_resource_sharing(db_session, sample_users):
    """Test resource sharing functionality"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    resource_manager = ResourceManager(db_session)
    
    # Create team
    team = team_manager.create_team(
        name="Resource Test Team",
        description="Testing resources",
        owner_id=owner.id
    )
    
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    
    # Create personal transcript
    transcript = Transcript(
        user_id=member.id,
        title="Test Transcript",
        content="This is a test transcript content",
        file_name="test.mp3",
        file_size=1024,
        language="en",
        confidence=0.95,
        word_count=6
    )
    
    db_session.add(transcript)
    db_session.commit()
    db_session.refresh(transcript)
    
    # Share with team
    success, message = resource_manager.share_transcript_with_team(
        transcript_id=transcript.id,
        team_id=team.id,
        user_id=member.id
    )
    
    assert success is True
    assert "successfully" in message
    
    # Verify transcript is now shared with team
    db_session.refresh(transcript)
    assert transcript.team_id == team.id
    
    # Get team resources
    resources = resource_manager.get_team_resources(team.id, owner.id)
    assert len(resources) == 1
    assert resources[0].id == transcript.id


def test_project_management(db_session, sample_users):
    """Test project management functionality"""
    owner, admin, member, viewer = sample_users
    resource_manager = ResourceManager(db_session)
    team_manager = TeamManager(db_session)
    
    # Create team
    team = team_manager.create_team(
        name="Project Test Team",
        description="Testing projects",
        owner_id=owner.id
    )
    
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    
    # Create project
    success, message, project = resource_manager.create_team_project(
        team_id=team.id,
        user_id=member.id,
        name="Test Project",
        description="A test project"
    )
    
    assert success is True
    assert project is not None
    assert project.name == "Test Project"
    assert project.created_by_id == member.id
    
    # Get team projects
    projects = resource_manager.get_team_projects(team.id, owner.id)
    assert len(projects) == 1
    assert projects[0].id == project.id
    
    # Archive project
    success, message = resource_manager.archive_project(project.id, member.id)
    assert success is True
    
    # Verify project is archived
    projects = resource_manager.get_team_projects(team.id, owner.id)
    assert len(projects) == 0  # Archived projects not included by default


def test_team_analytics(db_session, sample_users):
    """Test team analytics functionality"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team with members
    team = team_manager.create_team(
        name="Analytics Test Team",
        description="Testing analytics",
        owner_id=owner.id
    )
    
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    
    # Add some transcripts
    transcript1 = Transcript(
        user_id=owner.id,
        team_id=team.id,
        title="Owner Transcript",
        content="Content from owner",
        file_name="owner.mp3",
        file_size=2048,
        language="en",
        confidence=0.95,
        word_count=3
    )
    
    transcript2 = Transcript(
        user_id=member.id,
        team_id=team.id,
        title="Member Transcript", 
        content="Content from member",
        file_name="member.mp3",
        file_size=1024,
        language="en",
        confidence=0.90,
        word_count=3
    )
    
    db_session.add_all([transcript1, transcript2])
    db_session.commit()
    
    # Get analytics
    analytics = team_manager.get_team_analytics(team.id, owner.id)
    
    assert analytics['team_name'] == "Analytics Test Team"
    assert analytics['member_count'] == 2  # owner + member
    assert analytics['transcript_count'] == 2
    assert analytics['project_count'] == 0
    assert len(analytics['recent_transcripts']) == 2
    assert len(analytics['member_activity']) == 2


def test_team_notifications(db_session, sample_users):
    """Test team notification system"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    notification_manager = NotificationManager(db_session)
    
    # Create team
    team = team_manager.create_team(
        name="Notification Test Team",
        description="Testing notifications",
        owner_id=owner.id
    )
    
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    
    # Send team invitation notification
    notification = notification_manager.notify_team_invitation(
        invited_user_id=member.id,
        inviter_id=owner.id,
        team_id=team.id,
        team_name=team.name,
        role="member"
    )
    
    assert notification is not None
    assert notification.user_id == member.id
    assert notification.from_user_id == owner.id
    assert notification.type == 'team_invitation'
    assert team.name in notification.message
    
    # Test bulk team notifications
    notifications = notification_manager.notify_team_members(
        team_id=team.id,
        notification_type='team_announcement',
        title='Test Announcement',
        message='This is a test announcement',
        from_user_id=owner.id
    )
    
    # Should notify member but not owner (excluded as sender)
    assert len(notifications) == 1
    assert notifications[0].user_id == member.id


def test_leave_team(db_session, sample_users):
    """Test leaving team functionality"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team with member
    team = team_manager.create_team(
        name="Leave Test Team",
        description="Testing leave functionality",
        owner_id=owner.id
    )
    
    team_manager.invite_member(team.id, owner.id, "member@example.com", TeamRole.MEMBER)
    
    # Member leaves team
    success, message = team_manager.leave_team(team.id, member.id)
    assert success is True
    assert "Successfully left" in message
    
    # Verify member is no longer in team
    assert team_manager.is_team_member(team.id, member.id) is False
    
    # Owner cannot leave team
    success, message = team_manager.leave_team(team.id, owner.id)
    assert success is False
    assert "owner cannot leave" in message.lower()


def test_team_limits(db_session, sample_users):
    """Test team member limits"""
    owner, admin, member, viewer = sample_users
    team_manager = TeamManager(db_session)
    
    # Create team with low member limit
    team = team_manager.create_team(
        name="Limited Team",
        description="Testing limits",
        owner_id=owner.id,
        max_members=2  # Owner + 1 more
    )
    
    # Add one member (should succeed)
    success, message, _ = team_manager.invite_member(
        team.id, owner.id, "admin@example.com", TeamRole.ADMIN
    )
    assert success is True
    
    # Try to add another member (should fail due to limit)
    success, message, _ = team_manager.invite_member(
        team.id, owner.id, "member@example.com", TeamRole.MEMBER
    )
    assert success is False
    assert "maximum member limit" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])