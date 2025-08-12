#!/usr/bin/env python3
"""
Enhanced Collaborative Intelligence API Endpoints
Comprehensive API for discussion facilitation, MoM creation, action items, and feedback
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import asyncio
import logging
from pydantic import BaseModel, Field

# Import existing auth and core infrastructure
try:
    from api.auth.dependencies import get_current_user, require_permissions
    from api.core.base_service import BaseService
    from api.core.exceptions import ValidationError, NotFoundError
except ImportError:
    # Fallback for testing
    def get_current_user(): return {"user_id": "test_user"}
    def require_permissions(perms): return lambda: True
    class BaseService: pass
    class ValidationError(Exception): pass
    class NotFoundError(Exception): pass

# Import our enhanced system
try:
    from enhanced_collaborative_intelligence import (
        EnhancedCollaborativeIntelligence,
        MeetingOutcome
    )
    from collaborative_discussion_facilitator import (
        DiscussionContext,
        FacilitationMode
    )
    from collaborative_feedback_system import FeedbackType
except ImportError:
    # Mock for testing
    class EnhancedCollaborativeIntelligence:
        def __init__(self, engine): pass
        async def start_enhanced_session(self, session_id, context, **kwargs): return {"success": True}
        async def process_enhanced_discussion_update(self, session_id, data): return {}
        async def collect_participant_feedback(self, session_id, user_id, feedback_type, rating, text=None): return "feedback_id"
        async def generate_comprehensive_mom(self, session_id): return {}
        async def end_enhanced_session(self, session_id): return {}
        def get_session_status(self, session_id): return {}
    
    class DiscussionContext:
        def __init__(self, **kwargs): pass
    
    class FacilitationMode:
        BRAINSTORMING = "brainstorming"
        DECISION_MAKING = "decision_making"
        PROBLEM_SOLVING = "problem_solving"
    
    class FeedbackType:
        FACILITATION_QUALITY = "facilitation_quality"
        PARTICIPATION_BALANCE = "participation_balance"
        MEETING_EFFECTIVENESS = "meeting_effectiveness"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/collaboration/enhanced", tags=["Enhanced Collaborative Intelligence"])
security = HTTPBearer()

# Pydantic models for API
class StartEnhancedSessionRequest(BaseModel):
    """Request to start enhanced collaborative session"""
    session_id: str = Field(..., description="Collaborative session ID")
    topic: str = Field(..., description="Discussion topic")
    mode: str = Field(..., description="Facilitation mode", regex="^(brainstorming|decision_making|problem_solving|knowledge_sharing|conflict_resolution)$")
    duration_minutes: int = Field(30, description="Expected session duration", ge=5, le=480)
    participants: List[str] = Field(..., description="List of participant user IDs")
    objectives: List[str] = Field(default=[], description="Session objectives")
    enable_mom: bool = Field(True, description="Enable Minutes of Meeting generation")
    enable_action_tracking: bool = Field(True, description="Enable real-time action item tracking")
    enable_real_time_feedback: bool = Field(True, description="Enable real-time feedback collection")
    metadata: Dict[str, Any] = Field(default={}, description="Additional session metadata")

class FeedbackRequest(BaseModel):
    """Request to submit participant feedback"""
    feedback_type: str = Field(..., description="Type of feedback")
    rating: float = Field(..., description="Rating from 1-5", ge=1, le=5)
    text_feedback: Optional[str] = Field(None, description="Optional text feedback")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional feedback metadata")

class SessionStatusResponse(BaseModel):
    """Session status response"""
    session_id: str
    status: str
    duration: str
    features_enabled: Dict[str, bool]
    artifacts_count: Dict[str, int]
    facilitation_analytics: Dict[str, Any]
    feedback_summary: Dict[str, Any]

class MoMResponse(BaseModel):
    """Minutes of Meeting response"""
    session_info: Dict[str, Any]
    executive_summary: str
    key_decisions: List[str]
    action_items: List[Dict[str, Any]]
    discussion_highlights: List[str]
    participant_contributions: Dict[str, Any]
    next_steps: List[str]
    attachments: List[str]

class MeetingOutcomeResponse(BaseModel):
    """Comprehensive meeting outcome response"""
    session_id: str
    summary: str
    key_decisions: List[str]
    action_items: List[Dict[str, Any]]
    discussion_highlights: List[str]
    participant_insights: Dict[str, Any]
    facilitation_effectiveness: float
    next_steps: List[str]
    meeting_artifacts: Dict[str, Any]
    feedback_analytics: Dict[str, Any]
    generated_at: datetime

# Global enhanced intelligence instance
enhanced_intelligence_instance: Optional[EnhancedCollaborativeIntelligence] = None

def get_enhanced_intelligence() -> EnhancedCollaborativeIntelligence:
    """Get or create enhanced intelligence instance"""
    global enhanced_intelligence_instance
    if enhanced_intelligence_instance is None:
        # In production, this would use the real collaborative engine
        class MockEngine:
            def get_session_state(self, session_id): return {'segments': []}
            async def broadcast_message(self, session_id, message): pass
        
        enhanced_intelligence_instance = EnhancedCollaborativeIntelligence(MockEngine())
    return enhanced_intelligence_instance

@router.post("/start", response_model=Dict[str, Any])
async def start_enhanced_session(
    request: StartEnhancedSessionRequest,
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(require_permissions(["collaboration.facilitate"]))
):
    """Start enhanced collaborative session with all intelligence features"""
    try:
        enhanced_intelligence = get_enhanced_intelligence()
        
        # Create discussion context
        context = DiscussionContext(
            session_id=request.session_id,
            participants=request.participants,
            topic=request.topic,
            mode=getattr(FacilitationMode, request.mode.upper(), FacilitationMode.BRAINSTORMING),
            duration_minutes=request.duration_minutes,
            objectives=request.objectives,
            current_phase="starting",
            metadata={**request.metadata, "initiated_by": current_user.get("user_id")}
        )
        
        # Start enhanced session
        result = await enhanced_intelligence.start_enhanced_session(
            session_id=request.session_id,
            context=context,
            enable_mom=request.enable_mom,
            enable_action_tracking=request.enable_action_tracking,
            enable_real_time_feedback=request.enable_real_time_feedback
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to start enhanced session'))
        
        logger.info(f"Started enhanced session {request.session_id} for user {current_user.get('user_id')}")
        
        return {
            **result,
            "message": "Enhanced collaborative intelligence session started successfully",
            "started_by": current_user.get("user_id"),
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting enhanced session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(require_permissions(["collaboration.view"]))
):
    """Get comprehensive status of enhanced collaborative session"""
    try:
        enhanced_intelligence = get_enhanced_intelligence()
        status = enhanced_intelligence.get_session_status(session_id)
        
        if 'error' in status:
            raise HTTPException(status_code=404, detail=status['error'])
        
        return SessionStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update/{session_id}")
async def process_enhanced_discussion_update(
    session_id: str,
    session_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(require_permissions(["collaboration.participate"]))
):
    """Process discussion update with enhanced intelligence"""
    try:
        enhanced_intelligence = get_enhanced_intelligence()
        
        # Process the enhanced update
        result = await enhanced_intelligence.process_enhanced_discussion_update(
            session_id, session_data
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "processed_at": datetime.now().isoformat(),
            "processing_results": result
        }
        
    except Exception as e:
        logger.error(f"Error processing enhanced discussion update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback/{session_id}")
async def submit_participant_feedback(
    session_id: str,
    feedback: FeedbackRequest,
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(require_permissions(["collaboration.participate"]))
):
    """Submit participant feedback during the session"""
    try:
        enhanced_intelligence = get_enhanced_intelligence()
        
        feedback_id = await enhanced_intelligence.collect_participant_feedback(
            session_id=session_id,
            user_id=current_user.get("user_id"),
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            text_feedback=feedback.text_feedback
        )
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "session_id": session_id,
            "submitted_by": current_user.get("user_id"),
            "submitted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mom/{session_id}", response_model=MoMResponse)
async def generate_minutes_of_meeting(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(require_permissions(["collaboration.view"]))
):
    """Generate comprehensive Minutes of Meeting"""
    try:
        enhanced_intelligence = get_enhanced_intelligence()
        
        mom_content = await enhanced_intelligence.generate_comprehensive_mom(session_id)
        
        if 'error' in mom_content:
            raise HTTPException(status_code=400, detail=mom_content['error'])
        
        return MoMResponse(**mom_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating MoM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end/{session_id}", response_model=MeetingOutcomeResponse)
async def end_enhanced_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    _: bool = Depends(require_permissions(["collaboration.facilitate"]))
):
    """End enhanced session and generate comprehensive meeting outcome"""
    try:
        enhanced_intelligence = get_enhanced_intelligence()
        
        outcome = await enhanced_intelligence.end_enhanced_session(session_id)
        
        logger.info(f"Ended enhanced session {session_id} for user {current_user.get('user_id')}")
        
        return MeetingOutcomeResponse(
            session_id=outcome.session_id,
            summary=outcome.summary,
            key_decisions=outcome.key_decisions,
            action_items=outcome.action_items,
            discussion_highlights=outcome.discussion_highlights,
            participant_insights=outcome.participant_insights,
            facilitation_effectiveness=outcome.facilitation_effectiveness,
            next_steps=outcome.next_steps,
            meeting_artifacts=outcome.meeting_artifacts,
            feedback_analytics=outcome.feedback_analytics,
            generated_at=outcome.generated_at
        )
        
    except Exception as e:
        logger.error(f"Error ending enhanced session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{session_id}")
async def enhanced_collaboration_websocket(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket endpoint for real-time enhanced collaboration"""
    await websocket.accept()
    
    try:
        logger.info(f"Enhanced WebSocket connection established for session {session_id}")
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process different message types
                if message.get('type') == 'discussion_update':
                    # Enhanced discussion processing
                    enhanced_intelligence = get_enhanced_intelligence()
                    result = await enhanced_intelligence.process_enhanced_discussion_update(
                        session_id, message.get('data', {})
                    )
                    
                    response = {
                        "type": "enhanced_processing_result",
                        "session_id": session_id,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(response))
                
                elif message.get('type') == 'request_mom':
                    # Generate real-time MoM
                    enhanced_intelligence = get_enhanced_intelligence()
                    mom_content = await enhanced_intelligence.generate_comprehensive_mom(session_id)
                    
                    response = {
                        "type": "mom_generated",
                        "session_id": session_id,
                        "mom": mom_content,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(response))
                
                elif message.get('type') == 'submit_feedback':
                    # Process real-time feedback
                    enhanced_intelligence = get_enhanced_intelligence()
                    feedback_data = message.get('feedback', {})
                    
                    feedback_id = await enhanced_intelligence.collect_participant_feedback(
                        session_id=session_id,
                        user_id=message.get('user_id', 'anonymous'),
                        feedback_type=feedback_data.get('type', 'user_satisfaction'),
                        rating=feedback_data.get('rating', 3.0),
                        text_feedback=feedback_data.get('text')
                    )
                    
                    response = {
                        "type": "feedback_received",
                        "session_id": session_id,
                        "feedback_id": feedback_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(response))
                
                elif message.get('type') == 'get_status':
                    # Get real-time status
                    enhanced_intelligence = get_enhanced_intelligence()
                    status = enhanced_intelligence.get_session_status(session_id)
                    
                    response = {
                        "type": "session_status",
                        "session_id": session_id,
                        "status": status,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(response))
                
            except WebSocketDisconnect:
                logger.info(f"Enhanced WebSocket disconnected for session {session_id}")
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Enhanced WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
                
    except WebSocketDisconnect:
        logger.info(f"Enhanced WebSocket connection closed for session {session_id}")
    except Exception as e:
        logger.error(f"Enhanced WebSocket error for session {session_id}: {e}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for enhanced collaborative intelligence service"""
    return {
        "status": "healthy",
        "service": "enhanced_collaborative_intelligence",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "ai_facilitation",
            "mom_generation",
            "action_item_tracking",
            "real_time_feedback",
            "participant_analytics",
            "enhanced_nlp",
            "meeting_intelligence",
            "comprehensive_outcomes"
        ]
    }

# Export router for inclusion in main app
__all__ = ["router"]