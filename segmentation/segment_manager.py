"""
Advanced segmentation manager for intelligent content chunking
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)


class SegmentType(Enum):
    """Types of segments"""
    INTRODUCTION = "introduction"
    MAIN_TOPIC = "main_topic"
    SUB_TOPIC = "sub_topic"
    CONCLUSION = "conclusion"
    QUESTION = "question"
    ANSWER = "answer"
    TRANSITION = "transition"
    SPEAKER_CHANGE = "speaker_change"
    PAUSE = "pause"
    CUSTOM = "custom"


@dataclass
class Segment:
    """Represents a content segment"""
    id: int
    type: SegmentType
    start_time: Optional[float]
    end_time: Optional[float]
    start_char: int
    end_char: int
    text: str
    speaker: Optional[str]
    confidence: float
    keywords: List[str]
    summary: Optional[str]
    metadata: Dict[str, Any]


class SegmentManager:
    """Manages advanced segmentation of transcripts"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def segment_transcript(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None,
        speakers: Optional[List[str]] = None,
        method: str = "hybrid"
    ) -> List[Segment]:
        """
        Segment transcript using various methods
        
        Args:
            transcript: Full transcript text
            timestamps: Optional list of (start_time, end_time, text) tuples
            speakers: Optional list of speaker identifiers
            method: Segmentation method - "semantic", "structural", "temporal", "hybrid"
            
        Returns:
            List of segments
        """
        if method == "semantic":
            return self._semantic_segmentation(transcript, timestamps)
        elif method == "structural":
            return self._structural_segmentation(transcript, timestamps)
        elif method == "temporal":
            return self._temporal_segmentation(transcript, timestamps)
        else:  # hybrid
            return self._hybrid_segmentation(transcript, timestamps, speakers)
    
    def _semantic_segmentation(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None
    ) -> List[Segment]:
        """Segment based on semantic similarity"""
        sentences = sent_tokenize(transcript)
        
        if len(sentences) < 2:
            return [self._create_segment(
                0, SegmentType.MAIN_TOPIC, transcript, 0, len(transcript)
            )]
        
        # Calculate sentence embeddings
        try:
            embeddings = self.vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(embeddings)
        except:
            # Fallback to simple segmentation
            return self._simple_segmentation(transcript, timestamps)
        
        # Find semantic boundaries
        segments = []
        current_segment_start = 0
        current_segment_sentences = [sentences[0]]
        
        for i in range(1, len(sentences)):
            # Check similarity with previous sentence
            similarity = similarity_matrix[i, i-1]
            
            # If similarity is low, start new segment
            if similarity < 0.3:  # Threshold for topic change
                # Create segment from accumulated sentences
                segment_text = ' '.join(current_segment_sentences)
                segment_start_char = transcript.find(current_segment_sentences[0])
                segment_end_char = segment_start_char + len(segment_text)
                
                segments.append(self._create_segment(
                    len(segments),
                    self._determine_segment_type(segment_text, len(segments), len(sentences)),
                    segment_text,
                    segment_start_char,
                    segment_end_char,
                    timestamps=timestamps
                ))
                
                # Start new segment
                current_segment_sentences = [sentences[i]]
                current_segment_start = i
            else:
                current_segment_sentences.append(sentences[i])
        
        # Add final segment
        if current_segment_sentences:
            segment_text = ' '.join(current_segment_sentences)
            segment_start_char = transcript.find(current_segment_sentences[0])
            segment_end_char = segment_start_char + len(segment_text)
            
            segments.append(self._create_segment(
                len(segments),
                self._determine_segment_type(segment_text, len(segments), len(sentences)),
                segment_text,
                segment_start_char,
                segment_end_char,
                timestamps=timestamps
            ))
        
        return segments
    
    def _structural_segmentation(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None
    ) -> List[Segment]:
        """Segment based on structural patterns"""
        # Look for structural markers
        markers = {
            'introduction': [
                r'^(hello|hi|good\s+(morning|afternoon|evening)|welcome)',
                r'(my name is|i\'m|this is)',
                r'(today|in this|we\'ll be discussing)'
            ],
            'conclusion': [
                r'(in conclusion|to sum up|finally|in summary)',
                r'(thank you|thanks for|any questions)',
                r'(that\'s all|this concludes)'
            ],
            'question': [
                r'\?$',
                r'^(what|where|when|why|how|who|is|are|do|does|can|could|would|should)',
                r'(question is|wondering|curious about)'
            ],
            'transition': [
                r'(now|next|moving on|let\'s talk about)',
                r'(another point|furthermore|however|but|although)',
                r'(first|second|third|finally)'
            ]
        }
        
        segments = []
        sentences = sent_tokenize(transcript)
        current_pos = 0
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            segment_type = SegmentType.MAIN_TOPIC
            
            # Check for structural markers
            for marker_type, patterns in markers.items():
                for pattern in patterns:
                    if re.search(pattern, sentence_lower):
                        if marker_type == 'introduction':
                            segment_type = SegmentType.INTRODUCTION
                        elif marker_type == 'conclusion':
                            segment_type = SegmentType.CONCLUSION
                        elif marker_type == 'question':
                            segment_type = SegmentType.QUESTION
                        elif marker_type == 'transition':
                            segment_type = SegmentType.TRANSITION
                        break
            
            # Find sentence position in transcript
            start_char = transcript.find(sentence, current_pos)
            end_char = start_char + len(sentence)
            current_pos = end_char
            
            segments.append(self._create_segment(
                i,
                segment_type,
                sentence,
                start_char,
                end_char,
                timestamps=timestamps
            ))
        
        return self._merge_similar_segments(segments)
    
    def _temporal_segmentation(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None
    ) -> List[Segment]:
        """Segment based on time intervals"""
        if not timestamps:
            # Fallback to simple segmentation
            return self._simple_segmentation(transcript, None)
        
        segments = []
        segment_duration = 30.0  # 30 seconds per segment
        
        current_segment_texts = []
        current_segment_start = timestamps[0][0] if timestamps else 0
        current_start_char = 0
        
        for start_time, end_time, text in timestamps:
            if start_time - current_segment_start >= segment_duration:
                # Create segment
                if current_segment_texts:
                    segment_text = ' '.join(current_segment_texts)
                    segments.append(self._create_segment(
                        len(segments),
                        SegmentType.MAIN_TOPIC,
                        segment_text,
                        current_start_char,
                        current_start_char + len(segment_text),
                        start_time=current_segment_start,
                        end_time=start_time
                    ))
                
                # Start new segment
                current_segment_texts = [text]
                current_segment_start = start_time
                current_start_char = transcript.find(text, current_start_char)
            else:
                current_segment_texts.append(text)
        
        # Add final segment
        if current_segment_texts:
            segment_text = ' '.join(current_segment_texts)
            segments.append(self._create_segment(
                len(segments),
                SegmentType.MAIN_TOPIC,
                segment_text,
                current_start_char,
                len(transcript),
                start_time=current_segment_start,
                end_time=timestamps[-1][1] if timestamps else None
            ))
        
        return segments
    
    def _hybrid_segmentation(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None,
        speakers: Optional[List[str]] = None
    ) -> List[Segment]:
        """Combine multiple segmentation methods"""
        # Start with semantic segmentation
        segments = self._semantic_segmentation(transcript, timestamps)
        
        # Refine with structural analysis
        refined_segments = []
        for segment in segments:
            # Check if segment should be split based on structure
            sub_segments = self._structural_segmentation(segment.text, timestamps)
            
            if len(sub_segments) > 1:
                # Adjust character positions
                for sub_seg in sub_segments:
                    sub_seg.start_char += segment.start_char
                    sub_seg.end_char += segment.start_char
                    refined_segments.append(sub_seg)
            else:
                refined_segments.append(segment)
        
        # Apply speaker changes if available
        if speakers:
            refined_segments = self._apply_speaker_segmentation(refined_segments, speakers)
        
        # Merge very short segments
        final_segments = self._merge_short_segments(refined_segments)
        
        # Renumber segments
        for i, segment in enumerate(final_segments):
            segment.id = i
        
        return final_segments
    
    def _simple_segmentation(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float, str]]] = None
    ) -> List[Segment]:
        """Simple paragraph-based segmentation"""
        paragraphs = transcript.split('\n\n')
        segments = []
        current_pos = 0
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            start_char = transcript.find(paragraph, current_pos)
            end_char = start_char + len(paragraph)
            current_pos = end_char
            
            segments.append(self._create_segment(
                i,
                SegmentType.MAIN_TOPIC,
                paragraph,
                start_char,
                end_char,
                timestamps=timestamps
            ))
        
        return segments
    
    def _create_segment(
        self,
        id: int,
        segment_type: SegmentType,
        text: str,
        start_char: int,
        end_char: int,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        speaker: Optional[str] = None,
        timestamps: Optional[List[Tuple[float, float, str]]] = None
    ) -> Segment:
        """Create a segment with metadata"""
        # Extract keywords
        keywords = self._extract_keywords(text)
        
        # Generate summary (simple version)
        summary = self._generate_summary(text)
        
        # Calculate times from timestamps if not provided
        if timestamps and not start_time:
            start_time, end_time = self._estimate_times_from_position(
                start_char, end_char, len(text), timestamps
            )
        
        return Segment(
            id=id,
            type=segment_type,
            start_time=start_time,
            end_time=end_time,
            start_char=start_char,
            end_char=end_char,
            text=text,
            speaker=speaker,
            confidence=0.85,  # Default confidence
            keywords=keywords,
            summary=summary,
            metadata={}
        )
    
    def _determine_segment_type(
        self,
        text: str,
        position: int,
        total_segments: int
    ) -> SegmentType:
        """Determine segment type based on content and position"""
        text_lower = text.lower()
        
        # Position-based heuristics
        if position == 0:
            return SegmentType.INTRODUCTION
        elif position >= total_segments - 2:
            return SegmentType.CONCLUSION
        
        # Content-based heuristics
        if '?' in text:
            return SegmentType.QUESTION
        elif any(marker in text_lower for marker in ['now', 'next', 'moving on']):
            return SegmentType.TRANSITION
        
        return SegmentType.MAIN_TOPIC
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text"""
        try:
            # Use TF-IDF to extract keywords
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            top_indices = scores.argsort()[-max_keywords:][::-1]
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            return keywords
        except:
            # Fallback to simple word frequency
            words = word_tokenize(text.lower())
            word_freq = {}
            for word in words:
                if len(word) > 3 and word.isalpha():
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Return most frequent words
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:max_keywords]]
    
    def _generate_summary(self, text: str, max_length: int = 100) -> str:
        """Generate simple summary of text"""
        sentences = sent_tokenize(text)
        if not sentences:
            return ""
        
        # For now, return first sentence as summary
        summary = sentences[0]
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def _merge_similar_segments(
        self,
        segments: List[Segment],
        similarity_threshold: float = 0.8
    ) -> List[Segment]:
        """Merge segments with similar types"""
        if len(segments) <= 1:
            return segments
        
        merged = []
        current_segment = segments[0]
        
        for next_segment in segments[1:]:
            # Check if should merge
            if (current_segment.type == next_segment.type and
                current_segment.type in [SegmentType.MAIN_TOPIC, SegmentType.SUB_TOPIC]):
                # Merge segments
                current_segment.text += " " + next_segment.text
                current_segment.end_char = next_segment.end_char
                current_segment.end_time = next_segment.end_time
                current_segment.keywords.extend(next_segment.keywords)
            else:
                merged.append(current_segment)
                current_segment = next_segment
        
        merged.append(current_segment)
        return merged
    
    def _merge_short_segments(
        self,
        segments: List[Segment],
        min_length: int = 50
    ) -> List[Segment]:
        """Merge segments that are too short"""
        if len(segments) <= 1:
            return segments
        
        merged = []
        i = 0
        
        while i < len(segments):
            current = segments[i]
            
            # If segment is too short and not a special type
            if (len(current.text) < min_length and
                current.type in [SegmentType.MAIN_TOPIC, SegmentType.SUB_TOPIC]):
                
                # Try to merge with next segment
                if i + 1 < len(segments):
                    next_seg = segments[i + 1]
                    current.text += " " + next_seg.text
                    current.end_char = next_seg.end_char
                    current.end_time = next_seg.end_time
                    current.keywords.extend(next_seg.keywords)
                    i += 1  # Skip next segment
                
            merged.append(current)
            i += 1
        
        return merged
    
    def _apply_speaker_segmentation(
        self,
        segments: List[Segment],
        speakers: List[str]
    ) -> List[Segment]:
        """Add speaker information to segments"""
        # This is a placeholder - in real implementation,
        # would use speaker diarization results
        for i, segment in enumerate(segments):
            # Simple round-robin assignment for demo
            segment.speaker = speakers[i % len(speakers)] if speakers else None
            
            # Mark speaker changes
            if i > 0 and segment.speaker != segments[i-1].speaker:
                segment.type = SegmentType.SPEAKER_CHANGE
        
        return segments
    
    def _estimate_times_from_position(
        self,
        start_char: int,
        end_char: int,
        total_length: int,
        timestamps: List[Tuple[float, float, str]]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Estimate start/end times based on character position"""
        if not timestamps:
            return None, None
        
        # Simple linear interpolation
        total_duration = timestamps[-1][1] - timestamps[0][0]
        start_ratio = start_char / total_length
        end_ratio = end_char / total_length
        
        start_time = timestamps[0][0] + (total_duration * start_ratio)
        end_time = timestamps[0][0] + (total_duration * end_ratio)
        
        return start_time, end_time
    
    def export_segments(
        self,
        segments: List[Segment],
        format: str = "json"
    ) -> str:
        """Export segments in various formats"""
        if format == "json":
            import json
            return json.dumps([{
                'id': seg.id,
                'type': seg.type.value,
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'text': seg.text,
                'speaker': seg.speaker,
                'keywords': seg.keywords,
                'summary': seg.summary
            } for seg in segments], indent=2)
        
        elif format == "srt":
            # SubRip format
            lines = []
            for i, seg in enumerate(segments):
                if seg.start_time is not None and seg.end_time is not None:
                    start = self._format_time(seg.start_time)
                    end = self._format_time(seg.end_time)
                    lines.append(f"{i+1}")
                    lines.append(f"{start} --> {end}")
                    lines.append(seg.text)
                    lines.append("")
            return '\n'.join(lines)
        
        elif format == "vtt":
            # WebVTT format
            lines = ["WEBVTT", ""]
            for seg in segments:
                if seg.start_time is not None and seg.end_time is not None:
                    start = self._format_time(seg.start_time)
                    end = self._format_time(seg.end_time)
                    lines.append(f"{start} --> {end}")
                    lines.append(seg.text)
                    lines.append("")
            return '\n'.join(lines)
        
        else:
            # Plain text with markers
            lines = []
            for seg in segments:
                lines.append(f"[{seg.type.value.upper()}]")
                if seg.speaker:
                    lines.append(f"Speaker: {seg.speaker}")
                if seg.start_time and seg.end_time:
                    lines.append(f"Time: {seg.start_time:.1f}s - {seg.end_time:.1f}s")
                lines.append(seg.text)
                lines.append("")
            return '\n'.join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """Format time for SRT/VTT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')