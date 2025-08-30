"""
Whisper Advanced Audio Preprocessor

This module implements the AudioPreprocessor class for the Whisper Advanced Integration
system, providing comprehensive audio enhancement, quality assessment, and format
optimization specifically designed for optimal Whisper transcription performance.

Requirements addressed:
- 2.1: Intelligent audio preprocessing and voice activity detection
- 2.2: Automatic noise reduction and audio enhancement preprocessing
- 2.5: Audio quality assessment with detailed metrics
- 7.3: Audio format conversion and resampling for standardized input processing
"""

import os
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import time
import warnings
from enum import Enum
import json
import hashlib

# Import existing audio enhancement pipeline
from audio_enhancement_pipeline import AudioEnhancementPipeline, AudioQualityMetrics, EnhancementResult

# Import custom exceptions
from whisper_advanced_exceptions import (
    AudioFileError, ProcessingError, ResourceError, 
    InsufficientMemoryError, ValidationError
)

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioFormat(Enum):
    """Supported audio formats for Whisper processing"""
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"
    AAC = "aac"
    WEBM = "webm"

class ProcessingMode(Enum):
    """Audio processing modes for different quality/speed trade-offs"""
    FAST = "fast"           # Minimal processing for speed
    BALANCED = "balanced"   # Balanced processing for general use
    QUALITY = "quality"     # Maximum quality processing
    CUSTOM = "custom"       # Custom processing parameters

@dataclass
class AudioConfig:
    """Configuration for audio preprocessing"""
    # Target audio parameters for Whisper
    target_sample_rate: int = 16000  # Whisper's preferred sample rate
    target_channels: int = 1         # Mono for Whisper
    target_bit_depth: int = 16       # 16-bit for efficiency
    
    # Processing options
    enable_noise_reduction: bool = True
    enable_normalization: bool = True
    enable_enhancement: bool = True
    enable_repair: bool = True
    
    # Quality thresholds
    min_snr_db: float = 10.0        # Minimum acceptable SNR
    min_quality_score: float = 50.0  # Minimum quality score
    max_duration_seconds: float = 1800.0  # 30 minutes max
    
    # Processing mode
    processing_mode: ProcessingMode = ProcessingMode.BALANCED
    
    # Custom parameters (used when processing_mode is CUSTOM)
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AudioPreprocessingResult:
    """Result of audio preprocessing operation"""
    processed_audio_path: str
    original_path: str
    original_format: str
    processed_format: str
    original_metrics: AudioQualityMetrics
    processed_metrics: AudioQualityMetrics
    processing_time: float
    operations_applied: List[str]
    quality_improvement: float
    whisper_optimized: bool
    recommendations: List[str]
    metadata: Dict[str, Any]

class AudioPreprocessor:
    """
    Advanced audio preprocessor optimized for Whisper transcription
    
    This class provides comprehensive audio preprocessing capabilities including:
    - Format conversion and standardization
    - Quality assessment and optimization
    - Noise reduction and enhancement
    - Audio repair and normalization
    - Whisper-specific optimizations
    """
    
    def __init__(self, temp_dir: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the audio preprocessor
        
        Args:
            temp_dir: Directory for temporary files
            cache_dir: Directory for caching processed files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.cache_dir = cache_dir or os.path.join(self.temp_dir, "whisper_audio_cache")
        
        # Create directories
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize enhancement pipeline
        self.enhancement_pipeline = AudioEnhancementPipeline(temp_dir=self.temp_dir)
        
        # Supported formats
        self.supported_input_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.webm']
        self.whisper_optimal_formats = ['.wav', '.flac']
        
        # Processing statistics
        self.processing_stats = {
            'total_files_processed': 0,
            'total_processing_time': 0.0,
            'average_quality_improvement': 0.0,
            'format_conversions': {},
            'common_issues_fixed': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Whisper-specific optimization parameters
        self.whisper_optimization = {
            'preferred_sample_rate': 16000,
            'preferred_channels': 1,
            'preferred_bit_depth': 16,
            'max_frequency': 8000,  # Whisper's effective frequency range
            'optimal_snr_db': 20.0,
            'optimal_dynamic_range_db': 30.0
        }
        
        logger.info("AudioPreprocessor initialized for Whisper Advanced Integration")
    
    def preprocess_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        config: Optional[AudioConfig] = None
    ) -> AudioPreprocessingResult:
        """
        Preprocess audio file for optimal Whisper transcription
        
        Args:
            input_path: Path to input audio file
            output_path: Path for processed output (optional)
            config: Audio processing configuration
            
        Returns:
            AudioPreprocessingResult with detailed processing information
        """
        start_time = time.time()
        
        if config is None:
            config = AudioConfig()
        
        # Validate input file
        self._validate_input_file(input_path)
        
        # Generate output path if not provided
        if output_path is None:
            input_path_obj = Path(input_path)
            output_path = os.path.join(
                self.temp_dir,
                f"{input_path_obj.stem}_whisper_optimized.wav"
            )
        
        # Check cache
        cache_key = self._generate_cache_key(input_path, config)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            self.processing_stats['cache_hits'] += 1
            logger.info(f"Using cached preprocessing result for {input_path}")
            return cached_result
        
        self.processing_stats['cache_misses'] += 1
        
        logger.info(f"Starting audio preprocessing: {input_path}")
        
        try:
            # Load and analyze original audio
            original_audio, original_sr = self._load_audio_safely(input_path)
            original_format = Path(input_path).suffix.lower().lstrip('.')
            
            # Assess original quality
            original_metrics = self._assess_audio_quality(original_audio, original_sr)
            logger.info(f"Original audio quality: {original_metrics.quality_score:.1f}/100")
            
            # Determine processing pipeline based on config and quality
            processing_pipeline = self._determine_processing_pipeline(original_metrics, config)
            
            # Apply preprocessing pipeline
            processed_audio, processed_sr, operations_applied = self._apply_preprocessing_pipeline(
                original_audio, original_sr, processing_pipeline, config
            )
            
            # Optimize for Whisper
            whisper_optimized_audio, whisper_sr = self._optimize_for_whisper(
                processed_audio, processed_sr, config
            )
            operations_applied.append("whisper_optimization")
            
            # Save processed audio
            self._save_audio_safely(whisper_optimized_audio, whisper_sr, output_path)
            
            # Assess processed quality
            processed_metrics = self._assess_audio_quality(whisper_optimized_audio, whisper_sr)
            
            # Calculate improvement
            quality_improvement = processed_metrics.quality_score - original_metrics.quality_score
            
            # Generate recommendations
            recommendations = self._generate_whisper_recommendations(processed_metrics)
            
            # Create result
            result = AudioPreprocessingResult(
                processed_audio_path=output_path,
                original_path=input_path,
                original_format=original_format,
                processed_format="wav",
                original_metrics=original_metrics,
                processed_metrics=processed_metrics,
                processing_time=time.time() - start_time,
                operations_applied=operations_applied,
                quality_improvement=quality_improvement,
                whisper_optimized=True,
                recommendations=recommendations,
                metadata={
                    'original_sample_rate': original_sr,
                    'processed_sample_rate': whisper_sr,
                    'original_channels': original_audio.shape[0] if original_audio.ndim > 1 else 1,
                    'processed_channels': 1,
                    'duration_seconds': len(whisper_optimized_audio) / whisper_sr,
                    'processing_mode': config.processing_mode.value,
                    'cache_key': cache_key
                }
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Update statistics
            self._update_processing_stats(result)
            
            logger.info(f"Audio preprocessing completed in {result.processing_time:.2f}s")
            logger.info(f"Quality improvement: {quality_improvement:+.1f} points")
            
            return result
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {str(e)}")
            raise ProcessingError(
                message=f"Failed to preprocess audio: {str(e)}",
                processing_stage="audio_preprocessing",
                audio_duration=0.0,
                original_exception=e
            )    
  
  def assess_quality(self, audio_path: str) -> AudioQualityMetrics:
        """
        Assess audio quality without processing
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            AudioQualityMetrics with detailed quality assessment
        """
        try:
            self._validate_input_file(audio_path)
            audio_data, sample_rate = self._load_audio_safely(audio_path)
            return self._assess_audio_quality(audio_data, sample_rate)
            
        except Exception as e:
            raise ProcessingError(
                message=f"Failed to assess audio quality: {str(e)}",
                processing_stage="quality_assessment",
                original_exception=e
            )
    
    def optimize_for_whisper(
        self,
        input_path: str,
        output_path: Optional[str] = None
    ) -> AudioPreprocessingResult:
        """
        Quick optimization specifically for Whisper without full preprocessing
        
        Args:
            input_path: Path to input audio file
            output_path: Path for optimized output
            
        Returns:
            AudioPreprocessingResult with Whisper optimization details
        """
        config = AudioConfig(
            processing_mode=ProcessingMode.FAST,
            enable_noise_reduction=False,
            enable_enhancement=False,
            enable_repair=False,
            enable_normalization=True
        )
        
        return self.preprocess_audio(input_path, output_path, config)
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        stats = self.processing_stats.copy()
        
        # Calculate derived metrics
        if stats['total_files_processed'] > 0:
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_files_processed']
            stats['cache_hit_rate'] = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
        else:
            stats['average_processing_time'] = 0.0
            stats['cache_hit_rate'] = 0.0
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear preprocessing cache"""
        try:
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
            logger.info("Preprocessing cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")
    
    # Private methods
    def _validate_input_file(self, file_path: str) -> None:
        """Validate input audio file"""
        if not os.path.exists(file_path):
            raise AudioFileError(
                message=f"Audio file not found: {file_path}",
                file_path=file_path,
                error_code="FILE_NOT_FOUND"
            )
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_input_formats:
            raise AudioFileError(
                message=f"Unsupported audio format: {file_ext}",
                file_path=file_path,
                file_format=file_ext.lstrip('.'),
                error_code="UNSUPPORTED_FORMAT"
            )
        
        # Check file size (max 100MB)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 100:
            raise AudioFileError(
                message=f"File size too large: {file_size_mb:.1f}MB (max 100MB)",
                file_path=file_path,
                file_size_mb=file_size_mb,
                error_code="FILE_TOO_LARGE"
            )
    
    def _load_audio_safely(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Safely load audio file with error handling"""
        try:
            audio_data, sample_rate = librosa.load(file_path, sr=None, mono=False)
            
            # Ensure audio is 2D (channels, samples)
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(1, -1)
            
            # Check duration
            duration = audio_data.shape[1] / sample_rate
            if duration > 1800:  # 30 minutes
                raise AudioFileError(
                    message=f"Audio duration too long: {duration:.1f}s (max 1800s)",
                    file_path=file_path,
                    error_code="DURATION_TOO_LONG"
                )
            
            return audio_data, sample_rate
            
        except Exception as e:
            if isinstance(e, AudioFileError):
                raise
            raise AudioFileError(
                message=f"Failed to load audio file: {str(e)}",
                file_path=file_path,
                error_code="LOAD_FAILED",
                original_exception=e
            )
    
    def _save_audio_safely(self, audio_data: np.ndarray, sample_rate: int, output_path: str) -> None:
        """Safely save audio file with error handling"""
        try:
            # Ensure audio is in correct format for saving
            if audio_data.ndim > 1 and audio_data.shape[0] == 1:
                audio_data = audio_data[0]  # Convert to 1D for mono
            
            # Ensure no clipping
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data)) * 0.99
            
            sf.write(output_path, audio_data, sample_rate, subtype='PCM_16')
            
        except Exception as e:
            raise ProcessingError(
                message=f"Failed to save processed audio: {str(e)}",
                processing_stage="audio_saving",
                original_exception=e
            )
    
    def _assess_audio_quality(self, audio_data: np.ndarray, sample_rate: int) -> AudioQualityMetrics:
        """Assess audio quality using the enhancement pipeline"""
        try:
            return self.enhancement_pipeline._assess_audio_quality(audio_data, sample_rate)
        except Exception as e:
            logger.warning(f"Quality assessment failed: {str(e)}")
            # Return default metrics
            return AudioQualityMetrics(
                snr_db=20.0, thd_percent=1.0, dynamic_range_db=20.0,
                spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
                rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
                quality_score=50.0, recommendations=["Quality assessment failed"]
            )
    
    def _determine_processing_pipeline(
        self, 
        metrics: AudioQualityMetrics, 
        config: AudioConfig
    ) -> Dict[str, bool]:
        """Determine which processing steps to apply based on quality and config"""
        pipeline = {
            'noise_reduction': config.enable_noise_reduction and metrics.snr_db < 20.0,
            'enhancement': config.enable_enhancement and metrics.quality_score < 70.0,
            'repair': config.enable_repair and (metrics.thd_percent > 2.0 or metrics.peak_level_db > -1.0),
            'normalization': config.enable_normalization,
            'format_conversion': True  # Always convert for Whisper
        }
        
        # Adjust based on processing mode
        if config.processing_mode == ProcessingMode.FAST:
            pipeline['noise_reduction'] = False
            pipeline['enhancement'] = False
            pipeline['repair'] = False
        elif config.processing_mode == ProcessingMode.QUALITY:
            pipeline['noise_reduction'] = config.enable_noise_reduction
            pipeline['enhancement'] = config.enable_enhancement
            pipeline['repair'] = config.enable_repair
        
        return pipeline
    
    def _apply_preprocessing_pipeline(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        pipeline: Dict[str, bool],
        config: AudioConfig
    ) -> Tuple[np.ndarray, int, List[str]]:
        """Apply the determined preprocessing pipeline"""
        processed_audio = audio_data.copy()
        operations_applied = []
        
        try:
            # Apply enhancement if needed
            if pipeline.get('noise_reduction') or pipeline.get('enhancement') or pipeline.get('repair'):
                # Create temporary file for enhancement pipeline
                temp_input = os.path.join(self.temp_dir, "temp_input.wav")
                temp_output = os.path.join(self.temp_dir, "temp_enhanced.wav")
                
                # Save current audio
                if processed_audio.shape[0] == 1:
                    sf.write(temp_input, processed_audio[0], sample_rate)
                else:
                    sf.write(temp_input, processed_audio.T, sample_rate)
                
                # Apply enhancement
                enhancement_options = {
                    'noise_reduction': pipeline.get('noise_reduction', False),
                    'spectral_enhancement': pipeline.get('enhancement', False),
                    'audio_repair': pipeline.get('repair', False),
                    'normalization': False  # We'll handle this separately
                }
                
                enhancement_result = self.enhancement_pipeline.enhance_audio(
                    temp_input, temp_output, enhancement_options
                )
                
                # Load enhanced audio
                enhanced_audio, enhanced_sr = librosa.load(temp_output, sr=None, mono=False)
                if enhanced_audio.ndim == 1:
                    enhanced_audio = enhanced_audio.reshape(1, -1)
                
                processed_audio = enhanced_audio
                sample_rate = enhanced_sr
                operations_applied.extend(enhancement_result.enhancement_applied)
                
                # Clean up temp files
                for temp_file in [temp_input, temp_output]:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
            
            # Apply normalization if needed
            if pipeline.get('normalization'):
                processed_audio = self._apply_whisper_normalization(processed_audio, sample_rate)
                operations_applied.append("normalization")
            
            return processed_audio, sample_rate, operations_applied
            
        except Exception as e:
            logger.error(f"Preprocessing pipeline failed: {str(e)}")
            # Return original audio if processing fails
            return audio_data, sample_rate, ["preprocessing_failed"]
    
    def _optimize_for_whisper(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        config: AudioConfig
    ) -> Tuple[np.ndarray, int]:
        """Apply Whisper-specific optimizations"""
        optimized_audio = audio_data.copy()
        target_sr = config.target_sample_rate
        
        # Convert to mono if needed
        if optimized_audio.shape[0] > 1:
            optimized_audio = np.mean(optimized_audio, axis=0, keepdims=True)
        
        # Resample to target sample rate
        if sample_rate != target_sr:
            optimized_audio = librosa.resample(
                optimized_audio[0], 
                orig_sr=sample_rate, 
                target_sr=target_sr
            ).reshape(1, -1)
        
        # Apply low-pass filter at Whisper's effective frequency range
        if target_sr > 16000:
            nyquist = target_sr / 2
            cutoff = min(8000, nyquist * 0.95)
            from scipy import signal
            b, a = signal.butter(4, cutoff / nyquist, btype='low')
            optimized_audio[0] = signal.filtfilt(b, a, optimized_audio[0])
        
        return optimized_audio, target_sr
    
    def _apply_whisper_normalization(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply Whisper-optimized normalization"""
        normalized_channels = []
        
        for channel_idx in range(audio_data.shape[0]):
            channel_data = audio_data[channel_idx]
            
            # Calculate RMS level
            rms_level = np.sqrt(np.mean(channel_data**2))
            
            # Target RMS level for Whisper (around -20dB)
            target_rms = 0.1  # Linear equivalent of -20dB
            
            if rms_level > 0:
                gain = target_rms / rms_level
                
                # Limit gain to prevent excessive amplification
                max_gain = 10.0  # 20dB max gain
                gain = min(gain, max_gain)
                
                normalized_channel = channel_data * gain
                
                # Ensure no clipping
                peak_level = np.max(np.abs(normalized_channel))
                if peak_level > 0.99:
                    normalized_channel *= 0.99 / peak_level
                
                normalized_channels.append(normalized_channel)
            else:
                normalized_channels.append(channel_data)
        
        return np.array(normalized_channels)
    
    def _generate_whisper_recommendations(self, metrics: AudioQualityMetrics) -> List[str]:
        """Generate Whisper-specific recommendations based on quality metrics"""
        recommendations = []
        
        if metrics.snr_db < 15.0:
            recommendations.append("Consider using noise reduction for better transcription accuracy")
        
        if metrics.quality_score < 60.0:
            recommendations.append("Audio quality is below optimal - consider audio enhancement")
        
        if metrics.dynamic_range_db < 10.0:
            recommendations.append("Low dynamic range detected - audio may be over-compressed")
        
        if metrics.peak_level_db > -3.0:
            recommendations.append("Audio levels are high - normalization recommended")
        
        if metrics.spectral_centroid < 1000 or metrics.spectral_centroid > 4000:
            recommendations.append("Spectral characteristics may affect transcription quality")
        
        if not recommendations:
            recommendations.append("Audio is well-optimized for Whisper transcription")
        
        return recommendations
    
    def _generate_cache_key(self, file_path: str, config: AudioConfig) -> str:
        """Generate cache key for file and configuration"""
        # Include file modification time and size
        stat = os.stat(file_path)
        file_info = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
        
        # Include relevant config parameters
        config_str = f"{config.processing_mode.value}_{config.target_sample_rate}_{config.enable_noise_reduction}_{config.enable_enhancement}"
        
        # Create hash
        cache_key = hashlib.md5(f"{file_info}_{config_str}".encode()).hexdigest()
        return cache_key
    
    def _check_cache(self, cache_key: str) -> Optional[AudioPreprocessingResult]:
        """Check if result is cached"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if processed file still exists
                if os.path.exists(cached_data['processed_audio_path']):
                    # Reconstruct result object (simplified)
                    return AudioPreprocessingResult(
                        processed_audio_path=cached_data['processed_audio_path'],
                        original_path=cached_data['original_path'],
                        original_format=cached_data['original_format'],
                        processed_format=cached_data['processed_format'],
                        original_metrics=AudioQualityMetrics(**cached_data['original_metrics']),
                        processed_metrics=AudioQualityMetrics(**cached_data['processed_metrics']),
                        processing_time=cached_data['processing_time'],
                        operations_applied=cached_data['operations_applied'],
                        quality_improvement=cached_data['quality_improvement'],
                        whisper_optimized=cached_data['whisper_optimized'],
                        recommendations=cached_data['recommendations'],
                        metadata=cached_data['metadata']
                    )
            except Exception as e:
                logger.warning(f"Failed to load cached result: {str(e)}")
        
        return None
    
    def _cache_result(self, cache_key: str, result: AudioPreprocessingResult) -> None:
        """Cache processing result"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            # Convert result to serializable format
            cache_data = {
                'processed_audio_path': result.processed_audio_path,
                'original_path': result.original_path,
                'original_format': result.original_format,
                'processed_format': result.processed_format,
                'original_metrics': result.original_metrics.__dict__,
                'processed_metrics': result.processed_metrics.__dict__,
                'processing_time': result.processing_time,
                'operations_applied': result.operations_applied,
                'quality_improvement': result.quality_improvement,
                'whisper_optimized': result.whisper_optimized,
                'recommendations': result.recommendations,
                'metadata': result.metadata
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to cache result: {str(e)}")
    
    def _update_processing_stats(self, result: AudioPreprocessingResult) -> None:
        """Update processing statistics"""
        self.processing_stats['total_files_processed'] += 1
        self.processing_stats['total_processing_time'] += result.processing_time
        
        # Update average quality improvement
        total_improvement = (
            self.processing_stats['average_quality_improvement'] * 
            (self.processing_stats['total_files_processed'] - 1) + 
            result.quality_improvement
        )
        self.processing_stats['average_quality_improvement'] = total_improvement / self.processing_stats['total_files_processed']
        
        # Update format conversion stats
        format_key = f"{result.original_format}_to_{result.processed_format}"
        self.processing_stats['format_conversions'][format_key] = \
            self.processing_stats['format_conversions'].get(format_key, 0) + 1
        
        # Update common issues fixed
        for operation in result.operations_applied:
            self.processing_stats['common_issues_fixed'][operation] = \
                self.processing_stats['common_issues_fixed'].get(operation, 0) + 1

# Utility functions for common preprocessing tasks
def create_fast_config() -> AudioConfig:
    """Create configuration for fast preprocessing"""
    return AudioConfig(
        processing_mode=ProcessingMode.FAST,
        enable_noise_reduction=False,
        enable_enhancement=False,
        enable_repair=False,
        enable_normalization=True
    )

def create_quality_config() -> AudioConfig:
    """Create configuration for high-quality preprocessing"""
    return AudioConfig(
        processing_mode=ProcessingMode.QUALITY,
        enable_noise_reduction=True,
        enable_enhancement=True,
        enable_repair=True,
        enable_normalization=True,
        min_snr_db=15.0,
        min_quality_score=70.0
    )

def create_balanced_config() -> AudioConfig:
    """Create configuration for balanced preprocessing"""
    return AudioConfig(
        processing_mode=ProcessingMode.BALANCED,
        enable_noise_reduction=True,
        enable_enhancement=True,
        enable_repair=False,
        enable_normalization=True
    )

# Example usage
if __name__ == "__main__":
    # Example usage of the AudioPreprocessor
    try:
        # Initialize preprocessor
        preprocessor = AudioPreprocessor()
        
        # Example configuration
        config = create_balanced_config()
        
        print(f"AudioPreprocessor initialized")
        print(f"Supported formats: {preprocessor.supported_input_formats}")
        print(f"Whisper optimization parameters: {preprocessor.whisper_optimization}")
        
        # Get processing statistics
        stats = preprocessor.get_processing_statistics()
        print(f"Processing statistics: {stats}")
        
        print("AudioPreprocessor example completed successfully!")
        
    except Exception as e:
        print(f"Example failed: {str(e)}")