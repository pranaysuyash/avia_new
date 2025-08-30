"""
Test Suite for AI Provider Abstraction Layer

Comprehensive tests for provider abstraction, request/response normalization,
error handling, retry logic, and provider management.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from ai_provider_abstraction import (
    ProviderAbstraction, AIRequest, AIResponse, ProviderConfig,
    RequestType, ProviderType, ProviderStatus, ProviderError, ErrorResolution,
    OpenAIProvider, ElevenLabsProvider, LocalWhisperProvider, LocalSpacyProvider
)

class TestProviderAbstraction:
    """Test cases for Provider Abstraction Layer"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def abstraction(self, temp_db):
        """Create test abstraction instance"""
        return ProviderAbstraction(db_path=temp_db)
    
    @pytest.fixture
    def sample_request(self):
        """Create sample AI request"""
        return AIRequest(
            id="test_req_001",
            type=RequestType.TRANSCRIPTION,
            content="test_audio.wav",
            parameters={"language": "en"}
        )
    
    def test_abstraction_initialization(self, abstraction):
        """Test abstraction layer initialization"""
        assert abstraction is not None
        assert len(abstraction.providers) > 0
        assert os.path.exists(abstraction.db_path)
        
        # Check default providers are loaded
        provider_names = list(abstraction.providers.keys())
        assert "openai" in provider_names
        assert "elevenlabs" in provider_names
        assert "local_whisper" in provider_names
        assert "local_spacy" in provider_names
    
    def test_database_initialization(self, abstraction):
        """Test database tables are created"""
        import sqlite3
        
        conn = sqlite3.connect(abstraction.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "request_history" in tables
        assert "provider_metrics" in tables
        
        conn.close()
    
    @pytest.mark.asyncio
    async def test_basic_request_execution(self, abstraction, sample_request):
        """Test basic request execution"""
        response = await abstraction.execute_request(sample_request)
        
        assert response is not None
        assert response.request_id == sample_request.id
        assert isinstance(response.success, bool)
        assert response.processing_time >= 0
        assert response.provider in abstraction.providers
    
    @pytest.mark.asyncio
    async def test_specific_provider_request(self, abstraction):
        """Test request execution with specific provider"""
        request = AIRequest(
            id="test_specific_001",
            type=RequestType.TRANSCRIPTION,
            content="test_audio.wav"
        )
        
        # Test with OpenAI provider
        response = await abstraction.execute_request(request, "openai")
        
        assert response.success
        assert response.provider == "openai"
        assert "text" in response.result
    
    @pytest.mark.asyncio
    async def test_provider_auto_selection(self, abstraction):
        """Test automatic provider selection"""
        # Test transcription request (multiple providers support this)
        transcription_request = AIRequest(
            id="test_auto_001",
            type=RequestType.TRANSCRIPTION,
            content="test_audio.wav"
        )
        
        response = await abstraction.execute_request(transcription_request)
        assert response.success
        assert response.provider in ["openai", "local_whisper"]
        
        # Test TTS request (only ElevenLabs supports this)
        tts_request = AIRequest(
            id="test_auto_002",
            type=RequestType.TEXT_TO_SPEECH,
            content="Hello world"
        )
        
        response = await abstraction.execute_request(tts_request)
        assert response.success
        assert response.provider == "elevenlabs"
    
    @pytest.mark.asyncio
    async def test_unsupported_request_type(self, abstraction):
        """Test handling of unsupported request types"""
        # Create request with type not supported by any provider
        request = AIRequest(
            id="test_unsupported_001",
            type=RequestType.TRANSLATION,  # Not implemented in test providers
            content="Hello world"
        )
        
        response = await abstraction.execute_request(request)
        assert not response.success
        assert "No suitable provider found" in response.error
    
    @pytest.mark.asyncio
    async def test_invalid_provider_name(self, abstraction, sample_request):
        """Test handling of invalid provider name"""
        response = await abstraction.execute_request(sample_request, "nonexistent_provider")
        
        assert not response.success
        assert "not found" in response.error
    
    def test_provider_registration(self, abstraction):
        """Test provider registration and unregistration"""
        initial_count = len(abstraction.providers)
        
        # Create mock provider
        mock_config = ProviderConfig(provider_type=ProviderType.CUSTOM)
        mock_provider = Mock()
        mock_provider.config = mock_config
        
        # Register provider
        abstraction.register_provider("test_provider", mock_provider)
        assert len(abstraction.providers) == initial_count + 1
        assert "test_provider" in abstraction.providers
        
        # Unregister provider
        abstraction.unregister_provider("test_provider")
        assert len(abstraction.providers) == initial_count
        assert "test_provider" not in abstraction.providers
    
    def test_provider_status_check(self, abstraction):
        """Test provider status checking"""
        # Test existing provider
        status = abstraction.get_provider_status("openai")
        assert status == ProviderStatus.AVAILABLE
        
        # Test non-existent provider
        status = abstraction.get_provider_status("nonexistent")
        assert status is None
    
    def test_provider_configuration(self, abstraction):
        """Test provider configuration update"""
        new_config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="new_test_key",
            max_retries=5,
            timeout=60.0
        )
        
        abstraction.configure_provider("openai", new_config)
        
        # Verify configuration was updated
        provider = abstraction.providers["openai"]
        assert provider.config.api_key == "new_test_key"
        assert provider.config.max_retries == 5
        assert provider.config.timeout == 60.0
    
    def test_provider_metrics(self, abstraction):
        """Test provider metrics collection"""
        metrics = abstraction.get_provider_metrics()
        
        assert isinstance(metrics, dict)
        assert len(metrics) > 0
        
        for provider_name, provider_metrics in metrics.items():
            assert "status" in provider_metrics
            assert "request_count" in provider_metrics
            assert "error_count" in provider_metrics
            assert "error_rate" in provider_metrics
            assert "average_processing_time" in provider_metrics
            assert "supported_types" in provider_metrics
    
    @pytest.mark.asyncio
    async def test_request_history_logging(self, abstraction, sample_request):
        """Test request history logging"""
        initial_history_length = len(abstraction.get_request_history())
        
        await abstraction.execute_request(sample_request)
        
        # Check history was updated
        history = abstraction.get_request_history()
        assert len(history) == initial_history_length + 1
        
        # Check history entry
        latest_entry = history[-1]
        assert latest_entry["request_id"] == sample_request.id
        assert "provider" in latest_entry
        assert "success" in latest_entry
        assert "processing_time" in latest_entry

class TestOpenAIProvider:
    """Test cases for OpenAI provider"""
    
    @pytest.fixture
    def openai_provider(self):
        """Create OpenAI provider instance"""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test_key",
            model_name="gpt-4"
        )
        return OpenAIProvider(config)
    
    def test_supported_types(self, openai_provider):
        """Test OpenAI supported request types"""
        supported = openai_provider.get_supported_types()
        
        assert RequestType.TRANSCRIPTION in supported
        assert RequestType.TEXT_GENERATION in supported
        assert RequestType.SUMMARIZATION in supported
        assert RequestType.TRANSLATION in supported
    
    def test_request_validation(self, openai_provider):
        """Test OpenAI request validation"""
        # Valid transcription request
        valid_request = AIRequest(
            id="test_001",
            type=RequestType.TRANSCRIPTION,
            content="audio.wav"
        )
        assert openai_provider.validate_request(valid_request)
        
        # Invalid request (unsupported type)
        invalid_request = AIRequest(
            id="test_002",
            type=RequestType.TEXT_TO_SPEECH,
            content="text"
        )
        assert not openai_provider.validate_request(invalid_request)
        
        # Invalid request (no content)
        empty_request = AIRequest(
            id="test_003",
            type=RequestType.TRANSCRIPTION,
            content=""
        )
        assert not openai_provider.validate_request(empty_request)
    
    @pytest.mark.asyncio
    async def test_transcription_request(self, openai_provider):
        """Test OpenAI transcription request"""
        request = AIRequest(
            id="test_transcription",
            type=RequestType.TRANSCRIPTION,
            content="test_audio.wav"
        )
        
        response = await openai_provider.execute_request(request)
        
        assert response.success
        assert response.provider == "openai"
        assert "text" in response.result
        assert "language" in response.result
        assert "confidence" in response.result
    
    @pytest.mark.asyncio
    async def test_text_generation_request(self, openai_provider):
        """Test OpenAI text generation request"""
        request = AIRequest(
            id="test_generation",
            type=RequestType.TEXT_GENERATION,
            content="Write a story about AI"
        )
        
        response = await openai_provider.execute_request(request)
        
        assert response.success
        assert response.provider == "openai"
        assert "text" in response.result
        assert "model" in response.result
        assert "tokens_used" in response.result
    
    @pytest.mark.asyncio
    async def test_unsupported_request(self, openai_provider):
        """Test OpenAI unsupported request handling"""
        request = AIRequest(
            id="test_unsupported",
            type=RequestType.TEXT_TO_SPEECH,
            content="Hello world"
        )
        
        response = await openai_provider.execute_request(request)
        
        assert not response.success
        assert "Unsupported request type" in response.error

class TestElevenLabsProvider:
    """Test cases for ElevenLabs provider"""
    
    @pytest.fixture
    def elevenlabs_provider(self):
        """Create ElevenLabs provider instance"""
        config = ProviderConfig(
            provider_type=ProviderType.ELEVENLABS,
            api_key="test_key"
        )
        return ElevenLabsProvider(config)
    
    def test_supported_types(self, elevenlabs_provider):
        """Test ElevenLabs supported request types"""
        supported = elevenlabs_provider.get_supported_types()
        
        assert RequestType.TEXT_TO_SPEECH in supported
        assert len(supported) == 1  # Only supports TTS
    
    @pytest.mark.asyncio
    async def test_text_to_speech_request(self, elevenlabs_provider):
        """Test ElevenLabs TTS request"""
        request = AIRequest(
            id="test_tts",
            type=RequestType.TEXT_TO_SPEECH,
            content="Hello, this is a test message.",
            parameters={"voice_id": "test_voice"}
        )
        
        response = await elevenlabs_provider.execute_request(request)
        
        assert response.success
        assert response.provider == "elevenlabs"
        assert "audio_url" in response.result
        assert "duration" in response.result
        assert "voice_id" in response.result

class TestLocalProviders:
    """Test cases for local providers"""
    
    @pytest.fixture
    def whisper_provider(self):
        """Create local Whisper provider"""
        config = ProviderConfig(
            provider_type=ProviderType.LOCAL_WHISPER,
            parameters={"model_path": "base"}
        )
        return LocalWhisperProvider(config)
    
    @pytest.fixture
    def spacy_provider(self):
        """Create local spaCy provider"""
        config = ProviderConfig(
            provider_type=ProviderType.LOCAL_SPACY,
            model_name="en_core_web_sm"
        )
        return LocalSpacyProvider(config)
    
    @pytest.mark.asyncio
    async def test_local_whisper_transcription(self, whisper_provider):
        """Test local Whisper transcription"""
        request = AIRequest(
            id="test_local_transcription",
            type=RequestType.TRANSCRIPTION,
            content="local_audio.wav"
        )
        
        response = await whisper_provider.execute_request(request)
        
        assert response.success
        assert response.provider == "local_whisper"
        assert response.metadata["local"] is True
        assert response.metadata["privacy"] == "high"
        assert "text" in response.result
    
    @pytest.mark.asyncio
    async def test_spacy_entity_extraction(self, spacy_provider):
        """Test spaCy entity extraction"""
        request = AIRequest(
            id="test_entities",
            type=RequestType.ENTITY_EXTRACTION,
            content="John Doe works at OpenAI in San Francisco."
        )
        
        response = await spacy_provider.execute_request(request)
        
        assert response.success
        assert response.provider == "local_spacy"
        assert "entities" in response.result
        assert len(response.result["entities"]) > 0
    
    @pytest.mark.asyncio
    async def test_spacy_sentiment_analysis(self, spacy_provider):
        """Test spaCy sentiment analysis"""
        request = AIRequest(
            id="test_sentiment",
            type=RequestType.SENTIMENT_ANALYSIS,
            content="I love working with AI technology!"
        )
        
        response = await spacy_provider.execute_request(request)
        
        assert response.success
        assert response.provider == "local_spacy"
        assert "sentiment" in response.result
        assert "confidence" in response.result

class TestErrorHandling:
    """Test cases for error handling and retry logic"""
    
    @pytest.fixture
    def abstraction_with_mock_provider(self, temp_db):
        """Create abstraction with mock provider for error testing"""
        abstraction = ProviderAbstraction(db_path=temp_db)
        
        # Create mock provider that can simulate errors
        mock_provider = Mock()
        mock_provider.config = ProviderConfig(
            provider_type=ProviderType.CUSTOM,
            max_retries=2
        )
        mock_provider.get_supported_types.return_value = [RequestType.TRANSCRIPTION]
        mock_provider.get_status.return_value = ProviderStatus.AVAILABLE
        mock_provider.validate_request.return_value = True
        
        abstraction.register_provider("mock_provider", mock_provider)
        return abstraction, mock_provider
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, abstraction_with_mock_provider):
        """Test retry logic on provider failure"""
        abstraction, mock_provider = abstraction_with_mock_provider
        
        # Mock provider to fail first time, succeed second time
        responses = [
            AIResponse(request_id="test", success=False, error="Temporary failure"),
            AIResponse(request_id="test", success=True, result={"text": "success"})
        ]
        mock_provider.execute_request = AsyncMock(side_effect=responses)
        
        request = AIRequest(
            id="test_retry",
            type=RequestType.TRANSCRIPTION,
            content="test.wav"
        )
        
        response = await abstraction.execute_request(request, "mock_provider")
        
        # Should succeed after retry
        assert response.success
        assert mock_provider.execute_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, abstraction_with_mock_provider):
        """Test behavior when max retries are exceeded"""
        abstraction, mock_provider = abstraction_with_mock_provider
        
        # Mock provider to always fail
        mock_provider.execute_request = AsyncMock(
            return_value=AIResponse(request_id="test", success=False, error="Persistent failure")
        )
        
        request = AIRequest(
            id="test_max_retries",
            type=RequestType.TRANSCRIPTION,
            content="test.wav"
        )
        
        response = await abstraction.execute_request(request, "mock_provider")
        
        # Should fail after max retries
        assert not response.success
        assert mock_provider.execute_request.call_count == 3  # Initial + 2 retries
    
    def test_error_resolution_strategies(self):
        """Test different error resolution strategies"""
        # Test retry resolution
        retry_resolution = ErrorResolution("retry", retry_after=2.0)
        assert retry_resolution.action == "retry"
        assert retry_resolution.retry_after == 2.0
        
        # Test fallback resolution
        fallback_resolution = ErrorResolution("fallback", fallback_provider="backup_provider")
        assert fallback_resolution.action == "fallback"
        assert fallback_resolution.fallback_provider == "backup_provider"
        
        # Test fail resolution
        fail_resolution = ErrorResolution("fail")
        assert fail_resolution.action == "fail"
    
    def test_custom_error_handler_registration(self, abstraction):
        """Test custom error handler registration"""
        def custom_handler(error: ProviderError) -> ErrorResolution:
            return ErrorResolution("retry", retry_after=5.0)
        
        abstraction.register_error_handler("custom_error", custom_handler)
        
        assert "custom_error" in abstraction.error_handlers
        assert abstraction.error_handlers["custom_error"] == custom_handler

class TestProviderMetrics:
    """Test cases for provider metrics and monitoring"""
    
    @pytest.fixture
    def provider_with_metrics(self):
        """Create provider with some metrics"""
        config = ProviderConfig(provider_type=ProviderType.CUSTOM)
        provider = OpenAIProvider(config)
        
        # Simulate some requests
        provider.update_metrics(1.5, True)
        provider.update_metrics(2.0, True)
        provider.update_metrics(1.0, False)
        
        return provider
    
    def test_metrics_calculation(self, provider_with_metrics):
        """Test provider metrics calculation"""
        provider = provider_with_metrics
        
        assert provider.request_count == 3
        assert provider.error_count == 1
        assert provider.get_error_rate() == 1/3
        assert provider.get_average_processing_time() == (1.5 + 2.0 + 1.0) / 3
    
    def test_metrics_aggregation(self, abstraction):
        """Test metrics aggregation across providers"""
        metrics = abstraction.get_provider_metrics()
        
        # Should have metrics for all registered providers
        assert len(metrics) == len(abstraction.providers)
        
        for provider_name, provider_metrics in metrics.items():
            assert isinstance(provider_metrics["request_count"], int)
            assert isinstance(provider_metrics["error_rate"], float)
            assert isinstance(provider_metrics["average_processing_time"], float)
            assert isinstance(provider_metrics["supported_types"], list)

@pytest.mark.asyncio
async def test_concurrent_requests(temp_db):
    """Test concurrent request handling"""
    abstraction = ProviderAbstraction(db_path=temp_db)
    
    # Create multiple concurrent requests
    requests = []
    for i in range(5):
        request = AIRequest(
            id=f"concurrent_req_{i}",
            type=RequestType.TRANSCRIPTION,
            content=f"audio_{i}.wav"
        )
        requests.append(request)
    
    # Execute all requests concurrently
    tasks = [abstraction.execute_request(req) for req in requests]
    responses = await asyncio.gather(*tasks)
    
    # All requests should complete
    assert len(responses) == 5
    for response in responses:
        assert response is not None
        assert isinstance(response.success, bool)

def test_provider_configuration_validation():
    """Test provider configuration validation"""
    # Valid configuration
    valid_config = ProviderConfig(
        provider_type=ProviderType.OPENAI,
        api_key="test_key",
        max_retries=3,
        timeout=30.0
    )
    
    assert valid_config.provider_type == ProviderType.OPENAI
    assert valid_config.api_key == "test_key"
    assert valid_config.max_retries == 3
    assert valid_config.timeout == 30.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])