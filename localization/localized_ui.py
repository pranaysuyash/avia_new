"""
Localized UI components that automatically use the current language
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from .language_manager import get_text, get_current_language


def localized_header(key: str, level: int = 1):
    """Render a localized header"""
    text = get_text(key)
    if level == 1:
        st.header(text)
    elif level == 2:
        st.subheader(text)
    elif level == 3:
        st.markdown(f"### {text}")
    else:
        st.markdown(f"#### {text}")


def localized_button(key: str, type: str = "secondary", **kwargs) -> bool:
    """Render a localized button"""
    text = get_text(key)
    return st.button(text, type=type, **kwargs)


def localized_text_input(
    key: str,
    value: str = "",
    placeholder_key: Optional[str] = None,
    **kwargs
) -> str:
    """Render a localized text input"""
    label = get_text(key)
    placeholder = get_text(placeholder_key) if placeholder_key else ""
    return st.text_input(label, value=value, placeholder=placeholder, **kwargs)


def localized_text_area(
    key: str,
    value: str = "",
    placeholder_key: Optional[str] = None,
    **kwargs
) -> str:
    """Render a localized text area"""
    label = get_text(key)
    placeholder = get_text(placeholder_key) if placeholder_key else ""
    return st.text_area(label, value=value, placeholder=placeholder, **kwargs)


def localized_selectbox(
    key: str,
    options: List[str],
    option_keys: Optional[List[str]] = None,
    index: int = 0,
    **kwargs
) -> str:
    """Render a localized selectbox"""
    label = get_text(key)
    
    # Translate options if keys provided
    if option_keys:
        translated_options = [get_text(k) for k in option_keys]
        selected = st.selectbox(label, options=translated_options, index=index, **kwargs)
        # Return original option
        selected_index = translated_options.index(selected)
        return options[selected_index]
    else:
        return st.selectbox(label, options=options, index=index, **kwargs)


def localized_radio(
    key: str,
    options: List[str],
    option_keys: Optional[List[str]] = None,
    index: int = 0,
    **kwargs
) -> str:
    """Render localized radio buttons"""
    label = get_text(key)
    
    # Translate options if keys provided
    if option_keys:
        translated_options = [get_text(k) for k in option_keys]
        selected = st.radio(label, options=translated_options, index=index, **kwargs)
        # Return original option
        selected_index = translated_options.index(selected)
        return options[selected_index]
    else:
        return st.radio(label, options=options, index=index, **kwargs)


def localized_checkbox(key: str, value: bool = False, **kwargs) -> bool:
    """Render a localized checkbox"""
    label = get_text(key)
    return st.checkbox(label, value=value, **kwargs)


def localized_success(key: str, **format_args):
    """Show a localized success message"""
    message = get_text(key, **format_args)
    st.success(message)


def localized_error(key: str, **format_args):
    """Show a localized error message"""
    message = get_text(key, **format_args)
    st.error(message)


def localized_warning(key: str, **format_args):
    """Show a localized warning message"""
    message = get_text(key, **format_args)
    st.warning(message)


def localized_info(key: str, **format_args):
    """Show a localized info message"""
    message = get_text(key, **format_args)
    st.info(message)


def localized_metric(label_key: str, value: Any, delta: Optional[Any] = None, **kwargs):
    """Render a localized metric"""
    label = get_text(label_key)
    st.metric(label, value, delta, **kwargs)


def localized_tab(tab_keys: List[str]) -> List[Any]:
    """Create localized tabs"""
    tab_labels = [get_text(key) for key in tab_keys]
    return st.tabs(tab_labels)


def localized_expander(key: str, expanded: bool = False):
    """Create a localized expander"""
    label = get_text(key)
    return st.expander(label, expanded=expanded)


def localized_columns(ratios: List[int]):
    """Create columns (no localization needed, but included for consistency)"""
    return st.columns(ratios)


def localized_file_uploader(
    key: str,
    type: Optional[List[str]] = None,
    help_key: Optional[str] = None,
    **kwargs
):
    """Render a localized file uploader"""
    label = get_text(key)
    help_text = get_text(help_key) if help_key else None
    return st.file_uploader(label, type=type, help=help_text, **kwargs)


def localized_download_button(
    key: str,
    data: Any,
    file_name: str,
    mime: str,
    **kwargs
) -> bool:
    """Render a localized download button"""
    label = get_text(key)
    return st.download_button(label, data, file_name, mime, **kwargs)


def render_localized_page_header():
    """Render a standard localized page header"""
    current_lang = get_current_language()
    
    # Add RTL support for Arabic
    if current_lang == 'ar':
        st.markdown(
            """
            <style>
            .stApp {
                direction: rtl;
                text-align: right;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
    # Language selector in sidebar
    with st.sidebar:
        from .language_manager import render_language_selector
        with st.expander(get_text('settings.language'), expanded=False):
            render_language_selector()


def format_localized_date(date, format_type: str = "short") -> str:
    """Format a date according to the current locale"""
    current_lang = get_current_language()
    
    # Language-specific date formats
    date_formats = {
        'en': {'short': '%m/%d/%Y', 'long': '%B %d, %Y'},
        'es': {'short': '%d/%m/%Y', 'long': '%d de %B de %Y'},
        'fr': {'short': '%d/%m/%Y', 'long': '%d %B %Y'},
        'de': {'short': '%d.%m.%Y', 'long': '%d. %B %Y'},
        'it': {'short': '%d/%m/%Y', 'long': '%d %B %Y'},
        'pt': {'short': '%d/%m/%Y', 'long': '%d de %B de %Y'},
        'zh': {'short': '%Y/%m/%d', 'long': '%Y年%m月%d日'},
        'ja': {'short': '%Y/%m/%d', 'long': '%Y年%m月%d日'},
        'ko': {'short': '%Y/%m/%d', 'long': '%Y년 %m월 %d일'},
        'ar': {'short': '%d/%m/%Y', 'long': '%d %B %Y'}
    }
    
    format_str = date_formats.get(current_lang, date_formats['en'])[format_type]
    return date.strftime(format_str)


def format_localized_number(number: float, decimal_places: int = 2) -> str:
    """Format a number according to the current locale"""
    current_lang = get_current_language()
    
    # Language-specific number formats
    if current_lang in ['de', 'es', 'fr', 'it', 'pt']:
        # European format: comma as decimal separator
        formatted = f"{number:,.{decimal_places}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    else:
        # Standard format: period as decimal separator
        formatted = f"{number:,.{decimal_places}f}"
    
    return formatted