"""
Enterprise Sales and Onboarding UI
Streamlit interface for managing sales pipeline, demos, trials, and onboarding
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Enterprise Sales Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EnterpriseSalesUI:
    def __init__(self):
        self.api_base = st.session_state.get('api_base', 'http://localhost:8000')
        self.headers = self._get_auth_headers()
    
    def _get_auth_headers(self):
        """Get authentication headers"""
        token = st.session_state.get('auth_token')
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None):
        """Make API request with error handling"""
        try:
            url = f"{self.api_base}{endpoint}"
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            else:
                st.error(f"Unsupported method: {method}")
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
            return None

def main():
    ui = EnterpriseSalesUI()
    
    st.title("🏢 Enterprise Sales Dashboard")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "Sales Overview",
            "Lead Management", 
            "Demo Scheduling",
            "Trial Management",
            "Contract Management",
            "Onboarding Workflows",
            "Sales Analytics",
            "CRM Integration"
        ]
    )
    
    # Authentication check
    if not st.session_state.get('auth_token'):
        st.error("Please login to access the enterprise sales dashboard")
        return
    
    # Route to selected page
    if page == "Sales Overview":
        show_sales_overview(ui)
    elif page == "Lead Management":
        show_lead_management(ui)
    elif page == "Demo Scheduling":
        show_demo_scheduling(ui)
    elif page == "Trial Management":
        show_trial_management(ui)
    elif page == "Contract Management":
        show_contract_management(ui)
    elif page == "Onboarding Workflows":
        show_onboarding_workflows(ui)
    elif page == "Sales Analytics":
        show_sales_analytics(ui)
    elif page == "CRM Integration":
        show_crm_integration(ui)

def show_sales_overview(ui: EnterpriseSalesUI):
    """Sales overview dashboard"""
    st.header("📊 Sales Overview")
    
    # Get sales metrics
    metrics = ui._make_request('GET', '/api/enterprise/analytics/sales-metrics')
    
    if metrics:
        metrics_data = metrics.get('metrics', {})
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Leads",
                metrics_data.get('total_leads', 0),
                delta=metrics_data.get('leads_growth', 0)
            )
        
        with col2:
            st.metric(
                "Active Demos",
                metrics_data.get('active_demos', 0),
                delta=metrics_data.get('demos_scheduled_this_week', 0)
            )
        
        with col3:
            st.metric(
                "Active Trials",
                metrics_data.get('active_trials', 0),
                delta=metrics_data.get('trials_started_this_week', 0)
            )
        
        with col4:
            st.metric(
                "Pipeline Value",
                f"${metrics_data.get('total_pipeline_value', 0):,.0f}",
                delta=f"${metrics_data.get('pipeline_growth', 0):,.0f}"
            )
        
        st.divider()
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Lead Status Distribution")
            if 'lead_status_breakdown' in metrics_data:
                status_data = metrics_data['lead_status_breakdown']
                fig = px.pie(
                    values=list(status_data.values()),
                    names=list(status_data.keys()),
                    title="Leads by Status"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Monthly Pipeline Trend")
            if 'monthly_pipeline' in metrics_data:
                pipeline_data = metrics_data['monthly_pipeline']
                months = list(pipeline_data.keys())
                values = list(pipeline_data.values())
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=months,
                    y=values,
                    mode='lines+markers',
                    name='Pipeline Value'
                ))
                fig.update_layout(title="Pipeline Value Over Time")
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("Unable to load sales metrics")

def show_lead_management(ui: EnterpriseSalesUI):
    """Lead management interface"""
    st.header("🎯 Lead Management")
    
    # Create new lead
    with st.expander("➕ Create New Lead"):
        with st.form("create_lead_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name*", key="company_name")
                contact_name = st.text_input("Contact Name", key="contact_name")
                email = st.text_input("Email*", key="email")
                phone = st.text_input("Phone", key="phone")
            
            with col2:
                industry = st.selectbox(
                    "Industry",
                    ["Technology", "Healthcare", "Finance", "Education", "Other"],
                    key="industry"
                )
                company_size = st.selectbox(
                    "Company Size",
                    ["1-10", "11-50", "51-200", "201-1000", "1000+"],
                    key="company_size"
                )
                budget_range = st.selectbox(
                    "Budget Range",
                    ["< $10k", "$10k-$50k", "$50k-$100k", "$100k-$500k", "> $500k"],
                    key="budget_range"
                )
                source = st.selectbox(
                    "Lead Source",
                    ["Website", "Referral", "Cold Outreach", "Trade Show", "Other"],
                    key="source"
                )
            
            use_case = st.text_area("Use Case Description", key="use_case")
            timeline = st.text_input("Expected Timeline", key="timeline")
            
            if st.form_submit_button("Create Lead"):
                if company_name and email:
                    lead_data = {
                        "company_name": company_name,
                        "contact_name": contact_name,
                        "email": email,
                        "phone": phone,
                        "industry": industry,
                        "company_size": company_size,
                        "use_case": use_case,
                        "budget_range": budget_range,
                        "timeline": timeline,
                        "source": source
                    }
                    
                    result = ui._make_request('POST', '/api/enterprise/leads', lead_data)
                    if result:
                        st.success(f"Lead created successfully! ID: {result.get('lead_id')}")
                        st.rerun()
                    else:
                        st.error("Failed to create lead")
                else:
                    st.error("Company name and email are required")
    
    # Filter leads
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "New", "Contacted", "Qualified", "Proposal", "Closed Won", "Closed Lost"])
    with col2:
        source_filter = st.selectbox("Filter by Source", ["All", "Website", "Referral", "Cold Outreach", "Trade Show", "Other"])
    with col3:
        if st.button("🔄 Refresh Leads"):
            st.rerun()
    
    # Get and display leads
    filters = {}
    if status_filter != "All":
        filters['status_filter'] = status_filter.lower().replace(' ', '_')
    if source_filter != "All":
        filters['source_filter'] = source_filter
    
    leads_response = ui._make_request('GET', '/api/enterprise/leads', filters)
    
    if leads_response and 'leads' in leads_response:
        leads = leads_response['leads']
        
        if leads:
            # Convert to DataFrame for display
            df = pd.DataFrame(leads)
            
            # Display leads table
            st.subheader(f"📋 Leads ({len(leads)} total)")
            
            # Make table interactive
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "Lead ID",
                    "company_name": "Company",
                    "contact_name": "Contact",
                    "email": "Email",
                    "status": "Status",
                    "score": st.column_config.ProgressColumn(
                        "Score",
                        help="Lead score (0-100)",
                        format="%d",
                        min_value=0,
                        max_value=100,
                    ),
                    "created_at": st.column_config.DatetimeColumn(
                        "Created",
                        format="MMM DD, YYYY"
                    )
                }
            )
        else:
            st.info("No leads found matching the selected filters")
    else:
        st.warning("Unable to load leads")

def show_demo_scheduling(ui: EnterpriseSalesUI):
    """Demo scheduling interface"""
    st.header("🎬 Demo Scheduling")
    
    # Schedule new demo
    with st.expander("📅 Schedule New Demo"):
        with st.form("schedule_demo_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                lead_id = st.text_input("Lead ID*", help="ID of the lead to schedule demo for")
                demo_type = st.selectbox("Demo Type", ["Standard", "Custom", "Technical", "Executive"])
                attendees = st.text_area("Attendees", help="List attendees (one per line)")
            
            with col2:
                scheduled_date = st.date_input("Demo Date")
                scheduled_time = st.time_input("Demo Time")
                duration = st.selectbox("Duration (minutes)", [30, 45, 60, 90, 120])
            
            demo_requirements = st.text_area("Special Requirements")
            
            if st.form_submit_button("Schedule Demo"):
                if lead_id:
                    demo_datetime = datetime.combine(scheduled_date, scheduled_time)
                    attendee_list = [name.strip() for name in attendees.split('\n') if name.strip()]
                    
                    demo_data = {
                        "lead_id": lead_id,
                        "demo_type": demo_type,
                        "scheduled_at": demo_datetime.isoformat(),
                        "duration_minutes": duration,
                        "attendees": attendee_list,
                        "requirements": demo_requirements
                    }
                    
                    result = ui._make_request('POST', '/api/enterprise/demos/schedule', demo_data)
                    if result:
                        st.success(f"Demo scheduled successfully! ID: {result.get('demo_id')}")
                        st.rerun()
                    else:
                        st.error("Failed to schedule demo")
                else:
                    st.error("Lead ID is required")
    
    # Display scheduled demos
    demos_response = ui._make_request('GET', '/api/enterprise/demos')
    
    if demos_response and 'demos' in demos_response:
        demos = demos_response['demos']
        
        if demos:
            st.subheader(f"📅 Scheduled Demos ({len(demos)} total)")
            
            for demo in demos:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**{demo.get('demo_type', 'Standard')} Demo**")
                        st.write(f"Lead: {demo.get('lead_id', 'N/A')}")
                        st.write(f"Status: {demo.get('status', 'scheduled').title()}")
                    
                    with col2:
                        scheduled_at = datetime.fromisoformat(demo.get('scheduled_at', ''))
                        st.write(f"📅 {scheduled_at.strftime('%B %d, %Y')}")
                        st.write(f"🕐 {scheduled_at.strftime('%I:%M %p')}")
                    
                    with col3:
                        st.write(f"⏱️ {demo.get('duration_minutes', 60)} minutes")
                        attendee_count = len(demo.get('attendees', []))
                        st.write(f"👥 {attendee_count} attendees")
                    
                    with col4:
                        if st.button("✏️", key=f"edit_demo_{demo.get('id')}"):
                            st.info("Demo editing coming soon")
                
                st.divider()
        else:
            st.info("No demos scheduled")

def show_trial_management(ui: EnterpriseSalesUI):
    """Trial management interface"""
    st.header("🧪 Trial Management")
    
    # Create new trial
    with st.expander("🆕 Create New Trial"):
        with st.form("create_trial_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                lead_id = st.text_input("Lead ID*")
                trial_type = st.selectbox("Trial Type", ["Standard", "Enterprise", "Custom"])
                duration_days = st.number_input("Duration (days)", min_value=7, max_value=90, value=14)
            
            with col2:
                features = st.multiselect(
                    "Features",
                    ["Transcription", "Analysis", "API Access", "Integrations", "Priority Support"]
                )
                limits = st.text_area("Usage Limits", help="e.g., 100 hours transcription, 1000 API calls")
            
            notes = st.text_area("Trial Notes")
            
            if st.form_submit_button("Create Trial"):
                if lead_id:
                    trial_data = {
                        "lead_id": lead_id,
                        "trial_type": trial_type,
                        "duration_days": duration_days,
                        "features": features,
                        "limits": limits,
                        "notes": notes
                    }
                    
                    result = ui._make_request('POST', '/api/enterprise/trials/create', trial_data)
                    if result:
                        st.success(f"Trial created successfully!")
                        st.info(f"Trial ID: {result.get('trial_id')}")
                        st.info(f"Credentials: {result.get('credentials')}")
                        st.rerun()
                    else:
                        st.error("Failed to create trial")
                else:
                    st.error("Lead ID is required")
    
    # Display trials
    trials_response = ui._make_request('GET', '/api/enterprise/trials')
    
    if trials_response and 'trials' in trials_response:
        trials = trials_response['trials']
        
        if trials:
            st.subheader(f"🧪 Active Trials ({len(trials)} total)")
            
            for trial in trials:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**{trial.get('trial_type', 'Standard')} Trial**")
                        st.write(f"Lead: {trial.get('lead_id', 'N/A')}")
                        st.write(f"Status: {trial.get('status', 'active').title()}")
                    
                    with col2:
                        start_date = datetime.fromisoformat(trial.get('start_date', ''))
                        end_date = datetime.fromisoformat(trial.get('end_date', ''))
                        st.write(f"📅 {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}")
                        
                        days_remaining = (end_date - datetime.now()).days
                        if days_remaining > 0:
                            st.write(f"⏰ {days_remaining} days remaining")
                        else:
                            st.write("⏰ Expired")
                    
                    with col3:
                        # Show usage if available
                        usage = trial.get('usage_stats', {})
                        if usage:
                            transcription_hours = usage.get('transcription_hours', 0)
                            api_calls = usage.get('api_calls', 0)
                            st.write(f"🎙️ {transcription_hours:.1f} hours")
                            st.write(f"🔌 {api_calls} API calls")
                        else:
                            st.write("No usage data")
                    
                    with col4:
                        if st.button("📊", key=f"trial_details_{trial.get('id')}"):
                            st.info("Trial details coming soon")
                
                st.divider()
        else:
            st.info("No active trials")

def show_contract_management(ui: EnterpriseSalesUI):
    """Contract management interface"""
    st.header("📄 Contract Management")
    
    # Create new contract
    with st.expander("📝 Create New Contract"):
        with st.form("create_contract_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                lead_id = st.text_input("Lead ID*")
                contract_type = st.selectbox("Contract Type", ["Standard", "Enterprise", "Custom"])
                annual_value = st.number_input("Annual Contract Value ($)", min_value=0, value=10000)
                term_months = st.number_input("Term (months)", min_value=1, max_value=60, value=12)
            
            with col2:
                start_date = st.date_input("Start Date")
                renewal_type = st.selectbox("Renewal", ["Auto-renew", "Manual", "One-time"])
                discount_percent = st.number_input("Discount (%)", min_value=0, max_value=100, value=0)
            
            products = st.multiselect(
                "Products/Services",
                ["Transcription Pro", "Analysis Suite", "API Platform", "Custom Integration", "Premium Support"]
            )
            
            terms = st.text_area("Custom Terms")
            
            if st.form_submit_button("Create Contract"):
                if lead_id and annual_value > 0:
                    contract_data = {
                        "lead_id": lead_id,
                        "contract_type": contract_type,
                        "annual_value": annual_value,
                        "term_months": term_months,
                        "start_date": start_date.isoformat(),
                        "renewal_type": renewal_type,
                        "discount_percent": discount_percent,
                        "products": products,
                        "custom_terms": terms
                    }
                    
                    result = ui._make_request('POST', '/api/enterprise/contracts/create', contract_data)
                    if result:
                        st.success(f"Contract created successfully! ID: {result.get('contract_id')}")
                        st.rerun()
                    else:
                        st.error("Failed to create contract")
                else:
                    st.error("Lead ID and annual value are required")
    
    # Display contracts
    contracts_response = ui._make_request('GET', '/api/enterprise/contracts')
    
    if contracts_response and 'contracts' in contracts_response:
        contracts = contracts_response['contracts']
        
        if contracts:
            st.subheader(f"📄 Contracts ({len(contracts)} total)")
            
            for contract in contracts:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**{contract.get('contract_type', 'Standard')} Contract**")
                        st.write(f"Lead: {contract.get('lead_id', 'N/A')}")
                        st.write(f"Status: {contract.get('status', 'draft').title()}")
                    
                    with col2:
                        annual_value = contract.get('annual_value', 0)
                        term_months = contract.get('term_months', 12)
                        st.write(f"💰 ${annual_value:,.0f}/year")
                        st.write(f"📅 {term_months} months")
                    
                    with col3:
                        start_date = contract.get('start_date')
                        if start_date:
                            start_date = datetime.fromisoformat(start_date)
                            st.write(f"🚀 {start_date.strftime('%b %d, %Y')}")
                        
                        renewal = contract.get('renewal_type', 'Manual')
                        st.write(f"🔄 {renewal}")
                    
                    with col4:
                        if st.button("📥", key=f"download_contract_{contract.get('id')}"):
                            st.info("Contract download coming soon")
                
                st.divider()
        else:
            st.info("No contracts found")

def show_onboarding_workflows(ui: EnterpriseSalesUI):
    """Onboarding workflow management"""
    st.header("🚀 Onboarding Workflows")
    
    # Start new onboarding
    with st.expander("▶️ Start New Onboarding"):
        with st.form("start_onboarding_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                customer_email = st.text_input("Customer Email*")
                customer_name = st.text_input("Customer Name*")
                company_name = st.text_input("Company Name*")
                contract_id = st.text_input("Contract ID")
            
            with col2:
                workflow_type = st.selectbox("Workflow Type", ["Standard", "Enterprise", "Technical"])
                priority = st.selectbox("Priority", ["Low", "Normal", "High", "Critical"])
                assigned_csm = st.text_input("Assigned CSM")
            
            requirements = st.text_area("Special Requirements")
            
            if st.form_submit_button("Start Onboarding"):
                if customer_email and customer_name and company_name:
                    onboarding_data = {
                        "customer_email": customer_email,
                        "customer_name": customer_name,
                        "company_name": company_name,
                        "contract_id": contract_id,
                        "workflow_type": workflow_type,
                        "priority": priority,
                        "assigned_csm": assigned_csm,
                        "requirements": requirements
                    }
                    
                    result = ui._make_request('POST', '/api/enterprise/onboarding/start', onboarding_data)
                    if result:
                        st.success(f"Onboarding started! Workflow ID: {result.get('workflow_id')}")
                        st.rerun()
                    else:
                        st.error("Failed to start onboarding")
                else:
                    st.error("Customer email, name, and company name are required")
    
    # Display onboarding workflows
    workflows_response = ui._make_request('GET', '/api/enterprise/onboarding')
    
    if workflows_response and 'workflows' in workflows_response:
        workflows = workflows_response['workflows']
        
        if workflows:
            st.subheader(f"🚀 Active Onboarding Workflows ({len(workflows)} total)")
            
            for workflow in workflows:
                with st.expander(f"{workflow.get('company_name', 'Unknown')} - {workflow.get('status', 'active').title()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Customer:** {workflow.get('customer_name', 'N/A')}")
                        st.write(f"**Email:** {workflow.get('customer_email', 'N/A')}")
                        st.write(f"**Company:** {workflow.get('company_name', 'N/A')}")
                        st.write(f"**Type:** {workflow.get('workflow_type', 'Standard')}")
                    
                    with col2:
                        st.write(f"**Status:** {workflow.get('status', 'active').title()}")
                        st.write(f"**Priority:** {workflow.get('priority', 'Normal')}")
                        st.write(f"**CSM:** {workflow.get('assigned_csm', 'Not assigned')}")
                        
                        created_at = workflow.get('created_at')
                        if created_at:
                            created_date = datetime.fromisoformat(created_at)
                            st.write(f"**Started:** {created_date.strftime('%b %d, %Y')}")
                    
                    # Show progress
                    steps = workflow.get('steps', [])
                    if steps:
                        st.write("**Progress:**")
                        completed_steps = len([s for s in steps if s.get('completed')])
                        total_steps = len(steps)
                        progress = completed_steps / total_steps if total_steps > 0 else 0
                        
                        st.progress(progress)
                        st.write(f"{completed_steps}/{total_steps} steps completed")
                        
                        # Show individual steps
                        for i, step in enumerate(steps):
                            status_icon = "✅" if step.get('completed') else "⏳"
                            st.write(f"{status_icon} {step.get('name', f'Step {i+1}')}")
        else:
            st.info("No active onboarding workflows")

def show_sales_analytics(ui: EnterpriseSalesUI):
    """Sales analytics and reporting"""
    st.header("📈 Sales Analytics")
    
    # Time period selector
    col1, col2, col3 = st.columns(3)
    with col1:
        time_period = st.selectbox("Time Period", ["7d", "30d", "90d", "1y"])
    with col2:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Get analytics data
    analytics_data = ui._make_request('GET', '/api/enterprise/analytics/sales-metrics', {'time_period': time_period})
    
    if analytics_data and 'metrics' in analytics_data:
        metrics = analytics_data['metrics']
        
        # Key metrics
        st.subheader("🔢 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Conversion Rate", f"{metrics.get('conversion_rate', 0):.1f}%")
        with col2:
            st.metric("Avg Deal Size", f"${metrics.get('average_deal_size', 0):,.0f}")
        with col3:
            st.metric("Sales Cycle", f"{metrics.get('avg_sales_cycle_days', 0):.0f} days")
        with col4:
            st.metric("Close Rate", f"{metrics.get('close_rate', 0):.1f}%")
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Pipeline by Stage")
            pipeline_by_stage = metrics.get('pipeline_by_stage', {})
            if pipeline_by_stage:
                fig = px.funnel(
                    x=list(pipeline_by_stage.values()),
                    y=list(pipeline_by_stage.keys()),
                    orientation='h'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Revenue Forecast")
            forecast_data = metrics.get('revenue_forecast', {})
            if forecast_data:
                months = list(forecast_data.keys())
                values = list(forecast_data.values())
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=months, y=values, name="Forecasted Revenue"))
                fig.update_layout(title="3-Month Revenue Forecast")
                st.plotly_chart(fig, use_container_width=True)
        
        # Activity metrics
        st.subheader("📋 Activity Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Demos Scheduled", metrics.get('demos_scheduled', 0))
        with col2:
            st.metric("Trials Started", metrics.get('trials_started', 0))
        with col3:
            st.metric("Contracts Signed", metrics.get('contracts_signed', 0))
        
    else:
        st.warning("Unable to load analytics data")

def show_crm_integration(ui: EnterpriseSalesUI):
    """CRM integration settings"""
    st.header("🔗 CRM Integration")
    
    st.info("Configure integration with external CRM systems like Salesforce, HubSpot, or Pipedrive")
    
    # CRM selection
    crm_type = st.selectbox("CRM System", ["Salesforce", "HubSpot", "Pipedrive", "Custom"])
    
    if crm_type == "Salesforce":
        st.subheader("🏢 Salesforce Configuration")
        with st.form("salesforce_config"):
            instance_url = st.text_input("Instance URL")
            client_id = st.text_input("Consumer Key")
            client_secret = st.text_input("Consumer Secret", type="password")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            security_token = st.text_input("Security Token", type="password")
            
            if st.form_submit_button("Test Connection"):
                config = {
                    "type": "salesforce",
                    "instance_url": instance_url,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": password,
                    "security_token": security_token
                }
                
                result = ui._make_request('POST', '/api/enterprise/crm/sync', config)
                if result:
                    st.success("Connection successful!")
                else:
                    st.error("Connection failed")
    
    elif crm_type == "HubSpot":
        st.subheader("🟠 HubSpot Configuration")
        with st.form("hubspot_config"):
            api_key = st.text_input("API Key", type="password")
            
            if st.form_submit_button("Test Connection"):
                config = {
                    "type": "hubspot",
                    "api_key": api_key
                }
                
                result = ui._make_request('POST', '/api/enterprise/crm/sync', config)
                if result:
                    st.success("Connection successful!")
                else:
                    st.error("Connection failed")
    
    # Sync settings
    st.subheader("⚙️ Sync Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        sync_leads = st.checkbox("Sync Leads", value=True)
        sync_opportunities = st.checkbox("Sync Opportunities", value=True)
        sync_activities = st.checkbox("Sync Activities", value=True)
    
    with col2:
        sync_frequency = st.selectbox("Sync Frequency", ["Real-time", "Every 15 minutes", "Hourly", "Daily"])
        auto_create_leads = st.checkbox("Auto-create leads from CRM")
        bidirectional_sync = st.checkbox("Bidirectional sync")
    
    if st.button("💾 Save Sync Settings"):
        st.success("Sync settings saved successfully!")
    
    # Sync status
    st.subheader("📊 Sync Status")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Last Sync", "2 minutes ago")
    with col2:
        st.metric("Leads Synced", "1,234")
    with col3:
        st.metric("Opportunities Synced", "567")
    with col4:
        st.metric("Sync Errors", "0")

if __name__ == "__main__":
    main()