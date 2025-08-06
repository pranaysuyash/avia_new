"""
Enterprise Sales and Onboarding UI
Streamlit interface for enterprise sales features including pricing calculator,
demo scheduling, trial management, white-label customization, and customer success tracking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from enterprise_sales_system import (
    EnterpriseSalesSystem, PricingTier, TrialStatus, OnboardingStage, 
    HealthScore, DemoRequest, TrialAccount, WhiteLabelConfig
)

def render_enterprise_sales_dashboard():
    """Main enterprise sales dashboard"""
    st.title("🏢 Enterprise Sales & Onboarding")
    
    # Initialize system
    if 'enterprise_system' not in st.session_state:
        st.session_state.enterprise_system = EnterpriseSalesSystem()
    
    system = st.session_state.enterprise_system
    
    # Sidebar navigation
    st.sidebar.title("Enterprise Tools")
    page = st.sidebar.selectbox(
        "Select Tool",
        [
            "Sales Dashboard",
            "Pricing Calculator", 
            "Demo Scheduling",
            "Trial Management",
            "White-Label Config",
            "Onboarding Workflows",
            "Customer Success"
        ]
    )
    
    if page == "Sales Dashboard":
        render_sales_dashboard(system)
    elif page == "Pricing Calculator":
        render_pricing_calculator(system)
    elif page == "Demo Scheduling":
        render_demo_scheduling(system)
    elif page == "Trial Management":
        render_trial_management(system)
    elif page == "White-Label Config":
        render_whitelabel_config(system)
    elif page == "Onboarding Workflows":
        render_onboarding_workflows(system)
    elif page == "Customer Success":
        render_customer_success(system)

def render_sales_dashboard(system):
    """Render sales analytics dashboard"""
    st.header("📊 Sales Analytics Dashboard")
    
    # Get analytics data
    analytics = system.get_sales_analytics()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Demos Scheduled",
            analytics['total_demos_scheduled'],
            delta="+5 this week"
        )
    
    with col2:
        st.metric(
            "Active Trials",
            analytics['active_trials'],
            delta="+2 this week"
        )
    
    with col3:
        st.metric(
            "Conversion Rate",
            f"{analytics['trial_conversion_rate']:.1f}%",
            delta="+2.3%"
        )
    
    with col4:
        st.metric(
            "Enterprise Clients",
            analytics['total_enterprise_clients'],
            delta="+1 this month"
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Demo Requests by Type")
        demo_types = ["Live Demo", "Self-Guided", "Recorded Demo"]
        demo_counts = [12, 8, 5]
        
        fig = px.pie(
            values=demo_counts,
            names=demo_types,
            title="Demo Type Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Trial Conversion Funnel")
        stages = ["Demo", "Trial Started", "Trial Active", "Converted"]
        counts = [25, 18, 12, 8]
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=counts,
            textinfo="value+percent initial"
        ))
        fig.update_layout(title="Sales Funnel")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Sales Activity")
    
    activity_data = [
        {"Date": "2024-02-07", "Activity": "Demo scheduled", "Company": "TechCorp Inc", "Rep": "Sarah Johnson"},
        {"Date": "2024-02-06", "Activity": "Trial started", "Company": "DataFlow Ltd", "Rep": "Mike Chen"},
        {"Date": "2024-02-05", "Activity": "Enterprise deal closed", "Company": "GlobalMedia", "Rep": "Sarah Johnson"},
        {"Date": "2024-02-04", "Activity": "Custom pricing sent", "Company": "MegaCorp", "Rep": "David Wilson"},
    ]
    
    df = pd.DataFrame(activity_data)
    st.dataframe(df, use_container_width=True)

def render_pricing_calculator(system):
    """Render custom pricing calculator"""
    st.header("💰 Enterprise Pricing Calculator")
    
    st.write("Create custom pricing configurations for enterprise clients based on their specific requirements.")
    
    # Client information
    st.subheader("Client Information")
    col1, col2 = st.columns(2)
    
    with col1:
        client_name = st.text_input("Client Name", placeholder="Enter company name")
        user_count = st.number_input("Number of Users", min_value=1, max_value=10000, value=100)
        contract_length = st.selectbox("Contract Length (months)", [12, 24, 36], index=1)
    
    with col2:
        tier = st.selectbox("Base Tier", ["starter", "professional", "enterprise"])
        support_level = st.selectbox("Support Level", ["standard", "premium", "white-glove"])
        transcription_hours = st.number_input("Expected Monthly Transcription Hours", min_value=0, value=100)
    
    # Custom features
    st.subheader("Custom Features")
    custom_features = st.multiselect(
        "Select Additional Features",
        [
            "Advanced Analytics Dashboard",
            "Custom Integrations",
            "Dedicated Success Manager",
            "Priority Support",
            "Custom Branding",
            "On-Premises Deployment",
            "Advanced Security Features",
            "Custom AI Model Training"
        ]
    )
    
    # Calculate pricing
    if st.button("Calculate Custom Pricing", type="primary"):
        if client_name:
            requirements = {
                'tier': tier,
                'user_count': user_count,
                'contract_length': contract_length,
                'support_level': support_level,
                'custom_features': custom_features,
                'transcription_hours': transcription_hours
            }
            
            config = system.create_custom_pricing(client_name, requirements)
            
            # Display pricing breakdown
            st.success(f"Custom pricing created for {client_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Monthly Pricing")
                st.write(f"**Base Price:** ${config.base_price:,.2f}")
                st.write(f"**Per User:** ${config.per_user_price:,.2f}")
                st.write(f"**Per Hour Transcription:** ${config.per_hour_transcription:,.2f}")
                st.write(f"**Per GB Storage:** ${config.per_gb_storage:,.2f}")
                
                # Calculate total monthly estimate
                monthly_total = (
                    config.base_price +
                    (config.per_user_price * user_count) +
                    (config.per_hour_transcription * transcription_hours)
                )
                st.write(f"**Estimated Monthly Total:** ${monthly_total:,.2f}")
            
            with col2:
                st.subheader("Included Benefits")
                st.write(f"**API Calls Included:** {config.api_calls_included:,}")
                st.write(f"**Additional API Cost:** ${config.additional_api_cost:.3f}")
                st.write(f"**Support Level:** {config.support_level.title()}")
                
                if custom_features:
                    st.write("**Custom Features:**")
                    for feature in custom_features:
                        st.write(f"• {feature}")
            
            # Volume discounts
            st.subheader("Available Discounts")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Volume Discounts:**")
                for threshold, discount in config.volume_discounts.items():
                    st.write(f"• {threshold} users: {discount*100:.0f}% off")
            
            with col2:
                st.write("**Contract Length Discounts:**")
                for length, discount in config.contract_length_discount.items():
                    st.write(f"• {length}: {discount*100:.0f}% off")
            
            # Export pricing
            if st.button("Export Pricing Proposal"):
                pricing_data = {
                    'client_name': client_name,
                    'pricing_config': {
                        'base_price': config.base_price,
                        'per_user_price': config.per_user_price,
                        'per_hour_transcription': config.per_hour_transcription,
                        'estimated_monthly': monthly_total,
                        'custom_features': custom_features
                    }
                }
                
                st.download_button(
                    label="Download Pricing Proposal (JSON)",
                    data=json.dumps(pricing_data, indent=2),
                    file_name=f"{client_name}_pricing_proposal.json",
                    mime="application/json"
                )
        else:
            st.error("Please enter a client name")

def render_demo_scheduling(system):
    """Render demo scheduling interface"""
    st.header("📅 Demo Scheduling")
    
    tab1, tab2 = st.tabs(["Schedule New Demo", "Manage Demos"])
    
    with tab1:
        st.subheader("Schedule New Demo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name")
            contact_name = st.text_input("Contact Name")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")
        
        with col2:
            company_size = st.selectbox(
                "Company Size",
                ["1-10", "11-50", "51-200", "201-1000", "1000+"]
            )
            demo_type = st.selectbox(
                "Demo Type",
                ["live", "recorded", "self-guided"]
            )
            preferred_date = st.date_input("Preferred Date")
            preferred_time = st.selectbox(
                "Preferred Time",
                ["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"]
            )
        
        use_case = st.text_area("Use Case Description", placeholder="Describe how you plan to use the platform...")
        notes = st.text_area("Additional Notes", placeholder="Any specific requirements or questions...")
        
        if st.button("Schedule Demo", type="primary"):
            if all([company_name, contact_name, email]):
                demo_request = DemoRequest(
                    id="",  # Will be set by system
                    company_name=company_name,
                    contact_name=contact_name,
                    email=email,
                    phone=phone,
                    company_size=company_size,
                    use_case=use_case,
                    preferred_date=datetime.combine(preferred_date, datetime.min.time()),
                    preferred_time=preferred_time,
                    demo_type=demo_type,
                    status="scheduled",
                    notes=notes,
                    created_at=datetime.now()
                )
                
                demo_id = system.schedule_demo(demo_request)
                st.success(f"Demo scheduled successfully! Demo ID: {demo_id}")
                st.info("Confirmation email will be sent to the provided address.")
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("Scheduled Demos")
        
        if system.demo_requests:
            demo_data = []
            for demo_id, demo in system.demo_requests.items():
                demo_data.append({
                    "ID": demo_id[:8],
                    "Company": demo.company_name,
                    "Contact": demo.contact_name,
                    "Email": demo.email,
                    "Date": demo.preferred_date.strftime("%Y-%m-%d"),
                    "Time": demo.preferred_time,
                    "Type": demo.demo_type.title(),
                    "Status": demo.status.title()
                })
            
            df = pd.DataFrame(demo_data)
            st.dataframe(df, use_container_width=True)
            
            # Demo management
            selected_demo = st.selectbox(
                "Select Demo to Manage",
                options=list(system.demo_requests.keys()),
                format_func=lambda x: f"{system.demo_requests[x].company_name} - {x[:8]}"
            )
            
            if selected_demo:
                demo = system.demo_requests[selected_demo]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Mark as Completed"):
                        demo.status = "completed"
                        system.save_data()
                        st.success("Demo marked as completed")
                        st.rerun()
                
                with col2:
                    if st.button("Reschedule"):
                        demo.status = "rescheduled"
                        system.save_data()
                        st.info("Demo marked for rescheduling")
                        st.rerun()
                
                with col3:
                    if st.button("Cancel"):
                        demo.status = "cancelled"
                        system.save_data()
                        st.warning("Demo cancelled")
                        st.rerun()
        else:
            st.info("No demos scheduled yet.")

def render_trial_management(system):
    """Render trial account management"""
    st.header("🔬 Trial Management")
    
    tab1, tab2 = st.tabs(["Create Trial", "Manage Trials"])
    
    with tab1:
        st.subheader("Create New Trial Account")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name")
            contact_email = st.text_input("Contact Email")
        
        with col2:
            trial_type = st.selectbox(
                "Trial Type",
                ["standard", "extended", "poc"],
                help="Standard: 14 days, Extended: 30 days, POC: 60 days"
            )
        
        if st.button("Create Trial Account", type="primary"):
            if company_name and contact_email:
                trial = system.create_trial_account(company_name, contact_email, trial_type)
                st.success(f"Trial account created! Trial ID: {trial.id}")
                st.info(f"Trial expires on: {trial.end_date.strftime('%Y-%m-%d')}")
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("Active Trials")
        
        if system.trial_accounts:
            # Trial overview
            trial_data = []
            for trial_id, trial in system.trial_accounts.items():
                days_remaining = (trial.end_date - datetime.now()).days
                trial_data.append({
                    "ID": trial_id[:8],
                    "Company": trial.company_name,
                    "Email": trial.contact_email,
                    "Type": trial.trial_type.title(),
                    "Status": trial.status.value.title(),
                    "Days Remaining": max(0, days_remaining),
                    "Conversion Probability": f"{trial.conversion_probability*100:.0f}%"
                })
            
            df = pd.DataFrame(trial_data)
            st.dataframe(df, use_container_width=True)
            
            # Trial details
            selected_trial = st.selectbox(
                "Select Trial for Details",
                options=list(system.trial_accounts.keys()),
                format_func=lambda x: f"{system.trial_accounts[x].company_name} - {x[:8]}"
            )
            
            if selected_trial:
                trial = system.trial_accounts[selected_trial]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Trial Progress")
                    for goal in trial.trial_goals:
                        st.write(f"• {goal}")
                    
                    st.subheader("Usage Statistics")
                    st.write(f"**Transcription Hours:** {trial.usage_stats['transcription_hours']}")
                    st.write(f"**API Calls:** {trial.usage_stats['api_calls']:,}")
                    st.write(f"**Storage Used:** {trial.usage_stats['storage_gb']:.1f} GB")
                    st.write(f"**Active Users:** {trial.usage_stats['active_users']}")
                
                with col2:
                    st.subheader("Progress Metrics")
                    for metric, value in trial.progress_metrics.items():
                        st.progress(value, text=f"{metric.replace('_', ' ').title()}: {value*100:.0f}%")
                
                # Trial actions
                st.subheader("Trial Actions")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("Extend Trial"):
                        trial.end_date += timedelta(days=14)
                        system.save_data()
                        st.success("Trial extended by 14 days")
                        st.rerun()
                
                with col2:
                    if st.button("Convert to Paid"):
                        trial.status = TrialStatus.CONVERTED
                        system.save_data()
                        st.success("Trial converted to paid account")
                        st.rerun()
                
                with col3:
                    if st.button("Mark as Expired"):
                        trial.status = TrialStatus.EXPIRED
                        system.save_data()
                        st.warning("Trial marked as expired")
                        st.rerun()
                
                with col4:
                    if st.button("Cancel Trial"):
                        trial.status = TrialStatus.CANCELLED
                        system.save_data()
                        st.error("Trial cancelled")
                        st.rerun()
        else:
            st.info("No trial accounts created yet.")

def render_whitelabel_config(system):
    """Render white-label configuration interface"""
    st.header("🎨 White-Label Customization")
    
    st.write("Configure white-label deployments for enterprise clients with custom branding and features.")
    
    # Client selection or creation
    client_id = st.text_input("Client ID", placeholder="Enter unique client identifier")
    
    if client_id:
        # Load existing config if available
        existing_config = system.whitelabel_configs.get(client_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Branding Configuration")
            brand_name = st.text_input(
                "Brand Name", 
                value=existing_config.brand_name if existing_config else "",
                placeholder="Custom Platform Name"
            )
            logo_url = st.text_input(
                "Logo URL",
                value=existing_config.logo_url if existing_config else "",
                placeholder="https://example.com/logo.png"
            )
            primary_color = st.color_picker(
                "Primary Color",
                value=existing_config.primary_color if existing_config else "#1f77b4"
            )
            secondary_color = st.color_picker(
                "Secondary Color",
                value=existing_config.secondary_color if existing_config else "#ff7f0e"
            )
        
        with col2:
            st.subheader("Domain & Support")
            custom_domain = st.text_input(
                "Custom Domain",
                value=existing_config.custom_domain if existing_config else "",
                placeholder="platform.yourclient.com"
            )
            support_contact = st.text_input(
                "Support Contact",
                value=existing_config.support_contact if existing_config else "",
                placeholder="support@yourclient.com"
            )
            terms_url = st.text_input(
                "Terms of Service URL",
                value=existing_config.terms_url if existing_config else "",
                placeholder="https://yourclient.com/terms"
            )
            privacy_url = st.text_input(
                "Privacy Policy URL",
                value=existing_config.privacy_url if existing_config else "",
                placeholder="https://yourclient.com/privacy"
            )
        
        # Feature toggles
        st.subheader("Feature Configuration")
        
        default_features = existing_config.feature_toggles if existing_config else {}
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            transcription_enabled = st.checkbox(
                "Transcription Service",
                value=default_features.get('transcription', True)
            )
            entity_extraction = st.checkbox(
                "Entity Extraction",
                value=default_features.get('entity_extraction', True)
            )
            real_time_collab = st.checkbox(
                "Real-time Collaboration",
                value=default_features.get('real_time_collaboration', False)
            )
        
        with col2:
            api_access = st.checkbox(
                "API Access",
                value=default_features.get('api_access', True)
            )
            advanced_analytics = st.checkbox(
                "Advanced Analytics",
                value=default_features.get('advanced_analytics', False)
            )
            mobile_app = st.checkbox(
                "Mobile App Access",
                value=default_features.get('mobile_app', True)
            )
        
        with col3:
            white_glove_support = st.checkbox(
                "White-glove Support",
                value=default_features.get('white_glove_support', False)
            )
            custom_integrations = st.checkbox(
                "Custom Integrations",
                value=default_features.get('custom_integrations', False)
            )
            sso_integration = st.checkbox(
                "SSO Integration",
                value=default_features.get('sso_integration', False)
            )
        
        # Custom CSS
        st.subheader("Custom Styling")
        custom_css = st.text_area(
            "Custom CSS",
            value=existing_config.custom_css if existing_config else "",
            placeholder="/* Custom CSS styles */\n.header { background-color: #your-color; }",
            height=150
        )
        
        # Custom integrations
        st.subheader("Custom Integrations")
        integration_options = [
            "Salesforce CRM",
            "Microsoft Teams",
            "Slack",
            "Zoom",
            "Google Workspace",
            "Custom API Endpoints"
        ]
        
        selected_integrations = st.multiselect(
            "Select Integrations",
            integration_options,
            default=existing_config.custom_integrations if existing_config else []
        )
        
        # Save configuration
        if st.button("Save White-Label Configuration", type="primary"):
            config_data = {
                'brand_name': brand_name,
                'logo_url': logo_url,
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'custom_domain': custom_domain,
                'custom_css': custom_css,
                'feature_toggles': {
                    'transcription': transcription_enabled,
                    'entity_extraction': entity_extraction,
                    'real_time_collaboration': real_time_collab,
                    'api_access': api_access,
                    'advanced_analytics': advanced_analytics,
                    'mobile_app': mobile_app,
                    'white_glove_support': white_glove_support,
                    'custom_integrations': custom_integrations,
                    'sso_integration': sso_integration
                },
                'custom_integrations': selected_integrations,
                'support_contact': support_contact,
                'terms_url': terms_url,
                'privacy_url': privacy_url
            }
            
            config = system.create_whitelabel_config(client_id, config_data)
            st.success(f"White-label configuration saved for {client_id}")
            
            # Preview
            st.subheader("Configuration Preview")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Brand Name:** {brand_name}")
                st.write(f"**Primary Color:** {primary_color}")
                st.write(f"**Custom Domain:** {custom_domain}")
                st.write(f"**Support Contact:** {support_contact}")
            
            with col2:
                enabled_features = [k for k, v in config_data['feature_toggles'].items() if v]
                st.write("**Enabled Features:**")
                for feature in enabled_features:
                    st.write(f"• {feature.replace('_', ' ').title()}")

def render_onboarding_workflows(system):
    """Render onboarding workflow management"""
    st.header("🚀 Onboarding Workflows")
    
    if system.onboarding_workflows:
        # Workflow overview
        st.subheader("Active Onboarding Workflows")
        
        workflow_data = []
        for client_id, workflow in system.onboarding_workflows.items():
            overall_progress = sum(workflow.stage_progress.values()) / len(workflow.stage_progress) * 100
            days_since_start = (datetime.now() - workflow.start_date).days
            
            workflow_data.append({
                "Client ID": client_id[:8],
                "Current Stage": workflow.current_stage.value.title(),
                "Overall Progress": f"{overall_progress:.0f}%",
                "Days Since Start": days_since_start,
                "Assigned Specialist": workflow.assigned_specialist or "Unassigned",
                "Target Completion": workflow.target_completion.strftime("%Y-%m-%d")
            })
        
        df = pd.DataFrame(workflow_data)
        st.dataframe(df, use_container_width=True)
        
        # Detailed workflow management
        selected_workflow = st.selectbox(
            "Select Workflow for Details",
            options=list(system.onboarding_workflows.keys()),
            format_func=lambda x: f"Client {x[:8]}"
        )
        
        if selected_workflow:
            workflow = system.onboarding_workflows[selected_workflow]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Onboarding Progress")
                
                stages = ['welcome', 'setup', 'integration', 'training', 'launch']
                for stage in stages:
                    progress = workflow.stage_progress.get(stage, 0)
                    is_completed = stage in workflow.stages_completed
                    
                    status_icon = "✅" if is_completed else "🔄" if progress > 0 else "⏳"
                    st.write(f"{status_icon} **{stage.title()}**")
                    st.progress(progress, text=f"{progress*100:.0f}% complete")
                    
                    # Allow progress updates
                    if not is_completed:
                        new_progress = st.slider(
                            f"Update {stage} progress",
                            0.0, 1.0, progress,
                            key=f"progress_{stage}_{selected_workflow}"
                        )
                        
                        if new_progress != progress:
                            system.update_onboarding_progress(selected_workflow, stage, new_progress)
                            st.rerun()
            
            with col2:
                st.subheader("Workflow Details")
                st.write(f"**Current Stage:** {workflow.current_stage.value.title()}")
                st.write(f"**Start Date:** {workflow.start_date.strftime('%Y-%m-%d')}")
                st.write(f"**Target Completion:** {workflow.target_completion.strftime('%Y-%m-%d')}")
                st.write(f"**Assigned Specialist:** {workflow.assigned_specialist or 'Unassigned'}")
                
                # Assign specialist
                specialist = st.text_input(
                    "Assign Specialist",
                    value=workflow.assigned_specialist,
                    key=f"specialist_{selected_workflow}"
                )
                
                if st.button("Update Specialist"):
                    workflow.assigned_specialist = specialist
                    system.save_data()
                    st.success("Specialist assigned")
                    st.rerun()
                
                # Custom requirements
                st.subheader("Custom Requirements")
                if workflow.custom_requirements:
                    for req in workflow.custom_requirements:
                        st.write(f"• {req}")
                else:
                    st.write("No custom requirements specified")
                
                new_requirement = st.text_input("Add Custom Requirement")
                if st.button("Add Requirement") and new_requirement:
                    workflow.custom_requirements.append(new_requirement)
                    system.save_data()
                    st.success("Requirement added")
                    st.rerun()
    else:
        st.info("No active onboarding workflows. Workflows are automatically created when trial accounts are set up.")

def render_customer_success(system):
    """Render customer success tracking dashboard"""
    st.header("📈 Customer Success Tracking")
    
    # Generate sample customer health data if none exists
    if not system.customer_health:
        sample_clients = ["client_001", "client_002", "client_003", "client_004"]
        for client_id in sample_clients:
            system.calculate_customer_health(client_id)
    
    # Health score overview
    st.subheader("Customer Health Overview")
    
    health_data = []
    for client_id, metrics in system.customer_health.items():
        health_data.append({
            "Client ID": client_id,
            "Health Score": metrics.health_score,
            "Health Category": metrics.health_category.value.title(),
            "Engagement Score": metrics.engagement_score,
            "Last Login": metrics.last_login.strftime("%Y-%m-%d"),
            "Contract Renewal": metrics.contract_renewal_date.strftime("%Y-%m-%d"),
            "Risk Level": "High" if metrics.risk_factors else "Low"
        })
    
    df = pd.DataFrame(health_data)
    st.dataframe(df, use_container_width=True)
    
    # Health score distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Health Score Distribution")
        health_categories = [metrics.health_category.value for metrics in system.customer_health.values()]
        category_counts = pd.Series(health_categories).value_counts()
        
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="Customer Health Distribution",
            color_discrete_map={
                'excellent': '#2E8B57',
                'good': '#32CD32',
                'fair': '#FFD700',
                'poor': '#FF6347',
                'critical': '#DC143C'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Average Health Score Trend")
        # Simulate trend data
        dates = pd.date_range(start='2024-01-01', end='2024-02-07', freq='W')
        scores = [75, 78, 82, 79, 85, 88]  # Sample trend data
        
        fig = px.line(
            x=dates[:len(scores)],
            y=scores,
            title="Health Score Trend",
            labels={'x': 'Date', 'y': 'Average Health Score'}
        )
        fig.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed customer analysis
    st.subheader("Detailed Customer Analysis")
    
    selected_client = st.selectbox(
        "Select Client for Detailed Analysis",
        options=list(system.customer_health.keys()),
        format_func=lambda x: f"Client {x}"
    )
    
    if selected_client:
        metrics = system.customer_health[selected_client]
        
        # Health score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=metrics.health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Health Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 50], 'color': "yellow"},
                    {'range': [50, 70], 'color': "orange"},
                    {'range': [70, 90], 'color': "lightgreen"},
                    {'range': [90, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Usage Metrics")
            for metric, value in metrics.usage_metrics.items():
                st.metric(
                    metric.replace('_', ' ').title(),
                    f"{value}{'%' if 'rate' in metric else ''}"
                )
        
        with col2:
            st.subheader("Feature Adoption")
            for feature, adopted in metrics.feature_adoption.items():
                status = "✅ Adopted" if adopted else "❌ Not Adopted"
                st.write(f"**{feature.replace('_', ' ').title()}:** {status}")
        
        with col3:
            st.subheader("Key Information")
            st.write(f"**Engagement Score:** {metrics.engagement_score:.1f}")
            st.write(f"**Support Tickets:** {metrics.support_tickets}")
            st.write(f"**Last Login:** {metrics.last_login.strftime('%Y-%m-%d')}")
            st.write(f"**Contract Renewal:** {metrics.contract_renewal_date.strftime('%Y-%m-%d')}")
        
        # Risk factors and opportunities
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Risk Factors")
            if metrics.risk_factors:
                for risk in metrics.risk_factors:
                    st.warning(f"⚠️ {risk}")
            else:
                st.success("✅ No identified risk factors")
        
        with col2:
            st.subheader("Expansion Opportunities")
            for opportunity in metrics.expansion_opportunities:
                st.info(f"💡 {opportunity}")
        
        # Success milestones
        st.subheader("Success Milestones")
        for milestone in metrics.success_milestones:
            st.success(f"🎉 {milestone}")

if __name__ == "__main__":
    render_enterprise_sales_dashboard()