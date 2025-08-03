#!/usr/bin/env python3
"""
Usage Tracking and Quota Management UI Components (Task 48)
Streamlit interface for usage monitoring and quota management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import logging

# Import the usage tracking system
try:
    from usage_tracking_system import (
        UsageTrackingSystem, UsageMetric, UsagePeriod, 
        QuotaAction, SubscriptionTier
    )
except ImportError:
    st.error("Usage tracking system not found. Please ensure usage_tracking_system.py is available.")
    st.stop()

logger = logging.getLogger(__name__)

class UsageTrackingUI:
    """Streamlit UI for usage tracking and quota management"""
    
    def __init__(self):
        self.usage_system = UsageTrackingSystem()
        
        # Initialize session state
        if 'current_user_id' not in st.session_state:
            st.session_state.current_user_id = "demo_user_123"
        if 'selected_team_id' not in st.session_state:
            st.session_state.selected_team_id = None
        if 'selected_period' not in st.session_state:
            st.session_state.selected_period = UsagePeriod.MONTHLY.value
    
    def render_header(self):
        """Render the main header"""
        st.title("📊 Usage Tracking & Quota Management")
        st.markdown("Monitor your usage, track quotas, and manage subscription limits")
        
        # User selection
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            st.session_state.current_user_id = st.text_input(
                "User ID", 
                value=st.session_state.current_user_id,
                help="Enter the user ID to track usage for"
            )
        
        with col2:
            st.session_state.selected_team_id = st.text_input(
                "Team ID (Optional)", 
                value=st.session_state.selected_team_id or "",
                help="Enter team ID for team-based usage tracking"
            )
            if st.session_state.selected_team_id == "":
                st.session_state.selected_team_id = None
        
        with col3:
            st.session_state.selected_period = st.selectbox(
                "Period",
                options=[period.value for period in UsagePeriod],
                index=list(UsagePeriod).index(UsagePeriod.MONTHLY),
                help="Select the time period for usage analysis"
            )
    
    def render_usage_overview(self):
        """Render usage overview dashboard"""
        st.header("📈 Usage Overview")
        
        try:
            # Get usage analytics
            analytics = self.usage_system.get_usage_analytics(
                st.session_state.current_user_id,
                st.session_state.selected_team_id,
                st.session_state.selected_period
            )
            
            if 'error' in analytics:
                st.error(f"Error loading analytics: {analytics['error']}")
                return
            
            # Display subscription info
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Subscription Tier",
                    analytics['subscription_tier'].title(),
                    help="Current subscription level"
                )
            
            with col2:
                period_display = analytics['period'].replace('_', ' ').title()
                st.metric(
                    "Period",
                    period_display,
                    help=f"Usage period: {analytics['period_start'][:10]} to {analytics['period_end'][:10]}"
                )
            
            with col3:
                total_overage = analytics['total_overage_cost_cents']
                if total_overage > 0:
                    st.metric(
                        "Overage Cost",
                        f"${total_overage/100:.2f}",
                        delta=f"+${total_overage/100:.2f}",
                        delta_color="inverse",
                        help="Total overage charges for this period"
                    )
                else:
                    st.metric(
                        "Overage Cost",
                        "$0.00",
                        help="No overage charges for this period"
                    )
            
            with col4:
                warning_count = len(analytics['warnings'])
                if warning_count > 0:
                    st.metric(
                        "Warnings",
                        warning_count,
                        delta=f"+{warning_count}",
                        delta_color="inverse",
                        help="Number of quota warnings"
                    )
                else:
                    st.metric(
                        "Warnings",
                        "0",
                        help="No quota warnings"
                    )
            
            # Display warnings if any
            if analytics['warnings']:
                st.warning("⚠️ **Quota Warnings:**")
                for warning in analytics['warnings']:
                    st.write(f"• **{warning['metric'].replace('_', ' ').title()}**: {warning['percentage_used']:.1f}% used (threshold: {warning['threshold']:.1f}%)")
            
            # Render usage metrics
            self.render_usage_metrics(analytics['metrics'])
            
        except Exception as e:
            st.error(f"Error loading usage overview: {e}")
            logger.error(f"Error in render_usage_overview: {e}")
    
    def render_usage_metrics(self, metrics: Dict[str, Any]):
        """Render individual usage metrics"""
        st.subheader("📊 Usage Metrics")
        
        if not metrics:
            st.info("No usage data available for the selected period.")
            return
        
        # Create metrics grid
        cols = st.columns(2)
        
        for i, (metric, data) in enumerate(metrics.items()):
            with cols[i % 2]:
                self.render_metric_card(metric, data)
    
    def render_metric_card(self, metric: str, data: Dict[str, Any]):
        """Render individual metric card"""
        metric_display = metric.replace('_', ' ').title()
        
        with st.container():
            st.markdown(f"**{metric_display}**")
            
            # Progress bar
            if data['is_unlimited']:
                st.progress(0.0)
                st.write(f"Usage: {data['current_usage']:.1f} (Unlimited)")
            else:
                progress = min(data['percentage_used'] / 100, 1.0)
                st.progress(progress)
                st.write(f"Usage: {data['current_usage']:.1f} / {data['limit']:.1f} ({data['percentage_used']:.1f}%)")
            
            # Additional info
            col1, col2 = st.columns(2)
            
            with col1:
                if data['overage'] > 0:
                    st.write(f"🔴 Overage: {data['overage']:.1f}")
                else:
                    remaining = data['limit'] - data['current_usage'] if not data['is_unlimited'] else float('inf')
                    if remaining == float('inf'):
                        st.write("🟢 Unlimited")
                    else:
                        st.write(f"🟢 Remaining: {remaining:.1f}")
            
            with col2:
                if data['overage_cost_cents'] > 0:
                    st.write(f"💰 Cost: ${data['overage_cost_cents']/100:.2f}")
                else:
                    st.write(f"⚙️ Action: {data['action'].title()}")
            
            st.markdown("---")
    
    def render_usage_charts(self):
        """Render usage visualization charts"""
        st.header("📈 Usage Visualization")
        
        try:
            analytics = self.usage_system.get_usage_analytics(
                st.session_state.current_user_id,
                st.session_state.selected_team_id,
                st.session_state.selected_period
            )
            
            if 'error' in analytics or not analytics['metrics']:
                st.info("No usage data available for visualization.")
                return
            
            # Prepare data for charts
            metrics_data = []
            for metric, data in analytics['metrics'].items():
                if data['current_usage'] > 0:
                    metrics_data.append({
                        'Metric': metric.replace('_', ' ').title(),
                        'Current Usage': data['current_usage'],
                        'Limit': data['limit'] if not data['is_unlimited'] else data['current_usage'] * 2,
                        'Percentage Used': data['percentage_used'],
                        'Is Unlimited': data['is_unlimited'],
                        'Overage': data['overage'],
                        'Overage Cost': data['overage_cost_cents'] / 100
                    })
            
            if not metrics_data:
                st.info("No usage data to visualize.")
                return
            
            df = pd.DataFrame(metrics_data)
            
            # Usage vs Limits Chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Usage vs Limits")
                fig = go.Figure()
                
                # Current usage bars
                fig.add_trace(go.Bar(
                    name='Current Usage',
                    x=df['Metric'],
                    y=df['Current Usage'],
                    marker_color='lightblue'
                ))
                
                # Limit lines
                for i, row in df.iterrows():
                    if not row['Is Unlimited']:
                        fig.add_hline(
                            y=row['Limit'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"Limit: {row['Limit']:.1f}",
                            annotation_position="top right"
                        )
                
                fig.update_layout(
                    title="Current Usage vs Limits",
                    xaxis_title="Metrics",
                    yaxis_title="Usage Amount",
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Usage Percentage")
                
                # Filter out unlimited metrics for percentage chart
                limited_df = df[~df['Is Unlimited']]
                
                if not limited_df.empty:
                    fig = px.bar(
                        limited_df,
                        x='Metric',
                        y='Percentage Used',
                        title="Usage Percentage by Metric",
                        color='Percentage Used',
                        color_continuous_scale=['green', 'yellow', 'red'],
                        range_color=[0, 100]
                    )
                    
                    # Add warning threshold line
                    fig.add_hline(
                        y=80,
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="Warning Threshold (80%)",
                        annotation_position="top right"
                    )
                    
                    fig.update_layout(
                        xaxis_title="Metrics",
                        yaxis_title="Percentage Used (%)",
                        yaxis_range=[0, 120]
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No limited metrics to show percentage usage.")
            
            # Overage costs if any
            overage_df = df[df['Overage Cost'] > 0]
            if not overage_df.empty:
                st.subheader("Overage Costs")
                
                fig = px.bar(
                    overage_df,
                    x='Metric',
                    y='Overage Cost',
                    title="Overage Costs by Metric",
                    color='Overage Cost',
                    color_continuous_scale='Reds'
                )
                
                fig.update_layout(
                    xaxis_title="Metrics",
                    yaxis_title="Overage Cost ($)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering usage charts: {e}")
            logger.error(f"Error in render_usage_charts: {e}")
    
    def render_quota_management(self):
        """Render quota management interface"""
        st.header("⚙️ Quota Management")
        
        tab1, tab2, tab3 = st.tabs(["Current Quotas", "Usage Simulator", "Quota History"])
        
        with tab1:
            self.render_current_quotas()
        
        with tab2:
            self.render_usage_simulator()
        
        with tab3:
            self.render_quota_history()
    
    def render_current_quotas(self):
        """Render current quota status"""
        st.subheader("Current Quota Status")
        
        try:
            # Get quota status for all metrics
            quota_statuses = []
            for metric in UsageMetric:
                quota_status = self.usage_system.get_quota_status(
                    st.session_state.current_user_id,
                    metric.value,
                    st.session_state.selected_team_id
                )
                quota_statuses.append({
                    'Metric': metric.value.replace('_', ' ').title(),
                    'Current Usage': quota_status.current_usage,
                    'Limit': quota_status.limit if quota_status.limit != -1 else 'Unlimited',
                    'Remaining': quota_status.remaining if quota_status.remaining != -1 else 'Unlimited',
                    'Percentage Used': f"{quota_status.percentage_used:.1f}%",
                    'Status': '🔴 Exceeded' if quota_status.is_exceeded else '🟢 OK',
                    'Next Reset': quota_status.next_reset[:10] if quota_status.next_reset != 'N/A' else 'N/A'
                })
            
            df = pd.DataFrame(quota_statuses)
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading quota status: {e}")
    
    def render_usage_simulator(self):
        """Render usage simulation interface"""
        st.subheader("Usage Simulator")
        st.write("Simulate usage to see how it would affect your quotas.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_metric = st.selectbox(
                "Metric",
                options=[metric.value for metric in UsageMetric],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            usage_amount = st.number_input(
                "Usage Amount",
                min_value=0.0,
                value=1.0,
                step=0.1,
                help="Amount of usage to simulate"
            )
        
        with col3:
            if st.button("Simulate Usage", type="primary"):
                try:
                    # Check what would happen with this usage
                    allowed, message, quota_status = self.usage_system.quota_manager.check_quota(
                        st.session_state.current_user_id,
                        selected_metric,
                        usage_amount,
                        st.session_state.selected_team_id
                    )
                    
                    if allowed:
                        st.success(f"✅ Usage allowed: {message}")
                    else:
                        st.error(f"❌ Usage blocked: {message}")
                    
                    if quota_status:
                        st.write("**Quota Status After Simulation:**")
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric(
                                "Usage After",
                                f"{quota_status.current_usage + usage_amount:.1f}",
                                delta=f"+{usage_amount:.1f}"
                            )
                        
                        with col_b:
                            if quota_status.limit != -1:
                                st.metric(
                                    "Percentage Used",
                                    f"{((quota_status.current_usage + usage_amount) / quota_status.limit * 100):.1f}%"
                                )
                            else:
                                st.metric("Percentage Used", "N/A (Unlimited)")
                        
                        with col_c:
                            if quota_status.overage_cost_cents > 0:
                                st.metric(
                                    "Overage Cost",
                                    f"${quota_status.overage_cost_cents/100:.2f}",
                                    delta=f"+${quota_status.overage_cost_cents/100:.2f}",
                                    delta_color="inverse"
                                )
                            else:
                                st.metric("Overage Cost", "$0.00")
                
                except Exception as e:
                    st.error(f"Error simulating usage: {e}")
    
    def render_quota_history(self):
        """Render quota violation history"""
        st.subheader("Quota History")
        st.info("This would show historical quota violations and usage patterns. In a full implementation, this would query the quota_violations and usage_records tables.")
        
        # Mock data for demonstration
        mock_history = [
            {
                'Date': '2024-02-01',
                'Metric': 'Transcription Hours',
                'Action': 'Warning Sent',
                'Usage': '4.2/5.0',
                'Details': '84% of quota used'
            },
            {
                'Date': '2024-02-05',
                'Metric': 'API Calls',
                'Action': 'Quota Exceeded',
                'Usage': '1050/1000',
                'Details': 'Blocked 50 calls'
            },
            {
                'Date': '2024-02-10',
                'Metric': 'Storage',
                'Action': 'Overage Charged',
                'Usage': '1.2/1.0 GB',
                'Details': '$0.40 overage fee'
            }
        ]
        
        df = pd.DataFrame(mock_history)
        st.dataframe(df, use_container_width=True)
    
    def render_admin_tools(self):
        """Render admin tools for quota management"""
        st.header("🔧 Admin Tools")
        
        if st.checkbox("Show Admin Tools", help="Enable admin functionality"):
            st.warning("⚠️ Admin tools - use with caution")
            
            tab1, tab2, tab3 = st.tabs(["Record Usage", "Manage Quotas", "System Status"])
            
            with tab1:
                self.render_manual_usage_recording()
            
            with tab2:
                self.render_quota_configuration()
            
            with tab3:
                self.render_system_status()
    
    def render_manual_usage_recording(self):
        """Render manual usage recording interface"""
        st.subheader("Manual Usage Recording")
        
        col1, col2 = st.columns(2)
        
        with col1:
            metric = st.selectbox(
                "Metric",
                options=[metric.value for metric in UsageMetric],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="admin_metric"
            )
            
            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=1.0,
                step=0.1,
                key="admin_quantity"
            )
        
        with col2:
            user_id = st.text_input(
                "User ID",
                value=st.session_state.current_user_id,
                key="admin_user_id"
            )
            
            team_id = st.text_input(
                "Team ID (Optional)",
                value=st.session_state.selected_team_id or "",
                key="admin_team_id"
            )
        
        metadata = st.text_area(
            "Metadata (JSON)",
            value='{"source": "admin_manual", "reason": "manual_entry"}',
            help="Additional metadata in JSON format"
        )
        
        if st.button("Record Usage", type="primary"):
            try:
                metadata_dict = json.loads(metadata) if metadata else {}
                
                success, message, quota_status = self.usage_system.record_usage(
                    user_id=user_id,
                    metric=metric,
                    quantity=quantity,
                    team_id=team_id if team_id else None,
                    metadata=metadata_dict,
                    check_quota=True
                )
                
                if success:
                    st.success(f"✅ Usage recorded: {message}")
                else:
                    st.error(f"❌ Failed to record usage: {message}")
                
                if quota_status:
                    st.write(f"**Quota Status:** {quota_status.current_usage:.1f}/{quota_status.limit} ({quota_status.percentage_used:.1f}% used)")
                
            except json.JSONDecodeError:
                st.error("Invalid JSON in metadata field")
            except Exception as e:
                st.error(f"Error recording usage: {e}")
    
    def render_quota_configuration(self):
        """Render quota configuration interface"""
        st.subheader("Quota Configuration")
        st.info("This would allow admins to configure custom quota limits. In a full implementation, this would interface with the quota_limits table.")
        
        # Mock interface
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Subscription Tier", ["Free", "Pro", "Enterprise"])
            st.selectbox("Metric", [metric.value.replace('_', ' ').title() for metric in UsageMetric])
            st.number_input("Limit", min_value=-1.0, value=5.0, help="-1 for unlimited")
        
        with col2:
            st.selectbox("Period", [period.value.replace('_', ' ').title() for period in UsagePeriod])
            st.selectbox("Action", [action.value.title() for action in QuotaAction])
            st.number_input("Warning Threshold (%)", min_value=0.0, max_value=100.0, value=80.0)
        
        if st.button("Update Quota Configuration"):
            st.info("Quota configuration would be updated in the database.")
    
    def render_system_status(self):
        """Render system status information"""
        st.subheader("System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Users", "1,234", delta="12")
            st.metric("Total Usage Records", "45,678", delta="234")
        
        with col2:
            st.metric("Cache Hit Rate", "94.2%", delta="2.1%")
            st.metric("Avg Response Time", "45ms", delta="-5ms")
        
        with col3:
            st.metric("Quota Violations", "23", delta="3", delta_color="inverse")
            st.metric("System Health", "Healthy", help="All systems operational")
        
        # System logs (mock)
        st.subheader("Recent System Events")
        mock_logs = [
            "2024-02-08 10:30:15 - Usage cache flushed successfully",
            "2024-02-08 10:25:42 - Quota warning sent to user_123",
            "2024-02-08 10:20:18 - New subscription tier activated",
            "2024-02-08 10:15:33 - Database backup completed",
            "2024-02-08 10:10:07 - System health check passed"
        ]
        
        for log in mock_logs:
            st.text(log)
    
    def run(self):
        """Run the Streamlit application"""
        st.set_page_config(
            page_title="Usage Tracking & Quota Management",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox(
            "Select Page",
            ["Usage Overview", "Usage Charts", "Quota Management", "Admin Tools"]
        )
        
        # Render header
        self.render_header()
        
        # Render selected page
        if page == "Usage Overview":
            self.render_usage_overview()
        elif page == "Usage Charts":
            self.render_usage_charts()
        elif page == "Quota Management":
            self.render_quota_management()
        elif page == "Admin Tools":
            self.render_admin_tools()
        
        # Footer
        st.markdown("---")
        st.markdown("**Usage Tracking & Quota Management System** - Built with Streamlit")

def main():
    """Main function to run the UI"""
    ui = UsageTrackingUI()
    ui.run()

if __name__ == "__main__":
    main()