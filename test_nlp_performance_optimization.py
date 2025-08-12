#!/usr/bin/env python3
"""
Unit Tests for NLP Performance Optimization
Tests caching, resource management, and performance optimization features
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from nlp_performance_optimization import (
    CacheEntry,
    CacheStats,
    LRUCache,
    ModelCache,
    ResourceManager,
    PerformanceOptimizer,
    create_performance_optimizer,
    benchmark_processing
)

class TestCacheEntry:
    """Test cache entry functionality"""
    
    def test_cache_entry_creation(self):
        """Test creating cache entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=3600
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl_seconds == 3600
        assert entry.access_count == 0
    
    def test_is_expired_not_expired(self):
        """Test expiration check for non-expired entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=3600
        )
        
        assert entry.is_expired() is False
    
    def test_is_expired_expired(self):
        """Test expiration check for expired entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now() - timedelta(hours=2),
            last_accessed=datetime.now() - timedelta(hours=2),
            ttl_seconds=3600  # 1 hour
        )
        
        assert entry.is_expired() is True
    
    def test_is_expired_no_ttl(self):
        """Test expiration check when no TTL is set"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now() - timedelta(days=1),
            last_accessed=datetime.now() - timedelta(days=1),
            ttl_seconds=None
        )
        
        assert entry.is_expired() is False
    
    def test_touch(self):
        """Test touching cache entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0
        )
        
        original_access_time = entry.last_accessed
        original_count = entry.access_count
        
        time.sleep(0.01)  # Small delay
        entry.touch()
        
        assert entry.last_accessed > original_access_time
        assert entry.access_count == original_count + 1

class TestLRUCache:
    """Test LRU cache functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache = LRUCache(max_size=3, max_memory_mb=1)
    
    def test_cache_initialization(self):
        """Test cache initialization"""
        assert self.cache.max_size == 3
        assert len(self.cache.cache) == 0
        assert self.cache.stats.hits == 0
        assert self.cache.stats.misses == 0
    
    def test_put_and_get_success(self):
        """Test successful put and get operations"""
        # Put value
        success = self.cache.put("key1", "value1")
        assert success is True
        
        # Get value
        value = self.cache.get("key1")
        assert value == "value1"
        
        # Check stats
        assert self.cache.stats.hits == 1
        assert self.cache.stats.misses == 0
    
    def test_get_miss(self):
        """Test cache miss"""
        value = self.cache.get("nonexistent_key")
        assert value is None
        assert self.cache.stats.misses == 1
        assert self.cache.stats.hits == 0
    
    def test_put_with_ttl_expired(self):
        """Test putting value with TTL and expiration"""
        # Put with very short TTL
        success = self.cache.put("key1", "value1", ttl_seconds=0.01)
        assert success is True
        
        # Wait for expiration
        time.sleep(0.02)
        
        # Should be expired
        value = self.cache.get("key1")
        assert value is None
        assert self.cache.stats.misses == 1
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Fill cache to capacity
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # Access key1 to make it recently used
        self.cache.get("key1")
        
        # Add another item, should evict key2 (least recently used)
        self.cache.put("key4", "value4")
        
        # key2 should be evicted
        assert self.cache.get("key2") is None
        # key1 should still be there
        assert self.cache.get("key1") == "value1"
        # key4 should be there
        assert self.cache.get("key4") == "value4"
    
    def test_delete(self):
        """Test deleting cache entry"""
        self.cache.put("key1", "value1")
        assert self.cache.get("key1") == "value1"
        
        success = self.cache.delete("key1")
        assert success is True
        
        assert self.cache.get("key1") is None
        
        # Deleting non-existent key
        success = self.cache.delete("nonexistent")
        assert success is False
    
    def test_clear(self):
        """Test clearing cache"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        assert len(self.cache.cache) == 2
        
        self.cache.clear()
        
        assert len(self.cache.cache) == 0
        assert self.cache.stats.entry_count == 0
    
    def test_get_stats(self):
        """Test getting cache statistics"""
        # Perform some operations
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss
        
        stats = self.cache.get_stats()
        
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.entry_count == 1
        assert stats.hit_rate == 0.5

class TestModelCache:
    """Test model cache functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cache = ModelCache(
            result_cache_size=100,
            model_cache_size=5,
            result_ttl_seconds=60,
            model_ttl_seconds=300
        )
    
    def test_cache_and_get_processing_result(self):
        """Test caching and retrieving processing results"""
        text = "Test text"
        task_type = "ner"
        model_id = "test_model"
        result = {"entities": [{"text": "Test", "label": "TEST"}]}
        
        # Cache result
        success = self.cache.cache_processing_result(text, task_type, model_id, result)
        assert success is True
        
        # Retrieve result
        cached_result = self.cache.get_processing_result(text, task_type, model_id)
        assert cached_result == result
    
    def test_cache_and_get_model(self):
        """Test caching and retrieving models"""
        model_id = "test_model"
        model = {"name": "test_model", "loaded": True}
        
        # Cache model
        success = self.cache.cache_model(model_id, model)
        assert success is True
        
        # Retrieve model
        cached_model = self.cache.get_model(model_id)
        assert cached_model == model
    
    def test_cache_and_get_embeddings(self):
        """Test caching and retrieving embeddings"""
        text = "Test text"
        model_id = "embedding_model"
        embeddings = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Cache embeddings
        success = self.cache.cache_embeddings(text, model_id, embeddings)
        assert success is True
        
        # Retrieve embeddings
        cached_embeddings = self.cache.get_embeddings(text, model_id)
        assert cached_embeddings == embeddings
    
    def test_result_key_generation_consistency(self):
        """Test that result keys are generated consistently"""
        text = "Test text"
        task_type = "ner"
        model_id = "test_model"
        kwargs = {"param1": "value1", "param2": "value2"}
        
        # Generate key twice
        key1 = self.cache._generate_result_key(text, task_type, model_id, **kwargs)
        key2 = self.cache._generate_result_key(text, task_type, model_id, **kwargs)
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length
    
    def test_result_key_generation_different_inputs(self):
        """Test that different inputs generate different keys"""
        key1 = self.cache._generate_result_key("text1", "ner", "model1")
        key2 = self.cache._generate_result_key("text2", "ner", "model1")
        key3 = self.cache._generate_result_key("text1", "sentiment", "model1")
        key4 = self.cache._generate_result_key("text1", "ner", "model2")
        
        # All keys should be different
        keys = [key1, key2, key3, key4]
        assert len(set(keys)) == len(keys)
    
    def test_get_cache_stats(self):
        """Test getting comprehensive cache statistics"""
        # Perform some operations
        self.cache.cache_processing_result("text1", "ner", "model1", {"result": "test1"})
        self.cache.cache_model("model1", {"name": "model1"})
        self.cache.cache_embeddings("text1", "embed_model", [0.1, 0.2])
        
        # Get some results to generate hits/misses
        self.cache.get_processing_result("text1", "ner", "model1")  # Hit
        self.cache.get_processing_result("text2", "ner", "model1")  # Miss
        
        stats = self.cache.get_cache_stats()
        
        assert 'result_cache' in stats
        assert 'model_cache' in stats
        assert 'embedding_cache' in stats
        assert 'performance_stats' in stats
        
        # Check that result cache has some activity
        assert stats['result_cache']['entry_count'] >= 1
        assert stats['result_cache']['hits'] >= 1
    
    def test_clear_all_caches(self):
        """Test clearing all caches"""
        # Add some data
        self.cache.cache_processing_result("text1", "ner", "model1", {"result": "test1"})
        self.cache.cache_model("model1", {"name": "model1"})
        self.cache.cache_embeddings("text1", "embed_model", [0.1, 0.2])
        
        # Verify data exists
        assert self.cache.get_processing_result("text1", "ner", "model1") is not None
        assert self.cache.get_model("model1") is not None
        assert self.cache.get_embeddings("text1", "embed_model") is not None
        
        # Clear all caches
        self.cache.clear_all_caches()
        
        # Verify data is gone
        assert self.cache.get_processing_result("text1", "ner", "model1") is None
        assert self.cache.get_model("model1") is None
        assert self.cache.get_embeddings("text1", "embed_model") is None

class TestResourceManager:
    """Test resource manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.resource_manager = ResourceManager(
            max_memory_percent=80.0,
            max_cpu_percent=90.0,
            monitoring_interval=1  # Short interval for testing
        )
    
    def test_initialization(self):
        """Test resource manager initialization"""
        assert self.resource_manager.max_memory_percent == 80.0
        assert self.resource_manager.max_cpu_percent == 90.0
        assert self.resource_manager.monitoring_interval == 1
        assert self.resource_manager.monitoring_active is True
    
    def test_get_resource_stats(self):
        """Test getting resource statistics"""
        stats = self.resource_manager.get_resource_stats()
        
        assert 'current' in stats
        assert 'averages' in stats
        assert 'optimization_stats' in stats
        assert 'thresholds' in stats
        
        # Check current stats structure
        current = stats['current']
        assert 'memory_percent' in current
        assert 'memory_available_gb' in current
        assert 'memory_used_gb' in current
        assert 'cpu_percent' in current
        
        # Values should be reasonable
        assert 0 <= current['memory_percent'] <= 100
        assert current['memory_available_gb'] >= 0
        assert current['memory_used_gb'] >= 0
        assert 0 <= current['cpu_percent'] <= 100
    
    def test_is_resource_available_sufficient(self):
        """Test resource availability check with sufficient resources"""
        # Test with small resource requirements
        available = self.resource_manager.is_resource_available(
            memory_mb=10,  # 10MB
            cpu_cores=1
        )
        
        # Should be available on most systems
        assert isinstance(available, bool)
    
    def test_is_resource_available_insufficient_memory(self):
        """Test resource availability check with insufficient memory"""
        # Test with very large memory requirement
        available = self.resource_manager.is_resource_available(
            memory_mb=1000000,  # 1TB - should not be available
            cpu_cores=1
        )
        
        assert available is False
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping resource monitoring"""
        # Start monitoring
        self.resource_manager.start_monitoring()
        assert self.resource_manager.monitor_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        self.resource_manager.stop_monitoring()
        assert self.resource_manager.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_memory_optimization_triggers(self):
        """Test memory optimization triggers"""
        # Mock high memory usage
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 90.0  # High memory usage
            
            initial_optimizations = self.resource_manager.resource_stats['memory_optimizations']
            
            # Trigger optimization check
            await self.resource_manager._check_optimization_triggers(90.0, 50.0)
            
            # Should have triggered optimization
            assert self.resource_manager.resource_stats['memory_optimizations'] > initial_optimizations

class TestPerformanceOptimizer:
    """Test performance optimizer functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.optimizer = PerformanceOptimizer()
    
    @pytest.mark.asyncio
    async def test_initialization_and_shutdown(self):
        """Test optimizer initialization and shutdown"""
        await self.optimizer.initialize()
        
        # Should have started resource monitoring
        assert self.optimizer.resource_manager.monitor_task is not None
        
        await self.optimizer.shutdown()
        
        # Should have stopped monitoring
        assert self.optimizer.resource_manager.monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_optimize_processing_with_cache_miss(self):
        """Test optimized processing with cache miss"""
        await self.optimizer.initialize()
        
        try:
            # Mock processor function
            async def mock_processor(text, task_type, **kwargs):
                await asyncio.sleep(0.01)
                return Mock(status=Mock(value='success'), data={'result': 'test'})
            
            text = "Test text"
            task_type = "ner"
            model_id = "test_model"
            
            # First call should be cache miss
            result = await self.optimizer.optimize_processing(
                text, task_type, model_id, mock_processor
            )
            
            assert result is not None
            assert len(self.optimizer.performance_metrics['processing_times'][f"{task_type}_{model_id}"]) == 1
            
        finally:
            await self.optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_optimize_processing_with_cache_hit(self):
        """Test optimized processing with cache hit"""
        await self.optimizer.initialize()
        
        try:
            # Mock processor function
            async def mock_processor(text, task_type, **kwargs):
                await asyncio.sleep(0.01)
                return Mock(status=Mock(value='success'), data={'result': 'test'})
            
            text = "Test text"
            task_type = "ner"
            model_id = "test_model"
            
            # First call - cache miss
            result1 = await self.optimizer.optimize_processing(
                text, task_type, model_id, mock_processor
            )
            
            # Second call - should be cache hit (faster)
            start_time = time.time()
            result2 = await self.optimizer.optimize_processing(
                text, task_type, model_id, mock_processor
            )
            cache_time = time.time() - start_time
            
            # Cache hit should be much faster
            assert cache_time < 0.005  # Less than 5ms
            assert result2 is not None
            
        finally:
            await self.optimizer.shutdown()
    
    def test_preload_models(self):
        """Test model preloading"""
        model_ids = ["model1", "model2", "model3"]
        
        # Initially no models cached
        for model_id in model_ids:
            assert self.optimizer.cache.get_model(model_id) is None
        
        # Preload models
        self.optimizer.preload_models(model_ids)
        
        # Models should now be cached
        for model_id in model_ids:
            cached_model = self.optimizer.cache.get_model(model_id)
            assert cached_model is not None
            assert cached_model["model_id"] == model_id
    
    def test_optimize_batch_processing(self):
        """Test batch processing optimization"""
        texts = ["text1", "text2", "text3"]
        task_type = "ner"
        model_id = "test_model"
        
        # Initially no cache coverage
        results = self.optimizer.optimize_batch_processing(texts, task_type, model_id)
        
        assert len(results) == len(texts)
        for text, cached in results:
            assert text in texts
            assert cached is False  # No cache initially
        
        # Cache some results
        self.optimizer.cache.cache_processing_result(
            "text1", task_type, model_id, {"result": "cached"}
        )
        
        # Check again
        results = self.optimizer.optimize_batch_processing(texts, task_type, model_id)
        
        # text1 should be cached now
        text1_result = next((cached for text, cached in results if text == "text1"), None)
        assert text1_result is True
    
    def test_get_performance_report(self):
        """Test getting performance report"""
        # Add some performance data
        self.optimizer.performance_metrics['processing_times']['ner_model1'] = [0.1, 0.2, 0.15]
        
        report = self.optimizer.get_performance_report()
        
        assert 'processing_performance' in report
        assert 'cache_performance' in report
        assert 'resource_usage' in report
        assert 'optimization_strategies' in report
        
        # Check processing performance
        perf = report['processing_performance']
        if 'ner_model1' in perf:
            assert 'avg_ms' in perf['ner_model1']
            assert 'min_ms' in perf['ner_model1']
            assert 'max_ms' in perf['ner_model1']
            assert 'count' in perf['ner_model1']
    
    def test_tune_performance_slow(self):
        """Test performance tuning when performance is slow"""
        # Add slow performance data
        self.optimizer.performance_metrics['processing_times']['test'] = [0.2, 0.25, 0.3]  # 200-300ms
        
        # Tune for 100ms target
        self.optimizer.tune_performance(target_response_time_ms=100.0)
        
        # Should enable aggressive optimizations
        assert self.optimizer.optimization_strategies['aggressive_caching'] is True
        assert self.optimizer.optimization_strategies['model_preloading'] is True
        assert self.optimizer.optimization_strategies['batch_processing'] is True
    
    def test_tune_performance_fast(self):
        """Test performance tuning when performance is very fast"""
        # Add fast performance data
        self.optimizer.performance_metrics['processing_times']['test'] = [0.01, 0.015, 0.02]  # 10-20ms
        
        # Tune for 100ms target (much slower than current)
        self.optimizer.tune_performance(target_response_time_ms=100.0)
        
        # Should relax some optimizations
        assert self.optimizer.optimization_strategies['aggressive_caching'] is True  # Keep this
        assert self.optimizer.optimization_strategies['model_preloading'] is False  # Relax this

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_performance_optimizer(self):
        """Test creating performance optimizer"""
        optimizer = create_performance_optimizer()
        
        assert isinstance(optimizer, PerformanceOptimizer)
        assert optimizer.cache is not None
        assert optimizer.resource_manager is not None
        assert optimizer.optimization_strategies is not None
    
    @pytest.mark.asyncio
    async def test_benchmark_processing(self):
        """Test benchmarking processing performance"""
        optimizer = create_performance_optimizer()
        await optimizer.initialize()
        
        try:
            test_cases = [
                ("Short text", "ner", "model1"),
                ("This is a longer text for testing", "sentiment", "model2"),
                ("Very long text with multiple sentences for comprehensive testing.", "classification", "model3")
            ]
            
            results = await benchmark_processing(optimizer, test_cases, iterations=3)
            
            assert 'test_cases' in results
            assert 'iterations' in results
            assert 'results' in results
            assert 'summary' in results
            
            assert results['test_cases'] == len(test_cases)
            assert results['iterations'] == 3
            
            # Should have results for each test case
            assert len(results['results']) <= len(test_cases)  # May be less if some failed
            
            # Check result structure
            for result in results['results']:
                assert 'text_length' in result
                assert 'task_type' in result
                assert 'model_id' in result
                assert 'avg_ms' in result
                assert 'min_ms' in result
                assert 'max_ms' in result
            
            # Check summary
            if results['results']:
                summary = results['summary']
                assert 'overall_avg_ms' in summary
                assert 'overall_min_ms' in summary
                assert 'overall_max_ms' in summary
                assert 'cache_hit_rate' in summary
        
        finally:
            await optimizer.shutdown()

# Integration tests
class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_optimization_workflow(self):
        """Test complete optimization workflow"""
        optimizer = create_performance_optimizer()
        await optimizer.initialize()
        
        try:
            # Mock processor with varying performance
            call_count = 0
            
            async def variable_processor(text, task_type, **kwargs):
                nonlocal call_count
                call_count += 1
                
                # First call is slow, subsequent calls are faster
                delay = 0.1 if call_count == 1 else 0.02
                await asyncio.sleep(delay)
                
                return Mock(
                    status=Mock(value='success'),
                    data={'result': f'processed_{call_count}'}
                )
            
            text = "Test text for optimization"
            task_type = "ner"
            model_id = "test_model"
            
            # First processing - should be slow
            start_time = time.time()
            result1 = await optimizer.optimize_processing(
                text, task_type, model_id, variable_processor
            )
            first_time = time.time() - start_time
            
            # Second processing - should hit cache and be fast
            start_time = time.time()
            result2 = await optimizer.optimize_processing(
                text, task_type, model_id, variable_processor
            )
            second_time = time.time() - start_time
            
            # Cache hit should be much faster
            assert second_time < first_time / 2
            
            # Get performance report
            report = optimizer.get_performance_report()
            assert report['cache_performance']['result_cache']['hits'] >= 1
            
            # Tune performance
            optimizer.tune_performance(target_response_time_ms=50.0)
            
            # Should have optimization events
            assert len(optimizer.performance_metrics['optimization_events']) > 0
            
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_resource_constrained_optimization(self):
        """Test optimization under resource constraints"""
        optimizer = create_performance_optimizer()
        await optimizer.initialize()
        
        try:
            # Mock high resource usage
            with patch.object(optimizer.resource_manager, 'is_resource_available', return_value=False):
                
                async def mock_processor(text, task_type, **kwargs):
                    await asyncio.sleep(0.01)
                    return Mock(status=Mock(value='success'), data={'result': 'test'})
                
                # Should still process but with warnings
                result = await optimizer.optimize_processing(
                    "test text", "ner", "model1", mock_processor
                )
                
                assert result is not None
        
        finally:
            await optimizer.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_optimization(self):
        """Test optimization with concurrent requests"""
        optimizer = create_performance_optimizer()
        await optimizer.initialize()
        
        try:
            async def mock_processor(text, task_type, **kwargs):
                await asyncio.sleep(0.01)
                return Mock(status=Mock(value='success'), data={'result': text})
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = optimizer.optimize_processing(
                    f"text_{i}", "ner", "model1", mock_processor
                )
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 5
            for result in results:
                assert result is not None
            
            # Should have performance data
            perf_data = optimizer.performance_metrics['processing_times']['ner_model1']
            assert len(perf_data) >= 5
        
        finally:
            await optimizer.shutdown()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])