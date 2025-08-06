"""
Streamlit UI for Image and Document OCR Processing
Web interface for the OCR system with drag-and-drop, batch processing, and real-time preview
"""

import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
import json
import zipfile
from datetime import datetime
from pathlib import Path
import tempfile
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional

from image_ocr_processor import (
    OCRManager, OCRResult, DocumentResult, DocumentPage,
    validate_image_file, estimate_processing_time
)

class OCRStreamlitUI:
    """Streamlit interface for OCR processing"""
    
    def __init__(self):
        self.ocr_manager = OCRManager()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'ocr_results' not in st.session_state:
            st.session_state.ocr_results = []
        if 'processing_history' not in st.session_state:
            st.session_state.processing_history = []
        if 'current_language' not in st.session_state:
            st.session_state.current_language = 'en'
    
    def render_main_interface(self):
        """Render the main OCR interface"""
        st.header("📄 Image & Document OCR Processing")
        st.markdown("Extract text from images and documents with advanced OCR technology")
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🖼️ Single File OCR",
            "📚 Batch Processing", 
            "📊 Results Manager",
            "⚙️ Settings & Config",
            "📈 Analytics"
        ])
        
        with tab1:
            self.render_single_file_tab()
        
        with tab2:
            self.render_batch_processing_tab()
        
        with tab3:
            self.render_results_manager_tab()
        
        with tab4:
            self.render_settings_tab()
        
        with tab5:
            self.render_analytics_tab()
    
    def render_single_file_tab(self):
        """Render single file processing interface"""
        st.subheader("🖼️ Single File OCR Processing")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Upload File")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Choose an image or PDF file",
                type=['jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'pdf'],
                help="Supported formats: JPG, PNG, TIFF, BMP, PDF"
            )
            
            # Drag and drop area simulation
            if not uploaded_file:
                st.info("📁 Drag and drop a file above or click to browse")
        
        with col2:
            st.markdown("### Processing Options")
            
            # Language selection
            languages = self.ocr_manager.get_supported_languages()
            language_options = {lang['name']: lang['code'] for lang in languages}
            
            selected_language = st.selectbox(
                "Language",
                options=list(language_options.keys()),
                index=0,
                help="Select the primary language in your document"
            )
            
            language_code = language_options[selected_language]
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                extract_tables = st.checkbox("Extract table structures", value=True)
                enhance_contrast = st.checkbox("Enhance contrast", value=True)
                denoise_image = st.checkbox("Apply denoising", value=True)
                deskew_image = st.checkbox("Auto-correct skew", value=True)
        
        # Process file if uploaded
        if uploaded_file is not None:
            self.process_single_file(
                uploaded_file, language_code, extract_tables,
                enhance_contrast, denoise_image, deskew_image
            )
    
    def process_single_file(self, uploaded_file, language_code: str, 
                           extract_tables: bool, enhance_contrast: bool,
                           denoise_image: bool, deskew_image: bool):
        """Process a single uploaded file"""
        
        # Display file info
        st.markdown("### 📋 File Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            estimated_time = estimate_processing_time(uploaded_file.name)
            st.metric("Est. Processing Time", f"{estimated_time:.1f}s")
        
        # Preview image if it's an image file
        if uploaded_file.type.startswith('image/'):
            st.markdown("### 🖼️ Image Preview")
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", use_column_width=True)
        
        # Process button
        if st.button("🚀 Process File", type="primary", use_container_width=True):
            with st.spinner("Processing file... This may take a few moments."):
                try:
                    # Save uploaded file temporarily
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False, 
                        suffix=Path(uploaded_file.name).suffix
                    )
                    temp_file.write(uploaded_file.getvalue())
                    temp_file.close()
                    
                    # Process the file
                    result = self.ocr_manager.process_file(
                        temp_file.name, 
                        language_code, 
                        extract_tables
                    )
                    
                    # Store result
                    st.session_state.ocr_results.append({
                        'timestamp': datetime.now(),
                        'filename': uploaded_file.name,
                        'result': result,
                        'settings': {
                            'language': language_code,
                            'extract_tables': extract_tables,
                            'enhance_contrast': enhance_contrast,
                            'denoise': denoise_image,
                            'deskew': deskew_image
                        }
                    })
                    
                    # Display results
                    self.display_ocr_result(result, uploaded_file.name)
                    
                    # Clean up temp file
                    Path(temp_file.name).unlink()
                    
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
    
    def display_ocr_result(self, result, filename: str):
        """Display OCR processing results"""
        st.markdown("### ✅ Processing Results")
        
        if isinstance(result, OCRResult):
            # Single image result
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Confidence", f"{result.confidence:.1%}")
            with col2:
                st.metric("Word Count", result.word_count)
            with col3:
                st.metric("Processing Time", f"{result.processing_time:.2f}s")
            with col4:
                st.metric("Language", result.language.upper())
            
            # Extracted text
            st.markdown("### 📝 Extracted Text")
            st.text_area("Text Content", result.text, height=300)
            
            # Bounding boxes visualization
            if result.bounding_boxes:
                st.markdown("### 🎯 Text Detection Confidence")
                
                # Create confidence chart
                confidences = [box['confidence'] for box in result.bounding_boxes]
                fig = px.histogram(
                    x=confidences,
                    title="Text Detection Confidence Distribution",
                    labels={'x': 'Confidence Score', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Download options
            self.create_download_options(result, filename)
            
        elif isinstance(result, DocumentResult):
            # PDF document result
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Pages", result.total_pages)
            with col2:
                st.metric("Processing Time", f"{result.processing_time:.2f}s")
            with col3:
                st.metric("Total Characters", len(result.combined_text))
            
            # Page-by-page results
            st.markdown("### 📄 Page-by-Page Results")
            
            for page in result.pages:
                with st.expander(f"Page {page.page_number} (Confidence: {page.confidence:.1%})"):
                    st.text_area(
                        f"Page {page.page_number} Text",
                        page.text,
                        height=200,
                        key=f"page_{page.page_number}"
                    )
                    
                    if page.tables:
                        st.markdown(f"**Tables detected:** {len(page.tables)}")
            
            # Combined text
            st.markdown("### 📋 Complete Document Text")
            st.text_area("Full Document", result.combined_text, height=400)
            
            # Download options
            self.create_download_options(result, filename)
    
    def create_download_options(self, result, filename: str):
        """Create download options for results"""
        st.markdown("### 💾 Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Plain text download
            text_content = result.text if isinstance(result, OCRResult) else result.combined_text
            st.download_button(
                label="📄 Download Text",
                data=text_content,
                file_name=f"{Path(filename).stem}_extracted.txt",
                mime="text/plain"
            )
        
        with col2:
            # JSON download with metadata
            json_data = json.dumps(
                result.__dict__ if hasattr(result, '__dict__') else str(result),
                default=str,
                indent=2
            )
            st.download_button(
                label="📊 Download JSON",
                data=json_data,
                file_name=f"{Path(filename).stem}_data.json",
                mime="application/json"
            )
        
        with col3:
            # CSV download for structured data
            if isinstance(result, OCRResult) and result.bounding_boxes:
                df = pd.DataFrame(result.bounding_boxes)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📈 Download CSV",
                    data=csv_data,
                    file_name=f"{Path(filename).stem}_boxes.csv",
                    mime="text/csv"
                )
    
    def render_batch_processing_tab(self):
        """Render batch processing interface"""
        st.subheader("📚 Batch Processing")
        st.markdown("Process multiple files simultaneously")
        
        # File uploader for multiple files
        uploaded_files = st.file_uploader(
            "Choose multiple files",
            type=['jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'pdf'],
            accept_multiple_files=True,
            help="Upload multiple images or PDF files for batch processing"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            # Batch processing options
            col1, col2 = st.columns(2)
            
            with col1:
                # Language selection
                languages = self.ocr_manager.get_supported_languages()
                language_options = {lang['name']: lang['code'] for lang in languages}
                
                batch_language = st.selectbox(
                    "Batch Language",
                    options=list(language_options.keys()),
                    key="batch_language"
                )
                
                batch_language_code = language_options[batch_language]
            
            with col2:
                # Output options
                create_zip = st.checkbox("Create ZIP archive", value=True)
                include_metadata = st.checkbox("Include metadata", value=True)
            
            # Process batch
            if st.button("🚀 Process Batch", type="primary"):
                self.process_batch_files(
                    uploaded_files, batch_language_code, 
                    create_zip, include_metadata
                )
        else:
            st.info("📁 Upload multiple files to begin batch processing")
    
    def process_batch_files(self, uploaded_files, language_code: str,
                           create_zip: bool, include_metadata: bool):
        """Process multiple files in batch"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Save file temporarily
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=Path(uploaded_file.name).suffix
                )
                temp_file.write(uploaded_file.getvalue())
                temp_file.close()
                
                # Process file
                result = self.ocr_manager.process_file(temp_file.name, language_code)
                
                results.append({
                    'filename': uploaded_file.name,
                    'result': result,
                    'success': True
                })
                
                # Clean up
                Path(temp_file.name).unlink()
                
            except Exception as e:
                results.append({
                    'filename': uploaded_file.name,
                    'error': str(e),
                    'success': False
                })
        
        status_text.text("✅ Batch processing complete!")
        
        # Display results summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(results))
        with col2:
            st.metric("Successful", successful)
        with col3:
            st.metric("Failed", failed)
        
        # Show detailed results
        for result in results:
            if result['success']:
                with st.expander(f"✅ {result['filename']}"):
                    ocr_result = result['result']
                    text_content = ocr_result.text if isinstance(ocr_result, OCRResult) else ocr_result.combined_text
                    st.text_area("Extracted Text", text_content, height=150)
            else:
                with st.expander(f"❌ {result['filename']}"):
                    st.error(f"Error: {result['error']}")
        
        # Create batch download
        if create_zip and successful > 0:
            self.create_batch_download(results, include_metadata)
    
    def create_batch_download(self, results: List[Dict], include_metadata: bool):
        """Create ZIP download for batch results"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result in results:
                if result['success']:
                    filename = result['filename']
                    ocr_result = result['result']
                    
                    # Add text file
                    text_content = ocr_result.text if isinstance(ocr_result, OCRResult) else ocr_result.combined_text
                    text_filename = f"{Path(filename).stem}_extracted.txt"
                    zip_file.writestr(text_filename, text_content)
                    
                    # Add metadata if requested
                    if include_metadata:
                        metadata = json.dumps(
                            ocr_result.__dict__ if hasattr(ocr_result, '__dict__') else str(ocr_result),
                            default=str,
                            indent=2
                        )
                        metadata_filename = f"{Path(filename).stem}_metadata.json"
                        zip_file.writestr(metadata_filename, metadata)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 Download Batch Results",
            data=zip_buffer.getvalue(),
            file_name=f"batch_ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )
    
    def render_results_manager_tab(self):
        """Render results management interface"""
        st.subheader("📊 Results Manager")
        
        if not st.session_state.ocr_results:
            st.info("No OCR results yet. Process some files to see results here.")
            return
        
        st.markdown(f"**Total Results:** {len(st.session_state.ocr_results)}")
        
        # Filter and sort options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sort_by = st.selectbox("Sort by", ["Newest", "Oldest", "Filename", "Confidence"])
        
        with col2:
            filter_language = st.selectbox(
                "Filter by Language",
                ["All"] + list(set(r['settings']['language'] for r in st.session_state.ocr_results))
            )
        
        with col3:
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.0)
        
        # Filter results
        filtered_results = st.session_state.ocr_results.copy()
        
        if filter_language != "All":
            filtered_results = [r for r in filtered_results if r['settings']['language'] == filter_language]
        
        # Sort results
        if sort_by == "Newest":
            filtered_results.sort(key=lambda x: x['timestamp'], reverse=True)
        elif sort_by == "Oldest":
            filtered_results.sort(key=lambda x: x['timestamp'])
        elif sort_by == "Filename":
            filtered_results.sort(key=lambda x: x['filename'])
        elif sort_by == "Confidence":
            filtered_results.sort(key=lambda x: getattr(x['result'], 'confidence', 0), reverse=True)
        
        # Display results
        for i, result_data in enumerate(filtered_results):
            result = result_data['result']
            confidence = getattr(result, 'confidence', 1.0)
            
            if confidence >= min_confidence:
                with st.expander(f"📄 {result_data['filename']} - {result_data['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        text_content = result.text if isinstance(result, OCRResult) else result.combined_text
                        st.text_area("Extracted Text", text_content, height=200, key=f"result_{i}")
                    
                    with col2:
                        st.metric("Confidence", f"{confidence:.1%}")
                        st.metric("Language", result_data['settings']['language'].upper())
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                            st.session_state.ocr_results.remove(result_data)
                            st.rerun()
        
        # Bulk actions
        st.markdown("### Bulk Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📦 Export All Results"):
                self.export_all_results()
        
        with col2:
            if st.button("🗑️ Clear All Results"):
                st.session_state.ocr_results = []
                st.success("All results cleared")
                st.rerun()
    
    def export_all_results(self):
        """Export all results to a comprehensive report"""
        if not st.session_state.ocr_results:
            st.warning("No results to export")
            return
        
        # Create comprehensive report
        report_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_results': len(st.session_state.ocr_results),
            'results': []
        }
        
        for result_data in st.session_state.ocr_results:
            result = result_data['result']
            report_data['results'].append({
                'filename': result_data['filename'],
                'timestamp': result_data['timestamp'].isoformat(),
                'settings': result_data['settings'],
                'text': result.text if isinstance(result, OCRResult) else result.combined_text,
                'confidence': getattr(result, 'confidence', 1.0),
                'word_count': getattr(result, 'word_count', 0),
                'processing_time': getattr(result, 'processing_time', 0)
            })
        
        report_json = json.dumps(report_data, indent=2)
        
        st.download_button(
            label="📊 Download Complete Report",
            data=report_json,
            file_name=f"ocr_complete_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def render_settings_tab(self):
        """Render settings and configuration interface"""
        st.subheader("⚙️ Settings & Configuration")
        
        # System status
        st.markdown("### 🔧 System Status")
        stats = self.ocr_manager.get_processing_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Tesseract Available", "✅ Yes" if stats['tesseract_available'] else "❌ No")
            st.metric("EasyOCR Available", "✅ Yes" if stats['easyocr_available'] else "❌ No")
        
        with col2:
            st.metric("Supported Formats", len(stats['supported_formats']))
            st.metric("Supported Languages", stats['supported_languages'])
        
        # Supported formats
        st.markdown("### 📁 Supported File Formats")
        formats_df = pd.DataFrame({
            'Format': stats['supported_formats'],
            'Type': ['Image' if fmt != '.pdf' else 'Document' for fmt in stats['supported_formats']]
        })
        st.dataframe(formats_df, use_container_width=True)
        
        # Language support
        st.markdown("### 🌍 Language Support")
        languages = self.ocr_manager.get_supported_languages()
        lang_df = pd.DataFrame(languages)
        st.dataframe(lang_df, use_container_width=True)
        
        # Cleanup options
        st.markdown("### 🧹 Maintenance")
        if st.button("🗑️ Clean Temporary Files"):
            self.ocr_manager.cleanup_temp_files()
            st.success("Temporary files cleaned up")
    
    def render_analytics_tab(self):
        """Render analytics and statistics interface"""
        st.subheader("📈 Analytics & Statistics")
        
        if not st.session_state.ocr_results:
            st.info("No data available. Process some files to see analytics.")
            return
        
        # Overall statistics
        st.markdown("### 📊 Overall Statistics")
        
        total_files = len(st.session_state.ocr_results)
        total_words = sum(getattr(r['result'], 'word_count', 0) for r in st.session_state.ocr_results)
        avg_confidence = sum(getattr(r['result'], 'confidence', 0) for r in st.session_state.ocr_results) / total_files
        total_processing_time = sum(getattr(r['result'], 'processing_time', 0) for r in st.session_state.ocr_results)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Files Processed", total_files)
        with col2:
            st.metric("Total Words Extracted", f"{total_words:,}")
        with col3:
            st.metric("Average Confidence", f"{avg_confidence:.1%}")
        with col4:
            st.metric("Total Processing Time", f"{total_processing_time:.1f}s")
        
        # Confidence distribution
        st.markdown("### 📈 Confidence Distribution")
        confidences = [getattr(r['result'], 'confidence', 0) for r in st.session_state.ocr_results]
        
        fig = px.histogram(
            x=confidences,
            title="OCR Confidence Score Distribution",
            labels={'x': 'Confidence Score', 'y': 'Number of Files'},
            nbins=20
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Language usage
        st.markdown("### 🌍 Language Usage")
        languages = [r['settings']['language'] for r in st.session_state.ocr_results]
        lang_counts = pd.Series(languages).value_counts()
        
        fig = px.pie(
            values=lang_counts.values,
            names=lang_counts.index,
            title="Languages Processed"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Processing time analysis
        st.markdown("### ⏱️ Processing Performance")
        processing_times = [getattr(r['result'], 'processing_time', 0) for r in st.session_state.ocr_results]
        filenames = [r['filename'] for r in st.session_state.ocr_results]
        
        fig = px.bar(
            x=filenames,
            y=processing_times,
            title="Processing Time by File",
            labels={'x': 'File', 'y': 'Processing Time (seconds)'}
        )
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main function to run the OCR UI"""
    st.set_page_config(
        page_title="OCR Processing System",
        page_icon="📄",
        layout="wide"
    )
    
    ui = OCRStreamlitUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()