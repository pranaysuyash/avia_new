"""
Search API Endpoints
REST API for searching transcriptions and entities
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

from api.dependencies import auth_required, create_api_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

class SearchResult(BaseModel):
    id: str
    title: str
    relevance_score: float
    matched_text: str
    created_at: str

@router.get("/transcriptions")
async def search_transcriptions(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = "test_user"
):
    """Search through transcriptions"""
    try:
        # Mock search results
        results = [
            SearchResult(
                id="transcript_001",
                title=f"Search result for '{q}'",
                relevance_score=0.95,
                matched_text=f"...{q} mentioned in context...",
                created_at=datetime.now().isoformat()
            )
        ]
        
        return create_api_response({
            "results": results,
            "total_results": len(results),
            "query": q
        }, "Search completed successfully")
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/entities")
async def search_entities(
    q: str = Query(..., min_length=1),
    entity_type: Optional[str] = Query(default=None),
    user_id: str = "test_user"
):
    """Search for entities"""
    try:
        results = [{
            "entity": q,
            "entity_type": entity_type or "PERSON",
            "transcription_id": "transcript_001",
            "confidence": 0.9
        }]
        
        return create_api_response({
            "entities": results,
            "total_entities": len(results),
            "query": q
        }, "Entity search completed")
        
    except Exception as e:
        logger.error(f"Entity search failed: {e}")
        raise HTTPException(status_code=500, detail="Entity search failed")