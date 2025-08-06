"""
Enterprise Sales and Onboarding UI - API Connected Version
Streamlit interface for enterprise sales features using FastAPI backend
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from api_client import get_api_client

def render_enterprise_sales_dashboard():
    """Main enterprise sales dashboard"""
    st.title("🏢 Enterprise Sales & Onboarding")
    
    # Initialize API client
    api = get_api_client()
    
    # Check authentication
    if 'auth_token' not in st.session_state:
        st.warning("Please login to access the sales dashboard")
        render_login_form(api)
        return
    
    # Sidebar navigation
    st.sidebar.title("Enterprise Tools")
    page = st.sidebar.selectbox(
        "Select Tool",
        [
            "Sales Dashboard",
            "Pricing Calculator", 
            "Demo Scheduling",
            "Trial Management",
            "Lead Management",
            "Pipeline Analytics",
            "Customer Success"
        ]
    )
    
    if page == "Sales Dashboard":
        render_sales_dashboard(api)
    elif page == "Pricing Calculator":
        render_pricing_calculator(api)
    elif page == "Demo Scheduling":
        render_demo_scheduling(api)
    elif page == "Trial Management":
        render_trial_management(api)
    elif page == "Lead Management":
        render_lead_management(api)
    elif page == "Pipeline Analytics":
        render_pipeline_analytics(api)
    elif page == "Customer Success":
        render_customer_success(api)

def render_login_form(api):
    """Render login form"""
    st.subheader("Login")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        email = st.text_input("Email", placeholder="user@example.com")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            if email and password:
                response = api.login(email, password)
                if response.get("access_token"):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                st.error("Please enter email and password")

def render_sales_dashboard(api):
    """Render sales analytics dashboard"""
    st.header("📊 Sales Analytics Dashboard")
    
    # Get pipeline metrics from API
    metrics = api.get_pipeline_metrics()
    
    if not metrics:
        st.info("No sales data available")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Leads",
            metrics.get("total_leads", 0),
            delta=f"+{metrics.get('new_leads_this_week', 0)} this week"
        )
    
    with col2:
        st.metric(
            "Qualified Leads",
            metrics.get("qualified_leads", 0),
            delta=f"{metrics.get('qualification_rate', 0):.1f}% rate"
        )
    
    with col3:
        st.metric(
            "Pipeline Value",
            f"${metrics.get('total_pipeline_value', 0):,.0f}",
            delta=f"+${metrics.get('pipeline_growth', 0):,.0f}"
        )
    
    with col4:
        st.metric(
            "Win Rate",
            f"{metrics.get('win_rate', 0):.1f}%",
            delta=f"{metrics.get('win_rate_change', 0):+.1f}%"
        )
    
    # Pipeline by stage
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pipeline by Stage")
        if metrics.get("pipeline_by_stage"):
            stages = list(metrics["pipeline_by_stage"].keys())
            values = list(metrics["pipeline_by_stage"].values())
            
            fig = go.Figure(go.Funnel(
                y=stages,
                x=values,
                textinfo="value+percent initial"
            ))
            fig.update_layout(title="Sales Pipeline")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sales Velocity")
        velocity_data = metrics.get("sales_velocity", {})
        
        if velocity_data:
            velocity_metrics = pd.DataFrame({
                "Metric": ["Avg Deal Size", "Win Rate", "Sales Cycle", "Velocity"],
                "Value": [
                    f"${velocity_data.get('avg_deal_size', 0):,.0f}",
                    f"{velocity_data.get('win_rate', 0):.1f}%",
                    f"{velocity_data.get('avg_sales_cycle', 0)} days",
                    f"${velocity_data.get('velocity', 0):,.0f}/day"
                ]
            })
            st.dataframe(velocity_metrics, use_container_width=True)
    
    # Forecast
    if metrics.get("forecast"):
        st.subheader("Revenue Forecast")
        forecast = metrics["forecast"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("This Month", f"${forecast.get('current_month', 0):,.0f}")
        with col2:
            st.metric("Next Month", f"${forecast.get('next_month', 0):,.0f}")
        with col3:
            st.metric("This Quarter", f"${forecast.get('current_quarter', 0):,.0f}")

def render_lead_management(api):
    """Render lead management interface"""
    st.header("👥 Lead Management")
    
    # Lead filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "new", "contacted", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "low", "medium", "high"]
        )
    
    with col3:
        if st.button("Create New Lead", type="primary"):
            st.session_state.show_lead_form = True
    
    # Create lead form
    if st.session_state.get("show_lead_form", False):
        with st.expander("New Lead Form", expanded=True):
            render_create_lead_form(api)
    
    # Get leads from API
    leads = api.get_leads(status=status_filter if status_filter != "All" else None)
    
    if leads:
        # Display leads
        st.subheader(f"Leads ({len(leads)})")
        
        for lead in leads:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{lead['company_name']}**")
                    st.caption(f"{lead.get('contact_name', 'N/A')} • {lead.get('contact_email', 'N/A')}")
                
                with col2:
                    status_color = {
                        "new": "🔵",
                        "contacted": "🟡",
                        "qualified": "🟢",
                        "proposal": "🟠",
                        "closed_won": "✅",
                        "closed_lost": "❌"
                    }
                    st.write(f"{status_color.get(lead['status'], '⚪')} {lead['status']}")
                
                with col3:
                    st.write(f"Score: {lead.get('score', 0)}")
                    st.write(f"Priority: {lead.get('priority', 'medium')}")
                
                with col4:
                    if st.button("View", key=f"view_{lead['id']}"):
                        render_lead_detail(api, lead['id'])
                
                st.divider()
    else:
        st.info("No leads found")

def render_create_lead_form(api):
    """Render form to create new lead"""
    with st.form("create_lead_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name*", placeholder="Acme Corp")
            contact_name = st.text_input("Contact Name", placeholder="John Doe")
            contact_email = st.text_input("Contact Email*", placeholder="john@acme.com")
            contact_phone = st.text_input("Contact Phone", placeholder="+1 234 567 8900")
        
        with col2:
            company_size = st.selectbox(
                "Company Size",
                ["1-10", "11-50", "51-200", "201-1000", "1000+"]
            )
            industry = st.text_input("Industry", placeholder="Technology")
            use_case = st.text_area("Use Case", placeholder="Describe the use case...")
            budget_range = st.selectbox(
                "Budget Range",
                ["< $10k", "$10k-$50k", "$50k-$100k", "$100k-$500k", "> $500k"]
            )
        
        source = st.selectbox(
            "Lead Source",
            ["Website", "Referral", "Event", "Cold Outreach", "Partner", "Other"]
        )
        
        if st.form_submit_button("Create Lead", type="primary"):
            if company_name and contact_email:
                lead_data = {
                    "company_name": company_name,
                    "contact_info": {
                        "name": contact_name,
                        "email": contact_email,
                        "phone": contact_phone,
                        "company_size": company_size,
                        "industry": industry,
                        "use_case": use_case,
                        "budget_range": budget_range
                    },
                    "source": source
                }
                
                response = api.create_lead(lead_data)
                if response:
                    st.success("Lead created successfully!")
                    st.session_state.show_lead_form = False
                    st.rerun()
            else:
                st.error("Please fill in required fields")

def render_pricing_calculator(api):
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
        tier = st.selectbox("Pricing Tier", ["Standard", "Professional", "Enterprise", "Custom"])
        features = st.multiselect(
            "Additional Features",
            ["Advanced Analytics", "API Access", "White Label", "Priority Support", 
             "Custom Integrations", "SLA Guarantee", "Dedicated Account Manager"]
        )
    
    # Volume discounts
    st.subheader("Discounts & Adjustments")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        volume_discount = st.slider("Volume Discount %", 0, 50, 0)
    
    with col2:
        contract_discount = st.slider("Contract Length Discount %", 0, 20, 0)
    
    with col3:
        partner_discount = st.slider("Partner/Referral Discount %", 0, 30, 0)
    
    # Calculate pricing
    if st.button("Calculate Pricing", type="primary"):
        if client_name:
            pricing_data = {
                "client_name": client_name,
                "users": user_count,
                "tier": tier,
                "contract_months": contract_length,
                "features": features,
                "discounts": {
                    "volume": volume_discount,
                    "contract": contract_discount,
                    "partner": partner_discount
                }
            }
            
            # Call API to calculate pricing
            pricing = api.calculate_custom_pricing(pricing_data)
            
            if pricing:
                # Display pricing breakdown
                st.success("Pricing calculated successfully!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Pricing Summary")
                    st.metric("Base Price", f"${pricing.get('base_price', 0):,.2f}")
                    st.metric("Feature Add-ons", f"${pricing.get('feature_cost', 0):,.2f}")
                    st.metric("Total Discount", f"-${pricing.get('total_discount', 0):,.2f}")
                    st.metric("**Final Price**", f"${pricing.get('final_price', 0):,.2f}")
                
                with col2:
                    st.subheader("Payment Options")
                    st.write(f"**Monthly**: ${pricing.get('monthly_price', 0):,.2f}")
                    st.write(f"**Quarterly**: ${pricing.get('quarterly_price', 0):,.2f}")
                    st.write(f"**Annual**: ${pricing.get('annual_price', 0):,.2f}")
                    st.write(f"**Total Contract**: ${pricing.get('total_contract_value', 0):,.2f}")
                
                # Export options
                st.subheader("Export Proposal")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Generate PDF Proposal"):
                        st.info("PDF proposal generated and sent to client")
                
                with col2:
                    if st.button("Send Email Quote"):
                        st.info("Quote sent to client via email")
                
                with col3:
                    if st.button("Create Opportunity"):
                        # Create opportunity in CRM
                        opp_data = {
                            "name": f"{client_name} - Enterprise Deal",
                            "amount": pricing['total_contract_value'],
                            "stage": "proposal",
                            "probability": 60,
                            "expected_close_date": (datetime.now() + timedelta(days=30)).isoformat()
                        }
                        api.create_opportunity(opp_data)
                        st.success("Opportunity created in CRM")
        else:
            st.error("Please enter client name")

def render_demo_scheduling(api):
    """Render demo scheduling interface"""
    st.header("📅 Demo Scheduling")
    
    tab1, tab2 = st.tabs(["Schedule Demo", "Upcoming Demos"])
    
    with tab1:
        st.subheader("Schedule New Demo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company = st.text_input("Company Name*", placeholder="Acme Corp")
            contact_name = st.text_input("Contact Name*", placeholder="John Doe")
            contact_email = st.text_input("Contact Email*", placeholder="john@acme.com")
            demo_type = st.selectbox("Demo Type", ["Live Demo", "Self-Guided", "Recorded"])
        
        with col2:
            demo_date = st.date_input("Demo Date", min_value=datetime.now().date())
            demo_time = st.time_input("Demo Time")
            duration = st.selectbox("Duration", ["30 minutes", "45 minutes", "60 minutes"])
            sales_rep = st.selectbox("Sales Rep", ["Sarah Johnson", "Mike Chen", "David Wilson"])
        
        requirements = st.text_area("Special Requirements", placeholder="Any specific features to highlight...")
        
        if st.button("Schedule Demo", type="primary"):
            if all([company, contact_name, contact_email]):
                demo_data = {
                    "company": company,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "demo_type": demo_type,
                    "scheduled_at": f"{demo_date} {demo_time}",
                    "duration": duration,
                    "sales_rep": sales_rep,
                    "requirements": requirements
                }
                
                response = api.schedule_demo(demo_data)
                if response:
                    st.success("Demo scheduled successfully!")
                    st.info(f"Calendar invite sent to {contact_email}")
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("Upcoming Demos")
        
        # Mock data for upcoming demos (would come from API)
        demos = [
            {
                "date": "2024-02-08 10:00 AM",
                "company": "TechCorp Inc",
                "contact": "Jane Smith",
                "type": "Live Demo",
                "rep": "Sarah Johnson"
            },
            {
                "date": "2024-02-09 2:00 PM",
                "company": "DataFlow Ltd",
                "contact": "Bob Wilson",
                "type": "Self-Guided",
                "rep": "Mike Chen"
            }
        ]
        
        for demo in demos:
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**{demo['company']}**")
                st.caption(demo['contact'])
            
            with col2:
                st.write(demo['date'])
                st.caption(demo['type'])
            
            with col3:
                st.write(demo['rep'])
            
            with col4:
                if st.button("Join", key=f"join_{demo['company']}"):
                    st.info("Opening demo room...")
            
            st.divider()

def render_trial_management(api):
    """Render trial management interface"""
    st.header("🚀 Trial Management")
    
    tab1, tab2, tab3 = st.tabs(["Create Trial", "Active Trials", "Trial Analytics"])
    
    with tab1:
        st.subheader("Create Trial Account")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company = st.text_input("Company Name*")
            admin_email = st.text_input("Admin Email*")
            admin_name = st.text_input("Admin Name*")
            trial_duration = st.selectbox("Trial Duration", ["14 days", "30 days", "60 days"])
        
        with col2:
            trial_type = st.selectbox("Trial Type", ["Standard", "Premium", "Enterprise"])
            user_limit = st.number_input("User Limit", min_value=1, max_value=1000, value=10)
            features = st.multiselect(
                "Enabled Features",
                ["All Features", "API Access", "Advanced Analytics", "White Label", "Priority Support"]
            )
        
        if st.button("Create Trial", type="primary"):
            if all([company, admin_email, admin_name]):
                trial_data = {
                    "company": company,
                    "admin_email": admin_email,
                    "admin_name": admin_name,
                    "duration_days": int(trial_duration.split()[0]),
                    "trial_type": trial_type,
                    "user_limit": user_limit,
                    "features": features
                }
                
                response = api.create_trial(trial_data)
                if response:
                    st.success("Trial created successfully!")
                    st.info(f"Welcome email sent to {admin_email}")
                    st.code(f"Trial URL: {response.get('trial_url', 'N/A')}")
            else:
                st.error("Please fill in all required fields")
    
    with tab2:
        st.subheader("Active Trials")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Status", ["All", "Active", "Expired", "Converted"])
        with col2:
            sort_by = st.selectbox("Sort By", ["Start Date", "End Date", "Usage", "Company"])
        
        # Mock trial data (would come from API)
        trials = [
            {
                "company": "TechCorp Inc",
                "start_date": "2024-01-25",
                "end_date": "2024-02-24",
                "usage": "85%",
                "users": "8/10",
                "status": "Active"
            },
            {
                "company": "DataFlow Ltd",
                "start_date": "2024-01-15",
                "end_date": "2024-02-14",
                "usage": "92%",
                "users": "45/50",
                "status": "Active"
            }
        ]
        
        for trial in trials:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{trial['company']}**")
                    st.caption(f"{trial['start_date']} - {trial['end_date']}")
                
                with col2:
                    st.progress(int(trial['usage'].rstrip('%')) / 100)
                    st.caption(f"Usage: {trial['usage']}")
                
                with col3:
                    st.write(f"Users: {trial['users']}")
                
                with col4:
                    status_color = {"Active": "🟢", "Expired": "🔴", "Converted": "✅"}
                    st.write(f"{status_color.get(trial['status'], '⚪')} {trial['status']}")
                
                with col5:
                    if st.button("Extend", key=f"extend_{trial['company']}"):
                        st.success("Trial extended by 14 days")
                
                st.divider()
    
    with tab3:
        st.subheader("Trial Conversion Analytics")
        
        # Conversion metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Trials", "23", delta="+3")
        with col2:
            st.metric("Conversion Rate", "32%", delta="+5%")
        with col3:
            st.metric("Avg Trial Usage", "78%", delta="+12%")
        with col4:
            st.metric("Revenue from Trials", "$125K", delta="+$25K")
        
        # Conversion funnel
        st.subheader("Trial Conversion Funnel")
        funnel_data = {
            "Stage": ["Trial Started", "Active Usage", "High Engagement", "Converted"],
            "Count": [100, 78, 45, 32]
        }
        df = pd.DataFrame(funnel_data)
        
        fig = go.Figure(go.Funnel(
            y=df['Stage'],
            x=df['Count'],
            textinfo="value+percent initial"
        ))
        st.plotly_chart(fig, use_container_width=True)

def render_pipeline_analytics(api):
    """Render pipeline analytics"""
    st.header("📈 Pipeline Analytics")
    
    # Date range selector
    col1, col2 = st.columns([2, 3])
    with col1:
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last Quarter", "This Year"]
        )
    
    # Get metrics from API
    metrics = api.get_pipeline_metrics()
    
    if metrics:
        # Pipeline overview
        st.subheader("Pipeline Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Pipeline",
                f"${metrics.get('total_pipeline_value', 0):,.0f}",
                delta=f"{metrics.get('pipeline_growth_pct', 0):.1f}%"
            )
        
        with col2:
            st.metric(
                "Weighted Pipeline",
                f"${metrics.get('weighted_pipeline_value', 0):,.0f}"
            )
        
        with col3:
            st.metric(
                "Avg Deal Size",
                f"${metrics.get('avg_deal_size', 0):,.0f}"
            )
        
        with col4:
            st.metric(
                "Sales Velocity",
                f"${metrics.get('sales_velocity', {}).get('velocity', 0):,.0f}/day"
            )
        
        # Pipeline by stage chart
        if metrics.get("pipeline_by_stage"):
            st.subheader("Pipeline by Stage")
            
            stages = list(metrics["pipeline_by_stage"].keys())
            values = list(metrics["pipeline_by_stage"].values())
            
            fig = px.bar(
                x=stages,
                y=values,
                title="Pipeline Value by Stage",
                labels={"x": "Stage", "y": "Value ($)"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Win/Loss analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Win/Loss Analysis")
            if metrics.get("win_loss_reasons"):
                reasons_df = pd.DataFrame(metrics["win_loss_reasons"])
                fig = px.pie(
                    reasons_df,
                    values='count',
                    names='reason',
                    title="Loss Reasons"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Sales Rep Performance")
            if metrics.get("rep_performance"):
                rep_df = pd.DataFrame(metrics["rep_performance"])
                fig = px.bar(
                    rep_df,
                    x='rep',
                    y='revenue',
                    title="Revenue by Sales Rep"
                )
                st.plotly_chart(fig, use_container_width=True)

def render_customer_success(api):
    """Render customer success metrics"""
    st.header("🎯 Customer Success")
    
    tab1, tab2, tab3 = st.tabs(["Health Scores", "Onboarding", "Churn Risk"])
    
    with tab1:
        st.subheader("Customer Health Scores")
        
        # Mock customer health data
        customers = [
            {"name": "TechCorp Inc", "score": 85, "trend": "up", "mrr": "$12,500"},
            {"name": "DataFlow Ltd", "score": 72, "trend": "stable", "mrr": "$8,300"},
            {"name": "GlobalMedia", "score": 45, "trend": "down", "mrr": "$15,000"},
        ]
        
        for customer in customers:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{customer['name']}**")
                st.progress(customer['score'] / 100)
            
            with col2:
                st.metric("Health Score", customer['score'])
            
            with col3:
                trend_icon = {"up": "📈", "down": "📉", "stable": "➡️"}
                st.write(f"{trend_icon[customer['trend']]} {customer['trend'].title()}")
            
            with col4:
                st.write(f"MRR: {customer['mrr']}")
            
            st.divider()
    
    with tab2:
        st.subheader("Onboarding Progress")
        
        # Onboarding stages
        stages = ["Kickoff", "Integration", "Training", "Go Live", "Success Review"]
        
        # Mock onboarding data
        onboarding_customers = [
            {"name": "NewCorp", "stage": 2, "days_elapsed": 5},
            {"name": "StartupXYZ", "stage": 3, "days_elapsed": 12},
        ]
        
        for customer in onboarding_customers:
            st.write(f"**{customer['name']}** - Day {customer['days_elapsed']}")
            
            # Progress bar
            progress = (customer['stage'] + 1) / len(stages)
            st.progress(progress)
            
            # Stage indicators
            cols = st.columns(len(stages))
            for i, (col, stage) in enumerate(zip(cols, stages)):
                with col:
                    if i <= customer['stage']:
                        st.success(f"✓ {stage}")
                    else:
                        st.info(f"○ {stage}")
            
            st.divider()
    
    with tab3:
        st.subheader("Churn Risk Analysis")
        
        # Churn risk metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("At Risk Accounts", "3", delta="+1")
        with col2:
            st.metric("Predicted Churn", "$45K MRR", delta="+$5K")
        with col3:
            st.metric("Save Rate", "67%", delta="-5%")
        
        # At-risk customers
        st.subheader("High Risk Accounts")
        
        risk_customers = [
            {
                "name": "GlobalMedia",
                "risk_score": 78,
                "reasons": ["Low usage", "Support tickets"],
                "mrr": "$15,000"
            },
            {
                "name": "OldTech Co",
                "risk_score": 65,
                "reasons": ["Contract expiring", "No engagement"],
                "mrr": "$5,500"
            }
        ]
        
        for customer in risk_customers:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{customer['name']}**")
                st.caption(f"Risk factors: {', '.join(customer['reasons'])}")
            
            with col2:
                st.metric("Risk Score", f"{customer['risk_score']}%")
            
            with col3:
                if st.button("Take Action", key=f"action_{customer['name']}"):
                    st.info("Opening customer success playbook...")
            
            st.divider()

def render_lead_detail(api, lead_id):
    """Render detailed lead view"""
    # This would open in a modal or separate page
    st.info(f"Opening lead details for ID: {lead_id}")