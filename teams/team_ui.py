"""
Team UI components for Streamlit interface
"""

import streamlit as st
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from database.models import Team, TeamMember, TeamRole, User
from teams.team_manager import TeamManager
import logging

logger = logging.getLogger(__name__)


def render_team_dashboard(team_manager: TeamManager, user_id: int) -> None:
    """Render the main team dashboard"""
    st.header("🏢 Team Dashboard")
    
    # Get user's teams
    teams = team_manager.get_user_teams(user_id)
    owned_teams = team_manager.get_owned_teams(user_id)
    
    if not teams and not owned_teams:
        # No teams - show create team option
        st.info("You're not part of any teams yet. Create your first team or wait for an invitation!")
        
        with st.expander("➕ Create New Team", expanded=True):
            render_create_team_form(team_manager, user_id)
        return
    
    # Teams overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Teams You Own", len(owned_teams))
    
    with col2:
        st.metric("Teams You're In", len(teams))
    
    with col3:
        total_members = sum(len(team.members) for team in teams + owned_teams)
        st.metric("Total Team Members", total_members)
    
    # Team selector
    all_teams = list(set(teams + owned_teams))  # Remove duplicates
    team_options = {f"{team.name} ({'Owner' if team.owner_id == user_id else 'Member'})": team.id 
                   for team in all_teams}
    
    if team_options:
        selected_team_name = st.selectbox(
            "Select Team to View",
            options=list(team_options.keys()),
            key="dashboard_team_selector"
        )
        
        selected_team_id = team_options[selected_team_name]
        selected_team = team_manager.get_team(selected_team_id, user_id)
        
        if selected_team:
            render_team_overview(team_manager, selected_team, user_id)
    
    # Quick actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("➕ Create New Team", key="create_team_btn"):
            st.session_state.show_create_team = True
    
    with col2:
        if st.button("⚙️ Manage Teams", key="manage_teams_btn"):
            st.session_state.show_team_management = True
    
    # Show create team form if requested
    if st.session_state.get('show_create_team', False):
        with st.expander("Create New Team", expanded=True):
            render_create_team_form(team_manager, user_id)


def render_team_overview(team_manager: TeamManager, team: Team, user_id: int) -> None:
    """Render overview of a specific team"""
    st.subheader(f"📋 {team.name}")
    st.write(team.description)
    
    # Team stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Members", f"{len(team.members)}/{team.max_members}")
    
    with col2:
        storage_pct = (team.storage_used_mb / team.storage_quota_mb * 100) if team.storage_quota_mb > 0 else 0
        st.metric("Storage", f"{team.storage_used_mb:.1f}/{team.storage_quota_mb} MB")
        st.progress(min(storage_pct / 100, 1.0))
    
    with col3:
        transcript_count = len(team.transcripts) if team.transcripts else 0
        st.metric("Transcripts", transcript_count)
    
    with col4:
        project_count = len(team.projects) if team.projects else 0
        st.metric("Projects", project_count)
    
    # Team members
    st.markdown("### 👥 Team Members")
    if team.members:
        members_data = []
        for member in team.members:
            members_data.append({
                "Username": member.user.username,
                "Role": member.role.value.title(),
                "Joined": member.joined_at.strftime("%Y-%m-%d"),
                "Status": "🟢 Active"
            })
        
        df = pd.DataFrame(members_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No members in this team yet.")
    
    # Recent activity
    st.markdown("### 📈 Recent Activity")
    if team.transcripts:
        recent_transcripts = sorted(team.transcripts, key=lambda x: x.created_at, reverse=True)[:5]
        for transcript in recent_transcripts:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 **{transcript.title}**")
                    st.caption(f"By {transcript.user.username} • {transcript.created_at.strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if st.button("View", key=f"view_transcript_{transcript.id}"):
                        st.session_state.selected_transcript_id = transcript.id
    else:
        st.info("No recent activity.")
    
    # Team actions
    user_role = team_manager.get_user_role_in_team(team.id, user_id)
    if user_role in [TeamRole.OWNER, TeamRole.ADMIN]:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👥 Manage Members", key=f"manage_members_{team.id}"):
                st.session_state.show_member_management = team.id
        
        with col2:
            if st.button("📊 View Analytics", key=f"view_analytics_{team.id}"):
                st.session_state.show_team_analytics = team.id
        
        with col3:
            if user_role == TeamRole.OWNER:
                if st.button("⚙️ Team Settings", key=f"team_settings_{team.id}"):
                    st.session_state.show_team_settings = team.id


def render_team_management(team_manager: TeamManager, user_id: int) -> None:
    """Render team management interface"""
    st.header("⚙️ Team Management")
    
    # Get teams user can manage
    owned_teams = team_manager.get_owned_teams(user_id)
    admin_teams = []
    
    # Get teams where user is admin
    user_teams = team_manager.get_user_teams(user_id)
    for team in user_teams:
        if team_manager.get_user_role_in_team(team.id, user_id) == TeamRole.ADMIN:
            admin_teams.append(team)
    
    manageable_teams = list(set(owned_teams + admin_teams))
    
    if not manageable_teams:
        st.warning("You don't have management permissions for any teams.")
        return
    
    # Team selector
    team_options = {f"{team.name} ({'Owner' if team.owner_id == user_id else 'Admin'})": team.id 
                   for team in manageable_teams}
    
    selected_team_name = st.selectbox(
        "Select Team to Manage",
        options=list(team_options.keys()),
        key="management_team_selector"
    )
    
    selected_team_id = team_options[selected_team_name]
    selected_team = team_manager.get_team(selected_team_id, user_id)
    
    if not selected_team:
        st.error("Team not found or access denied.")
        return
    
    # Management tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Members", "📊 Analytics", "⚙️ Settings", "🗑️ Danger Zone"])
    
    with tab1:
        render_member_management(team_manager, selected_team, user_id)
    
    with tab2:
        render_team_analytics(team_manager, selected_team, user_id)
    
    with tab3:
        render_team_settings(team_manager, selected_team, user_id)
    
    with tab4:
        render_danger_zone(team_manager, selected_team, user_id)


def render_member_management(team_manager: TeamManager, team: Team, user_id: int) -> None:
    """Render member management interface"""
    st.subheader(f"👥 Manage Members - {team.name}")
    
    # Current members
    st.markdown("### Current Members")
    if team.members:
        for member in team.members:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                
                with col1:
                    st.write(f"**{member.user.username}**")
                    st.caption(f"{member.user.email}")
                
                with col2:
                    st.write(member.role.value.title())
                
                with col3:
                    st.write(member.joined_at.strftime("%Y-%m-%d"))
                
                with col4:
                    if member.user_id != user_id and member.user_id != team.owner_id:
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            # Change role button
                            if st.button("🔄", key=f"change_role_{member.id}", help="Change Role"):
                                st.session_state[f"show_role_change_{member.id}"] = True
                        
                        with col_b:
                            # Remove member button
                            if st.button("❌", key=f"remove_member_{member.id}", help="Remove Member"):
                                success, message = team_manager.remove_member(team.id, user_id, member.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                
                # Role change form
                if st.session_state.get(f"show_role_change_{member.id}", False):
                    with st.expander("Change Role", expanded=True):
                        new_role = st.selectbox(
                            "New Role",
                            options=[role.value for role in TeamRole if role != TeamRole.OWNER],
                            key=f"new_role_{member.id}"
                        )
                        
                        col_x, col_y = st.columns(2)
                        with col_x:
                            if st.button("Save", key=f"save_role_{member.id}"):
                                success, message = team_manager.change_member_role(
                                    team.id, user_id, member.user_id, TeamRole(new_role)
                                )
                                if success:
                                    st.success(message)
                                    st.session_state[f"show_role_change_{member.id}"] = False
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        with col_y:
                            if st.button("Cancel", key=f"cancel_role_{member.id}"):
                                st.session_state[f"show_role_change_{member.id}"] = False
                                st.rerun()
                
                st.markdown("---")
    
    # Invite new members
    st.markdown("### 👋 Invite New Members")
    with st.form("invite_member_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            email = st.text_input("Email Address", placeholder="user@example.com")
        
        with col2:
            role = st.selectbox(
                "Role",
                options=[role.value for role in TeamRole if role != TeamRole.OWNER],
                index=2  # Default to MEMBER
            )
        
        submitted = st.form_submit_button("Send Invitation")
        
        if submitted and email:
            success, message, membership = team_manager.invite_member(
                team.id, user_id, email, TeamRole(role)
            )
            
            if success:
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")


def render_team_analytics(team_manager: TeamManager, team: Team, user_id: int) -> None:
    """Render team analytics"""
    st.subheader(f"📊 Analytics - {team.name}")
    
    analytics = team_manager.get_team_analytics(team.id, user_id)
    
    if not analytics:
        st.error("Unable to load analytics data.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Members", analytics['member_count'])
    
    with col2:
        st.metric("Total Transcripts", analytics['transcript_count'])
    
    with col3:
        st.metric("Total Projects", analytics['project_count'])
    
    with col4:
        storage_pct = analytics['storage_percentage']
        st.metric("Storage Used", f"{storage_pct:.1f}%")
    
    # Storage chart
    st.markdown("### 💾 Storage Usage")
    storage_data = pd.DataFrame({
        'Type': ['Used', 'Available'],
        'Size (MB)': [
            analytics['storage_used_mb'],
            analytics['storage_quota_mb'] - analytics['storage_used_mb']
        ]
    })
    st.bar_chart(storage_data.set_index('Type'))
    
    # Member activity
    st.markdown("### 👥 Member Activity")
    if analytics['member_activity']:
        activity_df = pd.DataFrame(analytics['member_activity'])
        activity_df['joined_at'] = pd.to_datetime(activity_df['joined_at']).dt.strftime('%Y-%m-%d')
        st.dataframe(activity_df, use_container_width=True)
    
    # Recent transcripts
    st.markdown("### 📄 Recent Transcripts")
    if analytics['recent_transcripts']:
        for transcript in analytics['recent_transcripts']:
            st.write(f"📄 **{transcript['title']}**")
            st.caption(f"By {transcript['author']} • {transcript['created_at'].strftime('%Y-%m-%d %H:%M')}")


def render_team_settings(team_manager: TeamManager, team: Team, user_id: int) -> None:
    """Render team settings"""
    st.subheader(f"⚙️ Team Settings - {team.name}")
    
    # Only owners can edit most settings
    is_owner = team.owner_id == user_id
    can_edit = team_manager.can_user_perform_action(team.id, user_id, 'edit_team')
    
    if not can_edit:
        st.warning("You don't have permission to edit team settings.")
        return
    
    with st.form("team_settings_form"):
        st.markdown("### Basic Information")
        
        name = st.text_input("Team Name", value=team.name, disabled=not is_owner)
        description = st.text_area("Description", value=team.description or "")
        
        st.markdown("### Limits")
        col1, col2 = st.columns(2)
        
        with col1:
            max_members = st.number_input(
                "Maximum Members",
                min_value=len(team.members),
                max_value=100,
                value=team.max_members,
                disabled=not is_owner
            )
        
        with col2:
            storage_quota = st.number_input(
                "Storage Quota (MB)",
                min_value=int(team.storage_used_mb),
                max_value=50000,
                value=team.storage_quota_mb,
                disabled=not is_owner
            )
        
        submitted = st.form_submit_button("Save Settings")
        
        if submitted:
            success, message, updated_team = team_manager.update_team(
                team.id, user_id, name, description, max_members, storage_quota
            )
            
            if success:
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")


def render_danger_zone(team_manager: TeamManager, team: Team, user_id: int) -> None:
    """Render danger zone with destructive actions"""
    st.subheader(f"🗑️ Danger Zone - {team.name}")
    
    is_owner = team.owner_id == user_id
    
    if is_owner:
        st.error("⚠️ Dangerous Actions - These cannot be undone!")
        
        # Delete team
        st.markdown("### Delete Team")
        st.write("This will permanently delete the team and all its data.")
        
        if st.checkbox("I understand this action cannot be undone", key="delete_team_confirm"):
            if st.button("🗑️ Delete Team", type="primary"):
                success, message = team_manager.delete_team(team.id, user_id)
                if success:
                    st.success(message)
                    st.session_state.show_team_management = False
                    st.rerun()
                else:
                    st.error(message)
    else:
        # Leave team
        st.markdown("### Leave Team")
        st.write("You will no longer have access to this team's content.")
        
        if st.button("👋 Leave Team"):
            success, message = team_manager.leave_team(team.id, user_id)
            if success:
                st.success(message)
                st.session_state.show_team_management = False
                st.rerun()
            else:
                st.error(message)


def render_create_team_form(team_manager: TeamManager, user_id: int) -> None:
    """Render create team form"""
    with st.form("create_team_form"):
        st.markdown("### Create New Team")
        
        name = st.text_input("Team Name*", placeholder="My Awesome Team")
        description = st.text_area("Description", placeholder="What's this team for?")
        
        col1, col2 = st.columns(2)
        with col1:
            max_members = st.number_input("Maximum Members", min_value=2, max_value=100, value=10)
        
        with col2:
            storage_quota = st.number_input("Storage Quota (MB)", min_value=1000, max_value=50000, value=5000)
        
        submitted = st.form_submit_button("Create Team")
        
        if submitted:
            if not name:
                st.error("Team name is required.")
                return
            
            try:
                team = team_manager.create_team(
                    name=name,
                    description=description,
                    owner_id=user_id,
                    max_members=max_members,
                    storage_quota_mb=storage_quota
                )
                
                st.success(f"✅ Team '{team.name}' created successfully!")
                st.session_state.show_create_team = False
                st.rerun()
                
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Failed to create team: {str(e)}")
                logger.error(f"Error creating team: {e}")


def render_team_selector(team_manager: TeamManager, user_id: int, key: str = "team_selector") -> Optional[int]:
    """Render team selector dropdown"""
    teams = team_manager.get_user_teams(user_id)
    
    if not teams:
        st.info("You're not part of any teams yet.")
        return None
    
    team_options = {"Personal": None}  # Option for no team
    team_options.update({team.name: team.id for team in teams})
    
    selected_name = st.selectbox(
        "Select Team",
        options=list(team_options.keys()),
        key=key
    )
    
    return team_options[selected_name]


def show_team_invitation_notification(team_name: str, inviter_name: str, role: str) -> None:
    """Show team invitation notification"""
    st.success(f"🎉 You've been invited to join team **{team_name}** as a **{role}** by {inviter_name}!")