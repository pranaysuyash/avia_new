"""
AI Model Selection Engine UI

Streamlit interface for the AI Model Selection Engine with real-time monitoring,
model management, and selection visualization.
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List

from ai_model_selection_engine import (
    ModelSelectionEngine, AIRequest, UserPreferences, RequestContext,
    ModelCapability, ModelProvider, SelectionCriteria, AIModel
)

class ModelSelectionEngineUI:
    """Streamlit UI for AI Model Selection Engine"""
    
    def __init__(self):
        self.engine = None
        if 'selection_engine' not in st.session_state:
            st.session_state.selection_engine = ModelSelectionEngine()
        self.engine = st.session_state.selection_engine
    
    def render(self):
        """Render the main UI"""
        st.title("🤖 AI Model Selection Engine")
        st.markdown("Intelligent model selection with multi-criteria optimization")
        
        # Sidebar for navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Model Selection", "Model Management", "Performance Analytics", "Selection History"]
        )
        
        if page == "Model Selection":
            self.render_model_selection()
        elif page == "Model Management":
            self.render_model_management()
        elif page == "Performance Analytics":
            self.render_performance_analytics()
        elif page == "Selection History":
            self.render_selection_history()
    
    def render_model_selection(self):
        """Render model selection interface"""
        st.header("🎯 Model Selection")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Request Configuration")
            
            # Request details
            capability = st.selectbox(
                "AI Capability",
                options=[cap.value for cap in ModelCapability],
                help="Select the AI capability you need"
            )
            
            urgency = st.selectbox(
                "Urgency Level",
                options=["low", "normal", "high"],
                index=1,
                help="Higher urgency prioritizes speed over other factors"
            )
            
            quality_req = st.selectbox(
                "Quality Requirement",
                options=["basic", "standard", "high"],
                index=1,
                help="Higher quality requirements prioritize accuracy"
            )
            
            content_size = st.number_input(
                "Content Size (bytes)",
                min_value=0,
                value=1024,
                help="Size of content to process"
            )
            
            st.subheader("User Preferences")
            
            # User preferences
            preferred_providers = st.multiselect(
                "Preferred Providers",
                options=[provider.value for provider in ModelProvider],
                help="Select preferred AI providers"
            )
            
            col_pref1, col_pref2 = st.columns(2)
            
            with col_pref1:
                quality_threshold = st.slider(
                    "Quality Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.8,
                    step=0.05,
                    help="Minimum acceptable quality score"
                )
                
                max_latency = st.number_input(
                    "Max Latency (ms)",
                    min_value=100,
                    max_value=30000,
                    value=5000,
                    step=100,
                    help="Maximum acceptable response time"
                )
            
            with col_pref2:
                max_cost = st.number_input(
                    "Max Cost per Request ($)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.10,
                    step=0.01,
                    format="%.4f",
                    help="Maximum acceptable cost per request"
                )
                
                privacy_required = st.checkbox(
                    "Privacy Required",
                    help="Prefer local models for sensitive data"
                )
            
            st.subheader("Selection Criteria Weights")
            
            # Criteria weights
            col_w1, col_w2, col_w3 = st.columns(3)
            
            with col_w1:
                quality_weight = st.slider("Quality Weight", 0.0, 1.0, 0.3, 0.05)
                speed_weight = st.slider("Speed Weight", 0.0, 1.0, 0.25, 0.05)
            
            with col_w2:
                cost_weight = st.slider("Cost Weight", 0.0, 1.0, 0.2, 0.05)
                availability_weight = st.slider("Availability Weight", 0.0, 1.0, 0.15, 0.05)
            
            with col_w3:
                privacy_weight = st.slider("Privacy Weight", 0.0, 1.0, 0.1, 0.05)
            
            # Normalize weights
            total_weight = quality_weight + speed_weight + cost_weight + availability_weight + privacy_weight
            if total_weight > 0:
                weights = {
                    SelectionCriteria.QUALITY: quality_weight / total_weight,
                    SelectionCriteria.SPEED: speed_weight / total_weight,
                    SelectionCriteria.COST: cost_weight / total_weight,
                    SelectionCriteria.AVAILABILITY: availability_weight / total_weight,
                    SelectionCriteria.PRIVACY: privacy_weight / total_weight
                }
            else:
                weights = None
            
            # Selection button
            if st.button("🎯 Select Optimal Model", type="primary"):
                with st.spinner("Selecting optimal model..."):
                    selection_result = self.perform_model_selection(
                        capability, urgency, quality_req, content_size,
                        preferred_providers, quality_threshold, max_latency,
                        max_cost, privacy_required, weights
                    )
                    
                    if selection_result:
                        st.session_state.last_selection = selection_result
        
        with col2:
            st.subheader("Available Models")
            
            # Display available models
            summary = self.engine.get_model_performance_summary()
            
            for model_id, info in summary.items():
                with st.expander(f"📊 {info['name']}", expanded=False):
                    st.write(f"**Provider:** {info['provider']}")
                    st.write(f"**Capabilities:** {', '.join(info['capabilities'])}")
                    
                    metrics = info['metrics']
                    col_m1, col_m2 = st.columns(2)
                    
                    with col_m1:
                        st.metric("Latency", f"{metrics['latency_ms']:.0f}ms")
                        st.metric("Accuracy", f"{metrics['accuracy_score']:.2f}")
                    
                    with col_m2:
                        st.metric("Cost", f"${metrics['cost_per_request']:.4f}")
                        st.metric("Availability", f"{metrics['availability_percent']:.1f}%")
                    
                    # Status indicator
                    status = "🟢 Available" if info['is_available'] else "🔴 Unavailable"
                    st.write(f"**Status:** {status}")
                    st.write(f"**Priority:** {info['priority']}")
        
        # Display selection result
        if hasattr(st.session_state, 'last_selection') and st.session_state.last_selection:
            self.display_selection_result(st.session_state.last_selection)
    
    def perform_model_selection(self, capability, urgency, quality_req, content_size,
                              preferred_providers, quality_threshold, max_latency,
                              max_cost, privacy_required, weights):
        """Perform model selection with given parameters"""
        try:
            # Create request objects
            user_prefs = UserPreferences(
                preferred_providers=[ModelProvider(p) for p in preferred_providers],
                quality_threshold=quality_threshold,
                max_latency_ms=max_latency,
                max_cost_per_request=max_cost,
                privacy_required=privacy_required
            )
            
            context = RequestContext(
                user_id="ui_user",
                request_type=ModelCapability(capability),
                content_size=content_size,
                urgency=urgency,
                quality_requirement=quality_req
            )
            
            request = AIRequest(
                id=f"ui_req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                capability=ModelCapability(capability),
                content="ui_request",
                context=context,
                preferences=user_prefs
            )
            
            # Run selection (need to handle async in Streamlit)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            selection = loop.run_until_complete(
                self.engine.select_model(request, weights)
            )
            loop.close()
            
            return selection
            
        except Exception as e:
            st.error(f"Error in model selection: {str(e)}")
            return None
    
    def display_selection_result(self, selection):
        """Display model selection result"""
        st.subheader("🎯 Selection Result")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Selected Model",
                selection.primary_model.name,
                help="Primary model selected for the request"
            )
        
        with col2:
            st.metric(
                "Confidence Score",
                f"{selection.confidence_score:.3f}",
                help="Selection confidence (0-1)"
            )
        
        with col3:
            st.metric(
                "Provider",
                selection.primary_model.provider.value,
                help="AI service provider"
            )
        
        # Detailed information
        col_detail1, col_detail2 = st.columns(2)
        
        with col_detail1:
            st.write("**Estimated Performance:**")
            st.write(f"• Latency: {selection.estimated_latency:.0f}ms")
            st.write(f"• Cost: ${selection.estimated_cost:.4f}")
            st.write(f"• Accuracy: {selection.primary_model.metrics.accuracy_score:.2f}")
        
        with col_detail2:
            st.write("**Fallback Models:**")
            for i, fallback in enumerate(selection.fallback_models[:3], 1):
                st.write(f"{i}. {fallback.name} ({fallback.provider.value})")
        
        # Selection reasoning
        st.write("**Selection Reasoning:**")
        st.info(selection.selection_reasoning)
        
        # Simulate usage button
        if st.button("🚀 Simulate Model Usage"):
            self.simulate_model_usage(selection)
    
    def simulate_model_usage(self, selection):
        """Simulate model usage and update metrics"""
        import random
        
        # Simulate actual performance with some variance
        base_latency = selection.primary_model.metrics.latency_ms
        actual_latency = base_latency * random.uniform(0.8, 1.3)
        
        base_cost = selection.primary_model.metrics.cost_per_request
        actual_cost = base_cost * random.uniform(0.9, 1.1)
        
        success = random.random() > 0.05  # 95% success rate
        
        # Update metrics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            self.engine.update_model_metrics(
                selection.primary_model.id,
                actual_latency,
                actual_cost,
                success
            )
        )
        loop.close()
        
        # Show results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delta_latency = actual_latency - base_latency
            st.metric(
                "Actual Latency",
                f"{actual_latency:.0f}ms",
                delta=f"{delta_latency:+.0f}ms"
            )
        
        with col2:
            delta_cost = actual_cost - base_cost
            st.metric(
                "Actual Cost",
                f"${actual_cost:.4f}",
                delta=f"${delta_cost:+.4f}"
            )
        
        with col3:
            status = "✅ Success" if success else "❌ Failed"
            st.metric("Result", status)
        
        st.success("Model metrics updated based on simulated usage!")
    
    def render_model_management(self):
        """Render model management interface"""
        st.header("⚙️ Model Management")
        
        # Model overview
        summary = self.engine.get_model_performance_summary()
        
        # Create DataFrame for display
        model_data = []
        for model_id, info in summary.items():
            model_data.append({
                'ID': model_id,
                'Name': info['name'],
                'Provider': info['provider'],
                'Capabilities': ', '.join(info['capabilities']),
                'Latency (ms)': info['metrics']['latency_ms'],
                'Accuracy': info['metrics']['accuracy_score'],
                'Cost ($)': info['metrics']['cost_per_request'],
                'Availability (%)': info['metrics']['availability_percent'],
                'Error Rate': info['metrics']['error_rate'],
                'Status': 'Available' if info['is_available'] else 'Unavailable',
                'Priority': info['priority']
            })
        
        df = pd.DataFrame(model_data)
        
        # Display model table
        st.subheader("📊 Model Overview")
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                'Latency (ms)': st.column_config.NumberColumn(format="%.0f"),
                'Accuracy': st.column_config.NumberColumn(format="%.3f"),
                'Cost ($)': st.column_config.NumberColumn(format="%.4f"),
                'Availability (%)': st.column_config.NumberColumn(format="%.1f"),
                'Error Rate': st.column_config.NumberColumn(format="%.3f")
            }
        )
        
        # Model comparison charts
        st.subheader("📈 Model Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Latency vs Accuracy scatter plot
            fig_scatter = px.scatter(
                df,
                x='Latency (ms)',
                y='Accuracy',
                color='Provider',
                size='Cost ($)',
                hover_name='Name',
                title='Latency vs Accuracy (bubble size = cost)'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Cost comparison bar chart
            fig_bar = px.bar(
                df,
                x='Name',
                y='Cost ($)',
                color='Provider',
                title='Cost per Request by Model'
            )
            fig_bar.update_xaxis(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Model configuration
        st.subheader("⚙️ Model Configuration")
        
        selected_model = st.selectbox(
            "Select Model to Configure",
            options=list(summary.keys()),
            format_func=lambda x: summary[x]['name']
        )
        
        if selected_model:
            model_info = summary[selected_model]
            
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                new_priority = st.number_input(
                    "Priority",
                    min_value=1,
                    max_value=5,
                    value=model_info['priority'],
                    help="1 = highest priority, 5 = lowest priority"
                )
                
                is_available = st.checkbox(
                    "Available",
                    value=model_info['is_available'],
                    help="Enable/disable model availability"
                )
            
            with col_config2:
                st.write("**Current Metrics:**")
                st.write(f"Latency: {model_info['metrics']['latency_ms']:.0f}ms")
                st.write(f"Accuracy: {model_info['metrics']['accuracy_score']:.3f}")
                st.write(f"Cost: ${model_info['metrics']['cost_per_request']:.4f}")
                st.write(f"Error Rate: {model_info['metrics']['error_rate']:.3f}")
            
            if st.button("💾 Update Model Configuration"):
                # Update model configuration
                model = self.engine.models[selected_model]
                model.priority = new_priority
                model.is_available = is_available
                
                st.success(f"Updated configuration for {model_info['name']}")
                st.rerun()
    
    def render_performance_analytics(self):
        """Render performance analytics interface"""
        st.header("📊 Performance Analytics")
        
        summary = self.engine.get_model_performance_summary()
        
        # Performance metrics overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_latency = sum(info['metrics']['latency_ms'] for info in summary.values()) / len(summary)
            st.metric("Avg Latency", f"{avg_latency:.0f}ms")
        
        with col2:
            avg_accuracy = sum(info['metrics']['accuracy_score'] for info in summary.values()) / len(summary)
            st.metric("Avg Accuracy", f"{avg_accuracy:.3f}")
        
        with col3:
            avg_cost = sum(info['metrics']['cost_per_request'] for info in summary.values()) / len(summary)
            st.metric("Avg Cost", f"${avg_cost:.4f}")
        
        with col4:
            available_models = sum(1 for info in summary.values() if info['is_available'])
            st.metric("Available Models", f"{available_models}/{len(summary)}")
        
        # Performance trends (simulated data)
        st.subheader("📈 Performance Trends")
        
        # Generate sample trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        
        trend_data = []
        for model_id, info in summary.items():
            for date in dates:
                # Simulate some variance in metrics over time
                import random
                base_latency = info['metrics']['latency_ms']
                trend_data.append({
                    'Date': date,
                    'Model': info['name'],
                    'Provider': info['provider'],
                    'Latency': base_latency * random.uniform(0.8, 1.2),
                    'Accuracy': info['metrics']['accuracy_score'] * random.uniform(0.95, 1.05),
                    'Cost': info['metrics']['cost_per_request'] * random.uniform(0.9, 1.1)
                })
        
        trend_df = pd.DataFrame(trend_data)
        
        # Latency trend chart
        fig_latency = px.line(
            trend_df,
            x='Date',
            y='Latency',
            color='Model',
            title='Latency Trends Over Time'
        )
        st.plotly_chart(fig_latency, use_container_width=True)
        
        # Performance heatmap
        st.subheader("🔥 Performance Heatmap")
        
        # Create performance matrix
        models = list(summary.keys())
        metrics = ['Latency', 'Accuracy', 'Cost', 'Availability']
        
        heatmap_data = []
        for model_id in models:
            info = summary[model_id]
            row = [
                info['metrics']['latency_ms'],
                info['metrics']['accuracy_score'],
                info['metrics']['cost_per_request'],
                info['metrics']['availability_percent']
            ]
            heatmap_data.append(row)
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=metrics,
            y=[summary[m]['name'] for m in models],
            colorscale='RdYlGn_r',
            text=[[f"{val:.3f}" for val in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig_heatmap.update_layout(
            title='Model Performance Heatmap',
            xaxis_title='Metrics',
            yaxis_title='Models'
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    def render_selection_history(self):
        """Render selection history interface"""
        st.header("📋 Selection History")
        
        # Display selection history
        if hasattr(self.engine, 'selection_history') and self.engine.selection_history:
            history_df = pd.DataFrame(self.engine.selection_history)
            
            st.subheader("Recent Selections")
            
            # Format the dataframe for display
            display_df = history_df.copy()
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    'timestamp': st.column_config.DatetimeColumn('Timestamp'),
                    'selection_score': st.column_config.NumberColumn('Score', format="%.3f"),
                    'estimated_latency': st.column_config.NumberColumn('Est. Latency (ms)', format="%.0f"),
                    'estimated_cost': st.column_config.NumberColumn('Est. Cost ($)', format="%.4f")
                }
            )
            
            # Selection statistics
            st.subheader("📊 Selection Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_selections = len(history_df)
                st.metric("Total Selections", total_selections)
            
            with col2:
                if 'selection_score' in history_df.columns:
                    avg_score = history_df['selection_score'].mean()
                    st.metric("Avg Selection Score", f"{avg_score:.3f}")
            
            with col3:
                if 'selected_model_id' in history_df.columns:
                    most_selected = history_df['selected_model_id'].mode().iloc[0] if len(history_df) > 0 else "N/A"
                    st.metric("Most Selected Model", most_selected)
            
        else:
            st.info("No selection history available. Make some model selections to see history here.")
            
            # Show sample data structure
            st.subheader("📝 Expected Data Structure")
            sample_data = {
                'request_id': ['req_001', 'req_002'],
                'selected_model_id': ['openai_whisper_1', 'local_whisper'],
                'selection_score': [0.85, 0.72],
                'estimated_latency': [2000, 5000],
                'estimated_cost': [0.006, 0.0],
                'timestamp': [datetime.now().isoformat(), datetime.now().isoformat()]
            }
            
            st.json(sample_data)

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="AI Model Selection Engine",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .selection-result {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize and render UI
    ui = ModelSelectionEngineUI()
    ui.render()

if __name__ == "__main__":
    main()