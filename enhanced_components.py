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
    max_size_mb: int = 100,
    help_text: str = None,
    key: str = None
) -> Optional[Any]:
    """Enhanced file uploader with drag-and-drop styling and validation"""
    
    # Create custom styling for the file uploader
    uploader_css = f"""
    <style>
    .enhanced-uploader {{
        border: 2px dashed var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        background: var(--surface-color);
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}
    
    .enhanced-uploader:hover {{
        border-color: var(--primary-color);
        background: var(--surface-variant-color);
        transform: translateY(-2px);
        box-shadow: 0 8px 20px var(--shadow-color);
    }}
    
    .enhanced-uploader.drag-active {{
        border-color: var(--success-color);
        background: linear-gradient(135deg, var(--success-color)10, var(--primary-color)10);
        animation: pulse 1s infinite;
    }}
    
    .upload-icon {{
        font-size: 3rem;
        color: var(--primary-color);
        margin-bottom: 1rem;
        display: block;
    }}
    
    .upload-text {{
        color: var(--text-primary-color);
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }}
    
    .upload-subtext {{
        color: var(--text-secondary-color);
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }}
    
    .upload-specs {{
        background: var(--surface-variant-color);
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 1rem;
        font-size: 0.8rem;
        color: var(--text-secondary-color);
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1) translateY(-2px); }}
        50% {{ transform: scale(1.02) translateY(-2px); }}
        100% {{ transform: scale(1) translateY(-2px); }}
    }}
    </style>
    """
    
    st.markdown(uploader_css, unsafe_allow_html=True)
    
    # Create the enhanced uploader UI
    with st.container():
        # Display custom upload area
        types_str = ", ".join(accepted_types).upper()
        
        upload_html = f"""
        <div class="enhanced-uploader" id="enhanced-uploader-{key or 'default'}">
            <div class="upload-icon">📁</div>
            <div class="upload-text">Drag & Drop Your File Here</div>
            <div class="upload-subtext">or click to browse</div>
            <div class="upload-specs">
                <strong>Supported:</strong> {types_str} • <strong>Max Size:</strong> {max_size_mb}MB
            </div>
        </div>
        """
        
        st.markdown(upload_html, unsafe_allow_html=True)
        
        # Add JavaScript for enhanced drag-and-drop
        drag_drop_js = f"""
        <script>
        (function() {{
            const uploader = document.getElementById('enhanced-uploader-{key or "default"}');
            if (!uploader) return;
            
            let dragCounter = 0;
            
            uploader.addEventListener('dragenter', function(e) {{
                e.preventDefault();
                dragCounter++;
                this.classList.add('drag-active');
            }});
            
            uploader.addEventListener('dragleave', function(e) {{
                e.preventDefault();
                dragCounter--;
                if (dragCounter === 0) {{
                    this.classList.remove('drag-active');
                }}
            }});
            
            uploader.addEventListener('dragover', function(e) {{
                e.preventDefault();
            }});
            
            uploader.addEventListener('drop', function(e) {{
                e.preventDefault();
                dragCounter = 0;
                this.classList.remove('drag-active');
                
                // Add success animation
                this.style.borderColor = 'var(--success-color)';
                this.style.background = 'linear-gradient(135deg, var(--success-color)20, var(--success-color)10)';
                
                setTimeout(() => {{
                    this.style.borderColor = 'var(--border-color)';
                    this.style.background = 'var(--surface-color)';
                }}, 2000);
            }});
        }})();
        </script>
        """
        
        st.markdown(drag_drop_js, unsafe_allow_html=True)
        
        # Standard Streamlit file uploader (hidden with CSS)
        uploader_style = """
        <style>
        .stFileUploader {
            opacity: 0;
            height: 0;
            overflow: hidden;
        }
        </style>
        """
        st.markdown(uploader_style, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            label,
            type=accepted_types,
            help=help_text,
            key=key,
            label_visibility="collapsed"
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
    """Enhanced metric display with cards and animations"""
    
    # Create responsive columns
    cols = st.columns(columns)
    
    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            title = metric.get('title', 'Metric')
            value = metric.get('value', '0')
            delta = metric.get('delta', None) if show_delta else None
            help_text = metric.get('help', None)
            icon = metric.get('icon', '📊')
            
            # Create metric card
            card_html = f"""
            <div style="
                background: var(--surface-color);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 2px 8px var(--shadow-color);
                margin-bottom: 1rem;
                position: relative;
                overflow: hidden;
                {'animation: slideInUp 0.6s ease-out;' if animated else ''}
                animation-delay: {i * 0.1}s;
                animation-fill-mode: both;
            " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 24px var(--shadow-color)';" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px var(--shadow-color)';">
                
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <div style="
                    font-size: 0.8rem;
                    color: var(--text-secondary-color);
                    margin-bottom: 0.5rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    font-weight: 500;
                ">{title}</div>
                <div style="
                    font-size: 1.8rem;
                    font-weight: 700;
                    color: var(--text-primary-color);
                    margin-bottom: 0.25rem;
                ">{value}</div>
                {f'<div style="color: {"var(--success-color)" if not str(delta).startswith("-") else "var(--error-color)"}; font-size: 0.85rem; font-weight: 500;">{delta}</div>' if delta else ''}
                {f'<div style="color: var(--text-secondary-color); font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8;">{help_text}</div>' if help_text else ''}
            </div>
            """
            
            st.markdown(card_html, unsafe_allow_html=True)
    
    # Add animation CSS
    if animated:
        animation_css = """
        <style>
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
        """
        st.markdown(animation_css, unsafe_allow_html=True)

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
    
    # Loading animation
    loading_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem 2rem;
        text-align: center;
        background: var(--surface-color);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin: 2rem 0;
    ">
        {f'<div style="font-size: 3rem; margin-bottom: 1rem; animation: spin 2s linear infinite;">⚡</div>' if show_spinner else ''}
        <div style="
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-primary-color);
            margin-bottom: 0.5rem;
        ">{text}</div>
        <div style="
            color: var(--text-secondary-color);
            font-size: 0.9rem;
            margin-bottom: 2rem;
        ">Please wait while we process your content...</div>
        
        {f'''
        <div style="
            background: var(--surface-variant-color);
            border-radius: 12px;
            padding: 1rem;
            max-width: 400px;
            margin-top: 1rem;
        ">
            <div style="
                color: var(--text-secondary-color);
                font-size: 0.8rem;
                margin-bottom: 0.5rem;
                font-weight: 500;
            ">💡 Did you know?</div>
            <div id="rotating-tip" style="
                color: var(--text-primary-color);
                font-size: 0.85rem;
                line-height: 1.4;
            ">{tips_to_show[0]}</div>
        </div>
        ''' if show_tips and tips_to_show else ''}
    </div>
    
    <style>
    @keyframes spin {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    </style>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)
    
    # Add tip rotation JavaScript
    if show_tips and tips_to_show:
        tip_rotation_js = f"""
        <script>
        (function() {{
            const tips = {tips_to_show};
            const tipElement = document.getElementById('rotating-tip');
            let currentTip = 0;
            
            if (tipElement) {{
                setInterval(() => {{
                    currentTip = (currentTip + 1) % tips.length;
                    tipElement.style.opacity = '0';
                    setTimeout(() => {{
                        tipElement.textContent = tips[currentTip];
                        tipElement.style.opacity = '1';
                    }}, 300);
                }}, 3000);
            }}
        }})();
        </script>
        """
        st.markdown(tip_rotation_js, unsafe_allow_html=True)

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