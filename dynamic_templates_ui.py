"""
Dynamic Output Templates UI Components
Streamlit interface for template management and content formatting
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import tempfile
import os
from pathlib import Path

from dynamic_output_templates import (
    TemplateEngine, SmartFormatter, TemplateManager,
    ContentMetadata, TranscriptSegment, ActionItem, KeyPoint, FormattedOutput
)

class DynamicTemplatesUI:
    """Streamlit UI for dynamic output templates"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'selected_template' not in st.session_state:
            st.session_state.selected_template = None
        if 'formatted_outputs' not in st.session_state:
            st.session_state.formatted_outputs = []
        if 'custom_templates' not in st.session_state:
            st.session_state.custom_templates = {}
    
    def render_main_interface(self):
        """Render the main templates interface"""
        st.header("📄 Dynamic Output Templates & Formatting")
        st.markdown("Create professional, customizable outputs from your transcriptions")
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Quick Format", 
            "📋 Template Gallery", 
            "🛠️ Custom Templates",
            "📊 Batch Processing",
            "📁 Output Manager"
        ])
        
        with tab1:
            self.render_quick_format_tab()
        
        with tab2:
            self.render_template_gallery_tab()
        
        with tab3:
            self.render_custom_templates_tab()
        
        with tab4:
            self.render_batch_processing_tab()
        
        with tab5:
            self.render_output_manager_tab()
    
    def render_quick_format_tab(self):
        """Render quick format interface"""
        st.subheader("🎯 Quick Format")
        st.markdown("Quickly format your content with smart template selection")
        
        # Content input section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Content Input")
            
            # Sample data option
            use_sample = st.checkbox("Use sample data for demo", value=True)
            
            if use_sample:
                content_data = self.get_sample_data()
                st.info("Using sample meeting data for demonstration")
            else:
                content_data = self.get_user_content_input()
        
        with col2:
            st.markdown("### Format Options")
            
            # Content type selection
            content_type = st.selectbox(
                "Content Type",
                ["auto-detect", "meeting", "interview", "lecture", "podcast", "general"],
                help="Select content type or let the system auto-detect"
            )
            
            # Output format
            output_format = st.selectbox(
                "Output Format",
                ["html", "markdown", "text"],
                help="Choose the output format"
            )
            
            # Template selection
            available_templates = self.template_manager.template_engine.get_available_templates()
            template_options = [t['name'] for t in available_templates if t['format'] == output_format]
            
            if template_options:
                selected_template = st.selectbox(
                    "Template",
                    ["auto-select"] + template_options,
                    help="Choose a specific template or let the system auto-select"
                )
            else:
                st.warning(f"No templates available for {output_format} format")
                selected_template = "auto-select"
        
        # Format button
        if st.button("🚀 Format Content", type="primary", use_container_width=True):
            if content_data:
                self.process_quick_format(
                    content_data, 
                    content_type, 
                    output_format, 
                    selected_template
                )
            else:
                st.error("Please provide content data")
    
    def render_template_gallery_tab(self):
        """Render template gallery"""
        st.subheader("📋 Template Gallery")
        st.markdown("Browse and preview available templates")
        
        # Get available templates
        templates = self.template_manager.template_engine.get_available_templates()
        
        if not templates:
            st.info("No templates available")
            return
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            format_filter = st.selectbox(
                "Filter by Format",
                ["all"] + list(set(t['format'] for t in templates))
            )
        
        with col2:
            search_term = st.text_input("Search templates", placeholder="Enter search term...")
        
        with col3:
            sort_by = st.selectbox("Sort by", ["name", "format"])
        
        # Filter templates
        filtered_templates = templates
        if format_filter != "all":
            filtered_templates = [t for t in filtered_templates if t['format'] == format_filter]
        
        if search_term:
            filtered_templates = [
                t for t in filtered_templates 
                if search_term.lower() in t['name'].lower() or 
                   search_term.lower() in t['description'].lower()
            ]
        
        # Sort templates
        filtered_templates.sort(key=lambda x: x[sort_by])
        
        # Display templates in grid
        cols = st.columns(2)
        for i, template in enumerate(filtered_templates):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"### {template['name']}")
                    st.markdown(f"**Format:** {template['format'].upper()}")
                    st.markdown(f"**Description:** {template['description']}")
                    
                    col_preview, col_use = st.columns([1, 1])
                    
                    with col_preview:
                        if st.button(f"👁️ Preview", key=f"preview_{template['name']}"):
                            self.show_template_preview(template['file'])
                    
                    with col_use:
                        if st.button(f"✨ Use Template", key=f"use_{template['name']}"):
                            st.session_state.selected_template = template['file']
                            st.success(f"Selected template: {template['name']}")
                    
                    st.divider()
    
    def render_custom_templates_tab(self):
        """Render custom template creation interface"""
        st.subheader("🛠️ Custom Templates")
        st.markdown("Create and manage your own templates")
        
        # Template creation form
        with st.expander("➕ Create New Template", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                template_name = st.text_input(
                    "Template Name",
                    placeholder="my-custom-template"
                )
                
                template_format = st.selectbox(
                    "Format",
                    ["html", "markdown", "text"]
                )
                
                template_description = st.text_area(
                    "Description",
                    placeholder="Describe what this template is for..."
                )
            
            with col2:
                st.markdown("### Available Variables")
                st.code("""
# Metadata
{{ metadata.title }}
{{ metadata.content_type }}
{{ metadata.duration }}
{{ metadata.speakers }}
{{ metadata.date_created }}
{{ metadata.summary }}

# Content
{{ transcript_segments }}
{{ action_items }}
{{ key_points }}
{{ generated_at }}

# Computed
{{ total_duration }}
{{ speakers_list }}
{{ word_count }}
                """, language="jinja2")
            
            # Template content editor
            st.markdown("### Template Content")
            template_content = st.text_area(
                "Template Content (Jinja2 syntax)",
                height=300,
                placeholder="Enter your template content using Jinja2 syntax...",
                help="Use Jinja2 template syntax with the variables shown above"
            )
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Validate Template"):
                    if template_content:
                        validation = self.template_manager.validate_template(template_content)
                        if validation['valid']:
                            st.success("✅ Template is valid!")
                        else:
                            st.error(f"❌ {validation['message']}")
                    else:
                        st.warning("Please enter template content")
            
            with col2:
                if st.button("👁️ Preview Template"):
                    if template_content and template_name:
                        self.preview_custom_template(template_content, template_name)
                    else:
                        st.warning("Please enter template name and content")
            
            with col3:
                if st.button("💾 Save Template", type="primary"):
                    if template_name and template_content:
                        success = self.template_manager.template_engine.create_custom_template(
                            name=template_name,
                            content=template_content,
                            description=template_description,
                            format_type=template_format
                        )
                        
                        if success:
                            st.success(f"✅ Template '{template_name}' saved successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save template")
                    else:
                        st.warning("Please enter template name and content")
        
        # Existing custom templates
        self.render_existing_custom_templates()
    
    def render_batch_processing_tab(self):
        """Render batch processing interface"""
        st.subheader("📊 Batch Processing")
        st.markdown("Process multiple transcripts with the same template")
        
        # File upload for batch processing
        uploaded_files = st.file_uploader(
            "Upload Transcript Files",
            type=['json', 'txt'],
            accept_multiple_files=True,
            help="Upload multiple transcript files for batch processing"
        )
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} files")
            
            # Template selection for batch
            templates = self.template_manager.template_engine.get_available_templates()
            template_names = [t['name'] for t in templates]
            
            selected_template = st.selectbox(
                "Select Template for Batch Processing",
                template_names
            )
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                output_format = st.selectbox(
                    "Output Format",
                    ["html", "markdown", "text"]
                )
            
            with col2:
                zip_output = st.checkbox(
                    "Create ZIP archive",
                    value=True,
                    help="Package all outputs into a single ZIP file"
                )
            
            # Process batch
            if st.button("🚀 Process Batch", type="primary"):
                self.process_batch_files(uploaded_files, selected_template, output_format, zip_output)
        
        else:
            st.info("Upload transcript files to begin batch processing")
    
    def render_output_manager_tab(self):
        """Render output management interface"""
        st.subheader("📁 Output Manager")
        st.markdown("Manage your formatted outputs")
        
        if st.session_state.formatted_outputs:
            st.markdown(f"**Total outputs:** {len(st.session_state.formatted_outputs)}")
            
            # Filter and sort options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                format_filter = st.selectbox(
                    "Filter by Format",
                    ["all"] + list(set(output.format_type for output in st.session_state.formatted_outputs))
                )
            
            with col2:
                template_filter = st.selectbox(
                    "Filter by Template",
                    ["all"] + list(set(output.template_name for output in st.session_state.formatted_outputs))
                )
            
            with col3:
                sort_order = st.selectbox("Sort by", ["newest", "oldest", "name"])
            
            # Display outputs
            filtered_outputs = st.session_state.formatted_outputs
            
            if format_filter != "all":
                filtered_outputs = [o for o in filtered_outputs if o.format_type == format_filter]
            
            if template_filter != "all":
                filtered_outputs = [o for o in filtered_outputs if o.template_name == template_filter]
            
            # Sort outputs
            if sort_order == "newest":
                filtered_outputs.sort(key=lambda x: x.generated_at, reverse=True)
            elif sort_order == "oldest":
                filtered_outputs.sort(key=lambda x: x.generated_at)
            else:
                filtered_outputs.sort(key=lambda x: x.metadata.get('title', ''))
            
            for i, output in enumerate(filtered_outputs):
                with st.expander(f"📄 {output.metadata.get('title', f'Output {i+1}')} ({output.format_type.upper()})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Template:** {output.template_name}")
                        st.markdown(f"**Generated:** {output.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.markdown(f"**Format:** {output.format_type.upper()}")
                        
                        # Preview content
                        if output.format_type == "html":
                            st.components.v1.html(output.content, height=400, scrolling=True)
                        else:
                            st.text_area("Content Preview", output.content, height=200)
                    
                    with col2:
                        # Action buttons
                        if st.button(f"📋 Copy", key=f"copy_{i}"):
                            st.code(output.content)
                        
                        if st.button(f"💾 Download", key=f"download_{i}"):
                            self.create_download_link(output, i)
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                            st.session_state.formatted_outputs.remove(output)
                            st.rerun()
            
            # Bulk actions
            st.markdown("### Bulk Actions")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📦 Download All as ZIP"):
                    self.create_bulk_download()
            
            with col2:
                if st.button("🗑️ Clear All Outputs"):
                    st.session_state.formatted_outputs = []
                    st.success("All outputs cleared")
                    st.rerun()
        
        else:
            st.info("No formatted outputs yet. Use the Quick Format tab to create some!")
    
    def get_sample_data(self) -> Dict[str, Any]:
        """Get sample data for demonstration"""
        return {
            'metadata': ContentMetadata(
                title="Weekly Team Meeting - Project Alpha",
                content_type="meeting",
                duration=2700,  # 45 minutes
                speakers=["Sarah Johnson", "Mike Chen", "Lisa Rodriguez"],
                date_created=datetime.now(),
                summary="Weekly team meeting discussing Project Alpha progress, budget concerns, and upcoming milestones.",
                key_topics=["Budget Review", "Timeline Updates", "Resource Allocation"]
            ),
            'transcript_segments': [
                TranscriptSegment(0, 30, "Sarah Johnson", "Good morning everyone. Let's start with our weekly Project Alpha review."),
                TranscriptSegment(30, 75, "Mike Chen", "Thanks Sarah. I want to highlight that we're currently 15% over budget due to the additional security requirements."),
                TranscriptSegment(75, 120, "Lisa Rodriguez", "That's concerning. We need to identify cost-saving measures immediately."),
                TranscriptSegment(120, 180, "Sarah Johnson", "I agree. Mike, can you prepare a detailed budget analysis by Friday? We need to present options to the steering committee."),
                TranscriptSegment(180, 240, "Mike Chen", "Absolutely. I'll have that ready by Thursday actually, so we can review it before the presentation."),
                TranscriptSegment(240, 300, "Lisa Rodriguez", "Great. Also, I wanted to mention that the new team member, Alex, will be starting next Monday."),
                TranscriptSegment(300, 360, "Sarah Johnson", "Perfect timing. Alex's expertise in cloud architecture will be crucial for the next phase.")
            ]
        }
    
    def get_user_content_input(self) -> Optional[Dict[str, Any]]:
        """Get content input from user"""
        st.markdown("### Manual Content Input")
        
        # Metadata input
        with st.expander("Content Metadata", expanded=True):
            title = st.text_input("Title", placeholder="Enter content title...")
            content_type = st.selectbox("Content Type", ["meeting", "interview", "lecture", "podcast", "general"])
            
            col1, col2 = st.columns(2)
            with col1:
                duration = st.number_input("Duration (seconds)", min_value=0, value=0)
            with col2:
                speakers_input = st.text_input("Speakers (comma-separated)", placeholder="John Doe, Jane Smith")
            
            summary = st.text_area("Summary (optional)", placeholder="Brief summary of the content...")
        
        # Transcript input
        st.markdown("### Transcript Content")
        transcript_input = st.text_area(
            "Transcript",
            height=200,
            placeholder="Enter transcript content...\nFormat: [Speaker]: Text\nExample:\nJohn Doe: Hello everyone\nJane Smith: Thanks for joining"
        )
        
        if title and transcript_input:
            # Parse transcript
            segments = self.parse_transcript_input(transcript_input)
            speakers = [s.strip() for s in speakers_input.split(',')] if speakers_input else []
            
            return {
                'metadata': ContentMetadata(
                    title=title,
                    content_type=content_type,
                    duration=duration if duration > 0 else None,
                    speakers=speakers,
                    date_created=datetime.now(),
                    summary=summary if summary else None
                ),
                'transcript_segments': segments
            }
        
        return None
    
    def parse_transcript_input(self, transcript_text: str) -> List[TranscriptSegment]:
        """Parse user transcript input into segments"""
        segments = []
        lines = transcript_text.strip().split('\n')
        current_time = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse speaker and text
            if ':' in line:
                parts = line.split(':', 1)
                speaker = parts[0].strip()
                text = parts[1].strip()
                
                # Estimate duration based on text length (rough approximation)
                estimated_duration = max(5, len(text.split()) * 0.5)
                
                segments.append(TranscriptSegment(
                    start_time=current_time,
                    end_time=current_time + estimated_duration,
                    speaker=speaker,
                    text=text
                ))
                
                current_time += estimated_duration
            else:
                # No speaker identified, use previous speaker or "Unknown"
                speaker = segments[-1].speaker if segments else "Unknown Speaker"
                estimated_duration = max(5, len(line.split()) * 0.5)
                
                segments.append(TranscriptSegment(
                    start_time=current_time,
                    end_time=current_time + estimated_duration,
                    speaker=speaker,
                    text=line
                ))
                
                current_time += estimated_duration
        
        return segments
    
    def process_quick_format(
        self, 
        content_data: Dict[str, Any], 
        content_type: str, 
        output_format: str, 
        selected_template: str
    ):
        """Process quick format request"""
        with st.spinner("Formatting content..."):
            try:
                metadata = content_data['metadata']
                transcript_segments = content_data['transcript_segments']
                
                # Update content type if not auto-detect
                if content_type != "auto-detect":
                    metadata.content_type = content_type
                
                # Format content
                if selected_template == "auto-select":
                    # Use smart formatter
                    result = self.template_manager.smart_formatter.auto_format(
                        transcript_segments=transcript_segments,
                        metadata=metadata,
                        preferred_format=output_format
                    )
                else:
                    # Use specific template
                    template_file = f"{selected_template}.{output_format}"
                    
                    # Extract action items and key points
                    action_items = self.template_manager.smart_formatter.extract_action_items(transcript_segments)
                    key_points = self.template_manager.smart_formatter.extract_key_points(transcript_segments)
                    
                    result = self.template_manager.template_engine.format_content(
                        template_name=template_file,
                        metadata=metadata,
                        transcript_segments=transcript_segments,
                        action_items=action_items,
                        key_points=key_points
                    )
                
                # Store result
                st.session_state.formatted_outputs.append(result)
                
                # Display result
                st.success("✅ Content formatted successfully!")
                
                with st.expander("📄 Formatted Output", expanded=True):
                    if result.format_type == "html":
                        st.components.v1.html(result.content, height=600, scrolling=True)
                    elif result.format_type == "markdown":
                        st.markdown(result.content)
                    else:
                        st.text(result.content)
                
                # Download option
                self.create_download_link(result, len(st.session_state.formatted_outputs) - 1)
                
            except Exception as e:
                st.error(f"❌ Error formatting content: {str(e)}")
    
    def show_template_preview(self, template_file: str):
        """Show template preview"""
        with st.spinner("Generating preview..."):
            try:
                preview_content = self.template_manager.get_template_preview(template_file)
                
                with st.expander(f"👁️ Preview: {template_file}", expanded=True):
                    if template_file.endswith('.html'):
                        st.components.v1.html(preview_content, height=500, scrolling=True)
                    elif template_file.endswith('.md'):
                        st.markdown(preview_content)
                    else:
                        st.text(preview_content)
                        
            except Exception as e:
                st.error(f"Error generating preview: {str(e)}")
    
    def preview_custom_template(self, template_content: str, template_name: str):
        """Preview custom template"""
        with st.spinner("Generating preview..."):
            try:
                # Create temporary template
                temp_template = Template(template_content)
                
                # Use sample data
                sample_data = self.get_sample_data()
                
                # Add computed fields
                context = {
                    'metadata': sample_data['metadata'],
                    'transcript_segments': sample_data['transcript_segments'],
                    'action_items': [
                        ActionItem("Review budget analysis", "Mike Chen", datetime.now() + timedelta(days=2), "high"),
                        ActionItem("Prepare steering committee presentation", "Sarah Johnson", datetime.now() + timedelta(days=3), "high")
                    ],
                    'key_points': [
                        KeyPoint("15% over budget due to security requirements", 45, 1.0),
                        KeyPoint("New team member Alex starting Monday", 240, 0.8)
                    ],
                    'generated_at': datetime.now(),
                    'total_duration': 360,
                    'speakers_list': ["Sarah Johnson", "Mike Chen", "Lisa Rodriguez"],
                    'word_count': 150
                }
                
                preview_content = temp_template.render(**context)
                
                with st.expander(f"👁️ Preview: {template_name}", expanded=True):
                    if template_name.endswith('.html'):
                        st.components.v1.html(preview_content, height=500, scrolling=True)
                    elif template_name.endswith('.md'):
                        st.markdown(preview_content)
                    else:
                        st.text(preview_content)
                        
            except Exception as e:
                st.error(f"Error generating preview: {str(e)}")
    
    def render_existing_custom_templates(self):
        """Render existing custom templates management"""
        st.markdown("### 📚 Your Custom Templates")
        
        # Get custom templates (those with .meta.json files)
        templates_dir = Path(self.template_manager.template_engine.templates_dir)
        custom_templates = []
        
        for meta_file in templates_dir.glob("*.meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                if metadata.get('custom', False):
                    custom_templates.append(metadata)
            except Exception:
                continue
        
        if custom_templates:
            for template in custom_templates:
                with st.expander(f"📄 {template['name']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Description:** {template.get('description', 'No description')}")
                        st.markdown(f"**Format:** {template['format_type'].upper()}")
                        st.markdown(f"**Created:** {template.get('created_at', 'Unknown')}")
                    
                    with col2:
                        if st.button(f"👁️ Preview", key=f"preview_custom_{template['name']}"):
                            template_file = f"{template['name']}.{template['format_type']}"
                            self.show_template_preview(template_file)
                        
                        if st.button(f"📤 Export", key=f"export_{template['name']}"):
                            self.export_custom_template(template['name'], template['format_type'])
                        
                        if st.button(f"🗑️ Delete", key=f"delete_custom_{template['name']}"):
                            self.delete_custom_template(template['name'], template['format_type'])
        else:
            st.info("No custom templates created yet")
    
    def export_custom_template(self, template_name: str, format_type: str):
        """Export custom template"""
        template_content = self.template_manager.export_template(f"{template_name}.{format_type}")
        if template_content:
            st.download_button(
                label=f"📥 Download {template_name}",
                data=template_content,
                file_name=f"{template_name}.{format_type}",
                mime="text/plain"
            )
        else:
            st.error("Failed to export template")
    
    def delete_custom_template(self, template_name: str, format_type: str):
        """Delete custom template"""
        success = self.template_manager.delete_template(f"{template_name}.{format_type}")
        if success:
            st.success(f"✅ Template '{template_name}' deleted successfully!")
            st.rerun()
        else:
            st.error("❌ Failed to delete template")
    
    def process_batch_files(self, uploaded_files, selected_template: str, output_format: str, zip_output: bool):
        """Process multiple files in batch"""
        with st.spinner("Processing batch files..."):
            try:
                results = []
                
                for uploaded_file in uploaded_files:
                    # Parse file content
                    content = uploaded_file.read().decode('utf-8')
                    
                    if uploaded_file.name.endswith('.json'):
                        # JSON format
                        data = json.loads(content)
                        metadata = ContentMetadata(**data.get('metadata', {}))
                        segments = [TranscriptSegment(**seg) for seg in data.get('segments', [])]
                    else:
                        # Text format - parse as simple transcript
                        segments = self.parse_transcript_input(content)
                        metadata = ContentMetadata(
                            title=uploaded_file.name,
                            content_type="general",
                            date_created=datetime.now()
                        )
                    
                    # Format content
                    template_file = f"{selected_template}.{output_format}"
                    action_items = self.template_manager.smart_formatter.extract_action_items(segments)
                    key_points = self.template_manager.smart_formatter.extract_key_points(segments)
                    
                    result = self.template_manager.template_engine.format_content(
                        template_name=template_file,
                        metadata=metadata,
                        transcript_segments=segments,
                        action_items=action_items,
                        key_points=key_points
                    )
                    
                    results.append((uploaded_file.name, result))
                
                # Store results
                st.session_state.formatted_outputs.extend([r[1] for r in results])
                
                st.success(f"✅ Processed {len(results)} files successfully!")
                
                # Show results
                for filename, result in results:
                    with st.expander(f"📄 {filename}"):
                        if result.format_type == "html":
                            st.components.v1.html(result.content, height=300, scrolling=True)
                        elif result.format_type == "markdown":
                            st.markdown(result.content)
                        else:
                            st.text_area("Content", result.content, height=200)
                
                # Create ZIP if requested
                if zip_output and len(results) > 1:
                    self.create_batch_zip(results, output_format)
                    
            except Exception as e:
                st.error(f"❌ Error processing batch files: {str(e)}")
    
    def create_download_link(self, output: FormattedOutput, index: int):
        """Create download link for formatted output"""
        filename = f"{output.metadata.get('title', f'output_{index}')}.{output.format_type}"
        
        # Determine MIME type
        mime_types = {
            'html': 'text/html',
            'markdown': 'text/markdown',
            'text': 'text/plain'
        }
        
        st.download_button(
            label=f"📥 Download {output.format_type.upper()}",
            data=output.content,
            file_name=filename,
            mime=mime_types.get(output.format_type, 'text/plain'),
            key=f"download_btn_{index}"
        )
    
    def create_bulk_download(self):
        """Create bulk download of all outputs"""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, output in enumerate(st.session_state.formatted_outputs):
                filename = f"{output.metadata.get('title', f'output_{i}')}.{output.format_type}"
                zip_file.writestr(filename, output.content)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 Download All as ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"formatted_outputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )
    
    def create_batch_zip(self, results: List, output_format: str):
        """Create ZIP file for batch processing results"""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, result in results:
                output_filename = f"{filename.split('.')[0]}.{output_format}"
                zip_file.writestr(output_filename, result.content)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 Download Batch Results",
            data=zip_buffer.getvalue(),
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )

def main():
    """Main function to run the dynamic templates UI"""
    st.set_page_config(
        page_title="Dynamic Output Templates",
        page_icon="📄",
        layout="wide"
    )
    
    ui = DynamicTemplatesUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()lete_custom_template(self, template_name: str, format_type: str):
        """Delete custom template"""
        try:
            templates_dir = Path(self.template_manager.template_engine.templates_dir)
            template_file = templates_dir / f"{template_name}.{format_type}"
            meta_file = templates_dir / f"{template_name}.meta.json"
            
            if template_file.exists():
                template_file.unlink()
            if meta_file.exists():
                meta_file.unlink()
            
            st.success(f"✅ Template '{template_name}' deleted successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error deleting template: {str(e)}")
    
    def process_batch_files(self, uploaded_files, selected_template: str, output_format: str, zip_output: bool):
        """Process multiple files in batch"""
        with st.spinner(f"Processing {len(uploaded_files)} files..."):
            results = []
            
            for file in uploaded_files:
                try:
                    # Parse file content (simplified - assumes JSON format)
                    content = file.read().decode('utf-8')
                    
                    # For demo, create simple content
                    metadata = ContentMetadata(
                        title=file.name,
                        content_type="general",
                        date_created=datetime.now()
                    )
                    
                    # Simple transcript parsing
                    segments = [
                        TranscriptSegment(0, 30, "Speaker", content[:200])
                    ]
                    
                    # Format content
                    template_file = f"{selected_template}.{output_format}"
                    result = self.template_manager.template_engine.format_content(
                        template_name=template_file,
                        metadata=metadata,
                        transcript_segments=segments
                    )
                    
                    results.append((file.name, result))
                    
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}")
            
            if results:
                st.success(f"✅ Successfully processed {len(results)} files!")
                
                if zip_output:
                    self.create_batch_zip_download(results)
                else:
                    for filename, result in results:
                        st.session_state.formatted_outputs.append(result)
                        
                st.info("Check the Output Manager tab to view and download your results")
    
    def create_download_link(self, output: FormattedOutput, index: int):
        """Create download link for formatted output"""
        filename = f"{output.metadata.get('title', f'output_{index}')}.{output.format_type}"
        
        # Determine MIME type
        mime_types = {
            'html': 'text/html',
            'markdown': 'text/markdown',
            'text': 'text/plain'
        }
        
        st.download_button(
            label=f"📥 Download {output.format_type.upper()}",
            data=output.content,
            file_name=filename,
            mime=mime_types.get(output.format_type, 'text/plain'),
            key=f"download_btn_{index}"
        )
    
    def create_bulk_download(self):
        """Create bulk download of all outputs"""
        if not st.session_state.formatted_outputs:
            st.warning("No outputs to download")
            return
        
        # Create ZIP content
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, output in enumerate(st.session_state.formatted_outputs):
                filename = f"{output.metadata.get('title', f'output_{i}')}.{output.format_type}"
                zip_file.writestr(filename, output.content)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 Download All Outputs (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"formatted_outputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )
    
    def create_batch_zip_download(self, results: List[tuple]):
        """Create ZIP download for batch processing results"""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, result in results:
                output_filename = f"{filename}.{result.format_type}"
                zip_file.writestr(output_filename, result.content)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📦 Download Batch Results (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )

# Main function for standalone testing
def main():
    st.set_page_config(
        page_title="Dynamic Output Templates",
        page_icon="📄",
        layout="wide"
    )
    
    ui = DynamicTemplatesUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()