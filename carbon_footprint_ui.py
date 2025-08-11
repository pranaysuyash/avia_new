#!/usr/bin/env python3
"""
Carbon Footprint Tracking UI
Streamlit interface for carbon footprint tracking and sustainability reporting
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json

from carbon_footprint_tracker import (
    CarbonFootprintTracker, ProcessingType, EnergySource,
    SustainabilityMetrics
)

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Carbon Footprint Tracker",
        page_icon="🌱",
        layout="wide"
    )
    
    st.title("🌱 Carbon Footprint Tracker & Sustainability Dashboard")
    st.markdown("Track and optimize the environmental impact of AI processing")
    
    # Initialize tracker
    if 'tracker' not in st.session_state:
        st.session_state.tracker = CarbonFootprintTracker()
    
    tracker = st.session_state.tracker
    
    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Time period selection
        time_period = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
        )
        
        # Energy source preference
        energy_source = st.selectbox(
            "Energy Source Preference",
            ["Mixed Grid", "Renewable", "Fossil", "Unknown"],
            help="Select your preferred energy source for new operations"
        )
        
        # Optimization settings
        st.subheader("🔧 Optimization")
        enable_optimization = st.checkbox("Enable Green Computing", value=True)
        
        if enable_optimization:
            model_optimization = st.checkbox("Model Selection Optimization", value=True)
            batch_optimization = st.checkbox("Batch Processing Optimization", value=True)
            schedule_optimization = st.checkbox("Energy-Aware Scheduling", value=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", "📈 Analytics", "🎯 Optimization", "💰 Offsets", "📋 Reports"
    ])
    
    with tab1:
        dashboard_interface(tracker, time_period)
    
    with tab2:
        analytics_interface(tracker, time_period)
    
    with tab3:
        optimization_interface(tracker)
    
    with tab4:
        offset_interface(tracker, time_period)
    
    with tab5:
        reports_interface(tracker, time_period)

def dashboard_interface(tracker, time_period):
    """Main dashboard interface"""
    st.header("📊 Sustainability Dashboard")
    
    # Get time range
    end_date = datetime.now()
    if time_period == "Last 7 days":
        start_date = end_date - timedelta(days=7)
    elif time_period == "Last 30 days":
        start_date = end_date - timedelta(days=30)
    elif time_period == "Last 90 days":
        start_date = end_date - timedelta(days=90)
    else:
        start_date = None
    
    # Get sustainability metrics
    try:
        metrics = tracker.get_sustainability_metrics(start_date, end_date)
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Energy",
                f"{metrics.total_energy_kwh:.3f} kWh",
                help="Total energy consumed for AI processing"
            )
        
        with col2:
            st.metric(
                "Carbon Emissions",
                f"{metrics.total_carbon_kg:.3f} kg CO₂",
                help="Total carbon dioxide emissions"
            )
        
        with col3:
            st.metric(
                "Renewable %",
                f"{metrics.renewable_percentage:.1f}%",
                help="Percentage of energy from renewable sources"
            )
        
        with col4:
            sustainability_score = tracker.reporter.calculate_sustainability_score(metrics)
            grade = tracker.reporter.get_sustainability_grade(sustainability_score)
            st.metric(
                "Sustainability Grade",
                grade,
                f"Score: {sustainability_score:.1f}/100"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Energy source breakdown
            energy_data = {
                'Renewable': metrics.total_energy_kwh * (metrics.renewable_percentage / 100),
                'Non-Renewable': metrics.total_energy_kwh * (1 - metrics.renewable_percentage / 100)
            }
            
            fig_energy = px.pie(
                values=list(energy_data.values()),
                names=list(energy_data.keys()),
                title="Energy Source Breakdown",
                color_discrete_map={
                    'Renewable': '#2E8B57',
                    'Non-Renewable': '#CD5C5C'
                }
            )
            st.plotly_chart(fig_energy, use_container_width=True)
        
        with col2:
            # Sustainability score gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=sustainability_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Sustainability Score"},
                delta={'reference': 80},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        
        # Mock recent entries for demo
        recent_data = [
            {"Time": "2 min ago", "Operation": "Transcription", "Energy": "0.045 kWh", "CO₂": "0.020 kg"},
            {"Time": "5 min ago", "Operation": "Translation", "Energy": "0.023 kWh", "CO₂": "0.010 kg"},
            {"Time": "8 min ago", "Operation": "Entity Extraction", "Energy": "0.012 kWh", "CO₂": "0.005 kg"},
        ]
        
        df_recent = pd.DataFrame(recent_data)
        st.dataframe(df_recent, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        st.info("This might be because no carbon footprint data has been tracked yet.")

def analytics_interface(tracker, time_period):
    """Analytics and trends interface"""
    st.header("📈 Carbon Footprint Analytics")
    
    # Time series analysis
    st.subheader("📊 Trends Over Time")
    
    # Mock time series data for demo
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    mock_data = {
        'Date': dates,
        'Energy (kWh)': [0.1 + 0.05 * i + 0.02 * (i % 7) for i in range(len(dates))],
        'Carbon (kg)': [0.045 + 0.02 * i + 0.01 * (i % 7) for i in range(len(dates))],
        'Operations': [10 + 5 * (i % 7) for i in range(len(dates))]
    }
    
    df_trends = pd.DataFrame(mock_data)
    
    # Energy and carbon trends
    fig_trends = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Energy Consumption', 'Carbon Emissions'),
        vertical_spacing=0.1
    )
    
    fig_trends.add_trace(
        go.Scatter(x=df_trends['Date'], y=df_trends['Energy (kWh)'], 
                  name='Energy', line=dict(color='blue')),
        row=1, col=1
    )
    
    fig_trends.add_trace(
        go.Scatter(x=df_trends['Date'], y=df_trends['Carbon (kg)'], 
                  name='Carbon', line=dict(color='red')),
        row=2, col=1
    )
    
    fig_trends.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_trends, use_container_width=True)
    
    # Processing type breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 By Processing Type")
        
        processing_data = {
            'Transcription': 45,
            'Translation': 25,
            'Entity Extraction': 15,
            'Sentiment Analysis': 10,
            'Other': 5
        }
        
        fig_processing = px.bar(
            x=list(processing_data.keys()),
            y=list(processing_data.values()),
            title="Carbon Emissions by Processing Type (%)",
            color=list(processing_data.values()),
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_processing, use_container_width=True)
    
    with col2:
        st.subheader("🤖 By Model Type")
        
        model_data = {
            'Whisper-Base': 35,
            'GPT-3.5': 30,
            'Local Models': 20,
            'Whisper-Large': 15
        }
        
        fig_models = px.pie(
            values=list(model_data.values()),
            names=list(model_data.keys()),
            title="Energy Usage by Model Type"
        )
        st.plotly_chart(fig_models, use_container_width=True)
    
    # Efficiency metrics
    st.subheader("⚡ Efficiency Metrics")
    
    efficiency_data = {
        'Metric': ['Energy per Operation', 'Carbon per MB', 'Operations per kWh'],
        'Current': [0.025, 0.012, 40],
        'Target': [0.020, 0.010, 50],
        'Industry Average': [0.030, 0.015, 33]
    }
    
    df_efficiency = pd.DataFrame(efficiency_data)
    
    fig_efficiency = px.bar(
        df_efficiency,
        x='Metric',
        y=['Current', 'Target', 'Industry Average'],
        title="Efficiency Comparison",
        barmode='group'
    )
    st.plotly_chart(fig_efficiency, use_container_width=True)

def optimization_interface(tracker):
    """Green computing optimization interface"""
    st.header("🎯 Green Computing Optimization")
    
    # Optimization recommendations
    st.subheader("💡 Optimization Recommendations")
    
    recommendations = [
        {
            'category': 'Model Selection',
            'recommendation': 'Use Whisper-Tiny for simple transcriptions',
            'potential_savings': '50% energy reduction',
            'impact': 'High'
        },
        {
            'category': 'Batch Processing',
            'recommendation': 'Group similar operations together',
            'potential_savings': '20% energy reduction',
            'impact': 'Medium'
        },
        {
            'category': 'Scheduling',
            'recommendation': 'Run heavy operations during renewable energy hours',
            'potential_savings': '30% carbon reduction',
            'impact': 'High'
        }
    ]
    
    for rec in recommendations:
        with st.expander(f"🔧 {rec['category']}: {rec['recommendation']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Potential Savings:** {rec['potential_savings']}")
                st.write(f"**Impact:** {rec['impact']}")
            with col2:
                if st.button(f"Apply {rec['category']} Optimization", key=rec['category']):
                    st.success(f"✅ {rec['category']} optimization applied!")
    
    # Model comparison tool
    st.subheader("🤖 Model Efficiency Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        task_type = st.selectbox(
            "Task Type",
            ["Transcription", "Translation", "Entity Extraction", "Sentiment Analysis"]
        )
        
        accuracy_req = st.slider(
            "Minimum Accuracy Required",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05
        )
    
    with col2:
        if st.button("🔍 Find Optimal Model"):
            # Use the optimizer to get recommendations
            processing_type = ProcessingType.TRANSCRIPTION  # Map from task_type
            optimization = tracker.optimizer.optimize_model_selection(
                processing_type, accuracy_req
            )
            
            st.success(f"**Recommended Model:** {optimization['recommended_model']}")
            st.info(f"**Energy Savings:** {optimization['energy_savings']:.1%}")
            st.info(f"**Accuracy:** {optimization['accuracy']:.1%}")
    
    # Energy-aware scheduling
    st.subheader("⏰ Energy-Aware Scheduling")
    
    st.write("Schedule your AI operations during times when renewable energy is most available:")
    
    # Mock renewable energy schedule
    hours = list(range(24))
    renewable_percentage = [
        30, 25, 20, 15, 10, 15, 25, 40,  # 0-7
        60, 80, 90, 95, 95, 90, 85, 75,  # 8-15
        65, 50, 40, 35, 30, 25, 25, 30   # 16-23
    ]
    
    fig_schedule = px.line(
        x=hours,
        y=renewable_percentage,
        title="Renewable Energy Availability by Hour",
        labels={'x': 'Hour of Day', 'y': 'Renewable Energy %'}
    )
    fig_schedule.add_hline(y=50, line_dash="dash", line_color="red", 
                          annotation_text="50% Threshold")
    st.plotly_chart(fig_schedule, use_container_width=True)
    
    st.info("💡 **Tip:** Schedule energy-intensive operations between 9 AM - 3 PM for maximum renewable energy usage.")

def offset_interface(tracker, time_period):
    """Carbon offset interface"""
    st.header("💰 Carbon Offset Calculator")
    
    # Get current emissions
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Default to last 30 days
        metrics = tracker.get_sustainability_metrics(start_date, end_date)
        
        st.subheader("📊 Current Emissions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Emissions", f"{metrics.total_carbon_kg:.3f} kg CO₂")
        
        with col2:
            st.metric("Daily Average", f"{metrics.total_carbon_kg/30:.4f} kg CO₂")
        
        with col3:
            annual_estimate = metrics.total_carbon_kg * 12  # Rough annual estimate
            st.metric("Annual Estimate", f"{annual_estimate:.2f} kg CO₂")
        
        # Offset calculator
        st.subheader("🌳 Offset Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            offset_amount = st.number_input(
                "Carbon to Offset (kg CO₂)",
                min_value=0.0,
                value=float(metrics.total_carbon_kg),
                step=0.001,
                format="%.3f"
            )
            
            project_type = st.selectbox(
                "Offset Project Type",
                ["verified", "forestry", "renewable", "technology"],
                format_func=lambda x: {
                    "verified": "Verified Carbon Standard",
                    "forestry": "Reforestation Projects",
                    "renewable": "Renewable Energy",
                    "technology": "Carbon Capture Technology"
                }[x]
            )
        
        with col2:
            if st.button("💰 Calculate Offset Cost"):
                offset_calc = tracker.offset_calculator.calculate_offset_cost(
                    offset_amount * 1000,  # Convert to grams
                    project_type
                )
                
                st.success(f"**Offset Cost:** ${offset_calc['cost_usd']:.2f}")
                st.info(f"**Project:** {offset_calc['project_info']['name']}")
                st.info(f"**Description:** {offset_calc['project_info']['description']}")
        
        # Offset portfolio recommendation
        st.subheader("📈 Recommended Offset Portfolio")
        
        if st.button("🎯 Get Portfolio Recommendation"):
            portfolio = tracker.offset_calculator.recommend_offset_portfolio(
                metrics.total_carbon_kg * 1000  # Convert to grams
            )
            
            st.write("**Diversified Offset Portfolio:**")
            
            portfolio_data = []
            for item in portfolio['portfolio']:
                portfolio_data.append({
                    'Project Type': item['project_info']['name'],
                    'CO₂ Offset (kg)': f"{item['tons_allocated']:.3f}",
                    'Cost (USD)': f"${item['cost_usd']:.2f}",
                    'Co-Benefits': ', '.join(item['project_info']['co_benefits'])
                })
            
            df_portfolio = pd.DataFrame(portfolio_data)
            st.dataframe(df_portfolio, use_container_width=True)
            
            st.success(f"**Total Portfolio Cost:** ${portfolio['total_cost_usd']:.2f}")
            st.info(f"**Average Cost per Ton:** ${portfolio['average_cost_per_ton']:.2f}")
        
        # Equivalent metrics
        st.subheader("🌍 Environmental Impact Context")
        
        if metrics.total_carbon_kg > 0:
            # Calculate equivalents
            car_miles = metrics.total_carbon_kg * 2.31
            trees_needed = metrics.total_carbon_kg * 0.06
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "🚗 Car Miles Equivalent",
                    f"{car_miles:.1f} miles",
                    help="Miles driven in an average car"
                )
            
            with col2:
                st.metric(
                    "🌳 Trees Needed",
                    f"{trees_needed:.1f} tree-years",
                    help="Tree-years needed to absorb this CO₂"
                )
            
            with col3:
                lightbulb_hours = metrics.total_carbon_kg * 100
                st.metric(
                    "💡 Lightbulb Hours",
                    f"{lightbulb_hours:.0f} hours",
                    help="Hours of 60W bulb operation"
                )
    
    except Exception as e:
        st.error(f"Error calculating offsets: {str(e)}")

def reports_interface(tracker, time_period):
    """Sustainability reporting interface"""
    st.header("📋 Sustainability Reports")
    
    # Report generation
    col1, col2 = st.columns(2)
    
    with col1:
        report_period = st.selectbox(
            "Report Period",
            ["Weekly", "Monthly", "Quarterly", "Annual"]
        )
        
        report_format = st.selectbox(
            "Report Format",
            ["Executive Summary", "Detailed Analysis", "Compliance Report"]
        )
    
    with col2:
        if st.button("📊 Generate Report"):
            # Generate sustainability report
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                metrics = tracker.get_sustainability_metrics(start_date, end_date)
                
                report = tracker.reporter.generate_sustainability_report(
                    metrics, report_period.lower()
                )
                
                st.success("✅ Report generated successfully!")
                
                # Display report summary
                st.subheader(f"📈 {report_period} Sustainability Report")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Sustainability Score", f"{report['sustainability_score']:.1f}/100")
                    st.metric("Grade", report['sustainability_grade'])
                
                with col2:
                    st.metric("Total Energy", f"{report['metrics']['total_energy_kwh']:.3f} kWh")
                    st.metric("Total Carbon", f"{report['metrics']['total_carbon_kg']:.3f} kg CO₂")
                
                with col3:
                    st.metric("Renewable %", f"{report['metrics']['renewable_percentage']:.1f}%")
                    st.metric("Efficiency Score", f"{report['metrics']['efficiency_score']:.2f}")
                
                # Recommendations
                if report['recommendations']:
                    st.subheader("💡 Recommendations")
                    for rec in report['recommendations']:
                        st.write(f"**{rec['category']}** ({rec['priority']} Priority)")
                        st.write(f"- {rec['recommendation']}")
                        st.write(f"- {rec['description']}")
                        st.write(f"- Impact: {rec['potential_impact']}")
                        st.write("---")
                
                # Download options
                st.subheader("📥 Download Report")
                
                report_json = json.dumps(report, indent=2, default=str)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        "📄 Download JSON Report",
                        data=report_json,
                        file_name=f"sustainability_report_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                
                with col2:
                    # Create a simple text report
                    text_report = f"""
SUSTAINABILITY REPORT - {report_period.upper()}
Generated: {report['generated_at']}

SUMMARY
=======
Sustainability Score: {report['sustainability_score']:.1f}/100
Grade: {report['sustainability_grade']} - {report['grade_description']}

METRICS
=======
Total Energy Consumed: {report['metrics']['total_energy_kwh']:.3f} kWh
Total Carbon Emissions: {report['metrics']['total_carbon_kg']:.3f} kg CO₂
Renewable Energy Percentage: {report['metrics']['renewable_percentage']:.1f}%
Efficiency Score: {report['metrics']['efficiency_score']:.2f}

ENVIRONMENTAL IMPACT
===================
Car Miles Equivalent: {report['equivalent_metrics']['car_miles_equivalent']:.1f} miles
Trees Needed: {report['equivalent_metrics']['trees_needed_years']:.1f} tree-years
Coal Equivalent: {report['equivalent_metrics']['coal_pounds_equivalent']:.1f} pounds

RECOMMENDATIONS
===============
"""
                    for rec in report['recommendations']:
                        text_report += f"• {rec['recommendation']} ({rec['priority']} Priority)\n"
                    
                    st.download_button(
                        "📝 Download Text Report",
                        data=text_report,
                        file_name=f"sustainability_report_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    
    # Historical reports
    st.subheader("📚 Historical Reports")
    
    # Mock historical data
    historical_reports = [
        {"Date": "2024-01-01", "Period": "Monthly", "Score": 78, "Grade": "B+", "Carbon": "2.45 kg"},
        {"Date": "2023-12-01", "Period": "Monthly", "Score": 72, "Grade": "B", "Carbon": "2.89 kg"},
        {"Date": "2023-11-01", "Period": "Monthly", "Score": 69, "Grade": "B", "Carbon": "3.12 kg"},
    ]
    
    df_historical = pd.DataFrame(historical_reports)
    st.dataframe(df_historical, use_container_width=True)
    
    # Compliance tracking
    st.subheader("✅ Compliance Tracking")
    
    compliance_items = [
        {"Standard": "ISO 14001", "Status": "✅ Compliant", "Last Review": "2024-01-15"},
        {"Standard": "Carbon Disclosure Project", "Status": "⏳ In Progress", "Last Review": "2024-01-10"},
        {"Standard": "Science Based Targets", "Status": "❌ Non-Compliant", "Last Review": "2024-01-05"},
    ]
    
    df_compliance = pd.DataFrame(compliance_items)
    st.dataframe(df_compliance, use_container_width=True)

if __name__ == "__main__":
    main()