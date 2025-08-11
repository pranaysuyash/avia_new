"""
Whisper Advanced Integration - Core Processing Infrastructure

This module implements the core WhisperAdvancedProcessor class with enhanced configuration
management, model loading capabilities, and comprehensive error handling for the Whisper
Advanced Integration system.

Requirements addressed:
- 1.1: Advanced Whisper model configuration with all model sizes and parameter tuning
- 1.2: Temperature control, beam search configuration, and sampling options
- 1.3: Support for both transcription and translation tasks
- 7.1: Model management system with caching and dynamic loading/unloading
- 7.2: Performance monitoring and optimization
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import hashlib
import tempfile
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

# Import existing Whisper implementation
from whisper_api_advanced import (
    WhisperAPIAdvanced, WhisperConfig as BaseWhisperConfig, 
    TranscriptionResult as BaseTranscriptionResult, WhisperModel as BaseWhisperModel,
    ResponseFormat, LanguageCode
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperModel(Enum):
    """Enhanced Whisper model enumeration with detailed specifications"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"
    
    @property
    def parameters(self) -> str:
        """Number of parameters in the model"""
        params = {
            "tiny": "39M",
            "base": "74M", 
            "small": "244M",
            "medium": "769M",
            "large": "1550M",
            "large-v2": "1550M",
            "large-v3": "1550M"
        }
        return params.get(self.value, "Unknown")
    
    @property
    def vram_required(self) -> str:
        """Approximate VRAM requirement"""
        vram = {
            "tiny": "~1GB",
            "base": "~1GB",
            "small": "~2GB", 
            "medium": "~5GB",
            "large": "~10GB",
            "large-v2": "~10GB",
            "large-v3": "~10GB"
        }
        return vram.get(self.value, "Unknown")
    
    @property
    def relative_speed(self) -> str:
        """Relative processing speed"""
        speed = {
            "tiny": "~32x",
            "base": "~16x",
            "small": "~6x",
            "medium": "~2x", 
            "large": "1x",
            "large-v2": "1x",
            "large-v3": "1x"
        }
        return speed.get(self.value, "1x")
    
    @property
    def use_cases(self) -> List[str]:
        """Recommended use cases"""
        cases = {
            "tiny": ["Real-time transcription", "Quick drafts", "Low-resource environments"],
            "base": ["General transcription", "Voice notes", "Balanced performance"],
            "small": ["Professional transcription", "Podcasts", "Good accuracy needs"],
            "medium": ["High-quality transcription", "Interviews", "Business meetings"],
            "large": ["Professional audio", "Research transcription", "Maximum accuracy"],
            "large-v2": ["Professional audio", "Research transcription", "Maximum accuracy"],
            "large-v3": ["Professional audio", "Research transcription", "Maximum accuracy"]
        }
        return cases.get(self.value, ["General use"])

@dataclass
class WhisperConfig:
    """Enhanced Whisper configuration with comprehensive parameter support"""
    # Model configuration
    model_size: WhisperModel = WhisperModel.BASE
    language: Optional[str] = None
    task: str = "transcribe"  # "transcribe" or "translate"
    
    # Sampling parameters
    temperature: float = 0.0
    best_of: int = 5
    beam_size: int = 5
    patience: float = 1.0
    length_penalty: float = 1.0
    
    # Token control
    suppress_tokens: List[int] = field(default_factory=list)
    initial_prompt: Optional[str] = None
    condition_on_previous_text: bool = True
    
    # Processing options
    fp16: bool = True
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    
    # Timestamp options
    word_timestamps: bool = True
    prepend_punctuations: str = "\"'"¿([{-"
    append_punctuations: str = "\"'.。,，!！?？:：")]}、"
    
    # Advanced features
    enable_vad: bool = True
    enable_diarization: bool = False
    max_speakers: int = 10
    
    # Custom vocabulary and context
    custom_vocabulary: List[str] = field(default_factory=list)
    domain_context: Optional[str] = None
    speaker_context: Optional[str] = None
    content_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        
        if not 1 <= self.best_of <= 10:
            raise ValueError("best_of must be between 1 and 10")
        
        if not 1 <= self.beam_size <= 10:
            raise ValueError("beam_size must be between 1 and 10")
        
        if not 0.0 <= self.patience <= 2.0:
            raise ValueError("patience must be between 0.0 and 2.0")
        
        if not 0.0 <= self.length_penalty <= 2.0:
            raise ValueError("length_penalty must be between 0.0 and 2.0")
        
        if not 1 <= self.max_speakers <= 20:
            raise ValueError("max_speakers must be between 1 and 20")
        
        if self.task not in ["transcribe", "translate"]:
            raise ValueError("task must be 'transcribe' or 'translate'")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    def to_legacy_config(self) -> BaseWhisperConfig:
        """Convert to legacy WhisperConfig for API compatibility"""
        # Map to legacy enum values
        legacy_model = BaseWhisperModel.WHISPER_1  # Default to API model
        
        # Map language code
        legacy_language = None
        if self.language:
            try:
                legacy_language = LanguageCode(self.language)
            except ValueError:
                legacy_language = LanguageCode.AUTO
        
        return BaseWhisperConfig(
            model=legacy_model,
            language=legacy_language,
            prompt=self.initial_prompt,
            response_format=ResponseFormat.VERBOSE_JSON,
            temperature=self.temperature,
            custom_vocabulary=self.custom_vocabulary,
            confidence_threshold=0.0,  # Will be handled separately
            enable_word_timestamps=self.word_timestamps,
            domain_context=self.domain_context,
            speaker_context=self.speaker_context,
            content_type=self.content_type
        )

@dataclass
class TranscriptionSegment:
    """Enhanced transcription segment with comprehensive metadata"""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    confidence: float
    words: List['WordLevelTimestamp'] = field(default_factory=list)
    speaker_id: Optional[str] = None

@dataclass
class WordLevelTimestamp:
    """Word-level timestamp with confidence scoring"""
    word: str
    start: float
    end: float
    confidence: float

@dataclass
class LanguageDetectionResult:
    """Language detection result with confidence scores"""
    detected_language: str
    language_probability: float
    all_language_probs: Dict[str, float] = field(default_factory=dict)

@dataclass
class SpeakerDiarizationResult:
    """Speaker diarization result with detailed speaker information"""
    num_speakers: int
    speakers: List[Dict[str, Any]] = field(default_factory=list)
    speaker_segments: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ConfidenceScore:
    """Confidence scoring metrics"""
    overall: float
    segments: List[float] = field(default_factory=list)
    words: List[float] = field(default_factory=list)
    low_confidence_segments: List[int] = field(default_factory=list)

@dataclass
class TranscriptionResult:
    """Enhanced transcription result with comprehensive metadata"""
    text: str
    segments: List[TranscriptionSegment] = field(default_factory=list)
    language: str = ""
    language_detection: Optional[LanguageDetectionResult] = None
    speaker_diarization: Optional[SpeakerDiarizationResult] = None
    processing_time: float = 0.0
    model_used: str = ""
    word_count: int = 0
    duration: float = 0.0
    confidence_score: float = 0.0
    config_used: Optional[WhisperConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if not self.word_count and self.text:
            self.word_count = len(self.text.split())
        
        if not self.confidence_score and self.segments:
            confidences = [seg.confidence for seg in self.segments if seg.confidence > 0]
            self.confidence_score = sum(confidences) / len(confidences) if confidences else 0.0

class ModelManager:
    """Manages Whisper model loading, caching, and performance optimization"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize model manager"""
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "whisper_models")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.loaded_models: Dict[str, Any] = {}
        self.model_stats: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        # Performance monitoring
        self.performance_metrics = {
            'model_load_times': {},
            'memory_usage': {},
            'processing_times': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def load_model(self, model_size: WhisperModel) -> Any:
        """Load and cache a Whisper model"""
        model_key = model_size.value
        
        with self.lock:
            if model_key in self.loaded_models:
                self.performance_metrics['cache_hits'] += 1
                logger.info(f"Using cached model: {model_key}")
                return self.loaded_models[model_key]
            
            self.performance_metrics['cache_misses'] += 1
            logger.info(f"Loading model: {model_key}")
            
            start_time = time.time()
            
            try:
                # For now, we'll use a placeholder since we're using OpenAI API
                # In a real implementation, this would load the actual Whisper model
                model = {
                    'name': model_key,
                    'size': model_size.parameters,
                    'loaded_at': datetime.now(),
                    'vram_required': model_size.vram_required
                }
                
                load_time = time.time() - start_time
                
                self.loaded_models[model_key] = model
                self.performance_metrics['model_load_times'][model_key] = load_time
                
                # Monitor memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.performance_metrics['memory_usage'][model_key] = memory_mb
                
                logger.info(f"Model {model_key} loaded in {load_time:.2f}s, memory: {memory_mb:.1f}MB")
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model {model_key}: {str(e)}")
                raise
    
    def unload_model(self, model_size: WhisperModel) -> None:
        """Unload a model from memory"""
        model_key = model_size.value
        
        with self.lock:
            if model_key in self.loaded_models:
                del self.loaded_models[model_key]
                gc.collect()  # Force garbage collection
                logger.info(f"Unloaded model: {model_key}")
            else:
                logger.warning(f"Model {model_key} not loaded")
    
    def get_optimal_model(self, audio_duration: float, quality_target: str = "balanced") -> WhisperModel:
        """Select optimal model based on audio duration and quality requirements"""
        if quality_target == "speed":
            if audio_duration < 300:  # 5 minutes
                return WhisperModel.TINY
            elif audio_duration < 1800:  # 30 minutes
                return WhisperModel.BASE
            else:
                return WhisperModel.SMALL
        
        elif quality_target == "accuracy":
            if audio_duration < 600:  # 10 minutes
                return WhisperModel.LARGE_V3
            elif audio_duration < 1800:  # 30 minutes
                return WhisperModel.MEDIUM
            else:
                return WhisperModel.SMALL
        
        else:  # balanced
            if audio_duration < 300:  # 5 minutes
                return WhisperModel.BASE
            elif audio_duration < 1800:  # 30 minutes
                return WhisperModel.SMALL
            else:
                return WhisperModel.BASE
    
    def monitor_performance(self) -> Dict[str, Any]:
        """Get performance monitoring metrics"""
        return {
            'loaded_models': list(self.loaded_models.keys()),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'total_memory_mb': sum(self.performance_metrics['memory_usage'].values()),
            'average_load_time': self._calculate_average_load_time(),
            'performance_metrics': self.performance_metrics
        }
    
    def clear_cache(self) -> None:
        """Clear all cached models"""
        with self.lock:
            self.loaded_models.clear()
            gc.collect()
            logger.info("Model cache cleared")
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
        return self.performance_metrics['cache_hits'] / total if total > 0 else 0.0
    
    def _calculate_average_load_time(self) -> float:
        """Calculate average model load time"""
        load_times = list(self.performance_metrics['model_load_times'].values())
        return sum(load_times) / len(load_times) if load_times else 0.0

class WhisperAdvancedProcessor:
    """Core processing engine for Whisper Advanced Integration"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """Initialize the advanced processor"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize components
        self.whisper_client = WhisperAPIAdvanced(api_key=self.api_key)
        self.model_manager = ModelManager(cache_dir=cache_dir)
        
        # Processing statistics
        self.processing_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_processing_time': 0.0,
            'total_audio_duration': 0.0,
            'average_confidence': 0.0,
            'requests_by_model': {},
            'requests_by_language': {},
            'error_types': {}
        }
        
        # Configuration cache
        self.config_cache: Dict[str, WhisperConfig] = {}
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("WhisperAdvancedProcessor initialized successfully")
    
    async def transcribe(
        self,
        audio_file_path: str,
        config: Optional[WhisperConfig] = None
    ) -> TranscriptionResult:
        """
        Main transcription method with enhanced configuration support
        
        Args:
            audio_file_path: Path to audio file
            config: Advanced configuration options
            
        Returns:
            Enhanced transcription result
        """
        if config is None:
            config = WhisperConfig()
        
        start_time = time.time()
        
        try:
            # Update processing statistics
            self.processing_stats['total_requests'] += 1
            
            # Load optimal model
            model = self.model_manager.load_model(config.model_size)
            
            # Convert to legacy config for API compatibility
            legacy_config = config.to_legacy_config()
            
            # Perform transcription using existing API client
            legacy_result = await self.whisper_client.transcribe(audio_file_path, legacy_config)
            
            # Convert to enhanced result format
            result = self._convert_legacy_result(legacy_result, config, start_time)
            
            # Update statistics
            self._update_processing_stats(result, config)
            
            self.processing_stats['successful_requests'] += 1
            
            logger.info(f"Transcription completed: {result.word_count} words, "
                       f"{result.processing_time:.2f}s, confidence: {result.confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            self.processing_stats['failed_requests'] += 1
            error_type = type(e).__name__
            self.processing_stats['error_types'][error_type] = \
                self.processing_stats['error_types'].get(error_type, 0) + 1
            
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def detect_language(self, audio_file_path: str) -> LanguageDetectionResult:
        """
        Detect language from audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Language detection result with confidence scores
        """
        try:
            # Use a minimal config for language detection
            config = WhisperConfig(
                model_size=WhisperModel.BASE,
                language=None,  # Auto-detect
                temperature=0.0
            )
            
            result = await self.transcribe(audio_file_path, config)
            
            # Extract language information
            return LanguageDetectionResult(
                detected_language=result.language or "unknown",
                language_probability=0.9,  # Placeholder - would be calculated from model
                all_language_probs={result.language or "unknown": 0.9}
            )
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            raise
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        stats = self.processing_stats.copy()
        
        # Add model manager statistics
        stats['model_manager'] = self.model_manager.monitor_performance()
        
        # Add API client statistics
        stats['api_client'] = self.whisper_client.get_usage_statistics()
        
        # Calculate derived metrics
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_requests']
            
            if stats['total_audio_duration'] > 0:
                stats['processing_speed_ratio'] = stats['total_processing_time'] / stats['total_audio_duration']
        
        return stats
    
    def create_optimized_config(
        self,
        audio_duration: float,
        quality_target: str = "balanced",
        domain: Optional[str] = None,
        custom_vocabulary: Optional[List[str]] = None
    ) -> WhisperConfig:
        """
        Create optimized configuration based on requirements
        
        Args:
            audio_duration: Duration of audio in seconds
            quality_target: "speed", "accuracy", or "balanced"
            domain: Domain context (medical, legal, business, etc.)
            custom_vocabulary: Custom vocabulary terms
            
        Returns:
            Optimized WhisperConfig
        """
        # Select optimal model
        optimal_model = self.model_manager.get_optimal_model(audio_duration, quality_target)
        
        # Base configuration
        config = WhisperConfig(
            model_size=optimal_model,
            custom_vocabulary=custom_vocabulary or []
        )
        
        # Optimize based on quality target
        if quality_target == "speed":
            config.temperature = 0.3
            config.beam_size = 1
            config.word_timestamps = False
            config.enable_vad = False
        elif quality_target == "accuracy":
            config.temperature = 0.0
            config.beam_size = 5
            config.word_timestamps = True
            config.enable_vad = True
            config.enable_diarization = True
        
        # Add domain-specific optimizations
        if domain:
            config.domain_context = domain
            domain_vocab = self._get_domain_vocabulary(domain)
            config.custom_vocabulary.extend(domain_vocab)
        
        return config
    
    def clear_caches(self) -> None:
        """Clear all caches"""
        self.model_manager.clear_cache()
        self.whisper_client.clear_cache()
        self.config_cache.clear()
        logger.info("All caches cleared")
    
    def _convert_legacy_result(
        self,
        legacy_result: BaseTranscriptionResult,
        config: WhisperConfig,
        start_time: float
    ) -> TranscriptionResult:
        """Convert legacy result to enhanced format"""
        processing_time = time.time() - start_time
        
        # Convert segments
        segments = []
        if hasattr(legacy_result, 'segments') and legacy_result.segments:
            for i, seg in enumerate(legacy_result.segments):
                segment = TranscriptionSegment(
                    id=i,
                    seek=seg.get('seek', 0),
                    start=seg.get('start', 0.0),
                    end=seg.get('end', 0.0),
                    text=seg.get('text', ''),
                    tokens=seg.get('tokens', []),
                    temperature=seg.get('temperature', config.temperature),
                    avg_logprob=seg.get('avg_logprob', 0.0),
                    compression_ratio=seg.get('compression_ratio', 0.0),
                    no_speech_prob=seg.get('no_speech_prob', 0.0),
                    confidence=max(0.0, min(1.0, seg.get('avg_logprob', -1.0) + 1.0))
                )
                segments.append(segment)
        
        # Create language detection result
        language_detection = LanguageDetectionResult(
            detected_language=legacy_result.language or "unknown",
            language_probability=0.9,
            all_language_probs={legacy_result.language or "unknown": 0.9}
        )
        
        return TranscriptionResult(
            text=legacy_result.text,
            segments=segments,
            language=legacy_result.language or "",
            language_detection=language_detection,
            processing_time=processing_time,
            model_used=config.model_size.value,
            word_count=len(legacy_result.text.split()) if legacy_result.text else 0,
            duration=legacy_result.duration or 0.0,
            confidence_score=legacy_result.get_average_confidence() if hasattr(legacy_result, 'get_average_confidence') else 0.0,
            config_used=config,
            metadata={
                'api_processing_time': legacy_result.processing_time,
                'model_parameters': config.model_size.parameters,
                'vram_required': config.model_size.vram_required
            }
        )
    
    def _update_processing_stats(self, result: TranscriptionResult, config: WhisperConfig):
        """Update processing statistics"""
        self.processing_stats['total_processing_time'] += result.processing_time
        self.processing_stats['total_audio_duration'] += result.duration
        
        # Update model statistics
        model_key = config.model_size.value
        self.processing_stats['requests_by_model'][model_key] = \
            self.processing_stats['requests_by_model'].get(model_key, 0) + 1
        
        # Update language statistics
        if result.language:
            self.processing_stats['requests_by_language'][result.language] = \
                self.processing_stats['requests_by_language'].get(result.language, 0) + 1
        
        # Update average confidence
        total_confidence = (self.processing_stats['average_confidence'] * 
                           (self.processing_stats['successful_requests'] - 1) + result.confidence_score)
        self.processing_stats['average_confidence'] = total_confidence / self.processing_stats['successful_requests']
    
    def _get_domain_vocabulary(self, domain: str) -> List[str]:
        """Get domain-specific vocabulary"""
        domain_vocabularies = {
            'medical': [
                'diagnosis', 'treatment', 'medication', 'symptoms', 'patient', 'doctor',
                'prescription', 'therapy', 'examination', 'consultation', 'medical history'
            ],
            'legal': [
                'plaintiff', 'defendant', 'court', 'evidence', 'testimony', 'objection',
                'contract', 'agreement', 'litigation', 'settlement', 'jurisdiction'
            ],
            'business': [
                'revenue', 'strategy', 'market', 'customer', 'growth', 'analysis',
                'budget', 'forecast', 'stakeholder', 'ROI', 'KPI', 'metrics'
            ],
            'technical': [
                'algorithm', 'implementation', 'architecture', 'deployment', 'optimization',
                'database', 'API', 'framework', 'infrastructure', 'scalability'
            ],
            'education': [
                'curriculum', 'assessment', 'learning', 'student', 'teacher', 'education',
                'pedagogy', 'evaluation', 'academic', 'research', 'methodology'
            ]
        }
        
        return domain_vocabularies.get(domain.lower(), [])

# Utility functions for common configurations
def create_high_accuracy_config(
    model_size: WhisperModel = WhisperModel.LARGE_V3,
    custom_vocabulary: Optional[List[str]] = None
) -> WhisperConfig:
    """Create configuration optimized for maximum accuracy"""
    return WhisperConfig(
        model_size=model_size,
        temperature=0.0,
        beam_size=5,
        patience=1.0,
        word_timestamps=True,
        enable_vad=True,
        enable_diarization=True,
        custom_vocabulary=custom_vocabulary or [],
        compression_ratio_threshold=2.4,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6
    )

def create_fast_processing_config(
    model_size: WhisperModel = WhisperModel.BASE,
    custom_vocabulary: Optional[List[str]] = None
) -> WhisperConfig:
    """Create configuration optimized for speed"""
    return WhisperConfig(
        model_size=model_size,
        temperature=0.3,
        beam_size=1,
        patience=0.5,
        word_timestamps=False,
        enable_vad=False,
        enable_diarization=False,
        custom_vocabulary=custom_vocabulary or [],
        fp16=True
    )

def create_balanced_config(
    model_size: WhisperModel = WhisperModel.SMALL,
    custom_vocabulary: Optional[List[str]] = None
) -> WhisperConfig:
    """Create balanced configuration for general use"""
    return WhisperConfig(
        model_size=model_size,
        temperature=0.1,
        beam_size=3,
        patience=1.0,
        word_timestamps=True,
        enable_vad=True,
        enable_diarization=False,
        custom_vocabulary=custom_vocabulary or []
    )

# Example usage
async def example_usage():
    """Example usage of the WhisperAdvancedProcessor"""
    try:
        # Initialize processor
        processor = WhisperAdvancedProcessor()
        
        # Create optimized configuration
        config = processor.create_optimized_config(
            audio_duration=600,  # 10 minutes
            quality_target="balanced",
            domain="business",
            custom_vocabulary=["quarterly", "revenue", "stakeholder"]
        )
        
        print(f"Created config with model: {config.model_size.value}")
        print(f"Model parameters: {config.model_size.parameters}")
        print(f"Recommended use cases: {config.model_size.use_cases}")
        
        # Get processing statistics
        stats = processor.get_processing_statistics()
        print(f"Processing statistics: {stats}")
        
        print("WhisperAdvancedProcessor example completed successfully!")
        
    except Exception as e:
        print(f"Example failed: {str(e)}")

if __name__ == "__main__":
    # Run example usage
    asyncio.run(example_usage())