#!/usr/bin/env python3
"""
Predictive Analytics UI
Streamlit interface for predictive analytics and forecasting
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event, get_params, update_params

from predictive_analytics import get_predictive_service, ForecastType, ModelType

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Predictive Analytics & Forecasting",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Predictive Analytics & Forecasting")
    st.markdown("AI-powered predictive analytics for business intelligence and strategic planning")
    # Inline share UI
    try:
        render_share_inline("Shareable view link")
    except Exception:
        pass
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Analytics Modules")
        # Share + reset controls
        try:
            render_share_block("Share Predictive Analytics View")
        except Exception:
            pass
        if st.button("Reset View/Filters"):
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
            try:
                log_ux_event("st_filters_cleared", {"scope": "predictive_analytics"})
            except Exception:
                pass
            st.rerun()
        
        params = get_params()
        modules = [
            "Content Trends",
            "User Behavior",
            "Revenue Forecasting", 
            "Market Analysis",
            "Comprehensive Dashboard",
            "Model Performance"
        ]
        default_module = params.get('pa_module', modules[0])
        selected_module = st.selectbox(
            "Choose Analytics Module",
            modules,
            index=(modules.index(default_module) if default_module in modules else 0)
        )
        try:
            update_params({'pa_module': selected_module})
        except Exception:
            pass
        
        st.divider()
        
        # Global settings
        st.subheader("Forecast Settings")
        forecast_horizon = st.slider("Forecast Horizon (days)", 7, 365, 30)
        confidence_level = st.slider("Confidence Level", 0.8, 0.99, 0.95, 0.01)
        
        st.divider()
        
        # Model selection
        st.subheader("Model Selection")
        default_model = st.selectbox(
            "Default Model Type",
            ["Prophet", "ARIMA", "Random Forest", "Gradient Boosting"],
            help="Default model for time series forecasting"
        )
    
    # Main content based on selected module
    if selected_module == "Content Trends":
        content_trends_interface(forecast_horizon, default_model)
    elif selected_module == "User Behavior":
        user_behavior_interface(forecast_horizon)
    elif selected_module == "Revenue Forecasting":
        revenue_forecasting_interface(forecast_horizon)
    elif selected_module == "Market Analysis":
        market_analysis_interface()
    elif selected_module == "Comprehensive Dashboard":
        comprehensive_dashboard_interface(forecast_horizon)
    elif selected_module == "Model Performance":
        model_performance_interface()

def content_trends_interface(forecast_horizon: int, model_type: str):
    """Interface for content trend prediction"""
    st.header("📊 Content Trend Prediction")
    
    # Data input options
    data_input_method = st.radio(
        "Data Input Method",
        ["Upload CSV", "Generate Sample Data", "Connect Database"],
        horizontal=True
    )
    
    content_data = None
    
    if data_input_method == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload content metrics CSV",
            type=['csv'],
            help="CSV should contain columns: date, views, engagement_rate, duration_minutes"
        )
        
        if uploaded_file:
            content_data = pd.read_csv(uploaded_file)
            st.success(f"Loaded {len(content_data)} records")
            
            # Show data preview
            with st.expander("Data Preview"):
                st.dataframe(content_data.head())
    
    elif data_input_method == "Generate Sample Data":
        if st.button("Generate Sample Content Data"):
            content_data = generate_sample_content_data()
            st.success("Generated sample data")
            
            with st.expander("Sample Data Preview"):
                st.dataframe(content_data.head())
    
    if content_data is not None:
        # Model selection for this specific forecast
        col1, col2 = st.columns(2)
        
        with col1:
            selected_model = st.selectbox(
                "Model Type for This Forecast",
                ["Prophet", "ARIMA", "Random Forest", "Exponential Smoothing"],
                index=0 if model_type == "Prophet" else 1
            )
        
        with col2:
            include_confidence = st.checkbox("Include Confidence Intervals", value=True)
        
        if st.button("Generate Content Trend Forecast", type="primary"):
            with st.spinner("Generating forecast..."):
                service = get_predictive_service()
                
                # Map model name to enum
                model_map = {
                    "Prophet": ModelType.PROPHET,
                    "ARIMA": ModelType.ARIMA,
                    "Random Forest": ModelType.RANDOM_FOREST,
                    "Exponential Smoothing": ModelType.EXPONENTIAL_SMOOTHING
                }
                
                forecast_result = service.content_predictor.predict_content_trends(
                    content_data, forecast_horizon, model_map[selected_model]
                )
                
                # Display results
                display_forecast_results(forecast_result, "Content Views", include_confidence)
                
                # Show accuracy metrics
                if forecast_result.accuracy_metrics:
                    st.subheader("Model Performance")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("MAE", f"{forecast_result.accuracy_metrics.get('mae', 0):.2f}")
                    
                    with col2:
                        st.metric("RMSE", f"{forecast_result.accuracy_metrics.get('rmse', 0):.2f}")
                    
                    with col3:
                        if 'mape' in forecast_result.accuracy_metrics:
                            st.metric("MAPE", f"{forecast_result.accuracy_metrics['mape']:.1f}%")
                
                # Feature importance (if available)
                if forecast_result.feature_importance:
                    st.subheader("Feature Importance")
                    
                    importance_df = pd.DataFrame(
                        list(forecast_result.feature_importance.items()),
                        columns=['Feature', 'Importance']
                    ).sort_values('Importance', ascending=False)
                    
                    fig = px.bar(importance_df, x='Importance', y='Feature', orientation='h')
                    st.plotly_chart(fig, use_container_width=True)

def user_behavior_interface(forecast_horizon: int):
    """Interface for user behavior prediction"""
    st.header("👥 User Behavior Prediction")
    
    tab1, tab2 = st.tabs(["Engagement Forecasting", "Churn Prediction"])
    
    with tab1:
        st.subheader("User Engagement Forecasting")
        
        # Sample user engagement data
        if st.button("Generate Sample User Data"):
            user_data = generate_sample_user_data()
            
            service = get_predictive_service()
            engagement_forecast = service.user_predictor.predict_user_engagement(
                user_data, forecast_horizon
            )
            
            display_forecast_results(engagement_forecast, "Engagement Score", True)
    
    with tab2:
        st.subheader("Churn Prediction")
        
        # User features input
        st.write("Enter user characteristics for churn analysis:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_since_login = st.number_input("Days Since Last Login", 0, 365, 5)
            session_count = st.number_input("Total Sessions", 1, 1000, 50)
            avg_session_duration = st.number_input("Avg Session Duration (min)", 1, 120, 15)
        
        with col2:
            pages_viewed = st.number_input("Total Pages Viewed", 1, 10000, 200)
            actions_taken = st.number_input("Total Actions Taken", 0, 5000, 100)
            total_session_time = st.number_input("Total Session Time (hours)", 1, 1000, 25)
        
        if st.button("Predict Churn Risk"):
            # Create user features dataframe
            user_features = pd.DataFrame({
                'last_login': [datetime.now() - timedelta(days=days_since_login)],
                'session_count': [session_count],
                'total_session_time': [total_session_time * 60],  # Convert to minutes
                'pages_viewed': [pages_viewed],
                'actions_taken': [actions_taken]
            })
            
            service = get_predictive_service()
            churn_result = service.user_predictor.predict_user_churn(user_features)
            
            if 'error' not in churn_result:
                churn_prob = churn_result['churn_probabilities'][0]
                
                # Display churn probability
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Churn Probability", f"{churn_prob:.1%}")
                
                with col2:
                    risk_level = "High" if churn_prob > 0.7 else "Medium" if churn_prob > 0.3 else "Low"
                    st.metric("Risk Level", risk_level)
                
                with col3:
                    st.metric("Model Accuracy", f"{churn_result.get('model_accuracy', 0.85):.1%}")
                
                # Risk visualization
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = churn_prob * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Churn Risk %"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 30], 'color': "lightgreen"},
                            {'range': [30, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 70
                        }
                    }
                ))
                
                st.plotly_chart(fig, use_container_width=True)

def revenue_forecasting_interface(forecast_horizon: int):
    """Interface for revenue forecasting"""
    st.header("💰 Revenue Forecasting")
    
    # Revenue data input
    revenue_input_method = st.radio(
        "Revenue Data Input",
        ["Upload Historical Data", "Generate Sample Data"],
        horizontal=True
    )
    
    revenue_data = None
    
    if revenue_input_method == "Generate Sample Data":
        if st.button("Generate Sample Revenue Data"):
            revenue_data = generate_sample_revenue_data()
            st.success("Generated sample revenue data")
    
    elif revenue_input_method == "Upload Historical Data":
        uploaded_file = st.file_uploader(
            "Upload revenue CSV",
            type=['csv'],
            help="CSV should contain columns: date, revenue"
        )
        
        if uploaded_file:
            revenue_data = pd.read_csv(uploaded_file)
    
    if revenue_data is not None:
        # Forecast settings
        col1, col2 = st.columns(2)
        
        with col1:
            forecast_months = st.slider("Forecast Months", 1, 24, 12)
        
        with col2:
            include_scenarios = st.checkbox("Include Scenario Analysis", value=True)
        
        if st.button("Generate Revenue Forecast", type="primary"):
            with st.spinner("Generating revenue forecast..."):
                service = get_predictive_service()
                
                revenue_forecast = service.revenue_forecaster.forecast_revenue(
                    revenue_data, forecast_months, include_scenarios
                )
                
                if 'error' not in revenue_forecast:
                    # Display base forecast
                    base_forecast = revenue_forecast['base_forecast']
                    display_forecast_results(base_forecast, "Revenue ($)", True)
                    
                    # Scenario analysis
                    if include_scenarios and 'scenarios' in revenue_forecast:
                        st.subheader("Scenario Analysis")
                        
                        scenarios = revenue_forecast['scenarios']
                        scenario_df = pd.DataFrame(scenarios)
                        
                        # Scenario comparison chart
                        fig = go.Figure()
                        
                        for scenario_name, values in scenarios.items():
                            fig.add_trace(go.Scatter(
                                x=list(range(len(values))),
                                y=values,
                                mode='lines',
                                name=scenario_name.replace('_', ' ').title()
                            ))
                        
                        fig.update_layout(
                            title="Revenue Scenarios Comparison",
                            xaxis_title="Months",
                            yaxis_title="Revenue ($)",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Scenario summary
                        scenario_summary = {}
                        for name, values in scenarios.items():
                            scenario_summary[name.replace('_', ' ').title()] = {
                                'Total': f"${sum(values):,.0f}",
                                'Average Monthly': f"${np.mean(values):,.0f}",
                                'Growth Rate': f"{(values[-1] / values[0] - 1) * 100:.1f}%"
                            }
                        
                        st.subheader("Scenario Summary")
                        st.dataframe(pd.DataFrame(scenario_summary).T)

def market_analysis_interface():
    """Interface for market analysis"""
    st.header("🏪 Market Analysis")
    
    # Generate sample market data
    if st.button("Generate Sample Market Data"):
        market_data = generate_sample_market_data()
        
        service = get_predictive_service()
        market_analysis = service.market_analyzer.analyze_market_trends(market_data)
        
        if 'error' not in market_analysis:
            # Market size trend
            if 'market_size_trend' in market_analysis:
                st.subheader("Market Size Analysis")
                
                trend = market_analysis['market_size_trend']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Market Size", f"${trend.get('current_market_size', 0):,.0f}")
                
                with col2:
                    st.metric("YoY Growth", f"{trend.get('yoy_growth', 0):.1f}%")
                
                with col3:
                    st.metric("Trend", trend.get('trend', 'Unknown').title())
            
            # Growth rates
            if 'growth_rate' in market_analysis:
                st.subheader("Growth Rate Analysis")
                
                growth = market_analysis['growth_rate']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Monthly Growth", f"{growth.get('monthly_growth_rate', 0):.2f}%")
                
                with col2:
                    st.metric("Quarterly Growth", f"{growth.get('quarterly_growth_rate', 0):.2f}%")
                
                with col3:
                    st.metric("CAGR", f"{growth.get('compound_annual_growth_rate', 0):.2f}%")
            
            # Competitive landscape
            if 'competitive_landscape' in market_analysis:
                st.subheader("Competitive Landscape")
                
                comp = market_analysis['competitive_landscape']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Market Share", f"{comp.get('market_share', 0):.1f}%")
                    st.metric("Competitor Count", comp.get('competitor_count', 0))
                
                with col2:
                    st.metric("Market Concentration", comp.get('market_concentration', 'Unknown').title())
                    st.metric("Competitive Intensity", comp.get('competitive_intensity', 'Unknown').title())
            
            # Opportunities
            if 'opportunities' in market_analysis:
                st.subheader("Market Opportunities")
                
                opportunities = market_analysis['opportunities']
                
                for i, opp in enumerate(opportunities, 1):
                    with st.expander(f"Opportunity {i}: {opp['opportunity']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Potential Value:** ${opp['potential_value']:,}")
                            st.write(f"**Probability:** {opp['probability']:.0%}")
                        
                        with col2:
                            st.write(f"**Time to Market:** {opp['time_to_market']}")
                            st.write(f"**Investment Required:** ${opp['investment_required']:,}")

def comprehensive_dashboard_interface(forecast_horizon: int):
    """Comprehensive analytics dashboard"""
    st.header("🎯 Comprehensive Analytics Dashboard")
    
    if st.button("Generate Comprehensive Forecast", type="primary"):
        with st.spinner("Generating comprehensive analytics..."):
            # Generate sample data for all modules
            data_sources = {
                'content_data': generate_sample_content_data(),
                'user_data': generate_sample_user_data(),
                'revenue_data': generate_sample_revenue_data(),
                'market_data': generate_sample_market_data(),
                'user_features': generate_sample_user_features()
            }
            
            service = get_predictive_service()
            comprehensive_results = service.generate_comprehensive_forecast(
                data_sources, forecast_horizon
            )
            
            if 'error' not in comprehensive_results:
                # Executive Summary
                st.subheader("📋 Executive Summary")
                
                summary = comprehensive_results.get('summary', {})
                
                # Key insights
                if summary.get('key_insights'):
                    st.write("**Key Insights:**")
                    for insight in summary['key_insights']:
                        st.write(f"• {insight}")
                
                # Recommendations
                if summary.get('recommendations'):
                    st.write("**Recommendations:**")
                    for rec in summary['recommendations']:
                        st.write(f"• {rec}")
                
                # Risk factors
                if summary.get('risk_factors'):
                    st.write("**Risk Factors:**")
                    for risk in summary['risk_factors']:
                        st.write(f"• {risk}")
                
                # Opportunities
                if summary.get('opportunities'):
                    st.write("**Opportunities:**")
                    for opp in summary['opportunities']:
                        st.write(f"• {opp}")
                
                st.divider()
                
                # Individual forecasts
                forecasts = comprehensive_results.get('forecasts', {})
                
                # Create tabs for different forecasts
                if forecasts:
                    tabs = st.tabs(list(forecasts.keys()))
                    
                    for tab, (forecast_name, forecast_data) in zip(tabs, forecasts.items()):
                        with tab:
                            if hasattr(forecast_data, 'predictions'):
                                display_forecast_results(forecast_data, forecast_name.title(), True)
                            else:
                                st.json(forecast_data)

def model_performance_interface():
    """Interface for model performance analysis"""
    st.header("🎯 Model Performance Analysis")
    
    service = get_predictive_service()
    
    if st.button("Get Forecast Accuracy Metrics"):
        accuracy_data = service.get_forecast_accuracy()
        
        if 'error' not in accuracy_data and accuracy_data:
            st.subheader("Historical Forecast Accuracy")
            
            # Create accuracy dataframe
            accuracy_df = pd.DataFrame(accuracy_data).T
            accuracy_df.reset_index(inplace=True)
            accuracy_df.columns = ['Forecast Type', 'Average Accuracy', 'Forecast Count']
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(accuracy_df)
            
            with col2:
                # Accuracy chart
                fig = px.bar(
                    accuracy_df, 
                    x='Forecast Type', 
                    y='Average Accuracy',
                    title="Model Accuracy by Forecast Type"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical forecast data available yet. Generate some forecasts first!")

def display_forecast_results(forecast_result, metric_name: str, include_confidence: bool = True):
    """Display forecast results with charts"""
    if not hasattr(forecast_result, 'predictions') or not forecast_result.predictions:
        st.error("No forecast data available")
        return
    
    # Create forecast chart
    fig = go.Figure()
    
    # Add predictions
    x_values = forecast_result.dates if forecast_result.dates else list(range(len(forecast_result.predictions)))
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=forecast_result.predictions,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='blue', width=2)
    ))
    
    # Add confidence intervals if available
    if include_confidence and forecast_result.confidence_intervals:
        lower_bounds = [ci[0] for ci in forecast_result.confidence_intervals]
        upper_bounds = [ci[1] for ci in forecast_result.confidence_intervals]
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=upper_bounds,
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=lower_bounds,
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.2)',
            name='Confidence Interval',
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title=f"{metric_name} Forecast",
        xaxis_title="Time",
        yaxis_title=metric_name,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Forecast Points", len(forecast_result.predictions))
    
    with col2:
        st.metric("Average Value", f"{np.mean(forecast_result.predictions):.2f}")
    
    with col3:
        st.metric("Min Value", f"{min(forecast_result.predictions):.2f}")
    
    with col4:
        st.metric("Max Value", f"{max(forecast_result.predictions):.2f}")

# Sample data generation functions
def generate_sample_content_data() -> pd.DataFrame:
    """Generate sample content metrics data"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    
    # Generate realistic content metrics with trends and seasonality
    base_views = 1000
    trend = np.linspace(0, 500, len(dates))
    seasonal = 200 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
    noise = np.random.normal(0, 100, len(dates))
    
    views = base_views + trend + seasonal + noise
    views = np.maximum(views, 0)  # Ensure non-negative
    
    return pd.DataFrame({
        'date': dates,
        'views': views.astype(int),
        'engagement_rate': np.random.uniform(0.1, 0.8, len(dates)),
        'duration_minutes': np.random.uniform(2, 15, len(dates)),
        'topic': np.random.choice(['tech', 'business', 'lifestyle', 'education'], len(dates)),
        'sentiment_score': np.random.uniform(-1, 1, len(dates))
    })

def generate_sample_user_data() -> pd.DataFrame:
    """Generate sample user engagement data"""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    
    return pd.DataFrame({
        'date': dates,
        'session_duration': np.random.uniform(5, 45, len(dates)),
        'pages_viewed': np.random.poisson(8, len(dates)),
        'actions_taken': np.random.poisson(3, len(dates))
    })

def generate_sample_revenue_data() -> pd.DataFrame:
    """Generate sample revenue data"""
    dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='M')
    
    # Generate revenue with growth trend
    base_revenue = 50000
    growth_rate = 0.02  # 2% monthly growth
    revenues = []
    
    for i, date in enumerate(dates):
        revenue = base_revenue * (1 + growth_rate) ** i
        revenue += np.random.normal(0, revenue * 0.1)  # Add noise
        revenues.append(max(revenue, 0))
    
    return pd.DataFrame({
        'date': dates,
        'revenue': revenues
    })

def generate_sample_market_data() -> pd.DataFrame:
    """Generate sample market data"""
    dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='M')
    
    return pd.DataFrame({
        'date': dates,
        'market_size': np.random.uniform(1000000, 5000000, len(dates)),
        'revenue': np.random.uniform(50000, 200000, len(dates))
    })

def generate_sample_user_features() -> pd.DataFrame:
    """Generate sample user features for churn prediction"""
    n_users = 100
    
    return pd.DataFrame({
        'last_login': [datetime.now() - timedelta(days=np.random.randint(1, 60)) for _ in range(n_users)],
        'session_count': np.random.poisson(20, n_users),
        'total_session_time': np.random.uniform(100, 2000, n_users),
        'pages_viewed': np.random.poisson(100, n_users),
        'actions_taken': np.random.poisson(50, n_users)
    })

if __name__ == "__main__":
    main()
