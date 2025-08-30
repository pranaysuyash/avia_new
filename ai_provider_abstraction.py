"""
AI Provider Abstraction Layer

This module provides a unified interface for all AI providers including OpenAI, ElevenLabs,
and local models. It handles request/response normalization, provider-specific optimization,
and comprehensive error handling with retry logic.
"""

import asyncio
import logging
import time
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProviderType(Enum):
    """AI Provider Types"""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    LOCAL_WHISPER = "local_whisper"
    LOCAL_SPACY = "local_spacy"
    CUSTOM = "custom"

class RequestType(Enum):
    """AI Request Types"""
    TRANSCRIPTION = "transcription"
    TEXT_TO_SPEECH = "text_to_speech"
    TEXT_GENERATION = "text_generation"
    TRANSLATION = "translation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    SUMMARIZATION = "summarization"

class ProviderStatus(Enum):
    """Provider Status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

@dataclass
class AIRequest:
    """Standardized AI request"""
    id: str
    type: RequestType
    content: Any
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    priority: int = 1  # 1 = highest priority
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AIResponse:
    """Standardized AI response"""
    request_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    provider: str = ""
    model: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ProviderConfig:
    """Provider configuration"""
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    max_retries: int = 3
    timeout: float = 30.0
    rate_limit: Optional[int] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderError:
    """Provider error information"""
    provider: str
    error_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    retryable: bool = True

class ErrorResolution:
    """Error resolution strategy"""
    def __init__(self, action: str, retry_after: float = 0.0, fallback_provider: Optional[str] = None):
        self.action = action  # "retry", "fallback", "fail"
        self.retry_after = retry_after
        self.fallback_provider = fallback_provider

class BaseProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.status = ProviderStatus.AVAILABLE
        self.last_error: Optional[ProviderError] = None
        self.request_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        
    @abstractmethod
    async def execute_request(self, request: AIRequest) -> AIResponse:
        """Execute AI request"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[RequestType]:
        """Get supported request types"""
        pass
    
    @abstractmethod
    def validate_request(self, request: AIRequest) -> bool:
        """Validate request for this provider"""
        pass
    
    def get_status(self) -> ProviderStatus:
        """Get provider status"""
        return self.status
    
    def update_metrics(self, processing_time: float, success: bool):
        """Update provider metrics"""
        self.request_count += 1
        self.total_processing_time += processing_time
        if not success:
            self.error_count += 1
    
    def get_error_rate(self) -> float:
        """Get error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def get_average_processing_time(self) -> float:
        """Get average processing time"""
        if self.request_count == 0:
            return 0.0
        return self.total_processing_time / self.request_count

class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        
    async def execute_request(self, request: AIRequest) -> AIResponse:
        """Execute OpenAI request"""
        start_time = time.time()
        
        try:
            if request.type == RequestType.TRANSCRIPTION:
                result = await self._transcribe_audio(request)
            elif request.type == RequestType.TEXT_GENERATION:
                result = await self._generate_text(request)
            elif request.type == RequestType.SUMMARIZATION:
                result = await self._summarize_text(request)
            else:
                raise ValueError(f"Unsupported request type: {request.type}")
            
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, True)
            
            return AIResponse(
                request_id=request.id,
                success=True,
                result=result,
                processing_time=processing_time,
                provider="openai",
                model=self.config.model_name or "default",
                metadata={"api_version": "v1"}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, False)
            
            error_msg = str(e)
            logger.error(f"OpenAI request failed: {error_msg}")
            
            return AIResponse(
                request_id=request.id,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                provider="openai",
                model=self.config.model_name or "default"
            )
    
    async def _transcribe_audio(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate OpenAI Whisper transcription"""
        # In real implementation, this would call OpenAI API
        await asyncio.sleep(0.1)  # Simulate API call
        
        return {
            "text": f"Transcribed audio content from {request.content}",
            "language": "en",
            "confidence": 0.95,
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Sample transcription segment"}
            ]
        }
    
    async def _generate_text(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate OpenAI GPT text generation"""
        await asyncio.sleep(0.2)  # Simulate API call
        
        return {
            "text": f"Generated response for: {request.content}",
            "model": "gpt-4",
            "tokens_used": 150,
            "finish_reason": "stop"
        }
    
    async def _summarize_text(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate OpenAI text summarization"""
        await asyncio.sleep(0.15)  # Simulate API call
        
        return {
            "summary": f"Summary of: {str(request.content)[:100]}...",
            "original_length": len(str(request.content)),
            "summary_length": 50,
            "compression_ratio": 0.5
        }
    
    def get_supported_types(self) -> List[RequestType]:
        """Get supported request types"""
        return [
            RequestType.TRANSCRIPTION,
            RequestType.TEXT_GENERATION,
            RequestType.SUMMARIZATION,
            RequestType.TRANSLATION
        ]
    
    def validate_request(self, request: AIRequest) -> bool:
        """Validate OpenAI request"""
        if not self.api_key:
            return False
        
        if request.type not in self.get_supported_types():
            return False
        
        if request.type == RequestType.TRANSCRIPTION and not request.content:
            return False
        
        return True

class ElevenLabsProvider(BaseProvider):
    """ElevenLabs provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("ELEVENLABS_API_KEY")
    
    async def execute_request(self, request: AIRequest) -> AIResponse:
        """Execute ElevenLabs request"""
        start_time = time.time()
        
        try:
            if request.type == RequestType.TEXT_TO_SPEECH:
                result = await self._text_to_speech(request)
            else:
                raise ValueError(f"Unsupported request type: {request.type}")
            
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, True)
            
            return AIResponse(
                request_id=request.id,
                success=True,
                result=result,
                processing_time=processing_time,
                provider="elevenlabs",
                model=self.config.model_name or "eleven_monolingual_v1",
                metadata={"voice_id": request.parameters.get("voice_id", "default")}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, False)
            
            error_msg = str(e)
            logger.error(f"ElevenLabs request failed: {error_msg}")
            
            return AIResponse(
                request_id=request.id,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                provider="elevenlabs"
            )
    
    async def _text_to_speech(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate ElevenLabs TTS"""
        await asyncio.sleep(0.3)  # Simulate API call
        
        return {
            "audio_url": f"https://api.elevenlabs.io/audio/{request.id}.mp3",
            "audio_data": b"fake_audio_data",
            "duration": 5.2,
            "voice_id": request.parameters.get("voice_id", "default"),
            "model": "eleven_monolingual_v1"
        }
    
    def get_supported_types(self) -> List[RequestType]:
        """Get supported request types"""
        return [RequestType.TEXT_TO_SPEECH]
    
    def validate_request(self, request: AIRequest) -> bool:
        """Validate ElevenLabs request"""
        if not self.api_key:
            return False
        
        if request.type != RequestType.TEXT_TO_SPEECH:
            return False
        
        if not request.content or not isinstance(request.content, str):
            return False
        
        return True

class LocalWhisperProvider(BaseProvider):
    """Local Whisper provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.model_path = config.parameters.get("model_path", "base")
    
    async def execute_request(self, request: AIRequest) -> AIResponse:
        """Execute local Whisper request"""
        start_time = time.time()
        
        try:
            if request.type == RequestType.TRANSCRIPTION:
                result = await self._transcribe_local(request)
            else:
                raise ValueError(f"Unsupported request type: {request.type}")
            
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, True)
            
            return AIResponse(
                request_id=request.id,
                success=True,
                result=result,
                processing_time=processing_time,
                provider="local_whisper",
                model=self.model_path,
                metadata={"local": True, "privacy": "high"}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, False)
            
            error_msg = str(e)
            logger.error(f"Local Whisper request failed: {error_msg}")
            
            return AIResponse(
                request_id=request.id,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                provider="local_whisper"
            )
    
    async def _transcribe_local(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate local Whisper transcription"""
        await asyncio.sleep(0.5)  # Simulate local processing
        
        return {
            "text": f"Local transcription of {request.content}",
            "language": "en",
            "confidence": 0.88,
            "model": self.model_path,
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Local transcription segment"}
            ]
        }
    
    def get_supported_types(self) -> List[RequestType]:
        """Get supported request types"""
        return [RequestType.TRANSCRIPTION]
    
    def validate_request(self, request: AIRequest) -> bool:
        """Validate local Whisper request"""
        if request.type != RequestType.TRANSCRIPTION:
            return False
        
        if not request.content:
            return False
        
        return True

class LocalSpacyProvider(BaseProvider):
    """Local spaCy provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.model_name = config.model_name or "en_core_web_sm"
    
    async def execute_request(self, request: AIRequest) -> AIResponse:
        """Execute local spaCy request"""
        start_time = time.time()
        
        try:
            if request.type == RequestType.ENTITY_EXTRACTION:
                result = await self._extract_entities(request)
            elif request.type == RequestType.SENTIMENT_ANALYSIS:
                result = await self._analyze_sentiment(request)
            else:
                raise ValueError(f"Unsupported request type: {request.type}")
            
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, True)
            
            return AIResponse(
                request_id=request.id,
                success=True,
                result=result,
                processing_time=processing_time,
                provider="local_spacy",
                model=self.model_name,
                metadata={"local": True, "privacy": "high"}
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.update_metrics(processing_time, False)
            
            error_msg = str(e)
            logger.error(f"Local spaCy request failed: {error_msg}")
            
            return AIResponse(
                request_id=request.id,
                success=False,
                error=error_msg,
                processing_time=processing_time,
                provider="local_spacy"
            )
    
    async def _extract_entities(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate spaCy entity extraction"""
        await asyncio.sleep(0.05)  # Simulate local processing
        
        return {
            "entities": [
                {"text": "John Doe", "label": "PERSON", "start": 0, "end": 8},
                {"text": "New York", "label": "GPE", "start": 20, "end": 28}
            ],
            "model": self.model_name,
            "confidence_scores": [0.95, 0.92]
        }
    
    async def _analyze_sentiment(self, request: AIRequest) -> Dict[str, Any]:
        """Simulate spaCy sentiment analysis"""
        await asyncio.sleep(0.03)  # Simulate local processing
        
        return {
            "sentiment": "positive",
            "confidence": 0.85,
            "polarity": 0.7,
            "subjectivity": 0.6,
            "model": self.model_name
        }
    
    def get_supported_types(self) -> List[RequestType]:
        """Get supported request types"""
        return [
            RequestType.ENTITY_EXTRACTION,
            RequestType.SENTIMENT_ANALYSIS
        ]
    
    def validate_request(self, request: AIRequest) -> bool:
        """Validate spaCy request"""
        if request.type not in self.get_supported_types():
            return False
        
        if not request.content or not isinstance(request.content, str):
            return False
        
        return True

class ProviderAbstraction:
    """
    Main Provider Abstraction Layer
    
    Provides unified interface for all AI providers with request/response normalization,
    provider-specific optimization, and comprehensive error handling.
    """
    
    def __init__(self, db_path: str = "provider_abstraction.db"):
        self.db_path = db_path
        self.providers: Dict[str, BaseProvider] = {}
        self.request_history: List[Dict] = []
        self.error_handlers: Dict[str, Callable] = {}
        
        # Initialize database
        self._init_database()
        
        # Load default providers
        self._load_default_providers()
        
        logger.info("Provider Abstraction Layer initialized")
    
    def _init_database(self):
        """Initialize SQLite database for request history and metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Request history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                provider TEXT,
                request_type TEXT,
                success BOOLEAN,
                processing_time REAL,
                error_message TEXT,
                timestamp TIMESTAMP
            )
        """)
        
        # Provider metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_metrics (
                provider TEXT PRIMARY KEY,
                total_requests INTEGER,
                successful_requests INTEGER,
                total_processing_time REAL,
                last_updated TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_default_providers(self):
        """Load default AI providers"""
        # OpenAI provider
        openai_config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            model_name="gpt-4",
            max_retries=3,
            timeout=30.0
        )
        self.register_provider("openai", OpenAIProvider(openai_config))
        
        # ElevenLabs provider
        elevenlabs_config = ProviderConfig(
            provider_type=ProviderType.ELEVENLABS,
            model_name="eleven_monolingual_v1",
            max_retries=2,
            timeout=20.0
        )
        self.register_provider("elevenlabs", ElevenLabsProvider(elevenlabs_config))
        
        # Local Whisper provider
        whisper_config = ProviderConfig(
            provider_type=ProviderType.LOCAL_WHISPER,
            parameters={"model_path": "base"},
            max_retries=1,
            timeout=60.0
        )
        self.register_provider("local_whisper", LocalWhisperProvider(whisper_config))
        
        # Local spaCy provider
        spacy_config = ProviderConfig(
            provider_type=ProviderType.LOCAL_SPACY,
            model_name="en_core_web_sm",
            max_retries=1,
            timeout=10.0
        )
        self.register_provider("local_spacy", LocalSpacyProvider(spacy_config))
        
        logger.info(f"Loaded {len(self.providers)} default providers")
    
    def register_provider(self, name: str, provider: BaseProvider):
        """Register a new provider"""
        self.providers[name] = provider
        logger.info(f"Registered provider: {name}")
    
    def unregister_provider(self, name: str):
        """Unregister a provider"""
        if name in self.providers:
            del self.providers[name]
            logger.info(f"Unregistered provider: {name}")
    
    async def execute_request(self, request: AIRequest, provider_name: Optional[str] = None) -> AIResponse:
        """
        Execute AI request with automatic provider selection or specific provider
        
        Args:
            request: Standardized AI request
            provider_name: Optional specific provider name
            
        Returns:
            AIResponse with result or error information
        """
        try:
            # Select provider
            if provider_name:
                if provider_name not in self.providers:
                    return AIResponse(
                        request_id=request.id,
                        success=False,
                        error=f"Provider '{provider_name}' not found"
                    )
                provider = self.providers[provider_name]
            else:
                provider = self._select_best_provider(request)
                if not provider:
                    return AIResponse(
                        request_id=request.id,
                        success=False,
                        error="No suitable provider found"
                    )
                provider_name = self._get_provider_name(provider)
            
            # Validate request
            if not provider.validate_request(request):
                return AIResponse(
                    request_id=request.id,
                    success=False,
                    error=f"Request validation failed for provider '{provider_name}'"
                )
            
            # Execute with retry logic
            response = await self._execute_with_retry(provider, request, provider_name)
            
            # Log request
            await self._log_request(request, response, provider_name)
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing request: {str(e)}")
            return AIResponse(
                request_id=request.id,
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    def _select_best_provider(self, request: AIRequest) -> Optional[BaseProvider]:
        """Select the best provider for a request"""
        suitable_providers = []
        
        for name, provider in self.providers.items():
            if (request.type in provider.get_supported_types() and
                provider.get_status() == ProviderStatus.AVAILABLE and
                provider.validate_request(request)):
                suitable_providers.append((name, provider))
        
        if not suitable_providers:
            return None
        
        # Sort by error rate and average processing time
        suitable_providers.sort(key=lambda x: (
            x[1].get_error_rate(),
            x[1].get_average_processing_time()
        ))
        
        return suitable_providers[0][1]
    
    def _get_provider_name(self, provider: BaseProvider) -> str:
        """Get provider name from provider instance"""
        for name, p in self.providers.items():
            if p is provider:
                return name
        return "unknown"
    
    async def _execute_with_retry(self, provider: BaseProvider, request: AIRequest, provider_name: str) -> AIResponse:
        """Execute request with retry logic"""
        max_retries = provider.config.max_retries
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                response = await provider.execute_request(request)
                
                if response.success:
                    return response
                
                # Handle error
                error_resolution = self._handle_provider_error(
                    ProviderError(
                        provider=provider_name,
                        error_type="execution_error",
                        message=response.error or "Unknown error"
                    )
                )
                
                if error_resolution.action == "retry" and retry_count < max_retries:
                    retry_count += 1
                    if error_resolution.retry_after > 0:
                        await asyncio.sleep(error_resolution.retry_after)
                    logger.info(f"Retrying request {request.id} (attempt {retry_count})")
                    continue
                elif error_resolution.action == "fallback" and error_resolution.fallback_provider:
                    # Try fallback provider
                    fallback_provider = self.providers.get(error_resolution.fallback_provider)
                    if fallback_provider and fallback_provider.validate_request(request):
                        logger.info(f"Falling back to provider: {error_resolution.fallback_provider}")
                        return await fallback_provider.execute_request(request)
                
                return response
                
            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = min(2 ** retry_count, 10)  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    logger.info(f"Retrying request {request.id} after error (attempt {retry_count})")
                else:
                    return AIResponse(
                        request_id=request.id,
                        success=False,
                        error=f"Max retries exceeded: {str(e)}",
                        provider=provider_name
                    )
        
        return AIResponse(
            request_id=request.id,
            success=False,
            error="Max retries exceeded",
            provider=provider_name
        )
    
    def _handle_provider_error(self, error: ProviderError) -> ErrorResolution:
        """Handle provider error and determine resolution strategy"""
        # Check for custom error handler
        if error.error_type in self.error_handlers:
            return self.error_handlers[error.error_type](error)
        
        # Default error handling logic
        if "rate limit" in error.message.lower():
            return ErrorResolution("retry", retry_after=5.0)
        elif "timeout" in error.message.lower():
            return ErrorResolution("retry", retry_after=2.0)
        elif "unavailable" in error.message.lower():
            # Try to find fallback provider
            fallback = self._find_fallback_provider(error.provider)
            if fallback:
                return ErrorResolution("fallback", fallback_provider=fallback)
        
        return ErrorResolution("retry", retry_after=1.0)
    
    def _find_fallback_provider(self, failed_provider: str) -> Optional[str]:
        """Find suitable fallback provider"""
        for name, provider in self.providers.items():
            if (name != failed_provider and 
                provider.get_status() == ProviderStatus.AVAILABLE and
                provider.get_error_rate() < 0.5):
                return name
        return None
    
    async def _log_request(self, request: AIRequest, response: AIResponse, provider_name: str):
        """Log request to database and memory"""
        request_record = {
            "request_id": request.id,
            "provider": provider_name,
            "request_type": request.type.value,
            "success": response.success,
            "processing_time": response.processing_time,
            "error_message": response.error,
            "timestamp": datetime.now().isoformat()
        }
        
        self.request_history.append(request_record)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO request_history 
            (request_id, provider, request_type, success, processing_time, error_message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request_record["request_id"],
            request_record["provider"],
            request_record["request_type"],
            request_record["success"],
            request_record["processing_time"],
            request_record["error_message"],
            request_record["timestamp"]
        ))
        conn.commit()
        conn.close()
    
    def get_provider_status(self, provider_name: str) -> Optional[ProviderStatus]:
        """Get provider status"""
        if provider_name in self.providers:
            return self.providers[provider_name].get_status()
        return None
    
    def configure_provider(self, provider_name: str, config: ProviderConfig):
        """Configure existing provider"""
        if provider_name in self.providers:
            self.providers[provider_name].config = config
            logger.info(f"Updated configuration for provider: {provider_name}")
    
    def register_error_handler(self, error_type: str, handler: Callable[[ProviderError], ErrorResolution]):
        """Register custom error handler"""
        self.error_handlers[error_type] = handler
        logger.info(f"Registered error handler for: {error_type}")
    
    def get_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all providers"""
        metrics = {}
        
        for name, provider in self.providers.items():
            metrics[name] = {
                "status": provider.get_status().value,
                "request_count": provider.request_count,
                "error_count": provider.error_count,
                "error_rate": provider.get_error_rate(),
                "average_processing_time": provider.get_average_processing_time(),
                "supported_types": [t.value for t in provider.get_supported_types()]
            }
        
        return metrics
    
    def get_request_history(self, limit: int = 100) -> List[Dict]:
        """Get recent request history"""
        return self.request_history[-limit:]

# Example usage and testing
async def main():
    """Example usage of the Provider Abstraction Layer"""
    abstraction = ProviderAbstraction()
    
    # Test different request types
    requests = [
        AIRequest(
            id="req_001",
            type=RequestType.TRANSCRIPTION,
            content="audio_file.wav",
            parameters={"language": "en"}
        ),
        AIRequest(
            id="req_002",
            type=RequestType.TEXT_TO_SPEECH,
            content="Hello, this is a test message.",
            parameters={"voice_id": "default"}
        ),
        AIRequest(
            id="req_003",
            type=RequestType.ENTITY_EXTRACTION,
            content="John Doe works at OpenAI in San Francisco."
        ),
        AIRequest(
            id="req_004",
            type=RequestType.TEXT_GENERATION,
            content="Write a short story about AI.",
            parameters={"max_tokens": 100}
        )
    ]
    
    print("🤖 Provider Abstraction Layer Demo")
    print("=" * 40)
    
    # Execute requests
    for request in requests:
        print(f"\n📋 Executing {request.type.value} request...")
        
        response = await abstraction.execute_request(request)
        
        if response.success:
            print(f"✅ Success - Provider: {response.provider}")
            print(f"   Processing time: {response.processing_time:.3f}s")
            print(f"   Result: {str(response.result)[:100]}...")
        else:
            print(f"❌ Failed - Error: {response.error}")
    
    # Show provider metrics
    print(f"\n📊 Provider Metrics:")
    metrics = abstraction.get_provider_metrics()
    
    for provider_name, provider_metrics in metrics.items():
        print(f"\n{provider_name}:")
        print(f"  Status: {provider_metrics['status']}")
        print(f"  Requests: {provider_metrics['request_count']}")
        print(f"  Error Rate: {provider_metrics['error_rate']:.3f}")
        print(f"  Avg Time: {provider_metrics['average_processing_time']:.3f}s")
        print(f"  Supported: {', '.join(provider_metrics['supported_types'])}")

if __name__ == "__main__":
    asyncio.run(main())