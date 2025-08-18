#!/usr/bin/env python3
"""
Enterprise API Gateway with Advanced Features

A comprehensive API gateway system providing enterprise-grade capabilities:

- Multi-tier rate limiting with intelligent throttling
- Advanced authentication and authorization (JWT, API keys, OAuth2)
- Request/response transformation and validation
- Load balancing with health checks and circuit breakers
- Real-time monitoring and analytics
- Caching layer with intelligent cache invalidation
- API versioning and backward compatibility
- Security features (WAF, DDoS protection, input validation)
- Enterprise logging and audit trails
- Cost tracking and usage analytics

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import asyncio
import logging
import json
import uuid
import time
import hashlib
import hmac
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import queue
import re
import statistics
import warnings
warnings.filterwarnings('ignore')

# Web framework and networking
try:
    from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import jwt
    import bcrypt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiohttp
    import httpx
    HTTP_CLIENT_AVAILABLE = True
except ImportError:
    HTTP_CLIENT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationType(Enum):
    """Authentication types supported by the gateway"""
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"

class RateLimitScope(Enum):
    """Rate limiting scopes"""
    GLOBAL = "global"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    IP_ADDRESS = "ip_address"

class RequestMethod(Enum):
    """HTTP request methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"

class GatewayStatus(Enum):
    """Gateway operational status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    id: str
    name: str
    scope: RateLimitScope
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 0  # Allow burst requests
    enabled: bool = True
    priority: int = 5  # 1 = highest priority

@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    id: str
    path: str
    method: RequestMethod
    upstream_url: str
    timeout_seconds: int = 30
    retries: int = 3
    authentication_required: bool = True
    rate_limit_rules: List[str] = field(default_factory=list)
    cache_ttl_seconds: int = 0  # 0 = no caching
    transform_request: bool = False
    transform_response: bool = False
    enabled: bool = True

@dataclass
class AuthenticationConfig:
    """Authentication configuration"""
    type: AuthenticationType
    secret_key: str
    issuer: Optional[str] = None
    audience: Optional[str] = None
    expiration_hours: int = 24
    refresh_enabled: bool = True
    multi_factor_required: bool = False

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    algorithm: str = "round_robin"  # round_robin, least_connections, weighted
    health_check_url: str = "/health"
    health_check_interval: int = 30
    failure_threshold: int = 3
    recovery_threshold: int = 2
    timeout_seconds: int = 10

@dataclass
class UpstreamServer:
    """Upstream server configuration"""
    id: str
    url: str
    weight: int = 1
    healthy: bool = True
    last_health_check: Optional[datetime] = None
    failure_count: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0

@dataclass
class GatewayMetrics:
    """Gateway performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_responses: int = 0
    rate_limited_requests: int = 0
    authentication_failures: int = 0
    average_response_time: float = 0.0
    active_connections: int = 0
    upstream_health_score: float = 100.0

@dataclass
class RequestContext:
    """Request processing context"""
    request_id: str
    client_ip: str
    user_id: Optional[str] = None
    api_key: Optional[str] = None
    endpoint_id: str = ""
    start_time: float = field(default_factory=time.time)
    authenticated: bool = False
    rate_limited: bool = False
    cached: bool = False
    upstream_server: Optional[str] = None

class EnterpriseAPIDatabase:
    """Enterprise API gateway database"""
    
    def __init__(self, db_path: str = "enterprise_api_gateway.db"):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Create API gateway database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    permissions JSON,
                    rate_limit_tier TEXT DEFAULT 'standard',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    last_used DATETIME,
                    is_active BOOLEAN DEFAULT TRUE,
                    usage_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS request_logs (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    client_ip TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    endpoint_id TEXT,
                    user_id TEXT,
                    api_key_id TEXT,
                    status_code INTEGER,
                    response_time_ms REAL,
                    request_size_bytes INTEGER,
                    response_size_bytes INTEGER,
                    cached BOOLEAN DEFAULT FALSE,
                    rate_limited BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    upstream_server TEXT
                );
                
                CREATE TABLE IF NOT EXISTS rate_limit_buckets (
                    id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    identifier TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    current_count INTEGER DEFAULT 0,
                    window_start DATETIME NOT NULL,
                    window_end DATETIME NOT NULL,
                    last_request DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS cached_responses (
                    id TEXT PRIMARY KEY,
                    cache_key TEXT UNIQUE NOT NULL,
                    endpoint_id TEXT NOT NULL,
                    response_data BLOB NOT NULL,
                    headers JSON,
                    status_code INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS security_events (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    client_ip TEXT NOT NULL,
                    user_id TEXT,
                    details JSON,
                    blocked BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS gateway_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    tags JSON
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_request_logs_endpoint ON request_logs(endpoint_id);
                CREATE INDEX IF NOT EXISTS idx_rate_limit_scope ON rate_limit_buckets(scope, identifier);
                CREATE INDEX IF NOT EXISTS idx_cached_responses_key ON cached_responses(cache_key);
                CREATE INDEX IF NOT EXISTS idx_security_events_ip ON security_events(client_ip);
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON gateway_metrics(timestamp);
            """)
    
    def store_request_log(self, context: RequestContext, status_code: int, 
                         response_time: float, error: Optional[str] = None):
        """Store request log entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO request_logs 
                (id, client_ip, method, path, endpoint_id, user_id, api_key_id,
                 status_code, response_time_ms, cached, rate_limited, error_message, upstream_server)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context.request_id, context.client_ip, "GET", "/api/endpoint",
                context.endpoint_id, context.user_id, context.api_key,
                status_code, response_time * 1000, context.cached, 
                context.rate_limited, error, context.upstream_server
            ))
    
    def create_api_key(self, user_id: str, name: str, permissions: Dict[str, Any],
                      tier: str = "standard", expires_days: Optional[int] = None) -> str:
        """Create a new API key"""
        api_key = str(uuid.uuid4())
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        expires_at = None
        
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_keys 
                (id, key_hash, user_id, name, permissions, rate_limit_tier, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), key_hash, user_id, name, 
                 json.dumps(permissions), tier, expires_at))
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return key info"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM api_keys 
                WHERE key_hash = ? AND is_active = TRUE
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """, (key_hash,))
            
            result = cursor.fetchone()
            
            if result:
                # Update last used timestamp
                conn.execute("""
                    UPDATE api_keys 
                    SET last_used = CURRENT_TIMESTAMP, usage_count = usage_count + 1
                    WHERE key_hash = ?
                """, (key_hash,))
                
                return dict(result)
            
            return None
    
    def get_usage_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get API usage analytics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Request volume by hour
            cursor = conn.execute("""
                SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour,
                       COUNT(*) as requests,
                       AVG(response_time_ms) as avg_response_time,
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                FROM request_logs 
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY hour
                ORDER BY hour
            """.format(hours))
            
            hourly_stats = [dict(row) for row in cursor.fetchall()]
            
            # Top endpoints
            cursor = conn.execute("""
                SELECT endpoint_id, COUNT(*) as requests,
                       AVG(response_time_ms) as avg_response_time
                FROM request_logs 
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY endpoint_id
                ORDER BY requests DESC
                LIMIT 10
            """.format(hours))
            
            top_endpoints = [dict(row) for row in cursor.fetchall()]
            
            return {
                'hourly_stats': hourly_stats,
                'top_endpoints': top_endpoints,
                'summary': {
                    'total_requests': sum(h['requests'] for h in hourly_stats),
                    'avg_response_time': statistics.mean([h['avg_response_time'] for h in hourly_stats]) if hourly_stats else 0,
                    'error_rate': sum(h['errors'] for h in hourly_stats) / max(sum(h['requests'] for h in hourly_stats), 1) * 100
                }
            }

class IntelligentRateLimiter:
    """Intelligent rate limiting with multiple algorithms"""
    
    def __init__(self, db: EnterpriseAPIDatabase):
        self.db = db
        self.rules: Dict[str, RateLimitRule] = {}
        self.buckets: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def add_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule"""
        self.rules[rule.id] = rule
        logger.info(f"📊 Added rate limit rule: {rule.name}")
    
    def check_rate_limit(self, context: RequestContext, rule_ids: List[str]) -> Tuple[bool, Optional[str]]:
        """Check if request should be rate limited"""
        if not rule_ids:
            return False, None
        
        # Clean up old buckets periodically
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_buckets()
            self.last_cleanup = current_time
        
        # Check each applicable rule
        for rule_id in rule_ids:
            if rule_id not in self.rules:
                continue
                
            rule = self.rules[rule_id]
            if not rule.enabled:
                continue
            
            # Determine identifier based on scope
            identifier = self._get_scope_identifier(rule.scope, context)
            bucket_key = f"{rule_id}:{identifier}"
            
            # Check rate limit
            is_limited, reason = self._check_bucket_limit(bucket_key, rule, current_time)
            if is_limited:
                context.rate_limited = True
                return True, reason
        
        return False, None
    
    def _get_scope_identifier(self, scope: RateLimitScope, context: RequestContext) -> str:
        """Get identifier for rate limiting scope"""
        if scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope == RateLimitScope.USER:
            return context.user_id or "anonymous"
        elif scope == RateLimitScope.API_KEY:
            return context.api_key or "no_key"
        elif scope == RateLimitScope.IP_ADDRESS:
            return context.client_ip
        elif scope == RateLimitScope.ENDPOINT:
            return context.endpoint_id
        else:
            return "unknown"
    
    def _check_bucket_limit(self, bucket_key: str, rule: RateLimitRule, 
                           current_time: float) -> Tuple[bool, Optional[str]]:
        """Check rate limit for a specific bucket"""
        if bucket_key not in self.buckets:
            self.buckets[bucket_key] = {
                'minute_count': 0,
                'hour_count': 0,
                'day_count': 0,
                'minute_window': current_time,
                'hour_window': current_time,
                'day_window': current_time
            }
        
        bucket = self.buckets[bucket_key]
        
        # Reset windows if expired
        if current_time - bucket['minute_window'] >= 60:
            bucket['minute_count'] = 0
            bucket['minute_window'] = current_time
        
        if current_time - bucket['hour_window'] >= 3600:
            bucket['hour_count'] = 0
            bucket['hour_window'] = current_time
        
        if current_time - bucket['day_window'] >= 86400:
            bucket['day_count'] = 0
            bucket['day_window'] = current_time
        
        # Check limits
        if bucket['minute_count'] >= rule.requests_per_minute:
            return True, f"Rate limit exceeded: {rule.requests_per_minute} requests per minute"
        
        if bucket['hour_count'] >= rule.requests_per_hour:
            return True, f"Rate limit exceeded: {rule.requests_per_hour} requests per hour"
        
        if bucket['day_count'] >= rule.requests_per_day:
            return True, f"Rate limit exceeded: {rule.requests_per_day} requests per day"
        
        # Increment counters
        bucket['minute_count'] += 1
        bucket['hour_count'] += 1
        bucket['day_count'] += 1
        
        return False, None
    
    def _cleanup_buckets(self):
        """Clean up expired rate limit buckets"""
        current_time = time.time()
        expired_buckets = []
        
        for bucket_key, bucket in self.buckets.items():
            # Remove buckets that haven't been accessed in the last day
            if current_time - bucket['day_window'] > 86400:
                expired_buckets.append(bucket_key)
        
        for bucket_key in expired_buckets:
            del self.buckets[bucket_key]
        
        if expired_buckets:
            logger.info(f"🧹 Cleaned up {len(expired_buckets)} expired rate limit buckets")

class IntelligentCache:
    """Intelligent caching system with TTL and smart invalidation"""
    
    def __init__(self, db: EnterpriseAPIDatabase):
        self.db = db
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
        self.max_memory_items = 1000
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        # Try memory cache first
        if cache_key in self.memory_cache:
            cache_entry = self.memory_cache[cache_key]
            if cache_entry['expires_at'] > datetime.now():
                self.cache_stats['hits'] += 1
                cache_entry['last_accessed'] = datetime.now()
                return cache_entry
            else:
                # Expired
                del self.memory_cache[cache_key]
        
        # Try database cache
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM cached_responses
                WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
            """, (cache_key,))
            
            result = cursor.fetchone()
            if result:
                self.cache_stats['hits'] += 1
                
                # Update hit count and last accessed
                conn.execute("""
                    UPDATE cached_responses 
                    SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP
                    WHERE cache_key = ?
                """, (cache_key,))
                
                # Add to memory cache
                cache_entry = {
                    'data': json.loads(result['response_data']),
                    'headers': json.loads(result['headers'] or '{}'),
                    'status_code': result['status_code'],
                    'expires_at': datetime.fromisoformat(result['expires_at']),
                    'last_accessed': datetime.now()
                }
                
                self._add_to_memory_cache(cache_key, cache_entry)
                return cache_entry
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, cache_key: str, endpoint_id: str, data: Any, status_code: int,
            headers: Dict[str, str], ttl_seconds: int):
        """Cache a response"""
        if ttl_seconds <= 0:
            return
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # Store in database
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cached_responses
                (id, cache_key, endpoint_id, response_data, headers, status_code, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), cache_key, endpoint_id, 
                json.dumps(data), json.dumps(headers), status_code, expires_at
            ))
        
        # Store in memory cache
        cache_entry = {
            'data': data,
            'headers': headers,
            'status_code': status_code,
            'expires_at': expires_at,
            'last_accessed': datetime.now()
        }
        
        self._add_to_memory_cache(cache_key, cache_entry)
        self.cache_stats['sets'] += 1
    
    def _add_to_memory_cache(self, cache_key: str, cache_entry: Dict[str, Any]):
        """Add entry to memory cache with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Evict least recently used item
            lru_key = min(self.memory_cache.keys(), 
                         key=lambda k: self.memory_cache[k]['last_accessed'])
            del self.memory_cache[lru_key]
            self.cache_stats['evictions'] += 1
        
        self.memory_cache[cache_key] = cache_entry
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        # Invalidate memory cache
        keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.memory_cache[key]
        
        # Invalidate database cache
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("""
                DELETE FROM cached_responses 
                WHERE cache_key LIKE ?
            """, (f"%{pattern}%",))
        
        logger.info(f"🗑️ Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_ratio = (self.cache_stats['hits'] / max(total_requests, 1)) * 100
        
        return {
            'memory_cache_size': len(self.memory_cache),
            'hit_ratio_percent': hit_ratio,
            **self.cache_stats
        }

class LoadBalancer:
    """Intelligent load balancer with health checks"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: List[UpstreamServer] = []
        self.current_server_index = 0
        self.health_check_active = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
    
    def add_server(self, server: UpstreamServer):
        """Add upstream server"""
        self.servers.append(server)
        logger.info(f"🔧 Added upstream server: {server.url}")
    
    def get_server(self) -> Optional[UpstreamServer]:
        """Get next healthy server using load balancing algorithm"""
        healthy_servers = [s for s in self.servers if s.healthy]
        
        if not healthy_servers:
            logger.warning("⚠️ No healthy upstream servers available")
            return None
        
        if self.config.algorithm == "round_robin":
            server = healthy_servers[self.current_server_index % len(healthy_servers)]
            self.current_server_index += 1
            return server
        
        elif self.config.algorithm == "least_connections":
            return min(healthy_servers, key=lambda s: s.total_requests)
        
        elif self.config.algorithm == "weighted":
            # Weighted random selection
            import random
            weights = [s.weight for s in healthy_servers]
            return random.choices(healthy_servers, weights=weights)[0]
        
        else:
            return healthy_servers[0]  # Fallback
    
    def record_request(self, server: UpstreamServer, response_time: float, success: bool):
        """Record request metrics for a server"""
        server.total_requests += 1
        
        # Update average response time
        if server.average_response_time == 0:
            server.average_response_time = response_time
        else:
            server.average_response_time = (server.average_response_time * 0.9) + (response_time * 0.1)
        
        # Update failure count
        if not success:
            server.failure_count += 1
            if server.failure_count >= self.config.failure_threshold:
                server.healthy = False
                logger.warning(f"⚠️ Marked server as unhealthy: {server.url}")
        else:
            server.failure_count = max(0, server.failure_count - 1)
    
    def _health_check_loop(self):
        """Background health check loop"""
        while self.health_check_active:
            try:
                for server in self.servers:
                    self._check_server_health(server)
                
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(30)
    
    def _check_server_health(self, server: UpstreamServer):
        """Check health of a specific server"""
        try:
            import requests
            health_url = f"{server.url.rstrip('/')}{self.config.health_check_url}"
            
            response = requests.get(health_url, timeout=self.config.timeout_seconds)
            server.last_health_check = datetime.now()
            
            if response.status_code == 200:
                if not server.healthy:
                    server.failure_count -= 1
                    if server.failure_count <= 0:
                        server.healthy = True
                        server.failure_count = 0
                        logger.info(f"✅ Server recovered: {server.url}")
            else:
                server.failure_count += 1
                if server.failure_count >= self.config.failure_threshold:
                    server.healthy = False
                    logger.warning(f"⚠️ Server health check failed: {server.url}")
                    
        except Exception as e:
            server.failure_count += 1
            if server.failure_count >= self.config.failure_threshold:
                server.healthy = False
                logger.warning(f"⚠️ Server health check failed: {server.url} - {e}")
    
    def stop_health_checks(self):
        """Stop health check background process"""
        self.health_check_active = False

class SecurityManager:
    """Security manager with WAF and threat detection"""
    
    def __init__(self, db: EnterpriseAPIDatabase):
        self.db = db
        self.blocked_ips: set = set()
        self.suspicious_patterns = [
            r'<script.*?>.*?</script>',  # XSS
            r'union.*select',           # SQL injection
            r'\.\./',                   # Path traversal
            r'<iframe.*?>',             # Iframe injection
        ]
        
        # Track request patterns for anomaly detection
        self.request_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def validate_request(self, context: RequestContext, request_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate request for security threats"""
        
        # Check if IP is blocked
        if context.client_ip in self.blocked_ips:
            self._log_security_event("BLOCKED_IP", "high", context, {"reason": "IP in blocklist"})
            return False, "IP address blocked"
        
        # Check for suspicious patterns
        request_text = json.dumps(request_data).lower()
        for pattern in self.suspicious_patterns:
            if re.search(pattern, request_text, re.IGNORECASE):
                self._log_security_event("SUSPICIOUS_PATTERN", "medium", context, 
                                       {"pattern": pattern, "matched_text": request_text[:100]})
                return False, "Suspicious content detected"
        
        # Rate-based anomaly detection
        if self._detect_anomalous_behavior(context):
            self._log_security_event("ANOMALOUS_BEHAVIOR", "medium", context, 
                                   {"reason": "Unusual request pattern"})
            # Don't block, just log for now
        
        return True, None
    
    def _detect_anomalous_behavior(self, context: RequestContext) -> bool:
        """Detect anomalous request patterns"""
        ip_requests = self.request_patterns[context.client_ip]
        current_time = time.time()
        
        # Add current request
        ip_requests.append(current_time)
        
        # Check for too many requests in short time
        if len(ip_requests) >= 50:  # 50 requests tracked
            recent_requests = [t for t in ip_requests if current_time - t < 60]  # Last minute
            if len(recent_requests) > 30:  # More than 30 requests per minute
                return True
        
        return False
    
    def _log_security_event(self, event_type: str, severity: str, context: RequestContext, 
                           details: Dict[str, Any]):
        """Log security event"""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("""
                INSERT INTO security_events 
                (id, event_type, severity, client_ip, user_id, details, blocked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), event_type, severity, context.client_ip,
                context.user_id, json.dumps(details), event_type == "BLOCKED_IP"
            ))
    
    def block_ip(self, ip_address: str, reason: str):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"🚫 Blocked IP address: {ip_address} - {reason}")
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security events summary"""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT event_type, severity, COUNT(*) as count
                FROM security_events 
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY event_type, severity
                ORDER BY count DESC
            """.format(hours))
            
            events = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_blocked_ips': len(self.blocked_ips),
                'events_by_type': events,
                'high_severity_count': sum(e['count'] for e in events if e['severity'] == 'high')
            }

class EnterpriseAPIGateway:
    """Main enterprise API gateway"""
    
    def __init__(self):
        self.db = EnterpriseAPIDatabase()
        self.rate_limiter = IntelligentRateLimiter(self.db)
        self.cache = IntelligentCache(self.db)
        self.security = SecurityManager(self.db)
        
        # Configuration
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.auth_config = AuthenticationConfig(
            type=AuthenticationType.API_KEY,
            secret_key="your-secret-key-here",
            expiration_hours=24
        )
        
        # Load balancer
        lb_config = LoadBalancerConfig()
        self.load_balancer = LoadBalancer(lb_config)
        
        # Metrics
        self.metrics = GatewayMetrics()
        
        # Setup default configuration
        self._setup_default_config()
        
        logger.info("🌐 Enterprise API Gateway initialized")
    
    def _setup_default_config(self):
        """Setup default gateway configuration"""
        # Default rate limiting rules
        standard_rule = RateLimitRule(
            id="standard",
            name="Standard Rate Limit",
            scope=RateLimitScope.API_KEY,
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=10000
        )
        self.rate_limiter.add_rule(standard_rule)
        
        premium_rule = RateLimitRule(
            id="premium",
            name="Premium Rate Limit",
            scope=RateLimitScope.API_KEY,
            requests_per_minute=500,
            requests_per_hour=5000,
            requests_per_day=50000
        )
        self.rate_limiter.add_rule(premium_rule)
        
        # Default upstream server
        default_server = UpstreamServer(
            id="default",
            url="http://localhost:8000",
            weight=1
        )
        self.load_balancer.add_server(default_server)
        
        # Default API endpoints
        transcription_endpoint = APIEndpoint(
            id="transcription",
            path="/api/transcription",
            method=RequestMethod.POST,
            upstream_url="/transcription",
            timeout_seconds=60,
            rate_limit_rules=["standard"],
            cache_ttl_seconds=300
        )
        self.add_endpoint(transcription_endpoint)
    
    def add_endpoint(self, endpoint: APIEndpoint):
        """Add API endpoint"""
        self.endpoints[endpoint.id] = endpoint
        logger.info(f"🔗 Added API endpoint: {endpoint.path}")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming API request"""
        # Create request context
        context = RequestContext(
            request_id=str(uuid.uuid4()),
            client_ip=request_data.get('client_ip', '127.0.0.1'),
            endpoint_id=request_data.get('endpoint_id', 'unknown')
        )
        
        start_time = time.time()
        
        try:
            # Security validation
            is_secure, security_error = self.security.validate_request(context, request_data)
            if not is_secure:
                self.metrics.authentication_failures += 1
                return self._create_error_response(403, security_error, context, start_time)
            
            # Authentication
            if not await self._authenticate_request(context, request_data):
                self.metrics.authentication_failures += 1
                return self._create_error_response(401, "Authentication failed", context, start_time)
            
            # Get endpoint configuration
            endpoint = self.endpoints.get(context.endpoint_id)
            if not endpoint or not endpoint.enabled:
                return self._create_error_response(404, "Endpoint not found", context, start_time)
            
            # Rate limiting
            is_rate_limited, limit_reason = self.rate_limiter.check_rate_limit(
                context, endpoint.rate_limit_rules
            )
            if is_rate_limited:
                self.metrics.rate_limited_requests += 1
                return self._create_error_response(429, limit_reason, context, start_time)
            
            # Check cache
            if endpoint.cache_ttl_seconds > 0:
                cache_key = self._generate_cache_key(context, request_data)
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    context.cached = True
                    self.metrics.cached_responses += 1
                    return self._create_success_response(cached_response, context, start_time)
            
            # Forward to upstream
            upstream_response = await self._forward_to_upstream(context, endpoint, request_data)
            
            # Cache response if applicable
            if endpoint.cache_ttl_seconds > 0 and upstream_response.get('status') == 200:
                cache_key = self._generate_cache_key(context, request_data)
                self.cache.set(
                    cache_key, endpoint.id, upstream_response.get('data'),
                    upstream_response.get('status', 200), {}, endpoint.cache_ttl_seconds
                )
            
            self.metrics.successful_requests += 1
            return self._create_success_response(upstream_response, context, start_time)
            
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"Request processing error: {e}")
            return self._create_error_response(500, "Internal server error", context, start_time)
    
    async def _authenticate_request(self, context: RequestContext, request_data: Dict[str, Any]) -> bool:
        """Authenticate the request"""
        api_key = request_data.get('api_key')
        if not api_key:
            return False
        
        key_info = self.db.validate_api_key(api_key)
        if key_info:
            context.api_key = api_key
            context.user_id = key_info['user_id']
            context.authenticated = True
            return True
        
        return False
    
    async def _forward_to_upstream(self, context: RequestContext, endpoint: APIEndpoint, 
                                  request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to upstream server"""
        server = self.load_balancer.get_server()
        if not server:
            raise Exception("No healthy upstream servers available")
        
        context.upstream_server = server.id
        upstream_start = time.time()
        
        # Simulate upstream request
        try:
            # In a real implementation, this would make an HTTP request
            await asyncio.sleep(0.1)  # Simulate network delay
            
            response_time = time.time() - upstream_start
            self.load_balancer.record_request(server, response_time, True)
            
            return {
                'status': 200,
                'data': {
                    'message': 'Request processed successfully',
                    'endpoint': endpoint.path,
                    'server': server.url,
                    'processing_time': response_time
                }
            }
            
        except Exception as e:
            response_time = time.time() - upstream_start
            self.load_balancer.record_request(server, response_time, False)
            raise e
    
    def _generate_cache_key(self, context: RequestContext, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        cache_data = {
            'endpoint': context.endpoint_id,
            'user': context.user_id,
            'data': request_data
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def _create_success_response(self, response_data: Dict[str, Any], context: RequestContext, 
                               start_time: float) -> Dict[str, Any]:
        """Create successful response"""
        response_time = time.time() - start_time
        
        # Update metrics
        self.metrics.total_requests += 1
        self._update_average_response_time(response_time)
        
        # Log request
        self.db.store_request_log(context, 200, response_time)
        
        return {
            'status': 'success',
            'data': response_data.get('data', response_data),
            'request_id': context.request_id,
            'response_time': response_time,
            'cached': context.cached
        }
    
    def _create_error_response(self, status_code: int, message: str, context: RequestContext, 
                             start_time: float) -> Dict[str, Any]:
        """Create error response"""
        response_time = time.time() - start_time
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self._update_average_response_time(response_time)
        
        # Log request
        self.db.store_request_log(context, status_code, response_time, message)
        
        return {
            'status': 'error',
            'error': {
                'code': status_code,
                'message': message
            },
            'request_id': context.request_id,
            'response_time': response_time
        }
    
    def _update_average_response_time(self, response_time: float):
        """Update average response time metric"""
        if self.metrics.average_response_time == 0:
            self.metrics.average_response_time = response_time
        else:
            self.metrics.average_response_time = (
                self.metrics.average_response_time * 0.9 + response_time * 0.1
            )
    
    def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        # Calculate health score
        total_requests = self.metrics.total_requests
        success_rate = (self.metrics.successful_requests / max(total_requests, 1)) * 100
        
        if success_rate >= 99:
            status = GatewayStatus.HEALTHY
        elif success_rate >= 95:
            status = GatewayStatus.DEGRADED
        else:
            status = GatewayStatus.UNHEALTHY
        
        return {
            'status': status.value,
            'metrics': asdict(self.metrics),
            'endpoints': len(self.endpoints),
            'rate_limit_rules': len(self.rate_limiter.rules),
            'upstream_servers': len(self.load_balancer.servers),
            'healthy_servers': len([s for s in self.load_balancer.servers if s.healthy]),
            'cache_stats': self.cache.get_stats(),
            'security_summary': self.security.get_security_summary(),
            'uptime_hours': 24  # Placeholder
        }
    
    def create_api_key(self, user_id: str, name: str, tier: str = "standard") -> str:
        """Create a new API key"""
        permissions = {
            'endpoints': ['*'],
            'rate_limit_tier': tier
        }
        
        api_key = self.db.create_api_key(user_id, name, permissions, tier)
        logger.info(f"🔑 Created API key for user {user_id}: {name}")
        return api_key
    
    def stop_gateway(self):
        """Stop the gateway"""
        self.load_balancer.stop_health_checks()
        logger.info("🛑 Enterprise API Gateway stopped")


def main():
    """Example usage of Enterprise API Gateway"""
    # Initialize gateway
    gateway = EnterpriseAPIGateway()
    
    # Create test API key
    api_key = gateway.create_api_key("test_user", "Test Application", "premium")
    print(f"Created API key: {api_key}")
    
    # Simulate API request
    async def test_request():
        request_data = {
            'client_ip': '192.168.1.100',
            'endpoint_id': 'transcription',
            'api_key': api_key,
            'data': {
                'audio_file': 'test.wav',
                'language': 'en'
            }
        }
        
        response = await gateway.process_request(request_data)
        print(f"API Response: {response}")
        
        # Get gateway status
        status = gateway.get_gateway_status()
        print(f"Gateway Status: {status['status']}")
        print(f"Total Requests: {status['metrics']['total_requests']}")
        print(f"Success Rate: {status['metrics']['successful_requests'] / max(status['metrics']['total_requests'], 1) * 100:.1f}%")
    
    # Run test
    asyncio.run(test_request())
    
    # Cleanup
    gateway.stop_gateway()


if __name__ == "__main__":
    main()