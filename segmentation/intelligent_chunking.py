"""
Intelligent Content Chunking and Segmentation System
Implements Task 37: Advanced segmentation capabilities
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from .segment_manager import SegmentManager, Segment, SegmentType
from .segmentation_ui import render_segmentation_view, render_segmentation_settings

logger = logging.getLogger(__name__)


class IntelligentChunkingSystem:
    """Main system for intelligent content chunking and segmentation"""
    
    def __init__(self):
        self.segment_manager = SegmentManager()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state for segmentation"""
        if 'segmentation_settings' not in st.session_state:
            st.session_state.segmentation_settings = {
                'method': 'hybrid',
                'min_segment_length': 50,
                'merge_similar': True,
                'enable_silence_refinement': True,
                'preserve_manual_chapters': True
            }
        
        if 'manual_chapters' not in st.session_state:
            st.session_state.manual_chapters = []
        
        if 'current_segments' not in st.session_state:
            st.session_state.current_segments = []
    
    def process_transcript(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None,
        speakers: Optional[List[str]] = None,
        audio_path: Optional[str] = None
    ) -> List[Segment]:
        """
        Process transcript with intelligent chunking
        
        Args:
            transcript: Full transcript text
            timestamps: Optional timestamp data
            speakers: Optional speaker information
            audio_path: Optional path to audio file for silence detection
            
        Returns:
            List of processed segments
        """
        try:
            settings = st.session_state.segmentation_settings
            manual_chapters = st.session_state.get('manual_chapters', [])
            
            # Perform segmentation
            segments = self.segment_manager.segment_transcript(
                transcript=transcript,
                timestamps=timestamps,
                speakers=speakers,
                method=settings['method'],
                audio_path=audio_path if settings['enable_silence_refinement'] else None,
                manual_chapters=manual_chapters if settings['preserve_manual_chapters'] else None
            )
            
            # Store segments in session state
            st.session_state.current_segments = segments
            
            return segments
            
        except Exception as e:
            logger.error(f"Error in intelligent chunking: {e}")
            st.error(f"Segmentation failed: {str(e)}")
            return []
    
    def render_segmentation_interface(
        self,
        transcript: str,
        segments: Optional[List[Segment]] = None,
        audio_path: Optional[str] = None,
        editable: bool = True
    ) -> List[Segment]:
        """
        Render the complete segmentation interface
        
        Args:
            transcript: Full transcript text
            segments: Current segments (if None, uses session state)
            audio_path: Optional audio file path
            editable: Whether segments can be edited
            
        Returns:
            Updated segments
        """
        if segments is None:
            segments = st.session_state.get('current_segments', [])
        
        if not segments:
            st.info("No segments available. Process a transcript first to enable segmentation.")
            return []
        
        # Show segmentation settings if requested
        if st.session_state.get('show_segment_settings', False):
            render_segmentation_settings()
        
        # Render main segmentation view
        updated_segments = render_segmentation_view(
            transcript=transcript,
            segments=segments,
            editable=editable,
            audio_path=audio_path
        )
        
        # Update session state
        st.session_state.current_segments = updated_segments
        
        return updated_segments
    
    def export_segments(
        self,
        segments: Optional[List[Segment]] = None,
        format: str = "json"
    ) -> str:
        """Export segments in specified format"""
        if segments is None:
            segments = st.session_state.get('current_segments', [])
        
        if not segments:
            return ""
        
        return self.segment_manager.export_segments(segments, format)
    
    def get_segmentation_analytics(
        self,
        segments: Optional[List[Segment]] = None
    ) -> Dict[str, Any]:
        """Get analytics about current segmentation"""
        if segments is None:
            segments = st.session_state.get('current_segments', [])
        
        if not segments:
            return {}
        
        # Calculate analytics
        analytics = {
            'total_segments': len(segments),
            'segment_types': {},
            'average_length': 0,
            'total_duration': 0,
            'speakers': set(),
            'manual_chapters': 0,
            'silence_segments': 0
        }
        
        total_chars = 0
        
        for segment in segments:
            # Count by type
            seg_type = segment.type.value
            analytics['segment_types'][seg_type] = analytics['segment_types'].get(seg_type, 0) + 1
            
            # Length statistics
            total_chars += len(segment.text)
            
            # Duration
            if segment.start_time and segment.end_time:
                analytics['total_duration'] = max(
                    analytics['total_duration'],
                    segment.end_time
                )
            
            # Speakers
            if segment.speaker:
                analytics['speakers'].add(segment.speaker)
            
            # Special segment types
            if segment.is_manual:
                analytics['manual_chapters'] += 1
            
            if segment.type == SegmentType.SILENCE:
                analytics['silence_segments'] += 1
        
        analytics['average_length'] = total_chars / len(segments) if segments else 0
        analytics['speakers'] = list(analytics['speakers'])
        analytics['unique_speakers'] = len(analytics['speakers'])
        
        return analytics
    
    def create_chapter_from_segment(
        self,
        segment: Segment,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a manual chapter from an existing segment"""
        chapter_title = title or f"Chapter: {segment.text[:30]}..."
        
        return self.segment_manager.create_manual_chapter(
            title=chapter_title,
            start_time=segment.start_time or 0,
            description=segment.summary or segment.text[:100],
            metadata={
                'source_segment_id': segment.id,
                'source_segment_type': segment.type.value,
                'auto_generated': True
            }
        )
    
    def merge_segments(
        self,
        segment_ids: List[int],
        new_title: Optional[str] = None
    ) -> Optional[Segment]:
        """Merge multiple segments into one"""
        segments = st.session_state.get('current_segments', [])
        
        # Find segments to merge
        to_merge = [seg for seg in segments if seg.id in segment_ids]
        
        if len(to_merge) < 2:
            return None
        
        # Sort by start time/position
        to_merge.sort(key=lambda x: x.start_time or x.start_char)
        
        # Create merged segment
        merged_text = ' '.join(seg.text for seg in to_merge)
        merged_keywords = []
        for seg in to_merge:
            merged_keywords.extend(seg.keywords)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in merged_keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        merged_segment = Segment(
            id=to_merge[0].id,
            type=to_merge[0].type,
            start_time=to_merge[0].start_time,
            end_time=to_merge[-1].end_time,
            start_char=to_merge[0].start_char,
            end_char=to_merge[-1].end_char,
            text=merged_text,
            speaker=to_merge[0].speaker,
            confidence=sum(seg.confidence for seg in to_merge) / len(to_merge),
            keywords=unique_keywords[:10],  # Limit keywords
            summary=new_title or f"Merged: {merged_text[:50]}...",
            metadata={
                'merged_from': [seg.id for seg in to_merge],
                'merge_timestamp': st.session_state.get('current_time', 'unknown')
            }
        )
        
        # Update segments list
        updated_segments = [seg for seg in segments if seg.id not in segment_ids]
        updated_segments.append(merged_segment)
        
        # Sort by position
        updated_segments.sort(key=lambda x: x.start_time or x.start_char)
        
        # Renumber segments
        for i, seg in enumerate(updated_segments):
            seg.id = i
        
        st.session_state.current_segments = updated_segments
        
        return merged_segment
    
    def split_segment(
        self,
        segment_id: int,
        split_points: List[float]
    ) -> List[Segment]:
        """Split a segment at specified time points"""
        segments = st.session_state.get('current_segments', [])
        
        # Find segment to split
        target_segment = None
        for seg in segments:
            if seg.id == segment_id:
                target_segment = seg
                break
        
        if not target_segment or not split_points:
            return []
        
        # Sort split points
        split_points = sorted(split_points)
        
        # Create new segments
        new_segments = []
        current_start = target_segment.start_time or 0
        current_char_start = target_segment.start_char
        
        # Calculate text portions
        total_duration = (target_segment.end_time or 0) - (target_segment.start_time or 0)
        
        for i, split_time in enumerate(split_points + [target_segment.end_time or 0]):
            if split_time <= current_start:
                continue
            
            # Calculate text portion
            if total_duration > 0:
                start_ratio = (current_start - (target_segment.start_time or 0)) / total_duration
                end_ratio = (split_time - (target_segment.start_time or 0)) / total_duration
            else:
                start_ratio = i / (len(split_points) + 1)
                end_ratio = (i + 1) / (len(split_points) + 1)
            
            text_start = int(len(target_segment.text) * start_ratio)
            text_end = int(len(target_segment.text) * end_ratio)
            
            segment_text = target_segment.text[text_start:text_end].strip()
            
            if segment_text:
                new_segment = Segment(
                    id=len(new_segments),  # Temporary ID
                    type=target_segment.type,
                    start_time=current_start,
                    end_time=split_time,
                    start_char=current_char_start + text_start,
                    end_char=current_char_start + text_end,
                    text=segment_text,
                    speaker=target_segment.speaker,
                    confidence=target_segment.confidence,
                    keywords=target_segment.keywords[:3],  # Distribute keywords
                    summary=f"Split {i+1}: {segment_text[:30]}...",
                    metadata={
                        'split_from': target_segment.id,
                        'split_index': i
                    }
                )
                new_segments.append(new_segment)
            
            current_start = split_time
        
        # Update segments list
        updated_segments = [seg for seg in segments if seg.id != segment_id]
        updated_segments.extend(new_segments)
        
        # Sort and renumber
        updated_segments.sort(key=lambda x: x.start_time or x.start_char)
        for i, seg in enumerate(updated_segments):
            seg.id = i
        
        st.session_state.current_segments = updated_segments
        
        return new_segments


# Convenience functions for integration
def render_intelligent_chunking_interface(
    transcript: str,
    timestamps: Optional[List[Tuple[float, float, str]]] = None,
    speakers: Optional[List[str]] = None,
    audio_path: Optional[str] = None,
    editable: bool = True
) -> List[Segment]:
    """
    Main interface function for intelligent chunking
    
    This function provides the complete segmentation interface including:
    - Semantic chunking based on topic boundaries
    - Speaker-based segmentation for multi-person conversations  
    - Time-based chunking with configurable intervals
    - Silence-based automatic segmentation
    - Manual chapter marking with visual timeline editor
    """
    
    # Initialize system
    chunking_system = IntelligentChunkingSystem()
    
    # Process transcript if not already done
    if not st.session_state.get('current_segments'):
        with st.spinner("Processing transcript with intelligent chunking..."):
            segments = chunking_system.process_transcript(
                transcript=transcript,
                timestamps=timestamps,
                speakers=speakers,
                audio_path=audio_path
            )
    else:
        segments = st.session_state.current_segments
    
    # Render interface
    if segments:
        updated_segments = chunking_system.render_segmentation_interface(
            transcript=transcript,
            segments=segments,
            audio_path=audio_path,
            editable=editable
        )
        
        # Show analytics
        with st.expander("📊 Segmentation Analytics", expanded=False):
            analytics = chunking_system.get_segmentation_analytics(updated_segments)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Segments", analytics['total_segments'])
            with col2:
                st.metric("Avg Length", f"{analytics['average_length']:.0f} chars")
            with col3:
                st.metric("Speakers", analytics['unique_speakers'])
            with col4:
                st.metric("Duration", f"{analytics['total_duration']:.1f}s")
            
            # Segment type breakdown
            if analytics['segment_types']:
                st.markdown("**Segment Types:**")
                for seg_type, count in analytics['segment_types'].items():
                    st.write(f"• {seg_type.replace('_', ' ').title()}: {count}")
        
        return updated_segments
    
    return []


def get_chunking_system() -> IntelligentChunkingSystem:
    """Get the chunking system instance"""
    return IntelligentChunkingSystem()