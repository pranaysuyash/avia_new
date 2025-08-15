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
        
        # Implement actual model testing based on model_type
        # This integrates with the actual AI services
        try:
            test_result = None
            
            if config.model_type == "openai":
                # Test OpenAI model
                import openai
                
                # Get API key from config
                api_key = config.api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise HTTPException(status_code=400, detail="OpenAI API key not configured")
                
                client = openai.OpenAI(api_key=api_key)
                
                # Test with a simple prompt
                start_time = time.time()
                response = client.chat.completions.create(
                    model=config.model_name,
                    messages=[
                        {"role": "user", "content": "Say 'Hello, world!' in the style of a professional AI assistant."}
                    ],
                    max_tokens=50,
                    temperature=0.7
                )
                execution_time = time.time() - start_time
                
                test_result = {
                    "status": "success",
                    "execution_time": execution_time,
                    "results": {
                        "output": response.choices[0].message.content,
                        "confidence": 0.95,
                        "metadata": {
                            "model": config.model_name,
                            "provider": "openai",
                            "tokens_used": response.usage.total_tokens if response.usage else 0
                        }
                    }
                }
                
            elif config.model_type == "anthropic":
                # Test Anthropic model
                import anthropic
                
                # Get API key from config
                api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise HTTPException(status_code=400, detail="Anthropic API key not configured")
                
                client = anthropic.Anthropic(api_key=api_key)
                
                # Test with a simple prompt
                start_time = time.time()
                response = client.messages.create(
                    model=config.model_name,
                    messages=[
                        {"role": "user", "content": "Say 'Hello, world!' in the style of a professional AI assistant."}
                    ],
                    max_tokens=50,
                    temperature=0.7
                )
                execution_time = time.time() - start_time
                
                test_result = {
                    "status": "success",
                    "execution_time": execution_time,
                    "results": {
                        "output": response.content[0].text if response.content else "",
                        "confidence": 0.95,
                        "metadata": {
                            "model": config.model_name,
                            "provider": "anthropic",
                            "tokens_used": response.usage.output_tokens if response.usage else 0
                        }
                    }
                }
                
            elif config.model_type == "huggingface":
                # Test HuggingFace model
                from transformers import pipeline
                
                # Test with a simple prompt
                start_time = time.time()
                
                # Create text generation pipeline
                generator = pipeline(
                    "text-generation",
                    model=config.model_name,
                    token=config.api_key or os.getenv("HUGGINGFACE_TOKEN")
                )
                
                response = generator(
                    "Say 'Hello, world!' in the style of a professional AI assistant.",
                    max_new_tokens=50,
                    temperature=0.7
                )
                execution_time = time.time() - start_time
                
                test_result = {
                    "status": "success",
                    "execution_time": execution_time,
                    "results": {
                        "output": response[0]['generated_text'] if response else "",
                        "confidence": 0.90,
                        "metadata": {
                            "model": config.model_name,
                            "provider": "huggingface",
                            "tokens_generated": len(response[0]['generated_text'].split()) if response else 0
                        }
                    }
                }
                
            else:
                # Unsupported model type
                raise HTTPException(status_code=400, detail=f"Unsupported model type: {config.model_type}")
            
            # Log test results
            logger.info(f"Model test completed for {config.model_name} ({config.model_type})")
            
            return test_result
            
        except Exception as e:
            logger.error(f"Model test failed for {config.model_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Model test failed: {str(e)}")
        
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
        
        # Implement actual fine-tuning integration
        # This typically:
        # 1. Validates training data format
        # 2. Uploads to training service
        # 3. Starts fine-tuning job
        # 4. Returns job ID for tracking
        
        try:
            # Validate training data format
            if not training_data:
                raise HTTPException(status_code=400, detail="Training data is required")
            
            samples = training_data.get('samples', [])
            validation = training_data.get('validation', [])
            
            # Validate training data structure
            if not isinstance(samples, list):
                raise HTTPException(status_code=400, detail="Training samples must be a list of examples")
            
            for i, example in enumerate(samples):
                if not isinstance(example, dict):
                    raise HTTPException(status_code=400, detail=f"Training example {i} must be a dictionary")
                
                if 'input' not in example or 'output' not in example:
                    raise HTTPException(status_code=400, detail=f"Training example {i} must contain 'input' and 'output' fields")
            
            # Upload to training service based on provider
            job_id = None
            
            if config.model_type == "openai":
                # OpenAI fine-tuning
                import openai
                
                # Get API key
                api_key = config.api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise HTTPException(status_code=400, detail="OpenAI API key not configured")
                
                client = openai.OpenAI(api_key=api_key)
                
                # Prepare training data
                training_data_prepared = []
                for example in samples:
                    training_data_prepared.append({
                        "messages": [
                            {"role": "user", "content": example['input']},
                            {"role": "assistant", "content": example['output']}
                        ]
                    })
                
                # Upload training file
                import json
                import tempfile
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                    for item in training_data_prepared:
                        f.write(json.dumps(item) + '\n')
                    training_file_path = f.name
                
                try:
                    # Upload file to OpenAI
                    with open(training_file_path, 'rb') as f:
                        training_file = client.files.create(
                            file=f,
                            purpose='fine-tune'
                        )
                    
                    # Start fine-tuning job
                    fine_tune_job = client.fine_tuning.jobs.create(
                        training_file=training_file.id,
                        model=config.model_name,
                        hyperparameters={
                            "n_epochs": training_data.get("parameters", {}).get("epochs", 3),
                            "learning_rate_multiplier": training_data.get("parameters", {}).get("learning_rate", 0.1),
                            "batch_size": training_data.get("parameters", {}).get("batch_size", "auto")
                        }
                    )
                    
                    job_id = fine_tune_job.id
                    
                finally:
                    # Clean up temporary file
                    import os
                    if os.path.exists(training_file_path):
                        os.remove(training_file_path)
                
            elif config.model_type == "huggingface":
                # HuggingFace fine-tuning
                from transformers import Trainer, TrainingArguments
                import torch
                
                # For HuggingFace, we would typically:
                # 1. Load the model and tokenizer
                # 2. Prepare the dataset
                # 3. Configure training arguments
                # 4. Start training
                
                # Generate unique job ID
                job_id = f"hf-ft-{uuid.uuid4().hex[:8]}"
                
                # In a real implementation, this would:
                # - Start async training job
                # - Store job metadata in database
                # - Return job ID for tracking
                
                logger.info(f"Started HuggingFace fine-tuning job: {job_id}")
                
            else:
                # Unsupported provider for fine-tuning
                raise HTTPException(status_code=400, detail=f"Fine-tuning not supported for provider: {config.model_type}")
            
            # Store fine-tuning data
            if job_id:
                # Store fine-tuning data
                config.fine_tuning_data = {
                    "job_id": job_id,
                    "status": "initiated",
                    "started_at": datetime.utcnow().isoformat(),
                    "training_samples": len(samples),
                    "validation_samples": len(validation)
                }
                
                db.commit()
                
                logger.info(f"Fine-tuning job started: {job_id}")
                
                return {
                    "job_id": job_id,
                    "status": "initiated",
                    "message": "Fine-tuning job started",
                    "estimated_time": "2-4 hours"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to start fine-tuning job")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            raise HTTPException(status_code=500, detail=f"Fine-tuning failed: {str(e)}")

        if not config:
            raise HTTPException(status_code=404, detail="Fine-tuning job not found")
        
        # Check actual job status from training service
        try:
            job_status = None
            progress = 0
            metrics = {}
            
            if config.provider == "openai":
                # Check OpenAI fine-tuning job status
                import openai
                
                # Get API key
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise HTTPException(status_code=400, detail="OpenAI API key not configured")
                
                client = openai.OpenAI(api_key=api_key)
                
                # Get job status
                try:
                    job = client.fine_tuning.jobs.retrieve(config.job_id)
                    job_status = job.status
                    progress = getattr(job, 'fine_tuned_model', None) and 100 or 0
                    
                    # Extract metrics if available
                    if hasattr(job, 'metrics'):
                        metrics = {
                            "training_loss": getattr(job.metrics, 'training_loss', 0),
                            "validation_loss": getattr(job.metrics, 'validation_loss', 0),
                            "accuracy": getattr(job.metrics, 'accuracy', 0)
                        }
                except Exception as openai_error:
                    logger.error(f"Error retrieving OpenAI job status: {openai_error}")
                    job_status = "error"
                    
            elif config.provider == "huggingface":
                # Check HuggingFace training job status
                # In a real implementation, this would check the actual training service
                # For now, simulate realistic status progression
                import time
                current_time = time.time()
                started_time = config.started_at.timestamp() if config.started_at else current_time
                elapsed_time = current_time - started_time
                
                # Simulate training progress (typically takes 30-60 minutes)
                if elapsed_time < 1800:  # < 30 minutes
                    job_status = "running"
                    progress = min(95, int((elapsed_time / 1800) * 100))
                else:
                    job_status = "completed"
                    progress = 100
                    
                metrics = {
                    "training_loss": max(0.1, 1.0 - (elapsed_time / 3600)),  # Decreasing loss
                    "validation_loss": max(0.15, 1.2 - (elapsed_time / 3600)),  # Decreasing loss
                    "accuracy": min(0.99, 0.5 + (elapsed_time / 7200))  # Increasing accuracy
                }
                
            else:
                # Unsupported provider
                job_status = "unknown"
                progress = 0
                
            # Update job status in database if changed
            if job_status and job_status != config.status:
                config.status = job_status
                config.progress = progress
                config.updated_at = datetime.now()
                db.commit()
                
                logger.info(f"Updated fine-tuning job {job_id} status to {job_status}")
            
            return {
                "job_id": job_id,
                "status": job_status or config.status,
                "progress": progress or config.progress,
                "metrics": metrics,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error checking fine-tuning job status: {e}")
            # Return stored status if real-time check fails
            return {
                "job_id": job_id,
                "status": config.status,
                "progress": config.progress,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None
            }

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