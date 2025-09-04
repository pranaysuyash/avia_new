"""
Business Intelligence & ROI Dashboard
Streamlit interface for business metrics, predictions, and ROI analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import json
import numpy as np
from streamlit_intent_utils import (
    render_share_inline,
    render_share_block,
    log_ux_event,
    get_params,
    update_params,
    render_skeleton_list,
)

# Page configuration
st.set_page_config(
    page_title="Business Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .risk-high {
        background: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .risk-medium {
        background: #fed7aa;
        border-left: 4px solid #f97316;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .risk-low {
        background: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .opportunity-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .health-score {
        font-size: 2rem;
        font-weight: bold;
    }
    .health-excellent { color: #10b981; }
    .health-good { color: #3b82f6; }
    .health-fair { color: #f59e0b; }
    .health-poor { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_period' not in st.session_state:
    st.session_state.selected_period = 30
if 'forecast_data' not in st.session_state:
    st.session_state.forecast_data = None
if 'churn_predictions' not in st.session_state:
    st.session_state.churn_predictions = None

# Header
st.markdown('<h1 class="main-header">📊 Business Intelligence & ROI Dashboard</h1>', unsafe_allow_html=True)
try:
    render_share_inline("Shareable view link")
except Exception:
    pass

# Sidebar
with st.sidebar:
    st.header("📅 Time Period")
    # Share + reset controls
    try:
        render_share_block("Share BI Dashboard View")
    except Exception:
        pass
    if st.button("Reset View/Filters"):
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
        try:
            log_ux_event("st_filters_cleared", {"scope": "business_intelligence"})
        except Exception:
            pass
        st.rerun()
    
    period_options = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 365 days": 365,
        "Custom": 0
    }
    # Deep-link period selection
    params = get_params()
    qp_period = params.get('bi_period')
    options = list(period_options.keys())
    idx = options.index(qp_period) if qp_period in options else 1
    selected_period_text = st.selectbox("Select Period", options, index=idx)

    if selected_period_text == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_default = params.get('bi_start')
            start_date = st.date_input(
                "Start Date",
                value=(date.fromisoformat(start_default) if start_default else date.today() - timedelta(days=30))
            )
        with col2:
            end_default = params.get('bi_end')
            end_date = st.date_input(
                "End Date",
                value=(date.fromisoformat(end_default) if end_default else date.today())
            )
    else:
        days = period_options[selected_period_text]
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

    # Sync to URL
    try:
        update_params({
            'bi_period': selected_period_text,
            'bi_start': start_date.isoformat() if selected_period_text == 'Custom' else None,
            'bi_end': end_date.isoformat() if selected_period_text == 'Custom' else None,
        })
    except Exception:
        pass
    
    st.markdown("---")
    # Quick section selector synced to bi_tab
    _labels = {k: v for k, v in _tab_map}
    _keys = [k for k, _ in _tab_map]
    _sel_idx = _keys.index(_current) if _current in _keys else 0
    _sel = st.selectbox("Section", options=_keys, index=_sel_idx, format_func=lambda k: _labels[k])
    if _sel != _current:
        try:
            update_params({'bi_tab': _sel})
        except Exception:
            pass
        st.experimental_rerun()

    st.markdown("---")

    st.header("🎯 Quick Actions")
    if st.button("📈 Generate Forecast"):
        st.session_state.generate_forecast = True
    if st.button("🔍 Predict Churn"):
        st.session_state.predict_churn = True
    if st.button("💰 Calculate ROI"):
        st.session_state.calculate_roi = True
    if st.button("📊 Export Report"):
        st.info("Generating comprehensive report...")

# Main dashboard tabs
# Deep-linked tabs via bi_tab (exec|revenue|users|pred|ops)
_tab_map = [
    ("exec", "Executive Overview"),
    ("revenue", "Revenue & ROI"),
    ("users", "User Analytics"),
    ("pred", "Predictions"),
    ("ops", "Opportunities"),
]
_current = get_params().get('bi_tab', 'exec')
_ordered = [x for x in _tab_map if x[0] == _current] + [x for x in _tab_map if x[0] != _current]
_labels = [label for _, label in _ordered]
_tabs = st.tabs(_labels)
_key_to_tab = {k: _tabs[i] for i, (k, _) in enumerate(_ordered)}

with _key_to_tab["exec"]:
    st.header("🎯 Executive Overview")
    
    # Mock data for demonstration
    current_mrr = 125000
    last_mrr = 110000
    mrr_growth = ((current_mrr - last_mrr) / last_mrr) * 100
    
    active_users = 1250
    last_active = 1150
    user_growth = ((active_users - last_active) / last_active) * 100
    
    churn_rate = 4.5
    last_churn = 5.2
    
    ltv_cac_ratio = 3.2
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <h4>Monthly Recurring Revenue</h4>
            <h2 style="color: #3b82f6;">${:,.0f}</h2>
            <p style="color: {};">{}% {} MoM</p>
        </div>
        """.format(
            current_mrr,
            "green" if mrr_growth > 0 else "red",
            abs(mrr_growth),
            "↑" if mrr_growth > 0 else "↓"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <h4>Active Users</h4>
            <h2 style="color: #8b5cf6;">{:,}</h2>
            <p style="color: {};">{}% {} MoM</p>
        </div>
        """.format(
            active_users,
            "green" if user_growth > 0 else "red",
            abs(user_growth),
            "↑" if user_growth > 0 else "↓"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <h4>Churn Rate</h4>
            <h2 style="color: {};">{}%</h2>
            <p style="color: {};">{}% from last month</p>
        </div>
        """.format(
            "#ef4444" if churn_rate > 5 else "#10b981",
            churn_rate,
            "green" if churn_rate < last_churn else "red",
            abs(churn_rate - last_churn)
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <h4>LTV:CAC Ratio</h4>
            <h2 style="color: {};">{}x</h2>
            <p>{}</p>
        </div>
        """.format(
            "#10b981" if ltv_cac_ratio > 3 else "#f59e0b" if ltv_cac_ratio > 1 else "#ef4444",
            ltv_cac_ratio,
            "Healthy" if ltv_cac_ratio > 3 else "Needs Improvement"
        ), unsafe_allow_html=True)
    
    # Health scores
    st.subheader("🏥 Business Health Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    health_scores = {
        "Revenue Health": 85,
        "User Health": 78,
        "Product Health": 82,
        "Financial Health": 79
    }
    
    for col, (metric, score) in zip([col1, col2, col3, col4], health_scores.items()):
        with col:
            health_class = (
                "health-excellent" if score >= 85 else
                "health-good" if score >= 70 else
                "health-fair" if score >= 50 else
                "health-poor"
            )
            st.markdown(f"""
            <div style="text-align: center;">
                <h5>{metric}</h5>
                <div class="health-score {health_class}">{score}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Trend charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Revenue Trend")
        sph = st.container()
        with sph:
            try:
                render_skeleton_list(items=2)
            except Exception:
                pass
        # Generate sample data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        revenue_data = pd.DataFrame({
            'Date': dates,
            'Revenue': np.cumsum(np.random.normal(4000, 1000, len(dates))) + 100000
        })
        
        fig = px.line(revenue_data, x='Date', y='Revenue', 
                     title="Daily Revenue Trend",
                     line_shape='spline')
        fig.update_traces(line_color='#3b82f6', line_width=3)
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
        sph.empty()
    
    with col2:
        st.subheader("👥 User Growth")
        sph2 = st.container()
        with sph2:
            try:
                render_skeleton_list(items=2)
            except Exception:
                pass
        user_data = pd.DataFrame({
            'Date': dates,
            'Users': np.cumsum(np.random.poisson(5, len(dates))) + 1000
        })
        
        fig = px.area(user_data, x='Date', y='Users',
                      title="Active Users Over Time")
        fig.update_traces(fillcolor='rgba(139, 92, 246, 0.3)', line_color='#8b5cf6')
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
        sph2.empty()

with _key_to_tab["revenue"]:
    st.header("💰 Revenue & ROI Analysis")
    
    # ROI Calculator
    st.subheader("📊 ROI Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Investment Breakdown**")
        acquisition_cost = st.number_input("Customer Acquisition", value=50000, step=1000)
        operational_cost = st.number_input("Operational Costs", value=30000, step=1000)
        marketing_cost = st.number_input("Marketing Spend", value=20000, step=1000)
        infrastructure_cost = st.number_input("Infrastructure", value=15000, step=1000)
        
        total_investment = acquisition_cost + operational_cost + marketing_cost + infrastructure_cost
        st.metric("Total Investment", f"${total_investment:,.0f}")
    
    with col2:
        st.markdown("**Revenue Streams**")
        subscription_revenue = st.number_input("Subscription Revenue", value=150000, step=1000)
        transaction_revenue = st.number_input("Transaction Revenue", value=30000, step=1000)
        addon_revenue = st.number_input("Add-on Revenue", value=10000, step=1000)
        
        total_revenue = subscription_revenue + transaction_revenue + addon_revenue
        st.metric("Total Revenue", f"${total_revenue:,.0f}")
    
    # ROI Calculation
    if st.button("Calculate ROI", type="primary"):
        profit = total_revenue - total_investment
        roi_percentage = (profit / total_investment * 100) if total_investment > 0 else 0
        payback_period = total_investment / (total_revenue / 12) if total_revenue > 0 else float('inf')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Profit", f"${profit:,.0f}", 
                     f"{'+' if profit > 0 else ''}{profit/total_investment*100:.1f}%")
        with col2:
            st.metric("ROI", f"{roi_percentage:.1f}%",
                     "Positive" if roi_percentage > 0 else "Negative")
        with col3:
            st.metric("Payback Period", 
                     f"{payback_period:.1f} months" if payback_period != float('inf') else "Never")
        with col4:
            ltv = 2000  # Mock LTV
            cac = acquisition_cost / 100 if acquisition_cost > 0 else 500
            st.metric("LTV:CAC", f"{ltv/cac:.1f}x")
    
    # Revenue breakdown
    st.subheader("💵 Revenue Breakdown")
    
    revenue_breakdown = pd.DataFrame({
        'Source': ['Subscriptions', 'Transactions', 'Add-ons', 'Other'],
        'Amount': [120000, 30000, 10000, 5000],
        'Percentage': [72.7, 18.2, 6.1, 3.0]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        sph3 = st.container()
        with sph3:
            try:
                render_skeleton_list(items=2)
            except Exception:
                pass
        fig = px.pie(revenue_breakdown, values='Amount', names='Source',
                    title="Revenue by Source",
                    color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        sph3.empty()
    
    with col2:
        sph4 = st.container()
        with sph4:
            try:
                render_skeleton_list(items=2)
            except Exception:
                pass
        fig = px.bar(revenue_breakdown, x='Source', y='Amount',
                    title="Revenue Comparison",
                    color='Amount',
                    color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)
        sph4.empty()

with _key_to_tab["users"]:
    st.header("👥 User Analytics")
    
    # User segments
    st.subheader("🎯 User Segmentation")
    
    segments = pd.DataFrame({
        'Segment': ['Power Users', 'Regular Users', 'Occasional', 'At Risk', 'Churned'],
        'Count': [150, 450, 300, 200, 150],
        'Revenue': [45000, 60000, 25000, 15000, 0],
        'Avg_LTV': [2500, 1500, 800, 500, 0]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        sph5 = st.container()
        with sph5:
            try:
                render_skeleton_list(items=2)
            except Exception:
                pass
        fig = px.funnel(segments, y='Segment', x='Count',
                       title="User Funnel",
                       color='Count',
                       color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig, use_container_width=True)
        sph5.empty()
    
    with col2:
        sph6 = st.container()
        with sph6:
            try:
                render_skeleton_list(items=2)
            except Exception:
                pass
        fig = px.scatter(segments, x='Count', y='Revenue',
                        size='Avg_LTV', color='Segment',
                        title="Segment Value Analysis",
                        hover_data=['Avg_LTV'])
        st.plotly_chart(fig, use_container_width=True)
        sph6.empty()
    
    # Cohort analysis
    st.subheader("📅 Cohort Retention")
    
    # Mock cohort data
    cohorts = pd.DataFrame({
        'Cohort': ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024'],
        'Month 0': [100, 100, 100, 100],
        'Month 1': [85, 82, 88, 90],
        'Month 2': [72, 70, 75, 78],
        'Month 3': [65, 63, 68, None],
        'Month 4': [58, 56, None, None],
        'Month 5': [52, None, None, None]
    })
    
    sph7 = st.container()
    with sph7:
        try:
            render_skeleton_list(items=2)
        except Exception:
            pass
    fig = go.Figure()
    
    for col in cohorts.columns[1:]:
        fig.add_trace(go.Scatter(
            x=cohorts['Cohort'],
            y=cohorts[col],
            mode='lines+markers',
            name=col,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title="Cohort Retention Analysis",
        xaxis_title="Cohort",
        yaxis_title="Retention %",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    sph7.empty()
    
    # User activity heatmap
    st.subheader("🔥 User Activity Heatmap")
    
    # Generate mock activity data
    hours = list(range(24))
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    activity_data = np.random.randint(10, 100, size=(7, 24))
    
    sph8 = st.container()
    with sph8:
        try:
            render_skeleton_list(items=2)
        except Exception:
            pass
    fig = px.imshow(activity_data,
                   labels=dict(x="Hour of Day", y="Day of Week", color="Activity"),
                   x=hours,
                   y=days,
                   color_continuous_scale="Viridis",
                   title="Weekly Activity Pattern")
    st.plotly_chart(fig, use_container_width=True)
    sph8.empty()

with _key_to_tab["pred"]:
    st.header("🔮 Predictions & Forecasting")
    
    # Revenue forecast
    st.subheader("📈 Revenue Forecast")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_months = st.slider("Forecast Horizon (months)", 3, 24, 12)
    with col2:
        include_seasonality = st.checkbox("Include Seasonality", value=True)
    with col3:
        scenario = st.selectbox("Scenario", ["Most Likely", "Best Case", "Worst Case"])
    
    if st.button("Generate Forecast", type="primary"):
        sphp = st.container()
        with sphp:
            try:
                render_skeleton_list(items=3)
            except Exception:
                pass
        # Generate mock forecast data
        future_dates = pd.date_range(start=date.today(), periods=forecast_months, freq='M')
        
        base_revenue = 125000
        growth_rate = 0.05 if scenario == "Most Likely" else 0.10 if scenario == "Best Case" else 0.02
        
        forecast_data = []
        for i, d in enumerate(future_dates):
            seasonal_factor = 1.0
            if include_seasonality:
                month = d.month
                if month in [11, 12]:  # Q4 boost
                    seasonal_factor = 1.2
                elif month in [1, 2]:  # Q1 dip
                    seasonal_factor = 0.9
            
            revenue = base_revenue * (1 + growth_rate) ** i * seasonal_factor
            confidence_lower = revenue * 0.85
            confidence_upper = revenue * 1.15
            
            forecast_data.append({
                'Date': d,
                'Predicted': revenue,
                'Lower_Bound': confidence_lower,
                'Upper_Bound': confidence_upper
            })
        
        forecast_df = pd.DataFrame(forecast_data)
        
        fig = go.Figure()
        
        # Add predicted line
        fig.add_trace(go.Scatter(
            x=forecast_df['Date'],
            y=forecast_df['Predicted'],
            mode='lines',
            name='Forecast',
            line=dict(color='#3b82f6', width=3)
        ))
        
        # Add confidence interval
        fig.add_trace(go.Scatter(
            x=forecast_df['Date'].tolist() + forecast_df['Date'].tolist()[::-1],
            y=forecast_df['Upper_Bound'].tolist() + forecast_df['Lower_Bound'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(59, 130, 246, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False
        ))
        
        fig.update_layout(
            title=f"Revenue Forecast - {scenario}",
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        sphp.empty()
        
        # Forecast summary
        total_forecasted = forecast_df['Predicted'].sum()
        avg_monthly = forecast_df['Predicted'].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Forecasted Revenue", f"${total_forecasted:,.0f}")
        with col2:
            st.metric("Average Monthly Revenue", f"${avg_monthly:,.0f}")
        with col3:
            st.metric("Expected Growth", f"{(growth_rate * 100):.1f}% MoM")
    
    # Churn prediction
    st.subheader("🚨 Churn Risk Analysis")
    
    if st.button("Analyze Churn Risk", type="secondary"):
        # Mock churn predictions
        churn_data = pd.DataFrame({
            'User_ID': range(1, 21),
            'Churn_Probability': np.random.uniform(0.1, 0.95, 20),
            'Days_Since_Login': np.random.randint(1, 60, 20),
            'Revenue_At_Risk': np.random.uniform(50, 500, 20)
        })
        
        churn_data['Risk_Level'] = pd.cut(
            churn_data['Churn_Probability'],
            bins=[0, 0.3, 0.7, 1.0],
            labels=['Low', 'Medium', 'High']
        )
        
        # Risk summary
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk = churn_data[churn_data['Risk_Level'] == 'High']
        medium_risk = churn_data[churn_data['Risk_Level'] == 'Medium']
        low_risk = churn_data[churn_data['Risk_Level'] == 'Low']
        
        with col1:
            st.metric("High Risk Users", len(high_risk),
                     f"${high_risk['Revenue_At_Risk'].sum():,.0f} at risk")
        with col2:
            st.metric("Medium Risk Users", len(medium_risk),
                     f"${medium_risk['Revenue_At_Risk'].sum():,.0f} at risk")
        with col3:
            st.metric("Low Risk Users", len(low_risk))
        with col4:
            avg_churn_prob = churn_data['Churn_Probability'].mean()
            st.metric("Avg Churn Probability", f"{avg_churn_prob:.1%}")
        
        # Churn risk distribution
        fig = px.scatter(churn_data, x='Days_Since_Login', y='Churn_Probability',
                        size='Revenue_At_Risk', color='Risk_Level',
                        title="Churn Risk Distribution",
                        color_discrete_map={'High': '#ef4444', 'Medium': '#f59e0b', 'Low': '#10b981'})
        st.plotly_chart(fig, use_container_width=True)
        
        # At-risk users table
        st.markdown("**High Risk Users Requiring Immediate Attention:**")
        high_risk_display = high_risk[['User_ID', 'Churn_Probability', 'Days_Since_Login', 'Revenue_At_Risk']]
        high_risk_display.columns = ['User ID', 'Churn Risk', 'Days Inactive', 'Revenue at Risk']
        st.dataframe(high_risk_display, use_container_width=True)

with _key_to_tab["ops"]:
    st.header("💡 Growth Opportunities")
    
    # Opportunity cards
    st.subheader("🚀 Identified Opportunities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="opportunity-card">
            <h3>📈 Upsell Opportunities</h3>
            <p><strong>23 users</strong> ready for plan upgrade</p>
            <p>Potential Revenue: <strong>$12,500/month</strong></p>
            <p>Success Probability: <strong>72%</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="opportunity-card">
            <h3>🔄 Win-Back Campaign</h3>
            <p><strong>45 churned users</strong> with high win-back potential</p>
            <p>Potential Recovery: <strong>$8,200/month</strong></p>
            <p>Recommended: <strong>20% discount offer</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="opportunity-card">
            <h3>🎯 Cross-Sell Products</h3>
            <p><strong>67 users</strong> likely to purchase add-ons</p>
            <p>Potential Revenue: <strong>$5,400/month</strong></p>
            <p>Top Product: <strong>Advanced Analytics</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="opportunity-card">
            <h3>🌍 Market Expansion</h3>
            <p><strong>European market</strong> shows high demand</p>
            <p>Market Size: <strong>$2.5M TAM</strong></p>
            <p>Entry Strategy: <strong>Localized pricing</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Optimization suggestions
    st.subheader("⚡ Optimization Recommendations")
    
    recommendations = [
        {
            "area": "Pricing",
            "recommendation": "Implement usage-based pricing tier",
            "impact": "High",
            "effort": "Medium",
            "potential_value": "$15,000/month"
        },
        {
            "area": "Product",
            "recommendation": "Launch mobile app features",
            "impact": "High",
            "effort": "High",
            "potential_value": "$25,000/month"
        },
        {
            "area": "Marketing",
            "recommendation": "Referral program implementation",
            "impact": "Medium",
            "effort": "Low",
            "potential_value": "$8,000/month"
        },
        {
            "area": "Operations",
            "recommendation": "Automate onboarding process",
            "impact": "Medium",
            "effort": "Medium",
            "potential_value": "Save $5,000/month"
        }
    ]
    
    recommendations_df = pd.DataFrame(recommendations)
    
    # Impact vs Effort matrix
    sph9 = st.container()
    with sph9:
        try:
            render_skeleton_list(items=2)
        except Exception:
            pass
    fig = px.scatter(recommendations_df, x='effort', y='impact',
                    size='potential_value',
                    hover_data=['recommendation', 'potential_value'],
                    text='area',
                    title="Impact vs Effort Matrix",
                    color='area')
    
    # Add quadrant lines
    fig.add_hline(y="Medium", line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x="Medium", line_dash="dash", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)
    sph9.empty()
    
    # Recommendations table
    st.markdown("**Detailed Recommendations:**")
    st.dataframe(recommendations_df, use_container_width=True)
    
    # Action plan
    if st.button("Generate Action Plan", type="primary"):
        st.success("✅ Action plan generated!")
        
        action_plan = """
        ### 30-Day Action Plan
        
        **Week 1: Quick Wins**
        - Launch referral program (Low effort, Medium impact)
        - Start upsell campaign for identified users
        - Implement basic automation for onboarding
        
        **Week 2-3: Medium-term Initiatives**
        - Design and test usage-based pricing model
        - Prepare win-back campaign materials
        - Begin mobile app feature development
        
        **Week 4: Execution & Monitoring**
        - Roll out new pricing to test segment
        - Launch win-back campaign
        - Monitor metrics and adjust strategies
        
        **Expected Outcomes:**
        - Revenue increase: $35,000-$50,000/month
        - Churn reduction: 2-3%
        - User satisfaction: +15 NPS points
        """
        
        st.markdown(action_plan)
        
        if st.button("📥 Export Action Plan"):
            st.download_button(
                "Download Plan",
                action_plan,
                "action_plan.md",
                "text/markdown"
            )

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
with col2:
    st.caption("Business Intelligence Dashboard v1.0")
with col3:
    st.caption("Powered by Advanced Analytics & ML")
