#!/usr/bin/env python3
"""
Enhanced Audio Processing Module
Provides advanced audio processing capabilities including normalization, 
segmentation, and quality enhancement
"""

import os
import logging
from typing import List, Tuple, Optional
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import tempfile

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Enhanced audio processing with quality improvements"""
    
    def __init__(self):
        self.temp_files = []
    
    def normalize_volume(self, audio_path: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume to consistent levels
        
        Args:
            audio_path: Path to input audio file
            target_dBFS: Target volume level in dBFS
            
        Returns:
            Path to normalized audio file
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Normalize volume
            normalized_audio = normalize(audio)
            
            # Adjust to target level
            change_in_dBFS = target_dBFS - normalized_audio.dBFS
            normalized_audio = normalized_audio.apply_gain(change_in_dBFS)
            
            # Save normalized audio
            output_path = self._create_temp_file("_normalized.wav")
            normalized_audio.export(output_path, format="wav")
            
            logger.info(f"Audio normalized: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Volume normalization failed: {e}")
            return audio_path  # Return original if processing fails
    
    def compress_dynamic_range(self, audio_path: str, threshold: float = -20.0, 
                             ratio: float = 4.0, attack: float = 5.0, release: float = 50.0) -> str:
        """
        Apply dynamic range compression for consistent audio levels
        
        Args:
            audio_path: Path to input audio file
            threshold: Compression threshold in dBFS
            ratio: Compression ratio
            attack: Attack time in ms
            release: Release time in ms
            
        Returns:
            Path to compressed audio file
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Apply compression
            compressed_audio = compress_dynamic_range(
                audio, 
                threshold=threshold,
                ratio=ratio,
                attack=attack,
                release=release
            )
            
            # Save compressed audio
            output_path = self._create_temp_file("_compressed.wav")
            compressed_audio.export(output_path, format="wav")
            
            logger.info(f"Dynamic range compressed: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Dynamic range compression failed: {e}")
            return audio_path
    
    def segment_audio(self, audio_path: str, segment_length_ms: int = 300000, 
                     overlap_ms: int = 5000) -> List[str]:
        """
        Segment long audio files into manageable chunks
        
        Args:
            audio_path: Path to input audio file
            segment_length_ms: Length of each segment in milliseconds (default: 5 minutes)
            overlap_ms: Overlap between segments in milliseconds
            
        Returns:
            List of paths to audio segments
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Calculate segments
            segments = []
            start = 0
            segment_num = 0
            
            while start < len(audio):
                end = min(start + segment_length_ms, len(audio))
                
                # Extract segment
                segment = audio[start:end]
                
                # Save segment
                segment_path = self._create_temp_file(f"_segment_{segment_num:03d}.wav")
                segment.export(segment_path, format="wav")
                segments.append(segment_path)
                
                # Move to next segment with overlap
                start = end - overlap_ms
                segment_num += 1
                
                # Prevent infinite loop
                if start >= end:
                    break
            
            logger.info(f"Audio segmented into {len(segments)} parts: {audio_path}")
            return segments
            
        except Exception as e:
            logger.error(f"Audio segmentation failed: {e}")
            return [audio_path]  # Return original if segmentation fails
    
    def enhance_speech(self, audio_path: str) -> str:
        """
        Apply speech enhancement techniques
        
        Args:
            audio_path: Path to input audio file
            
        Returns:
            Path to enhanced audio file
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Apply enhancements
            enhanced_audio = audio
            
            # High-pass filter to remove low-frequency noise
            enhanced_audio = enhanced_audio.high_pass_filter(80)
            
            # Low-pass filter to remove high-frequency noise
            enhanced_audio = enhanced_audio.low_pass_filter(8000)
            
            # Normalize
            enhanced_audio = normalize(enhanced_audio)
            
            # Save enhanced audio
            output_path = self._create_temp_file("_enhanced.wav")
            enhanced_audio.export(output_path, format="wav")
            
            logger.info(f"Speech enhanced: {audio_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Speech enhancement failed: {e}")
            return audio_path
    
    def get_audio_info(self, audio_path: str) -> dict:
        """
        Get detailed audio information
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            return {
                'duration_ms': len(audio),
                'duration_seconds': len(audio) / 1000.0,
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'frame_count': audio.frame_count(),
                'dBFS': audio.dBFS,
                'max_dBFS': audio.max_dBFS,
                'rms': audio.rms
            }
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {}
    
    def detect_silence(self, audio_path: str, silence_thresh: int = -40, 
                      min_silence_len: int = 1000) -> List[Tuple[int, int]]:
        """
        Detect silent segments in audio
        
        Args:
            audio_path: Path to audio file
            silence_thresh: Silence threshold in dBFS
            min_silence_len: Minimum silence length in ms
            
        Returns:
            List of (start, end) tuples for silent segments
        """
        try:
            from pydub.silence import detect_silence
            
            audio = AudioSegment.from_file(audio_path)
            
            silent_segments = detect_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh
            )
            
            logger.info(f"Detected {len(silent_segments)} silent segments")
            return silent_segments
            
        except Exception as e:
            logger.error(f"Silence detection failed: {e}")
            return []
    
    def _create_temp_file(self, suffix: str) -> str:
        """Create temporary file and track for cleanup"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        self.temp_files.append(temp_file.name)
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

def process_audio_for_transcription(audio_path: str, enhance_quality: bool = True) -> str:
    """
    Process audio file for optimal transcription quality
    
    Args:
        audio_path: Path to input audio file
        enhance_quality: Whether to apply quality enhancements
        
    Returns:
        Path to processed audio file
    """
    processor = AudioProcessor()
    
    try:
        processed_path = audio_path
        
        if enhance_quality:
            # Apply enhancements in sequence
            processed_path = processor.enhance_speech(processed_path)
            processed_path = processor.normalize_volume(processed_path)
            processed_path = processor.compress_dynamic_range(processed_path)
        
        logger.info(f"Audio processing complete: {audio_path} -> {processed_path}")
        return processed_path
        
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        return audio_path  # Return original if processing fails

def get_audio_statistics(audio_path: str) -> dict:
    """
    Get comprehensive audio statistics
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dictionary with audio statistics
    """
    processor = AudioProcessor()
    
    try:
        info = processor.get_audio_info(audio_path)
        silent_segments = processor.detect_silence(audio_path)
        
        # Calculate additional statistics
        total_silence_ms = sum(end - start for start, end in silent_segments)
        speech_ratio = 1.0 - (total_silence_ms / info.get('duration_ms', 1))
        
        stats = {
            **info,
            'silent_segments': len(silent_segments),
            'total_silence_ms': total_silence_ms,
            'speech_ratio': speech_ratio,
            'estimated_words': int(info.get('duration_seconds', 0) * 2.5 * speech_ratio)  # ~150 WPM
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get audio statistics: {e}")
        return {}