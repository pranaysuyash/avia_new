"""
Multi-LLM Provider API Endpoints
Provides REST API interface for managing and switching between multiple LLM providers
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging
import uuid
from enum import Enum
import aiohttp
import asyncio

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from api.middleware.audit_logging import audit_log
from database.connection import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/llm-providers")

# Enums
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"
    LOCAL = "local"
    CUSTOM = "custom"

class ModelType(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"

class ProviderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"
    RATE_LIMITED = "rate_limited"

# Provider configurations storage (replace with database in production)
provider_configs = {}
active_providers = {}
provider_stats = {}

# Pydantic models
class ProviderConfig(BaseModel):
    provider: LLMProvider
    api_key: Optional[str] = Field(None, description="API key for the provider")
    api_endpoint: Optional[str] = Field(None, description="Custom API endpoint")
    organization_id: Optional[str] = Field(None, description="Organization ID (for OpenAI)")
    project_id: Optional[str] = Field(None, description="Project ID (for Google)")
    region: Optional[str] = Field(None, description="Region (for AWS/Azure)")
    model_mappings: Dict[ModelType, str] = Field(
        default_factory=dict,
        description="Model names for different tasks"
    )
    max_tokens: Optional[int] = Field(4096, description="Maximum tokens per request")
    temperature: Optional[float] = Field(0.7, description="Default temperature")
    timeout: Optional[int] = Field(30, description="Request timeout in seconds")
    retry_attempts: Optional[int] = Field(3, description="Number of retry attempts")
    rate_limit: Optional[int] = Field(None, description="Requests per minute")
    custom_headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    enabled: bool = Field(True, description="Whether provider is enabled")
    priority: int = Field(0, description="Priority for fallback ordering")
    
    @validator('api_key')
    def validate_api_key(cls, v, values):
        if values.get('provider') != LLMProvider.LOCAL and not v:
            raise ValueError("API key is required for non-local providers")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "api_key": "sk-...",
                "model_mappings": {
                    "chat": "gpt-4",
                    "embedding": "text-embedding-ada-002",
                    "transcription": "whisper-1"
                },
                "max_tokens": 4096,
                "temperature": 0.7,
                "enabled": True,
                "priority": 1
            }
        }

class ProviderTestRequest(BaseModel):
    provider: LLMProvider
    config: ProviderConfig
    test_prompt: str = Field("Hello, can you respond to confirm the connection is working?")
    model_type: ModelType = Field(ModelType.CHAT, description="Type of model to test")

class ProviderTestResponse(BaseModel):
    success: bool
    provider: LLMProvider
    response_time: float
    message: str
    model_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ProviderSwitchRequest(BaseModel):
    provider: LLMProvider
    model_type: Optional[ModelType] = Field(None, description="Switch only for specific model type")

class ProviderStatusResponse(BaseModel):
    provider: LLMProvider
    status: ProviderStatus
    health_score: float = Field(..., ge=0, le=100, description="Health score 0-100")
    response_time_avg: Optional[float] = None
    error_rate: Optional[float] = None
    requests_today: int = 0
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    models_available: List[str] = []

class ProviderBenchmarkRequest(BaseModel):
    providers: List[LLMProvider] = Field(..., description="Providers to benchmark")
    test_cases: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"prompt": "Translate 'Hello world' to French", "type": "translation"},
            {"prompt": "Summarize: The quick brown fox jumps over the lazy dog.", "type": "summarization"},
            {"prompt": "What is 2+2?", "type": "chat"}
        ],
        description="Test cases for benchmarking"
    )
    iterations: int = Field(3, description="Number of iterations per test")

class ProviderUsageStats(BaseModel):
    provider: LLMProvider
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost: float
    average_response_time: float
    uptime_percentage: float
    last_7_days: List[Dict[str, Any]]
    by_model_type: Dict[ModelType, Dict[str, Any]]

@router.get("/", response_model=List[Dict[str, Any]])
async def list_providers(
    include_disabled: bool = Query(False, description="Include disabled providers"),
    current_user=Depends(get_current_user)
):
    """
    List all configured LLM providers
    """
    try:
        user_id = current_user.get("user_id")
        user_configs = provider_configs.get(user_id, {})
        
        providers = []
        for provider, config in user_configs.items():
            if not include_disabled and not config.get("enabled", True):
                continue
            
            # Get status
            status_info = await get_provider_status_internal(user_id, provider)
            
            providers.append({
                "provider": provider,
                "enabled": config.get("enabled", True),
                "priority": config.get("priority", 0),
                "status": status_info.status,
                "health_score": status_info.health_score,
                "models": config.get("model_mappings", {}),
                "is_active": provider in active_providers.get(user_id, {}).values()
            })
        
        # Sort by priority
        providers.sort(key=lambda x: x["priority"], reverse=True)
        
        return providers
        
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configure", response_model=Dict[str, Any])
async def configure_provider(
    config: ProviderConfig,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("llm_configuration"))
):
    """
    Configure a new LLM provider or update existing configuration
    """
    try:
        user_id = current_user.get("user_id")
        
        # Initialize user configs if not exists
        if user_id not in provider_configs:
            provider_configs[user_id] = {}
        
        # Store configuration (encrypt API key in production)
        provider_configs[user_id][config.provider] = config.dict()
        
        # Test connection if enabled
        if config.enabled:
            test_result = await test_provider_internal(config)
            if not test_result.success:
                # Store but mark as error
                provider_configs[user_id][config.provider]["status"] = ProviderStatus.ERROR
                provider_configs[user_id][config.provider]["last_error"] = test_result.error
        
        # Track API usage
        await track_api_call("llm_configuration", current_user)
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="llm_provider_configured",
            details={"provider": config.provider, "enabled": config.enabled}
        )
        
        return {
            "success": True,
            "provider": config.provider,
            "message": f"Provider {config.provider} configured successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to configure provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test", response_model=ProviderTestResponse)
async def test_provider(
    request: ProviderTestRequest,
    current_user=Depends(get_current_user)
):
    """
    Test a provider configuration
    """
    try:
        result = await test_provider_internal(request.config, request.test_prompt, request.model_type)
        return result
        
    except Exception as e:
        logger.error(f"Provider test failed: {e}")
        return ProviderTestResponse(
            success=False,
            provider=request.provider,
            response_time=0,
            message="Test failed",
            error=str(e)
        )

@router.get("/{provider}/status", response_model=ProviderStatusResponse)
async def get_provider_status(
    provider: LLMProvider,
    current_user=Depends(get_current_user)
):
    """
    Get the current status of a specific provider
    """
    try:
        user_id = current_user.get("user_id")
        status = await get_provider_status_internal(user_id, provider)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get provider status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/switch", response_model=Dict[str, Any])
async def switch_provider(
    request: ProviderSwitchRequest,
    current_user=Depends(get_current_user)
):
    """
    Switch the active provider
    """
    try:
        user_id = current_user.get("user_id")
        
        # Check if provider is configured
        if user_id not in provider_configs or request.provider not in provider_configs[user_id]:
            raise HTTPException(status_code=404, detail="Provider not configured")
        
        # Check if provider is enabled
        config = provider_configs[user_id][request.provider]
        if not config.get("enabled", True):
            raise HTTPException(status_code=400, detail="Provider is disabled")
        
        # Initialize active providers for user
        if user_id not in active_providers:
            active_providers[user_id] = {}
        
        # Switch provider
        if request.model_type:
            active_providers[user_id][request.model_type] = request.provider
            message = f"Switched {request.model_type} to {request.provider}"
        else:
            # Switch all model types
            for model_type in ModelType:
                active_providers[user_id][model_type] = request.provider
            message = f"Switched all model types to {request.provider}"
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="llm_provider_switched",
            details={"provider": request.provider, "model_type": request.model_type}
        )
        
        return {
            "success": True,
            "message": message,
            "active_providers": active_providers.get(user_id, {})
        }
        
    except Exception as e:
        logger.error(f"Failed to switch provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/benchmark", response_model=Dict[str, Any])
async def benchmark_providers(
    request: ProviderBenchmarkRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("llm_benchmark"))
):
    """
    Benchmark multiple providers
    """
    try:
        user_id = current_user.get("user_id")
        benchmark_id = str(uuid.uuid4())
        
        # Start benchmark in background
        background_tasks.add_task(
            run_benchmark,
            benchmark_id,
            user_id,
            request.providers,
            request.test_cases,
            request.iterations
        )
        
        # Track API usage
        await track_api_call("llm_benchmark", current_user)
        
        return {
            "benchmark_id": benchmark_id,
            "status": "started",
            "providers": request.providers,
            "test_cases": len(request.test_cases),
            "iterations": request.iterations
        }
        
    except Exception as e:
        logger.error(f"Failed to start benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/benchmark/{benchmark_id}", response_model=Dict[str, Any])
async def get_benchmark_results(
    benchmark_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get benchmark results
    """
    # In production, retrieve from database
    # For now, return mock data
    return {
        "benchmark_id": benchmark_id,
        "status": "completed",
        "results": {
            "openai": {
                "average_response_time": 0.523,
                "success_rate": 100,
                "quality_score": 95,
                "cost_per_1k_tokens": 0.03
            },
            "anthropic": {
                "average_response_time": 0.612,
                "success_rate": 100,
                "quality_score": 93,
                "cost_per_1k_tokens": 0.025
            }
        },
        "recommendations": [
            "OpenAI shows best overall performance",
            "Anthropic offers better cost efficiency",
            "Consider using OpenAI for quality-critical tasks"
        ]
    }

@router.get("/usage/stats", response_model=List[ProviderUsageStats])
async def get_usage_stats(
    days: int = Query(7, description="Number of days to include"),
    current_user=Depends(get_current_user)
):
    """
    Get usage statistics for all providers
    """
    try:
        user_id = current_user.get("user_id")
        stats = []
        
        # Get stats for each configured provider
        if user_id in provider_configs:
            for provider in provider_configs[user_id]:
                # In production, fetch from database
                provider_stat = ProviderUsageStats(
                    provider=provider,
                    total_requests=1234,
                    successful_requests=1200,
                    failed_requests=34,
                    total_tokens=456789,
                    total_cost=12.34,
                    average_response_time=0.567,
                    uptime_percentage=97.2,
                    last_7_days=[
                        {"date": "2024-01-01", "requests": 150, "tokens": 45000},
                        {"date": "2024-01-02", "requests": 180, "tokens": 52000},
                    ],
                    by_model_type={
                        ModelType.CHAT: {"requests": 800, "tokens": 300000},
                        ModelType.EMBEDDING: {"requests": 400, "tokens": 156789}
                    }
                )
                stats.append(provider_stat)
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{provider}")
async def delete_provider(
    provider: LLMProvider,
    current_user=Depends(get_current_user)
):
    """
    Delete a provider configuration
    """
    try:
        user_id = current_user.get("user_id")
        
        if user_id not in provider_configs or provider not in provider_configs[user_id]:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Remove from configurations
        del provider_configs[user_id][provider]
        
        # Remove from active providers if set
        if user_id in active_providers:
            for model_type, active_provider in list(active_providers[user_id].items()):
                if active_provider == provider:
                    del active_providers[user_id][model_type]
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="llm_provider_deleted",
            details={"provider": provider}
        )
        
        return {"success": True, "message": f"Provider {provider} deleted"}
        
    except Exception as e:
        logger.error(f"Failed to delete provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fallback/configure")
async def configure_fallback(
    fallback_order: List[LLMProvider],
    model_type: Optional[ModelType] = None,
    current_user=Depends(get_current_user)
):
    """
    Configure fallback order for providers
    """
    try:
        user_id = current_user.get("user_id")
        
        # Validate all providers are configured
        if user_id not in provider_configs:
            raise HTTPException(status_code=400, detail="No providers configured")
        
        for provider in fallback_order:
            if provider not in provider_configs[user_id]:
                raise HTTPException(status_code=400, detail=f"Provider {provider} not configured")
        
        # Store fallback configuration
        # In production, store in database
        
        return {
            "success": True,
            "fallback_order": fallback_order,
            "model_type": model_type
        }
        
    except Exception as e:
        logger.error(f"Failed to configure fallback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{provider}")
async def get_available_models(
    provider: LLMProvider,
    model_type: Optional[ModelType] = None,
    current_user=Depends(get_current_user)
):
    """
    Get available models for a provider
    """
    try:
        # Provider-specific model lists
        models = {
            LLMProvider.OPENAI: {
                ModelType.CHAT: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                ModelType.EMBEDDING: ["text-embedding-ada-002", "text-embedding-3-small"],
                ModelType.TRANSCRIPTION: ["whisper-1"],
            },
            LLMProvider.ANTHROPIC: {
                ModelType.CHAT: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            },
            LLMProvider.GOOGLE: {
                ModelType.CHAT: ["gemini-pro", "gemini-pro-vision"],
                ModelType.EMBEDDING: ["embedding-001"],
            },
            LLMProvider.COHERE: {
                ModelType.CHAT: ["command", "command-light"],
                ModelType.EMBEDDING: ["embed-english-v3.0", "embed-multilingual-v3.0"],
            }
        }
        
        provider_models = models.get(provider, {})
        
        if model_type:
            return {
                "provider": provider,
                "model_type": model_type,
                "models": provider_models.get(model_type, [])
            }
        else:
            return {
                "provider": provider,
                "models": provider_models
            }
        
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def test_provider_internal(
    config: ProviderConfig,
    test_prompt: str = "Hello, can you respond?",
    model_type: ModelType = ModelType.CHAT
) -> ProviderTestResponse:
    """
    Test a provider configuration internally
    """
    start_time = datetime.now()
    
    try:
        # Provider-specific testing logic
        if config.provider == LLMProvider.OPENAI:
            response = await test_openai(config, test_prompt, model_type)
        elif config.provider == LLMProvider.ANTHROPIC:
            response = await test_anthropic(config, test_prompt, model_type)
        elif config.provider == LLMProvider.GOOGLE:
            response = await test_google(config, test_prompt, model_type)
        elif config.provider == LLMProvider.LOCAL:
            response = await test_local(config, test_prompt, model_type)
        else:
            raise ValueError(f"Provider {config.provider} not implemented")
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return ProviderTestResponse(
            success=True,
            provider=config.provider,
            response_time=response_time,
            message="Provider test successful",
            model_info=response.get("model_info")
        )
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        return ProviderTestResponse(
            success=False,
            provider=config.provider,
            response_time=response_time,
            message="Provider test failed",
            error=str(e)
        )

async def test_openai(config: ProviderConfig, prompt: str, model_type: ModelType) -> Dict[str, Any]:
    """
    Test OpenAI provider
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        if config.organization_id:
            headers["OpenAI-Organization"] = config.organization_id
        
        model = config.model_mappings.get(model_type, "gpt-3.5-turbo")
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": config.temperature
        }
        
        url = config.api_endpoint or "https://api.openai.com/v1/chat/completions"
        
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                raise Exception(f"OpenAI API error: {response.status}")
            
            result = await response.json()
            return {
                "response": result["choices"][0]["message"]["content"],
                "model_info": {"model": model, "usage": result.get("usage")}
            }

async def test_anthropic(config: ProviderConfig, prompt: str, model_type: ModelType) -> Dict[str, Any]:
    """
    Test Anthropic provider
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        model = config.model_mappings.get(model_type, "claude-3-haiku")
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": config.temperature
        }
        
        url = config.api_endpoint or "https://api.anthropic.com/v1/messages"
        
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                raise Exception(f"Anthropic API error: {response.status}")
            
            result = await response.json()
            return {
                "response": result["content"][0]["text"],
                "model_info": {"model": model, "usage": result.get("usage")}
            }

async def test_google(config: ProviderConfig, prompt: str, model_type: ModelType) -> Dict[str, Any]:
    """
    Test Google provider
    """
    # Implement Google Gemini API testing
    raise NotImplementedError("Google provider testing not yet implemented")

async def test_local(config: ProviderConfig, prompt: str, model_type: ModelType) -> Dict[str, Any]:
    """
    Test local provider
    """
    # Implement local model testing (e.g., Ollama, llama.cpp)
    return {
        "response": "Local model response (mock)",
        "model_info": {"model": "local", "type": model_type}
    }

async def get_provider_status_internal(user_id: str, provider: LLMProvider) -> ProviderStatusResponse:
    """
    Get internal provider status
    """
    # In production, fetch from monitoring data
    return ProviderStatusResponse(
        provider=provider,
        status=ProviderStatus.ACTIVE,
        health_score=95.5,
        response_time_avg=0.523,
        error_rate=0.02,
        requests_today=150,
        last_used=datetime.now(),
        models_available=["gpt-4", "gpt-3.5-turbo"]
    )

async def run_benchmark(
    benchmark_id: str,
    user_id: str,
    providers: List[LLMProvider],
    test_cases: List[Dict[str, Any]],
    iterations: int
):
    """
    Run benchmark in background
    """
    # Implement actual benchmarking logic
    logger.info(f"Running benchmark {benchmark_id} for user {user_id}")
    
    results = {}
    for provider in providers:
        if user_id not in provider_configs or provider not in provider_configs[user_id]:
            continue
        
        config = ProviderConfig(**provider_configs[user_id][provider])
        provider_results = []
        
        for test_case in test_cases:
            for _ in range(iterations):
                result = await test_provider_internal(
                    config,
                    test_case["prompt"],
                    ModelType(test_case.get("type", "chat"))
                )
                provider_results.append(result)
        
        # Calculate statistics
        results[provider] = {
            "success_rate": sum(1 for r in provider_results if r.success) / len(provider_results) * 100,
            "average_response_time": sum(r.response_time for r in provider_results) / len(provider_results)
        }
    
    # Store results in database
    logger.info(f"Benchmark {benchmark_id} completed: {results}")

@router.get("/health")
async def health_check():
    """
    Health check for LLM provider service
    """
    return {
        "status": "healthy",
        "service": "llm_providers",
        "configured_providers": sum(len(configs) for configs in provider_configs.values()),
        "active_users": len(active_providers),
        "timestamp": datetime.now().isoformat()
    }