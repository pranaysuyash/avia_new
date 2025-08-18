"""
Utility modules for audio and text processing
"""

from .audio_processing import AudioProcessor
from .text_processing import TextProcessor

# Add a validation module
from .validation import validate_email

__all__ = ['AudioProcessor', 'TextProcessor', 'validate_email']