"""
Medical Transcription Streamlit UI - Task 129
HIPAA-compliant medical transcription interface with specialized medical features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import uuid

try:
    from medical_transcription_system import (
        MedicalTranscriptionSystem, HIPAACompliance, MedicalEntityType
    )
    from comprehensive_medical_schema import ComprehensiveSchemaProcessor
    COMPREHENSIVE_SCHEMA_AVAILABLE = True
except ImportError as e:
    st.error("Medical transcription system not found. Please ensure medical_transcription_system.py is available.")
    COMPREHENSIVE_SCHEMA_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Medical Transcription System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for medical theme
st.markdown("""
<style>
    .medical-header {
        background: linear-gradient(90deg, #2E8B57 0%, #228B22 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .phi-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .compliance-good {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
    }
    
    .compliance-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
    }
    
    .compliance-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
    }
    
    .entity-chip {
        display: inline-block;
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 15px;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        font-size: 0.8rem;
        color: #1976d2;
    }
    
    .medical-section {
        border-left: 4px solid #2E8B57;
        padding-left: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'medical_system' not in st.session_state:
        compliance_level = st.session_state.get('compliance_level', HIPAACompliance.STANDARD)
        st.session_state.medical_system = MedicalTranscriptionSystem(compliance_level)
    
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    if 'current_report' not in st.session_state:
        st.session_state.current_report = None

def main():
    init_session_state()
    
    # Header
    st.markdown("""
    <div class="medical-header">
        <h1>🏥 Medical Transcription System</h1>
        <p>HIPAA-Compliant Medical Transcription with Specialized NLP</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ System Configuration")
        
        # HIPAA Compliance Level
        compliance_level = st.selectbox(
            "HIPAA Compliance Level",
            options=[HIPAACompliance.STRICT, HIPAACompliance.STANDARD, HIPAACompliance.RESEARCH],
            format_func=lambda x: {
                HIPAACompliance.STRICT: "🔒 Strict (No PHI allowed)",
                HIPAACompliance.STANDARD: "🛡️ Standard (PHI anonymized)",
                HIPAACompliance.RESEARCH: "📊 Research (Limited PHI)"
            }[x],
            index=1
        )
        
        if st.session_state.get('compliance_level') != compliance_level:
            st.session_state.compliance_level = compliance_level
            st.session_state.medical_system = MedicalTranscriptionSystem(compliance_level)
            st.success("Compliance level updated!")
        
        # Comprehensive Schema Processing
        if COMPREHENSIVE_SCHEMA_AVAILABLE:
            st.session_state.use_comprehensive_schema = st.checkbox(
                "🧠 Enable Comprehensive Analysis",
                value=st.session_state.get('use_comprehensive_schema', True),
                help="Enable advanced analysis including voice biomarkers, emotional state, social determinants, and ambient context"
            )
        
        st.divider()
        
        # Quick Stats
        st.header("📊 Quick Stats")
        
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Processed", len(st.session_state.processing_history))
            with col2:
                phi_count = sum(1 for h in st.session_state.processing_history if h.get('phi_detected', False))
                st.metric("PHI Detected", phi_count)
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🩺 Transcription", "📋 Reports", "🔍 Entity Analysis", 
        "🛡️ Compliance", "📊 Analytics"
    ])
    
    with tab1:
        render_transcription_tab()
    
    with tab2:
        render_reports_tab()
    
    with tab3:
        render_entity_analysis_tab()
    
    with tab4:
        render_compliance_tab()
    
    with tab5:
        render_analytics_tab()

def render_transcription_tab():
    st.header("🩺 Medical Transcription Processing")
    
    # Input form
    with st.form("transcription_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            transcript_text = st.text_area(
                "Medical Transcript",
                height=300,
                placeholder="Enter or paste medical transcript here...\n\nExample:\nPatient presents with chief complaint of chest pain.\nHistory of Present Illness: Patient reports onset of sharp chest pain 2 hours ago...",
                help="Enter the medical transcript text for processing"
            )
        
        with col2:
            st.subheader("Metadata")
            
            patient_id = st.text_input(
                "Patient ID",
                value=f"PATIENT_{datetime.now().strftime('%Y%m%d_%H%M')}",
                help="Anonymous patient identifier"
            )
            
            provider_id = st.text_input(
                "Provider ID",
                value="DR_ATTENDING",
                help="Provider identifier"
            )
            
            report_type = st.selectbox(
                "Report Type",
                options=['consultation', 'progress_note', 'discharge_summary'],
                format_func=lambda x: {
                    'consultation': '👨‍⚕️ Consultation Note',
                    'progress_note': '📝 Progress Note (SOAP)',
                    'discharge_summary': '🏠 Discharge Summary'
                }[x]
            )
            
            transcript_id = st.text_input(
                "Transcript ID",
                value=f"TRANS_{uuid.uuid4().hex[:8]}",
                help="Unique transcript identifier"
            )
        
        submitted = st.form_submit_button("🔄 Process Transcript", type="primary")
        
        if submitted:
            if not transcript_text.strip():
                st.error("Please enter transcript text to process.")
                return
            
            with st.spinner("Processing medical transcript..."):
                metadata = {
                    'patient_id': patient_id,
                    'provider_id': provider_id,
                    'report_type': report_type,
                    'transcript_id': transcript_id,
                    'user_id': 'streamlit_user'
                }
                
                result = st.session_state.medical_system.process_medical_transcription(
                    transcript_text, metadata
                )
                
                # Enhanced processing with comprehensive schema if available
                if COMPREHENSIVE_SCHEMA_AVAILABLE and st.session_state.get('use_comprehensive_schema', True):
                    try:
                        comprehensive_processor = ComprehensiveSchemaProcessor()
                        comprehensive_data = comprehensive_processor.process_comprehensive_transcript(
                            transcript_text, 
                            result.get('entities', []),
                            metadata
                        )
                        
                        # Merge comprehensive data into result
                        result.update({
                            'vital_signs': comprehensive_data.get('vital_signs', []),
                            'test_results': comprehensive_data.get('test_results', []),
                            'voice_biomarkers': comprehensive_data.get('voice_biomarkers', []),
                            'ambient_sounds': comprehensive_data.get('ambient_sounds', []),
                            'emotional_state': comprehensive_data.get('emotional_state', []),
                            'social_determinants': comprehensive_data.get('social_determinants', []),
                            'comprehensive_analysis': comprehensive_data.get('comprehensive_analysis', {})
                        })
                    except Exception as e:
                        st.warning(f"Comprehensive schema processing encountered an error: {e}")
                        st.info("Continuing with standard medical processing...")
                
                # Store in session state
                result['timestamp'] = datetime.now()
                result['original_text'] = transcript_text
                result['metadata'] = metadata
                st.session_state.processing_history.append(result)
                st.session_state.current_report = result
    
    # Display results
    if st.session_state.current_report:
        display_processing_results(st.session_state.current_report)

def display_processing_results(result):
    """Display processing results with appropriate styling"""
    
    if result['success']:
        st.success("✅ Transcript processed successfully!")
        
        # PHI Violations Alert
        if result.get('phi_violations'):
            st.markdown("""
            <div class="phi-warning">
                <h4>⚠️ PHI Detection Alert</h4>
                <p>Protected Health Information (PHI) was detected and handled according to your compliance settings.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View PHI Violations", expanded=False):
                for violation in result['phi_violations']:
                    st.write(f"**Type:** {violation.violation_type}")
                    st.write(f"**Text:** `{violation.text}`")
                    st.write(f"**Severity:** {violation.severity}")
                    st.write(f"**Recommendation:** {violation.recommendation}")
                    st.divider()
        
        # Extracted Entities
        if result.get('entities'):
            st.subheader("🔍 Extracted Medical Entities")
            
            # Group entities by type
            entity_groups = {}
            for entity in result['entities']:
                entity_type = entity['entity_type']
                if entity_type not in entity_groups:
                    entity_groups[entity_type] = []
                entity_groups[entity_type].append(entity)
            
            # Display entities by type
            for entity_type, entities in entity_groups.items():
                with st.expander(f"{entity_type.title()} ({len(entities)})", expanded=True):
                    for entity in entities:
                        confidence_color = "🟢" if entity['confidence'] > 0.8 else "🟡" if entity['confidence'] > 0.6 else "🔴"
                        st.markdown(f"""
                        **{entity['text']}** {confidence_color} {entity['confidence']:.2f}
                        - **Normalized:** {entity['normalized_form']}
                        - **Context:** {entity.get('context', 'N/A')}
                        """)
        
        # Medical Report Sections
        if result.get('sections'):
            st.subheader("📋 Generated Medical Report")
            
            for section_name, content in result['sections'].items():
                if content.strip():
                    st.markdown(f"""
                    <div class="medical-section">
                        <h4>{section_name.replace('_', ' ').title()}</h4>
                        <p>{content}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Clinical Information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if result.get('medications'):
                st.subheader("💊 Medications")
                for med in result['medications']:
                    st.markdown(f"• **{med['name']}** ({med['confidence']:.2f})")
        
        with col2:
            if result.get('procedures'):
                st.subheader("🔬 Procedures")
                for proc in result['procedures']:
                    st.markdown(f"• **{proc['name']}** ({proc['confidence']:.2f})")
        
        with col3:
            if result.get('diagnoses'):
                st.subheader("🩺 Diagnoses")
                for diag in result['diagnoses']:
                    st.markdown(f"• **{diag['name']}** ({diag['confidence']:.2f})")
        
        # Comprehensive Analysis Dashboard
        if result.get('comprehensive_analysis'):
            st.subheader("🧠 Comprehensive Clinical Analysis")
            
            # Analysis metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Patient Engagement Score",
                    f"{result['comprehensive_analysis']['patient_engagement_score']:.1f}",
                    help="Overall patient engagement and participation level"
                )
            
            with col2:
                excellent_indicators = len([i for i in result['comprehensive_analysis']['care_quality_indicators'] 
                                         if i['status'] == 'excellent'])
                st.metric(
                    "Excellent Quality Indicators",
                    excellent_indicators,
                    help="Number of care quality indicators rated as excellent"
                )
            
            with col3:
                high_priority = len([r for r in result['comprehensive_analysis']['clinical_decision_support'] 
                                   if r['priority'] == 'high'])
                st.metric(
                    "High Priority Actions",
                    high_priority,
                    help="Number of high-priority clinical recommendations"
                )
            
            # Care Quality Indicators
            if result['comprehensive_analysis']['care_quality_indicators']:
                st.markdown("#### 📊 Care Quality Assessment")
                for indicator in result['comprehensive_analysis']['care_quality_indicators']:
                    status_emoji = {
                        'excellent': '🟢',
                        'good': '🔵',
                        'needs_improvement': '🟡',
                        'concerning': '🔴'
                    }
                    st.markdown(f"""
                    {status_emoji.get(indicator['status'], '⚪')} **{indicator['indicator']}**: {indicator['status'].replace('_', ' ').title()}
                    - {indicator['details']}
                    """)
            
            # Clinical Decision Support
            if result['comprehensive_analysis']['clinical_decision_support']:
                st.markdown("#### 🎯 Clinical Decision Support")
                for recommendation in result['comprehensive_analysis']['clinical_decision_support']:
                    priority_color = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    st.markdown(f"""
                    {priority_color.get(recommendation['priority'], '⚪')} **{recommendation['priority'].upper()} PRIORITY**
                    - {recommendation['recommendation']}
                    - *Evidence Level: {recommendation['evidence_level']}*
                    """)
        
        # Advanced Clinical Data
        st.subheader("🔬 Advanced Clinical Analysis")
        
        # Create tabs for different data types
        advanced_tabs = []
        advanced_data = {}
        
        if result.get('vital_signs'):
            advanced_tabs.append("Vital Signs")
            advanced_data["Vital Signs"] = result['vital_signs']
        
        if result.get('test_results'):
            advanced_tabs.append("Lab Results")
            advanced_data["Lab Results"] = result['test_results']
        
        if result.get('voice_biomarkers'):
            advanced_tabs.append("Voice Biomarkers")
            advanced_data["Voice Biomarkers"] = result['voice_biomarkers']
        
        if result.get('emotional_state'):
            advanced_tabs.append("Emotional Analysis")
            advanced_data["Emotional Analysis"] = result['emotional_state']
        
        if result.get('social_determinants'):
            advanced_tabs.append("Social Determinants")
            advanced_data["Social Determinants"] = result['social_determinants']
        
        if result.get('ambient_sounds'):
            advanced_tabs.append("Environmental Context")
            advanced_data["Environmental Context"] = result['ambient_sounds']
        
        if advanced_tabs:
            tabs = st.tabs(advanced_tabs)
            
            for i, tab_name in enumerate(advanced_tabs):
                with tabs[i]:
                    data = advanced_data[tab_name]
                    
                    if tab_name == "Vital Signs":
                        for vital in data:
                            col1, col2, col3 = st.columns([2, 1, 2])
                            with col1:
                                st.write(f"**{vital['type']}**")
                            with col2:
                                st.write(f"{vital['value']} {vital['unit']}")
                            with col3:
                                if vital.get('interpretation'):
                                    st.write(vital['interpretation'])
                    
                    elif tab_name == "Lab Results":
                        for test in data:
                            result_color = "🔴" if test.get('abnormal') else "🟢"
                            st.markdown(f"""
                            {result_color} **{test['test_name']}**: {test['value']}
                            {f"*Reference: {test['reference_range']}*" if test.get('reference_range') else ""}
                            {f"- {test['interpretation']}" if test.get('interpretation') else ""}
                            """)
                    
                    elif tab_name == "Voice Biomarkers":
                        for biomarker in data:
                            st.markdown(f"""
                            **{biomarker['biomarker_type']}**
                            - Value: {biomarker['value']} (Confidence: {biomarker['confidence']:.2f})
                            - Interpretation: {biomarker['interpretation']}
                            """)
                    
                    elif tab_name == "Emotional Analysis":
                        for emotion in data:
                            intensity_bar = "🔴" * min(int(emotion['intensity']), 10)
                            st.markdown(f"""
                            **{emotion['emotion']}** {intensity_bar} ({emotion['intensity']}/10)
                            - Context: {emotion['context']}
                            """)
                    
                    elif tab_name == "Social Determinants":
                        for determinant in data:
                            impact_emoji = {
                                'high': '🔴',
                                'medium': '🟡',
                                'low': '🟢'
                            }
                            st.markdown(f"""
                            {impact_emoji.get(determinant['impact_level'], '⚪')} **{determinant['factor']}**
                            - Category: {determinant['category']}
                            - Impact Level: {determinant['impact_level'].title()}
                            {f"- Notes: {determinant['notes']}" if determinant.get('notes') else ""}
                            """)
                    
                    elif tab_name == "Environmental Context":
                        for sound in data:
                            st.markdown(f"""
                            **{sound['sound_type']}** ({sound['duration']}s)
                            - Context: {sound['context']}
                            {f"- Clinical Relevance: {sound['clinical_relevance']}" if sound.get('clinical_relevance') else ""}
                            """)
        
        # Compliance Status
        compliance_status = result.get('compliance_status', 'unknown')
        if compliance_status == 'compliant':
            st.markdown("""
            <div class="compliance-good">
                <h4>✅ HIPAA Compliant</h4>
                <p>This transcript meets HIPAA compliance requirements.</p>
            </div>
            """, unsafe_allow_html=True)
        elif compliance_status == 'pending_review':
            st.markdown("""
            <div class="compliance-warning">
                <h4>⏳ Pending Review</h4>
                <p>This transcript requires manual review for final compliance approval.</p>
            </div>
            """, unsafe_allow_html=True)
        
    else:
        st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        
        if result.get('violations'):
            st.warning("PHI violations detected:")
            for violation in result['violations']:
                st.write(f"• {violation.violation_type}: {violation.text}")

def render_reports_tab():
    st.header("📋 Medical Reports")
    
    if not st.session_state.processing_history:
        st.info("No reports generated yet. Process a transcript first!")
        return
    
    # Report selection
    report_options = []
    for i, report in enumerate(st.session_state.processing_history):
        if report['success']:
            timestamp = report['timestamp'].strftime('%Y-%m-%d %H:%M')
            patient_id = report['metadata']['patient_id']
            report_type = report['metadata']['report_type']
            report_options.append(f"{timestamp} - {patient_id} - {report_type}")
    
    if not report_options:
        st.warning("No successful reports available.")
        return
    
    selected_report_idx = st.selectbox(
        "Select Report",
        options=range(len(report_options)),
        format_func=lambda x: report_options[x]
    )
    
    # Find corresponding successful report
    successful_reports = [r for r in st.session_state.processing_history if r['success']]
    if selected_report_idx < len(successful_reports):
        selected_report = successful_reports[selected_report_idx]
        
        # Display report details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Report Content")
            
            # Original transcript
            with st.expander("Original Transcript"):
                st.text_area("", value=selected_report['original_text'], height=200, disabled=True)
            
            # Report sections
            if selected_report.get('sections'):
                for section_name, content in selected_report['sections'].items():
                    if content.strip():
                        with st.expander(section_name.replace('_', ' ').title(), expanded=True):
                            st.write(content)
        
        with col2:
            st.subheader("Report Metadata")
            
            metadata = selected_report['metadata']
            st.write(f"**Patient ID:** {metadata['patient_id']}")
            st.write(f"**Provider ID:** {metadata['provider_id']}")
            st.write(f"**Report Type:** {metadata['report_type']}")
            st.write(f"**Transcript ID:** {metadata['transcript_id']}")
            st.write(f"**Processed:** {selected_report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Compliance Status:** {selected_report.get('compliance_status', 'N/A')}")
            
            st.divider()
            
            # Export options
            st.subheader("Export Options")
            
            if st.button("📄 Export as JSON"):
                export_data = {
                    'report_id': selected_report.get('report_id'),
                    'metadata': metadata,
                    'sections': selected_report.get('sections', {}),
                    'entities': selected_report.get('entities', []),
                    'medications': selected_report.get('medications', []),
                    'procedures': selected_report.get('procedures', []),
                    'diagnoses': selected_report.get('diagnoses', []),
                    'processed_at': selected_report['timestamp'].isoformat()
                }
                
                st.download_button(
                    "Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"medical_report_{metadata['patient_id']}_{selected_report['timestamp'].strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )

def render_entity_analysis_tab():
    st.header("🔍 Medical Entity Analysis")
    
    if not st.session_state.processing_history:
        st.info("No data available. Process transcripts first!")
        return
    
    # Aggregate entities from all reports
    all_entities = []
    for report in st.session_state.processing_history:
        if report['success'] and report.get('entities'):
            for entity in report['entities']:
                entity['report_timestamp'] = report['timestamp']
                entity['patient_id'] = report['metadata']['patient_id']
                all_entities.append(entity)
    
    if not all_entities:
        st.warning("No entities extracted from processed transcripts.")
        return
    
    # Entity statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entities", len(all_entities))
    
    with col2:
        entity_types = set(e['entity_type'] for e in all_entities)
        st.metric("Entity Types", len(entity_types))
    
    with col3:
        high_confidence = sum(1 for e in all_entities if e['confidence'] > 0.8)
        st.metric("High Confidence", high_confidence)
    
    with col4:
        avg_confidence = sum(e['confidence'] for e in all_entities) / len(all_entities)
        st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    # Entity type distribution
    st.subheader("📊 Entity Type Distribution")
    
    entity_counts = {}
    for entity in all_entities:
        entity_type = entity['entity_type']
        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
    
    if entity_counts:
        fig = px.pie(
            values=list(entity_counts.values()),
            names=list(entity_counts.keys()),
            title="Distribution of Medical Entity Types"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Confidence distribution
    st.subheader("📈 Confidence Score Distribution")
    
    confidence_scores = [e['confidence'] for e in all_entities]
    fig = px.histogram(
        x=confidence_scores,
        bins=20,
        title="Distribution of Entity Confidence Scores",
        labels={'x': 'Confidence Score', 'y': 'Count'}
    )
    fig.add_vline(x=0.8, line_dash="dash", line_color="red", 
                  annotation_text="High Confidence Threshold")
    st.plotly_chart(fig, use_container_width=True)
    
    # Entity details table
    st.subheader("🔍 Entity Details")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entity_type_filter = st.multiselect(
            "Filter by Entity Type",
            options=list(entity_types),
            default=list(entity_types)
        )
    
    with col2:
        min_confidence = st.slider(
            "Minimum Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1
        )
    
    with col3:
        max_entities = st.number_input(
            "Max Entities to Show",
            min_value=10,
            max_value=1000,
            value=100,
            step=10
        )
    
    # Filter and display entities
    filtered_entities = [
        e for e in all_entities
        if e['entity_type'] in entity_type_filter and e['confidence'] >= min_confidence
    ]
    
    filtered_entities = sorted(filtered_entities, key=lambda x: x['confidence'], reverse=True)[:max_entities]
    
    if filtered_entities:
        entity_df = pd.DataFrame([
            {
                'Text': e['text'],
                'Type': e['entity_type'],
                'Confidence': f"{e['confidence']:.3f}",
                'Normalized': e['normalized_form'],
                'Patient ID': e['patient_id'],
                'Timestamp': e['report_timestamp'].strftime('%Y-%m-%d %H:%M')
            }
            for e in filtered_entities
        ])
        
        st.dataframe(entity_df, use_container_width=True)
    else:
        st.warning("No entities match the current filters.")

def render_compliance_tab():
    st.header("🛡️ HIPAA Compliance Dashboard")
    
    # Compliance report
    compliance_report = st.session_state.medical_system.get_compliance_report()
    
    # Summary metrics
    st.subheader("📊 Compliance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Transcriptions",
            compliance_report['summary']['total_transcriptions']
        )
    
    with col2:
        st.metric(
            "PHI Incidents",
            compliance_report['summary']['phi_incidents_detected']
        )
    
    with col3:
        st.metric(
            "Unresolved PHI",
            compliance_report['summary']['unresolved_phi_incidents']
        )
    
    with col4:
        compliance_rate = compliance_report['summary']['compliance_rate']
        st.metric(
            "Compliance Rate",
            f"{compliance_rate:.1f}%"
        )
    
    # Compliance status indicator
    if compliance_rate >= 95:
        st.markdown("""
        <div class="compliance-good">
            <h4>✅ Excellent Compliance</h4>
            <p>Your system maintains excellent HIPAA compliance standards.</p>
        </div>
        """, unsafe_allow_html=True)
    elif compliance_rate >= 85:
        st.markdown("""
        <div class="compliance-warning">
            <h4>⚠️ Good Compliance</h4>
            <p>Your system maintains good compliance but has room for improvement.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="compliance-danger">
            <h4>🚨 Compliance Attention Required</h4>
            <p>Your system requires immediate attention to improve HIPAA compliance.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Audit activity
    if compliance_report.get('audit_activity'):
        st.subheader("📋 Audit Activity")
        
        audit_df = pd.DataFrame([
            {'Action': action, 'Count': count}
            for action, count in compliance_report['audit_activity'].items()
        ])
        
        fig = px.bar(
            audit_df,
            x='Action',
            y='Count',
            title="Audit Events by Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # PHI Incidents from session
    phi_incidents = []
    for report in st.session_state.processing_history:
        if report.get('phi_violations'):
            for violation in report['phi_violations']:
                phi_incidents.append({
                    'timestamp': report['timestamp'],
                    'patient_id': report['metadata']['patient_id'],
                    'violation_type': violation.violation_type,
                    'severity': violation.severity,
                    'text': violation.text[:50] + '...' if len(violation.text) > 50 else violation.text
                })
    
    if phi_incidents:
        st.subheader("⚠️ PHI Incidents")
        
        phi_df = pd.DataFrame(phi_incidents)
        st.dataframe(phi_df, use_container_width=True)
    
    # Compliance recommendations
    st.subheader("💡 Compliance Recommendations")
    
    if compliance_rate < 95:
        st.warning("""
        **Recommendations to improve compliance:**
        - Review and update PHI detection patterns
        - Provide additional training on HIPAA requirements
        - Implement stricter validation before processing
        - Regular audit of transcription processes
        """)
    else:
        st.success("""
        **Your compliance is excellent! Continue with:**
        - Regular monitoring and auditing
        - Keeping staff training up to date
        - Reviewing and updating policies as needed
        """)

def render_analytics_tab():
    st.header("📊 Medical Transcription Analytics")
    
    if not st.session_state.processing_history:
        st.info("No data available. Process transcripts first!")
        return
    
    # Processing trends
    st.subheader("📈 Processing Trends")
    
    # Create time series data
    processing_data = []
    for report in st.session_state.processing_history:
        processing_data.append({
            'timestamp': report['timestamp'],
            'success': report['success'],
            'entity_count': len(report.get('entities', [])),
            'phi_detected': bool(report.get('phi_violations')),
            'report_type': report['metadata']['report_type']
        })
    
    if processing_data:
        df = pd.DataFrame(processing_data)
        
        # Success rate over time
        fig = px.line(
            df,
            x='timestamp',
            y='success',
            title="Processing Success Rate Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Entity extraction over time
        fig = px.scatter(
            df,
            x='timestamp',
            y='entity_count',
            color='report_type',
            size='entity_count',
            title="Medical Entities Extracted Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Report type distribution
    st.subheader("📋 Report Type Distribution")
    
    report_types = {}
    for report in st.session_state.processing_history:
        if report['success']:
            report_type = report['metadata']['report_type']
            report_types[report_type] = report_types.get(report_type, 0) + 1
    
    if report_types:
        fig = px.bar(
            x=list(report_types.keys()),
            y=list(report_types.values()),
            title="Distribution of Report Types"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("⚡ Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        successful_reports = [r for r in st.session_state.processing_history if r['success']]
        success_rate = len(successful_reports) / len(st.session_state.processing_history) * 100 if st.session_state.processing_history else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col2:
        phi_reports = [r for r in st.session_state.processing_history if r.get('phi_violations')]
        phi_rate = len(phi_reports) / len(st.session_state.processing_history) * 100 if st.session_state.processing_history else 0
        st.metric("PHI Detection Rate", f"{phi_rate:.1f}%")
    
    with col3:
        avg_entities = sum(len(r.get('entities', [])) for r in successful_reports) / len(successful_reports) if successful_reports else 0
        st.metric("Avg Entities/Report", f"{avg_entities:.1f}")
    
    # System usage
    st.subheader("🔍 System Usage Analytics")
    
    if st.session_state.processing_history:
        # Usage by hour
        hourly_usage = {}
        for report in st.session_state.processing_history:
            hour = report['timestamp'].hour
            hourly_usage[hour] = hourly_usage.get(hour, 0) + 1
        
        hours = list(range(24))
        usage_counts = [hourly_usage.get(h, 0) for h in hours]
        
        fig = px.bar(
            x=hours,
            y=usage_counts,
            title="System Usage by Hour of Day",
            labels={'x': 'Hour', 'y': 'Number of Transcriptions'}
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()