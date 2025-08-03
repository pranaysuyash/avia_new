#!/usr/bin/env python3
"""
Fixed UI Styles and Theme Management
Properly handles text visibility without aggressive CSS overrides
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manages application themes with proper contrast ratios"""
    
    # WCAG AA compliant color schemes
    THEMES = {
        "light": {
            "name": "Light",
            "primary": "#0066cc",  # Blue with good contrast
            "secondary": "#e67e00",  # Orange with good contrast
            "success": "#008a00",  # Green with good contrast
            "warning": "#c85000",  # Dark orange
            "error": "#d13438",  # Red with good contrast
            "info": "#006cbe",  # Info blue
            "background": "#ffffff",
            "surface": "#f5f5f5",
            "surface_variant": "#eeeeee",
            "text_primary": "#202020",  # Very dark gray for max contrast
            "text_secondary": "#505050",  # Medium gray with good contrast
            "text_on_primary": "#ffffff",
            "text_on_surface": "#202020",
            "border": "#d0d0d0",
            "shadow": "rgba(0, 0, 0, 0.1)",
            "accent": "#7c3aed",  # Purple
            "code_bg": "#f6f8fa",
            "code_text": "#24292e"
        },
        "dark": {
            "name": "Dark",
            "primary": "#58a6ff",  # Light blue for dark mode
            "secondary": "#ffa657",  # Light orange
            "success": "#56d364",  # Light green
            "warning": "#e3b341",  # Yellow
            "error": "#f85149",  # Light red
            "info": "#79c0ff",  # Light info blue
            "background": "#0d1117",
            "surface": "#161b22",
            "surface_variant": "#21262d",
            "text_primary": "#f0f6fc",  # Very light gray
            "text_secondary": "#c9d1d9",  # Light gray
            "text_on_primary": "#0d1117",
            "text_on_surface": "#f0f6fc",
            "border": "#30363d",
            "shadow": "rgba(0, 0, 0, 0.3)",
            "accent": "#a78bfa",  # Light purple
            "code_bg": "#161b22",
            "code_text": "#e6edf3"
        },
        "high_contrast": {
            "name": "High Contrast",
            "primary": "#0000ff",  # Pure blue
            "secondary": "#ff6600",  # Bright orange
            "success": "#00aa00",  # Bright green
            "warning": "#ff9900",  # Bright orange
            "error": "#ff0000",  # Pure red
            "info": "#0099ff",  # Bright blue
            "background": "#ffffff",
            "surface": "#f0f0f0",
            "surface_variant": "#e0e0e0",
            "text_primary": "#000000",  # Pure black
            "text_secondary": "#333333",  # Very dark gray
            "text_on_primary": "#ffffff",
            "text_on_surface": "#000000",
            "border": "#000000",
            "shadow": "rgba(0, 0, 0, 0.2)",
            "accent": "#6600cc",  # Purple
            "code_bg": "#ffffcc",
            "code_text": "#000000"
        }
    }
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize theme session state"""
        if 'app_theme' not in st.session_state:
            st.session_state.app_theme = 'light'
        if 'theme_applied' not in st.session_state:
            st.session_state.theme_applied = False
    
    def get_current_theme(self) -> Dict[str, str]:
        """Get current theme colors"""
        theme_name = st.session_state.get('app_theme', 'light')
        return self.THEMES.get(theme_name, self.THEMES['light'])
    
    def apply_theme(self):
        """Apply theme CSS with proper text visibility"""
        theme = self.get_current_theme()
        
        css = f"""
        <style>
        /* Import system fonts for better readability */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* CSS Custom Properties for theme */
        :root {{
            --primary: {theme['primary']};
            --secondary: {theme['secondary']};
            --success: {theme['success']};
            --warning: {theme['warning']};
            --error: {theme['error']};
            --info: {theme['info']};
            --background: {theme['background']};
            --surface: {theme['surface']};
            --surface-variant: {theme['surface_variant']};
            --text-primary: {theme['text_primary']};
            --text-secondary: {theme['text_secondary']};
            --text-on-primary: {theme['text_on_primary']};
            --text-on-surface: {theme['text_on_surface']};
            --border: {theme['border']};
            --shadow: {theme['shadow']};
            --accent: {theme['accent']};
            --code-bg: {theme['code_bg']};
            --code-text: {theme['code_text']};
        }}
        
        /* Base application styles */
        .stApp {{
            background-color: var(--background);
            color: var(--text-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        
        /* Ensure text visibility on all elements */
        .stApp * {{
            color: inherit;
        }}
        
        /* Headers with proper contrast */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-primary);
            font-weight: 600;
            line-height: 1.2;
        }}
        
        /* Paragraphs and text */
        p, .stMarkdown, .stText {{
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        /* Links */
        a {{
            color: var(--primary);
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* Sidebar specific styles */
        section[data-testid="stSidebar"] {{
            background-color: var(--surface);
            color: var(--text-on-surface);
        }}
        
        section[data-testid="stSidebar"] * {{
            color: var(--text-on-surface);
        }}
        
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stCheckbox label {{
            color: var(--text-on-surface);
            font-weight: 500;
        }}
        
        /* Button styles with proper contrast */
        .stButton > button {{
            background-color: var(--primary);
            color: var(--text-on-primary);
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .stButton > button:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        
        /* Secondary buttons */
        .stButton > button[kind="secondary"] {{
            background-color: var(--surface-variant);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }}
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            background-color: var(--surface);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
        }}
        
        /* Labels */
        .stTextInput > label,
        .stTextArea > label,
        .stSelectbox > label,
        .stRadio > label,
        .stCheckbox > label {{
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 0.25rem;
        }}
        
        /* Metrics */
        [data-testid="metric-container"] {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
        }}
        
        [data-testid="metric-container"] [data-testid="metric-label"] {{
            color: var(--text-secondary);
        }}
        
        [data-testid="metric-container"] [data-testid="metric-value"] {{
            color: var(--text-primary);
        }}
        
        /* Info, warning, error boxes */
        .stAlert {{
            border-radius: 8px;
            border: 1px solid;
        }}
        
        div[data-baseweb="notification"][kind="info"] {{
            background-color: var(--info);
            color: var(--text-on-primary);
            border-color: var(--info);
        }}
        
        div[data-baseweb="notification"][kind="warning"] {{
            background-color: var(--warning);
            color: var(--text-on-primary);
            border-color: var(--warning);
        }}
        
        div[data-baseweb="notification"][kind="error"] {{
            background-color: var(--error);
            color: var(--text-on-primary);
            border-color: var(--error);
        }}
        
        div[data-baseweb="notification"][kind="success"] {{
            background-color: var(--success);
            color: var(--text-on-primary);
            border-color: var(--success);
        }}
        
        /* Code blocks */
        pre, code {{
            background-color: var(--code-bg);
            color: var(--code-text);
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        
        /* Tables */
        .stTable {{
            background-color: var(--surface);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .stTable th {{
            background-color: var(--surface-variant);
            color: var(--text-primary);
            font-weight: 600;
        }}
        
        .stTable td {{
            color: var(--text-primary);
        }}
        
        /* Progress bars */
        .stProgress > div > div {{
            background-color: var(--primary);
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: var(--surface);
            color: var(--text-primary);
            border-radius: 8px;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: var(--surface);
            border-radius: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            color: var(--text-primary);
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: var(--surface-variant);
        }}
        
        /* File uploader */
        .stFileUploader > div {{
            background-color: var(--surface);
            border: 2px dashed var(--border);
            border-radius: 8px;
            color: var(--text-primary);
        }}
        
        /* Ensure help text is visible */
        .stHelp {{
            color: var(--text-secondary);
        }}
        
        /* Ensure all text in the main area is visible */
        .main .block-container {{
            color: var(--text-primary);
        }}
        
        /* Fix for any remaining visibility issues */
        .element-container {{
            color: var(--text-primary);
        }}
        
        /* Remove any conflicting styles */
        .css-1d391kg {{
            background-color: var(--surface);
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
        st.session_state.theme_applied = True
    
    def render_theme_selector(self):
        """Render theme selector in sidebar"""
        with st.sidebar:
            theme_options = list(self.THEMES.keys())
            theme_names = [self.THEMES[key]['name'] for key in theme_options]
            
            current_idx = theme_options.index(st.session_state.app_theme)
            
            selected_name = st.selectbox(
                "🎨 Theme",
                theme_names,
                index=current_idx,
                help="Choose a color theme for better visibility"
            )
            
            # Map back to theme key
            selected_idx = theme_names.index(selected_name)
            selected_theme = theme_options[selected_idx]
            
            if selected_theme != st.session_state.app_theme:
                st.session_state.app_theme = selected_theme
                st.session_state.theme_applied = False
                st.rerun()


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get or create theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme():
    """Apply the current theme"""
    manager = get_theme_manager()
    if not st.session_state.get('theme_applied', False):
        manager.apply_theme()


def render_theme_selector():
    """Render theme selector in sidebar"""
    manager = get_theme_manager()
    manager.render_theme_selector()


# Additional utility functions for specific styling needs
def style_metric_card(label: str, value: str, delta: Optional[str] = None, 
                     delta_color: str = "normal") -> str:
    """Create a styled metric card"""
    theme = get_theme_manager().get_current_theme()
    
    delta_html = ""
    if delta:
        delta_color_map = {
            "normal": theme['text_secondary'],
            "positive": theme['success'],
            "negative": theme['error']
        }
        color = delta_color_map.get(delta_color, theme['text_secondary'])
        delta_html = f'<div style="color: {color}; font-size: 0.9rem;">{delta}</div>'
    
    return f"""
    <div style="
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px {theme['shadow']};
    ">
        <div style="color: {theme['text_secondary']}; font-size: 0.9rem; font-weight: 500;">
            {label}
        </div>
        <div style="color: {theme['text_primary']}; font-size: 1.5rem; font-weight: 600; margin: 0.25rem 0;">
            {value}
        </div>
        {delta_html}
    </div>
    """


def style_info_box(content: str, type: str = "info") -> str:
    """Create a styled info/warning/error box"""
    theme = get_theme_manager().get_current_theme()
    
    type_styles = {
        "info": {
            "bg": theme['info'],
            "text": theme['text_on_primary'],
            "icon": "ℹ️"
        },
        "warning": {
            "bg": theme['warning'],
            "text": theme['text_on_primary'],
            "icon": "⚠️"
        },
        "error": {
            "bg": theme['error'],
            "text": theme['text_on_primary'],
            "icon": "❌"
        },
        "success": {
            "bg": theme['success'],
            "text": theme['text_on_primary'],
            "icon": "✅"
        }
    }
    
    style = type_styles.get(type, type_styles["info"])
    
    return f"""
    <div style="
        background-color: {style['bg']};
        color: {style['text']};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    ">
        <span style="font-size: 1.2rem;">{style['icon']}</span>
        <div>{content}</div>
    </div>
    """