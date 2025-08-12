#!/usr/bin/env python3
"""
Unit Tests for Cloud-Local Model Integration
Tests fallback mechanisms, provider management, and integration logic
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from cloud_local_model_integration import (
    ModelProvider,
    ProcessingStatus,
    ProcessingResult,
    ProviderConfig,
    CloudModelProvider,
    OpenAIProvider,
    HuggingFaceProvider,
    LocalModelProvider,
    SpacyLocalProvider,
    CloudLocalModelIntegrator
)

class TestProviderConfig:
    """Test provider configuration functionality"""
    
    def test_provider_config_creation(self):
        """Test creating provider configuration"""
        config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            api_key="test_key",
            model_id="gpt-3.5-turbo",
            max_retries=3,
            timeout_seconds=30,
            priority=1
        )
        
        assert config.provider == ModelProvider.OPENAI
        assert config.api_key == "test_key"
        assert config.model_id == "gpt-3.5-turbo"
        assert config.max_retries == 3
        assert config.timeout_seconds == 30
        assert config.priority == 1
        assert config.enabled is True
    
    def test_is_available_enabled(self):
        """Test availability check when enabled"""
        config = ProviderConfig(
            provider=ModelProvider.SPACY_LOCAL,
            model_id="en_core_web_sm",
            enabled=True
        )
        
        assert config.is_available() is True
    
    def test_is_available_disabled(self):
        """Test availability check when disabled"""
        config = ProviderConfig(
            provider=ModelProvider.SPACY_LOCAL,
            model_id="en_core_web_sm",
            enabled=False
        )
        
        assert config.is_available() is False
    
    def test_is_available_quota_exceeded(self):
        """Test availability check when quota is exceeded"""
        config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-3.5-turbo",
            enabled=True,
            monthly_quota=100,
            current_usage=150
        )
        
        assert config.is_available() is False
    
    def test_is_available_within_quota(self):
        """Test availability check when within quota"""
        config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-3.5-turbo",
            enabled=True,
            monthly_quota=100,
            current_usage=50
        )
        
        assert config.is_available() is True
    
    def test_update_usage_success(self):
        """Test updating usage statistics on success"""
        config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-3.5-turbo"
        )
        
        initial_usage = config.current_usage
        initial_success_rate = config.success_rate
        
        config.update_usage(success=True, response_time=0.5)
        
        assert config.current_usage == initial_usage + 1
        assert config.last_used is not None
        assert config.average_response_time == 0.5
        # Success rate should remain high or increase
        assert config.success_rate >= initial_success_rate
    
    def test_update_usage_failure(self):
        """Test updating usage statistics on failure"""
        config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            model_id="gpt-3.5-turbo",
            success_rate=1.0
        )
        
        config.update_usage(success=False, response_time=2.0)
        
        assert config.current_usage == 1
        assert config.last_used is not None
        assert config.average_response_time == 2.0
        # Success rate should decrease
        assert config.success_rate < 1.0

class TestProcessingResult:
    """Test processing result functionality"""
    
    def test_processing_result_success(self):
        """Test creating successful processing result"""
        result = ProcessingResult(
            status=ProcessingStatus.SUCCESS,
            data={"entities": [{"text": "test", "label": "TEST"}]},
            processing_time=0.5,
            provider_used=ModelProvider.OPENAI,
            model_id="gpt-3.5-turbo",
            confidence_score=0.95
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "entities" in result.data
        assert result.processing_time == 0.5
        assert result.provider_used == ModelProvider.OPENAI
        assert result.confidence_score == 0.95
    
    def test_processing_result_failure(self):
        """Test creating failed processing result"""
        result = ProcessingResult(
            status=ProcessingStatus.FAILED,
            error_message="API key invalid",
            processing_time=0.1,
            provider_used=ModelProvider.OPENAI
        )
        
        assert result.status == ProcessingStatus.FAILED
        assert result.error_message == "API key invalid"
        assert result.data is None
        assert result.processing_time == 0.1

class TestOpenAIProvider:
    """Test OpenAI provider functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = ProviderConfig(
            provider=ModelProvider.OPENAI,
            api_key="test_key",
            model_id="gpt-3.5-turbo",
            timeout_seconds=5
        )
        self.provider = OpenAIProvider(self.config)
    
    @pytest.mark.asyncio
    async def test_process_ner_success(self):
        """Test successful NER processing"""
        result = await self.provider.process("Test text", "ner")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "entities" in result.data
        assert result.provider_used == ModelProvider.OPENAI
        assert result.processing_time > 0
        assert result.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_process_sentiment_success(self):
        """Test successful sentiment processing"""
        result = await self.provider.process("This is great!", "sentiment")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "sentiment" in result.data
        assert result.provider_used == ModelProvider.OPENAI
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_process_classification_success(self):
        """Test successful classification processing"""
        result = await self.provider.process("Technology news", "classification")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "classification" in result.data
        assert result.provider_used == ModelProvider.OPENAI
    
    @pytest.mark.asyncio
    async def test_process_unsupported_task(self):
        """Test processing unsupported task type"""
        result = await self.provider.process("Test text", "unsupported_task")
        
        assert result.status == ProcessingStatus.FAILED
        assert "Unsupported task type" in result.error_message
        assert result.provider_used == ModelProvider.OPENAI
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test provider cleanup"""
        await self.provider.initialize()
        assert self.provider.session is not None
        
        await self.provider.cleanup()
        assert self.provider.session is None

class TestHuggingFaceProvider:
    """Test Hugging Face provider functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = ProviderConfig(
            provider=ModelProvider.HUGGINGFACE,
            api_key="test_key",
            model_id="distilbert-base-uncased",
            timeout_seconds=5
        )
        self.provider = HuggingFaceProvider(self.config)
    
    @pytest.mark.asyncio
    async def test_process_ner_success(self):
        """Test successful NER processing"""
        result = await self.provider.process("Test text", "ner")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "entities" in result.data
        assert result.provider_used == ModelProvider.HUGGINGFACE
    
    @pytest.mark.asyncio
    async def test_process_sentiment_success(self):
        """Test successful sentiment processing"""
        result = await self.provider.process("This is great!", "sentiment")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "sentiment" in result.data
        assert result.provider_used == ModelProvider.HUGGINGFACE

class TestSpacyLocalProvider:
    """Test spaCy local provider functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = ProviderConfig(
            provider=ModelProvider.SPACY_LOCAL,
            model_id="en_core_web_sm",
            timeout_seconds=5
        )
        self.provider = SpacyLocalProvider(self.config)
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test provider initialization"""
        assert self.provider.is_loaded is False
        
        await self.provider.initialize()
        
        assert self.provider.is_loaded is True
        assert self.provider.model is not None
    
    @pytest.mark.asyncio
    async def test_process_ner_success(self):
        """Test successful NER processing"""
        result = await self.provider.process("Test text", "ner")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "entities" in result.data
        assert result.provider_used == ModelProvider.SPACY_LOCAL
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_process_sentiment_success(self):
        """Test successful sentiment processing"""
        result = await self.provider.process("This is great!", "sentiment")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "sentiment" in result.data
        assert result.provider_used == ModelProvider.SPACY_LOCAL
    
    @pytest.mark.asyncio
    async def test_process_pos_success(self):
        """Test successful POS tagging"""
        result = await self.provider.process("Test text", "pos")
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert "tokens" in result.data
        assert result.provider_used == ModelProvider.SPACY_LOCAL
    
    @pytest.mark.asyncio
    async def test_is_healthy(self):
        """Test health check"""
        # Before initialization
        assert self.provider.is_healthy() is False
        
        # After initialization
        await self.provider.initialize()
        assert self.provider.is_healthy() is True

class TestCloudLocalModelIntegrator:
    """Test cloud-local model integrator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.integrator = CloudLocalModelIntegrator()
    
    def test_initialization(self):
        """Test integrator initialization"""
        assert len(self.integrator.providers) > 0
        assert len(self.integrator.provider_configs) > 0
        assert len(self.integrator.fallback_chains) > 0
        
        # Check that local providers are always available
        assert 'spacy_sm' in self.integrator.providers
        assert 'spacy_md' in self.integrator.providers
        assert 'spacy_lg' in self.integrator.providers
    
    def test_get_provider_order_default(self):
        """Test getting provider order for default task"""
        order = self.integrator._get_provider_order("unknown_task")
        
        assert isinstance(order, list)
        assert len(order) > 0
        # Should include local providers
        assert any('spacy' in provider for provider in order)
    
    def test_get_provider_order_ner(self):
        """Test getting provider order for NER task"""
        order = self.integrator._get_provider_order("ner")
        
        assert isinstance(order, list)
        assert len(order) > 0
        # Should prioritize cloud providers if available, then local
        local_providers = [p for p in order if 'spacy' in p]
        assert len(local_providers) > 0
    
    def test_get_provider_order_with_preference(self):
        """Test getting provider order with preferred provider"""
        preferred = "spacy_sm"
        order = self.integrator._get_provider_order("ner", preferred)
        
        if preferred in order:
            assert order[0] == preferred
    
    @pytest.mark.asyncio
    async def test_process_success(self):
        """Test successful processing"""
        result = await self.integrator.process("Test text", "ner")
        
        # Should succeed with local providers
        assert result.status == ProcessingStatus.SUCCESS
        assert result.data is not None
        assert result.provider_used is not None
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_process_with_preferred_provider(self):
        """Test processing with preferred provider"""
        result = await self.integrator.process(
            "Test text", 
            "ner", 
            preferred_provider="spacy_sm"
        )
        
        assert result.status == ProcessingStatus.SUCCESS
        # Should use spaCy local provider
        assert result.provider_used == ModelProvider.SPACY_LOCAL
    
    @pytest.mark.asyncio
    async def test_process_fallback_behavior(self):
        """Test fallback behavior when providers fail"""
        # Disable all providers except one
        for name, config in self.integrator.provider_configs.items():
            if name != 'spacy_sm':
                config.enabled = False
        
        result = await self.integrator.process("Test text", "ner")
        
        # Should still succeed with the remaining provider
        assert result.status == ProcessingStatus.SUCCESS
        assert result.provider_used == ModelProvider.SPACY_LOCAL
    
    def test_add_provider(self):
        """Test adding custom provider"""
        custom_config = ProviderConfig(
            provider=ModelProvider.CUSTOM_API,
            model_id="custom_model",
            priority=1
        )
        
        # Create mock provider
        mock_provider = Mock()
        
        initial_count = len(self.integrator.providers)
        self.integrator.add_provider("custom", mock_provider, custom_config)
        
        assert len(self.integrator.providers) == initial_count + 1
        assert "custom" in self.integrator.providers
        assert "custom" in self.integrator.provider_configs
    
    def test_update_fallback_chain(self):
        """Test updating fallback chain"""
        new_chain = ["spacy_sm", "spacy_md"]
        self.integrator.update_fallback_chain("test_task", new_chain)
        
        assert "test_task" in self.integrator.fallback_chains
        assert self.integrator.fallback_chains["test_task"] == new_chain
    
    def test_get_provider_status(self):
        """Test getting provider status"""
        status = self.integrator.get_provider_status()
        
        assert isinstance(status, dict)
        assert len(status) > 0
        
        # Check status structure
        for provider_name, provider_status in status.items():
            assert 'provider_type' in provider_status
            assert 'model_id' in provider_status
            assert 'enabled' in provider_status
            assert 'available' in provider_status
            assert 'priority' in provider_status
    
    def test_get_statistics_initial(self):
        """Test getting initial statistics"""
        stats = self.integrator.get_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_requests' in stats
        assert 'successful_requests' in stats
        assert 'failed_requests' in stats
        assert 'success_rate' in stats
        assert 'provider_usage' in stats
        assert 'fallback_usage' in stats
        
        # Initial values
        assert stats['total_requests'] == 0
        assert stats['successful_requests'] == 0
        assert stats['failed_requests'] == 0
    
    @pytest.mark.asyncio
    async def test_statistics_after_processing(self):
        """Test statistics after processing requests"""
        # Process some requests
        await self.integrator.process("Test text 1", "ner")
        await self.integrator.process("Test text 2", "sentiment")
        
        stats = self.integrator.get_statistics()
        
        assert stats['total_requests'] >= 2
        assert stats['successful_requests'] >= 0
        assert stats['success_rate'] >= 0
        assert len(stats['provider_usage']) > 0
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup functionality"""
        # Initialize some providers
        for provider in self.integrator.providers.values():
            if hasattr(provider, 'initialize'):
                await provider.initialize()
        
        # Cleanup should not raise exceptions
        await self.integrator.cleanup()

class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_cloud_unavailable_fallback_to_local(self):
        """Test fallback to local when cloud providers are unavailable"""
        integrator = CloudLocalModelIntegrator()
        
        # Disable cloud providers
        for name, config in integrator.provider_configs.items():
            if config.provider in [ModelProvider.OPENAI, ModelProvider.HUGGINGFACE]:
                config.enabled = False
        
        result = await integrator.process("Test text", "ner")
        
        # Should succeed with local providers
        assert result.status == ProcessingStatus.SUCCESS
        assert result.provider_used == ModelProvider.SPACY_LOCAL
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_fallback(self):
        """Test fallback when quota is exceeded"""
        integrator = CloudLocalModelIntegrator()
        
        # Set quota exceeded for cloud providers
        for name, config in integrator.provider_configs.items():
            if config.provider in [ModelProvider.OPENAI, ModelProvider.HUGGINGFACE]:
                config.monthly_quota = 10
                config.current_usage = 15  # Exceed quota
        
        result = await integrator.process("Test text", "ner")
        
        # Should fallback to local providers
        assert result.status == ProcessingStatus.SUCCESS
        assert result.provider_used == ModelProvider.SPACY_LOCAL
    
    @pytest.mark.asyncio
    async def test_multiple_task_types(self):
        """Test processing multiple task types"""
        integrator = CloudLocalModelIntegrator()
        
        tasks = [
            ("Test entity extraction", "ner"),
            ("This is a positive sentiment", "sentiment"),
            ("Part of speech tagging test", "pos")
        ]
        
        results = []
        for text, task_type in tasks:
            result = await integrator.process(text, task_type)
            results.append(result)
        
        # All should succeed
        for result in results:
            assert result.status == ProcessingStatus.SUCCESS
            assert result.data is not None
        
        # Should have used appropriate providers for each task
        assert len(set(r.provider_used for r in results)) >= 1

# Performance and load tests
class TestPerformanceAndLoad:
    """Test performance and load scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test concurrent processing requests"""
        integrator = CloudLocalModelIntegrator()
        
        # Create multiple concurrent requests
        tasks = [
            integrator.process(f"Test text {i}", "ner")
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result.status == ProcessingStatus.SUCCESS
        
        # Statistics should reflect multiple requests
        stats = integrator.get_statistics()
        assert stats['total_requests'] >= 5
    
    @pytest.mark.asyncio
    async def test_provider_health_tracking(self):
        """Test provider health tracking over time"""
        integrator = CloudLocalModelIntegrator()
        
        # Process several requests
        for i in range(10):
            await integrator.process(f"Test text {i}", "ner")
        
        # Check provider health
        status = integrator.get_provider_status()
        
        for provider_name, provider_status in status.items():
            if provider_status['enabled']:
                # Should have reasonable success rate
                assert provider_status['success_rate'] >= 0.0
                # Should have recorded usage
                assert provider_status['current_usage'] >= 0

# Utility function tests
@pytest.mark.asyncio
async def test_create_integrator():
    """Test utility function for creating integrator"""
    from cloud_local_model_integration import create_integrator
    
    integrator = await create_integrator()
    
    assert isinstance(integrator, CloudLocalModelIntegrator)
    assert len(integrator.providers) > 0
    
    # Local providers should be initialized
    for name, provider in integrator.providers.items():
        if isinstance(provider, SpacyLocalProvider):
            # Should be initialized or disabled if failed
            config = integrator.provider_configs[name]
            if config.enabled:
                assert provider.is_loaded

if __name__ == "__main__":
    pytest.main([__file__, "-v"])