#!/usr/bin/env python3
"""
User Confidence Engine UI - Intent-First Interface
Streamlit interface for user-facing system confidence indicators
"""

import streamlit as st
import asyncio
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from user_confidence_engine import (
    UserConfidenceEngine, ConfidenceLevel, ImpactLevel
)

class UserConfidenceUI:
    """Streamlit UI for User Confidence Engine"""
    
    def __init__(self):
        self.engine = UserConfidenceEngine()
        
        # Initialize session state
        if 'confidence_data' not in st.session_state:
            st.session_state.confidence_data = None
        if 'last_update' not in st.session_state:
            st.session_state.last_update = None
    
    def render_main_dashboard(self):
        """Render the main user confidence dashboard"""
        
        st.title("🎯 System Status & Confidence")
        st.markdown("Real-time system health translated into user-friendly insights")
        
        # Auto-refresh controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### Current System Status")
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=True)
        
        with col3:
            if st.button("🔄 Refresh Now") or auto_refresh:
                self._update_confidence_data()
        
        # Main confidence display
        if st.session_state.confidence_data:
            self._render_confidence_overview()
            self._render_detailed_metrics()
            self._render_proactive_alerts()
            self._render_impact_analysis()
        else:
            with st.spinner("Loading system confidence data..."):
                self._update_confidence_data()
                if st.session_state.confidence_data:
                    st.rerun()
    
    def _update_confidence_data(self):
        """Update confidence data from engine"""
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            confidence_data = loop.run_until_complete(
                self.engine.get_user_confidence_indicators()
            )
            loop.close()
            
            st.session_state.confidence_data = confidence_data
            st.session_state.last_update = datetime.now()
            
        except Exception as e:
            st.error(f"Error updating confidence data: {e}")
    
    def _render_confidence_overview(self):
        """Render main confidence overview"""
        confidence = st.session_state.confidence_data
        
        # Main status card
        confidence_color = self._get_confidence_color(confidence.confidence_level)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {confidence_color}20, {confidence_color}10);
            border-left: 5px solid {confidence_color};
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        ">
            <h2 style="color: {confidence_color}; margin: 0;">
                {confidence.user_message}
            </h2>
            <p style="font-size: 18px; margin: 10px 0 0 0;">
                <strong>Processing Time:</strong> {confidence.estimated_processing_time}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Reliability Score",
                f"{confidence.reliability_score:.1%}",
                delta=None,
                help="Overall system reliability based on current performance"
            )
        
        with col2:
            confidence_emoji = self._get_confidence_emoji(confidence.confidence_level)
            st.metric(
                "Confidence Level",
                f"{confidence_emoji} {confidence.confidence_level.value.title()}",
                help="User confidence level in system performance"
            )
        
        with col3:
            quality_score = confidence.quality_indicators.get('transcription_accuracy', 0.96)
            st.metric(
                "Quality Score",
                f"{quality_score:.1%}",
                delta="+2.1%" if quality_score > 0.95 else None,
                help="Current transcription accuracy and quality"
            )
        
        with col4:
            st.metric(
                "System Status",
                "🟢 Optimal" if confidence.reliability_score > 0.9 else "🟡 Good",
                help="Overall system operational status"
            )
    
    def _render_detailed_metrics(self):
        """Render detailed system metrics"""
        confidence = st.session_state.confidence_data
        
        st.markdown("### 📊 Detailed System Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Quality Indicators")
            quality = confidence.quality_indicators
            
            # Quality metrics
            metrics_data = {
                'Metric': ['Transcription Accuracy', 'Processing Speed', 'AI Model Status', 'Data Security'],
                'Status': [
                    f"{quality.get('transcription_accuracy', 0.96):.1%}",
                    quality.get('processing_speed', 'optimal').title(),
                    quality.get('ai_model_status', 'premium_active').replace('_', ' ').title(),
                    quality.get('data_security', 'fully_encrypted').replace('_', ' ').title()
                ],
                'Indicator': ['🟢', '🟢', '🟢', '🟢']
            }
            
            df = pd.DataFrame(metrics_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("#### System Performance")
            
            # Create performance gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = confidence.reliability_score * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "System Reliability"},
                delta = {'reference': 95},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': self._get_confidence_color(confidence.confidence_level)},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgray"},
                        {'range': [70, 85], 'color': "yellow"},
                        {'range': [85, 100], 'color': "lightgreen"}
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
    
    def _render_proactive_alerts(self):
        """Render proactive alerts and recommendations"""
        confidence = st.session_state.confidence_data
        
        if confidence.proactive_alerts:
            st.markdown("### 🔔 Proactive Insights")
            
            for i, alert in enumerate(confidence.proactive_alerts):
                alert_type = self._classify_alert_type(alert)
                icon, color = self._get_alert_styling(alert_type)
                
                st.markdown(f"""
                <div style="
                    background: {color}15;
                    border-left: 4px solid {color};
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                ">
                    <p style="margin: 0; color: {color};">
                        {icon} <strong>{alert}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Next maintenance window
        if confidence.next_maintenance:
            st.info(f"📅 **Scheduled Maintenance:** {confidence.next_maintenance}")
    
    def _render_impact_analysis(self):
        """Render impact analysis section"""
        st.markdown("### ⚠️ System Impact Analysis")
        
        # Test different scenarios
        scenarios = [
            ("Current CPU Load", "cpu_usage", 75.0),
            ("Current Memory Usage", "memory_usage", 68.0),
            ("Current Disk Usage", "disk_usage", 45.0),
            ("Current Error Rate", "error_rate", 1.2)
        ]
        
        impact_data = []
        
        for scenario_name, metric, value in scenarios:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                impact = loop.run_until_complete(
                    self.engine.predict_user_impact(metric, value)
                )
                loop.close()
                
                impact_data.append({
                    'Scenario': scenario_name,
                    'Impact Level': impact.impact_level.value.title(),
                    'User Message': impact.user_message,
                    'Affected Features': ', '.join(impact.affected_features) if impact.affected_features else 'None'
                })
                
            except Exception as e:
                st.error(f"Error analyzing {scenario_name}: {e}")
        
        if impact_data:
            df = pd.DataFrame(impact_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
    
    def _get_confidence_color(self, level: ConfidenceLevel) -> str:
        """Get color for confidence level"""
        colors = {
            ConfidenceLevel.EXCELLENT: "#00C851",
            ConfidenceLevel.GOOD: "#39C0ED", 
            ConfidenceLevel.FAIR: "#ffbb33",
            ConfidenceLevel.POOR: "#ff4444"
        }
        return colors.get(level, "#6c757d")
    
    def _get_confidence_emoji(self, level: ConfidenceLevel) -> str:
        """Get emoji for confidence level"""
        emojis = {
            ConfidenceLevel.EXCELLENT: "🟢",
            ConfidenceLevel.GOOD: "🔵",
            ConfidenceLevel.FAIR: "🟡", 
            ConfidenceLevel.POOR: "🔴"
        }
        return emojis.get(level, "⚪")
    
    def _classify_alert_type(self, alert: str) -> str:
        """Classify alert type from message"""
        alert_lower = alert.lower()
        if 'maintenance' in alert_lower:
            return 'maintenance'
        elif 'optimal' in alert_lower or 'faster' in alert_lower:
            return 'opportunity'
        elif 'peak' in alert_lower:
            return 'warning'
        else:
            return 'info'
    
    def _get_alert_styling(self, alert_type: str) -> tuple:
        """Get icon and color for alert type"""
        styling = {
            'maintenance': ('🔧', '#17a2b8'),
            'opportunity': ('⚡', '#28a745'),
            'warning': ('⚠️', '#ffc107'),
            'info': ('ℹ️', '#6f42c1')
        }
        return styling.get(alert_type, ('ℹ️', '#6c757d'))

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="System Confidence Dashboard",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    </style>
    """, unsafe_allow_html=True)
    
    ui = UserConfidenceUI()
    ui.render_main_dashboard()
    
    # Sidebar with additional info
    with st.sidebar:
        st.markdown("### 🎯 About System Confidence")
        st.markdown("""
        This dashboard translates technical system metrics into user-friendly 
        confidence indicators, helping you understand:
        
        - **System Reliability**: How dependable the system is right now
        - **Processing Times**: Expected wait times for your tasks
        - **Proactive Alerts**: Helpful insights and recommendations
        - **Impact Analysis**: How system conditions affect your experience
        """)
        
        st.markdown("### 🔄 Auto-Refresh")
        st.markdown("The dashboard automatically updates to provide real-time insights.")
        
        if st.session_state.last_update:
            st.markdown(f"**Last Updated:** {st.session_state.last_update.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()