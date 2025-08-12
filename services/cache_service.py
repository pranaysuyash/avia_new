"""
Cache Service
Production caching with Redis and in-memory fallback
"""

import json
import pickle
import logging
import hashlib
from typing import Any, Optional, Union, List, Dict
from datetime import datetime, timedelta
import asyncio
from functools import wraps

import redis
from redis.exceptions import RedisError
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base cache backend interface"""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    async def clear(self) -> bool:
        raise NotImplementedError
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        raise NotImplementedError


class RedisBackend(CacheBackend):
    """Redis cache backend"""
    
    def __init__(self, url: str = "redis://localhost:6379", **kwargs):
        self.redis_client = None
        self.url = url
        self.kwargs = kwargs
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=False,
                **self.kwargs
            )
            await self.redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return self._deserialize(value)
            return None
        except RedisError as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            serialized = self._serialize(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)
            return True
        except RedisError as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis_client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            await self.redis_client.flushdb()
            return True
        except RedisError as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values"""
        try:
            values = await self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = self._deserialize(value)
            return result
        except RedisError as e:
            logger.error(f"Redis mget error: {e}")
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values"""
        try:
            # Serialize all values
            serialized = {k: self._serialize(v) for k, v in mapping.items()}
            
            # Use pipeline for atomic operation
            pipe = self.redis_client.pipeline()
            for key, value in serialized.items():
                if ttl:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)
            await pipe.execute()
            return True
        except RedisError as e:
            logger.error(f"Redis mset error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.redis_client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis increment error: {e}")
            return 0
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        try:
            return await self.redis_client.decrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis decrement error: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key"""
        try:
            return await self.redis_client.expire(key, ttl)
        except RedisError as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            return await self.redis_client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis ttl error: {e}")
            return -1
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if isinstance(value, (str, int, float)):
            return str(value).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try to decode as string first
            return value.decode('utf-8')
        except:
            # Fall back to pickle
            try:
                return pickle.loads(value)
            except:
                return value


class InMemoryBackend(CacheBackend):
    """In-memory cache backend (fallback)"""
    
    def __init__(self):
        self.cache = {}
        self.expiry = {}
        
    async def connect(self):
        """No connection needed for in-memory"""
        logger.info("In-memory cache initialized")
    
    async def disconnect(self):
        """Clear memory"""
        self.cache.clear()
        self.expiry.clear()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check expiry
        if key in self.expiry:
            if datetime.now() > self.expiry[key]:
                del self.cache[key]
                del self.expiry[key]
                return None
        
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        self.cache[key] = value
        
        if ttl:
            self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
        elif key in self.expiry:
            del self.expiry[key]
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.expiry:
                del self.expiry[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if key in self.expiry:
            if datetime.now() > self.expiry[key]:
                del self.cache[key]
                del self.expiry[key]
                return False
        return key in self.cache
    
    async def clear(self) -> bool:
        """Clear all cache"""
        self.cache.clear()
        self.expiry.clear()
        return True
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values"""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values"""
        for key, value in mapping.items():
            await self.set(key, value, ttl)
        return True


class CacheService:
    """High-level cache service with multiple backend support"""
    
    def __init__(self, backend: str = "redis", **backend_config):
        self.backend_name = backend
        self.backend = self._create_backend(backend, **backend_config)
        self.connected = False
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
    
    def _create_backend(self, backend: str, **config) -> CacheBackend:
        """Create cache backend"""
        if backend == "redis":
            return RedisBackend(
                url=config.get("url", "redis://localhost:6379"),
                **config
            )
        elif backend == "memory":
            return InMemoryBackend()
        else:
            raise ValueError(f"Unknown cache backend: {backend}")
    
    async def connect(self):
        """Connect to cache backend"""
        if not self.connected:
            await self.backend.connect()
            self.connected = True
    
    async def disconnect(self):
        """Disconnect from cache backend"""
        if self.connected:
            await self.backend.disconnect()
            self.connected = False
    
    async def get(
        self,
        key: str,
        default: Any = None,
        namespace: Optional[str] = None
    ) -> Any:
        """Get value from cache"""
        if not self.connected:
            await self.connect()
        
        # Add namespace to key
        if namespace:
            key = f"{namespace}:{key}"
        
        value = await self.backend.get(key)
        
        if value is not None:
            self.hits += 1
            logger.debug(f"Cache hit: {key}")
            return value
        else:
            self.misses += 1
            logger.debug(f"Cache miss: {key}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set value in cache"""
        if not self.connected:
            await self.connect()
        
        # Add namespace to key
        if namespace:
            key = f"{namespace}:{key}"
        
        result = await self.backend.set(key, value, ttl)
        
        if result:
            self.sets += 1
            logger.debug(f"Cache set: {key}")
        
        return result
    
    async def delete(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> bool:
        """Delete key from cache"""
        if not self.connected:
            await self.connect()
        
        # Add namespace to key
        if namespace:
            key = f"{namespace}:{key}"
        
        result = await self.backend.delete(key)
        
        if result:
            self.deletes += 1
            logger.debug(f"Cache delete: {key}")
        
        return result
    
    async def exists(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> bool:
        """Check if key exists"""
        if not self.connected:
            await self.connect()
        
        # Add namespace to key
        if namespace:
            key = f"{namespace}:{key}"
        
        return await self.backend.exists(key)
    
    async def clear(
        self,
        namespace: Optional[str] = None
    ) -> bool:
        """Clear cache (or namespace)"""
        if not self.connected:
            await self.connect()
        
        if namespace:
            # Clear only keys in namespace
            # This is a simplified implementation
            logger.warning(f"Namespace clearing not fully implemented for {self.backend_name}")
            return False
        else:
            return await self.backend.clear()
    
    async def get_many(
        self,
        keys: List[str],
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get multiple values"""
        if not self.connected:
            await self.connect()
        
        # Add namespace to keys
        if namespace:
            keys = [f"{namespace}:{k}" for k in keys]
        
        return await self.backend.get_many(keys)
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set multiple values"""
        if not self.connected:
            await self.connect()
        
        # Add namespace to keys
        if namespace:
            mapping = {f"{namespace}:{k}": v for k, v in mapping.items()}
        
        return await self.backend.set_many(mapping, ttl)
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create a string representation of arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            return hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": hit_rate,
            "backend": self.backend_name
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0


def cached(
    ttl: int = 3600,
    namespace: Optional[str] = None,
    key_prefix: Optional[str] = None
):
    """Decorator for caching function results"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check if object has cache_service
            if not hasattr(self, 'cache_service'):
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.extend([str(arg) for arg in args])
            cache_key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cached_value = await self.cache_service.get(
                cache_key,
                namespace=namespace
            )
            
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(self, *args, **kwargs)
            
            await self.cache_service.set(
                cache_key,
                result,
                ttl=ttl,
                namespace=namespace
            )
            
            return result
        
        return wrapper
    return decorator


# Synchronous Redis client for compatibility
class SyncCacheService:
    """Synchronous cache service wrapper"""
    
    def __init__(self, url: str = "redis://localhost:6379"):
        try:
            self.redis_client = redis.from_url(url, decode_responses=False)
            self.redis_client.ping()
            self.connected = True
            logger.info("Sync Redis cache connected")
        except Exception as e:
            logger.warning(f"Sync Redis connection failed, using memory cache: {e}")
            self.redis_client = None
            self.cache = {}
            self.connected = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
            except Exception as e:
                logger.error(f"Sync cache get error: {e}")
        else:
            return self.cache.get(key)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if self.redis_client:
            try:
                serialized = pickle.dumps(value)
                if ttl:
                    self.redis_client.setex(key, ttl, serialized)
                else:
                    self.redis_client.set(key, serialized)
                return True
            except Exception as e:
                logger.error(f"Sync cache set error: {e}")
        else:
            self.cache[key] = value
            return True
        return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.redis_client:
            try:
                return self.redis_client.delete(key) > 0
            except Exception as e:
                logger.error(f"Sync cache delete error: {e}")
        else:
            if key in self.cache:
                del self.cache[key]
                return True
        return False