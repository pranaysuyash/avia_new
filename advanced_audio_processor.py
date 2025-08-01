#!/usr/bin/env python3
"""
Advanced Audio Processing Module
Implements advanced audio processing features including noise reduction,
quality analysis, trimming, segmentation, real-time streaming, and bookmarking.
"""

import os
import logging
import tempfile
import numpy as np
import librosa
import soundfile as sf
from typing import List, Tuple, Dict, Optional, Generator, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import threading
import queue
import time

from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import detect_silence

logger = logging.getLogger(__name__)

@dataclass
class AudioBookmark:
    """Represents an audio bookmark with metadata"""
    timestamp: float
    title: str
    description: str = ""
    created_at: datetime = None
    bookmark_type: str = "manual"  # manual, auto, chapter
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AudioChapter:
    """Represents an audio chapter with start/end times"""
    start_time: float
    end_time: float
    title: str
    description: str = ""
    confidence: float = 1.0  # For auto-generated chapters

@dataclass
class AudioQualityMetrics:
    """Audio quality analysis metrics"""
    snr_db: float  # Signal-to-noise ratio
    dynamic_range_db: float
    spectral_centroid: float
    zero_crossing_rate: float
    rms_energy: float
    spectral_rolloff: float
    mfcc_features: np.ndarray
    quality_score: float  # Overall quality score 0-100
    recommendations: List[str]

class NoiseReducer:
    """Advanced noise reduction using spectral subtraction"""
    
    def __init__(self, noise_factor: float = 0.8, stationary: bool = True):
        self.noise_factor = noise_factor
        self.stationary = stationary
    
    def reduce_noise(self, audio_path: str, noise_duration: float = 1.0) -> str:
        """
        Reduce noise using spectral subtraction
        
        Args:
            audio_path: Path to input audio file
            noise_duration: Duration of noise sample from beginning (seconds)
            
        Returns:
            Path to noise-reduced audio file
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Estimate noise from the first portion
            noise_sample_length = int(noise_duration * sr)
            noise_sample = y[:noise_sample_length]
            
            # Compute STFT
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise spectrum
            noise_stft = librosa.stft(noise_sample)
            noise_magnitude = np.abs(noise_stft)
            noise_power = np.mean(noise_magnitude ** 2, axis=1, keepdims=True)
            
            # Spectral subtraction
            signal_power = magnitude ** 2
            enhanced_power = signal_power - self.noise_factor * noise_power
            
            # Ensure non-negative values
            enhanced_power = np.maximum(enhanced_power, 0.1 * signal_power)
            enhanced_magnitude = np.sqrt(enhanced_power)
            
            # Reconstruct signal
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft)
            
            # Save enhanced audio
            output_path = self._create_temp_file("_noise_reduced.wav")
            sf.write(output_path, enhanced_audio, sr)
            
            logger.info(f"Noise reduction applied: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Noise reduction failed: {e}")
            return audio_path
    
    def _create_temp_file(self, suffix: str) -> str:
        """Create temporary file"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        return temp_file.name

class AudioQualityAnalyzer:
    """Analyze audio quality and provide optimization suggestions"""
    
    def analyze_quality(self, audio_path: str) -> AudioQualityMetrics:
        """
        Comprehensive audio quality analysis
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            AudioQualityMetrics object with analysis results
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculate various quality metrics
            snr_db = self._calculate_snr(y)
            dynamic_range_db = self._calculate_dynamic_range(y)
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
            rms_energy = np.mean(librosa.feature.rms(y=y))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            mfcc_features = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13), axis=1)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                snr_db, dynamic_range_db, spectral_centroid, zero_crossing_rate, rms_energy
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                snr_db, dynamic_range_db, spectral_centroid, rms_energy
            )
            
            return AudioQualityMetrics(
                snr_db=snr_db,
                dynamic_range_db=dynamic_range_db,
                spectral_centroid=spectral_centroid,
                zero_crossing_rate=zero_crossing_rate,
                rms_energy=rms_energy,
                spectral_rolloff=spectral_rolloff,
                mfcc_features=mfcc_features,
                quality_score=quality_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return AudioQualityMetrics(
                snr_db=0, dynamic_range_db=0, spectral_centroid=0,
                zero_crossing_rate=0, rms_energy=0, spectral_rolloff=0,
                mfcc_features=np.array([]), quality_score=0,
                recommendations=["Analysis failed - check audio file format"]
            )
    
    def _calculate_snr(self, y: np.ndarray) -> float:
        """Calculate signal-to-noise ratio"""
        # Simple SNR estimation using signal power vs noise floor
        signal_power = np.mean(y ** 2)
        noise_power = np.mean(np.sort(y ** 2)[:len(y) // 10])  # Bottom 10% as noise
        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
        else:
            snr = 60  # Very high SNR if no detectable noise
        return float(snr)
    
    def _calculate_dynamic_range(self, y: np.ndarray) -> float:
        """Calculate dynamic range in dB"""
        max_amplitude = np.max(np.abs(y))
        min_amplitude = np.mean(np.sort(np.abs(y))[:len(y) // 100])  # Bottom 1%
        if min_amplitude > 0:
            dynamic_range = 20 * np.log10(max_amplitude / min_amplitude)
        else:
            dynamic_range = 96  # Theoretical max for 16-bit audio
        return float(dynamic_range)
    
    def _calculate_quality_score(self, snr: float, dynamic_range: float, 
                               spectral_centroid: float, zcr: float, rms: float) -> float:
        """Calculate overall quality score (0-100)"""
        # Normalize metrics and combine
        snr_score = min(100, max(0, (snr + 10) * 2))  # -10dB to 40dB -> 0-100
        dr_score = min(100, max(0, dynamic_range * 2))  # 0-50dB -> 0-100
        
        # Spectral centroid should be in speech range (500-4000 Hz)
        sc_score = 100 - abs(spectral_centroid - 2000) / 20
        sc_score = min(100, max(0, sc_score))
        
        # Combine scores with weights
        quality_score = (snr_score * 0.4 + dr_score * 0.3 + sc_score * 0.3)
        return float(quality_score)
    
    def _generate_recommendations(self, snr: float, dynamic_range: float,
                                spectral_centroid: float, rms: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if snr < 10:
            recommendations.append("Apply noise reduction - low signal-to-noise ratio detected")
        
        if dynamic_range < 20:
            recommendations.append("Audio appears compressed - consider using original source")
        
        if spectral_centroid < 500:
            recommendations.append("Audio may be muffled - apply high-pass filter")
        elif spectral_centroid > 4000:
            recommendations.append("Audio may be harsh - apply low-pass filter")
        
        if rms < 0.01:
            recommendations.append("Audio level is very low - apply normalization")
        elif rms > 0.5:
            recommendations.append("Audio level is very high - reduce gain to prevent clipping")
        
        if not recommendations:
            recommendations.append("Audio quality is good - no specific optimizations needed")
        
        return recommendations

class AudioTrimmer:
    """Advanced audio trimming and segmentation tools"""
    
    def trim_silence(self, audio_path: str, silence_thresh: int = -40,
                    min_silence_len: int = 1000, keep_silence: int = 100) -> str:
        """
        Trim silence from beginning and end of audio
        
        Args:
            audio_path: Path to input audio file
            silence_thresh: Silence threshold in dBFS
            min_silence_len: Minimum silence length to trim (ms)
            keep_silence: Amount of silence to keep (ms)
            
        Returns:
            Path to trimmed audio file
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Detect silence at beginning and end
            silence_ranges = detect_silence(
                audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
            )
            
            if not silence_ranges:
                return audio_path  # No silence to trim
            
            # Find start and end points
            start_trim = 0
            end_trim = len(audio)
            
            # Trim from beginning
            if silence_ranges[0][0] == 0:
                start_trim = max(0, silence_ranges[0][1] - keep_silence)
            
            # Trim from end
            if silence_ranges[-1][1] == len(audio):
                end_trim = min(len(audio), silence_ranges[-1][0] + keep_silence)
            
            # Apply trimming
            trimmed_audio = audio[start_trim:end_trim]
            
            # Save trimmed audio
            output_path = self._create_temp_file("_trimmed.wav")
            trimmed_audio.export(output_path, format="wav")
            
            logger.info(f"Audio trimmed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio trimming failed: {e}")
            return audio_path
    
    def segment_by_silence(self, audio_path: str, silence_thresh: int = -40,
                          min_silence_len: int = 500, min_segment_len: int = 2000) -> List[str]:
        """
        Segment audio by silence detection
        
        Args:
            audio_path: Path to input audio file
            silence_thresh: Silence threshold in dBFS
            min_silence_len: Minimum silence length for splitting (ms)
            min_segment_len: Minimum segment length (ms)
            
        Returns:
            List of paths to audio segments
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Detect silence
            silence_ranges = detect_silence(
                audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
            )
            
            if not silence_ranges:
                return [audio_path]  # No silence found, return original
            
            # Create segments
            segments = []
            last_end = 0
            
            for silence_start, silence_end in silence_ranges:
                # Create segment from last_end to silence_start
                if silence_start - last_end >= min_segment_len:
                    segment = audio[last_end:silence_start]
                    segment_path = self._create_temp_file(f"_segment_{len(segments):03d}.wav")
                    segment.export(segment_path, format="wav")
                    segments.append(segment_path)
                
                last_end = silence_end
            
            # Add final segment
            if len(audio) - last_end >= min_segment_len:
                segment = audio[last_end:]
                segment_path = self._create_temp_file(f"_segment_{len(segments):03d}.wav")
                segment.export(segment_path, format="wav")
                segments.append(segment_path)
            
            logger.info(f"Audio segmented into {len(segments)} parts by silence")
            return segments if segments else [audio_path]
            
        except Exception as e:
            logger.error(f"Silence-based segmentation failed: {e}")
            return [audio_path]
    
    def extract_segment(self, audio_path: str, start_time: float, end_time: float) -> str:
        """
        Extract specific time segment from audio
        
        Args:
            audio_path: Path to input audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Path to extracted segment
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Convert to milliseconds
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            # Extract segment
            segment = audio[start_ms:end_ms]
            
            # Save segment
            output_path = self._create_temp_file(f"_segment_{start_time:.1f}_{end_time:.1f}.wav")
            segment.export(output_path, format="wav")
            
            logger.info(f"Segment extracted: {start_time:.1f}s-{end_time:.1f}s from {audio_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Segment extraction failed: {e}")
            return audio_path
    
    def _create_temp_file(self, suffix: str) -> str:
        """Create temporary file"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        return temp_file.name

class RealTimeStreamProcessor:
    """Real-time audio streaming and transcription support"""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_streaming = False
        self.stream_thread = None
        self.callbacks = []
    
    def add_callback(self, callback):
        """Add callback function for processed audio chunks"""
        self.callbacks.append(callback)
    
    def start_streaming(self, audio_source=None):
        """
        Start real-time audio streaming
        
        Args:
            audio_source: Audio source (microphone, file, etc.)
        """
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stream_thread = threading.Thread(target=self._stream_worker, args=(audio_source,))
        self.stream_thread.start()
        logger.info("Real-time streaming started")
    
    def stop_streaming(self):
        """Stop real-time audio streaming"""
        self.is_streaming = False
        if self.stream_thread:
            self.stream_thread.join()
        logger.info("Real-time streaming stopped")
    
    def process_chunk(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """
        Process individual audio chunk
        
        Args:
            audio_chunk: Audio data chunk
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Basic audio analysis
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            zero_crossings = np.sum(np.diff(np.signbit(audio_chunk)))
            
            # Voice activity detection (simple energy-based)
            is_speech = rms > 0.01 and zero_crossings > 10
            
            result = {
                'timestamp': time.time(),
                'rms': float(rms),
                'zero_crossings': int(zero_crossings),
                'is_speech': is_speech,
                'chunk_size': len(audio_chunk)
            }
            
            # Call registered callbacks
            for callback in self.callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Chunk processing failed: {e}")
            return {'error': str(e)}
    
    def _stream_worker(self, audio_source):
        """Worker thread for streaming processing"""
        # This is a placeholder for actual streaming implementation
        # In a real implementation, this would interface with audio input devices
        logger.info("Stream worker started (placeholder implementation)")
        
        while self.is_streaming:
            try:
                # Simulate audio chunk processing
                time.sleep(0.1)  # 100ms chunks
                
                # In real implementation, get audio from source
                # For now, just process empty chunks
                dummy_chunk = np.zeros(self.chunk_size)
                self.process_chunk(dummy_chunk)
                
            except Exception as e:
                logger.error(f"Stream worker error: {e}")
                break

class AudioBookmarkManager:
    """Manage audio bookmarks and chapters"""
    
    def __init__(self):
        self.bookmarks: List[AudioBookmark] = []
        self.chapters: List[AudioChapter] = []
    
    def add_bookmark(self, timestamp: float, title: str, description: str = "",
                    bookmark_type: str = "manual") -> AudioBookmark:
        """
        Add a bookmark at specified timestamp
        
        Args:
            timestamp: Time position in seconds
            title: Bookmark title
            description: Optional description
            bookmark_type: Type of bookmark (manual, auto, chapter)
            
        Returns:
            Created AudioBookmark object
        """
        bookmark = AudioBookmark(
            timestamp=timestamp,
            title=title,
            description=description,
            bookmark_type=bookmark_type
        )
        
        self.bookmarks.append(bookmark)
        self.bookmarks.sort(key=lambda b: b.timestamp)
        
        logger.info(f"Bookmark added: {title} at {timestamp:.1f}s")
        return bookmark
    
    def remove_bookmark(self, timestamp: float, tolerance: float = 1.0) -> bool:
        """
        Remove bookmark near specified timestamp
        
        Args:
            timestamp: Target timestamp
            tolerance: Time tolerance in seconds
            
        Returns:
            True if bookmark was removed
        """
        for i, bookmark in enumerate(self.bookmarks):
            if abs(bookmark.timestamp - timestamp) <= tolerance:
                removed = self.bookmarks.pop(i)
                logger.info(f"Bookmark removed: {removed.title}")
                return True
        return False
    
    def get_bookmarks_in_range(self, start_time: float, end_time: float) -> List[AudioBookmark]:
        """Get bookmarks within time range"""
        return [b for b in self.bookmarks if start_time <= b.timestamp <= end_time]
    
    def auto_generate_chapters(self, audio_path: str, min_chapter_length: float = 60.0) -> List[AudioChapter]:
        """
        Automatically generate chapters based on audio analysis
        
        Args:
            audio_path: Path to audio file
            min_chapter_length: Minimum chapter length in seconds
            
        Returns:
            List of generated AudioChapter objects
        """
        try:
            # Load audio for analysis
            y, sr = librosa.load(audio_path, sr=None)
            duration = len(y) / sr
            
            # Simple chapter detection based on silence and energy changes
            # This is a basic implementation - could be enhanced with more sophisticated methods
            
            # Detect major silence breaks
            audio_segment = AudioSegment.from_file(audio_path)
            silence_ranges = detect_silence(
                audio_segment, min_silence_len=2000, silence_thresh=-30
            )
            
            # Convert to seconds and filter by minimum chapter length
            chapter_breaks = [0.0]  # Always start with beginning
            
            for silence_start, silence_end in silence_ranges:
                break_time = silence_start / 1000.0  # Convert to seconds
                if break_time - chapter_breaks[-1] >= min_chapter_length:
                    chapter_breaks.append(break_time)
            
            # Add end time
            if duration - chapter_breaks[-1] >= min_chapter_length / 2:
                chapter_breaks.append(duration)
            
            # Create chapters
            chapters = []
            for i in range(len(chapter_breaks) - 1):
                start_time = chapter_breaks[i]
                end_time = chapter_breaks[i + 1]
                
                chapter = AudioChapter(
                    start_time=start_time,
                    end_time=end_time,
                    title=f"Chapter {i + 1}",
                    description=f"Auto-generated chapter from {start_time:.1f}s to {end_time:.1f}s",
                    confidence=0.7  # Moderate confidence for auto-generated
                )
                chapters.append(chapter)
            
            self.chapters.extend(chapters)
            logger.info(f"Generated {len(chapters)} automatic chapters")
            return chapters
            
        except Exception as e:
            logger.error(f"Auto chapter generation failed: {e}")
            return []
    
    def add_chapter(self, start_time: float, end_time: float, title: str,
                   description: str = "", confidence: float = 1.0) -> AudioChapter:
        """
        Add a manual chapter
        
        Args:
            start_time: Chapter start time in seconds
            end_time: Chapter end time in seconds
            title: Chapter title
            description: Optional description
            confidence: Confidence score (1.0 for manual)
            
        Returns:
            Created AudioChapter object
        """
        chapter = AudioChapter(
            start_time=start_time,
            end_time=end_time,
            title=title,
            description=description,
            confidence=confidence
        )
        
        self.chapters.append(chapter)
        self.chapters.sort(key=lambda c: c.start_time)
        
        logger.info(f"Chapter added: {title} ({start_time:.1f}s - {end_time:.1f}s)")
        return chapter
    
    def export_bookmarks(self, output_path: str):
        """Export bookmarks to JSON file"""
        try:
            data = {
                'bookmarks': [
                    {
                        'timestamp': b.timestamp,
                        'title': b.title,
                        'description': b.description,
                        'created_at': b.created_at.isoformat(),
                        'bookmark_type': b.bookmark_type
                    }
                    for b in self.bookmarks
                ],
                'chapters': [
                    {
                        'start_time': c.start_time,
                        'end_time': c.end_time,
                        'title': c.title,
                        'description': c.description,
                        'confidence': c.confidence
                    }
                    for c in self.chapters
                ]
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Bookmarks exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Bookmark export failed: {e}")
    
    def import_bookmarks(self, input_path: str):
        """Import bookmarks from JSON file"""
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Import bookmarks
            for b_data in data.get('bookmarks', []):
                bookmark = AudioBookmark(
                    timestamp=b_data['timestamp'],
                    title=b_data['title'],
                    description=b_data.get('description', ''),
                    bookmark_type=b_data.get('bookmark_type', 'manual'),
                    created_at=datetime.fromisoformat(b_data['created_at'])
                )
                self.bookmarks.append(bookmark)
            
            # Import chapters
            for c_data in data.get('chapters', []):
                chapter = AudioChapter(
                    start_time=c_data['start_time'],
                    end_time=c_data['end_time'],
                    title=c_data['title'],
                    description=c_data.get('description', ''),
                    confidence=c_data.get('confidence', 1.0)
                )
                self.chapters.append(chapter)
            
            # Sort by timestamp
            self.bookmarks.sort(key=lambda b: b.timestamp)
            self.chapters.sort(key=lambda c: c.start_time)
            
            logger.info(f"Imported {len(self.bookmarks)} bookmarks and {len(self.chapters)} chapters")
            
        except Exception as e:
            logger.error(f"Bookmark import failed: {e}")

class AdvancedAudioProcessor:
    """Main class combining all advanced audio processing features"""
    
    def __init__(self):
        self.noise_reducer = NoiseReducer()
        self.quality_analyzer = AudioQualityAnalyzer()
        self.trimmer = AudioTrimmer()
        self.stream_processor = RealTimeStreamProcessor()
        self.bookmark_manager = AudioBookmarkManager()
        self.temp_files = []
    
    def enhance_audio(self, audio_path: str, apply_noise_reduction: bool = True,
                     apply_normalization: bool = True, trim_silence: bool = True) -> str:
        """
        Apply comprehensive audio enhancement
        
        Args:
            audio_path: Path to input audio file
            apply_noise_reduction: Whether to apply noise reduction
            apply_normalization: Whether to normalize audio levels
            trim_silence: Whether to trim silence from ends
            
        Returns:
            Path to enhanced audio file
        """
        try:
            enhanced_path = audio_path
            
            # Apply noise reduction
            if apply_noise_reduction:
                enhanced_path = self.noise_reducer.reduce_noise(enhanced_path)
                self.temp_files.append(enhanced_path)
            
            # Trim silence
            if trim_silence:
                enhanced_path = self.trimmer.trim_silence(enhanced_path)
                self.temp_files.append(enhanced_path)
            
            # Apply normalization using pydub
            if apply_normalization:
                audio = AudioSegment.from_file(enhanced_path)
                normalized_audio = normalize(audio)
                
                output_path = self._create_temp_file("_enhanced.wav")
                normalized_audio.export(output_path, format="wav")
                enhanced_path = output_path
                self.temp_files.append(enhanced_path)
            
            logger.info(f"Audio enhancement complete: {audio_path} -> {enhanced_path}")
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            return audio_path
    
    def analyze_and_optimize(self, audio_path: str) -> Tuple[AudioQualityMetrics, str]:
        """
        Analyze audio quality and apply optimizations
        
        Args:
            audio_path: Path to input audio file
            
        Returns:
            Tuple of (quality metrics, optimized audio path)
        """
        # Analyze quality
        metrics = self.quality_analyzer.analyze_quality(audio_path)
        
        # Apply optimizations based on analysis
        optimized_path = audio_path
        
        if metrics.snr_db < 15:
            optimized_path = self.noise_reducer.reduce_noise(optimized_path)
            self.temp_files.append(optimized_path)
        
        if metrics.rms_energy < 0.01 or metrics.rms_energy > 0.5:
            audio = AudioSegment.from_file(optimized_path)
            normalized_audio = normalize(audio)
            
            temp_path = self._create_temp_file("_optimized.wav")
            normalized_audio.export(temp_path, format="wav")
            optimized_path = temp_path
            self.temp_files.append(optimized_path)
        
        return metrics, optimized_path
    
    def create_segments_with_bookmarks(self, audio_path: str, segment_method: str = "silence") -> Dict[str, Any]:
        """
        Create audio segments and generate bookmarks
        
        Args:
            audio_path: Path to input audio file
            segment_method: Segmentation method ("silence", "time", "auto")
            
        Returns:
            Dictionary with segments and bookmarks
        """
        try:
            segments = []
            
            if segment_method == "silence":
                segments = self.trimmer.segment_by_silence(audio_path)
            elif segment_method == "time":
                # 5-minute segments
                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)
                segment_length_ms = 5 * 60 * 1000  # 5 minutes
                
                for i in range(0, duration_ms, segment_length_ms):
                    end_time = min(i + segment_length_ms, duration_ms)
                    segment = audio[i:end_time]
                    
                    segment_path = self._create_temp_file(f"_time_segment_{i//1000:04d}.wav")
                    segment.export(segment_path, format="wav")
                    segments.append(segment_path)
                    self.temp_files.append(segment_path)
            
            # Create bookmarks for segments
            current_time = 0.0
            for i, segment_path in enumerate(segments):
                segment_audio = AudioSegment.from_file(segment_path)
                segment_duration = len(segment_audio) / 1000.0
                
                self.bookmark_manager.add_bookmark(
                    timestamp=current_time,
                    title=f"Segment {i + 1}",
                    description=f"Auto-generated segment bookmark",
                    bookmark_type="auto"
                )
                
                current_time += segment_duration
            
            # Auto-generate chapters
            chapters = self.bookmark_manager.auto_generate_chapters(audio_path)
            
            return {
                'segments': segments,
                'bookmarks': self.bookmark_manager.bookmarks,
                'chapters': chapters,
                'total_segments': len(segments)
            }
            
        except Exception as e:
            logger.error(f"Segmentation with bookmarks failed: {e}")
            return {'segments': [audio_path], 'bookmarks': [], 'chapters': []}
    
    def _create_temp_file(self, suffix: str) -> str:
        """Create temporary file and track for cleanup"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        return temp_file.name
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_file}: {e}")
        self.temp_files.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()

# Convenience functions for easy integration
def enhance_audio_for_transcription(audio_path: str, **kwargs) -> str:
    """
    Enhance audio file for optimal transcription quality
    
    Args:
        audio_path: Path to input audio file
        **kwargs: Enhancement options
        
    Returns:
        Path to enhanced audio file
    """
    processor = AdvancedAudioProcessor()
    try:
        enhanced_path = processor.enhance_audio(audio_path, **kwargs)
        # Don't cleanup automatically - let caller handle cleanup
        # processor.cleanup()
        return enhanced_path
    except Exception as e:
        logger.error(f"Audio enhancement failed: {e}")
        return audio_path

def analyze_audio_quality(audio_path: str) -> AudioQualityMetrics:
    """
    Analyze audio quality and get recommendations
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        AudioQualityMetrics object
    """
    analyzer = AudioQualityAnalyzer()
    return analyzer.analyze_quality(audio_path)

def create_audio_segments(audio_path: str, method: str = "silence") -> List[str]:
    """
    Create audio segments using specified method
    
    Args:
        audio_path: Path to input audio file
        method: Segmentation method
        
    Returns:
        List of segment file paths
    """
    processor = AdvancedAudioProcessor()
    try:
        result = processor.create_segments_with_bookmarks(audio_path, method)
        return result['segments']
    except Exception as e:
        logger.error(f"Audio segmentation failed: {e}")
        return [audio_path]