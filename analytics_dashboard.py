"""
Interactive Analytics Dashboard
Real-time analytics dashboard with interactive visualizations and monitoring
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import redis.asyncio as redis
from pathlib import Path
import time
from collections import defaultdict, deque
import threading
import queue

# Import our analytics components
from advanced_analytics_reporting import (
    AdvancedAnalyticsEngine, ReportGenerator, ReportScheduler,
    MetricDefinition, MetricCategory, AnalyticsData, ReportConfig,
    ReportType, ReportFormat
)

logger = logging.getLogger(__name__)

class DashboardConfig:
    """Dashboard configuration settings"""
    
    def __init__(self):
        self.refresh_interval = 30  # seconds
        self.max_data_points = 1000
        self.default_time_range = "24h"
        self.theme = "plotly_dark"
        self.auto_refresh = True
        self.show_anomalies = True
        self.show_predictions = True

class RealTimeDashboard:
    """Real-time analytics dashboard"""
    
    def __init__(self, analytics_engine: AdvancedAnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.config = DashboardConfig()
        self.data_queue = queue.Queue()
        self.running = False
        self.last_update = datetime.now()
        
        # Dashboard state
        self.selected_metrics = []
        self.time_range = "24h"
        self.filters = {}
        
        # Initialize Streamlit page config
        st.set_page_config(
            page_title="Analytics Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def run(self):
        """Run the interactive dashboard"""
        # Initialize session state
        if 'dashboard_initialized' not in st.session_state:
            st.session_state.dashboard_initialized = True
            st.session_state.selected_metrics = list(self.analytics_engine.metric_definitions.keys())[:6]
            st.session_state.auto_refresh = True
            st.session_state.refresh_interval = 30
        
        # Dashboard header
        st.title("🔍 Advanced Analytics Dashboard")
        st.markdown("Real-time monitoring and analytics for your transcription platform")
        
        # Sidebar configuration
        self._render_sidebar()
        
        # Main dashboard content
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.subheader("📈 Key Metrics Overview")
            self._render_metrics_overview()
        
        with col2:
            st.subheader("🎯 Performance Summary")
            self._render_performance_summary()
        
        with col3:
            st.subheader("🚨 Alerts & Status")
            self._render_alerts_panel()
        
        # Detailed charts section
        st.subheader("📊 Detailed Analytics")
        self._render_detailed_charts()
        
        # Advanced analytics section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔮 Predictive Analysis")
            self._render_predictions()
        
        with col2:
            st.subheader("🎲 Anomaly Detection")
            self._render_anomalies()
        
        # Medical analytics section (if available)
        if any('medical' in metric_id.lower() for metric_id in st.session_state.selected_metrics):
            st.subheader("🏥 Medical Analytics")
            self._render_medical_analytics()
        
        # Auto-refresh functionality
        if st.session_state.auto_refresh:
            time.sleep(st.session_state.refresh_interval)
            st.rerun()
    
    def _render_sidebar(self):
        """Render the sidebar configuration panel"""
        st.sidebar.title("⚙️ Dashboard Settings")
        
        # Metric selection
        st.sidebar.subheader("📊 Metrics to Display")
        available_metrics = list(self.analytics_engine.metric_definitions.keys())
        st.session_state.selected_metrics = st.sidebar.multiselect(
            "Select metrics to monitor:",
            available_metrics,
            default=st.session_state.get('selected_metrics', available_metrics[:6]),
            help="Choose which metrics to display on the dashboard"
        )
        
        # Time range selection
        st.sidebar.subheader("⏰ Time Range")
        time_ranges = {
            "Last Hour": "1h",
            "Last 6 Hours": "6h", 
            "Last 24 Hours": "24h",
            "Last 7 Days": "7d",
            "Last 30 Days": "30d"
        }
        
        selected_range = st.sidebar.selectbox(
            "Time Range:",
            options=list(time_ranges.keys()),
            index=2,  # Default to 24h
            help="Select the time period for analytics"
        )
        self.time_range = time_ranges[selected_range]
        
        # Filters
        st.sidebar.subheader("🎛️ Filters")
        
        # Session type filter
        session_types = ["all", "medical", "general", "legal"]
        selected_session_type = st.sidebar.selectbox(
            "Session Type:",
            session_types,
            help="Filter by session type"
        )
        
        if selected_session_type != "all":
            self.filters["session_type"] = selected_session_type
        else:
            self.filters = {}
        
        # Auto-refresh settings
        st.sidebar.subheader("🔄 Auto Refresh")
        st.session_state.auto_refresh = st.sidebar.checkbox(
            "Enable auto-refresh",
            value=st.session_state.get('auto_refresh', True),
            help="Automatically refresh dashboard data"
        )
        
        if st.session_state.auto_refresh:
            st.session_state.refresh_interval = st.sidebar.slider(
                "Refresh interval (seconds):",
                min_value=10,
                max_value=300,
                value=st.session_state.get('refresh_interval', 30),
                step=10,
                help="How often to refresh the dashboard"
            )
        
        # Dashboard actions
        st.sidebar.subheader("📋 Actions")
        
        if st.sidebar.button("🔄 Refresh Now", help="Manually refresh all data"):
            st.rerun()
        
        if st.sidebar.button("📊 Generate Report", help="Generate comprehensive report"):
            self._generate_report()
        
        if st.sidebar.button("⚠️ Test Alert", help="Test alert system"):
            st.sidebar.success("Test alert triggered!")
        
        # Export options
        if st.sidebar.button("📁 Export Data", help="Export current dashboard data"):
            self._export_dashboard_data()
    
    def _render_metrics_overview(self):
        """Render key metrics overview cards"""
        metrics_data = {}
        
        # Calculate current values for selected metrics
        for metric_id in st.session_state.selected_metrics[:4]:  # Show top 4 metrics
            try:
                current_value = self.analytics_engine.calculate_metric(
                    metric_id, self.time_range, self.filters
                )
                trend = self.analytics_engine.calculate_trend(metric_id, periods=7)
                
                metrics_data[metric_id] = {
                    "value": current_value,
                    "trend": trend
                }
            except Exception as e:
                logger.error(f"Error calculating metric {metric_id}: {e}")
                continue
        
        # Display metrics in a grid
        cols = st.columns(len(metrics_data))
        
        for i, (metric_id, data) in enumerate(metrics_data.items()):
            with cols[i]:
                metric_def = self.analytics_engine.metric_definitions.get(metric_id)
                if not metric_def:
                    continue
                
                # Determine trend color and icon
                trend_direction = data["trend"].get("direction", "stable")
                trend_percent = data["trend"].get("change_percent", 0)
                
                if trend_direction == "increasing":
                    trend_color = "normal" if metric_def.trend_direction == "higher_better" else "inverse"
                    trend_icon = "⬆️"
                else:
                    trend_color = "inverse" if metric_def.trend_direction == "higher_better" else "normal"
                    trend_icon = "⬇️" if trend_direction == "decreasing" else "➡️"
                
                # Create metric card
                st.metric(
                    label=metric_def.name,
                    value=f"{data['value']:.2f} {metric_def.unit}",
                    delta=f"{trend_percent:.1f}% {trend_icon}",
                    delta_color=trend_color
                )
    
    def _render_performance_summary(self):
        """Render performance summary charts"""
        # Create performance summary chart
        metrics_for_summary = st.session_state.selected_metrics[:3]
        
        if not metrics_for_summary:
            st.warning("No metrics selected for performance summary")
            return
        
        # Calculate performance scores
        performance_data = []
        
        for metric_id in metrics_for_summary:
            try:
                current_value = self.analytics_engine.calculate_metric(
                    metric_id, self.time_range, self.filters
                )
                metric_def = self.analytics_engine.metric_definitions.get(metric_id)
                
                if metric_def and metric_def.target_value:
                    # Calculate performance score (0-100%)
                    if metric_def.trend_direction == "higher_better":
                        score = min(100, (current_value / metric_def.target_value) * 100)
                    else:
                        score = max(0, 100 - ((current_value / metric_def.target_value) * 100))
                    
                    performance_data.append({
                        "metric": metric_def.name,
                        "score": score,
                        "current": current_value,
                        "target": metric_def.target_value
                    })
            except Exception as e:
                logger.error(f"Error calculating performance for {metric_id}: {e}")
                continue
        
        if performance_data:
            # Create radar chart
            df = pd.DataFrame(performance_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=df['score'],
                theta=df['metric'],
                fill='toself',
                name='Performance Score',
                line_color='rgb(68, 68, 68)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Performance Score Overview",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available for selected metrics")
    
    def _render_alerts_panel(self):
        """Render alerts and status panel"""
        # Get recent anomalies and alerts
        alerts = []
        anomaly_count = 0
        
        for metric_id in st.session_state.selected_metrics:
            try:
                anomalies = self.analytics_engine.detect_anomalies(metric_id, time_range="24h")
                anomaly_count += len(anomalies)
                
                # Check for threshold violations
                current_value = self.analytics_engine.calculate_metric(metric_id, "1h", self.filters)
                metric_def = self.analytics_engine.metric_definitions.get(metric_id)
                
                if metric_def:
                    if (metric_def.critical_threshold and 
                        ((metric_def.trend_direction == "lower_better" and current_value > metric_def.critical_threshold) or
                         (metric_def.trend_direction == "higher_better" and current_value < metric_def.critical_threshold))):
                        alerts.append({
                            "level": "🔴 CRITICAL",
                            "metric": metric_def.name,
                            "message": f"Value {current_value:.2f} exceeds critical threshold {metric_def.critical_threshold}"
                        })
                    elif (metric_def.warning_threshold and 
                          ((metric_def.trend_direction == "lower_better" and current_value > metric_def.warning_threshold) or
                           (metric_def.trend_direction == "higher_better" and current_value < metric_def.warning_threshold))):
                        alerts.append({
                            "level": "🟡 WARNING", 
                            "metric": metric_def.name,
                            "message": f"Value {current_value:.2f} exceeds warning threshold {metric_def.warning_threshold}"
                        })
                        
            except Exception as e:
                logger.error(f"Error checking alerts for {metric_id}: {e}")
                continue
        
        # Display system status
        if not alerts:
            st.success("🟢 All Systems Normal")
        else:
            st.error(f"⚠️ {len(alerts)} Active Alerts")
        
        # Display alerts
        if alerts:
            for alert in alerts[:5]:  # Show top 5 alerts
                st.warning(f"{alert['level']} **{alert['metric']}**: {alert['message']}")
        
        # Display anomaly count
        if anomaly_count > 0:
            st.info(f"🔍 {anomaly_count} anomalies detected in last 24h")
        
        # System health indicators
        st.markdown("### System Health")
        
        # Calculate overall health score
        health_score = 100
        if alerts:
            critical_alerts = len([a for a in alerts if "CRITICAL" in a["level"]])
            warning_alerts = len([a for a in alerts if "WARNING" in a["level"]])
            health_score = max(0, 100 - (critical_alerts * 20) - (warning_alerts * 10))
        
        if health_score >= 90:
            st.success(f"Health Score: {health_score}%")
        elif health_score >= 70:
            st.warning(f"Health Score: {health_score}%")
        else:
            st.error(f"Health Score: {health_score}%")
    
    def _render_detailed_charts(self):
        """Render detailed charts for selected metrics"""
        num_metrics = len(st.session_state.selected_metrics)
        if num_metrics == 0:
            st.warning("No metrics selected")
            return
        
        # Create charts in a grid layout
        cols_per_row = 2
        rows = (num_metrics + cols_per_row - 1) // cols_per_row
        
        for row in range(rows):
            cols = st.columns(cols_per_row)
            
            for col_idx in range(cols_per_row):
                metric_idx = row * cols_per_row + col_idx
                if metric_idx >= num_metrics:
                    break
                
                metric_id = st.session_state.selected_metrics[metric_idx]
                
                with cols[col_idx]:
                    self._render_metric_chart(metric_id)
    
    def _render_metric_chart(self, metric_id: str):
        """Render individual metric chart"""
        try:
            metric_def = self.analytics_engine.metric_definitions.get(metric_id)
            if not metric_def:
                st.error(f"Metric definition not found: {metric_id}")
                return
            
            # Get trend data
            periods = 24 if self.time_range.endswith('h') else 30
            trend_data = self.analytics_engine.calculate_trend(
                metric_id, 
                periods=periods,
                period_length="1h" if self.time_range.endswith('h') else "1d"
            )
            
            if not trend_data.get('values') or not trend_data.get('timestamps'):
                st.info(f"No data available for {metric_def.name}")
                return
            
            # Create time series chart
            fig = go.Figure()
            
            # Main trend line
            fig.add_trace(go.Scatter(
                x=trend_data['timestamps'],
                y=trend_data['values'],
                mode='lines+markers',
                name=metric_def.name,
                line=dict(width=2, color='#1f77b4'),
                marker=dict(size=4)
            ))
            
            # Add threshold lines if available
            if metric_def.warning_threshold:
                fig.add_hline(
                    y=metric_def.warning_threshold,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Warning"
                )
            
            if metric_def.critical_threshold:
                fig.add_hline(
                    y=metric_def.critical_threshold,
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Critical"
                )
            
            # Add target line if available
            if metric_def.target_value:
                fig.add_hline(
                    y=metric_def.target_value,
                    line_dash="dot",
                    line_color="green",
                    annotation_text="Target"
                )
            
            # Update layout
            fig.update_layout(
                title=f"{metric_def.name} ({metric_def.unit})",
                xaxis_title="Time",
                yaxis_title=metric_def.unit,
                height=300,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show current value and trend
            current_value = trend_data.get('latest_value', 0)
            change_percent = trend_data.get('change_percent', 0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current", f"{current_value:.2f}")
            with col2:
                st.metric("Change", f"{change_percent:+.1f}%")
                
        except Exception as e:
            st.error(f"Error rendering chart for {metric_id}: {e}")
            logger.error(f"Chart rendering error for {metric_id}: {e}")
    
    def _render_predictions(self):
        """Render predictive analysis section"""
        if not st.session_state.selected_metrics:
            st.info("Select metrics to see predictions")
            return
        
        # Select metric for prediction
        selected_metric = st.selectbox(
            "Select metric for prediction:",
            st.session_state.selected_metrics,
            help="Choose a metric to see predictive analysis"
        )
        
        if selected_metric:
            try:
                # Get historical data for prediction
                trend_data = self.analytics_engine.calculate_trend(
                    selected_metric, periods=30, period_length="1d"
                )
                
                if trend_data.get('values'):
                    values = trend_data['values']
                    timestamps = pd.to_datetime(trend_data['timestamps'])
                    
                    # Simple linear prediction for next 7 days
                    from scipy import stats
                    x = np.arange(len(values))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                    
                    # Generate predictions
                    future_days = 7
                    future_x = np.arange(len(values), len(values) + future_days)
                    predictions = slope * future_x + intercept
                    
                    # Create future timestamps
                    last_timestamp = timestamps[-1]
                    future_timestamps = [last_timestamp + timedelta(days=i+1) for i in range(future_days)]
                    
                    # Create prediction chart
                    fig = go.Figure()
                    
                    # Historical data
                    fig.add_trace(go.Scatter(
                        x=timestamps,
                        y=values,
                        mode='lines+markers',
                        name='Historical',
                        line=dict(color='blue')
                    ))
                    
                    # Predictions
                    fig.add_trace(go.Scatter(
                        x=future_timestamps,
                        y=predictions,
                        mode='lines+markers',
                        name='Predicted',
                        line=dict(color='red', dash='dash')
                    ))
                    
                    fig.update_layout(
                        title=f"7-Day Prediction for {selected_metric}",
                        xaxis_title="Date",
                        yaxis_title="Value",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show prediction summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Trend", "Increasing" if slope > 0 else "Decreasing")
                    with col2:
                        st.metric("Confidence", f"{abs(r_value):.2f}")
                    with col3:
                        avg_prediction = np.mean(predictions)
                        st.metric("Avg Predicted", f"{avg_prediction:.2f}")
                        
                else:
                    st.info("Insufficient data for prediction")
                    
            except Exception as e:
                st.error(f"Error generating predictions: {e}")
    
    def _render_anomalies(self):
        """Render anomaly detection section"""
        if not st.session_state.selected_metrics:
            st.info("Select metrics to see anomaly detection")
            return
        
        # Select metric for anomaly detection
        selected_metric = st.selectbox(
            "Select metric for anomaly detection:",
            st.session_state.selected_metrics,
            key="anomaly_metric",
            help="Choose a metric to analyze for anomalies"
        )
        
        if selected_metric:
            try:
                anomalies = self.analytics_engine.detect_anomalies(
                    selected_metric, time_range="7d", method="zscore"
                )
                
                if anomalies:
                    st.write(f"**Found {len(anomalies)} anomalies in the last 7 days:**")
                    
                    # Create anomaly visualization
                    anomaly_df = pd.DataFrame(anomalies)
                    anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
                    
                    fig = go.Figure()
                    
                    # Plot anomalies
                    colors = ['red' if severity == 'high' else 'orange' for severity in anomaly_df['severity']]
                    
                    fig.add_trace(go.Scatter(
                        x=anomaly_df['timestamp'],
                        y=anomaly_df['value'],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color=colors,
                            symbol='x'
                        ),
                        name='Anomalies',
                        text=[f"Severity: {s}<br>Z-score: {z:.2f}" for s, z in zip(anomaly_df['severity'], anomaly_df.get('z_score', [0]*len(anomaly_df)))],
                        hovertemplate='<b>%{text}</b><br>Value: %{y}<br>Time: %{x}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=f"Anomalies in {selected_metric}",
                        xaxis_title="Time",
                        yaxis_title="Value",
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show anomaly summary table
                    st.dataframe(
                        anomaly_df[['timestamp', 'value', 'severity']],
                        use_container_width=True
                    )
                    
                else:
                    st.success("No anomalies detected in the last 7 days")
                    
            except Exception as e:
                st.error(f"Error detecting anomalies: {e}")
    
    def _render_medical_analytics(self):
        """Render medical-specific analytics"""
        st.markdown("### Medical Transcription Analytics")
        
        # Medical compliance metrics
        medical_metrics = [m for m in st.session_state.selected_metrics if 'medical' in m.lower() or 'hipaa' in m.lower()]
        
        if not medical_metrics:
            st.info("No medical metrics selected")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Compliance Overview")
            
            compliance_data = []
            for metric_id in medical_metrics:
                try:
                    current_value = self.analytics_engine.calculate_metric(metric_id, "24h")
                    metric_def = self.analytics_engine.metric_definitions.get(metric_id)
                    
                    if metric_def:
                        compliance_data.append({
                            "Metric": metric_def.name,
                            "Current": f"{current_value:.1f}%",
                            "Target": f"{metric_def.target_value:.1f}%" if metric_def.target_value else "N/A",
                            "Status": "✅ Compliant" if current_value >= (metric_def.target_value or 95) else "⚠️ At Risk"
                        })
                except Exception as e:
                    logger.error(f"Error calculating medical metric {metric_id}: {e}")
                    continue
            
            if compliance_data:
                df = pd.DataFrame(compliance_data)
                st.dataframe(df, use_container_width=True)
        
        with col2:
            st.markdown("#### Medical Session Analysis")
            
            # Analyze medical vs general sessions
            try:
                medical_sessions = self.analytics_engine.calculate_metric(
                    "daily_active_users", "7d", {"session_type": "medical"}
                )
                total_sessions = self.analytics_engine.calculate_metric(
                    "daily_active_users", "7d"
                )
                
                if total_sessions > 0:
                    medical_percentage = (medical_sessions / total_sessions) * 100
                    
                    # Create pie chart
                    fig = go.Figure(data=[go.Pie(
                        labels=['Medical', 'General'],
                        values=[medical_sessions, total_sessions - medical_sessions],
                        hole=0.4
                    )])
                    
                    fig.update_layout(
                        title="Session Type Distribution (7 days)",
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.metric("Medical Sessions", f"{medical_percentage:.1f}%")
                else:
                    st.info("No session data available")
                    
            except Exception as e:
                st.error(f"Error analyzing medical sessions: {e}")
    
    def _generate_report(self):
        """Generate and download comprehensive report"""
        try:
            report_generator = ReportGenerator(self.analytics_engine)
            
            # Create report configuration
            report_config = ReportConfig(
                id=str(uuid.uuid4()),
                name=f"Dashboard_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=ReportType.PERFORMANCE,
                format=ReportFormat.HTML,
                metrics=st.session_state.selected_metrics,
                time_range=self.time_range,
                filters=self.filters
            )
            
            # Generate report
            with st.spinner("Generating report..."):
                report = asyncio.run(report_generator.generate_report(report_config))
            
            if report.file_path and Path(report.file_path).exists():
                # Provide download link
                with open(report.file_path, 'rb') as f:
                    st.download_button(
                        label="📄 Download Report",
                        data=f.read(),
                        file_name=f"{report.name}.html",
                        mime="text/html"
                    )
                st.success("Report generated successfully!")
            else:
                st.error("Failed to generate report file")
                
        except Exception as e:
            st.error(f"Error generating report: {e}")
            logger.error(f"Report generation error: {e}")
    
    def _export_dashboard_data(self):
        """Export current dashboard data"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "time_range": self.time_range,
                "filters": self.filters,
                "metrics": {}
            }
            
            # Collect current metric values
            for metric_id in st.session_state.selected_metrics:
                try:
                    current_value = self.analytics_engine.calculate_metric(
                        metric_id, self.time_range, self.filters
                    )
                    trend_data = self.analytics_engine.calculate_trend(metric_id)
                    
                    export_data["metrics"][metric_id] = {
                        "current_value": current_value,
                        "trend": trend_data
                    }
                except Exception as e:
                    logger.error(f"Error exporting metric {metric_id}: {e}")
                    continue
            
            # Convert to JSON
            json_data = json.dumps(export_data, indent=2, default=str)
            
            # Provide download
            st.download_button(
                label="📊 Download Dashboard Data",
                data=json_data,
                file_name=f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("Dashboard data exported!")
            
        except Exception as e:
            st.error(f"Error exporting data: {e}")

# Dashboard entry point
def main():
    """Main dashboard application"""
    # Initialize analytics engine
    analytics_engine = AdvancedAnalyticsEngine()
    
    # Create and run dashboard
    dashboard = RealTimeDashboard(analytics_engine)
    dashboard.run()

if __name__ == "__main__":
    main()