"""
Localization system for multi-language UI support
"""

from .language_manager import LanguageManager, get_text, set_language, get_current_language
from .translations import SUPPORTED_LANGUAGES

__all__ = [
    'LanguageManager',
    'get_text',
    'set_language', 
    'get_current_language',
    'SUPPORTED_LANGUAGES'
]