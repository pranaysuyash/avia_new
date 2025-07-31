"""
Version control UI components for Streamlit
"""

import streamlit as st
from datetime import datetime
from typing import List, Optional, Dict, Any
from database.models import Transcript, TranscriptVersion, User
from .version_manager import VersionManager
import difflib


def render_version_history(
    transcript_id: int,
    version_manager: VersionManager,
    current_user: User
) -> None:
    """Render version history for a transcript"""
    
    st.markdown("### 📚 Version History")
    
    # Get version stats
    stats = version_manager.get_version_stats(transcript_id)
    
    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Versions", stats['total_versions'])
    with col2:
        st.metric("Contributors", len(stats['contributors']))
    with col3:
        if stats['last_modified']:
            st.metric("Last Modified", stats['last_modified'].strftime("%Y-%m-%d %H:%M"))
    with col4:
        if stats['most_active_contributor']:
            st.metric("Top Contributor", stats['most_active_contributor'])
    
    st.divider()
    
    # Search versions
    search_query = st.text_input("🔍 Search versions", placeholder="Search by summary or content...")
    
    # Get versions
    if search_query:
        versions = version_manager.search_versions(transcript_id, search_query)
    else:
        versions = version_manager.get_versions(transcript_id)
    
    if not versions:
        st.info("No versions found.")
        return
    
    # Version list
    for version in versions:
        with st.expander(
            f"v{version.version_number} - {version.change_summary} "
            f"({version.changed_by.username}, {version.created_at.strftime('%Y-%m-%d %H:%M')})"
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Author:** {version.changed_by.username}")
                st.write(f"**Date:** {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Summary:** {version.change_summary}")
                
                # Show content preview
                preview_length = 200
                if len(version.content) > preview_length:
                    st.text(version.content[:preview_length] + "...")
                else:
                    st.text(version.content)
            
            with col2:
                # Action buttons
                if st.button(f"View Full", key=f"view_v{version.version_number}"):
                    st.session_state.viewing_version = version.version_number
                    st.rerun()
                
                if st.button(f"Compare", key=f"compare_v{version.version_number}"):
                    st.session_state.compare_version = version.version_number
                    st.rerun()
                
                if version.version_number > 1:
                    if st.button(f"Restore", key=f"restore_v{version.version_number}"):
                        st.session_state.restore_version = version.version_number
                        st.rerun()
    
    # Handle version viewing
    if hasattr(st.session_state, 'viewing_version'):
        render_version_view(
            transcript_id,
            st.session_state.viewing_version,
            version_manager
        )
        if st.button("Close Version View"):
            del st.session_state.viewing_version
            st.rerun()
    
    # Handle version comparison
    if hasattr(st.session_state, 'compare_version'):
        render_version_comparison_dialog(
            transcript_id,
            version_manager,
            st.session_state.compare_version
        )
    
    # Handle version restore
    if hasattr(st.session_state, 'restore_version'):
        render_version_restore_dialog(
            transcript_id,
            st.session_state.restore_version,
            version_manager,
            current_user
        )


def render_version_view(
    transcript_id: int,
    version_number: int,
    version_manager: VersionManager
) -> None:
    """Render full view of a specific version"""
    
    version = version_manager.get_version(transcript_id, version_number)
    if not version:
        st.error("Version not found")
        return
    
    st.markdown("---")
    st.subheader(f"Version {version.version_number}")
    
    # Version info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Author:** {version.changed_by.username}")
    with col2:
        st.write(f"**Date:** {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        st.write(f"**Words:** {len(version.content.split())}")
    
    st.write(f"**Change Summary:** {version.change_summary}")
    
    # Full content
    st.text_area("Content", version.content, height=400, disabled=True)
    
    # Entities if available
    if version.entities:
        st.subheader("Entities")
        st.json(version.entities)


def render_version_comparison(
    transcript_id: int,
    version1_number: int,
    version2_number: int,
    version_manager: VersionManager
) -> None:
    """Render comparison between two versions"""
    
    st.markdown("### 📊 Version Comparison")
    
    try:
        diff_data = version_manager.get_diff(
            transcript_id,
            version1_number,
            version2_number
        )
    except ValueError as e:
        st.error(str(e))
        return
    
    # Display version info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Version {version1_number}**")
        st.write(f"Author: {diff_data['version1'].changed_by.username}")
        st.write(f"Date: {diff_data['version1'].created_at.strftime('%Y-%m-%d %H:%M')}")
    with col2:
        st.write(f"**Version {version2_number}**")
        st.write(f"Author: {diff_data['version2'].changed_by.username}")
        st.write(f"Date: {diff_data['version2'].created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Display statistics
    st.divider()
    stats = diff_data['stats']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lines Added", f"+{stats['lines_added']}", delta_color="normal")
    with col2:
        st.metric("Lines Removed", f"-{stats['lines_removed']}", delta_color="inverse")
    with col3:
        st.metric("Total Changes", stats['lines_added'] + stats['lines_removed'])
    
    # Display diff
    st.divider()
    st.subheader("Content Changes")
    
    # Choose diff view
    diff_view = st.radio(
        "View mode",
        ["Unified", "Side by Side", "Inline"],
        horizontal=True
    )
    
    if diff_view == "Unified":
        # Unified diff
        diff_text = '\n'.join(diff_data['text_diff'])
        if diff_text:
            st.code(diff_text, language='diff')
        else:
            st.info("No changes in content")
    
    elif diff_view == "Side by Side":
        # Side by side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Version " + str(version1_number) + "**")
            content1 = diff_data['version1'].content
            st.text_area("", content1, height=400, disabled=True, key="v1_content")
        
        with col2:
            st.write("**Version " + str(version2_number) + "**")
            content2 = diff_data['version2'].content
            st.text_area("", content2, height=400, disabled=True, key="v2_content")
    
    else:  # Inline
        # Inline diff with color coding
        for op, line in diff_data['inline_diff']:
            if op == 'equal':
                st.text(f"  {line}")
            elif op == 'delete':
                st.markdown(f'<div style="background-color: #ffdddd; padding: 2px;">- {line}</div>', 
                          unsafe_allow_html=True)
            elif op == 'insert':
                st.markdown(f'<div style="background-color: #ddffdd; padding: 2px;">+ {line}</div>', 
                          unsafe_allow_html=True)
    
    # Entity changes
    if any(diff_data['entity_diff'].values()):
        st.divider()
        st.subheader("Entity Changes")
        
        if diff_data['entity_diff']['added']:
            st.write("**Added Entities:**")
            for key, value in diff_data['entity_diff']['added'].items():
                st.write(f"- {key}: {', '.join(value) if isinstance(value, list) else value}")
        
        if diff_data['entity_diff']['removed']:
            st.write("**Removed Entities:**")
            for key, value in diff_data['entity_diff']['removed'].items():
                st.write(f"- {key}: {', '.join(value) if isinstance(value, list) else value}")
        
        if diff_data['entity_diff']['modified']:
            st.write("**Modified Entities:**")
            for key, changes in diff_data['entity_diff']['modified'].items():
                st.write(f"- {key}:")
                st.write(f"  Old: {', '.join(changes['old']) if isinstance(changes['old'], list) else changes['old']}")
                st.write(f"  New: {', '.join(changes['new']) if isinstance(changes['new'], list) else changes['new']}")


def render_version_comparison_dialog(
    transcript_id: int,
    version_manager: VersionManager,
    selected_version: int
) -> None:
    """Render dialog for selecting versions to compare"""
    
    with st.container():
        st.markdown("---")
        st.subheader("Compare Versions")
        
        versions = version_manager.get_versions(transcript_id)
        version_options = {f"v{v.version_number} - {v.change_summary[:30]}...": v.version_number 
                          for v in versions}
        
        col1, col2 = st.columns(2)
        with col1:
            version1 = st.selectbox(
                "First Version",
                options=list(version_options.keys()),
                index=list(version_options.values()).index(selected_version)
            )
        
        with col2:
            version2 = st.selectbox(
                "Second Version",
                options=list(version_options.keys()),
                index=0
            )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Compare", type="primary"):
                v1_num = version_options[version1]
                v2_num = version_options[version2]
                if v1_num != v2_num:
                    st.session_state.comparing_versions = (v1_num, v2_num)
                    del st.session_state.compare_version
                    st.rerun()
                else:
                    st.error("Please select different versions to compare")
        
        with col2:
            if st.button("Cancel"):
                del st.session_state.compare_version
                st.rerun()
    
    # Show comparison if versions selected
    if hasattr(st.session_state, 'comparing_versions'):
        v1, v2 = st.session_state.comparing_versions
        render_version_comparison(transcript_id, v1, v2, version_manager)
        if st.button("Close Comparison"):
            del st.session_state.comparing_versions
            st.rerun()


def render_edit_transcript_dialog(
    transcript: Transcript,
    version_manager: VersionManager,
    current_user: User
) -> None:
    """Render dialog for editing a transcript"""
    
    st.markdown("### ✏️ Edit Transcript")
    
    # Get latest version for conflict detection
    latest_version = version_manager.get_latest_version(transcript.id)
    base_version_number = latest_version.version_number if latest_version else 0
    
    # Check for active editors
    active_editors = version_manager.get_active_editors(transcript.id)
    if active_editors:
        other_editors = [e for e in active_editors if e['user'] != current_user.username]
        if other_editors:
            st.warning(f"⚠️ Active editors: {', '.join([e['user'] for e in other_editors])}")
    
    with st.form("edit_transcript_form"):
        # Edit content
        new_content = st.text_area(
            "Content",
            value=transcript.content,
            height=400,
            help="Edit the transcript content"
        )
        
        # Change summary
        change_summary = st.text_input(
            "Change Summary",
            placeholder="Briefly describe your changes...",
            help="Required: Describe what you changed and why"
        )
        
        # Conflict resolution strategy
        st.write("**Conflict Resolution**")
        conflict_strategy = st.radio(
            "If conflicts occur, how should they be resolved?",
            ["smart", "current", "incoming"],
            index=0,
            help="Smart: AI-assisted merge, Current: Keep existing, Incoming: Use your changes"
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes", type="primary"):
                if new_content and change_summary:
                    if new_content != transcript.content:
                        try:
                            # Create notification manager
                            from notifications import NotificationManager
                            from database.models import get_db_session
                            notification_session = get_db_session()
                            notification_mgr = NotificationManager(notification_session)
                            
                            # Update with conflict resolution and notifications
                            updated_transcript, version, conflict_info = version_manager.update_transcript(
                                transcript_id=transcript.id,
                                user_id=current_user.id,
                                new_content=new_content,
                                change_summary=change_summary,
                                base_version_number=base_version_number,
                                conflict_strategy=conflict_strategy,
                                notification_manager=notification_mgr
                            )
                            
                            if conflict_info['has_conflicts']:
                                st.success(f"Changes saved with {len(conflict_info['conflicts'])} conflicts resolved!")
                                st.info(f"Resolution strategy: {conflict_info['resolution_strategy']}")
                            else:
                                st.success("Changes saved successfully!")
                            
                            st.session_state.show_edit_dialog = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error saving changes: {str(e)}")
                    else:
                        st.warning("No changes detected")
                else:
                    st.error("Please provide content and a change summary")
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.show_edit_dialog = False
                st.rerun()
    
    # Show current version info
    st.divider()
    st.caption(f"Editing version {base_version_number} (Last modified by {latest_version.changed_by.username if latest_version else 'System'})")


def render_version_restore_dialog(
    transcript_id: int,
    version_number: int,
    version_manager: VersionManager,
    current_user: User
) -> None:
    """Render dialog for restoring a version"""
    
    version = version_manager.get_version(transcript_id, version_number)
    if not version:
        st.error("Version not found")
        return
    
    st.markdown("---")
    st.subheader(f"Restore to Version {version_number}")
    
    st.warning("⚠️ This will replace the current transcript content with this version.")
    
    # Show version details
    st.write(f"**Version:** {version.version_number}")
    st.write(f"**Author:** {version.changed_by.username}")
    st.write(f"**Date:** {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"**Summary:** {version.change_summary}")
    
    # Show preview
    st.text_area("Content Preview", version.content[:500] + "...", height=200, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Restore", type="primary"):
            try:
                version_manager.restore_version(
                    transcript_id=transcript_id,
                    version_number=version_number,
                    user_id=current_user.id
                )
                st.success(f"Restored to version {version_number}")
                del st.session_state.restore_version
                st.rerun()
            except Exception as e:
                st.error(f"Error restoring version: {str(e)}")
    
    with col2:
        if st.button("❌ Cancel"):
            del st.session_state.restore_version
            st.rerun()


def render_version_timeline(
    transcript_id: int,
    version_manager: VersionManager
) -> None:
    """Render a visual timeline of version changes"""
    
    timeline = version_manager.get_version_timeline(transcript_id)
    
    if not timeline:
        st.info("No version history available")
        return
    
    st.markdown("### 📈 Change Timeline")
    
    # Create timeline visualization
    for i, entry in enumerate(timeline):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.write(f"**v{entry['version_number']}**")
            st.caption(entry['date'].strftime("%Y-%m-%d"))
        
        with col2:
            st.write(f"**{entry['summary']}**")
            st.caption(f"by {entry['author']}")
            
            # Show change metrics
            if entry['lines_changed'] > 0:
                st.progress(min(entry['lines_changed'] / 100, 1.0))
                st.caption(f"{entry['lines_changed']} lines, {entry['words_changed']} words")
        
        with col3:
            if st.button("View", key=f"timeline_view_{entry['version_number']}"):
                st.session_state.viewing_version = entry['version_number']
                st.rerun()
        
        if i < len(timeline) - 1:
            st.divider()