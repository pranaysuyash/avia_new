#!/usr/bin/env python3
"""
Refactored Enhanced Components - Using native Streamlit with centralized styling
No more inline HTML generation - let ui_styles_refactored.py handle all styling
"""

import streamlit as st
import logging
from typing import Optional, List, Dict, Any, Tuple
import time

logger = logging.getLogger(__name__)

def enhanced_file_uploader(
    label: str,
    accepted_types: List[str],
    max_size_mb: int = 2048,
    help_text: str = None,
    key: str = None
) -> Optional[Any]:
    """
    Enhanced file uploader using native Streamlit with centralized styling
    The drag-and-drop styling is handled by CSS in ui_styles_refactored.py
    """
    # Simply use Streamlit's native file uploader
    # The CSS will style it appropriately
    uploaded_file = st.file_uploader(
        label=label,
        type=accepted_types,
        help=help_text,
        key=key
    )
    
    # Validate file size if uploaded
    if uploaded_file is not None:
        file_size_mb = len(uploaded_file.read()) / (1024 * 1024)
        uploaded_file.seek(0)  # Reset file pointer
        
        if file_size_mb > max_size_mb:
            st.error(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
            return None
    
    return uploaded_file

def enhanced_progress_indicator(
    progress: int,
    text: str = "",
    key: str = None
) -> None:
    """
    Enhanced progress indicator using native Streamlit progress bar
    Custom styling is applied via CSS targeting .stProgress
    """
    # Use native Streamlit progress with text
    st.progress(progress / 100, text=text)

def enhanced_metric_display(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None
) -> None:
    """
    Enhanced metric display using native Streamlit metric
    The metric-card styling is applied via CSS
    """
    # Wrap in a div with our custom class for styling
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )
    st.markdown('</div>', unsafe_allow_html=True)

def enhanced_entity_display(entities: Dict[str, List[str]]) -> None:
    """
    Enhanced entity display using Streamlit components with CSS styling
    Each entity type gets an expander with styled tags
    """
    # Entity type configurations
    entity_configs = {
        "PERSON": {"icon": "👤", "label": "People", "class": "entity-tag-person"},
        "ORG": {"icon": "🏢", "label": "Organizations", "class": "entity-tag-org"},
        "GPE": {"icon": "📍", "label": "Locations", "class": "entity-tag-location"},
        "LOC": {"icon": "📍", "label": "Locations", "class": "entity-tag-location"},
        "DATE": {"icon": "📅", "label": "Dates", "class": "entity-tag-date"},
        "TIME": {"icon": "🕐", "label": "Times", "class": "entity-tag-date"},
        "MONEY": {"icon": "💰", "label": "Money", "class": "entity-tag-money"},
        "PERCENT": {"icon": "📊", "label": "Percentages", "class": "entity-tag-percent"},
    }
    
    # Display entities by type
    for entity_type, entity_list in entities.items():
        if entity_list:  # Only show if there are entities
            config = entity_configs.get(entity_type, {
                "icon": "📌",
                "label": entity_type,
                "class": "entity-tag"
            })
            
            with st.expander(f"{config['icon']} {config['label']} ({len(entity_list)})"):
                # Create a flex container with entity tags
                tags_html = " ".join([
                    f'<span class="{config["class"]} entity-tag">{entity}</span>'
                    for entity in entity_list
                ])
                st.markdown(
                    f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{tags_html}</div>',
                    unsafe_allow_html=True
                )

def enhanced_audio_player(
    audio_data,
    title: str = "Audio Player",
    show_download: bool = True
) -> None:
    """
    Enhanced audio player using native Streamlit components
    Container styling handled by CSS
    """
    # Create container with custom class
    st.markdown('<div class="audio-player-container">', unsafe_allow_html=True)
    
    # Title
    st.markdown(f"**{title}**")
    
    # Native audio player
    st.audio(audio_data)
    
    # Download button if requested
    if show_download and audio_data is not None:
        st.download_button(
            label="📥 Download Audio",
            data=audio_data,
            file_name="audio_file.wav",
            mime="audio/wav"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

def enhanced_loading_state(text: str = "Processing...") -> None:
    """
    Enhanced loading state using native Streamlit spinner
    """
    with st.spinner(text):
        # The spinner will handle the loading animation
        # Additional loading UI can be added here if needed
        pass

def create_tab_navigation(tabs: Dict[str, str], active_tab: str) -> str:
    """
    Create a tab navigation bar using native Streamlit columns and buttons
    Returns the selected tab
    """
    selected_tab = active_tab
    
    # Create columns for tabs
    cols = st.columns(len(tabs))
    
    for idx, (key, label) in enumerate(tabs.items()):
        with cols[idx]:
            # Use button type to indicate active state
            if st.button(
                label,
                key=f"tab_{key}",
                use_container_width=True,
                type="primary" if active_tab == key else "secondary"
            ):
                selected_tab = key
    
    return selected_tab

def create_stat_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    trend: Optional[Tuple[str, str]] = None  # (direction, percentage)
) -> None:
    """
    Create a statistics card using native Streamlit components
    """
    with st.container():
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        
        # Header with icon
        if icon:
            st.markdown(f"### {icon} {title}")
        else:
            st.markdown(f"### {title}")
        
        # Main value
        st.markdown(f"<h2 style='margin: 0;'>{value}</h2>", unsafe_allow_html=True)
        
        # Subtitle
        if subtitle:
            st.caption(subtitle)
        
        # Trend indicator
        if trend:
            direction, percentage = trend
            color = "green" if direction == "up" else "red"
            arrow = "↑" if direction == "up" else "↓"
            st.markdown(
                f"<span style='color: {color};'>{arrow} {percentage}</span>",
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

def create_action_button(
    label: str,
    icon: Optional[str] = None,
    variant: str = "primary",
    full_width: bool = False,
    key: Optional[str] = None
) -> bool:
    """
    Create an action button with optional icon
    """
    button_label = f"{icon} {label}" if icon else label
    
    return st.button(
        button_label,
        type=variant,
        use_container_width=full_width,
        key=key
    )

def create_info_card(
    title: str,
    content: str,
    variant: str = "info",
    icon: Optional[str] = None
) -> None:
    """
    Create an information card using native Streamlit components
    """
    # Map variants to Streamlit message types
    variant_map = {
        "info": st.info,
        "success": st.success,
        "warning": st.warning,
        "error": st.error
    }
    
    message_func = variant_map.get(variant, st.info)
    
    # Format content with title
    if icon:
        full_content = f"**{icon} {title}**\n\n{content}"
    else:
        full_content = f"**{title}**\n\n{content}"
    
    message_func(full_content)

def create_sidebar_section(
    title: str,
    icon: Optional[str] = None,
    expanded: bool = True
) -> Any:
    """
    Create a sidebar section using expander
    Returns the expander context
    """
    section_title = f"{icon} {title}" if icon else title
    return st.sidebar.expander(section_title, expanded=expanded)

def render_empty_state(
    title: str,
    description: str,
    icon: str = "📭",
    action_label: Optional[str] = None,
    action_callback: Optional[callable] = None
) -> None:
    """
    Render an empty state placeholder
    """
    # Center the empty state
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 3rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
                <h3>{title}</h3>
                <p style="color: var(--text-secondary-color);">{description}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if action_label and action_callback:
            if st.button(action_label, type="primary", use_container_width=True):
                action_callback()

def create_feature_card(
    title: str,
    description: str,
    icon: str,
    features: List[str],
    action_label: str,
    enabled: bool = True
) -> bool:
    """
    Create a feature showcase card
    """
    with st.container():
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown(f"### {icon} {title}")
        st.markdown(description)
        
        # Feature list
        for feature in features:
            st.markdown(f"✓ {feature}")
        
        # Action button
        clicked = st.button(
            action_label,
            type="primary" if enabled else "secondary",
            disabled=not enabled,
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return clicked

# Utility functions for common patterns

def show_success_message(message: str, duration: int = 3) -> None:
    """Show a success message that auto-dismisses"""
    placeholder = st.empty()
    placeholder.success(message)
    time.sleep(duration)
    placeholder.empty()

def show_error_message(message: str, details: Optional[str] = None) -> None:
    """Show an error message with optional details"""
    st.error(message)
    if details:
        with st.expander("Error Details"):
            st.code(details)

def create_download_section(
    title: str,
    files: Dict[str, Tuple[str, str, str]]  # filename: (data, mime_type, label)
) -> None:
    """Create a download section with multiple file options"""
    st.markdown(f"### {title}")
    
    cols = st.columns(len(files))
    for idx, (filename, (data, mime_type, label)) in enumerate(files.items()):
        with cols[idx]:
            st.download_button(
                label=label,
                data=data,
                file_name=filename,
                mime=mime_type,
                use_container_width=True
            )