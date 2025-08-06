#!/usr/bin/env python3
"""
Advanced Document Analysis System - Streamlit UI
Professional interface for document analysis, classification, and insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import time

# Import our document analysis system
from advanced_document_analyzer import (
    AdvancedDocumentAnalyzer,
    create_searchable_index,
    search_documents
)

class AdvancedDocumentAnalyzerUI:
    """Streamlit UI for Advanced Document Analysis"""
    
    def __init__(self):
        self.analyzer = AdvancedDocumentAnalyzer()
        
        # Initialize session state
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = []
        if 'search_index' not in st.session_state:
            st.session_state.search_index = {}
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = set()
    
    def render_header(self):
        """Render the application header"""
        st.set_page_config(
            page_title="Advanced Document Analyzer",
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("📄 Advanced Document Analysis System")
        st.markdown("""
        **Comprehensive document processing with AI-powered analysis, classification, and insights extraction.**
        
        Upload documents to get:
        • Document classification and categorization
        • Entity extraction and insights
        • Form field and table extraction
        • Compliance checking and PII detection
        • Searchable document archive
        """)
    
    def render_sidebar(self):
        """Render the sidebar with controls"""
        st.sidebar.header("🔧 Analysis Settings")
        
        # Analysis options
        st.sidebar.subheader("Processing Options")
        extract_forms = st.sidebar.checkbox("Extract Form Fields", value=True)
        extract_tables = st.sidebar.checkbox("Extract Tables", value=True)
        
        # Language selection
        languages = [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('auto', 'Auto-detect')
        ]
        
        selected_lang = st.sidebar.selectbox(
            "Document Language",
            options=[code for code, _ in languages],
            format_func=lambda x: next(name for code, name in languages if code == x),
            index=0
        )
        
        # Batch processing
        st.sidebar.subheader("Batch Processing")
        batch_mode = st.sidebar.checkbox("Batch Mode", value=False)
        
        if batch_mode:
            st.sidebar.info("Upload multiple files for batch processing")
        
        # Clear results
        if st.sidebar.button("🗑️ Clear All Results"):
            st.session_state.analysis_results = []
            st.session_state.search_index = {}
            st.session_state.processed_files = set()
            st.rerun()
        
        return {
            'extract_forms': extract_forms,
            'extract_tables': extract_tables,
            'language': selected_lang,
            'batch_mode': batch_mode
        }
    
    def render_file_upload(self, settings: Dict[str, Any]):
        """Render file upload interface"""
        st.header("📁 Document Upload")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose document files",
            type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
            accept_multiple_files=settings['batch_mode'],
            help="Supported formats: PDF, TXT, PNG, JPG, JPEG, TIFF, BMP"
        )
        
        if uploaded_files:
            if not isinstance(uploaded_files, list):
                uploaded_files = [uploaded_files]
            
            # Process files
            if st.button("🚀 Analyze Documents", type="primary"):
                self.process_uploaded_files(uploaded_files, settings)
    
    def process_uploaded_files(self, uploaded_files: List, settings: Dict[str, Any]):
        """Process uploaded files"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            # Skip if already processed
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if file_key in st.session_state.processed_files:
                continue
            
            status_text.text(f"Processing {uploaded_file.name}...")
            
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Analyze document
                result = self.analyzer.analyze_document(
                    tmp_path,
                    language=settings['language'],
                    extract_forms=settings['extract_forms'],
                    extract_tables=settings['extract_tables']
                )
                
                # Add to results
                results.append(result)
                st.session_state.processed_files.add(file_key)
                
                # Clean up temp file
                Path(tmp_path).unlink()
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Add results to session state
        st.session_state.analysis_results.extend(results)
        
        # Update search index
        if results:
            st.session_state.search_index = create_searchable_index(st.session_state.analysis_results)
        
        status_text.text("✅ Processing complete!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
        
        if results:
            st.success(f"Successfully analyzed {len(results)} documents!")
            st.rerun()
    
    def render_results_overview(self):
        """Render results overview"""
        if not st.session_state.analysis_results:
            st.info("📄 Upload documents to see analysis results here.")
            return
        
        st.header("📊 Analysis Overview")
        
        results = st.session_state.analysis_results
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", len(results))
        
        with col2:
            avg_time = sum(r.processing_time for r in results) / len(results)
            st.metric("Avg Processing Time", f"{avg_time:.2f}s")
        
        with col3:
            total_flags = sum(len(r.insights.compliance_flags) for r in results)
            st.metric("Compliance Flags", total_flags)
        
        with col4:
            docs_with_forms = sum(1 for r in results if r.form_fields)
            st.metric("Documents with Forms", docs_with_forms)
        
        # Document type distribution
        doc_types = [r.classification.document_type for r in results]
        type_counts = pd.Series(doc_types).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Document Types")
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Document Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Processing Performance")
            processing_times = [r.processing_time for r in results]
            filenames = [r.filename for r in results]
            
            fig = px.bar(
                x=filenames,
                y=processing_times,
                title="Processing Time by Document",
                labels={'x': 'Document', 'y': 'Time (seconds)'}
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_document_details(self):
        """Render detailed document analysis"""
        if not st.session_state.analysis_results:
            return
        
        st.header("🔍 Document Details")
        
        results = st.session_state.analysis_results
        
        # Document selector
        selected_doc = st.selectbox(
            "Select Document",
            options=range(len(results)),
            format_func=lambda x: results[x].filename
        )
        
        if selected_doc is not None:
            result = results[selected_doc]
            
            # Document info
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📄 Document Information")
                st.write(f"**Filename:** {result.filename}")
                st.write(f"**Type:** {result.classification.document_type}")
                st.write(f"**Confidence:** {result.classification.confidence:.2f}")
                st.write(f"**Language:** {result.insights.language_detected}")
                st.write(f"**Processing Time:** {result.processing_time:.2f}s")
            
            with col2:
                st.subheader("📈 Document Metrics")
                st.write(f"**Readability Score:** {result.insights.readability_score:.1f}")
                st.write(f"**Sentiment:** {result.insights.sentiment.get('label', 'neutral')}")
                st.write(f"**Entities Found:** {len(result.insights.key_entities)}")
                st.write(f"**Topics Identified:** {len(result.insights.topics)}")
                st.write(f"**Form Fields:** {len(result.form_fields)}")
                st.write(f"**Tables:** {len(result.tables)}")
            
            # Tabs for detailed information
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏷️ Classification", "🔍 Insights", "📝 Forms", "📊 Tables", "⚠️ Compliance"
            ])
            
            with tab1:
                st.subheader("Document Classification")
                
                # Classification confidence
                st.write("**Top Categories:**")
                for i, category in enumerate(result.classification.categories[:5]):
                    st.write(f"{i+1}. {category['type']}: {category['score']:.2f}")
            
            with tab2:
                st.subheader("Document Insights")
                
                # Entities
                if result.insights.key_entities:
                    st.write("**Key Entities:**")
                    entities_df = pd.DataFrame(result.insights.key_entities)
                    st.dataframe(entities_df[['text', 'label', 'confidence']], use_container_width=True)
                
                # Topics
                if result.insights.topics:
                    st.write("**Topics:**")
                    topics_df = pd.DataFrame(result.insights.topics)
                    fig = px.bar(
                        topics_df,
                        x='topic',
                        y='score',
                        title="Topic Relevance Scores"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("Form Fields")
                
                if result.form_fields:
                    form_data = []
                    for field in result.form_fields:
                        form_data.append({
                            'Field Name': field.field_name,
                            'Value': field.field_value,
                            'Type': field.field_type,
                            'Confidence': f"{field.confidence:.2f}"
                        })
                    
                    form_df = pd.DataFrame(form_data)
                    st.dataframe(form_df, use_container_width=True)
                else:
                    st.info("No form fields detected in this document.")
            
            with tab4:
                st.subheader("Tables")
                
                if result.tables:
                    for i, table in enumerate(result.tables):
                        st.write(f"**Table {i+1}:**")
                        
                        # Create DataFrame from table data
                        if table.headers and table.rows:
                            table_df = pd.DataFrame(table.rows, columns=table.headers)
                            st.dataframe(table_df, use_container_width=True)
                        
                        st.write(f"Confidence: {table.confidence:.2f}")
                        st.write("---")
                else:
                    st.info("No tables detected in this document.")
            
            with tab5:
                st.subheader("Compliance Flags")
                
                if result.insights.compliance_flags:
                    for flag in result.insights.compliance_flags:
                        severity_color = {
                            'HIGH': '🔴',
                            'MEDIUM': '🟡',
                            'LOW': '🟢'
                        }.get(flag['severity'], '⚪')
                        
                        st.write(f"{severity_color} **{flag['type']}** - {flag['category']}")
                        st.write(f"   {flag['description']}")
                        
                        if 'count' in flag:
                            st.write(f"   Count: {flag['count']}")
                        
                        st.write("---")
                else:
                    st.success("✅ No compliance issues detected.")
    
    def render_search_interface(self):
        """Render document search interface"""
        if not st.session_state.search_index:
            return
        
        st.header("🔎 Document Search")
        
        # Search input
        search_query = st.text_input(
            "Search documents",
            placeholder="Enter search terms (e.g., 'invoice', 'john smith', 'contract')",
            help="Search across document content, entities, and metadata"
        )
        
        if search_query:
            # Perform search
            search_results = search_documents(st.session_state.search_index, search_query)
            
            if search_results:
                st.success(f"Found {len(search_results)} documents matching '{search_query}'")
                
                # Display results
                for filename in search_results:
                    # Find the corresponding result
                    result = next((r for r in st.session_state.analysis_results if r.filename == filename), None)
                    
                    if result:
                        with st.expander(f"📄 {filename}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Type:** {result.classification.document_type}")
                                st.write(f"**Confidence:** {result.classification.confidence:.2f}")
                            
                            with col2:
                                st.write(f"**Language:** {result.insights.language_detected}")
                                st.write(f"**Entities:** {len(result.insights.key_entities)}")
                            
                            # Show relevant entities
                            if result.insights.key_entities:
                                entities = [e['text'] for e in result.insights.key_entities[:5]]
                                st.write(f"**Key Entities:** {', '.join(entities)}")
            else:
                st.warning(f"No documents found matching '{search_query}'")
    
    def render_export_options(self):
        """Render export options"""
        if not st.session_state.analysis_results:
            return
        
        st.header("📤 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as JSON", type="secondary"):
                try:
                    json_data = self.analyzer.export_results(st.session_state.analysis_results, "json")
                    
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_data,
                        file_name=f"document_analysis_{int(time.time())}.json",
                        mime="application/json"
                    )
                    
                    st.success("✅ JSON export ready for download!")
                    
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        with col2:
            if st.button("📊 Export Summary", type="secondary"):
                try:
                    summary = self.analyzer.get_analysis_summary(st.session_state.analysis_results)
                    summary_json = json.dumps(summary, indent=2)
                    
                    st.download_button(
                        label="💾 Download Summary",
                        data=summary_json,
                        file_name=f"analysis_summary_{int(time.time())}.json",
                        mime="application/json"
                    )
                    
                    st.success("✅ Summary export ready for download!")
                    
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
    
    def render_analytics_dashboard(self):
        """Render analytics dashboard"""
        if not st.session_state.analysis_results:
            return
        
        st.header("📈 Analytics Dashboard")
        
        results = st.session_state.analysis_results
        
        # Compliance overview
        st.subheader("🛡️ Compliance Overview")
        
        total_flags = sum(len(r.insights.compliance_flags) for r in results)
        docs_with_flags = sum(1 for r in results if r.insights.compliance_flags)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Flags", total_flags)
        
        with col2:
            st.metric("Documents with Issues", docs_with_flags)
        
        with col3:
            compliance_rate = ((len(results) - docs_with_flags) / len(results)) * 100 if results else 0
            st.metric("Compliance Rate", f"{compliance_rate:.1f}%")
        
        # Language distribution
        if len(results) > 1:
            st.subheader("🌍 Language Distribution")
            
            languages = [r.insights.language_detected for r in results]
            lang_counts = pd.Series(languages).value_counts()
            
            fig = px.bar(
                x=lang_counts.index,
                y=lang_counts.values,
                title="Documents by Language",
                labels={'x': 'Language', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Readability analysis
        st.subheader("📖 Readability Analysis")
        
        readability_scores = [r.insights.readability_score for r in results]
        filenames = [r.filename for r in results]
        
        fig = px.scatter(
            x=filenames,
            y=readability_scores,
            title="Document Readability Scores",
            labels={'x': 'Document', 'y': 'Readability Score'},
            hover_data={'x': True, 'y': True}
        )
        fig.update_xaxis(tickangle=45)
        fig.add_hline(y=60, line_dash="dash", line_color="orange", 
                     annotation_text="Average Readability")
        st.plotly_chart(fig, use_container_width=True)
    
    def run(self):
        """Run the Streamlit application"""
        self.render_header()
        
        # Sidebar
        settings = self.render_sidebar()
        
        # Main content
        self.render_file_upload(settings)
        
        # Results sections
        if st.session_state.analysis_results:
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Overview", "🔍 Details", "🔎 Search", "📤 Export", "📈 Analytics"
            ])
            
            with tab1:
                self.render_results_overview()
            
            with tab2:
                self.render_document_details()
            
            with tab3:
                self.render_search_interface()
            
            with tab4:
                self.render_export_options()
            
            with tab5:
                self.render_analytics_dashboard()

def main():
    """Main function to run the Streamlit app"""
    app = AdvancedDocumentAnalyzerUI()
    app.run()

if __name__ == "__main__":
    main()