"""
Annotations module for collaborative transcript annotation
"""

from .annotation_manager import AnnotationManager
from .annotation_ui import (
    render_annotation_ui,
    render_annotation_thread,
    render_annotation_input,
    render_annotation_sidebar
)

__all__ = [
    'AnnotationManager',
    'render_annotation_ui',
    'render_annotation_thread',
    'render_annotation_input',
    'render_annotation_sidebar'
]