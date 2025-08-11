"""
Hybrid Summarization API Endpoints
REST API for hybrid summarization functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import os
import sys
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_middleware import get_current_active_user, require_write
from api.dependencies import create_api_response, create_error_response

# Import hybrid summarization system
from hybrid_summarization_system import (
    HybridSummarizer, MultiDocumentSummarizer, SummarizationPersonalizer,
    SummarizationRequest, SummaryResult, DocumentSummary,
    SummarizationType, SummaryLength, SummaryStyle
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid-summarization", tags=["Hybrid Summarization"])

# Initialize components
hybrid_summarizer = HybridSummarizer()
multi_doc_summarizer = MultiDocumentSummarizer()
personalizer = SummarizationPersonalizer()

# Pydantic models for API
class SummarizationRequestAPI(BaseModel):
    """API request model for summarization"""
    text: str = Field(..., description="Text to summarize", min_length=10)
    summary_type: str = Field(default="hybrid", description="Type of summarization")
    length: str = Field(default="medium", description="Summary length")
    style: str = Field(default="formal", description="Summary style")
    query: Optional[str] = Field(None, description="Query for focused summarization")
    max_sentences: Optional[int] = Field(None, description="Maximum sentences", ge=1, le=50)
    max_words: Optional[int] = Field(None, description="Maximum words", ge=10, le=1000)
    focus_keywords: Optional[List[str]] = Field(None, description="Keywords to focus on")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords to exclude")
    preserve_structure: bool = Field(default=False, description="Preserve original structure")
    include_quotes: bool = Field(default=True, description="Include quotes in summary")
    language: str = Field(default="en", description="Language code")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")

class MultiDocumentRequestAPI(BaseModel):
    """API request model for multi-document summarization"""
    documents: List[Dict[str, str]] = Field(..., description="List of documents to summarize")
    summary_type: str = Field(default="hybrid", description="Type of summarization")
    length: str = Field(default="medium", description="Summary length")
    style: str = Field(default="formal", description="Summary style")
    query: Optional[str] = Field(None, description="Query for focused summarization")
    max_sentences: Optional[int] = Field(None, description="Maximum sentences", ge=1, le=50)
    max_words: Optional[int] = Field(None, description="Maximum words", ge=10, le=1000)
    focus_keywords: Optional[List[str]] = Field(None, description="Keywords to focus on")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords to exclude")
    language: str = Field(default="en", description="Language code")

class UserPreferencesAPI(BaseModel):
    """API model for user preferences"""
    preferred_length: str = Field(default="medium", description="Preferred summary length")
    preferred_style: str = Field(default="formal", description="Preferred summary style")
    focus_areas: List[str] = Field(default=[], description="Areas of focus")
    avoid_topics: List[str] = Field(default=[], description="Topics to avoid")
    technical_level: str = Field(default="medium", description="Technical level preference")
    include_examples: bool = Field(default=True, description="Include examples")
    include_numbers: bool = Field(default=True, description="Include numbers")
    language: str = Field(default="en", description="Preferred language")

class SummaryResultAPI(BaseModel):
    """API response model for summary results"""
    summary: str
    summary_type: str
    length: str
    style: str
    word_count: int
    sentence_count: int
    compression_ratio: float
    quality_score: float
    key_points: List[str]
    extracted_sentences: List[str]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]
    created_at: datetime

def _convert_enum_values(request_data: dict) -> SummarizationRequest:
    """Convert string values to enum values"""
    # Convert summary_type
    summary_type_map = {
        "extractive": SummarizationType.EXTRACTIVE,
        "abstractive": SummarizationType.ABSTRACTIVE,
        "hybrid": SummarizationType.HYBRID,
        "query_focused": SummarizationType.QUERY_FOCUSED,
        "multi_document": SummarizationType.MULTI_DOCUMENT
    }
    
    # Convert length
    length_map = {
        "brief": SummaryLength.BRIEF,
        "short": SummaryLength.SHORT,
        "medium": SummaryLength.MEDIUM,
        "long": SummaryLength.LONG,
        "custom": SummaryLength.CUSTOM
    }
    
    # Convert style
    style_map = {
        "formal": SummaryStyle.FORMAL,
        "casual": SummaryStyle.CASUAL,
        "technical": SummaryStyle.TECHNICAL,
        "executive": SummaryStyle.EXECUTIVE,
        "academic": SummaryStyle.ACADEMIC,
        "journalistic": SummaryStyle.JOURNALISTIC
    }
    
    return SummarizationRequest(
        text=request_data["text"],
        summary_type=summary_type_map.get(request_data.get("summary_type", "hybrid"), SummarizationType.HYBRID),
        length=length_map.get(request_data.get("length", "medium"), SummaryLength.MEDIUM),
        style=style_map.get(request_data.get("style", "formal"), SummaryStyle.FORMAL),
        query=request_data.get("query"),
        max_sentences=request_data.get("max_sentences"),
        max_words=request_data.get("max_words"),
        focus_keywords=request_data.get("focus_keywords"),
        exclude_keywords=request_data.get("exclude_keywords"),
        preserve_structure=request_data.get("preserve_structure", False),
        include_quotes=request_data.get("include_quotes", True),
        language=request_data.get("language", "en"),
        user_preferences=request_data.get("user_preferences")
    )

def _convert_result_to_api(result: SummaryResult) -> SummaryResultAPI:
    """Convert SummaryResult to API response model"""
    return SummaryResultAPI(
        summary=result.summary,
        summary_type=result.summary_type.value,
        length=result.length.value,
        style=result.style.value,
        word_count=result.word_count,
        sentence_count=result.sentence_count,
        compression_ratio=result.compression_ratio,
        quality_score=result.quality_score,
        key_points=result.key_points,
        extracted_sentences=result.extracted_sentences,
        confidence_score=result.confidence_score,
        processing_time=result.processing_time,
        metadata=result.metadata,
        created_at=result.created_at
    )

@router.post("/summarize", response_model=SummaryResultAPI)
async def create_summary(
    request: SummarizationRequestAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a hybrid summary from text"""
    try:
        # Convert API request to internal request
        internal_request = _convert_enum_values(request.dict())
        
        # Generate summary
        result = await hybrid_summarizer.summarize(internal_request)
        
        # Convert result to API response
        api_result = _convert_result_to_api(result)
        
        logger.info(f"Summary created for user {current_user.get('user_id', 'unknown')}: "
                   f"{result.word_count} words, {result.quality_score:.2f} quality")
        
        return create_api_response(
            data=api_result,
            message="Summary created successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create summary"
        )

@router.post("/multi-document", response_model=SummaryResultAPI)
async def create_multi_document_summary(
    request: MultiDocumentRequestAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a summary from multiple documents"""
    try:
        if not request.documents:
            raise ValueError("No documents provided")
        
        # Validate documents
        for i, doc in enumerate(request.documents):
            if not doc.get('content'):
                raise ValueError(f"Document {i} has no content")
        
        # Create internal request
        internal_request = _convert_enum_values({
            "text": "",  # Will be set by multi-doc summarizer
            "summary_type": request.summary_type,
            "length": request.length,
            "style": request.style,
            "query": request.query,
            "max_sentences": request.max_sentences,
            "max_words": request.max_words,
            "focus_keywords": request.focus_keywords,
            "exclude_keywords": request.exclude_keywords,
            "language": request.language
        })
        
        # Generate multi-document summary
        result = await multi_doc_summarizer.summarize_documents(
            request.documents, internal_request
        )
        
        # Convert result to API response
        api_result = _convert_result_to_api(result)
        
        logger.info(f"Multi-document summary created for user {current_user.get('user_id', 'unknown')}: "
                   f"{len(request.documents)} documents, {result.word_count} words")
        
        return create_api_response(
            data=api_result,
            message="Multi-document summary created successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in multi-document summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in multi-document summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create multi-document summary"
        )

@router.get("/types")
async def get_summary_types():
    """Get available summary types"""
    return create_api_response(
        data={
            "summary_types": [
                {"value": "extractive", "label": "Extractive", "description": "Extract key sentences from original text"},
                {"value": "abstractive", "label": "Abstractive", "description": "Generate new summary text"},
                {"value": "hybrid", "label": "Hybrid", "description": "Combine extractive and abstractive approaches"},
                {"value": "query_focused", "label": "Query Focused", "description": "Focus on specific query or topic"},
                {"value": "multi_document", "label": "Multi-Document", "description": "Summarize multiple documents"}
            ],
            "lengths": [
                {"value": "brief", "label": "Brief", "description": "1-2 sentences"},
                {"value": "short", "label": "Short", "description": "3-5 sentences"},
                {"value": "medium", "label": "Medium", "description": "1-2 paragraphs"},
                {"value": "long", "label": "Long", "description": "3+ paragraphs"},
                {"value": "custom", "label": "Custom", "description": "User-defined length"}
            ],
            "styles": [
                {"value": "formal", "label": "Formal", "description": "Professional and formal tone"},
                {"value": "casual", "label": "Casual", "description": "Conversational and relaxed tone"},
                {"value": "technical", "label": "Technical", "description": "Technical terminology and precision"},
                {"value": "executive", "label": "Executive", "description": "Focus on decisions and outcomes"},
                {"value": "academic", "label": "Academic", "description": "Analytical and scholarly approach"},
                {"value": "journalistic", "label": "Journalistic", "description": "Who, what, when, where, why format"}
            ]
        },
        message="Summary configuration options retrieved successfully"
    )

@router.post("/preferences/{user_id}")
async def set_user_preferences(
    user_id: str,
    preferences: UserPreferencesAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Set user summarization preferences"""
    try:
        # Verify user can modify preferences (either own preferences or admin)
        if current_user.get('user_id') != user_id and not current_user.get('is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify other user's preferences"
            )
        
        # Create user profile
        personalizer.create_user_profile(user_id, preferences.dict())
        
        logger.info(f"Preferences updated for user {user_id}")
        
        return create_api_response(
            data={"user_id": user_id, "preferences": preferences.dict()},
            message="User preferences updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )

@router.get("/preferences/{user_id}")
async def get_user_preferences(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get user summarization preferences"""
    try:
        # Verify user can access preferences
        if current_user.get('user_id') != user_id and not current_user.get('is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other user's preferences"
            )
        
        # Get user profile
        profile = personalizer.user_profiles.get(user_id)
        
        if not profile:
            # Return default preferences
            profile = {
                'preferred_length': 'medium',
                'preferred_style': 'formal',
                'focus_areas': [],
                'avoid_topics': [],
                'technical_level': 'medium',
                'include_examples': True,
                'include_numbers': True,
                'language': 'en'
            }
        
        return create_api_response(
            data={"user_id": user_id, "preferences": profile},
            message="User preferences retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user preferences"
        )

@router.post("/batch")
async def create_batch_summaries(
    requests: List[SummarizationRequestAPI],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user)
):
    """Create multiple summaries in batch"""
    try:
        if len(requests) > 10:  # Limit batch size
            raise ValueError("Batch size cannot exceed 10 requests")
        
        # Process summaries
        results = []
        for i, request in enumerate(requests):
            try:
                internal_request = _convert_enum_values(request.dict())
                result = await hybrid_summarizer.summarize(internal_request)
                api_result = _convert_result_to_api(result)
                results.append({
                    "index": i,
                    "status": "success",
                    "result": api_result
                })
            except Exception as e:
                logger.error(f"Error processing batch item {i}: {e}")
                results.append({
                    "index": i,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Batch summarization completed for user {current_user.get('user_id', 'unknown')}: "
                   f"{len(requests)} requests processed")
        
        return create_api_response(
            data={"results": results, "total": len(requests)},
            message="Batch summarization completed"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in batch summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in batch summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch summarization"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        test_request = SummarizationRequest(
            text="This is a test sentence for health check.",
            summary_type=SummarizationType.EXTRACTIVE,
            length=SummaryLength.BRIEF
        )
        
        result = await hybrid_summarizer.summarize(test_request)
        
        return create_api_response(
            data={
                "status": "healthy",
                "components": {
                    "hybrid_summarizer": "operational",
                    "multi_doc_summarizer": "operational",
                    "personalizer": "operational"
                },
                "test_result": {
                    "processing_time": result.processing_time,
                    "quality_score": result.quality_score
                }
            },
            message="Hybrid summarization service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=create_error_response(
                error="Service unhealthy",
                details=str(e)
            )
        )