"""
Theme and Visibility Manager
Handles CSS theming, contrast checking, and accessibility features
"""

import streamlit as st
from typing import Dict, Any, Tuple
import colorsys


class ThemeManager:
    """Manage themes, contrast, and visual accessibility"""
    
    def __init__(self):
        self.themes = {
            'light': {
                'primary_color': '#0066cc',
                'background_color': '#ffffff',
                'secondary_background_color': '#f8f9fa',
                'text_color': '#000000',
                'secondary_text_color': '#333333',
                'success_color': '#007700',
                'error_color': '#cc0000',
                'warning_color': '#ff6600',
                'info_color': '#0066cc'
            },
            'dark': {
                'primary_color': '#ff6b6b',
                'background_color': '#0e1117',
                'secondary_background_color': '#262730',
                'text_color': '#fafafa',
                'secondary_text_color': '#a4a8b6',
                'success_color': '#09ab3b',
                'error_color': '#ff6565',
                'warning_color': '#ffab00',
                'info_color': '#00d4ff'
            },
            'high_contrast': {
                'primary_color': '#0066cc',
                'background_color': '#ffffff',
                'secondary_background_color': '#f8f9fa',
                'text_color': '#000000',
                'secondary_text_color': '#333333',
                'success_color': '#007700',
                'error_color': '#cc0000',
                'warning_color': '#ff8800',
                'info_color': '#0066cc'
            },
            'accessibility': {
                'primary_color': '#0073e6',
                'background_color': '#ffffff',
                'secondary_background_color': '#f5f5f5',
                'text_color': '#000000',
                'secondary_text_color': '#4a4a4a',
                'success_color': '#228b22',
                'error_color': '#dc143c',
                'warning_color': '#ff8c00',
                'info_color': '#1e90ff'
            }
        }
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to hex color"""
        return '#%02x%02x%02x' % rgb
    
    def calculate_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance of a color"""
        def normalize(channel):
            channel = channel / 255.0
            if channel <= 0.03928:
                return channel / 12.92
            else:
                return pow((channel + 0.055) / 1.055, 2.4)
        
        r, g, b = rgb
        return 0.2126 * normalize(r) + 0.7152 * normalize(g) + 0.0722 * normalize(b)
    
    def calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors"""
        rgb1 = self.hex_to_rgb(color1)
        rgb2 = self.hex_to_rgb(color2)
        
        lum1 = self.calculate_luminance(rgb1)
        lum2 = self.calculate_luminance(rgb2)
        
        # Ensure lighter color is numerator
        if lum1 > lum2:
            return (lum1 + 0.05) / (lum2 + 0.05)
        else:
            return (lum2 + 0.05) / (lum1 + 0.05)
    
    def get_accessibility_rating(self, contrast_ratio: float) -> Tuple[str, str]:
        """Get WCAG accessibility rating for contrast ratio"""
        if contrast_ratio >= 7.0:
            return "AAA", "🟢 Excellent"
        elif contrast_ratio >= 4.5:
            return "AA", "🟡 Good"
        elif contrast_ratio >= 3.0:
            return "A", "🟠 Fair"
        else:
            return "FAIL", "🔴 Poor"
    
    def apply_theme(self, theme_name: str = 'light'):
        """Apply theme to Streamlit app with aggressive CSS"""
        if theme_name not in self.themes:
            theme_name = 'light'
        
        theme = self.themes[theme_name]
        
        # AGGRESSIVE CSS for maximum visibility
        css = f"""
        <style>
        /* FORCE text color everywhere */
        * {{
            color: {theme['text_color']} !important;
        }}
        
        /* Main app styling */
        .stApp {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* ALL text elements */
        .stMarkdown, .stMarkdown *, .stText, .stText *, 
        p, div, span, label, .stSelectbox label, 
        .stFileUploader label, .stSlider label,
        .stCheckbox label, .stRadio label {{
            color: {theme['text_color']} !important;
            font-weight: 500 !important;
        }}
        
        /* Sidebar styling with high contrast */
        .css-1d391kg, .css-1d391kg *, 
        [data-testid="stSidebar"], [data-testid="stSidebar"] * {{
            background-color: {theme['secondary_background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Sidebar text specifically */  
        .css-1d391kg .stMarkdown, 
        .css-1d391kg .stMarkdown *,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stMarkdown * {{
            color: {theme['text_color']} !important;
            font-weight: 600 !important;
        }}
        
        /* Headers with maximum contrast */
        h1, h2, h3, h4, h5, h6 {{
            color: {theme['text_color']} !important;
            font-weight: bold !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1) !important;
        }}
        
        /* Input labels with dark text */
        .stSelectbox > label, .stFileUploader > label, 
        .stSlider > label, .stCheckbox > label,
        .stRadio > label, .stTextInput > label {{
            color: {theme['text_color']} !important;
            font-weight: 600 !important;
            font-size: 1.1em !important;
        }}
        
        /* Force all paragraphs to be visible */
        p, .stMarkdown p {{
            color: {theme['text_color']} !important;
            font-weight: 500 !important;
        }}
        
        /* Configuration section visibility */
        .stSelectbox, .stCheckbox, .stSlider {{
            color: {theme['text_color']} !important;
        }}
        
        /* File uploader text */
        .stFileUploader .stFileUploadButton {{
            color: white !important;
            background-color: {theme['primary_color']} !important;
        }}
        
        /* Success/Error/Warning with better contrast */
        .stSuccess {{
            background-color: {theme['success_color']}30 !important;
            border: 2px solid {theme['success_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        .stError {{
            background-color: {theme['error_color']}30 !important;
            border: 2px solid {theme['error_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        .stWarning {{
            background-color: {theme['warning_color']}30 !important;
            border: 2px solid {theme['warning_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        .stInfo {{
            background-color: {theme['info_color']}30 !important;
            border: 2px solid {theme['info_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Buttons with high contrast */
        .stButton > button {{
            background-color: {theme['primary_color']} !important;
            color: white !important;
            border: 2px solid {theme['primary_color']} !important;
            font-weight: bold !important;
            font-size: 1.1em !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme['primary_color']}dd !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        }}
        
        /* Expanders with visible headers */
        .streamlit-expanderHeader {{
            background-color: {theme['secondary_background_color']} !important;
            color: {theme['text_color']} !important;
            font-weight: bold !important;
            border: 1px solid {theme['primary_color']} !important;
        }}
        
        /* Tables with high contrast */
        .stDataFrame table {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
            border: 1px solid {theme['primary_color']} !important;
        }}
        
        .stDataFrame th {{
            background-color: {theme['secondary_background_color']} !important;
            color: {theme['text_color']} !important;
            font-weight: bold !important;
        }}
        
        /* Audio controls */
        .stAudio {{
            background-color: {theme['secondary_background_color']} !important;
            border: 2px solid {theme['primary_color']} !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }}
        
        /* Progress bars */
        .stProgress > div > div > div {{
            background-color: {theme['primary_color']} !important;
        }}
        
        /* Custom high visibility class */
        .high-visibility {{
            color: {theme['text_color']} !important;
            background-color: {theme['background_color']} !important;
            border: 2px solid {theme['primary_color']} !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        
        /* Force visibility on all elements */
        body, body * {{
            color: {theme['text_color']} !important;
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def render_theme_selector(self):
        """Render theme selection interface"""
        st.sidebar.markdown("### 🎨 Theme Settings")
        
        # Theme selector
        current_theme = st.session_state.get('current_theme', 'light')
        theme_options = {
            'light': '☀️ Light Theme',
            'dark': '🌙 Dark Theme', 
            'high_contrast': '🔲 High Contrast',
            'accessibility': '♿ Accessibility'
        }
        
        selected_theme = st.sidebar.selectbox(
            "Choose Theme",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=list(theme_options.keys()).index(current_theme),
            key="theme_selector"
        )
        
        if selected_theme != current_theme:
            st.session_state.current_theme = selected_theme
            st.rerun()
        
        # Apply the selected theme
        self.apply_theme(selected_theme)
        
        # Font size controls
        font_size = st.sidebar.slider(
            "Font Size",
            min_value=12,
            max_value=20,
            value=st.session_state.get('font_size', 14),
            key="font_size_slider"
        )
        
        if font_size != st.session_state.get('font_size', 14):
            st.session_state.font_size = font_size
            # Apply font size CSS
            font_css = f"""
            <style>
            .stApp, .stMarkdown, p, div, span {{
                font-size: {font_size}px !important;
            }}
            </style>
            """
            st.markdown(font_css, unsafe_allow_html=True)
    
    def render_accessibility_checker(self):
        """Render accessibility testing interface"""
        st.subheader("♿ Accessibility Checker")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fg_color = st.color_picker("Foreground Color", "#000000", key="fg_color")
        
        with col2:
            bg_color = st.color_picker("Background Color", "#ffffff", key="bg_color")
        
        # Calculate contrast ratio
        contrast_ratio = self.calculate_contrast_ratio(fg_color, bg_color)
        rating, status = self.get_accessibility_rating(contrast_ratio)
        
        # Display results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Contrast Ratio", f"{contrast_ratio:.2f}:1")
        
        with col2:
            st.metric("WCAG Rating", rating)
        
        with col3:
            st.markdown(f"**Status:** {status}")
        
        # Preview
        st.markdown("### Preview")
        preview_css = f"""
        <div style="
            background-color: {bg_color};
            color: {fg_color};
            padding: 2rem;
            border: 1px solid #ccc;
            border-radius: 0.5rem;
            text-align: center;
            margin: 1rem 0;
        ">
            <h3 style="color: {fg_color}; margin-bottom: 1rem;">Sample Heading</h3>
            <p style="color: {fg_color}; margin-bottom: 1rem;">
                This is sample text to test the contrast ratio between foreground and background colors.
                Good contrast ensures that text is readable for all users, including those with visual impairments.
            </p>
            <button style="
                background-color: {fg_color};
                color: {bg_color};
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 0.25rem;
                cursor: pointer;
            ">Sample Button</button>
        </div>
        """
        st.markdown(preview_css, unsafe_allow_html=True)
        
        # Recommendations
        if contrast_ratio < 4.5:
            st.warning("⚠️ Consider improving contrast for better accessibility")
            
            # Suggest better colors
            st.markdown("### 💡 Suggestions")
            
            # Try to improve the colors
            fg_rgb = self.hex_to_rgb(fg_color)
            bg_rgb = self.hex_to_rgb(bg_color)
            
            # Make foreground darker if needed
            if contrast_ratio < 4.5:
                # Darken foreground
                darker_fg = tuple(max(0, c - 50) for c in fg_rgb)
                darker_fg_hex = self.rgb_to_hex(darker_fg)
                improved_ratio = self.calculate_contrast_ratio(darker_fg_hex, bg_color)
                
                st.markdown(f"**Darker foreground:** {darker_fg_hex} (Ratio: {improved_ratio:.2f}:1)")
                
                # Lighten background
                lighter_bg = tuple(min(255, c + 50) for c in bg_rgb)
                lighter_bg_hex = self.rgb_to_hex(lighter_bg)
                improved_ratio2 = self.calculate_contrast_ratio(fg_color, lighter_bg_hex)
                
                st.markdown(f"**Lighter background:** {lighter_bg_hex} (Ratio: {improved_ratio2:.2f}:1)")


def render_enhanced_metric(label: str, value: str, delta: str = None, help_text: str = None):
    """Render enhanced metric with better visibility"""
    metric_html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-delta" style="color: #28a745;">{delta}</div>' if delta else ''}
        {f'<div class="metric-help" style="color: #6c757d; font-size: 0.8rem; margin-top: 0.5rem;">{help_text}</div>' if help_text else ''}
    </div>
    """
    st.markdown(metric_html, unsafe_allow_html=True)


def check_text_visibility():
    """Check if text is visible with current theme"""
    # This would analyze the current page for text visibility issues
    # For now, return basic recommendations
    return {
        'issues_found': False,
        'recommendations': [
            "Ensure sufficient contrast between text and background",
            "Use consistent font sizes throughout the app",
            "Test with different themes for accessibility",
            "Provide keyboard navigation support"
        ]
    }


# Initialize theme manager
theme_manager = ThemeManager()


def apply_custom_theme():
    """Apply custom theme based on user preferences"""
    current_theme = st.session_state.get('current_theme', 'light')
    theme_manager.apply_theme(current_theme)


# Export main functions
__all__ = [
    'ThemeManager',
    'theme_manager', 
    'render_enhanced_metric',
    'check_text_visibility',
    'apply_custom_theme'
]