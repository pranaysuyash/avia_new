"""
AI Model Selection Engine Foundation

This module implements intelligent model selection with multi-criteria decision making,
real-time performance assessment, user preference awareness, and automatic fallback strategies.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """AI Model Providers"""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    LOCAL_WHISPER = "local_whisper"
    LOCAL_SPACY = "local_spacy"
    CUSTOM = "custom"

class ModelCapability(Enum):
    """AI Model Capabilities"""
    TRANSCRIPTION = "transcription"
    TEXT_TO_SPEECH = "text_to_speech"
    TEXT_GENERATION = "text_generation"
    TRANSLATION = "translation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    SUMMARIZATION = "summarization"

class SelectionCriteria(Enum):
    """Model Selection Criteria"""
    QUALITY = "quality"
    SPEED = "speed"
    COST = "cost"
    AVAILABILITY = "availability"
    PRIVACY = "privacy"

@dataclass
class ModelMetrics:
    """Performance and cost metrics for a model"""
    latency_ms: float = 0.0
    accuracy_score: float = 0.0
    cost_per_request: float = 0.0
    availability_percent: float = 100.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class AIModel:
    """AI Model representation"""
    id: str
    name: str
    provider: ModelProvider
    capabilities: List[ModelCapability]
    metrics: ModelMetrics
    configuration: Dict[str, Any] = field(default_factory=dict)
    is_available: bool = True
    priority: int = 1  # 1 = highest priority
    
@dataclass
class UserPreferences:
    """User-specific preferences for model selection"""
    preferred_providers: List[ModelProvider] = field(default_factory=list)
    quality_threshold: float = 0.8
    max_latency_ms: float = 5000.0
    max_cost_per_request: float = 0.10
    privacy_required: bool = False
    
@dataclass
class RequestContext:
    """Context information for AI requests"""
    user_id: str
    request_type: ModelCapability
    content_size: int = 0
    urgency: str = "normal"  # low, normal, high
    quality_requirement: str = "standard"  # basic, standard, high
    
@dataclass
class AIRequest:
    """AI Request representation"""
    id: str
    capability: ModelCapability
    content: Any
    context: RequestContext
    preferences: UserPreferences
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ModelScore:
    """Scoring result for model selection"""
    model: AIModel
    total_score: float
    criteria_scores: Dict[SelectionCriteria, float]
    reasoning: str
    
@dataclass
class ModelSelection:
    """Final model selection result"""
    primary_model: AIModel
    fallback_models: List[AIModel]
    selection_reasoning: str
    confidence_score: float
    estimated_cost: float
    estimated_latency: float

class ModelSelectionEngine:
    """
    Intelligent AI Model Selection Engine
    
    Provides multi-criteria decision making for optimal model selection
    based on quality, speed, cost, and availability requirements.
    """
    
    def __init__(self, db_path: str = "ai_model_selection.db"):
        self.db_path = db_path
        self.models: Dict[str, AIModel] = {}
        self.selection_history: List[Dict] = []
        self.performance_cache: Dict[str, Dict] = {}
        
        # Initialize database
        self._init_database()
        
        # Load default models
        self._load_default_models()
        
        logger.info("AI Model Selection Engine initialized")
    
    def _init_database(self):
        """Initialize SQLite database for model metrics and history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Model metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                model_id TEXT PRIMARY KEY,
                latency_ms REAL,
                accuracy_score REAL,
                cost_per_request REAL,
                availability_percent REAL,
                throughput_rps REAL,
                error_rate REAL,
                last_updated TIMESTAMP
            )
        """)
        
        # Selection history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS selection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                selected_model_id TEXT,
                criteria_used TEXT,
                selection_score REAL,
                actual_latency REAL,
                actual_cost REAL,
                success BOOLEAN,
                timestamp TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_default_models(self):
        """Load default AI models with initial configurations"""
        default_models = [
            AIModel(
                id="openai_whisper_1",
                name="OpenAI Whisper-1",
                provider=ModelProvider.OPENAI,
                capabilities=[ModelCapability.TRANSCRIPTION],
                metrics=ModelMetrics(
                    latency_ms=2000.0,
                    accuracy_score=0.95,
                    cost_per_request=0.006,
                    availability_percent=99.5,
                    throughput_rps=10.0
                ),
                priority=1
            ),
            AIModel(
                id="openai_gpt4",
                name="OpenAI GPT-4",
                provider=ModelProvider.OPENAI,
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.SUMMARIZATION],
                metrics=ModelMetrics(
                    latency_ms=3000.0,
                    accuracy_score=0.92,
                    cost_per_request=0.03,
                    availability_percent=99.0,
                    throughput_rps=5.0
                ),
                priority=1
            ),
            AIModel(
                id="elevenlabs_tts",
                name="ElevenLabs TTS",
                provider=ModelProvider.ELEVENLABS,
                capabilities=[ModelCapability.TEXT_TO_SPEECH],
                metrics=ModelMetrics(
                    latency_ms=1500.0,
                    accuracy_score=0.90,
                    cost_per_request=0.018,
                    availability_percent=98.5,
                    throughput_rps=8.0
                ),
                priority=1
            ),
            AIModel(
                id="local_whisper",
                name="Local Whisper",
                provider=ModelProvider.LOCAL_WHISPER,
                capabilities=[ModelCapability.TRANSCRIPTION],
                metrics=ModelMetrics(
                    latency_ms=5000.0,
                    accuracy_score=0.88,
                    cost_per_request=0.0,
                    availability_percent=100.0,
                    throughput_rps=3.0
                ),
                priority=2
            ),
            AIModel(
                id="local_spacy",
                name="Local spaCy NLP",
                provider=ModelProvider.LOCAL_SPACY,
                capabilities=[ModelCapability.ENTITY_EXTRACTION, ModelCapability.SENTIMENT_ANALYSIS],
                metrics=ModelMetrics(
                    latency_ms=500.0,
                    accuracy_score=0.82,
                    cost_per_request=0.0,
                    availability_percent=100.0,
                    throughput_rps=50.0
                ),
                priority=2
            )
        ]
        
        for model in default_models:
            self.models[model.id] = model
            
        logger.info(f"Loaded {len(default_models)} default AI models")
    
    async def select_model(self, request: AIRequest, criteria_weights: Optional[Dict[SelectionCriteria, float]] = None) -> ModelSelection:
        """
        Select the optimal AI model for a given request
        
        Args:
            request: AI request with context and preferences
            criteria_weights: Optional weights for selection criteria
            
        Returns:
            ModelSelection with primary and fallback models
        """
        try:
            # Get available models for the requested capability
            available_models = self._get_available_models(request.capability)
            
            if not available_models:
                raise ValueError(f"No available models for capability: {request.capability}")
            
            # Set default criteria weights if not provided
            if criteria_weights is None:
                criteria_weights = self._get_default_criteria_weights(request)
            
            # Score all available models
            model_scores = await self._score_models(available_models, request, criteria_weights)
            
            # Sort by total score (descending)
            model_scores.sort(key=lambda x: x.total_score, reverse=True)
            
            # Select primary model (highest score)
            primary_model = model_scores[0].model
            
            # Select fallback models (next best options)
            fallback_models = [score.model for score in model_scores[1:4]]  # Top 3 alternatives
            
            # Create selection result
            selection = ModelSelection(
                primary_model=primary_model,
                fallback_models=fallback_models,
                selection_reasoning=model_scores[0].reasoning,
                confidence_score=model_scores[0].total_score,
                estimated_cost=primary_model.metrics.cost_per_request,
                estimated_latency=primary_model.metrics.latency_ms
            )
            
            # Log selection for learning
            await self._log_selection(request, selection, model_scores[0])
            
            logger.info(f"Selected model {primary_model.name} for {request.capability} with score {model_scores[0].total_score:.3f}")
            
            return selection
            
        except Exception as e:
            logger.error(f"Error in model selection: {str(e)}")
            raise
    
    def _get_available_models(self, capability: ModelCapability) -> List[AIModel]:
        """Get all available models that support the requested capability"""
        available = []
        for model in self.models.values():
            if (capability in model.capabilities and 
                model.is_available and 
                model.metrics.availability_percent > 50.0):
                available.append(model)
        
        return available
    
    def _get_default_criteria_weights(self, request: AIRequest) -> Dict[SelectionCriteria, float]:
        """Get default criteria weights based on request context"""
        weights = {
            SelectionCriteria.QUALITY: 0.3,
            SelectionCriteria.SPEED: 0.25,
            SelectionCriteria.COST: 0.2,
            SelectionCriteria.AVAILABILITY: 0.15,
            SelectionCriteria.PRIVACY: 0.1
        }
        
        # Adjust weights based on context
        if request.context.urgency == "high":
            weights[SelectionCriteria.SPEED] = 0.4
            weights[SelectionCriteria.QUALITY] = 0.2
        elif request.context.quality_requirement == "high":
            weights[SelectionCriteria.QUALITY] = 0.5
            weights[SelectionCriteria.SPEED] = 0.15
        
        if request.preferences.privacy_required:
            weights[SelectionCriteria.PRIVACY] = 0.4
            # Reduce other weights proportionally
            for criteria in [SelectionCriteria.QUALITY, SelectionCriteria.SPEED, SelectionCriteria.COST]:
                weights[criteria] *= 0.75
        
        return weights
    
    async def _score_models(self, models: List[AIModel], request: AIRequest, criteria_weights: Dict[SelectionCriteria, float]) -> List[ModelScore]:
        """Score models based on multiple criteria"""
        scores = []
        
        for model in models:
            criteria_scores = {}
            
            # Quality score (accuracy)
            criteria_scores[SelectionCriteria.QUALITY] = model.metrics.accuracy_score
            
            # Speed score (inverse of latency, normalized)
            max_acceptable_latency = request.preferences.max_latency_ms
            if model.metrics.latency_ms <= max_acceptable_latency:
                criteria_scores[SelectionCriteria.SPEED] = 1.0 - (model.metrics.latency_ms / max_acceptable_latency)
            else:
                criteria_scores[SelectionCriteria.SPEED] = 0.1  # Penalty for exceeding max latency
            
            # Cost score (inverse of cost, normalized)
            max_acceptable_cost = request.preferences.max_cost_per_request
            if model.metrics.cost_per_request <= max_acceptable_cost:
                if max_acceptable_cost > 0:
                    criteria_scores[SelectionCriteria.COST] = 1.0 - (model.metrics.cost_per_request / max_acceptable_cost)
                else:
                    criteria_scores[SelectionCriteria.COST] = 1.0 if model.metrics.cost_per_request == 0 else 0.5
            else:
                criteria_scores[SelectionCriteria.COST] = 0.1  # Penalty for exceeding max cost
            
            # Availability score
            criteria_scores[SelectionCriteria.AVAILABILITY] = model.metrics.availability_percent / 100.0
            
            # Privacy score
            if request.preferences.privacy_required:
                # Local models get higher privacy scores
                if model.provider in [ModelProvider.LOCAL_WHISPER, ModelProvider.LOCAL_SPACY]:
                    criteria_scores[SelectionCriteria.PRIVACY] = 1.0
                else:
                    criteria_scores[SelectionCriteria.PRIVACY] = 0.3
            else:
                criteria_scores[SelectionCriteria.PRIVACY] = 1.0  # Privacy not a concern
            
            # Calculate weighted total score
            total_score = sum(
                criteria_scores[criteria] * weight 
                for criteria, weight in criteria_weights.items()
            )
            
            # Apply user preference bonuses
            if model.provider in request.preferences.preferred_providers:
                total_score *= 1.1  # 10% bonus for preferred providers
            
            # Apply priority adjustment
            priority_multiplier = 1.0 + (0.05 * (3 - model.priority))  # Higher priority = higher multiplier
            total_score *= priority_multiplier
            
            # Generate reasoning
            reasoning = self._generate_selection_reasoning(model, criteria_scores, criteria_weights)
            
            scores.append(ModelScore(
                model=model,
                total_score=total_score,
                criteria_scores=criteria_scores,
                reasoning=reasoning
            ))
        
        return scores
    
    def _generate_selection_reasoning(self, model: AIModel, criteria_scores: Dict[SelectionCriteria, float], weights: Dict[SelectionCriteria, float]) -> str:
        """Generate human-readable reasoning for model selection"""
        top_criteria = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:2]
        
        reasoning_parts = [f"Selected {model.name} ({model.provider.value})"]
        
        for criteria, weight in top_criteria:
            score = criteria_scores[criteria]
            if criteria == SelectionCriteria.QUALITY:
                reasoning_parts.append(f"Quality: {score:.2f} (accuracy)")
            elif criteria == SelectionCriteria.SPEED:
                reasoning_parts.append(f"Speed: {score:.2f} (latency: {model.metrics.latency_ms}ms)")
            elif criteria == SelectionCriteria.COST:
                reasoning_parts.append(f"Cost: {score:.2f} (${model.metrics.cost_per_request:.4f}/req)")
            elif criteria == SelectionCriteria.AVAILABILITY:
                reasoning_parts.append(f"Availability: {score:.2f} ({model.metrics.availability_percent}%)")
            elif criteria == SelectionCriteria.PRIVACY:
                privacy_level = "High" if model.provider in [ModelProvider.LOCAL_WHISPER, ModelProvider.LOCAL_SPACY] else "Standard"
                reasoning_parts.append(f"Privacy: {privacy_level}")
        
        return "; ".join(reasoning_parts)
    
    async def _log_selection(self, request: AIRequest, selection: ModelSelection, score: ModelScore):
        """Log selection decision for learning and analysis"""
        selection_record = {
            "request_id": request.id,
            "selected_model_id": selection.primary_model.id,
            "criteria_used": json.dumps({k.value: v for k, v in score.criteria_scores.items()}),
            "selection_score": score.total_score,
            "estimated_latency": selection.estimated_latency,
            "estimated_cost": selection.estimated_cost,
            "timestamp": datetime.now().isoformat()
        }
        
        self.selection_history.append(selection_record)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO selection_history 
            (request_id, selected_model_id, criteria_used, selection_score, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            selection_record["request_id"],
            selection_record["selected_model_id"],
            selection_record["criteria_used"],
            selection_record["selection_score"],
            selection_record["timestamp"]
        ))
        conn.commit()
        conn.close()
    
    async def update_model_metrics(self, model_id: str, actual_latency: float, actual_cost: float, success: bool):
        """Update model metrics based on actual performance"""
        if model_id not in self.models:
            logger.warning(f"Model {model_id} not found for metrics update")
            return
        
        model = self.models[model_id]
        
        # Update metrics with exponential moving average
        alpha = 0.1  # Learning rate
        
        if actual_latency > 0:
            model.metrics.latency_ms = (1 - alpha) * model.metrics.latency_ms + alpha * actual_latency
        
        if actual_cost >= 0:
            model.metrics.cost_per_request = (1 - alpha) * model.metrics.cost_per_request + alpha * actual_cost
        
        # Update error rate
        if success:
            model.metrics.error_rate = (1 - alpha) * model.metrics.error_rate
        else:
            model.metrics.error_rate = (1 - alpha) * model.metrics.error_rate + alpha * 1.0
        
        model.metrics.last_updated = datetime.now()
        
        # Store updated metrics in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO model_metrics 
            (model_id, latency_ms, accuracy_score, cost_per_request, availability_percent, 
             throughput_rps, error_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_id,
            model.metrics.latency_ms,
            model.metrics.accuracy_score,
            model.metrics.cost_per_request,
            model.metrics.availability_percent,
            model.metrics.throughput_rps,
            model.metrics.error_rate,
            model.metrics.last_updated.isoformat()
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Updated metrics for model {model_id}: latency={actual_latency}ms, cost=${actual_cost:.4f}, success={success}")
    
    def get_fallback_models(self, primary_model: AIModel, capability: ModelCapability) -> List[AIModel]:
        """Get fallback models for a given primary model and capability"""
        fallback_models = []
        
        for model in self.models.values():
            if (model.id != primary_model.id and 
                capability in model.capabilities and 
                model.is_available):
                fallback_models.append(model)
        
        # Sort by priority and availability
        fallback_models.sort(key=lambda x: (x.priority, -x.metrics.availability_percent))
        
        return fallback_models[:3]  # Return top 3 fallback options
    
    def get_model_performance_summary(self) -> Dict[str, Dict]:
        """Get performance summary for all models"""
        summary = {}
        
        for model_id, model in self.models.items():
            summary[model_id] = {
                "name": model.name,
                "provider": model.provider.value,
                "capabilities": [cap.value for cap in model.capabilities],
                "metrics": {
                    "latency_ms": model.metrics.latency_ms,
                    "accuracy_score": model.metrics.accuracy_score,
                    "cost_per_request": model.metrics.cost_per_request,
                    "availability_percent": model.metrics.availability_percent,
                    "error_rate": model.metrics.error_rate
                },
                "is_available": model.is_available,
                "priority": model.priority
            }
        
        return summary

# Example usage and testing
async def main():
    """Example usage of the Model Selection Engine"""
    engine = ModelSelectionEngine()
    
    # Create sample request
    user_prefs = UserPreferences(
        preferred_providers=[ModelProvider.OPENAI],
        quality_threshold=0.85,
        max_latency_ms=3000.0,
        max_cost_per_request=0.02
    )
    
    context = RequestContext(
        user_id="user123",
        request_type=ModelCapability.TRANSCRIPTION,
        content_size=1024,
        urgency="normal",
        quality_requirement="high"
    )
    
    request = AIRequest(
        id="req_001",
        capability=ModelCapability.TRANSCRIPTION,
        content="audio_file.wav",
        context=context,
        preferences=user_prefs
    )
    
    # Select model
    selection = await engine.select_model(request)
    
    print(f"Selected Model: {selection.primary_model.name}")
    print(f"Provider: {selection.primary_model.provider.value}")
    print(f"Reasoning: {selection.selection_reasoning}")
    print(f"Confidence: {selection.confidence_score:.3f}")
    print(f"Estimated Cost: ${selection.estimated_cost:.4f}")
    print(f"Estimated Latency: {selection.estimated_latency}ms")
    print(f"Fallback Models: {[m.name for m in selection.fallback_models]}")
    
    # Simulate actual usage and update metrics
    await engine.update_model_metrics(
        selection.primary_model.id,
        actual_latency=2100.0,
        actual_cost=0.007,
        success=True
    )
    
    # Get performance summary
    summary = engine.get_model_performance_summary()
    print("\nModel Performance Summary:")
    for model_id, info in summary.items():
        print(f"  {info['name']}: Latency={info['metrics']['latency_ms']:.0f}ms, "
              f"Accuracy={info['metrics']['accuracy_score']:.2f}, "
              f"Cost=${info['metrics']['cost_per_request']:.4f}")

if __name__ == "__main__":
    asyncio.run(main())