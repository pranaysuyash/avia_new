#!/usr/bin/env python3
"""
Quality Optimization Engine UI - Intent-First Interface
Streamlit interface for quality-focused LLM provider selection
"""

import streamlit as st
import asyncio
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from quality_optimization_engine import (
    QualityOptimizationEngine, QualityTier, TaskComplexity, UserFeedback
)
from multi_llm_provider_system import LLMRequest, TaskType, LLMProvider

class QualityOptimizationUI:
    """Streamlit UI for Quality Optimization Engine"""
    
    def __init__(self):
        self.engine = QualityOptimizationEngine()
        
        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = "demo_user"
        if 'recommendation_history' not in st.session_state:
            st.session_state.recommendation_history = []
    
    def render_main_interface(self):
        """Render the main quality optimization interface"""
        
        st.title("🎯 AI Quality Optimization")
        st.markdown("Get the best AI provider for your specific needs with transparent quality insights")
        
        # User identification
        col1, col2 = st.columns([3, 1])
        with col1:
            st.session_state.user_id = st.text_input(
                "User ID", 
                value=st.session_state.user_id,
                help="Your user ID for personalized recommendations"
            )
        
        with col2:
            cost_preference = st.selectbox(
                "Cost Preference",
                ["balanced", "premium", "economy"],
                help="Your cost vs quality preference"
            )
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Get Recommendation", 
            "📊 Compare Providers", 
            "💬 Provide Feedback",
            "📈 Your Insights"
        ])
        
        with tab1:
            self._render_recommendation_tab(cost_preference)
        
        with tab2:
            self._render_comparison_tab()
        
        with tab3:
            self._render_feedback_tab()
        
        with tab4:
            self._render_insights_tab()
    
    def _render_recommendation_tab(self, cost_preference: str):
        """Render the recommendation tab"""
        
        st.header("🎯 Get AI Provider Recommendation")
        
        # Input form
        with st.form("recommendation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                task_type = st.selectbox(
                    "Task Type",
                    options=[task.value for task in TaskType],
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="What type of task do you need help with?"
                )
                
                max_tokens = st.slider(
                    "Response Length",
                    min_value=100,
                    max_value=2000,
                    value=500,
                    help="Maximum length of the AI response"
                )
            
            with col2:
                temperature = st.slider(
                    "Creativity Level",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    help="Higher values = more creative, lower = more focused"
                )
            
            prompt = st.text_area(
                "Your Request",
                placeholder="Enter your request or question here...",
                height=150,
                help="Describe what you need the AI to help you with"
            )
            
            system_message = st.text_input(
                "System Instructions (Optional)",
                placeholder="You are a helpful assistant...",
                help="Optional instructions to guide the AI's behavior"
            )
            
            context = st.text_area(
                "Additional Context (Optional)",
                placeholder="Any additional context or background information...",
                help="Provide context that might help the AI understand your request better"
            )
            
            submitted = st.form_submit_button("🎯 Get Recommendation", type="primary")
        
        if submitted and prompt:
            self._process_recommendation_request(
                prompt, task_type, max_tokens, temperature, 
                system_message, context, cost_preference
            )
        elif submitted:
            st.error("Please enter your request in the text area above.")
    
    def _process_recommendation_request(
        self, prompt, task_type, max_tokens, temperature, 
        system_message, context, cost_preference
    ):
        """Process recommendation request"""
        
        with st.spinner("Analyzing your request and finding the best AI provider..."):
            try:
                # Create LLM request
                request = LLMRequest(
                    prompt=prompt,
                    task_type=TaskType(task_type),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_message=system_message if system_message else None,
                    context=context if context else None
                )
                
                # Get recommendation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                recommendation = loop.run_until_complete(
                    self.engine.get_optimal_provider_recommendation(
                        request, st.session_state.user_id, cost_preference
                    )
                )
                loop.close()
                
                # Display recommendation
                self._display_recommendation(recommendation, request)
                
                # Store in history
                st.session_state.recommendation_history.append({
                    'timestamp': datetime.now(),
                    'recommendation': recommendation,
                    'request': request
                })
                
            except Exception as e:
                st.error(f"Error getting recommendation: {e}")
    
    def _display_recommendation(self, recommendation, request):
        """Display the provider recommendation"""
        
        st.success("✅ Recommendation Ready!")
        
        # Main recommendation card
        provider_name = recommendation.recommended_provider.value.title()
        quality_color = self._get_quality_color(recommendation.quality_tier)
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {quality_color}20, {quality_color}10);
            border-left: 5px solid {quality_color};
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        ">
            <h2 style="color: {quality_color}; margin: 0;">
                🎯 Recommended: {provider_name}
            </h2>
            <p style="font-size: 18px; margin: 10px 0;">
                <strong>Quality Tier:</strong> {recommendation.quality_tier.value.title()} 
                ({recommendation.quality_score:.1%} quality score)
            </p>
            <p style="font-size: 16px; margin: 5px 0;">
                <strong>Estimated Cost:</strong> ${recommendation.cost_estimate:.3f}
            </p>
            <p style="font-size: 16px; margin: 5px 0;">
                <strong>Confidence:</strong> {recommendation.confidence:.1%}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Reasoning
        st.markdown("### 🤔 Why This Recommendation?")
        st.info(recommendation.reasoning)
        
        # Alternative options
        if recommendation.alternatives:
            st.markdown("### 🔄 Alternative Options")
            
            for i, alt in enumerate(recommendation.alternatives[:3]):
                with st.expander(f"{alt.provider.value.title()} - {alt.quality_score:.1%} quality, ${alt.cost_estimate:.3f}"):
                    st.write(f"**Description:** {alt.description}")
                    st.write(f"**Speed:** {alt.speed_estimate}")
                    
                    if alt.pros:
                        st.write("**Pros:**")
                        for pro in alt.pros:
                            st.write(f"  ✅ {pro}")
                    
                    if alt.cons:
                        st.write("**Cons:**")
                        for con in alt.cons:
                            st.write(f"  ❌ {con}")
    
    def _render_comparison_tab(self):
        """Render the provider comparison tab"""
        
        st.header("📊 Provider Quality Comparison")
        
        # Input for comparison
        col1, col2 = st.columns(2)
        
        with col1:
            task_type = st.selectbox(
                "Task Type for Comparison",
                options=[task.value for task in TaskType],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="comparison_task_type"
            )
        
        with col2:
            sample_prompt = st.text_input(
                "Sample Prompt (Optional)",
                placeholder="Enter a sample prompt to get more accurate comparison...",
                key="comparison_prompt"
            )
        
        if st.button("📊 Compare Providers"):
            self._show_provider_comparison(task_type, sample_prompt)
    
    def _show_provider_comparison(self, task_type, sample_prompt):
        """Show detailed provider comparison"""
        
        with st.spinner("Comparing AI providers..."):
            try:
                # Create sample request
                request = LLMRequest(
                    prompt=sample_prompt or "Sample task for comparison",
                    task_type=TaskType(task_type),
                    max_tokens=500
                )
                
                # Get comparison
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                comparison = loop.run_until_complete(
                    self.engine.get_quality_comparison(request)
                )
                loop.close()
                
                if comparison:
                    # Create comparison table
                    comparison_data = []
                    for provider, metrics in comparison.items():
                        comparison_data.append({
                            'Provider': provider.value.title(),
                            'Quality Score': f"{metrics['quality_score']:.1%}",
                            'Accuracy': f"{metrics['accuracy']:.1%}",
                            'Speed Score': f"{metrics['speed_score']:.1%}",
                            'Cost Efficiency': f"{metrics['cost_efficiency']:.1%}",
                            'Est. Cost': f"${metrics['cost_estimate']:.3f}",
                            'Speed': metrics['speed_estimate'],
                            'Recommendation': metrics['recommendation']
                        })
                    
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, hide_index=True, use_container_width=True)
                    
                    # Quality radar chart
                    self._create_quality_radar_chart(comparison)
                    
                    # Cost vs Quality scatter plot
                    self._create_cost_quality_scatter(comparison)
                
            except Exception as e:
                st.error(f"Error comparing providers: {e}")
    
    def _create_quality_radar_chart(self, comparison):
        """Create radar chart for quality metrics"""
        
        st.markdown("### 🎯 Quality Metrics Radar Chart")
        
        fig = go.Figure()
        
        metrics = ['accuracy', 'speed_score', 'cost_efficiency', 'quality_score']
        metric_labels = ['Accuracy', 'Speed', 'Cost Efficiency', 'Overall Quality']
        
        for provider, data in comparison.items():
            values = [data[metric] for metric in metrics]
            values.append(values[0])  # Close the radar chart
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metric_labels + [metric_labels[0]],
                fill='toself',
                name=provider.value.title()
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_cost_quality_scatter(self, comparison):
        """Create cost vs quality scatter plot"""
        
        st.markdown("### 💰 Cost vs Quality Analysis")
        
        providers = []
        quality_scores = []
        cost_estimates = []
        
        for provider, data in comparison.items():
            providers.append(provider.value.title())
            quality_scores.append(data['quality_score'])
            cost_estimates.append(data['cost_estimate'])
        
        fig = px.scatter(
            x=cost_estimates,
            y=quality_scores,
            text=providers,
            title="Cost vs Quality Trade-off",
            labels={'x': 'Estimated Cost ($)', 'y': 'Quality Score'},
            size=[0.1] * len(providers),  # Same size for all points
            color=quality_scores,
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_traces(textposition="top center")
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_feedback_tab(self):
        """Render the feedback tab"""
        
        st.header("💬 Provide Feedback")
        st.markdown("Help us improve recommendations by sharing your experience")
        
        # Feedback form
        with st.form("feedback_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                provider = st.selectbox(
                    "AI Provider Used",
                    options=[provider.value for provider in LLMProvider],
                    format_func=lambda x: x.title()
                )
                
                task_type = st.selectbox(
                    "Task Type",
                    options=[task.value for task in TaskType],
                    format_func=lambda x: x.replace('_', ' ').title(),
                    key="feedback_task_type"
                )
            
            with col2:
                quality_rating = st.slider(
                    "Quality Rating",
                    min_value=1.0,
                    max_value=5.0,
                    value=3.0,
                    step=0.5,
                    help="How would you rate the quality of the AI response?"
                )
                
                speed_rating = st.slider(
                    "Speed Rating", 
                    min_value=1.0,
                    max_value=5.0,
                    value=3.0,
                    step=0.5,
                    help="How would you rate the response speed?"
                )
            
            satisfaction_rating = st.slider(
                "Overall Satisfaction",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5,
                help="How satisfied are you with the overall experience?"
            )
            
            text_feedback = st.text_area(
                "Additional Comments (Optional)",
                placeholder="Share any specific feedback about your experience...",
                help="Your comments help us improve our recommendations"
            )
            
            submitted = st.form_submit_button("📝 Submit Feedback", type="primary")
        
        if submitted:
            self._process_feedback(
                provider, task_type, quality_rating, speed_rating, 
                satisfaction_rating, text_feedback
            )
    
    def _process_feedback(
        self, provider, task_type, quality_rating, speed_rating, 
        satisfaction_rating, text_feedback
    ):
        """Process user feedback"""
        
        try:
            feedback = UserFeedback(
                user_id=st.session_state.user_id,
                provider=LLMProvider(provider),
                task_type=TaskType(task_type),
                quality_rating=quality_rating,
                speed_rating=speed_rating,
                satisfaction_rating=satisfaction_rating,
                text_feedback=text_feedback if text_feedback else None
            )
            
            # Record feedback
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.engine.record_user_feedback(feedback))
            loop.close()
            
            st.success("✅ Thank you for your feedback! This helps us improve our recommendations.")
            
        except Exception as e:
            st.error(f"Error submitting feedback: {e}")
    
    def _render_insights_tab(self):
        """Render the user insights tab"""
        
        st.header("📈 Your Quality Insights")
        
        try:
            # Get user insights
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            insights = loop.run_until_complete(
                self.engine.get_user_quality_insights(st.session_state.user_id)
            )
            loop.close()
            
            if insights['total_interactions'] == 0:
                st.info("No interaction history yet. Use the recommendation feature and provide feedback to see personalized insights!")
                return
            
            # Display insights
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Interactions",
                    insights['total_interactions']
                )
            
            with col2:
                st.metric(
                    "Average Satisfaction",
                    f"{insights['average_satisfaction']:.1f}/5.0"
                )
            
            with col3:
                st.metric(
                    "Average Quality Rating",
                    f"{insights['average_quality_rating']:.1f}/5.0"
                )
            
            # Preferred providers
            if insights['preferred_providers']:
                st.markdown("### 🏆 Your Preferred Providers")
                
                for provider_info in insights['preferred_providers']:
                    st.write(f"**{provider_info['provider'].title()}**: "
                           f"{provider_info['satisfaction']:.1f}/5.0 satisfaction "
                           f"({provider_info['usage_count']} uses)")
            
            # Quality trends
            if insights['quality_trends']:
                st.markdown("### 📈 Quality Trends")
                trends = insights['quality_trends']
                
                trend_emoji = {
                    'improving': '📈',
                    'stable': '➡️',
                    'declining': '📉'
                }.get(trends.get('quality_trend', 'stable'), '➡️')
                
                st.write(f"{trend_emoji} **Quality Trend**: {trends.get('quality_trend', 'stable').title()}")
                st.write(f"**Recent Average Quality**: {trends.get('recent_average_quality', 0):.1f}/5.0")
                st.write(f"**Recent Average Satisfaction**: {trends.get('recent_average_satisfaction', 0):.1f}/5.0")
            
            # Personalized recommendations
            if insights['recommendations']:
                st.markdown("### 💡 Personalized Recommendations")
                for rec in insights['recommendations']:
                    st.info(rec)
            
        except Exception as e:
            st.error(f"Error loading insights: {e}")
    
    def _get_quality_color(self, tier: QualityTier) -> str:
        """Get color for quality tier"""
        colors = {
            QualityTier.PREMIUM: "#00C851",
            QualityTier.STANDARD: "#39C0ED",
            QualityTier.ECONOMY: "#ffbb33"
        }
        return colors.get(tier, "#6c757d")

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="AI Quality Optimization",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    </style>
    """, unsafe_allow_html=True)
    
    ui = QualityOptimizationUI()
    ui.render_main_interface()
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("### 🎯 About Quality Optimization")
        st.markdown("""
        This system helps you choose the best AI provider for your specific needs by:
        
        - **Quality Analysis**: Comparing accuracy, speed, and reliability
        - **Cost Transparency**: Clear cost estimates for each option
        - **Personalized Recommendations**: Learning from your feedback
        - **Task Optimization**: Matching providers to task requirements
        """)
        
        st.markdown("### 🔄 How It Works")
        st.markdown("""
        1. **Describe your task** - Tell us what you need
        2. **Get recommendations** - See the best provider for your needs
        3. **Compare options** - Understand the trade-offs
        4. **Provide feedback** - Help us improve future recommendations
        """)
        
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Be specific about your task for better recommendations
        - Consider the cost vs quality trade-offs
        - Provide feedback to get more personalized suggestions
        - Check the comparison tab to understand provider strengths
        """)

if __name__ == "__main__":
    main()