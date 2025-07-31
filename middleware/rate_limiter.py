#!/usr/bin/env python3
"""
Rate Limiting Middleware for Audio/Video Transcription App
Implements per-user and per-IP rate limiting
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation with sliding window"""
    
    def __init__(self):
        # Store request counts: {identifier: [(timestamp, count)]}
        self.requests = defaultdict(list)
        
        # Rate limit configurations
        self.limits = {
            'global': {'requests': 1000, 'window': 3600},  # 1000 req/hour globally
            'authenticated': {'requests': 100, 'window': 3600},  # 100 req/hour per user
            'anonymous': {'requests': 20, 'window': 3600},  # 20 req/hour per IP
            'api': {'requests': 50, 'window': 3600},  # 50 API calls/hour
            'upload': {'requests': 10, 'window': 3600},  # 10 uploads/hour
            'processing': {'requests': 5, 'window': 3600},  # 5 processing jobs/hour
        }
        
        # Clean up old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def _cleanup_old_entries(self):
        """Remove expired entries from request tracking"""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # Find the oldest window we need to keep
        max_window = max(limit['window'] for limit in self.limits.values())
        cutoff_time = current_time - max_window
        
        # Clean up old entries
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                (ts, count) for ts, count in self.requests[identifier]
                if ts > cutoff_time
            ]
            
            # Remove empty entries
            if not self.requests[identifier]:
                del self.requests[identifier]
        
        self.last_cleanup = current_time
        logger.debug(f"Cleaned up rate limiter entries, {len(self.requests)} identifiers remaining")
    
    def _get_request_count(self, identifier: str, window: int) -> int:
        """Get request count for identifier within time window"""
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Sum requests within window
        return sum(
            count for ts, count in self.requests[identifier]
            if ts > cutoff_time
        )
    
    def check_rate_limit(self, identifier: str, limit_type: str = 'global') -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit
        Returns: (allowed, retry_after_seconds)
        """
        self._cleanup_old_entries()
        
        if limit_type not in self.limits:
            logger.warning(f"Unknown rate limit type: {limit_type}")
            return True, None
        
        limit_config = self.limits[limit_type]
        max_requests = limit_config['requests']
        window = limit_config['window']
        
        current_count = self._get_request_count(identifier, window)
        
        if current_count >= max_requests:
            # Calculate when the oldest request will expire
            requests_in_window = [
                ts for ts, _ in self.requests[identifier]
                if ts > time.time() - window
            ]
            
            if requests_in_window:
                oldest_request = min(requests_in_window)
                retry_after = int(oldest_request + window - time.time()) + 1
            else:
                retry_after = 1
            
            logger.warning(f"Rate limit exceeded for {identifier} ({limit_type}): {current_count}/{max_requests}")
            return False, retry_after
        
        return True, None
    
    def record_request(self, identifier: str, count: int = 1):
        """Record a request for rate limiting"""
        current_time = time.time()
        self.requests[identifier].append((current_time, count))
    
    def get_remaining_requests(self, identifier: str, limit_type: str = 'global') -> int:
        """Get remaining requests for identifier"""
        if limit_type not in self.limits:
            return 0
        
        limit_config = self.limits[limit_type]
        max_requests = limit_config['requests']
        window = limit_config['window']
        
        current_count = self._get_request_count(identifier, window)
        return max(0, max_requests - current_count)
    
    def reset_limits(self, identifier: str):
        """Reset rate limits for an identifier (admin function)"""
        if identifier in self.requests:
            del self.requests[identifier]
            logger.info(f"Reset rate limits for {identifier}")

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_client_identifier(request_type: str = 'global') -> str:
    """Get identifier for rate limiting based on request type"""
    from auth import get_current_user
    
    # For authenticated users, use user ID
    user = get_current_user()
    if user:
        return f"user:{user.id}"
    
    # For anonymous users, try to get IP (in production with proper proxy)
    # For now, use session ID as identifier
    if 'session_id' in st.session_state:
        return f"session:{st.session_state.session_id}"
    
    # Fallback to a generic identifier
    return "anonymous:unknown"

def rate_limit(limit_type: str = 'authenticated'):
    """Decorator for rate limiting functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identifier = get_client_identifier(limit_type)
            
            # Check rate limit
            allowed, retry_after = rate_limiter.check_rate_limit(identifier, limit_type)
            
            if not allowed:
                error_msg = f"Rate limit exceeded. Please try again in {retry_after} seconds."
                
                # Log the rate limit violation
                logger.warning(f"Rate limit violation: {identifier} for {limit_type}")
                
                # In Streamlit, show error
                st.error(error_msg)
                st.stop()
            
            # Record the request
            rate_limiter.record_request(identifier)
            
            # Execute the function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def check_api_rate_limit(api_key: str) -> Tuple[bool, Optional[int], Optional[Dict]]:
    """Check API rate limit for a given API key"""
    identifier = f"api:{api_key}"
    allowed, retry_after = rate_limiter.check_rate_limit(identifier, 'api')
    
    # Get rate limit headers
    headers = {
        'X-RateLimit-Limit': str(rate_limiter.limits['api']['requests']),
        'X-RateLimit-Remaining': str(rate_limiter.get_remaining_requests(identifier, 'api')),
        'X-RateLimit-Reset': str(int(time.time() + rate_limiter.limits['api']['window']))
    }
    
    if not allowed and retry_after:
        headers['Retry-After'] = str(retry_after)
    
    return allowed, retry_after, headers

def get_rate_limit_status(identifier: str = None) -> Dict[str, any]:
    """Get current rate limit status for an identifier"""
    if identifier is None:
        identifier = get_client_identifier()
    
    status = {}
    
    for limit_type, config in rate_limiter.limits.items():
        current_count = rate_limiter._get_request_count(identifier, config['window'])
        remaining = max(0, config['requests'] - current_count)
        
        status[limit_type] = {
            'limit': config['requests'],
            'window': config['window'],
            'used': current_count,
            'remaining': remaining,
            'reset_time': datetime.now() + timedelta(seconds=config['window'])
        }
    
    return status

# Middleware for Streamlit pages
def apply_rate_limiting():
    """Apply rate limiting to current Streamlit page"""
    if 'rate_limit_checked' not in st.session_state:
        identifier = get_client_identifier()
        
        # Check global rate limit
        allowed, retry_after = rate_limiter.check_rate_limit(identifier, 'global')
        
        if not allowed:
            st.error(f"Too many requests. Please try again in {retry_after} seconds.")
            st.stop()
        
        # Record the page view
        rate_limiter.record_request(identifier)
        st.session_state.rate_limit_checked = True