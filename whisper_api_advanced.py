"""
Whisper API Advanced Configuration System

This module implements Task 118: Advanced Whisper API configuration with custom prompts,
temperature control, language detection, custom vocabulary injection, and confidence
threshold tuning for enhanced transcription accuracy.

Requirements addressed:
- 3.1: Speech-to-text transcription with high accuracy
- 3.2: Support for multiple audio formats and quality levels
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
from openai import OpenAI
import numpy as np
from pathlib import Path
import tempfile
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperModel(Enum):
    """Available Whisper models with their characteristics"""
    WHISPER_1 = "whisper-1"
    
    @property
    def max_file_size_mb(self) -> int:
        """Maximum file size in MB for this model"""
        return 25
    
    @property
    def supported_formats(self) -> List[str]:
        """Supported audio formats"""
        return ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']

class ResponseFormat(Enum):
    """Available response formats"""
    JSON = "json"
    TEXT = "text"
    SRT = "srt"
    VERBOSE_JSON = "verbose_json"
    VTT = "vtt"

class LanguageCode(Enum):
    """Supported language codes for Whisper API"""
    AUTO = None  # Auto-detect
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE = "zh"
    DUTCH = "nl"
    ARABIC = "ar"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    CZECH = "cs"
    HUNGARIAN = "hu"
    TURKISH = "tr"
    HINDI = "hi"
    THAI = "th"
    VIETNAMESE = "vi"
    INDONESIAN = "id"
    MALAY = "ms"
    HEBREW = "he"
    GREEK = "el"
    BULGARIAN = "bg"
    CROATIAN = "hr"
    ROMANIAN = "ro"
    SLOVAK = "sk"
    SLOVENIAN = "sl"
    ESTONIAN = "et"
    LATVIAN = "lv"
    LITHUANIAN = "lt"
    UKRAINIAN = "uk"
    WELSH = "cy"
    IRISH = "ga"
    BASQUE = "eu"
    CATALAN = "ca"
    GALICIAN = "gl"

@dataclass
class WhisperConfig:
    """Advanced configuration for Whisper API calls"""
    model: WhisperModel = WhisperModel.WHISPER_1
    language: Optional[LanguageCode] = LanguageCode.AUTO
    prompt: Optional[str] = None
    response_format: ResponseFormat = ResponseFormat.VERBOSE_JSON
    temperature: float = 0.0
    timestamp_granularities: List[str] = None
    
    # Advanced settings
    custom_vocabulary: List[str] = None
    confidence_threshold: float = 0.0
    enable_word_timestamps: bool = True
    enable_segment_timestamps: bool = True
    max_segment_length: Optional[int] = None
    suppress_silence: bool = True
    
    # Context and domain-specific settings
    domain_context: Optional[str] = None
    speaker_context: Optional[str] = None
    content_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate and set defaults after initialization"""
        if self.timestamp_granularities is None:
            self.timestamp_granularities = ["segment"]
        
        if self.custom_vocabulary is None:
            self.custom_vocabulary = []
        
        # Validate temperature
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        
        # Validate confidence threshold
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
    
    def to_api_params(self) -> Dict[str, Any]:
        """Convert configuration to Whisper API parameters"""
        params = {
            "model": self.model.value,
            "response_format": self.response_format.value,
            "temperature": self.temperature,
        }
        
        if self.language and self.language != LanguageCode.AUTO:
            params["language"] = self.language.value
        
        if self.prompt:
            params["prompt"] = self._build_enhanced_prompt()
        
        if "word" in self.timestamp_granularities or "segment" in self.timestamp_granularities:
            params["timestamp_granularities"] = self.timestamp_granularities
        
        return params
    
    def _build_enhanced_prompt(self) -> str:
        """Build enhanced prompt with context and vocabulary"""
        prompt_parts = []
        
        # Add base prompt
        if self.prompt:
            prompt_parts.append(self.prompt)
        
        # Add domain context
        if self.domain_context:
            prompt_parts.append(f"Domain: {self.domain_context}")
        
        # Add speaker context
        if self.speaker_context:
            prompt_parts.append(f"Speaker: {self.speaker_context}")
        
        # Add content type context
        if self.content_type:
            prompt_parts.append(f"Content type: {self.content_type}")
        
        # Add custom vocabulary
        if self.custom_vocabulary:
            vocab_text = ", ".join(self.custom_vocabulary[:20])  # Limit to avoid prompt length issues
            prompt_parts.append(f"Key terms: {vocab_text}")
        
        return ". ".join(prompt_parts)

@dataclass
class TranscriptionResult:
    """Enhanced transcription result with metadata"""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: List[Dict[str, Any]] = None
    words: List[Dict[str, Any]] = None
    confidence_scores: Dict[str, float] = None
    processing_time: float = 0.0
    model_used: str = ""
    config_used: Optional[WhisperConfig] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.segments is None:
            self.segments = []
        if self.words is None:
            self.words = []
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.metadata is None:
            self.metadata = {}
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence score"""
        if not self.words:
            return 0.0
        
        confidences = [word.get('confidence', 0.0) for word in self.words if 'confidence' in word]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def get_low_confidence_segments(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Get segments with confidence below threshold"""
        low_confidence = []
        
        for segment in self.segments:
            if segment.get('avg_logprob', 0) < threshold:
                low_confidence.append(segment)
        
        return low_confidence
    
    def filter_by_confidence(self, threshold: float) -> 'TranscriptionResult':
        """Return filtered result with only high-confidence content"""
        if not self.words:
            return self
        
        filtered_words = [word for word in self.words if word.get('confidence', 1.0) >= threshold]
        filtered_text = " ".join([word.get('word', '') for word in filtered_words])
        
        # Create new result with filtered content
        return TranscriptionResult(
            text=filtered_text,
            language=self.language,
            duration=self.duration,
            words=filtered_words,
            confidence_scores=self.confidence_scores,
            processing_time=self.processing_time,
            model_used=self.model_used,
            config_used=self.config_used,
            metadata={**self.metadata, 'filtered_by_confidence': threshold}
        )

class WhisperAPIAdvanced:
    """Advanced Whisper API client with enhanced configuration options"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the advanced Whisper API client"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.cache = {}  # Simple in-memory cache
        self.usage_stats = {
            'total_requests': 0,
            'total_duration': 0.0,
            'total_cost_estimate': 0.0,
            'requests_by_model': {},
            'average_processing_time': 0.0
        }
    
    async def transcribe(
        self,
        audio_file_path: str,
        config: Optional[WhisperConfig] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file with advanced configuration
        
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
            # Validate file
            self._validate_audio_file(audio_file_path)
            
            # Check cache
            cache_key = self._generate_cache_key(audio_file_path, config)
            if cache_key in self.cache:
                logger.info("Returning cached transcription result")
                return self.cache[cache_key]
            
            # Prepare API parameters
            api_params = config.to_api_params()
            
            # Open and transcribe file
            with open(audio_file_path, 'rb') as audio_file:
                logger.info(f"Transcribing with config: {api_params}")
                
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **api_params
                )
            
            # Process response
            result = self._process_response(response, config, start_time)
            
            # Cache result
            self.cache[cache_key] = result
            
            # Update usage stats
            self._update_usage_stats(result, config)
            
            logger.info(f"Transcription completed in {result.processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    async def transcribe_with_retry(
        self,
        audio_file_path: str,
        config: Optional[WhisperConfig] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> TranscriptionResult:
        """
        Transcribe with automatic retry and exponential backoff
        
        Args:
            audio_file_path: Path to audio file
            config: Advanced configuration options
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            
        Returns:
            Enhanced transcription result
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.transcribe(audio_file_path, config)
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Transcription attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All transcription attempts failed. Last error: {str(e)}")
        
        raise last_exception
    
    async def batch_transcribe(
        self,
        audio_files: List[str],
        config: Optional[WhisperConfig] = None,
        max_concurrent: int = 3
    ) -> List[TranscriptionResult]:
        """
        Transcribe multiple audio files concurrently
        
        Args:
            audio_files: List of audio file paths
            config: Advanced configuration options
            max_concurrent: Maximum concurrent transcriptions
            
        Returns:
            List of transcription results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def transcribe_single(file_path: str) -> TranscriptionResult:
            async with semaphore:
                return await self.transcribe_with_retry(file_path, config)
        
        tasks = [transcribe_single(file_path) for file_path in audio_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to transcribe {audio_files[i]}: {str(result)}")
                # Create error result
                error_result = TranscriptionResult(
                    text="",
                    metadata={'error': str(result), 'file_path': audio_files[i]}
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def create_domain_config(
        self,
        domain: str,
        vocabulary: List[str] = None,
        context_prompt: str = None
    ) -> WhisperConfig:
        """
        Create domain-specific configuration
        
        Args:
            domain: Domain type (medical, legal, technical, etc.)
            vocabulary: Domain-specific vocabulary
            context_prompt: Domain context prompt
            
        Returns:
            Configured WhisperConfig for the domain
        """
        domain_configs = {
            'medical': {
                'prompt': "This is a medical conversation with healthcare terminology, medications, and procedures.",
                'vocabulary': ['diagnosis', 'treatment', 'medication', 'symptoms', 'patient', 'doctor'],
                'temperature': 0.1,  # Lower temperature for accuracy
                'confidence_threshold': 0.7
            },
            'legal': {
                'prompt': "This is a legal conversation with legal terminology, case references, and formal language.",
                'vocabulary': ['plaintiff', 'defendant', 'court', 'evidence', 'testimony', 'objection'],
                'temperature': 0.1,
                'confidence_threshold': 0.8
            },
            'technical': {
                'prompt': "This is a technical conversation with specialized terminology and concepts.",
                'vocabulary': ['algorithm', 'implementation', 'architecture', 'deployment', 'optimization'],
                'temperature': 0.2,
                'confidence_threshold': 0.6
            },
            'business': {
                'prompt': "This is a business conversation with corporate terminology and strategic discussions.",
                'vocabulary': ['revenue', 'strategy', 'market', 'customer', 'growth', 'analysis'],
                'temperature': 0.3,
                'confidence_threshold': 0.5
            },
            'education': {
                'prompt': "This is an educational conversation with academic terminology and learning concepts.",
                'vocabulary': ['curriculum', 'assessment', 'learning', 'student', 'teacher', 'education'],
                'temperature': 0.2,
                'confidence_threshold': 0.6
            }
        }
        
        base_config = domain_configs.get(domain.lower(), domain_configs['business'])
        
        # Merge with custom parameters
        custom_vocab = vocabulary or []
        combined_vocab = base_config['vocabulary'] + custom_vocab
        
        final_prompt = context_prompt or base_config['prompt']
        
        return WhisperConfig(
            prompt=final_prompt,
            custom_vocabulary=combined_vocab,
            temperature=base_config['temperature'],
            confidence_threshold=base_config['confidence_threshold'],
            domain_context=domain,
            response_format=ResponseFormat.VERBOSE_JSON,
            enable_word_timestamps=True,
            timestamp_granularities=["word", "segment"]
        )
    
    def optimize_config_for_quality(self, config: WhisperConfig) -> WhisperConfig:
        """
        Optimize configuration for maximum transcription quality
        
        Args:
            config: Base configuration to optimize
            
        Returns:
            Optimized configuration
        """
        optimized = WhisperConfig(
            model=config.model,
            language=config.language,
            prompt=config.prompt,
            response_format=ResponseFormat.VERBOSE_JSON,
            temperature=0.0,  # Lowest temperature for consistency
            custom_vocabulary=config.custom_vocabulary,
            confidence_threshold=0.7,  # Higher threshold
            enable_word_timestamps=True,
            enable_segment_timestamps=True,
            timestamp_granularities=["word", "segment"],
            suppress_silence=True,
            domain_context=config.domain_context,
            speaker_context=config.speaker_context,
            content_type=config.content_type
        )
        
        return optimized
    
    def optimize_config_for_speed(self, config: WhisperConfig) -> WhisperConfig:
        """
        Optimize configuration for faster processing
        
        Args:
            config: Base configuration to optimize
            
        Returns:
            Speed-optimized configuration
        """
        optimized = WhisperConfig(
            model=config.model,
            language=config.language,
            prompt=config.prompt,
            response_format=ResponseFormat.TEXT,  # Simpler format
            temperature=0.3,  # Slightly higher for faster processing
            custom_vocabulary=config.custom_vocabulary[:10],  # Limit vocabulary
            confidence_threshold=0.3,  # Lower threshold
            enable_word_timestamps=False,  # Disable for speed
            enable_segment_timestamps=False,
            timestamp_granularities=["segment"],
            suppress_silence=False,
            domain_context=config.domain_context
        )
        
        return optimized
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get detailed usage statistics"""
        return {
            **self.usage_stats,
            'cache_size': len(self.cache),
            'cache_hit_rate': self._calculate_cache_hit_rate()
        }
    
    def clear_cache(self):
        """Clear the transcription cache"""
        self.cache.clear()
        logger.info("Transcription cache cleared")
    
    def _validate_audio_file(self, file_path: str):
        """Validate audio file before transcription"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > WhisperModel.WHISPER_1.max_file_size_mb:
            raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds maximum ({WhisperModel.WHISPER_1.max_file_size_mb}MB)")
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        if file_ext not in WhisperModel.WHISPER_1.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _generate_cache_key(self, file_path: str, config: WhisperConfig) -> str:
        """Generate cache key for file and configuration"""
        # Include file modification time and size for cache invalidation
        stat = os.stat(file_path)
        file_info = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
        
        # Convert config to serializable dict
        config_dict = asdict(config)
        
        # Convert enum values to strings for JSON serialization
        if 'model' in config_dict and hasattr(config_dict['model'], 'value'):
            config_dict['model'] = config_dict['model'].value
        if 'language' in config_dict and hasattr(config_dict['language'], 'value'):
            config_dict['language'] = config_dict['language'].value
        if 'response_format' in config_dict and hasattr(config_dict['response_format'], 'value'):
            config_dict['response_format'] = config_dict['response_format'].value
        
        config_str = json.dumps(config_dict, sort_keys=True, default=str)
        
        return hashlib.md5(f"{file_info}_{config_str}".encode()).hexdigest()
    
    def _process_response(
        self,
        response: Any,
        config: WhisperConfig,
        start_time: float
    ) -> TranscriptionResult:
        """Process Whisper API response into enhanced result"""
        processing_time = time.time() - start_time
        
        if config.response_format == ResponseFormat.VERBOSE_JSON:
            # Extract detailed information from verbose response
            result = TranscriptionResult(
                text=response.text,
                language=getattr(response, 'language', None),
                duration=getattr(response, 'duration', None),
                segments=getattr(response, 'segments', []),
                words=getattr(response, 'words', []),
                processing_time=processing_time,
                model_used=config.model.value,
                config_used=config
            )
            
            # Calculate confidence scores
            if result.segments:
                segment_confidences = []
                for segment in result.segments:
                    if 'avg_logprob' in segment:
                        # Convert log probability to confidence (approximate)
                        confidence = min(1.0, max(0.0, (segment['avg_logprob'] + 1.0)))
                        segment_confidences.append(confidence)
                
                if segment_confidences:
                    result.confidence_scores['average'] = sum(segment_confidences) / len(segment_confidences)
                    result.confidence_scores['segments'] = segment_confidences
            
            # Filter by confidence if threshold is set
            if config.confidence_threshold > 0.0:
                result = result.filter_by_confidence(config.confidence_threshold)
        
        else:
            # Simple text response
            result = TranscriptionResult(
                text=response.text if hasattr(response, 'text') else str(response),
                processing_time=processing_time,
                model_used=config.model.value,
                config_used=config
            )
        
        return result
    
    def _update_usage_stats(self, result: TranscriptionResult, config: WhisperConfig):
        """Update usage statistics"""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_duration'] += result.duration or 0.0
        self.usage_stats['total_cost_estimate'] += self._estimate_cost(result.duration or 0.0)
        
        model_key = config.model.value
        if model_key not in self.usage_stats['requests_by_model']:
            self.usage_stats['requests_by_model'][model_key] = 0
        self.usage_stats['requests_by_model'][model_key] += 1
        
        # Update average processing time
        total_time = (self.usage_stats['average_processing_time'] * 
                     (self.usage_stats['total_requests'] - 1) + result.processing_time)
        self.usage_stats['average_processing_time'] = total_time / self.usage_stats['total_requests']
    
    def _estimate_cost(self, duration_seconds: float) -> float:
        """Estimate API cost based on duration (approximate)"""
        # Whisper API pricing is approximately $0.006 per minute
        minutes = duration_seconds / 60.0
        return minutes * 0.006
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.usage_stats['total_requests'] == 0:
            return 0.0
        
        # This is a simplified calculation - in practice, you'd track cache hits
        return min(0.3, len(self.cache) / max(1, self.usage_stats['total_requests']))

# Utility functions for common use cases
def create_medical_transcription_config(
    custom_vocabulary: List[str] = None,
    speaker_context: str = None
) -> WhisperConfig:
    """Create optimized configuration for medical transcription"""
    medical_vocab = [
        'diagnosis', 'treatment', 'medication', 'symptoms', 'patient', 'doctor',
        'prescription', 'dosage', 'therapy', 'examination', 'consultation',
        'medical history', 'vital signs', 'blood pressure', 'heart rate'
    ]
    
    if custom_vocabulary:
        medical_vocab.extend(custom_vocabulary)
    
    return WhisperConfig(
        prompt="This is a medical conversation between healthcare professionals and patients. Please transcribe accurately with proper medical terminology.",
        custom_vocabulary=medical_vocab,
        temperature=0.1,
        confidence_threshold=0.8,
        domain_context="medical",
        speaker_context=speaker_context,
        content_type="medical consultation",
        response_format=ResponseFormat.VERBOSE_JSON,
        enable_word_timestamps=True,
        timestamp_granularities=["word", "segment"]
    )

def create_meeting_transcription_config(
    participants: List[str] = None,
    meeting_type: str = "business meeting"
) -> WhisperConfig:
    """Create optimized configuration for meeting transcription"""
    business_vocab = [
        'agenda', 'action items', 'follow up', 'deadline', 'project', 'budget',
        'timeline', 'deliverables', 'stakeholders', 'objectives', 'strategy',
        'revenue', 'quarterly', 'metrics', 'KPI', 'ROI'
    ]
    
    speaker_info = f"Participants: {', '.join(participants)}" if participants else None
    
    return WhisperConfig(
        prompt=f"This is a {meeting_type} with multiple speakers discussing business topics. Please transcribe clearly with proper punctuation.",
        custom_vocabulary=business_vocab,
        temperature=0.2,
        confidence_threshold=0.6,
        domain_context="business",
        speaker_context=speaker_info,
        content_type=meeting_type,
        response_format=ResponseFormat.VERBOSE_JSON,
        enable_word_timestamps=True,
        timestamp_granularities=["segment"]
    )

def create_interview_transcription_config(
    interviewer: str = None,
    interviewee: str = None,
    topic: str = None
) -> WhisperConfig:
    """Create optimized configuration for interview transcription"""
    interview_vocab = [
        'question', 'answer', 'experience', 'background', 'skills', 'qualifications',
        'responsibilities', 'achievements', 'challenges', 'goals', 'objectives'
    ]
    
    participants = []
    if interviewer:
        participants.append(f"Interviewer: {interviewer}")
    if interviewee:
        participants.append(f"Interviewee: {interviewee}")
    
    speaker_info = ", ".join(participants) if participants else None
    topic_context = f" about {topic}" if topic else ""
    
    return WhisperConfig(
        prompt=f"This is an interview{topic_context} with clear question and answer format. Please transcribe with proper speaker identification.",
        custom_vocabulary=interview_vocab,
        temperature=0.2,
        confidence_threshold=0.7,
        domain_context="interview",
        speaker_context=speaker_info,
        content_type="interview",
        response_format=ResponseFormat.VERBOSE_JSON,
        enable_word_timestamps=True,
        timestamp_granularities=["segment"]
    )

# Example usage and testing functions
async def example_usage():
    """Example usage of the advanced Whisper API"""
    try:
        # Initialize the advanced client
        whisper_client = WhisperAPIAdvanced()
        
        # Example 1: Basic transcription with custom configuration
        config = WhisperConfig(
            temperature=0.1,
            custom_vocabulary=['artificial intelligence', 'machine learning', 'neural networks'],
            confidence_threshold=0.7,
            enable_word_timestamps=True
        )
        
        # result = await whisper_client.transcribe('sample_audio.mp3', config)
        # print(f"Transcription: {result.text}")
        # print(f"Confidence: {result.get_average_confidence():.2f}")
        
        # Example 2: Domain-specific configuration
        medical_config = whisper_client.create_domain_config(
            domain='medical',
            vocabulary=['hypertension', 'diabetes', 'cardiovascular'],
            context_prompt="This is a patient consultation discussing medical conditions."
        )
        
        # Example 3: Batch transcription
        audio_files = ['file1.mp3', 'file2.mp3', 'file3.mp3']
        # results = await whisper_client.batch_transcribe(audio_files, medical_config)
        
        # Example 4: Usage statistics
        stats = whisper_client.get_usage_statistics()
        print(f"Usage stats: {stats}")
        
        print("Advanced Whisper API examples completed successfully!")
        
    except Exception as e:
        print(f"Example failed: {str(e)}")

if __name__ == "__main__":
    # Run example usage
    asyncio.run(example_usage())