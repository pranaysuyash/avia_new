"""
Comprehensive Search API Endpoints
Provides REST API for advanced search functionality across all data types
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from api.database import get_db, User
from api.auth import get_current_active_user
from services.comprehensive_search_service import (
    search_service,
    SearchQuery,
    SearchFilter,
    SearchType,
    SearchScope,
    SortOrder,
    SearchResponse,
    SearchResult
)
from services.audit_logging_service import audit_service, AuditEventType

router = APIRouter(
    prefix="/api/v1/search",
    tags=["comprehensive-search"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for request/response
class SearchFilterRequest(BaseModel):
    """Search filter request model"""
    field: str = Field(..., description="Field to filter on")
    operator: str = Field(..., pattern="^(eq|ne|gt|lt|gte|lte|contains|in|not_in)$", description="Filter operator")
    value: Any = Field(..., description="Filter value")
    case_sensitive: bool = Field(default=False, description="Case sensitive filtering")


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_type: SearchType = Field(default=SearchType.FULL_TEXT, description="Type of search")
    scope: SearchScope = Field(default=SearchScope.ALL, description="Search scope")
    filters: List[SearchFilterRequest] = Field(default=[], description="Search filters")
    sort_order: SortOrder = Field(default=SortOrder.RELEVANCE, description="Sort order")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results per page")
    offset: int = Field(default=0, ge=0, description="Results offset for pagination")
    highlight: bool = Field(default=True, description="Highlight search matches")
    facets: List[str] = Field(default=[], description="Facet fields")


class SearchResultResponse(BaseModel):
    """Single search result response model"""
    id: str
    type: str
    title: str
    content: str
    highlighted_content: str
    metadata: Dict[str, Any]
    score: float
    created_at: str
    updated_at: str


class SearchResponseModel(BaseModel):
    """Complete search response model"""
    results: List[SearchResultResponse]
    total_count: int
    query: str
    search_time_ms: float
    facets: Dict[str, Dict[str, int]]
    suggestions: List[str]
    filters_applied: List[SearchFilterRequest]
    page: int
    per_page: int
    has_more: bool


class SearchAnalyticsResponse(BaseModel):
    """Search analytics response model"""
    total_searches: int
    unique_queries: int
    avg_search_time_ms: float
    avg_results_count: float
    popular_queries: List[Dict[str, Any]]
    search_types: Dict[str, int]
    search_scopes: Dict[str, int]
    daily_stats: Dict[str, Dict[str, float]]


class SearchSuggestionResponse(BaseModel):
    """Search suggestions response model"""
    suggestions: List[str]
    prefix: str


class SearchClickRequest(BaseModel):
    """Search click tracking request"""
    query: str = Field(..., description="Original search query")
    result_id: str = Field(..., description="ID of clicked result")


# Search endpoints
@router.post("/", response_model=SearchResponseModel)
async def search(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform comprehensive search across data types
    
    Supports full-text search, semantic search, fuzzy search, and more
    across transcripts, users (admin only), and other content.
    """
    try:
        # Convert request to service objects
        search_filters = [
            SearchFilter(
                field=f.field,
                operator=f.operator,
                value=f.value,
                case_sensitive=f.case_sensitive
            ) for f in search_request.filters
        ]
        
        search_query = SearchQuery(
            query=search_request.query,
            search_type=search_request.search_type,
            scope=search_request.scope,
            filters=search_filters,
            sort_order=search_request.sort_order,
            limit=search_request.limit,
            offset=search_request.offset,
            highlight=search_request.highlight,
            facets=search_request.facets,
            user_id=current_user.id
        )
        
        # Perform search
        response = await search_service.search(search_query, current_user.id)
        
        # Convert response
        result_responses = []
        for result in response.results:
            result_response = SearchResultResponse(
                id=result.id,
                type=result.type,
                title=result.title,
                content=result.content,
                highlighted_content=result.highlighted_content,
                metadata=result.metadata,
                score=result.score,
                created_at=result.created_at.isoformat(),
                updated_at=result.updated_at.isoformat()
            )
            result_responses.append(result_response)
        
        filter_responses = [
            SearchFilterRequest(
                field=f.field,
                operator=f.operator,
                value=f.value,
                case_sensitive=f.case_sensitive
            ) for f in response.filters_applied
        ]
        
        return SearchResponseModel(
            results=result_responses,
            total_count=response.total_count,
            query=response.query,
            search_time_ms=response.search_time_ms,
            facets=response.facets,
            suggestions=response.suggestions,
            filters_applied=filter_responses,
            page=response.page,
            per_page=response.per_page,
            has_more=response.has_more
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/suggestions", response_model=SearchSuggestionResponse)
async def get_search_suggestions(
    prefix: str = Query(..., min_length=2, max_length=50, description="Search prefix"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum suggestions"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get search suggestions for autocomplete
    
    Returns popular and matching queries based on the provided prefix.
    """
    try:
        suggestions = await search_service.get_search_suggestions(prefix, limit)
        
        return SearchSuggestionResponse(
            suggestions=suggestions,
            prefix=prefix
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/click")
async def track_search_click(
    click_request: SearchClickRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Track search result clicks for analytics
    
    Records when users click on search results to improve relevance.
    """
    try:
        await search_service.record_search_click(
            current_user.id,
            click_request.query,
            click_request.result_id
        )
        
        # Log the click event
        audit_service.log_event(
            event_type=AuditEventType.SEARCH_RESULT_CLICK,
            action=f"Search result clicked: {click_request.result_id}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "query": click_request.query,
                "result_id": click_request.result_id
            }
        )
        
        return {"status": "success", "message": "Click tracked"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track click: {str(e)}"
        )


@router.get("/analytics", response_model=SearchAnalyticsResponse)
async def get_search_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Days to analyze"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get search analytics for the current user
    
    Returns search patterns, popular queries, and performance metrics.
    """
    try:
        analytics = await search_service.get_search_analytics(
            user_id=current_user.id,
            days=days
        )
        
        return SearchAnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/analytics/admin", response_model=SearchAnalyticsResponse)
async def get_admin_search_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Days to analyze"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get search analytics for all users (admin only)
    
    Returns system-wide search patterns and performance metrics.
    """
    # Check admin privileges (simplified check)
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    try:
        analytics = await search_service.get_search_analytics(
            user_id=None,  # All users
            days=days
        )
        
        # Log admin analytics access
        audit_service.log_event(
            event_type=AuditEventType.ADMIN_ACTION,
            action="Admin accessed search analytics",
            user_id=current_user.id,
            username=current_user.username,
            details={"days": days}
        )
        
        return SearchAnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin analytics: {str(e)}"
        )


# Advanced search endpoints
@router.post("/transcripts", response_model=SearchResponseModel)
async def search_transcripts(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search transcripts only
    
    Specialized endpoint for transcript-only search with transcription-specific
    filters and sorting options.
    """
    try:
        # Override scope to transcripts only
        search_request.scope = SearchScope.TRANSCRIPTS
        
        # Convert and perform search
        search_filters = [
            SearchFilter(
                field=f.field,
                operator=f.operator,
                value=f.value,
                case_sensitive=f.case_sensitive
            ) for f in search_request.filters
        ]
        
        search_query = SearchQuery(
            query=search_request.query,
            search_type=search_request.search_type,
            scope=search_request.scope,
            filters=search_filters,
            sort_order=search_request.sort_order,
            limit=search_request.limit,
            offset=search_request.offset,
            highlight=search_request.highlight,
            facets=search_request.facets or ["language", "duration", "created_month"],
            user_id=current_user.id
        )
        
        response = await search_service.search(search_query, current_user.id)
        
        # Convert response
        result_responses = []
        for result in response.results:
            result_response = SearchResultResponse(
                id=result.id,
                type=result.type,
                title=result.title,
                content=result.content,
                highlighted_content=result.highlighted_content,
                metadata=result.metadata,
                score=result.score,
                created_at=result.created_at.isoformat(),
                updated_at=result.updated_at.isoformat()
            )
            result_responses.append(result_response)
        
        filter_responses = [
            SearchFilterRequest(
                field=f.field,
                operator=f.operator,
                value=f.value,
                case_sensitive=f.case_sensitive
            ) for f in response.filters_applied
        ]
        
        return SearchResponseModel(
            results=result_responses,
            total_count=response.total_count,
            query=response.query,
            search_time_ms=response.search_time_ms,
            facets=response.facets,
            suggestions=response.suggestions,
            filters_applied=filter_responses,
            page=response.page,
            per_page=response.per_page,
            has_more=response.has_more
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcript search failed: {str(e)}"
        )


@router.get("/similar/{result_id}")
async def find_similar_content(
    result_id: str,
    limit: int = Query(default=5, ge=1, le=20, description="Maximum similar results"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find similar content to a specific result
    
    Uses content similarity to find related transcripts or content.
    """
    try:
        # This is a simplified implementation
        # In production, you'd use vector embeddings for semantic similarity
        
        # For now, we'll find content with similar keywords
        # First, get the original content
        db = next(get_db())
        
        try:
            # Assume result_id is a transcript ID
            from api.database import Transcript
            original = db.query(Transcript).filter(Transcript.id == int(result_id)).first()
            
            if not original:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Original content not found"
                )
            
            # Check access permissions
            if original.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this content"
                )
            
            # Extract keywords from original content
            if original.content:
                # Simple keyword extraction (in production, use NLP)
                import re
                words = re.findall(r'\b\w+\b', original.content.lower())
                common_words = {'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'are', 'as', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall', 'of', 'in', 'for', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among'}
                keywords = [w for w in words if len(w) > 3 and w not in common_words]
                
                # Get most frequent keywords
                from collections import Counter
                keyword_counts = Counter(keywords)
                top_keywords = [k for k, _ in keyword_counts.most_common(10)]
                
                if top_keywords:
                    # Search using these keywords
                    search_query = SearchQuery(
                        query=" ".join(top_keywords[:5]),  # Use top 5 keywords
                        search_type=SearchType.FULL_TEXT,
                        scope=SearchScope.TRANSCRIPTS,
                        filters=[],
                        sort_order=SortOrder.RELEVANCE,
                        limit=limit + 1,  # +1 to account for original
                        offset=0,
                        highlight=False,
                        facets=[],
                        user_id=current_user.id
                    )
                    
                    response = await search_service.search(search_query, current_user.id)
                    
                    # Filter out the original result
                    similar_results = [
                        r for r in response.results 
                        if r.id != result_id
                    ][:limit]
                    
                    return {
                        "original_id": result_id,
                        "similar_results": [
                            {
                                "id": r.id,
                                "type": r.type,
                                "title": r.title,
                                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                                "metadata": r.metadata,
                                "similarity_score": r.score,
                                "created_at": r.created_at.isoformat(),
                            } for r in similar_results
                        ],
                        "total_similar": len(similar_results)
                    }
                else:
                    return {
                        "original_id": result_id,
                        "similar_results": [],
                        "total_similar": 0,
                        "message": "No keywords found for similarity matching"
                    }
            else:
                return {
                    "original_id": result_id,
                    "similar_results": [],
                    "total_similar": 0,
                    "message": "Original content is empty"
                }
            
        finally:
            db.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar content: {str(e)}"
        )


@router.get("/export")
async def export_search_results(
    query: str = Query(..., description="Search query to export"),
    format_type: str = Query(default="json", pattern="^(json|csv)$", description="Export format"),
    max_results: int = Query(default=1000, ge=1, le=10000, description="Maximum results to export"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export search results
    
    Allows users to export large search result sets in JSON or CSV format.
    """
    try:
        # Perform comprehensive search
        search_query = SearchQuery(
            query=query,
            search_type=SearchType.FULL_TEXT,
            scope=SearchScope.ALL,
            filters=[],
            sort_order=SortOrder.RELEVANCE,
            limit=max_results,
            offset=0,
            highlight=False,
            facets=[],
            user_id=current_user.id
        )
        
        response = await search_service.search(search_query, current_user.id)
        
        # Log export action
        audit_service.log_event(
            event_type=AuditEventType.DATA_EXPORT_REQUEST,
            action=f"Search results exported: {query}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "query": query,
                "format": format_type,
                "results_count": len(response.results)
            }
        )
        
        if format_type == "csv":
            # Return CSV data
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "ID", "Type", "Title", "Content", "Score", 
                "Created At", "Updated At", "Metadata"
            ])
            
            # Write data
            for result in response.results:
                writer.writerow([
                    result.id,
                    result.type,
                    result.title,
                    result.content[:500] + "..." if len(result.content) > 500 else result.content,
                    result.score,
                    result.created_at.isoformat(),
                    result.updated_at.isoformat(),
                    str(result.metadata)
                ])
            
            csv_data = output.getvalue()
            output.close()
            
            return {
                "format": "csv",
                "data": csv_data,
                "query": query,
                "total_results": len(response.results),
                "exported_at": datetime.utcnow().isoformat()
            }
        
        else:  # JSON format
            export_data = {
                "query": query,
                "total_results": response.total_count,
                "exported_results": len(response.results),
                "exported_at": datetime.utcnow().isoformat(),
                "search_time_ms": response.search_time_ms,
                "results": [
                    {
                        "id": r.id,
                        "type": r.type,
                        "title": r.title,
                        "content": r.content,
                        "metadata": r.metadata,
                        "score": r.score,
                        "created_at": r.created_at.isoformat(),
                        "updated_at": r.updated_at.isoformat()
                    } for r in response.results
                ]
            }
            
            return export_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


# Health check
@router.get("/health")
async def search_health_check():
    """
    Search service health check
    """
    try:
        # Test basic search functionality
        test_query = SearchQuery(
            query="test",
            limit=1,
            offset=0
        )
        
        # This should complete without error (even if no results)
        test_response = await search_service.search(test_query)
        
        return {
            "status": "healthy",
            "search_service": "operational",
            "test_query_time_ms": test_response.search_time_ms,
            "cache_connected": search_service.cache_ttl > 0,
            "analytics_count": len(search_service.search_analytics)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }