#!/usr/bin/env python3
"""
Usage Tracking Middleware
Automatically tracks API calls and resource usage
"""

import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
import time
import asyncio
from datetime import datetime

from database.models import User
from services.subscription_service import SubscriptionService
from database.connection import get_db

logger = logging.getLogger(__name__)

class UsageTrackingRoute(APIRoute):
    """Custom route class for usage tracking"""
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            # Skip tracking for certain endpoints
            skip_endpoints = [
                '/api/auth',
                '/api/subscriptions',
                '/api/health',
                '/docs',
                '/openapi.json'
            ]
            
            # Check if we should skip this endpoint
            for skip in skip_endpoints:
                if request.url.path.startswith(skip):
                    return await original_route_handler(request)
            
            # Get user from request if authenticated
            user = getattr(request.state, 'user', None)
            if not user:
                return await original_route_handler(request)
            
            # Track API call
            start_time = time.time()
            
            # Call original handler
            response = await original_route_handler(request)
            
            # Track usage asynchronously
            duration = time.time() - start_time
            asyncio.create_task(
                self._track_api_usage(user.id, request, response, duration)
            )
            
            return response
        
        return custom_route_handler
    
    async def _track_api_usage(
        self,
        user_id: int,
        request: Request,
        response: Response,
        duration: float
    ):
        """Track API usage asynchronously"""
        try:
            subscription_service = SubscriptionService(get_db)
            
            # Track API call
            subscription_service.track_usage(
                user_id=user_id,
                usage_type='api_calls',
                quantity=1,
                resource_type='api_endpoint',
                description=f"{request.method} {request.url.path}"
            )
            
            # Log the usage
            logger.debug(
                f"API usage tracked: user_id={user_id}, "
                f"endpoint={request.url.path}, duration={duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")


class UsageTrackingMiddleware:
    """Middleware for tracking usage across the application"""
    
    def __init__(self, app):
        self.app = app
        self.subscription_service = SubscriptionService(get_db)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract path
        path = scope.get("path", "")
        
        # Skip certain paths
        skip_paths = ['/health', '/docs', '/openapi.json', '/static']
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                await self.app(scope, receive, send)
                return
        
        # Process request
        await self.app(scope, receive, send)


def check_usage_limit(usage_type: str, amount: int = 1):
    """Dependency to check usage limits before processing"""
    async def _check_usage(request: Request, user: User):
        subscription_service = SubscriptionService(get_db)
        
        allowed, message, usage_info = subscription_service.check_usage_limit(
            user_id=user.id,
            usage_type=usage_type,
            amount=amount
        )
        
        if not allowed:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    'error': 'usage_limit_exceeded',
                    'message': message,
                    'usage': usage_info,
                    'upgrade_url': '/subscription'
                }
            )
        
        # Store usage info in request for later tracking
        request.state.usage_type = usage_type
        request.state.usage_amount = amount
        
        return True
    
    return _check_usage


def track_resource_usage(resource_type: str, usage_type: str):
    """Decorator to track resource usage after successful operation"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request and user from kwargs
            request = None
            user = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, User):
                    user = arg
            
            # Also check kwargs
            request = request or kwargs.get('request')
            user = user or kwargs.get('current_user')
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Track usage if we have user info
            if user and result:
                subscription_service = SubscriptionService(get_db)
                
                # Determine quantity based on result
                quantity = 1
                resource_id = None
                
                if isinstance(result, dict):
                    # Extract resource ID if available
                    resource_id = result.get('id')
                    
                    # Calculate quantity based on usage type
                    if usage_type == 'minutes' and 'duration' in result:
                        quantity = result['duration'] / 60.0  # Convert to minutes
                    elif usage_type == 'storage' and 'file_size' in result:
                        quantity = result['file_size'] / (1024 ** 3)  # Convert to GB
                
                # Track the usage
                try:
                    subscription_service.track_usage(
                        user_id=user.id,
                        usage_type=usage_type,
                        quantity=quantity,
                        resource_type=resource_type,
                        resource_id=resource_id
                    )
                except Exception as e:
                    logger.error(f"Error tracking {resource_type} usage: {e}")
            
            return result
        
        return wrapper
    return decorator