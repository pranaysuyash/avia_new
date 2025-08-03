# Speech-to-Text Module
# Handles transcription using OpenAI Whisper API with local fallback

import os
import time
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import openai
import whisper

from errors import (
    TranscriptionError, APIError, NetworkError, handle_error,
    ErrorCode, create_api_key_error, create_network_timeout_error
)

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Data class for transcription results"""
    text: str
    confidence: float
    processing_time: float
    model_used: str
    language: str = "en"
    timestamps: Optional[List[Dict]] = None
    
    def word_count(self) -> int:
        if not self.text.strip():
            return 0
        return len(self.text.split())
    
    def get_duration(self) -> float:
        """Get total duration from timestamps if available"""
        if self.timestamps and len(self.timestamps) > 0:
            return max(segment.get('end', 0) for segment in self.timestamps)
        return 0.0
    
    def get_speech_rate(self) -> float:
        """Calculate words per minute"""
        duration = self.get_duration()
        if duration > 0:
            return (self.word_count() / duration) * 60
        return 0.0

# TranscriptionError is now imported from errors module

class WhisperTranscriber:
    """Handles both API and local Whisper transcription"""
    
    def __init__(self):
        self.api_client = None
        self.local_model = None
        self._setup_api_client()
    
    def _setup_api_client(self):
        """Initialize OpenAI API client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.api_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI API client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI API client: {e}")
                self.api_client = None
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.api_client = None
    
    def _load_local_model(self, model_size: str = "base"):
        """Load local Whisper model"""
        try:
            if self.local_model is None:
                logger.info(f"Loading local Whisper model: {model_size}")
                self.local_model = whisper.load_model(model_size)
                logger.info("Local Whisper model loaded successfully")
            return self.local_model
        except Exception as e:
            logger.error(f"Failed to load local Whisper model: {e}")
            raise TranscriptionError(
                message=f"Failed to load local Whisper model: {e}",
                error_code=ErrorCode.LOCAL_MODEL_ERROR,
                user_message="Unable to load offline transcription model. Please check your installation.",
                model_used=f"whisper-local-{model_size}",
                suggestions=[
                    "Try using API mode instead of local processing",
                    "Restart the application",
                    "Check available disk space and memory",
                    "Reinstall the whisper package: pip install openai-whisper"
                ]
            )
    
    def _transcribe_with_api(self, audio_path: str, max_retries: int = 3) -> TranscriptionResult:
        """Transcribe using OpenAI Whisper API with retry logic"""
        if not self.api_client:
            raise create_api_key_error("OpenAI")
        
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                with open(audio_path, "rb") as audio_file:
                    logger.info(f"Attempting API transcription (attempt {attempt + 1}/{max_retries})")
                    
                    response = self.api_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                    
                    processing_time = time.time() - start_time
                    
                    # Extract confidence from segments if available
                    confidence = 0.9  # Default high confidence for API
                    if hasattr(response, 'segments') and response.segments:
                        confidences = []
                        for seg in response.segments:
                            if hasattr(seg, 'avg_logprob'):
                                confidences.append(seg.avg_logprob)
                            elif hasattr(seg, '__dict__') and 'avg_logprob' in seg.__dict__:
                                confidences.append(seg.__dict__['avg_logprob'])
                        if confidences:
                            confidence = max(0.1, min(1.0, sum(confidences) / len(confidences) + 1.0))
                    
                    result = TranscriptionResult(
                        text=response.text.strip(),
                        confidence=confidence,
                        processing_time=processing_time,
                        model_used="whisper-1-api",
                        language=getattr(response, 'language', 'en')
                    )
                    
                    logger.info(f"API transcription successful in {processing_time:.2f}s")
                    return result
                    
            except openai.RateLimitError as e:
                wait_time = min(60, (2 ** attempt))  # Exponential backoff, max 60s
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise APIError(
                        message=f"Rate limit exceeded after {max_retries} attempts",
                        error_code=ErrorCode.API_RATE_LIMIT,
                        user_message="API rate limit exceeded. Please try again later or use offline mode.",
                        api_name="OpenAI",
                        suggestions=[
                            "Wait a few minutes before retrying",
                            "Try using offline transcription mode",
                            "Consider upgrading your OpenAI API plan"
                        ]
                    )
            
            except openai.APIError as e:
                wait_time = min(30, (2 ** attempt))  # Exponential backoff
                logger.warning(f"API error: {e}, waiting {wait_time}s before retry {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise APIError(
                        message=f"API error after {max_retries} attempts: {e}",
                        error_code=ErrorCode.API_SERVICE_UNAVAILABLE,
                        user_message="Transcription service is temporarily unavailable. Please try offline mode.",
                        api_name="OpenAI",
                        suggestions=[
                            "Try again in a few minutes",
                            "Use offline transcription mode",
                            "Check OpenAI service status"
                        ]
                    )
            
            except Exception as e:
                logger.error(f"Unexpected error during API transcription: {e}")
                app_error = handle_error(e, {
                    "api_name": "OpenAI",
                    "operation": "transcription",
                    "file_path": audio_path
                })
                raise app_error
        
        raise TranscriptionError(
            f"Failed to transcribe after {max_retries} attempts",
            "MAX_RETRIES_EXCEEDED",
            "Transcription failed after multiple attempts. Please try offline mode."
        )
    
    def _transcribe_with_local_model(self, audio_path: str, model_size: str = "base") -> TranscriptionResult:
        """Transcribe using local Whisper model"""
        start_time = time.time()
        
        try:
            model = self._load_local_model(model_size)
            
            logger.info("Starting local transcription")
            result = model.transcribe(audio_path, verbose=False)
            
            processing_time = time.time() - start_time
            
            # Calculate average confidence from segments
            confidence = 0.7  # Default confidence for local model
            if 'segments' in result and result['segments']:
                confidences = []
                for segment in result['segments']:
                    if 'avg_logprob' in segment:
                        # Convert log probability to confidence (approximate)
                        conf = max(0.1, min(1.0, segment['avg_logprob'] + 1.0))
                        confidences.append(conf)
                if confidences:
                    confidence = sum(confidences) / len(confidences)
            
            transcription_result = TranscriptionResult(
                text=result['text'].strip(),
                confidence=confidence,
                processing_time=processing_time,
                model_used=f"whisper-local-{model_size}",
                language=result.get('language', 'en')
            )
            
            logger.info(f"Local transcription successful in {processing_time:.2f}s")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            raise TranscriptionError(
                f"Local transcription failed: {e}",
                "LOCAL_TRANSCRIPTION_ERROR",
                "Offline transcription failed. Please check your audio file and try again."
            )
    
    def transcribe(self, audio_path: str, use_api: bool = True, model_size: str = "base") -> TranscriptionResult:
        """
        Transcribe audio file to text with automatic fallback
        
        Args:
            audio_path: Path to audio file
            use_api: Whether to try API first (True) or use local model (False)
            model_size: Local model size ('tiny', 'base', 'small', 'medium', 'large')
        
        Returns:
            TranscriptionResult with text and metadata
        """
        if not os.path.exists(audio_path):
            raise TranscriptionError(
                message=f"Audio file not found: {audio_path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
                user_message="Audio file not found. Please check the file path.",
                model_used="unknown",
                suggestions=[
                    "Check that the file exists and the path is correct",
                    "Try uploading the file again"
                ]
            )
        
        # Try API first if requested and available
        if use_api and self.api_client:
            try:
                return self._transcribe_with_api(audio_path)
            except (TranscriptionError, APIError) as e:
                logger.warning(f"API transcription failed: {getattr(e, 'message', str(e))}")
                logger.info("Falling back to local model")
                # Fall through to local model
        
        # Use local model as fallback or primary method
        return self._transcribe_with_local_model(audio_path, model_size)
    
    def transcribe_with_timestamps(self, audio_path: str, use_api: bool = True) -> List[Dict]:
        """
        Transcribe with word-level timestamps for advanced features
        
        Args:
            audio_path: Path to audio file
            use_api: Whether to try API first
        
        Returns:
            List of dictionaries with text, start, and end timestamps
        """
        if not os.path.exists(audio_path):
            raise TranscriptionError(
                message=f"Audio file not found: {audio_path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
                user_message="Audio file not found. Please check the file path.",
                model_used="unknown",
                suggestions=[
                    "Check that the file exists and the path is correct",
                    "Try uploading the file again"
                ]
            )
        
        # For timestamped transcription, we primarily use local model
        # as it provides more detailed segment information
        try:
            model = self._load_local_model("base")
            result = model.transcribe(audio_path, verbose=True, word_timestamps=True)
            
            timestamps = []
            if 'segments' in result:
                for segment in result['segments']:
                    segment_data = {
                        'text': segment['text'].strip(),
                        'start': segment['start'],
                        'end': segment['end'],
                        'confidence': max(0.1, min(1.0, segment.get('avg_logprob', -1) + 1.0))
                    }
                    
                    # Add word-level timestamps if available
                    if 'words' in segment:
                        segment_data['words'] = [
                            {
                                'word': word['word'],
                                'start': word['start'],
                                'end': word['end'],
                                'confidence': max(0.1, min(1.0, word.get('probability', 0.7)))
                            }
                            for word in segment['words']
                        ]
                    
                    timestamps.append(segment_data)
            
            logger.info(f"Timestamped transcription completed with {len(timestamps)} segments")
            return timestamps
            
        except Exception as e:
            logger.error(f"Timestamped transcription failed: {e}")
            raise TranscriptionError(
                message=f"Timestamped transcription failed: {e}",
                error_code=ErrorCode.TRANSCRIPTION_FAILED,
                user_message="Failed to generate timestamped transcription. Please try regular transcription.",
                model_used="whisper-local",
                suggestions=[
                    "Try regular transcription without timestamps",
                    "Check audio file quality",
                    "Use API transcription mode"
                ]
            )
    
    def get_transcription_confidence(self, audio_path: str) -> float:
        """
        Return confidence score for transcription quality
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Use local model for confidence assessment as it provides detailed metrics
            model = self._load_local_model("base")
            result = model.transcribe(audio_path, verbose=True)
            
            if 'segments' in result and result['segments']:
                confidences = []
                for segment in result['segments']:
                    if 'avg_logprob' in segment:
                        # Convert log probability to confidence score
                        conf = max(0.1, min(1.0, segment['avg_logprob'] + 1.0))
                        confidences.append(conf)
                
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    logger.info(f"Average transcription confidence: {avg_confidence:.3f}")
                    return avg_confidence
            
            # Default confidence if no segments available
            return 0.7
            
        except Exception as e:
            logger.error(f"Failed to assess transcription confidence: {e}")
            return 0.5  # Return moderate confidence on error
    
    def transcribe_enhanced(self, audio_path: str, use_api: bool = True, model_size: str = "base",
                          language: str = None, enable_timestamps: bool = False) -> TranscriptionResult:
        """
        Enhanced transcription with multi-language support and timestamps
        
        Args:
            audio_path: Path to audio file
            use_api: Whether to try API first
            model_size: Local model size
            language: Language code (e.g., 'en', 'es', 'fr') - None for auto-detection
            enable_timestamps: Whether to include word-level timestamps
        
        Returns:
            TranscriptionResult with enhanced features
        """
        start_time = time.time()
        
        # Try API first if requested and available
        if use_api and self.api_client:
            try:
                return self._transcribe_with_api_enhanced(audio_path, language, enable_timestamps)
            except Exception as e:
                logger.warning(f"Enhanced API transcription failed: {e}")
                logger.info("Falling back to local model")
        
        # Use local model with enhanced features
        return self._transcribe_with_local_model_enhanced(audio_path, model_size, language, enable_timestamps)
    
    def _transcribe_with_api_enhanced(self, audio_path: str, language: str = None, 
                                    enable_timestamps: bool = False) -> TranscriptionResult:
        """Enhanced API transcription with language and timestamp support"""
        if not self.api_client:
            raise create_api_key_error("OpenAI")
        
        start_time = time.time()
        
        try:
            with open(audio_path, "rb") as audio_file:
                logger.info(f"Starting enhanced API transcription (language: {language}, timestamps: {enable_timestamps})")
                
                # Prepare API parameters
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json" if enable_timestamps else "json"
                }
                
                if language:
                    params["language"] = language
                
                response = self.api_client.audio.transcriptions.create(**params)
                
                processing_time = time.time() - start_time
                
                # Extract confidence and timestamps
                confidence = 0.9  # Default high confidence for API
                timestamps = []
                
                if hasattr(response, 'segments') and response.segments:
                    confidences = []
                    for seg in response.segments:
                        if hasattr(seg, 'avg_logprob'):
                            confidences.append(seg.avg_logprob)
                        
                        if enable_timestamps:
                            timestamps.append({
                                'text': seg.text,
                                'start': seg.start,
                                'end': seg.end,
                                'confidence': max(0.1, min(1.0, getattr(seg, 'avg_logprob', -0.1) + 1.0))
                            })
                    
                    if confidences:
                        confidence = max(0.1, min(1.0, sum(confidences) / len(confidences) + 1.0))
                
                result = TranscriptionResult(
                    text=response.text.strip(),
                    confidence=confidence,
                    processing_time=processing_time,
                    model_used="whisper-1-api-enhanced",
                    language=getattr(response, 'language', language or 'en')
                )
                
                # Add timestamps if requested
                if enable_timestamps and timestamps:
                    result.timestamps = timestamps
                
                logger.info(f"Enhanced API transcription successful in {processing_time:.2f}s")
                return result
                
        except Exception as e:
            logger.error(f"Enhanced API transcription failed: {e}")
            raise TranscriptionError(
                message=f"Enhanced API transcription failed: {e}",
                error_code=ErrorCode.API_SERVICE_UNAVAILABLE,
                user_message="Enhanced transcription service failed. Please try basic mode.",
                model_used="whisper-1-api-enhanced",
                suggestions=[
                    "Try basic transcription mode",
                    "Use offline transcription",
                    "Check your internet connection"
                ]
            )
    
    def _transcribe_with_local_model_enhanced(self, audio_path: str, model_size: str = "base",
                                            language: str = None, enable_timestamps: bool = False) -> TranscriptionResult:
        """Enhanced local transcription with language and timestamp support"""
        start_time = time.time()
        
        try:
            model = self._load_local_model(model_size)
            
            # Prepare transcription parameters
            transcribe_params = {
                'verbose': True,
                'word_timestamps': enable_timestamps
            }
            
            if language:
                transcribe_params['language'] = language
            
            logger.info(f"Starting enhanced local transcription (language: {language}, timestamps: {enable_timestamps})")
            result = model.transcribe(audio_path, **transcribe_params)
            
            processing_time = time.time() - start_time
            
            # Calculate confidence
            confidence = 0.7
            timestamps = []
            
            if 'segments' in result and result['segments']:
                confidences = []
                for segment in result['segments']:
                    if 'avg_logprob' in segment:
                        conf = max(0.1, min(1.0, segment['avg_logprob'] + 1.0))
                        confidences.append(conf)
                    
                    if enable_timestamps:
                        segment_data = {
                            'text': segment['text'].strip(),
                            'start': segment['start'],
                            'end': segment['end'],
                            'confidence': max(0.1, min(1.0, segment.get('avg_logprob', -1) + 1.0))
                        }
                        
                        # Add word-level timestamps if available
                        if 'words' in segment:
                            segment_data['words'] = [
                                {
                                    'word': word['word'],
                                    'start': word['start'],
                                    'end': word['end'],
                                    'confidence': max(0.1, min(1.0, word.get('probability', 0.7)))
                                }
                                for word in segment['words']
                            ]
                        
                        timestamps.append(segment_data)
                
                if confidences:
                    confidence = sum(confidences) / len(confidences)
            
            transcription_result = TranscriptionResult(
                text=result['text'].strip(),
                confidence=confidence,
                processing_time=processing_time,
                model_used=f"whisper-local-{model_size}-enhanced",
                language=result.get('language', language or 'en')
            )
            
            # Add timestamps if requested
            if enable_timestamps and timestamps:
                transcription_result.timestamps = timestamps
            
            logger.info(f"Enhanced local transcription successful in {processing_time:.2f}s")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Enhanced local transcription failed: {e}")
            raise TranscriptionError(
                message=f"Enhanced local transcription failed: {e}",
                error_code=ErrorCode.LOCAL_MODEL_ERROR,
                user_message="Enhanced offline transcription failed. Please try basic mode.",
                model_used=f"whisper-local-{model_size}-enhanced",
                suggestions=[
                    "Try basic transcription mode",
                    "Use API transcription instead",
                    "Check audio file quality"
                ]
            )

# Global transcriber instance
_transcriber = None

def get_transcriber() -> WhisperTranscriber:
    """Get or create global transcriber instance"""
    global _transcriber
    if _transcriber is None:
        _transcriber = WhisperTranscriber()
    return _transcriber

# Public API functions
def transcribe(audio_path: str, use_api: bool = True) -> str:
    """
    Transcribe audio file to text
    
    Args:
        audio_path: Path to audio file
        use_api: Whether to try API first (True) or use local model (False)
    
    Returns:
        Transcribed text as string
    """
    transcriber = get_transcriber()
    result = transcriber.transcribe(audio_path, use_api)
    return result.text

def transcribe_with_timestamps(audio_path: str) -> List[Dict]:
    """
    Transcribe with word-level timestamps for advanced features
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        List of dictionaries with text, start, and end timestamps
    """
    transcriber = get_transcriber()
    return transcriber.transcribe_with_timestamps(audio_path)

def get_transcription_confidence(audio_path: str) -> float:
    """
    Return confidence score for transcription quality
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    transcriber = get_transcriber()
    return transcriber.get_transcription_confidence(audio_path)

def transcribe_detailed(audio_path: str, use_api: bool = True, model_size: str = "base", 
                      language: str = None, enable_timestamps: bool = False) -> TranscriptionResult:
    """
    Transcribe audio file and return detailed results with enhanced features
    
    Args:
        audio_path: Path to audio file
        use_api: Whether to try API first
        model_size: Local model size for fallback
        language: Language code (e.g., 'en', 'es', 'fr') - None for auto-detection
        enable_timestamps: Whether to include word-level timestamps
    
    Returns:
        TranscriptionResult with detailed metadata
    """
    transcriber = get_transcriber()
    
    # Enhanced transcription with language support
    if language or enable_timestamps:
        return transcriber.transcribe_enhanced(audio_path, use_api, model_size, language, enable_timestamps)
    else:
        return transcriber.transcribe(audio_path, use_api, model_size)