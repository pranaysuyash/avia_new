"""
API Usage Monitoring and Analytics System

Tracks API usage, generates analytics, and provides usage insights
for the developer platform.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio
import logging

from sqlalchemy.orm import Session
from fastapi import Request, Response
from api.database import get_db, APIKey, APIUsageLog

logger = logging.getLogger(__name__)

@dataclass
class UsageMetrics:
    """Usage metrics for API monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    total_data_processed: int = 0
    unique_users: int = 0
    top_endpoints: Dict[str, int] = None
    error_rates: Dict[str, float] = None
    
    def __post_init__(self):
        if self.top_endpoints is None:
            self.top_endpoints = {}
        if self.error_rates is None:
            self.error_rates = {}

class APIUsageMonitor:
    """Monitor and track API usage"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def track_request(
        self,
        request: Request,
        response: Response,
        api_key_id: str,
        processing_time: float
    ):
        """Track API request usage"""
        try:
            db = next(get_db())
            
            # Create usage log entry
            usage_log = APIUsageLog(
                api_key_id=api_key_id,
                endpoint=str(request.url.path),
                method=request.method,
                status_code=response.status_code,
                response_time_ms=processing_time * 1000,
                request_size=int(request.headers.get("content-length", 0)),
                response_size=len(response.body) if hasattr(response, 'body') else 0,
                user_agent=request.headers.get("user-agent", ""),
                ip_address=request.client.host if request.client else "",
                timestamp=datetime.utcnow()
            )
            
            db.add(usage_log)
            db.commit()
            
            # Update API key last used
            api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if api_key:
                api_key.last_used_at = datetime.utcnow()
                api_key.usage_count += 1
                db.commit()
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to track API usage: {e}")
    
    def get_usage_metrics(
        self,
        api_key_id: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageMetrics:
        """Get usage metrics for specified filters"""
        
        # Check cache first
        cache_key = f"{api_key_id}_{user_id}_{start_date}_{end_date}"
        if cache_key in self.metrics_cache:
            cached_data, timestamp = self.metrics_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        try:
            db = next(get_db())
            
            # Build query
            query = db.query(APIUsageLog)
            
            if api_key_id:
                query = query.filter(APIUsageLog.api_key_id == api_key_id)
            
            if user_id:
                # Join with APIKey to filter by user
                query = query.join(APIKey).filter(APIKey.user_id == user_id)
            
            if start_date:
                query = query.filter(APIUsageLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(APIUsageLog.timestamp <= end_date)
            
            logs = query.all()
            
            # Calculate metrics
            metrics = self._calculate_metrics(logs)
            
            # Cache results
            self.metrics_cache[cache_key] = (metrics, time.time())
            
            db.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get usage metrics: {e}")
            return UsageMetrics()
    
    def _calculate_metrics(self, logs: List[APIUsageLog]) -> UsageMetrics:
        """Calculate metrics from usage logs"""
        if not logs:
            return UsageMetrics()
        
        total_requests = len(logs)
        successful_requests = len([l for l in logs if l.status_code < 400])
        failed_requests = total_requests - successful_requests
        
        # Average response time
        avg_response_time = sum(l.response_time_ms for l in logs) / total_requests
        
        # Total data processed
        total_data_processed = sum(l.request_size + l.response_size for l in logs)
        
        # Unique users (API keys)
        unique_users = len(set(l.api_key_id for l in logs))
        
        # Top endpoints
        endpoint_counts = defaultdict(int)
        for log in logs:
            endpoint_counts[f"{log.method} {log.endpoint}"] += 1
        
        top_endpoints = dict(sorted(
            endpoint_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        # Error rates by endpoint
        error_rates = {}
        for endpoint, count in endpoint_counts.items():
            endpoint_logs = [l for l in logs if f"{l.method} {l.endpoint}" == endpoint]
            errors = len([l for l in endpoint_logs if l.status_code >= 400])
            error_rates[endpoint] = (errors / len(endpoint_logs)) * 100 if endpoint_logs else 0
        
        return UsageMetrics(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            total_data_processed=total_data_processed,
            unique_users=unique_users,
            top_endpoints=top_endpoints,
            error_rates=error_rates
        )

# Global usage monitor instance
usage_monitor = APIUsageMonitor()