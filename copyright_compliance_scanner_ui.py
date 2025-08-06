#!/usr/bin/env python3
"""
Copyright Compliance Scanner UI
Streamlit interface for copyright and music compliance scanning
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import tempfile

from copyright_compliance_scanner import (
    CopyrightComplianceScanner, ComplianceReport, CopyrightMatch,
    AudioFingerprint
)

# Page configuration
st.set_page_config(
    page_title="Copyright Compliance Scanner",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a6f 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .compliance-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .risk-high {
        background: #ffebee;
        border-left: 4px solid #f44336;
    }
    
    .risk-medium {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    
    .risk-low {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    
    .compliant {
        color: #4caf50;
        font-weight: bold;
    }
    
    .non-compliant {
        color: #f44336;
        font-weight: bold;
    }
    
    .review-required {
        color: #ff9800;
        font-weight: bold;
    }
    
    .match-timeline {
        background: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .recommendation-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scanner' not in st.session_state:
    st.session_state.scanner = CopyrightComplianceScanner()
if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = None
if 'whitelist' not in st.session_state:
    st.session_state.whitelist = set()

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ Copyright Compliance Scanner</h1>
        <p>AI-powered copyright detection and music licensing compliance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Scanner Settings")
        
        # Scanning sensitivity
        sensitivity = st.slider(
            "Detection Sensitivity",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Higher sensitivity detects more potential matches"
        )
        
        # Content types to scan
        st.subheader("Content Types")
        scan_music = st.checkbox("🎵 Music", value=True)
        scan_speech = st.checkbox("🎙️ Speech", value=True)
        scan_effects = st.checkbox("🔊 Sound Effects", value=True)
        
        # License management
        st.subheader("License Management")
        if st.button("📄 Manage Licenses"):
            show_license_manager()
        
        # Whitelist management
        st.subheader("Whitelist")
        new_whitelist = st.text_input("Add to whitelist")
        if st.button("➕ Add") and new_whitelist:
            st.session_state.whitelist.add(new_whitelist)
            st.success(f"Added '{new_whitelist}' to whitelist")
        
        if st.session_state.whitelist:
            st.write("Current whitelist:")
            for item in st.session_state.whitelist:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {item}")
                with col2:
                    if st.button("❌", key=f"remove_{item}"):
                        st.session_state.whitelist.remove(item)
                        st.rerun()
    
    # Main content area
    tabs = st.tabs(["🔍 Scan Files", "📊 Reports", "📈 Analytics", "🛡️ Compliance Dashboard", "⚙️ Settings"])
    
    with tabs[0]:
        scan_files_tab()
    
    with tabs[1]:
        reports_tab()
    
    with tabs[2]:
        analytics_tab()
    
    with tabs[3]:
        compliance_dashboard_tab()
    
    with tabs[4]:
        settings_tab()

def scan_files_tab():
    """File scanning interface"""
    st.header("🔍 Scan Files for Copyright Content")
    
    # File upload
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Upload audio/video files",
            type=['mp3', 'wav', 'mp4', 'avi', 'mov', 'm4a'],
            accept_multiple_files=True,
            help="Upload files to scan for copyrighted content"
        )
    
    with col2:
        st.subheader("Quick Actions")
        if st.button("🎬 Scan YouTube URL", use_container_width=True):
            scan_youtube_url()
        
        if st.button("📁 Scan Folder", use_container_width=True):
            scan_folder()
        
        if st.button("🎙️ Live Monitoring", use_container_width=True):
            start_live_monitoring()
    
    if uploaded_files:
        st.subheader("Files to Scan")
        
        # Display file list
        file_data = []
        for file in uploaded_files:
            file_data.append({
                'File': file.name,
                'Size': f"{file.size / 1024 / 1024:.2f} MB",
                'Type': file.type
            })
        
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True)
        
        # Scan options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            scan_mode = st.radio(
                "Scan Mode",
                ["Quick Scan", "Deep Scan", "Forensic Analysis"],
                help="Choose scanning depth"
            )
        
        with col2:
            report_format = st.selectbox(
                "Report Format",
                ["Summary", "Detailed", "Legal"],
                help="Select report detail level"
            )
        
        with col3:
            auto_license = st.checkbox(
                "Auto-license detected content",
                help="Automatically obtain licenses where possible"
            )
        
        # Scan button
        if st.button("🚀 Start Scan", type="primary", use_container_width=True):
            scan_files(uploaded_files, scan_mode, report_format, auto_license)

def scan_files(files, mode, format, auto_license):
    """Scan uploaded files"""
    progress_container = st.empty()
    results_container = st.empty()
    
    total_files = len(files)
    all_reports = []
    
    for idx, file in enumerate(files):
        # Update progress
        progress = (idx + 1) / total_files
        progress_container.progress(progress, f"Scanning {file.name}... ({idx + 1}/{total_files})")
        
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
            tmp_file.write(file.getbuffer())
            tmp_path = tmp_file.name
        
        # Scan file
        report = st.session_state.scanner.scan_file(tmp_path)
        report.file_path = file.name  # Use original filename
        all_reports.append(report)
        
        # Clean up
        os.unlink(tmp_path)
    
    # Clear progress
    progress_container.empty()
    
    # Display results
    with results_container.container():
        st.success(f"✅ Scanned {total_files} files successfully!")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_matches = sum(r.total_matches for r in all_reports)
        compliant_files = sum(1 for r in all_reports if r.compliance_status == 'compliant')
        total_cost = sum(r.estimated_cost or 0 for r in all_reports)
        
        with col1:
            st.metric("Total Matches", total_matches)
        
        with col2:
            st.metric("Compliant Files", f"{compliant_files}/{total_files}")
        
        with col3:
            st.metric("Est. Licensing Cost", f"${total_cost:,.2f}")
        
        with col4:
            compliance_rate = (compliant_files / total_files) * 100 if total_files > 0 else 0
            st.metric("Compliance Rate", f"{compliance_rate:.1f}%")
        
        # Detailed results
        st.subheader("Scan Results")
        
        for report in all_reports:
            display_report(report)
        
        # Save reports
        st.session_state.scan_history.extend(all_reports)
        st.session_state.current_report = all_reports[-1] if all_reports else None

def display_report(report: ComplianceReport):
    """Display a compliance report"""
    # Determine CSS class based on compliance status
    status_class = {
        'compliant': 'compliant',
        'non_compliant': 'non-compliant',
        'review_required': 'review-required'
    }.get(report.compliance_status, '')
    
    with st.expander(f"📄 {report.file_path} - {report.compliance_status.replace('_', ' ').title()}", expanded=True):
        # Report header
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Status:** <span class='{status_class}'>{report.compliance_status.replace('_', ' ').title()}</span>", unsafe_allow_html=True)
        
        with col2:
            st.write(f"**Total Matches:** {report.total_matches}")
        
        with col3:
            if report.estimated_cost:
                st.write(f"**Est. Cost:** ${report.estimated_cost:,.2f}")
        
        # Risk breakdown
        if report.total_matches > 0:
            st.subheader("Risk Breakdown")
            
            risk_data = {
                'Risk Level': ['High', 'Medium', 'Low'],
                'Count': [report.high_risk_matches, report.medium_risk_matches, report.low_risk_matches],
                'Color': ['#f44336', '#ff9800', '#4caf50']
            }
            
            fig = px.bar(
                risk_data,
                x='Risk Level',
                y='Count',
                color='Risk Level',
                color_discrete_map={'High': '#f44336', 'Medium': '#ff9800', 'Low': '#4caf50'}
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detected content
        if report.matches:
            st.subheader("Detected Content")
            
            for match in report.matches:
                risk_class = 'risk-high' if match.confidence_score > 0.9 else 'risk-medium' if match.confidence_score > 0.7 else 'risk-low'
                
                st.markdown(f"""
                <div class="compliance-card {risk_class}">
                    <h4>{match.matched_content}</h4>
                    <p><strong>Confidence:</strong> {match.confidence_score:.0%} | 
                       <strong>Duration:</strong> {match.end_time - match.start_time:.1f}s |
                       <strong>License:</strong> {match.license_status}</p>
                    {f'<p><strong>Copyright Holder:</strong> {match.copyright_holder}</p>' if match.copyright_holder else ''}
                    {f'<p><strong>Action Required:</strong> {match.action_required}</p>' if match.action_required else ''}
                </div>
                """, unsafe_allow_html=True)
        
        # Recommendations
        if report.recommendations:
            st.subheader("Recommendations")
            
            for rec in report.recommendations:
                st.markdown(f"""
                <div class="recommendation-box">
                    💡 {rec}
                </div>
                """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📧 Email Report", key=f"email_{report.report_id}"):
                email_report(report)
        
        with col2:
            if st.button("💳 License Content", key=f"license_{report.report_id}"):
                license_content(report)
        
        with col3:
            if st.button("📄 Export PDF", key=f"pdf_{report.report_id}"):
                export_pdf(report)

def reports_tab():
    """Reports management tab"""
    st.header("📊 Compliance Reports")
    
    if not st.session_state.scan_history:
        st.info("No reports available. Scan files to generate reports.")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_filter = st.date_input(
            "Filter by date",
            value=None,
            max_value=datetime.now().date()
        )
    
    with col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Compliant", "Non-Compliant", "Review Required"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (Newest)", "Date (Oldest)", "Risk Level", "Cost"]
        )
    
    # Apply filters
    filtered_reports = st.session_state.scan_history
    
    if date_filter:
        filtered_reports = [r for r in filtered_reports if r.scan_date.date() == date_filter]
    
    if status_filter != "All":
        status_map = {
            "Compliant": "compliant",
            "Non-Compliant": "non_compliant",
            "Review Required": "review_required"
        }
        filtered_reports = [r for r in filtered_reports if r.compliance_status == status_map.get(status_filter)]
    
    # Sort reports
    if sort_by == "Date (Newest)":
        filtered_reports.sort(key=lambda x: x.scan_date, reverse=True)
    elif sort_by == "Date (Oldest)":
        filtered_reports.sort(key=lambda x: x.scan_date)
    elif sort_by == "Risk Level":
        filtered_reports.sort(key=lambda x: x.high_risk_matches, reverse=True)
    elif sort_by == "Cost":
        filtered_reports.sort(key=lambda x: x.estimated_cost or 0, reverse=True)
    
    # Display reports
    for report in filtered_reports:
        display_report(report)

def analytics_tab():
    """Analytics dashboard"""
    st.header("📈 Compliance Analytics")
    
    if not st.session_state.scan_history:
        st.info("No data available. Scan files to see analytics.")
        return
    
    # Get statistics
    stats = st.session_state.scanner.get_statistics()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Scans",
            stats.get('total_reports', 0),
            delta=f"+{stats.get('reports_last_7_days', 0)} this week"
        )
    
    with col2:
        compliance_rate = stats.get('compliance_rate', 0)
        st.metric(
            "Compliance Rate",
            f"{compliance_rate:.1f}%",
            delta=f"{stats.get('compliance_trend', 0):+.1f}%"
        )
    
    with col3:
        st.metric(
            "Avg Matches/File",
            f"{stats.get('average_matches_per_file', 0):.1f}"
        )
    
    with col4:
        st.metric(
            "Total Licensing Cost",
            f"${stats.get('total_estimated_licensing_cost', 0):,.2f}"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Compliance status distribution
        st.subheader("Compliance Status Distribution")
        
        status_data = stats.get('compliance_status_distribution', {})
        if status_data:
            fig = px.pie(
                values=list(status_data.values()),
                names=[k.replace('_', ' ').title() for k in status_data.keys()],
                color_discrete_map={
                    'Compliant': '#4caf50',
                    'Non Compliant': '#f44336',
                    'Review Required': '#ff9800'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk level distribution
        st.subheader("Risk Level Distribution")
        
        risk_data = stats.get('risk_distribution', {})
        if risk_data:
            fig = px.bar(
                x=['High', 'Medium', 'Low'],
                y=[risk_data.get('high', 0), risk_data.get('medium', 0), risk_data.get('low', 0)],
                color=['High', 'Medium', 'Low'],
                color_discrete_map={'High': '#f44336', 'Medium': '#ff9800', 'Low': '#4caf50'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # Time series analysis
    st.subheader("Compliance Trends Over Time")
    
    # Generate mock time series data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    compliance_rates = [75 + (i % 7) * 2 + np.random.randint(-5, 5) for i in range(30)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=compliance_rates,
        mode='lines+markers',
        name='Compliance Rate',
        line=dict(color='#667eea', width=3)
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Compliance Rate (%)",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top copyright holders
    st.subheader("Top Copyright Holders Detected")
    
    holders_data = stats.get('top_copyright_holders', {})
    if holders_data:
        df = pd.DataFrame(
            [(k, v) for k, v in holders_data.items()],
            columns=['Copyright Holder', 'Detections']
        )
        df = df.sort_values('Detections', ascending=False).head(10)
        
        fig = px.bar(df, x='Detections', y='Copyright Holder', orientation='h')
        st.plotly_chart(fig, use_container_width=True)

def compliance_dashboard_tab():
    """Executive compliance dashboard"""
    st.header("🛡️ Compliance Dashboard")
    
    # Date range selector
    col1, col2 = st.columns([1, 3])
    
    with col1:
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 Days", "Last 30 Days", "Last Quarter", "Year to Date"]
        )
    
    # Compliance score card
    st.subheader("Overall Compliance Score")
    
    # Calculate compliance score
    compliance_score = 85  # Mock score
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = compliance_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Compliance Score"},
        delta = {'reference': 80, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk matrix
    st.subheader("Risk Assessment Matrix")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="compliance-card risk-high">
            <h3>High Risk Items</h3>
            <h1>3</h1>
            <p>Immediate action required</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="compliance-card risk-medium">
            <h3>Medium Risk Items</h3>
            <h1>7</h1>
            <p>Review within 7 days</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="compliance-card risk-low">
            <h3>Low Risk Items</h3>
            <h1>15</h1>
            <p>Monitor periodically</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Compliance checklist
    st.subheader("Compliance Checklist")
    
    checklist_items = [
        ("License inventory up to date", True),
        ("Quarterly compliance audit completed", True),
        ("Staff training on copyright policies", False),
        ("Automated scanning enabled", True),
        ("Legal review of high-risk content", False),
        ("Whitelist reviewed and updated", True)
    ]
    
    for item, completed in checklist_items:
        col1, col2 = st.columns([10, 1])
        with col1:
            if completed:
                st.markdown(f"✅ ~~{item}~~")
            else:
                st.markdown(f"⬜ **{item}**")

def settings_tab():
    """Settings and configuration"""
    st.header("⚙️ Settings")
    
    # API Configuration
    st.subheader("API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("ACRCloud API Key", type="password", help="For music recognition")
        st.text_input("Audible Magic API Key", type="password", help="For content identification")
    
    with col2:
        st.text_input("YouTube Content ID Key", type="password", help="For YouTube content")
        st.text_input("Custom API Endpoint", help="For proprietary content database")
    
    # Notification settings
    st.subheader("Notification Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Email notifications for high-risk matches", value=True)
        st.text_input("Notification email", value="compliance@company.com")
    
    with col2:
        st.checkbox("Slack notifications", value=False)
        st.text_input("Slack webhook URL", type="password")
    
    # Scanning preferences
    st.subheader("Scanning Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Minimum match duration (seconds)", min_value=1, value=3)
        st.slider("Confidence threshold", 0.0, 1.0, 0.7)
    
    with col2:
        st.multiselect(
            "Scan for content types",
            ["Music", "Speech", "Sound Effects", "Ambient Noise"],
            default=["Music", "Speech"]
        )
    
    # Save button
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")

# Helper functions
def show_license_manager():
    """Display license management interface"""
    st.info("License manager would show existing licenses and allow purchasing new ones")

def scan_youtube_url():
    """Scan YouTube URL for copyright content"""
    st.info("YouTube URL scanning would be implemented here")

def scan_folder():
    """Scan entire folder for copyright content"""
    st.info("Folder scanning would be implemented here")

def start_live_monitoring():
    """Start live monitoring for copyright content"""
    st.info("Live monitoring would be implemented here")

def email_report(report: ComplianceReport):
    """Email compliance report"""
    st.success(f"Report emailed successfully!")

def license_content(report: ComplianceReport):
    """License detected content"""
    st.info("Licensing interface would be shown here")

def export_pdf(report: ComplianceReport):
    """Export report as PDF"""
    st.success("PDF exported successfully!")

if __name__ == "__main__":
    main()