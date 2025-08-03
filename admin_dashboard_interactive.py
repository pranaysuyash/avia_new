#!/usr/bin/env python3
"""
Interactive Admin Dashboard Module
Provides real-time updates, interactive charts, and clear system health visualization
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass
from enum import Enum

from design_system import get_design_system, ComponentVariant


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SystemMetric:
    """System metric data"""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    trend: List[float] = None


class InteractiveAdminDashboard:
    """Interactive admin dashboard with real-time updates"""
    
    def __init__(self):
        self.ds = get_design_system()
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize dashboard session state"""
        if 'dashboard_refresh_rate' not in st.session_state:
            st.session_state.dashboard_refresh_rate = 5  # seconds
        if 'selected_time_range' not in st.session_state:
            st.session_state.selected_time_range = '1h'
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
    
    def render(self):
        """Render the interactive admin dashboard"""
        # Header with controls
        self._render_header()
        
        # Main dashboard layout
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "💚 System Health",
            "📈 Analytics",
            "🔔 Alerts"
        ])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_system_health_tab()
        
        with tab3:
            self._render_analytics_tab()
        
        with tab4:
            self._render_alerts_tab()
        
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time.sleep(0.1)  # Small delay to prevent too frequent refreshes
            if (datetime.now() - st.session_state.last_refresh).seconds >= st.session_state.dashboard_refresh_rate:
                st.session_state.last_refresh = datetime.now()
                st.rerun()
    
    def _render_header(self):
        """Render dashboard header with controls"""
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.title("🎛️ Admin Dashboard")
        
        with col2:
            # Time range selector
            time_range = st.selectbox(
                "Time Range",
                options=['5m', '15m', '1h', '6h', '24h', '7d'],
                index=2,
                key="time_range_select"
            )
            st.session_state.selected_time_range = time_range
        
        with col3:
            # Refresh controls
            refresh_rate = st.slider(
                "Refresh Rate (s)",
                min_value=1,
                max_value=60,
                value=st.session_state.dashboard_refresh_rate,
                key="refresh_rate_slider"
            )
            st.session_state.dashboard_refresh_rate = refresh_rate
        
        with col4:
            # Auto-refresh toggle
            auto_refresh = st.checkbox(
                "Auto Refresh",
                value=st.session_state.auto_refresh,
                key="auto_refresh_toggle"
            )
            st.session_state.auto_refresh = auto_refresh
        
        # Last update time
        st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        self.ds.divider()
    
    def _render_overview_tab(self):
        """Render overview tab with key metrics"""
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._render_metric_card(
                "Active Users",
                self._get_active_users(),
                delta="+12%",
                delta_color="positive",
                icon="👥"
            )
        
        with col2:
            self._render_metric_card(
                "Transcriptions Today",
                self._get_transcriptions_today(),
                delta="+28%",
                delta_color="positive",
                icon="📝"
            )
        
        with col3:
            self._render_metric_card(
                "API Calls",
                self._get_api_calls(),
                delta="-5%",
                delta_color="negative",
                icon="🔌"
            )
        
        with col4:
            self._render_metric_card(
                "System Load",
                f"{self._get_system_load():.1%}",
                delta="Normal",
                delta_color="normal",
                icon="💻"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Transcription Activity")
            self._render_activity_chart()
        
        with col2:
            st.subheader("🍕 Processing Distribution")
            self._render_distribution_chart()
        
        # Recent activity
        st.subheader("📜 Recent Activity")
        self._render_recent_activity()
    
    def _render_system_health_tab(self):
        """Render system health monitoring"""
        # Overall health status
        health_status = self._calculate_overall_health()
        self._render_health_status_card(health_status)
        
        # System metrics grid
        st.subheader("📊 System Metrics")
        
        metrics = self._get_system_metrics()
        
        # Create responsive grid
        cols = st.columns(3)
        for idx, metric in enumerate(metrics):
            with cols[idx % 3]:
                self._render_metric_gauge(metric)
        
        # Service status
        st.subheader("🔧 Service Status")
        self._render_service_status()
        
        # Performance trends
        st.subheader("📈 Performance Trends")
        self._render_performance_trends()
    
    def _render_analytics_tab(self):
        """Render analytics with interactive charts"""
        # Date filter
        col1, col2 = st.columns([3, 1])
        with col1:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=7), datetime.now()),
                key="analytics_date_range"
            )
        
        with col2:
            if st.button("🔄 Refresh Analytics", use_container_width=True):
                st.rerun()
        
        # Analytics grid
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 User Analytics")
            self._render_user_analytics()
            
            st.subheader("🎯 Usage Patterns")
            self._render_usage_patterns()
        
        with col2:
            st.subheader("⚡ Performance Analytics")
            self._render_performance_analytics()
            
            st.subheader("💰 Cost Analysis")
            self._render_cost_analysis()
    
    def _render_alerts_tab(self):
        """Render alerts and notifications"""
        # Alert filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            severity_filter = st.multiselect(
                "Severity",
                ["Critical", "Warning", "Info"],
                default=["Critical", "Warning"],
                key="alert_severity_filter"
            )
        
        with col2:
            category_filter = st.multiselect(
                "Category",
                ["System", "API", "Performance", "Security"],
                default=["System", "API"],
                key="alert_category_filter"
            )
        
        with col3:
            if st.button("🗑️ Clear Resolved", use_container_width=True):
                st.info("Cleared resolved alerts")
        
        # Active alerts
        st.subheader("🚨 Active Alerts")
        self._render_active_alerts(severity_filter, category_filter)
        
        # Alert history
        st.subheader("📋 Alert History")
        self._render_alert_history()
    
    # Helper methods for rendering components
    
    def _render_metric_card(self, label: str, value: Any, delta: str = None, 
                           delta_color: str = "normal", icon: str = None):
        """Render an interactive metric card"""
        # Add click interaction
        metric_key = f"metric_{label.lower().replace(' ', '_')}"
        
        if f"{metric_key}_expanded" not in st.session_state:
            st.session_state[f"{metric_key}_expanded"] = False
        
        # Create clickable metric
        if st.button(f"{icon} {label}", key=f"{metric_key}_btn", use_container_width=True):
            st.session_state[f"{metric_key}_expanded"] = not st.session_state[f"{metric_key}_expanded"]
        
        # Display metric
        self.ds.metric_card(label, value, delta, delta_color, icon)
        
        # Show details if expanded
        if st.session_state[f"{metric_key}_expanded"]:
            with st.expander("Details", expanded=True):
                self._render_metric_details(label)
    
    def _render_metric_gauge(self, metric: SystemMetric):
        """Render a gauge chart for a metric"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=metric.value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': metric.name},
            delta={'reference': metric.threshold_warning},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self._get_gauge_color(metric)},
                'steps': [
                    {'range': [0, metric.threshold_warning], 'color': "lightgray"},
                    {'range': [metric.threshold_warning, metric.threshold_critical], 'color': "yellow"},
                    {'range': [metric.threshold_critical, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': metric.threshold_critical
                }
            }
        ))
        
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_activity_chart(self):
        """Render interactive activity chart"""
        # Generate sample data
        hours = pd.date_range(
            end=datetime.now(),
            periods=24,
            freq='H'
        )
        
        data = pd.DataFrame({
            'Time': hours,
            'Transcriptions': np.random.poisson(10, 24),
            'API Calls': np.random.poisson(50, 24),
            'Errors': np.random.poisson(1, 24)
        })
        
        # Create interactive line chart
        fig = px.line(
            data,
            x='Time',
            y=['Transcriptions', 'API Calls'],
            title=None,
            labels={'value': 'Count', 'Time': ''},
            line_shape='spline'
        )
        
        fig.update_layout(
            hovermode='x unified',
            showlegend=True,
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_distribution_chart(self):
        """Render processing distribution pie chart"""
        data = pd.DataFrame({
            'Type': ['Basic NER', 'Advanced NER', 'Speaker Diarization', 'WhisperX'],
            'Count': [45, 30, 20, 5]
        })
        
        fig = px.pie(
            data,
            values='Count',
            names='Type',
            title=None,
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        
        fig.update_layout(
            showlegend=False,
            height=300,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_health_status_card(self, status: HealthStatus):
        """Render overall health status"""
        status_config = {
            HealthStatus.HEALTHY: {
                "icon": "✅",
                "color": "success",
                "message": "All systems operational"
            },
            HealthStatus.WARNING: {
                "icon": "⚠️",
                "color": "warning",
                "message": "Minor issues detected"
            },
            HealthStatus.CRITICAL: {
                "icon": "🚨",
                "color": "error",
                "message": "Critical issues requiring attention"
            }
        }
        
        config = status_config[status]
        
        # Create status card
        self.ds.card(
            title=f"{config['icon']} System Health: {status.value.upper()}",
            content=config['message'],
            expandable=False
        )
        
        # Show health score
        health_score = self._calculate_health_score()
        self.ds.progress_indicator(
            current=health_score,
            total=100,
            label="Overall Health Score",
            show_percentage=True
        )
    
    def _render_service_status(self):
        """Render service status grid"""
        services = [
            {"name": "API Gateway", "status": "online", "latency": "12ms", "uptime": "99.9%"},
            {"name": "Transcription Service", "status": "online", "latency": "145ms", "uptime": "99.7%"},
            {"name": "NER Engine", "status": "online", "latency": "23ms", "uptime": "99.8%"},
            {"name": "Database", "status": "warning", "latency": "89ms", "uptime": "98.5%"},
            {"name": "Cache", "status": "online", "latency": "2ms", "uptime": "99.99%"},
            {"name": "Queue Worker", "status": "online", "latency": "N/A", "uptime": "99.6%"}
        ]
        
        # Create service cards
        cols = st.columns(3)
        for idx, service in enumerate(services):
            with cols[idx % 3]:
                self._render_service_card(service)
    
    def _render_service_card(self, service: Dict[str, str]):
        """Render individual service status card"""
        status_icons = {
            "online": "🟢",
            "warning": "🟡",
            "offline": "🔴"
        }
        
        icon = status_icons.get(service['status'], "⚪")
        
        card_content = f"""
        <div style="text-align: center;">
            <h4>{icon} {service['name']}</h4>
            <p>Latency: <strong>{service['latency']}</strong></p>
            <p>Uptime: <strong>{service['uptime']}</strong></p>
        </div>
        """
        
        self.ds.card(content=card_content)
    
    def _render_performance_trends(self):
        """Render performance trend charts"""
        # Generate sample trend data
        times = pd.date_range(end=datetime.now(), periods=100, freq='5min')
        
        metrics_data = pd.DataFrame({
            'Time': times,
            'CPU Usage': np.random.normal(45, 10, 100).clip(0, 100),
            'Memory Usage': np.random.normal(60, 5, 100).clip(0, 100),
            'Disk I/O': np.random.normal(30, 15, 100).clip(0, 100),
            'Network I/O': np.random.normal(25, 10, 100).clip(0, 100)
        })
        
        # Create subplots
        fig = go.Figure()
        
        for col in ['CPU Usage', 'Memory Usage', 'Disk I/O', 'Network I/O']:
            fig.add_trace(go.Scatter(
                x=metrics_data['Time'],
                y=metrics_data[col],
                mode='lines',
                name=col,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            hovermode='x unified',
            height=400,
            showlegend=True,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="",
            yaxis_title="Usage %"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_active_alerts(self, severity_filter: List[str], category_filter: List[str]):
        """Render active alerts list"""
        # Sample alerts
        alerts = [
            {
                "id": "ALT001",
                "severity": "Critical",
                "category": "System",
                "message": "High memory usage detected (>90%)",
                "time": "2 minutes ago",
                "status": "active"
            },
            {
                "id": "ALT002",
                "severity": "Warning",
                "category": "API",
                "message": "API rate limit approaching threshold",
                "time": "15 minutes ago",
                "status": "active"
            },
            {
                "id": "ALT003",
                "severity": "Warning",
                "category": "Performance",
                "message": "Slow query detected in transcription lookup",
                "time": "1 hour ago",
                "status": "active"
            }
        ]
        
        # Filter alerts
        filtered_alerts = [
            alert for alert in alerts
            if alert['severity'] in severity_filter and alert['category'] in category_filter
        ]
        
        if not filtered_alerts:
            self.ds.empty_state(
                title="No Active Alerts",
                description="No alerts match your current filters",
                icon="🎉"
            )
        else:
            for alert in filtered_alerts:
                self._render_alert_item(alert)
    
    def _render_alert_item(self, alert: Dict[str, Any]):
        """Render individual alert item"""
        severity_colors = {
            "Critical": "error",
            "Warning": "warning",
            "Info": "info"
        }
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            variant = ComponentVariant[severity_colors.get(alert['severity'], 'info').upper()]
            badge = self.ds.badge(alert['severity'], variant=variant)
            st.markdown(f"{badge} {alert['message']}", unsafe_allow_html=True)
        
        with col2:
            st.caption(alert['category'])
        
        with col3:
            st.caption(alert['time'])
        
        with col4:
            if st.button("Dismiss", key=f"dismiss_{alert['id']}"):
                st.success("Alert dismissed")
    
    # Data generation methods (would connect to real data in production)
    
    def _get_active_users(self) -> int:
        """Get active users count"""
        return np.random.randint(80, 120)
    
    def _get_transcriptions_today(self) -> int:
        """Get today's transcription count"""
        return np.random.randint(200, 300)
    
    def _get_api_calls(self) -> str:
        """Get API calls count"""
        calls = np.random.randint(5000, 8000)
        return f"{calls:,}"
    
    def _get_system_load(self) -> float:
        """Get system load percentage"""
        return np.random.uniform(0.3, 0.7)
    
    def _calculate_overall_health(self) -> HealthStatus:
        """Calculate overall system health"""
        health_score = self._calculate_health_score()
        
        if health_score >= 90:
            return HealthStatus.HEALTHY
        elif health_score >= 70:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    def _calculate_health_score(self) -> int:
        """Calculate health score (0-100)"""
        return np.random.randint(85, 95)
    
    def _get_system_metrics(self) -> List[SystemMetric]:
        """Get system metrics"""
        return [
            SystemMetric(
                name="CPU Usage",
                value=np.random.uniform(30, 70),
                unit="%",
                status=HealthStatus.HEALTHY,
                threshold_warning=70,
                threshold_critical=90
            ),
            SystemMetric(
                name="Memory Usage",
                value=np.random.uniform(50, 80),
                unit="%",
                status=HealthStatus.WARNING,
                threshold_warning=70,
                threshold_critical=90
            ),
            SystemMetric(
                name="Disk Usage",
                value=np.random.uniform(20, 50),
                unit="%",
                status=HealthStatus.HEALTHY,
                threshold_warning=70,
                threshold_critical=85
            ),
            SystemMetric(
                name="Network I/O",
                value=np.random.uniform(10, 40),
                unit="Mbps",
                status=HealthStatus.HEALTHY,
                threshold_warning=60,
                threshold_critical=80
            ),
            SystemMetric(
                name="Queue Length",
                value=np.random.randint(0, 50),
                unit="jobs",
                status=HealthStatus.HEALTHY,
                threshold_warning=100,
                threshold_critical=200
            ),
            SystemMetric(
                name="Error Rate",
                value=np.random.uniform(0, 5),
                unit="%",
                status=HealthStatus.HEALTHY,
                threshold_warning=5,
                threshold_critical=10
            )
        ]
    
    def _get_gauge_color(self, metric: SystemMetric) -> str:
        """Get gauge color based on metric status"""
        if metric.status == HealthStatus.HEALTHY:
            return "green"
        elif metric.status == HealthStatus.WARNING:
            return "yellow"
        else:
            return "red"
    
    def _render_metric_details(self, metric_name: str):
        """Render detailed view for a metric"""
        st.write(f"Detailed view for {metric_name}")
        # Add sparkline or mini chart here
        
    def _render_recent_activity(self):
        """Render recent activity feed"""
        activities = [
            {"user": "john.doe@example.com", "action": "Transcribed audio file", "time": "2 min ago"},
            {"user": "jane.smith@example.com", "action": "Exported results to PDF", "time": "5 min ago"},
            {"user": "admin@example.com", "action": "Updated API settings", "time": "10 min ago"},
            {"user": "mike.jones@example.com", "action": "Processed batch of 5 files", "time": "15 min ago"}
        ]
        
        for activity in activities:
            st.markdown(f"**{activity['user']}** {activity['action']} - _{activity['time']}_")
    
    def _render_user_analytics(self):
        """Render user analytics charts"""
        # User growth chart
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        users = np.cumsum(np.random.randint(5, 15, 30))
        
        fig = px.area(
            x=dates,
            y=users,
            labels={'x': '', 'y': 'Total Users'},
            title="User Growth"
        )
        
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_usage_patterns(self):
        """Render usage pattern heatmap"""
        # Generate heatmap data
        hours = list(range(24))
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        z = np.random.randint(0, 50, size=(7, 24))
        
        fig = px.imshow(
            z,
            labels=dict(x="Hour", y="Day", color="Usage"),
            x=hours,
            y=days,
            title="Weekly Usage Heatmap",
            color_continuous_scale="Blues"
        )
        
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_performance_analytics(self):
        """Render performance analytics"""
        # Response time distribution
        response_times = np.random.lognormal(3, 0.5, 1000)
        
        fig = px.histogram(
            response_times,
            nbins=50,
            labels={'value': 'Response Time (ms)', 'count': 'Frequency'},
            title="API Response Time Distribution"
        )
        
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_cost_analysis(self):
        """Render cost analysis chart"""
        # Cost breakdown
        costs = pd.DataFrame({
            'Service': ['Compute', 'Storage', 'API Calls', 'Bandwidth', 'Other'],
            'Cost': [450, 120, 280, 90, 60]
        })
        
        fig = px.bar(
            costs,
            x='Service',
            y='Cost',
            title="Monthly Cost Breakdown ($)",
            text='Cost'
        )
        
        fig.update_traces(texttemplate='$%{text}', textposition='outside')
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_alert_history(self):
        """Render alert history table"""
        history_data = pd.DataFrame({
            'Time': pd.date_range(end=datetime.now(), periods=10, freq='H'),
            'Severity': np.random.choice(['Critical', 'Warning', 'Info'], 10),
            'Category': np.random.choice(['System', 'API', 'Performance', 'Security'], 10),
            'Message': ['Sample alert message'] * 10,
            'Status': np.random.choice(['Resolved', 'Active', 'Acknowledged'], 10)
        })
        
        st.dataframe(
            history_data,
            use_container_width=True,
            hide_index=True
        )


# Convenience function
def render_interactive_admin_dashboard():
    """Render the interactive admin dashboard"""
    dashboard = InteractiveAdminDashboard()
    dashboard.render()