#!/usr/bin/env python3
"""
Design System Module
Provides consistent UI components and design patterns
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ComponentSize(Enum):
    """Standard component sizes"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ComponentVariant(Enum):
    """Component style variants"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    GHOST = "ghost"


@dataclass
class DesignTokens:
    """Design system tokens for consistency"""
    # Spacing
    spacing_xs: str = "0.25rem"
    spacing_sm: str = "0.5rem"
    spacing_md: str = "1rem"
    spacing_lg: str = "1.5rem"
    spacing_xl: str = "2rem"
    spacing_xxl: str = "3rem"
    
    # Border radius
    radius_sm: str = "4px"
    radius_md: str = "8px"
    radius_lg: str = "12px"
    radius_xl: str = "16px"
    radius_round: str = "9999px"
    
    # Font sizes
    font_xs: str = "0.75rem"
    font_sm: str = "0.875rem"
    font_md: str = "1rem"
    font_lg: str = "1.125rem"
    font_xl: str = "1.25rem"
    font_2xl: str = "1.5rem"
    font_3xl: str = "2rem"
    
    # Font weights
    font_normal: int = 400
    font_medium: int = 500
    font_semibold: int = 600
    font_bold: int = 700
    
    # Shadows
    shadow_sm: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    shadow_md: str = "0 4px 6px rgba(0, 0, 0, 0.1)"
    shadow_lg: str = "0 10px 15px rgba(0, 0, 0, 0.1)"
    shadow_xl: str = "0 20px 25px rgba(0, 0, 0, 0.1)"
    
    # Transitions
    transition_fast: str = "150ms ease"
    transition_normal: str = "250ms ease"
    transition_slow: str = "350ms ease"


class DesignSystem:
    """Central design system for consistent UI"""
    
    def __init__(self):
        self.tokens = DesignTokens()
        self._init_component_styles()
    
    def _init_component_styles(self):
        """Initialize component-specific styles"""
        css = f"""
        <style>
        /* Design System Base Styles */
        
        /* Consistent spacing classes */
        .ds-spacing-xs {{ margin: {self.tokens.spacing_xs}; }}
        .ds-spacing-sm {{ margin: {self.tokens.spacing_sm}; }}
        .ds-spacing-md {{ margin: {self.tokens.spacing_md}; }}
        .ds-spacing-lg {{ margin: {self.tokens.spacing_lg}; }}
        .ds-spacing-xl {{ margin: {self.tokens.spacing_xl}; }}
        
        /* Button styles */
        .ds-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: {self.tokens.font_medium};
            border-radius: {self.tokens.radius_md};
            transition: all {self.tokens.transition_fast};
            cursor: pointer;
            border: none;
            text-decoration: none;
        }}
        
        .ds-button-sm {{
            padding: {self.tokens.spacing_xs} {self.tokens.spacing_sm};
            font-size: {self.tokens.font_sm};
        }}
        
        .ds-button-md {{
            padding: {self.tokens.spacing_sm} {self.tokens.spacing_md};
            font-size: {self.tokens.font_md};
        }}
        
        .ds-button-lg {{
            padding: {self.tokens.spacing_sm} {self.tokens.spacing_lg};
            font-size: {self.tokens.font_lg};
        }}
        
        /* Card styles */
        .ds-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: {self.tokens.radius_lg};
            padding: {self.tokens.spacing_lg};
            margin-bottom: {self.tokens.spacing_md};
            box-shadow: {self.tokens.shadow_sm};
            transition: all {self.tokens.transition_normal};
        }}
        
        .ds-card:hover {{
            box-shadow: {self.tokens.shadow_md};
        }}
        
        .ds-card-header {{
            margin-bottom: {self.tokens.spacing_md};
            padding-bottom: {self.tokens.spacing_md};
            border-bottom: 1px solid var(--border);
        }}
        
        /* Badge styles */
        .ds-badge {{
            display: inline-flex;
            align-items: center;
            padding: {self.tokens.spacing_xs} {self.tokens.spacing_sm};
            font-size: {self.tokens.font_xs};
            font-weight: {self.tokens.font_medium};
            border-radius: {self.tokens.radius_round};
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        
        /* Input styles */
        .ds-input {{
            width: 100%;
            padding: {self.tokens.spacing_sm};
            border: 1px solid var(--border);
            border-radius: {self.tokens.radius_md};
            font-size: {self.tokens.font_md};
            transition: all {self.tokens.transition_fast};
            background: var(--surface);
            color: var(--text-primary);
        }}
        
        .ds-input:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
        }}
        
        /* Grid system */
        .ds-grid {{
            display: grid;
            gap: {self.tokens.spacing_md};
        }}
        
        .ds-grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .ds-grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        .ds-grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        
        /* Responsive grid */
        @media (max-width: 768px) {{
            .ds-grid-2, .ds-grid-3, .ds-grid-4 {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Animation classes */
        .ds-fade-in {{
            animation: dsFadeIn {self.tokens.transition_normal};
        }}
        
        @keyframes dsFadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Skeleton loader */
        .ds-skeleton {{
            background: linear-gradient(90deg, var(--surface) 25%, var(--surface-variant) 50%, var(--surface) 75%);
            background-size: 200% 100%;
            animation: dsSkeletonLoading 1.5s infinite;
            border-radius: {self.tokens.radius_md};
        }}
        
        @keyframes dsSkeletonLoading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    # Component Methods
    
    def button(self, 
               label: str,
               variant: ComponentVariant = ComponentVariant.PRIMARY,
               size: ComponentSize = ComponentSize.MEDIUM,
               icon: Optional[str] = None,
               full_width: bool = False,
               disabled: bool = False,
               key: Optional[str] = None) -> bool:
        """Create a styled button"""
        # Map size to class
        size_class = f"ds-button-{size.value}"
        
        # Build button HTML
        icon_html = f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ""
        
        # Use Streamlit button with custom styling
        button_style = f"""
        <style>
        div[data-testid="stButton"] > button {{
            width: {'100%' if full_width else 'auto'};
        }}
        </style>
        """
        st.markdown(button_style, unsafe_allow_html=True)
        
        return st.button(
            f"{icon} {label}" if icon else label,
            disabled=disabled,
            key=key,
            type=variant.value if variant == ComponentVariant.PRIMARY else "secondary"
        )
    
    def card(self, 
             title: Optional[str] = None,
             subtitle: Optional[str] = None,
             content: Optional[str] = None,
             footer: Optional[str] = None,
             expandable: bool = False) -> None:
        """Create a styled card"""
        if expandable and title:
            with st.expander(title, expanded=True):
                if subtitle:
                    st.caption(subtitle)
                if content:
                    st.markdown(content)
                if footer:
                    st.markdown(f"---\n{footer}")
        else:
            card_html = '<div class="ds-card ds-fade-in">'
            
            if title or subtitle:
                card_html += '<div class="ds-card-header">'
                if title:
                    card_html += f'<h3 style="margin: 0;">{title}</h3>'
                if subtitle:
                    card_html += f'<p style="margin: 0.5rem 0 0 0; color: var(--text-secondary);">{subtitle}</p>'
                card_html += '</div>'
            
            if content:
                card_html += f'<div class="ds-card-content">{content}</div>'
            
            if footer:
                card_html += f'<div class="ds-card-footer" style="margin-top: {self.tokens.spacing_md}; padding-top: {self.tokens.spacing_md}; border-top: 1px solid var(--border);">{footer}</div>'
            
            card_html += '</div>'
            
            st.markdown(card_html, unsafe_allow_html=True)
    
    def badge(self,
              text: str,
              variant: ComponentVariant = ComponentVariant.PRIMARY,
              icon: Optional[str] = None) -> str:
        """Create a styled badge"""
        variant_styles = {
            ComponentVariant.PRIMARY: "background: var(--primary); color: var(--text-on-primary);",
            ComponentVariant.SECONDARY: "background: var(--surface-variant); color: var(--text-primary);",
            ComponentVariant.SUCCESS: "background: var(--success); color: var(--text-on-primary);",
            ComponentVariant.WARNING: "background: var(--warning); color: var(--text-on-primary);",
            ComponentVariant.ERROR: "background: var(--error); color: var(--text-on-primary);",
            ComponentVariant.INFO: "background: var(--info); color: var(--text-on-primary);",
        }
        
        style = variant_styles.get(variant, variant_styles[ComponentVariant.PRIMARY])
        icon_html = f'{icon} ' if icon else ''
        
        return f'<span class="ds-badge" style="{style}">{icon_html}{text}</span>'
    
    def metric_card(self,
                    label: str,
                    value: Union[str, int, float],
                    delta: Optional[Union[str, int, float]] = None,
                    delta_color: str = "normal",
                    icon: Optional[str] = None) -> None:
        """Create a styled metric card"""
        # Format value
        if isinstance(value, (int, float)):
            value = f"{value:,}"
        
        # Build metric HTML
        metric_html = f"""
        <div class="ds-card" style="text-align: center;">
            {f'<div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>' if icon else ''}
            <div style="color: var(--text-secondary); font-size: {self.tokens.font_sm}; margin-bottom: 0.5rem;">
                {label}
            </div>
            <div style="font-size: {self.tokens.font_2xl}; font-weight: {self.tokens.font_semibold}; color: var(--text-primary);">
                {value}
            </div>
        """
        
        if delta is not None:
            delta_colors = {
                "normal": "var(--text-secondary)",
                "positive": "var(--success)",
                "negative": "var(--error)",
                "off": "var(--text-secondary)"
            }
            color = delta_colors.get(delta_color, "var(--text-secondary)")
            
            # Add arrow for positive/negative
            arrow = ""
            if delta_color == "positive":
                arrow = "↑ "
            elif delta_color == "negative":
                arrow = "↓ "
            
            metric_html += f"""
            <div style="color: {color}; font-size: {self.tokens.font_sm}; margin-top: 0.5rem;">
                {arrow}{delta}
            </div>
            """
        
        metric_html += "</div>"
        st.markdown(metric_html, unsafe_allow_html=True)
    
    def progress_indicator(self,
                          current: int,
                          total: int,
                          label: Optional[str] = None,
                          show_percentage: bool = True) -> None:
        """Create a styled progress indicator"""
        percentage = (current / total) * 100 if total > 0 else 0
        
        progress_html = f"""
        <div style="margin-bottom: {self.tokens.spacing_md};">
            {f'<div style="margin-bottom: {self.tokens.spacing_xs}; color: var(--text-secondary); font-size: {self.tokens.font_sm};">{label}</div>' if label else ''}
            <div style="background: var(--surface-variant); height: 8px; border-radius: {self.tokens.radius_round}; overflow: hidden;">
                <div style="background: var(--primary); height: 100%; width: {percentage}%; transition: width {self.tokens.transition_normal};"></div>
            </div>
            {f'<div style="text-align: right; margin-top: {self.tokens.spacing_xs}; color: var(--text-secondary); font-size: {self.tokens.font_sm};">{percentage:.0f}%</div>' if show_percentage else ''}
        </div>
        """
        st.markdown(progress_html, unsafe_allow_html=True)
    
    def skeleton_loader(self,
                       height: str = "20px",
                       width: str = "100%",
                       count: int = 1) -> None:
        """Create skeleton loading placeholders"""
        for i in range(count):
            st.markdown(
                f'<div class="ds-skeleton" style="height: {height}; width: {width}; margin-bottom: {self.tokens.spacing_sm};"></div>',
                unsafe_allow_html=True
            )
    
    def tabs_custom(self,
                    tabs: List[Tuple[str, str]],
                    default_tab: int = 0) -> str:
        """Create custom styled tabs
        
        Args:
            tabs: List of (label, key) tuples
            default_tab: Index of default active tab
            
        Returns:
            Key of selected tab
        """
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = tabs[default_tab][1]
        
        # Create tab buttons
        cols = st.columns(len(tabs))
        for idx, (col, (label, key)) in enumerate(zip(cols, tabs)):
            with col:
                if st.button(
                    label,
                    key=f"tab_{key}",
                    type="primary" if st.session_state.active_tab == key else "secondary",
                    use_container_width=True
                ):
                    st.session_state.active_tab = key
                    st.rerun()
        
        return st.session_state.active_tab
    
    def info_alert(self,
                   message: str,
                   variant: ComponentVariant = ComponentVariant.INFO,
                   icon: bool = True,
                   dismissible: bool = False) -> None:
        """Create a styled alert/info box"""
        icons = {
            ComponentVariant.INFO: "ℹ️",
            ComponentVariant.SUCCESS: "✅",
            ComponentVariant.WARNING: "⚠️",
            ComponentVariant.ERROR: "❌"
        }
        
        if variant == ComponentVariant.INFO:
            st.info(message, icon=icons[variant] if icon else None)
        elif variant == ComponentVariant.SUCCESS:
            st.success(message, icon=icons[variant] if icon else None)
        elif variant == ComponentVariant.WARNING:
            st.warning(message, icon=icons[variant] if icon else None)
        elif variant == ComponentVariant.ERROR:
            st.error(message, icon=icons[variant] if icon else None)
    
    def divider(self, 
                style: str = "solid",
                spacing: str = "md") -> None:
        """Create a styled divider"""
        spacing_value = getattr(self.tokens, f"spacing_{spacing}", self.tokens.spacing_md)
        
        divider_styles = {
            "solid": "1px solid var(--border)",
            "dashed": "1px dashed var(--border)",
            "dotted": "1px dotted var(--border)",
            "thick": "3px solid var(--border)"
        }
        
        st.markdown(
            f'<hr style="border: none; border-top: {divider_styles.get(style, divider_styles["solid"])}; margin: {spacing_value} 0;" />',
            unsafe_allow_html=True
        )
    
    def empty_state(self,
                    title: str,
                    description: Optional[str] = None,
                    icon: Optional[str] = None,
                    action_label: Optional[str] = None,
                    action_callback: Optional[callable] = None) -> None:
        """Create an empty state placeholder"""
        empty_html = f"""
        <div class="ds-card" style="text-align: center; padding: {self.tokens.spacing_xxl};">
            {f'<div style="font-size: 3rem; margin-bottom: {self.tokens.spacing_md};">{icon}</div>' if icon else ''}
            <h3 style="color: var(--text-primary); margin-bottom: {self.tokens.spacing_sm};">{title}</h3>
            {f'<p style="color: var(--text-secondary); margin-bottom: {self.tokens.spacing_lg};">{description}</p>' if description else ''}
        </div>
        """
        st.markdown(empty_html, unsafe_allow_html=True)
        
        if action_label and action_callback:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button(action_label, use_container_width=True, type="primary"):
                    action_callback()


# Singleton instance
_design_system = None


def get_design_system() -> DesignSystem:
    """Get or create design system instance"""
    global _design_system
    if _design_system is None:
        _design_system = DesignSystem()
    return _design_system


# Convenience functions
def ds_button(*args, **kwargs):
    """Create a design system button"""
    return get_design_system().button(*args, **kwargs)


def ds_card(*args, **kwargs):
    """Create a design system card"""
    return get_design_system().card(*args, **kwargs)


def ds_badge(*args, **kwargs):
    """Create a design system badge"""
    return get_design_system().badge(*args, **kwargs)


def ds_metric(*args, **kwargs):
    """Create a design system metric card"""
    return get_design_system().metric_card(*args, **kwargs)


def ds_progress(*args, **kwargs):
    """Create a design system progress indicator"""
    return get_design_system().progress_indicator(*args, **kwargs)


def ds_skeleton(*args, **kwargs):
    """Create a design system skeleton loader"""
    return get_design_system().skeleton_loader(*args, **kwargs)


def ds_divider(*args, **kwargs):
    """Create a design system divider"""
    return get_design_system().divider(*args, **kwargs)


def ds_empty_state(*args, **kwargs):
    """Create a design system empty state"""
    return get_design_system().empty_state(*args, **kwargs)