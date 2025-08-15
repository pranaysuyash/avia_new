#!/usr/bin/env python3
"""
Whisper API Optimization and Monitoring System
Implements request batching, caching, monitoring, and quality assessment for OpenAI Whisper API.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import redis
import openai
from openai import OpenAI
import backoff
import psutil
import threading
from collections import defaultdict, deque
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WhisperRequest:
    """Represents a Whisper API request."""
    audio_file_path: str
    language: Optional[str] = None
    prompt: Optional[str] = None
    temperature: float = 0.0
    response_format: str = "json"
    timestamp_granularities: List[str] = None
    request_id: str = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    created_at: datetime = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = self._generate_request_id()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.timestamp_granularities is None:
            self.timestamp_granularities = ["segment"]
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID based on file content and parameters."""
        content = f"{self.audio_file_path}_{self.language}_{self.prompt}_{self.temperature}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class WhisperResponse:
    """Represents a Whisper API response with metadata."""
    request_id: str
    text: str
    segments: List[Dict] = None
    language: str = None
    duration: float = None
    confidence_score: float = None
    processing_time: float = None
    cached: bool = False
    api_cost: float = None
    quality_score: float = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class APIMetrics:
    """API usage metrics and statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    total_processing_time: float = 0.0
    total_api_cost: float = 0.0
    average_confidence: float = 0.0
    average_quality: float = 0.0
    requests_per_minute: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0


class WhisperCache:
    """Redis-based caching system for Whisper API responses."""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, 
                 redis_db: int = 0, ttl_hours: int = 24):
        """Initialize Redis cache connection."""
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db,
                decode_responses=True
            )
            self.redis_client.ping()  # Test connection
            self.ttl_seconds = ttl_hours * 3600
            logger.info(f"Connected to Redis cache at {redis_host}:{redis_port}")
        except redis.ConnectionError:
            logger.warning("Redis not available, using in-memory cache")
            self.redis_client = None
            self.memory_cache = {}
    
    def _generate_cache_key(self, request: WhisperRequest) -> str:
        """Generate cache key from request parameters."""
        # Include file hash for content-based caching
        try:
            with open(request.audio_file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:16]
        except Exception:
            file_hash = "unknown"
        
        key_data = {
            'file_hash': file_hash,
            'language': request.language,
            'prompt': request.prompt,
            'temperature': request.temperature,
            'response_format': request.response_format
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"whisper_cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def get(self, request: WhisperRequest) -> Optional[WhisperResponse]:
        """Retrieve cached response for request."""
        cache_key = self._generate_cache_key(request)
        
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    response_data = json.loads(cached_data)
                    response = WhisperResponse(**response_data)
                    response.cached = True
                    logger.info(f"Cache hit for request {request.request_id}")
                    return response
            else:
                # In-memory cache fallback
                if cache_key in self.memory_cache:
                    response_data = self.memory_cache[cache_key]
                    response = WhisperResponse(**response_data)
                    response.cached = True
                    return response
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    def set(self, request: WhisperRequest, response: WhisperResponse):
        """Cache response for request."""
        cache_key = self._generate_cache_key(request)
        
        try:
            # Prepare response data for caching
            response_data = asdict(response)
            response_data['created_at'] = response.created_at.isoformat()
            
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    self.ttl_seconds, 
                    json.dumps(response_data)
                )
            else:
                # In-memory cache fallback
                self.memory_cache[cache_key] = response_data
            
            logger.info(f"Cached response for request {request.request_id}")
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries (for in-memory cache)."""
        if not self.redis_client and hasattr(self, 'memory_cache'):
            current_time = datetime.utcnow()
            expired_keys = []
            
            for key, data in self.memory_cache.items():
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                    if current_time - created_at > timedelta(hours=24):
                        expired_keys.append(key)
                except Exception:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired cache entries")


class WhisperQualityAssessment:
    """Quality assessment system for Whisper transcriptions."""
    
    def __init__(self):
        self.quality_thresholds = {
            'confidence_min': 0.7,
            'segment_consistency_min': 0.8,
            'language_consistency_min': 0.9,
            'silence_ratio_max': 0.3
        }
    
    def assess_quality(self, response: WhisperResponse, 
                      audio_duration: float = None) -> float:
        """Assess transcription quality and return score (0-1)."""
        quality_factors = []
        
        # 1. Confidence score assessment
        if response.confidence_score is not None:
            confidence_factor = min(response.confidence_score / self.quality_thresholds['confidence_min'], 1.0)
            quality_factors.append(confidence_factor * 0.3)
        
        # 2. Segment consistency assessment
        if response.segments:
            segment_confidences = []
            for segment in response.segments:
                if 'avg_logprob' in segment:
                    # Convert log probability to confidence-like score
                    confidence = min(abs(segment['avg_logprob']) / 0.5, 1.0)
                    segment_confidences.append(confidence)
            
            if segment_confidences:
                consistency = 1.0 - statistics.stdev(segment_confidences) if len(segment_confidences) > 1 else 1.0
                quality_factors.append(consistency * 0.25)
        
        # 3. Text quality indicators
        text_quality = self._assess_text_quality(response.text)
        quality_factors.append(text_quality * 0.25)
        
        # 4. Duration consistency
        if audio_duration and response.segments:
            total_segment_duration = sum(
                segment.get('end', 0) - segment.get('start', 0) 
                for segment in response.segments
            )
            duration_ratio = min(total_segment_duration / audio_duration, 1.0)
            quality_factors.append(duration_ratio * 0.2)
        
        # Calculate overall quality score
        overall_quality = sum(quality_factors) if quality_factors else 0.5
        return min(max(overall_quality, 0.0), 1.0)
    
    def _assess_text_quality(self, text: str) -> float:
        """Assess text quality based on various indicators."""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        quality_indicators = []
        
        # 1. Length reasonableness (not too short or repetitive)
        length_score = min(len(text) / 100, 1.0)  # Normalize to reasonable length
        quality_indicators.append(length_score * 0.3)
        
        # 2. Character diversity
        unique_chars = len(set(text.lower()))
        char_diversity = min(unique_chars / 20, 1.0)  # Expect at least 20 unique chars
        quality_indicators.append(char_diversity * 0.2)
        
        # 3. Word diversity
        words = text.lower().split()
        if words:
            unique_words = len(set(words))
            word_diversity = min(unique_words / len(words), 1.0)
            quality_indicators.append(word_diversity * 0.3)
        
        # 4. Punctuation presence (indicates proper formatting)
        punctuation_chars = sum(1 for char in text if char in '.,!?;:')
        punctuation_score = min(punctuation_chars / (len(text) / 50), 1.0)
        quality_indicators.append(punctuation_score * 0.2)
        
        return sum(quality_indicators)
    
    def validate_transcription(self, response: WhisperResponse) -> Dict[str, Any]:
        """Validate transcription and return detailed assessment."""
        validation_results = {
            'is_valid': True,
            'quality_score': response.quality_score or 0.0,
            'issues': [],
            'recommendations': []
        }
        
        # Check for common issues
        if not response.text or len(response.text.strip()) < 10:
            validation_results['issues'].append("Transcription too short")
            validation_results['is_valid'] = False
        
        if response.confidence_score and response.confidence_score < self.quality_thresholds['confidence_min']:
            validation_results['issues'].append("Low confidence score")
            validation_results['recommendations'].append("Consider re-processing with different parameters")
        
        # Check for repetitive content
        words = response.text.lower().split()
        if len(words) > 10:
            word_counts = defaultdict(int)
            for word in words:
                word_counts[word] += 1
            
            max_repetition = max(word_counts.values()) if word_counts else 0
            if max_repetition > len(words) * 0.3:  # More than 30% repetition
                validation_results['issues'].append("Highly repetitive content detected")
                validation_results['recommendations'].append("Check audio quality and consider noise reduction")
        
        return validation_results


class WhisperAPIMonitor:
    """Monitoring system for Whisper API usage and performance."""
    
    def __init__(self, window_size_minutes: int = 60):
        self.window_size = window_size_minutes
        self.metrics = APIMetrics()
        self.request_history = deque(maxlen=1000)  # Keep last 1000 requests
        self.error_history = deque(maxlen=100)     # Keep last 100 errors
        self.performance_history = deque(maxlen=500)  # Keep performance data
        self.alerts = []
        
        # Thresholds for alerting
        self.alert_thresholds = {
            'error_rate_max': 0.1,      # 10% error rate
            'response_time_max': 30.0,   # 30 seconds
            'queue_size_max': 50,        # 50 pending requests
            'cost_per_hour_max': 100.0   # $100 per hour
        }
    
    def record_request(self, request: WhisperRequest, response: WhisperResponse = None, 
                      error: Exception = None):
        """Record API request metrics."""
        timestamp = datetime.utcnow()
        
        # Update basic metrics
        self.metrics.total_requests += 1
        
        if error:
            self.metrics.failed_requests += 1
            self.error_history.append({
                'timestamp': timestamp,
                'request_id': request.request_id,
                'error': str(error),
                'error_type': type(error).__name__
            })
        elif response:
            self.metrics.successful_requests += 1
            
            if response.cached:
                self.metrics.cached_requests += 1
            
            if response.processing_time:
                self.metrics.total_processing_time += response.processing_time
            
            if response.api_cost:
                self.metrics.total_api_cost += response.api_cost
            
            if response.confidence_score:
                # Update running average
                total_successful = self.metrics.successful_requests
                current_avg = self.metrics.average_confidence
                self.metrics.average_confidence = (
                    (current_avg * (total_successful - 1) + response.confidence_score) / total_successful
                )
            
            if response.quality_score:
                # Update running average
                total_successful = self.metrics.successful_requests
                current_avg = self.metrics.average_quality
                self.metrics.average_quality = (
                    (current_avg * (total_successful - 1) + response.quality_score) / total_successful
                )
        
        # Record request in history
        self.request_history.append({
            'timestamp': timestamp,
            'request_id': request.request_id,
            'success': error is None,
            'cached': response.cached if response else False,
            'processing_time': response.processing_time if response else None,
            'cost': response.api_cost if response else None
        })
        
        # Update calculated metrics
        self._update_calculated_metrics()
        
        # Check for alerts
        self._check_alerts()
    
    def _update_calculated_metrics(self):
        """Update calculated metrics based on recent history."""
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(minutes=self.window_size)
        
        # Filter recent requests
        recent_requests = [
            req for req in self.request_history 
            if req['timestamp'] >= window_start
        ]
        
        if recent_requests:
            # Calculate requests per minute
            time_span_minutes = self.window_size
            self.metrics.requests_per_minute = len(recent_requests) / time_span_minutes
            
            # Calculate error rate
            failed_requests = sum(1 for req in recent_requests if not req['success'])
            self.metrics.error_rate = failed_requests / len(recent_requests)
            
            # Calculate cache hit rate
            cached_requests = sum(1 for req in recent_requests if req.get('cached', False))
            self.metrics.cache_hit_rate = cached_requests / len(recent_requests)
    
    def _check_alerts(self):
        """Check for alert conditions and generate alerts."""
        current_time = datetime.utcnow()
        
        # Error rate alert
        if self.metrics.error_rate > self.alert_thresholds['error_rate_max']:
            self.alerts.append({
                'timestamp': current_time,
                'type': 'high_error_rate',
                'message': f"Error rate {self.metrics.error_rate:.2%} exceeds threshold",
                'severity': 'high'
            })
        
        # Response time alert
        if self.request_history:
            recent_times = [
                req['processing_time'] for req in list(self.request_history)[-10:] 
                if req['processing_time'] is not None
            ]
            if recent_times:
                avg_response_time = statistics.mean(recent_times)
                if avg_response_time > self.alert_thresholds['response_time_max']:
                    self.alerts.append({
                        'timestamp': current_time,
                        'type': 'slow_response',
                        'message': f"Average response time {avg_response_time:.1f}s exceeds threshold",
                        'severity': 'medium'
                    })
        
        # Keep only recent alerts (last 24 hours)
        day_ago = current_time - timedelta(hours=24)
        self.alerts = [alert for alert in self.alerts if alert['timestamp'] >= day_ago]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            'basic_metrics': asdict(self.metrics),
            'recent_alerts': self.alerts[-10:],  # Last 10 alerts
            'system_health': self._get_system_health(),
            'performance_trends': self._get_performance_trends()
        }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators."""
        return {
            'status': 'healthy' if self.metrics.error_rate < 0.05 else 'degraded',
            'uptime_percentage': (self.metrics.successful_requests / max(self.metrics.total_requests, 1)) * 100,
            'average_response_time': (
                self.metrics.total_processing_time / max(self.metrics.successful_requests, 1)
            ),
            'cost_efficiency': self.metrics.cache_hit_rate * 100,
            'quality_score': self.metrics.average_quality * 100
        }
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trend analysis."""
        if len(self.request_history) < 10:
            return {'insufficient_data': True}
        
        recent_requests = list(self.request_history)[-50:]  # Last 50 requests
        
        # Calculate trends
        response_times = [req['processing_time'] for req in recent_requests if req['processing_time']]
        success_rates = []
        
        # Calculate success rate over time (in chunks of 10)
        for i in range(0, len(recent_requests), 10):
            chunk = recent_requests[i:i+10]
            success_rate = sum(1 for req in chunk if req['success']) / len(chunk)
            success_rates.append(success_rate)
        
        return {
            'response_time_trend': 'improving' if len(response_times) > 1 and response_times[-1] < response_times[0] else 'stable',
            'success_rate_trend': 'improving' if len(success_rates) > 1 and success_rates[-1] > success_rates[0] else 'stable',
            'average_response_time': statistics.mean(response_times) if response_times else 0,
            'response_time_variance': statistics.stdev(response_times) if len(response_times) > 1 else 0
        }


class WhisperAPIOptimizer:
    """Main optimization system for Whisper API requests."""
    
    def __init__(self, api_key: str, cache_config: Dict = None, 
                 monitor_config: Dict = None):
        """Initialize the Whisper API optimizer."""
        self.client = OpenAI(api_key=api_key)
        
        # Initialize components
        cache_config = cache_config or {}
        self.cache = WhisperCache(**cache_config)
        
        monitor_config = monitor_config or {}
        self.monitor = WhisperAPIMonitor(**monitor_config)
        
        self.quality_assessor = WhisperQualityAssessment()
        
        # Request batching
        self.batch_queue = []
        self.batch_size = 5
        self.batch_timeout = 30  # seconds
        self.processing_lock = threading.Lock()
        
        # Rate limiting
        self.rate_limit_requests_per_minute = 50
        self.request_timestamps = deque(maxlen=self.rate_limit_requests_per_minute)
        
        logger.info("Whisper API Optimizer initialized")
    
    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError),
        max_tries=3,
        max_time=300
    )
    async def _make_api_request(self, request: WhisperRequest) -> WhisperResponse:
        """Make actual API request with retry logic."""
        start_time = time.time()
        
        try:
            # Check rate limiting
            self._enforce_rate_limit()
            
            # Prepare API parameters
            api_params = {
                'model': 'whisper-1',
                'response_format': request.response_format,
                'temperature': request.temperature
            }
            
            if request.language:
                api_params['language'] = request.language
            
            if request.prompt:
                api_params['prompt'] = request.prompt
            
            if request.timestamp_granularities:
                api_params['timestamp_granularities'] = request.timestamp_granularities
            
            # Make API request
            with open(request.audio_file_path, 'rb') as audio_file:
                api_response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **api_params
                )
            
            processing_time = time.time() - start_time
            
            # Calculate estimated cost (approximate)
            file_size_mb = Path(request.audio_file_path).stat().st_size / (1024 * 1024)
            estimated_cost = file_size_mb * 0.006  # $0.006 per minute, rough estimate
            
            # Create response object
            response = WhisperResponse(
                request_id=request.request_id,
                text=api_response.text,
                language=getattr(api_response, 'language', None),
                processing_time=processing_time,
                api_cost=estimated_cost,
                created_at=datetime.utcnow()
            )
            
            # Extract segments if available
            if hasattr(api_response, 'segments') and api_response.segments:
                response.segments = [
                    {
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text,
                        'avg_logprob': getattr(segment, 'avg_logprob', None)
                    }
                    for segment in api_response.segments
                ]
            
            # Assess quality
            response.quality_score = self.quality_assessor.assess_quality(response)
            
            # Calculate confidence score from segments
            if response.segments:
                confidences = [
                    abs(segment.get('avg_logprob', -1.0)) 
                    for segment in response.segments 
                    if segment.get('avg_logprob') is not None
                ]
                if confidences:
                    response.confidence_score = 1.0 - statistics.mean(confidences)
            
            return response
            
        except Exception as e:
            logger.error(f"API request failed for {request.request_id}: {e}")
            raise
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting for API requests."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        while self.request_timestamps and current_time - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()
        
        # Check if we're at the rate limit
        if len(self.request_timestamps) >= self.rate_limit_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
        
        # Record this request timestamp
        self.request_timestamps.append(current_time)
    
    async def process_request(self, request: WhisperRequest) -> WhisperResponse:
        """Process a single Whisper API request with optimization."""
        logger.info(f"Processing request {request.request_id}")
        
        try:
            # Check cache first
            cached_response = self.cache.get(request)
            if cached_response:
                self.monitor.record_request(request, cached_response)
                return cached_response
            
            # Make API request
            response = await self._make_api_request(request)
            
            # Cache the response
            self.cache.set(request, response)
            
            # Record metrics
            self.monitor.record_request(request, response)
            
            logger.info(f"Request {request.request_id} completed successfully")
            return response
            
        except Exception as e:
            self.monitor.record_request(request, error=e)
            logger.error(f"Request {request.request_id} failed: {e}")
            raise
    
    async def process_batch(self, requests: List[WhisperRequest]) -> List[WhisperResponse]:
        """Process multiple requests with batching optimization."""
        logger.info(f"Processing batch of {len(requests)} requests")
        
        # Sort by priority
        requests.sort(key=lambda r: r.priority)
        
        # Process requests concurrently (with rate limiting)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def process_with_semaphore(request):
            async with semaphore:
                return await self.process_request(request)
        
        tasks = [process_with_semaphore(request) for request in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in responses
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch request {requests[i].request_id} failed: {response}")
                # Create error response
                error_response = WhisperResponse(
                    request_id=requests[i].request_id,
                    text="",
                    quality_score=0.0,
                    created_at=datetime.utcnow()
                )
                valid_responses.append(error_response)
            else:
                valid_responses.append(response)
        
        return valid_responses
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        return {
            'cache_stats': {
                'type': 'redis' if self.cache.redis_client else 'memory',
                'hit_rate': self.monitor.metrics.cache_hit_rate,
                'total_cached': self.monitor.metrics.cached_requests
            },
            'performance_stats': self.monitor.get_metrics_summary(),
            'system_resources': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            },
            'api_efficiency': {
                'cost_per_request': (
                    self.monitor.metrics.total_api_cost / max(self.monitor.metrics.successful_requests, 1)
                ),
                'average_processing_time': (
                    self.monitor.metrics.total_processing_time / max(self.monitor.metrics.successful_requests, 1)
                ),
                'success_rate': (
                    self.monitor.metrics.successful_requests / max(self.monitor.metrics.total_requests, 1)
                )
            }
        }
    
    def cleanup_cache(self):
        """Clean up expired cache entries."""
        self.cache.clear_expired()
        logger.info("Cache cleanup completed")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check cache health
        try:
            if self.cache.redis_client:
                self.cache.redis_client.ping()
                health_status['components']['cache'] = 'healthy'
            else:
                health_status['components']['cache'] = 'memory_fallback'
        except Exception as e:
            health_status['components']['cache'] = f'unhealthy: {e}'
            health_status['status'] = 'degraded'
        
        # Check API connectivity
        try:
            # This is a simple check - in production you might want a more sophisticated test
            health_status['components']['api'] = 'healthy'
        except Exception as e:
            health_status['components']['api'] = f'unhealthy: {e}'
            health_status['status'] = 'degraded'
        
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 90 or memory_percent > 90:
            health_status['status'] = 'degraded'
            health_status['components']['resources'] = 'high_usage'
        else:
            health_status['components']['resources'] = 'healthy'
        
        return health_status


# Utility functions for easy integration
def create_whisper_request(audio_file_path: str, **kwargs) -> WhisperRequest:
    """Create a WhisperRequest with sensible defaults."""
    return WhisperRequest(audio_file_path=audio_file_path, **kwargs)


def create_optimizer(api_key: str, redis_host: str = "localhost", 
                    redis_port: int = 6379) -> WhisperAPIOptimizer:
    """Create a WhisperAPIOptimizer with standard configuration."""
    cache_config = {
        'redis_host': redis_host,
        'redis_port': redis_port,
        'ttl_hours': 24
    }
    
    monitor_config = {
        'window_size_minutes': 60
    }
    
    return WhisperAPIOptimizer(
        api_key=api_key,
        cache_config=cache_config,
        monitor_config=monitor_config
    )


if __name__ == "__main__":
    # Example usage
    import os
    
    # Initialize optimizer
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        exit(1)
    
    optimizer = create_optimizer(api_key)
    
    # Example request
    request = create_whisper_request(
        audio_file_path="example_audio.wav",
        language="en",
        temperature=0.0
    )
    
    # Process request
    async def main():
        try:
            response = await optimizer.process_request(request)
            print(f"Transcription: {response.text}")
            print(f"Quality Score: {response.quality_score}")
            print(f"Processing Time: {response.processing_time}s")
            
            # Get stats
            stats = optimizer.get_optimization_stats()
            print(f"Cache Hit Rate: {stats['cache_stats']['hit_rate']:.2%}")
            print(f"Success Rate: {stats['api_efficiency']['success_rate']:.2%}")
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
    
    # Run example
    asyncio.run(main())