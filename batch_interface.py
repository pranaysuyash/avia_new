#!/usr/bin/env python3
"""
Batch Processing Interface for Audio/Video Transcription App
Streamlit interface components for batch processing functionality
"""

import streamlit as st
import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from batch_processor import batch_processor, BatchJobStatus
from batch_export import batch_exporter
from openai_batch_processor import openai_batch_processor
import utils
from session_manager import session_manager

logger = logging.getLogger(__name__)

def render_batch_interface(analysis_mode: str):
    """Render the main batch processing interface"""
    
    st.header("📦 Batch Processing")
    st.markdown("Process multiple audio/video files simultaneously with progress tracking and batch export.")
    # Inline share and sidebar share/reset
    try:
        from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event
        render_share_inline("Shareable view link")
        with st.sidebar:
            render_share_block("Share Batch View")
            if st.button("Reset View/Filters"):
                try:
                    st.experimental_set_query_params()
                except Exception:
                    pass
                try:
                    log_ux_event("st_filters_cleared", {"scope": "batch_processing"})
                except Exception:
                    pass
                st.rerun()
    except Exception:
        pass
    
    # Initialize batch processor if not running
    if not batch_processor.is_running:
        batch_processor.start_processing()
    
    # Create tabs for different batch operations
    tab1, tab2, tab3 = st.tabs(["📁 Upload & Process", "📊 Job Status", "📥 Export Results"])
    
    with tab1:
        render_batch_upload_interface(analysis_mode)
    
    with tab2:
        render_job_status_interface()
    
    with tab3:
        render_export_interface()

def render_batch_upload_interface(analysis_mode: str):
    """Render the batch file upload interface"""
    
    st.subheader("Upload Multiple Files")
    
    # File upload section
    uploaded_files = st.file_uploader(
        "Select multiple audio/video files",
        type=["mp3", "wav", "mp4", "m4a"],
        accept_multiple_files=True,
        help=f"Upload multiple files for batch processing. Max size per file: {utils.get_file_size_limit()}MB"
    )
    
    if uploaded_files:
        # Display file information
        st.markdown("### 📋 Selected Files")
        
        total_size = 0
        valid_files = []
        
        # Create file info table
        file_data = []
        for i, file in enumerate(uploaded_files):
            file_size_mb = file.size / (1024 * 1024)
            total_size += file_size_mb
            
            is_valid = file_size_mb <= utils.get_file_size_limit()
            valid_files.append(is_valid)
            
            file_data.append({
                "File": file.name,
                "Size": f"{file_size_mb:.1f} MB",
                "Format": file.name.split('.')[-1].upper(),
                "Status": "✅ Valid" if is_valid else "❌ Too Large"
            })
        
        # Display file table
        import pandas as pd
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", len(uploaded_files))
        with col2:
            st.metric("Valid Files", sum(valid_files))
        with col3:
            st.metric("Total Size", f"{total_size:.1f} MB")
        with col4:
            estimated_time = estimate_processing_time(len(uploaded_files), total_size, analysis_mode)
            st.metric("Est. Time", estimated_time)
        
        # Job configuration
        st.markdown("### ⚙️ Processing Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_name = st.text_input(
                "Job Name (optional)",
                value=f"Batch Job {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                help="Give your batch job a descriptive name"
            )
        
        with col2:
            selected_analysis_mode = st.selectbox(
                "Analysis Mode",
                ["Basic (spaCy)", "Advanced (OpenAI)", "Advanced+ (Speaker Diarization)"],
                index=["Basic (spaCy)", "Advanced (OpenAI)", "Advanced+ (Speaker Diarization)"].index(analysis_mode),
                help="Choose analysis mode for all files in this batch"
            )
        
        # Processing options
        with st.expander("🔧 Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                auto_export = st.checkbox(
                    "Auto-export when complete",
                    value=True,
                    help="Automatically prepare export when batch processing completes"
                )
                
                export_format = st.selectbox(
                    "Export Format",
                    ["json", "csv", "xlsx", "txt", "zip"],
                    index=4,  # Default to zip
                    help="Format for automatic export"
                )
            
            with col2:
                include_metadata = st.checkbox(
                    "Include metadata in export",
                    value=True,
                    help="Include job information and processing details"
                )
                
                cleanup_after_export = st.checkbox(
                    "Cleanup files after export",
                    value=False,
                    help="Automatically delete temporary files after successful export"
                )
        
        # OpenAI Batch Processing Information
        if "Advanced" in selected_analysis_mode and len(uploaded_files) >= 3:
            # Check if eligible for OpenAI batch processing
            temp_job = type('TempJob', (), {
                'analysis_mode': selected_analysis_mode,
                'files': [type('TempFile', (), {'size_bytes': f.size}) for f in uploaded_files]
            })()
            
            if openai_batch_processor.can_use_batch_processing(temp_job):
                cost_estimate = openai_batch_processor.get_batch_cost_estimate(temp_job)
                
                st.info(f"""
                🚀 **OpenAI Batch Processing Eligible!**
                
                Your job qualifies for OpenAI's batch processing API, which offers:
                • **{cost_estimate['savings_percentage']:.0f}% cost savings** (estimated ${cost_estimate['savings']:.3f} saved)
                • **Higher throughput** with parallel processing
                • **Better reliability** with automatic retry handling
                
                Estimated costs: ${cost_estimate['batch_cost']:.3f} (vs ${cost_estimate['standard_cost']:.3f} standard)
                """)
            else:
                st.warning("""
                ⚠️ **Standard Processing Mode**
                
                This job will use standard API calls. For OpenAI batch processing benefits:
                • Use 3+ files minimum
                • Keep total size under 2GB
                • Ensure OpenAI API key is configured
                """)
        
        # Start processing button
        if st.button("🚀 Start Batch Processing", type="primary", disabled=not any(valid_files)):
            start_batch_processing(
                uploaded_files, 
                valid_files, 
                job_name, 
                selected_analysis_mode,
                auto_export,
                export_format,
                include_metadata,
                cleanup_after_export
            )
        
        # Show warnings for invalid files
        if uploaded_files and not all(valid_files):
            invalid_count = len(valid_files) - sum(valid_files)
            st.warning(f"⚠️ {invalid_count} file(s) exceed the size limit and will be skipped.")
    
    else:
        # Show help when no files uploaded
        st.info("👆 Select multiple audio/video files to get started with batch processing")
        
        with st.expander("💡 Batch Processing Tips"):
            st.markdown("""
            **Optimal Batch Processing:**
            - Upload 5-20 files per batch for best performance
            - Keep individual files under 2GB
            - Mix of short and long files processes more efficiently
            - Use consistent audio quality across files
            
            **Supported Formats:**
            - **Audio:** MP3, WAV (direct processing)
            - **Video:** MP4, M4A (audio extraction required)
            
            **Processing Modes:**
            - **Basic:** Fast local processing, works offline
            - **Advanced:** AI-powered analysis with summaries
            - **Advanced+:** Speaker diarization and multi-language support
            
            **Export Options:**
            - **JSON:** Structured data with full details
            - **CSV:** Spreadsheet-compatible format
            - **Excel:** Multi-sheet workbook with analysis
            - **TXT:** Human-readable text format
            - **ZIP:** All formats bundled together
            """)

def start_batch_processing(uploaded_files, valid_files, job_name, analysis_mode, auto_export, export_format, include_metadata, cleanup_after_export):
    """Start batch processing with uploaded files"""
    
    try:
        # Filter valid files and create temporary files
        temp_files = []
        file_info_list = []
        
        temp_dir = utils.ensure_temp_directory()
        
        for i, (file, is_valid) in enumerate(zip(uploaded_files, valid_files)):
            if not is_valid:
                continue
            
            # Create temporary file
            temp_path = os.path.join(temp_dir, f"batch_{utils.get_timestamp()}_{i}_{file.name}")
            
            # Save uploaded file to temporary location
            with open(temp_path, "wb") as f:
                f.write(file.read())
            
            temp_files.append(temp_path)
            
            file_info = {
                'name': file.name,
                'size_bytes': file.size,
                'format': file.name.split('.')[-1].lower(),
                'temp_path': temp_path
            }
            file_info_list.append(file_info)
        
        if not file_info_list:
            st.error("❌ No valid files to process")
            return
        
        # Create batch job
        job_id = batch_processor.create_batch_job(
            files=file_info_list,
            analysis_mode=analysis_mode,
            job_name=job_name
        )
        
        # Store job configuration in session state
        if 'batch_jobs' not in st.session_state:
            st.session_state.batch_jobs = {}
        
        st.session_state.batch_jobs[job_id] = {
            'auto_export': auto_export,
            'export_format': export_format,
            'include_metadata': include_metadata,
            'cleanup_after_export': cleanup_after_export,
            'temp_files': temp_files
        }
        
        st.success(f"✅ Batch job '{job_name}' started with {len(file_info_list)} files")
        st.info(f"📋 Job ID: {job_id}")
        
        # Switch to status tab
        st.session_state.batch_active_tab = 1
        st.rerun()
        
    except Exception as e:
        logger.error(f"Failed to start batch processing: {e}")
        st.error(f"❌ Failed to start batch processing: {str(e)}")
        
        # Cleanup temporary files on error
        for temp_path in temp_files:
            utils.cleanup_file(temp_path)

def render_job_status_interface():
    """Render the job status monitoring interface"""
    
    st.subheader("Job Status & Progress")
    
    # Get all jobs
    all_jobs = batch_processor.get_all_jobs()
    
    if not all_jobs:
        st.info("📭 No batch jobs found. Start a new batch job in the Upload & Process tab.")
        return
    
    # Sort jobs by creation time (newest first)
    sorted_jobs = sorted(
        all_jobs.items(),
        key=lambda x: x[1]['created_time'] if x[1]['created_time'] else '',
        reverse=True
    )
    
    # Display each job
    for job_id, job_data in sorted_jobs:
        render_job_status_card(job_id, job_data)

def render_job_status_card(job_id: str, job_data: Dict[str, Any]):
    """Render a status card for a single job"""
    
    status = job_data['status']
    
    # Choose appropriate emoji and color based on status
    status_info = {
        'pending': {'emoji': '⏳', 'color': 'blue'},
        'processing': {'emoji': '⚙️', 'color': 'orange'},
        'completed': {'emoji': '✅', 'color': 'green'},
        'failed': {'emoji': '❌', 'color': 'red'},
        'cancelled': {'emoji': '🚫', 'color': 'gray'}
    }
    
    info = status_info.get(status, {'emoji': '❓', 'color': 'gray'})
    
    with st.container():
        # Job header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {info['emoji']} {job_data['name']}")
            st.caption(f"Job ID: {job_id} • Mode: {job_data['analysis_mode']}")
        
        with col2:
            if status == 'processing':
                if st.button("🛑 Cancel", key=f"cancel_{job_id}"):
                    if batch_processor.cancel_job(job_id):
                        st.success("Job cancelled")
                        st.rerun()
        
        with col3:
            if status in ['completed', 'failed']:
                if st.button("🗑️ Delete", key=f"delete_{job_id}"):
                    if batch_processor.delete_job(job_id):
                        st.success("Job deleted")
                        st.rerun()
        
        # Progress bar
        if status == 'processing':
            progress = job_data['progress_percentage']
            st.progress(progress / 100, text=f"Progress: {progress}%")
        
        # Job statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Files", job_data['total_files'])
        with col2:
            st.metric("Completed", job_data['completed_files'])
        with col3:
            st.metric("Failed", job_data['failed_files'])
        with col4:
            if job_data.get('summary'):
                st.metric("Total Words", job_data['summary']['total_words'])
            else:
                st.metric("Status", status.title())
        
        # File details
        if st.checkbox(f"Show file details", key=f"details_{job_id}"):
            render_file_details(job_data['files'])
        
        # OpenAI Batch Status (if applicable)
        openai_batches = openai_batch_processor.get_all_active_batches()
        job_batches = {bid: batch for bid, batch in openai_batches.items() if batch.job_id == job_id}
        
        if job_batches:
            with st.expander("🤖 OpenAI Batch Status"):
                for batch_id, batch_job in job_batches.items():
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Batch Type", batch_job.request_type.title())
                    with col2:
                        st.metric("Status", batch_job.status.value.title())
                    with col3:
                        if batch_job.completed_at:
                            duration = (batch_job.completed_at - batch_job.created_at).total_seconds()
                            st.metric("Duration", f"{duration:.0f}s")
                        else:
                            elapsed = (datetime.now() - batch_job.created_at).total_seconds()
                            st.metric("Elapsed", f"{elapsed:.0f}s")
                    
                    if batch_job.error_message:
                        st.error(f"Error: {batch_job.error_message}")
        
        # Job summary for completed jobs
        if status == 'completed' and job_data.get('summary'):
            with st.expander("📊 Job Summary"):
                summary = job_data['summary']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Processing Time", f"{summary['processing_time']:.1f}s")
                    st.metric("Average Confidence", f"{summary['average_confidence']:.3f}")
                
                with col2:
                    st.metric("Total Words", summary['total_words'])
                    success_rate = (job_data['completed_files'] / job_data['total_files']) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Show cost savings if OpenAI batch was used
                if job_batches:
                    st.markdown("**💰 OpenAI Batch Processing Benefits:**")
                    st.success("• 50% cost reduction compared to standard API calls")
                    st.success("• Improved reliability with automatic retry handling")
                    st.success("• Higher throughput with parallel processing")
        
        st.markdown("---")

def render_file_details(files: List[Dict[str, Any]]):
    """Render detailed information about files in a job"""
    
    # Create file status table
    file_data = []
    for file_info in files:
        status_emoji = {
            'pending': '⏳',
            'processing': '⚙️',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(file_info['status'], '❓')
        
        file_data.append({
            "Status": f"{status_emoji} {file_info['status'].title()}",
            "File Name": file_info['name'],
            "Size": f"{file_info['size_bytes'] / (1024*1024):.1f} MB",
            "Format": file_info['format'].upper(),
            "Progress": f"{file_info['progress']}%",
            "Time": f"{file_info['processing_time']:.1f}s" if file_info['processing_time'] > 0 else "-",
            "Error": file_info.get('error_message', '')[:50] + "..." if file_info.get('error_message', '') else ""
        })
    
    import pandas as pd
    df = pd.DataFrame(file_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_export_interface():
    """Render the export interface for completed jobs"""
    
    st.subheader("Export Results")
    
    # Get completed jobs
    all_jobs = batch_processor.get_all_jobs()
    completed_jobs = {
        job_id: job_data for job_id, job_data in all_jobs.items()
        if job_data['status'] == 'completed'
    }
    
    if not completed_jobs:
        st.info("📭 No completed jobs available for export. Complete a batch job first.")
        return
    
    # Job selection
    job_options = {f"{job_data['name']} ({job_id})": job_id for job_id, job_data in completed_jobs.items()}
    
    selected_job_display = st.selectbox(
        "Select job to export",
        options=list(job_options.keys()),
        help="Choose a completed batch job to export results"
    )
    
    if not selected_job_display:
        return
    
    selected_job_id = job_options[selected_job_display]
    job_data = completed_jobs[selected_job_id]
    
    # Get job object for export
    job_status = batch_processor.get_job_status(selected_job_id)
    if not job_status:
        st.error("❌ Could not retrieve job data")
        return
    
    # Export configuration
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "Export Format",
            ["json", "csv", "xlsx", "txt", "zip"],
            index=4,  # Default to zip
            help="Choose the format for exporting results"
        )
    
    with col2:
        include_metadata = st.checkbox(
            "Include metadata",
            value=True,
            help="Include job information and processing details in export"
        )
    
    # Show export preview/stats
    if st.checkbox("Show export preview"):
        render_export_preview(selected_job_id, job_data)
    
    # Export button
    if st.button("📥 Export Results", type="primary"):
        export_job_results(selected_job_id, export_format, include_metadata)

def render_export_preview(job_id: str, job_data: Dict[str, Any]):
    """Render a preview of what will be exported"""
    
    st.markdown("#### 📋 Export Preview")
    
    # Get export stats
    job_results = batch_processor.get_job_results(job_id)
    if not job_results:
        st.warning("No results available for preview")
        return
    
    # Calculate statistics
    total_transcripts = len([r for r in job_results.values() if r.transcript])
    total_words = sum(r.word_count for r in job_results.values())
    total_entities = sum(
        sum(len(entities) for entities in r.entities.values()) 
        for r in job_results.values() 
        if r.entities
    )
    has_summaries = any(r.summary for r in job_results.values())
    
    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Transcripts", total_transcripts)
    with col2:
        st.metric("Total Words", total_words)
    with col3:
        st.metric("Entities", total_entities)
    with col4:
        st.metric("Summaries", "Yes" if has_summaries else "No")
    
    # Show sample content
    if job_results:
        sample_result = next(iter(job_results.values()))
        
        with st.expander("📄 Sample Transcript"):
            preview_text = sample_result.transcript[:500] + "..." if len(sample_result.transcript) > 500 else sample_result.transcript
            st.text_area("Sample content", value=preview_text, height=100, disabled=True)
        
        if sample_result.entities:
            with st.expander("🏷️ Sample Entities"):
                for entity_type, entities in sample_result.entities.items():
                    if entities:
                        st.write(f"**{entity_type}:** {', '.join(entities[:5])}")

def export_job_results(job_id: str, format_type: str, include_metadata: bool):
    """Export results for a specific job"""
    
    try:
        # Get job object (this is a simplified version - in real implementation,
        # you'd need to reconstruct the BatchJob object from the stored data)
        job_status = batch_processor.get_job_status(job_id)
        if not job_status:
            st.error("❌ Could not retrieve job data")
            return
        
        # Implement actual export functionality
        try:
            # Reconstruct the BatchJob object
            job = batch_processor.get_job(job_id)
            if not job:
                st.error(f"Job {job_id} not found")
                return
            
            # Use batch_exporter to export job results
            export_data = batch_exporter.export_job_results(
                job=job,
                format_type=format_type,
                include_metadata=include_metadata
            )
            
            if export_data:
                # Determine file extension based on format
                file_extension = format_type.lower()
                if format_type == "JSON":
                    file_extension = "json"
                elif format_type == "CSV":
                    file_extension = "csv"
                elif format_type == "TXT":
                    file_extension = "txt"
                elif format_type == "HTML":
                    file_extension = "html"
                
                # Generate filename
                filename = f"batch_export_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
                
                # Provide download button with the exported data
                st.download_button(
                    label=f"📥 Download {format_type} Export",
                    data=export_data,
                    file_name=filename,
                    mime=f"text/{file_extension}" if file_extension in ["json", "csv", "txt", "html"] else "application/octet-stream"
                )
                
                st.success(f"✅ Export prepared in {format_type} format")
            else:
                st.error("❌ Failed to generate export data")
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            st.error(f"❌ Export failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        st.error(f"❌ Export failed: {str(e)}")

def estimate_processing_time(num_files: int, total_size_mb: float, analysis_mode: str) -> str:
    """Estimate processing time for batch job"""
    
    # Base processing time per MB (rough estimates)
    time_per_mb = {
        "Basic (spaCy)": 2,  # seconds per MB
        "Advanced (OpenAI)": 5,  # seconds per MB  
        "Advanced+ (Speaker Diarization)": 8  # seconds per MB
    }
    
    base_time = total_size_mb * time_per_mb.get(analysis_mode, 3)
    
    # Add overhead for multiple files
    overhead = num_files * 10  # 10 seconds overhead per file
    
    total_seconds = base_time + overhead
    
    if total_seconds < 60:
        return f"{int(total_seconds)}s"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        return f"{minutes}m"
    else:
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def cleanup_batch_session():
    """Clean up batch processing session data"""
    
    if 'batch_jobs' in st.session_state:
        # Cleanup temporary files for completed jobs
        for job_id, job_config in st.session_state.batch_jobs.items():
            if job_config.get('cleanup_after_export', False):
                for temp_file in job_config.get('temp_files', []):
                    utils.cleanup_file(temp_file)
        
        # Clear session data
        del st.session_state.batch_jobs
    
    logger.info("Batch session cleaned up")
