#!/usr/bin/env python3
"""
Business Intelligence Advisor UI - Streamlit Interface
Strategic business insights and recommendations dashboard

Intent-First Transformation: From technical analytics to strategic decision support
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from business_intelligence_advisor import BusinessIntelligenceAdvisor, BusinessPriority, DecisionUrgency

# Page configuration
st.set_page_config(
    page_title="Business Intelligence Advisor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .insight-card {
        border-left: 4px solid #ff6b6b;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .opportunity-card {
        border-left: 4px solid #4ecdc4;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f0fff4;
        border-radius: 5px;
    }
    .action-card {
        border-left: 4px solid #45b7d1;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f0f8ff;
        border-radius: 5px;
    }
    .critical-alert {
        background-color: #ffe6e6;
        border: 2px solid #ff4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-metric {
        background-color: #e6ffe6;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'advisor' not in st.session_state:
        st.session_state.advisor = BusinessIntelligenceAdvisor()
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'sample_data_loaded' not in st.session_state:
        st.session_state.sample_data_loaded = False

def load_sample_data():
    """Load sample business data for demonstration"""
    return {
        "content_performance": {
            "views": 75000,
            "engagement_rate": 0.72,
            "conversion_rate": 0.12,
            "production_cost": 8000,
            "revenue_generated": 45000
        },
        "user_behavior": {
            "avg_session_duration": 180,
            "bounce_rate": 0.35,
            "conversion_funnel": {
                "landing": 1.0,
                "signup": 0.75,
                "trial": 0.45,
                "purchase": 0.18
            },
            "feature_adoption": {
                "basic_features": 0.85,
                "advanced_features": 0.42
            }
        },
        "performance_metrics": {
            "user_acquisition_cost": 65,
            "customer_lifetime_value": 220,
            "churn_rate": 0.14,
            "feature_adoption_rate": 0.42
        },
        "user_segments": {
            "enterprise": {
                "size": 2500,
                "avg_revenue_per_user": 650,
                "growth_rate": 0.28
            },
            "small_business": {
                "size": 8000,
                "avg_revenue_per_user": 120,
                "growth_rate": 0.18
            },
            "individual": {
                "size": 15000,
                "avg_revenue_per_user": 45,
                "growth_rate": 0.22
            }
        }
    }

def display_executive_dashboard(results):
    """Display executive summary dashboard"""
    st.header("🎯 Executive Dashboard")
    
    summary = results["executive_summary"]
    stats = results["insights_summary"]
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Business Health</h3>
            <h2>{summary['business_health_score']:.1f}/1.0</h2>
            <p>Overall Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Potential Value</h3>
            <h2>${stats['estimated_total_value']:,.0f}</h2>
            <p>Revenue Impact</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Critical Issues</h3>
            <h2>{stats['critical_count']}</h2>
            <p>Immediate Action</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Growth Opportunities</h3>
            <h2>{stats['growth_opportunities_count']}</h2>
            <p>Identified</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Key findings
    st.subheader("📊 Key Findings")
    for finding in summary["key_findings"]:
        st.write(f"• {finding}")
    
    # Top priorities
    st.subheader("🎯 Top Priorities")
    for i, priority in enumerate(summary["top_priorities"], 1):
        st.write(f"{i}. **{priority}**")

def display_critical_insights(results):
    """Display critical business insights"""
    st.header("🚨 Critical Insights")
    
    critical_insights = results["critical_insights"]
    high_priority_insights = results["high_priority_insights"]
    
    if critical_insights:
        st.subheader("⚠️ Immediate Action Required")
        for insight in critical_insights:
            st.markdown(f"""
            <div class="critical-alert">
                <h4>🚨 {insight['title']}</h4>
                <p><strong>Impact:</strong> ${insight['potential_value']:,.0f}</p>
                <p><strong>Description:</strong> {insight['description']}</p>
                <p><strong>Timeline:</strong> {insight['timeline']}</p>
                <p><strong>Owner:</strong> {', '.join(insight['stakeholders'][:2])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Recommended Actions"):
                for i, action in enumerate(insight['recommended_actions'], 1):
                    st.write(f"{i}. {action}")
            
            with st.expander("Success Metrics"):
                for metric in insight['success_metrics']:
                    st.markdown(f'<div class="success-metric">✓ {metric}</div>', unsafe_allow_html=True)
    
    if high_priority_insights:
        st.subheader("🔥 High Priority Items")
        for insight in high_priority_insights:
            st.markdown(f"""
            <div class="insight-card">
                <h4>{insight['title']}</h4>
                <p>{insight['description']}</p>
                <p><strong>Potential Value:</strong> ${insight['potential_value']:,.0f}</p>
                <p><strong>Timeline:</strong> {insight['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)

def display_growth_opportunities(results):
    """Display growth opportunities"""
    st.header("🚀 Growth Opportunities")
    
    opportunities = results["growth_opportunities"]
    
    if opportunities:
        # Create opportunity comparison chart
        opp_data = []
        for opp in opportunities:
            opp_data.append({
                'Opportunity': opp['title'],
                'Revenue Potential': opp['revenue_potential'],
                'ROI Estimate': opp['roi_estimate'],
                'Success Probability': opp['success_probability'] * 100,
                'Investment Required': opp['investment_required']
            })
        
        df_opp = pd.DataFrame(opp_data)
        
        # ROI vs Investment scatter plot
        fig = px.scatter(df_opp, 
                        x='Investment Required', 
                        y='Revenue Potential',
                        size='Success Probability',
                        color='ROI Estimate',
                        hover_name='Opportunity',
                        title="Growth Opportunities: Investment vs Revenue Potential",
                        labels={'Success Probability': 'Success Probability (%)'})
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display opportunity cards
        for opp in opportunities:
            st.markdown(f"""
            <div class="opportunity-card">
                <h4>💰 {opp['title']}</h4>
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <p><strong>Revenue Potential:</strong> ${opp['revenue_potential']:,.0f}</p>
                        <p><strong>ROI Estimate:</strong> {opp['roi_estimate']:.1f}x</p>
                    </div>
                    <div>
                        <p><strong>Investment:</strong> ${opp['investment_required']:,.0f}</p>
                        <p><strong>Success Rate:</strong> {opp['success_probability']:.0%}</p>
                    </div>
                </div>
                <p><strong>Time to Market:</strong> {opp['time_to_market']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"Implementation Plan - {opp['title']}"):
                for i, step in enumerate(opp['implementation_steps'], 1):
                    st.write(f"{i}. {step}")

def display_strategic_recommendations(results):
    """Display strategic recommendations"""
    st.header("🎯 Strategic Recommendations")
    
    recommendations = results["strategic_recommendations"]
    
    if recommendations:
        for rec in recommendations:
            st.markdown(f"""
            <div class="action-card">
                <h4>📈 {rec['title']}</h4>
                <p><strong>Category:</strong> {rec['category'].title()}</p>
                <p><strong>Expected Outcome:</strong> {rec['expected_outcome']}</p>
                <p><strong>Budget Required:</strong> ${rec['resource_requirements']['budget']:,.0f}</p>
                <p><strong>Timeline:</strong> {rec['resource_requirements']['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Implementation Plan")
                for phase in rec['implementation_plan']:
                    st.write(f"**{phase['phase'].title()}** ({phase['timeline']})")
                    for action in phase['actions']:
                        st.write(f"  • {action}")
            
            with col2:
                st.subheader("Success Criteria")
                for criteria in rec['success_criteria']:
                    st.markdown(f'<div class="success-metric">✓ {criteria}</div>', unsafe_allow_html=True)

def display_next_actions(results):
    """Display prioritized next actions"""
    st.header("📋 Next Actions")
    
    actions = results["next_actions"]
    
    if actions:
        # Create action priority chart
        action_data = []
        for action in actions:
            priority_score = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(action['priority'], 1)
            action_data.append({
                'Action': action['action'][:50] + "..." if len(action['action']) > 50 else action['action'],
                'Priority Score': priority_score,
                'Potential Value': action['potential_value'],
                'Owner': action['owner']
            })
        
        df_actions = pd.DataFrame(action_data)
        
        fig = px.bar(df_actions, 
                    x='Priority Score', 
                    y='Action',
                    color='Potential Value',
                    orientation='h',
                    title="Action Priority Matrix",
                    color_continuous_scale='Viridis')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display action list
        st.subheader("🎯 Prioritized Action Items")
        for action in actions:
            priority_color = {
                "critical": "#ff4444",
                "high": "#ff8800", 
                "medium": "#ffaa00",
                "low": "#00aa00"
            }.get(action['priority'], "#666666")
            
            st.markdown(f"""
            <div style="border-left: 4px solid {priority_color}; padding: 1rem; margin: 0.5rem 0; background-color: #f8f9fa;">
                <h5>#{action['rank']} {action['action']}</h5>
                <p><strong>From:</strong> {action['insight_title']}</p>
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>Priority:</strong> {action['priority'].upper()}</span>
                    <span><strong>Value:</strong> ${action['potential_value']:,.0f}</span>
                    <span><strong>Owner:</strong> {action['owner']}</span>
                </div>
                <p><strong>Timeline:</strong> {action['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)

def display_performance_analytics(business_data):
    """Display performance analytics charts"""
    st.header("📊 Performance Analytics")
    
    # Conversion funnel chart
    if 'user_behavior' in business_data and 'conversion_funnel' in business_data['user_behavior']:
        funnel_data = business_data['user_behavior']['conversion_funnel']
        
        fig = go.Figure(go.Funnel(
            y = list(funnel_data.keys()),
            x = list(funnel_data.values()),
            textinfo = "value+percent initial"
        ))
        
        fig.update_layout(title="Conversion Funnel Analysis")
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics comparison
    if 'performance_metrics' in business_data:
        metrics = business_data['performance_metrics']
        
        # Market benchmarks (mock data)
        benchmarks = {
            "user_acquisition_cost": {"our_value": metrics.get('user_acquisition_cost', 0), "market_avg": 50, "best_in_class": 30},
            "customer_lifetime_value": {"our_value": metrics.get('customer_lifetime_value', 0), "market_avg": 200, "best_in_class": 350},
            "churn_rate": {"our_value": metrics.get('churn_rate', 0), "market_avg": 0.15, "best_in_class": 0.08},
            "feature_adoption_rate": {"our_value": metrics.get('feature_adoption_rate', 0), "market_avg": 0.4, "best_in_class": 0.65}
        }
        
        # Create comparison chart
        metric_names = []
        our_values = []
        market_avgs = []
        best_in_class = []
        
        for metric, data in benchmarks.items():
            metric_names.append(metric.replace('_', ' ').title())
            our_values.append(data['our_value'])
            market_avgs.append(data['market_avg'])
            best_in_class.append(data['best_in_class'])
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Our Performance', x=metric_names, y=our_values))
        fig.add_trace(go.Bar(name='Market Average', x=metric_names, y=market_avgs))
        fig.add_trace(go.Bar(name='Best in Class', x=metric_names, y=best_in_class))
        
        fig.update_layout(
            title="Performance vs Market Benchmarks",
            barmode='group',
            yaxis_title="Value"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.title("🎯 Business Intelligence Advisor")
    st.markdown("**Transform analytics into strategic business insights and actionable recommendations**")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Data input options
        data_source = st.selectbox(
            "Data Source",
            ["Sample Data", "Upload JSON", "Manual Input"]
        )
        
        if data_source == "Sample Data":
            if st.button("Load Sample Data"):
                st.session_state.sample_data_loaded = True
                st.success("Sample data loaded!")
        
        elif data_source == "Upload JSON":
            uploaded_file = st.file_uploader("Upload business data JSON", type=['json'])
            if uploaded_file:
                try:
                    business_data = json.load(uploaded_file)
                    st.session_state.business_data = business_data
                    st.success("Data uploaded successfully!")
                except Exception as e:
                    st.error(f"Error loading file: {e}")
        
        # Analysis controls
        st.header("📊 Analysis Controls")
        
        if st.button("🚀 Generate Strategic Insights", type="primary"):
            if st.session_state.sample_data_loaded or 'business_data' in st.session_state:
                with st.spinner("Analyzing business data and generating insights..."):
                    business_data = load_sample_data() if st.session_state.sample_data_loaded else st.session_state.business_data
                    results = st.session_state.advisor.generate_strategic_insights(business_data)
                    st.session_state.analysis_results = results
                    st.session_state.business_data = business_data
                st.success("Analysis complete!")
            else:
                st.error("Please load data first!")
        
        # Export options
        if st.session_state.analysis_results:
            st.header("💾 Export")
            if st.button("Download Report"):
                report_json = json.dumps(st.session_state.analysis_results, indent=2, default=str)
                st.download_button(
                    label="📄 Download JSON Report",
                    data=report_json,
                    file_name=f"business_intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    # Main content
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        business_data = st.session_state.business_data
        
        # Navigation tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Executive Dashboard", 
            "🚨 Critical Insights", 
            "🚀 Growth Opportunities",
            "🎯 Strategic Recommendations",
            "📋 Next Actions",
            "📈 Performance Analytics"
        ])
        
        with tab1:
            display_executive_dashboard(results)
        
        with tab2:
            display_critical_insights(results)
        
        with tab3:
            display_growth_opportunities(results)
        
        with tab4:
            display_strategic_recommendations(results)
        
        with tab5:
            display_next_actions(results)
        
        with tab6:
            display_performance_analytics(business_data)
        
        # Footer with summary
        st.markdown("---")
        st.subheader("📈 Analysis Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Insights", results["insights_summary"]["total_insights"])
        
        with col2:
            st.metric("Potential Value", f"${results['insights_summary']['estimated_total_value']:,.0f}")
        
        with col3:
            st.metric("Processing Time", f"{results['insights_summary']['processing_time']:.2f}s")
    
    else:
        # Welcome screen
        st.markdown("""
        ## 🎯 Welcome to Business Intelligence Advisor
        
        Transform your business analytics into strategic insights and actionable recommendations.
        
        ### 🚀 Key Features:
        - **Strategic Insights**: Convert technical metrics into business intelligence
        - **Growth Opportunities**: Identify and prioritize revenue opportunities  
        - **Performance Alerts**: Get notified of critical issues requiring attention
        - **Action Prioritization**: Receive prioritized next steps with clear ownership
        - **Executive Dashboards**: High-level summaries for leadership decisions
        
        ### 📊 What You'll Get:
        - Business health scoring and trend analysis
        - Competitive positioning insights
        - Revenue optimization recommendations
        - User experience improvement strategies
        - Market opportunity identification
        
        **Get started by loading sample data or uploading your business metrics!**
        """)
        
        # Sample data preview
        if st.button("👀 Preview Sample Data Structure"):
            sample_data = load_sample_data()
            st.json(sample_data)

if __name__ == "__main__":
    main()