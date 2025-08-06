"""
LLM Provider Optimization UI Component
Streamlit interface for LLM provider comparison, A/B testing, and optimization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from llm_provider_optimization import (
    LLMProviderOptimizer, OptimizationStrategy, ABTestConfig, ABTestStatus,
    ProviderType, TaskType
)
from multi_llm_provider_system import MultiLLMProviderSystem

class LLMProviderOptimizationUI:
    """Streamlit UI for LLM provider optimization"""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_systems()
    
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="LLM Provider Optimization",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_systems(self):
        """Initialize optimization systems"""
        if 'provider_system' not in st.session_state:
            st.session_state.provider_system = MultiLLMProviderSystem()
        
        if 'optimizer' not in st.session_state:
            st.session_state.optimizer = LLMProviderOptimizer(st.session_state.provider_system)
    
    def render_main_interface(self):
        """Render the main interface"""
        st.title("⚡ LLM Provider Optimization & Comparison")
        st.markdown("Advanced analytics and optimization for multiple LLM providers")
        
        # Sidebar navigation
        page = self.render_sidebar()
        
        # Main content based on selected page
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "A/B Testing":
            self.render_ab_testing()
        elif page == "Cost Analysis":
            self.render_cost_analysis()
        elif page == "Performance Benchmarks":
            self.render_performance_benchmarks()
        elif page == "Provider Comparison":
            self.render_provider_comparison()
        elif page == "Recommendations":
            self.render_recommendations()
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        st.sidebar.header("🎛️ Navigation")
        
        pages = [
            "Dashboard",
            "A/B Testing", 
            "Cost Analysis",
            "Performance Benchmarks",
            "Provider Comparison",
            "Recommendations"
        ]
        
        selected_page = st.sidebar.selectbox("Select Page", pages)
        
        # Optimization strategy selector
        st.sidebar.header("⚙️ Settings")
        
        strategy_options = [s.value for s in OptimizationStrategy]
        current_strategy = st.sidebar.selectbox(
            "Optimization Strategy",
            strategy_options,
            index=strategy_options.index(st.session_state.optimizer.optimization_strategy.value)
        )
        
        if current_strategy != st.session_state.optimizer.optimization_strategy.value:
            st.session_state.optimizer.set_optimization_strategy(OptimizationStrategy(current_strategy))
            st.sidebar.success(f"Strategy updated to: {current_strategy}")
        
        # System status
        st.sidebar.header("📊 System Status")
        
        metrics_count = len(st.session_state.optimizer.metrics_cache)
        active_tests = len(st.session_state.optimizer.active_ab_tests)
        
        st.sidebar.metric("Providers Monitored", metrics_count)
        st.sidebar.metric("Active A/B Tests", active_tests)
        
        return selected_page    
  
  def render_dashboard(self):
        """Render main dashboard"""
        st.header("📊 Provider Performance Dashboard")
        
        optimizer = st.session_state.optimizer
        
        if not optimizer.metrics_cache:
            st.info("No provider metrics available yet. Start using the system to see data.")
            return
        
        # Key metrics overview
        col1, col2, col3, col4 = st.columns(4)
        
        total_requests = sum(m.total_requests for m in optimizer.metrics_cache.values())
        total_cost = sum(m.total_cost for m in optimizer.metrics_cache.values())
        avg_success_rate = sum(m.success_rate for m in optimizer.metrics_cache.values()) / len(optimizer.metrics_cache)
        avg_latency = sum(m.average_latency for m in optimizer.metrics_cache.values()) / len(optimizer.metrics_cache)
        
        with col1:
            st.metric("Total Requests", f"{total_requests:,}")
        
        with col2:
            st.metric("Total Cost", f"${total_cost:.2f}")
        
        with col3:
            st.metric("Avg Success Rate", f"{avg_success_rate:.1f}%")
        
        with col4:
            st.metric("Avg Latency", f"{avg_latency:.2f}s")
        
        # Provider performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_cost_comparison_chart()
        
        with col2:
            self.render_latency_comparison_chart()
        
        # Recent activity
        st.subheader("📈 Provider Metrics Table")
        self.render_metrics_table()
    
    def render_cost_comparison_chart(self):
        """Render cost comparison chart"""
        optimizer = st.session_state.optimizer
        
        providers = []
        costs = []
        
        for provider_type, metrics in optimizer.metrics_cache.items():
            providers.append(provider_type.value)
            costs.append(metrics.cost_per_token * 1000)  # Convert to cost per 1K tokens
        
        fig = px.bar(
            x=providers,
            y=costs,
            title="Cost per 1K Tokens by Provider",
            labels={'x': 'Provider', 'y': 'Cost per 1K Tokens ($)'}
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_latency_comparison_chart(self):
        """Render latency comparison chart"""
        optimizer = st.session_state.optimizer
        
        providers = []
        latencies = []
        
        for provider_type, metrics in optimizer.metrics_cache.items():
            providers.append(provider_type.value)
            latencies.append(metrics.average_latency)
        
        fig = px.bar(
            x=providers,
            y=latencies,
            title="Average Latency by Provider",
            labels={'x': 'Provider', 'y': 'Average Latency (seconds)'},
            color=latencies,
            color_continuous_scale='RdYlGn_r'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_metrics_table(self):
        """Render provider metrics table"""
        optimizer = st.session_state.optimizer
        
        data = []
        for provider_type, metrics in optimizer.metrics_cache.items():
            data.append({
                'Provider': provider_type.value,
                'Total Requests': metrics.total_requests,
                'Success Rate': f"{metrics.success_rate:.1f}%",
                'Avg Latency': f"{metrics.average_latency:.2f}s",
                'Cost/Token': f"${metrics.cost_per_token:.6f}",
                'Total Cost': f"${metrics.total_cost:.2f}",
                'Quality Score': f"{metrics.average_quality_score:.2f}/5.0",
                'Uptime': f"{metrics.uptime_percentage:.1f}%"
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    def render_ab_testing(self):
        """Render A/B testing interface"""
        st.header("🧪 A/B Testing")
        
        tab1, tab2, tab3 = st.tabs(["Create Test", "Active Tests", "Results"])
        
        with tab1:
            self.render_create_ab_test()
        
        with tab2:
            self.render_active_tests()
        
        with tab3:
            self.render_ab_test_results()
    
    def render_create_ab_test(self):
        """Render A/B test creation form"""
        st.subheader("Create New A/B Test")
        
        with st.form("create_ab_test"):
            test_name = st.text_input("Test Name", placeholder="e.g., GPT vs Claude Comparison")
            test_description = st.text_area("Description", placeholder="Describe the purpose of this test")
            
            # Provider selection
            available_providers = [p.value for p in ProviderType]
            selected_providers = st.multiselect(
                "Select Providers to Test",
                available_providers,
                default=available_providers[:2] if len(available_providers) >= 2 else available_providers
            )
            
            # Traffic split
            st.write("Traffic Split:")
            traffic_split = {}
            remaining_traffic = 100.0
            
            for i, provider in enumerate(selected_providers):
                if i == len(selected_providers) - 1:
                    # Last provider gets remaining traffic
                    split = remaining_traffic
                    st.write(f"{provider}: {split:.1f}%")
                else:
                    split = st.slider(
                        f"{provider} Traffic %",
                        min_value=0.0,
                        max_value=remaining_traffic,
                        value=remaining_traffic / (len(selected_providers) - i),
                        step=5.0
                    )
                    remaining_traffic -= split
                
                traffic_split[ProviderType(provider)] = split / 100.0
            
            # Task types
            available_tasks = [t.value for t in TaskType]
            selected_tasks = st.multiselect(
                "Task Types",
                available_tasks,
                default=[TaskType.TEXT_GENERATION.value]
            )
            
            # Test parameters
            col1, col2 = st.columns(2)
            
            with col1:
                min_samples = st.number_input("Minimum Samples", min_value=10, value=100)
                confidence_level = st.slider("Confidence Level", 0.90, 0.99, 0.95, 0.01)
            
            with col2:
                start_date = st.date_input("Start Date", datetime.now().date())
                end_date = st.date_input("End Date (Optional)", None)
            
            submitted = st.form_submit_button("Create A/B Test")
            
            if submitted:
                if len(selected_providers) < 2:
                    st.error("Please select at least 2 providers for A/B testing")
                elif not test_name:
                    st.error("Please provide a test name")
                else:
                    try:
                        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        config = ABTestConfig(
                            test_id=test_id,
                            name=test_name,
                            description=test_description,
                            providers=[ProviderType(p) for p in selected_providers],
                            traffic_split=traffic_split,
                            task_types=[TaskType(t) for t in selected_tasks],
                            start_date=datetime.combine(start_date, datetime.min.time()),
                            end_date=datetime.combine(end_date, datetime.min.time()) if end_date else None,
                            min_samples=min_samples,
                            confidence_level=confidence_level
                        )
                        
                        st.session_state.optimizer.create_ab_test(config)
                        st.success(f"✅ A/B test '{test_name}' created successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error creating A/B test: {e}")
    
    def render_active_tests(self):
        """Render active A/B tests"""
        st.subheader("Active A/B Tests")
        
        optimizer = st.session_state.optimizer
        
        if not optimizer.active_ab_tests:
            st.info("No active A/B tests. Create one in the 'Create Test' tab.")
            return
        
        for test_id, config in optimizer.active_ab_tests.items():
            with st.expander(f"📊 {config.name} ({test_id})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Description:** {config.description}")
                    st.write(f"**Status:** {config.status.value}")
                    st.write(f"**Start Date:** {config.start_date.strftime('%Y-%m-%d %H:%M')}")
                    if config.end_date:
                        st.write(f"**End Date:** {config.end_date.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    st.write("**Providers:**")
                    for provider, split in config.traffic_split.items():
                        st.write(f"  • {provider.value}: {split:.1%}")
                    
                    st.write("**Task Types:**")
                    for task_type in config.task_types:
                        st.write(f"  • {task_type.value}")
                
                # Control buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"Pause Test", key=f"pause_{test_id}"):
                        config.status = ABTestStatus.PAUSED
                        st.success("Test paused")
                        st.rerun()
                
                with col2:
                    if st.button(f"Resume Test", key=f"resume_{test_id}"):
                        config.status = ABTestStatus.ACTIVE
                        st.success("Test resumed")
                        st.rerun()
                
                with col3:
                    if st.button(f"Stop Test", key=f"stop_{test_id}"):
                        config.status = ABTestStatus.COMPLETED
                        st.success("Test completed")
                        st.rerun()
    
    def render_ab_test_results(self):
        """Render A/B test results"""
        st.subheader("A/B Test Results")
        
        optimizer = st.session_state.optimizer
        
        if not optimizer.active_ab_tests:
            st.info("No A/B tests available.")
            return
        
        # Test selection
        test_options = {f"{config.name} ({test_id})": test_id 
                       for test_id, config in optimizer.active_ab_tests.items()}
        
        selected_test_display = st.selectbox("Select Test", list(test_options.keys()))
        
        if selected_test_display:
            test_id = test_options[selected_test_display]
            
            try:
                results = optimizer.analyze_ab_test_results(test_id)
                
                if not results:
                    st.info("No results available yet. Test may need more samples.")
                    return
                
                # Results summary
                st.write("### Test Results Summary")
                
                results_data = []
                for result in results:
                    results_data.append({
                        'Provider': result.provider_type.value,
                        'Sample Size': result.sample_size,
                        'Success Rate': f"{result.metrics.success_rate:.1f}%",
                        'Avg Latency': f"{result.metrics.average_latency:.2f}s",
                        'Cost/Token': f"${result.metrics.cost_per_token:.6f}",
                        'Quality Score': f"{result.metrics.average_quality_score:.2f}",
                        'Statistically Significant': "✅" if result.statistical_significance else "❌",
                        'P-Value': f"{result.p_value:.4f}"
                    })
                
                df = pd.DataFrame(results_data)
                st.dataframe(df, use_container_width=True)
                
                # Visualization
                if len(results) >= 2:
                    self.render_ab_test_charts(results)
                
            except Exception as e:
                st.error(f"Error analyzing test results: {e}")
    
    def render_ab_test_charts(self, results):
        """Render A/B test result charts"""
        providers = [r.provider_type.value for r in results]
        success_rates = [r.metrics.success_rate for r in results]
        latencies = [r.metrics.average_latency for r in results]
        costs = [r.metrics.cost_per_token * 1000 for r in results]
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=providers,
                y=success_rates,
                title="Success Rate Comparison",
                labels={'x': 'Provider', 'y': 'Success Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                x=providers,
                y=latencies,
                title="Latency Comparison",
                labels={'x': 'Provider', 'y': 'Average Latency (s)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_cost_analysis(self):
        """Render cost analysis interface"""
        st.header("💰 Cost Analysis")
        
        # Period selection
        col1, col2 = st.columns(2)
        
        with col1:
            period_days = st.selectbox(
                "Analysis Period",
                [7, 14, 30, 60, 90],
                index=2,
                format_func=lambda x: f"Last {x} days"
            )
        
        with col2:
            if st.button("🔄 Refresh Analysis"):
                with st.spinner("Analyzing costs..."):
                    analyses = st.session_state.optimizer.analyze_costs(period_days)
                    st.session_state.cost_analyses = analyses
                st.success("Cost analysis updated!")
        
        # Display cost analysis
        if hasattr(st.session_state, 'cost_analyses'):
            analyses = st.session_state.cost_analyses
            
            if not analyses:
                st.info("No cost data available for the selected period.")
                return
            
            # Cost overview
            total_cost = sum(a.total_cost for a in analyses)
            total_requests = sum(a.total_requests for a in analyses)
            total_tokens = sum(a.total_tokens for a in analyses)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Cost", f"${total_cost:.2f}")
            
            with col2:
                st.metric("Total Requests", f"{total_requests:,}")
            
            with col3:
                st.metric("Total Tokens", f"{total_tokens:,}")
            
            # Cost breakdown charts
            self.render_cost_breakdown_charts(analyses)
            
            # Detailed cost table
            st.subheader("📊 Detailed Cost Breakdown")
            
            cost_data = []
            for analysis in analyses:
                cost_data.append({
                    'Provider': analysis.provider_type.value,
                    'Total Cost': f"${analysis.total_cost:.2f}",
                    'Requests': analysis.total_requests,
                    'Tokens': f"{analysis.total_tokens:,}",
                    'Cost/Request': f"${analysis.cost_per_request:.4f}",
                    'Cost/Token': f"${analysis.cost_per_token:.6f}",
                    'Projected Monthly': f"${analysis.projected_monthly_cost:.2f}"
                })
            
            df = pd.DataFrame(cost_data)
            st.dataframe(df, use_container_width=True)
    
    def render_cost_breakdown_charts(self, analyses):
        """Render cost breakdown charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost by provider pie chart
            providers = [a.provider_type.value for a in analyses]
            costs = [a.total_cost for a in analyses]
            
            fig = px.pie(
                values=costs,
                names=providers,
                title="Cost Distribution by Provider"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Projected monthly costs
            providers = [a.provider_type.value for a in analyses]
            projected_costs = [a.projected_monthly_cost for a in analyses]
            
            fig = px.bar(
                x=providers,
                y=projected_costs,
                title="Projected Monthly Costs",
                labels={'x': 'Provider', 'y': 'Projected Monthly Cost ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_performance_benchmarks(self):
        """Render performance benchmarks interface"""
        st.header("🏃 Performance Benchmarks")
        
        # Benchmark controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            available_providers = [p.value for p in ProviderType]
            selected_providers = st.multiselect(
                "Select Providers",
                available_providers,
                default=available_providers[:2] if len(available_providers) >= 2 else available_providers
            )
        
        with col2:
            available_tasks = [t.value for t in TaskType]
            selected_tasks = st.multiselect(
                "Select Task Types",
                available_tasks,
                default=[TaskType.TEXT_GENERATION.value]
            )
        
        with col3:
            if st.button("🚀 Run Benchmarks"):
                if selected_providers and selected_tasks:
                    with st.spinner("Running benchmarks... This may take a few minutes."):
                        try:
                            providers = [ProviderType(p) for p in selected_providers]
                            tasks = [TaskType(t) for t in selected_tasks]
                            
                            benchmarks = st.session_state.optimizer.run_performance_benchmark(providers, tasks)
                            st.session_state.benchmarks = benchmarks
                            st.success("✅ Benchmarks completed!")
                            
                        except Exception as e:
                            st.error(f"Error running benchmarks: {e}")
                else:
                    st.error("Please select providers and task types")
        
        # Display benchmark results
        if hasattr(st.session_state, 'benchmarks'):
            benchmarks = st.session_state.benchmarks
            
            if benchmarks:
                st.subheader("📊 Benchmark Results")
                
                # Benchmark summary table
                benchmark_data = []
                for benchmark in benchmarks:
                    benchmark_data.append({
                        'Provider': benchmark.provider_type.value,
                        'Task Type': benchmark.task_type.value,
                        'Overall Score': f"{benchmark.overall_score:.1f}/100",
                        'Latency P50': f"{benchmark.latency_p50:.2f}s",
                        'Latency P95': f"{benchmark.latency_p95:.2f}s",
                        'Throughput': f"{benchmark.throughput_rps:.1f} req/s",
                        'Quality Score': f"{benchmark.quality_score:.2f}/5.0",
                        'Reliability': f"{benchmark.reliability_score:.1f}%",
                        'Cost Efficiency': f"{benchmark.cost_efficiency_score:.2f}"
                    })
                
                df = pd.DataFrame(benchmark_data)
                st.dataframe(df, use_container_width=True)
                
                # Benchmark visualization
                self.render_benchmark_charts(benchmarks)
    
    def render_benchmark_charts(self, benchmarks):
        """Render benchmark result charts"""
        # Overall score comparison
        providers = [b.provider_type.value for b in benchmarks]
        overall_scores = [b.overall_score for b in benchmarks]
        
        fig = px.bar(
            x=providers,
            y=overall_scores,
            title="Overall Performance Score",
            labels={'x': 'Provider', 'y': 'Overall Score'},
            color=overall_scores,
            color_continuous_scale='RdYlGn'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Multi-metric radar chart
        if len(benchmarks) >= 2:
            self.render_radar_chart(benchmarks)
    
    def render_radar_chart(self, benchmarks):
        """Render radar chart for multi-metric comparison"""
        fig = go.Figure()
        
        metrics = ['Quality Score', 'Reliability', 'Cost Efficiency', 'Throughput']
        
        for benchmark in benchmarks:
            values = [
                benchmark.quality_score * 20,  # Scale to 0-100
                benchmark.reliability_score,
                min(100, benchmark.cost_efficiency_score * 10),  # Scale and cap
                min(100, benchmark.throughput_rps * 10)  # Scale and cap
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metrics,
                fill='toself',
                name=f"{benchmark.provider_type.value} - {benchmark.task_type.value}"
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Multi-Metric Performance Comparison"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_provider_comparison(self):
        """Render provider comparison interface"""
        st.header("🔍 Provider Comparison")
        
        # Provider selection
        available_providers = [p.value for p in ProviderType]
        selected_providers = st.multiselect(
            "Select Providers to Compare",
            available_providers,
            default=available_providers[:3] if len(available_providers) >= 3 else available_providers
        )
        
        if len(selected_providers) < 2:
            st.info("Please select at least 2 providers to compare.")
            return
        
        # Get comparison data
        providers = [ProviderType(p) for p in selected_providers]
        comparison = st.session_state.optimizer.get_provider_comparison(providers)
        
        if not comparison['providers']:
            st.info("No data available for selected providers.")
            return
        
        # Comparison table
        st.subheader("📊 Provider Comparison Table")
        
        df = pd.DataFrame(comparison['providers'])
        st.dataframe(df, use_container_width=True)
        
        # Comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost comparison
            fig = px.bar(
                df,
                x='provider',
                y='cost_per_token',
                title="Cost per Token Comparison",
                labels={'provider': 'Provider', 'cost_per_token': 'Cost per Token ($)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Latency comparison
            fig = px.bar(
                df,
                x='provider',
                y='average_latency',
                title="Average Latency Comparison",
                labels={'provider': 'Provider', 'average_latency': 'Average Latency (s)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        if comparison['recommendations']:
            st.subheader("💡 Recommendations")
            for rec in comparison['recommendations']:
                st.write(f"• {rec}")
    
    def render_recommendations(self):
        """Render optimization recommendations"""
        st.header("💡 Optimization Recommendations")
        
        if st.button("🔄 Generate New Recommendations"):
            with st.spinner("Analyzing system performance..."):
                recommendations = st.session_state.optimizer.generate_optimization_recommendations()
                st.session_state.recommendations = recommendations
            st.success("Recommendations updated!")
        
        if hasattr(st.session_state, 'recommendations'):
            recommendations = st.session_state.recommendations
            
            if not recommendations:
                st.info("No optimization recommendations at this time. System is performing well!")
                return
            
            for i, rec in enumerate(recommendations, 1):
                with st.expander(f"💡 Recommendation {i}: {rec.recommendation_type.replace('_', ' ').title()}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Provider:** {rec.provider_type.value}")
                        if rec.task_type:
                            st.write(f"**Task Type:** {rec.task_type.value}")
                        st.write(f"**Current Cost:** ${rec.current_cost:.2f}")
                        st.write(f"**Projected Cost:** ${rec.projected_cost:.2f}")
                    
                    with col2:
                        st.write(f"**Potential Savings:** ${rec.potential_savings:.2f}")
                        st.write(f"**Confidence:** {rec.confidence_score:.1%}")
                        
                        # Progress bar for confidence
                        st.progress(rec.confidence_score)
                    
                    st.write(f"**Description:** {rec.description}")
                    
                    st.write("**Action Items:**")
                    for action in rec.action_items:
                        st.write(f"• {action}")

def main():
    """Main function to run the Streamlit app"""
    ui = LLMProviderOptimizationUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()