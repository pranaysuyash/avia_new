#!/usr/bin/env python3
"""
NLP Performance Optimization and Caching
Implements intelligent caching, resource management, and performance optimization
"""

import asyncio
import logging
import hashlib
import time
import json
import pickle
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import OrderedDict, defaultdict
import psutil
import gc
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheType(Enum):
    """Types of caches available"""
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"
    REDIS = "redis"

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl_seconds is None:
            return False
        
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def touch(self):
        """Update access information"""
        self.last_accessed = datetime.now()
        self.access_count += 1

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    
    def update_hit_rate(self):
        """Update hit rate calculation"""
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0

class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                self.stats.update_hit_rate()
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                self._update_stats()
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.touch()
            
            self.stats.hits += 1
            self.stats.update_hit_rate()
            
            return entry.value
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Put value in cache"""
        with self.lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = len(str(value).encode('utf-8'))
            
            # Check if value is too large
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"Value too large for cache: {size_bytes} bytes")
                return False
            
            # Remove existing entry if present
            if key in self.cache:
                old_entry = self.cache[key]
                self.stats.size_bytes -= old_entry.size_bytes
                del self.cache[key]
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl_seconds,
                size_bytes=size_bytes
            )
            
            # Evict entries if necessary
            self._evict_if_needed(size_bytes)
            
            # Add new entry
            self.cache[key] = entry
            self.stats.size_bytes += size_bytes
            self._update_stats()
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.stats.size_bytes -= entry.size_bytes
                del self.cache[key]
                self._update_stats()
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()
    
    def _evict_if_needed(self, new_entry_size: int):
        """Evict entries if cache limits would be exceeded"""
        # Check size limit
        while (len(self.cache) >= self.max_size or 
               self.stats.size_bytes + new_entry_size > self.max_memory_bytes):
            if not self.cache:
                break
            
            # Remove least recently used (first item)
            oldest_key, oldest_entry = self.cache.popitem(last=False)
            self.stats.size_bytes -= oldest_entry.size_bytes
            self.stats.evictions += 1
            
            logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def _update_stats(self):
        """Update cache statistics"""
        self.stats.entry_count = len(self.cache)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self.lock:
            self.stats.update_hit_rate()
            return self.stats

class ModelCache:
    """Specialized cache for NLP models and results"""
    
    def __init__(self, 
                 result_cache_size: int = 10000,
                 model_cache_size: int = 10,
                 result_ttl_seconds: int = 3600,
                 model_ttl_seconds: int = 86400):
        
        # Separate caches for different types of data
        self.result_cache = LRUCache(result_cache_size, max_memory_mb=50)
        self.model_cache = LRUCache(model_cache_size, max_memory_mb=500)
        self.embedding_cache = LRUCache(result_cache_size // 2, max_memory_mb=100)
        
        self.result_ttl = result_ttl_seconds
        self.model_ttl = model_ttl_seconds
        
        # Performance tracking
        self.performance_stats = {
            'cache_saves_ms': [],
            'cache_loads_ms': [],
            'model_loads_ms': [],
            'processing_speedup': []
        }
    
    def get_processing_result(self, text: str, task_type: str, 
                            model_id: str, **kwargs) -> Optional[Any]:
        """Get cached processing result"""
        cache_key = self._generate_result_key(text, task_type, model_id, **kwargs)
        
        start_time = time.time()
        result = self.result_cache.get(cache_key)
        load_time = (time.time() - start_time) * 1000
        
        if result is not None:
            self.performance_stats['cache_loads_ms'].append(load_time)
            logger.debug(f"Cache hit for processing result: {cache_key[:20]}...")
        
        return result
    
    def cache_processing_result(self, text: str, task_type: str, 
                              model_id: str, result: Any, **kwargs) -> bool:
        """Cache processing result"""
        cache_key = self._generate_result_key(text, task_type, model_id, **kwargs)
        
        start_time = time.time()
        success = self.result_cache.put(cache_key, result, self.result_ttl)
        save_time = (time.time() - start_time) * 1000
        
        if success:
            self.performance_stats['cache_saves_ms'].append(save_time)
            logger.debug(f"Cached processing result: {cache_key[:20]}...")
        
        return success
    
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get cached model"""
        return self.model_cache.get(model_id)
    
    def cache_model(self, model_id: str, model: Any) -> bool:
        """Cache model"""
        start_time = time.time()
        success = self.model_cache.put(model_id, model, self.model_ttl)
        load_time = (time.time() - start_time) * 1000
        
        if success:
            self.performance_stats['model_loads_ms'].append(load_time)
            logger.info(f"Cached model: {model_id}")
        
        return success
    
    def get_embeddings(self, text: str, model_id: str) -> Optional[Any]:
        """Get cached embeddings"""
        cache_key = self._generate_embedding_key(text, model_id)
        return self.embedding_cache.get(cache_key)
    
    def cache_embeddings(self, text: str, model_id: str, embeddings: Any) -> bool:
        """Cache embeddings"""
        cache_key = self._generate_embedding_key(text, model_id)
        return self.embedding_cache.put(cache_key, embeddings, self.result_ttl)
    
    def _generate_result_key(self, text: str, task_type: str, 
                           model_id: str, **kwargs) -> str:
        """Generate cache key for processing results"""
        # Create deterministic key from inputs
        key_data = {
            'text': text,
            'task_type': task_type,
            'model_id': model_id,
            'kwargs': sorted(kwargs.items()) if kwargs else []
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _generate_embedding_key(self, text: str, model_id: str) -> str:
        """Generate cache key for embeddings"""
        key_string = f"{model_id}:{text}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'result_cache': asdict(self.result_cache.get_stats()),
            'model_cache': asdict(self.model_cache.get_stats()),
            'embedding_cache': asdict(self.embedding_cache.get_stats()),
            'performance_stats': {
                'avg_cache_save_ms': sum(self.performance_stats['cache_saves_ms']) / 
                                   max(len(self.performance_stats['cache_saves_ms']), 1),
                'avg_cache_load_ms': sum(self.performance_stats['cache_loads_ms']) / 
                                   max(len(self.performance_stats['cache_loads_ms']), 1),
                'avg_model_load_ms': sum(self.performance_stats['model_loads_ms']) / 
                                   max(len(self.performance_stats['model_loads_ms']), 1),
                'total_cache_operations': len(self.performance_stats['cache_saves_ms']) + 
                                        len(self.performance_stats['cache_loads_ms'])
            }
        }
    
    def clear_all_caches(self):
        """Clear all caches"""
        self.result_cache.clear()
        self.model_cache.clear()
        self.embedding_cache.clear()
        logger.info("All caches cleared")

class ResourceManager:
    """Manages system resources and performance optimization"""
    
    def __init__(self, 
                 max_memory_percent: float = 80.0,
                 max_cpu_percent: float = 90.0,
                 monitoring_interval: int = 30):
        
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent
        self.monitoring_interval = monitoring_interval
        
        # Resource monitoring
        self.resource_stats = {
            'memory_usage_history': [],
            'cpu_usage_history': [],
            'gc_collections': 0,
            'memory_optimizations': 0
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'high_memory_threshold': 70.0,
            'critical_memory_threshold': 85.0,
            'high_cpu_threshold': 80.0,
            'critical_cpu_threshold': 95.0
        }
        
        # Start monitoring
        self.monitoring_active = True
        self.monitor_task = None
    
    def start_monitoring(self):
        """Start resource monitoring"""
        if not self.monitor_task:
            self.monitor_task = asyncio.create_task(self._monitor_resources())
            logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None
            logger.info("Resource monitoring stopped")
    
    async def _monitor_resources(self):
        """Monitor system resources continuously"""
        while self.monitoring_active:
            try:
                # Get current resource usage
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Store in history
                self.resource_stats['memory_usage_history'].append({
                    'timestamp': datetime.now(),
                    'memory_percent': memory_percent,
                    'cpu_percent': cpu_percent
                })
                
                # Keep only recent history (last 100 measurements)
                if len(self.resource_stats['memory_usage_history']) > 100:
                    self.resource_stats['memory_usage_history'].pop(0)
                
                # Check for optimization opportunities
                await self._check_optimization_triggers(memory_percent, cpu_percent)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_optimization_triggers(self, memory_percent: float, cpu_percent: float):
        """Check if optimization is needed"""
        
        # Memory optimization
        if memory_percent > self.performance_thresholds['critical_memory_threshold']:
            logger.warning(f"Critical memory usage: {memory_percent:.1f}%")
            await self._optimize_memory_usage()
        elif memory_percent > self.performance_thresholds['high_memory_threshold']:
            logger.info(f"High memory usage: {memory_percent:.1f}%")
            await self._gentle_memory_optimization()
        
        # CPU optimization
        if cpu_percent > self.performance_thresholds['critical_cpu_threshold']:
            logger.warning(f"Critical CPU usage: {cpu_percent:.1f}%")
            await self._optimize_cpu_usage()
    
    async def _optimize_memory_usage(self):
        """Aggressive memory optimization"""
        logger.info("Performing aggressive memory optimization")
        
        # Force garbage collection
        collected = gc.collect()
        self.resource_stats['gc_collections'] += 1
        self.resource_stats['memory_optimizations'] += 1
        
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Additional memory optimization could include:
        # - Clearing caches
        # - Unloading unused models
        # - Reducing batch sizes
    
    async def _gentle_memory_optimization(self):
        """Gentle memory optimization"""
        logger.debug("Performing gentle memory optimization")
        
        # Light garbage collection
        gc.collect(0)  # Only collect generation 0
        self.resource_stats['memory_optimizations'] += 1
    
    async def _optimize_cpu_usage(self):
        """CPU usage optimization"""
        logger.info("Optimizing CPU usage")
        
        # Could implement:
        # - Reduce concurrent processing
        # - Switch to lighter models
        # - Implement backpressure
        
        # For now, just add a small delay to reduce load
        await asyncio.sleep(0.1)
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource statistics"""
        current_memory = psutil.virtual_memory()
        current_cpu = psutil.cpu_percent()
        
        # Calculate averages from history
        if self.resource_stats['memory_usage_history']:
            recent_memory = [
                entry['memory_percent'] 
                for entry in self.resource_stats['memory_usage_history'][-10:]
            ]
            recent_cpu = [
                entry['cpu_percent'] 
                for entry in self.resource_stats['memory_usage_history'][-10:]
            ]
            
            avg_memory = sum(recent_memory) / len(recent_memory)
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
        else:
            avg_memory = current_memory.percent
            avg_cpu = current_cpu
        
        return {
            'current': {
                'memory_percent': current_memory.percent,
                'memory_available_gb': current_memory.available / (1024**3),
                'memory_used_gb': current_memory.used / (1024**3),
                'cpu_percent': current_cpu
            },
            'averages': {
                'memory_percent': avg_memory,
                'cpu_percent': avg_cpu
            },
            'optimization_stats': {
                'gc_collections': self.resource_stats['gc_collections'],
                'memory_optimizations': self.resource_stats['memory_optimizations']
            },
            'thresholds': self.performance_thresholds
        }
    
    def is_resource_available(self, memory_mb: int = 0, cpu_cores: int = 0) -> bool:
        """Check if requested resources are available"""
        current_memory = psutil.virtual_memory()
        current_cpu = psutil.cpu_percent()
        
        # Check memory availability
        if memory_mb > 0:
            required_bytes = memory_mb * 1024 * 1024
            if current_memory.available < required_bytes:
                return False
        
        # Check CPU availability (simplified)
        if cpu_cores > 0:
            if current_cpu > self.performance_thresholds['high_cpu_threshold']:
                return False
        
        return True

class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.cache = ModelCache()
        self.resource_manager = ResourceManager()
        
        # Performance tracking
        self.performance_metrics = {
            'processing_times': defaultdict(list),
            'cache_hit_rates': defaultdict(list),
            'resource_usage': [],
            'optimization_events': []
        }
        
        # Optimization strategies
        self.optimization_strategies = {
            'aggressive_caching': True,
            'resource_monitoring': True,
            'automatic_gc': True,
            'model_preloading': True,
            'batch_processing': True
        }
    
    async def initialize(self):
        """Initialize performance optimizer"""
        if self.optimization_strategies['resource_monitoring']:
            self.resource_manager.start_monitoring()
        
        logger.info("Performance optimizer initialized")
    
    async def shutdown(self):
        """Shutdown performance optimizer"""
        self.resource_manager.stop_monitoring()
        logger.info("Performance optimizer shutdown")
    
    async def optimize_processing(self, text: str, task_type: str, 
                                model_id: str, processor_func, **kwargs) -> Any:
        """Optimize processing with caching and resource management"""
        
        start_time = time.time()
        
        # Check cache first
        if self.optimization_strategies['aggressive_caching']:
            cached_result = self.cache.get_processing_result(
                text, task_type, model_id, **kwargs
            )
            
            if cached_result is not None:
                processing_time = time.time() - start_time
                self.performance_metrics['processing_times'][f"{task_type}_{model_id}"].append(processing_time)
                
                logger.debug(f"Cache hit for {task_type} with {model_id}")
                return cached_result
        
        # Check resource availability
        if not self.resource_manager.is_resource_available():
            logger.warning("Resources constrained, may affect performance")
        
        # Process with optimization
        try:
            result = await processor_func(text, task_type, **kwargs)
            
            # Cache result if successful
            if (self.optimization_strategies['aggressive_caching'] and 
                hasattr(result, 'status') and 
                result.status.value == 'success'):
                
                self.cache.cache_processing_result(
                    text, task_type, model_id, result, **kwargs
                )
            
            # Track performance
            processing_time = time.time() - start_time
            self.performance_metrics['processing_times'][f"{task_type}_{model_id}"].append(processing_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def preload_models(self, model_ids: List[str]):
        """Preload frequently used models"""
        if not self.optimization_strategies['model_preloading']:
            return
        
        logger.info(f"Preloading models: {model_ids}")
        
        for model_id in model_ids:
            # Check if already cached
            if self.cache.get_model(model_id) is None:
                # In a real implementation, this would load the actual model
                # For now, we'll just cache a placeholder
                self.cache.cache_model(model_id, {"model_id": model_id, "loaded": True})
    
    def optimize_batch_processing(self, texts: List[str], task_type: str, 
                                 model_id: str) -> List[Tuple[str, bool]]:
        """Optimize batch processing by checking cache coverage"""
        if not self.optimization_strategies['batch_processing']:
            return [(text, False) for text in texts]
        
        results = []
        for text in texts:
            cached = self.cache.get_processing_result(text, task_type, model_id) is not None
            results.append((text, cached))
        
        cache_coverage = sum(1 for _, cached in results if cached) / len(results)
        logger.info(f"Batch cache coverage: {cache_coverage:.2%}")
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        
        # Calculate average processing times
        avg_processing_times = {}
        for key, times in self.performance_metrics['processing_times'].items():
            if times:
                avg_processing_times[key] = {
                    'avg_ms': (sum(times) / len(times)) * 1000,
                    'min_ms': min(times) * 1000,
                    'max_ms': max(times) * 1000,
                    'count': len(times)
                }
        
        # Get cache statistics
        cache_stats = self.cache.get_cache_stats()
        
        # Get resource statistics
        resource_stats = self.resource_manager.get_resource_stats()
        
        return {
            'processing_performance': avg_processing_times,
            'cache_performance': cache_stats,
            'resource_usage': resource_stats,
            'optimization_strategies': self.optimization_strategies,
            'optimization_events': len(self.performance_metrics['optimization_events'])
        }
    
    def tune_performance(self, target_response_time_ms: float = 100.0):
        """Auto-tune performance based on target response time"""
        
        logger.info(f"Tuning performance for target response time: {target_response_time_ms}ms")
        
        # Analyze current performance
        current_times = []
        for times in self.performance_metrics['processing_times'].values():
            current_times.extend(times)
        
        if not current_times:
            logger.warning("No performance data available for tuning")
            return
        
        avg_time_ms = (sum(current_times) / len(current_times)) * 1000
        
        logger.info(f"Current average response time: {avg_time_ms:.1f}ms")
        
        # Adjust strategies based on performance
        if avg_time_ms > target_response_time_ms:
            # Performance is too slow, enable more aggressive optimizations
            self.optimization_strategies['aggressive_caching'] = True
            self.optimization_strategies['model_preloading'] = True
            self.optimization_strategies['batch_processing'] = True
            
            logger.info("Enabled aggressive optimizations")
            
        elif avg_time_ms < target_response_time_ms * 0.5:
            # Performance is very good, can relax some optimizations
            self.optimization_strategies['aggressive_caching'] = True  # Keep this
            self.optimization_strategies['model_preloading'] = False
            
            logger.info("Relaxed some optimizations")
        
        self.performance_metrics['optimization_events'].append({
            'timestamp': datetime.now(),
            'target_ms': target_response_time_ms,
            'actual_ms': avg_time_ms,
            'action': 'tuned_strategies'
        })

# Utility functions
def create_performance_optimizer() -> PerformanceOptimizer:
    """Create and initialize performance optimizer"""
    return PerformanceOptimizer()

async def benchmark_processing(optimizer: PerformanceOptimizer, 
                             test_cases: List[Tuple[str, str, str]], 
                             iterations: int = 10) -> Dict[str, Any]:
    """Benchmark processing performance"""
    
    results = {
        'test_cases': len(test_cases),
        'iterations': iterations,
        'results': [],
        'summary': {}
    }
    
    for text, task_type, model_id in test_cases:
        case_results = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Mock processing function
            async def mock_processor(text, task_type, **kwargs):
                await asyncio.sleep(0.01)  # Simulate processing
                return {"status": "success", "data": {"result": "mock"}}
            
            try:
                result = await optimizer.optimize_processing(
                    text, task_type, model_id, mock_processor
                )
                
                processing_time = time.time() - start_time
                case_results.append(processing_time * 1000)  # Convert to ms
                
            except Exception as e:
                logger.error(f"Benchmark failed: {e}")
                case_results.append(float('inf'))
        
        # Calculate statistics for this test case
        if case_results and all(t != float('inf') for t in case_results):
            case_stats = {
                'text_length': len(text),
                'task_type': task_type,
                'model_id': model_id,
                'avg_ms': sum(case_results) / len(case_results),
                'min_ms': min(case_results),
                'max_ms': max(case_results),
                'std_dev': (sum((x - sum(case_results)/len(case_results))**2 for x in case_results) / len(case_results))**0.5
            }
            
            results['results'].append(case_stats)
    
    # Calculate overall summary
    if results['results']:
        all_times = [r['avg_ms'] for r in results['results']]
        results['summary'] = {
            'overall_avg_ms': sum(all_times) / len(all_times),
            'overall_min_ms': min(all_times),
            'overall_max_ms': max(all_times),
            'cache_hit_rate': optimizer.cache.result_cache.get_stats().hit_rate
        }
    
    return results

# Example usage
async def example_usage():
    """Example usage of performance optimization"""
    
    # Create optimizer
    optimizer = create_performance_optimizer()
    await optimizer.initialize()
    
    try:
        # Example processing with optimization
        async def mock_processor(text, task_type, **kwargs):
            await asyncio.sleep(0.05)  # Simulate processing time
            return {
                "status": "success",
                "data": {"entities": [{"text": "example", "label": "TEST"}]},
                "processing_time": 0.05
            }
        
        # Process some examples
        test_text = "This is a test for performance optimization."
        
        print("Processing with optimization...")
        result1 = await optimizer.optimize_processing(
            test_text, "ner", "test_model", mock_processor
        )
        
        print("Processing same text again (should hit cache)...")
        result2 = await optimizer.optimize_processing(
            test_text, "ner", "test_model", mock_processor
        )
        
        # Get performance report
        report = optimizer.get_performance_report()
        print(f"Performance report: {json.dumps(report, indent=2, default=str)}")
        
        # Tune performance
        optimizer.tune_performance(target_response_time_ms=50.0)
        
    finally:
        await optimizer.shutdown()

if __name__ == "__main__":
    asyncio.run(example_usage())