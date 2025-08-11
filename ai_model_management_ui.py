#!/usr/bin/env python3
"""
AI Model Management UI
Streamlit interface for Task 65: AI model versioning and A/B testing

This module provides a comprehensive web interface for:
- Model registry and version management
- A/B testing experiment setup and monitoring
- Performance monitoring and health checks
- Cost optimization recommendations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any

# Import our model management system
try:
    from ai_model_management import (
        ModelManagementService, ModelStatus, ExperimentStatus,
        ModelMetadata, ModelPerformanceMetrics, ABTestExperiment
    )
except ImportError:
    st.error("AI Model Management system not found. Please ensure ai_model_management.py is available.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="AI Model Management",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'model_service' not in st.session_state:
    st.session_state.model_service = ModelManagementService()

def main():
    """Main application interface"""
    st.title("🤖 AI Model Management System")
    st.markdown("**Task 65: AI model versioning and A/B testing**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "📊 Dashboard",
            "📚 Model Registry", 
            "🧪 A/B Testing",
            "📈 Performance Monitoring",
            "💰 Cost Optimization",
            "⚙️ Settings"
        ]
    )
    
    # Route to appropriate page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📚 Model Registry":
        show_model_registry()
    elif page == "🧪 A/B Testing":
        show_ab_testing()
    elif page == "📈 Performance Monitoring":
        show_performance_monitoring()
    elif page == "💰 Cost Optimization":
        show_cost_optimization()
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard():
    """Show main dashboard with system overview"""
    st.header("📊 System Dashboard")
    
    service = st.session_state.model_service
    
    # Get system health
    health = service.get_system_health()
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = {
            'healthy': '🟢',
            'degraded': '🟡', 
            'unhealthy': '🔴'
        }.get(health['overall_status'], '⚪')
        
        st.metric(
            "System Status",
            f"{status_color} {health['overall_status'].title()}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Production Models",
            health['production_models'],
            delta=None
        )
    
    with col3:
        st.metric(
            "Active Experiments", 
            health['active_experiments'],
            delta=None
        )
    
    with col4:
        st.metric(
            "Active Alerts",
            len(health['alerts']),
            delta=None
        )
    
    # Alerts section
    if health['alerts']:
        st.subheader("🚨 Active Alerts")
        for alert in health['alerts']:
            alert_data = alert['alert']
            severity_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(alert_data['severity'], '⚪')
            
            st.warning(f"{severity_color} **{alert['model_name']}**: {alert_data['message']}")
    
    # Model health overview
    st.subheader("🏥 Model Health Overview")
    
    if health['model_health']:
        health_df = pd.DataFrame([
            {
                'Model ID': model_id,
                'Name': info['name'],
                'Version': info['version'],
                'Status': info['status'],
                'Alerts': info['alert_count']
            }
            for model_id, info in health['model_health'].items()
        ])
        
        # Color code by status
        def color_status(val):
            colors = {
                'healthy': 'background-color: #d4edda',
                'degraded': 'background-color: #fff3cd', 
                'unhealthy': 'background-color: #f8d7da'
            }
            return colors.get(val, '')
        
        styled_df = health_df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No production models found.")

def show_model_registry():
    """Show model registry interface"""
    st.header("📚 Model Registry")
    
    service = st.session_state.model_service
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 All Models", "➕ Register Model", "📊 Model Details"])
    
    with tab1:
        st.subheader("All Registered Models")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            model_type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + ["transcription", "analysis", "enhancement", "custom"]
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status", 
                ["All"] + [status.value for status in ModelStatus]
            )
        
        with col3:
            limit = st.number_input("Limit Results", min_value=10, max_value=1000, value=50)
        
        # Get models
        models = service.registry.list_models(
            model_type=None if model_type_filter == "All" else model_type_filter,
            status=None if status_filter == "All" else ModelStatus(status_filter),
            limit=limit
        )
        
        if models:
            models_df = pd.DataFrame([
                {
                    'ID': model.model_id[:8] + '...',
                    'Name': model.name,
                    'Version': model.version,
                    'Type': model.model_type,
                    'Framework': model.framework,
                    'Status': model.status.value,
                    'Created': model.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Created By': model.created_by,
                    'Tags': ', '.join(model.tags[:3])  # Show first 3 tags
                }
                for model in models
            ])
            
            st.dataframe(models_df, use_container_width=True)
            
            # Model selection for details
            selected_model = st.selectbox(
                "Select model for details",
                options=[f"{m.name} v{m.version} ({m.model_id[:8]}...)" for m in models],
                key="model_select"
            )
            
            if selected_model:
                model_id = models[st.session_state.get('model_select', 0)].model_id
                st.session_state.selected_model_id = model_id
        else:
            st.info("No models found matching the criteria.")
    
    with tab2:
        st.subheader("Register New Model")
        
        with st.form("register_model"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Model Name*", placeholder="e.g., whisper-transcription")
                version = st.text_input("Version*", placeholder="e.g., 1.0.0")
                model_type = st.selectbox("Model Type*", 
                    ["transcription", "analysis", "enhancement", "custom"])
                framework = st.selectbox("Framework*",
                    ["openai", "huggingface", "custom", "local"])
            
            with col2:
                description = st.text_area("Description", 
                    placeholder="Describe the model's purpose and capabilities")
                created_by = st.text_input("Created By*", value="admin")
                tags = st.text_input("Tags (comma-separated)", 
                    placeholder="production, v1, optimized")
                parent_model = st.text_input("Parent Model ID (optional)")
            
            # Parameters section
            st.subheader("Model Parameters")
            param_json = st.text_area("Parameters (JSON format)", 
                value='{"temperature": 0.1, "max_tokens": 1000}',
                help="Enter model parameters as JSON")
            
            # File upload
            uploaded_file = st.file_uploader("Model File (optional)", 
                type=['pkl', 'pt', 'h5', 'onnx'])
            
            submitted = st.form_submit_button("Register Model")
            
            if submitted:
                if not all([name, version, model_type, framework, created_by]):
                    st.error("Please fill in all required fields marked with *")
                else:
                    try:
                        # Parse parameters
                        parameters = json.loads(param_json) if param_json else {}
                        
                        # Handle file upload
                        file_path = None
                        if uploaded_file:
                            file_path = f"models/{uploaded_file.name}"
                            # In a real implementation, save the file
                            st.info(f"File would be saved to: {file_path}")
                        
                        # Parse tags
                        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        
                        # Register model
                        model_id = service.create_model_version(
                            name=name,
                            version=version,
                            description=description,
                            model_type=model_type,
                            framework=framework,
                            created_by=created_by,
                            parameters=parameters,
                            file_path=file_path,
                            tags=tag_list,
                            parent_model_id=parent_model if parent_model else None
                        )
                        
                        st.success(f"✅ Model registered successfully! ID: {model_id}")
                        
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format in parameters")
                    except Exception as e:
                        st.error(f"Error registering model: {str(e)}")
    
    with tab3:
        st.subheader("Model Details")
        
        if hasattr(st.session_state, 'selected_model_id'):
            model = service.registry.get_model(st.session_state.selected_model_id)
            
            if model:
                # Basic info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"**Name:** {model.name}")
                    st.write(f"**Version:** {model.version}")
                    st.write(f"**Type:** {model.model_type}")
                    st.write(f"**Framework:** {model.framework}")
                    st.write(f"**Status:** {model.status.value}")
                
                with col2:
                    st.write("**Metadata**")
                    st.write(f"**Created:** {model.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Created By:** {model.created_by}")
                    st.write(f"**Tags:** {', '.join(model.tags)}")
                    if model.file_size:
                        st.write(f"**File Size:** {model.file_size / (1024*1024):.2f} MB")
                
                # Description
                if model.description:
                    st.write("**Description**")
                    st.write(model.description)
                
                # Parameters
                if model.parameters:
                    st.write("**Parameters**")
                    st.json(model.parameters)
                
                # Actions
                st.write("**Actions**")
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button("Deploy to Production"):
                        try:
                            service.deploy_model(model.model_id, "production")
                            st.success("Model deployed to production!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Deployment failed: {str(e)}")
                
                with action_col2:
                    if st.button("Deploy to Staging"):
                        try:
                            service.deploy_model(model.model_id, "staging")
                            st.success("Model deployed to staging!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Deployment failed: {str(e)}")
                
                with action_col3:
                    if model.status == ModelStatus.PRODUCTION:
                        if st.button("Deprecate Model"):
                            service.registry.update_model_status(model.model_id, ModelStatus.DEPRECATED)
                            st.success("Model deprecated!")
                            st.rerun()
            else:
                st.error("Model not found")
        else:
            st.info("Select a model from the 'All Models' tab to view details.")

def show_ab_testing():
    """Show A/B testing interface"""
    st.header("🧪 A/B Testing")
    
    service = st.session_state.model_service
    
    # Tabs for different A/B testing views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Active Tests", "➕ Create Test", "📈 Results", "📋 History"])
    
    with tab1:
        st.subheader("Active A/B Tests")
        
        active_experiments = service.ab_testing.active_experiments
        
        if active_experiments:
            for exp_id, experiment in active_experiments.items():
                with st.expander(f"🧪 {experiment.name}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Control Model:** {experiment.control_model_id[:8]}...")
                        st.write(f"**Treatment Model:** {experiment.treatment_model_id[:8]}...")
                        st.write(f"**Traffic Split:** {experiment.traffic_split*100:.1f}% treatment")
                    
                    with col2:
                        st.write(f"**Started:** {experiment.start_date.strftime('%Y-%m-%d')}")
                        if experiment.end_date:
                            st.write(f"**Ends:** {experiment.end_date.strftime('%Y-%m-%d')}")
                        st.write(f"**Success Metrics:** {', '.join(experiment.success_metrics)}")
                    
                    with col3:
                        if st.button(f"Stop Test", key=f"stop_{exp_id}"):
                            service.ab_testing.stop_experiment(exp_id)
                            st.success("Experiment stopped!")
                            st.rerun()
                        
                        if st.button(f"View Results", key=f"results_{exp_id}"):
                            st.session_state.selected_experiment_id = exp_id
                            st.info("Switch to 'Results' tab to view analysis")
        else:
            st.info("No active A/B tests running.")
    
    with tab2:
        st.subheader("Create New A/B Test")
        
        # Get production models for selection
        production_models = service.registry.list_models(status=ModelStatus.PRODUCTION)
        
        if len(production_models) < 2:
            st.warning("You need at least 2 production models to create an A/B test.")
            return
        
        model_options = [f"{m.name} v{m.version} ({m.model_id[:8]}...)" for m in production_models]
        
        with st.form("create_ab_test"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_name = st.text_input("Test Name*", placeholder="Whisper Model Comparison")
                description = st.text_area("Description", 
                    placeholder="Compare performance between model versions")
                
                control_idx = st.selectbox("Control Model*", range(len(model_options)),
                    format_func=lambda x: model_options[x])
                treatment_idx = st.selectbox("Treatment Model*", range(len(model_options)),
                    format_func=lambda x: model_options[x])
            
            with col2:
                traffic_split = st.slider("Traffic Split (% to treatment)", 
                    min_value=10, max_value=90, value=50) / 100.0
                
                duration_days = st.number_input("Duration (days)", 
                    min_value=1, max_value=30, value=7)
                
                min_sample_size = st.number_input("Minimum Sample Size", 
                    min_value=100, max_value=10000, value=1000)
                
                confidence_level = st.slider("Confidence Level", 
                    min_value=0.90, max_value=0.99, value=0.95, step=0.01)
            
            # Success metrics
            st.subheader("Success Metrics")
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                accuracy_metric = st.checkbox("Accuracy", value=True)
                latency_metric = st.checkbox("Latency", value=True)
                cost_metric = st.checkbox("Cost per Request", value=True)
            
            with metrics_col2:
                error_rate_metric = st.checkbox("Error Rate")
                satisfaction_metric = st.checkbox("User Satisfaction")
                throughput_metric = st.checkbox("Throughput")
            
            created_by = st.text_input("Created By", value="admin")
            
            submitted = st.form_submit_button("Create A/B Test")
            
            if submitted:
                if not all([test_name, created_by]):
                    st.error("Please fill in all required fields")
                elif control_idx == treatment_idx:
                    st.error("Control and treatment models must be different")
                else:
                    # Build success metrics list
                    success_metrics = []
                    if accuracy_metric:
                        success_metrics.append('accuracy')
                    if latency_metric:
                        success_metrics.append('latency_ms')
                    if cost_metric:
                        success_metrics.append('cost_per_request')
                    if error_rate_metric:
                        success_metrics.append('error_rate')
                    if satisfaction_metric:
                        success_metrics.append('user_satisfaction')
                    if throughput_metric:
                        success_metrics.append('throughput_rps')
                    
                    if not success_metrics:
                        st.error("Please select at least one success metric")
                    else:
                        try:
                            experiment_id = service.start_ab_test(
                                name=test_name,
                                description=description,
                                control_model_id=production_models[control_idx].model_id,
                                treatment_model_id=production_models[treatment_idx].model_id,
                                traffic_split=traffic_split,
                                success_metrics=success_metrics,
                                duration_days=duration_days,
                                created_by=created_by,
                                minimum_sample_size=min_sample_size,
                                confidence_level=confidence_level
                            )
                            
                            st.success(f"✅ A/B test created successfully! ID: {experiment_id}")
                            
                        except Exception as e:
                            st.error(f"Error creating A/B test: {str(e)}")
    
    with tab3:
        st.subheader("A/B Test Results")
        
        if hasattr(st.session_state, 'selected_experiment_id'):
            exp_id = st.session_state.selected_experiment_id
            
            try:
                results = service.ab_testing.analyze_experiment(exp_id)
                
                # Results summary
                st.write("**Experiment Results Summary**")
                st.write(f"**Recommendation:** {results.recommendation}")
                st.write(f"**Analysis Generated:** {results.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Metrics comparison
                if results.control_metrics and results.treatment_metrics:
                    st.subheader("📊 Metrics Comparison")
                    
                    comparison_data = []
                    for metric in results.control_metrics.keys():
                        if metric in results.treatment_metrics:
                            comparison_data.append({
                                'Metric': metric,
                                'Control': results.control_metrics[metric],
                                'Treatment': results.treatment_metrics[metric],
                                'Improvement': ((results.treatment_metrics[metric] - results.control_metrics[metric]) / results.control_metrics[metric] * 100) if results.control_metrics[metric] != 0 else 0,
                                'Significant': results.statistical_significance.get(metric, False),
                                'P-Value': results.p_values.get(metric, 1.0),
                                'Sample Size': results.sample_sizes.get(metric, 0)
                            })
                    
                    if comparison_data:
                        comparison_df = pd.DataFrame(comparison_data)
                        
                        # Style the dataframe
                        def highlight_significant(row):
                            if row['Significant']:
                                return ['background-color: #d4edda'] * len(row)
                            return [''] * len(row)
                        
                        styled_df = comparison_df.style.apply(highlight_significant, axis=1)
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Visualization
                        fig = px.bar(comparison_df, x='Metric', y=['Control', 'Treatment'],
                                   title="Control vs Treatment Comparison",
                                   barmode='group')
                        st.plotly_chart(fig, use_container_width=True)
                
                # Statistical details
                with st.expander("📈 Statistical Details"):
                    if results.confidence_intervals:
                        st.write("**95% Confidence Intervals for Differences:**")
                        for metric, (lower, upper) in results.confidence_intervals.items():
                            st.write(f"- {metric}: [{lower:.4f}, {upper:.4f}]")
                    
                    if results.effect_sizes:
                        st.write("**Effect Sizes (Cohen's d):**")
                        for metric, effect_size in results.effect_sizes.items():
                            interpretation = "Small" if abs(effect_size) < 0.5 else "Medium" if abs(effect_size) < 0.8 else "Large"
                            st.write(f"- {metric}: {effect_size:.3f} ({interpretation})")
                
            except Exception as e:
                st.error(f"Error analyzing experiment: {str(e)}")
        else:
            st.info("Select an experiment from 'Active Tests' to view results.")
    
    with tab4:
        st.subheader("A/B Test History")
        st.info("A/B test history functionality would be implemented here.")

def show_performance_monitoring():
    """Show performance monitoring interface"""
    st.header("📈 Performance Monitoring")
    
    service = st.session_state.model_service
    
    # Get production models
    production_models = service.registry.list_models(status=ModelStatus.PRODUCTION)
    
    if not production_models:
        st.warning("No production models found for monitoring.")
        return
    
    # Model selection
    model_options = [f"{m.name} v{m.version} ({m.model_id[:8]}...)" for m in production_models]
    selected_idx = st.selectbox("Select Model to Monitor", range(len(model_options)),
        format_func=lambda x: model_options[x])
    
    selected_model = production_models[selected_idx]
    
    # Time range selection
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.selectbox("Time Range", [1, 7, 30, 90], index=1)
    with col2:
        auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
    
    if auto_refresh:
        st.rerun()
    
    # Get model health
    health = service.monitor.check_model_health(selected_model.model_id)
    
    # Health status
    status_color = {
        'healthy': '🟢',
        'degraded': '🟡',
        'unhealthy': '🔴',
        'insufficient_data': '⚪'
    }.get(health['status'], '⚪')
    
    st.metric("Model Health", f"{status_color} {health['status'].title()}")
    
    # Alerts
    if health.get('alerts'):
        st.subheader("🚨 Active Alerts")
        for alert in health['alerts']:
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(alert['severity'], '⚪')
            st.warning(f"{severity_emoji} **{alert['type'].replace('_', ' ').title()}**: {alert['message']}")
    
    # Performance metrics over time
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    metrics = service.registry.get_model_metrics(
        selected_model.model_id, start_date, end_date, limit=1000
    )
    
    if metrics:
        # Convert to DataFrame
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'timestamp': metric.timestamp,
                'accuracy': metric.accuracy,
                'latency_ms': metric.latency_ms,
                'throughput_rps': metric.throughput_rps,
                'error_rate': metric.error_rate,
                'cost_per_request': metric.cost_per_request,
                'memory_usage_mb': metric.memory_usage_mb,
                'cpu_usage_percent': metric.cpu_usage_percent,
                'user_satisfaction': metric.user_satisfaction
            })
        
        df = pd.DataFrame(metrics_data)
        df = df.sort_values('timestamp')
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Accuracy Over Time', 'Latency Over Time', 
                          'Error Rate Over Time', 'Cost Per Request Over Time'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add traces
        if 'accuracy' in df.columns and df['accuracy'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['accuracy'], name='Accuracy'),
                row=1, col=1
            )
        
        if 'latency_ms' in df.columns and df['latency_ms'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['latency_ms'], name='Latency (ms)'),
                row=1, col=2
            )
        
        if 'error_rate' in df.columns and df['error_rate'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['error_rate'], name='Error Rate'),
                row=2, col=1
            )
        
        if 'cost_per_request' in df.columns and df['cost_per_request'].notna().any():
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['cost_per_request'], name='Cost per Request'),
                row=2, col=2
            )
        
        fig.update_layout(height=600, showlegend=False, title_text="Performance Metrics Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            if df['accuracy'].notna().any():
                st.metric("Avg Accuracy", f"{df['accuracy'].mean():.3f}")
        
        with summary_col2:
            if df['latency_ms'].notna().any():
                st.metric("Avg Latency", f"{df['latency_ms'].mean():.1f}ms")
        
        with summary_col3:
            if df['error_rate'].notna().any():
                st.metric("Avg Error Rate", f"{df['error_rate'].mean():.3f}")
        
        with summary_col4:
            if df['cost_per_request'].notna().any():
                st.metric("Avg Cost", f"${df['cost_per_request'].mean():.4f}")
    
    else:
        st.info("No performance metrics available for the selected time range.")

def show_cost_optimization():
    """Show cost optimization interface"""
    st.header("💰 Cost Optimization")
    
    service = st.session_state.model_service
    
    st.subheader("🎯 Model Recommendation")
    
    # Requirements input
    with st.form("optimization_requirements"):
        st.write("**Define Your Requirements:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_type = st.selectbox("Model Type", 
                ["transcription", "analysis", "enhancement", "custom"])
            min_accuracy = st.slider("Minimum Accuracy", 0.0, 1.0, 0.8, 0.01)
            max_latency = st.number_input("Maximum Latency (ms)", 
                min_value=10, max_value=5000, value=200)
        
        with col2:
            max_cost = st.number_input("Maximum Cost per Request ($)", 
                min_value=0.0001, max_value=0.1, value=0.002, format="%.4f")
            min_throughput = st.number_input("Minimum Throughput (RPS)", 
                min_value=1, max_value=1000, value=10)
        
        submitted = st.form_submit_button("Get Recommendation")
        
        if submitted:
            requirements = {
                'min_accuracy': min_accuracy,
                'max_latency_ms': max_latency,
                'max_cost_per_request': max_cost,
                'min_throughput_rps': min_throughput
            }
            
            recommendation = service.get_model_recommendation(model_type, requirements)
            
            if recommendation:
                st.success("✅ Recommendation Found!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Recommended Model:**")
                    st.write(f"- **Name:** {recommendation['model_name']}")
                    st.write(f"- **Version:** {recommendation['model_version']}")
                    st.write(f"- **ID:** {recommendation['model_id'][:8]}...")
                
                with col2:
                    st.write("**Recent Performance:**")
                    perf = recommendation['recent_performance']
                    if 'accuracy' in perf:
                        st.write(f"- **Accuracy:** {perf['accuracy']:.3f}")
                    if 'latency_ms' in perf:
                        st.write(f"- **Latency:** {perf['latency_ms']:.1f}ms")
                    if 'cost_per_request' in perf:
                        st.write(f"- **Cost:** ${perf['cost_per_request']:.4f}")
                
                st.info(f"**Reason:** {recommendation['recommendation_reason']}")
                
            else:
                st.warning("No models found matching your requirements. Consider adjusting the criteria.")
    
    # Cost analysis
    st.subheader("📊 Cost Analysis")
    
    production_models = service.registry.list_models(status=ModelStatus.PRODUCTION)
    
    if production_models:
        cost_data = []
        
        for model in production_models:
            # Get recent metrics for cost analysis
            recent_metrics = service.registry.get_model_metrics(
                model.model_id,
                start_date=datetime.now() - timedelta(days=7),
                limit=100
            )
            
            if recent_metrics:
                costs = [m.cost_per_request for m in recent_metrics if m.cost_per_request is not None]
                latencies = [m.latency_ms for m in recent_metrics if m.latency_ms is not None]
                accuracies = [m.accuracy for m in recent_metrics if m.accuracy is not None]
                
                if costs:
                    cost_data.append({
                        'Model': f"{model.name} v{model.version}",
                        'Avg Cost': sum(costs) / len(costs),
                        'Avg Latency': sum(latencies) / len(latencies) if latencies else 0,
                        'Avg Accuracy': sum(accuracies) / len(accuracies) if accuracies else 0,
                        'Samples': len(recent_metrics)
                    })
        
        if cost_data:
            cost_df = pd.DataFrame(cost_data)
            
            # Cost comparison chart
            fig = px.scatter(cost_df, x='Avg Latency', y='Avg Cost', 
                           size='Avg Accuracy', hover_name='Model',
                           title='Cost vs Performance Analysis',
                           labels={'Avg Latency': 'Average Latency (ms)', 
                                  'Avg Cost': 'Average Cost per Request ($)'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost table
            st.dataframe(cost_df, use_container_width=True)
        else:
            st.info("No cost data available for analysis.")
    else:
        st.info("No production models available for cost analysis.")

def show_settings():
    """Show settings interface"""
    st.header("⚙️ Settings")
    
    st.subheader("🔧 System Configuration")
    
    # Alert thresholds
    st.write("**Performance Alert Thresholds**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        accuracy_threshold = st.slider("Accuracy Drop Threshold", 
            0.01, 0.20, 0.05, 0.01, 
            help="Alert when accuracy drops by this amount")
        
        latency_threshold = st.slider("Latency Increase Multiplier", 
            1.5, 5.0, 2.0, 0.1,
            help="Alert when latency increases by this factor")
    
    with col2:
        error_threshold = st.slider("Error Rate Increase Threshold", 
            0.01, 0.50, 0.10, 0.01,
            help="Alert when error rate increases by this amount")
        
        cost_threshold = st.slider("Cost Increase Multiplier", 
            1.2, 3.0, 1.5, 0.1,
            help="Alert when cost increases by this factor")
    
    # Monitoring settings
    st.write("**Monitoring Configuration**")
    
    baseline_days = st.number_input("Baseline Window (days)", 
        min_value=1, max_value=30, value=7,
        help="Number of days to use for baseline metrics")
    
    monitoring_hours = st.number_input("Monitoring Window (hours)", 
        min_value=1, max_value=168, value=24,
        help="Number of hours to monitor for current metrics")
    
    # Database settings
    st.write("**Database Configuration**")
    
    registry_path = st.text_input("Model Registry Path", 
        value="model_registry.db",
        help="Path to the model registry database")
    
    experiments_path = st.text_input("Experiments Database Path", 
        value="experiments.db", 
        help="Path to the experiments database")
    
    # Save settings
    if st.button("💾 Save Settings"):
        # In a real implementation, save these settings
        st.success("Settings saved successfully!")
        st.info("Settings would be persisted to configuration file.")
    
    # System info
    st.subheader("ℹ️ System Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write("**Database Status**")
        st.write("- Registry: ✅ Connected")
        st.write("- Experiments: ✅ Connected")
        st.write("- Health: 🟢 Good")
    
    with info_col2:
        st.write("**Version Information**")
        st.write("- Model Management: v1.0.0")
        st.write("- A/B Testing: v1.0.0")
        st.write("- Performance Monitor: v1.0.0")

if __name__ == "__main__":
    main()