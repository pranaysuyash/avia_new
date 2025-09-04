#!/usr/bin/env python3
"""
Demo: Team Workspaces and Collaboration Features
Interactive demonstration of enterprise team management and RBAC
"""

import streamlit as st
import secrets
import json
from datetime import datetime
from team_workspaces import TeamWorkspaceUI, TeamWorkspaceManager, Role

def main():
    """Main demo application"""
    st.set_page_config(
        page_title="Team Workspaces Demo",
        page_icon="👥",
        layout="wide"
    )
    
    # Header
    st.title("👥 Team Workspaces & Collaboration Demo")
    st.markdown("""
    **Enterprise-grade team management with Role-Based Access Control (RBAC)**
    
    This demo showcases:
    - 🏢 Multi-team workspace management
    - 🔐 Role-based permissions (Viewer, Member, Editor, Admin, Owner)
    - 👥 Team member invitations and management
    - 📁 Workspace organization and content sharing
    - 📊 Usage analytics and subscription tiers
    """)
    st.markdown("---")
    
    # Initialize demo data
    if 'demo_initialized' not in st.session_state:
        initialize_demo_data()
    
    # User selection for demo
    demo_users = {
        "Alice (CEO)": "alice_ceo",
        "Bob (Dev Lead)": "bob_dev_lead", 
        "Carol (Designer)": "carol_designer",
        "Dave (Intern)": "dave_intern"
    }
    
    selected_user = st.selectbox(
        "👤 Select Demo User",
        options=list(demo_users.keys()),
        help="Switch between different users to see role-based permissions in action"
    )
    
    current_user_id = demo_users[selected_user]
    st.session_state.current_demo_user = current_user_id
    
    # Show user role info
    user_info = get_demo_user_info(current_user_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current User", user_info['name'])
    with col2:
        st.metric("Primary Role", user_info['role'])
    with col3:
        st.metric("Teams", len(user_info['teams']))
    
    st.markdown("---")
    
    # Main interface
    ui = TeamWorkspaceUI()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard", 
        "👥 Teams", 
        "📁 Workspaces", 
        "⚙️ Management", 
        "📊 Analytics"
    ])
    
    with tab1:
        render_dashboard(current_user_id, user_info)
    
    with tab2:
        render_teams_tab(ui, current_user_id)
    
    with tab3:
        render_workspaces_tab(ui, current_user_id)
    
    with tab4:
        render_management_tab(ui, current_user_id)
    
    with tab5:
        render_analytics_tab(current_user_id)

def initialize_demo_data():
    """Initialize demo data with sample teams and users"""
    st.session_state.demo_initialized = True
    
    # Demo user profiles
    st.session_state.demo_users = {
        "alice_ceo": {
            "name": "Alice Johnson",
            "email": "alice@acme.com",
            "role": "Owner",
            "teams": ["acme_corp", "executive_team"],
            "permissions": ["all"]
        },
        "bob_dev_lead": {
            "name": "Bob Smith", 
            "email": "bob@acme.com",
            "role": "Admin",
            "teams": ["acme_corp"],
            "permissions": ["content:*", "workspace:*", "team:manage"]
        },
        "carol_designer": {
            "name": "Carol Davis",
            "email": "carol@acme.com", 
            "role": "Editor",
            "teams": ["acme_corp"],
            "permissions": ["content:create", "content:edit", "workspace:create"]
        },
        "dave_intern": {
            "name": "Dave Wilson",
            "email": "dave@acme.com",
            "role": "Viewer", 
            "teams": ["acme_corp"],
            "permissions": ["content:view", "workspace:view"]
        }
    }
    
    # Demo teams
    st.session_state.demo_teams = {
        "acme_corp": {
            "name": "Acme Corporation",
            "description": "Main company workspace",
            "owner": "alice_ceo",
            "tier": "enterprise",
            "members": 4,
            "workspaces": ["development", "design", "marketing"],
            "storage_used": "45.2 GB",
            "storage_limit": "100 GB"
        },
        "executive_team": {
            "name": "Executive Team",
            "description": "C-level strategic planning",
            "owner": "alice_ceo", 
            "tier": "pro",
            "members": 1,
            "workspaces": ["strategy", "board_meetings"],
            "storage_used": "2.1 GB",
            "storage_limit": "10 GB"
        }
    }
    
    # Demo workspaces
    st.session_state.demo_workspaces = {
        "development": {
            "name": "Development",
            "team": "acme_corp",
            "description": "Software development projects",
            "content_count": 156,
            "recent_activity": "2 hours ago"
        },
        "design": {
            "name": "Design",
            "team": "acme_corp", 
            "description": "UI/UX design assets",
            "content_count": 89,
            "recent_activity": "1 day ago"
        },
        "marketing": {
            "name": "Marketing",
            "team": "acme_corp",
            "description": "Marketing campaigns and content",
            "content_count": 234,
            "recent_activity": "3 hours ago"
        }
    }

def get_demo_user_info(user_id):
    """Get demo user information"""
    return st.session_state.demo_users.get(user_id, {})

def render_dashboard(user_id, user_info):
    """Render user dashboard"""
    st.header(f"Welcome back, {user_info.get('name', 'User')}! 👋")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Teams",
            len(user_info.get('teams', [])),
            help="Number of teams you're a member of"
        )
    
    with col2:
        total_workspaces = sum(
            len(st.session_state.demo_teams[team_id]['workspaces'])
            for team_id in user_info.get('teams', [])
            if team_id in st.session_state.demo_teams
        )
        st.metric(
            "Workspaces", 
            total_workspaces,
            help="Total workspaces across all your teams"
        )
    
    with col3:
        st.metric(
            "Content Items",
            "479",
            delta="23 this week",
            help="Total content items you have access to"
        )
    
    with col4:
        st.metric(
            "Storage Used",
            "47.3 GB",
            delta="2.1 GB this month",
            help="Total storage used across all teams"
        )
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    activity_data = [
        {"Time": "2 hours ago", "Action": "Created transcription", "Workspace": "Development", "User": "Bob Smith"},
        {"Time": "3 hours ago", "Action": "Shared analysis report", "Workspace": "Marketing", "User": "Carol Davis"},
        {"Time": "1 day ago", "Action": "Updated design assets", "Workspace": "Design", "User": "Carol Davis"},
        {"Time": "1 day ago", "Action": "Invited new member", "Workspace": "Acme Corporation", "User": "Alice Johnson"},
        {"Time": "2 days ago", "Action": "Created workspace", "Workspace": "Strategy", "User": "Alice Johnson"}
    ]
    
    st.dataframe(activity_data, use_container_width=True)
    
    # Quick actions based on role
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 New Transcription", use_container_width=True):
            st.info("Would open transcription upload interface")
    
    with col2:
        if user_info.get('role') in ['Admin', 'Owner', 'Editor']:
            if st.button("👥 Invite Member", use_container_width=True):
                st.info("Would open team invitation interface")
        else:
            st.button("👥 Invite Member", disabled=True, help="Insufficient permissions")
    
    with col3:
        if user_info.get('role') in ['Admin', 'Owner']:
            if st.button("📁 New Workspace", use_container_width=True):
                st.info("Would open workspace creation interface")
        else:
            st.button("📁 New Workspace", disabled=True, help="Insufficient permissions")

def render_teams_tab(ui, user_id):
    """Render teams management tab"""
    st.header("👥 Your Teams")
    
    user_info = get_demo_user_info(user_id)
    user_teams = user_info.get('teams', [])
    
    if not user_teams:
        st.info("You're not a member of any teams yet.")
        return
    
    # Team cards
    for team_id in user_teams:
        if team_id not in st.session_state.demo_teams:
            continue
            
        team = st.session_state.demo_teams[team_id]
        
        with st.container():
            st.markdown(f"### 🏢 {team['name']}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Members", team['members'])
            
            with col2:
                st.metric("Workspaces", len(team['workspaces']))
            
            with col3:
                st.metric("Tier", team['tier'].title())
            
            with col4:
                st.metric("Storage", f"{team['storage_used']} / {team['storage_limit']}")
            
            st.write(f"📝 {team['description']}")
            
            # Team actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"View {team['name']}", key=f"view_{team_id}"):
                    st.session_state.selected_team = team_id
                    st.success(f"Selected team: {team['name']}")
            
            with col2:
                if user_info.get('role') in ['Admin', 'Owner']:
                    if st.button(f"Manage {team['name']}", key=f"manage_{team_id}"):
                        st.info("Would open team management interface")
                else:
                    st.button(f"Manage {team['name']}", disabled=True, key=f"manage_{team_id}_disabled")
            
            with col3:
                if st.button(f"Analytics", key=f"analytics_{team_id}"):
                    st.info("Would show team analytics")
            
            st.markdown("---")

def render_workspaces_tab(ui, user_id):
    """Render workspaces tab"""
    st.header("📁 Workspaces")
    
    user_info = get_demo_user_info(user_id)
    user_teams = user_info.get('teams', [])
    
    # Get all workspaces user has access to
    accessible_workspaces = []
    for team_id in user_teams:
        if team_id in st.session_state.demo_teams:
            team = st.session_state.demo_teams[team_id]
            for workspace_id in team['workspaces']:
                if workspace_id in st.session_state.demo_workspaces:
                    workspace = st.session_state.demo_workspaces[workspace_id].copy()
                    workspace['team_name'] = team['name']
                    accessible_workspaces.append(workspace)
    
    if not accessible_workspaces:
        st.info("No workspaces available.")
        return
    
    # Workspace grid
    cols = st.columns(2)
    
    for i, workspace in enumerate(accessible_workspaces):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"#### 📁 {workspace['name']}")
                st.write(f"**Team:** {workspace['team_name']}")
                st.write(f"📝 {workspace['description']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Content", workspace['content_count'])
                with col2:
                    st.write(f"🕒 {workspace['recent_activity']}")
                
                # Workspace actions
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"Open", key=f"open_{workspace['name']}"):
                        st.session_state.selected_workspace = workspace['name']
                        st.success(f"Opened workspace: {workspace['name']}")
                
                with col2:
                    if user_info.get('role') in ['Admin', 'Owner', 'Editor']:
                        if st.button(f"Share", key=f"share_{workspace['name']}"):
                            st.info("Would open sharing interface")
                    else:
                        st.button(f"Share", disabled=True, key=f"share_{workspace['name']}_disabled")
                
                st.markdown("---")

def render_management_tab(ui, user_id):
    """Render team management tab"""
    st.header("⚙️ Team Management")
    
    user_info = get_demo_user_info(user_id)
    
    if user_info.get('role') not in ['Admin', 'Owner']:
        st.warning("⚠️ You don't have management permissions. Contact your team admin for access.")
        return
    
    # Team selection for management
    user_teams = user_info.get('teams', [])
    team_options = {
        st.session_state.demo_teams[team_id]['name']: team_id 
        for team_id in user_teams 
        if team_id in st.session_state.demo_teams
    }
    
    if not team_options:
        st.info("No teams available for management.")
        return
    
    selected_team_name = st.selectbox("Select Team to Manage", list(team_options.keys()))
    selected_team_id = team_options[selected_team_name]
    team = st.session_state.demo_teams[selected_team_id]
    
    # Team overview
    st.subheader(f"Managing: {team['name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Members", team['members'], help="Current team members")
    
    with col2:
        st.metric("Workspaces", len(team['workspaces']), help="Active workspaces")
    
    with col3:
        st.metric("Subscription", team['tier'].title(), help="Current subscription tier")
    
    with col4:
        storage_pct = (float(team['storage_used'].split()[0]) / float(team['storage_limit'].split()[0])) * 100
        st.metric("Storage Usage", f"{storage_pct:.1f}%", help="Storage utilization")
    
    # Management sections
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Members", "📧 Invitations", "📁 Workspaces", "⚙️ Settings"])
    
    with tab1:
        st.subheader("Team Members")
        
        # Sample member data
        member_data = [
            {"Name": "Alice Johnson", "Email": "alice@acme.com", "Role": "Owner", "Joined": "2024-01-15", "Status": "Active"},
            {"Name": "Bob Smith", "Email": "bob@acme.com", "Role": "Admin", "Joined": "2024-02-01", "Status": "Active"},
            {"Name": "Carol Davis", "Email": "carol@acme.com", "Role": "Editor", "Joined": "2024-02-15", "Status": "Active"},
            {"Name": "Dave Wilson", "Email": "dave@acme.com", "Role": "Viewer", "Joined": "2024-03-01", "Status": "Active"}
        ]
        
        st.dataframe(member_data, use_container_width=True)
        
        # Member actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👥 Invite New Member"):
                show_invite_form(selected_team_id)
        
        with col2:
            if st.button("📊 Member Analytics"):
                st.info("Would show member activity analytics")
    
    with tab2:
        st.subheader("Pending Invitations")
        
        # Sample invitation data
        invitation_data = [
            {"Email": "newdev@acme.com", "Role": "Editor", "Invited": "2024-03-05", "Expires": "2024-03-12", "Status": "Pending"},
            {"Email": "designer@acme.com", "Role": "Member", "Invited": "2024-03-03", "Expires": "2024-03-10", "Status": "Pending"}
        ]
        
        if invitation_data:
            st.dataframe(invitation_data, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Resend Invitations"):
                    st.success("Invitations resent!")
            
            with col2:
                if st.button("❌ Cancel Selected"):
                    st.info("Would cancel selected invitations")
        else:
            st.info("No pending invitations")
    
    with tab3:
        st.subheader("Workspace Management")
        
        workspace_data = []
        for ws_id in team['workspaces']:
            if ws_id in st.session_state.demo_workspaces:
                ws = st.session_state.demo_workspaces[ws_id]
                workspace_data.append({
                    "Name": ws['name'],
                    "Description": ws['description'],
                    "Content": ws['content_count'],
                    "Last Activity": ws['recent_activity']
                })
        
        st.dataframe(workspace_data, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📁 Create Workspace"):
                st.info("Would open workspace creation form")
        
        with col2:
            if st.button("⚙️ Manage Permissions"):
                st.info("Would open permission management")
        
        with col3:
            if st.button("📊 Workspace Analytics"):
                st.info("Would show workspace usage analytics")
    
    with tab4:
        st.subheader("Team Settings")
        
        # Team settings form
        with st.form("team_settings"):
            st.text_input("Team Name", value=team['name'])
            st.text_area("Description", value=team['description'])
            
            st.selectbox(
                "Subscription Tier",
                options=["free", "pro", "enterprise"],
                index=["free", "pro", "enterprise"].index(team['tier'])
            )
            
            st.checkbox("Allow member invitations", value=True)
            st.checkbox("Enable external sharing", value=False)
            st.checkbox("Require 2FA for all members", value=True)
            
            if st.form_submit_button("Save Settings"):
                st.success("Team settings updated!")

def show_invite_form(team_id):
    """Show member invitation form"""
    with st.form("invite_member"):
        st.subheader("Invite New Member")
        
        email = st.text_input("Email Address")
        role = st.selectbox(
            "Role",
            options=["viewer", "member", "editor", "admin"],
            format_func=lambda x: x.title()
        )
        
        message = st.text_area(
            "Personal Message (Optional)",
            placeholder="Welcome to our team! We're excited to have you join us."
        )
        
        if st.form_submit_button("Send Invitation"):
            if email and "@" in email:
                st.success(f"Invitation sent to {email} as {role.title()}!")
            else:
                st.error("Please enter a valid email address")

def render_analytics_tab(user_id):
    """Render analytics dashboard"""
    st.header("📊 Analytics Dashboard")
    
    user_info = get_demo_user_info(user_id)
    
    # Usage metrics
    st.subheader("📈 Usage Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Daily Active Users", "23", delta="3")
    
    with col2:
        st.metric("Content Created", "156", delta="12")
    
    with col3:
        st.metric("Transcriptions", "89", delta="8")
    
    with col4:
        st.metric("Storage Growth", "2.1 GB", delta="0.3 GB")
    
    # Charts (placeholder)
    st.subheader("📊 Activity Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Content Creation Over Time**")
        # Placeholder for chart
        chart_data = {
            "Date": ["2024-03-01", "2024-03-02", "2024-03-03", "2024-03-04", "2024-03-05"],
            "Transcriptions": [12, 15, 8, 22, 18],
            "Analyses": [5, 8, 3, 12, 9]
        }
        st.line_chart(chart_data, x="Date")
    
    with col2:
        st.markdown("**Team Activity Distribution**")
        # Placeholder for pie chart data
        activity_data = {
            "Development": 45,
            "Design": 25,
            "Marketing": 20,
            "Strategy": 10
        }
        st.bar_chart(activity_data)
    
    # Team performance
    if user_info.get('role') in ['Admin', 'Owner']:
        st.subheader("👥 Team Performance")
        
        performance_data = [
            {"Member": "Alice Johnson", "Content Created": 45, "Last Active": "2 hours ago", "Role": "Owner"},
            {"Member": "Bob Smith", "Content Created": 89, "Last Active": "1 hour ago", "Role": "Admin"},
            {"Member": "Carol Davis", "Content Created": 67, "Last Active": "3 hours ago", "Role": "Editor"},
            {"Member": "Dave Wilson", "Content Created": 23, "Last Active": "1 day ago", "Role": "Viewer"}
        ]
        
        st.dataframe(performance_data, use_container_width=True)
    
    # Export options
    st.subheader("📤 Export Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Usage Report"):
            st.info("Would generate and download usage report")
    
    with col2:
        if st.button("👥 Export Member Activity"):
            st.info("Would generate member activity report")
    
    with col3:
        if st.button("💾 Export All Data"):
            st.info("Would export comprehensive analytics data")

if __name__ == "__main__":
    main()