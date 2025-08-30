"""
API Endpoints for AI Provider Abstraction Layer

FastAPI endpoints for unified provider interface, request execution,
provider management, and metrics monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from ai_provider_abstraction import (
    ProviderAbstraction, AIRequest, ProviderConfig, RequestType, 
    ProviderType, ProviderStatus
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/provider-abstraction", tags=["Provider Abstraction"])

# Global abstraction instance
_abstraction_instance = None

def get_abstraction() -> ProviderAbstraction:
    """Get or create provider abstraction instance"""
    global _abstraction_instance
    if _abstraction_instance is None:
        _abstraction_instance = ProviderAbstraction("api_provider_abstraction.db")
    return _abstraction_instance

# Pydantic models for API
class AIRequestModel(BaseModel):
    """AI request model for API"""
    type: str = Field(..., description="Request type (transcription, text_to_speech, etc.)")
    content: Any = Field(..., description="Content to process")
    parameters: Dict[str, Any] = Field(default={}, description="Additional parameters")
    timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")
    priority: int = Field(default=1, ge=1, le=5, description="Request priority (1=highest)")

class AIResponseModel(BaseModel):
    """AI response model for API"""
    request_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    processing_time: float
    provider: str
    model: str
    timestamp: datetime

class ProviderConfigModel(BaseModel):
    """Provider configuration model"""
    provider_type: str = Field(..., description="Provider type")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for the provider")
    model_name: Optional[str] = Field(None, description="Model name to use")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    timeout: float = Field(default=30.0, gt=0, description="Request timeout")
    parameters: Dict[str, Any] = Field(default={}, description="Additional parameters")

class ProviderMetricsResponse(BaseModel):
    """Provider metrics response"""
    providers: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]
    timestamp: datetime

@router.post("/execute", response_model=AIResponseModel)
async def execute_request(
    request: AIRequestModel,
    provider_name: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Execute AI request through provider abstraction layer
    
    This endpoint provides a unified interface for executing AI requests
    across multiple providers with automatic selection and fallback.
    """
    try:
        # Validate request type
        try:
            request_type = RequestType(request.type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request type: {request.type}. "
                       f"Valid options: {[rt.value for rt in RequestType]}"
            )
        
        # Generate unique request ID
        request_id = f"api_req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create AI request
        ai_request = AIRequest(
            id=request_id,
            type=request_type,
            content=request.content,
            parameters=request.parameters,
            timeout=request.timeout,
            priority=request.priority
        )
        
        # Execute request
        response = await abstraction.execute_request(ai_request, provider_name)
        
        # Convert to API response model
        api_response = AIResponseModel(
            request_id=response.request_id,
            success=response.success,
            result=response.result,
            error=response.error,
            metadata=response.metadata,
            processing_time=response.processing_time,
            provider=response.provider,
            model=response.model,
            timestamp=response.timestamp
        )
        
        logger.info(f"Request {request_id} executed: {response.success} via {response.provider}")
        
        return api_response
        
    except Exception as e:
        logger.error(f"Error executing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request execution failed: {str(e)}")

@router.get("/providers", response_model=ProviderMetricsResponse)
async def get_providers(
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Get information about all registered providers
    
    Returns comprehensive metrics and status information for all providers.
    """
    try:
        metrics = abstraction.get_provider_metrics()
        
        # Calculate summary statistics
        total_providers = len(metrics)
        available_providers = sum(1 for m in metrics.values() if m['status'] == 'available')
        total_requests = sum(m['request_count'] for m in metrics.values())
        avg_error_rate = sum(m['error_rate'] for m in metrics.values()) / total_providers if total_providers > 0 else 0
        
        summary = {
            "total_providers": total_providers,
            "available_providers": available_providers,
            "total_requests": total_requests,
            "average_error_rate": avg_error_rate,
            "supported_types": list(set(
                req_type for provider_metrics in metrics.values() 
                for req_type in provider_metrics['supported_types']
            ))
        }
        
        response = ProviderMetricsResponse(
            providers=metrics,
            summary=summary,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")

@router.get("/providers/{provider_name}")
async def get_provider_details(
    provider_name: str,
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Get detailed information about a specific provider
    """
    try:
        if provider_name not in abstraction.providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        provider = abstraction.providers[provider_name]
        metrics = abstraction.get_provider_metrics()[provider_name]
        
        provider_details = {
            "name": provider_name,
            "status": provider.get_status().value,
            "configuration": {
                "provider_type": provider.config.provider_type.value,
                "model_name": provider.config.model_name,
                "max_retries": provider.config.max_retries,
                "timeout": provider.config.timeout,
                "has_api_key": bool(provider.config.api_key)
            },
            "metrics": metrics,
            "supported_types": [rt.value for rt in provider.get_supported_types()]
        }
        
        return provider_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider details: {str(e)}")

@router.put("/providers/{provider_name}/config")
async def update_provider_config(
    provider_name: str,
    config: ProviderConfigModel,
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Update provider configuration
    """
    try:
        if provider_name not in abstraction.providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        # Convert to internal config model
        try:
            provider_type = ProviderType(config.provider_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider type: {config.provider_type}"
            )
        
        provider_config = ProviderConfig(
            provider_type=provider_type,
            api_key=config.api_key,
            base_url=config.base_url,
            model_name=config.model_name,
            max_retries=config.max_retries,
            timeout=config.timeout,
            parameters=config.parameters
        )
        
        # Update configuration
        abstraction.configure_provider(provider_name, provider_config)
        
        return {
            "status": "success",
            "message": f"Configuration updated for provider {provider_name}",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update provider config: {str(e)}")

@router.get("/providers/{provider_name}/status")
async def get_provider_status(
    provider_name: str,
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Get provider status
    """
    try:
        status = abstraction.get_provider_status(provider_name)
        
        if status is None:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        return {
            "provider": provider_name,
            "status": status.value,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")

@router.get("/history")
async def get_request_history(
    limit: int = 100,
    provider: Optional[str] = None,
    success_only: bool = False,
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Get request history with optional filtering
    """
    try:
        history = abstraction.get_request_history(limit=limit)
        
        # Apply filters
        if provider:
            history = [h for h in history if h.get('provider') == provider]
        
        if success_only:
            history = [h for h in history if h.get('success')]
        
        return {
            "history": history,
            "total_records": len(history),
            "filters": {
                "limit": limit,
                "provider": provider,
                "success_only": success_only
            },
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting request history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get request history: {str(e)}")

@router.get("/capabilities")
async def get_capabilities():
    """
    Get available request types and capabilities
    """
    try:
        capabilities = [
            {
                "value": rt.value,
                "name": rt.name,
                "description": get_request_type_description(rt)
            }
            for rt in RequestType
        ]
        
        return {
            "capabilities": capabilities,
            "total": len(capabilities)
        }
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

@router.get("/provider-types")
async def get_provider_types():
    """
    Get available provider types
    """
    try:
        provider_types = [
            {
                "value": pt.value,
                "name": pt.name,
                "description": get_provider_type_description(pt)
            }
            for pt in ProviderType
        ]
        
        return {
            "provider_types": provider_types,
            "total": len(provider_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting provider types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider types: {str(e)}")

@router.post("/test/{provider_name}")
async def test_provider(
    provider_name: str,
    request: AIRequestModel,
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Test a specific provider with a sample request
    """
    try:
        if provider_name not in abstraction.providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        # Validate request type
        try:
            request_type = RequestType(request.type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request type: {request.type}"
            )
        
        # Create test request
        test_request_id = f"test_{provider_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        ai_request = AIRequest(
            id=test_request_id,
            type=request_type,
            content=request.content,
            parameters=request.parameters,
            timeout=request.timeout
        )
        
        # Execute test
        response = await abstraction.execute_request(ai_request, provider_name)
        
        return {
            "test_id": test_request_id,
            "provider": provider_name,
            "success": response.success,
            "result": response.result,
            "error": response.error,
            "processing_time": response.processing_time,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Provider test failed: {str(e)}")

@router.get("/health")
async def health_check(
    abstraction: ProviderAbstraction = Depends(get_abstraction)
):
    """
    Health check endpoint for provider abstraction service
    """
    try:
        metrics = abstraction.get_provider_metrics()
        available_providers = sum(1 for m in metrics.values() if m['status'] == 'available')
        
        health_status = {
            "status": "healthy" if available_providers > 0 else "degraded",
            "timestamp": datetime.now(),
            "providers": {
                "total": len(metrics),
                "available": available_providers,
                "unavailable": len(metrics) - available_providers
            },
            "database": "connected",
            "version": "1.0.0"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e),
            "version": "1.0.0"
        }

# Helper functions
def get_request_type_description(request_type: RequestType) -> str:
    """Get description for a request type"""
    descriptions = {
        RequestType.TRANSCRIPTION: "Convert audio to text",
        RequestType.TEXT_TO_SPEECH: "Convert text to audio",
        RequestType.TEXT_GENERATION: "Generate text content",
        RequestType.TRANSLATION: "Translate between languages",
        RequestType.SENTIMENT_ANALYSIS: "Analyze sentiment in text",
        RequestType.ENTITY_EXTRACTION: "Extract named entities from text",
        RequestType.SUMMARIZATION: "Summarize long text content"
    }
    return descriptions.get(request_type, "AI processing capability")

def get_provider_type_description(provider_type: ProviderType) -> str:
    """Get description for a provider type"""
    descriptions = {
        ProviderType.OPENAI: "OpenAI cloud AI services",
        ProviderType.ELEVENLABS: "ElevenLabs text-to-speech services",
        ProviderType.LOCAL_WHISPER: "Local Whisper transcription",
        ProviderType.LOCAL_SPACY: "Local spaCy NLP processing",
        ProviderType.CUSTOM: "Custom AI provider implementation"
    }
    return descriptions.get(provider_type, "AI service provider")

# Include router in main app
def include_router(app):
    """Include this router in the main FastAPI app"""
    app.include_router(router)