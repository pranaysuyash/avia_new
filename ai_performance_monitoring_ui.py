#!/usr/bin/env python3
"""
AI Performance Monitoring UI
Streamlit interface for AI performance monitoring and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json

from ai_performance_monitoring import (
    PerformanceMonitor, RequestMetrics, AlertThreshold, 
    MetricType, AlertSeverity, ResourceUsage
)

class PerformanceMonitoringUI:
    """Streamlit UI for AI Performance Monitoring"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.monitor.start_monitoring()
        
        # Initialize session state
        if 'monitor_data' not in st.session_state:
            st.session_state.monitor_data = []
        if 'alerts_configured' not in st.session_state:
            st.session_state.alerts_configured = False
    
    def render(self):
        """Render the complete monitoring interface"""
        st.set_page_config(
            page_title="AI Performance Monitor",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("🤖 AI Performance Monitoring Dashboard")
        st.markdown("Real-time monitoring and analytics for AI model performance")
        
        # Sidebar for controls
        self._render_sidebar()
        
        # Main dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Real-time Metrics", 
            "📊 Performance Analytics", 
            "🚨 Alerts & Monitoring",
            "📉 Trend Analysis",
            "⚖️ Model Comparison"
        ])
        
        with tab1:
            self._render_realtime_metrics()
        
        with tab2:
            self._render_performance_analytics()
        
        with tab3:
            self._render_alerts_monitoring()
        
        with tab4:
            self._render_trend_analysis()
        
        with tab5:
            self._render_model_comparison()
    
    def _render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.header("🎛️ Controls")
        
        # Demo data generation
        st.sidebar.subheader("Demo Data")
        if st.sidebar.button("Generate Sample Data"):
            self._generate_sample_data()
            st.sidebar.success("Sample data generated!")
        
        # Monitoring controls
        st.sidebar.subheader("Monitoring")
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        # Clear data
        if st.sidebar.button("Clear All Data"):
            self.monitor = PerformanceMonitor()
            st.session_state.monitor_data = []
            st.sidebar.success("Data cleared!")
        
        # Export data
        if st.sidebar.button("Export Metrics"):
            export_data = self.monitor.export_metrics()
            st.sidebar.download_button(
                "Download JSON",
                export_data,
                file_name=f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def _render_realtime_metrics(self):
        """Render real-time metrics dashboard"""
        st.header("📈 Real-time Performance Metrics")
        
        # Get available models
        models = self._get_available_models()
        
        if not models:
            st.info("No performance data available. Generate sample data to see metrics.")
            return
        
        # Model selector
        selected_model = st.selectbox("Select Model", models)
        
        if selected_model:
            # Get real-time metrics
            realtime_data = self.monitor.get_realtime_metrics(selected_model)
            
            if realtime_data:
                # Display key metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Throughput (RPS)",
                        f"{realtime_data.get('current_throughput', 0):.2f}",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "Avg Latency (ms)",
                        f"{realtime_data.get('avg_latency', 0):.1f}",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        "Error Rate (%)",
                        f"{realtime_data.get('error_rate', 0):.2f}",
                        delta=None
                    )
                
                with col4:
                    st.metric(
                        "Total Requests",
                        f"{realtime_data.get('total_requests', 0):,}",
                        delta=None
                    )
                
                # Real-time charts
                self._render_realtime_charts(selected_model)
            else:
                st.warning(f"No real-time data available for {selected_model}")
    
    def _render_performance_analytics(self):
        """Render performance analytics dashboard"""
        st.header("📊 Performance Analytics")
        
        models = self._get_available_models()
        if not models:
            st.info("No performance data available.")
            return
        
        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox("Select Model", models, key="analytics_model")
        with col2:
            timeframe_hours = st.selectbox(
                "Time Range", 
                [1, 6, 12, 24, 48, 168], 
                format_func=lambda x: f"{x} hours" if x < 24 else f"{x//24} days"
            )
        
        if selected_model:
            timeframe = timedelta(hours=timeframe_hours)
            metrics = self.monitor.get_performance_metrics(selected_model, timeframe=timeframe)
            
            if metrics:
                # Performance summary
                st.subheader("Performance Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Requests", f"{metrics.total_requests:,}")
                    st.metric("Success Rate", f"{(metrics.successful_requests/metrics.total_requests)*100:.1f}%")
                
                with col2:
                    st.metric("Avg Latency", f"{metrics.avg_latency_ms:.1f} ms")
                    st.metric("P95 Latency", f"{metrics.p95_latency_ms:.1f} ms")
                
                with col3:
                    st.metric("Throughput", f"{metrics.throughput_rps:.2f} RPS")
                    st.metric("Total Cost", f"${metrics.total_cost:.4f}")
                
                # Detailed charts
                self._render_performance_charts(metrics)
            else:
                st.warning(f"No analytics data available for {selected_model}")
    
    def _render_alerts_monitoring(self):
        """Render alerts and monitoring configuration"""
        st.header("🚨 Alerts & Monitoring")
        
        # Alert configuration
        st.subheader("Configure Alerts")
        
        models = self._get_available_models()
        if models:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                alert_model = st.selectbox("Model", models, key="alert_model")
            
            with col2:
                metric_type = st.selectbox(
                    "Metric", 
                    [MetricType.LATENCY, MetricType.ERROR_RATE, MetricType.COST, MetricType.THROUGHPUT],
                    format_func=lambda x: x.value.replace('_', ' ').title()
                )
            
            with col3:
                comparison = st.selectbox("Condition", ["gt", "lt", "eq"], 
                                        format_func=lambda x: {"gt": ">", "lt": "<", "eq": "="}[x])
            
            with col4:
                threshold_value = st.number_input("Threshold", min_value=0.0, value=100.0)
            
            severity = st.selectbox("Severity", list(AlertSeverity), 
                                  format_func=lambda x: x.value.title())
            
            if st.button("Add Alert Threshold"):
                threshold = AlertThreshold(
                    metric_type=metric_type,
                    threshold_value=threshold_value,
                    comparison=comparison,
                    severity=severity
                )
                self.monitor.set_alert_threshold(alert_model, threshold)
                st.success(f"Alert threshold added for {alert_model}")
        
        # Active alerts
        st.subheader("Active Alerts")
        active_alerts = self.monitor.get_active_alerts()
        
        if active_alerts:
            alerts_data = []
            for alert in active_alerts:
                alerts_data.append({
                    "ID": alert.id,
                    "Model": alert.model_id,
                    "Metric": alert.metric_type.value,
                    "Current": f"{alert.current_value:.2f}",
                    "Threshold": f"{alert.threshold_value:.2f}",
                    "Severity": alert.severity.value,
                    "Time": alert.timestamp.strftime("%H:%M:%S"),
                    "Resolved": alert.resolved
                })
            
            df_alerts = pd.DataFrame(alerts_data)
            st.dataframe(df_alerts, use_container_width=True)
            
            # Resolve alerts
            if st.button("Resolve All Alerts"):
                for alert in active_alerts:
                    self.monitor.resolve_alert(alert.id)
                st.success("All alerts resolved!")
        else:
            st.info("No active alerts")
    
    def _render_trend_analysis(self):
        """Render trend analysis dashboard"""
        st.header("📉 Trend Analysis")
        
        models = self._get_available_models()
        if not models:
            st.info("No trend data available.")
            return
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_model = st.selectbox("Select Model", models, key="trend_model")
        with col2:
            metric_type = st.selectbox(
                "Metric Type", 
                [MetricType.LATENCY, MetricType.ERROR_RATE, MetricType.COST, MetricType.THROUGHPUT],
                format_func=lambda x: x.value.replace('_', ' ').title(),
                key="trend_metric"
            )
        with col3:
            period_days = st.selectbox("Analysis Period", [1, 3, 7, 14, 30], 
                                     format_func=lambda x: f"{x} days")
        
        if selected_model:
            period = timedelta(days=period_days)
            trend = self.monitor.analyze_trends(selected_model, metric_type, period)
            
            if trend:
                # Trend summary
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    direction_color = {
                        "improving": "🟢",
                        "degrading": "🔴", 
                        "stable": "🟡"
                    }
                    st.metric(
                        "Trend Direction",
                        f"{direction_color.get(trend.trend_direction, '⚪')} {trend.trend_direction.title()}"
                    )
                
                with col2:
                    st.metric("Trend Strength", f"{trend.trend_strength:.2f}")
                
                with col3:
                    st.metric("Prediction", f"{trend.prediction:.2f}")
                
                with col4:
                    st.metric("Confidence", f"{trend.confidence:.2f}")
                
                # Trend visualization
                st.subheader("Trend Visualization")
                
                # Generate sample trend data for visualization
                trend_data = self._generate_trend_chart_data(trend)
                if trend_data:
                    fig = px.line(
                        trend_data, 
                        x="time", 
                        y="value",
                        title=f"{metric_type.value.replace('_', ' ').title()} Trend for {selected_model}",
                        labels={"value": metric_type.value.replace('_', ' ').title()}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No trend data available for {selected_model}")
    
    def _render_model_comparison(self):
        """Render model comparison dashboard"""
        st.header("⚖️ Model Comparison")
        
        models = self._get_available_models()
        if len(models) < 2:
            st.info("Need at least 2 models for comparison.")
            return
        
        # Model selection
        selected_models = st.multiselect("Select Models to Compare", models, default=models[:3])
        
        if len(selected_models) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                metric_type = st.selectbox(
                    "Comparison Metric",
                    [MetricType.LATENCY, MetricType.THROUGHPUT, MetricType.ERROR_RATE, MetricType.COST],
                    format_func=lambda x: x.value.replace('_', ' ').title(),
                    key="comparison_metric"
                )
            with col2:
                timeframe_hours = st.selectbox(
                    "Time Range",
                    [1, 6, 12, 24],
                    format_func=lambda x: f"{x} hours",
                    key="comparison_timeframe"
                )
            
            # Get comparison data
            timeframe = timedelta(hours=timeframe_hours)
            comparison = self.monitor.get_model_comparison(selected_models, metric_type, timeframe)
            
            if comparison and comparison.get("rankings"):
                # Comparison chart
                rankings = comparison["rankings"]
                models_list = [item[0] for item in rankings]
                values = [item[1]["value"] for item in rankings]
                
                fig = px.bar(
                    x=models_list,
                    y=values,
                    title=f"Model Comparison: {metric_type.value.replace('_', ' ').title()}",
                    labels={"x": "Model", "y": metric_type.value.replace('_', ' ').title()}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed comparison table
                st.subheader("Detailed Comparison")
                comparison_data = []
                for model, data in rankings:
                    comparison_data.append({
                        "Model": model,
                        "Value": f"{data['value']:.3f}",
                        "Total Requests": data['total_requests'],
                        "Success Rate": f"{data['success_rate']:.1f}%"
                    })
                
                df_comparison = pd.DataFrame(comparison_data)
                st.dataframe(df_comparison, use_container_width=True)
                
                # Best model highlight
                if comparison.get("best_model"):
                    st.success(f"🏆 Best performing model: **{comparison['best_model']}**")
            else:
                st.warning("No comparison data available for selected models")
    
    def _render_realtime_charts(self, model_id: str):
        """Render real-time performance charts"""
        st.subheader("Real-time Performance Charts")
        
        # Generate sample real-time data
        chart_data = self._generate_realtime_chart_data(model_id)
        
        if chart_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Latency chart
                fig_latency = px.line(
                    chart_data, 
                    x="timestamp", 
                    y="latency",
                    title="Latency Over Time",
                    labels={"latency": "Latency (ms)"}
                )
                st.plotly_chart(fig_latency, use_container_width=True)
            
            with col2:
                # Throughput chart
                fig_throughput = px.line(
                    chart_data, 
                    x="timestamp", 
                    y="throughput",
                    title="Throughput Over Time",
                    labels={"throughput": "Requests/sec"}
                )
                st.plotly_chart(fig_throughput, use_container_width=True)
    
    def _render_performance_charts(self, metrics):
        """Render detailed performance charts"""
        st.subheader("Performance Distribution")
        
        # Create sample distribution data
        latency_dist = self._generate_latency_distribution()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Latency distribution
            fig_hist = px.histogram(
                x=latency_dist,
                nbins=20,
                title="Latency Distribution",
                labels={"x": "Latency (ms)", "y": "Frequency"}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Resource usage gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=metrics.resource_usage.cpu_percent,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "CPU Usage (%)"},
                gauge={'axis': {'range': [None, 100]},
                      'bar': {'color': "darkblue"},
                      'steps': [
                          {'range': [0, 50], 'color': "lightgray"},
                          {'range': [50, 80], 'color': "yellow"},
                          {'range': [80, 100], 'color': "red"}],
                      'threshold': {'line': {'color': "red", 'width': 4},
                                  'thickness': 0.75, 'value': 90}}))
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    def _get_available_models(self) -> List[str]:
        """Get list of available models from monitoring data"""
        models = set()
        
        # Get models from request history
        if hasattr(self.monitor, 'request_history'):
            for req in self.monitor.request_history:
                models.add(req.model_id)
        
        # Add sample models if none exist
        if not models:
            models = {"gpt-4", "gpt-3.5-turbo", "claude-3", "local-llama"}
        
        return sorted(list(models))
    
    def _generate_sample_data(self):
        """Generate sample performance data for demonstration"""
        import random
        
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "local-llama"]
        providers = ["openai", "openai", "anthropic", "local"]
        
        # Generate 50 sample requests
        for i in range(50):
            model_idx = random.randint(0, len(models) - 1)
            
            request_metrics = RequestMetrics(
                request_id=f"req_{i:04d}",
                model_id=models[model_idx],
                provider=providers[model_idx],
                start_time=datetime.now() - timedelta(minutes=random.randint(1, 60)),
                end_time=datetime.now() - timedelta(minutes=random.randint(0, 59)),
                latency_ms=random.uniform(50, 2000),
                success=random.random() > 0.05,  # 95% success rate
                input_tokens=random.randint(10, 1000),
                output_tokens=random.randint(10, 500),
                cost=random.uniform(0.001, 0.1),
                quality_score=random.uniform(0.7, 1.0),
                resource_usage=ResourceUsage(
                    cpu_percent=random.uniform(10, 80),
                    memory_mb=random.uniform(100, 1000),
                    gpu_percent=random.uniform(0, 90)
                )
            )
            
            # Fix end_time to be after start_time
            if request_metrics.end_time <= request_metrics.start_time:
                request_metrics.end_time = request_metrics.start_time + timedelta(milliseconds=request_metrics.latency_ms)
            
            self.monitor.track_request(request_metrics)
    
    def _generate_realtime_chart_data(self, model_id: str) -> pd.DataFrame:
        """Generate sample real-time chart data"""
        import random
        
        timestamps = []
        latencies = []
        throughputs = []
        
        base_time = datetime.now() - timedelta(minutes=30)
        
        for i in range(30):
            timestamps.append(base_time + timedelta(minutes=i))
            latencies.append(random.uniform(100, 500))
            throughputs.append(random.uniform(1, 10))
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "latency": latencies,
            "throughput": throughputs
        })
    
    def _generate_latency_distribution(self) -> List[float]:
        """Generate sample latency distribution data"""
        import random
        return [random.gauss(200, 50) for _ in range(1000)]
    
    def _generate_trend_chart_data(self, trend) -> pd.DataFrame:
        """Generate sample trend chart data"""
        import random
        
        timestamps = []
        values = []
        
        base_time = datetime.now() - trend.analysis_period
        
        for i in range(trend.data_points):
            timestamps.append(base_time + timedelta(hours=i))
            # Simulate trend based on direction
            if trend.trend_direction == "improving":
                values.append(100 - i * 2 + random.uniform(-5, 5))
            elif trend.trend_direction == "degrading":
                values.append(100 + i * 2 + random.uniform(-5, 5))
            else:
                values.append(100 + random.uniform(-10, 10))
        
        return pd.DataFrame({
            "time": timestamps,
            "value": values
        })

def main():
    """Main function to run the Streamlit app"""
    ui = PerformanceMonitoringUI()
    ui.render()

if __name__ == "__main__":
    main()