#!/usr/bin/env python3
"""
Advanced Caching and Optimization System
Implements multi-tier caching, query optimization, and performance monitoring
"""

import asyncio
import json
import logging
import hashlib
import pickle
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
import statistics

import redis
import redis.sentinel
from redis.cluster import RedisCluster
import memcache
import aiomcache
import aioredis
from functools import wraps, lru_cache
import numpy as np
from collections import OrderedDict, deque
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheTier(Enum):
    """Cache tier levels"""
    L1_MEMORY = "l1_memory"      # In-process memory cache
    L2_DISTRIBUTED = "l2_dist"    # Distributed memory cache (Redis/Memcached)
    L3_PERSISTENT = "l3_persist"  # Persistent cache (Redis with AOF)
    L4_DISK = "l4_disk"          # Disk-based cache

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    tier: CacheTier
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    memory_usage: int = 0
    tier_distribution: Dict[str, int] = field(default_factory=dict)

class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats.hits += 1
                return self.cache[key]
            self.stats.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache"""
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache.move_to_end(key)
            else:
                # Add new
                if len(self.cache) >= self.capacity:
                    # Evict least recently used
                    self.cache.popitem(last=False)
                    self.stats.evictions += 1
            self.cache[key] = value
    
    def clear(self) -> None:
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()

class BloomFilter:
    """Bloom filter for cache optimization"""
    
    def __init__(self, capacity: int = 100000, error_rate: float = 0.001):
        self.capacity = capacity
        self.error_rate = error_rate
        self.bit_array_size = self._calculate_size()
        self.num_hash_functions = self._calculate_hash_count()
        self.bit_array = np.zeros(self.bit_array_size, dtype=bool)
    
    def _calculate_size(self) -> int:
        """Calculate optimal bit array size"""
        import math
        m = -self.capacity * math.log(self.error_rate) / (math.log(2) ** 2)
        return int(m)
    
    def _calculate_hash_count(self) -> int:
        """Calculate optimal number of hash functions"""
        import math
        k = (self.bit_array_size / self.capacity) * math.log(2)
        return max(1, int(k))
    
    def _hash(self, item: str, seed: int) -> int:
        """Generate hash for item"""
        h = hashlib.md5(f"{item}{seed}".encode()).hexdigest()
        return int(h, 16) % self.bit_array_size
    
    def add(self, item: str) -> None:
        """Add item to filter"""
        for i in range(self.num_hash_functions):
            index = self._hash(item, i)
            self.bit_array[index] = True
    
    def contains(self, item: str) -> bool:
        """Check if item might be in set"""
        for i in range(self.num_hash_functions):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False
        return True

class AdvancedCachingSystem:
    """Advanced multi-tier caching system"""
    
    def __init__(
        self,
        redis_urls: Optional[List[str]] = None,
        memcached_servers: Optional[List[str]] = None,
        enable_clustering: bool = False
    ):
        # L1: In-memory cache
        self.l1_cache = LRUCache(capacity=10000)
        self.bloom_filter = BloomFilter()
        
        # L2: Distributed cache
        self.redis_clients = []
        self.memcached_client = None
        
        if redis_urls:
            if enable_clustering:
                # Redis Cluster setup
                self.redis_cluster = RedisCluster(
                    startup_nodes=[
                        {"host": url.split(":")[0], "port": int(url.split(":")[1])}
                        for url in redis_urls
                    ],
                    decode_responses=True
                )
            else:
                # Standard Redis setup
                for url in redis_urls:
                    client = redis.from_url(url)
                    self.redis_clients.append(client)
        
        if memcached_servers:
            self.memcached_client = memcache.Client(memcached_servers)
        
        # Performance monitoring
        self.stats = CacheStats()
        self.response_times = deque(maxlen=1000)
        
        # Cache warming
        self.warm_cache_executor = ThreadPoolExecutor(max_workers=5)
        
        # Optimization settings
        self.optimization_enabled = True
        self.auto_tier_migration = True
        self.compression_threshold = 1024  # Compress values > 1KB
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            return 0
    
    def _compress(self, data: bytes) -> bytes:
        """Compress data if above threshold"""
        if len(data) > self.compression_threshold:
            import zlib
            return zlib.compress(data)
        return data
    
    def _decompress(self, data: bytes) -> bytes:
        """Decompress data if compressed"""
        try:
            import zlib
            return zlib.decompress(data)
        except:
            return data
    
    async def get(
        self,
        key: str,
        tier: Optional[CacheTier] = None
    ) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        self.stats.total_requests += 1
        
        # Check bloom filter first
        if not self.bloom_filter.contains(key):
            self.stats.misses += 1
            return None
        
        # Try L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            self._record_response_time(start_time)
            return value
        
        # Try L2 distributed cache
        if self.redis_clients:
            for client in self.redis_clients:
                try:
                    cached = client.get(f"cache:{key}")
                    if cached:
                        value = pickle.loads(self._decompress(cached))
                        # Promote to L1
                        self.l1_cache.put(key, value)
                        self.stats.hits += 1
                        self._record_response_time(start_time)
                        return value
                except Exception as e:
                    logger.error(f"Redis get error: {e}")
        
        # Try Memcached
        if self.memcached_client:
            try:
                cached = self.memcached_client.get(key)
                if cached:
                    value = pickle.loads(cached)
                    # Promote to L1
                    self.l1_cache.put(key, value)
                    self.stats.hits += 1
                    self._record_response_time(start_time)
                    return value
            except Exception as e:
                logger.error(f"Memcached get error: {e}")
        
        self.stats.misses += 1
        self._record_response_time(start_time)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tier: CacheTier = CacheTier.L1_MEMORY
    ) -> None:
        """Set value in cache"""
        # Add to bloom filter
        self.bloom_filter.add(key)
        
        # Estimate size
        size = self._estimate_size(value)
        
        # L1 cache
        if tier == CacheTier.L1_MEMORY or size < 1024:  # Small values in L1
            self.l1_cache.put(key, value)
        
        # L2 distributed cache
        if tier in [CacheTier.L2_DISTRIBUTED, CacheTier.L3_PERSISTENT]:
            serialized = self._compress(pickle.dumps(value))
            
            if self.redis_clients:
                for client in self.redis_clients:
                    try:
                        if ttl:
                            client.setex(f"cache:{key}", ttl, serialized)
                        else:
                            client.set(f"cache:{key}", serialized)
                    except Exception as e:
                        logger.error(f"Redis set error: {e}")
            
            if self.memcached_client and size < 1048576:  # Memcached 1MB limit
                try:
                    self.memcached_client.set(key, pickle.dumps(value), time=ttl or 0)
                except Exception as e:
                    logger.error(f"Memcached set error: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete from all cache tiers"""
        # Remove from L1
        with self.l1_cache.lock:
            if key in self.l1_cache.cache:
                del self.l1_cache.cache[key]
        
        # Remove from L2
        if self.redis_clients:
            for client in self.redis_clients:
                try:
                    client.delete(f"cache:{key}")
                except:
                    pass
        
        if self.memcached_client:
            try:
                self.memcached_client.delete(key)
            except:
                pass
    
    def _record_response_time(self, start_time: float) -> None:
        """Record response time for monitoring"""
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        self.response_times.append(response_time)
        self.stats.avg_response_time = statistics.mean(self.response_times)
    
    def cached(
        self,
        ttl: Optional[int] = 3600,
        tier: CacheTier = CacheTier.L1_MEMORY
    ):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_value = await self.get(key, tier)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(key, result, ttl, tier)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_key(func.__name__, *args, **kwargs)
                
                # Try to get from L1 cache (sync)
                cached_value = self.l1_cache.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache in L1
                self.l1_cache.put(key, result)
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def warm_cache(
        self,
        keys: List[str],
        loader_func: Callable,
        ttl: Optional[int] = 3600
    ) -> None:
        """Pre-warm cache with data"""
        tasks = []
        for key in keys:
            if not await self.get(key):
                # Load data
                data = await loader_func(key)
                if data:
                    tasks.append(self.set(key, data, ttl))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = self.stats.hits / max(self.stats.total_requests, 1)
        
        # Get memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": hit_rate,
            "evictions": self.stats.evictions,
            "total_requests": self.stats.total_requests,
            "avg_response_time_ms": self.stats.avg_response_time,
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "l1_cache_size": len(self.l1_cache.cache),
            "bloom_filter_size": self.bloom_filter.bit_array_size
        }
    
    async def optimize_cache(self) -> None:
        """Optimize cache based on usage patterns"""
        if not self.optimization_enabled:
            return
        
        stats = self.get_stats()
        
        # Adjust L1 cache size based on hit rate
        if stats["hit_rate"] < 0.5 and self.l1_cache.capacity < 50000:
            self.l1_cache.capacity = min(self.l1_cache.capacity * 2, 50000)
            logger.info(f"Increased L1 cache capacity to {self.l1_cache.capacity}")
        
        # Clear cold entries
        if stats["memory_usage_mb"] > 500:  # If using > 500MB
            # Clear least recently used entries
            with self.l1_cache.lock:
                entries_to_remove = len(self.l1_cache.cache) // 4
                for _ in range(entries_to_remove):
                    if self.l1_cache.cache:
                        self.l1_cache.cache.popitem(last=False)
                        self.stats.evictions += 1
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        # Clear from L1
        keys_to_remove = []
        with self.l1_cache.lock:
            for key in self.l1_cache.cache:
                if pattern in key:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self.l1_cache.cache[key]
        
        # Clear from Redis
        if self.redis_clients:
            for client in self.redis_clients:
                try:
                    for key in client.scan_iter(f"cache:*{pattern}*"):
                        client.delete(key)
                except Exception as e:
                    logger.error(f"Pattern invalidation error: {e}")

class QueryOptimizer:
    """Query optimization for database and API calls"""
    
    def __init__(self, cache_system: AdvancedCachingSystem):
        self.cache = cache_system
        self.query_patterns = {}
        self.execution_stats = {}
    
    async def optimize_query(
        self,
        query: str,
        params: Optional[Dict] = None
    ) -> Any:
        """Optimize and cache query results"""
        # Generate query fingerprint
        query_hash = hashlib.md5(f"{query}{params}".encode()).hexdigest()
        
        # Check cache
        cached = await self.cache.get(query_hash)
        if cached:
            return cached
        
        # Analyze query pattern
        pattern = self._extract_pattern(query)
        
        # Apply optimizations based on pattern
        if pattern in self.query_patterns:
            query = self.query_patterns[pattern](query, params)
        
        return query
    
    def _extract_pattern(self, query: str) -> str:
        """Extract query pattern for optimization"""
        # Simple pattern extraction (can be enhanced)
        import re
        pattern = re.sub(r'\b\d+\b', 'N', query)
        pattern = re.sub(r"'[^']*'", "'S'", pattern)
        return pattern

# Example usage
async def main():
    """Example usage of caching system"""
    
    # Initialize caching system
    cache = AdvancedCachingSystem(
        redis_urls=["redis://localhost:6379"],
        enable_clustering=False
    )
    
    # Example 1: Direct cache usage
    await cache.set("user:123", {"name": "John", "email": "john@example.com"}, ttl=3600)
    user = await cache.get("user:123")
    print(f"Cached user: {user}")
    
    # Example 2: Using cache decorator
    @cache.cached(ttl=600, tier=CacheTier.L2_DISTRIBUTED)
    async def expensive_operation(param: str) -> str:
        await asyncio.sleep(2)  # Simulate expensive operation
        return f"Result for {param}"
    
    # First call - will execute function
    result1 = await expensive_operation("test")
    print(f"First call: {result1}")
    
    # Second call - will use cache
    result2 = await expensive_operation("test")
    print(f"Second call (cached): {result2}")
    
    # Get statistics
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # Optimize cache
    await cache.optimize_cache()

if __name__ == "__main__":
    asyncio.run(main())