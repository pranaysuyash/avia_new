#!/usr/bin/env python3
"""
Enhanced UI Components for Audio/Video Transcription App
Provides modern, interactive components with drag-and-drop and animations
"""

import streamlit as st
import logging
from typing import Optional, List, Dict, Any
from ui_styles import create_loading_animation, create_metric_card, create_entity_tag, create_progress_bar

logger = logging.getLogger(__name__)

def enhanced_file_uploader(
    label: str,
    accepted_types: List[str],
    max_size_mb: int = 2048,
    help_text: str = None,
    key: str = None
) -> Optional[Any]:
    """Enhanced file uploader with drag-and-drop styling and validation"""
    
    # Use Streamlit's native file uploader directly
    uploaded_file = st.file_uploader(
        label=label,
        type=accepted_types,
        help=help_text,
        key=key
    )
    
    return uploaded_file

def enhanced_progress_indicator(
    progress: int,
    text: str = "",
    show_percentage: bool = True,
    animated: bool = True,
    color_scheme: str = "primary"
) -> None:
    """Enhanced progress indicator with animations and styling"""
    
    # Color schemes
    color_schemes = {
        "primary": ("var(--primary-color)", "var(--accent-color)"),
        "success": ("var(--success-color)", "var(--success-color)"),
        "warning": ("var(--warning-color)", "var(--warning-color)"),
        "error": ("var(--error-color)", "var(--error-color)")
    }
    
    start_color, end_color = color_schemes.get(color_scheme, color_schemes["primary"])
    
    # Create progress bar HTML
    percentage_text = f"{progress}%" if show_percentage else ""
    display_text = f"{text} {percentage_text}".strip()
    
    animation_css = """
    @keyframes progress-fill {
        0% { width: 0%; }
        100% { width: """ + str(progress) + """%; }
    }
    
    @keyframes progress-shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }
    """ if animated else ""
    
    progress_html = f"""
    <div style="margin: 1rem 0;">
        <div style="
            background: var(--surface-variant-color);
            border-radius: 12px;
            height: 24px;
            overflow: hidden;
            position: relative;
            box-shadow: inset 0 2px 4px var(--shadow-color);
        ">
            <div style="
                background: linear-gradient(90deg, {start_color}, {end_color});
                height: 100%;
                width: {progress}%;
                border-radius: 12px;
                transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 0.85rem;
                font-weight: 600;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3);
                position: relative;
                overflow: hidden;
                {'animation: progress-fill 1s ease-out;' if animated else ''}
            ">
                {display_text}
                {'<div style="position: absolute; top: 0; left: 0; bottom: 0; right: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); animation: progress-shimmer 2s infinite;"></div>' if animated and progress > 0 else ''}
            </div>
        </div>
    </div>
    
    <style>
    {animation_css}
    </style>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)

def enhanced_metric_display(
    metrics: List[Dict[str, Any]],
    columns: int = 3,
    show_delta: bool = True,
    animated: bool = True
) -> None:
    """Enhanced metric display with native Streamlit metrics"""
    
    # Create responsive columns
    cols = st.columns(columns)
    
    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            title = metric.get('title', 'Metric')
            value = metric.get('value', '0')
            delta = metric.get('delta', None) if show_delta else None
            help_text = metric.get('help', None)
            icon = metric.get('icon', '📊')
            
            # Use native Streamlit metric with icon in label
            st.metric(
                label=f"{icon} {title}",
                value=value,
                delta=delta,
                help=help_text
            )

def enhanced_entity_display(
    entities: Dict[str, List[str]],
    entity_confidence: Dict[str, Dict[str, float]] = None,
    show_confidence: bool = True,
    interactive: bool = True
) -> None:
    """Enhanced entity display with styling and interactivity"""
    
    if not entities:
        st.info("No entities found")
        return
    
    # Entity type configurations
    entity_configs = {
        "PERSON": {"color": "var(--info-color)", "icon": "👤", "label": "People"},
        "ORG": {"color": "var(--warning-color)", "icon": "🏢", "label": "Organizations"},
        "DATE": {"color": "var(--success-color)", "icon": "📅", "label": "Dates"},
        "TIME": {"color": "var(--secondary-color)", "icon": "⏰", "label": "Times"},
        "GPE": {"color": "var(--primary-color)", "icon": "🌍", "label": "Locations"},
        "MONEY": {"color": "var(--accent-color)", "icon": "💰", "label": "Money"},
        "CARDINAL": {"color": "var(--text-secondary-color)", "icon": "🔢", "label": "Numbers"}
    }
    
    # Display entities by category
    for entity_type, entity_list in entities.items():
        if not entity_list:
            continue
            
        config = entity_configs.get(entity_type.upper(), {
            "color": "var(--text-secondary-color)",
            "icon": "🏷️",
            "label": entity_type.title()
        })
        
        with st.expander(f"{config['icon']} {config['label']} ({len(entity_list)} found)", expanded=True):
            # Create entity tags
            entity_html = '<div style="margin: 0.5rem 0; line-height: 2;">'
            
            for entity in entity_list:
                confidence = None
                if show_confidence and entity_confidence:
                    confidence = entity_confidence.get(entity_type, {}).get(entity, None)
                
                confidence_text = f" ({confidence:.2f})" if confidence else ""
                
                entity_html += f"""
                <span style="
                    background: linear-gradient(135deg, {config['color']}20, {config['color']}10);
                    border: 1px solid {config['color']}40;
                    border-radius: 20px;
                    color: var(--text-primary-color);
                    display: inline-block;
                    font-size: 0.85rem;
                    font-weight: 500;
                    margin: 2px 4px;
                    padding: 6px 12px;
                    transition: all 0.3s ease;
                    cursor: {'pointer' if interactive else 'default'};
                " {'onmouseover="this.style.transform=\'translateY(-2px)\'; this.style.boxShadow=\'0 4px 12px var(--shadow-color)\';" onmouseout="this.style.transform=\'translateY(0)\'; this.style.boxShadow=\'none\';"' if interactive else ''}>
                    {entity}{confidence_text}
                </span>
                """
            
            entity_html += '</div>'
            st.markdown(entity_html, unsafe_allow_html=True)

def enhanced_loading_state(
    text: str = "Processing...",
    show_spinner: bool = True,
    show_tips: bool = True,
    tips: List[str] = None
) -> None:
    """Enhanced loading state with animations and tips"""
    
    default_tips = [
        "💡 Clear audio produces better transcripts",
        "🎯 Advanced mode provides more detailed analysis",
        "⚡ Processing time depends on file size",
        "🔍 You can search within transcripts after processing",
        "📊 Results can be downloaded in multiple formats"
    ]
    
    tips_to_show = tips or default_tips
    
    # Use Streamlit's native components for cleaner display
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if show_spinner:
                st.markdown(
                    """
                    <div style="text-align: center; padding: 2rem;">
                        <div style="font-size: 3rem; animation: spin 2s linear infinite;">⚡</div>
                    </div>
                    <style>
                    @keyframes spin {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown(f"### {text}")
            st.markdown("Please wait while we process your content...")
            
            if show_tips and tips_to_show:
                with st.container():
                    st.info(f"💡 **Tip:** {tips_to_show[0]}")

def enhanced_audio_player(
    audio_bytes: bytes,
    title: str = "Generated Audio",
    show_controls: bool = True,
    show_download: bool = True,
    filename: str = "audio.mp3"
) -> None:
    """Enhanced audio player with custom styling"""
    
    player_html = f"""
    <div style="
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px var(--shadow-color);
    ">
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 1.5rem; margin-right: 0.5rem;">🎵</div>
            <div style="
                font-weight: 600;
                color: var(--text-primary-color);
                font-size: 1.1rem;
            ">{title}</div>
        </div>
    </div>
    """
    
    st.markdown(player_html, unsafe_allow_html=True)
    
    # Standard audio player
    st.audio(audio_bytes, format="audio/mp3")
    
    # Download button if requested
    if show_download:
        st.download_button(
            label="📥 Download Audio",
            data=audio_bytes,
            file_name=filename,
            mime="audio/mp3",
            help="Download the generated audio file"
        )

def create_responsive_layout(mobile_breakpoint: int = 768):
    """Create responsive layout utilities"""
    
    responsive_css = f"""
    <style>
    /* Responsive utilities */
    .responsive-hide-mobile {{
        display: block;
    }}
    
    .responsive-show-mobile {{
        display: none;
    }}
    
    @media (max-width: {mobile_breakpoint}px) {{
        .responsive-hide-mobile {{
            display: none;
        }}
        
        .responsive-show-mobile {{
            display: block;
        }}
        
        /* Stack columns on mobile */
        .stColumns > div {{
            width: 100% !important;
            margin-bottom: 1rem;
        }}
        
        /* Adjust button sizes */
        .stButton > button {{
            width: 100%;
            margin-bottom: 0.5rem;
        }}
        
        /* Adjust text sizes */
        h1 {{ font-size: 2rem !important; }}
        h2 {{ font-size: 1.5rem !important; }}
        h3 {{ font-size: 1.25rem !important; }}
        
        /* Adjust padding */
        .main .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
    }}
    
    @media (max-width: 480px) {{
        .main .block-container {{
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        
        h1 {{ font-size: 1.75rem !important; }}
    }}
    </style>
    """
    
    st.markdown(responsive_css, unsafe_allow_html=True)