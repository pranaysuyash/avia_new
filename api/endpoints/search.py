"""
Search API Endpoints
REST API for advanced search and similarity functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Dict, Any
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import auth_required, read_required, create_api_response
from api.models import SearchRequest, SearchResponse, SearchResult

# Import search modules
from search.search_manager import SearchManager, SearchQuery
from search.query_parser import QueryParser
from session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

# Initialize components
search_manager = None  # Will be initialized on first use
session_manager = SessionManager()


def get_search_manager():
    """Get or create search manager instance"""
    global search_manager
    if search_manager is None:
        try:
            search_manager = SearchManager()
        except Exception as e:
            logger.error(f"Failed to initialize search manager: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service unavailable"
            )
    return search_manager


@router.post("/query", response_model=SearchResponse)
async def search_transcripts(
    request: SearchRequest,
    user_id: str = Depends(read_required)
):
    """Search through transcripts with advanced filtering"""
    try:
        manager = get_search_manager()
        
        # Create search query
        search_query = SearchQuery(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            filters=request.filters or {},
            sort_by=request.sort_by,
            user_id=user_id
        )
        
        # Execute search
        search_results = await manager.search(search_query)
        
        # Convert results to API format
        results = []
        for result in search_results.results:
            results.append(SearchResult(
                transcript_id=result.get('transcript_id', ''),
                title=result.get('title'),
                snippet=result.get('snippet', '')[:200] if request.include_snippets else '',
                score=result.get('score', 0.0),
                created_at=datetime.fromisoformat(result.get('created_at', datetime.now().isoformat())),
                duration=result.get('duration'),
                word_count=result.get('word_count')
            ))
        
        response_data = {
            "results": [result.dict() for result in results],
            "facets": search_results.facets,
            "aggregations": search_results.aggregations,
            "query_info": {
                "original_query": request.query,
                "processed_query": search_results.processed_query,
                "search_time_ms": search_results.search_time_ms
            }
        }
        
        return {
            "success": True,
            "message": f"Found {search_results.total_count} results",
            "data": response_data,
            "total_count": search_results.total_count,
            "page": (request.offset // request.limit) + 1,
            "per_page": request.limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(default=5, ge=1, le=20),
    user_id: str = Depends(read_required)
):
    """Get search suggestions based on partial query"""
    try:
        manager = get_search_manager()
        
        # Get suggestions (this would typically use autocomplete index)
        suggestions = await manager.get_suggestions(query, limit)
        
        return create_api_response({
            "query": query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }, "Search suggestions retrieved")
        
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search suggestions"
        )


@router.get("/similar/{transcript_id}")
async def find_similar_transcripts(
    transcript_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    user_id: str = Depends(read_required)
):
    """Find transcripts similar to the given transcript"""
    try:
        manager = get_search_manager()
        
        # Find similar transcripts
        similar_results = await manager.find_similar(transcript_id, limit, user_id)
        
        results = []
        for result in similar_results:
            results.append({
                "transcript_id": result.get('transcript_id', ''),
                "title": result.get('title'),
                "similarity_score": result.get('similarity_score', 0.0),
                "snippet": result.get('snippet', ''),
                "created_at": result.get('created_at'),
                "duration": result.get('duration'),
                "word_count": result.get('word_count')
            })
        
        return create_api_response({
            "source_transcript_id": transcript_id,
            "similar_transcripts": results,
            "count": len(results)
        }, f"Found {len(results)} similar transcripts")
        
    except Exception as e:
        logger.error(f"Similar search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar transcripts"
        )


@router.get("/facets")
async def get_search_facets(
    user_id: str = Depends(read_required)
):
    """Get available search facets and filters"""
    try:
        manager = get_search_manager()
        
        # Get facet information
        facets = await manager.get_facets(user_id)
        
        return create_api_response({
            "facets": facets,
            "available_filters": [
                {
                    "name": "language",
                    "type": "categorical",
                    "description": "Filter by transcript language"
                },
                {
                    "name": "duration",
                    "type": "range",
                    "description": "Filter by audio duration (seconds)"
                },
                {
                    "name": "word_count",
                    "type": "range", 
                    "description": "Filter by word count"
                },
                {
                    "name": "created_date",
                    "type": "date_range",
                    "description": "Filter by creation date"
                },
                {
                    "name": "has_speakers",
                    "type": "boolean",
                    "description": "Filter by speaker diarization availability"
                },
                {
                    "name": "has_entities",
                    "type": "boolean",
                    "description": "Filter by entity extraction availability"
                }
            ]
        }, "Search facets retrieved")
        
    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search facets"
        )


@router.get("/trending")
async def get_trending_queries(
    period: str = Query(default="7d", regex="^(1d|7d|30d)$"),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = Depends(read_required)
):
    """Get trending search queries"""
    try:
        manager = get_search_manager()
        
        # Get trending queries (this would typically use analytics data)
        trending = await manager.get_trending_queries(period, limit)
        
        return create_api_response({
            "period": period,
            "trending_queries": trending,
            "count": len(trending)
        }, f"Retrieved {len(trending)} trending queries")
        
    except Exception as e:
        logger.error(f"Trending queries error: {e}")
        # Return empty trending data if analytics not available
        return create_api_response({
            "period": period,
            "trending_queries": [],
            "count": 0
        }, "No trending data available")


@router.post("/index/rebuild")
async def rebuild_search_index(
    user_id: str = Depends(auth_required)  # Admin only in production
):
    """Rebuild the search index"""
    try:
        manager = get_search_manager()
        
        # Start index rebuild (this would be async in production)
        rebuild_stats = await manager.rebuild_index(user_id)
        
        return create_api_response({
            "rebuild_started": True,
            "estimated_time_minutes": rebuild_stats.get('estimated_time', 5),
            "documents_to_index": rebuild_stats.get('document_count', 0)
        }, "Search index rebuild started")
        
    except Exception as e:
        logger.error(f"Index rebuild error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start index rebuild"
        )


@router.get("/index/status")
async def get_index_status(
    user_id: str = Depends(read_required)
):
    """Get search index status and statistics"""
    try:
        manager = get_search_manager()
        
        # Get index statistics
        index_stats = await manager.get_index_stats()
        
        return create_api_response({
            "index_size": index_stats.get('size_mb', 0),
            "document_count": index_stats.get('document_count', 0),
            "last_updated": index_stats.get('last_updated'),
            "index_version": index_stats.get('version', '1.0'),
            "available_fields": [
                "text", "title", "language", "duration", 
                "word_count", "entities", "speakers", "created_at"
            ]
        }, "Index status retrieved")
        
    except Exception as e:
        logger.error(f"Index status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get index status"
        )


@router.get("/history")
async def get_search_history(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(read_required)
):
    """Get user's search history"""
    try:
        # This would typically come from database
        # For now, return from session data
        session_data = session_manager.get_session_data(user_id) or {}
        search_history = session_data.get('search_history', [])
        
        # Apply limit
        recent_searches = search_history[-limit:] if search_history else []
        
        return create_api_response({
            "searches": recent_searches,
            "count": len(recent_searches),
            "total_searches": len(search_history)
        }, "Search history retrieved")
        
    except Exception as e:
        logger.error(f"Search history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search history"
        )


@router.delete("/history")
async def clear_search_history(
    user_id: str = Depends(auth_required)
):
    """Clear user's search history"""
    try:
        # Clear search history from session
        session_data = session_manager.get_session_data(user_id) or {}
        session_data['search_history'] = []
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(
            {"cleared": True}, 
            "Search history cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear search history"
        )


@router.post("/save")
async def save_search(
    query: str,
    name: str,
    user_id: str = Depends(auth_required)
):
    """Save a search query for later use"""
    try:
        # Save search to session (would be database in production)
        session_data = session_manager.get_session_data(user_id) or {}
        saved_searches = session_data.get('saved_searches', [])
        
        # Add new saved search
        saved_search = {
            "id": f"saved_{len(saved_searches) + 1}",
            "name": name,
            "query": query,
            "created_at": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        saved_searches.append(saved_search)
        session_data['saved_searches'] = saved_searches
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(saved_search, "Search saved successfully")
        
    except Exception as e:
        logger.error(f"Save search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save search"
        )


@router.get("/saved")
async def get_saved_searches(
    user_id: str = Depends(read_required)
):
    """Get user's saved searches"""
    try:
        session_data = session_manager.get_session_data(user_id) or {}
        saved_searches = session_data.get('saved_searches', [])
        
        return create_api_response({
            "saved_searches": saved_searches,
            "count": len(saved_searches)
        }, "Saved searches retrieved")
        
    except Exception as e:
        logger.error(f"Get saved searches error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get saved searches"
        )