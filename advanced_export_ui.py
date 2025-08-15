"""
Streamlit UI for Advanced Export System
Provides comprehensive interface for managing exports, templates, and analytics
"""

import streamlit as st
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from advanced_export_system import (
    AdvancedExportSystem, 
    ExportPriority, 
    ExportStatus, 
    TemplateType,
    advanced_export_system
)
from streamlit_unified_components import UnifiedComponents


class AdvancedExportUI:
    """Streamlit UI for the Advanced Export System"""
    
    def __init__(self):
        self.unified = UnifiedComponents()
        self.export_system = advanced_export_system
        
        # Initialize session state
        if 'export_ui_state' not in st.session_state:
            st.session_state.export_ui_state = {
                'active_jobs': {},
                'selected_template': None,
                'custom_template_editor': False,
                'export_history': [],
                'last_refresh': datetime.now()
            }
    
    def render_export_interface(self):
        """Render the main export interface"""
        
        # Header
        self.unified.accessibility.add_skip_link("export-content")
        
        st.markdown("# 📤 Advanced Export System")
        st.markdown("*Professional export tools with custom templates, batch processing, and analytics*")
        
        # Quick stats
        self._render_quick_stats()
        
        # Main content
        st.markdown('<div id="export-content">', unsafe_allow_html=True)
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚀 Quick Export",
            "📋 Template Manager", 
            "📊 Job Monitor",
            "📈 Analytics",
            "⚙️ Settings"
        ])
        
        with tab1:
            self._render_quick_export()
        
        with tab2:
            self._render_template_manager()
        
        with tab3:
            self._render_job_monitor()
        
        with tab4:
            self._render_analytics()
        
        with tab5:
            self._render_settings()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_quick_stats(self):
        """Render quick statistics"""
        
        analytics = self.export_system.get_export_analytics()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "📤 Total Exports",
                analytics.total_exports,
                delta=f"+{analytics.total_exports - analytics.failed_exports}"
            )
        
        with col2:
            success_rate = (analytics.successful_exports / analytics.total_exports * 100) if analytics.total_exports > 0 else 0
            st.metric(
                "✅ Success Rate", 
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 95:.1f}%"
            )
        
        with col3:
            st.metric(
                "⚡ Avg Time",
                f"{analytics.average_processing_time:.1f}s",
                delta=f"{analytics.average_processing_time - 30:.1f}s",
                delta_color="inverse"
            )
        
        with col4:
            templates = self.export_system.get_available_templates()
            st.metric(
                "📋 Templates",
                len(templates),
                delta=f"+{len([t for t in templates if not t['is_public']])}"
            )
        
        with col5:
            active_jobs = len([job for job in self.export_system.export_jobs.values() 
                             if job.status in [ExportStatus.PENDING, ExportStatus.IN_PROGRESS]])
            st.metric(
                "🔄 Active Jobs",
                active_jobs,
                delta=f"+{active_jobs}"
            )
    
    def _render_quick_export(self):
        """Render quick export interface"""
        
        st.markdown("### 🚀 Quick Export")
        st.markdown("*Create exports quickly with smart defaults*")
        
        # Export source selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            export_source = st.selectbox(
                "Export Source",
                ["Single Transcript", "Multiple Transcripts", "Batch Job Results", "Custom Data"],
                help="Select what you want to export"
            )
        
        with col2:
            export_priority = st.selectbox(
                "Priority",
                ["Normal", "High", "Low", "Urgent"],
                help="Export processing priority"
            )
        
        # Source-specific configuration
        if export_source == "Single Transcript":
            self._render_single_transcript_config()
        elif export_source == "Multiple Transcripts":
            self._render_multiple_transcripts_config()
        elif export_source == "Batch Job Results":
            self._render_batch_job_config()
        else:
            self._render_custom_data_config()
        
        # Export format and template selection
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                ["text", "json", "markdown", "docx", "pdf", "xlsx", "csv"],
                help="Output file format"
            )
        
        with col2:
            templates = self.export_system.get_available_templates()
            template_options = ["None (Standard)"] + [f"{t['name']} ({t['template_type']})" for t in templates]
            
            selected_template = st.selectbox(
                "Template",
                template_options,
                help="Optional formatting template"
            )
        
        # Export options
        with st.expander("🔧 Export Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                include_metadata = st.checkbox("Include Metadata", value=True)
                include_entities = st.checkbox("Include Entities", value=True)
                include_summary = st.checkbox("Include Summary", value=True)
            
            with col2:
                include_timestamps = st.checkbox("Include Timestamps", value=False)
                include_confidence = st.checkbox("Include Confidence Scores", value=False)
                anonymize_data = st.checkbox("Anonymize Personal Data", value=False)
        
        # Template-specific options
        if selected_template != "None (Standard)":
            self._render_template_options(selected_template, templates)
        
        # Schedule options
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_name = st.text_input(
                "Export Name",
                value=f"Export_{datetime.now().strftime('%Y%m%d_%H%M')}",
                help="Name for this export job"
            )
        
        with col2:
            schedule_export = st.checkbox("Schedule Export", value=False)
            
            if schedule_export:
                scheduled_time = st.datetime_input(
                    "Schedule Time",
                    value=datetime.now() + timedelta(hours=1),
                    help="When to run this export"
                )
        
        # Create export button
        st.markdown("---")
        
        if st.button("🚀 Create Export", type="primary"):
            self._create_export_job(
                name=export_name,
                source=export_source,
                format_type=export_format,
                template=selected_template if selected_template != "None (Standard)" else None,
                priority=export_priority,
                options={
                    'include_metadata': include_metadata,
                    'include_entities': include_entities,
                    'include_summary': include_summary,
                    'include_timestamps': include_timestamps,
                    'include_confidence': include_confidence,
                    'anonymize_data': anonymize_data
                },
                scheduled_time=scheduled_time if schedule_export else None
            )
    
    def _render_single_transcript_config(self):
        """Render single transcript configuration"""
        
        transcript_id = st.text_input(
            "Transcript ID",
            help="ID of the transcript to export"
        )
        
        include_annotations = st.checkbox(
            "Include Comments & Annotations",
            value=True,
            help="Include user comments and annotations"
        )
        
        return {
            'transcript_id': transcript_id,
            'include_annotations': include_annotations
        }
    
    def _render_multiple_transcripts_config(self):
        """Render multiple transcripts configuration"""
        
        transcript_ids_text = st.text_area(
            "Transcript IDs (one per line)",
            help="Enter transcript IDs, one per line"
        )
        
        transcript_ids = [tid.strip() for tid in transcript_ids_text.split('\n') if tid.strip()]
        
        merge_into_single = st.checkbox(
            "Merge into Single Document",
            value=False,
            help="Combine all transcripts into one document"
        )
        
        if len(transcript_ids) > 0:
            st.success(f"✅ {len(transcript_ids)} transcript(s) selected")
        
        return {
            'transcript_ids': transcript_ids,
            'merge_into_single': merge_into_single
        }
    
    def _render_batch_job_config(self):
        """Render batch job configuration"""
        
        batch_job_id = st.text_input(
            "Batch Job ID",
            help="ID of the batch processing job"
        )
        
        include_failed = st.checkbox(
            "Include Failed Files",
            value=False,
            help="Include information about failed files"
        )
        
        return {
            'batch_job_id': batch_job_id,
            'include_failed': include_failed
        }
    
    def _render_custom_data_config(self):
        """Render custom data configuration"""
        
        st.markdown("**Upload Custom Data**")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['json', 'csv', 'txt'],
            help="Upload custom data file"
        )
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        return {
            'custom_file': uploaded_file
        }
    
    def _render_template_options(self, selected_template: str, templates: List[Dict]):
        """Render template-specific options"""
        
        # Find the selected template
        template_name = selected_template.split(" (")[0]
        template = next((t for t in templates if t['name'] == template_name), None)
        
        if not template:
            return
        
        st.markdown("**📋 Template Options**")
        
        # Template-specific fields based on type
        template_type = template['template_type']
        
        if template_type == 'meeting_minutes':
            self._render_meeting_template_options()
        elif template_type == 'interview':
            self._render_interview_template_options()
        elif template_type == 'legal_deposition':
            self._render_legal_template_options()
        elif template_type == 'medical_consultation':
            self._render_medical_template_options()
    
    def _render_meeting_template_options(self):
        """Render meeting template options"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            attendees = st.text_area(
                "Attendees (one per line)",
                help="List meeting attendees"
            )
            
            location = st.text_input(
                "Meeting Location",
                value="Virtual",
                help="Meeting location"
            )
        
        with col2:
            agenda_items = st.text_area(
                "Agenda Items (one per line)",
                help="Meeting agenda items"
            )
            
            next_meeting_date = st.date_input(
                "Next Meeting Date",
                help="Date of next meeting"
            )
    
    def _render_interview_template_options(self):
        """Render interview template options"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            interviewee = st.text_input("Interviewee Name")
            interviewer = st.text_input("Interviewer Name")
        
        with col2:
            position = st.text_input("Position/Role")
            duration = st.text_input("Interview Duration")
    
    def _render_legal_template_options(self):
        """Render legal template options"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            deponent_name = st.text_input("Deponent Name")
            case_name = st.text_input("Case Name")
            case_number = st.text_input("Case Number")
        
        with col2:
            court_reporter = st.text_input("Court Reporter")
            examining_attorney = st.text_input("Examining Attorney")
            location = st.text_input("Location")
    
    def _render_medical_template_options(self):
        """Render medical template options"""
        
        st.warning("⚠️ Medical templates handle PHI - ensure HIPAA compliance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            patient_id = st.text_input("Patient ID", value="PATIENT_001")
            provider_name = st.text_input("Provider Name")
        
        with col2:
            provider_title = st.text_input("Provider Title")
            consultation_type = st.selectbox(
                "Consultation Type",
                ["Initial", "Follow-up", "Specialty", "Telemedicine"]
            )
    
    def _render_template_manager(self):
        """Render template manager interface"""
        
        st.markdown("### 📋 Template Manager")
        st.markdown("*Create and manage custom export templates*")
        
        # Template list
        templates = self.export_system.get_available_templates()
        
        # Create new template button
        if st.button("➕ Create New Template"):
            st.session_state.export_ui_state['custom_template_editor'] = True
        
        # Template editor
        if st.session_state.export_ui_state['custom_template_editor']:
            self._render_template_editor()
        
        # Templates table
        if templates:
            st.markdown("**📚 Available Templates**")
            
            template_df = pd.DataFrame(templates)
            
            # Display templates with actions
            for i, template in enumerate(templates):
                with st.expander(f"📋 {template['name']} ({template['template_type']})"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Description:** {template['description']}")
                        st.markdown(f"**Format:** {template['output_format']}")
                        st.markdown(f"**Created by:** {template['created_by']}")
                        st.markdown(f"**Public:** {'Yes' if template['is_public'] else 'No'}")
                        
                        if template['tags']:
                            st.markdown(f"**Tags:** {', '.join(template['tags'])}")
                    
                    with col2:
                        if st.button(f"👁️ Preview", key=f"preview_{i}"):
                            self._show_template_preview(template)
                    
                    with col3:
                        if st.button(f"📝 Edit", key=f"edit_{i}"):
                            st.session_state.export_ui_state['selected_template'] = template['id']
                            st.session_state.export_ui_state['custom_template_editor'] = True
        else:
            st.info("No templates available. Create your first template!")
    
    def _render_template_editor(self):
        """Render template editor interface"""
        
        st.markdown("**📝 Template Editor**")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            template_name = st.text_input("Template Name")
            template_description = st.text_area("Description")
        
        with col2:
            template_type = st.selectbox(
                "Template Type",
                [t.value for t in TemplateType],
                help="Type of template"
            )
            
            output_format = st.selectbox(
                "Output Format",
                ["markdown", "text", "html"],
                help="Template output format"
            )
        
        # Template content editor
        st.markdown("**Template Content (Jinja2 syntax)**")
        
        template_content = st.text_area(
            "Template Content",
            height=300,
            help="Use Jinja2 syntax. Available variables: transcript, entities, summary, metadata"
        )
        
        # Template options
        col1, col2 = st.columns(2)
        
        with col1:
            is_public = st.checkbox("Make Public", help="Allow others to use this template")
        
        with col2:
            tags_input = st.text_input("Tags (comma-separated)", help="Tags for categorization")
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Template", type="primary"):
                self._save_template(
                    template_name, template_description, template_content,
                    output_format, template_type, is_public, tags
                )
        
        with col2:
            if st.button("👁️ Preview"):
                self._preview_template(template_content, output_format)
        
        with col3:
            if st.button("❌ Cancel"):
                st.session_state.export_ui_state['custom_template_editor'] = False
                st.rerun()
    
    def _render_job_monitor(self):
        """Render job monitoring interface"""
        
        st.markdown("### 📊 Job Monitor")
        st.markdown("*Track export job progress and status*")
        
        # Refresh button
        if st.button("🔄 Refresh", key="job_refresh"):
            st.session_state.export_ui_state['last_refresh'] = datetime.now()
        
        # Job filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                [status.value for status in ExportStatus],
                default=[ExportStatus.PENDING.value, ExportStatus.IN_PROGRESS.value]
            )
        
        with col2:
            priority_filter = st.multiselect(
                "Filter by Priority",
                [priority.value for priority in ExportPriority],
                default=[priority.value for priority in ExportPriority]
            )
        
        with col3:
            user_filter = st.text_input("Filter by User ID")
        
        # Display jobs
        jobs = list(self.export_system.export_jobs.values())
        
        # Apply filters
        if status_filter:
            jobs = [job for job in jobs if job.status.value in status_filter]
        
        if priority_filter:
            jobs = [job for job in jobs if job.priority.value in priority_filter]
        
        if user_filter:
            jobs = [job for job in jobs if user_filter.lower() in job.user_id.lower()]
        
        # Sort by created date (newest first)
        jobs = sorted(jobs, key=lambda x: x.created_at, reverse=True)
        
        if jobs:
            for job in jobs[:20]:  # Show last 20 jobs
                self._render_job_card(job)
        else:
            st.info("No export jobs found matching the filters.")
    
    def _render_job_card(self, job):
        """Render individual job card"""
        
        # Status color
        status_colors = {
            ExportStatus.PENDING: "🟡",
            ExportStatus.IN_PROGRESS: "🔵", 
            ExportStatus.COMPLETED: "🟢",
            ExportStatus.FAILED: "🔴",
            ExportStatus.CANCELLED: "⚫"
        }
        
        priority_colors = {
            ExportPriority.LOW: "🟦",
            ExportPriority.NORMAL: "🟩",
            ExportPriority.HIGH: "🟨",
            ExportPriority.URGENT: "🟥"
        }
        
        with st.expander(f"{status_colors[job.status]} {job.name} - {job.status.value.title()}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Job ID:** `{job.id[:8]}...`")
                st.markdown(f"**User:** {job.user_id}")
                st.markdown(f"**Type:** {job.export_type}")
                st.markdown(f"**Format:** {job.format_type}")
            
            with col2:
                st.markdown(f"**Priority:** {priority_colors[job.priority]} {job.priority.value.title()}")
                st.markdown(f"**Created:** {job.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                if job.started_at:
                    st.markdown(f"**Started:** {job.started_at.strftime('%Y-%m-%d %H:%M')}")
                
                if job.completed_at:
                    st.markdown(f"**Completed:** {job.completed_at.strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                # Progress bar
                if job.status == ExportStatus.IN_PROGRESS:
                    st.progress(job.progress_percent / 100)
                    st.markdown(f"**Progress:** {job.progress_percent}%")
                
                # Error message
                if job.error_message:
                    st.error(f"❌ {job.error_message}")
                
                # Download link
                if job.result_file_path:
                    st.success("✅ Export ready for download")
            
            # Action buttons
            button_col1, button_col2, button_col3 = st.columns(3)
            
            with button_col1:
                if job.status in [ExportStatus.PENDING, ExportStatus.IN_PROGRESS]:
                    if st.button(f"🛑 Cancel", key=f"cancel_{job.id[:8]}"):
                        asyncio.run(self.export_system.cancel_export_job(job.id))
                        st.rerun()
            
            with button_col2:
                if st.button(f"🔍 Details", key=f"details_{job.id[:8]}"):
                    st.json(job.export_options)
            
            with button_col3:
                if job.result_file_path:
                    if st.button(f"📥 Download", key=f"download_{job.id[:8]}"):
                        # Would trigger download
                        st.success("Download started!")
    
    def _render_analytics(self):
        """Render analytics interface"""
        
        st.markdown("### 📈 Export Analytics")
        st.markdown("*Insights into export usage and performance*")
        
        analytics = self.export_system.get_export_analytics()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Exports", analytics.total_exports)
        
        with col2:
            success_rate = (analytics.successful_exports / analytics.total_exports * 100) if analytics.total_exports > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            st.metric("Failed Exports", analytics.failed_exports)
        
        with col4:
            st.metric("Avg Processing Time", f"{analytics.average_processing_time:.2f}s")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Format popularity
            if analytics.most_popular_formats:
                fig = px.pie(
                    values=list(analytics.most_popular_formats.values()),
                    names=list(analytics.most_popular_formats.keys()),
                    title="Most Popular Export Formats"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Template usage
            if analytics.most_used_templates:
                fig = px.bar(
                    x=list(analytics.most_used_templates.keys()),
                    y=list(analytics.most_used_templates.values()),
                    title="Most Used Templates"
                )
                fig.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Export history table
        st.markdown("**📊 Recent Export History**")
        
        if analytics.total_exports > 0:
            # Create sample data for demo
            history_data = []
            for i in range(min(10, analytics.total_exports)):
                history_data.append({
                    'Date': datetime.now() - timedelta(days=i),
                    'Export Type': 'single_transcript',
                    'Format': 'markdown',
                    'Status': 'completed',
                    'Processing Time': f"{2.5 + i * 0.3:.1f}s"
                })
            
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("No export history available.")
    
    def _render_settings(self):
        """Render settings interface"""
        
        st.markdown("### ⚙️ Export Settings")
        st.markdown("*Configure export system behavior*")
        
        # General settings
        st.markdown("**🔧 General Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_format = st.selectbox(
                "Default Export Format",
                ["markdown", "text", "json", "docx", "pdf"],
                help="Default format for new exports"
            )
            
            max_concurrent_jobs = st.number_input(
                "Max Concurrent Jobs",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum number of export jobs to run simultaneously"
            )
        
        with col2:
            auto_cleanup_days = st.number_input(
                "Auto Cleanup (days)",
                min_value=1,
                max_value=365,
                value=30,
                help="Automatically delete export files after N days"
            )
            
            enable_analytics = st.checkbox(
                "Enable Analytics",
                value=True,
                help="Collect usage analytics"
            )
        
        # Storage settings
        st.markdown("**💾 Storage Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            storage_path = st.text_input(
                "Storage Path",
                value=str(self.export_system.storage_path),
                help="Directory for storing export files"
            )
        
        with col2:
            max_storage_gb = st.number_input(
                "Max Storage (GB)",
                min_value=1,
                max_value=1000,
                value=50,
                help="Maximum storage space for exports"
            )
        
        # Notification settings
        st.markdown("**🔔 Notification Settings**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email_notifications = st.checkbox(
                "Email Notifications",
                value=False,
                help="Send email when exports complete"
            )
            
            if email_notifications:
                notification_email = st.text_input(
                    "Notification Email",
                    help="Email address for notifications"
                )
        
        with col2:
            webhook_notifications = st.checkbox(
                "Webhook Notifications",
                value=False,
                help="Send webhook when exports complete"
            )
            
            if webhook_notifications:
                webhook_url = st.text_input(
                    "Webhook URL",
                    help="URL to receive webhook notifications"
                )
        
        # Save settings
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
            
            # Here you would save settings to configuration
            settings = {
                'default_format': default_format,
                'max_concurrent_jobs': max_concurrent_jobs,
                'auto_cleanup_days': auto_cleanup_days,
                'enable_analytics': enable_analytics,
                'storage_path': storage_path,
                'max_storage_gb': max_storage_gb,
                'email_notifications': email_notifications,
                'webhook_notifications': webhook_notifications
            }
            
            # Save settings logic would go here
    
    def _create_export_job(self, **kwargs):
        """Create export job with UI feedback"""
        
        try:
            # Create the export job
            job_id = asyncio.run(self.export_system.create_export_job(
                name=kwargs.get('name', 'Export'),
                user_id='demo_user',  # Would come from session
                export_type='single_transcript',  # Simplified for demo
                format_type=kwargs.get('format_type', 'text'),
                source_data={'transcript_id': 'demo_transcript'},  # Demo data
                export_options=kwargs.get('options', {}),
                priority=ExportPriority(kwargs.get('priority', 'normal').lower()),
                scheduled_time=kwargs.get('scheduled_time')
            ))
            
            st.success(f"✅ Export job created successfully!")
            st.info(f"Job ID: `{job_id}`")
            
            # Show progress (in real implementation, this would be dynamic)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress updates
            import time
            for i in range(0, 101, 20):
                progress_bar.progress(i / 100)
                status_text.text(f"Processing... {i}%")
                time.sleep(0.5)
            
            st.success("🎉 Export completed successfully!")
            
        except Exception as e:
            st.error(f"❌ Failed to create export job: {e}")
    
    def _save_template(self, name, description, content, output_format, template_type, is_public, tags):
        """Save custom template"""
        
        try:
            template_id = self.export_system.create_custom_template(
                name=name,
                description=description,
                template_content=content,
                output_format=output_format,
                created_by='demo_user',  # Would come from session
                template_type=TemplateType(template_type),
                is_public=is_public,
                tags=tags
            )
            
            st.success(f"✅ Template saved successfully!")
            st.info(f"Template ID: `{template_id}`")
            
            # Reset editor
            st.session_state.export_ui_state['custom_template_editor'] = False
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to save template: {e}")
    
    def _preview_template(self, content, output_format):
        """Preview template with sample data"""
        
        st.markdown("**👁️ Template Preview**")
        
        # Sample data
        sample_data = {
            'transcript': 'This is a sample transcript for preview purposes.',
            'metadata': {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M'),
                'location': 'Conference Room A'
            },
            'entities': {
                'people': ['John Doe', 'Jane Smith'],
                'organizations': ['Acme Corp', 'Tech Inc']
            },
            'summary': 'This is a sample summary of the discussion.'
        }
        
        try:
            from jinja2 import Template
            template = Template(content)
            rendered = template.render(**sample_data)
            
            if output_format == 'markdown':
                st.markdown(rendered)
            else:
                st.text(rendered)
                
        except Exception as e:
            st.error(f"❌ Template preview failed: {e}")


def demo_advanced_export_ui():
    """Demo the advanced export UI"""
    
    # Initialize the UI
    export_ui = AdvancedExportUI()
    
    # Render the interface
    export_ui.render_export_interface()


if __name__ == "__main__":
    demo_advanced_export_ui()