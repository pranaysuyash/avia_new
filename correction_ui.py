"""
Transcription Correction UI - Streamlit Interface for Manual Corrections
Provides an intuitive interface for reviewing and correcting transcriptions
"""

import streamlit as st
import pandas as pd
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from difflib import SequenceMatcher
import re
from pathlib import Path

# Import the correction engine
from transcription_correction_engine import (
    TranscriptionCorrectionSystem,
    CorrectionType,
    CorrectionResult,
    UserCorrection
)


class CorrectionUI:
    """Streamlit UI for transcription correction"""
    
    def __init__(self):
        """Initialize the correction UI"""
        self.correction_system = TranscriptionCorrectionSystem()
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'current_text' not in st.session_state:
            st.session_state.current_text = ""
        if 'original_text' not in st.session_state:
            st.session_state.original_text = ""
        if 'corrections' not in st.session_state:
            st.session_state.corrections = []
        if 'correction_history' not in st.session_state:
            st.session_state.correction_history = []
        if 'active_correction_types' not in st.session_state:
            st.session_state.active_correction_types = [
                CorrectionType.SPELLING,
                CorrectionType.GRAMMAR,
                CorrectionType.PUNCTUATION
            ]
        if 'confidence_threshold' not in st.session_state:
            st.session_state.confidence_threshold = 0.5
        if 'custom_dictionary' not in st.session_state:
            st.session_state.custom_dictionary = []
        if 'show_diff' not in st.session_state:
            st.session_state.show_diff = True
        if 'auto_correct' not in st.session_state:
            st.session_state.auto_correct = False
            
    def render_header(self):
        """Render the application header"""
        st.title("🎯 Transcription Correction System")
        st.markdown("""
        Advanced AI-powered correction system for transcription accuracy improvement.
        Features automatic error detection, manual editing, and learning from user feedback.
        """)
        
    def render_sidebar(self):
        """Render the sidebar with settings and controls"""
        with st.sidebar:
            st.header("⚙️ Correction Settings")
            
            # Correction types selection
            st.subheader("Correction Types")
            correction_types = []
            
            if st.checkbox("Spelling Correction", value=True):
                correction_types.append(CorrectionType.SPELLING)
            if st.checkbox("Grammar Correction", value=True):
                correction_types.append(CorrectionType.GRAMMAR)
            if st.checkbox("Punctuation Correction", value=True):
                correction_types.append(CorrectionType.PUNCTUATION)
            if st.checkbox("Contextual Correction", value=False):
                correction_types.append(CorrectionType.CONTEXTUAL)
            if st.checkbox("Technical Terms", value=False):
                correction_types.append(CorrectionType.TECHNICAL_TERMS)
            if st.checkbox("Homophone Detection", value=False):
                correction_types.append(CorrectionType.HOMOPHONES)
                
            st.session_state.active_correction_types = correction_types
            
            # Confidence threshold
            st.subheader("Confidence Settings")
            st.session_state.confidence_threshold = st.slider(
                "Minimum Confidence",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.confidence_threshold,
                step=0.05,
                help="Only show corrections above this confidence level"
            )
            
            # Display options
            st.subheader("Display Options")
            st.session_state.show_diff = st.checkbox(
                "Show Visual Diff",
                value=st.session_state.show_diff
            )
            st.session_state.auto_correct = st.checkbox(
                "Auto-Apply High Confidence",
                value=st.session_state.auto_correct,
                help="Automatically apply corrections with confidence > 0.9"
            )
            
            # Custom dictionary management
            st.subheader("Custom Dictionary")
            new_term = st.text_input("Add Technical Term")
            if st.button("Add to Dictionary"):
                if new_term and new_term not in st.session_state.custom_dictionary:
                    st.session_state.custom_dictionary.append(new_term)
                    asyncio.run(
                        self.correction_system.add_custom_terms([new_term])
                    )
                    st.success(f"Added '{new_term}' to dictionary")
                    
            if st.session_state.custom_dictionary:
                st.write("Current Terms:")
                for term in st.session_state.custom_dictionary[:10]:
                    st.write(f"• {term}")
                if len(st.session_state.custom_dictionary) > 10:
                    st.write(f"... and {len(st.session_state.custom_dictionary) - 10} more")
                    
    def render_input_section(self):
        """Render the text input section"""
        st.header("📝 Input Transcription")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Text input methods
            input_method = st.radio(
                "Input Method",
                ["Paste Text", "Upload File", "Sample Text"],
                horizontal=True
            )
            
        with col2:
            context = st.text_input(
                "Context (optional)",
                placeholder="e.g., Medical, Legal, Technical",
                help="Provide context for better corrections"
            )
            
        if input_method == "Paste Text":
            text_input = st.text_area(
                "Paste your transcription here",
                height=200,
                placeholder="Enter or paste the transcription text you want to correct..."
            )
            
        elif input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Choose a text file",
                type=['txt', 'srt', 'vtt', 'json']
            )
            text_input = ""
            if uploaded_file is not None:
                text_input = uploaded_file.read().decode('utf-8')
                st.text_area("Uploaded Text Preview", text_input[:1000], height=100)
                
        else:  # Sample Text
            sample_texts = {
                "Medical": "The patient presented with seveer headache and nausea she was prescribed acetaminophen 500mg twice dayly the symptoms beggan three days ago",
                "Technical": "The API endpoint returns a jason response with the users data the authentification token expires after 24 hour you need to refesh it regulary",
                "General": "I think their going to there house tommorow we should of left earlier but we didnt no the traffic would be so bad"
            }
            selected_sample = st.selectbox("Choose sample", list(sample_texts.keys()))
            text_input = sample_texts[selected_sample]
            st.text_area("Sample Text", text_input, height=100)
            
        if st.button("🔍 Analyze and Correct", type="primary"):
            if text_input:
                st.session_state.original_text = text_input
                st.session_state.current_text = text_input
                asyncio.run(self.process_corrections(text_input, context))
            else:
                st.warning("Please provide text to correct")
                
    async def process_corrections(self, text: str, context: Optional[str] = None):
        """Process corrections for the input text"""
        with st.spinner("Analyzing text and detecting errors..."):
            result = await self.correction_system.correct_transcription(
                text=text,
                correction_types=st.session_state.active_correction_types,
                context=context,
                confidence_threshold=st.session_state.confidence_threshold
            )
            
            st.session_state.corrections = result['corrections']
            
            # Auto-apply high confidence corrections if enabled
            if st.session_state.auto_correct:
                auto_applied = []
                current_text = text
                for correction in result['corrections']:
                    if correction.confidence > 0.9:
                        current_text = current_text.replace(
                            correction.original,
                            correction.corrected
                        )
                        auto_applied.append(correction)
                        
                st.session_state.current_text = current_text
                if auto_applied:
                    st.info(f"Auto-applied {len(auto_applied)} high-confidence corrections")
                    
    def render_corrections_section(self):
        """Render the corrections section"""
        if not st.session_state.corrections:
            return
            
        st.header("✏️ Detected Corrections")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Errors", len(st.session_state.corrections))
        with col2:
            avg_confidence = sum(c.confidence for c in st.session_state.corrections) / len(st.session_state.corrections)
            st.metric("Avg Confidence", f"{avg_confidence:.2%}")
        with col3:
            high_conf = sum(1 for c in st.session_state.corrections if c.confidence > 0.8)
            st.metric("High Confidence", high_conf)
        with col4:
            types = set(c.correction_type for c in st.session_state.corrections)
            st.metric("Error Types", len(types))
            
        # Corrections table
        st.subheader("Correction Details")
        
        # Create interactive correction interface
        corrections_data = []
        for i, correction in enumerate(st.session_state.corrections):
            corrections_data.append({
                "Index": i,
                "Type": correction.correction_type.value,
                "Original": correction.original,
                "Suggested": correction.corrected,
                "Confidence": f"{correction.confidence:.2%}",
                "Reason": correction.reason
            })
            
        df = pd.DataFrame(corrections_data)
        
        # Allow filtering by type
        filter_type = st.selectbox(
            "Filter by Type",
            ["All"] + [t.value for t in CorrectionType]
        )
        
        if filter_type != "All":
            df = df[df["Type"] == filter_type]
            
        # Display corrections with accept/reject options
        for idx, row in df.iterrows():
            with st.expander(f"{row['Type']}: '{row['Original']}' → '{row['Suggested']}'"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Original:** {row['Original']}")
                    st.write(f"**Suggested:** {row['Suggested']}")
                    
                with col2:
                    st.write(f"**Confidence:** {row['Confidence']}")
                    st.write(f"**Reason:** {row['Reason']}")
                    
                with col3:
                    if st.button(f"✓ Accept", key=f"accept_{idx}"):
                        self.apply_correction(row['Index'])
                    if st.button(f"✗ Reject", key=f"reject_{idx}"):
                        self.reject_correction(row['Index'])
                    if st.button(f"✏️ Edit", key=f"edit_{idx}"):
                        self.edit_correction(row['Index'])
                        
    def apply_correction(self, index: int):
        """Apply a specific correction"""
        correction = st.session_state.corrections[index]
        st.session_state.current_text = st.session_state.current_text.replace(
            correction.original,
            correction.corrected,
            1
        )
        
        # Learn from acceptance
        asyncio.run(
            self.correction_system.learn_from_correction(
                UserCorrection(
                    original_text=correction.original,
                    corrected_text=correction.corrected,
                    correction_type=correction.correction_type,
                    context=correction.context,
                    accepted=True
                )
            )
        )
        
        st.success(f"Applied correction: '{correction.original}' → '{correction.corrected}'")
        st.rerun()
        
    def reject_correction(self, index: int):
        """Reject a specific correction"""
        correction = st.session_state.corrections[index]
        
        # Learn from rejection
        asyncio.run(
            self.correction_system.learn_from_correction(
                UserCorrection(
                    original_text=correction.original,
                    corrected_text=correction.corrected,
                    correction_type=correction.correction_type,
                    context=correction.context,
                    accepted=False
                )
            )
        )
        
        # Remove from corrections list
        st.session_state.corrections.pop(index)
        st.info(f"Rejected correction for '{correction.original}'")
        st.rerun()
        
    def edit_correction(self, index: int):
        """Allow manual editing of a correction"""
        correction = st.session_state.corrections[index]
        
        new_text = st.text_input(
            f"Edit correction for '{correction.original}'",
            value=correction.corrected,
            key=f"edit_input_{index}"
        )
        
        if st.button(f"Save Edit", key=f"save_edit_{index}"):
            st.session_state.current_text = st.session_state.current_text.replace(
                correction.original,
                new_text,
                1
            )
            
            # Learn from custom correction
            asyncio.run(
                self.correction_system.learn_from_correction(
                    UserCorrection(
                        original_text=correction.original,
                        corrected_text=new_text,
                        correction_type=correction.correction_type,
                        context=correction.context,
                        accepted=True
                    )
                )
            )
            
            st.success(f"Applied custom correction: '{correction.original}' → '{new_text}'")
            st.rerun()
            
    def render_output_section(self):
        """Render the corrected output section"""
        if not st.session_state.current_text:
            return
            
        st.header("📄 Corrected Output")
        
        # Display options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            output_format = st.selectbox(
                "Output Format",
                ["Plain Text", "Highlighted Changes", "Side-by-Side"]
            )
            
        with col2:
            if st.button("📋 Copy to Clipboard"):
                st.write(st.session_state.current_text)
                st.success("Text copied to clipboard!")
                
        with col3:
            if st.button("💾 Download Corrected"):
                self.download_corrected_text()
                
        # Display corrected text based on format
        if output_format == "Plain Text":
            st.text_area(
                "Corrected Text",
                st.session_state.current_text,
                height=300
            )
            
        elif output_format == "Highlighted Changes":
            self.render_highlighted_changes()
            
        else:  # Side-by-Side
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original")
                st.text_area(
                    "Original Text",
                    st.session_state.original_text,
                    height=300
                )
            with col2:
                st.subheader("Corrected")
                st.text_area(
                    "Corrected Text",
                    st.session_state.current_text,
                    height=300
                )
                
    def render_highlighted_changes(self):
        """Render text with highlighted changes"""
        if st.session_state.show_diff:
            # Create diff visualization
            matcher = SequenceMatcher(
                None,
                st.session_state.original_text,
                st.session_state.current_text
            )
            
            html_output = "<div style='line-height: 1.8;'>"
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    html_output += st.session_state.original_text[i1:i2]
                elif tag == 'delete':
                    html_output += f"<span style='background-color: #ffcccc; text-decoration: line-through;'>{st.session_state.original_text[i1:i2]}</span>"
                elif tag == 'insert':
                    html_output += f"<span style='background-color: #ccffcc; font-weight: bold;'>{st.session_state.current_text[j1:j2]}</span>"
                elif tag == 'replace':
                    html_output += f"<span style='background-color: #ffcccc; text-decoration: line-through;'>{st.session_state.original_text[i1:i2]}</span>"
                    html_output += f"<span style='background-color: #ccffcc; font-weight: bold;'>{st.session_state.current_text[j1:j2]}</span>"
                    
            html_output += "</div>"
            
            st.markdown(html_output, unsafe_allow_html=True)
            
            # Legend
            st.markdown("""
            <div style='margin-top: 20px;'>
                <span style='background-color: #ffcccc; padding: 2px 5px;'>Removed</span>
                <span style='background-color: #ccffcc; padding: 2px 5px;'>Added</span>
            </div>
            """, unsafe_allow_html=True)
            
    def render_analytics_section(self):
        """Render analytics and statistics"""
        if not st.session_state.corrections:
            return
            
        st.header("📊 Correction Analytics")
        
        # Error type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of error types
            error_types = {}
            for correction in st.session_state.corrections:
                error_type = correction.correction_type.value
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
            fig = px.pie(
                values=list(error_types.values()),
                names=list(error_types.keys()),
                title="Error Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Confidence distribution
            confidences = [c.confidence for c in st.session_state.corrections]
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=confidences,
                    nbinsx=20,
                    name="Confidence Distribution"
                )
            ])
            fig.update_layout(
                title="Correction Confidence Distribution",
                xaxis_title="Confidence",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Correction timeline (if we have timestamps)
        if st.session_state.correction_history:
            st.subheader("Correction History")
            
            history_df = pd.DataFrame(st.session_state.correction_history)
            
            fig = px.line(
                history_df,
                x='timestamp',
                y='corrections_count',
                title="Corrections Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Learning metrics
        st.subheader("Learning System Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patterns = asyncio.run(
                self.correction_system.learning_system.get_correction_patterns(limit=100)
            )
            st.metric("Learned Patterns", len(patterns))
            
        with col2:
            if patterns:
                avg_frequency = sum(p['frequency'] for p in patterns) / len(patterns)
                st.metric("Avg Pattern Frequency", f"{avg_frequency:.1f}")
            else:
                st.metric("Avg Pattern Frequency", "0")
                
        with col3:
            if patterns:
                high_freq = sum(1 for p in patterns if p['frequency'] > 5)
                st.metric("High Frequency Patterns", high_freq)
            else:
                st.metric("High Frequency Patterns", "0")
                
    def render_batch_processing(self):
        """Render batch processing section"""
        st.header("📦 Batch Processing")
        
        st.markdown("""
        Process multiple transcription files at once for efficient correction.
        """)
        
        uploaded_files = st.file_uploader(
            "Upload multiple files",
            type=['txt', 'srt', 'vtt'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} files for processing")
            
            # Batch processing options
            col1, col2 = st.columns(2)
            
            with col1:
                batch_context = st.text_input(
                    "Batch Context",
                    placeholder="e.g., Medical transcriptions"
                )
                
            with col2:
                export_format = st.selectbox(
                    "Export Format",
                    ["Text Files", "JSON", "CSV Report"]
                )
                
            if st.button("🚀 Process Batch", type="primary"):
                self.process_batch(uploaded_files, batch_context, export_format)
                
    def process_batch(
        self,
        files: List,
        context: Optional[str],
        export_format: str
    ):
        """Process multiple files in batch"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, file in enumerate(files):
            status_text.text(f"Processing {file.name}...")
            
            text = file.read().decode('utf-8')
            
            result = asyncio.run(
                self.correction_system.correct_transcription(
                    text=text,
                    correction_types=st.session_state.active_correction_types,
                    context=context,
                    confidence_threshold=st.session_state.confidence_threshold
                )
            )
            
            results.append({
                'filename': file.name,
                'original_text': text,
                'corrected_text': result['corrected_text'],
                'corrections': result['corrections'],
                'metrics': result['metrics']
            })
            
            progress_bar.progress((i + 1) / len(files))
            
        status_text.text("Batch processing complete!")
        
        # Export results
        self.export_batch_results(results, export_format)
        
    def export_batch_results(self, results: List[Dict], format: str):
        """Export batch processing results"""
        if format == "Text Files":
            # Create a zip file with corrected texts
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for result in results:
                    zip_file.writestr(
                        f"corrected_{result['filename']}",
                        result['corrected_text']
                    )
                    
            st.download_button(
                label="📥 Download Corrected Files",
                data=zip_buffer.getvalue(),
                file_name="corrected_transcriptions.zip",
                mime="application/zip"
            )
            
        elif format == "JSON":
            # Export as JSON with all details
            json_data = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON Report",
                data=json_data,
                file_name="correction_report.json",
                mime="application/json"
            )
            
        else:  # CSV Report
            # Create summary CSV
            csv_data = []
            for result in results:
                csv_data.append({
                    'Filename': result['filename'],
                    'Total Corrections': len(result['corrections']),
                    'Characters Changed': result['metrics'].get('characters_changed', 0),
                    'Processing Time': result['metrics'].get('processing_time', 0)
                })
                
            df = pd.DataFrame(csv_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV Report",
                data=csv,
                file_name="correction_summary.csv",
                mime="text/csv"
            )
            
    def download_corrected_text(self):
        """Download the corrected text"""
        st.download_button(
            label="Download Corrected Text",
            data=st.session_state.current_text,
            file_name="corrected_transcription.txt",
            mime="text/plain"
        )
        
    def render_keyboard_shortcuts(self):
        """Display keyboard shortcuts"""
        with st.expander("⌨️ Keyboard Shortcuts"):
            st.markdown("""
            - **Ctrl+Enter**: Process corrections
            - **Ctrl+A**: Accept all corrections
            - **Ctrl+R**: Reject all corrections
            - **Ctrl+S**: Save corrected text
            - **Ctrl+Z**: Undo last change
            - **Ctrl+D**: Toggle diff view
            """)
            
    def run(self):
        """Main application entry point"""
        self.render_header()
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "✏️ Correction",
            "📊 Analytics",
            "📦 Batch Processing",
            "📚 Help"
        ])
        
        with tab1:
            self.render_input_section()
            self.render_corrections_section()
            self.render_output_section()
            
        with tab2:
            self.render_analytics_section()
            
        with tab3:
            self.render_batch_processing()
            
        with tab4:
            st.header("📚 Help & Documentation")
            
            st.markdown("""
            ### How to Use
            
            1. **Input Text**: Paste, upload, or select sample text
            2. **Configure Settings**: Choose correction types and confidence threshold
            3. **Process**: Click "Analyze and Correct" to detect errors
            4. **Review**: Accept, reject, or edit individual corrections
            5. **Export**: Download or copy the corrected text
            
            ### Correction Types
            
            - **Spelling**: Detects and corrects misspelled words
            - **Grammar**: Fixes grammatical errors
            - **Punctuation**: Adds or corrects punctuation
            - **Contextual**: Context-aware corrections
            - **Technical Terms**: Domain-specific terminology
            - **Homophones**: Words that sound alike but have different meanings
            
            ### Tips
            
            - Provide context for better accuracy
            - Add technical terms to custom dictionary
            - The system learns from your corrections
            - Use batch processing for multiple files
            """)
            
            self.render_keyboard_shortcuts()


def main():
    """Main function to run the Streamlit app"""
    st.set_page_config(
        page_title="Transcription Correction System",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
    }
    .correction-accept {
        background-color: #4CAF50;
        color: white;
    }
    .correction-reject {
        background-color: #f44336;
        color: white;
    }
    .correction-edit {
        background-color: #2196F3;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    app = CorrectionUI()
    app.run()


if __name__ == "__main__":
    main()