"""
AI Customization API Endpoints
FastAPI endpoints for AI model configuration and customization
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import uuid

from api.dependencies import get_current_user, require_roles
from api.middleware.quota_enforcement import require_quota
from database.connection import get_db
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Float, Integer
from database.models import Base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai")

# Database models for AI customization
class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    model_type = Column(String, nullable=False)  # transcription, ner, summarization, etc.
    base_model = Column(String, nullable=False)  # whisper, gpt, bert, etc.
    parameters = Column(JSON, default=dict)
    fine_tuning_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CustomPrompt(Base):
    __tablename__ = "custom_prompts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    prompt_type = Column(String, nullable=False)  # system, user, assistant
    content = Column(String, nullable=False)
    variables = Column(JSON)  # Dynamic variables in the prompt
    tags = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String, nullable=False)
    accuracy = Column(Float)
    speed = Column(Float)  # tokens/second or similar
    cost_per_request = Column(Float)
    usage_count = Column(Integer, default=0)
    feedback_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class ModelConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    model_type: str = Field(..., description="Type of AI model")
    base_model: str = Field(..., description="Base model to use")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Enhanced Transcription Model",
                "description": "Custom model for technical presentations",
                "model_type": "transcription",
                "base_model": "whisper-large-v3",
                "parameters": {
                    "language": "en",
                    "task": "transcribe",
                    "temperature": 0.7,
                    "beam_size": 5,
                    "best_of": 5,
                    "patience": 1.0,
                    "length_penalty": 1.0,
                    "suppress_tokens": [-1],
                    "condition_on_previous_text": True,
                    "fp16": True,
                    "compression_ratio_threshold": 2.4,
                    "logprob_threshold": -1.0,
                    "no_speech_threshold": 0.6
                },
                "is_public": False
            }
        }

class ModelConfigResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    model_type: str
    base_model: str
    parameters: Dict[str, Any]
    is_active: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    performance_metrics: Optional[Dict[str, Any]] = None

class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    prompt_type: str = Field(..., description="Type of prompt")
    content: str = Field(..., min_length=1, max_length=5000)
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Technical Documentation Summary",
                "prompt_type": "system",
                "content": "You are an expert technical writer. Summarize the following transcript focusing on: {focus_areas}. Ensure the summary is {tone} and includes {requirements}.",
                "variables": ["focus_areas", "tone", "requirements"],
                "tags": ["summary", "technical", "documentation"]
            }
        }

class PromptResponse(BaseModel):
    id: str
    user_id: str
    name: str
    prompt_type: str
    content: str
    variables: Optional[List[str]]
    tags: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ModelTestRequest(BaseModel):
    config_id: str
    test_input: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "config_id": "123e4567-e89b-12d3-a456-426614174000",
                "test_input": {
                    "audio_url": "https://example.com/sample.mp3",
                    "language": "en",
                    "task": "transcribe"
                }
            }
        }

# Endpoints
@router.post("/models/config", response_model=ModelConfigResponse)
@require_quota('api_calls', 1, 'custom_models')  # Require custom models feature
async def create_model_config(
    config: ModelConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new AI model configuration"""
    try:
        # Create model config
        db_config = AIModelConfig(
            user_id=current_user['id'],
            name=config.name,
            description=config.description,
            model_type=config.model_type,
            base_model=config.base_model,
            parameters=config.parameters,
            is_public=config.is_public
        )
        
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        return ModelConfigResponse(
            id=db_config.id,
            user_id=db_config.user_id,
            name=db_config.name,
            description=db_config.description,
            model_type=db_config.model_type,
            base_model=db_config.base_model,
            parameters=db_config.parameters,
            is_active=db_config.is_active,
            is_public=db_config.is_public,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating model config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/config", response_model=List[ModelConfigResponse])
@require_quota('api_calls', 1, 'custom_models')
async def list_model_configs(
    model_type: Optional[str] = None,
    include_public: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available AI model configurations"""
    try:
        query = db.query(AIModelConfig).filter(
            AIModelConfig.is_active == True
        )
        
        # Filter by ownership and public configs
        if include_public:
            query = query.filter(
                (AIModelConfig.user_id == current_user['id']) |
                (AIModelConfig.is_public == True)
            )
        else:
            query = query.filter(AIModelConfig.user_id == current_user['id'])
        
        # Filter by model type
        if model_type:
            query = query.filter(AIModelConfig.model_type == model_type)
        
        configs = query.all()
        
        # Get performance metrics for each config
        results = []
        for config in configs:
            # Get latest performance metrics
            perf = db.query(ModelPerformance).filter(
                ModelPerformance.config_id == config.id
            ).order_by(ModelPerformance.created_at.desc()).first()
            
            performance_metrics = None
            if perf:
                performance_metrics = {
                    "accuracy": perf.accuracy,
                    "speed": perf.speed,
                    "cost_per_request": perf.cost_per_request,
                    "usage_count": perf.usage_count,
                    "feedback_score": perf.feedback_score
                }
            
            results.append(ModelConfigResponse(
                id=config.id,
                user_id=config.user_id,
                name=config.name,
                description=config.description,
                model_type=config.model_type,
                base_model=config.base_model,
                parameters=config.parameters,
                is_active=config.is_active,
                is_public=config.is_public,
                created_at=config.created_at,
                updated_at=config.updated_at,
                performance_metrics=performance_metrics
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error listing model configs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/config/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific AI model configuration"""
    try:
        config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.is_active == True
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        # Check permissions
        if not config.is_public and config.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get performance metrics
        perf = db.query(ModelPerformance).filter(
            ModelPerformance.config_id == config.id
        ).order_by(ModelPerformance.created_at.desc()).first()
        
        performance_metrics = None
        if perf:
            performance_metrics = {
                "accuracy": perf.accuracy,
                "speed": perf.speed,
                "cost_per_request": perf.cost_per_request,
                "usage_count": perf.usage_count,
                "feedback_score": perf.feedback_score
            }
        
        return ModelConfigResponse(
            id=config.id,
            user_id=config.user_id,
            name=config.name,
            description=config.description,
            model_type=config.model_type,
            base_model=config.base_model,
            parameters=config.parameters,
            is_active=config.is_active,
            is_public=config.is_public,
            created_at=config.created_at,
            updated_at=config.updated_at,
            performance_metrics=performance_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/models/config/{config_id}")
async def update_model_config(
    config_id: str,
    update: ModelConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an AI model configuration"""
    try:
        config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.user_id == current_user['id']
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        # Update fields
        config.name = update.name
        config.description = update.description
        config.parameters = update.parameters
        config.is_public = update.is_public
        config.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(config)
        
        return {"message": "Model config updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/config/{config_id}")
async def delete_model_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an AI model configuration"""
    try:
        config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.user_id == current_user['id']
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        # Soft delete
        config.is_active = False
        config.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Model config deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/test")
@require_quota('api_calls', 1, 'custom_models')
async def test_model_config(
    test_request: ModelTestRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test an AI model configuration"""
    try:
        # Get config
        config = db.query(AIModelConfig).filter(
            AIModelConfig.id == test_request.config_id,
            AIModelConfig.is_active == True
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        # Check permissions
        if not config.is_public and config.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # TODO: Implement actual model testing based on model_type
        # This would integrate with the actual AI services
        
        # Mock response for now
        test_result = {
            "status": "success",
            "execution_time": 2.34,
            "results": {
                "output": "This is a test output from the model",
                "confidence": 0.95,
                "metadata": {
                    "tokens_used": 150,
                    "model_version": config.base_model
                }
            },
            "cost": 0.002
        }
        
        # Update usage count
        perf = db.query(ModelPerformance).filter(
            ModelPerformance.config_id == config.id
        ).order_by(ModelPerformance.created_at.desc()).first()
        
        if perf:
            perf.usage_count += 1
            db.commit()
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing model config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Prompt management endpoints
@router.post("/prompts", response_model=PromptResponse)
@require_quota('api_calls', 1, 'custom_models')
async def create_prompt(
    prompt: PromptCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a custom prompt template"""
    try:
        db_prompt = CustomPrompt(
            user_id=current_user['id'],
            name=prompt.name,
            prompt_type=prompt.prompt_type,
            content=prompt.content,
            variables=prompt.variables,
            tags=prompt.tags
        )
        
        db.add(db_prompt)
        db.commit()
        db.refresh(db_prompt)
        
        return PromptResponse(
            id=db_prompt.id,
            user_id=db_prompt.user_id,
            name=db_prompt.name,
            prompt_type=db_prompt.prompt_type,
            content=db_prompt.content,
            variables=db_prompt.variables,
            tags=db_prompt.tags,
            is_active=db_prompt.is_active,
            created_at=db_prompt.created_at,
            updated_at=db_prompt.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts", response_model=List[PromptResponse])
async def list_prompts(
    prompt_type: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List custom prompts"""
    try:
        query = db.query(CustomPrompt).filter(
            CustomPrompt.user_id == current_user['id'],
            CustomPrompt.is_active == True
        )
        
        if prompt_type:
            query = query.filter(CustomPrompt.prompt_type == prompt_type)
        
        prompts = query.all()
        
        # Filter by tag if specified
        if tag:
            prompts = [p for p in prompts if tag in (p.tags or [])]
        
        return [
            PromptResponse(
                id=prompt.id,
                user_id=prompt.user_id,
                name=prompt.name,
                prompt_type=prompt.prompt_type,
                content=prompt.content,
                variables=prompt.variables,
                tags=prompt.tags,
                is_active=prompt.is_active,
                created_at=prompt.created_at,
                updated_at=prompt.updated_at
            )
            for prompt in prompts
        ]
        
    except Exception as e:
        logger.error(f"Error listing prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/available")
async def get_available_models(
    current_user: dict = Depends(get_current_user)
):
    """Get list of available base AI models"""
    return {
        "transcription": [
            {
                "id": "whisper-tiny",
                "name": "Whisper Tiny",
                "description": "Fastest, least accurate",
                "size": "39M parameters",
                "languages": ["en"],
                "cost_multiplier": 0.5
            },
            {
                "id": "whisper-base",
                "name": "Whisper Base",
                "description": "Good balance of speed and accuracy",
                "size": "74M parameters",
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
                "cost_multiplier": 0.7
            },
            {
                "id": "whisper-small",
                "name": "Whisper Small",
                "description": "Better accuracy, slower",
                "size": "244M parameters",
                "languages": ["multilingual"],
                "cost_multiplier": 1.0
            },
            {
                "id": "whisper-medium",
                "name": "Whisper Medium",
                "description": "High accuracy",
                "size": "769M parameters",
                "languages": ["multilingual"],
                "cost_multiplier": 1.5
            },
            {
                "id": "whisper-large-v3",
                "name": "Whisper Large V3",
                "description": "Best accuracy, slowest",
                "size": "1550M parameters",
                "languages": ["multilingual"],
                "cost_multiplier": 2.0
            }
        ],
        "ner": [
            {
                "id": "spacy-small",
                "name": "spaCy Small",
                "description": "Fast NER for common entities",
                "languages": ["en"],
                "entity_types": ["PERSON", "ORG", "LOC", "DATE", "TIME", "MONEY"]
            },
            {
                "id": "spacy-large",
                "name": "spaCy Large",
                "description": "Comprehensive NER",
                "languages": ["en", "es", "fr", "de"],
                "entity_types": ["PERSON", "ORG", "LOC", "DATE", "TIME", "MONEY", "PRODUCT", "EVENT", "FAC", "GPE", "LANGUAGE", "LAW", "NORP", "PERCENT", "QUANTITY"]
            },
            {
                "id": "bert-ner",
                "name": "BERT NER",
                "description": "Transformer-based NER",
                "languages": ["multilingual"],
                "entity_types": ["custom"]
            }
        ],
        "summarization": [
            {
                "id": "bart-base",
                "name": "BART Base",
                "description": "Fast summarization",
                "max_length": 1024
            },
            {
                "id": "bart-large",
                "name": "BART Large",
                "description": "High-quality summaries",
                "max_length": 1024
            },
            {
                "id": "t5-base",
                "name": "T5 Base",
                "description": "Versatile text generation",
                "max_length": 512
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Advanced summarization with context",
                "max_length": 4096
            }
        ],
        "sentiment": [
            {
                "id": "roberta-sentiment",
                "name": "RoBERTa Sentiment",
                "description": "Accurate sentiment analysis",
                "classes": ["positive", "negative", "neutral"]
            },
            {
                "id": "bert-emotion",
                "name": "BERT Emotion",
                "description": "Detailed emotion detection",
                "classes": ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]
            }
        ]
    }

@router.get("/models/presets")
async def get_model_presets(
    current_user: dict = Depends(get_current_user)
):
    """Get recommended model configuration presets"""
    return {
        "presets": [
            {
                "id": "podcast-transcription",
                "name": "Podcast Transcription",
                "description": "Optimized for podcast audio",
                "model_type": "transcription",
                "base_model": "whisper-medium",
                "parameters": {
                    "language": "en",
                    "task": "transcribe",
                    "temperature": 0.8,
                    "beam_size": 5,
                    "patience": 1.2,
                    "condition_on_previous_text": True,
                    "no_speech_threshold": 0.5
                }
            },
            {
                "id": "meeting-minutes",
                "name": "Meeting Minutes",
                "description": "Optimized for meeting recordings",
                "model_type": "transcription",
                "base_model": "whisper-large-v3",
                "parameters": {
                    "language": "auto",
                    "task": "transcribe",
                    "temperature": 0.5,
                    "beam_size": 10,
                    "best_of": 5,
                    "patience": 1.5,
                    "condition_on_previous_text": True,
                    "no_speech_threshold": 0.6,
                    "compression_ratio_threshold": 2.4
                }
            },
            {
                "id": "legal-ner",
                "name": "Legal Entity Recognition",
                "description": "Extract legal entities and terms",
                "model_type": "ner",
                "base_model": "bert-ner",
                "parameters": {
                    "entity_types": ["PERSON", "ORG", "LAW", "CASE", "STATUTE", "REGULATION"],
                    "confidence_threshold": 0.8,
                    "context_window": 128
                }
            },
            {
                "id": "medical-transcription",
                "name": "Medical Transcription",
                "description": "HIPAA-compliant medical transcription",
                "model_type": "transcription",
                "base_model": "whisper-large-v3",
                "parameters": {
                    "language": "en",
                    "task": "transcribe",
                    "temperature": 0.3,
                    "beam_size": 10,
                    "best_of": 10,
                    "patience": 2.0,
                    "condition_on_previous_text": True,
                    "no_speech_threshold": 0.7,
                    "medical_terminology": True
                }
            }
        ]
    }

@router.post("/models/fine-tune")
async def initiate_fine_tuning(
    config_id: str,
    training_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate fine-tuning of a model (Admin only)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get config
        config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.user_id == current_user['id']
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        # TODO: Implement actual fine-tuning integration
        # This would typically:
        # 1. Validate training data format
        # 2. Upload to training service
        # 3. Start fine-tuning job
        # 4. Return job ID for tracking
        
        # Mock response
        job_id = str(uuid.uuid4())
        
        # Store fine-tuning data
        config.fine_tuning_data = {
            "job_id": job_id,
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "training_samples": len(training_data.get('samples', [])),
            "validation_samples": len(training_data.get('validation', []))
        }
        
        db.commit()
        
        return {
            "job_id": job_id,
            "status": "initiated",
            "message": "Fine-tuning job started",
            "estimated_time": "2-4 hours"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating fine-tuning: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/fine-tune/{job_id}/status")
async def get_fine_tuning_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check fine-tuning job status"""
    try:
        # Find config with this job ID
        configs = db.query(AIModelConfig).filter(
            AIModelConfig.user_id == current_user['id']
        ).all()
        
        config = None
        for c in configs:
            if c.fine_tuning_data and c.fine_tuning_data.get('job_id') == job_id:
                config = c
                break
        
        if not config:
            raise HTTPException(status_code=404, detail="Fine-tuning job not found")
        
        # TODO: Check actual job status from training service
        
        # Mock status update
        return {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "metrics": {
                "training_loss": 0.234,
                "validation_loss": 0.256,
                "accuracy": 0.942
            },
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking fine-tuning status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/feedback")
async def submit_model_feedback(
    config_id: str = Body(...),
    score: float = Body(..., ge=1, le=5),
    feedback: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a model configuration"""
    try:
        # Verify config exists and user has access
        config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.is_active == True
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Model config not found")
        
        if not config.is_public and config.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update performance metrics
        perf = db.query(ModelPerformance).filter(
            ModelPerformance.config_id == config_id
        ).order_by(ModelPerformance.created_at.desc()).first()
        
        if perf:
            # Update average feedback score
            if perf.feedback_score:
                # Simple average - in production, would weight by number of feedbacks
                perf.feedback_score = (perf.feedback_score + score) / 2
            else:
                perf.feedback_score = score
            
            db.commit()
        
        return {
            "message": "Feedback submitted successfully",
            "current_score": perf.feedback_score if perf else score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))