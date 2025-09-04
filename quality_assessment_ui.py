"""
Quality Assessment UI - Streamlit Implementation
Comprehensive quality analysis dashboard with full medical schema integration
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import asyncio
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event, get_params, update_params

# Import our quality assessment system
from quality_assessment_system import (
    QualityAssessmentEngine, 
    QualityAssessmentResult,
    QualityDimension,
    QualityLevel
)
from quality_metrics_engine import QualityMetricsEngine, QualityMetricsSummary

class QualityAssessmentDashboard:
    """Streamlit dashboard for comprehensive quality assessment visualization"""
    
    def __init__(self):
        self.quality_engine = QualityAssessmentEngine()
        self.metrics_engine = QualityMetricsEngine()
        
        # Configure page
        st.set_page_config(
            page_title="Quality Assessment Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        if 'quality_assessments' not in st.session_state:
            st.session_state.quality_assessments = []
        if 'quality_metrics' not in st.session_state:
            st.session_state.quality_metrics = None
        if 'medical_features_enabled' not in st.session_state:
            st.session_state.medical_features_enabled = False
        if 'selected_transcript' not in st.session_state:
            st.session_state.selected_transcript = None
    
    def render_dashboard(self):
        """Render the complete quality assessment dashboard"""
        
        # Header
        self._render_header()
        # Inline share input
        try:
            render_share_inline("Shareable view link")
        except Exception:
            pass
        
        # Sidebar configuration
        self._render_sidebar()
        
        # Main content based on selected view
        view = st.session_state.get('dashboard_view', 'overview')
        
        if view == 'overview':
            self._render_overview_tab()
        elif view == 'detailed_analysis':
            self._render_detailed_analysis_tab()
        elif view == 'medical_insights' and st.session_state.medical_features_enabled:
            self._render_medical_insights_tab()
        elif view == 'recommendations':
            self._render_recommendations_tab()
        elif view == 'trends':
            self._render_trends_analysis_tab()
        elif view == 'benchmarks':
            self._render_benchmarks_tab()
    
    def _render_header(self):
        """Render dashboard header with controls"""
        st.title("📊 Quality Assessment Dashboard")
        st.markdown("---")
        
        # Top-level metrics row
        if st.session_state.quality_assessments:
            latest_assessment = max(
                st.session_state.quality_assessments, 
                key=lambda x: x.assessment_timestamp
            )
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "Overall Quality Score",
                    f"{latest_assessment.overall_score:.1f}%",
                    delta=None,
                    help="Latest overall quality assessment score"
                )
            
            with col2:
                accuracy_score = latest_assessment.dimension_scores.get(
                    QualityDimension.ACCURACY, 
                    type('obj', (), {'score': 0})()
                ).score
                st.metric(
                    "Accuracy",
                    f"{accuracy_score:.1f}%",
                    help="Transcription accuracy score"
                )
            
            with col3:
                completeness_score = latest_assessment.dimension_scores.get(
                    QualityDimension.COMPLETENESS,
                    type('obj', (), {'score': 0})()
                ).score
                st.metric(
                    "Completeness",
                    f"{completeness_score:.1f}%",
                    help="Content completeness score"
                )
            
            with col4:
                if st.session_state.medical_features_enabled:
                    medical_accuracy = latest_assessment.dimension_scores.get(
                        QualityDimension.MEDICAL_ACCURACY,
                        type('obj', (), {'score': 0})()
                    ).score
                    st.metric(
                        "Medical Accuracy",
                        f"{medical_accuracy:.1f}%",
                        help="Medical terminology accuracy"
                    )
                else:
                    consistency_score = latest_assessment.dimension_scores.get(
                        QualityDimension.CONSISTENCY,
                        type('obj', (), {'score': 0})()
                    ).score
                    st.metric(
                        "Consistency",
                        f"{consistency_score:.1f}%",
                        help="Content consistency score"
                    )
            
            with col5:
                if st.session_state.medical_features_enabled:
                    hipaa_score = latest_assessment.dimension_scores.get(
                        QualityDimension.HIPAA_COMPLIANCE,
                        type('obj', (), {'score': 0})()
                    ).score
                    st.metric(
                        "HIPAA Compliance",
                        f"{hipaa_score:.1f}%",
                        help="HIPAA compliance score"
                    )
                else:
                    st.metric(
                        "Total Assessments",
                        len(st.session_state.quality_assessments),
                        help="Number of quality assessments performed"
                    )
        
        st.markdown("---")
    
    def _render_sidebar(self):
        """Render sidebar with configuration options"""
        with st.sidebar:
            st.header("⚙️ Dashboard Configuration")
            
            # Medical features toggle
            params = get_params()
            medical_enabled = st.checkbox(
                "Enable Medical Features",
                value=(params.get('qa_med', '1' if st.session_state.medical_features_enabled else '0') == '1'),
                help="Show medical-specific quality metrics and HIPAA compliance"
            )
            if medical_enabled != st.session_state.medical_features_enabled:
                st.session_state.medical_features_enabled = medical_enabled
                try:
                    update_params({'qa_med': '1' if medical_enabled else '0'})
                except Exception:
                    pass
                st.rerun()
            
            # Dashboard view selection
            view_options = [
                "overview",
                "detailed_analysis", 
                "recommendations",
                "trends",
                "benchmarks"
            ]
            
            if st.session_state.medical_features_enabled:
                view_options.insert(-2, "medical_insights")
            
            view_labels = {
                "overview": "📈 Overview",
                "detailed_analysis": "🔍 Detailed Analysis", 
                "medical_insights": "🏥 Medical Insights",
                "recommendations": "💡 Recommendations",
                "trends": "📊 Trends Analysis",
                "benchmarks": "🏆 Benchmarks"
            }
            
            qp_view = params.get('qa_view', st.session_state.get('dashboard_view', 'overview'))
            try:
                initial_index = view_options.index(qp_view) if qp_view in view_options else 0
            except Exception:
                initial_index = 0
            selected_view = st.selectbox(
                "Dashboard View",
                view_options,
                format_func=lambda x: view_labels.get(x, x),
                index=initial_index
            )
            st.session_state.dashboard_view = selected_view
            try:
                update_params({'qa_view': selected_view})
            except Exception:
                pass
            
            st.markdown("---")
            
            # Time range filter
            st.subheader("🕒 Time Range")
            qp_range = params.get('qa_range', st.session_state.get('time_range', 'Last 30 days'))
            time_range = st.selectbox(
                "Select time range",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                index=["Last 7 days", "Last 30 days", "Last 90 days", "All time"].index(qp_range) if qp_range in ["Last 7 days", "Last 30 days", "Last 90 days", "All time"] else 1
            )
            st.session_state.time_range = time_range
            try:
                update_params({'qa_range': time_range})
            except Exception:
                pass
            
            # Quality assessment controls
            st.markdown("---")
            st.subheader("🔧 Quality Assessment")
            
            # File upload for new assessment
            uploaded_file = st.file_uploader(
                "Upload transcript for assessment",
                type=['txt', 'json'],
                help="Upload a transcript file to perform quality assessment"
            )
            
            if uploaded_file is not None:
                if st.button("Run Quality Assessment", type="primary"):
                    self._process_uploaded_file(uploaded_file)
            
            # Sample data button
            if st.button("Load Sample Data"):
                self._load_sample_data()
            
            # Refresh data button
            if st.button("🔄 Refresh Data"):
                self._refresh_quality_data()
    
    def _render_overview_tab(self):
        """Render overview tab with key metrics and visualizations"""
        if not st.session_state.quality_assessments:
            st.warning("No quality assessments available. Upload a transcript or load sample data to begin.")
            return
        
        # Filter assessments by time range
        filtered_assessments = self._filter_assessments_by_time_range()
        
        if not filtered_assessments:
            st.warning("No assessments found in the selected time range.")
            return
        
        # Quality trends over time
        st.subheader("📈 Quality Trends Over Time")
        self._render_quality_trends_chart(filtered_assessments)
        
        # Current quality breakdown
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🎯 Current Quality Breakdown")
            self._render_quality_radar_chart(filtered_assessments[-1])
        
        with col2:
            st.subheader("📊 Quality Distribution")
            self._render_quality_distribution_chart(filtered_assessments)
        
        # Medical schema coverage (if medical features enabled)
        if st.session_state.medical_features_enabled:
            st.subheader("🏥 Medical Schema Coverage")
            self._render_medical_schema_coverage(filtered_assessments[-1])
        
        # Risk indicators
        if st.session_state.quality_metrics:
            st.subheader("⚠️ Risk Indicators")
            self._render_risk_indicators()
    
    def _render_detailed_analysis_tab(self):
        """Render detailed analysis with dimension breakdowns"""
        if not st.session_state.quality_assessments:
            st.warning("No quality assessments available.")
            return
        
        filtered_assessments = self._filter_assessments_by_time_range()
        latest_assessment = filtered_assessments[-1] if filtered_assessments else None
        
        if not latest_assessment:
            st.warning("No assessments in selected time range.")
            return
        
        st.subheader("🔍 Quality Dimension Analysis")
        
        # Dimension scores breakdown
        dimension_data = []
        for dimension, metric in latest_assessment.dimension_scores.items():
            dimension_data.append({
                'Dimension': dimension.value.replace('_', ' ').title(),
                'Score': metric.score,
                'Level': metric.level.value,
                'Confidence': metric.confidence,
                'Details': metric.details
            })
        
        df = pd.DataFrame(dimension_data)
        
        # Interactive dimension analysis
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Dimension scores bar chart
            fig = px.bar(
                df, 
                x='Dimension', 
                y='Score',
                color='Level',
                title="Quality Dimension Scores",
                color_discrete_map={
                    'EXCELLENT': '#4CAF50',
                    'VERY_GOOD': '#8BC34A', 
                    'GOOD': '#FFC107',
                    'FAIR': '#FF9800',
                    'POOR': '#F44336'
                }
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Confidence levels
            fig_confidence = px.bar(
                df,
                x='Dimension',
                y='Confidence',
                title="Assessment Confidence by Dimension",
                color='Confidence',
                color_continuous_scale='Viridis'
            )
            fig_confidence.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_confidence, use_container_width=True)
        
        # Detailed dimension information
        st.subheader("📋 Dimension Details")
        
        for _, row in df.iterrows():
            with st.expander(f"🔹 {row['Dimension']} - {row['Score']:.1f}% ({row['Level']})"):
                st.write(f"**Confidence:** {row['Confidence']:.1%}")
                st.write(f"**Details:** {row['Details']}")
                
                # Show suggestions if available
                dimension_obj = next(
                    (dim for dim in QualityDimension if dim.value.replace('_', ' ').title() == row['Dimension']),
                    None
                )
                if dimension_obj and dimension_obj in latest_assessment.dimension_scores:
                    suggestions = latest_assessment.dimension_scores[dimension_obj].suggestions
                    if suggestions:
                        st.write("**Improvement Suggestions:**")
                        for suggestion in suggestions:
                            st.write(f"• {suggestion}")
    
    def _render_medical_insights_tab(self):
        """Render medical-specific insights and analysis"""
        if not st.session_state.medical_features_enabled:
            st.warning("Medical features are not enabled.")
            return
        
        if not st.session_state.quality_assessments:
            st.warning("No quality assessments available.")
            return
        
        filtered_assessments = self._filter_assessments_by_time_range()
        latest_assessment = filtered_assessments[-1] if filtered_assessments else None
        
        if not latest_assessment:
            st.warning("No assessments in selected time range.")
            return
        
        st.subheader("🏥 Medical Quality Insights")
        
        # Medical accuracy analysis
        col1, col2 = st.columns(2)
        
        with col1:
            medical_accuracy = latest_assessment.dimension_scores.get(QualityDimension.MEDICAL_ACCURACY)
            if medical_accuracy:
                st.metric(
                    "Medical Accuracy Score",
                    f"{medical_accuracy.score:.1f}%",
                    help="Accuracy of medical terminology and concepts"
                )
                
                # Medical terminology analysis
                if hasattr(medical_accuracy, 'evidence') and 'medical_terms_identified' in medical_accuracy.evidence:
                    st.write("**Medical Terms Identified:**")
                    terms = medical_accuracy.evidence['medical_terms_identified']
                    if terms:
                        st.write(f"• {len(terms)} medical terms detected")
                        with st.expander("View identified terms"):
                            for term in terms[:20]:  # Show first 20 terms
                                st.write(f"• {term}")
                
                # Medication analysis
                if hasattr(medical_accuracy, 'evidence') and 'medications_identified' in medical_accuracy.evidence:
                    medications = medical_accuracy.evidence['medications_identified']
                    if medications:
                        st.write("**Medications Identified:**")
                        st.write(f"• {len(medications)} medications detected")
                        with st.expander("View identified medications"):
                            for med in medications:
                                st.write(f"• {med}")
        
        with col2:
            hipaa_compliance = latest_assessment.dimension_scores.get(QualityDimension.HIPAA_COMPLIANCE)
            if hipaa_compliance:
                st.metric(
                    "HIPAA Compliance Score", 
                    f"{hipaa_compliance.score:.1f}%",
                    help="HIPAA compliance assessment score"
                )
                
                # PHI detection analysis
                if hasattr(hipaa_compliance, 'evidence') and 'phi_violations' in hipaa_compliance.evidence:
                    violations = hipaa_compliance.evidence['phi_violations']
                    if violations:
                        st.error(f"⚠️ {len(violations)} potential PHI violations detected")
                        with st.expander("View PHI violations"):
                            for violation in violations:
                                st.write(f"• {violation}")
                    else:
                        st.success("✅ No PHI violations detected")
        
        # Medical schema coverage visualization
        if hasattr(latest_assessment, 'metadata') and 'medical_schema_coverage' in latest_assessment.metadata:
            st.subheader("📋 Medical Schema Coverage Analysis")
            coverage = latest_assessment.metadata['medical_schema_coverage']
            
            coverage_df = pd.DataFrame([
                {'Category': k.replace('_', ' ').title(), 'Covered': v}
                for k, v in coverage.items()
            ])
            
            fig = px.bar(
                coverage_df,
                x='Category',
                y='Covered',
                color='Covered',
                title="Medical Schema Coverage by Category",
                color_discrete_map={True: '#4CAF50', False: '#F44336'}
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Social determinants analysis
        if hasattr(latest_assessment, 'metadata') and 'social_determinants_analysis' in latest_assessment.metadata:
            st.subheader("🏛️ Social Determinants of Health Analysis")
            social_determinants = latest_assessment.metadata['social_determinants_analysis']
            
            if social_determinants.get('addressed_determinants'):
                addressed = social_determinants['addressed_determinants']
                st.write(f"**Addressed Social Determinants:** {len(addressed)}")
                
                col1, col2 = st.columns(2)
                with col1:
                    for determinant in addressed[:len(addressed)//2]:
                        st.write(f"✅ {determinant}")
                with col2:
                    for determinant in addressed[len(addressed)//2:]:
                        st.write(f"✅ {determinant}")
    
    def _render_recommendations_tab(self):
        """Render recommendations and improvement opportunities"""
        if not st.session_state.quality_assessments:
            st.warning("No quality assessments available.")
            return
        
        filtered_assessments = self._filter_assessments_by_time_range()
        latest_assessment = filtered_assessments[-1] if filtered_assessments else None
        
        if not latest_assessment:
            st.warning("No assessments in selected time range.")
            return
        
        st.subheader("💡 Quality Improvement Recommendations")
        
        # Current recommendations
        if latest_assessment.recommendations:
            st.write("**Current Recommendations:**")
            for i, rec in enumerate(latest_assessment.recommendations):
                st.info(f"**{i+1}.** {rec}")
        
        # Improvement opportunities from metrics engine
        if st.session_state.quality_metrics and st.session_state.quality_metrics.improvement_opportunities:
            st.subheader("🎯 Improvement Opportunities")
            for i, opportunity in enumerate(st.session_state.quality_metrics.improvement_opportunities):
                st.success(f"**{i+1}.** {opportunity}")
        
        # Strengths and weaknesses analysis
        col1, col2 = st.columns(2)
        
        with col1:
            if latest_assessment.strengths:
                st.subheader("✅ Strengths")
                for strength in latest_assessment.strengths:
                    st.write(f"• {strength}")
        
        with col2:
            if latest_assessment.weaknesses:
                st.subheader("⚠️ Areas for Improvement")
                for weakness in latest_assessment.weaknesses:
                    st.write(f"• {weakness}")
        
        # Action plan generator
        st.subheader("📋 Generated Action Plan")
        if st.button("Generate Action Plan"):
            action_plan = self._generate_action_plan(latest_assessment)
            st.markdown(action_plan)
    
    def _render_trends_analysis_tab(self):
        """Render trend analysis and projections"""
        if not st.session_state.quality_metrics or not st.session_state.quality_metrics.trend_analysis:
            st.warning("No trend analysis data available.")
            return
        
        st.subheader("📊 Quality Trends Analysis")
        
        trend_data = []
        for trend in st.session_state.quality_metrics.trend_analysis:
            trend_data.append({
                'Dimension': trend.dimension.value.replace('_', ' ').title(),
                'Trend': trend.trend_direction.value.title(),
                'Strength': trend.trend_strength,
                'Slope': trend.slope,
                'Projected 30-day': trend.projected_score_30_days,
                'Confidence': trend.prediction_confidence,
                'Data Points': trend.data_points
            })
        
        df = pd.DataFrame(trend_data)
        
        # Trend direction visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Trend Directions', 'Trend Strength', 'Future Projections', 'Prediction Confidence'],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Trend directions
        trend_colors = {'Improving': '#4CAF50', 'Stable': '#2196F3', 'Declining': '#F44336', 'Volatile': '#FF9800'}
        fig.add_trace(
            go.Bar(x=df['Dimension'], y=df['Strength'], 
                   marker_color=[trend_colors.get(trend, '#666666') for trend in df['Trend']], 
                   name='Trend Strength'),
            row=1, col=1
        )
        
        # Future projections
        fig.add_trace(
            go.Bar(x=df['Dimension'], y=df['Projected 30-day'], name='30-day Projection'),
            row=2, col=1
        )
        
        # Prediction confidence
        fig.add_trace(
            go.Bar(x=df['Dimension'], y=df['Confidence'], name='Confidence'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed trend information
        st.subheader("📈 Detailed Trend Analysis")
        for _, row in df.iterrows():
            with st.expander(f"📊 {row['Dimension']} - {row['Trend']} Trend"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Trend Strength", f"{row['Strength']:.1%}")
                with col2:
                    st.metric("30-day Projection", f"{row['Projected 30-day']:.1f}%")
                with col3:
                    st.metric("Confidence", f"{row['Confidence']:.1%}")
                
                st.write(f"**Slope:** {row['Slope']:.3f} points per day")
                st.write(f"**Data Points:** {row['Data Points']}")
    
    def _render_benchmarks_tab(self):
        """Render benchmark comparisons"""
        if not st.session_state.quality_metrics or not st.session_state.quality_metrics.benchmark_comparisons:
            st.warning("No benchmark comparison data available.")
            return
        
        st.subheader("🏆 Industry Benchmark Comparisons")
        
        benchmark_data = []
        for comparison in st.session_state.quality_metrics.benchmark_comparisons:
            benchmark_data.append({
                'Dimension': comparison.dimension.value.replace('_', ' ').title(),
                'Current Score': comparison.current_score,
                'Industry Benchmark': comparison.industry_benchmark,
                'Gap': comparison.current_score - comparison.industry_benchmark,
                'Percentile Rank': comparison.percentile_rank,
                'Position': comparison.competitive_position.title(),
                'Improvement Potential': comparison.improvement_potential
            })
        
        df = pd.DataFrame(benchmark_data)
        
        # Benchmark comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Current Score',
            x=df['Dimension'],
            y=df['Current Score'],
            marker_color='#2196F3'
        ))
        
        fig.add_trace(go.Bar(
            name='Industry Benchmark', 
            x=df['Dimension'],
            y=df['Industry Benchmark'],
            marker_color='#FF9800'
        ))
        
        fig.update_layout(
            title="Current Performance vs Industry Benchmarks",
            xaxis_title="Quality Dimensions",
            yaxis_title="Score (%)",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gap analysis
        st.subheader("📊 Gap Analysis")
        
        # Create gap visualization
        fig_gap = px.bar(
            df,
            x='Dimension',
            y='Gap',
            color='Gap',
            color_continuous_scale=['red', 'yellow', 'green'],
            title="Performance Gap vs Industry Benchmark",
            color_continuous_midpoint=0
        )
        fig_gap.update_layout(height=400)
        st.plotly_chart(fig_gap, use_container_width=True)
        
        # Detailed benchmark information
        st.subheader("📋 Detailed Benchmark Analysis")
        for _, row in df.iterrows():
            with st.expander(f"🎯 {row['Dimension']} - {row['Position']} Position"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Score", f"{row['Current Score']:.1f}%")
                with col2:
                    st.metric("Industry Benchmark", f"{row['Industry Benchmark']:.1f}%")
                with col3:
                    gap_delta = f"{row['Gap']:+.1f}%" if row['Gap'] != 0 else "0%"
                    st.metric("Gap", gap_delta)
                with col4:
                    st.metric("Percentile Rank", f"{row['Percentile Rank']:.0f}%")
                
                st.write(f"**Competitive Position:** {row['Position']}")
                st.write(f"**Improvement Potential:** {row['Improvement Potential']:.1f} points")
    
    def _render_quality_trends_chart(self, assessments: List[QualityAssessmentResult]):
        """Render quality trends over time chart"""
        if len(assessments) < 2:
            st.info("Need at least 2 assessments to show trends.")
            return
        
        # Prepare data for plotting
        dates = [assessment.assessment_timestamp for assessment in assessments]
        overall_scores = [assessment.overall_score for assessment in assessments]
        
        # Create traces for each dimension
        dimension_data = {}
        for assessment in assessments:
            for dimension, metric in assessment.dimension_scores.items():
                if dimension not in dimension_data:
                    dimension_data[dimension] = []
                dimension_data[dimension].append(metric.score)
        
        # Create the plot
        fig = go.Figure()
        
        # Add overall score line
        fig.add_trace(go.Scatter(
            x=dates,
            y=overall_scores,
            mode='lines+markers',
            name='Overall Score',
            line=dict(color='#2196F3', width=3),
            marker=dict(size=8)
        ))
        
        # Add dimension lines (show top 3 most important)
        colors = ['#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#00BCD4']
        for i, (dimension, scores) in enumerate(list(dimension_data.items())[:5]):
            if len(scores) == len(dates):
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=scores,
                    mode='lines+markers',
                    name=dimension.value.replace('_', ' ').title(),
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6),
                    opacity=0.7
                ))
        
        fig.update_layout(
            title="Quality Scores Over Time",
            xaxis_title="Date",
            yaxis_title="Quality Score (%)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_quality_radar_chart(self, assessment: QualityAssessmentResult):
        """Render radar chart for quality dimensions"""
        dimensions = []
        scores = []
        
        for dimension, metric in assessment.dimension_scores.items():
            dimensions.append(dimension.value.replace('_', ' ').title())
            scores.append(metric.score)
        
        # Add the first dimension at the end to close the radar chart
        dimensions.append(dimensions[0])
        scores.append(scores[0])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=dimensions,
            fill='toself',
            name='Current Assessment',
            line_color='#2196F3'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            height=400,
            title="Quality Dimension Breakdown"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_quality_distribution_chart(self, assessments: List[QualityAssessmentResult]):
        """Render quality score distribution"""
        scores = [assessment.overall_score for assessment in assessments]
        
        fig = px.histogram(
            x=scores,
            nbins=10,
            title="Quality Score Distribution",
            labels={'x': 'Quality Score (%)', 'y': 'Frequency'},
            color_discrete_sequence=['#2196F3']
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_medical_schema_coverage(self, assessment: QualityAssessmentResult):
        """Render medical schema coverage visualization"""
        if not hasattr(assessment, 'metadata') or 'medical_schema_coverage' not in assessment.metadata:
            st.info("Medical schema coverage data not available.")
            return
        
        coverage = assessment.metadata['medical_schema_coverage']
        categories = list(coverage.keys())
        covered = list(coverage.values())
        
        fig = px.bar(
            x=[cat.replace('_', ' ').title() for cat in categories],
            y=[1 if cov else 0 for cov in covered],
            color=covered,
            title="Medical Schema Coverage by Category",
            color_discrete_map={True: '#4CAF50', False: '#F44336'},
            labels={'x': 'Schema Categories', 'y': 'Coverage Status'}
        )
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Coverage summary
        covered_count = sum(covered)
        total_count = len(covered)
        coverage_percentage = (covered_count / total_count) * 100 if total_count > 0 else 0
        
        st.metric(
            "Overall Schema Coverage",
            f"{coverage_percentage:.1f}%",
            f"{covered_count}/{total_count} categories covered"
        )
    
    def _render_risk_indicators(self):
        """Render risk indicators visualization"""
        if not st.session_state.quality_metrics or not st.session_state.quality_metrics.risk_indicators:
            return
        
        risk_data = st.session_state.quality_metrics.risk_indicators
        
        col1, col2 = st.columns(2)
        
        for i, (risk_type, risk_value) in enumerate(risk_data.items()):
            col = col1 if i % 2 == 0 else col2
            
            # Determine risk level and color
            if risk_value < 0.3:
                risk_level = "Low"
                color = "#4CAF50"
            elif risk_value < 0.7:
                risk_level = "Medium" 
                color = "#FF9800"
            else:
                risk_level = "High"
                color = "#F44336"
            
            with col:
                st.metric(
                    risk_type.replace('_', ' ').title(),
                    f"{risk_level}",
                    f"{risk_value:.1%} risk score",
                    help=f"Risk indicator for {risk_type.replace('_', ' ')}"
                )
    
    def _filter_assessments_by_time_range(self) -> List[QualityAssessmentResult]:
        """Filter assessments based on selected time range"""
        if not st.session_state.quality_assessments:
            return []
        
        time_range = st.session_state.get('time_range', 'All time')
        
        if time_range == 'All time':
            return st.session_state.quality_assessments
        
        # Extract number of days
        days_map = {
            'Last 7 days': 7,
            'Last 30 days': 30,
            'Last 90 days': 90
        }
        
        days = days_map.get(time_range, 30)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return [
            assessment for assessment in st.session_state.quality_assessments
            if assessment.assessment_timestamp >= cutoff_date
        ]
    
    def _process_uploaded_file(self, uploaded_file):
        """Process uploaded file for quality assessment"""
        try:
            # Read file content
            if uploaded_file.type == "text/plain":
                content = str(uploaded_file.read(), "utf-8")
            else:
                content = uploaded_file.getvalue().decode("utf-8")
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Running quality assessment...")
            progress_bar.progress(30)
            
            # Run quality assessment
            assessment_result = self.quality_engine.assess_transcript_quality(
                transcript=content,
                transcript_id=f"upload_{datetime.utcnow().isoformat()}",
                metadata={
                    'source': 'upload',
                    'filename': uploaded_file.name,
                    'medical_features_enabled': st.session_state.medical_features_enabled
                }
            )
            
            progress_bar.progress(70)
            status_text.text("Calculating quality metrics...")
            
            # Add to session state
            st.session_state.quality_assessments.append(assessment_result)
            
            # Update metrics
            if len(st.session_state.quality_assessments) > 1:
                metrics = self.metrics_engine.calculate_comprehensive_metrics(
                    st.session_state.quality_assessments
                )
                st.session_state.quality_metrics = metrics
            
            progress_bar.progress(100)
            status_text.text("Quality assessment completed!")
            
            st.success(f"Quality assessment completed! Overall score: {assessment_result.overall_score:.1f}%")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    def _load_sample_data(self):
        """Load sample quality assessment data"""
        sample_assessments = self._generate_sample_assessments()
        st.session_state.quality_assessments = sample_assessments
        
        # Calculate sample metrics
        metrics = self.metrics_engine.calculate_comprehensive_metrics(sample_assessments)
        st.session_state.quality_metrics = metrics
        
        st.success(f"Loaded {len(sample_assessments)} sample quality assessments!")
        st.rerun()
    
    def _generate_sample_assessments(self) -> List[QualityAssessmentResult]:
        """Generate sample quality assessment data for demonstration"""
        # This would normally come from your database
        # For demo purposes, we'll create some sample data
        sample_data = []
        
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(10):
            assessment_date = base_date + timedelta(days=i*3)
            
            # Simulate varying quality scores
            base_score = 75 + (i * 2) + np.random.normal(0, 5)
            base_score = max(50, min(95, base_score))  # Clamp between 50-95
            
            # Create dimension scores
            dimension_scores = {}
            for dimension in QualityDimension:
                score = base_score + np.random.normal(0, 8)
                score = max(40, min(100, score))
                
                level = QualityLevel.POOR
                if score >= 90:
                    level = QualityLevel.EXCELLENT
                elif score >= 80:
                    level = QualityLevel.VERY_GOOD
                elif score >= 70:
                    level = QualityLevel.GOOD
                elif score >= 60:
                    level = QualityLevel.FAIR
                
                dimension_scores[dimension] = type('DimensionMetric', (), {
                    'score': score,
                    'level': level,
                    'details': f"Sample details for {dimension.value}",
                    'suggestions': [f"Improve {dimension.value.replace('_', ' ')}"],
                    'evidence': {'sample': True},
                    'confidence': np.random.uniform(0.7, 0.95)
                })()
            
            # Create assessment result
            assessment = QualityAssessmentResult(
                id=f"sample_{i}",
                transcript_id=f"transcript_{i}",
                overall_score=base_score,
                overall_level=QualityLevel.GOOD,
                dimension_scores=dimension_scores,
                summary=f"Sample assessment {i+1} with overall score of {base_score:.1f}%",
                recommendations=[f"Sample recommendation {i+1}"],
                strengths=[f"Sample strength {i+1}"],
                weaknesses=[f"Sample weakness {i+1}"],
                metadata={
                    'medical_schema_coverage': {
                        'patient_information': True,
                        'clinical_data': True,
                        'social_determinants': i % 2 == 0,
                        'preventive_care': i % 3 == 0,
                        'medication_management': True,
                        'care_quality_assessment': i % 2 == 1
                    }
                },
                assessment_timestamp=assessment_date,
                processing_time=np.random.uniform(1000, 5000)
            )
            
            sample_data.append(assessment)
        
        return sample_data
    
    def _refresh_quality_data(self):
        """Refresh quality assessment data"""
        # In a real application, this would fetch fresh data from the database
        if st.session_state.quality_assessments:
            # Recalculate metrics
            metrics = self.metrics_engine.calculate_comprehensive_metrics(
                st.session_state.quality_assessments
            )
            st.session_state.quality_metrics = metrics
            st.success("Quality data refreshed!")
        else:
            st.info("No data to refresh. Load sample data or upload a transcript first.")
        
        st.rerun()
    
    def _generate_action_plan(self, assessment: QualityAssessmentResult) -> str:
        """Generate an action plan based on assessment results"""
        action_plan = f"""
## 📋 Quality Improvement Action Plan

**Assessment Date:** {assessment.assessment_timestamp.strftime('%Y-%m-%d %H:%M')}
**Overall Score:** {assessment.overall_score:.1f}%

### 🎯 Priority Actions

"""
        
        # Add priority actions based on lowest scoring dimensions
        sorted_dimensions = sorted(
            assessment.dimension_scores.items(),
            key=lambda x: x[1].score
        )
        
        for i, (dimension, metric) in enumerate(sorted_dimensions[:3]):
            action_plan += f"""
**{i+1}. Improve {dimension.value.replace('_', ' ').title()}** (Current: {metric.score:.1f}%)
- Focus Area: {metric.details}
- Suggested Actions:
"""
            for suggestion in metric.suggestions:
                action_plan += f"  - {suggestion}\n"
        
        # Add general recommendations
        action_plan += f"""
### 💡 General Recommendations

"""
        for rec in assessment.recommendations:
            action_plan += f"- {rec}\n"
        
        # Add timeline
        action_plan += f"""
### ⏱️ Implementation Timeline

- **Week 1-2:** Focus on highest priority dimension improvements
- **Week 3-4:** Implement systematic changes
- **Week 5-6:** Monitor and measure improvements
- **Week 7-8:** Fine-tune and optimize

### 📈 Success Metrics

- Target overall score improvement: {min(95, assessment.overall_score + 10):.1f}%
- Focus on consistency across all dimensions
- Maintain strengths while addressing weaknesses
"""
        
        return action_plan


# Streamlit app entry point
def main():
    dashboard = QualityAssessmentDashboard()
    dashboard.render_dashboard()


if __name__ == "__main__":
    main()
