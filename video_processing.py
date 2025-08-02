#!/usr/bin/env python3
"""
Video Processing Module
Implements Task 30: Add video-specific processing features

This module provides comprehensive video processing capabilities including:
- Video thumbnail generation and preview
- Subtitle/caption generation (SRT, VTT formats)
- Video player with synchronized transcript highlighting
- Video chapter detection based on content analysis
- Video quality analysis and optimization recommendations
"""

import os
import cv2
import json
import logging
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffmpeg

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Video file metadata"""
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    format: str
    size_bytes: int
    aspect_ratio: str
    has_audio: bool
    audio_codec: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_sample_rate: Optional[int] = None


@dataclass
class VideoThumbnail:
    """Video thumbnail information"""
    timestamp: float
    image_path: str
    width: int
    height: int
    quality_score: float
    is_keyframe: bool


@dataclass
class VideoChapter:
    """Video chapter information"""
    start_time: float
    end_time: float
    title: str
    description: str
    thumbnail_path: Optional[str] = None
    confidence: float = 0.0
    keywords: List[str] = None


@dataclass
class SubtitleEntry:
    """Subtitle entry for SRT/VTT files"""
    index: int
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class VideoQualityMetrics:
    """Video quality analysis metrics"""
    resolution_score: float
    bitrate_score: float
    fps_score: float
    compression_score: float
    overall_score: float
    recommendations: List[str]
    technical_details: Dict[str, Any]


class VideoProcessor:
    """Comprehensive video processing system"""
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        
    def extract_metadata(self, video_path: str) -> VideoMetadata:
        """Extract comprehensive metadata from video file"""
        try:
            # Use ffprobe to get detailed video information
            probe = ffmpeg.probe(video_path)
            
            # Get video stream info
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not video_stream:
                raise ValueError("No video stream found in file")
            
            # Extract video metadata
            duration = float(probe['format']['duration'])
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            
            # Calculate FPS
            fps_str = video_stream.get('r_frame_rate', '30/1')
            fps_parts = fps_str.split('/')
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0
            
            # Get bitrate
            bitrate = int(probe['format'].get('bit_rate', 0))
            
            # Get codec and format info
            codec = video_stream.get('codec_name', 'unknown')
            format_name = probe['format'].get('format_name', 'unknown')
            
            # File size
            size_bytes = int(probe['format'].get('size', 0))
            
            # Calculate aspect ratio
            aspect_ratio = f"{width}:{height}"
            gcd = self._gcd(width, height)
            if gcd > 1:
                aspect_ratio = f"{width//gcd}:{height//gcd}"
            
            # Audio information
            has_audio = audio_stream is not None
            audio_codec = audio_stream.get('codec_name') if audio_stream else None
            audio_bitrate = int(audio_stream.get('bit_rate', 0)) if audio_stream else None
            audio_sample_rate = int(audio_stream.get('sample_rate', 0)) if audio_stream else None
            
            return VideoMetadata(
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                bitrate=bitrate,
                codec=codec,
                format=format_name,
                size_bytes=size_bytes,
                aspect_ratio=aspect_ratio,
                has_audio=has_audio,
                audio_codec=audio_codec,
                audio_bitrate=audio_bitrate,
                audio_sample_rate=audio_sample_rate
            )
            
        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            raise
    
    def generate_thumbnails(self, 
                          video_path: str, 
                          count: int = 10, 
                          output_dir: str = None,
                          quality_threshold: float = 0.5) -> List[VideoThumbnail]:
        """Generate high-quality thumbnails from video"""
        try:
            output_dir = output_dir or os.path.join(self.temp_dir, 'thumbnails')
            os.makedirs(output_dir, exist_ok=True)
            
            metadata = self.extract_metadata(video_path)
            duration = metadata.duration
            
            # Calculate thumbnail timestamps
            timestamps = []
            if count == 1:
                timestamps = [duration / 2]  # Middle frame
            else:
                step = duration / (count + 1)
                timestamps = [step * (i + 1) for i in range(count)]
            
            thumbnails = []
            cap = cv2.VideoCapture(video_path)
            
            try:
                for i, timestamp in enumerate(timestamps):
                    # Seek to timestamp
                    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                    ret, frame = cap.read()
                    
                    if not ret:
                        continue
                    
                    # Calculate quality score
                    quality_score = self._calculate_frame_quality(frame)
                    
                    if quality_score < quality_threshold:
                        # Try nearby frames for better quality
                        best_frame = frame
                        best_quality = quality_score
                        
                        for offset in [-1, 1, -2, 2]:
                            test_timestamp = max(0, min(duration, timestamp + offset))
                            cap.set(cv2.CAP_PROP_POS_MSEC, test_timestamp * 1000)
                            ret, test_frame = cap.read()
                            
                            if ret:
                                test_quality = self._calculate_frame_quality(test_frame)
                                if test_quality > best_quality:
                                    best_frame = test_frame
                                    best_quality = test_quality
                                    timestamp = test_timestamp
                        
                        frame = best_frame
                        quality_score = best_quality
                    
                    # Save thumbnail
                    thumbnail_filename = f"thumbnail_{i:03d}_{timestamp:.2f}s.jpg"
                    thumbnail_path = os.path.join(output_dir, thumbnail_filename)
                    
                    # Resize if needed (maintain aspect ratio)
                    height, width = frame.shape[:2]
                    if width > 320:
                        scale = 320 / width
                        new_width = 320
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Save with high quality
                    cv2.imwrite(thumbnail_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    # Check if it's a keyframe
                    is_keyframe = self._is_keyframe(cap)
                    
                    thumbnail = VideoThumbnail(
                        timestamp=timestamp,
                        image_path=thumbnail_path,
                        width=frame.shape[1],
                        height=frame.shape[0],
                        quality_score=quality_score,
                        is_keyframe=is_keyframe
                    )
                    
                    thumbnails.append(thumbnail)
                    logger.info(f"Generated thumbnail at {timestamp:.2f}s with quality {quality_score:.3f}")
                
            finally:
                cap.release()
            
            return thumbnails
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnails: {e}")
            raise
    
    def generate_subtitles(self, 
                         transcript_data: Dict[str, Any], 
                         output_path: str,
                         format_type: str = 'srt',
                         max_chars_per_line: int = 42,
                         max_lines: int = 2) -> str:
        """Generate subtitle files in SRT or VTT format"""
        try:
            # Parse transcript data
            if isinstance(transcript_data, dict) and 'segments' in transcript_data:
                # Whisper-style transcript with segments
                segments = transcript_data['segments']
                subtitle_entries = []
                
                for i, segment in enumerate(segments):
                    start_time = segment.get('start', 0)
                    end_time = segment.get('end', start_time + 3)
                    text = segment.get('text', '').strip()
                    
                    if text:
                        # Split long text into multiple lines
                        lines = self._split_text_for_subtitles(text, max_chars_per_line, max_lines)
                        
                        entry = SubtitleEntry(
                            index=i + 1,
                            start_time=start_time,
                            end_time=end_time,
                            text='\n'.join(lines),
                            confidence=segment.get('confidence')
                        )
                        subtitle_entries.append(entry)
            
            elif isinstance(transcript_data, str):
                # Plain text transcript - create basic timing
                words = transcript_data.split()
                words_per_second = 2.5  # Average speaking rate
                
                subtitle_entries = []
                current_text = []
                current_start = 0
                entry_index = 1
                
                for i, word in enumerate(words):
                    current_text.append(word)
                    
                    # Check if we should create a new subtitle entry
                    text_length = len(' '.join(current_text))
                    if (text_length >= max_chars_per_line * max_lines or 
                        i == len(words) - 1 or
                        word.endswith('.') or word.endswith('!') or word.endswith('?')):
                        
                        end_time = current_start + len(current_text) / words_per_second
                        
                        lines = self._split_text_for_subtitles(' '.join(current_text), max_chars_per_line, max_lines)
                        
                        entry = SubtitleEntry(
                            index=entry_index,
                            start_time=current_start,
                            end_time=end_time,
                            text='\n'.join(lines)
                        )
                        subtitle_entries.append(entry)
                        
                        current_start = end_time
                        current_text = []
                        entry_index += 1
            
            else:
                raise ValueError("Unsupported transcript data format")
            
            # Generate subtitle file
            if format_type.lower() == 'srt':
                content = self._generate_srt_content(subtitle_entries)
            elif format_type.lower() == 'vtt':
                content = self._generate_vtt_content(subtitle_entries)
            else:
                raise ValueError(f"Unsupported subtitle format: {format_type}")
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Generated {format_type.upper()} subtitles with {len(subtitle_entries)} entries")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate subtitles: {e}")
            raise
    
    def detect_chapters(self, 
                       video_path: str, 
                       transcript_data: Dict[str, Any],
                       min_chapter_length: float = 30.0,
                       scene_threshold: float = 0.3) -> List[VideoChapter]:
        """Detect video chapters based on content analysis"""
        try:
            chapters = []
            
            # Method 1: Scene change detection
            scene_chapters = self._detect_scene_changes(video_path, scene_threshold, min_chapter_length)
            
            # Method 2: Content-based detection from transcript
            if transcript_data:
                content_chapters = self._detect_content_chapters(transcript_data, min_chapter_length)
                
                # Merge and optimize chapters
                chapters = self._merge_chapters(scene_chapters, content_chapters)
            else:
                chapters = scene_chapters
            
            # Generate thumbnails for chapters
            for chapter in chapters:
                thumbnail_path = self._generate_chapter_thumbnail(video_path, chapter.start_time)
                chapter.thumbnail_path = thumbnail_path
            
            logger.info(f"Detected {len(chapters)} chapters")
            return chapters
            
        except Exception as e:
            logger.error(f"Failed to detect chapters: {e}")
            return []
    
    def analyze_video_quality(self, video_path: str) -> VideoQualityMetrics:
        """Analyze video quality and provide optimization recommendations"""
        try:
            metadata = self.extract_metadata(video_path)
            
            # Calculate quality scores (0-1 scale)
            resolution_score = self._score_resolution(metadata.width, metadata.height)
            bitrate_score = self._score_bitrate(metadata.bitrate, metadata.width, metadata.height, metadata.fps)
            fps_score = self._score_fps(metadata.fps)
            compression_score = self._score_compression(metadata)
            
            # Calculate overall score
            weights = {'resolution': 0.3, 'bitrate': 0.3, 'fps': 0.2, 'compression': 0.2}
            overall_score = (
                resolution_score * weights['resolution'] +
                bitrate_score * weights['bitrate'] +
                fps_score * weights['fps'] +
                compression_score * weights['compression']
            )
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(metadata, {
                'resolution': resolution_score,
                'bitrate': bitrate_score,
                'fps': fps_score,
                'compression': compression_score
            })
            
            # Technical details
            technical_details = {
                'file_size_mb': metadata.size_bytes / (1024 * 1024),
                'duration_minutes': metadata.duration / 60,
                'bitrate_mbps': metadata.bitrate / 1_000_000,
                'pixels_total': metadata.width * metadata.height,
                'data_rate': metadata.size_bytes / metadata.duration if metadata.duration > 0 else 0
            }
            
            return VideoQualityMetrics(
                resolution_score=resolution_score,
                bitrate_score=bitrate_score,
                fps_score=fps_score,
                compression_score=compression_score,
                overall_score=overall_score,
                recommendations=recommendations,
                technical_details=technical_details
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze video quality: {e}")
            raise
    
    def create_video_preview(self, 
                           video_path: str, 
                           output_path: str,
                           duration: float = 30.0,
                           start_offset: float = 10.0) -> str:
        """Create a short preview clip from the video"""
        try:
            metadata = self.extract_metadata(video_path)
            
            # Adjust start offset if video is too short
            if metadata.duration < start_offset + duration:
                start_offset = max(0, metadata.duration - duration)
                duration = min(duration, metadata.duration)
            
            # Create preview using ffmpeg
            (
                ffmpeg
                .input(video_path, ss=start_offset, t=duration)
                .output(output_path, vcodec='libx264', acodec='aac', preset='fast')
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"Created video preview: {duration}s starting at {start_offset}s")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create video preview: {e}")
            raise
    
    # Helper methods
    
    def _gcd(self, a: int, b: int) -> int:
        """Calculate greatest common divisor"""
        while b:
            a, b = b, a % b
        return a
    
    def _calculate_frame_quality(self, frame: np.ndarray) -> float:
        """Calculate quality score for a frame (0-1 scale)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(1.0, laplacian_var / 1000.0)
            
            # Calculate brightness distribution
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_norm = hist / hist.sum()
            
            # Avoid very dark or very bright images
            dark_pixels = hist_norm[:50].sum()
            bright_pixels = hist_norm[200:].sum()
            brightness_score = 1.0 - max(dark_pixels, bright_pixels)
            
            # Calculate contrast using standard deviation
            contrast_score = min(1.0, gray.std() / 64.0)
            
            # Combined quality score
            quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
            
            return quality_score
            
        except Exception:
            return 0.5  # Default score if calculation fails
    
    def _is_keyframe(self, cap: cv2.VideoCapture) -> bool:
        """Check if current frame is a keyframe"""
        try:
            # This is a simplified check - in practice, keyframe detection
            # would require more sophisticated analysis
            current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            return current_pos % 30 == 0  # Assume keyframes every 30 frames
        except Exception:
            return False
    
    def _split_text_for_subtitles(self, text: str, max_chars_per_line: int, max_lines: int) -> List[str]:
        """Split text into subtitle-appropriate lines"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Check if adding this word would exceed line length
            test_line = ' '.join(current_line + [word])
            
            if len(test_line) <= max_chars_per_line:
                current_line.append(word)
            else:
                # Start new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, split it
                    lines.append(word[:max_chars_per_line])
                    current_line = [word[max_chars_per_line:]] if len(word) > max_chars_per_line else []
                
                # Check max lines limit
                if len(lines) >= max_lines:
                    break
        
        # Add remaining words
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _generate_srt_content(self, entries: List[SubtitleEntry]) -> str:
        """Generate SRT format content"""
        content = []
        
        for entry in entries:
            # Format timestamps
            start_time = self._format_srt_timestamp(entry.start_time)
            end_time = self._format_srt_timestamp(entry.end_time)
            
            # Add entry
            content.append(f"{entry.index}")
            content.append(f"{start_time} --> {end_time}")
            content.append(entry.text)
            content.append("")  # Empty line between entries
        
        return '\n'.join(content)
    
    def _generate_vtt_content(self, entries: List[SubtitleEntry]) -> str:
        """Generate VTT format content"""
        content = ["WEBVTT", ""]
        
        for entry in entries:
            # Format timestamps
            start_time = self._format_vtt_timestamp(entry.start_time)
            end_time = self._format_vtt_timestamp(entry.end_time)
            
            # Add entry
            content.append(f"{start_time} --> {end_time}")
            content.append(entry.text)
            content.append("")  # Empty line between entries
        
        return '\n'.join(content)
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format timestamp for VTT format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def _detect_scene_changes(self, video_path: str, threshold: float, min_length: float) -> List[VideoChapter]:
        """Detect scene changes in video"""
        try:
            chapters = []
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return chapters
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            # Sample frames for scene detection
            sample_interval = max(1, int(fps))  # Sample every second
            prev_frame = None
            scene_changes = [0.0]  # Start with beginning
            
            for frame_num in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                if prev_frame is not None:
                    # Calculate frame difference
                    diff = cv2.absdiff(prev_frame, frame)
                    diff_score = np.mean(diff) / 255.0
                    
                    if diff_score > threshold:
                        timestamp = frame_num / fps
                        # Ensure minimum chapter length
                        if not scene_changes or timestamp - scene_changes[-1] >= min_length:
                            scene_changes.append(timestamp)
                
                prev_frame = frame.copy()
            
            cap.release()
            
            # Add end timestamp
            if not scene_changes or scene_changes[-1] < duration - 1:
                scene_changes.append(duration)
            
            # Create chapters
            for i in range(len(scene_changes) - 1):
                chapter = VideoChapter(
                    start_time=scene_changes[i],
                    end_time=scene_changes[i + 1],
                    title=f"Chapter {i + 1}",
                    description=f"Scene from {self._format_time(scene_changes[i])} to {self._format_time(scene_changes[i + 1])}",
                    confidence=0.7
                )
                chapters.append(chapter)
            
            return chapters
            
        except Exception as e:
            logger.error(f"Failed to detect scene changes: {e}")
            return []
    
    def _detect_content_chapters(self, transcript_data: Dict[str, Any], min_length: float) -> List[VideoChapter]:
        """Detect chapters based on transcript content"""
        try:
            chapters = []
            
            if 'segments' not in transcript_data:
                return chapters
            
            segments = transcript_data['segments']
            current_chapter_start = 0.0
            current_chapter_text = []
            
            # Look for topic changes in transcript
            for i, segment in enumerate(segments):
                text = segment.get('text', '').strip()
                start_time = segment.get('start', 0)
                
                current_chapter_text.append(text)
                
                # Check for chapter boundaries (simple heuristics)
                is_chapter_end = (
                    # Long pause (if available)
                    (i < len(segments) - 1 and 
                     segments[i + 1].get('start', start_time) - segment.get('end', start_time) > 3.0) or
                    # Topic change indicators
                    any(phrase in text.lower() for phrase in [
                        'next topic', 'moving on', 'now let\'s', 'in conclusion',
                        'to summarize', 'next section', 'chapter', 'part'
                    ]) or
                    # Minimum length reached and natural break
                    (start_time - current_chapter_start >= min_length and 
                     text.endswith(('.', '!', '?')))
                )
                
                if is_chapter_end and start_time - current_chapter_start >= min_length:
                    # Create chapter
                    chapter_text = ' '.join(current_chapter_text)
                    title = self._extract_chapter_title(chapter_text)
                    
                    chapter = VideoChapter(
                        start_time=current_chapter_start,
                        end_time=start_time,
                        title=title,
                        description=chapter_text[:200] + '...' if len(chapter_text) > 200 else chapter_text,
                        confidence=0.8,
                        keywords=self._extract_keywords(chapter_text)
                    )
                    chapters.append(chapter)
                    
                    # Start new chapter
                    current_chapter_start = start_time
                    current_chapter_text = []
            
            # Add final chapter if needed
            if current_chapter_text:
                chapter_text = ' '.join(current_chapter_text)
                title = self._extract_chapter_title(chapter_text)
                
                final_segment = segments[-1] if segments else {'end': current_chapter_start + 60}
                
                chapter = VideoChapter(
                    start_time=current_chapter_start,
                    end_time=final_segment.get('end', current_chapter_start + 60),
                    title=title,
                    description=chapter_text[:200] + '...' if len(chapter_text) > 200 else chapter_text,
                    confidence=0.8,
                    keywords=self._extract_keywords(chapter_text)
                )
                chapters.append(chapter)
            
            return chapters
            
        except Exception as e:
            logger.error(f"Failed to detect content chapters: {e}")
            return []
    
    def _merge_chapters(self, scene_chapters: List[VideoChapter], content_chapters: List[VideoChapter]) -> List[VideoChapter]:
        """Merge scene-based and content-based chapters"""
        # For now, prefer content-based chapters if available
        if content_chapters:
            return content_chapters
        return scene_chapters
    
    def _generate_chapter_thumbnail(self, video_path: str, timestamp: float) -> str:
        """Generate thumbnail for a specific chapter"""
        try:
            output_dir = os.path.join(self.temp_dir, 'chapter_thumbnails')
            os.makedirs(output_dir, exist_ok=True)
            
            thumbnail_path = os.path.join(output_dir, f"chapter_{timestamp:.2f}s.jpg")
            
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Resize to standard thumbnail size
                height, width = frame.shape[:2]
                if width > 320:
                    scale = 320 / width
                    new_width = 320
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                
                cv2.imwrite(thumbnail_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                return thumbnail_path
            
        except Exception as e:
            logger.error(f"Failed to generate chapter thumbnail: {e}")
        
        return None
    
    def _extract_chapter_title(self, text: str) -> str:
        """Extract a meaningful title from chapter text"""
        # Simple title extraction - first sentence or key phrases
        sentences = text.split('.')
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) < 60:
                return first_sentence
        
        # Fallback to first few words
        words = text.split()[:8]
        return ' '.join(words) + ('...' if len(text.split()) > 8 else '')
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = text.lower().split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Return top keywords by frequency
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _score_resolution(self, width: int, height: int) -> float:
        """Score video resolution (0-1 scale)"""
        pixels = width * height
        
        # Resolution scoring
        if pixels >= 3840 * 2160:  # 4K
            return 1.0
        elif pixels >= 1920 * 1080:  # 1080p
            return 0.9
        elif pixels >= 1280 * 720:  # 720p
            return 0.7
        elif pixels >= 854 * 480:  # 480p
            return 0.5
        elif pixels >= 640 * 360:  # 360p
            return 0.3
        else:
            return 0.1
    
    def _score_bitrate(self, bitrate: int, width: int, height: int, fps: float) -> float:
        """Score video bitrate relative to resolution and fps"""
        if bitrate == 0:
            return 0.0
        
        pixels = width * height
        bitrate_mbps = bitrate / 1_000_000
        
        # Calculate expected bitrate for quality
        if pixels >= 3840 * 2160:  # 4K
            expected_bitrate = 25 if fps <= 30 else 40
        elif pixels >= 1920 * 1080:  # 1080p
            expected_bitrate = 8 if fps <= 30 else 12
        elif pixels >= 1280 * 720:  # 720p
            expected_bitrate = 5 if fps <= 30 else 7.5
        else:
            expected_bitrate = 2.5
        
        # Score based on how close to expected
        ratio = bitrate_mbps / expected_bitrate
        if 0.8 <= ratio <= 1.5:
            return 1.0
        elif 0.5 <= ratio < 0.8 or 1.5 < ratio <= 2.0:
            return 0.7
        elif 0.3 <= ratio < 0.5 or 2.0 < ratio <= 3.0:
            return 0.5
        else:
            return 0.2
    
    def _score_fps(self, fps: float) -> float:
        """Score video frame rate"""
        if fps >= 60:
            return 1.0
        elif fps >= 30:
            return 0.9
        elif fps >= 24:
            return 0.7
        elif fps >= 15:
            return 0.4
        else:
            return 0.1
    
    def _score_compression(self, metadata: VideoMetadata) -> float:
        """Score compression efficiency"""
        # Simple compression scoring based on file size vs duration and resolution
        if metadata.duration == 0:
            return 0.5
        
        pixels_per_second = metadata.width * metadata.height * metadata.fps
        bytes_per_pixel_per_second = metadata.size_bytes / (pixels_per_second * metadata.duration)
        
        # Typical ranges for different quality levels
        if 0.0001 <= bytes_per_pixel_per_second <= 0.001:
            return 1.0  # Good compression
        elif 0.00005 <= bytes_per_pixel_per_second < 0.0001 or 0.001 < bytes_per_pixel_per_second <= 0.002:
            return 0.7  # Acceptable compression
        else:
            return 0.3  # Poor compression
    
    def _generate_quality_recommendations(self, metadata: VideoMetadata, scores: Dict[str, float]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        # Resolution recommendations
        if scores['resolution'] < 0.7:
            if metadata.width < 1280:
                recommendations.append("Consider recording or encoding at higher resolution (720p minimum recommended)")
        
        # Bitrate recommendations
        if scores['bitrate'] < 0.7:
            if metadata.bitrate < 2_000_000:
                recommendations.append("Increase bitrate for better video quality")
            elif metadata.bitrate > 20_000_000:
                recommendations.append("Consider reducing bitrate to optimize file size")
        
        # FPS recommendations
        if scores['fps'] < 0.7:
            if metadata.fps < 24:
                recommendations.append("Increase frame rate to at least 24 FPS for smoother playback")
        
        # Compression recommendations
        if scores['compression'] < 0.7:
            recommendations.append("Optimize encoding settings for better compression efficiency")
        
        # General recommendations
        if metadata.size_bytes > 500_000_000:  # > 500MB
            recommendations.append("Consider compressing video to reduce file size")
        
        if not metadata.has_audio:
            recommendations.append("Video has no audio track - consider adding audio if needed")
        
        return recommendations


def create_video_player_html(video_path: str, 
                           subtitle_path: str = None,
                           chapters: List[VideoChapter] = None) -> str:
    """Create HTML5 video player with synchronized transcript highlighting"""
    
    video_name = os.path.basename(video_path)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Player - {video_name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .video-container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .video-player {{
                width: 100%;
                background: black;
            }}
            .controls-panel {{
                display: flex;
                height: 400px;
            }}
            .chapters-panel {{
                width: 250px;
                background: #f8f9fa;
                border-right: 1px solid #dee2e6;
                overflow-y: auto;
            }}
            .transcript-panel {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: white;
            }}
            .chapter-item {{
                padding: 12px;
                border-bottom: 1px solid #dee2e6;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .chapter-item:hover {{
                background-color: #e9ecef;
            }}
            .chapter-item.active {{
                background-color: #007bff;
                color: white;
            }}
            .chapter-title {{
                font-weight: bold;
                margin-bottom: 4px;
            }}
            .chapter-time {{
                font-size: 0.9em;
                color: #6c757d;
            }}
            .chapter-item.active .chapter-time {{
                color: #cce7ff;
            }}
            .transcript-segment {{
                margin-bottom: 10px;
                padding: 8px;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .transcript-segment:hover {{
                background-color: #f8f9fa;
            }}
            .transcript-segment.active {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
            }}
            .segment-time {{
                font-size: 0.8em;
                color: #6c757d;
                margin-bottom: 4px;
            }}
            .segment-text {{
                line-height: 1.5;
            }}
            .video-info {{
                padding: 20px;
                background: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}
            .info-item {{
                display: flex;
                justify-content: space-between;
            }}
            .info-label {{
                font-weight: bold;
                color: #495057;
            }}
            .info-value {{
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="video-container">
            <video class="video-player" controls id="videoPlayer">
                <source src="{video_path}" type="video/mp4">
                {f'<track kind="subtitles" src="{subtitle_path}" srclang="en" label="English" default>' if subtitle_path else ''}
                Your browser does not support the video tag.
            </video>
            
            <div class="controls-panel">
                <div class="chapters-panel">
                    <h3 style="padding: 15px; margin: 0; background: #e9ecef; font-size: 1.1em;">Chapters</h3>
                    <div id="chaptersList">
                        <!-- Chapters will be populated by JavaScript -->
                    </div>
                </div>
                
                <div class="transcript-panel">
                    <h3 style="margin-top: 0;">Transcript</h3>
                    <div id="transcriptContent">
                        <!-- Transcript will be populated by JavaScript -->
                    </div>
                </div>
            </div>
            
            <div class="video-info">
                <h3 style="margin-top: 0;">Video Information</h3>
                <div class="info-grid" id="videoInfo">
                    <!-- Video info will be populated by JavaScript -->
                </div>
            </div>
        </div>

        <script>
            // Video player and synchronization logic
            const video = document.getElementById('videoPlayer');
            const chaptersList = document.getElementById('chaptersList');
            const transcriptContent = document.getElementById('transcriptContent');
            const videoInfo = document.getElementById('videoInfo');
            
            // Sample data - in real implementation, this would come from the backend
            const chapters = {json.dumps([asdict(chapter) for chapter in chapters] if chapters else [])};
            const transcript = []; // Would be populated with transcript segments
            
            // Initialize chapters
            function initializeChapters() {{
                if (chapters.length === 0) {{
                    chaptersList.innerHTML = '<p style="padding: 15px; color: #6c757d;">No chapters detected</p>';
                    return;
                }}
                
                chapters.forEach((chapter, index) => {{
                    const chapterElement = document.createElement('div');
                    chapterElement.className = 'chapter-item';
                    chapterElement.innerHTML = `
                        <div class="chapter-title">${{chapter.title}}</div>
                        <div class="chapter-time">${{formatTime(chapter.start_time)}} - ${{formatTime(chapter.end_time)}}</div>
                    `;
                    
                    chapterElement.addEventListener('click', () => {{
                        video.currentTime = chapter.start_time;
                        updateActiveChapter();
                    }});
                    
                    chaptersList.appendChild(chapterElement);
                }});
            }}
            
            // Update active chapter based on current time
            function updateActiveChapter() {{
                const currentTime = video.currentTime;
                const chapterItems = document.querySelectorAll('.chapter-item');
                
                chapters.forEach((chapter, index) => {{
                    const chapterElement = chapterItems[index];
                    if (currentTime >= chapter.start_time && currentTime < chapter.end_time) {{
                        chapterElement.classList.add('active');
                    }} else {{
                        chapterElement.classList.remove('active');
                    }}
                }});
            }}
            
            // Format time in MM:SS format
            function formatTime(seconds) {{
                const minutes = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
            }}
            
            // Initialize video info
            function initializeVideoInfo() {{
                // This would be populated with actual video metadata
                const info = [
                    {{ label: 'Duration', value: formatTime(video.duration || 0) }},
                    {{ label: 'Resolution', value: 'Loading...' }},
                    {{ label: 'File Size', value: 'Loading...' }},
                    {{ label: 'Format', value: 'MP4' }}
                ];
                
                info.forEach(item => {{
                    const infoElement = document.createElement('div');
                    infoElement.className = 'info-item';
                    infoElement.innerHTML = `
                        <span class="info-label">${{item.label}}:</span>
                        <span class="info-value">${{item.value}}</span>
                    `;
                    videoInfo.appendChild(infoElement);
                }});
            }}
            
            // Event listeners
            video.addEventListener('timeupdate', updateActiveChapter);
            video.addEventListener('loadedmetadata', () => {{
                initializeVideoInfo();
            }});
            
            // Initialize
            initializeChapters();
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {{
                if (e.target.tagName.toLowerCase() === 'input') return;
                
                switch(e.key) {{
                    case ' ':
                        e.preventDefault();
                        if (video.paused) {{
                            video.play();
                        }} else {{
                            video.pause();
                        }}
                        break;
                    case 'ArrowLeft':
                        video.currentTime = Math.max(0, video.currentTime - 10);
                        break;
                    case 'ArrowRight':
                        video.currentTime = Math.min(video.duration, video.currentTime + 10);
                        break;
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html_content


# Example usage and testing functions
if __name__ == "__main__":
    # Example usage
    processor = VideoProcessor()
    
    # Test with a sample video file
    video_path = "sample_video.mp4"
    
    if os.path.exists(video_path):
        try:
            # Extract metadata
            metadata = processor.extract_metadata(video_path)
            print(f"Video metadata: {metadata}")
            
            # Generate thumbnails
            thumbnails = processor.generate_thumbnails(video_path, count=5)
            print(f"Generated {len(thumbnails)} thumbnails")
            
            # Analyze quality
            quality = processor.analyze_video_quality(video_path)
            print(f"Video quality score: {quality.overall_score:.2f}")
            print(f"Recommendations: {quality.recommendations}")
            
        except Exception as e:
            print(f"Error processing video: {e}")
    else:
        print("Sample video file not found")