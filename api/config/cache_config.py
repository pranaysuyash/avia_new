"""
Cache Configuration
Centralized configuration for Redis caching
"""

import os
from typing import Optional, Dict, Any

class CacheConfig:
    """Redis cache configuration"""
    
    # Connection settings
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # TTL settings (in seconds)
    DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", 3600))  # 1 hour
    TRANSCRIPTION_TTL = int(os.getenv("TRANSCRIPTION_CACHE_TTL", 86400))  # 24 hours
    USER_LIST_TTL = int(os.getenv("USER_LIST_CACHE_TTL", 300))  # 5 minutes
    SEARCH_TTL = int(os.getenv("SEARCH_CACHE_TTL", 1800))  # 30 minutes
    STATS_TTL = int(os.getenv("STATS_CACHE_TTL", 60))  # 1 minute
    
    # Cache size limits
    MAX_CACHE_SIZE_MB = int(os.getenv("MAX_CACHE_SIZE_MB", 1024))  # 1GB
    MAX_TRANSCRIPTION_SIZE_MB = int(os.getenv("MAX_TRANSCRIPTION_SIZE_MB", 50))  # 50MB per transcription
    
    # Cache warming settings
    WARM_CACHE_ON_STARTUP = os.getenv("WARM_CACHE_ON_STARTUP", "false").lower() == "true"
    WARM_CACHE_BATCH_SIZE = int(os.getenv("WARM_CACHE_BATCH_SIZE", 10))
    
    # Cache strategies
    CACHE_STRATEGIES = {
        "transcription": {
            "ttl": TRANSCRIPTION_TTL,
            "max_size_mb": MAX_TRANSCRIPTION_SIZE_MB,
            "compression": True,
            "serializer": "json"  # or "pickle" for complex objects
        },
        "user_data": {
            "ttl": USER_LIST_TTL,
            "max_size_mb": 5,
            "compression": False,
            "serializer": "json"
        },
        "search_results": {
            "ttl": SEARCH_TTL,
            "max_size_mb": 10,
            "compression": True,
            "serializer": "json"
        },
        "analytics": {
            "ttl": STATS_TTL,
            "max_size_mb": 1,
            "compression": False,
            "serializer": "json"
        }
    }
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL"""
        if cls.REDIS_URL:
            return cls.REDIS_URL
        
        auth = f":{cls.REDIS_PASSWORD}@" if cls.REDIS_PASSWORD else ""
        return f"redis://{auth}{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    @classmethod
    def get_connection_params(cls) -> Dict[str, Any]:
        """Get Redis connection parameters"""
        return {
            "host": cls.REDIS_HOST,
            "port": cls.REDIS_PORT,
            "db": cls.REDIS_DB,
            "password": cls.REDIS_PASSWORD,
            "decode_responses": False,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "socket_keepalive": True,
            "socket_keepalive_options": {},
            "max_connections": 50,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
    
    @classmethod
    def get_cache_key_prefix(cls, cache_type: str) -> str:
        """Get cache key prefix for different cache types"""
        prefixes = {
            "transcription": "trans:",
            "user": "user:",
            "search": "search:",
            "stats": "stats:",
            "session": "sess:",
            "temp": "tmp:"
        }
        return prefixes.get(cache_type, "cache:")
    
    @classmethod
    def should_cache(cls, data_size_mb: float, cache_type: str = "default") -> bool:
        """Determine if data should be cached based on size"""
        strategy = cls.CACHE_STRATEGIES.get(cache_type, {})
        max_size = strategy.get("max_size_mb", cls.MAX_TRANSCRIPTION_SIZE_MB)
        return data_size_mb <= max_size


class CacheKeyGenerator:
    """Generate consistent cache keys"""
    
    @staticmethod
    def transcription_key(file_hash: str, params_hash: str) -> str:
        """Generate key for transcription cache"""
        return f"{CacheConfig.get_cache_key_prefix('transcription')}{file_hash}:{params_hash}"
    
    @staticmethod
    def user_list_key(user_id: str, list_type: str, page: int = 0) -> str:
        """Generate key for user lists (transcripts, teams, etc.)"""
        return f"{CacheConfig.get_cache_key_prefix('user')}{user_id}:{list_type}:p{page}"
    
    @staticmethod
    def search_key(query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate key for search results"""
        import hashlib
        import json
        
        filter_str = json.dumps(filters or {}, sort_keys=True)
        query_hash = hashlib.md5(f"{query}:{filter_str}".encode()).hexdigest()[:16]
        return f"{CacheConfig.get_cache_key_prefix('search')}{query_hash}"
    
    @staticmethod
    def stats_key(stat_type: str, time_range: str = "day") -> str:
        """Generate key for statistics"""
        return f"{CacheConfig.get_cache_key_prefix('stats')}{stat_type}:{time_range}"
    
    @staticmethod
    def session_key(session_id: str) -> str:
        """Generate key for session data"""
        return f"{CacheConfig.get_cache_key_prefix('session')}{session_id}"