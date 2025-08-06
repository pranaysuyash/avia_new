"""
Multi-LLM Provider System UI
Streamlit interface for managing and testing multiple LLM providers
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from multi_llm_provider_system import (
    MultiLLMProviderSystem, LLMRequest, LLMProvider, TaskType,
    ProviderConfig, ProviderStats
)

class MultiLLMProviderUI:
    """Streamlit UI for Multi-LLM Provider System"""
    
    def __init__(self):
        self.setup_page_config()
        if 'llm_system' not in st.session_state:
            st.session_state.llm_system = MultiLLMProviderSystem()
    
    def setup_page_config(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="Multi-LLM Provider System",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_main_interface(self):
        """Render the main interface"""
        st.title("🤖 Multi-LLM Provider System")
        st.markdown("Manage and test multiple LLM providers with intelligent fallback and optimization")
        
        # Sidebar for navigation
        self.render_sidebar()
        
        # Main content based on selected tab
        if st.session_state.get('selected_tab', 'Testing') == 'Testing':
            self.render_testing_interface()
        elif st.session_state.selected_tab == 'Configuration':
            self.render_configuration_interface()
        elif st.session_state.selected_tab == 'Analytics':
            self.render_analytics_interface()
        elif st.session_state.selected_tab == 'Comparison':
            self.render_comparison_interface()
    
    def render_sidebar(self):
        """Render sidebar navigation and controls"""
        st.sidebar.header("🎛️ Navigation")
        
        # Tab selection
        tabs = ['Testing', 'Configuration', 'Analytics', 'Comparison']
        selected_tab = st.sidebar.selectbox("Select View", tabs)
        st.session_state.selected_tab = selected_tab
        
        st.sidebar.markdown("---")
        
        # System status
        st.sidebar.subheader("📊 System Status")
        
        system = st.session_state.llm_system
        available_providers = list(system.providers.keys())
        
        st.sidebar.metric("Available Providers", len(available_providers))
        st.sidebar.metric("Cache Size", len(system.request_cache))
        
        # Provider status
        st.sidebar.subheader("🔌 Provider Status")
        for provider in LLMProvider:
            if provider in available_providers:
                st.sidebar.success(f"✅ {provider.value}")
            else:
                st.sidebar.error(f"❌ {provider.value}")
        
        st.sidebar.markdown("---")
        
        # Quick actions
        st.sidebar.subheader("⚡ Quick Actions")
        
        if st.sidebar.button("🗑️ Clear Cache"):
            system.clear_cache()
            st.sidebar.success("Cache cleared!")
        
        if st.sidebar.button("🔄 Refresh Stats"):
            st.rerun()
    
    def render_testing_interface(self):
        """Render the testing interface"""
        st.header("🧪 LLM Provider Testing")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input form
            st.subheader("📝 Test Request")
            
            with st.form("llm_test_form"):
                prompt = st.text_area(
                    "Prompt",
                    placeholder="Enter your prompt here...",
                    height=100
                )
                
                col_task, col_tokens = st.columns(2)
                
                with col_task:
                    task_type = st.selectbox(
                        "Task Type",
                        options=[task.value for task in TaskType],
                        format_func=lambda x: x.replace('_', ' ').title()
                    )
                
                with col_tokens:
                    max_tokens = st.number_input(
                        "Max Tokens",
                        min_value=50,
                        max_value=4000,
                        value=500,
                        step=50
                    )
                
                col_temp, col_provider = st.columns(2)
                
                with col_temp:
                    temperature = st.slider(
                        "Temperature",
                        min_value=0.0,
                        max_value=2.0,
                        value=0.7,
                        step=0.1
                    )
                
                with col_provider:
                    use_fallback = st.checkbox("Use Fallback Chain", value=True)
                    if not use_fallback:
                        specific_provider = st.selectbox(
                            "Specific Provider",
                            options=[p.value for p in st.session_state.llm_system.providers.keys()]
                        )
                
                system_message = st.text_input(
                    "System Message (Optional)",
                    placeholder="You are a helpful assistant..."
                )
                
                context = st.text_area(
                    "Context (Optional)",
                    placeholder="Additional context for the request...",
                    height=60
                )
                
                submitted = st.form_submit_button("🚀 Generate Response", type="primary")
                
                if submitted and prompt:
                    self.process_test_request(
                        prompt, task_type, max_tokens, temperature,
                        system_message, context, use_fallback,
                        specific_provider if not use_fallback else None
                    )
        
        with col2:
            # Quick test templates
            st.subheader("📋 Quick Templates")
            
            templates = {
                "Text Generation": {
                    "prompt": "Write a short story about a robot learning to paint",
                    "task_type": TaskType.TEXT_GENERATION.value,
                    "max_tokens": 300
                },
                "Summarization": {
                    "prompt": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.",
                    "task_type": TaskType.SUMMARIZATION.value,
                    "max_tokens": 100
                },
                "Entity Extraction": {
                    "prompt": "Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976 in Cupertino, California.",
                    "task_type": TaskType.ENTITY_EXTRACTION.value,
                    "max_tokens": 150
                },
                "Classification": {
                    "prompt": "This movie was absolutely fantastic! The acting was superb and the plot kept me engaged throughout.",
                    "task_type": TaskType.CLASSIFICATION.value,
                    "max_tokens": 50
                }
            }
            
            for template_name, template_data in templates.items():
                if st.button(f"📄 {template_name}", key=f"template_{template_name}"):
                    st.session_state.template_data = template_data
                    st.rerun()
        
        # Display results
        if 'test_results' in st.session_state:
            self.display_test_results()
    
    def process_test_request(self, prompt: str, task_type: str, max_tokens: int,
                           temperature: float, system_message: str, context: str,
                           use_fallback: bool, specific_provider: str = None):
        """Process a test request"""
        try:
            # Create request
            request = LLMRequest(
                prompt=prompt,
                task_type=TaskType(task_type),
                max_tokens=max_tokens,
                temperature=temperature,
                system_message=system_message if system_message else None,
                context=context if context else None
            )
            
            system = st.session_state.llm_system
            
            with st.spinner("Generating response..."):
                # Run async function
                if use_fallback:
                    response = asyncio.run(system.generate(request))
                    st.session_state.test_results = {
                        'single': response,
                        'request': request
                    }
                else:
                    # Use specific provider
                    provider_enum = LLMProvider(specific_provider)
                    if provider_enum in system.providers:
                        provider = system.providers[provider_enum]
                        response = asyncio.run(provider.generate(request))
                        st.session_state.test_results = {
                            'single': response,
                            'request': request
                        }
                    else:
                        st.error(f"Provider {specific_provider} not available")
                        return
            
            st.success("✅ Response generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")
    
    def display_test_results(self):
        """Display test results"""
        st.subheader("📊 Test Results")
        
        results = st.session_state.test_results
        
        if 'single' in results:
            response = results['single']
            request = results['request']
            
            # Response details
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Provider", response.provider.value)
            
            with col2:
                st.metric("Tokens Used", response.tokens_used)
            
            with col3:
                st.metric("Cost", f"${response.cost:.4f}")
            
            with col4:
                st.metric("Latency", f"{response.latency:.2f}s")
            
            # Response content
            st.subheader("📝 Generated Response")
            st.text_area(
                "Response Content",
                value=response.content,
                height=200,
                disabled=True
            )
            
            # Metadata
            if response.metadata:
                st.subheader("🔍 Response Metadata")
                st.json(response.metadata)
        
        elif 'comparison' in results:
            self.display_comparison_results(results['comparison'])
    
    def render_configuration_interface(self):
        """Render provider configuration interface"""
        st.header("⚙️ Provider Configuration")
        
        system = st.session_state.llm_system
        
        # Provider configuration tabs
        provider_tabs = st.tabs([provider.value.title() for provider in LLMProvider])
        
        for i, provider in enumerate(LLMProvider):
            with provider_tabs[i]:
                self.render_provider_config(provider, system)
    
    def render_provider_config(self, provider: LLMProvider, system: MultiLLMProviderSystem):
        """Render configuration for a specific provider"""
        config = system.configs.get(provider)
        
        if not config:
            st.warning(f"No configuration found for {provider.value}")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Configuration")
            
            with st.form(f"config_{provider.value}"):
                enabled = st.checkbox("Enabled", value=config.enabled)
                
                api_key = st.text_input(
                    "API Key",
                    value=config.api_key,
                    type="password",
                    help="Leave empty for local models"
                )
                
                model = st.text_input("Model", value=config.model)
                
                priority = st.number_input(
                    "Priority",
                    min_value=1,
                    max_value=10,
                    value=config.priority,
                    help="Lower number = higher priority"
                )
                
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=50,
                    max_value=4000,
                    value=config.max_tokens
                )
                
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=config.temperature,
                    step=0.1
                )
                
                cost_per_token = st.number_input(
                    "Cost per Token",
                    min_value=0.0,
                    max_value=0.01,
                    value=config.cost_per_token,
                    step=0.0001,
                    format="%.4f"
                )
                
                rate_limit = st.number_input(
                    "Rate Limit (req/min)",
                    min_value=1,
                    max_value=1000,
                    value=config.rate_limit
                )
                
                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=5,
                    max_value=120,
                    value=config.timeout
                )
                
                if st.form_submit_button("💾 Save Configuration"):
                    # Update configuration
                    new_config = ProviderConfig(
                        provider=provider,
                        api_key=api_key,
                        model=model,
                        enabled=enabled,
                        priority=priority,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        cost_per_token=cost_per_token,
                        rate_limit=rate_limit,
                        timeout=timeout
                    )
                    
                    system.add_provider_config(new_config)
                    st.success(f"✅ Configuration saved for {provider.value}")
                    st.rerun()
        
        with col2:
            st.subheader("📊 Provider Statistics")
            
            if provider in system.providers:
                stats = system.providers[provider].stats
                
                # Metrics
                col_req, col_success = st.columns(2)
                
                with col_req:
                    st.metric("Total Requests", stats.total_requests)
                
                with col_success:
                    st.metric("Success Rate", f"{stats.success_rate:.1%}")
                
                col_tokens, col_cost = st.columns(2)
                
                with col_tokens:
                    st.metric("Total Tokens", stats.total_tokens)
                
                with col_cost:
                    st.metric("Total Cost", f"${stats.total_cost:.4f}")
                
                col_latency, col_last = st.columns(2)
                
                with col_latency:
                    st.metric("Avg Latency", f"{stats.average_latency:.2f}s")
                
                with col_last:
                    last_used = stats.last_used.strftime("%H:%M:%S") if stats.last_used else "Never"
                    st.metric("Last Used", last_used)
                
                # Latency history chart
                if stats.latency_history:
                    st.subheader("📈 Latency History")
                    
                    fig = px.line(
                        x=list(range(len(stats.latency_history))),
                        y=stats.latency_history,
                        title="Response Latency Over Time",
                        labels={"x": "Request Number", "y": "Latency (seconds)"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.info(f"{provider.value} provider not initialized")
    
    def render_analytics_interface(self):
        """Render analytics and monitoring interface"""
        st.header("📊 Analytics & Monitoring")
        
        system = st.session_state.llm_system
        stats = system.get_provider_stats()
        
        if not stats:
            st.info("No statistics available yet. Run some tests to see analytics.")
            return
        
        # Overview metrics
        st.subheader("📈 Overview")
        
        total_requests = sum(stat.total_requests for stat in stats.values())
        total_cost = sum(stat.total_cost for stat in stats.values())
        total_tokens = sum(stat.total_tokens for stat in stats.values())
        avg_success_rate = sum(stat.success_rate for stat in stats.values()) / len(stats) if stats else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", total_requests)
        
        with col2:
            st.metric("Total Cost", f"${total_cost:.4f}")
        
        with col3:
            st.metric("Total Tokens", total_tokens)
        
        with col4:
            st.metric("Avg Success Rate", f"{avg_success_rate:.1%}")
        
        # Provider comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Requests by provider
            provider_names = [provider.value for provider in stats.keys()]
            request_counts = [stat.total_requests for stat in stats.values()]
            
            fig = px.bar(
                x=provider_names,
                y=request_counts,
                title="Requests by Provider",
                labels={"x": "Provider", "y": "Total Requests"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Success rates
            success_rates = [stat.success_rate * 100 for stat in stats.values()]
            
            fig = px.bar(
                x=provider_names,
                y=success_rates,
                title="Success Rate by Provider",
                labels={"x": "Provider", "y": "Success Rate (%)"},
                color=success_rates,
                color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Cost and latency analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost by provider
            costs = [stat.total_cost for stat in stats.values()]
            
            fig = px.pie(
                values=costs,
                names=provider_names,
                title="Cost Distribution by Provider"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Average latency
            latencies = [stat.average_latency for stat in stats.values()]
            
            fig = px.bar(
                x=provider_names,
                y=latencies,
                title="Average Latency by Provider",
                labels={"x": "Provider", "y": "Latency (seconds)"},
                color=latencies,
                color_continuous_scale="RdYlBu_r"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed statistics table
        st.subheader("📋 Detailed Statistics")
        
        stats_data = []
        for provider, stat in stats.items():
            stats_data.append({
                "Provider": provider.value,
                "Total Requests": stat.total_requests,
                "Successful": stat.successful_requests,
                "Failed": stat.failed_requests,
                "Success Rate": f"{stat.success_rate:.1%}",
                "Total Tokens": stat.total_tokens,
                "Total Cost": f"${stat.total_cost:.4f}",
                "Avg Latency": f"{stat.average_latency:.2f}s",
                "Last Used": stat.last_used.strftime("%Y-%m-%d %H:%M:%S") if stat.last_used else "Never"
            })
        
        df = pd.DataFrame(stats_data)
        st.dataframe(df, use_container_width=True)
        
        # Export statistics
        if st.button("📥 Export Statistics"):
            export_data = system.export_stats()
            st.download_button(
                label="Download Statistics JSON",
                data=json.dumps(export_data, indent=2, default=str),
                file_name=f"llm_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def render_comparison_interface(self):
        """Render provider comparison interface"""
        st.header("🔄 Provider Comparison")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🧪 Comparison Test")
            
            with st.form("comparison_form"):
                prompt = st.text_area(
                    "Prompt for Comparison",
                    placeholder="Enter a prompt to test across multiple providers...",
                    height=100
                )
                
                col_task, col_tokens = st.columns(2)
                
                with col_task:
                    task_type = st.selectbox(
                        "Task Type",
                        options=[task.value for task in TaskType],
                        format_func=lambda x: x.replace('_', ' ').title(),
                        key="comparison_task"
                    )
                
                with col_tokens:
                    max_tokens = st.number_input(
                        "Max Tokens",
                        min_value=50,
                        max_value=1000,
                        value=200,
                        step=50,
                        key="comparison_tokens"
                    )
                
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.7,
                    step=0.1,
                    key="comparison_temp"
                )
                
                # Provider selection
                available_providers = list(st.session_state.llm_system.providers.keys())
                selected_providers = st.multiselect(
                    "Select Providers to Compare",
                    options=[p.value for p in available_providers],
                    default=[p.value for p in available_providers[:3]]  # Select first 3 by default
                )
                
                submitted = st.form_submit_button("🔄 Compare Providers", type="primary")
                
                if submitted and prompt and selected_providers:
                    self.process_comparison_request(
                        prompt, task_type, max_tokens, temperature, selected_providers
                    )
        
        with col2:
            st.subheader("📊 Comparison Metrics")
            
            if 'comparison_results' in st.session_state:
                results = st.session_state.comparison_results
                
                # Quick metrics
                providers = list(results.keys())
                
                if providers:
                    # Cost comparison
                    costs = [results[p].cost for p in providers]
                    cheapest = providers[costs.index(min(costs))]
                    st.metric("💰 Cheapest", cheapest.value)
                    
                    # Speed comparison
                    latencies = [results[p].latency for p in providers]
                    fastest = providers[latencies.index(min(latencies))]
                    st.metric("⚡ Fastest", fastest.value)
                    
                    # Token efficiency
                    tokens = [results[p].tokens_used for p in providers]
                    most_efficient = providers[tokens.index(min(tokens))]
                    st.metric("🎯 Most Efficient", most_efficient.value)
        
        # Display comparison results
        if 'comparison_results' in st.session_state:
            self.display_comparison_results()
    
    def process_comparison_request(self, prompt: str, task_type: str, max_tokens: int,
                                 temperature: float, selected_providers: List[str]):
        """Process a comparison request"""
        try:
            # Create request
            request = LLMRequest(
                prompt=prompt,
                task_type=TaskType(task_type),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Convert provider names to enums
            provider_enums = [LLMProvider(p) for p in selected_providers]
            
            system = st.session_state.llm_system
            
            with st.spinner("Generating responses from multiple providers..."):
                # Run comparison
                results = asyncio.run(
                    system.generate_with_comparison(request, provider_enums)
                )
                
                st.session_state.comparison_results = results
                st.session_state.comparison_request = request
            
            st.success(f"✅ Comparison completed with {len(results)} providers!")
            
        except Exception as e:
            st.error(f"❌ Error in comparison: {str(e)}")
    
    def display_comparison_results(self):
        """Display comparison results"""
        st.subheader("🔄 Comparison Results")
        
        results = st.session_state.comparison_results
        request = st.session_state.comparison_request
        
        # Summary table
        comparison_data = []
        for provider, response in results.items():
            comparison_data.append({
                "Provider": provider.value,
                "Model": response.model,
                "Tokens": response.tokens_used,
                "Cost": f"${response.cost:.4f}",
                "Latency": f"{response.latency:.2f}s",
                "Confidence": f"{response.confidence:.1%}",
                "Content Length": len(response.content)
            })
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Detailed responses
        st.subheader("📝 Detailed Responses")
        
        provider_tabs = st.tabs([provider.value for provider in results.keys()])
        
        for i, (provider, response) in enumerate(results.items()):
            with provider_tabs[i]:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text_area(
                        f"Response from {provider.value}",
                        value=response.content,
                        height=200,
                        disabled=True,
                        key=f"response_{provider.value}"
                    )
                
                with col2:
                    st.metric("Tokens", response.tokens_used)
                    st.metric("Cost", f"${response.cost:.4f}")
                    st.metric("Latency", f"{response.latency:.2f}s")
                    st.metric("Confidence", f"{response.confidence:.1%}")
        
        # Comparison charts
        st.subheader("📊 Comparison Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost comparison
            providers = [p.value for p in results.keys()]
            costs = [r.cost for r in results.values()]
            
            fig = px.bar(
                x=providers,
                y=costs,
                title="Cost Comparison",
                labels={"x": "Provider", "y": "Cost ($)"},
                color=costs,
                color_continuous_scale="RdYlGn_r"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Latency comparison
            latencies = [r.latency for r in results.values()]
            
            fig = px.bar(
                x=providers,
                y=latencies,
                title="Latency Comparison",
                labels={"x": "Provider", "y": "Latency (seconds)"},
                color=latencies,
                color_continuous_scale="RdYlBu_r"
            )
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main function to run the Streamlit app"""
    ui = MultiLLMProviderUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()