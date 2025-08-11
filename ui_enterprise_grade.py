"""
Enterprise-Grade UI/UX System for Transcription App
Complete redesign with professional aesthetics and advanced interactions
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, List, Optional, Any, Tuple
import json
import time
from datetime import datetime
import random

class EnterpriseUI:
    """Enterprise-grade UI system with professional design patterns"""
    
    # Professional Color Palette
    COLORS = {
        'light': {
            # Primary Colors
            'primary': '#1E40AF',        # Deep blue
            'primary_hover': '#1E3A8A',
            'primary_light': '#DBEAFE',
            
            # Secondary Colors  
            'secondary': '#7C3AED',       # Purple
            'secondary_hover': '#6D28D9',
            'secondary_light': '#EDE9FE',
            
            # Accent Colors
            'accent': '#10B981',          # Emerald
            'accent_hover': '#059669',
            'accent_light': '#D1FAE5',
            
            # Status Colors
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'info': '#3B82F6',
            
            # Neutral Colors
            'background': '#FFFFFF',
            'surface': '#F9FAFB',
            'card': '#FFFFFF',
            'border': '#E5E7EB',
            'text_primary': '#111827',
            'text_secondary': '#6B7280',
            'text_muted': '#9CA3AF',
            
            # Gradient Backgrounds
            'gradient_primary': 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
            'gradient_secondary': 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
            'gradient_accent': 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
            'gradient_dark': 'linear-gradient(135deg, #1E3A8A 0%, #312E81 100%)',
        },
        'dark': {
            # Primary Colors
            'primary': '#3B82F6',
            'primary_hover': '#2563EB',
            'primary_light': '#1E3A8A',
            
            # Secondary Colors
            'secondary': '#8B5CF6',
            'secondary_hover': '#7C3AED',
            'secondary_light': '#312E81',
            
            # Accent Colors
            'accent': '#10B981',
            'accent_hover': '#059669',
            'accent_light': '#064E3B',
            
            # Status Colors
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'info': '#3B82F6',
            
            # Neutral Colors
            'background': '#0F172A',
            'surface': '#1E293B',
            'card': '#1E293B',
            'border': '#334155',
            'text_primary': '#F9FAFB',
            'text_secondary': '#CBD5E1',
            'text_muted': '#94A3B8',
            
            # Gradient Backgrounds
            'gradient_primary': 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
            'gradient_secondary': 'linear-gradient(135deg, #F093FB 0%, #F5576C 100%)',
            'gradient_accent': 'linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%)',
            'gradient_dark': 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
        }
    }
    
    @staticmethod
    def inject_enterprise_css():
        """Inject enterprise-grade CSS with animations and modern design"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        css = f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
            
            /* Global Styles */
            .stApp {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: {colors['background']};
                color: {colors['text_primary']};
            }}
            
            /* Enhanced Typography */
            h1, h2, h3, h4, h5, h6 {{
                font-weight: 700;
                letter-spacing: -0.02em;
                color: {colors['text_primary']};
            }}
            
            /* Professional Card Design */
            .enterprise-card {{
                background: {colors['card']};
                border: 1px solid {colors['border']};
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            .enterprise-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }}
            
            /* Glass Morphism Effect */
            .glass-card {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 24px;
            }}
            
            /* Premium Buttons */
            .premium-button {{
                background: {colors['gradient_primary']};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.025em;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                position: relative;
                overflow: hidden;
            }}
            
            .premium-button::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s ease;
            }}
            
            .premium-button:hover::before {{
                left: 100%;
            }}
            
            .premium-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            }}
            
            /* Smooth Animations */
            @keyframes slideInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
            
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            
            .animate-slide-in {{
                animation: slideInUp 0.5s ease-out;
            }}
            
            .animate-fade-in {{
                animation: fadeIn 0.3s ease-out;
            }}
            
            .animate-pulse {{
                animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }}
            
            /* Professional Sidebar */
            section[data-testid="stSidebar"] {{
                background: {colors['surface']};
                border-right: 1px solid {colors['border']};
                box-shadow: 2px 0 4px rgba(0, 0, 0, 0.05);
            }}
            
            section[data-testid="stSidebar"] > div {{
                padding-top: 2rem;
            }}
            
            /* Enhanced Form Elements */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > div {{
                background: {colors['background']};
                border: 2px solid {colors['border']};
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                transition: all 0.2s ease;
            }}
            
            .stTextInput > div > div > input:focus,
            .stTextArea > div > div > textarea:focus {{
                border-color: {colors['primary']};
                box-shadow: 0 0 0 3px {colors['primary_light']};
                outline: none;
            }}
            
            /* Status Indicators */
            .status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                border-radius: 9999px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            
            .status-badge.success {{
                background: {colors['accent_light']};
                color: {colors['accent']};
            }}
            
            .status-badge.warning {{
                background: #FEF3C7;
                color: {colors['warning']};
            }}
            
            .status-badge.error {{
                background: #FEE2E2;
                color: {colors['error']};
            }}
            
            /* Progress Indicators */
            .progress-ring {{
                transform: rotate(-90deg);
                transition: stroke-dashoffset 0.5s ease;
            }}
            
            /* Tooltip Styling */
            .tooltip {{
                position: relative;
                display: inline-block;
            }}
            
            .tooltip .tooltiptext {{
                visibility: hidden;
                background: {colors['text_primary']};
                color: {colors['background']};
                text-align: center;
                border-radius: 8px;
                padding: 8px 12px;
                position: absolute;
                z-index: 1000;
                bottom: 125%;
                left: 50%;
                margin-left: -60px;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 12px;
                font-weight: 500;
                white-space: nowrap;
            }}
            
            .tooltip:hover .tooltiptext {{
                visibility: visible;
                opacity: 1;
            }}
            
            /* Modern Scrollbar */
            ::-webkit-scrollbar {{
                width: 10px;
                height: 10px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: {colors['surface']};
                border-radius: 10px;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: {colors['border']};
                border-radius: 10px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: {colors['text_muted']};
            }}
            
            /* Floating Action Button */
            .fab {{
                position: fixed;
                bottom: 24px;
                right: 24px;
                width: 56px;
                height: 56px;
                border-radius: 28px;
                background: {colors['gradient_primary']};
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                cursor: pointer;
                transition: all 0.3s ease;
                z-index: 1000;
            }}
            
            .fab:hover {{
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
            }}
            
            /* Modern Tabs */
            .enterprise-tabs {{
                display: flex;
                gap: 8px;
                padding: 4px;
                background: {colors['surface']};
                border-radius: 12px;
                margin-bottom: 24px;
            }}
            
            .enterprise-tab {{
                flex: 1;
                padding: 12px 24px;
                background: transparent;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                color: {colors['text_secondary']};
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            
            .enterprise-tab.active {{
                background: {colors['background']};
                color: {colors['primary']};
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}
            
            .enterprise-tab:hover:not(.active) {{
                background: {colors['background']};
                opacity: 0.7;
            }}
            
            /* Data Table Styling */
            .enterprise-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
            }}
            
            .enterprise-table thead tr {{
                background: {colors['surface']};
            }}
            
            .enterprise-table th {{
                padding: 12px 16px;
                text-align: left;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: {colors['text_secondary']};
                border-bottom: 2px solid {colors['border']};
            }}
            
            .enterprise-table td {{
                padding: 16px;
                border-bottom: 1px solid {colors['border']};
            }}
            
            .enterprise-table tbody tr:hover {{
                background: {colors['surface']};
            }}
            
            /* Loading Skeleton */
            .skeleton {{
                background: linear-gradient(90deg, {colors['surface']} 25%, {colors['border']} 50%, {colors['surface']} 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
            }}
            
            @keyframes loading {{
                0% {{ background-position: 200% 0; }}
                100% {{ background-position: -200% 0; }}
            }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    @staticmethod
    def create_header(title: str, subtitle: str = "", icon: str = "🎯"):
        """Create professional header with gradient background"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        header_html = f"""
        <div class="animate-slide-in" style="
            background: {colors['gradient_primary']};
            border-radius: 20px;
            padding: 32px;
            margin-bottom: 32px;
            position: relative;
            overflow: hidden;
        ">
            <div style="position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 8px;">
                    <span style="font-size: 48px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));">{icon}</span>
                    <h1 style="
                        color: white;
                        font-size: 36px;
                        font-weight: 800;
                        margin: 0;
                        letter-spacing: -0.03em;
                    ">{title}</h1>
                </div>
                {f'<p style="color: rgba(255,255,255,0.9); font-size: 16px; margin: 0;">{subtitle}</p>' if subtitle else ''}
            </div>
            <div style="
                position: absolute;
                top: -50%;
                right: -10%;
                width: 300px;
                height: 300px;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
            "></div>
            <div style="
                position: absolute;
                bottom: -30%;
                left: -5%;
                width: 200px;
                height: 200px;
                background: rgba(255,255,255,0.05);
                border-radius: 50%;
            "></div>
        </div>
        """
        
        st.markdown(header_html, unsafe_allow_html=True)
    
    @staticmethod
    def create_metric_card(title: str, value: str, change: str = "", icon: str = "📊", color: str = "primary"):
        """Create professional metric card with animations"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        change_color = colors['success'] if change.startswith('+') else colors['error'] if change.startswith('-') else colors['text_secondary']
        
        return f"""
        <div class="enterprise-card animate-fade-in" style="
            background: {colors['card']};
            border: 1px solid {colors['border']};
            border-radius: 16px;
            padding: 24px;
            height: 100%;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
                <div style="
                    width: 48px;
                    height: 48px;
                    background: {colors[f'{color}_light']};
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                ">{icon}</div>
                {f'<span style="color: {change_color}; font-size: 14px; font-weight: 600;">{change}</span>' if change else ''}
            </div>
            <div style="color: {colors['text_secondary']}; font-size: 14px; font-weight: 500; margin-bottom: 4px;">
                {title}
            </div>
            <div style="color: {colors['text_primary']}; font-size: 32px; font-weight: 700; letter-spacing: -0.02em;">
                {value}
            </div>
        </div>
        """
    
    @staticmethod
    def create_progress_ring(percentage: float, size: int = 120, stroke_width: int = 8):
        """Create animated circular progress indicator"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        radius = (size - stroke_width) / 2
        circumference = radius * 2 * 3.14159
        stroke_dashoffset = circumference - (percentage / 100) * circumference
        
        return f"""
        <div style="position: relative; width: {size}px; height: {size}px;">
            <svg width="{size}" height="{size}" style="transform: rotate(-90deg);">
                <circle
                    cx="{size/2}"
                    cy="{size/2}"
                    r="{radius}"
                    stroke="{colors['border']}"
                    stroke-width="{stroke_width}"
                    fill="none"
                />
                <circle
                    cx="{size/2}"
                    cy="{size/2}"
                    r="{radius}"
                    stroke="url(#gradient)"
                    stroke-width="{stroke_width}"
                    fill="none"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{stroke_dashoffset}"
                    stroke-linecap="round"
                    style="transition: stroke-dashoffset 0.5s ease;"
                />
                <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{colors['primary']};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{colors['secondary']};stop-opacity:1" />
                    </linearGradient>
                </defs>
            </svg>
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
            ">
                <div style="font-size: 24px; font-weight: 700; color: {colors['text_primary']};">
                    {percentage:.1f}%
                </div>
                <div style="font-size: 12px; color: {colors['text_secondary']};">
                    Complete
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def create_status_timeline(items: List[Dict[str, Any]]):
        """Create professional status timeline"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        timeline_html = '<div style="position: relative; padding: 20px 0;">'
        
        for i, item in enumerate(items):
            status_color = colors['success'] if item['status'] == 'completed' else colors['warning'] if item['status'] == 'in_progress' else colors['text_muted']
            
            timeline_html += f"""
            <div style="display: flex; align-items: flex-start; margin-bottom: 32px;" class="animate-slide-in" style="animation-delay: {i * 0.1}s;">
                <div style="position: relative;">
                    <div style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: {'linear-gradient(135deg, ' + colors['success'] + ' 0%, ' + colors['accent'] + ' 100%)' if item['status'] == 'completed' else colors['surface']};
                        border: 3px solid {status_color};
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: {'white' if item['status'] == 'completed' else status_color};
                        font-weight: 700;
                    ">
                        {item.get('icon', '✓' if item['status'] == 'completed' else str(i+1))}
                    </div>
                    {f'''<div style="
                        position: absolute;
                        top: 40px;
                        left: 19px;
                        width: 2px;
                        height: 60px;
                        background: {colors['border']};
                    "></div>''' if i < len(items) - 1 else ''}
                </div>
                <div style="margin-left: 20px; flex: 1;">
                    <div style="font-weight: 600; color: {colors['text_primary']}; margin-bottom: 4px;">
                        {item['title']}
                    </div>
                    <div style="font-size: 14px; color: {colors['text_secondary']}; margin-bottom: 4px;">
                        {item.get('description', '')}
                    </div>
                    <div style="font-size: 12px; color: {colors['text_muted']};">
                        {item.get('time', '')}
                    </div>
                </div>
            </div>
            """
        
        timeline_html += '</div>'
        return timeline_html
    
    @staticmethod
    def create_action_button(text: str, icon: str = "", variant: str = "primary", full_width: bool = False):
        """Create professional action button with hover effects"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        button_id = f"btn_{random.randint(1000, 9999)}"
        
        gradient = colors[f'gradient_{variant}'] if f'gradient_{variant}' in colors else colors['gradient_primary']
        
        return f"""
        <button id="{button_id}" class="premium-button" style="
            background: {gradient};
            width: {'100%' if full_width else 'auto'};
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        ">
            {f'<span style="font-size: 18px;">{icon}</span>' if icon else ''}
            <span>{text}</span>
        </button>
        """
    
    @staticmethod
    def create_feature_grid(features: List[Dict[str, str]]):
        """Create professional feature grid layout"""
        theme = st.session_state.get('theme', 'light')
        colors = EnterpriseUI.COLORS[theme]
        
        grid_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 24px 0;">'
        
        for i, feature in enumerate(features):
            grid_html += f"""
            <div class="enterprise-card animate-slide-in" style="animation-delay: {i * 0.05}s;">
                <div style="
                    width: 48px;
                    height: 48px;
                    background: {colors['primary_light']};
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    margin-bottom: 16px;
                ">{feature.get('icon', '🚀')}</div>
                <h3 style="
                    color: {colors['text_primary']};
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 8px;
                ">{feature['title']}</h3>
                <p style="
                    color: {colors['text_secondary']};
                    font-size: 14px;
                    line-height: 1.5;
                ">{feature['description']}</p>
            </div>
            """
        
        grid_html += '</div>'
        return grid_html

def apply_enterprise_theme():
    """Apply enterprise-grade theme to the entire application"""
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Inject enterprise CSS
    EnterpriseUI.inject_enterprise_css()
    
    # Return UI instance for use in app
    return EnterpriseUI()

def render_enterprise_sidebar():
    """Render professional sidebar with modern design"""
    ui = EnterpriseUI()
    theme = st.session_state.get('theme', 'light')
    colors = ui.COLORS[theme]
    
    # Sidebar header with branding
    st.sidebar.markdown(f"""
    <div style="
        background: {colors['gradient_primary']};
        margin: -1rem -1rem 2rem -1rem;
        padding: 2rem 1rem;
        text-align: center;
    ">
        <div style="
            width: 80px;
            height: 80px;
            background: white;
            border-radius: 20px;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        ">🎯</div>
        <h2 style="color: white; margin: 0; font-weight: 700;">TranscribeAI</h2>
        <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 12px;">Enterprise Edition</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation menu with icons
    menu_items = [
        {"icon": "🏠", "label": "Dashboard", "key": "dashboard"},
        {"icon": "📁", "label": "Upload", "key": "upload"},
        {"icon": "📝", "label": "Transcriptions", "key": "transcriptions"},
        {"icon": "🧠", "label": "AI Analysis", "key": "analysis"},
        {"icon": "👥", "label": "Team", "key": "team"},
        {"icon": "⚙️", "label": "Settings", "key": "settings"},
    ]
    
    selected_page = st.sidebar.radio(
        "Navigation",
        options=[item['key'] for item in menu_items],
        format_func=lambda x: next(item['icon'] + " " + item['label'] for item in menu_items if item['key'] == x),
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # Quick stats
    st.sidebar.markdown(f"""
    <div style="
        background: {colors['surface']};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    ">
        <h4 style="margin: 0 0 12px 0; font-size: 14px; color: {colors['text_secondary']};">Quick Stats</h4>
        <div style="display: grid; gap: 8px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: {colors['text_muted']}; font-size: 13px;">Files Processed</span>
                <span style="color: {colors['text_primary']}; font-weight: 600; font-size: 13px;">1,247</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: {colors['text_muted']}; font-size: 13px;">API Status</span>
                <span style="color: {colors['success']}; font-weight: 600; font-size: 13px;">● Online</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: {colors['text_muted']}; font-size: 13px;">Queue</span>
                <span style="color: {colors['text_primary']}; font-weight: 600; font-size: 13px;">3 jobs</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Theme toggle
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("☀️ Light", use_container_width=True, disabled=theme == 'light'):
            st.session_state.theme = 'light'
            st.rerun()
    with col2:
        if st.button("🌙 Dark", use_container_width=True, disabled=theme == 'dark'):
            st.session_state.theme = 'dark'
            st.rerun()
    
    return selected_page

def demo_enterprise_ui():
    """Demonstrate the enterprise UI components"""
    st.set_page_config(
        page_title="Enterprise UI Demo",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply enterprise theme
    ui = apply_enterprise_theme()
    
    # Render sidebar and get selected page
    selected_page = render_enterprise_sidebar()
    
    # Main content area
    if selected_page == "dashboard":
        # Professional header
        ui.create_header(
            "Analytics Dashboard",
            "Real-time insights and performance metrics",
            "📊"
        )
        
        # Metrics grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(ui.create_metric_card(
                "Total Transcriptions",
                "12,847",
                "+12.5%",
                "📝",
                "primary"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(ui.create_metric_card(
                "Processing Time",
                "2.3s",
                "-18%",
                "⚡",
                "accent"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(ui.create_metric_card(
                "Accuracy Rate",
                "98.7%",
                "+2.1%",
                "🎯",
                "secondary"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(ui.create_metric_card(
                "Active Users",
                "156",
                "+8",
                "👥",
                "primary"
            ), unsafe_allow_html=True)
        
        # Progress section
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown("<h3>Processing Status</h3>", unsafe_allow_html=True)
            st.markdown(ui.create_progress_ring(67.5), unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h3>Recent Activity</h3>", unsafe_allow_html=True)
            timeline_items = [
                {
                    "title": "Audio file uploaded",
                    "description": "quarterly_earnings_call.mp4",
                    "time": "2 minutes ago",
                    "status": "completed",
                    "icon": "✅"
                },
                {
                    "title": "Transcription in progress",
                    "description": "Processing with WhisperX model",
                    "time": "Now",
                    "status": "in_progress",
                    "icon": "⚡"
                },
                {
                    "title": "Entity extraction pending",
                    "description": "Waiting for transcription",
                    "time": "Up next",
                    "status": "pending",
                    "icon": "⏳"
                }
            ]
            st.markdown(ui.create_status_timeline(timeline_items), unsafe_allow_html=True)
        
        # Features grid
        st.markdown("<br><h3>Key Features</h3>", unsafe_allow_html=True)
        features = [
            {
                "icon": "🎯",
                "title": "High Accuracy",
                "description": "98.7% transcription accuracy with advanced AI models"
            },
            {
                "icon": "⚡",
                "title": "Fast Processing",
                "description": "Real-time transcription with minimal latency"
            },
            {
                "icon": "🌍",
                "title": "Multi-Language",
                "description": "Support for 50+ languages with automatic detection"
            },
            {
                "icon": "🔒",
                "title": "Enterprise Security",
                "description": "End-to-end encryption and GDPR compliance"
            }
        ]
        st.markdown(ui.create_feature_grid(features), unsafe_allow_html=True)
        
        # Action buttons
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(ui.create_action_button(
                "Start New Transcription",
                "🎤",
                "primary",
                full_width=True
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(ui.create_action_button(
                "View Analytics",
                "📊",
                "secondary",
                full_width=True
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(ui.create_action_button(
                "Export Report",
                "📥",
                "accent",
                full_width=True
            ), unsafe_allow_html=True)
    
    elif selected_page == "upload":
        ui.create_header(
            "Upload & Process",
            "Upload your media files for AI-powered transcription",
            "📁"
        )
        
        # Upload area with modern design
        st.markdown(f"""
        <div class="glass-card" style="
            border: 2px dashed {ui.COLORS[st.session_state.theme]['border']};
            text-align: center;
            padding: 60px 40px;
            cursor: pointer;
            transition: all 0.3s ease;
        ">
            <div style="font-size: 64px; margin-bottom: 20px;">☁️</div>
            <h3 style="margin-bottom: 8px;">Drop your files here</h3>
            <p style="color: {ui.COLORS[st.session_state.theme]['text_secondary']};">
                or click to browse • Supports MP3, WAV, MP4, MOV • Max 5GB
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    demo_enterprise_ui()
