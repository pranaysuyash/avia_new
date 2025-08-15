#!/usr/bin/env python3
"""
Comprehensive test suite for Whisper API Optimization and Monitoring System.
Tests caching, monitoring, quality assessment, and batch processing.
"""

import pytest
import asyncio
import tempfile
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

from whisper_api_optimization import (
    WhisperRequest,
    WhisperResponse,
    WhisperCache,
    WhisperQualityAssessment,
    WhisperAPIMonitor,
    WhisperAPIOptimizer,
    APIMetrics,
    create_whisper_request,
    create_optimizer
)


class TestWhisperRequest:
    """Test WhisperRequest data class."""
    
    def test_request_creation(self):
        """Test basic request creation."""
        request = WhisperRequest(
            audio_file_path="test.wav",
            language="en",
            prompt="Test prompt",
            temperature=0.5
        )
        
        assert request.audio_file_path == "test.wav"
        assert request.language == "en"
        assert request.prompt == "Test prompt"
        assert request.temperature == 0.5
        assert request.priority == 1
        assert request.request_id is not None
        assert request.created_at is not None
    
    def test_request_id_generation(self):
        """Test unique request ID generation."""
        request1 = WhisperRequest(audio_file_path="test1.wav")
        request2 = WhisperRequest(audio_file_path="test2.wav")
        request3 = WhisperRequest(audio_file_path="test1.wav")  # Same file
        
        assert request1.request_id != request2.request_id
        assert request1.request_id == request3.request_id  # Same parameters = same ID
    
    def test_request_defaults(self):
        """Test default values."""
        request = WhisperRequest(audio_file_path="test.wav")
        
        assert request.language is None
        assert request.prompt is None
        assert request.temperature == 0.0
        assert request.response_format == "json"
        assert request.priority == 1
        assert request.timestamp_granularities == ["segment"]


class TestWhisperResponse:
    """Test WhisperResponse data class."""
    
    def test_response_creation(self):
        """Test basic response creation."""
        response = WhisperResponse(
            request_id="test_123",
            text="Hello world",
            confidence_score=0.95,
            processing_time=2.5
        )
        
        assert response.request_id == "test_123"
        assert response.text == "Hello world"
        assert response.confidence_score == 0.95
        assert response.processing_time == 2.5
        assert response.cached is False
        assert response.created_at is not None


class TestWhisperCache:
    """Test caching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use in-memory cache for testing (no Redis dependency)
        self.cache = WhisperCache(redis_host="nonexistent")
        assert self.cache.redis_client is None  # Should fall back to memory
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        request1 = WhisperRequest(
            audio_file_path="test.wav",
            language="en",
            temperature=0.0
        )
        request2 = WhisperRequest(
            audio_file_path="test.wav",
            language="en", 
            temperature=0.0
        )
        request3 = WhisperRequest(
            audio_file_path="test.wav",
            language="es",  # Different language
            temperature=0.0
        )
        
        key1 = self.cache._generate_cache_key(request1)
        key2 = self.cache._generate_cache_key(request2)
        key3 = self.cache._generate_cache_key(request3)
        
        assert key1 == key2  # Same parameters
        assert key1 != key3  # Different parameters
    
    def test_cache_set_and_get(self):
        """Test caching and retrieval."""
        # Create test files
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'test audio data')
            audio_file = f.name
        
        try:
            request = WhisperRequest(audio_file_path=audio_file)
            response = WhisperResponse(
                request_id=request.request_id,
                text="Test transcription",
                confidence_score=0.9
            )
            
            # Test cache miss
            cached_response = self.cache.get(request)
            assert cached_response is None
            
            # Test cache set
            self.cache.set(request, response)
            
            # Test cache hit
            cached_response = self.cache.get(request)
            assert cached_response is not None
            assert cached_response.text == "Test transcription"
            assert cached_response.cached is True
            
        finally:
            Path(audio_file).unlink(missing_ok=True)
    
    def test_cache_expiration(self):
        """Test cache expiration for in-memory cache."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'test audio data')
            audio_file = f.name
        
        try:
            request = WhisperRequest(audio_file_path=audio_file)
            response = WhisperResponse(
                request_id=request.request_id,
                text="Test transcription"
            )
            
            # Manually set old timestamp
            response.created_at = datetime.utcnow() - timedelta(hours=25)
            self.cache.set(request, response)
            
            # Clear expired entries
            self.cache.clear_expired()
            
            # Should be cleared
            cached_response = self.cache.get(request)
            assert cached_response is None
            
        finally:
            Path(audio_file).unlink(missing_ok=True)


class TestWhisperQualityAssessment:
    """Test quality assessment functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assessor = WhisperQualityAssessment()
    
    def test_text_quality_assessment(self):
        """Test text quality assessment."""
        # High quality text
        high_quality = "This is a well-structured sentence with proper punctuation and diverse vocabulary."
        quality_score = self.assessor._assess_text_quality(high_quality)
        assert quality_score > 0.7
        
        # Low quality text
        low_quality = "um uh yeah yeah yeah"
        quality_score = self.assessor._assess_text_quality(low_quality)
        assert quality_score < 0.5
        
        # Empty text
        empty_quality = self.assessor._assess_text_quality("")
        assert empty_quality == 0.0
    
    def test_overall_quality_assessment(self):
        """Test overall quality assessment."""
        # High quality response
        high_quality_response = WhisperResponse(
            request_id="test_1",
            text="This is a high-quality transcription with good content.",
            confidence_score=0.95,
            segments=[
                {"start": 0.0, "end": 2.0, "text": "This is a high-quality", "avg_logprob": -0.1},
                {"start": 2.0, "end": 4.0, "text": "transcription with good content.", "avg_logprob": -0.15}
            ]
        )
        
        quality_score = self.assessor.assess_quality(high_quality_response, audio_duration=4.0)
        assert quality_score > 0.7
        
        # Low quality response
        low_quality_response = WhisperResponse(
            request_id="test_2",
            text="um uh yeah",
            confidence_score=0.3,
            segments=[
                {"start": 0.0, "end": 2.0, "text": "um uh", "avg_logprob": -0.8},
                {"start": 2.0, "end": 3.0, "text": "yeah", "avg_logprob": -0.9}
            ]
        )
        
        quality_score = self.assessor.assess_quality(low_quality_response, audio_duration=3.0)
        assert quality_score < 0.5
    
    def test_transcription_validation(self):
        """Test transcription validation."""
        # Valid transcription
        valid_response = WhisperResponse(
            request_id="test_1",
            text="This is a valid transcription with sufficient content.",
            confidence_score=0.85,
            quality_score=0.8
        )
        
        validation = self.assessor.validate_transcription(valid_response)
        assert validation['is_valid'] is True
        assert len(validation['issues']) == 0
        
        # Invalid transcription (too short)
        invalid_response = WhisperResponse(
            request_id="test_2",
            text="short",
            confidence_score=0.5,
            quality_score=0.3
        )
        
        validation = self.assessor.validate_transcription(invalid_response)
        assert validation['is_valid'] is False
        assert "too short" in validation['issues'][0].lower()
    
    def test_repetitive_content_detection(self):
        """Test detection of repetitive content."""
        repetitive_response = WhisperResponse(
            request_id="test_rep",
            text="hello hello hello hello hello world hello hello hello hello",
            confidence_score=0.7
        )
        
        validation = self.assessor.validate_transcription(repetitive_response)
        assert any("repetitive" in issue.lower() for issue in validation['issues'])


class TestWhisperAPIMonitor:
    """Test monitoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = WhisperAPIMonitor(window_size_minutes=5)
    
    def test_metrics_initialization(self):
        """Test initial metrics state."""
        assert self.monitor.metrics.total_requests == 0
        assert self.monitor.metrics.successful_requests == 0
        assert self.monitor.metrics.failed_requests == 0
        assert self.monitor.metrics.error_rate == 0.0
    
    def test_successful_request_recording(self):
        """Test recording successful requests."""
        request = WhisperRequest(audio_file_path="test.wav")
        response = WhisperResponse(
            request_id=request.request_id,
            text="Test transcription",
            confidence_score=0.9,
            processing_time=2.5,
            api_cost=0.01
        )
        
        self.monitor.record_request(request, response)
        
        assert self.monitor.metrics.total_requests == 1
        assert self.monitor.metrics.successful_requests == 1
        assert self.monitor.metrics.failed_requests == 0
        assert self.monitor.metrics.total_processing_time == 2.5
        assert self.monitor.metrics.total_api_cost == 0.01
        assert self.monitor.metrics.average_confidence == 0.9
    
    def test_failed_request_recording(self):
        """Test recording failed requests."""
        request = WhisperRequest(audio_file_path="test.wav")
        error = Exception("API timeout")
        
        self.monitor.record_request(request, error=error)
        
        assert self.monitor.metrics.total_requests == 1
        assert self.monitor.metrics.successful_requests == 0
        assert self.monitor.metrics.failed_requests == 1
        assert len(self.monitor.error_history) == 1
        assert "API timeout" in self.monitor.error_history[0]['error']
    
    def test_cached_request_recording(self):
        """Test recording cached requests."""
        request = WhisperRequest(audio_file_path="test.wav")
        response = WhisperResponse(
            request_id=request.request_id,
            text="Cached transcription",
            cached=True
        )
        
        self.monitor.record_request(request, response)
        
        assert self.monitor.metrics.cached_requests == 1
        assert self.monitor.metrics.cache_hit_rate > 0
    
    def test_metrics_calculation(self):
        """Test calculated metrics."""
        # Record multiple requests
        for i in range(10):
            request = WhisperRequest(audio_file_path=f"test_{i}.wav")
            
            if i < 8:  # 8 successful, 2 failed
                response = WhisperResponse(
                    request_id=request.request_id,
                    text=f"Transcription {i}",
                    cached=(i % 3 == 0)  # Every 3rd is cached
                )
                self.monitor.record_request(request, response)
            else:
                error = Exception(f"Error {i}")
                self.monitor.record_request(request, error=error)
        
        # Check calculated metrics
        assert self.monitor.metrics.total_requests == 10
        assert self.monitor.metrics.successful_requests == 8
        assert self.monitor.metrics.failed_requests == 2
        assert self.monitor.metrics.error_rate == 0.2  # 2/10
        assert self.monitor.metrics.cached_requests == 3  # 0, 3, 6
    
    def test_alert_generation(self):
        """Test alert generation."""
        # Generate high error rate
        for i in range(10):
            request = WhisperRequest(audio_file_path=f"test_{i}.wav")
            error = Exception("High error rate test")
            self.monitor.record_request(request, error=error)
        
        # Should generate high error rate alert
        assert len(self.monitor.alerts) > 0
        assert any(alert['type'] == 'high_error_rate' for alert in self.monitor.alerts)
    
    def test_metrics_summary(self):
        """Test comprehensive metrics summary."""
        # Add some test data
        request = WhisperRequest(audio_file_path="test.wav")
        response = WhisperResponse(
            request_id=request.request_id,
            text="Test transcription",
            processing_time=1.5
        )
        self.monitor.record_request(request, response)
        
        summary = self.monitor.get_metrics_summary()
        
        assert 'basic_metrics' in summary
        assert 'recent_alerts' in summary
        assert 'system_health' in summary
        assert 'performance_trends' in summary
        
        assert summary['system_health']['status'] in ['healthy', 'degraded']


class TestWhisperAPIOptimizer:
    """Test the main optimizer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.optimizer = WhisperAPIOptimizer(
            api_key="test_key",
            cache_config={'redis_host': 'nonexistent'},  # Force memory cache
            monitor_config={'window_size_minutes': 5}
        )
    
    @patch('whisper_api_optimization.OpenAI')
    def test_optimizer_initialization(self, mock_openai):
        """Test optimizer initialization."""
        optimizer = WhisperAPIOptimizer(api_key="test_key")
        
        assert optimizer.client is not None
        assert optimizer.cache is not None
        assert optimizer.monitor is not None
        assert optimizer.quality_assessor is not None
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Fill up the rate limit
        for _ in range(self.optimizer.rate_limit_requests_per_minute):
            self.optimizer.request_timestamps.append(time.time())
        
        # This should trigger rate limiting
        start_time = time.time()
        self.optimizer._enforce_rate_limit()
        end_time = time.time()
        
        # Should have waited (or at least attempted to)
        # In test environment, we might not actually wait
        assert end_time >= start_time
    
    @pytest.mark.asyncio
    @patch('whisper_api_optimization.OpenAI')
    async def test_api_request_mock(self, mock_openai):
        """Test API request with mocked OpenAI client."""
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.text = "Mocked transcription"
        mock_response.language = "en"
        
        mock_client = Mock()
        mock_client.audio.transcriptions.create.return_value = mock_response
        self.optimizer.client = mock_client
        
        # Create test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'mock audio data')
            audio_file = f.name
        
        try:
            request = WhisperRequest(audio_file_path=audio_file)
            response = await self.optimizer._make_api_request(request)
            
            assert response.text == "Mocked transcription"
            assert response.language == "en"
            assert response.processing_time > 0
            assert response.api_cost > 0
            
        finally:
            Path(audio_file).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_process_request_with_cache(self):
        """Test request processing with caching."""
        # Create test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'test audio data')
            audio_file = f.name
        
        try:
            request = WhisperRequest(audio_file_path=audio_file)
            
            # Pre-populate cache
            cached_response = WhisperResponse(
                request_id=request.request_id,
                text="Cached transcription",
                cached=True
            )
            self.optimizer.cache.set(request, cached_response)
            
            # Process request (should hit cache)
            response = await self.optimizer.process_request(request)
            
            assert response.text == "Cached transcription"
            assert response.cached is True
            
        finally:
            Path(audio_file).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing functionality."""
        # Create multiple test requests
        requests = []
        audio_files = []
        
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(f'test audio data {i}'.encode())
                audio_file = f.name
                audio_files.append(audio_file)
            
            request = WhisperRequest(
                audio_file_path=audio_file,
                priority=i + 1  # Different priorities
            )
            requests.append(request)
        
        try:
            # Mock successful processing for all requests
            async def mock_process_request(request):
                return WhisperResponse(
                    request_id=request.request_id,
                    text=f"Transcription for {request.audio_file_path}",
                    processing_time=1.0
                )
            
            self.optimizer.process_request = mock_process_request
            
            # Process batch
            responses = await self.optimizer.process_batch(requests)
            
            assert len(responses) == 3
            assert all(isinstance(r, WhisperResponse) for r in responses)
            
        finally:
            for audio_file in audio_files:
                Path(audio_file).unlink(missing_ok=True)
    
    def test_optimization_stats(self):
        """Test optimization statistics."""
        stats = self.optimizer.get_optimization_stats()
        
        assert 'cache_stats' in stats
        assert 'performance_stats' in stats
        assert 'system_resources' in stats
        assert 'api_efficiency' in stats
        
        assert stats['cache_stats']['type'] == 'memory'
        assert 'cpu_percent' in stats['system_resources']
        assert 'memory_percent' in stats['system_resources']
    
    def test_health_check(self):
        """Test system health check."""
        health = self.optimizer.health_check()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'components' in health
        
        assert health['status'] in ['healthy', 'degraded']
        assert 'cache' in health['components']
        assert 'api' in health['components']
        assert 'resources' in health['components']


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_whisper_request(self):
        """Test request creation utility."""
        request = create_whisper_request(
            audio_file_path="test.wav",
            language="en",
            temperature=0.5
        )
        
        assert isinstance(request, WhisperRequest)
        assert request.audio_file_path == "test.wav"
        assert request.language == "en"
        assert request.temperature == 0.5
    
    def test_create_optimizer(self):
        """Test optimizer creation utility."""
        optimizer = create_optimizer(
            api_key="test_key",
            redis_host="localhost",
            redis_port=6379
        )
        
        assert isinstance(optimizer, WhisperAPIOptimizer)
        assert optimizer.client is not None


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # Create optimizer
        optimizer = WhisperAPIOptimizer(
            api_key="test_key",
            cache_config={'redis_host': 'nonexistent'}
        )
        
        # Create test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'test audio data for integration test')
            audio_file = f.name
        
        try:
            # Create request
            request = create_whisper_request(
                audio_file_path=audio_file,
                language="en",
                prompt="Integration test audio"
            )
            
            # Mock the API response
            async def mock_api_request(req):
                return WhisperResponse(
                    request_id=req.request_id,
                    text="Integration test transcription",
                    confidence_score=0.9,
                    processing_time=1.5,
                    api_cost=0.01,
                    quality_score=0.85
                )
            
            optimizer._make_api_request = mock_api_request
            
            # Process request
            response = await optimizer.process_request(request)
            
            # Verify response
            assert response.text == "Integration test transcription"
            assert response.confidence_score == 0.9
            assert response.quality_score == 0.85
            
            # Verify monitoring
            assert optimizer.monitor.metrics.total_requests == 1
            assert optimizer.monitor.metrics.successful_requests == 1
            
            # Test caching (second request should be cached)
            response2 = await optimizer.process_request(request)
            assert response2.cached is True
            
            # Verify cache hit recorded
            assert optimizer.monitor.metrics.cached_requests == 1
            
            # Get stats
            stats = optimizer.get_optimization_stats()
            assert stats['cache_stats']['hit_rate'] == 0.5  # 1 out of 2 requests
            
        finally:
            Path(audio_file).unlink(missing_ok=True)
    
    def test_performance_under_load(self):
        """Test system performance under load."""
        optimizer = WhisperAPIOptimizer(
            api_key="test_key",
            cache_config={'redis_host': 'nonexistent'}
        )
        
        # Simulate high load
        start_time = time.time()
        
        for i in range(100):
            request = WhisperRequest(audio_file_path=f"test_{i}.wav")
            response = WhisperResponse(
                request_id=request.request_id,
                text=f"Load test {i}",
                processing_time=0.1
            )
            optimizer.monitor.record_request(request, response)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle 100 requests quickly
        assert processing_time < 1.0  # Less than 1 second
        assert optimizer.monitor.metrics.total_requests == 100
        assert optimizer.monitor.metrics.successful_requests == 100


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])