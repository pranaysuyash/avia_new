#!/usr/bin/env python3
"""
Audio Processing Integration Module
Seamlessly integrates all audio processing features into the main application
"""

import os
import logging
import tempfile
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import time

from audio_processor import AudioProcessor
from advanced_audio_processor import (
    AdvancedAudioProcessor,
    AudioQualityMetrics,
    AudioBookmark,
    AudioChapter
)

logger = logging.getLogger(__name__)

class AudioProcessingIntegration:
    """Integrates audio processing into the main transcription workflow"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.advanced_processor = AdvancedAudioProcessor()
        self._temp_files = []
        
    def enhance_for_transcription(self, audio_path: str, 
                                settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enhance audio specifically for transcription accuracy
        
        Args:
            audio_path: Path to input audio file
            settings: Optional enhancement settings
            
        Returns:
            Dictionary with enhanced audio path and metadata
        """
        if settings is None:
            settings = self._get_default_transcription_settings()
        
        result = {
            'original_path': audio_path,
            'enhanced_path': audio_path,
            'quality_metrics': None,
            'segments': [],
            'bookmarks': [],
            'chapters': [],
            'processing_time': 0,
            'enhancements_applied': []
        }
        
        start_time = time.time()
        
        try:
            # Analyze original quality
            logger.info("Analyzing audio quality...")
            quality_metrics = self.advanced_processor.quality_analyzer.analyze_quality(audio_path)
            result['quality_metrics'] = quality_metrics
            
            # Determine which enhancements to apply based on quality
            enhancements_needed = self._determine_enhancements(quality_metrics, settings)
            
            current_path = audio_path
            
            # Apply enhancements in optimal order
            if enhancements_needed.get('noise_reduction'):
                logger.info("Applying noise reduction...")
                current_path = self.advanced_processor.noise_reducer.reduce_noise(
                    current_path,
                    noise_duration=settings.get('noise_sample_duration', 1.0)
                )
                self._temp_files.append(current_path)
                result['enhancements_applied'].append('Noise Reduction')
            
            if enhancements_needed.get('trim_silence'):
                logger.info("Trimming silence...")
                current_path = self.advanced_processor.trimmer.trim_silence(
                    current_path,
                    silence_thresh=settings.get('silence_threshold', -40),
                    min_silence_len=settings.get('min_silence_len', 1000),
                    keep_silence=settings.get('keep_silence', 100)
                )
                self._temp_files.append(current_path)
                result['enhancements_applied'].append('Silence Trimming')
            
            if enhancements_needed.get('normalize_volume'):
                logger.info("Normalizing volume...")
                current_path = self.audio_processor.normalize_volume(
                    current_path,
                    target_dBFS=settings.get('target_volume', -20.0)
                )
                self._temp_files.append(current_path)
                result['enhancements_applied'].append('Volume Normalization')
            
            if enhancements_needed.get('compress_dynamic_range'):
                logger.info("Applying dynamic range compression...")
                current_path = self.audio_processor.compress_dynamic_range(
                    current_path,
                    threshold=settings.get('compression_threshold', -20.0),
                    ratio=settings.get('compression_ratio', 4.0),
                    attack=settings.get('compression_attack', 5.0),
                    release=settings.get('compression_release', 50.0)
                )
                self._temp_files.append(current_path)
                result['enhancements_applied'].append('Dynamic Range Compression')
            
            # Handle segmentation if needed
            if settings.get('segment_long_audio', False):
                logger.info("Segmenting audio...")
                segment_result = self._segment_audio(current_path, settings)
                result['segments'] = segment_result['segments']
                result['bookmarks'] = segment_result['bookmarks']
                result['chapters'] = segment_result['chapters']
                if segment_result['segments']:
                    result['enhancements_applied'].append('Audio Segmentation')
            
            result['enhanced_path'] = current_path
            result['processing_time'] = time.time() - start_time
            
            # Re-analyze quality if enhancements were applied
            if current_path != audio_path:
                result['quality_after'] = self.advanced_processor.quality_analyzer.analyze_quality(current_path)
            
            logger.info(f"Audio enhancement complete. Applied {len(result['enhancements_applied'])} enhancements in {result['processing_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Audio enhancement error: {e}")
            result['error'] = str(e)
        
        return result
    
    def process_for_specific_use_case(self, audio_path: str, use_case: str) -> Dict[str, Any]:
        """
        Process audio optimized for specific use cases
        
        Args:
            audio_path: Path to input audio
            use_case: One of 'meeting', 'podcast', 'lecture', 'interview', 'dictation'
            
        Returns:
            Processing results dictionary
        """
        use_case_settings = {
            'meeting': {
                'noise_reduction': True,
                'normalize_volume': True,
                'target_volume': -18,
                'compress_dynamic_range': True,
                'compression_ratio': 5.0,
                'trim_silence': False,  # Keep pauses in meetings
                'segment_long_audio': True,
                'segment_method': 'silence',
                'min_segment_duration': 30  # 30 second minimum segments
            },
            'podcast': {
                'noise_reduction': True,
                'normalize_volume': True,
                'target_volume': -16,
                'compress_dynamic_range': True,
                'compression_ratio': 4.0,
                'trim_silence': True,
                'silence_threshold': -45,
                'segment_long_audio': False
            },
            'lecture': {
                'noise_reduction': True,
                'normalize_volume': True,
                'target_volume': -20,
                'compress_dynamic_range': True,
                'compression_ratio': 3.5,
                'trim_silence': True,
                'segment_long_audio': True,
                'segment_method': 'time',
                'segment_minutes': 10  # 10-minute segments
            },
            'interview': {
                'noise_reduction': True,
                'normalize_volume': True,
                'target_volume': -18,
                'compress_dynamic_range': True,
                'compression_ratio': 3.5,
                'trim_silence': True,
                'silence_threshold': -42,
                'segment_long_audio': False
            },
            'dictation': {
                'noise_reduction': True,
                'normalize_volume': True,
                'target_volume': -20,
                'compress_dynamic_range': False,  # Preserve natural speech dynamics
                'trim_silence': True,
                'silence_threshold': -38,
                'segment_long_audio': False
            }
        }
        
        settings = use_case_settings.get(use_case, self._get_default_transcription_settings())
        settings['use_case'] = use_case
        
        return self.enhance_for_transcription(audio_path, settings)
    
    def batch_process_audio_files(self, file_paths: List[str], 
                                 settings: Optional[Dict[str, Any]] = None,
                                 progress_callback=None) -> List[Dict[str, Any]]:
        """
        Process multiple audio files in batch
        
        Args:
            file_paths: List of audio file paths
            settings: Enhancement settings
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processing results
        """
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            if progress_callback:
                progress_callback(i / total_files, f"Processing {os.path.basename(file_path)}...")
            
            try:
                result = self.enhance_for_transcription(file_path, settings)
                result['file_index'] = i
                result['file_name'] = os.path.basename(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results.append({
                    'file_index': i,
                    'file_name': os.path.basename(file_path),
                    'error': str(e)
                })
        
        if progress_callback:
            progress_callback(1.0, "Batch processing complete")
        
        return results
    
    def _determine_enhancements(self, metrics: AudioQualityMetrics, 
                              settings: Dict[str, Any]) -> Dict[str, bool]:
        """
        Intelligently determine which enhancements to apply based on quality metrics
        
        Args:
            metrics: Audio quality metrics
            settings: User settings
            
        Returns:
            Dictionary of enhancement flags
        """
        enhancements = {
            'noise_reduction': False,
            'normalize_volume': False,
            'compress_dynamic_range': False,
            'trim_silence': False
        }
        
        # Check if noise reduction is needed
        if settings.get('noise_reduction', True) and metrics.snr_db < 15:
            enhancements['noise_reduction'] = True
        
        # Check if volume normalization is needed
        if settings.get('normalize_volume', True) and (
            metrics.rms_energy < 0.01 or metrics.rms_energy > 0.5
        ):
            enhancements['normalize_volume'] = True
        
        # Check if dynamic range compression is needed
        if settings.get('compress_dynamic_range', True) and metrics.dynamic_range_db > 40:
            enhancements['compress_dynamic_range'] = True
        
        # Silence trimming is usually safe to apply
        if settings.get('trim_silence', True):
            enhancements['trim_silence'] = True
        
        return enhancements
    
    def _segment_audio(self, audio_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Segment audio based on settings
        
        Args:
            audio_path: Path to audio file
            settings: Segmentation settings
            
        Returns:
            Dictionary with segments, bookmarks, and chapters
        """
        method = settings.get('segment_method', 'silence')
        
        if method == 'silence':
            segments = self.advanced_processor.trimmer.segment_by_silence(
                audio_path,
                silence_thresh=settings.get('silence_segment_threshold', -40),
                min_silence_len=settings.get('min_silence_for_split', 500),
                min_segment_len=settings.get('min_segment_duration', 2000)
            )
        elif method == 'time':
            minutes = settings.get('segment_minutes', 5)
            segments = self._segment_by_fixed_time(audio_path, minutes)
        else:  # auto
            result = self.advanced_processor.create_segments_with_bookmarks(
                audio_path,
                segment_method='auto'
            )
            return result
        
        # Create bookmarks for segments
        bookmarks = []
        current_time = 0.0
        
        for i, segment_path in enumerate(segments):
            from pydub import AudioSegment
            segment_audio = AudioSegment.from_file(segment_path)
            duration = len(segment_audio) / 1000.0
            
            bookmark = self.advanced_processor.bookmark_manager.add_bookmark(
                timestamp=current_time,
                title=f"Segment {i + 1}",
                description=f"Auto-generated segment",
                bookmark_type="auto"
            )
            bookmarks.append(bookmark)
            
            current_time += duration
        
        return {
            'segments': segments,
            'bookmarks': bookmarks,
            'chapters': []
        }
    
    def _segment_by_fixed_time(self, audio_path: str, minutes: int) -> List[str]:
        """Segment audio by fixed time intervals"""
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        segment_length_ms = minutes * 60 * 1000
        
        segments = []
        for i in range(0, duration_ms, segment_length_ms):
            end_time = min(i + segment_length_ms, duration_ms)
            segment = audio[i:end_time]
            
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_segment_{i//60000:03d}.wav",
                delete=False
            )
            segment.export(temp_file.name, format="wav")
            segments.append(temp_file.name)
            self._temp_files.append(temp_file.name)
        
        return segments
    
    def _get_default_transcription_settings(self) -> Dict[str, Any]:
        """Get default settings optimized for transcription"""
        return {
            'noise_reduction': True,
            'normalize_volume': True,
            'target_volume': -20.0,
            'compress_dynamic_range': True,
            'compression_threshold': -20.0,
            'compression_ratio': 4.0,
            'compression_attack': 5.0,
            'compression_release': 50.0,
            'trim_silence': True,
            'silence_threshold': -40,
            'min_silence_len': 1000,
            'keep_silence': 100,
            'segment_long_audio': False,
            'noise_sample_duration': 1.0
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing"""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_file}: {e}")
        self._temp_files.clear()
    
    def export_processing_report(self, results: Dict[str, Any], output_path: str):
        """
        Export detailed processing report
        
        Args:
            results: Processing results dictionary
            output_path: Path to save report
        """
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'original_file': results.get('original_path', ''),
            'enhanced_file': results.get('enhanced_path', ''),
            'processing_time': results.get('processing_time', 0),
            'enhancements_applied': results.get('enhancements_applied', []),
            'quality_metrics': {
                'before': self._metrics_to_dict(results.get('quality_metrics')),
                'after': self._metrics_to_dict(results.get('quality_after'))
            },
            'segments': len(results.get('segments', [])),
            'bookmarks': len(results.get('bookmarks', [])),
            'chapters': len(results.get('chapters', []))
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def _metrics_to_dict(self, metrics: Optional[AudioQualityMetrics]) -> Dict[str, Any]:
        """Convert AudioQualityMetrics to dictionary"""
        if not metrics:
            return {}
        
        return {
            'quality_score': metrics.quality_score,
            'snr_db': metrics.snr_db,
            'dynamic_range_db': metrics.dynamic_range_db,
            'spectral_centroid': metrics.spectral_centroid,
            'zero_crossing_rate': metrics.zero_crossing_rate,
            'rms_energy': metrics.rms_energy,
            'spectral_rolloff': metrics.spectral_rolloff,
            'recommendations': metrics.recommendations
        }

# Convenience functions for easy integration
def create_audio_processing_integration():
    """Create and return an AudioProcessingIntegration instance"""
    return AudioProcessingIntegration()

def enhance_audio_auto(audio_path: str) -> str:
    """
    Automatically enhance audio with intelligent settings
    
    Args:
        audio_path: Path to input audio
        
    Returns:
        Path to enhanced audio
    """
    integration = AudioProcessingIntegration()
    result = integration.enhance_for_transcription(audio_path)
    return result.get('enhanced_path', audio_path)