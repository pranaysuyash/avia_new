"""
Enhanced Export UI Module
Provides quick export functionality directly in the transcript display area
"""

import streamlit as st
import json
import io
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from export_manager import MultimediaExporter, ExportConfig
import logging

logger = logging.getLogger(__name__)


def render_quick_export_buttons(
    transcript: str,
    entities: Optional[Dict[str, Any]] = None,
    summary: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Render quick export buttons right after transcript display
    
    Args:
        transcript: The transcript text
        entities: Extracted entities dictionary
        summary: AI-generated summary (if available)
        metadata: Additional metadata (duration, language, etc.)
    """
    if not transcript:
        return
    
    # Create export data package
    export_data = {
        "transcript": transcript,
        "entities": entities or {},
        "summary": summary or "",
        "metadata": metadata or {},
        "export_date": datetime.now().isoformat()
    }
    
    # Quick export buttons in columns
    st.markdown("### 📥 Quick Export")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Text export
        st.download_button(
            label="📄 TXT",
            data=transcript,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="Download transcript as plain text",
            use_container_width=True
        )
    
    with col2:
        # JSON export
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📊 JSON",
            data=json_data,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download complete data in JSON format",
            use_container_width=True
        )
    
    with col3:
        # CSV export (for segments if available)
        csv_data = create_csv_export(export_data)
        st.download_button(
            label="📈 CSV",
            data=csv_data,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download as CSV (entities and metadata)",
            use_container_width=True
        )
    
    with col4:
        # Markdown export
        md_data = create_markdown_export(export_data)
        st.download_button(
            label="📝 MD",
            data=md_data,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            help="Download as Markdown document",
            use_container_width=True
        )
    
    with col5:
        # Advanced export options
        if st.button("🗂️ More", help="Access advanced export options", use_container_width=True):
            st.session_state.show_advanced_export = True
            st.rerun()


def create_csv_export(data: Dict[str, Any]) -> str:
    """Create CSV export from transcript data"""
    rows = []
    
    # Add metadata rows
    rows.append(["Metadata", "Value"])
    rows.append(["Export Date", data.get("export_date", "")])
    if "metadata" in data:
        for key, value in data["metadata"].items():
            rows.append([key.title(), str(value)])
    
    rows.append([])  # Empty row
    rows.append(["Entity Type", "Entity", "Count"])
    
    # Add entities
    if "entities" in data and data["entities"]:
        for entity_type, entity_list in data["entities"].items():
            entity_counts = {}
            for entity in entity_list:
                if isinstance(entity, dict):
                    text = entity.get("text", entity.get("name", str(entity)))
                else:
                    text = str(entity)
                entity_counts[text] = entity_counts.get(text, 0) + 1
            
            for entity_text, count in entity_counts.items():
                rows.append([entity_type, entity_text, count])
    
    # Convert to CSV
    output = io.StringIO()
    for row in rows:
        output.write(",".join([f'"{str(cell)}"' for cell in row]) + "\n")
    
    return output.getvalue()


def create_markdown_export(data: Dict[str, Any]) -> str:
    """Create Markdown export from transcript data"""
    lines = []
    
    # Title
    lines.append("# Transcript Export")
    lines.append("")
    lines.append(f"*Exported on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
    lines.append("")
    
    # Metadata
    if "metadata" in data and data["metadata"]:
        lines.append("## Metadata")
        lines.append("")
        for key, value in data["metadata"].items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        lines.append("")
    
    # Summary
    if data.get("summary"):
        lines.append("## Summary")
        lines.append("")
        lines.append(data["summary"])
        lines.append("")
    
    # Transcript
    lines.append("## Transcript")
    lines.append("")
    lines.append(data.get("transcript", "No transcript available"))
    lines.append("")
    
    # Entities
    if data.get("entities"):
        lines.append("## Extracted Entities")
        lines.append("")
        for entity_type, entity_list in data["entities"].items():
            lines.append(f"### {entity_type}")
            lines.append("")
            # Deduplicate entities
            unique_entities = set()
            for entity in entity_list:
                if isinstance(entity, dict):
                    text = entity.get("text", entity.get("name", str(entity)))
                else:
                    text = str(entity)
                unique_entities.add(text)
            
            for entity_text in sorted(unique_entities):
                lines.append(f"- {entity_text}")
            lines.append("")
    
    return "\n".join(lines)


def render_advanced_export_modal():
    """Render advanced export options in a modal-like container"""
    if not st.session_state.get("show_advanced_export", False):
        return
    
    # Create a container for the modal
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown("### 🗂️ Advanced Export Options")
            
            # Export format selection
            export_format = st.selectbox(
                "Select Export Format",
                ["PDF", "DOCX", "XLSX", "HTML", "XML", "All Formats (ZIP)"],
                help="Choose the format for your export"
            )
            
            # Export options
            st.markdown("#### Options")
            include_timestamps = st.checkbox("Include timestamps", value=True)
            include_speakers = st.checkbox("Include speaker labels", value=True)
            include_confidence = st.checkbox("Include confidence scores", value=False)
            include_visualizations = st.checkbox("Include visualizations", value=False)
            
            # Export button
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Export", type="primary", use_container_width=True):
                    # Trigger export
                    handle_advanced_export(
                        export_format,
                        include_timestamps,
                        include_speakers,
                        include_confidence,
                        include_visualizations
                    )
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_advanced_export = False
                    st.rerun()


def handle_advanced_export(
    format_type: str,
    include_timestamps: bool,
    include_speakers: bool,
    include_confidence: bool,
    include_visualizations: bool
):
    """Handle advanced export with selected options"""
    try:
        # Get data from session state
        transcript_data = {
            "transcript": st.session_state.get("transcript", ""),
            "entities": st.session_state.get("entities", {}),
            "summary": st.session_state.get("summary", ""),
            "title": f"Transcript Export - {datetime.now().strftime('%Y-%m-%d')}",
            "metadata": {
                "duration": st.session_state.get("duration", 0),
                "language": st.session_state.get("language", "en"),
                "confidence": st.session_state.get("confidence", 0)
            }
        }
        
        # Create export config
        config = ExportConfig(
            format=format_type.lower().replace(" ", "_"),
            include_timestamps=include_timestamps,
            include_speaker_info=include_speakers,
            include_confidence=include_confidence,
            include_visualizations=include_visualizations
        )
        
        # Create exporter
        exporter = MultimediaExporter()
        
        # Handle different export types
        if "ZIP" in format_type:
            # Export all formats
            formats = ["pdf", "docx", "json", "csv", "html", "md"]
            export_path = exporter.create_export_package(
                transcript_data,
                formats,
                include_media=False
            )
            
            # Provide download
            with open(export_path, "rb") as f:
                st.download_button(
                    label="📦 Download Export Package",
                    data=f.read(),
                    file_name=f"transcript_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
        else:
            # Single format export
            export_path = exporter.export_transcript(transcript_data, config)
            
            # Provide download
            with open(export_path, "rb") as f:
                mime_types = {
                    "pdf": "application/pdf",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "html": "text/html",
                    "xml": "application/xml"
                }
                
                st.download_button(
                    label=f"📥 Download {format_type}",
                    data=f.read(),
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{config.format}",
                    mime=mime_types.get(config.format, "application/octet-stream")
                )
        
        st.success(f"✅ Export completed successfully!")
        st.session_state.show_advanced_export = False
        
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")
        logger.error(f"Export error: {str(e)}")


def render_inline_search(transcript: str):
    """
    Render inline search functionality for the transcript
    
    Args:
        transcript: The transcript text to search in
    """
    if not transcript:
        return transcript
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "🔍 Search in transcript",
            placeholder="Type to search...",
            key="transcript_search",
            label_visibility="collapsed"
        )
    
    with col2:
        case_sensitive = st.checkbox("Case sensitive", key="search_case_sensitive")
    
    if search_term:
        # Find and highlight matches
        highlighted_transcript = highlight_search_matches(
            transcript, 
            search_term, 
            case_sensitive
        )
        
        # Count matches
        if case_sensitive:
            match_count = transcript.count(search_term)
        else:
            match_count = transcript.lower().count(search_term.lower())
        
        if match_count > 0:
            st.success(f"Found {match_count} match{'es' if match_count > 1 else ''}")
            return highlighted_transcript
        else:
            st.warning("No matches found")
    
    return transcript


def highlight_search_matches(text: str, search_term: str, case_sensitive: bool = False) -> str:
    """
    Highlight search matches in text with HTML markup
    
    Args:
        text: The text to search in
        search_term: The search term
        case_sensitive: Whether to perform case-sensitive search
        
    Returns:
        HTML string with highlighted matches
    """
    if not search_term:
        return text
    
    # Escape HTML special characters in the text
    import html
    text = html.escape(text)
    search_term_escaped = html.escape(search_term)
    
    # Replace matches with highlighted version
    if case_sensitive:
        highlighted = text.replace(
            search_term_escaped,
            f'<mark style="background-color: #ffeb3b; padding: 2px;">{search_term_escaped}</mark>'
        )
    else:
        # Case-insensitive replacement
        import re
        pattern = re.compile(re.escape(search_term_escaped), re.IGNORECASE)
        highlighted = pattern.sub(
            lambda m: f'<mark style="background-color: #ffeb3b; padding: 2px;">{m.group()}</mark>',
            text
        )
    
    # Preserve line breaks
    highlighted = highlighted.replace('\n', '<br>')
    
    return highlighted