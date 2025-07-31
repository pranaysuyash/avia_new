#!/usr/bin/env python3
"""
UI Styles and Theme Management for Audio/Video Transcription App
Provides modern CSS styling, theme management, and responsive design
"""

import streamlit as st
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Color palettes for different themes
THEMES = {
    "light": {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e", 
        "success": "#2ca02c",
        "warning": "#ff9800",
        "error": "#d62728",
        "info": "#17a2b8",
        "background": "#ffffff",
        "surface": "#f8f9fa",
        "surface_variant": "#e9ecef",
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "border": "#dee2e6",
        "shadow": "rgba(0, 0, 0, 0.1)",
        "accent": "#6f42c1"
    },
    "dark": {
        "primary": "#4dabf7",
        "secondary": "#ffd43b",
        "success": "#51cf66", 
        "warning": "#ffa726",
        "error": "#ff6b6b",
        "info": "#22d3ee",
        "background": "#0d1117",
        "surface": "#161b22",
        "surface_variant": "#21262d",
        "text_primary": "#f0f6fc",
        "text_secondary": "#8b949e",
        "border": "#30363d",
        "shadow": "rgba(0, 0, 0, 0.3)",
        "accent": "#a855f7"
    }
}

def get_theme_colors(theme_name: str = "light") -> Dict[str, str]:
    """Get color palette for specified theme"""
    return THEMES.get(theme_name, THEMES["light"])

def inject_custom_css(theme: str = "light"):
    """Inject custom CSS for modern styling and theme support"""
    colors = get_theme_colors(theme)
    
    css = f"""
    <style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for theme colors */
    :root {{
        --primary-color: {colors['primary']};
        --secondary-color: {colors['secondary']};
        --success-color: {colors['success']};
        --warning-color: {colors['warning']};
        --error-color: {colors['error']};
        --info-color: {colors['info']};
        --background-color: {colors['background']};
        --surface-color: {colors['surface']};
        --surface-variant-color: {colors['surface_variant']};
        --text-primary-color: {colors['text_primary']};
        --text-secondary-color: {colors['text_secondary']};
        --border-color: {colors['border']};
        --shadow-color: {colors['shadow']};
        --accent-color: {colors['accent']};
    }}
    
    /* Global styles */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-primary-color);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: all 0.3s ease;
    }}
    
    /* Main container styling */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}
    
    /* Header styling */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-primary-color);
        font-weight: 600;
        letter-spacing: -0.025em;
    }}
    
    h1 {{
        font-size: 2.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background-color: var(--surface-color);
        border-right: 1px solid var(--border-color);
    }}
    
    .css-1d391kg .css-1v0mbdj {{
        color: var(--text-primary-color);
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px var(--shadow-color);
        position: relative;
        overflow: hidden;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px var(--shadow-color);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Secondary button styling */
    .stButton > button[kind="secondary"] {{
        background: var(--surface-variant-color);
        color: var(--text-primary-color);
        border: 1px solid var(--border-color);
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background: var(--surface-color);
        border-color: var(--primary-color);
    }}
    
    /* File uploader styling */
    .stFileUploader {{
        background: var(--surface-color);
        border: 2px dashed var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }}
    
    .stFileUploader:hover {{
        border-color: var(--primary-color);
        background: var(--surface-variant-color);
        transform: translateY(-2px);
    }}
    
    .stFileUploader [data-testid="stFileUploaderDropzone"] {{
        background: transparent;
        border: none;
    }}
    
    /* Drag and drop enhancement */
    .stFileUploader.drag-over {{
        border-color: var(--success-color);
        background: linear-gradient(135deg, var(--success-color)10, var(--primary-color)10);
        animation: pulse 1s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.02); }}
        100% {{ transform: scale(1); }}
    }}
    
    /* Text input styling */
    .stTextInput > div > div > input {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary-color);
        padding: 0.75rem;
        transition: all 0.3s ease;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px var(--primary-color)20;
    }}
    
    /* Text area styling */
    .stTextArea > div > div > textarea {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary-color);
        font-family: 'Inter', monospace;
        line-height: 1.6;
        transition: all 0.3s ease;
    }}
    
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px var(--primary-color)20;
    }}
    
    /* Select box styling */
    .stSelectbox > div > div {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }}
    
    /* Metric styling */
    .metric-container {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px var(--shadow-color);
    }}
    
    .metric-container:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px var(--shadow-color);
    }}
    
    /* Progress bar styling */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        border-radius: 10px;
        height: 8px;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: var(--surface-color);
        border-radius: 12px;
        padding: 4px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: var(--text-secondary-color);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: var(--primary-color);
        color: white;
    }}
    
    /* Expander styling */
    .streamlit-expanderHeader {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary-color);
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: var(--surface-variant-color);
        border-color: var(--primary-color);
    }}
    
    /* Alert styling */
    .stAlert {{
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 8px var(--shadow-color);
    }}
    
    .stSuccess {{
        background: linear-gradient(135deg, var(--success-color)15, var(--success-color)05);
        border-left: 4px solid var(--success-color);
    }}
    
    .stError {{
        background: linear-gradient(135deg, var(--error-color)15, var(--error-color)05);
        border-left: 4px solid var(--error-color);
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, var(--warning-color)15, var(--warning-color)05);
        border-left: 4px solid var(--warning-color);
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, var(--info-color)15, var(--info-color)05);
        border-left: 4px solid var(--info-color);
    }}
    
    /* Entity tag styling */
    .entity-tag {{
        background: linear-gradient(135deg, var(--primary-color)20, var(--accent-color)20);
        border: 1px solid var(--primary-color)40;
        border-radius: 20px;
        color: var(--text-primary-color);
        display: inline-block;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 2px 4px;
        padding: 4px 12px;
        transition: all 0.3s ease;
    }}
    
    .entity-tag:hover {{
        transform: translateY(-1px);
        box-shadow: 0 2px 8px var(--shadow-color);
    }}
    
    /* Loading animation */
    .loading-spinner {{
        animation: spin 1s linear infinite;
        color: var(--primary-color);
    }}
    
    @keyframes spin {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    
    /* Smooth transitions for theme switching */
    * {{
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }}
    
    /* Audio player styling */
    audio {{
        width: 100%;
        border-radius: 8px;
        background: var(--surface-color);
    }}
    
    /* Download button styling */
    .stDownloadButton > button {{
        background: var(--success-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stDownloadButton > button:hover {{
        background: var(--success-color);
        filter: brightness(1.1);
        transform: translateY(-1px);
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        
        h1 {{
            font-size: 2rem;
        }}
        
        .stButton > button {{
            width: 100%;
            margin-bottom: 0.5rem;
        }}
        
        .metric-container {{
            margin-bottom: 1rem;
        }}
        
        /* Stack columns on mobile */
        .stColumns > div {{
            width: 100% !important;
            margin-bottom: 1rem;
        }}
        
        /* Adjust sidebar for mobile */
        .css-1d391kg {{
            width: 100% !important;
        }}
        
        /* Mobile-friendly tabs */
        .stTabs [data-baseweb="tab"] {{
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }}
        
        /* Mobile file uploader */
        .enhanced-uploader {{
            padding: 1.5rem 1rem;
        }}
        
        .upload-icon {{
            font-size: 2rem;
        }}
        
        /* Mobile entity tags */
        .entity-tag {{
            font-size: 0.8rem;
            padding: 3px 8px;
            margin: 1px 2px;
        }}
    }}
    
    @media (max-width: 480px) {{
        .main .block-container {{
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }}
        
        h1 {{
            font-size: 1.75rem;
        }}
        
        .enhanced-uploader {{
            padding: 1rem;
        }}
        
        .upload-icon {{
            font-size: 1.5rem;
        }}
        
        .upload-text {{
            font-size: 1rem;
        }}
        
        .upload-subtext {{
            font-size: 0.8rem;
        }}
        
        /* Smaller metrics on mobile */
        .metric-container {{
            padding: 1rem;
        }}
        
        /* Adjust text areas for mobile */
        .stTextArea > div > div > textarea {{
            font-size: 0.9rem;
        }}
        
        /* Mobile-friendly progress bars */
        .stProgress > div > div > div {{
            height: 6px;
        }}
    }}
    
    /* Touch-friendly interactions */
    @media (hover: none) and (pointer: coarse) {{
        .stButton > button {{
            min-height: 44px;
            font-size: 1rem;
        }}
        
        .entity-tag {{
            min-height: 32px;
            padding: 6px 12px;
        }}
        
        .metric-container {{
            min-height: 80px;
        }}
    }}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--surface-color);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border-color);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-secondary-color);
    }}
    
    /* Theme toggle button */
    .theme-toggle {{
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 50%;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px var(--shadow-color);
    }}
    
    .theme-toggle:hover {{
        transform: scale(1.1);
        box-shadow: 0 4px 16px var(--shadow-color);
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def create_drag_drop_enhancement():
    """Add JavaScript for enhanced drag and drop functionality and mobile detection"""
    js_code = """
    <script>
    // Mobile device detection
    function detectMobileDevice() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
        
        // Store mobile detection result
        if (window.parent && window.parent.streamlitSetComponentValue) {
            window.parent.streamlitSetComponentValue('is_mobile', isMobile);
        }
        
        // Add mobile class to body
        if (isMobile) {
            document.body.classList.add('mobile-device');
        } else {
            document.body.classList.remove('mobile-device');
        }
        
        return isMobile;
    }
    
    // Enhanced drag and drop functionality
    function setupDragDrop() {
        const fileUploaders = document.querySelectorAll('.enhanced-uploader, .stFileUploader');
        
        fileUploaders.forEach(uploader => {
            if (!uploader) return;
            
            let dragCounter = 0;
            
            // Add drag over effects
            uploader.addEventListener('dragenter', function(e) {
                e.preventDefault();
                dragCounter++;
                this.classList.add('drag-over');
            });
            
            uploader.addEventListener('dragleave', function(e) {
                e.preventDefault();
                dragCounter--;
                if (dragCounter === 0) {
                    this.classList.remove('drag-over');
                }
            });
            
            uploader.addEventListener('dragover', function(e) {
                e.preventDefault();
            });
            
            uploader.addEventListener('drop', function(e) {
                e.preventDefault();
                dragCounter = 0;
                this.classList.remove('drag-over');
                
                // Add success animation
                this.style.borderColor = 'var(--success-color)';
                this.style.background = 'linear-gradient(135deg, var(--success-color)20, var(--success-color)10)';
                
                setTimeout(() => {
                    this.style.borderColor = 'var(--border-color)';
                    this.style.background = 'var(--surface-color)';
                }, 2000);
            });
        });
    }
    
    // Smooth scroll enhancement
    function enhanceSmoothScroll() {
        document.documentElement.style.scrollBehavior = 'smooth';
    }
    
    // Initialize all enhancements
    function initializeEnhancements() {
        detectMobileDevice();
        setupDragDrop();
        enhanceSmoothScroll();
    }
    
    // Setup when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeEnhancements);
    } else {
        initializeEnhancements();
    }
    
    // Re-setup on Streamlit reruns
    setTimeout(initializeEnhancements, 100);
    
    // Handle window resize for responsive behavior
    window.addEventListener('resize', detectMobileDevice);
    </script>
    """
    
    st.markdown(js_code, unsafe_allow_html=True)

def create_loading_animation(text: str = "Processing..."):
    """Create animated loading indicator"""
    return f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 2rem;">
        <div class="loading-spinner" style="font-size: 1.5rem; margin-right: 0.5rem;">⚡</div>
        <span style="font-weight: 500; color: var(--text-primary-color);">{text}</span>
    </div>
    """

def create_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """Create styled metric card"""
    delta_html = ""
    if delta:
        delta_color = "var(--success-color)" if not delta.startswith("-") else "var(--error-color)"
        delta_html = f'<div style="color: {delta_color}; font-size: 0.8rem; margin-top: 0.25rem;">{delta}</div>'
    
    help_html = ""
    if help_text:
        help_html = f'<div style="color: var(--text-secondary-color); font-size: 0.75rem; margin-top: 0.5rem;">{help_text}</div>'
    
    return f"""
    <div class="metric-container">
        <div style="font-size: 0.8rem; color: var(--text-secondary-color); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">{title}</div>
        <div style="font-size: 1.5rem; font-weight: 600; color: var(--text-primary-color);">{value}</div>
        {delta_html}
        {help_html}
    </div>
    """

def create_entity_tag(entity: str, entity_type: str, confidence: float = None):
    """Create styled entity tag"""
    confidence_html = ""
    if confidence is not None:
        confidence_html = f' <span style="opacity: 0.7;">({confidence:.2f})</span>'
    
    # Color coding by entity type
    type_colors = {
        "PERSON": "var(--info-color)",
        "ORG": "var(--warning-color)", 
        "DATE": "var(--success-color)",
        "GPE": "var(--primary-color)",
        "MONEY": "var(--accent-color)",
        "TIME": "var(--secondary-color)"
    }
    
    color = type_colors.get(entity_type.upper(), "var(--text-secondary-color)")
    
    return f"""
    <span class="entity-tag" style="border-color: {color}40; background: linear-gradient(135deg, {color}20, {color}10);">
        {entity}{confidence_html}
    </span>
    """

def create_progress_bar(progress: int, text: str = "", animated: bool = True):
    """Create custom progress bar"""
    animation = "animation: progress-fill 2s ease-in-out;" if animated else ""
    
    return f"""
    <div style="background: var(--surface-variant-color); border-radius: 10px; height: 20px; overflow: hidden; margin: 1rem 0;">
        <div style="
            background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
            height: 100%;
            width: {progress}%;
            border-radius: 10px;
            transition: width 0.5s ease;
            {animation}
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8rem;
            font-weight: 500;
        ">
            {text}
        </div>
    </div>
    
    <style>
    @keyframes progress-fill {{
        0% {{ width: 0%; }}
        100% {{ width: {progress}%; }}
    }}
    </style>
    """

def apply_theme_toggle():
    """Create theme toggle functionality"""
    # Get current theme from session state or user preferences
    current_theme = st.session_state.get('ui_theme', st.session_state.get('user_preferences', type('obj', (object,), {'theme': 'light'})).theme)
    
    # Theme toggle in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🎨 Appearance**")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            theme_icon = "🌙" if current_theme == "light" else "☀️"
            if st.button(theme_icon, help="Toggle dark/light theme", key="theme_toggle"):
                # Import session_manager here to avoid circular imports
                from session_manager import session_manager
                new_theme = session_manager.toggle_theme()
                st.rerun()
        
        with col2:
            st.write(f"**{current_theme.title()}**")
        
        # Additional UI preferences
        if hasattr(st.session_state, 'user_preferences'):
            prefs = st.session_state.user_preferences
            
            # Animations toggle
            animations = st.checkbox(
                "Animations",
                value=prefs.animations_enabled,
                help="Enable smooth animations and transitions",
                key="animations_toggle"
            )
            if animations != prefs.animations_enabled:
                prefs.animations_enabled = animations
            
            # Responsive design toggle
            responsive = st.checkbox(
                "Mobile Optimized",
                value=prefs.responsive_design,
                help="Optimize layout for mobile devices",
                key="responsive_toggle"
            )
            if responsive != prefs.responsive_design:
                prefs.responsive_design = responsive
    
    return current_theme

def create_responsive_columns(num_cols: int, mobile_stack: bool = True):
    """Create responsive column layout"""
    if mobile_stack:
        # On mobile, stack columns vertically
        css = f"""
        <style>
        @media (max-width: 768px) {{
            .stColumns > div {{
                width: 100% !important;
                margin-bottom: 1rem;
            }}
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    return st.columns(num_cols)

def add_smooth_transitions():
    """Add smooth transitions for better UX"""
    css = """
    <style>
    /* Smooth page transitions */
    .stApp {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hover effects for interactive elements */
    .stButton > button,
    .stSelectbox,
    .stTextInput,
    .stTextArea,
    .stFileUploader {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Focus states */
    .stButton > button:focus,
    .stSelectbox:focus-within,
    .stTextInput:focus-within,
    .stTextArea:focus-within {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)