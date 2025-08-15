"""
Transcript Correction API Endpoints
Connects React frontend to the existing TranscriptionCorrectionSystem
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import asyncio
import logging
from datetime import datetime

# Import existing correction system
from transcription_correction_engine import (
    TranscriptionCorrectionSystem,
    CorrectionType,
    CorrectionResult,
    UserCorrection
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transcript-correction", tags=["transcript-correction"])

# Global correction system instance
_correction_system: Optional[TranscriptionCorrectionSystem] = None

def get_correction_system() -> TranscriptionCorrectionSystem:
    """Get or create correction system instance"""
    global _correction_system
    if _correction_system is None:
        _correction_system = TranscriptionCorrectionSystem(enable_learning=True)
    return _correction_system

# Request/Response Models
class CorrectionRequest(BaseModel):
    text: str = Field(..., description="Text to correct")
    correction_types: List[CorrectionType] = Field(
        default=[CorrectionType.SPELLING, CorrectionType.GRAMMAR, CorrectionType.PUNCTUATION],
        description="Types of corrections to apply"
    )
    context: Optional[str] = Field(None, description="Additional context for correction")
    user_id: Optional[str] = Field(None, description="User ID for learning")

class CorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    corrections: List[Dict[str, Any]]
    confidence_score: float
    processing_time_ms: int

class UserFeedbackRequest(BaseModel):
    original_text: str
    suggested_correction: str
    user_correction: str
    accepted: bool
    correction_type: CorrectionType
    user_id: Optional[str] = None

class SegmentCorrectionRequest(BaseModel):
    segment_id: str
    original_text: str
    corrected_text: str
    user_id: Optional[str] = None

@router.post("/correct", response_model=CorrectionResponse)
async def correct_text(
    request: CorrectionRequest,
    correction_system: TranscriptionCorrectionSystem = Depends(get_correction_system)
):
    """
    Apply AI-powered corrections to text
    """
    try:
        start_time = datetime.now()
        
        # Apply corrections using existing system
        result = await correction_system.correct_transcription(
            text=request.text,
            correction_types=request.correction_types,
            context=request.context
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return CorrectionResponse(
            original_text=request.text,
            corrected_text=result.corrected_text,
            corrections=[correction.to_dict() for correction in result.corrections],
            confidence_score=result.confidence_score,
            processing_time_ms=int(processing_time)
        )
        
    except Exception as e:
        logger.error(f"Correction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Correction failed: {str(e)}")

@router.post("/feedback")
async def submit_correction_feedback(
    request: UserFeedbackRequest,
    correction_system: TranscriptionCorrectionSystem = Depends(get_correction_system)
):
    """
    Submit user feedback on corrections for learning
    """
    try:
        if correction_system.learning_system:
            user_correction = UserCorrection(
                original_text=request.original_text,
                suggested_correction=request.suggested_correction,
                user_correction=request.user_correction,
                accepted=request.accepted,
                correction_type=request.correction_type,
                user_id=request.user_id,
                timestamp=datetime.now()
            )
            
            await correction_system.learn_from_correction(user_correction)
            
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

@router.post("/segment/correct")
async def correct_segment(
    request: SegmentCorrectionRequest,
    correction_system: TranscriptionCorrectionSystem = Depends(get_correction_system)
):
    """
    Apply corrections to a specific transcript segment
    """
    try:
        # Apply corrections to segment
        correction_request = CorrectionRequest(
            text=request.original_text,
            user_id=request.user_id
        )
        
        result = await correct_text(correction_request, correction_system)
        
        # If user provided manual correction, learn from it
        if request.corrected_text != result.corrected_text and correction_system.learning_system:
            user_correction = UserCorrection(
                original_text=request.original_text,
                suggested_correction=result.corrected_text,
                user_correction=request.corrected_text,
                accepted=False,  # User chose different correction
                correction_type=CorrectionType.SPELLING,  # Default type
                user_id=request.user_id,
                timestamp=datetime.now()
            )
            
            await correction_system.learn_from_correction(user_correction)
        
        return {
            "segment_id": request.segment_id,
            "original_text": request.original_text,
            "ai_suggestion": result.corrected_text,
            "final_text": request.corrected_text,
            "corrections_applied": result.corrections
        }
        
    except Exception as e:
        logger.error(f"Segment correction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Segment correction failed: {str(e)}")

@router.get("/suggestions/{text}")
async def get_correction_suggestions(
    text: str,
    correction_system: TranscriptionCorrectionSystem = Depends(get_correction_system)
):
    """
    Get real-time correction suggestions for text
    """
    try:
        # Get quick suggestions without full processing
        result = await correction_system.correct_transcription(
            text=text,
            correction_types=[CorrectionType.SPELLING, CorrectionType.GRAMMAR]
        )
        
        return {
            "suggestions": [
                {
                    "type": correction.correction_type.value,
                    "original": correction.original,
                    "suggestion": correction.corrected,
                    "confidence": correction.confidence,
                    "position": correction.position
                }
                for correction in result.corrections
            ]
        }
        
    except Exception as e:
        logger.error(f"Suggestion generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")

@router.get("/stats")
async def get_correction_stats(
    correction_system: TranscriptionCorrectionSystem = Depends(get_correction_system)
):
    """
    Get correction system statistics
    """
    try:
        stats = {}
        
        if correction_system.learning_system:
            patterns = await correction_system.learning_system.get_correction_patterns(limit=100)
            stats = {
                "learned_patterns": len(patterns),
                "total_corrections": len(patterns),
                "accuracy_improvement": "N/A"  # Would need historical data
            }
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        correction_system = get_correction_system()
        return {
            "status": "healthy",
            "correction_system": "operational",
            "learning_enabled": correction_system.learning_system is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }