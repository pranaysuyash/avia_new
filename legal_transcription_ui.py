#!/usr/bin/env python3
"""
Streamlit UI for legal transcription and analysis system.
Provides comprehensive interface for legal document processing with compliance features.
"""

import streamlit as st
import pandas as pd
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

from legal_transcription_system import LegalTranscriptionSystem
from legal_schema_processor import LegalSchemaProcessor

# Initialize systems
@st.cache_resource
def get_legal_system():
    """Get cached legal transcription system."""
    return LegalTranscriptionSystem()

@st.cache_resource  
def get_schema_processor():
    """Get cached schema processor."""
    return LegalSchemaProcessor()

def main():
    """Main legal transcription UI application."""
    st.set_page_config(
        page_title="Legal Transcription & Analysis",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("⚖️ Legal Transcription & Analysis System")
    st.markdown("Professional legal document processing with compliance features")
    
    # Initialize systems
    legal_system = get_legal_system()
    schema_processor = get_schema_processor()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Function",
        [
            "Audio Transcription",
            "Text Analysis", 
            "Document Search",
            "Compliance Check",
            "Export & Reports",
            "Case Management"
        ]
    )
    
    if page == "Audio Transcription":
        render_audio_transcription_page(legal_system, schema_processor)
    elif page == "Text Analysis":
        render_text_analysis_page(legal_system, schema_processor)
    elif page == "Document Search":
        render_document_search_page(legal_system, schema_processor)
    elif page == "Compliance Check":
        render_compliance_check_page(legal_system, schema_processor)
    elif page == "Export & Reports":
        render_export_reports_page(legal_system, schema_processor)
    elif page == "Case Management":
        render_case_management_page(legal_system, schema_processor)


def render_audio_transcription_page(legal_system, schema_processor):
    """Render the audio transcription page."""
    st.header("🎙️ Legal Audio Transcription")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Audio File")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose audio file",
            type=['wav', 'mp3', 'mp4', 'm4a', 'flac'],
            help="Upload legal proceeding audio file"
        )
        
        if uploaded_file:
            # Case information
            st.subheader("Case Information")
            
            col_a, col_b = st.columns(2)
            with col_a:
                case_number = st.text_input("Case Number", placeholder="2023-CV-1234")
                proceeding_type = st.selectbox(
                    "Proceeding Type",
                    ["hearing", "deposition", "trial", "mediation", "arbitration", "conference"]
                )
                
            with col_b:
                court_jurisdiction = st.text_input("Court Jurisdiction", placeholder="Federal District Court")
                confidentiality_level = st.selectbox(
                    "Confidentiality Level",
                    ["standard", "confidential", "privileged", "sealed"]
                )
            
            # Participants
            participants_text = st.text_area(
                "Participants (one per line)",
                placeholder="Judge Smith\nAttorney Jones\nWitness Doe"
            )
            participants = [p.strip() for p in participants_text.split('\n') if p.strip()]
            
            # Attorney-client privilege
            attorney_client_privilege = st.checkbox(
                "Contains Attorney-Client Privileged Communications",
                help="Check if the recording contains privileged communications"
            )
            
            # Process button
            if st.button("🔄 Process Legal Transcription", type="primary"):
                with st.spinner("Processing legal audio transcription..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_file_path = tmp_file.name
                        
                        # Process transcription
                        result = legal_system.process_legal_recording(
                            tmp_file_path,
                            case_number=case_number,
                            proceeding_type=proceeding_type,
                            participants=participants,
                            confidentiality_level=confidentiality_level,
                            court_jurisdiction=court_jurisdiction,
                            attorney_client_privilege=attorney_client_privilege
                        )
                        
                        # Clean up temp file
                        os.unlink(tmp_file_path)
                        
                        # Store result in session state
                        st.session_state['transcription_result'] = result
                        
                        st.success("✅ Legal transcription completed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Transcription failed: {str(e)}")
    
    with col2:
        st.subheader("Processing Options")
        
        # Advanced options
        with st.expander("Advanced Settings"):
            enable_speaker_diarization = st.checkbox("Enable Speaker Diarization", value=True)
            enhance_legal_terminology = st.checkbox("Enhance Legal Terminology", value=True)
            auto_redaction = st.checkbox("Auto-suggest Redactions", value=True)
            format_citations = st.checkbox("Format Legal Citations", value=True)
        
        # Processing status
        if 'transcription_result' in st.session_state:
            result = st.session_state['transcription_result']
            
            st.success("Processing Complete")
            st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
            st.metric("Confidence Score", f"{result.get('confidence_score', 0):.2f}")
            
            # Quick stats
            if 'legal_analysis' in result:
                analysis = result['legal_analysis']
                st.metric("Legal Entities", len(analysis.get('entities', [])))
                st.metric("Document Type", analysis.get('document_type', 'Unknown'))
    
    # Display results
    if 'transcription_result' in st.session_state:
        display_transcription_results(st.session_state['transcription_result'], schema_processor)


def render_text_analysis_page(legal_system, schema_processor):
    """Render the text analysis page."""
    st.header("📄 Legal Text Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Input Legal Text")
        
        # Text input options
        input_method = st.radio(
            "Input Method",
            ["Direct Text", "Upload Document"],
            horizontal=True
        )
        
        legal_text = ""
        
        if input_method == "Direct Text":
            legal_text = st.text_area(
                "Legal Text",
                height=300,
                placeholder="Paste legal document text here..."
            )
        else:
            uploaded_doc = st.file_uploader(
                "Upload Document",
                type=['txt', 'pdf', 'docx'],
                help="Upload legal document for analysis"
            )
            
            if uploaded_doc:
                # Process uploaded document
                if uploaded_doc.type == "text/plain":
                    legal_text = str(uploaded_doc.read(), "utf-8")
                else:
                    st.info("PDF and DOCX processing requires additional libraries")
        
        if legal_text and st.button("🔍 Analyze Legal Text", type="primary"):
            with st.spinner("Analyzing legal text..."):
                try:
                    # Perform analysis
                    analysis_result = legal_system.analyze_legal_content(legal_text)
                    entities = schema_processor.extract_legal_entities(legal_text)
                    privilege_markers = schema_processor.detect_privilege_markers(legal_text)
                    redaction_suggestions = schema_processor.suggest_redactions(legal_text)
                    document_type = schema_processor.classify_document_type(legal_text)
                    
                    # Store results
                    st.session_state['analysis_result'] = {
                        'text': legal_text,
                        'analysis': analysis_result,
                        'entities': entities,
                        'privilege_markers': privilege_markers,
                        'redaction_suggestions': redaction_suggestions,
                        'document_type': document_type
                    }
                    
                    st.success("✅ Analysis completed successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
    
    with col2:
        st.subheader("Analysis Options")
        
        # Analysis settings
        with st.expander("Analysis Settings"):
            extract_entities = st.checkbox("Extract Legal Entities", value=True)
            detect_privilege = st.checkbox("Detect Privilege Markers", value=True)
            suggest_redactions = st.checkbox("Suggest Redactions", value=True)
            classify_document = st.checkbox("Classify Document Type", value=True)
        
        # Quick stats
        if 'analysis_result' in st.session_state:
            result = st.session_state['analysis_result']
            
            st.success("Analysis Complete")
            st.metric("Document Type", result.get('document_type', 'Unknown'))
            st.metric("Legal Entities", len(result.get('entities', [])))
            st.metric("Privilege Markers", len(result.get('privilege_markers', [])))
            st.metric("Redaction Suggestions", len(result.get('redaction_suggestions', [])))
    
    # Display analysis results
    if 'analysis_result' in st.session_state:
        display_analysis_results(st.session_state['analysis_result'])


def render_document_search_page(legal_system, schema_processor):
    """Render the document search page."""
    st.header("🔍 Legal Document Search")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Search Parameters")
        
        # Search query
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter search terms, case names, or legal concepts"
        )
        
        # Filters
        col_a, col_b = st.columns(2)
        with col_a:
            case_filter = st.text_input("Case Number Filter", placeholder="2023-CV-1234")
            document_type_filter = st.selectbox(
                "Document Type Filter",
                ["All", "motion", "deposition", "hearing", "trial", "brief", "contract"]
            )
        
        with col_b:
            date_from = st.date_input("Date From")
            date_to = st.date_input("Date To")
        
        if st.button("🔍 Search Documents", type="primary"):
            with st.spinner("Searching legal documents..."):
                try:
                    # Prepare search parameters
                    search_params = {
                        'query': search_query,
                        'case_number': case_filter if case_filter else None,
                        'document_type': document_type_filter if document_type_filter != "All" else None,
                        'date_range': {
                            'from': date_from.isoformat(),
                            'to': date_to.isoformat()
                        } if date_from and date_to else None
                    }
                    
                    # Perform search
                    search_results = legal_system.search_legal_documents(**search_params)
                    
                    # Store results
                    st.session_state['search_results'] = search_results
                    
                    st.success(f"✅ Found {len(search_results)} documents")
                    
                except Exception as e:
                    st.error(f"❌ Search failed: {str(e)}")
    
    with col2:
        st.subheader("Search Options")
        
        with st.expander("Advanced Search"):
            semantic_search = st.checkbox("Semantic Search", value=True)
            include_entities = st.checkbox("Include Entity Matching", value=True)
            relevance_threshold = st.slider("Relevance Threshold", 0.0, 1.0, 0.5)
        
        # Search stats
        if 'search_results' in st.session_state:
            results = st.session_state['search_results']
            
            st.success("Search Complete")
            st.metric("Total Results", len(results))
            
            if results:
                avg_relevance = sum(r.get('relevance_score', 0) for r in results) / len(results)
                st.metric("Avg Relevance", f"{avg_relevance:.2f}")
    
    # Display search results
    if 'search_results' in st.session_state:
        display_search_results(st.session_state['search_results'])


def render_compliance_check_page(legal_system, schema_processor):
    """Render the compliance check page."""
    st.header("✅ Legal Compliance Check")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Compliance Validation")
        
        # Document selection
        document_source = st.radio(
            "Document Source",
            ["Upload Document", "Use Previous Analysis"],
            horizontal=True
        )
        
        document_text = ""
        
        if document_source == "Upload Document":
            uploaded_file = st.file_uploader(
                "Upload Document for Compliance Check",
                type=['txt', 'pdf', 'docx']
            )
            
            if uploaded_file and uploaded_file.type == "text/plain":
                document_text = str(uploaded_file.read(), "utf-8")
        
        elif 'analysis_result' in st.session_state:
            document_text = st.session_state['analysis_result'].get('text', '')
            st.info("Using text from previous analysis")
        
        # Compliance standards
        st.subheader("Compliance Standards")
        compliance_standards = st.multiselect(
            "Select Standards to Check",
            ["federal_rules", "state_rules", "court_rules", "ethics_rules", "privacy_rules"],
            default=["federal_rules", "court_rules"]
        )
        
        if document_text and st.button("🔍 Check Compliance", type="primary"):
            with st.spinner("Checking compliance..."):
                try:
                    # Perform compliance check
                    compliance_result = legal_system.validate_comprehensive_compliance(
                        {'transcript': document_text},
                        standards=compliance_standards
                    )
                    
                    # Store results
                    st.session_state['compliance_result'] = compliance_result
                    
                    st.success("✅ Compliance check completed!")
                    
                except Exception as e:
                    st.error(f"❌ Compliance check failed: {str(e)}")
    
    with col2:
        st.subheader("Compliance Options")
        
        with st.expander("Check Settings"):
            strict_mode = st.checkbox("Strict Mode", value=False)
            include_recommendations = st.checkbox("Include Recommendations", value=True)
            detailed_analysis = st.checkbox("Detailed Analysis", value=True)
        
        # Compliance stats
        if 'compliance_result' in st.session_state:
            result = st.session_state['compliance_result']
            
            st.success("Check Complete")
            overall_score = result.get('overall_score', 0)
            st.metric("Overall Score", f"{overall_score:.1f}/10")
            
            # Score color coding
            if overall_score >= 8:
                st.success("🟢 High Compliance")
            elif overall_score >= 6:
                st.warning("🟡 Moderate Compliance")
            else:
                st.error("🔴 Low Compliance")
    
    # Display compliance results
    if 'compliance_result' in st.session_state:
        display_compliance_results(st.session_state['compliance_result'])


def render_export_reports_page(legal_system, schema_processor):
    """Render the export and reports page."""
    st.header("📊 Export & Reports")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Export Options")
        
        # Export format selection
        export_format = st.selectbox(
            "Export Format",
            ["Court Reporter Format", "Legal Brief Format", "Discovery Format", "JSON Data", "PDF Report"]
        )
        
        # Export options
        include_analysis = st.checkbox("Include Legal Analysis", value=True)
        redact_privileged = st.checkbox("Redact Privileged Content", value=True)
        include_metadata = st.checkbox("Include Metadata", value=True)
        
        # Data source
        if 'transcription_result' in st.session_state or 'analysis_result' in st.session_state:
            if st.button("📄 Generate Export", type="primary"):
                with st.spinner("Generating export..."):
                    try:
                        # Determine data source
                        if 'transcription_result' in st.session_state:
                            data = st.session_state['transcription_result']
                        else:
                            data = st.session_state['analysis_result']
                        
                        # Generate export based on format
                        if export_format == "Court Reporter Format":
                            exported_content = legal_system.export_court_format(data, include_analysis)
                        elif export_format == "Legal Brief Format":
                            exported_content = legal_system.export_legal_brief_format(data, include_analysis)
                        elif export_format == "Discovery Format":
                            exported_content = legal_system.export_discovery_format(data, include_analysis)
                        elif export_format == "JSON Data":
                            exported_content = json.dumps(data, indent=2)
                        else:
                            exported_content = "PDF export requires additional implementation"
                        
                        # Store export
                        st.session_state['exported_content'] = exported_content
                        st.session_state['export_format'] = export_format
                        
                        st.success("✅ Export generated successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Export failed: {str(e)}")
        else:
            st.info("No data available for export. Please process a transcription or analysis first.")
    
    with col2:
        st.subheader("Report Statistics")
        
        # Generate statistics from available data
        if 'transcription_result' in st.session_state:
            result = st.session_state['transcription_result']
            
            st.metric("Document Type", result.get('legal_analysis', {}).get('document_type', 'Unknown'))
            st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
            
            entities = result.get('legal_analysis', {}).get('entities', [])
            st.metric("Legal Entities", len(entities))
        
        elif 'analysis_result' in st.session_state:
            result = st.session_state['analysis_result']
            
            st.metric("Document Type", result.get('document_type', 'Unknown'))
            st.metric("Text Length", len(result.get('text', '')))
            st.metric("Legal Entities", len(result.get('entities', [])))
    
    # Display export content
    if 'exported_content' in st.session_state:
        st.subheader(f"Exported Content - {st.session_state.get('export_format', 'Unknown Format')}")
        
        # Download button
        st.download_button(
            label="📥 Download Export",
            data=st.session_state['exported_content'],
            file_name=f"legal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        # Preview
        with st.expander("Preview Export Content"):
            st.text_area(
                "Export Preview",
                value=st.session_state['exported_content'][:2000] + "..." if len(st.session_state['exported_content']) > 2000 else st.session_state['exported_content'],
                height=400,
                disabled=True
            )


def render_case_management_page(legal_system, schema_processor):
    """Render the case management page."""
    st.header("📁 Case Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Case Information")
        
        # Case lookup
        case_number = st.text_input("Case Number", placeholder="2023-CV-1234")
        
        if case_number and st.button("🔍 Load Case Documents"):
            with st.spinner("Loading case documents..."):
                try:
                    # Get case documents
                    documents = legal_system.get_case_documents(case_number)
                    
                    # Store results
                    st.session_state['case_documents'] = documents
                    st.session_state['current_case'] = case_number
                    
                    st.success(f"✅ Loaded {len(documents)} documents for case {case_number}")
                    
                except Exception as e:
                    st.error(f"❌ Failed to load case documents: {str(e)}")
        
        # Case statistics
        if 'case_documents' in st.session_state:
            documents = st.session_state['case_documents']
            
            st.subheader("Case Statistics")
            
            # Document type distribution
            doc_types = {}
            for doc in documents:
                doc_type = doc.get('document_type', 'Unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            if doc_types:
                fig = px.pie(
                    values=list(doc_types.values()),
                    names=list(doc_types.keys()),
                    title="Document Type Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Case Actions")
        
        if 'current_case' in st.session_state:
            current_case = st.session_state['current_case']
            
            st.info(f"Current Case: {current_case}")
            
            # Case actions
            if st.button("📊 Generate Case Report"):
                st.info("Case report generation would be implemented here")
            
            if st.button("🔍 Search Within Case"):
                st.info("Case-specific search would be implemented here")
            
            if st.button("📤 Export Case Data"):
                st.info("Case data export would be implemented here")
        
        else:
            st.info("Select a case to view available actions")
    
    # Display case documents
    if 'case_documents' in st.session_state:
        display_case_documents(st.session_state['case_documents'])


def display_transcription_results(result: Dict[str, Any], schema_processor):
    """Display transcription results."""
    st.subheader("📝 Transcription Results")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Transcript", "Legal Analysis", "Entities", "Compliance"])
    
    with tab1:
        st.subheader("Full Transcript")
        transcript = result.get('transcript', 'No transcript available')
        st.text_area("Transcript", value=transcript, height=400, disabled=True)
        
        # Speaker segments if available
        if 'speaker_segments' in result:
            st.subheader("Speaker Segments")
            segments_df = pd.DataFrame(result['speaker_segments'])
            st.dataframe(segments_df, use_container_width=True)
    
    with tab2:
        st.subheader("Legal Analysis")
        analysis = result.get('legal_analysis', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Document Type", analysis.get('document_type', 'Unknown'))
            st.metric("Confidence Score", f"{analysis.get('confidence_score', 0):.2f}")
        
        with col2:
            st.metric("Legal Entities Found", len(analysis.get('entities', [])))
            st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
    
    with tab3:
        st.subheader("Legal Entities")
        entities = result.get('legal_analysis', {}).get('entities', [])
        
        if entities:
            entities_df = pd.DataFrame(entities)
            st.dataframe(entities_df, use_container_width=True)
            
            # Entity type distribution
            entity_types = {}
            for entity in entities:
                entity_type = entity.get('type', 'Unknown')
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            if entity_types:
                fig = px.bar(
                    x=list(entity_types.keys()),
                    y=list(entity_types.values()),
                    title="Entity Type Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No legal entities found")
    
    with tab4:
        st.subheader("Compliance Information")
        compliance = result.get('compliance_check', {})
        
        if compliance:
            st.metric("Compliance Score", f"{compliance.get('overall_score', 0):.1f}/10")
            
            # Compliance details
            if 'checks' in compliance:
                checks_df = pd.DataFrame(compliance['checks'])
                st.dataframe(checks_df, use_container_width=True)
        else:
            st.info("No compliance information available")


def display_analysis_results(result: Dict[str, Any]):
    """Display text analysis results."""
    st.subheader("📊 Analysis Results")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Entities", "Privilege", "Redactions"])
    
    with tab1:
        st.subheader("Document Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Document Type", result.get('document_type', 'Unknown'))
        with col2:
            st.metric("Legal Entities", len(result.get('entities', [])))
        with col3:
            st.metric("Text Length", len(result.get('text', '')))
    
    with tab2:
        st.subheader("Legal Entities")
        entities = result.get('entities', [])
        
        if entities:
            entities_df = pd.DataFrame(entities)
            st.dataframe(entities_df, use_container_width=True)
        else:
            st.info("No legal entities found")
    
    with tab3:
        st.subheader("Privilege Markers")
        privilege_markers = result.get('privilege_markers', [])
        
        if privilege_markers:
            privilege_df = pd.DataFrame(privilege_markers)
            st.dataframe(privilege_df, use_container_width=True)
        else:
            st.info("No privilege markers detected")
    
    with tab4:
        st.subheader("Redaction Suggestions")
        redactions = result.get('redaction_suggestions', [])
        
        if redactions:
            redactions_df = pd.DataFrame(redactions)
            st.dataframe(redactions_df, use_container_width=True)
        else:
            st.info("No redaction suggestions")


def display_search_results(results: List[Dict[str, Any]]):
    """Display search results."""
    st.subheader("🔍 Search Results")
    
    if results:
        for i, result in enumerate(results):
            with st.expander(f"Result {i+1}: {result.get('title', 'Untitled')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Case:** {result.get('case_number', 'Unknown')}")
                    st.write(f"**Type:** {result.get('document_type', 'Unknown')}")
                    st.write(f"**Content Preview:** {result.get('content', '')[:200]}...")
                
                with col2:
                    st.metric("Relevance", f"{result.get('relevance_score', 0):.2f}")
                    st.write(f"**Date:** {result.get('date', 'Unknown')}")
    else:
        st.info("No search results found")


def display_compliance_results(result: Dict[str, Any]):
    """Display compliance check results."""
    st.subheader("✅ Compliance Results")
    
    overall_score = result.get('overall_score', 0)
    
    # Overall score display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{overall_score:.1f}/10")
    with col2:
        status = "Pass" if overall_score >= 7 else "Review Required" if overall_score >= 5 else "Fail"
        st.metric("Status", status)
    with col3:
        st.metric("Checks Performed", len(result.get('checks', [])))
    
    # Detailed checks
    if 'checks' in result:
        st.subheader("Detailed Checks")
        checks_df = pd.DataFrame(result['checks'])
        st.dataframe(checks_df, use_container_width=True)
    
    # Recommendations
    if 'recommendations' in result:
        st.subheader("Recommendations")
        for rec in result['recommendations']:
            st.write(f"• {rec}")


def display_case_documents(documents: List[Dict[str, Any]]):
    """Display case documents."""
    st.subheader("📁 Case Documents")
    
    if documents:
        # Create summary dataframe
        doc_data = []
        for doc in documents:
            doc_data.append({
                'ID': doc.get('id', 'Unknown'),
                'Type': doc.get('document_type', 'Unknown'),
                'Date': doc.get('date', 'Unknown'),
                'Title': doc.get('title', 'Untitled')[:50] + '...' if len(doc.get('title', '')) > 50 else doc.get('title', 'Untitled')
            })
        
        docs_df = pd.DataFrame(doc_data)
        st.dataframe(docs_df, use_container_width=True)
        
        # Document details
        selected_doc = st.selectbox("Select Document for Details", [doc.get('id', f'Doc {i}') for i, doc in enumerate(documents)])
        
        if selected_doc:
            # Find selected document
            doc = next((d for d in documents if d.get('id') == selected_doc), None)
            if doc:
                st.subheader(f"Document Details: {selected_doc}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {doc.get('document_type', 'Unknown')}")
                    st.write(f"**Date:** {doc.get('date', 'Unknown')}")
                
                with col2:
                    st.write(f"**Size:** {len(doc.get('content', ''))} characters")
                    st.write(f"**Entities:** {len(doc.get('entities', []))}")
                
                # Content preview
                content = doc.get('content', 'No content available')
                st.text_area("Content Preview", value=content[:1000] + "..." if len(content) > 1000 else content, height=200, disabled=True)
    else:
        st.info("No documents found for this case")


if __name__ == "__main__":
    main()