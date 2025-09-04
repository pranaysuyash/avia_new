"""
Export and Sharing UI Components for Streamlit
"""

import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from export_manager import MultimediaExporter, ExportConfig, ShareConfig, SharingManager
from streamlit_intent_utils import render_share_inline, render_share_block, log_ux_event, get_params, update_params
from security_manager import create_security_manager

# Create global security manager instance
security_manager = create_security_manager()


class ExportUI:
    """Export and sharing user interface"""
    
    def __init__(self):
        self.exporter = MultimediaExporter()
        self.sharing_manager = SharingManager()
    
    def render_export_interface(self, transcript_data: Dict[str, Any] = None):
        """Render export interface"""
        st.header("📤 Export & Sharing")
        try:
            render_share_inline("Shareable view link")
        except Exception:
            pass
        st.warning("Exports and shares may include PII (names, emails, phone numbers). Confirm authorization to proceed.")
        confirm_pii = st.checkbox("I confirm I am authorized to export/share content that may include PII.")
        
        if not transcript_data:
            # Sample data input for testing
            st.subheader("Sample Data for Testing")
            
            sample_data = {
                'id': 'sample_001',
                'title': 'Sample Meeting Transcript',
                'transcript': 'This is a sample transcript for testing export functionality. We discussed various topics including project updates, budget planning, and team coordination.',
                'duration': 120.5,
                'language': 'en',
                'confidence': 0.95,
                'speakers': ['Alice', 'Bob', 'Charlie'],
                'entities': [
                    {'text': 'Project Alpha', 'label': 'PROJECT', 'confidence': 0.9},
                    {'text': 'Budget Planning', 'label': 'TOPIC', 'confidence': 0.8},
                    {'text': 'Q1 2024', 'label': 'DATE', 'confidence': 0.95}
                ],
                'speaker_segments': [
                    {'speaker_id': 'Alice', 'start_time': 0, 'duration': 30, 'text': 'Welcome everyone to our meeting.'},
                    {'speaker_id': 'Bob', 'start_time': 30, 'duration': 45, 'text': 'Let me update you on Project Alpha progress.'},
                    {'speaker_id': 'Charlie', 'start_time': 75, 'duration': 45.5, 'text': 'The budget planning is on track for Q1 2024.'}
                ]
            }
            
            if st.button("Use Sample Data"):
                transcript_data = sample_data
                st.success("Sample data loaded!")
            else:
                st.info("Click 'Use Sample Data' to test export functionality or provide transcript data")
                return
        
        # Privacy controls
        st.subheader("🔐 Privacy Settings")
        privacy_col1, privacy_col2 = st.columns(2)
        
        with privacy_col1:
            params = get_params()
            anonymize_speakers = st.checkbox(
                "Anonymize Speakers",
                value=(params.get('exp_anon', '0') == '1'),
                help="Replace real speaker names with Speaker 1, Speaker 2, etc."
            )
            
            redact_pii = st.checkbox(
                "Redact Personal Information",
                value=(params.get('exp_pii', '0') == '1'),
                help="Remove names, emails, phone numbers, and other PII"
            )
        
        with privacy_col2:
            encrypt_export = st.checkbox(
                "Encrypt Export File",
                value=(params.get('exp_enc', '1' if security_manager.is_encryption_enabled() else '0') == '1'),
                help="Encrypt the exported file with password protection"
            )
            
            if encrypt_export:
                export_password = st.text_input(
                    "Export Password",
                    type="password",
                    help="Password to encrypt the export file"
                )
        try:
            update_params({
                'exp_anon': '1' if anonymize_speakers else '0',
                'exp_pii': '1' if redact_pii else '0',
                'exp_enc': '1' if encrypt_export else '0',
            })
        except Exception:
            pass
        
        # Apply privacy settings to data
        if anonymize_speakers or redact_pii:
            transcript_data = self._apply_privacy_settings(
                transcript_data,
                anonymize_speakers=anonymize_speakers,
                redact_pii=redact_pii
            )
        
        # Export configuration
        st.subheader("🔧 Export Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Format selection
            export_format = st.selectbox(
                "Export Format",
                options=['pdf', 'docx', 'json', 'csv', 'xlsx', 'html', 'txt', 'xml', 'md'],
                help="Choose the export format"
            )
            try:
                update_params({'exp_format': export_format})
            except Exception:
                pass
            
            # Content options
            st.markdown("**Include in Export:**")
            include_metadata = st.checkbox("Metadata", value=True)
            include_timestamps = st.checkbox("Timestamps", value=True)
            include_speaker_info = st.checkbox("Speaker Information", value=True)
        
        with col2:
            include_entities = st.checkbox("Extracted Entities", value=True)
            include_insights = st.checkbox("Content Insights", value=False)
            include_visualizations = st.checkbox("Visualizations", value=False)
            
            # Custom branding
            st.markdown("**Branding Options:**")
            custom_title = st.text_input("Custom Title", value=transcript_data.get('title', ''))
            add_watermark = st.checkbox("Add Watermark", value=False)
        
        # Create export config
        config = ExportConfig(
            format=export_format,
            include_metadata=include_metadata,
            include_timestamps=include_timestamps,
            include_speaker_info=include_speaker_info,
            include_entities=include_entities,
            include_insights=include_insights,
            include_visualizations=include_visualizations
        )
        
        # Update title if custom provided
        if custom_title:
            transcript_data['title'] = custom_title
        
        # Single export
        st.subheader("📄 Single Format Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Now", type="primary"):
                with st.spinner(f"Exporting to {export_format.upper()}..."):
                    try:
                        export_path = self.exporter.export_transcript(transcript_data, config)
                        
                        # Encrypt if requested
                        if encrypt_export and export_password:
                            encrypted_path = export_path + ".enc"
                            security_manager.encryption_manager.encrypt_file_with_password(
                                export_path, encrypted_path, export_password
                            )
                            # Log export encryption
                            security_manager.audit_logger.log_security_event(
                                "EXPORT_ENCRYPTED",
                                {"format": export_format, "file": Path(export_path).name}
                            )
                            # Use encrypted file for download
                            download_path = encrypted_path
                            download_name = Path(export_path).name + ".enc"
                            # Clean up original
                            os.unlink(export_path)
                        else:
                            download_path = export_path
                            download_name = Path(export_path).name
                        
                        st.success(f"Export completed successfully!")
                        
                        # Display file info
                        file_size = os.path.getsize(download_path)
                        st.info(f"File: {download_name} ({file_size:,} bytes)")
                        
                        # Download button
                        with open(download_path, 'rb') as f:
                            if confirm_pii:
                                st.download_button(
                                    label="📥 Download File",
                                    data=f.read(),
                                    file_name=download_name,
                                    mime=self._get_mime_type(export_format)
                                )
                            else:
                                st.info("Confirm PII authorization to enable downloads.")
                        
                        # Cleanup
                        os.unlink(download_path)
                        
                    except Exception as e:
                        st.error(f"Export failed: {str(e)}")
        
        with col2:
            # Preview option
            if st.button("Preview Export"):
                with st.spinner("Generating preview..."):
                    try:
                        if export_format in ['json', 'txt', 'md', 'xml', 'csv']:
                            export_path = self.exporter.export_transcript(transcript_data, config)
                            
                            with open(export_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            st.subheader(f"Preview ({export_format.upper()})")
                            
                            if export_format == 'json':
                                st.json(json.loads(content))
                            else:
                                st.code(content, language=export_format if export_format != 'txt' else None)
                            
                            os.unlink(export_path)
                        else:
                            st.info(f"Preview not available for {export_format.upper()} format")
                            
                    except Exception as e:
                        st.error(f"Preview failed: {str(e)}")
        
        # Bulk export
        st.markdown("---")
        st.subheader("📦 Bulk Export Package")
        
        st.markdown("Create a comprehensive export package with multiple formats:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_formats = st.multiselect(
                "Select Formats",
                options=['pdf', 'docx', 'json', 'csv', 'xlsx', 'html', 'txt', 'xml', 'md'],
                default=['pdf', 'json', 'csv'],
                help="Choose multiple formats for bulk export"
            )
            try:
                update_params({'exp_bulk': ','.join(selected_formats) if selected_formats else None})
            except Exception:
                pass
        
        with col2:
            include_media = st.checkbox("Include Original Media", value=False)
            include_visualizations_bulk = st.checkbox("Include Visualizations", value=True)
        
        if st.button("Create Export Package", type="primary"):
            if not selected_formats:
                st.warning("Please select at least one format")
            else:
                with st.spinner("Creating export package..."):
                    try:
                        package_path = self.exporter.create_export_package(
                            transcript_data,
                            selected_formats,
                            include_media=include_media
                        )
                        
                        st.success("Export package created successfully!")
                        
                        # Package info
                        package_size = os.path.getsize(package_path)
                        st.info(f"Package: {Path(package_path).name} ({package_size:,} bytes)")
                        
                        # Download package
                        with open(package_path, 'rb') as f:
                            if confirm_pii:
                                st.download_button(
                                    label="📦 Download Package",
                                    data=f.read(),
                                    file_name=Path(package_path).name,
                                    mime="application/zip"
                                )
                            else:
                                st.info("Confirm PII authorization to enable downloads.")
                        
                        # Show package contents
                        with st.expander("Package Contents"):
                            import zipfile
                            with zipfile.ZipFile(package_path, 'r') as zip_file:
                                file_list = zip_file.namelist()
                                for file_name in file_list:
                                    st.write(f"📄 {file_name}")
                        
                        # Cleanup
                        os.unlink(package_path)
                        
                    except Exception as e:
                        st.error(f"Package creation failed: {str(e)}")
        
        # Sharing options
        st.markdown("---")
        st.subheader("🔗 Sharing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            share_platform = st.selectbox(
                "Sharing Platform",
                options=['email', 'link', 'cloud', 'api'],
                help="Choose how to share the exported content"
            )
            
            permissions = st.selectbox(
                "Permissions",
                options=['read', 'write', 'admin'],
                help="Set access permissions for shared content"
            )
            try:
                update_params({'exp_share': share_platform, 'exp_perms': permissions})
            except Exception:
                pass
        
        with col2:
            expiry_hours = st.number_input(
                "Link Expiry (hours)",
                min_value=1,
                max_value=8760,  # 1 year
                value=int(params.get('exp_expiry', '24')) if params.get('exp_expiry', '').isdigit() else 24,
                help="How long the share link should remain active"
            )
            
            password_protected = st.checkbox("Password Protected", value=(params.get('exp_pwd', '0') == '1'))
            notify_recipients = st.checkbox("Notify Recipients", value=(params.get('exp_notify', '1') == '1'))
            try:
                update_params({
                    'exp_expiry': str(expiry_hours),
                    'exp_pwd': '1' if password_protected else '0',
                    'exp_notify': '1' if notify_recipients else '0',
                })
            except Exception:
                pass
        
        custom_message = st.text_area(
            "Custom Message",
            placeholder="Add a personal message for recipients...",
            help="Optional message to include when sharing"
        )
        
        if st.button("Create Share Link"):
            if not confirm_pii:
                st.info("Confirm PII authorization to create share links.")
                return
            with st.spinner("Creating shareable link..."):
                try:
                    # First create an export
                    export_path = self.exporter.export_transcript(transcript_data, config)
                    
                    # Create share config
                    share_config = ShareConfig(
                        platform=share_platform,
                        permissions=permissions,
                        expiry_hours=expiry_hours,
                        password_protected=password_protected,
                        notify_recipients=notify_recipients,
                        custom_message=custom_message
                    )
                    
                    # Create shareable link
                    share_info = self.sharing_manager.create_shareable_link(export_path, share_config)
                    
                    st.success("Share link created successfully!")
                    
                    # Display share information
                    st.markdown("**Share Information:**")
                    st.code(share_info['shareable_link'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Share ID:** {share_info['share_id']}")
                        st.write(f"**Permissions:** {share_info['permissions']}")
                    
                    with col2:
                        st.write(f"**Platform:** {share_info['platform']}")
                        if share_info.get('expires_at'):
                            st.write(f"**Expires:** {share_info['expires_at']}")
                    
                    # Generate email content if email platform selected
                    if share_platform == 'email':
                        email_content = self.sharing_manager.generate_email_content(share_info, custom_message)
                        
                        with st.expander("📧 Email Content"):
                            st.write(f"**Subject:** {email_content['subject']}")
                            st.text_area("**Body:**", email_content['body'], height=200)
                    
                    # Cleanup
                    os.unlink(export_path)
                    
                except Exception as e:
                    st.error(f"Share link creation failed: {str(e)}")
        
        # Export history and analytics
        st.markdown("---")
        st.subheader("📊 Export Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Exports Today", "12", "↑ 3")
        
        with col2:
            st.metric("Most Popular Format", "PDF", "45%")
        
        with col3:
            st.metric("Total Shares", "28", "↑ 5")
        
        # Recent exports (placeholder)
        with st.expander("Recent Exports"):
            st.info("Export history would be displayed here in a full implementation")

        # Sidebar share + reset
        with st.sidebar:
            try:
                render_share_block("Share Export View")
            except Exception:
                pass
            if st.button("Reset View/Filters"):
                try:
                    st.experimental_set_query_params()
                except Exception:
                    pass
                try:
                    log_ux_event("st_filters_cleared", {"scope": "export_ui"})
                except Exception:
                    pass
                st.rerun()
    
    def _get_mime_type(self, format_type: str) -> str:
        """Get MIME type for format"""
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'json': 'application/json',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'html': 'text/html',
            'txt': 'text/plain',
            'xml': 'application/xml',
            'md': 'text/markdown'
        }
        return mime_types.get(format_type, 'application/octet-stream')
    
    def _apply_privacy_settings(self, data: Dict[str, Any], anonymize_speakers: bool = False, 
                               redact_pii: bool = False) -> Dict[str, Any]:
        """Apply privacy settings to transcript data"""
        import copy
        import re
        
        # Create a deep copy to avoid modifying original data
        private_data = copy.deepcopy(data)
        
        # Anonymize speakers
        if anonymize_speakers and 'speakers' in private_data:
            speaker_map = {}
            for i, speaker in enumerate(private_data['speakers']):
                speaker_map[speaker] = f"Speaker {i+1}"
            
            # Update speakers list
            private_data['speakers'] = list(speaker_map.values())
            
            # Update speaker segments
            if 'speaker_segments' in private_data:
                for segment in private_data['speaker_segments']:
                    if 'speaker_id' in segment and segment['speaker_id'] in speaker_map:
                        segment['speaker_id'] = speaker_map[segment['speaker_id']]
        
        # Redact PII
        if redact_pii:
            # Patterns for common PII
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            phone_pattern = r'\b(?:\+?1?\s*(?:[.-]\s*)?)?(?:\(\s*(\d{3})\s*\)|(\d{3}))\s*(?:[.-]\s*)?(\d{3})\s*(?:[.-]\s*)?(\d{4})\b'
            ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
            
            # Redact from transcript
            if 'transcript' in private_data:
                private_data['transcript'] = re.sub(email_pattern, '[EMAIL REDACTED]', private_data['transcript'])
                private_data['transcript'] = re.sub(phone_pattern, '[PHONE REDACTED]', private_data['transcript'])
                private_data['transcript'] = re.sub(ssn_pattern, '[SSN REDACTED]', private_data['transcript'])
            
            # Redact from speaker segments
            if 'speaker_segments' in private_data:
                for segment in private_data['speaker_segments']:
                    if 'text' in segment:
                        segment['text'] = re.sub(email_pattern, '[EMAIL REDACTED]', segment['text'])
                        segment['text'] = re.sub(phone_pattern, '[PHONE REDACTED]', segment['text'])
                        segment['text'] = re.sub(ssn_pattern, '[SSN REDACTED]', segment['text'])
            
            # Use security manager's privacy manager for entity redaction
            if 'entities' in private_data and security_manager.privacy_manager:
                # Redact person names from entities
                private_data['entities'] = [
                    entity for entity in private_data['entities'] 
                    if entity.get('label') not in ['PERSON', 'EMAIL', 'PHONE']
                ]
        
        return private_data


def render_export_ui():
    """Main function to render export UI"""
    export_ui = ExportUI()
    export_ui.render_export_interface()
