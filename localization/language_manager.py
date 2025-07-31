"""
Language management system for multi-language UI support
"""

import streamlit as st
from typing import Optional, Dict, Any
from .translations import TRANSLATIONS, SUPPORTED_LANGUAGES
import json
import os
import logging

logger = logging.getLogger(__name__)


class LanguageManager:
    """Manages language selection and translation retrieval"""
    
    def __init__(self):
        self.translations = TRANSLATIONS
        self.supported_languages = SUPPORTED_LANGUAGES
        self._initialize_language()
    
    def _initialize_language(self):
        """Initialize language from session state or user preferences"""
        if 'language' not in st.session_state:
            # Try to load from user preferences or default to English
            st.session_state.language = self._load_user_language_preference() or 'en'
    
    def _load_user_language_preference(self) -> Optional[str]:
        """Load user's language preference from database or config"""
        # In a real implementation, this would load from user profile
        # For now, check if there's a saved preference in local storage
        try:
            pref_file = os.path.expanduser('~/.transcription_app_language.json')
            if os.path.exists(pref_file):
                with open(pref_file, 'r') as f:
                    data = json.load(f)
                    return data.get('language', 'en')
        except Exception as e:
            logger.error(f"Error loading language preference: {e}")
        return None
    
    def _save_user_language_preference(self, language: str):
        """Save user's language preference"""
        try:
            pref_file = os.path.expanduser('~/.transcription_app_language.json')
            with open(pref_file, 'w') as f:
                json.dump({'language': language}, f)
        except Exception as e:
            logger.error(f"Error saving language preference: {e}")
    
    def get_text(self, key: str, **kwargs) -> str:
        """
        Get translated text for a given key
        
        Args:
            key: Translation key (e.g., 'app.title')
            **kwargs: Format parameters for string interpolation
            
        Returns:
            Translated text or key if translation not found
        """
        language = st.session_state.get('language', 'en')
        
        # Get translation
        if key in self.translations:
            translation = self.translations[key].get(language, self.translations[key].get('en', key))
        else:
            logger.warning(f"Translation key not found: {key}")
            translation = key
        
        # Apply format parameters if provided
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except Exception as e:
                logger.error(f"Error formatting translation: {e}")
        
        return translation
    
    def set_language(self, language: str):
        """Set the current language"""
        if language in self.supported_languages:
            st.session_state.language = language
            self._save_user_language_preference(language)
            return True
        return False
    
    def get_current_language(self) -> str:
        """Get the current language code"""
        return st.session_state.get('language', 'en')
    
    def get_current_language_name(self) -> str:
        """Get the current language display name"""
        lang_code = self.get_current_language()
        return self.supported_languages.get(lang_code, 'English')
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.supported_languages.copy()
    
    def add_custom_translations(self, custom_translations: Dict[str, Dict[str, str]]):
        """Add custom translations to the system"""
        for key, translations in custom_translations.items():
            if key not in self.translations:
                self.translations[key] = {}
            self.translations[key].update(translations)
    
    def export_translations(self, language: str) -> Dict[str, str]:
        """Export all translations for a specific language"""
        result = {}
        for key, translations in self.translations.items():
            if language in translations:
                result[key] = translations[language]
        return result
    
    def import_translations(self, language: str, translations: Dict[str, str]):
        """Import translations for a specific language"""
        for key, translation in translations.items():
            if key not in self.translations:
                self.translations[key] = {}
            self.translations[key][language] = translation
    
    def get_missing_translations(self, language: str) -> list:
        """Get list of keys missing translations for a language"""
        missing = []
        for key, translations in self.translations.items():
            if language not in translations:
                missing.append(key)
        return missing
    
    def get_translation_coverage(self, language: str) -> float:
        """Get percentage of translated keys for a language"""
        total_keys = len(self.translations)
        translated_keys = sum(1 for translations in self.translations.values() if language in translations)
        return (translated_keys / total_keys * 100) if total_keys > 0 else 0


# Global instance
_language_manager = None


def get_language_manager() -> LanguageManager:
    """Get or create the global language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


# Convenience functions
def get_text(key: str, **kwargs) -> str:
    """Get translated text for a given key"""
    return get_language_manager().get_text(key, **kwargs)


def set_language(language: str) -> bool:
    """Set the current language"""
    return get_language_manager().set_language(language)


def get_current_language() -> str:
    """Get the current language code"""
    return get_language_manager().get_current_language()


def render_language_selector(key: str = "main_language_selector"):
    """Render a language selector widget"""
    manager = get_language_manager()
    current_lang = manager.get_current_language()
    languages = manager.get_supported_languages()
    
    # Create display options
    options = list(languages.values())
    codes = list(languages.keys())
    
    # Find current index
    current_index = codes.index(current_lang) if current_lang in codes else 0
    
    # Render selector
    selected = st.selectbox(
        get_text('settings.language'),
        options=options,
        index=current_index,
        key=key
    )
    
    # Get selected code
    selected_index = options.index(selected)
    selected_code = codes[selected_index]
    
    # Update language if changed
    if selected_code != current_lang:
        set_language(selected_code)
        st.rerun()