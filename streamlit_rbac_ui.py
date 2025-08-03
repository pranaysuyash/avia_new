#!/usr/bin/env python3
"""
Streamlit RBAC Management UI
Interface for managing roles, permissions, and team access
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import requests
import json

from auth.rbac_service import Permission, ResourceType, RolePermissions, UserRole, TeamRole
from ui_styles_refactored import apply_theme
from enhanced_components_refactored import (
    enhanced_button,
    enhanced_card,
    enhanced_table,
    enhanced_select,
    enhanced_tabs
)

class RBACManagementUI:
    """Role-Based Access Control Management Interface"""
    
    def __init__(self):
        self.api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000/api')
        self.headers = self._get_auth_headers()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if 'access_token' in st.session_state:
            return {'Authorization': f"Bearer {st.session_state.access_token}"}
        return {}
    
    def _api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
    
    def render_main(self):
        """Render main RBAC management interface"""
        st.title("🔐 Access Control Management")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Check if user has permission to view this page
        current_user = st.session_state.get('user', {})
        if current_user.get('role') not in ['admin', 'owner']:
            st.error("You don't have permission to access this page.")
            return
        
        # Tab selection
        tabs = ["Team Management", "Role Permissions", "User Access", "Audit Log"]
        selected_tab = enhanced_tabs(tabs, key="rbac_tabs")
        
        if selected_tab == "Team Management":
            self._render_team_management()
        elif selected_tab == "Role Permissions":
            self._render_role_permissions()
        elif selected_tab == "User Access":
            self._render_user_access()
        elif selected_tab == "Audit Log":
            self._render_audit_log()
    
    def _render_team_management(self):
        """Render team management interface"""
        st.header("Team Management")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if enhanced_button("➕ Create Team", "primary", key="create_team_btn"):
                st.session_state.show_create_team = True
        
        # Create team dialog
        if st.session_state.get('show_create_team', False):
            self._render_create_team_dialog()
        
        # List teams
        teams = self._api_request('GET', '/teams')
        
        if teams:
            for team in teams:
                with enhanced_card():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.subheader(team['name'])
                        if team.get('description'):
                            st.caption(team['description'])
                        
                        # Team stats
                        stats_col1, stats_col2, stats_col3 = st.columns(3)
                        with stats_col1:
                            st.metric("Members", f"{team['member_count']}/{team['max_members']}")
                        with stats_col2:
                            st.metric("Storage", f"{team['storage_used_mb']:.1f}/{team['storage_quota_mb']} MB")
                        with stats_col3:
                            st.metric("Transcripts", team['transcript_count'])
                    
                    with col2:
                        st.caption("Your Role")
                        st.write(f"**{team['user_role']}**")
                    
                    with col3:
                        st.caption("Status")
                        status = "🟢 Active" if team['is_active'] else "🔴 Inactive"
                        st.write(status)
                    
                    with col4:
                        if enhanced_button("Manage", "secondary", key=f"manage_team_{team['id']}"):
                            st.session_state.selected_team = team
                            st.session_state.show_team_details = True
        
        # Team details dialog
        if st.session_state.get('show_team_details', False):
            self._render_team_details_dialog()
    
    def _render_create_team_dialog(self):
        """Render create team dialog"""
        with st.container():
            st.markdown("### Create New Team")
            
            with st.form("create_team_form"):
                name = st.text_input("Team Name", placeholder="Enter team name")
                description = st.text_area("Description", placeholder="Optional team description")
                
                col1, col2 = st.columns(2)
                with col1:
                    max_members = st.number_input("Max Members", min_value=2, max_value=100, value=10)
                with col2:
                    storage_quota = st.number_input("Storage Quota (MB)", min_value=100, max_value=100000, value=5000)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Create Team", type="primary"):
                        if name:
                            result = self._api_request('POST', '/teams', {
                                'name': name,
                                'description': description,
                                'max_members': max_members,
                                'storage_quota_mb': storage_quota
                            })
                            
                            if result:
                                st.success(f"Team '{name}' created successfully!")
                                st.session_state.show_create_team = False
                                st.rerun()
                        else:
                            st.error("Team name is required")
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_create_team = False
                        st.rerun()
    
    def _render_team_details_dialog(self):
        """Render team details and management"""
        team = st.session_state.selected_team
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {team['name']}")
            with col2:
                if enhanced_button("✖️ Close", "secondary", key="close_team_details"):
                    st.session_state.show_team_details = False
                    st.rerun()
            
            # Team settings
            with st.expander("Team Settings", expanded=True):
                with st.form("update_team_form"):
                    name = st.text_input("Team Name", value=team['name'])
                    description = st.text_area("Description", value=team.get('description', ''))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        max_members = st.number_input("Max Members", 
                                                    min_value=team['member_count'], 
                                                    max_value=100, 
                                                    value=team['max_members'])
                    with col2:
                        storage_quota = st.number_input("Storage Quota (MB)", 
                                                      min_value=100, 
                                                      max_value=100000, 
                                                      value=team['storage_quota_mb'])
                    
                    is_active = st.checkbox("Team Active", value=team['is_active'])
                    
                    if st.form_submit_button("Update Settings"):
                        result = self._api_request('PUT', f"/teams/{team['id']}", {
                            'name': name,
                            'description': description,
                            'max_members': max_members,
                            'storage_quota_mb': storage_quota,
                            'is_active': is_active
                        })
                        
                        if result:
                            st.success("Team settings updated!")
                            st.rerun()
            
            # Team members
            with st.expander("Team Members", expanded=True):
                members = self._api_request('GET', f"/teams/{team['id']}/members")
                
                if members:
                    # Add member button
                    if team['user_role'] in ['owner', 'admin']:
                        if enhanced_button("➕ Invite Member", "primary", key="invite_member"):
                            st.session_state.show_invite_member = True
                    
                    # Members table
                    member_data = []
                    for member in members:
                        member_data.append({
                            'User': member['user']['full_name'] or member['user']['username'],
                            'Email': member['user']['email'],
                            'Role': member['role'],
                            'Joined': datetime.fromisoformat(member['joined_at']).strftime('%Y-%m-%d'),
                            'ID': member['id']
                        })
                    
                    df = pd.DataFrame(member_data)
                    
                    # Display table with actions
                    for idx, row in df.iterrows():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                        
                        with col1:
                            st.write(row['User'])
                        with col2:
                            st.caption(row['Email'])
                        with col3:
                            if team['user_role'] in ['owner', 'admin'] and row['Role'] != 'owner':
                                new_role = st.selectbox(
                                    "Role",
                                    options=['admin', 'member', 'viewer'],
                                    index=['admin', 'member', 'viewer'].index(row['Role']),
                                    key=f"role_{row['ID']}"
                                )
                                
                                if new_role != row['Role']:
                                    if st.button("Update", key=f"update_{row['ID']}"):
                                        result = self._api_request('PUT', 
                                            f"/teams/{team['id']}/members/{row['ID']}", 
                                            {'role': new_role}
                                        )
                                        if result:
                                            st.success("Role updated!")
                                            st.rerun()
                            else:
                                st.write(row['Role'])
                        
                        with col4:
                            st.caption(row['Joined'])
                        
                        with col5:
                            if team['user_role'] in ['owner', 'admin'] and row['Role'] != 'owner':
                                if st.button("🗑️", key=f"remove_{row['ID']}"):
                                    if st.confirm(f"Remove {row['User']} from team?"):
                                        result = self._api_request('DELETE', 
                                            f"/teams/{team['id']}/members/{row['ID']}"
                                        )
                                        if result:
                                            st.success("Member removed!")
                                            st.rerun()
            
            # Invite member dialog
            if st.session_state.get('show_invite_member', False):
                self._render_invite_member_dialog(team['id'])
    
    def _render_invite_member_dialog(self, team_id: int):
        """Render invite member dialog"""
        with st.container():
            st.markdown("#### Invite Team Member")
            
            with st.form("invite_member_form"):
                email = st.text_input("Email Address", placeholder="user@example.com")
                role = st.selectbox("Role", options=['member', 'viewer', 'admin'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Send Invite"):
                        if email:
                            result = self._api_request('POST', f"/teams/{team_id}/invite", {
                                'email': email,
                                'role': role
                            })
                            
                            if result:
                                st.success(f"Invitation sent to {email}")
                                st.session_state.show_invite_member = False
                                st.rerun()
                        else:
                            st.error("Email is required")
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_invite_member = False
                        st.rerun()
    
    def _render_role_permissions(self):
        """Render role permissions matrix"""
        st.header("Role Permissions")
        
        st.markdown("""
        This matrix shows the permissions granted to each role in the system.
        System roles apply globally, while team roles apply within team contexts.
        """)
        
        # System roles
        st.subheader("System Roles")
        
        system_permissions = []
        for role, perms in RolePermissions.SYSTEM_ROLES.items():
            system_permissions.append({
                'Role': role.value.upper(),
                'Permissions': len(perms),
                'Key Permissions': ', '.join([p.value for p in list(perms)[:5]]) + ('...' if len(perms) > 5 else '')
            })
        
        df_system = pd.DataFrame(system_permissions)
        st.dataframe(df_system, use_container_width=True)
        
        # Team roles
        st.subheader("Team Roles")
        
        team_permissions = []
        for role, perms in RolePermissions.TEAM_ROLES.items():
            team_permissions.append({
                'Role': role.value.upper(),
                'Permissions': len(perms),
                'Key Permissions': ', '.join([p.value for p in list(perms)[:5]]) + ('...' if len(perms) > 5 else '')
            })
        
        df_team = pd.DataFrame(team_permissions)
        st.dataframe(df_team, use_container_width=True)
        
        # Detailed permissions view
        with st.expander("View Detailed Permissions"):
            selected_role_type = st.radio("Role Type", ["System Roles", "Team Roles"])
            
            if selected_role_type == "System Roles":
                selected_role = st.selectbox("Select Role", 
                    options=[r.value for r in UserRole])
                
                if selected_role:
                    role_enum = UserRole(selected_role)
                    perms = RolePermissions.SYSTEM_ROLES.get(role_enum, set())
                    
                    st.markdown(f"**{selected_role.upper()} Permissions:**")
                    
                    # Group permissions by category
                    perm_categories = {}
                    for perm in perms:
                        category = perm.value.split(':')[0]
                        if category not in perm_categories:
                            perm_categories[category] = []
                        perm_categories[category].append(perm.value)
                    
                    for category, perms_list in sorted(perm_categories.items()):
                        st.markdown(f"**{category.title()}:**")
                        for perm in sorted(perms_list):
                            st.markdown(f"- {perm}")
            
            else:  # Team Roles
                selected_role = st.selectbox("Select Role", 
                    options=[r.value for r in TeamRole])
                
                if selected_role:
                    role_enum = TeamRole(selected_role)
                    perms = RolePermissions.TEAM_ROLES.get(role_enum, set())
                    
                    st.markdown(f"**{selected_role.upper()} Permissions:**")
                    
                    # Group permissions by category
                    perm_categories = {}
                    for perm in perms:
                        category = perm.value.split(':')[0]
                        if category not in perm_categories:
                            perm_categories[category] = []
                        perm_categories[category].append(perm.value)
                    
                    for category, perms_list in sorted(perm_categories.items()):
                        st.markdown(f"**{category.title()}:**")
                        for perm in sorted(perms_list):
                            st.markdown(f"- {perm}")
    
    def _render_user_access(self):
        """Render user access management"""
        st.header("User Access Management")
        
        # Search/filter
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("Search users", placeholder="Name, email, or username")
        with col2:
            role_filter = st.selectbox("Filter by role", 
                options=["All", "admin", "user", "viewer"])
        with col3:
            status_filter = st.selectbox("Filter by status", 
                options=["All", "Active", "Inactive", "Locked"])
        
        # Get users (this would be an admin endpoint)
        if st.session_state.get('user', {}).get('role') == 'admin':
            users = self._api_request('GET', '/admin/users')
            
            if users:
                # Filter users
                filtered_users = users
                if search:
                    filtered_users = [u for u in filtered_users 
                                    if search.lower() in u.get('username', '').lower() 
                                    or search.lower() in u.get('email', '').lower()
                                    or search.lower() in u.get('full_name', '').lower()]
                
                if role_filter != "All":
                    filtered_users = [u for u in filtered_users if u.get('role') == role_filter]
                
                if status_filter != "All":
                    if status_filter == "Active":
                        filtered_users = [u for u in filtered_users if u.get('is_active')]
                    elif status_filter == "Inactive":
                        filtered_users = [u for u in filtered_users if not u.get('is_active')]
                    elif status_filter == "Locked":
                        filtered_users = [u for u in filtered_users if u.get('locked_until')]
                
                # Display users
                for user in filtered_users:
                    with enhanced_card():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{user.get('full_name') or user['username']}**")
                            st.caption(user['email'])
                        
                        with col2:
                            new_role = st.selectbox(
                                "Role",
                                options=['admin', 'user', 'viewer'],
                                index=['admin', 'user', 'viewer'].index(user['role']),
                                key=f"user_role_{user['id']}"
                            )
                            
                            if new_role != user['role']:
                                if st.button("Update", key=f"update_user_{user['id']}"):
                                    # Update user role
                                    result = self._api_request('PUT', 
                                        f"/admin/users/{user['id']}/role", 
                                        {'role': new_role}
                                    )
                                    if result:
                                        st.success("Role updated!")
                                        st.rerun()
                        
                        with col3:
                            is_active = st.checkbox("Active", 
                                                  value=user.get('is_active', True),
                                                  key=f"active_{user['id']}")
                            
                            if is_active != user.get('is_active', True):
                                # Update user status
                                result = self._api_request('PUT', 
                                    f"/admin/users/{user['id']}/status", 
                                    {'is_active': is_active}
                                )
                                if result:
                                    st.success("Status updated!")
                                    st.rerun()
                        
                        with col4:
                            if st.button("View Details", key=f"view_{user['id']}"):
                                st.session_state.selected_user = user
                                st.session_state.show_user_details = True
        
        # User details dialog
        if st.session_state.get('show_user_details', False):
            self._render_user_details_dialog()
    
    def _render_user_details_dialog(self):
        """Render user details dialog"""
        user = st.session_state.selected_user
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### User Details: {user.get('full_name') or user['username']}")
            with col2:
                if enhanced_button("✖️ Close", "secondary", key="close_user_details"):
                    st.session_state.show_user_details = False
                    st.rerun()
            
            # User info
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Email:**", user['email'])
                st.write("**Username:**", user['username'])
                st.write("**Role:**", user['role'])
                st.write("**Status:**", "Active" if user.get('is_active') else "Inactive")
            
            with col2:
                st.write("**Created:**", datetime.fromisoformat(user['created_at']).strftime('%Y-%m-%d'))
                st.write("**Last Login:**", 
                        datetime.fromisoformat(user['last_login']).strftime('%Y-%m-%d %H:%M') 
                        if user.get('last_login') else "Never")
                st.write("**Verified:**", "✅" if user.get('is_verified') else "❌")
                st.write("**MFA:**", "Enabled" if user.get('mfa_enabled') else "Disabled")
            
            # User teams
            st.subheader("Team Memberships")
            if user.get('teams'):
                for team in user['teams']:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{team['name']}**")
                    with col2:
                        st.caption(team['role'])
            else:
                st.info("User is not a member of any teams")
            
            # User activity
            st.subheader("Recent Activity")
            # This would show recent transcripts, API calls, etc.
            st.info("Activity tracking coming soon...")
    
    def _render_audit_log(self):
        """Render audit log"""
        st.header("Access Audit Log")
        
        st.markdown("""
        Monitor access control events and permission changes across the system.
        """)
        
        # Date range filter
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        with col3:
            event_type = st.selectbox("Event Type", 
                options=["All", "Permission Granted", "Permission Denied", 
                        "Role Changed", "Team Access", "API Access"])
        
        # Mock audit log data
        audit_logs = [
            {
                'timestamp': '2024-01-20 10:30:45',
                'user': 'john.doe',
                'event': 'Permission Granted',
                'resource': 'transcript:123',
                'permission': 'transcript:read',
                'status': 'Success'
            },
            {
                'timestamp': '2024-01-20 10:28:12',
                'user': 'jane.smith',
                'event': 'Permission Denied',
                'resource': 'team:456',
                'permission': 'team:delete',
                'status': 'Denied'
            },
            {
                'timestamp': '2024-01-20 10:25:00',
                'user': 'admin',
                'event': 'Role Changed',
                'resource': 'user:789',
                'permission': 'user:manage_roles',
                'status': 'Success',
                'details': 'Changed role from viewer to member'
            }
        ]
        
        # Display logs
        for log in audit_logs:
            with enhanced_card():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{log['timestamp']}**")
                    st.caption(f"User: {log['user']}")
                
                with col2:
                    st.write(f"**{log['event']}**")
                    st.caption(f"Permission: {log['permission']}")
                
                with col3:
                    st.write(f"Resource: {log['resource']}")
                    if log.get('details'):
                        st.caption(log['details'])
                
                with col4:
                    if log['status'] == 'Success':
                        st.success(log['status'])
                    else:
                        st.error(log['status'])

# Initialize and render
def main():
    """Main function to render RBAC UI"""
    rbac_ui = RBACManagementUI()
    rbac_ui.render_main()

if __name__ == "__main__":
    main()