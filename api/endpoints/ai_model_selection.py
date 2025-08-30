"""
API Endpoints for AI Model Selection Engine

FastAPI endpoints for model selection, management, and performance monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from ai_model_selection_engine import (
    ModelSelectionEngine, AIRequest, UserPreferences, RequestContext,
    ModelCapability, ModelProvider, SelectionCriteria, ModelSelection
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/model-selection", tags=["Model Selection"])

# Global engine instance
_engine_instance = None

def get_engine() -> ModelSelectionEngine:
    """Get or create model selection engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ModelSelectionEngine("api_model_selection.db")
    return _engine_instance

# Pydantic models for API
class UserPreferencesRequest(BaseModel):
    """User preferences for model selection"""
    preferred_providers: List[str] = Field(default=[], description="Preferred AI providers")
    quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum quality threshold")
    max_latency_ms: float = Field(default=5000.0, gt=0, description="Maximum acceptable latency in milliseconds")
    max_cost_per_request: float = Field(default=0.10, ge=0.0, description="Maximum cost per request")
    privacy_required: bool = Field(default=False, description="Whether privacy is required (prefer local models)")

class RequestContextRequest(BaseModel):
    """Request context information"""
    user_id: str = Field(..., description="User identifier")
    content_size: int = Field(default=0, ge=0, description="Size of content to process")
    urgency: str = Field(default="normal", regex="^(low|normal|high)$", description="Request urgency level")
    quality_requirement: str = Field(default="standard", regex="^(basic|standard|high)$", description="Quality requirement")

class ModelSelectionRequest(BaseModel):
    """Model selection request"""
    capability: str = Field(..., description="Required AI capability")
    content: str = Field(..., description="Content identifier or description")
    context: RequestContextRequest = Field(..., description="Request context")
    preferences: UserPreferencesRequest = Field(..., description="User preferences")
    criteria_weights: Optional[Dict[str, float]] = Field(default=None, description="Custom criteria weights")

class ModelSelectionResponse(BaseModel):
    """Model selection response"""
    request_id: str
    primary_model: Dict[str, Any]
    fallback_models: List[Dict[str, Any]]
    selection_reasoning: str
    confidence_score: float
    estimated_cost: float
    estimated_latency: float
    timestamp: datetime

class ModelMetricsUpdate(BaseModel):
    """Model metrics update request"""
    model_id: str = Field(..., description="Model identifier")
    actual_latency: float = Field(..., gt=0, description="Actual latency in milliseconds")
    actual_cost: float = Field(..., ge=0, description="Actual cost")
    success: bool = Field(..., description="Whether the request was successful")

class ModelPerformanceResponse(BaseModel):
    """Model performance summary response"""
    models: Dict[str, Dict[str, Any]]
    summary_stats: Dict[str, Any]
    timestamp: datetime

@router.post("/select", response_model=ModelSelectionResponse)
async def select_model(
    request: ModelSelectionRequest,
    background_tasks: BackgroundTasks,
    engine: ModelSelectionEngine = Depends(get_engine)
):
    """
    Select the optimal AI model for a given request
    
    This endpoint analyzes the request requirements and user preferences
    to select the best available AI model based on multiple criteria.
    """
    try:
        # Convert string enums to proper types
        try:
            capability = ModelCapability(request.capability)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid capability: {request.capability}. "
                       f"Valid options: {[c.value for c in ModelCapability]}"
            )
        
        # Convert provider strings to enums
        preferred_providers = []
        for provider_str in request.preferences.preferred_providers:
            try:
                preferred_providers.append(ModelProvider(provider_str))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {provider_str}. "
                           f"Valid options: {[p.value for p in ModelProvider]}"
                )
        
        # Create user preferences
        user_prefs = UserPreferences(
            preferred_providers=preferred_providers,
            quality_threshold=request.preferences.quality_threshold,
            max_latency_ms=request.preferences.max_latency_ms,
            max_cost_per_request=request.preferences.max_cost_per_request,
            privacy_required=request.preferences.privacy_required
        )
        
        # Create request context
        context = RequestContext(
            user_id=request.context.user_id,
            request_type=capability,
            content_size=request.context.content_size,
            urgency=request.context.urgency,
            quality_requirement=request.context.quality_requirement
        )
        
        # Generate unique request ID
        request_id = f"api_req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create AI request
        ai_request = AIRequest(
            id=request_id,
            capability=capability,
            content=request.content,
            context=context,
            preferences=user_prefs
        )
        
        # Convert criteria weights if provided
        criteria_weights = None
        if request.criteria_weights:
            criteria_weights = {}
            for criteria_str, weight in request.criteria_weights.items():
                try:
                    criteria = SelectionCriteria(criteria_str)
                    criteria_weights[criteria] = weight
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid criteria: {criteria_str}. "
                               f"Valid options: {[c.value for c in SelectionCriteria]}"
                    )
        
        # Perform model selection
        selection = await engine.select_model(ai_request, criteria_weights)
        
        # Convert models to dictionaries for response
        def model_to_dict(model):
            return {
                "id": model.id,
                "name": model.name,
                "provider": model.provider.value,
                "capabilities": [cap.value for cap in model.capabilities],
                "metrics": {
                    "latency_ms": model.metrics.latency_ms,
                    "accuracy_score": model.metrics.accuracy_score,
                    "cost_per_request": model.metrics.cost_per_request,
                    "availability_percent": model.metrics.availability_percent,
                    "throughput_rps": model.metrics.throughput_rps,
                    "error_rate": model.metrics.error_rate
                },
                "is_available": model.is_available,
                "priority": model.priority
            }
        
        # Create response
        response = ModelSelectionResponse(
            request_id=request_id,
            primary_model=model_to_dict(selection.primary_model),
            fallback_models=[model_to_dict(model) for model in selection.fallback_models],
            selection_reasoning=selection.selection_reasoning,
            confidence_score=selection.confidence_score,
            estimated_cost=selection.estimated_cost,
            estimated_latency=selection.estimated_latency,
            timestamp=datetime.now()
        )
        
        logger.info(f"Model selection completed for request {request_id}: {selection.primary_model.name}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in model selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model selection failed: {str(e)}")

@router.post("/update-metrics")
async def update_model_metrics(
    update: ModelMetricsUpdate,
    background_tasks: BackgroundTasks,
    engine: ModelSelectionEngine = Depends(get_engine)
):
    """
    Update model performance metrics based on actual usage
    
    This endpoint allows clients to report actual performance metrics
    to improve future model selection decisions.
    """
    try:
        # Update metrics in background
        background_tasks.add_task(
            engine.update_model_metrics,
            update.model_id,
            update.actual_latency,
            update.actual_cost,
            update.success
        )
        
        logger.info(f"Metrics update queued for model {update.model_id}")
        
        return {
            "status": "success",
            "message": f"Metrics update queued for model {update.model_id}",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error updating model metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics update failed: {str(e)}")

@router.get("/models", response_model=ModelPerformanceResponse)
async def get_model_performance(
    engine: ModelSelectionEngine = Depends(get_engine)
):
    """
    Get performance summary for all registered models
    
    Returns comprehensive performance metrics and availability status
    for all models in the system.
    """
    try:
        summary = engine.get_model_performance_summary()
        
        # Calculate summary statistics
        models_list = list(summary.values())
        available_models = [m for m in models_list if m['is_available']]
        
        summary_stats = {
            "total_models": len(models_list),
            "available_models": len(available_models),
            "average_latency": sum(m['metrics']['latency_ms'] for m in available_models) / len(available_models) if available_models else 0,
            "average_accuracy": sum(m['metrics']['accuracy_score'] for m in available_models) / len(available_models) if available_models else 0,
            "average_cost": sum(m['metrics']['cost_per_request'] for m in available_models) / len(available_models) if available_models else 0,
            "providers": list(set(m['provider'] for m in models_list)),
            "capabilities": list(set(cap for m in models_list for cap in m['capabilities']))
        }
        
        response = ModelPerformanceResponse(
            models=summary,
            summary_stats=summary_stats,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting model performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {str(e)}")

@router.get("/models/{model_id}")
async def get_model_details(
    model_id: str,
    engine: ModelSelectionEngine = Depends(get_engine)
):
    """
    Get detailed information about a specific model
    """
    try:
        if model_id not in engine.models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        model = engine.models[model_id]
        
        model_details = {
            "id": model.id,
            "name": model.name,
            "provider": model.provider.value,
            "capabilities": [cap.value for cap in model.capabilities],
            "metrics": {
                "latency_ms": model.metrics.latency_ms,
                "accuracy_score": model.metrics.accuracy_score,
                "cost_per_request": model.metrics.cost_per_request,
                "availability_percent": model.metrics.availability_percent,
                "throughput_rps": model.metrics.throughput_rps,
                "error_rate": model.metrics.error_rate,
                "last_updated": model.metrics.last_updated.isoformat()
            },
            "configuration": model.configuration,
            "is_available": model.is_available,
            "priority": model.priority
        }
        
        return model_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")

@router.get("/capabilities")
async def get_available_capabilities():
    """
    Get list of available AI capabilities
    """
    try:
        capabilities = [
            {
                "value": cap.value,
                "name": cap.name,
                "description": get_capability_description(cap)
            }
            for cap in ModelCapability
        ]
        
        return {
            "capabilities": capabilities,
            "total": len(capabilities)
        }
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")

@router.get("/providers")
async def get_available_providers():
    """
    Get list of available AI providers
    """
    try:
        providers = [
            {
                "value": provider.value,
                "name": provider.name,
                "description": get_provider_description(provider)
            }
            for provider in ModelProvider
        ]
        
        return {
            "providers": providers,
            "total": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")

@router.get("/selection-criteria")
async def get_selection_criteria():
    """
    Get list of available selection criteria
    """
    try:
        criteria = [
            {
                "value": crit.value,
                "name": crit.name,
                "description": get_criteria_description(crit)
            }
            for crit in SelectionCriteria
        ]
        
        return {
            "criteria": criteria,
            "total": len(criteria)
        }
        
    except Exception as e:
        logger.error(f"Error getting selection criteria: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get selection criteria: {str(e)}")

@router.get("/health")
async def health_check(
    engine: ModelSelectionEngine = Depends(get_engine)
):
    """
    Health check endpoint for the model selection service
    """
    try:
        summary = engine.get_model_performance_summary()
        available_models = sum(1 for info in summary.values() if info['is_available'])
        
        health_status = {
            "status": "healthy" if available_models > 0 else "degraded",
            "timestamp": datetime.now(),
            "models": {
                "total": len(summary),
                "available": available_models,
                "unavailable": len(summary) - available_models
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
def get_capability_description(capability: ModelCapability) -> str:
    """Get description for a capability"""
    descriptions = {
        ModelCapability.TRANSCRIPTION: "Convert audio to text",
        ModelCapability.TEXT_TO_SPEECH: "Convert text to audio",
        ModelCapability.TEXT_GENERATION: "Generate text content",
        ModelCapability.TRANSLATION: "Translate between languages",
        ModelCapability.SENTIMENT_ANALYSIS: "Analyze sentiment in text",
        ModelCapability.ENTITY_EXTRACTION: "Extract named entities from text",
        ModelCapability.SUMMARIZATION: "Summarize long text content"
    }
    return descriptions.get(capability, "AI processing capability")

def get_provider_description(provider: ModelProvider) -> str:
    """Get description for a provider"""
    descriptions = {
        ModelProvider.OPENAI: "OpenAI cloud AI services",
        ModelProvider.ELEVENLABS: "ElevenLabs text-to-speech services",
        ModelProvider.LOCAL_WHISPER: "Local Whisper transcription",
        ModelProvider.LOCAL_SPACY: "Local spaCy NLP processing",
        ModelProvider.CUSTOM: "Custom AI model implementation"
    }
    return descriptions.get(provider, "AI service provider")

def get_criteria_description(criteria: SelectionCriteria) -> str:
    """Get description for selection criteria"""
    descriptions = {
        SelectionCriteria.QUALITY: "Model accuracy and output quality",
        SelectionCriteria.SPEED: "Response time and latency",
        SelectionCriteria.COST: "Cost per request or usage",
        SelectionCriteria.AVAILABILITY: "Model uptime and reliability",
        SelectionCriteria.PRIVACY: "Data privacy and local processing"
    }
    return descriptions.get(criteria, "Model selection criteria")

# Include router in main app
def include_router(app):
    """Include this router in the main FastAPI app"""
    app.include_router(router)