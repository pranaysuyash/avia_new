"""
Data Analytics and Business Intelligence UI
Streamlit interface for customer lifetime value, churn prediction, usage analytics, 
competitive analysis, and predictive analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
from data_analytics_business_intelligence import DataAnalyticsBI, CustomerSegment, FeatureAdoptionStage

def init_analytics_system():
    """Initialize the analytics system"""
    if 'analytics_system' not in st.session_state:
        st.session_state.analytics_system = DataAnalyticsBI()
    return st.session_state.analytics_system

def render_customer_lifetime_value():
    """Render customer lifetime value analysis"""
    st.header("💰 Customer Lifetime Value Analysis")
    
    analytics = init_analytics_system()
    
    # Individual CLV Analysis
    st.subheader("Individual Customer Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input("User ID", placeholder="user1")
        
    with col2:
        if st.button("Calculate CLV"):
            if user_id:
                clv = analytics.calculate_customer_ltv(user_id)
                if clv:
                    st.success(f"✅ CLV calculated for {user_id}")
                    
                    # Display CLV metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Current CLV", f"${clv.current_clv:.2f}")
                    with col2:
                        st.metric("Predicted CLV", f"${clv.predicted_clv:.2f}")
                    with col3:
                        st.metric("Customer Segment", clv.segment.value.replace('_', ' ').title())
                    with col4:
                        st.metric("Churn Risk", f"{clv.churn_probability:.1%}")
                    
                    # CLV Details
                    st.subheader("CLV Details")
                    clv_data = {
                        "Metric": ["Total Revenue", "Acquisition Cost", "Subscription Months", 
                                 "Engagement Score", "Last Activity"],
                        "Value": [f"${clv.total_revenue:.2f}", f"${clv.acquisition_cost:.2f}",
                                f"{clv.subscription_months} months", f"{clv.engagement_score:.1f}/100",
                                clv.last_activity.strftime("%Y-%m-%d")]
                    }
                    st.table(pd.DataFrame(clv_data))
                else:
                    st.error("User not found or insufficient data")
            else:
                st.error("Please enter a User ID")
    
    # Cohort Analysis
    st.subheader("📊 CLV Cohort Analysis")
    
    cohort_period = st.selectbox("Cohort Period", ["monthly", "quarterly"], index=0)
    
    if st.button("Generate Cohort Analysis"):
        try:
            cohort_data = analytics.get_clv_cohort_analysis(cohort_period)
            
            if not cohort_data.empty:
                st.dataframe(cohort_data, use_container_width=True)
                
                # Visualize cohort CLV trends
                fig = px.line(
                    x=cohort_data.index.astype(str), 
                    y=cohort_data['avg_clv'],
                    title="Average CLV by Cohort",
                    labels={'x': 'Cohort', 'y': 'Average CLV ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # CLV distribution
                fig2 = px.bar(
                    x=cohort_data.index.astype(str),
                    y=cohort_data['total_clv'],
                    title="Total CLV by Cohort",
                    labels={'x': 'Cohort', 'y': 'Total CLV ($)'}
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("No cohort data available")
        except Exception as e:
            st.error(f"Error generating cohort analysis: {str(e)}")

def render_churn_prediction():
    """Render churn prediction and retention analytics"""
    st.header("🚨 Churn Prediction & Retention Analytics")
    
    analytics = init_analytics_system()
    
    # Model Training Section
    st.subheader("🤖 Churn Prediction Model")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Train Churn Model"):
            with st.spinner("Training churn prediction model..."):
                results = analytics.train_churn_prediction_model()
                
                if "accuracy" in results:
                    st.success(f"✅ Model trained successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Model Accuracy", f"{results['accuracy']:.1%}")
                    with col2:
                        st.metric("Training Samples", results['samples'])
                    with col3:
                        st.metric("Status", "Ready")
                    
                    # Feature importance
                    if "feature_importance" in results:
                        st.subheader("Feature Importance")
                        importance_df = pd.DataFrame(
                            list(results['feature_importance'].items()),
                            columns=['Feature', 'Importance']
                        ).sort_values('Importance', ascending=True)
                        
                        fig = px.bar(
                            importance_df, 
                            x='Importance', 
                            y='Feature',
                            orientation='h',
                            title="Churn Prediction Feature Importance"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Failed to train model - insufficient data")
    
    with col2:
        st.info("💡 **Model Features:**\n"
               "- Revenue patterns\n"
               "- Usage frequency\n"
               "- Support interactions\n"
               "- Engagement metrics\n"
               "- Account age")
    
    # Individual Churn Prediction
    st.subheader("Individual Churn Risk Assessment")
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input("User ID for Churn Analysis", placeholder="user3")
    
    with col2:
        if st.button("Analyze Churn Risk"):
            if user_id:
                churn_report = analytics.generate_churn_prediction_report(user_id)
                
                # Risk level color coding
                risk_colors = {"low": "green", "medium": "orange", "high": "red"}
                risk_color = risk_colors.get(churn_report.risk_level, "gray")
                
                st.markdown(f"### Churn Risk: <span style='color:{risk_color}'>{churn_report.risk_level.upper()}</span>", 
                           unsafe_allow_html=True)
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Churn Probability", f"{churn_report.churn_probability:.1%}")
                with col2:
                    st.metric("Risk Level", churn_report.risk_level.title())
                with col3:
                    st.metric("Confidence", f"{churn_report.prediction_confidence:.1%}")
                with col4:
                    st.metric("Days to Churn", f"{churn_report.days_to_predicted_churn}")
                
                # Key factors and recommendations
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔍 Key Risk Factors")
                    if churn_report.key_factors:
                        for factor in churn_report.key_factors:
                            st.write(f"• {factor}")
                    else:
                        st.write("No specific risk factors identified")
                
                with col2:
                    st.subheader("💡 Recommended Actions")
                    if churn_report.recommended_actions:
                        for action in churn_report.recommended_actions:
                            st.write(f"• {action}")
                    else:
                        st.write("Continue monitoring customer health")
            else:
                st.error("Please enter a User ID")

def render_feature_adoption():
    """Render product usage analytics and feature adoption"""
    st.header("📈 Feature Adoption & Usage Analytics")
    
    analytics = init_analytics_system()
    
    # Track Feature Usage
    st.subheader("Track Feature Usage")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        user_id = st.text_input("User ID", placeholder="user1", key="feature_user")
    with col2:
        feature_name = st.selectbox("Feature", 
                                  ["transcription", "translation", "speaker_diarization", 
                                   "export", "sharing", "analytics"])
    with col3:
        session_duration = st.number_input("Session Duration (seconds)", min_value=0, value=300)
    
    if st.button("Track Usage"):
        if user_id and feature_name:
            analytics.track_feature_usage(user_id, feature_name, session_duration)
            st.success(f"✅ Tracked {feature_name} usage for {user_id}")
        else:
            st.error("Please fill in all fields")
    
    # Feature Adoption Analytics
    st.subheader("📊 Feature Adoption Overview")
    
    if st.button("Generate Feature Analytics"):
        features = analytics.get_feature_adoption_analytics()
        
        if features:
            # Create feature adoption summary
            feature_data = []
            for feature in features:
                feature_data.append({
                    "Feature": feature.feature_name,
                    "Total Users": feature.total_users,
                    "Active Users": feature.active_users,
                    "Adoption Rate": f"{feature.adoption_rate:.1f}%",
                    "Retention Rate": f"{feature.retention_rate:.1f}%",
                    "Avg Usage": f"{feature.avg_usage_frequency:.1f}",
                    "Satisfaction": f"{feature.user_satisfaction:.1f}/5.0"
                })
            
            df = pd.DataFrame(feature_data)
            st.dataframe(df, use_container_width=True)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Adoption rate chart
                fig1 = px.bar(
                    df, 
                    x='Feature', 
                    y='Adoption Rate',
                    title="Feature Adoption Rates",
                    color='Adoption Rate',
                    color_continuous_scale='viridis'
                )
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # User satisfaction chart
                fig2 = px.scatter(
                    df,
                    x='Total Users',
                    y='Satisfaction',
                    size='Active Users',
                    color='Feature',
                    title="Feature Usage vs Satisfaction",
                    hover_data=['Adoption Rate']
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Feature adoption stages
            st.subheader("Feature Adoption Stages")
            
            # Create adoption funnel data
            stage_data = []
            for feature in features:
                for stage, count in feature.stage_distribution.items():
                    stage_data.append({
                        "Feature": feature.feature_name,
                        "Stage": stage.replace('_', ' ').title(),
                        "Users": count
                    })
            
            if stage_data:
                stage_df = pd.DataFrame(stage_data)
                
                # Stacked bar chart for adoption stages
                fig3 = px.bar(
                    stage_df,
                    x='Feature',
                    y='Users',
                    color='Stage',
                    title="Feature Adoption Stages Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig3.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("No feature adoption data available")

def render_competitive_analysis():
    """Render competitive analysis and market research"""
    st.header("🏆 Competitive Analysis & Market Research")
    
    analytics = init_analytics_system()
    
    # Add Competitive Benchmark
    st.subheader("Add Competitive Benchmark")
    
    with st.expander("Add New Benchmark", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            metric_name = st.text_input("Metric Name", placeholder="transcription_accuracy")
            our_value = st.number_input("Our Value", min_value=0.0, value=95.0)
            competitor_name = st.text_input("Competitor Name", placeholder="Competitor A")
        
        with col2:
            competitor_value = st.number_input("Competitor Value", min_value=0.0, value=90.0)
            market_average = st.number_input("Market Average", min_value=0.0, value=88.0)
            source = st.text_input("Source", placeholder="Industry Report 2024")
        
        if st.button("Add Benchmark"):
            if metric_name and competitor_name:
                analytics.add_competitive_benchmark(
                    metric_name, our_value, competitor_name, 
                    competitor_value, market_average, source
                )
                st.success(f"✅ Added benchmark for {metric_name}")
            else:
                st.error("Please fill in metric name and competitor name")
    
    # Competitive Analysis Dashboard
    st.subheader("📊 Competitive Analysis Dashboard")
    
    if st.button("Generate Competitive Analysis"):
        metrics = analytics.get_competitive_analysis()
        
        if metrics:
            # Create competitive metrics summary
            comp_data = []
            for metric in metrics:
                comp_data.append({
                    "Metric": metric.metric_name.replace('_', ' ').title(),
                    "Our Value": f"{metric.our_value:.2f}",
                    "Competitor Avg": f"{metric.competitor_avg:.2f}",
                    "Market Leader": f"{metric.market_leader:.2f}",
                    "Percentile Rank": f"{metric.percentile_rank:.1f}%",
                    "Trend": metric.trend_direction.title(),
                    "Last Updated": metric.benchmark_date.strftime("%Y-%m-%d")
                })
            
            df = pd.DataFrame(comp_data)
            st.dataframe(df, use_container_width=True)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Competitive positioning radar chart
                categories = [metric.metric_name.replace('_', ' ').title() for metric in metrics]
                our_values = [metric.our_value for metric in metrics]
                competitor_values = [metric.competitor_avg for metric in metrics]
                
                fig1 = go.Figure()
                
                fig1.add_trace(go.Scatterpolar(
                    r=our_values,
                    theta=categories,
                    fill='toself',
                    name='Our Performance',
                    line_color='blue'
                ))
                
                fig1.add_trace(go.Scatterpolar(
                    r=competitor_values,
                    theta=categories,
                    fill='toself',
                    name='Competitor Average',
                    line_color='red'
                ))
                
                fig1.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, max(max(our_values), max(competitor_values)) * 1.1])
                    ),
                    title="Competitive Positioning Radar",
                    showlegend=True
                )
                
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Market position chart
                percentile_ranks = [metric.percentile_rank for metric in metrics]
                
                fig2 = px.bar(
                    x=categories,
                    y=percentile_ranks,
                    title="Market Position by Metric",
                    labels={'x': 'Metrics', 'y': 'Percentile Rank (%)'},
                    color=percentile_ranks,
                    color_continuous_scale='RdYlGn'
                )
                fig2.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Trend analysis
            st.subheader("📈 Trend Analysis")
            trend_counts = {}
            for metric in metrics:
                trend_counts[metric.trend_direction] = trend_counts.get(metric.trend_direction, 0) + 1
            
            if trend_counts:
                fig3 = px.pie(
                    values=list(trend_counts.values()),
                    names=list(trend_counts.keys()),
                    title="Performance Trend Distribution"
                )
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("No competitive analysis data available")

def render_predictive_analytics():
    """Render predictive analytics for business growth"""
    st.header("🔮 Predictive Analytics & Business Growth")
    
    analytics = init_analytics_system()
    
    # Growth Prediction Models
    st.subheader("🤖 Growth Prediction Models")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Train Revenue Model"):
            with st.spinner("Training revenue prediction model..."):
                results = analytics.train_growth_prediction_model("revenue")
                if "error" not in results:
                    st.success(f"✅ Revenue model trained!")
                    st.metric("Model MSE", f"{results['mse']:.2f}")
                else:
                    st.error(results["error"])
    
    with col2:
        if st.button("Train User Growth Model"):
            with st.spinner("Training user growth model..."):
                results = analytics.train_growth_prediction_model("users")
                if "error" not in results:
                    st.success(f"✅ User growth model trained!")
                    st.metric("Model MSE", f"{results['mse']:.2f}")
                else:
                    st.error(results["error"])
    
    with col3:
        if st.button("Train Usage Model"):
            with st.spinner("Training usage prediction model..."):
                results = analytics.train_growth_prediction_model("usage")
                if "error" not in results:
                    st.success(f"✅ Usage model trained!")
                    st.metric("Model MSE", f"{results['mse']:.2f}")
                else:
                    st.error(results["error"])
    
    # Growth Predictions
    st.subheader("📈 Business Growth Predictions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metric_type = st.selectbox("Metric to Predict", ["revenue", "users", "usage"])
        days_ahead = st.slider("Prediction Period (days)", 7, 90, 30)
    
    with col2:
        if st.button("Generate Prediction"):
            prediction = analytics.predict_business_growth(metric_type, days_ahead)
            
            st.subheader(f"{metric_type.title()} Prediction")
            
            # Prediction metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Value", f"{prediction.current_value:.2f}")
            with col2:
                st.metric("Predicted Value", f"{prediction.predicted_value:.2f}")
            with col3:
                st.metric("Growth Rate", f"{prediction.growth_rate:.1f}%")
            with col4:
                confidence_range = prediction.confidence_interval[1] - prediction.confidence_interval[0]
                st.metric("Confidence Range", f"±{confidence_range/2:.2f}")
            
            # Prediction visualization
            dates = pd.date_range(start=datetime.now(), periods=days_ahead+1, freq='D')
            
            # Simple linear interpolation for visualization
            current_val = prediction.current_value
            predicted_val = prediction.predicted_value
            values = np.linspace(current_val, predicted_val, len(dates))
            
            # Confidence intervals
            conf_lower = np.linspace(prediction.confidence_interval[0], 
                                   prediction.confidence_interval[0], len(dates))
            conf_upper = np.linspace(prediction.confidence_interval[1], 
                                   prediction.confidence_interval[1], len(dates))
            
            fig = go.Figure()
            
            # Predicted values
            fig.add_trace(go.Scatter(
                x=dates, y=values,
                mode='lines',
                name='Predicted Values',
                line=dict(color='blue', width=3)
            ))
            
            # Confidence interval
            fig.add_trace(go.Scatter(
                x=dates, y=conf_upper,
                mode='lines',
                line=dict(width=0),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=dates, y=conf_lower,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.2)',
                name='Confidence Interval',
                showlegend=True
            ))
            
            # Current point
            fig.add_trace(go.Scatter(
                x=[dates[0]], y=[current_val],
                mode='markers',
                marker=dict(size=10, color='red'),
                name='Current Value'
            ))
            
            fig.update_layout(
                title=f"{metric_type.title()} Prediction - {days_ahead} Days",
                xaxis_title="Date",
                yaxis_title=f"{metric_type.title()} Value",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key drivers
            st.subheader("🔑 Key Growth Drivers")
            for driver in prediction.key_drivers:
                st.write(f"• {driver}")

def render_analytics_summary():
    """Render comprehensive analytics summary dashboard"""
    st.header("📊 Analytics Summary Dashboard")
    
    analytics = init_analytics_system()
    
    if st.button("Generate Analytics Summary"):
        summary = analytics.get_analytics_summary()
        
        # Customer Metrics
        st.subheader("👥 Customer Metrics")
        if summary.get("customer_metrics"):
            customer_metrics = summary["customer_metrics"]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Customers", customer_metrics.get("total_customers", 0))
            with col2:
                st.metric("Active Customers", customer_metrics.get("active_customers", 0))
            with col3:
                st.metric("Avg Revenue/Customer", f"${customer_metrics.get('avg_revenue_per_customer', 0):.2f}")
            with col4:
                st.metric("Avg Engagement", f"{customer_metrics.get('avg_engagement_score', 0):.1f}/100")
        
        # Usage Metrics
        st.subheader("📱 Usage Metrics (Last 30 Days)")
        if summary.get("usage_metrics"):
            usage_metrics = summary["usage_metrics"]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Usage Events", usage_metrics.get("total_usage_events", 0))
            with col2:
                st.metric("Active Users", usage_metrics.get("active_users", 0))
            with col3:
                st.metric("Avg Session Duration", f"{usage_metrics.get('avg_session_duration', 0):.0f}s")
            with col4:
                st.metric("Features Used", usage_metrics.get("features_used", 0))
        
        # Revenue Metrics
        st.subheader("💰 Revenue Metrics (Last 30 Days)")
        if summary.get("revenue_metrics"):
            revenue_metrics = summary["revenue_metrics"]
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Revenue", f"${revenue_metrics.get('total_revenue', 0):.2f}")
            with col2:
                st.metric("Avg Transaction", f"${revenue_metrics.get('avg_transaction', 0):.2f}")
            with col3:
                st.metric("Total Transactions", revenue_metrics.get("total_transactions", 0))
        
        # Generation timestamp
        st.caption(f"Generated at: {summary.get('generated_at', 'Unknown')}")

def main():
    """Main data analytics and business intelligence UI"""
    st.set_page_config(
        page_title="Data Analytics & Business Intelligence",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Data Analytics & Business Intelligence")
    st.markdown("Comprehensive analytics for customer insights, churn prediction, and business growth")
    
    # Initialize sample data
    analytics = init_analytics_system()
    
    # Add sample data button
    if st.sidebar.button("🔄 Initialize Sample Data"):
        with st.spinner("Adding sample data..."):
            analytics.add_sample_data()
            st.sidebar.success("✅ Sample data added!")
    
    # Sidebar navigation
    st.sidebar.title("Analytics Modules")
    page = st.sidebar.selectbox("Choose an analysis", [
        "Analytics Summary",
        "Customer Lifetime Value",
        "Churn Prediction",
        "Feature Adoption",
        "Competitive Analysis",
        "Predictive Analytics"
    ])
    
    # Render selected page
    if page == "Analytics Summary":
        render_analytics_summary()
    elif page == "Customer Lifetime Value":
        render_customer_lifetime_value()
    elif page == "Churn Prediction":
        render_churn_prediction()
    elif page == "Feature Adoption":
        render_feature_adoption()
    elif page == "Competitive Analysis":
        render_competitive_analysis()
    elif page == "Predictive Analytics":
        render_predictive_analytics()
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Use the sample data to explore all analytics features!")

if __name__ == "__main__":
    main()