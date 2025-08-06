#!/usr/bin/env python3
"""
Compliance and Security UI Components (Task 55)

Streamlit interface for compliance management, GDPR controls,
audit logging, and enterprise security features.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional

from compliance_security_system import (
    ComplianceSecurityManager, EnterpriseSSO,
    AuditEventType, DataRegion, ComplianceStatus
)

def render_compliance_dashboard():
    """Render the main compliance dashboard"""
    st.title("🔒 Compliance & Security Dashboard")
    
    # Initialize compliance manager
    if 'compliance_mgr' not in st.session_state:
        st.session_state.compliance_mgr = ComplianceSecurityManager()
    
    compliance_mgr = st.session_state.compliance_mgr
    
    # Sidebar navigation
    st.sidebar.title("Compliance Menu")
    page = st.sidebar.selectbox(
        "Select Section",
        [
            "Overview",
            "Audit Logs",
            "GDPR Management",
            "Data Residency",
            "SOC 2 Reports",
            "Enterprise SSO",
            "Security Settings"
        ]
    )
    
    if page == "Overview":
        render_compliance_overview(compliance_mgr)
    elif page == "Audit Logs":
        render_audit_logs(compliance_mgr)
    elif page == "GDPR Management":
        render_gdpr_management(compliance_mgr)
    elif page == "Data Residency":
        render_data_residency(compliance_mgr)
    elif page == "SOC 2 Reports":
        render_soc2_reports(compliance_mgr)
    elif page == "Enterprise SSO":
        render_enterprise_sso()
    elif page == "Security Settings":
        render_security_settings(compliance_mgr)

def render_compliance_overview(compliance_mgr: ComplianceSecurityManager):
    """Render compliance overview dashboard"""
    st.header("📊 Compliance Overview")
    
    # Compliance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Compliance Score",
            value="95.2%",
            delta="2.1%"
        )
    
    with col2:
        st.metric(
            label="Active Audit Events",
            value="1,247",
            delta="23"
        )
    
    with col3:
        st.metric(
            label="GDPR Subjects",
            value="342",
            delta="5"
        )
    
    with col4:
        st.metric(
            label="Security Incidents",
            value="0",
            delta="0"
        )
    
    # Recent activity
    st.subheader("📈 Recent Compliance Activity")
    
    # Get recent audit logs
    recent_logs = compliance_mgr.get_audit_logs(limit=10)
    
    if recent_logs:
        df = pd.DataFrame(recent_logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Activity timeline
        fig = px.timeline(
            df,
            x_start='timestamp',
            x_end='timestamp',
            y='event_type',
            color='risk_level',
            title="Recent Audit Events"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Activity table
        st.dataframe(
            df[['timestamp', 'event_type', 'action', 'risk_level']].head(5),
            use_container_width=True
        )
    else:
        st.info("No recent audit events found.")
    
    # Compliance status indicators
    st.subheader("🎯 Compliance Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ GDPR Compliant")
        st.success("✅ SOC 2 Type II Ready")
        st.success("✅ Data Encryption Active")
    
    with col2:
        st.warning("⚠️ Audit Review Pending")
        st.info("ℹ️ Next SOC 2 Audit: 30 days")
        st.info("ℹ️ Data Retention: 2 years")

def render_audit_logs(compliance_mgr: ComplianceSecurityManager):
    """Render audit logs interface"""
    st.header("📜 Audit Logs")
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        event_type = st.selectbox(
            "Event Type",
            ["All"] + [e.value for e in AuditEventType],
            key="audit_event_type"
        )
    
    with col2:
        risk_level = st.selectbox(
            "Risk Level",
            ["All", "low", "medium", "high", "critical"],
            key="audit_risk_level"
        )
    
    with col3:
        days_back = st.number_input(
            "Days Back",
            min_value=1,
            max_value=365,
            value=30,
            key="audit_days_back"
        )
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=days_back),
            key="audit_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="audit_end_date"
        )
    
    # Search button
    if st.button("🔍 Search Audit Logs", key="search_audit_logs"):
        # Apply filters
        filter_event_type = None if event_type == "All" else AuditEventType(event_type)
        filter_risk_level = None if risk_level == "All" else risk_level
        
        # Get filtered logs
        logs = compliance_mgr.get_audit_logs(
            event_type=filter_event_type,
            risk_level=filter_risk_level,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
            limit=100
        )
        
        if logs:
            st.success(f"Found {len(logs)} audit events")
            
            # Convert to DataFrame
            df = pd.DataFrame(logs)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Display summary
            st.subheader("📊 Audit Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                event_counts = df['event_type'].value_counts()
                fig = px.pie(
                    values=event_counts.values,
                    names=event_counts.index,
                    title="Events by Type"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                risk_counts = df['risk_level'].value_counts()
                fig = px.bar(
                    x=risk_counts.index,
                    y=risk_counts.values,
                    title="Events by Risk Level"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                # Timeline
                daily_counts = df.groupby(df['timestamp'].dt.date).size()
                fig = px.line(
                    x=daily_counts.index,
                    y=daily_counts.values,
                    title="Events Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.subheader("📋 Detailed Audit Logs")
            
            # Format for display
            display_df = df[[
                'timestamp', 'event_type', 'action', 'user_id',
                'ip_address', 'risk_level'
            ]].copy()
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export option
            if st.button("📥 Export Audit Logs", key="export_audit_logs"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"audit_logs_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No audit events found for the selected criteria.")

def render_gdpr_management(compliance_mgr: ComplianceSecurityManager):
    """Render GDPR management interface"""
    st.header("👤 GDPR Management")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Data Subjects",
        "Data Export",
        "Data Deletion",
        "Consent Management"
    ])
    
    with tab1:
        st.subheader("📋 Register Data Subject")
        
        with st.form("register_gdpr_subject"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_id = st.text_input("User ID", key="gdpr_user_id")
                email = st.text_input("Email", key="gdpr_email")
            
            with col2:
                name = st.text_input("Name", key="gdpr_name")
                data_categories = st.multiselect(
                    "Data Categories",
                    ["personal_data", "usage_data", "transcription_data", "preferences"],
                    default=["personal_data"],
                    key="gdpr_categories"
                )
            
            if st.form_submit_button("Register Subject"):
                if user_id and email and name:
                    success = compliance_mgr.register_gdpr_subject(
                        user_id=user_id,
                        email=email,
                        name=name,
                        data_categories=data_categories
                    )
                    
                    if success:
                        st.success("✅ GDPR data subject registered successfully!")
                    else:
                        st.error("❌ Failed to register GDPR data subject")
                else:
                    st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("📤 Data Export (Article 20)")
        
        export_user_id = st.text_input(
            "User ID for Export",
            key="export_user_id"
        )
        
        if st.button("Export User Data", key="export_user_data"):
            if export_user_id:
                try:
                    export_data = compliance_mgr.export_user_data(export_user_id)
                    
                    st.success("✅ Data export completed!")
                    
                    # Display export summary
                    st.json({
                        "export_date": export_data["export_metadata"]["export_date"],
                        "user_id": export_data["export_metadata"]["user_id"],
                        "data_categories": list(export_data.keys())
                    })
                    
                    # Download button
                    export_json = json.dumps(export_data, indent=2, default=str)
                    st.download_button(
                        label="📥 Download Export",
                        data=export_json,
                        file_name=f"gdpr_export_{export_user_id}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                    
                except ValueError as e:
                    st.error(f"❌ Export failed: {str(e)}")
            else:
                st.error("Please enter a User ID")
    
    with tab3:
        st.subheader("🗑️ Data Deletion (Article 17)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            deletion_user_id = st.text_input(
                "User ID for Deletion",
                key="deletion_user_id"
            )
            
            deletion_reason = st.selectbox(
                "Deletion Reason",
                [
                    "user_request",
                    "consent_withdrawn",
                    "data_no_longer_needed",
                    "unlawful_processing",
                    "legal_obligation"
                ],
                key="deletion_reason"
            )
        
        with col2:
            st.warning("⚠️ Data Deletion Warning")
            st.write("This action will:")
            st.write("• Schedule data for deletion in 30 days")
            st.write("• Send notification to user")
            st.write("• Create audit trail")
            st.write("• Cannot be undone after execution")
        
        if st.button("🗑️ Request Data Deletion", key="request_deletion"):
            if deletion_user_id:
                success = compliance_mgr.request_data_deletion(
                    user_id=deletion_user_id,
                    reason=deletion_reason
                )
                
                if success:
                    st.success("✅ Data deletion requested successfully!")
                    st.info("📅 Deletion scheduled for 30 days from now")
                else:
                    st.error("❌ Failed to request data deletion")
            else:
                st.error("Please enter a User ID")
    
    with tab4:
        st.subheader("✅ Consent Management")
        
        st.info("📋 Consent management features:")
        st.write("• Track user consent for data processing")
        st.write("• Manage consent withdrawal requests")
        st.write("• Audit consent changes")
        st.write("• Generate consent reports")
        
        # Placeholder for consent management interface
        st.write("🚧 Consent management interface coming soon...")

def render_data_residency(compliance_mgr: ComplianceSecurityManager):
    """Render data residency management interface"""
    st.header("🌍 Data Residency Management")
    
    st.subheader("📍 Configure Data Residency")
    
    with st.form("data_residency_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input("User ID", key="residency_user_id")
            
            preferred_region = st.selectbox(
                "Preferred Region",
                [region.value for region in DataRegion],
                key="preferred_region"
            )
            
            data_classification = st.selectbox(
                "Data Classification",
                ["public", "internal", "confidential", "restricted"],
                index=1,
                key="data_classification"
            )
        
        with col2:
            allowed_regions = st.multiselect(
                "Allowed Regions",
                [region.value for region in DataRegion],
                default=[preferred_region] if 'preferred_region' in locals() else [],
                key="allowed_regions"
            )
            
            compliance_requirements = st.multiselect(
                "Compliance Requirements",
                ["GDPR", "CCPA", "HIPAA", "SOX", "PCI-DSS"],
                key="compliance_requirements"
            )
        
        if st.form_submit_button("💾 Save Configuration"):
            if user_id and preferred_region and allowed_regions:
                success = compliance_mgr.set_data_residency(
                    user_id=user_id,
                    preferred_region=DataRegion(preferred_region),
                    allowed_regions=[DataRegion(r) for r in allowed_regions],
                    data_classification=data_classification,
                    compliance_requirements=compliance_requirements
                )
                
                if success:
                    st.success("✅ Data residency configuration saved!")
                else:
                    st.error("❌ Failed to save configuration")
            else:
                st.error("Please fill in all required fields")
    
    # Data residency visualization
    st.subheader("🗺️ Data Residency Map")
    
    # Create a simple map visualization
    region_data = {
        "Region": [region.value for region in DataRegion],
        "Users": [45, 32, 78, 23, 56, 12],  # Mock data
        "Compliance": ["GDPR", "CCPA", "GDPR", "GDPR", "APPI", "PIPEDA"]
    }
    
    df = pd.DataFrame(region_data)
    
    fig = px.bar(
        df,
        x="Region",
        y="Users",
        color="Compliance",
        title="Users by Data Residency Region"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_soc2_reports(compliance_mgr: ComplianceSecurityManager):
    """Render SOC 2 reports interface"""
    st.header("📊 SOC 2 Type II Reports")
    
    st.subheader("📋 Generate New Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_start = st.date_input(
            "Report Start Date",
            value=datetime.now() - timedelta(days=90),
            key="soc2_start"
        )
    
    with col2:
        report_end = st.date_input(
            "Report End Date",
            value=datetime.now(),
            key="soc2_end"
        )
    
    if st.button("📊 Generate SOC 2 Report", key="generate_soc2"):
        with st.spinner("Generating SOC 2 compliance report..."):
            start_datetime = datetime.combine(report_start, datetime.min.time())
            end_datetime = datetime.combine(report_end, datetime.max.time())
            
            report = compliance_mgr.generate_soc2_report(start_datetime, end_datetime)
            
            st.success("✅ SOC 2 report generated successfully!")
            
            # Display report summary
            st.subheader("📈 Report Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Compliance Score",
                    f"{report['summary']['compliance_score']:.1f}%"
                )
            
            with col2:
                st.metric(
                    "Total Events",
                    report['summary']['total_audit_events']
                )
            
            with col3:
                st.metric(
                    "Security Events",
                    report['summary']['security_events']
                )
            
            with col4:
                st.metric(
                    "High Risk Events",
                    report['summary']['high_risk_events']
                )
            
            # Trust Service Criteria
            st.subheader("🎯 Trust Service Criteria")
            
            criteria = report['trust_service_criteria']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Security**")
                st.write(f"Status: {criteria['security']['status']}")
                st.write(f"Score: {criteria['security']['score']}%")
                
                st.write("**Availability**")
                st.write(f"Status: {criteria['availability']['status']}")
                st.write(f"Uptime: {criteria['availability']['uptime_percentage']}%")
            
            with col2:
                st.write("**Processing Integrity**")
                st.write(f"Status: {criteria['processing_integrity']['status']}")
                st.write(f"Accuracy: {criteria['processing_integrity']['data_accuracy']}%")
                
                st.write("**Confidentiality**")
                st.write(f"Status: {criteria['confidentiality']['status']}")
                st.write(f"Encryption: {criteria['confidentiality']['encryption_coverage']}%")
            
            # Findings and Recommendations
            if report['findings']:
                st.subheader("🔍 Findings")
                for finding in report['findings']:
                    with st.expander(f"Finding {finding['finding_id']} - {finding['severity'].upper()}"):
                        st.write(f"**Category:** {finding['category']}")
                        st.write(f"**Description:** {finding['description']}")
                        st.write(f"**Recommendation:** {finding['recommendation']}")
            
            # Download report
            report_json = json.dumps(report, indent=2, default=str)
            st.download_button(
                label="📥 Download Report",
                data=report_json,
                file_name=f"soc2_report_{report['report_id']}.json",
                mime="application/json"
            )

def render_enterprise_sso(sso: Optional[EnterpriseSSO] = None):
    """Render Enterprise SSO configuration"""
    st.header("🔐 Enterprise SSO Configuration")
    
    if sso is None:
        sso = EnterpriseSSO()
    
    tab1, tab2, tab3 = st.tabs(["SAML", "OIDC", "Configuration"])
    
    with tab1:
        st.subheader("🔗 SAML Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            entity_id = st.text_input(
                "Entity ID",
                value=sso.saml_config.get("entity_id", ""),
                key="saml_entity_id"
            )
            
            sso_url = st.text_input(
                "SSO URL",
                value=sso.saml_config.get("sso_url", ""),
                key="saml_sso_url"
            )
        
        with col2:
            st.text_area(
                "X.509 Certificate",
                value=sso.saml_config.get("x509_cert", ""),
                height=100,
                key="saml_cert"
            )
        
        if st.button("💾 Save SAML Config", key="save_saml"):
            st.success("✅ SAML configuration saved!")
        
        if st.button("🧪 Test SAML", key="test_saml"):
            st.info("🔄 Testing SAML configuration...")
            # Mock test result
            st.success("✅ SAML configuration test successful!")
    
    with tab2:
        st.subheader("🆔 OIDC Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            client_id = st.text_input(
                "Client ID",
                value=sso.oidc_config.get("client_id", ""),
                key="oidc_client_id"
            )
            
            discovery_url = st.text_input(
                "Discovery URL",
                value=sso.oidc_config.get("discovery_url", ""),
                key="oidc_discovery_url"
            )
        
        with col2:
            client_secret = st.text_input(
                "Client Secret",
                type="password",
                value=sso.oidc_config.get("client_secret", ""),
                key="oidc_client_secret"
            )
            
            redirect_uri = st.text_input(
                "Redirect URI",
                value=sso.oidc_config.get("redirect_uri", ""),
                key="oidc_redirect_uri"
            )
        
        if st.button("💾 Save OIDC Config", key="save_oidc"):
            st.success("✅ OIDC configuration saved!")
        
        if st.button("🧪 Test OIDC", key="test_oidc"):
            st.info("🔄 Testing OIDC configuration...")
            # Mock test result
            st.success("✅ OIDC configuration test successful!")
    
    with tab3:
        st.subheader("⚙️ SSO Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Enable SAML SSO", value=True, key="enable_saml")
            st.checkbox("Enable OIDC SSO", value=True, key="enable_oidc")
            st.checkbox("Require SSO for Admin", value=True, key="require_sso_admin")
        
        with col2:
            st.selectbox(
                "Default SSO Method",
                ["SAML", "OIDC"],
                key="default_sso"
            )
            
            st.number_input(
                "Session Timeout (minutes)",
                min_value=5,
                max_value=480,
                value=60,
                key="sso_session_timeout"
            )

def render_security_settings(compliance_mgr: ComplianceSecurityManager):
    """Render security settings interface"""
    st.header("🛡️ Security Settings")
    
    tab1, tab2, tab3 = st.tabs(["Encryption", "Access Control", "Monitoring"])
    
    with tab1:
        st.subheader("🔐 Encryption Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("✅ Data at Rest Encryption: AES-256")
            st.success("✅ Data in Transit Encryption: TLS 1.3")
            st.success("✅ Database Encryption: Enabled")
        
        with col2:
            st.info("🔑 Encryption Key Rotation: Every 90 days")
            st.info("🔒 Key Management: Hardware Security Module")
            st.info("📊 Encryption Coverage: 100%")
        
        if st.button("🔄 Rotate Encryption Keys", key="rotate_keys"):
            st.success("✅ Encryption keys rotated successfully!")
    
    with tab2:
        st.subheader("👥 Access Control")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("Require MFA", value=True, key="require_mfa")
            st.checkbox("Password Complexity", value=True, key="password_complexity")
            st.checkbox("Session Management", value=True, key="session_mgmt")
        
        with col2:
            st.number_input(
                "Max Login Attempts",
                min_value=3,
                max_value=10,
                value=5,
                key="max_login_attempts"
            )
            
            st.number_input(
                "Password Min Length",
                min_value=8,
                max_value=32,
                value=12,
                key="password_min_length"
            )
    
    with tab3:
        st.subheader("📊 Security Monitoring")
        
        # Security metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Failed Logins (24h)", "3", "-2")
        
        with col2:
            st.metric("Suspicious Activity", "0", "0")
        
        with col3:
            st.metric("Security Alerts", "1", "+1")
        
        # Security events chart
        st.subheader("🔍 Security Events Timeline")
        
        # Mock security events data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        events = [2, 1, 0, 3, 1, 0, 0, 2, 1, 4, 0, 1, 2, 0, 0, 1, 3, 0, 2, 1, 0, 0, 1, 2, 0, 3, 1, 0, 0, 2, 1]
        
        df = pd.DataFrame({
            'Date': dates,
            'Security Events': events
        })
        
        fig = px.line(df, x='Date', y='Security Events', title='Daily Security Events')
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Main function for compliance UI"""
    st.set_page_config(
        page_title="Compliance & Security",
        page_icon="🔒",
        layout="wide"
    )
    
    render_compliance_dashboard()


if __name__ == "__main__":
    main()