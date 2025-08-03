#!/usr/bin/env python3
"""
Streamlit Comprehensive Admin Dashboard
Unified administrative interface for system management
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from ui_styles_refactored import apply_theme
from enhanced_components_refactored import (
    enhanced_button,
    enhanced_card,
    enhanced_progress_indicator,
    enhanced_metric,
    enhanced_tabs
)

# Import specialized admin components
from streamlit_admin_usage_dashboard import AdminUsageDashboard

class AdminDashboard:
    """Comprehensive admin dashboard"""
    
    def __init__(self):
        self.api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000/api')
        self.headers = self._get_auth_headers()
        self.usage_dashboard = AdminUsageDashboard()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if 'access_token' in st.session_state:
            return {'Authorization': f"Bearer {st.session_state.access_token}"}
        return {}
    
    def _api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Make API request with error handling"""
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
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
            return None
    
    def render_main(self):
        """Render main admin dashboard"""
        st.set_page_config(
            page_title="Admin Dashboard",
            page_icon="👑",
            layout="wide"
        )
        
        st.title("👑 Admin Dashboard")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Check admin access
        user = st.session_state.get('user', {})
        if user.get('role') != 'admin':
            st.error("Admin access required")
            st.info("Please login with an admin account to access this dashboard.")
            return
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            
            # Main sections
            main_section = st.radio(
                "Main Section",
                ["Dashboard", "Users", "Teams", "Subscriptions", "System", "Reports"]
            )
            
            st.divider()
            
            # Quick stats
            st.subheader("Quick Stats")
            self._render_quick_stats()
            
            st.divider()
            
            # Quick actions
            st.subheader("Quick Actions")
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
            
            if st.button("📧 Send Announcement", use_container_width=True):
                st.session_state.show_announcement = True
            
            if st.button("⚠️ System Alert", use_container_width=True):
                st.session_state.show_system_alert = True
        
        # Main content area
        if main_section == "Dashboard":
            self._render_dashboard_section()
        elif main_section == "Users":
            self._render_users_section()
        elif main_section == "Teams":
            self._render_teams_section()
        elif main_section == "Subscriptions":
            self._render_subscriptions_section()
        elif main_section == "System":
            self._render_system_section()
        elif main_section == "Reports":
            self._render_reports_section()
        
        # Modals
        self._render_modals()
    
    def _render_quick_stats(self):
        """Render quick statistics in sidebar"""
        # Get stats from API
        stats = self._api_request('GET', '/admin/stats/quick')
        
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Users", stats.get('total_users', 0))
                st.metric("Teams", stats.get('total_teams', 0))
            with col2:
                st.metric("Active", stats.get('active_users', 0))
                st.metric("Revenue", f"${stats.get('mrr', 0):,}")
        else:
            # Mock data if API not available
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Users", "1,234")
                st.metric("Teams", "156")
            with col2:
                st.metric("Active", "892")
                st.metric("Revenue", "$25,600")
    
    def _render_dashboard_section(self):
        """Render main dashboard section"""
        # Tab selection
        tabs = ["Overview", "Analytics", "Activity", "Alerts"]
        selected_tab = enhanced_tabs(tabs, key="dashboard_tabs")
        
        if selected_tab == "Overview":
            self._render_overview_tab()
        elif selected_tab == "Analytics":
            # Use the usage dashboard analytics
            self.usage_dashboard._render_system_overview()
        elif selected_tab == "Activity":
            self._render_activity_tab()
        elif selected_tab == "Alerts":
            self._render_alerts_tab()
    
    def _render_overview_tab(self):
        """Render overview tab"""
        st.header("System Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            enhanced_metric(
                "Total Users",
                "1,234",
                "+12% from last month",
                "users_metric"
            )
        
        with col2:
            enhanced_metric(
                "Active Today",
                "342",
                "27.7% of total",
                "active_metric"
            )
        
        with col3:
            enhanced_metric(
                "Transcripts Today",
                "856",
                "+45 from yesterday",
                "transcripts_metric"
            )
        
        with col4:
            enhanced_metric(
                "System Health",
                "98.5%",
                "All systems operational",
                "health_metric"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("User Growth")
            self._render_user_growth_chart()
        
        with col2:
            st.subheader("Revenue Trend")
            self._render_revenue_trend_chart()
        
        # Recent activity
        st.subheader("Recent Activity")
        self._render_recent_activity()
    
    def _render_users_section(self):
        """Render users management section"""
        st.header("User Management")
        
        # Search and filters
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            search = st.text_input("Search users", placeholder="Name, email, or username...")
        
        with col2:
            role_filter = st.selectbox("Role", ["All", "Admin", "User", "Viewer"])
        
        with col3:
            status_filter = st.selectbox("Status", ["All", "Active", "Inactive", "Suspended"])
        
        with col4:
            plan_filter = st.selectbox("Plan", ["All", "Free", "Basic", "Pro", "Enterprise"])
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if enhanced_button("➕ Add User", "primary", key="add_user"):
                st.session_state.show_add_user = True
        
        with col2:
            if enhanced_button("📊 Export", "secondary", key="export_users"):
                st.info("Exporting users...")
        
        with col3:
            if enhanced_button("📧 Bulk Email", "secondary", key="bulk_email"):
                st.session_state.show_bulk_email = True
        
        with col4:
            if enhanced_button("🔄 Refresh", "secondary", key="refresh_users"):
                st.rerun()
        
        # Users table
        st.subheader("Users")
        self._render_users_table(search, role_filter, status_filter, plan_filter)
    
    def _render_teams_section(self):
        """Render teams management section"""
        st.header("Team Management")
        
        # Teams overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Teams", "156")
        
        with col2:
            st.metric("Active Teams", "142")
        
        with col3:
            st.metric("Avg Team Size", "4.2")
        
        with col4:
            st.metric("Enterprise Teams", "23")
        
        # Teams list
        st.subheader("Teams")
        
        # Mock teams data
        teams_data = [
            {"name": "Marketing Team", "members": 8, "owner": "John Doe", "plan": "Pro", "created": "2024-01-15"},
            {"name": "Development", "members": 12, "owner": "Jane Smith", "plan": "Enterprise", "created": "2023-11-20"},
            {"name": "Sales Team", "members": 6, "owner": "Bob Wilson", "plan": "Pro", "created": "2024-02-01"},
            {"name": "Support", "members": 5, "owner": "Alice Brown", "plan": "Basic", "created": "2023-12-10"},
        ]
        
        for team in teams_data:
            with enhanced_card():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                
                with col1:
                    st.write(f"**{team['name']}**")
                    st.caption(f"Owner: {team['owner']}")
                
                with col2:
                    st.write(f"👥 {team['members']} members")
                
                with col3:
                    st.write(f"📦 {team['plan']} plan")
                
                with col4:
                    st.write(f"📅 {team['created']}")
                
                with col5:
                    if st.button("Manage", key=f"manage_team_{team['name']}"):
                        st.session_state.selected_team = team
    
    def _render_subscriptions_section(self):
        """Render subscriptions management section"""
        st.header("Subscription Management")
        
        # Use the usage dashboard subscription features
        self.usage_dashboard._render_plan_distribution()
        
        # Additional subscription management
        st.subheader("Subscription Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with enhanced_card():
                st.write("**Coupon Management**")
                if st.button("Create Coupon", key="create_coupon"):
                    st.session_state.show_create_coupon = True
                if st.button("View Active Coupons", key="view_coupons"):
                    st.session_state.show_coupons = True
        
        with col2:
            with enhanced_card():
                st.write("**Plan Management**")
                if st.button("Edit Plans", key="edit_plans"):
                    st.session_state.show_edit_plans = True
                if st.button("Feature Flags", key="feature_flags"):
                    st.session_state.show_feature_flags = True
        
        with col3:
            with enhanced_card():
                st.write("**Billing**")
                if st.button("Failed Payments", key="failed_payments"):
                    st.session_state.show_failed_payments = True
                if st.button("Refunds", key="refunds"):
                    st.session_state.show_refunds = True
    
    def _render_system_section(self):
        """Render system management section"""
        st.header("System Management")
        
        tabs = ["Health", "Configuration", "Integrations", "Logs", "Backup"]
        selected_tab = enhanced_tabs(tabs, key="system_tabs")
        
        if selected_tab == "Health":
            self._render_system_health()
        elif selected_tab == "Configuration":
            self._render_system_configuration()
        elif selected_tab == "Integrations":
            self._render_integrations()
        elif selected_tab == "Logs":
            self._render_system_logs()
        elif selected_tab == "Backup":
            self._render_backup_restore()
    
    def _render_reports_section(self):
        """Render reports section"""
        st.header("Reports & Analytics")
        
        # Report types
        report_type = st.selectbox(
            "Select Report Type",
            ["User Activity", "Revenue Report", "Usage Analytics", "System Performance", "Audit Log"]
        )
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Generate report button
        if enhanced_button("Generate Report", "primary", key="generate_report"):
            st.info(f"Generating {report_type} report...")
            
            # Mock report generation
            if report_type == "User Activity":
                self._generate_user_activity_report(start_date, end_date)
            elif report_type == "Revenue Report":
                self._generate_revenue_report(start_date, end_date)
            elif report_type == "Usage Analytics":
                self.usage_dashboard._render_reports_tab()
        
        # Scheduled reports
        st.subheader("Scheduled Reports")
        self._render_scheduled_reports()
    
    def _render_user_growth_chart(self):
        """Render user growth chart"""
        # Mock data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        users = [1000 + i * 8 + (i % 7) * 3 for i in range(30)]
        
        df = pd.DataFrame({
            'Date': dates,
            'Users': users
        })
        
        fig = px.area(
            df,
            x='Date',
            y='Users',
            title='User Growth - Last 30 Days'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_revenue_trend_chart(self):
        """Render revenue trend chart"""
        # Mock data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        revenue = [20000 + i * 200 + (i % 5) * 500 for i in range(30)]
        
        df = pd.DataFrame({
            'Date': dates,
            'Revenue': revenue
        })
        
        fig = px.line(
            df,
            x='Date',
            y='Revenue',
            title='Daily Revenue - Last 30 Days',
            markers=True
        )
        
        fig.update_layout(yaxis_tickformat='$,.0f')
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_activity(self):
        """Render recent activity feed"""
        activities = [
            {"time": "2 minutes ago", "user": "john.doe", "action": "Created new transcript", "icon": "📝"},
            {"time": "5 minutes ago", "user": "jane.smith", "action": "Upgraded to Pro plan", "icon": "⬆️"},
            {"time": "12 minutes ago", "user": "bob.wilson", "action": "Joined Marketing Team", "icon": "👥"},
            {"time": "25 minutes ago", "user": "alice.brown", "action": "Exported 50 transcripts", "icon": "📊"},
            {"time": "1 hour ago", "user": "system", "action": "Completed daily backup", "icon": "💾"},
        ]
        
        for activity in activities:
            col1, col2, col3 = st.columns([1, 3, 2])
            
            with col1:
                st.write(activity['icon'])
            
            with col2:
                st.write(f"**{activity['user']}** {activity['action']}")
            
            with col3:
                st.caption(activity['time'])
    
    def _render_activity_tab(self):
        """Render activity tab"""
        st.subheader("System Activity")
        
        # Activity filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            activity_type = st.selectbox(
                "Activity Type",
                ["All", "User Actions", "System Events", "API Calls", "Errors"]
            )
        
        with col2:
            time_range = st.selectbox(
                "Time Range",
                ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
            )
        
        with col3:
            severity = st.selectbox(
                "Severity",
                ["All", "Info", "Warning", "Error", "Critical"]
            )
        
        # Activity stream
        st.write("")
        
        # Mock activity data
        activities = [
            {
                "timestamp": "2024-01-20 14:32:15",
                "type": "user_action",
                "severity": "info",
                "user": "john.doe@example.com",
                "action": "transcript.create",
                "details": "Created transcript 'Q4 Earnings Call'",
                "ip": "192.168.1.100"
            },
            {
                "timestamp": "2024-01-20 14:31:45",
                "type": "system_event",
                "severity": "warning",
                "user": "system",
                "action": "storage.threshold",
                "details": "Storage usage at 85% capacity",
                "ip": "N/A"
            },
            {
                "timestamp": "2024-01-20 14:30:22",
                "type": "api_call",
                "severity": "info",
                "user": "api_key_123***",
                "action": "api.transcribe",
                "details": "POST /api/transcripts - 200 OK (2.3s)",
                "ip": "203.0.113.42"
            },
            {
                "timestamp": "2024-01-20 14:28:10",
                "type": "error",
                "severity": "error",
                "user": "jane.smith@example.com",
                "action": "payment.failed",
                "details": "Payment failed: Card declined",
                "ip": "10.0.0.52"
            }
        ]
        
        for activity in activities:
            severity_colors = {
                "info": "blue",
                "warning": "orange",
                "error": "red",
                "critical": "red"
            }
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 4, 2])
                
                with col1:
                    st.caption(activity['timestamp'])
                
                with col2:
                    color = severity_colors.get(activity['severity'], 'gray')
                    st.markdown(f"<span style='color: {color}'>● {activity['severity'].upper()}</span>", unsafe_allow_html=True)
                
                with col3:
                    st.write(f"**{activity['user']}** - {activity['action']}")
                    st.caption(activity['details'])
                
                with col4:
                    st.caption(f"IP: {activity['ip']}")
                
                st.divider()
    
    def _render_alerts_tab(self):
        """Render alerts tab"""
        st.subheader("System Alerts")
        
        # Alert summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Critical", "2", "⬆️ 1")
        
        with col2:
            st.metric("Warning", "5", "⬇️ 2")
        
        with col3:
            st.metric("Info", "12", "➡️ 0")
        
        with col4:
            st.metric("Resolved Today", "8", "✅")
        
        # Active alerts
        st.write("")
        st.write("**Active Alerts**")
        
        alerts = [
            {
                "id": "ALT-001",
                "severity": "critical",
                "title": "Database connection pool exhausted",
                "description": "Connection pool is at 95% capacity",
                "time": "10 minutes ago",
                "affected": "All database operations"
            },
            {
                "id": "ALT-002",
                "severity": "critical",
                "title": "API rate limit exceeded for user",
                "description": "User 'api_user_42' exceeded 10,000 requests/hour",
                "time": "25 minutes ago",
                "affected": "API endpoint /transcribe"
            },
            {
                "id": "ALT-003",
                "severity": "warning",
                "title": "Disk space low on server-02",
                "description": "Only 15% disk space remaining",
                "time": "1 hour ago",
                "affected": "File uploads may fail"
            }
        ]
        
        for alert in alerts:
            severity_colors = {
                "critical": "#FF4444",
                "warning": "#FF8800",
                "info": "#4488FF"
            }
            
            with enhanced_card():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    color = severity_colors.get(alert['severity'], "#888888")
                    st.markdown(f"<h4 style='color: {color}'>● {alert['title']}</h4>", unsafe_allow_html=True)
                    st.write(alert['description'])
                    st.caption(f"ID: {alert['id']} | Time: {alert['time']} | Affected: {alert['affected']}")
                
                with col2:
                    if st.button("Acknowledge", key=f"ack_{alert['id']}"):
                        st.success("Alert acknowledged")
                    if st.button("Resolve", key=f"resolve_{alert['id']}"):
                        st.success("Alert resolved")
    
    def _render_users_table(self, search: str, role: str, status: str, plan: str):
        """Render users table with filters"""
        # Mock user data
        users_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "username": "johndoe",
                "role": "Admin",
                "status": "Active",
                "plan": "Pro",
                "created": "2023-10-15",
                "last_active": "2 hours ago"
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "username": "janesmith",
                "role": "User",
                "status": "Active",
                "plan": "Basic",
                "created": "2023-11-20",
                "last_active": "5 minutes ago"
            },
            {
                "id": 3,
                "name": "Bob Wilson",
                "email": "bob.wilson@example.com",
                "username": "bobwilson",
                "role": "User",
                "status": "Inactive",
                "plan": "Free",
                "created": "2024-01-05",
                "last_active": "3 days ago"
            }
        ]
        
        # Filter users
        filtered_users = users_data
        if search:
            filtered_users = [u for u in filtered_users if search.lower() in u['name'].lower() or search.lower() in u['email'].lower()]
        if role != "All":
            filtered_users = [u for u in filtered_users if u['role'] == role]
        if status != "All":
            filtered_users = [u for u in filtered_users if u['status'] == status]
        if plan != "All":
            filtered_users = [u for u in filtered_users if u['plan'] == plan]
        
        # Display users
        for user in filtered_users:
            with enhanced_card():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 2])
                
                with col1:
                    st.write(f"**{user['name']}**")
                    st.caption(f"{user['email']} | @{user['username']}")
                
                with col2:
                    status_color = "green" if user['status'] == "Active" else "gray"
                    st.markdown(f"<span style='color: {status_color}'>● {user['status']}</span>", unsafe_allow_html=True)
                    st.caption(f"Last active: {user['last_active']}")
                
                with col3:
                    st.write(f"**{user['role']}**")
                    st.caption(user['plan'])
                
                with col4:
                    st.caption("Since")
                    st.caption(user['created'])
                
                with col5:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("👁️", key=f"view_{user['id']}", help="View details"):
                            st.session_state.selected_user = user
                    with col_b:
                        if st.button("✏️", key=f"edit_{user['id']}", help="Edit user"):
                            st.session_state.edit_user = user
                    with col_c:
                        if st.button("🔒", key=f"suspend_{user['id']}", help="Suspend user"):
                            st.warning(f"User {user['name']} suspended")
    
    def _render_system_health(self):
        """Render system health monitoring"""
        st.subheader("System Health")
        
        # Overall health score
        health_score = 98.5
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = health_score,
                title = {'text': "Overall System Health"},
                delta = {'reference': 95},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen" if health_score > 90 else "orange"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 90], 'color': "lightgreen"},
                        {'range': [90, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Service status
        st.write("**Service Status**")
        
        services = [
            {"name": "API Server", "status": "operational", "uptime": "99.99%", "response": "45ms"},
            {"name": "Database", "status": "operational", "uptime": "99.95%", "response": "12ms"},
            {"name": "Redis Cache", "status": "operational", "uptime": "100%", "response": "2ms"},
            {"name": "File Storage", "status": "degraded", "uptime": "98.5%", "response": "150ms"},
            {"name": "Email Service", "status": "operational", "uptime": "99.8%", "response": "200ms"},
            {"name": "WebSocket Server", "status": "operational", "uptime": "99.9%", "response": "5ms"}
        ]
        
        cols = st.columns(3)
        for idx, service in enumerate(services):
            with cols[idx % 3]:
                status_colors = {
                    "operational": "green",
                    "degraded": "orange",
                    "down": "red"
                }
                
                with enhanced_card():
                    color = status_colors.get(service['status'], 'gray')
                    st.markdown(f"<h4>{service['name']}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: {color}'>● {service['status'].upper()}</span>", unsafe_allow_html=True)
                    st.caption(f"Uptime: {service['uptime']}")
                    st.caption(f"Response: {service['response']}")
    
    def _render_system_configuration(self):
        """Render system configuration"""
        st.subheader("System Configuration")
        
        # Configuration categories
        config_category = st.selectbox(
            "Configuration Category",
            ["General", "Security", "Email", "Storage", "API", "Limits"]
        )
        
        if config_category == "General":
            with st.form("general_config"):
                st.write("**General Settings**")
                
                app_name = st.text_input("Application Name", value="Transcription Platform")
                app_url = st.text_input("Application URL", value="https://app.example.com")
                timezone = st.selectbox("Default Timezone", ["UTC", "US/Eastern", "US/Pacific", "Europe/London"])
                maintenance_mode = st.checkbox("Maintenance Mode", value=False)
                
                if st.form_submit_button("Save Changes"):
                    st.success("Configuration saved")
        
        elif config_category == "Security":
            with st.form("security_config"):
                st.write("**Security Settings**")
                
                session_timeout = st.number_input("Session Timeout (minutes)", value=60, min_value=5)
                max_login_attempts = st.number_input("Max Login Attempts", value=5, min_value=3)
                password_min_length = st.number_input("Min Password Length", value=8, min_value=6)
                require_2fa = st.checkbox("Require 2FA for Admin", value=True)
                
                if st.form_submit_button("Save Changes"):
                    st.success("Security settings updated")
        
        elif config_category == "Limits":
            with st.form("limits_config"):
                st.write("**System Limits**")
                
                max_file_size = st.number_input("Max File Size (MB)", value=2048, min_value=100)
                max_transcript_length = st.number_input("Max Transcript Length (minutes)", value=240, min_value=60)
                rate_limit_per_hour = st.number_input("API Rate Limit (per hour)", value=1000, min_value=100)
                concurrent_transcriptions = st.number_input("Max Concurrent Transcriptions", value=10, min_value=1)
                
                if st.form_submit_button("Save Changes"):
                    st.success("Limits updated")
    
    def _render_integrations(self):
        """Render integrations management"""
        st.subheader("Integrations")
        
        integrations = [
            {
                "name": "Stripe",
                "description": "Payment processing",
                "status": "connected",
                "last_sync": "5 minutes ago"
            },
            {
                "name": "SendGrid",
                "description": "Email delivery",
                "status": "connected",
                "last_sync": "1 hour ago"
            },
            {
                "name": "AWS S3",
                "description": "File storage",
                "status": "connected",
                "last_sync": "real-time"
            },
            {
                "name": "Slack",
                "description": "Team notifications",
                "status": "disconnected",
                "last_sync": "N/A"
            },
            {
                "name": "Google Analytics",
                "description": "Usage analytics",
                "status": "connected",
                "last_sync": "10 minutes ago"
            }
        ]
        
        for integration in integrations:
            with enhanced_card():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{integration['name']}**")
                    st.caption(integration['description'])
                
                with col2:
                    status_color = "green" if integration['status'] == "connected" else "red"
                    st.markdown(f"<span style='color: {status_color}'>● {integration['status'].upper()}</span>", unsafe_allow_html=True)
                
                with col3:
                    st.caption(f"Last sync: {integration['last_sync']}")
                
                with col4:
                    if integration['status'] == "connected":
                        if st.button("Configure", key=f"config_{integration['name']}"):
                            st.info(f"Configure {integration['name']}")
                    else:
                        if st.button("Connect", key=f"connect_{integration['name']}"):
                            st.success(f"Connected to {integration['name']}")
    
    def _render_system_logs(self):
        """Render system logs viewer"""
        st.subheader("System Logs")
        
        # Log filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            log_level = st.selectbox("Log Level", ["All", "Debug", "Info", "Warning", "Error"])
        
        with col2:
            log_source = st.selectbox("Source", ["All", "API", "Database", "Auth", "Payment"])
        
        with col3:
            time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days"])
        
        with col4:
            if st.button("🔄 Refresh Logs"):
                st.rerun()
        
        # Search
        search = st.text_input("Search logs", placeholder="Search by message, error code, user...")
        
        # Mock log entries
        logs = [
            {
                "timestamp": "2024-01-20 14:35:22",
                "level": "INFO",
                "source": "API",
                "message": "POST /api/transcripts - 201 Created",
                "details": "User: john.doe@example.com, Duration: 1.2s"
            },
            {
                "timestamp": "2024-01-20 14:34:15",
                "level": "WARNING",
                "source": "Database",
                "message": "Slow query detected",
                "details": "Query took 2.5s: SELECT * FROM transcripts WHERE..."
            },
            {
                "timestamp": "2024-01-20 14:33:08",
                "level": "ERROR",
                "source": "Payment",
                "message": "Payment processing failed",
                "details": "Stripe error: card_declined for user_id: 12345"
            },
            {
                "timestamp": "2024-01-20 14:32:01",
                "level": "DEBUG",
                "source": "Auth",
                "message": "JWT token validated",
                "details": "Token for user: jane.smith@example.com"
            }
        ]
        
        # Display logs
        for log in logs:
            level_colors = {
                "DEBUG": "gray",
                "INFO": "blue",
                "WARNING": "orange",
                "ERROR": "red"
            }
            
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 5])
                
                with col1:
                    st.caption(log['timestamp'])
                
                with col2:
                    color = level_colors.get(log['level'], 'black')
                    st.markdown(f"<span style='color: {color}'>{log['level']}</span> | {log['source']}", unsafe_allow_html=True)
                
                with col3:
                    st.write(log['message'])
                    if log['details']:
                        st.caption(log['details'])
                
                st.divider()
        
        # Export logs button
        if st.button("📥 Export Logs"):
            st.info("Exporting logs...")
    
    def _render_backup_restore(self):
        """Render backup and restore interface"""
        st.subheader("Backup & Restore")
        
        # Backup status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Last Backup", "2 hours ago")
        
        with col2:
            st.metric("Backup Size", "4.2 GB")
        
        with col3:
            st.metric("Next Scheduled", "In 4 hours")
        
        # Backup actions
        st.write("")
        st.write("**Backup Actions**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if enhanced_button("🔄 Backup Now", "primary", key="backup_now"):
                with st.spinner("Creating backup..."):
                    import time
                    time.sleep(2)
                st.success("Backup completed successfully")
        
        with col2:
            if enhanced_button("📅 Schedule Backup", "secondary", key="schedule_backup"):
                st.info("Configure backup schedule")
        
        with col3:
            if enhanced_button("⚙️ Backup Settings", "secondary", key="backup_settings"):
                st.info("Configure backup settings")
        
        # Backup history
        st.write("")
        st.write("**Backup History**")
        
        backups = [
            {"id": "BKP-20240120-1200", "date": "2024-01-20 12:00", "size": "4.2 GB", "type": "Automatic", "status": "Success"},
            {"id": "BKP-20240120-0000", "date": "2024-01-20 00:00", "size": "4.1 GB", "type": "Automatic", "status": "Success"},
            {"id": "BKP-20240119-1200", "date": "2024-01-19 12:00", "size": "4.0 GB", "type": "Automatic", "status": "Success"},
            {"id": "BKP-20240119-0900", "date": "2024-01-19 09:00", "size": "3.9 GB", "type": "Manual", "status": "Success"},
        ]
        
        for backup in backups:
            with enhanced_card():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 2])
                
                with col1:
                    st.write(f"**{backup['id']}**")
                    st.caption(backup['date'])
                
                with col2:
                    st.write(f"💾 {backup['size']}")
                
                with col3:
                    st.caption(backup['type'])
                
                with col4:
                    st.success(backup['status'])
                
                with col5:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("📥", key=f"download_{backup['id']}", help="Download"):
                            st.info("Downloading backup...")
                    with col_b:
                        if st.button("♻️", key=f"restore_{backup['id']}", help="Restore"):
                            st.warning("Restore from this backup?")
    
    def _render_scheduled_reports(self):
        """Render scheduled reports section"""
        scheduled_reports = [
            {"name": "Weekly User Activity", "frequency": "Every Monday", "recipients": "admin@example.com", "next_run": "In 2 days"},
            {"name": "Monthly Revenue Report", "frequency": "1st of month", "recipients": "finance@example.com", "next_run": "In 10 days"},
            {"name": "Daily System Health", "frequency": "Daily at 9 AM", "recipients": "ops@example.com", "next_run": "Tomorrow"},
        ]
        
        for report in scheduled_reports:
            with enhanced_card():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{report['name']}**")
                    st.caption(f"To: {report['recipients']}")
                
                with col2:
                    st.caption(report['frequency'])
                
                with col3:
                    st.caption(f"Next: {report['next_run']}")
                
                with col4:
                    if st.button("Edit", key=f"edit_report_{report['name']}"):
                        st.info("Edit report schedule")
    
    def _render_modals(self):
        """Render modal dialogs"""
        # Add user modal
        if st.session_state.get('show_add_user', False):
            with st.container():
                st.markdown("### Add New User")
                with st.form("add_user_form"):
                    name = st.text_input("Full Name")
                    email = st.text_input("Email")
                    username = st.text_input("Username")
                    role = st.selectbox("Role", ["User", "Admin", "Viewer"])
                    plan = st.selectbox("Plan", ["Free", "Basic", "Pro", "Enterprise"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Add User"):
                            st.success("User added successfully")
                            st.session_state.show_add_user = False
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_add_user = False
        
        # System announcement modal
        if st.session_state.get('show_announcement', False):
            with st.container():
                st.markdown("### Send System Announcement")
                with st.form("announcement_form"):
                    title = st.text_input("Title")
                    message = st.text_area("Message")
                    priority = st.selectbox("Priority", ["Info", "Warning", "Critical"])
                    recipients = st.multiselect("Recipients", ["All Users", "Pro Users", "Enterprise Users", "Admins Only"])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Send"):
                            st.success("Announcement sent")
                            st.session_state.show_announcement = False
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_announcement = False

# Initialize and render
def main():
    """Main function to render admin dashboard"""
    dashboard = AdminDashboard()
    dashboard.render_main()

if __name__ == "__main__":
    main()