#!/usr/bin/env python3
"""
Test script to demonstrate the localization system
"""

import streamlit as st
from localization import (
    get_text, set_language, get_current_language, 
    render_language_selector, SUPPORTED_LANGUAGES
)
from localization.localized_ui import (
    localized_header, localized_button, localized_text_input,
    render_localized_page_header, localized_info, localized_error,
    localized_success, localized_warning, localized_tab,
    format_localized_date, format_localized_number
)
from datetime import datetime


def main():
    st.set_page_config(
        page_title="Localization Test",
        page_icon="🌍",
        layout="wide"
    )
    
    # Apply localization settings
    render_localized_page_header()
    
    # Main header
    st.title(f"🌍 {get_text('app.title')} - Localization Demo")
    
    # Show current language
    current_lang = get_current_language()
    st.info(f"Current Language: {SUPPORTED_LANGUAGES[current_lang]} ({current_lang})")
    
    # Tabs demonstration
    tab_keys = ['results.transcript', 'results.entities', 'results.analysis', 'settings.language']
    tabs = localized_tab(tab_keys)
    
    with tabs[0]:
        localized_header('results.transcript')
        st.write("This tab shows the transcript content.")
        
        # Authentication demo
        col1, col2 = st.columns(2)
        with col1:
            email = localized_text_input('auth.email', key='demo_email')
            password = st.text_input(get_text('auth.password'), type='password', key='demo_password')
        
        with col2:
            if localized_button('auth.login', key='demo_login'):
                localized_success('message.success')
            
            if localized_button('auth.signup', key='demo_signup'):
                localized_info('message.loading')
    
    with tabs[1]:
        localized_header('results.entities')
        st.write("This tab shows extracted entities.")
        
        # Action buttons demo
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            localized_button('action.save', key='demo_save')
        with col2:
            localized_button('action.edit', key='demo_edit')
        with col3:
            localized_button('action.share', key='demo_share')
        with col4:
            localized_button('action.delete', key='demo_delete', type='primary')
    
    with tabs[2]:
        localized_header('results.analysis')
        st.write("This tab shows analysis results.")
        
        # Team demo
        if localized_button('teams.create', key='demo_create_team'):
            localized_success('message.success')
        
        if localized_button('teams.invite', key='demo_invite'):
            localized_warning('message.error')
    
    with tabs[3]:
        localized_header('settings.language')
        st.write("Language settings and formatting demos")
        
        # Date formatting
        st.subheader("Date Formatting")
        today = datetime.now()
        st.write(f"Short format: {format_localized_date(today, 'short')}")
        st.write(f"Long format: {format_localized_date(today, 'long')}")
        
        # Number formatting
        st.subheader("Number Formatting")
        number = 1234567.89
        st.write(f"Formatted number: {format_localized_number(number, 2)}")
        
        # All available translations
        st.subheader("Available Translations")
        from localization.translations import TRANSLATIONS
        
        # Show translation coverage
        from localization.language_manager import get_language_manager
        manager = get_language_manager()
        
        st.write("Translation Coverage by Language:")
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            coverage = manager.get_translation_coverage(lang_code)
            st.progress(coverage / 100)
            st.write(f"{lang_name}: {coverage:.1f}%")
    
    # Navigation demo in sidebar
    with st.sidebar:
        st.header(get_text('nav.transcription'))
        nav_options = [
            'nav.transcription',
            'nav.batch',
            'nav.my_transcripts',
            'nav.teams',
            'nav.shares',
            'nav.notifications'
        ]
        
        for nav_key in nav_options:
            st.write(f"- {get_text(nav_key)}")
    
    # File upload demo
    st.markdown("---")
    localized_header('upload.header')
    uploaded_file = st.file_uploader(
        get_text('upload.choose_file'),
        type=['mp3', 'wav', 'mp4'],
        key='demo_upload'
    )
    
    if uploaded_file:
        if localized_button('upload.process', type='primary', key='demo_process'):
            with st.spinner(get_text('message.loading')):
                import time
                time.sleep(2)
            localized_success('message.success')


if __name__ == "__main__":
    main()