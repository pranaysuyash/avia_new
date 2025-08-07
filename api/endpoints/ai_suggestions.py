"""
AI Suggestions API Endpoints
Provides intelligent content suggestions, auto-completion, and smart replies
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from api.database import get_db, User
from api.auth import get_current_active_user, get_current_user_ws
from services.ai_suggestions_service import (
    ai_suggestions_service,
    SuggestionType,
    ContentContext,
    Suggestion,
    AutoCompleteResult,
    ContentSuggestion,
    SmartReply
)
from services.audit_logging_service import audit_service, AuditEventType

router = APIRouter(
    prefix="/api/v1/ai-suggestions",
    tags=["ai-suggestions"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models
class AutoCompleteRequest(BaseModel):
    """Auto-completion request"""
    text: str = Field(..., min_length=1, max_length=1000, description="Partial text to complete")
    context: ContentContext = Field(..., description="Content context")
    max_completions: int = Field(5, ge=1, le=10, description="Maximum number of completions")
    language: str = Field("en", description="Language code")


class ContentSuggestionRequest(BaseModel):
    """Content suggestion request"""
    content: str = Field(..., min_length=1, max_length=10000, description="Content to analyze")
    context: ContentContext = Field(..., description="Content context")
    suggestion_types: Optional[List[SuggestionType]] = Field(None, description="Specific suggestion types")


class SmartReplyRequest(BaseModel):
    """Smart reply request"""
    message: str = Field(..., min_length=1, max_length=5000, description="Message to reply to")
    context: ContentContext = Field(ContentContext.CHAT, description="Content context")
    max_replies: int = Field(3, ge=1, le=5, description="Maximum number of replies")


class SuggestionFeedback(BaseModel):
    """Feedback on a suggestion"""
    suggestion_id: str = Field(..., description="Suggestion ID")
    accepted: bool = Field(..., description="Whether suggestion was accepted")
    context: ContentContext = Field(..., description="Content context")


class BatchAutoCompleteRequest(BaseModel):
    """Batch auto-completion request"""
    requests: List[AutoCompleteRequest] = Field(..., max_items=10)


# Auto-completion endpoint
@router.post("/autocomplete", response_model=Dict[str, Any])
async def get_auto_completions(
    request: AutoCompleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get auto-completion suggestions for partial text
    
    Returns intelligent completions based on:
    - User's writing history
    - Context awareness
    - Common patterns
    - AI predictions
    """
    
    try:
        result = await ai_suggestions_service.get_auto_completions(
            db=db,
            user_id=current_user.id,
            text=request.text,
            context=request.context,
            max_completions=request.max_completions,
            language=request.language
        )
        
        return {
            "completions": result.completions,
            "confidence_scores": result.confidence_scores,
            "context_aware": result.context_aware,
            "language": result.language
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auto-completions: {str(e)}"
        )


# Batch auto-completion endpoint
@router.post("/autocomplete/batch", response_model=List[Dict[str, Any]])
async def get_batch_auto_completions(
    batch_request: BatchAutoCompleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get auto-completions for multiple texts in batch
    
    Useful for real-time applications needing multiple completions
    """
    
    try:
        tasks = []
        for request in batch_request.requests:
            task = ai_suggestions_service.get_auto_completions(
                db=db,
                user_id=current_user.id,
                text=request.text,
                context=request.context,
                max_completions=request.max_completions,
                language=request.language
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        return [
            {
                "text": req.text,
                "completions": result.completions,
                "confidence_scores": result.confidence_scores,
                "context_aware": result.context_aware,
                "language": result.language
            }
            for req, result in zip(batch_request.requests, results)
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch auto-completions: {str(e)}"
        )


# Content suggestions endpoint
@router.post("/suggest", response_model=Dict[str, Any])
async def get_content_suggestions(
    request: ContentSuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive content suggestions
    
    Provides:
    - Grammar corrections
    - Style improvements
    - Content expansion ideas
    - Summarization options
    - Keyword extraction
    - Related content
    """
    
    # Check user tier for advanced features
    if request.suggestion_types and SuggestionType.CONTENT_EXPANSION in request.suggestion_types:
        if current_user.subscription_tier not in ["pro", "enterprise"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Content expansion requires Pro or Enterprise subscription"
            )
    
    try:
        result = await ai_suggestions_service.get_content_suggestions(
            db=db,
            user_id=current_user.id,
            content=request.content,
            context=request.context,
            suggestion_types=request.suggestion_types
        )
        
        # Convert suggestions to dict format
        suggestions_dict = []
        for suggestion in result.suggestions:
            suggestions_dict.append({
                "id": suggestion.id,
                "type": suggestion.type.value,
                "text": suggestion.text,
                "confidence": suggestion.confidence,
                "metadata": suggestion.metadata,
                "created_at": suggestion.created_at.isoformat()
            })
        
        return {
            "suggestions": suggestions_dict,
            "keywords": result.keywords,
            "topics": result.topics,
            "related_content": result.related_content,
            "generated_at": result.generated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content suggestions: {str(e)}"
        )


# Smart reply endpoint
@router.post("/smart-reply", response_model=Dict[str, Any])
async def get_smart_replies(
    request: SmartReplyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate smart reply suggestions
    
    Provides contextual reply options with:
    - Multiple tone options
    - Context-aware responses
    - Personalized based on user style
    """
    
    if current_user.subscription_tier not in ["pro", "enterprise"]:
        # Limit free users to 1 reply
        request.max_replies = min(request.max_replies, 1)
    
    try:
        result = await ai_suggestions_service.get_smart_replies(
            db=db,
            user_id=current_user.id,
            message=request.message,
            context=request.context,
            max_replies=request.max_replies
        )
        
        return {
            "replies": result.replies,
            "tones": result.tones,
            "contexts": result.contexts,
            "confidence": result.confidence
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate smart replies: {str(e)}"
        )


# Suggestion feedback endpoint
@router.post("/feedback")
async def submit_suggestion_feedback(
    feedback: SuggestionFeedback,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a suggestion
    
    Helps improve future suggestions through learning
    """
    
    try:
        await ai_suggestions_service.learn_from_feedback(
            db=db,
            user_id=current_user.id,
            suggestion_id=feedback.suggestion_id,
            accepted=feedback.accepted,
            context=feedback.context
        )
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# Real-time auto-completion WebSocket
@router.websocket("/ws/autocomplete")
async def autocomplete_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time auto-completion
    
    Protocol:
    - Client sends: {"text": "partial text", "context": "email"}
    - Server responds: {"completions": [...], "confidence_scores": [...]}
    """
    
    await websocket.accept()
    
    try:
        # Authenticate user
        current_user = await get_current_user_ws(token, db)
        if not current_user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        # Track connection
        connection_id = f"autocomplete_{current_user.id}_{datetime.utcnow().timestamp()}"
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Validate request
            if "text" not in data or "context" not in data:
                await websocket.send_json({
                    "error": "Invalid request format"
                })
                continue
            
            try:
                # Get auto-completions
                context = ContentContext(data["context"])
                result = await ai_suggestions_service.get_auto_completions(
                    db=db,
                    user_id=current_user.id,
                    text=data["text"],
                    context=context,
                    max_completions=data.get("max_completions", 5),
                    language=data.get("language", "en")
                )
                
                # Send response
                await websocket.send_json({
                    "completions": result.completions,
                    "confidence_scores": result.confidence_scores,
                    "context_aware": result.context_aware,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                await websocket.send_json({
                    "error": f"Failed to get completions: {str(e)}"
                })
    
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal error")


# Grammar check endpoint
@router.post("/grammar-check", response_model=Dict[str, Any])
async def check_grammar(
    content: str = Query(..., description="Content to check"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Quick grammar check for content
    
    Returns grammar corrections with explanations
    """
    
    try:
        # Get grammar suggestions only
        result = await ai_suggestions_service.get_content_suggestions(
            db=db,
            user_id=current_user.id,
            content=content,
            context=ContentContext.DOCUMENT,
            suggestion_types=[SuggestionType.GRAMMAR_CORRECTION]
        )
        
        corrections = []
        for suggestion in result.suggestions:
            if suggestion.type == SuggestionType.GRAMMAR_CORRECTION:
                corrections.append({
                    "error": suggestion.metadata.get("error", ""),
                    "correction": suggestion.metadata.get("correction", ""),
                    "reason": suggestion.metadata.get("reason", ""),
                    "corrected_text": suggestion.text
                })
        
        return {
            "has_errors": len(corrections) > 0,
            "corrections": corrections,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check grammar: {str(e)}"
        )


# Summarization endpoint
@router.post("/summarize", response_model=Dict[str, Any])
async def summarize_content(
    content: str = Query(..., description="Content to summarize"),
    length: str = Query("medium", regex="^(short|medium|long)$", description="Summary length"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate content summary
    
    Length options:
    - short: 1-2 sentences
    - medium: 3-5 sentences
    - long: Detailed summary
    """
    
    try:
        # Get summarization suggestions
        result = await ai_suggestions_service.get_content_suggestions(
            db=db,
            user_id=current_user.id,
            content=content,
            context=ContentContext.DOCUMENT,
            suggestion_types=[SuggestionType.SUMMARIZATION]
        )
        
        # Find summary matching requested length
        summary = None
        for suggestion in result.suggestions:
            if suggestion.type == SuggestionType.SUMMARIZATION:
                summary_length = suggestion.metadata.get("length", "medium")
                if summary_length == length:
                    summary = suggestion.text
                    break
        
        # Fallback to first summary
        if not summary and result.suggestions:
            summary = result.suggestions[0].text
        
        return {
            "summary": summary or "Unable to generate summary",
            "keywords": result.keywords[:5],
            "word_count": len(content.split()),
            "summary_word_count": len(summary.split()) if summary else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize content: {str(e)}"
        )


# Writing assistant settings
@router.get("/settings", response_model=Dict[str, Any])
async def get_writing_settings(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's writing assistant settings"""
    
    # In production, these would be stored in database
    return {
        "auto_complete_enabled": True,
        "grammar_check_enabled": True,
        "style_suggestions_enabled": current_user.subscription_tier in ["pro", "enterprise"],
        "smart_reply_enabled": True,
        "suggestion_delay_ms": 500,
        "min_text_length": 3,
        "preferred_tone": "professional",
        "language": "en"
    }


@router.put("/settings")
async def update_writing_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Update user's writing assistant settings"""
    
    # Validate settings based on subscription tier
    if settings.get("style_suggestions_enabled") and current_user.subscription_tier not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Style suggestions require Pro or Enterprise subscription"
        )
    
    # In production, save to database
    return {
        "status": "success",
        "message": "Settings updated successfully"
    }


# Health check
@router.get("/health")
async def ai_suggestions_health_check():
    """AI suggestions service health check"""
    
    return {
        "status": "healthy",
        "service": "ai_suggestions",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "autocomplete": "operational",
            "suggestions": "operational",
            "smart_reply": "operational",
            "grammar_check": "operational"
        }
    }