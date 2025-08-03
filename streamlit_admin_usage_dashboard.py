#!/usr/bin/env python3
"""
Streamlit Admin Usage Dashboard
Comprehensive admin view of system usage
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

class AdminUsageDashboard:
    """Admin usage monitoring dashboard"""
    
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
        """Render main admin dashboard"""
        st.title("👑 Admin Usage Dashboard")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Check admin access
        user = st.session_state.get('user', {})
        if user.get('role') != 'admin':
            st.error("Admin access required")
            return
        
        # Tab selection
        tabs = ["System Overview", "User Analytics", "Plan Distribution", 
                "Resource Usage", "Revenue Analytics", "Alerts & Actions"]
        selected_tab = enhanced_tabs(tabs, key="admin_tabs")
        
        if selected_tab == "System Overview":
            self._render_system_overview()
        elif selected_tab == "User Analytics":
            self._render_user_analytics()
        elif selected_tab == "Plan Distribution":
            self._render_plan_distribution()
        elif selected_tab == "Resource Usage":
            self._render_resource_usage()
        elif selected_tab == "Revenue Analytics":
            self._render_revenue_analytics()
        elif selected_tab == "Alerts & Actions":
            self._render_alerts_actions()
    
    def _render_system_overview(self):
        """Render system overview tab"""
        st.header("System Overview")
        
        # Get system-wide statistics
        trends = self._api_request('GET', '/usage/analytics/trends', {'days': 30})
        usage_by_plan = self._api_request('GET', '/usage/analytics/by-plan', {'days': 30})
        
        # Calculate totals
        if trends and 'trends' in trends:
            total_transcripts = 0
            total_minutes = 0
            total_api_calls = 0
            total_storage = 0
            
            for date_data in trends['trends'].values():
                total_transcripts += date_data.get('transcripts', 0)
                total_minutes += date_data.get('minutes', 0)
                total_api_calls += date_data.get('api_calls', 0)
                total_storage = max(total_storage, date_data.get('storage', 0))
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                enhanced_metric(
                    "Total Transcripts",
                    f"{int(total_transcripts):,}",
                    "Last 30 days"
                )
            
            with col2:
                enhanced_metric(
                    "Minutes Processed",
                    f"{int(total_minutes):,}",
                    "Last 30 days"
                )
            
            with col3:
                enhanced_metric(
                    "API Calls",
                    f"{int(total_api_calls):,}",
                    "Last 30 days"
                )
            
            with col4:
                enhanced_metric(
                    "Total Storage",
                    f"{total_storage:.1f} GB",
                    "Current usage"
                )
        
        # Usage trends chart
        st.subheader("System Usage Trends")
        if trends:
            self._render_system_trends_chart(trends)
        
        # Plan distribution
        if usage_by_plan:
            st.subheader("Usage by Plan")
            self._render_plan_usage_summary(usage_by_plan)
    
    def _render_user_analytics(self):
        """Render user analytics tab"""
        st.header("User Analytics")
        
        # Top users by usage type
        usage_type = st.selectbox(
            "Select Usage Type",
            ['transcripts', 'minutes', 'storage', 'api_calls']
        )
        
        days = st.slider("Period (days)", 7, 90, 30)
        limit = st.slider("Top N Users", 5, 50, 20)
        
        top_users = self._api_request(
            'GET',
            '/usage/analytics/top-users',
            {'usage_type': usage_type, 'days': days, 'limit': limit}
        )
        
        if top_users:
            # Create bar chart
            df = pd.DataFrame(top_users)
            
            fig = px.bar(
                df,
                x='username',
                y='total_usage',
                title=f'Top {limit} Users by {usage_type.title()}',
                labels={'total_usage': usage_type.title(), 'username': 'User'},
                color='total_usage',
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # User details table
            st.subheader("User Details")
            
            # Add action buttons to dataframe
            for idx, user in enumerate(top_users):
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                
                with col1:
                    st.write(f"**{user['full_name']}** (@{user['username']})")
                
                with col2:
                    st.write(f"{user['total_usage']:.0f} {usage_type}")
                
                with col3:
                    if st.button("View Details", key=f"view_{user['user_id']}"):
                        st.session_state.selected_user = user['user_id']
                
                with col4:
                    if st.button("Send Alert", key=f"alert_{user['user_id']}"):
                        st.info(f"Alert sent to {user['username']}")
                
                with col5:
                    if st.button("Limit Access", key=f"limit_{user['user_id']}"):
                        st.warning(f"Access limited for {user['username']}")
    
    def _render_plan_distribution(self):
        """Render plan distribution tab"""
        st.header("Plan Distribution")
        
        # Get usage by plan
        usage_by_plan = self._api_request('GET', '/usage/analytics/by-plan', {'days': 30})
        
        if usage_by_plan and 'usage_by_plan' in usage_by_plan:
            plans_data = usage_by_plan['usage_by_plan']
            
            # Create plan distribution pie chart
            plan_users = [(plan, data['unique_users']) for plan, data in plans_data.items()]
            df_plans = pd.DataFrame(plan_users, columns=['Plan', 'Users'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    df_plans,
                    values='Users',
                    names='Plan',
                    title='User Distribution by Plan'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Revenue estimation
                st.subheader("Revenue Estimation")
                
                plan_prices = {
                    'Free': 0,
                    'Basic': 29,
                    'Pro': 99,
                    'Enterprise': 499
                }
                
                total_mrr = 0
                for plan, data in plans_data.items():
                    users = data['unique_users']
                    price = plan_prices.get(plan, 0)
                    mrr = users * price
                    total_mrr += mrr
                    
                    if price > 0:
                        with enhanced_card():
                            st.write(f"**{plan}**")
                            st.write(f"Users: {users}")
                            st.write(f"MRR: ${mrr:,}")
                
                st.metric("Total MRR", f"${total_mrr:,}")
            
            # Usage breakdown by plan
            st.subheader("Usage Breakdown by Plan")
            
            for plan, data in plans_data.items():
                with st.expander(f"{plan} Plan ({data['unique_users']} users)"):
                    if 'usage' in data:
                        cols = st.columns(4)
                        for idx, (usage_type, usage_data) in enumerate(data['usage'].items()):
                            with cols[idx % 4]:
                                st.metric(
                                    usage_type.title(),
                                    f"{usage_data['total']:.0f}",
                                    f"{usage_data['records']} records"
                                )
    
    def _render_resource_usage(self):
        """Render resource usage tab"""
        st.header("Resource Usage Analysis")
        
        # Get resource distribution
        distribution = self._api_request(
            'GET',
            '/usage/analytics/resource-distribution',
            {'days': 30}
        )
        
        if distribution and 'distribution' in distribution:
            dist_data = distribution['distribution']
            
            if dist_data:
                # Resource type breakdown
                df_dist = pd.DataFrame(dist_data)
                
                fig = px.sunburst(
                    df_dist,
                    path=['resource_type'],
                    values='total_usage',
                    title='Resource Usage Distribution'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed metrics
                st.subheader("Resource Metrics")
                
                cols = st.columns(len(dist_data))
                for idx, resource in enumerate(dist_data):
                    with cols[idx]:
                        with enhanced_card():
                            st.write(f"**{resource['resource_type'].title()}**")
                            st.metric("Total Usage", f"{resource['total_usage']:.0f}")
                            st.metric("Unique Resources", resource['unique_resources'])
                            st.metric("Total Records", resource['total_records'])
        
        # Storage analysis
        st.subheader("Storage Analysis")
        
        # Mock storage data - would come from API
        storage_data = {
            'Audio Files': 245.6,
            'Video Files': 512.3,
            'Transcripts': 12.4,
            'Exports': 5.8,
            'Temporary': 8.9
        }
        
        df_storage = pd.DataFrame(
            list(storage_data.items()),
            columns=['Type', 'Size (GB)']
        )
        
        fig_storage = px.bar(
            df_storage,
            x='Type',
            y='Size (GB)',
            title='Storage Usage by Type',
            color='Size (GB)',
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig_storage, use_container_width=True)
    
    def _render_revenue_analytics(self):
        """Render revenue analytics tab"""
        st.header("Revenue Analytics")
        
        # Mock revenue data - would come from Stripe/payment processor
        st.subheader("Monthly Recurring Revenue (MRR)")
        
        # MRR trend
        months = pd.date_range(end=datetime.now(), periods=12, freq='M')
        mrr_data = {
            'Month': months,
            'MRR': [12000, 13500, 14200, 15800, 16500, 17200, 
                    18900, 20100, 21500, 22800, 24200, 25600]
        }
        
        df_mrr = pd.DataFrame(mrr_data)
        
        fig_mrr = px.line(
            df_mrr,
            x='Month',
            y='MRR',
            title='MRR Growth',
            markers=True
        )
        
        fig_mrr.update_layout(yaxis_tickformat='$,.0f')
        st.plotly_chart(fig_mrr, use_container_width=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            enhanced_metric("Current MRR", "$25,600", "+5.8%")
        
        with col2:
            enhanced_metric("ARR", "$307,200", "Annual")
        
        with col3:
            enhanced_metric("ARPU", "$85", "Per user")
        
        with col4:
            enhanced_metric("Churn Rate", "2.3%", "Monthly")
        
        # Subscription metrics
        st.subheader("Subscription Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # New vs Churned
            churn_data = {
                'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'New': [45, 52, 48, 61, 55, 58],
                'Churned': [12, 15, 10, 18, 14, 13],
                'Net': [33, 37, 38, 43, 41, 45]
            }
            
            df_churn = pd.DataFrame(churn_data)
            
            fig_churn = go.Figure()
            fig_churn.add_trace(go.Bar(name='New', x=df_churn['Month'], y=df_churn['New']))
            fig_churn.add_trace(go.Bar(name='Churned', x=df_churn['Month'], y=-df_churn['Churned']))
            
            fig_churn.update_layout(
                title='New vs Churned Subscriptions',
                barmode='relative'
            )
            
            st.plotly_chart(fig_churn, use_container_width=True)
        
        with col2:
            # Plan upgrades/downgrades
            movement_data = {
                'Type': ['Upgrades', 'Downgrades', 'Reactivations'],
                'Count': [28, 8, 12]
            }
            
            df_movement = pd.DataFrame(movement_data)
            
            fig_movement = px.bar(
                df_movement,
                x='Type',
                y='Count',
                title='Plan Movement (Last 30 days)',
                color='Type'
            )
            
            st.plotly_chart(fig_movement, use_container_width=True)
    
    def _render_alerts_actions(self):
        """Render alerts and actions tab"""
        st.header("Alerts & Administrative Actions")
        
        # System alerts
        st.subheader("System Alerts")
        
        alerts = [
            {
                'level': 'critical',
                'message': 'Storage usage at 92% capacity',
                'time': '2 hours ago',
                'action': 'Expand storage'
            },
            {
                'level': 'warning',
                'message': '5 users exceeded their monthly limits',
                'time': '5 hours ago',
                'action': 'Send notifications'
            },
            {
                'level': 'info',
                'message': 'Daily backup completed successfully',
                'time': '12 hours ago',
                'action': None
            }
        ]
        
        for alert in alerts:
            icon = {
                'critical': '🔴',
                'warning': '🟡',
                'info': '🔵'
            }.get(alert['level'], '🔵')
            
            with enhanced_card():
                col1, col2, col3 = st.columns([1, 4, 2])
                
                with col1:
                    st.write(f"{icon} {alert['level'].upper()}")
                
                with col2:
                    st.write(f"**{alert['message']}**")
                    st.caption(alert['time'])
                
                with col3:
                    if alert['action']:
                        if st.button(alert['action'], key=f"alert_{alert['time']}"):
                            st.success(f"Action taken: {alert['action']}")
        
        # Administrative actions
        st.subheader("Administrative Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with enhanced_card():
                st.write("**Usage Management**")
                
                if enhanced_button("Reset Test User Limits", "secondary", key="reset_limits"):
                    st.success("Test user limits reset")
                
                if enhanced_button("Clear Usage Cache", "secondary", key="clear_cache"):
                    st.success("Usage cache cleared")
                
                if enhanced_button("Run Usage Audit", "secondary", key="run_audit"):
                    st.info("Usage audit started...")
        
        with col2:
            with enhanced_card():
                st.write("**Notification Management**")
                
                if enhanced_button("Send System Announcement", "primary", key="send_announcement"):
                    st.success("Announcement sent to all users")
                
                if enhanced_button("Test Alert System", "secondary", key="test_alerts"):
                    st.success("Alert system test completed")
                
                if enhanced_button("View Email Queue", "secondary", key="view_queue"):
                    st.info("Email queue: 0 pending")
        
        # Bulk actions
        st.subheader("Bulk User Actions")
        
        with st.form("bulk_actions"):
            action = st.selectbox(
                "Select Action",
                ["Send usage summary", "Reset limits", "Apply discount", "Suspend access"]
            )
            
            user_filter = st.selectbox(
                "Apply to",
                ["All users", "Free tier only", "Paid users only", "High usage users"]
            )
            
            confirm = st.checkbox("I confirm this action")
            
            if st.form_submit_button("Execute Action"):
                if confirm:
                    st.success(f"Action '{action}' applied to {user_filter}")
                else:
                    st.error("Please confirm the action")
    
    def _render_system_trends_chart(self, trends_data: Dict):
        """Render system-wide usage trends chart"""
        if not trends_data.get('trends'):
            return
        
        # Prepare data
        df_data = []
        for date_str, usage in trends_data['trends'].items():
            for usage_type, value in usage.items():
                df_data.append({
                    'Date': date_str,
                    'Type': usage_type,
                    'Value': value
                })
        
        df = pd.DataFrame(df_data)
        
        # Create stacked area chart
        fig = px.area(
            df,
            x='Date',
            y='Value',
            color='Type',
            title='System Usage Over Time',
            labels={'Value': 'Usage', 'Type': 'Usage Type'}
        )
        
        fig.update_layout(
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_plan_usage_summary(self, usage_data: Dict):
        """Render plan usage summary cards"""
        if not usage_data.get('usage_by_plan'):
            return
        
        plans = usage_data['usage_by_plan']
        
        cols = st.columns(len(plans))
        
        for idx, (plan_name, plan_data) in enumerate(plans.items()):
            with cols[idx]:
                with enhanced_card():
                    st.write(f"**{plan_name}**")
                    st.metric("Users", plan_data['unique_users'])
                    
                    if 'usage' in plan_data:
                        for usage_type, usage_info in plan_data['usage'].items():
                            st.caption(f"{usage_type}: {usage_info['total']:.0f}")

# Initialize and render
def main():
    """Main function to render admin dashboard"""
    dashboard = AdminUsageDashboard()
    dashboard.render_main()

if __name__ == "__main__":
    main()