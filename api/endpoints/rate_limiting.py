"""
Rate Limiting Management API Endpoints
Provides REST API for managing and monitoring rate limits
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from api.database import get_db, User
from api.auth import get_current_active_user, get_current_admin_user
from services.rate_limiting_service import (
    rate_limiting_service,
    RateLimitScope,
    RateLimitConfig,
    RateLimitAlgorithm
)
from services.audit_logging_service import audit_service, AuditEventType

router = APIRouter(
    prefix="/api/v1/rate-limiting",
    tags=["rate-limiting"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models
class RateLimitConfigRequest(BaseModel):
    """Request model for rate limit configuration"""
    requests_per_second: float = Field(gt=0, description="Requests allowed per second")
    burst_capacity: int = Field(gt=0, description="Maximum burst capacity")
    window_size: int = Field(default=60, gt=0, description="Window size in seconds")
    algorithm: RateLimitAlgorithm = Field(default=RateLimitAlgorithm.TOKEN_BUCKET)
    enabled: bool = Field(default=True, description="Whether rate limiting is enabled")


class RateLimitConfigResponse(BaseModel):
    """Response model for rate limit configuration"""
    scope: str
    endpoint: Optional[str] = None
    requests_per_second: float
    burst_capacity: int
    window_size: int
    algorithm: str
    enabled: bool


class RateLimitStatusResponse(BaseModel):
    """Response model for rate limit status"""
    identifier: str
    scope: str
    current_status: Dict[str, Any]
    configured_limits: RateLimitConfigResponse
    next_reset: Optional[str] = None


class RateLimitStatsResponse(BaseModel):
    """Response model for rate limiting statistics"""
    global_stats: Dict[str, Any]
    top_limited_ips: List[Dict[str, Any]]
    top_limited_users: List[Dict[str, Any]]
    algorithm_distribution: Dict[str, int]
    recent_violations: List[Dict[str, Any]]


class RateLimitResetRequest(BaseModel):
    """Request model for rate limit reset"""
    identifier: str
    scope: RateLimitScope
    endpoint: Optional[str] = None


# Configuration endpoints
@router.get("/config", response_model=List[RateLimitConfigResponse])
async def get_rate_limit_configs(
    scope: Optional[RateLimitScope] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get rate limiting configurations
    
    Requires admin privileges.
    """
    try:
        configs = []
        
        # Get default scope configurations
        for config_scope, config in rate_limiting_service.default_configs.items():
            if scope is None or config_scope == scope:
                configs.append(RateLimitConfigResponse(
                    scope=config_scope.value,
                    requests_per_second=config.requests_per_second,
                    burst_capacity=config.burst_capacity,
                    window_size=config.window_size,
                    algorithm=config.algorithm.value,
                    enabled=config.enabled
                ))
        
        # Get endpoint-specific configurations
        if scope is None or scope == RateLimitScope.ENDPOINT:
            for endpoint, config in rate_limiting_service.endpoint_configs.items():
                configs.append(RateLimitConfigResponse(
                    scope=RateLimitScope.ENDPOINT.value,
                    endpoint=endpoint,
                    requests_per_second=config.requests_per_second,
                    burst_capacity=config.burst_capacity,
                    window_size=config.window_size,
                    algorithm=config.algorithm.value,
                    enabled=config.enabled
                ))
        
        return configs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit configs: {str(e)}"
        )


@router.post("/config/{scope}")
async def update_rate_limit_config(
    scope: RateLimitScope,
    config: RateLimitConfigRequest,
    endpoint: Optional[str] = Query(None, description="Endpoint for endpoint-specific limits"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update rate limiting configuration
    
    Requires admin privileges.
    """
    try:
        # Create configuration
        new_config = RateLimitConfig(
            requests_per_second=config.requests_per_second,
            burst_capacity=config.burst_capacity,
            window_size=config.window_size,
            algorithm=config.algorithm,
            enabled=config.enabled
        )
        
        # Update configuration
        rate_limiting_service.update_config(scope, new_config, endpoint)
        
        # Log configuration change
        audit_service.log_event(
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            action=f"Rate limit config updated: {scope.value}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "scope": scope.value,
                "endpoint": endpoint,
                "requests_per_second": config.requests_per_second,
                "burst_capacity": config.burst_capacity,
                "algorithm": config.algorithm.value,
                "enabled": config.enabled
            }
        )
        
        return {
            "message": f"Rate limit configuration updated for {scope.value}",
            "scope": scope.value,
            "endpoint": endpoint
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rate limit config: {str(e)}"
        )


# Status and monitoring endpoints
@router.get("/status/{identifier}")
async def get_rate_limit_status(
    identifier: str,
    scope: RateLimitScope,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get current rate limiting status for an identifier
    
    Requires admin privileges.
    """
    try:
        # Get rate limit information
        rate_limit_info = await rate_limiting_service.get_rate_limit_info(identifier, scope)
        
        # Get configuration
        config = rate_limiting_service._get_config(scope)
        
        return RateLimitStatusResponse(
            identifier=identifier,
            scope=scope.value,
            current_status=rate_limit_info,
            configured_limits=RateLimitConfigResponse(
                scope=scope.value,
                requests_per_second=config.requests_per_second,
                burst_capacity=config.burst_capacity,
                window_size=config.window_size,
                algorithm=config.algorithm.value,
                enabled=config.enabled
            ),
            next_reset=None  # Could be calculated based on algorithm
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )


@router.get("/stats", response_model=RateLimitStatsResponse)
async def get_rate_limiting_stats(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get global rate limiting statistics
    
    Requires admin privileges.
    """
    try:
        # Get global statistics
        global_stats = await rate_limiting_service.get_global_stats()
        
        # Get algorithm distribution
        algorithm_distribution = global_stats.get('algorithm_usage', {})
        
        # Mock data for demonstration (in production, you'd query actual violation logs)
        recent_violations = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "identifier": "192.168.1.100",
                "scope": "ip",
                "endpoint": "/api/v1/transcription/transcribe",
                "violation_type": "token_bucket_exhausted"
            }
        ]
        
        top_limited_ips = [
            {"ip": "192.168.1.100", "violations": 15, "last_violation": datetime.utcnow().isoformat()},
            {"ip": "10.0.0.50", "violations": 8, "last_violation": datetime.utcnow().isoformat()}
        ]
        
        top_limited_users = [
            {"user_id": 123, "violations": 5, "last_violation": datetime.utcnow().isoformat()},
            {"user_id": 456, "violations": 3, "last_violation": datetime.utcnow().isoformat()}
        ]
        
        return RateLimitStatsResponse(
            global_stats=global_stats,
            top_limited_ips=top_limited_ips,
            top_limited_users=top_limited_users,
            algorithm_distribution=algorithm_distribution,
            recent_violations=recent_violations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limiting stats: {str(e)}"
        )


# Management endpoints
@router.post("/reset")
async def reset_rate_limit(
    reset_request: RateLimitResetRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset rate limiting for a specific identifier
    
    Requires admin privileges. Use with caution.
    """
    try:
        await rate_limiting_service.reset_rate_limit(
            identifier=reset_request.identifier,
            scope=reset_request.scope,
            endpoint=reset_request.endpoint
        )
        
        # Log rate limit reset
        audit_service.log_event(
            event_type=AuditEventType.RATE_LIMIT_RESET,
            action=f"Rate limit reset: {reset_request.scope.value}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "identifier": reset_request.identifier,
                "scope": reset_request.scope.value,
                "endpoint": reset_request.endpoint
            }
        )
        
        return {
            "message": f"Rate limit reset for {reset_request.identifier}",
            "identifier": reset_request.identifier,
            "scope": reset_request.scope.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limit: {str(e)}"
        )


@router.post("/test/{identifier}")
async def test_rate_limit(
    identifier: str,
    scope: RateLimitScope,
    requests: int = Query(default=1, ge=1, le=100, description="Number of requests to simulate"),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Test rate limiting for an identifier (for debugging)
    
    Requires admin privileges. Simulates requests to test rate limiting behavior.
    """
    try:
        results = []
        
        for i in range(requests):
            result = await rate_limiting_service.check_rate_limit(identifier, scope)
            
            results.append({
                "request_number": i + 1,
                "allowed": result.allowed,
                "remaining": result.remaining,
                "reset_time": result.reset_time,
                "retry_after": result.retry_after,
                "headers": result.headers
            })
            
            # Small delay to simulate real requests
            import asyncio
            await asyncio.sleep(0.1)
        
        # Log test
        audit_service.log_event(
            event_type=AuditEventType.RATE_LIMIT_TEST,
            action=f"Rate limit test: {scope.value}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "identifier": identifier,
                "scope": scope.value,
                "requests_tested": requests,
                "total_allowed": sum(1 for r in results if r["allowed"])
            }
        )
        
        return {
            "identifier": identifier,
            "scope": scope.value,
            "total_requests": requests,
            "total_allowed": sum(1 for r in results if r["allowed"]),
            "total_denied": sum(1 for r in results if not r["allowed"]),
            "detailed_results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test rate limit: {str(e)}"
        )


# Health check for rate limiting system
@router.get("/health")
async def rate_limiting_health(
    current_user: User = Depends(get_current_active_user)
):
    """
    Check health of rate limiting system
    
    Returns status of Redis connection and rate limiting service.
    """
    try:
        from api.cache.redis_cache import redis_cache
        
        # Test basic rate limiting functionality
        test_result = await rate_limiting_service.check_rate_limit(
            identifier="health_check",
            scope=RateLimitScope.GLOBAL
        )
        
        health_info = {
            "status": "healthy",
            "redis_connected": redis_cache.is_connected(),
            "rate_limiting_functional": test_result is not None,
            "active_buckets": len(rate_limiting_service.active_buckets),
            "active_windows": len(rate_limiting_service.active_windows),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_info
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }