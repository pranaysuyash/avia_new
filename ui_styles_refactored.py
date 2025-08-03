#!/usr/bin/env python3
"""
Refactored UI Styles - Enterprise-grade styling system
Single source of truth for all visual styling
"""

import streamlit as st
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Color palettes for different themes
THEMES = {
    "light": {
        "primary": "#3b82f6",      # Modern blue
        "secondary": "#8b5cf6",    # Purple accent
        "success": "#10b981",      # Green
        "warning": "#f59e0b",      # Amber
        "error": "#ef4444",        # Red
        "info": "#06b6d4",         # Cyan
        "background": "#ffffff",
        "surface": "#f9fafb",
        "surface_variant": "#f3f4f6",
        "text_primary": "#111827",
        "text_secondary": "#6b7280",
        "border": "#e5e7eb",
        "shadow": "rgba(0, 0, 0, 0.05)",
        "accent": "#ec4899",       # Pink accent
        "hover": "#f3f4f6",
        "active": "#e5e7eb"
    },
    "dark": {
        "primary": "#60a5fa",      # Lighter blue for dark mode
        "secondary": "#a78bfa",    # Lighter purple
        "success": "#34d399",      # Lighter green
        "warning": "#fbbf24",      # Lighter amber
        "error": "#f87171",        # Lighter red
        "info": "#22d3ee",         # Lighter cyan
        "background": "#0f172a",   # Slate 900
        "surface": "#1e293b",      # Slate 800
        "surface_variant": "#334155", # Slate 700
        "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8",
        "border": "#475569",
        "shadow": "rgba(0, 0, 0, 0.3)",
        "accent": "#f472b6",       # Lighter pink
        "hover": "#334155",
        "active": "#475569"
    }
}

def get_theme_colors(theme_name: str = "light") -> Dict[str, str]:
    """Get color palette for specified theme"""
    return THEMES.get(theme_name, THEMES["light"])

def apply_theme(theme: str = "light"):
    """Apply theme with centralized styling - single source of truth"""
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
        --hover-color: {colors['hover']};
        --active-color: {colors['active']};
        
        /* Spacing system */
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
        --spacing-2xl: 3rem;
        
        /* Border radius system */
        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
        --radius-full: 9999px;
        
        /* Transition system */
        --transition-fast: 150ms ease;
        --transition-base: 300ms ease;
        --transition-slow: 500ms ease;
    }}
    
    /* Global styles - targeting generic elements */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-primary-color);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: background-color var(--transition-base);
    }}
    
    /* Main container - use data-testid for stability */
    [data-testid="stAppViewContainer"] {{
        background-color: var(--background-color);
    }}
    
    /* Sidebar - target by data-testid */
    [data-testid="stSidebar"] {{
        background-color: var(--surface-color);
        border-right: 1px solid var(--border-color);
    }}
    
    /* Headers - generic targeting */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-primary-color);
        font-weight: 600;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }}
    
    /* Buttons - target Streamlit button classes generically */
    .stButton > button {{
        background-color: var(--surface-color);
        color: var(--text-primary-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: var(--spacing-sm) var(--spacing-lg);
        font-weight: 500;
        transition: all var(--transition-fast);
        box-shadow: 0 1px 2px var(--shadow-color);
    }}
    
    .stButton > button:hover {{
        background-color: var(--hover-color);
        border-color: var(--primary-color);
        box-shadow: 0 2px 4px var(--shadow-color);
    }}
    
    /* Primary button styling */
    .stButton > button[kind="primary"] {{
        background-color: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background-color: var(--secondary-color);
        border-color: var(--secondary-color);
    }}
    
    /* Reusable utility classes */
    .metric-card {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        text-align: center;
        box-shadow: 0 1px 3px var(--shadow-color);
        transition: all var(--transition-fast);
    }}
    
    .metric-card:hover {{
        border-color: var(--primary-color);
        box-shadow: 0 4px 6px var(--shadow-color);
    }}
    
    .entity-tag {{
        display: inline-block;
        padding: var(--spacing-xs) var(--spacing-md);
        margin: var(--spacing-xs);
        border-radius: var(--radius-full);
        font-size: 0.875rem;
        font-weight: 500;
        transition: all var(--transition-fast);
    }}
    
    .entity-tag-person {{
        background-color: var(--primary-color);
        color: white;
    }}
    
    .entity-tag-org {{
        background-color: var(--secondary-color);
        color: white;
    }}
    
    .entity-tag-location {{
        background-color: var(--success-color);
        color: white;
    }}
    
    .entity-tag-date {{
        background-color: var(--warning-color);
        color: white;
    }}
    
    /* Progress bar styling */
    .stProgress > div > div {{
        background-color: var(--primary-color);
        transition: width var(--transition-base);
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: var(--surface-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-xs);
        gap: var(--spacing-xs);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: var(--radius-md);
        padding: var(--spacing-sm) var(--spacing-lg);
        background-color: transparent;
        color: var(--text-secondary-color);
        font-weight: 500;
        transition: all var(--transition-fast);
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: var(--hover-color);
        color: var(--text-primary-color);
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--background-color);
        color: var(--primary-color);
        box-shadow: 0 1px 3px var(--shadow-color);
    }}
    
    /* Input fields */
    .stTextInput > div > div > input {{
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary-color);
        padding: var(--spacing-sm) var(--spacing-md);
        transition: all var(--transition-fast);
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }}
    
    /* Select boxes */
    .stSelectbox > div > div {{
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        transition: all var(--transition-fast);
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
        font-weight: 500;
        transition: all var(--transition-fast);
    }}
    
    .streamlit-expanderHeader:hover {{
        background-color: var(--hover-color);
        border-color: var(--primary-color);
    }}
    
    /* Cards and containers */
    .content-card {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-xl);
        margin: var(--spacing-md) 0;
        box-shadow: 0 1px 3px var(--shadow-color);
    }}
    
    /* Audio player container */
    .audio-player-container {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        margin: var(--spacing-md) 0;
    }}
    
    /* File uploader */
    .stFileUploader > div {{
        background-color: var(--surface-color);
        border: 2px dashed var(--border-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-xl);
        transition: all var(--transition-fast);
    }}
    
    .stFileUploader > div:hover {{
        border-color: var(--primary-color);
        background-color: var(--hover-color);
    }}
    
    /* Metrics display */
    [data-testid="metric-container"] {{
        background-color: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        box-shadow: 0 1px 3px var(--shadow-color);
    }}
    
    /* Success/Error/Warning/Info messages */
    .stAlert {{
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
        border-width: 1px;
    }}
    
    /* Code blocks */
    .stCodeBlock {{
        background-color: var(--surface-variant-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
    }}
    
    /* Horizontal line */
    hr {{
        border: none;
        border-top: 1px solid var(--border-color);
        margin: var(--spacing-xl) 0;
    }}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--surface-color);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border-color);
        border-radius: var(--radius-sm);
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-secondary-color);
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateX(-100%); }}
        to {{ transform: translateX(0); }}
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    
    /* Apply smooth transitions to all interactive elements */
    button, input, select, textarea, a {{
        transition: all var(--transition-fast);
    }}
    
    /* Focus states for accessibility */
    *:focus {{
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }}
    
    /* Ensure text remains visible */
    p, span, div, label {{
        color: var(--text-primary-color);
    }}
    
    /* Caption and help text */
    .caption, [data-testid="caption"] {{
        color: var(--text-secondary-color);
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)