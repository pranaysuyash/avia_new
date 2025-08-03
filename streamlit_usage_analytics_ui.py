#!/usr/bin/env python3
"""
Streamlit Usage Analytics UI
Comprehensive usage tracking and analytics dashboard
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

class UsageAnalyticsUI:
    """Usage analytics dashboard interface"""
    
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
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
    
    def render_main(self):
        """Render main analytics interface"""
        st.title("📊 Usage Analytics")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Get dashboard data
        dashboard_data = self._api_request('GET', '/usage/analytics/dashboard')
        
        if not dashboard_data:
            st.error("Failed to load analytics data")
            return
        
        # Tab selection
        tabs = ["Overview", "Trends", "Patterns", "Forecasts", "Alerts", "Reports"]
        selected_tab = enhanced_tabs(tabs, key="analytics_tabs")
        
        if selected_tab == "Overview":
            self._render_overview_tab(dashboard_data)
        elif selected_tab == "Trends":
            self._render_trends_tab(dashboard_data)
        elif selected_tab == "Patterns":
            self._render_patterns_tab(dashboard_data)
        elif selected_tab == "Forecasts":
            self._render_forecasts_tab(dashboard_data)
        elif selected_tab == "Alerts":
            self._render_alerts_tab(dashboard_data)
        elif selected_tab == "Reports":
            self._render_reports_tab()
    
    def _render_overview_tab(self, data: Dict):
        """Render overview tab"""
        st.header("Usage Overview")
        
        # Current month summary
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate current month totals from trends
        current_month_start = datetime.now().replace(day=1).date()
        current_usage = {
            'transcripts': 0,
            'minutes': 0,
            'storage': 0,
            'api_calls': 0
        }
        
        for date_str, usage in data.get('trends', {}).get('trends', {}).items():
            date = datetime.fromisoformat(date_str).date()
            if date >= current_month_start:
                for usage_type, value in usage.items():
                    if usage_type in current_usage:
                        current_usage[usage_type] += value
        
        with col1:
            enhanced_metric(
                "Transcripts",
                f"{int(current_usage['transcripts'])}",
                "This month"
            )
        
        with col2:
            enhanced_metric(
                "Minutes",
                f"{int(current_usage['minutes'])}",
                "Processed"
            )
        
        with col3:
            enhanced_metric(
                "Storage",
                f"{current_usage['storage']:.1f} GB",
                "Used"
            )
        
        with col4:
            enhanced_metric(
                "API Calls",
                f"{int(current_usage['api_calls'])}",
                "This month"
            )
        
        # Usage chart
        st.subheader("30-Day Usage Trend")
        self._render_usage_chart(data.get('trends', {}))
        
        # Alerts summary
        alerts = data.get('alerts', [])
        if alerts:
            st.subheader("⚠️ Active Alerts")
            for alert in alerts:
                severity_color = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(alert.get('severity', 'low'), '🟢')
                
                with st.expander(f"{severity_color} {alert['message']}"):
                    st.write(f"**Type:** {alert['type']}")
                    st.write(f"**Usage Type:** {alert['usage_type']}")
                    if 'current_usage' in alert:
                        st.write(f"**Current:** {alert['current_usage']:.0f}")
                    if 'limit' in alert:
                        st.write(f"**Limit:** {alert['limit']}")
    
    def _render_trends_tab(self, data: Dict):
        """Render trends tab"""
        st.header("Usage Trends")
        
        # Period selector
        col1, col2 = st.columns([3, 1])
        with col1:
            days = st.slider("Select period (days)", 7, 90, 30)
        
        # Get trends data
        trends = self._api_request('GET', '/usage/analytics/trends', {'days': days})
        
        if trends:
            # Usage type selector
            usage_types = ['All', 'transcripts', 'minutes', 'storage', 'api_calls']
            selected_type = st.selectbox("Usage Type", usage_types)
            
            # Create line chart
            df_data = []
            for date_str, usage_data in trends.get('trends', {}).items():
                for usage_type, value in usage_data.items():
                    if selected_type == 'All' or usage_type == selected_type:
                        df_data.append({
                            'Date': date_str,
                            'Usage Type': usage_type,
                            'Value': value
                        })
            
            if df_data:
                df = pd.DataFrame(df_data)
                
                fig = px.line(
                    df,
                    x='Date',
                    y='Value',
                    color='Usage Type',
                    title=f'Usage Trends - Last {days} Days',
                    labels={'Value': 'Usage', 'Date': 'Date'}
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
                
                # Summary statistics
                st.subheader("Summary Statistics")
                
                summary_cols = st.columns(len(df['Usage Type'].unique()))
                for idx, usage_type in enumerate(df['Usage Type'].unique()):
                    type_data = df[df['Usage Type'] == usage_type]
                    with summary_cols[idx % len(summary_cols)]:
                        with enhanced_card():
                            st.write(f"**{usage_type.title()}**")
                            st.write(f"Total: {type_data['Value'].sum():.0f}")
                            st.write(f"Average: {type_data['Value'].mean():.1f}")
                            st.write(f"Peak: {type_data['Value'].max():.0f}")
    
    def _render_patterns_tab(self, data: Dict):
        """Render usage patterns tab"""
        st.header("Usage Patterns")
        
        # Get hourly patterns
        hourly_data = self._api_request('GET', '/usage/analytics/hourly', {'days': 7})
        
        if hourly_data:
            st.subheader("Usage by Hour of Day")
            
            # Create heatmap data
            hours = list(range(24))
            usage_types = ['transcripts', 'minutes', 'api_calls']
            
            heatmap_data = []
            for usage_type in usage_types:
                row_data = []
                for hour in hours:
                    hour_usage = hourly_data.get('hourly_usage', {}).get(hour, {})
                    value = hour_usage.get(usage_type, {}).get('total', 0)
                    row_data.append(value)
                heatmap_data.append(row_data)
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=[f"{h:02d}:00" for h in hours],
                y=usage_types,
                colorscale='Blues',
                hoverongaps=False
            ))
            
            fig.update_layout(
                title="Activity Heatmap - Last 7 Days",
                xaxis_title="Hour of Day",
                yaxis_title="Usage Type",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Resource distribution
        st.subheader("Resource Distribution")
        
        distribution = self._api_request('GET', '/usage/analytics/resource-distribution', {'days': 30})
        
        if distribution and distribution.get('distribution'):
            df_dist = pd.DataFrame(distribution['distribution'])
            
            if not df_dist.empty:
                fig = px.pie(
                    df_dist,
                    values='total_usage',
                    names='resource_type',
                    title='Resource Usage Distribution'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_forecasts_tab(self, data: Dict):
        """Render forecasts tab"""
        st.header("Usage Forecasts")
        
        forecasts = data.get('forecasts', {})
        
        if not forecasts:
            st.info("No forecast data available")
            return
        
        # Create forecast cards
        cols = st.columns(2)
        
        for idx, (usage_type, forecast) in enumerate(forecasts.items()):
            if forecast:
                with cols[idx % 2]:
                    with enhanced_card():
                        st.subheader(usage_type.title())
                        
                        # Progress bar
                        if forecast['limit'] > 0:
                            current_pct = (forecast['current_usage'] / forecast['limit']) * 100
                            projected_pct = forecast['projected_percentage']
                            
                            st.write(f"**Current Usage:** {forecast['current_usage']:.0f} / {forecast['limit']}")
                            enhanced_progress_indicator(
                                int(current_pct),
                                f"{current_pct:.0f}%",
                                key=f"current_{usage_type}"
                            )
                            
                            st.write(f"**Projected Usage:** {forecast['projected_usage']:.0f}")
                            
                            # Color code based on projection
                            if projected_pct > 100:
                                color = "🔴"
                            elif projected_pct > 90:
                                color = "🟡"
                            else:
                                color = "🟢"
                            
                            st.write(f"{color} Projected: {projected_pct:.0f}% of limit")
                            
                            if forecast['days_until_limit']:
                                st.warning(f"Will reach limit in {forecast['days_until_limit']} days")
                        else:
                            st.info("Unlimited")
                        
                        st.write(f"**Daily Average:** {forecast['daily_average']:.1f}")
    
    def _render_alerts_tab(self, data: Dict):
        """Render alerts tab"""
        st.header("Usage Alerts")
        
        # Alert settings
        with st.expander("Alert Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                email_alerts = st.checkbox("Email Alerts", value=True)
                weekly_summary = st.checkbox("Weekly Summary", value=True)
            
            with col2:
                monthly_summary = st.checkbox("Monthly Summary", value=True)
                threshold = st.slider("Alert Threshold (%)", 50, 100, 90)
            
            if enhanced_button("Save Settings", "primary", key="save_alert_settings"):
                # Save settings API call
                st.success("Alert settings saved")
        
        # Current alerts
        st.subheader("Active Alerts")
        
        alerts = data.get('alerts', [])
        
        if not alerts:
            st.success("No active alerts")
        else:
            for alert in alerts:
                severity_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(alert.get('severity', 'low'), '🟢')
                
                with enhanced_card():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.write(f"{severity_icon} **{alert['message']}**")
                        st.caption(f"Type: {alert['type']} | Usage: {alert['usage_type']}")
                    
                    with col2:
                        if st.button("Dismiss", key=f"dismiss_{alert.get('id', alert['type'])}"):
                            st.info("Alert dismissed")
        
        # Manual actions
        st.subheader("Manual Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if enhanced_button("Check for Alerts", "secondary", key="check_alerts"):
                result = self._api_request('POST', '/usage/analytics/alerts/send')
                if result:
                    st.success(f"Sent {result['sent_count']} alerts")
        
        with col2:
            if enhanced_button("Send Usage Summary", "secondary", key="send_summary"):
                period = st.selectbox("Period", ["weekly", "monthly"], key="summary_period")
                result = self._api_request('POST', f'/usage/analytics/summary/{period}')
                if result:
                    st.success(result['message'])
    
    def _render_reports_tab(self):
        """Render reports tab"""
        st.header("Usage Reports")
        
        # Report configuration
        with st.form("report_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=30)
                )
            
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now()
                )
            
            format_option = st.selectbox(
                "Export Format",
                ["View in Browser", "Download CSV", "Download PDF"]
            )
            
            generate_button = st.form_submit_button("Generate Report")
        
        if generate_button:
            # Generate report
            report_data = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'format': 'csv' if 'CSV' in format_option else 'json'
            }
            
            if 'CSV' in format_option:
                # Download CSV
                response = requests.post(
                    f"{self.api_base_url}/usage/analytics/report",
                    json=report_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    st.download_button(
                        "Download Report",
                        data=response.content,
                        file_name=f"usage_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            else:
                # Display in browser
                report = self._api_request('POST', '/usage/analytics/report', report_data)
                
                if report:
                    st.subheader("Report Summary")
                    
                    # Display summary
                    if report.get('usage_summary'):
                        for usage_type, data in report['usage_summary'].items():
                            with enhanced_card():
                                st.write(f"**{usage_type.title()}**")
                                st.write(f"Total: {data['total_quantity']:.0f}")
                                st.write(f"Records: {data['record_count']}")
                    
                    # Display as table
                    if report.get('trends'):
                        st.subheader("Daily Usage")
                        
                        # Convert to DataFrame
                        df_data = []
                        for date, usage in report['trends'].items():
                            row = {'Date': date}
                            row.update(usage)
                            df_data.append(row)
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
    
    def _render_usage_chart(self, trends_data: Dict):
        """Render usage trend chart"""
        if not trends_data.get('trends'):
            st.info("No trend data available")
            return
        
        # Prepare data for chart
        dates = []
        transcripts = []
        minutes = []
        api_calls = []
        
        for date_str, usage in sorted(trends_data['trends'].items()):
            dates.append(date_str)
            transcripts.append(usage.get('transcripts', 0))
            minutes.append(usage.get('minutes', 0))
            api_calls.append(usage.get('api_calls', 0))
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add traces
        fig.add_trace(go.Scatter(
            x=dates,
            y=transcripts,
            name='Transcripts',
            mode='lines+markers',
            line=dict(color='#007bff', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=minutes,
            name='Minutes',
            mode='lines+markers',
            line=dict(color='#28a745', width=2),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=api_calls,
            name='API Calls',
            mode='lines+markers',
            line=dict(color='#ffc107', width=2)
        ))
        
        # Update layout
        fig.update_layout(
            hovermode='x unified',
            yaxis=dict(title='Count'),
            yaxis2=dict(
                title='Minutes',
                overlaying='y',
                side='right'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Initialize and render
def main():
    """Main function to render usage analytics UI"""
    analytics_ui = UsageAnalyticsUI()
    analytics_ui.render_main()

if __name__ == "__main__":
    main()