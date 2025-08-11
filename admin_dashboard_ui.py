#!/usr/bin/env python3
"""
Admin Dashboard UI Components (Task 49)
Streamlit interface for comprehensive admin panel and business analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import time

from admin_dashboard import (
    AdminDashboardSystem, AdminUser, RevenueRecord, UserActivity,
    SystemMetric, SupportTicket, UserStatus, SubscriptionTier,
    TicketStatus, TicketPriority
)

class AdminDashboardUI:
    """UI components for admin dashboard functionality"""
    
    def __init__(self):
        if 'admin_system' not in st.session_state:
            st.session_state.admin_system = AdminDashboardSystem()
        
        self.admin_system = st.session_state.admin_system
        
        # Initialize session state
        if 'selected_user' not in st.session_state:
            st.session_state.selected_user = None
        if 'dashboard_data' not in st.session_state:
            st.session_state.dashboard_data = {}
    
    def render_admin_dashboard(self):
        """Render the main admin dashboard interface"""
        st.set_page_config(
            page_title="Admin Dashboard",
            page_icon="🏢",
            layout="wide"
        )
        
        st.title("🏢 Admin Dashboard & Business Analytics")
        
        # Sidebar navigation
        with st.sidebar:
            st.header("Navigation")
            
            page = st.selectbox(
                "Select Page:",
                [
                    "📊 Overview",
                    "👥 User Management", 
                    "💰 Revenue Analytics",
                    "🏥 System Health",
                    "🎫 Support Tickets",
                    "📈 Business Intelligence",
                    "📋 Executive Reports"
                ]
            )
            
            # Refresh data button
            if st.button("🔄 Refresh Data"):
                st.session_state.dashboard_data = {}
                st.rerun()
        
        # Route to appropriate page
        if page == "📊 Overview":
            self._render_overview()
        elif page == "👥 User Management":
            self._render_user_management()
        elif page == "💰 Revenue Analytics":
            self._render_revenue_analytics()
        elif page == "🏥 System Health":
            self._render_system_health()
        elif page == "🎫 Support Tickets":
            self._render_support_tickets()
        elif page == "📈 Business Intelligence":
            self._render_business_intelligence()
        elif page == "📋 Executive Reports":
            self._render_executive_reports()
    
    def _render_overview(self):
        """Render dashboard overview"""
        st.header("📊 Dashboard Overview")
        
        # Get overview data
        if 'overview_data' not in st.session_state.dashboard_data:
            with st.spinner("Loading dashboard data..."):
                st.session_state.dashboard_data['overview_data'] = self.admin_system.get_dashboard_overview()
        
        overview = st.session_state.dashboard_data['overview_data']
        
        if 'error' in overview:
            st.error(f"Error loading dashboard data: {overview['error']}")
            return
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_users = overview.get('users', {}).get('total_users', 0)
            active_users = overview.get('users', {}).get('active_users', 0)
            st.metric(
                "Total Users", 
                f"{total_users:,}",
                delta=f"{active_users} active"
            )
        
        with col2:
            total_revenue = overview.get('revenue', {}).get('total_revenue', 0)
            period_revenue = overview.get('revenue', {}).get('period_revenue', 0)
            st.metric(
                "Total Revenue", 
                f"${total_revenue:,.2f}",
                delta=f"${period_revenue:.2f} this month"
            )
        
        with col3:
            system_status = overview.get('system_health', {}).get('status', 'unknown')
            status_color = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(system_status, "⚪")
            st.metric(
                "System Health", 
                f"{status_color} {system_status.title()}",
                delta=f"{len(overview.get('system_health', {}).get('alerts', []))} alerts"
            )
        
        with col4:
            new_tickets = overview.get('support', {}).get('new_tickets', 0)
            total_tickets = overview.get('support', {}).get('total_tickets', 0)
            st.metric(
                "Support Tickets", 
                f"{total_tickets}",
                delta=f"{new_tickets} new"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # User growth chart
            st.subheader("📈 User Growth")
            
            growth_data = overview.get('users', {}).get('growth_data', [])
            if growth_data:
                df_growth = pd.DataFrame(growth_data, columns=['date', 'new_users'])
                fig = px.line(df_growth, x='date', y='new_users', 
                            title="Daily New User Registrations")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No growth data available")
        
        with col2:
            # Revenue trend chart
            st.subheader("💰 Revenue Trend")
            
            daily_revenue = overview.get('revenue', {}).get('daily_revenue', [])
            if daily_revenue:
                df_revenue = pd.DataFrame(daily_revenue, columns=['date', 'revenue'])
                fig = px.bar(df_revenue, x='date', y='revenue',
                           title="Daily Revenue")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data available")
        
        # System alerts
        alerts = overview.get('system_health', {}).get('alerts', [])
        if alerts:
            st.subheader("🚨 System Alerts")
            for alert in alerts:
                st.warning(alert)
        
        # Recent activity summary
        st.subheader("📋 Recent Activity Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**User Activity**")
            activity_types = overview.get('engagement', {}).get('activity_types', [])
            if activity_types:
                for activity_type, count in activity_types[:5]:
                    st.write(f"• {activity_type}: {count}")
            else:
                st.info("No activity data")
        
        with col2:
            st.write("**Revenue Breakdown**")
            tier_revenue = overview.get('revenue', {}).get('tier_revenue', {})
            for tier, amount in tier_revenue.items():
                st.write(f"• {tier.title()}: ${amount:.2f}")
        
        with col3:
            st.write("**Support Status**")
            status_dist = overview.get('support', {}).get('status_distribution', {})
            for status, count in status_dist.items():
                st.write(f"• {status.title()}: {count}")
    
    def _render_user_management(self):
        """Render user management interface"""
        st.header("👥 User Management")
        
        # User search and filters
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Users:",
                placeholder="Search by username, email, or name..."
            )
        
        with col2:
            status_filter = st.selectbox(
                "Status Filter:",
                options=["All", "Active", "Inactive", "Suspended", "Pending"],
                index=0
            )
        
        with col3:
            tier_filter = st.selectbox(
                "Subscription Tier:",
                options=["All", "Free", "Pro", "Enterprise"],
                index=0
            )
        
        # Get users
        filters = {}
        if status_filter != "All":
            filters['status'] = status_filter.lower()
        if tier_filter != "All":
            filters['subscription_tier'] = tier_filter.lower()
        
        if search_query:
            users = self.admin_system.user_management.search_users(search_query, filters)
        else:
            users = self.admin_system.db.get_users(
                status=filters.get('status'),
                limit=50
            )
        
        # User statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(users))
        
        with col2:
            active_count = sum(1 for u in users if u.status == 'active')
            st.metric("Active Users", active_count)
        
        with col3:
            pro_count = sum(1 for u in users if u.subscription_tier == 'pro')
            st.metric("Pro Users", pro_count)
        
        with col4:
            enterprise_count = sum(1 for u in users if u.subscription_tier == 'enterprise')
            st.metric("Enterprise Users", enterprise_count)
        
        # Users table
        if users:
            st.subheader("User List")
            
            # Convert to DataFrame for display
            user_data = []
            for user in users:
                user_data.append({
                    'Username': user.username,
                    'Email': user.email,
                    'Full Name': user.full_name,
                    'Status': user.status.title(),
                    'Tier': user.subscription_tier.title(),
                    'Created': user.created_at.strftime('%Y-%m-%d'),
                    'Last Login': user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never',
                    'Revenue': f"${user.total_revenue:.2f}",
                    'Usage': f"{user.total_usage:.1f}h",
                    'Tickets': user.support_tickets
                })
            
            df_users = pd.DataFrame(user_data)
            
            # Display with selection
            selected_indices = st.dataframe(
                df_users,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # User actions
            if selected_indices and len(selected_indices['selection']['rows']) > 0:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_user = users[selected_idx]
                
                st.subheader(f"User Actions: {selected_user.username}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("👁️ View Details"):
                        self._show_user_details(selected_user)
                
                with col2:
                    if st.button("✏️ Edit User"):
                        self._show_edit_user_dialog(selected_user)
                
                with col3:
                    if st.button("🔄 Change Status"):
                        self._show_status_change_dialog(selected_user)
                
                with col4:
                    if st.button("📊 View Analytics"):
                        self._show_user_analytics(selected_user)
        else:
            st.info("No users found matching the criteria.")
    
    def _render_revenue_analytics(self):
        """Render revenue analytics interface"""
        st.header("💰 Revenue Analytics")
        
        # Time period selector
        col1, col2 = st.columns([1, 3])
        
        with col1:
            period = st.selectbox(
                "Analysis Period:",
                options=["Last 7 days", "Last 30 days", "Last 90 days", "Last year"],
                index=1
            )
            
            days_map = {
                "Last 7 days": 7,
                "Last 30 days": 30,
                "Last 90 days": 90,
                "Last year": 365
            }
            days = days_map[period]
        
        # Get revenue data
        revenue_overview = self.admin_system.revenue_tracking.get_revenue_overview(days)
        subscription_metrics = self.admin_system.revenue_tracking.get_subscription_metrics()
        
        # Revenue metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Revenue",
                f"${revenue_overview.get('total_revenue', 0):,.2f}"
            )
        
        with col2:
            st.metric(
                "Period Revenue",
                f"${revenue_overview.get('period_revenue', 0):,.2f}"
            )
        
        with col3:
            st.metric(
                "Monthly MRR",
                f"${subscription_metrics.get('total_mrr', 0):,.2f}"
            )
        
        with col4:
            st.metric(
                "Paying Users",
                f"{revenue_overview.get('paying_users', 0):,}"
            )
        
        # Revenue charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily revenue trend
            st.subheader("📈 Daily Revenue Trend")
            daily_revenue = revenue_overview.get('daily_revenue', [])
            
            if daily_revenue:
                df_daily = pd.DataFrame(daily_revenue, columns=['date', 'revenue'])
                fig = px.line(df_daily, x='date', y='revenue',
                            title=f"Daily Revenue - {period}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data available")
        
        with col2:
            # Revenue by subscription tier
            st.subheader("🎯 Revenue by Tier")
            tier_revenue = revenue_overview.get('tier_revenue', {})
            
            if tier_revenue:
                fig = px.pie(
                    values=list(tier_revenue.values()),
                    names=list(tier_revenue.keys()),
                    title="Revenue Distribution by Subscription Tier"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tier revenue data available")
        
        # Subscription metrics
        st.subheader("📊 Subscription Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Current subscription distribution
            current_dist = subscription_metrics.get('current_distribution', {})
            if current_dist:
                fig = px.bar(
                    x=list(current_dist.keys()),
                    y=list(current_dist.values()),
                    title="Current Subscription Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Churn analysis
            churn_rate = subscription_metrics.get('churn_rate', 0)
            churned_users = subscription_metrics.get('churned_users', 0)
            
            st.metric("Churn Rate", f"{churn_rate:.1f}%")
            st.metric("Churned Users", churned_users)
            
            if churn_rate > 5:
                st.warning("⚠️ High churn rate detected. Consider retention strategies.")
            elif churn_rate < 2:
                st.success("✅ Healthy churn rate.")
        
        # Revenue insights
        st.subheader("💡 Revenue Insights")
        
        arpu = revenue_overview.get('average_revenue_per_user', 0)
        st.write(f"**Average Revenue Per User (ARPU):** ${arpu:.2f}")
        
        # Growth recommendations
        if arpu < 50:
            st.info("💡 Consider upselling strategies to increase ARPU")
        
        if subscription_metrics.get('total_mrr', 0) < 10000:
            st.info("💡 Focus on acquiring more paying customers to grow MRR")
    
    def _render_system_health(self):
        """Render system health monitoring interface"""
        st.header("🏥 System Health Monitoring")
        
        # Get system health data
        health_overview = self.admin_system.health_monitor.get_system_health_overview()
        
        # System status
        status = health_overview.get('status', 'unknown')
        status_colors = {
            'healthy': '🟢',
            'warning': '🟡', 
            'critical': '🔴',
            'unknown': '⚪'
        }
        
        st.subheader(f"System Status: {status_colors.get(status, '⚪')} {status.title()}")
        
        # Alerts
        alerts = health_overview.get('alerts', [])
        if alerts:
            st.subheader("🚨 Active Alerts")
            for alert in alerts:
                st.error(alert)
        else:
            st.success("✅ No active alerts")
        
        # Current metrics
        current_metrics = health_overview.get('current_metrics', {})
        
        if current_metrics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cpu_usage = current_metrics.get('cpu_usage', {}).get('current_value', 0)
                st.metric("CPU Usage", f"{cpu_usage:.1f}%")
                
                if cpu_usage > 80:
                    st.error("High CPU usage!")
                elif cpu_usage > 60:
                    st.warning("Moderate CPU usage")
                else:
                    st.success("Normal CPU usage")
            
            with col2:
                memory_usage = current_metrics.get('memory_usage', {}).get('current_value', 0)
                st.metric("Memory Usage", f"{memory_usage:.1f}%")
                
                if memory_usage > 85:
                    st.error("High memory usage!")
                elif memory_usage > 70:
                    st.warning("Moderate memory usage")
                else:
                    st.success("Normal memory usage")
            
            with col3:
                db_connections = current_metrics.get('database_connections', {}).get('current_value', 0)
                st.metric("DB Connections", f"{int(db_connections)}")
            
            with col4:
                api_response = current_metrics.get('api_response_time', {}).get('current_value', 0)
                st.metric("API Response", f"{api_response:.0f}ms")
                
                if api_response > 1000:
                    st.error("Slow API responses!")
                elif api_response > 500:
                    st.warning("Moderate API response time")
                else:
                    st.success("Fast API responses")
        
        # Performance trends
        st.subheader("📈 Performance Trends")
        trends = health_overview.get('trends', {})
        
        if trends:
            # Create performance trend chart
            metrics_data = []
            for metric_name, trend_data in trends.items():
                metrics_data.append({
                    'Metric': metric_name.replace('_', ' ').title(),
                    'Average': trend_data.get('average', 0),
                    'Minimum': trend_data.get('minimum', 0),
                    'Maximum': trend_data.get('maximum', 0)
                })
            
            if metrics_data:
                df_trends = pd.DataFrame(metrics_data)
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Average',
                    x=df_trends['Metric'],
                    y=df_trends['Average'],
                    marker_color='blue'
                ))
                
                fig.add_trace(go.Bar(
                    name='Maximum',
                    x=df_trends['Metric'],
                    y=df_trends['Maximum'],
                    marker_color='red'
                ))
                
                fig.update_layout(
                    title="Performance Metrics Trends",
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # System recommendations
        st.subheader("💡 System Recommendations")
        
        if status == 'critical':
            st.error("🚨 Immediate action required! System is in critical state.")
        elif status == 'warning':
            st.warning("⚠️ System performance issues detected. Monitor closely.")
        else:
            st.success("✅ System is operating normally.")
        
        # Performance optimization tips
        with st.expander("🔧 Performance Optimization Tips"):
            st.write("""
            **CPU Optimization:**
            - Monitor high CPU processes
            - Consider scaling horizontally
            - Optimize database queries
            
            **Memory Optimization:**
            - Check for memory leaks
            - Optimize caching strategies
            - Consider increasing memory allocation
            
            **Database Optimization:**
            - Monitor connection pooling
            - Optimize slow queries
            - Consider read replicas
            
            **API Optimization:**
            - Implement response caching
            - Optimize database queries
            - Consider CDN for static content
            """)
    
    def _render_support_tickets(self):
        """Render support ticket management interface"""
        st.header("🎫 Support Ticket Management")
        
        # Ticket filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Status Filter:",
                options=["All", "Open", "In Progress", "Resolved", "Closed"],
                index=0
            )
        
        with col2:
            priority_filter = st.selectbox(
                "Priority Filter:",
                options=["All", "Low", "Medium", "High", "Critical"],
                index=0
            )
        
        with col3:
            if st.button("➕ Create New Ticket"):
                self._show_create_ticket_dialog()
        
        # Get tickets
        filters = {}
        if status_filter != "All":
            filters['status'] = status_filter.lower().replace(' ', '_')
        if priority_filter != "All":
            filters['priority'] = priority_filter.lower()
        
        tickets = self.admin_system.support_system.get_tickets(
            status=filters.get('status'),
            priority=filters.get('priority'),
            limit=50
        )
        
        # Support metrics
        support_metrics = self.admin_system.support_system.get_support_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tickets", support_metrics.get('total_tickets', 0))
        
        with col2:
            st.metric("New Tickets", support_metrics.get('new_tickets', 0))
        
        with col3:
            avg_resolution = support_metrics.get('avg_resolution_hours', 0)
            st.metric("Avg Resolution", f"{avg_resolution:.1f}h")
        
        with col4:
            avg_response = support_metrics.get('avg_response_hours', 0)
            st.metric("Avg Response", f"{avg_response:.1f}h")
        
        # Tickets table
        if tickets:
            st.subheader("Support Tickets")
            
            # Convert to DataFrame
            ticket_data = []
            for ticket in tickets:
                ticket_data.append({
                    'ID': ticket.ticket_id[-8:],  # Show last 8 chars
                    'Subject': ticket.subject[:50] + "..." if len(ticket.subject) > 50 else ticket.subject,
                    'Status': ticket.status.replace('_', ' ').title(),
                    'Priority': ticket.priority.title(),
                    'Category': ticket.category.title(),
                    'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Assigned': ticket.assigned_to or "Unassigned"
                })
            
            df_tickets = pd.DataFrame(ticket_data)
            
            # Display with selection
            selected_indices = st.dataframe(
                df_tickets,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Ticket actions
            if selected_indices and len(selected_indices['selection']['rows']) > 0:
                selected_idx = selected_indices['selection']['rows'][0]
                selected_ticket = tickets[selected_idx]
                
                self._show_ticket_details(selected_ticket)
        else:
            st.info("No tickets found matching the criteria.")
        
        # Support analytics
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
            status_dist = support_metrics.get('status_distribution', {})
            if status_dist:
                fig = px.pie(
                    values=list(status_dist.values()),
                    names=[s.replace('_', ' ').title() for s in status_dist.keys()],
                    title="Ticket Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Priority distribution
            priority_dist = support_metrics.get('priority_distribution', {})
            if priority_dist:
                fig = px.bar(
                    x=[p.title() for p in priority_dist.keys()],
                    y=list(priority_dist.values()),
                    title="Ticket Priority Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_business_intelligence(self):
        """Render business intelligence interface"""
        st.header("📈 Business Intelligence")
        
        # Get analytics data
        engagement_metrics = self.admin_system.analytics.get_engagement_metrics()
        conversion_funnel = self.admin_system.analytics.get_conversion_funnel()
        cohort_analysis = self.admin_system.analytics.get_cohort_analysis()
        
        # Engagement metrics
        st.subheader("👥 User Engagement")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_session = engagement_metrics.get('avg_session_duration', 0)
            st.metric("Avg Session Duration", f"{avg_session:.1f} min")
        
        with col2:
            # Calculate DAU from daily active users data
            dau_data = engagement_metrics.get('daily_active_users', [])
            current_dau = dau_data[-1][1] if dau_data else 0
            st.metric("Daily Active Users", current_dau)
        
        with col3:
            activity_types = engagement_metrics.get('activity_types', [])
            total_activities = sum(count for _, count in activity_types)
            st.metric("Total Activities", total_activities)
        
        # Daily active users chart
        if dau_data:
            st.subheader("📊 Daily Active Users Trend")
            df_dau = pd.DataFrame(dau_data, columns=['date', 'dau'])
            fig = px.line(df_dau, x='date', y='dau', title="Daily Active Users")
            st.plotly_chart(fig, use_container_width=True)
        
        # Activity types distribution
        if activity_types:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Activity Types")
                df_activities = pd.DataFrame(activity_types, columns=['activity_type', 'count'])
                fig = px.pie(df_activities, values='count', names='activity_type',
                           title="User Activity Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("👑 Most Active Users")
                most_active = engagement_metrics.get('most_active_users', [])
                if most_active:
                    df_active = pd.DataFrame(most_active, columns=['user_id', 'activity_count'])
                    fig = px.bar(df_active, x='user_id', y='activity_count',
                               title="Top 10 Most Active Users")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Conversion funnel
        st.subheader("🎯 Conversion Funnel")
        
        funnel_stages = conversion_funnel.get('funnel_stages', {})
        conversion_rates = conversion_funnel.get('conversion_rates', {})
        
        if funnel_stages:
            col1, col2 = st.columns(2)
            
            with col1:
                # Funnel visualization
                stages = list(funnel_stages.keys())
                values = list(funnel_stages.values())
                
                fig = go.Figure(go.Funnel(
                    y=stages,
                    x=values,
                    textinfo="value+percent initial"
                ))
                fig.update_layout(title="User Conversion Funnel")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Conversion rates
                st.write("**Conversion Rates:**")
                for rate_name, rate_value in conversion_rates.items():
                    st.metric(
                        rate_name.replace('_', ' ').title(),
                        f"{rate_value:.1f}%"
                    )
                    
                    # Add recommendations
                    if rate_name == 'activation_rate' and rate_value < 50:
                        st.warning("💡 Low activation rate. Improve onboarding.")
                    elif rate_name == 'conversion_rate' and rate_value < 10:
                        st.warning("💡 Low conversion rate. Optimize pricing/features.")
        
        # Cohort analysis
        st.subheader("📅 Cohort Retention Analysis")
        
        cohort_data = cohort_analysis.get('cohort_data', [])
        if cohort_data:
            df_cohort = pd.DataFrame(cohort_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Cohort sizes
                fig = px.bar(df_cohort, x='cohort_month', y='cohort_size',
                           title="Cohort Sizes by Month")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Retention rates
                fig = px.line(df_cohort, x='cohort_month', y='retention_rate',
                            title="Cohort Retention Rates")
                st.plotly_chart(fig, use_container_width=True)
            
            # Cohort table
            st.subheader("📋 Cohort Details")
            st.dataframe(df_cohort, use_container_width=True)
        
        # Business insights
        st.subheader("💡 Business Insights")
        
        insights = []
        
        # Engagement insights
        if avg_session < 5:
            insights.append("⚠️ Low session duration. Consider improving user experience.")
        elif avg_session > 20:
            insights.append("✅ High user engagement with long session durations.")
        
        # Conversion insights
        activation_rate = conversion_rates.get('activation_rate', 0)
        if activation_rate < 30:
            insights.append("🎯 Focus on user activation strategies.")
        
        conversion_rate = conversion_rates.get('conversion_rate', 0)
        if conversion_rate < 5:
            insights.append("💰 Optimize conversion funnel to increase paid conversions.")
        
        # Cohort insights
        if cohort_data:
            avg_retention = sum(c['retention_rate'] for c in cohort_data) / len(cohort_data)
            if avg_retention < 20:
                insights.append("📉 Low retention rates. Implement retention strategies.")
            elif avg_retention > 50:
                insights.append("🎉 Excellent retention rates!")
        
        if insights:
            for insight in insights:
                if "⚠️" in insight or "🎯" in insight or "💰" in insight or "📉" in insight:
                    st.warning(insight)
                else:
                    st.success(insight)
        else:
            st.info("No specific insights available. Continue monitoring metrics.")
    
    def _render_executive_reports(self):
        """Render executive reports interface"""
        st.header("📋 Executive Reports")
        
        # Report period selector
        col1, col2 = st.columns([1, 3])
        
        with col1:
            report_period = st.selectbox(
                "Report Period:",
                options=[7, 30, 90, 365],
                format_func=lambda x: f"Last {x} days",
                index=1
            )
        
        with col2:
            if st.button("📊 Generate Report", type="primary"):
                with st.spinner("Generating executive report..."):
                    report = self.admin_system.generate_executive_report(report_period)
                    st.session_state.executive_report = report
        
        # Display report if available
        if 'executive_report' in st.session_state:
            report = st.session_state.executive_report
            
            if 'error' in report:
                st.error(f"Error generating report: {report['error']}")
                return
            
            # Report header
            st.subheader(f"📈 Executive Summary - {report_period} Days")
            st.write(f"**Report Generated:** {datetime.fromisoformat(report['report_date']).strftime('%Y-%m-%d %H:%M')}")
            
            # Key Performance Indicators
            st.subheader("🎯 Key Performance Indicators")
            
            kpis = report.get('kpis', {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Users", f"{kpis.get('total_users', 0):,}")
                st.metric("Active Users", f"{kpis.get('active_users', 0):,}")
            
            with col2:
                st.metric("Total Revenue", f"${kpis.get('total_revenue', 0):,.2f}")
                st.metric("Monthly Revenue", f"${kpis.get('monthly_revenue', 0):,.2f}")
            
            with col3:
                st.metric("Support Tickets", kpis.get('support_tickets', 0))
                st.metric("System Health", kpis.get('system_health', 'Unknown').title())
            
            with col4:
                st.metric("Conversion Rate", f"{kpis.get('conversion_rate', 0):.1f}%")
                st.metric("Churn Rate", f"{kpis.get('churn_rate', 0):.1f}%")
            
            # Growth Metrics
            st.subheader("📈 Growth Metrics")
            
            growth_metrics = report.get('growth_metrics', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                user_growth = growth_metrics.get('user_growth', 0)
                st.metric("User Growth", f"+{user_growth:,}")
            
            with col2:
                revenue_growth = growth_metrics.get('revenue_growth', 0)
                st.metric("Revenue Growth", f"${revenue_growth:,.2f}")
            
            with col3:
                mrr = growth_metrics.get('mrr', 0)
                st.metric("Monthly Recurring Revenue", f"${mrr:,.2f}")
            
            # Conversion Funnel
            st.subheader("🎯 Conversion Funnel Analysis")
            
            conversion_funnel = report.get('conversion_funnel', {})
            funnel_stages = conversion_funnel.get('funnel_stages', {})
            
            if funnel_stages:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Funnel chart
                    stages = list(funnel_stages.keys())
                    values = list(funnel_stages.values())
                    
                    fig = go.Figure(go.Funnel(
                        y=[s.title() for s in stages],
                        x=values,
                        textinfo="value+percent initial"
                    ))
                    fig.update_layout(title="User Conversion Funnel")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Conversion rates
                    conversion_rates = conversion_funnel.get('conversion_rates', {})
                    
                    st.write("**Conversion Rates:**")
                    for rate_name, rate_value in conversion_rates.items():
                        st.write(f"• {rate_name.replace('_', ' ').title()}: {rate_value:.1f}%")
            
            # Subscription Metrics
            st.subheader("💳 Subscription Analysis")
            
            subscription_metrics = report.get('subscription_metrics', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Current distribution
                current_dist = subscription_metrics.get('current_distribution', {})
                if current_dist:
                    fig = px.pie(
                        values=list(current_dist.values()),
                        names=[tier.title() for tier in current_dist.keys()],
                        title="Current Subscription Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # MRR breakdown
                monthly_mrr = subscription_metrics.get('monthly_mrr', {})
                if monthly_mrr:
                    fig = px.bar(
                        x=[tier.title() for tier in monthly_mrr.keys()],
                        y=list(monthly_mrr.values()),
                        title="Monthly Recurring Revenue by Tier"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Business Recommendations
            st.subheader("💡 Strategic Recommendations")
            
            recommendations = report.get('recommendations', [])
            
            if recommendations:
                for i, recommendation in enumerate(recommendations, 1):
                    st.write(f"{i}. {recommendation}")
            else:
                st.success("✅ All key metrics are performing well. Continue current strategies.")
            
            # Executive Summary
            st.subheader("📝 Executive Summary")
            
            # Generate summary text
            summary_text = f"""
            **Period Overview ({report_period} days):**
            
            • **User Base:** {kpis.get('total_users', 0):,} total users with {kpis.get('active_users', 0):,} active users
            • **Revenue Performance:** ${kpis.get('total_revenue', 0):,.2f} total revenue, ${kpis.get('monthly_revenue', 0):,.2f} this period
            • **Growth:** +{growth_metrics.get('user_growth', 0):,} new users, ${growth_metrics.get('revenue_growth', 0):,.2f} revenue growth
            • **System Health:** {kpis.get('system_health', 'Unknown').title()} status with {kpis.get('support_tickets', 0)} support tickets
            • **Conversion:** {kpis.get('conversion_rate', 0):.1f}% conversion rate, {kpis.get('churn_rate', 0):.1f}% churn rate
            
            **Key Insights:**
            • Monthly Recurring Revenue: ${growth_metrics.get('mrr', 0):,.2f}
            • Average Revenue Per User: ${kpis.get('monthly_revenue', 0) / max(kpis.get('active_users', 1), 1):.2f}
            • User Activation Rate: {conversion_funnel.get('conversion_rates', {}).get('activation_rate', 0):.1f}%
            """
            
            st.markdown(summary_text)
            
            # Download report
            if st.button("📥 Download Report"):
                # In a real implementation, this would generate a PDF or Excel file
                st.success("Report download feature would be implemented here")
    
    def _show_user_details(self, user: AdminUser):
        """Show detailed user information"""
        with st.expander(f"👤 User Details: {user.username}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User ID:** {user.user_id}")
                st.write(f"**Username:** {user.username}")
                st.write(f"**Email:** {user.email}")
                st.write(f"**Full Name:** {user.full_name}")
                st.write(f"**Status:** {user.status.title()}")
            
            with col2:
                st.write(f"**Subscription:** {user.subscription_tier.title()}")
                st.write(f"**Created:** {user.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
                st.write(f"**Total Usage:** {user.total_usage:.1f} hours")
                st.write(f"**Total Revenue:** ${user.total_revenue:.2f}")
            
            # User activity summary
            activity_summary = self.admin_system.user_management.get_user_activity_summary(user.user_id)
            
            if activity_summary:
                st.subheader("📊 Activity Summary (Last 30 days)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Activity Types:**")
                    for activity_type, count in activity_summary.get('activity_types', {}).items():
                        st.write(f"• {activity_type}: {count}")
                
                with col2:
                    total_time = activity_summary.get('total_time', 0)
                    st.write(f"**Total Activity Time:** {total_time:.1f} minutes")
                
                # Recent activities
                recent_activities = activity_summary.get('recent_activities', [])
                if recent_activities:
                    st.subheader("🕒 Recent Activities")
                    
                    activity_data = []
                    for activity in recent_activities[:5]:
                        activity_data.append({
                            'Type': activity[0],
                            'Description': activity[1][:50] + "..." if len(activity[1]) > 50 else activity[1],
                            'Time': datetime.fromisoformat(activity[2]).strftime('%Y-%m-%d %H:%M'),
                            'Duration': f"{activity[3]:.1f}min" if activity[3] else "N/A"
                        })
                    
                    df_activities = pd.DataFrame(activity_data)
                    st.dataframe(df_activities, use_container_width=True)
    
    def _show_edit_user_dialog(self, user: AdminUser):
        """Show edit user dialog"""
        st.info("Edit user functionality would be implemented here")
    
    def _show_status_change_dialog(self, user: AdminUser):
        """Show status change dialog"""
        with st.form(f"status_change_{user.user_id}"):
            st.subheader(f"Change Status: {user.username}")
            
            new_status = st.selectbox(
                "New Status:",
                options=[status.value for status in UserStatus],
                index=[status.value for status in UserStatus].index(user.status)
            )
            
            reason = st.text_area("Reason for change:")
            
            if st.form_submit_button("Update Status"):
                if new_status != user.status:
                    success = self.admin_system.user_management.update_user_status(
                        user.user_id, UserStatus(new_status), "admin_user"
                    )
                    
                    if success:
                        st.success(f"User status updated to {new_status}")
                        st.rerun()
                    else:
                        st.error("Failed to update user status")
                else:
                    st.info("No change in status")
    
    def _show_user_analytics(self, user: AdminUser):
        """Show user analytics"""
        st.info("User analytics functionality would be implemented here")
    
    def _show_create_ticket_dialog(self):
        """Show create ticket dialog"""
        with st.form("create_ticket"):
            st.subheader("➕ Create New Support Ticket")
            
            user_id = st.text_input("User ID:")
            subject = st.text_input("Subject:")
            description = st.text_area("Description:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                priority = st.selectbox(
                    "Priority:",
                    options=[p.value for p in TicketPriority],
                    index=1  # Default to medium
                )
            
            with col2:
                category = st.selectbox(
                    "Category:",
                    options=["General", "Technical", "Billing", "Feature Request", "Bug Report"],
                    index=0
                )
            
            if st.form_submit_button("Create Ticket"):
                if user_id and subject and description:
                    ticket_id = self.admin_system.support_system.create_ticket(
                        user_id, subject, description,
                        TicketPriority(priority), category.lower()
                    )
                    
                    if ticket_id:
                        st.success(f"Ticket created successfully: {ticket_id}")
                        st.rerun()
                    else:
                        st.error("Failed to create ticket")
                else:
                    st.error("Please fill in all required fields")
    
    def _show_ticket_details(self, ticket: SupportTicket):
        """Show ticket details"""
        with st.expander(f"🎫 Ticket Details: {ticket.ticket_id[-8:]}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Ticket ID:** {ticket.ticket_id}")
                st.write(f"**User ID:** {ticket.user_id}")
                st.write(f"**Subject:** {ticket.subject}")
                st.write(f"**Status:** {ticket.status.replace('_', ' ').title()}")
                st.write(f"**Priority:** {ticket.priority.title()}")
            
            with col2:
                st.write(f"**Category:** {ticket.category.title()}")
                st.write(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Updated:** {ticket.updated_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Assigned To:** {ticket.assigned_to or 'Unassigned'}")
                
                if ticket.resolved_at:
                    st.write(f"**Resolved:** {ticket.resolved_at.strftime('%Y-%m-%d %H:%M')}")
            
            st.write(f"**Description:**")
            st.write(ticket.description)
            
            if ticket.resolution:
                st.write(f"**Resolution:**")
                st.write(ticket.resolution)
            
            # Ticket actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"✏️ Update Status", key=f"update_{ticket.ticket_id}"):
                    self._show_update_ticket_dialog(ticket)
            
            with col2:
                if st.button(f"👤 Assign", key=f"assign_{ticket.ticket_id}"):
                    st.info("Assign ticket functionality would be implemented here")
            
            with col3:
                if st.button(f"✅ Resolve", key=f"resolve_{ticket.ticket_id}"):
                    self._show_resolve_ticket_dialog(ticket)
    
    def _show_update_ticket_dialog(self, ticket: SupportTicket):
        """Show update ticket dialog"""
        st.info("Update ticket functionality would be implemented here")
    
    def _show_resolve_ticket_dialog(self, ticket: SupportTicket):
        """Show resolve ticket dialog"""
        with st.form(f"resolve_ticket_{ticket.ticket_id}"):
            st.subheader(f"✅ Resolve Ticket: {ticket.ticket_id[-8:]}")
            
            resolution = st.text_area("Resolution Details:")
            
            if st.form_submit_button("Resolve Ticket"):
                if resolution:
                    success = self.admin_system.support_system.update_ticket_status(
                        ticket.ticket_id, TicketStatus.RESOLVED, resolution=resolution
                    )
                    
                    if success:
                        st.success("Ticket resolved successfully")
                        st.rerun()
                    else:
                        st.error("Failed to resolve ticket")
                else:
                    st.error("Please provide resolution details")

def main():
    """Main function for testing the UI"""
    admin_ui = AdminDashboardUI()
    admin_ui.render_admin_dashboard()

if __name__ == "__main__":
    main()