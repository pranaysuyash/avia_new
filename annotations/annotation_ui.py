"""
Annotation UI components for Streamlit
"""

import streamlit as st
from datetime import datetime
from typing import List, Optional, Dict, Any
from database.models import Annotation, User, Transcript
from .annotation_manager import AnnotationManager
import re


def render_annotation_ui(
    transcript_id: int,
    transcript_content: str,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render the main annotation interface"""
    
    # Handle edit transcript dialog
    if st.session_state.get('show_edit_transcript', False):
        from database.models import Transcript, get_db_session
        from versioning import VersionManager, render_edit_transcript_dialog
        
        session = get_db_session()
        transcript = session.query(Transcript).filter_by(id=transcript_id).first()
        
        if transcript:
            version_manager = VersionManager(session)
            render_edit_transcript_dialog(transcript, version_manager, current_user)
        
        if st.button("Close Edit Dialog"):
            st.session_state.show_edit_transcript = False
            st.rerun()
        return
    
    # Create columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Transcript with annotation highlights
        render_annotated_transcript(
            transcript_id,
            transcript_content,
            annotation_manager,
            current_user
        )
    
    with col2:
        # Annotation sidebar
        render_annotation_sidebar(
            transcript_id,
            annotation_manager,
            current_user
        )


def render_annotated_transcript(
    transcript_id: int,
    transcript_content: str,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render transcript with clickable annotation areas"""
    
    st.markdown("### 📄 Transcript")
    
    # Get all annotations for this transcript
    annotations = annotation_manager.get_transcript_annotations(transcript_id)
    
    # Create annotation map
    annotation_map = {}
    for ann in annotations:
        if ann.position_start is not None and ann.position_end is not None:
            for pos in range(ann.position_start, ann.position_end + 1):
                if pos not in annotation_map:
                    annotation_map[pos] = []
                annotation_map[pos].append(ann)
    
    # Display transcript with annotation indicators
    lines = transcript_content.split('\n')
    for i, line in enumerate(lines):
        # Check if this line has annotations
        line_start = sum(len(lines[j]) + 1 for j in range(i))
        line_end = line_start + len(line)
        
        has_annotation = any(
            pos in annotation_map 
            for pos in range(line_start, line_end)
        )
        
        if has_annotation:
            # Highlight annotated lines
            st.markdown(
                f'<div style="background-color: #fff3cd; padding: 5px; '
                f'border-left: 3px solid #ffc107; margin: 2px 0;">{line}</div>',
                unsafe_allow_html=True
            )
        else:
            st.text(line)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Annotation", key="add_annotation_btn"):
            st.session_state.show_annotation_dialog = True
    with col2:
        if st.button("✏️ Edit Transcript", key="edit_transcript_btn"):
            st.session_state.show_edit_transcript = True
    
    # Annotation dialog
    if st.session_state.get('show_annotation_dialog', False):
        render_annotation_dialog(
            transcript_id,
            transcript_content,
            annotation_manager,
            current_user
        )


def render_annotation_dialog(
    transcript_id: int,
    transcript_content: str,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render dialog for creating new annotation"""
    
    with st.form("new_annotation_form"):
        st.markdown("### 💬 New Annotation")
        
        # Text selection (simplified for now)
        selected_text = st.text_area(
            "Highlighted Text (optional)",
            help="Paste the text you want to annotate",
            height=50
        )
        
        # Annotation content
        content = st.text_area(
            "Your Comment",
            placeholder="Add your annotation here... Use @username to mention someone",
            height=100
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", type="primary"):
                if content:
                    # Find position if text is selected
                    position_start = None
                    position_end = None
                    if selected_text:
                        pos = transcript_content.find(selected_text)
                        if pos != -1:
                            position_start = pos
                            position_end = pos + len(selected_text)
                    
                    # Create notification manager
                    from notifications import NotificationManager
                    from database.models import get_db_session
                    notification_session = get_db_session()
                    notification_mgr = NotificationManager(notification_session)
                    
                    # Create annotation with notifications
                    annotation = annotation_manager.create_annotation(
                        transcript_id=transcript_id,
                        user_id=current_user.id,
                        content=content,
                        position_start=position_start,
                        position_end=position_end,
                        highlighted_text=selected_text if selected_text else None,
                        notification_manager=notification_mgr
                    )
                    
                    # Mentions are handled in annotation_manager now
                    
                    st.success("Annotation added!")
                    st.session_state.show_annotation_dialog = False
                    st.rerun()
                else:
                    st.error("Please enter a comment")
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_annotation_dialog = False
                st.rerun()


def render_annotation_sidebar(
    transcript_id: int,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render annotation sidebar with list of all annotations"""
    
    st.markdown("### 💬 Annotations")
    
    # Filter options
    show_resolved = st.checkbox("Show resolved", value=True)
    only_mine = st.checkbox("Only my annotations", value=False)
    
    # Get annotations
    annotations = annotation_manager.get_transcript_annotations(
        transcript_id,
        only_unresolved=not show_resolved
    )
    
    # Filter by user if requested
    if only_mine:
        annotations = [a for a in annotations if a.user_id == current_user.id]
    
    # Get stats
    stats = annotation_manager.get_annotation_stats(transcript_id)
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", stats['total_annotations'])
    with col2:
        st.metric("Resolved", stats['resolved_count'])
    with col3:
        st.metric("Users", stats['unique_users'])
    
    st.divider()
    
    # Display annotations
    if annotations:
        for ann in annotations:
            if not ann.parent_id:  # Only show top-level annotations
                render_annotation_thread(ann, annotation_manager, current_user)
    else:
        st.info("No annotations yet. Be the first to add one!")
    
    # Export options
    st.divider()
    st.markdown("### 📤 Export")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Markdown", key="export_md"):
            md_content = annotation_manager.export_annotations(
                transcript_id, format='markdown'
            )
            st.download_button(
                "Download Markdown",
                md_content,
                "annotations.md",
                "text/markdown"
            )
    
    with col2:
        if st.button("📊 JSON", key="export_json"):
            json_content = annotation_manager.export_annotations(
                transcript_id, format='json'
            )
            st.download_button(
                "Download JSON",
                json_content,
                "annotations.json",
                "application/json"
            )


def render_annotation_thread(
    annotation: Annotation,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render a single annotation thread"""
    
    with st.container():
        # Annotation header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{annotation.user.username}**")
            st.caption(annotation.created_at.strftime("%Y-%m-%d %H:%M"))
        with col2:
            if annotation.is_resolved:
                st.success("✓ Resolved")
        
        # Highlighted text if any
        if annotation.highlighted_text:
            st.markdown(
                f'<blockquote style="background-color: #f8f9fa; '
                f'border-left: 3px solid #dee2e6; padding: 10px; '
                f'margin: 10px 0;">{annotation.highlighted_text}</blockquote>',
                unsafe_allow_html=True
            )
        
        # Annotation content
        st.markdown(annotation.content)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💬", key=f"reply_{annotation.id}", help="Reply"):
                st.session_state[f'show_reply_{annotation.id}'] = True
        
        with col2:
            if annotation.user_id == current_user.id:
                if st.button("✏️", key=f"edit_{annotation.id}", help="Edit"):
                    st.session_state[f'show_edit_{annotation.id}'] = True
        
        with col3:
            if not annotation.is_resolved:
                if st.button("✓", key=f"resolve_{annotation.id}", help="Resolve"):
                    annotation_manager.resolve_annotation(
                        annotation.id, current_user.id
                    )
                    st.rerun()
            else:
                if st.button("↩", key=f"unresolve_{annotation.id}", help="Reopen"):
                    annotation_manager.unresolve_annotation(
                        annotation.id, current_user.id
                    )
                    st.rerun()
        
        with col4:
            if annotation.user_id == current_user.id:
                if st.button("🗑️", key=f"delete_{annotation.id}", help="Delete"):
                    if st.session_state.get(f'confirm_delete_{annotation.id}', False):
                        annotation_manager.delete_annotation(
                            annotation.id, current_user.id
                        )
                        st.rerun()
                    else:
                        st.session_state[f'confirm_delete_{annotation.id}'] = True
                        st.warning("Click again to confirm deletion")
        
        # Reply form
        if st.session_state.get(f'show_reply_{annotation.id}', False):
            render_reply_form(annotation, annotation_manager, current_user)
        
        # Edit form
        if st.session_state.get(f'show_edit_{annotation.id}', False):
            render_edit_form(annotation, annotation_manager, current_user)
        
        # Show replies
        if annotation.replies:
            with st.container():
                st.markdown("---")
                for reply in annotation.replies:
                    render_annotation_reply(reply, annotation_manager, current_user)
        
        st.markdown("---")


def render_annotation_reply(
    reply: Annotation,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render a reply to an annotation"""
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"↳ **{reply.user.username}**: {reply.content}")
        st.caption(reply.created_at.strftime("%Y-%m-%d %H:%M"))
    with col2:
        if reply.user_id == current_user.id:
            if st.button("🗑️", key=f"delete_reply_{reply.id}", help="Delete"):
                annotation_manager.delete_annotation(reply.id, current_user.id)
                st.rerun()


def render_reply_form(
    parent_annotation: Annotation,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render form for replying to an annotation"""
    
    with st.form(f"reply_form_{parent_annotation.id}"):
        reply_content = st.text_area(
            "Your Reply",
            placeholder="Type your reply...",
            height=80,
            key=f"reply_content_{parent_annotation.id}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Send"):
                if reply_content:
                    # Create notification manager
                    from notifications import NotificationManager
                    from database.models import get_db_session
                    notification_session = get_db_session()
                    notification_mgr = NotificationManager(notification_session)
                    
                    annotation_manager.create_annotation(
                        transcript_id=parent_annotation.transcript_id,
                        user_id=current_user.id,
                        content=reply_content,
                        parent_id=parent_annotation.id,
                        notification_manager=notification_mgr
                    )
                    st.session_state[f'show_reply_{parent_annotation.id}'] = False
                    st.rerun()
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state[f'show_reply_{parent_annotation.id}'] = False
                st.rerun()


def render_edit_form(
    annotation: Annotation,
    annotation_manager: AnnotationManager,
    current_user: User
) -> None:
    """Render form for editing an annotation"""
    
    with st.form(f"edit_form_{annotation.id}"):
        edited_content = st.text_area(
            "Edit Comment",
            value=annotation.content,
            height=100,
            key=f"edit_content_{annotation.id}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save"):
                annotation_manager.update_annotation(
                    annotation.id,
                    current_user.id,
                    content=edited_content
                )
                st.session_state[f'show_edit_{annotation.id}'] = False
                st.rerun()
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state[f'show_edit_{annotation.id}'] = False
                st.rerun()


def render_annotation_input(
    transcript_id: int,
    annotation_manager: AnnotationManager,
    current_user: User,
    selected_text: Optional[str] = None,
    position_start: Optional[int] = None,
    position_end: Optional[int] = None
) -> None:
    """Render a simple annotation input form"""
    
    with st.form("quick_annotation"):
        content = st.text_input(
            "Add a quick annotation",
            placeholder="Type your comment and press Enter..."
        )
        
        if st.form_submit_button("Add") and content:
            annotation_manager.create_annotation(
                transcript_id=transcript_id,
                user_id=current_user.id,
                content=content,
                position_start=position_start,
                position_end=position_end,
                highlighted_text=selected_text
            )
            st.success("Annotation added!")
            st.rerun()