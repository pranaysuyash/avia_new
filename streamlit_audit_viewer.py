#!/usr/bin/env python3
"""
Streamlit Audit Log Viewer
Administrative interface for viewing and analyzing audit logs
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import json

from ui_styles_refactored import apply_theme
from enhanced_components_refactored import (
    enhanced_button,
    enhanced_card,
    enhanced_progress_indicator,
    enhanced_metric,
    enhanced_tabs
)

class AuditLogViewer:
    """Audit log viewing and analysis interface"""
    
    def __init__(self):
        self.api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000/api')
        self.headers = self._get_auth_headers()
    
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
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
    
    def render_main(self):
        """Render main audit viewer interface"""
        st.title("🔍 Audit Log Viewer")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Check admin access
        user = st.session_state.get('user', {})
        if user.get('role') != 'admin':
            st.error("Admin access required")
            return
        
        # Tab selection
        tabs = ["Log Search", "Security Events", "User Activity", 
                "Compliance Reports", "Analytics", "Export"]
        selected_tab = enhanced_tabs(tabs, key="audit_tabs")
        
        if selected_tab == "Log Search":
            self._render_log_search()
        elif selected_tab == "Security Events":
            self._render_security_events()
        elif selected_tab == "User Activity":
            self._render_user_activity()
        elif selected_tab == "Compliance Reports":
            self._render_compliance_reports()
        elif selected_tab == "Analytics":
            self._render_analytics()
        elif selected_tab == "Export":
            self._render_export()
    
    def _render_log_search(self):
        """Render log search interface"""
        st.header("Audit Log Search")
        
        # Search filters
        with st.form("log_search"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=date.today() - timedelta(days=7),
                    max_value=date.today()
                )
                
                user_id = st.number_input(
                    "User ID (optional)",
                    min_value=0,
                    value=0,
                    help="Enter 0 to search all users"
                )
                
                resource_type = st.selectbox(
                    "Resource Type",
                    ["All", "transcript", "user", "team", "subscription", "system"]
                )
            
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=date.today(),
                    max_value=date.today()
                )
                
                # Get event types
                event_types_response = self._api_request('GET', '/audit/event-types')
                event_types = event_types_response.get('event_types', []) if event_types_response else []
                
                event_type = st.selectbox(
                    "Event Type",
                    ["All"] + event_types
                )
                
                result_filter = st.selectbox(
                    "Result",
                    ["All", "success", "failure", "error"]
                )
            
            search_button = st.form_submit_button("Search Logs")
        
        if search_button:
            # Build query parameters
            params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'limit': 100
            }
            
            if user_id > 0:
                params['user_id'] = user_id
            
            if event_type != "All":
                params['event_type'] = event_type
            
            if resource_type != "All":
                params['resource_type'] = resource_type
            
            if result_filter != "All":
                params['result'] = result_filter
            
            # Fetch logs
            logs_response = self._api_request('GET', '/audit/logs', params)
            
            if logs_response:
                self._display_logs(logs_response)
    
    def _render_security_events(self):
        """Render security events view"""
        st.header("Security Events Monitor")
        
        # Time range selector
        days = st.slider("Days to show", 1, 30, 7)
        
        # Fetch security events
        events = self._api_request('GET', '/audit/logs/security', {'days': days})
        
        if events and events.get('logs'):
            # Security alerts
            st.subheader("🚨 Recent Security Alerts")
            
            critical_events = [
                log for log in events['logs']
                if log['event_type'] in ['login_failed', 'user_suspend', 'system_error']
            ]
            
            if critical_events:
                for event in critical_events[:5]:
                    with enhanced_card():
                        col1, col2, col3 = st.columns([1, 3, 2])
                        
                        with col1:
                            icon = {
                                'login_failed': '🔐',
                                'user_suspend': '⛔',
                                'system_error': '❌'
                            }.get(event['event_type'], '⚠️')
                            st.write(f"### {icon}")
                        
                        with col2:
                            st.write(f"**{event['action']}**")
                            st.caption(f"User: {event['username'] or 'Unknown'}")
                            if event.get('ip_address'):
                                st.caption(f"IP: {event['ip_address']}")
                        
                        with col3:
                            timestamp = datetime.fromisoformat(event['timestamp'])
                            st.caption(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                            if event.get('error_message'):
                                st.error(event['error_message'])
            
            # Failed login attempts chart
            st.subheader("Failed Login Attempts")
            
            failed_logins = [
                log for log in events['logs']
                if log['event_type'] == 'login_failed'
            ]
            
            if failed_logins:
                # Group by date
                df_failed = pd.DataFrame(failed_logins)
                df_failed['date'] = pd.to_datetime(df_failed['timestamp']).dt.date
                
                daily_failures = df_failed.groupby('date').size().reset_index(name='count')
                
                fig = px.bar(
                    daily_failures,
                    x='date',
                    y='count',
                    title='Failed Login Attempts by Day'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Top failed usernames
                if 'username' in df_failed.columns:
                    top_failed = df_failed['username'].value_counts().head(10)
                    
                    st.subheader("Top Failed Login Usernames")
                    for username, count in top_failed.items():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(username or "Unknown")
                        with col2:
                            st.write(f"{count} attempts")
    
    def _render_user_activity(self):
        """Render user activity tracking"""
        st.header("User Activity Tracking")
        
        # User selection
        user_id = st.number_input(
            "Enter User ID",
            min_value=1,
            help="Enter the ID of the user to track"
        )
        
        days = st.slider("Days of activity", 1, 90, 30)
        
        if st.button("Load User Activity"):
            activity = self._api_request(
                'GET',
                f'/audit/logs/user/{user_id}',
                {'days': days, 'limit': 500}
            )
            
            if activity and activity.get('logs'):
                # User info
                logs = activity['logs']
                if logs:
                    st.subheader(f"Activity for User: {logs[0].get('username', 'Unknown')}")
                
                # Activity timeline
                df = pd.DataFrame(logs)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Activity by type
                activity_types = df['event_type'].value_counts()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_pie = px.pie(
                        values=activity_types.values,
                        names=activity_types.index,
                        title='Activity Distribution'
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Activity over time
                    df['date'] = df['timestamp'].dt.date
                    daily_activity = df.groupby('date').size().reset_index(name='count')
                    
                    fig_line = px.line(
                        daily_activity,
                        x='date',
                        y='count',
                        title='Daily Activity',
                        markers=True
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                
                # Recent activities
                st.subheader("Recent Activities")
                for _, log in df.head(20).iterrows():
                    with st.expander(
                        f"{log['timestamp'].strftime('%Y-%m-%d %H:%M')} - {log['event_type']}"
                    ):
                        st.write(f"**Action:** {log['action']}")
                        st.write(f"**Result:** {log['result']}")
                        if log.get('resource_type'):
                            st.write(f"**Resource:** {log['resource_type']} ({log.get('resource_id', 'N/A')})")
                        if log.get('details'):
                            st.json(log['details'])
    
    def _render_compliance_reports(self):
        """Render compliance reporting interface"""
        st.header("Compliance Reports")
        
        with st.form("compliance_report"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Report Start Date",
                    value=date.today() - timedelta(days=30)
                )
                
                report_type = st.selectbox(
                    "Report Type",
                    ["Full Audit Report", "User Access Report", "Data Export Report", "Security Report"]
                )
            
            with col2:
                end_date = st.date_input(
                    "Report End Date",
                    value=date.today()
                )
                
                user_filter = st.number_input(
                    "Filter by User ID (0 for all)",
                    min_value=0,
                    value=0
                )
            
            generate_button = st.form_submit_button("Generate Report")
        
        if generate_button:
            # Generate compliance report
            params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
            if user_filter > 0:
                params['user_id'] = user_filter
            
            report = self._api_request('GET', '/audit/logs/compliance-report', params)
            
            if report:
                # Display report
                st.success("Report generated successfully")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    enhanced_metric(
                        "Total Events",
                        f"{report['summary']['total_events']:,}",
                        "In period"
                    )
                
                with col2:
                    enhanced_metric(
                        "Unique Users",
                        str(report['summary']['unique_users']),
                        "Active"
                    )
                
                with col3:
                    # Calculate success rate
                    result_dist = report.get('result_distribution', [])
                    success_count = next((r['count'] for r in result_dist if r['result'] == 'success'), 0)
                    total_count = sum(r['count'] for r in result_dist)
                    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                    
                    enhanced_metric(
                        "Success Rate",
                        f"{success_rate:.1f}%",
                        "Operations"
                    )
                
                with col4:
                    # Find most common event
                    event_dist = report.get('event_distribution', [])
                    if event_dist:
                        top_event = max(event_dist, key=lambda x: x['count'])
                        enhanced_metric(
                            "Top Event",
                            top_event['event_type'],
                            f"{top_event['count']} times"
                        )
                
                # Event distribution chart
                if report.get('event_distribution'):
                    st.subheader("Event Type Distribution")
                    
                    df_events = pd.DataFrame(report['event_distribution'])
                    
                    fig = px.bar(
                        df_events.head(15),
                        x='event_type',
                        y='count',
                        title='Top 15 Event Types'
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Top users
                if report.get('top_users'):
                    st.subheader("Most Active Users")
                    
                    df_users = pd.DataFrame(report['top_users'])
                    st.dataframe(df_users, use_container_width=True)
    
    def _render_analytics(self):
        """Render audit analytics dashboard"""
        st.header("Audit Analytics")
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.today() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today()
            )
        
        # Fetch logs for analysis
        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'limit': 1000
        }
        
        logs_response = self._api_request('GET', '/audit/logs', params)
        
        if logs_response and logs_response.get('logs'):
            logs = logs_response['logs']
            df = pd.DataFrame(logs)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Activity heatmap
            st.subheader("Activity Heatmap")
            
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            
            heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
            
            # Ensure correct day ordering
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
            heatmap_pivot = heatmap_pivot.reindex(day_order)
            
            fig_heatmap = px.imshow(
                heatmap_pivot,
                labels=dict(x="Hour of Day", y="Day of Week", color="Activity Count"),
                x=list(range(24)),
                y=day_order,
                color_continuous_scale='Blues'
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Success/Failure trends
            st.subheader("Operation Success Trends")
            
            df['date'] = df['timestamp'].dt.date
            result_trends = df.groupby(['date', 'result']).size().reset_index(name='count')
            
            fig_trends = px.line(
                result_trends,
                x='date',
                y='count',
                color='result',
                title='Daily Operation Results',
                markers=True
            )
            
            st.plotly_chart(fig_trends, use_container_width=True)
            
            # Resource access patterns
            if 'resource_type' in df.columns:
                st.subheader("Resource Access Patterns")
                
                resource_access = df[df['resource_type'].notna()]['resource_type'].value_counts().head(10)
                
                fig_resources = px.bar(
                    x=resource_access.values,
                    y=resource_access.index,
                    orientation='h',
                    title='Top 10 Accessed Resource Types',
                    labels={'x': 'Access Count', 'y': 'Resource Type'}
                )
                
                st.plotly_chart(fig_resources, use_container_width=True)
    
    def _render_export(self):
        """Render export interface"""
        st.header("Export Audit Logs")
        
        with st.form("export_logs"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=date.today() - timedelta(days=30)
                )
                
                export_format = st.selectbox(
                    "Export Format",
                    ["CSV", "JSON"]
                )
            
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=date.today()
                )
                
                # Get event types
                event_types_response = self._api_request('GET', '/audit/event-types')
                event_types = event_types_response.get('event_types', []) if event_types_response else []
                
                event_filter = st.selectbox(
                    "Filter by Event Type",
                    ["All"] + event_types
                )
            
            export_button = st.form_submit_button("Export Logs")
        
        if export_button:
            # Build export parameters
            params = {
                'format': export_format.lower(),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
            if event_filter != "All":
                params['event_type'] = event_filter
            
            # Make export request
            url = f"{self.api_base_url}/audit/logs/export"
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                # Provide download
                filename = f"audit_logs_{start_date}_{end_date}.{export_format.lower()}"
                
                st.download_button(
                    label=f"Download {export_format} File",
                    data=response.content,
                    file_name=filename,
                    mime="text/csv" if export_format == "CSV" else "application/json"
                )
                
                st.success(f"Export ready for download: {filename}")
                
            except requests.exceptions.RequestException as e:
                st.error(f"Export failed: {str(e)}")
    
    def _display_logs(self, logs_response: Dict):
        """Display logs in a formatted table"""
        logs = logs_response.get('logs', [])
        total = logs_response.get('total', 0)
        
        st.info(f"Found {total} logs (showing {len(logs)})")
        
        if logs:
            # Convert to DataFrame for display
            df = pd.DataFrame(logs)
            
            # Format timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Select columns to display
            display_columns = ['timestamp', 'event_type', 'username', 'action', 'result']
            if 'resource_type' in df.columns:
                display_columns.append('resource_type')
            if 'resource_id' in df.columns:
                display_columns.append('resource_id')
            
            # Display with expandable details
            for idx, row in df.iterrows():
                with st.expander(
                    f"{row['timestamp']} - {row['event_type']} - {row['action']}"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {row.get('username', 'Unknown')}")
                        st.write(f"**Result:** {row['result']}")
                        if row.get('ip_address'):
                            st.write(f"**IP Address:** {row['ip_address']}")
                    
                    with col2:
                        if row.get('resource_type'):
                            st.write(f"**Resource Type:** {row['resource_type']}")
                        if row.get('resource_id'):
                            st.write(f"**Resource ID:** {row['resource_id']}")
                    
                    if row.get('details'):
                        st.subheader("Details")
                        st.json(row['details'])
                    
                    if row.get('error_message'):
                        st.error(f"Error: {row['error_message']}")

# Initialize and render
def main():
    """Main function to render audit viewer"""
    viewer = AuditLogViewer()
    viewer.render_main()

if __name__ == "__main__":
    main()