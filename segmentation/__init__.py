"""
Advanced segmentation system for smart content chunking

This module implements Task 37: Add intelligent content chunking and segmentation
- Semantic chunking based on topic boundaries
- Speaker-based segmentation for multi-person conversations
- Time-based chunking with configurable intervals
- Silence-based automatic segmentation
- Manual chapter marking with visual timeline editor
"""

from .segment_manager import SegmentManager, Segment, SegmentType
from .segmentation_ui import render_segmentation_view, render_segment_editor
from .intelligent_chunking import (
    IntelligentChunkingSystem,
    render_intelligent_chunking_interface,
    get_chunking_system
)

__all__ = [
    'SegmentManager',
    'Segment', 
    'SegmentType',
    'render_segmentation_view',
    'render_segment_editor',
    'IntelligentChunkingSystem',
    'render_intelligent_chunking_interface',
    'get_chunking_system'
]