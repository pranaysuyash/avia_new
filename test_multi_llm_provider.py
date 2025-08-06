#!/usr/bin/env python3
"""
Comprehensive test suite for Multi-LLM Provider System
Tests all components including provider implementations, fallback mechanisms, and system integration
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock heavy dependencies before importing
sys.modules['openai'] = Mock()
sys.modules['transformers'] = Mock()
sys.modules['torch'] = Mock()
sys.modules['anthropic'] = Mock()
sys.modules['google'] = Mock()
sys.modules['google.generativeai'] = Mock()
sys.modules['groq'] = Mock()

from multi_llm_provider_system import (
    MultiLLMProviderSystem, LLMProvider, TaskType, LLMRequest, LLMResponse,
    ProviderConfig, ProviderStats, BaseLLMProvider, OpenAIProvider,
    HuggingFaceProvider, ClaudeProvider, GeminiProvider, GroqProvider
)

class TestLLMDataStructures(unittest.TestCase):
    """Test cases for LLM data structures"""
    
    def test_llm_request_creation(self):
        """Test LLMRequest creation and validation"""
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION,
            max_tokens=100,
            temperature=0.7
        )
        
        self.assertEqual(request.prompt, "Test prompt")
        self.assertEqual(request.task_type, TaskType.TEXT_GENERATION)
        self.assertEqual(request.max_tokens, 100)
        self.assertEqual(request.temperature, 0.7)
        self.assertIsNone(request.system_message)
        self.assertIsNone(request.context)
        self.assertIsInstance(request.metadata, dict)
    
    def test_llm_response_creation(self):
        """Test LLMResponse creation and validation"""
        response = LLMResponse(
            content="Test response",
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            tokens_used=50,
            cost=0.001,
            latency=1.5,
            confidence=0.9
        )
        
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.provider, LLMProvider.OPENAI)
        self.assertEqual(response.model, "gpt-3.5-turbo")
        self.assertEqual(response.tokens_used, 50)
        self.assertEqual(response.cost, 0.001)
        self.assertEqual(response.latency, 1.5)
        self.assertEqual(response.confidence, 0.9)
        self.assertIsInstance(response.timestamp, datetime)
    
    def test_provider_config_creation(self):
        """Test ProviderConfig creation and validation"""
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7,
            enabled=True,
            priority=1,
            cost_per_token=0.0015
        )
        
        self.assertEqual(config.provider, LLMProvider.OPENAI)
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "gpt-3.5-turbo")
        self.assertEqual(config.max_tokens, 1000)
        self.assertEqual(config.temperature, 0.7)
        self.assertTrue(config.enabled)
        self.assertEqual(config.priority, 1)
        self.assertEqual(config.cost_per_token, 0.0015)
    
    def test_provider_stats_initialization(self):
        """Test ProviderStats initialization"""
        stats = ProviderStats(provider=LLMProvider.OPENAI)
        
        self.assertEqual(stats.provider, LLMProvider.OPENAI)
        self.assertEqual(stats.total_requests, 0)
        self.assertEqual(stats.successful_requests, 0)
        self.assertEqual(stats.failed_requests, 0)
        self.assertEqual(stats.total_tokens, 0)
        self.assertEqual(stats.total_cost, 0.0)
        self.assertEqual(stats.average_latency, 0.0)
        self.assertEqual(stats.success_rate, 0.0)
        self.assertIsNone(stats.last_used)
        self.assertIsInstance(stats.latency_history, list)

class TestBaseLLMProvider(unittest.TestCase):
    """Test cases for BaseLLMProvider abstract class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="test-model"
        )
    
    def test_base_provider_abstract_methods(self):
        """Test that BaseLLMProvider is abstract"""
        with self.assertRaises(TypeError):
            BaseLLMProvider(self.config)

class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing"""
    
    def _setup_client(self):
        self.client = Mock()
    
    async def _generate_response(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="Mock response",
            provider=self.config.provider,
            model=self.config.model,
            tokens_used=10,
            cost=0.001,
            latency=0.0,
            confidence=0.8
        )

class TestMockLLMProvider(unittest.TestCase):
    """Test cases for mock LLM provider"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="test-model"
        )
        self.provider = MockLLMProvider(self.config)
    
    def test_provider_initialization(self):
        """Test provider initialization"""
        self.assertEqual(self.provider.config, self.config)
        self.assertIsInstance(self.provider.stats, ProviderStats)
        self.assertEqual(self.provider.stats.provider, LLMProvider.OPENAI)
    
    async def test_generate_response(self):
        """Test response generation"""
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        response = await self.provider.generate(request)
        
        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.content, "Mock response")
        self.assertEqual(response.provider, LLMProvider.OPENAI)
        self.assertEqual(response.tokens_used, 10)
        self.assertGreater(response.latency, 0)  # Should be set by parent class
    
    async def test_stats_tracking(self):
        """Test statistics tracking"""
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        # Initial stats
        self.assertEqual(self.provider.stats.total_requests, 0)
        self.assertEqual(self.provider.stats.successful_requests, 0)
        
        # Generate response
        await self.provider.generate(request)
        
        # Check updated stats
        self.assertEqual(self.provider.stats.total_requests, 1)
        self.assertEqual(self.provider.stats.successful_requests, 1)
        self.assertEqual(self.provider.stats.failed_requests, 0)
        self.assertEqual(self.provider.stats.success_rate, 1.0)
        self.assertIsNotNone(self.provider.stats.last_used)

class TestMultiLLMProviderSystem(unittest.TestCase):
    """Test cases for MultiLLMProviderSystem"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-claude-key',
            'GOOGLE_API_KEY': 'test-gemini-key',
            'GROQ_API_KEY': 'test-groq-key'
        })
        self.env_patcher.start()
        
        # Mock provider availability
        self.openai_patcher = patch('multi_llm_provider_system.OPENAI_AVAILABLE', True)
        self.claude_patcher = patch('multi_llm_provider_system.CLAUDE_AVAILABLE', True)
        self.gemini_patcher = patch('multi_llm_provider_system.GEMINI_AVAILABLE', True)
        self.groq_patcher = patch('multi_llm_provider_system.GROQ_AVAILABLE', True)
        self.hf_patcher = patch('multi_llm_provider_system.HUGGINGFACE_AVAILABLE', True)
        
        self.openai_patcher.start()
        self.claude_patcher.start()
        self.gemini_patcher.start()
        self.groq_patcher.start()
        self.hf_patcher.start()
        
        # Mock provider classes
        self.provider_patches = {}
        provider_classes = [
            'OpenAIProvider', 'ClaudeProvider', 'GeminiProvider', 
            'GroqProvider', 'HuggingFaceProvider'
        ]
        
        for provider_class in provider_classes:
            mock_provider = Mock()
            mock_provider.stats = ProviderStats(provider=LLMProvider.OPENAI)
            mock_provider.generate = AsyncMock(return_value=LLMResponse(
                content="Mock response",
                provider=LLMProvider.OPENAI,
                model="mock-model",
                tokens_used=10,
                cost=0.001,
                latency=1.0,
                confidence=0.8
            ))
            
            patcher = patch(f'multi_llm_provider_system.{provider_class}', return_value=mock_provider)
            self.provider_patches[provider_class] = patcher
            patcher.start()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()
        self.openai_patcher.stop()
        self.claude_patcher.stop()
        self.gemini_patcher.stop()
        self.groq_patcher.stop()
        self.hf_patcher.stop()
        
        for patcher in self.provider_patches.values():
            patcher.stop()
    
    def test_system_initialization(self):
        """Test system initialization"""
        system = MultiLLMProviderSystem()
        
        self.assertIsInstance(system.providers, dict)
        self.assertIsInstance(system.configs, dict)
        self.assertIsInstance(system.fallback_chains, dict)
        self.assertIsInstance(system.request_cache, dict)
        
        # Check that providers are initialized
        self.assertGreater(len(system.providers), 0)
        self.assertGreater(len(system.configs), 0)
    
    def test_configuration_loading(self):
        """Test configuration loading from environment"""
        system = MultiLLMProviderSystem()
        
        # Check that configurations are loaded
        self.assertIn(LLMProvider.OPENAI, system.configs)
        self.assertIn(LLMProvider.CLAUDE, system.configs)
        self.assertIn(LLMProvider.GEMINI, system.configs)
        self.assertIn(LLMProvider.GROQ, system.configs)
        
        # Check that API keys are set
        self.assertEqual(system.configs[LLMProvider.OPENAI].api_key, 'test-openai-key')
        self.assertEqual(system.configs[LLMProvider.CLAUDE].api_key, 'test-claude-key')
        self.assertEqual(system.configs[LLMProvider.GEMINI].api_key, 'test-gemini-key')
        self.assertEqual(system.configs[LLMProvider.GROQ].api_key, 'test-groq-key')
    
    def test_fallback_chains_setup(self):
        """Test fallback chains setup"""
        system = MultiLLMProviderSystem()
        
        # Check that fallback chains are set up for all task types
        for task_type in TaskType:
            self.assertIn(task_type, system.fallback_chains)
            self.assertIsInstance(system.fallback_chains[task_type], list)
            self.assertGreater(len(system.fallback_chains[task_type]), 0)
    
    async def test_generate_response(self):
        """Test response generation"""
        system = MultiLLMProviderSystem()
        
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        response = await system.generate(request)
        
        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.content, "Mock response")
        self.assertIsInstance(response.provider, LLMProvider)
    
    async def test_generate_with_fallback(self):
        """Test response generation with fallback"""
        system = MultiLLMProviderSystem()
        
        # Mock first provider to fail
        first_provider = list(system.providers.values())[0]
        first_provider.generate.side_effect = Exception("Provider failed")
        
        # Second provider should succeed
        if len(system.providers) > 1:
            second_provider = list(system.providers.values())[1]
            second_provider.generate.return_value = LLMResponse(
                content="Fallback response",
                provider=LLMProvider.CLAUDE,
                model="claude-model",
                tokens_used=15,
                cost=0.002,
                latency=1.5,
                confidence=0.9
            )
        
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        if len(system.providers) > 1:
            response = await system.generate(request)
            self.assertEqual(response.content, "Fallback response")
        else:
            with self.assertRaises(Exception):
                await system.generate(request)
    
    async def test_generate_with_comparison(self):
        """Test response generation with comparison"""
        system = MultiLLMProviderSystem()
        
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        results = await system.generate_with_comparison(request)
        
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
        
        for provider_type, response in results.items():
            self.assertIsInstance(provider_type, LLMProvider)
            self.assertIsInstance(response, LLMResponse)
    
    def test_cache_functionality(self):
        """Test response caching"""
        system = MultiLLMProviderSystem()
        
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        # Test cache key generation
        cache_key = system._get_cache_key(request)
        self.assertIsInstance(cache_key, str)
        self.assertGreater(len(cache_key), 0)
        
        # Test cache validation
        response = LLMResponse(
            content="Test response",
            provider=LLMProvider.OPENAI,
            model="test-model",
            tokens_used=10,
            cost=0.001,
            latency=1.0,
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        self.assertTrue(system._is_cache_valid(response))
        
        # Test expired cache
        old_response = LLMResponse(
            content="Old response",
            provider=LLMProvider.OPENAI,
            model="test-model",
            tokens_used=10,
            cost=0.001,
            latency=1.0,
            confidence=0.8,
            timestamp=datetime.now() - timedelta(hours=2)
        )
        
        self.assertFalse(system._is_cache_valid(old_response))
    
    def test_provider_stats(self):
        """Test provider statistics retrieval"""
        system = MultiLLMProviderSystem()
        
        stats = system.get_provider_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertGreater(len(stats), 0)
        
        for provider_type, provider_stats in stats.items():
            self.assertIsInstance(provider_type, LLMProvider)
            self.assertIsInstance(provider_stats, ProviderStats)
    
    def test_best_provider_selection(self):
        """Test best provider selection for task types"""
        system = MultiLLMProviderSystem()
        
        for task_type in TaskType:
            best_provider = system.get_best_provider_for_task(task_type)
            if best_provider is not None:
                self.assertIsInstance(best_provider, LLMProvider)
                self.assertIn(best_provider, system.providers)
    
    def test_cache_management(self):
        """Test cache management operations"""
        system = MultiLLMProviderSystem()
        
        # Add something to cache
        cache_key = "test_key"
        response = LLMResponse(
            content="Test response",
            provider=LLMProvider.OPENAI,
            model="test-model",
            tokens_used=10,
            cost=0.001,
            latency=1.0,
            confidence=0.8
        )
        
        system.request_cache[cache_key] = response
        self.assertEqual(len(system.request_cache), 1)
        
        # Clear cache
        system.clear_cache()
        self.assertEqual(len(system.request_cache), 0)
    
    def test_provider_config_update(self):
        """Test provider configuration updates"""
        system = MultiLLMProviderSystem()
        
        new_config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="new-test-key",
            model="gpt-4",
            priority=1,
            enabled=True
        )
        
        system.add_provider_config(new_config)
        
        self.assertEqual(system.configs[LLMProvider.OPENAI].api_key, "new-test-key")
        self.assertEqual(system.configs[LLMProvider.OPENAI].model, "gpt-4")
    
    def test_stats_export(self):
        """Test statistics export"""
        system = MultiLLMProviderSystem()
        
        exported_stats = system.export_stats()
        
        self.assertIsInstance(exported_stats, dict)
        self.assertIn("provider_stats", exported_stats)
        self.assertIn("cache_size", exported_stats)
        self.assertIn("available_providers", exported_stats)
        self.assertIn("fallback_chains", exported_stats)
        
        # Check provider stats structure
        provider_stats = exported_stats["provider_stats"]
        self.assertIsInstance(provider_stats, dict)
        
        for provider_name, stats in provider_stats.items():
            self.assertIsInstance(provider_name, str)
            self.assertIsInstance(stats, dict)
            self.assertIn("total_requests", stats)
            self.assertIn("successful_requests", stats)
            self.assertIn("success_rate", stats)

class TestProviderSpecificImplementations(unittest.TestCase):
    """Test cases for provider-specific implementations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="test-model"
        )
    
    @patch('multi_llm_provider_system.OPENAI_AVAILABLE', True)
    @patch('multi_llm_provider_system.openai')
    def test_openai_provider_setup(self, mock_openai):
        """Test OpenAI provider setup"""
        mock_client = Mock()
        mock_openai.AsyncOpenAI.return_value = mock_client
        
        provider = OpenAIProvider(self.config)
        
        self.assertEqual(provider.client, mock_client)
        mock_openai.AsyncOpenAI.assert_called_once_with(api_key="test-key")
    
    @patch('multi_llm_provider_system.CLAUDE_AVAILABLE', True)
    @patch('multi_llm_provider_system.anthropic')
    def test_claude_provider_setup(self, mock_anthropic):
        """Test Claude provider setup"""
        mock_client = Mock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client
        
        provider = ClaudeProvider(self.config)
        
        self.assertEqual(provider.client, mock_client)
        mock_anthropic.AsyncAnthropic.assert_called_once_with(api_key="test-key")
    
    @patch('multi_llm_provider_system.GEMINI_AVAILABLE', True)
    @patch('multi_llm_provider_system.genai')
    def test_gemini_provider_setup(self, mock_genai):
        """Test Gemini provider setup"""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        provider = GeminiProvider(self.config)
        
        self.assertEqual(provider.model, mock_model)
        mock_genai.configure.assert_called_once_with(api_key="test-key")
        mock_genai.GenerativeModel.assert_called_once_with("test-model")
    
    @patch('multi_llm_provider_system.GROQ_AVAILABLE', True)
    @patch('multi_llm_provider_system.Groq')
    def test_groq_provider_setup(self, mock_groq_class):
        """Test Groq provider setup"""
        mock_client = Mock()
        mock_groq_class.return_value = mock_client
        
        provider = GroqProvider(self.config)
        
        self.assertEqual(provider.client, mock_client)
        mock_groq_class.assert_called_once_with(api_key="test-key")

class TestAsyncOperations(unittest.TestCase):
    """Test cases for async operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.loop.close()
    
    def test_async_mock_provider(self):
        """Test async operations with mock provider"""
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="test-model"
        )
        
        provider = MockLLMProvider(config)
        
        request = LLMRequest(
            prompt="Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
        
        # Run async test
        response = self.loop.run_until_complete(provider.generate(request))
        
        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.content, "Mock response")

def run_tests():
    """Run all tests"""
    print("🧪 Running Multi-LLM Provider System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestLLMDataStructures,
        TestBaseLLMProvider,
        TestMockLLMProvider,
        TestMultiLLMProviderSystem,
        TestProviderSpecificImplementations,
        TestAsyncOperations
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('\\n')[-2]}")
    
    if not result.failures and not result.errors:
        print("✅ All tests passed successfully!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)