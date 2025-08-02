"""
Mock Search API Endpoints
Simplified search endpoint for testing
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import random

router = APIRouter(tags=["Search"])

# Mock transcription data for search results
MOCK_TRANSCRIPTIONS = [
    {
        "transcript_id": "t1",
        "title": "Tech Conference 2024 Keynote",
        "full_text": "Welcome to our annual tech conference. Today we'll be discussing artificial intelligence, machine learning, and the future of technology...",
        "snippet": "Welcome to our annual tech conference. Today we'll be discussing artificial intelligence...",
        "created_at": "2024-01-15T10:30:00",
        "duration": 3600,
        "word_count": 8500,
        "language": "en",
        "entities": [
            {"text": "Tech Conference", "label": "EVENT"},
            {"text": "artificial intelligence", "label": "TECHNOLOGY"},
            {"text": "machine learning", "label": "TECHNOLOGY"}
        ]
    },
    {
        "transcript_id": "t2", 
        "title": "Product Team Meeting Q1",
        "full_text": "Let's review our Q1 product roadmap. We have several key features to deliver including the new dashboard, API improvements, and mobile app updates...",
        "snippet": "Let's review our Q1 product roadmap. We have several key features to deliver...",
        "created_at": "2024-02-01T14:00:00",
        "duration": 2400,
        "word_count": 5200,
        "language": "en",
        "entities": [
            {"text": "Q1", "label": "DATE"},
            {"text": "dashboard", "label": "PRODUCT"},
            {"text": "API", "label": "TECHNOLOGY"},
            {"text": "mobile app", "label": "PRODUCT"}
        ]
    },
    {
        "transcript_id": "t3",
        "title": "Customer Interview - Sarah Johnson",
        "full_text": "Thank you for joining us today Sarah. Can you tell us about your experience with our platform? I've been using it for about 6 months now...",
        "snippet": "Thank you for joining us today Sarah. Can you tell us about your experience...",
        "created_at": "2024-02-10T09:15:00",
        "duration": 1800,
        "word_count": 3200,
        "language": "en",
        "entities": [
            {"text": "Sarah Johnson", "label": "PERSON"},
            {"text": "6 months", "label": "DURATION"}
        ]
    },
    {
        "transcript_id": "t4",
        "title": "Engineering Standup - Sprint 23",
        "full_text": "Good morning team. Let's go through our updates for Sprint 23. John, can you start with the API refactoring progress?...",
        "snippet": "Good morning team. Let's go through our updates for Sprint 23...",
        "created_at": "2024-02-20T10:00:00",
        "duration": 900,
        "word_count": 1500,
        "language": "en",
        "entities": [
            {"text": "Sprint 23", "label": "EVENT"},
            {"text": "John", "label": "PERSON"},
            {"text": "API refactoring", "label": "TASK"}
        ]
    },
    {
        "transcript_id": "t5",
        "title": "Marketing Strategy Session",
        "full_text": "Today we'll discuss our Q2 marketing strategy. We need to focus on content marketing, social media engagement, and SEO improvements...",
        "snippet": "Today we'll discuss our Q2 marketing strategy. We need to focus on content marketing...",
        "created_at": "2024-03-01T15:30:00",
        "duration": 3000,
        "word_count": 6000,
        "language": "en",
        "entities": [
            {"text": "Q2", "label": "DATE"},
            {"text": "content marketing", "label": "STRATEGY"},
            {"text": "social media", "label": "PLATFORM"},
            {"text": "SEO", "label": "TECHNOLOGY"}
        ]
    }
]

@router.get("/search")
async def search_transcriptions(
    q: str = Query(..., description="Search query"),
    dateRange: Optional[str] = Query("all", description="Date range filter"),
    language: Optional[str] = Query("all", description="Language filter"),
    hasEntities: Optional[bool] = Query(False, description="Has entities filter"),
    sortBy: Optional[str] = Query("relevance", description="Sort by field")
):
    """Search through transcriptions"""
    
    # Filter results based on query
    results = []
    query_lower = q.lower()
    
    for transcript in MOCK_TRANSCRIPTIONS:
        # Simple text matching
        if (query_lower in transcript["title"].lower() or 
            query_lower in transcript["full_text"].lower() or
            any(query_lower in entity["text"].lower() for entity in transcript["entities"])):
            
            # Apply filters
            if language != "all" and transcript["language"] != language:
                continue
            
            if hasEntities and len(transcript["entities"]) == 0:
                continue
            
            # Calculate mock relevance score
            title_matches = transcript["title"].lower().count(query_lower)
            text_matches = transcript["full_text"].lower().count(query_lower)
            entity_matches = sum(1 for e in transcript["entities"] if query_lower in e["text"].lower())
            
            score = (title_matches * 3) + text_matches + (entity_matches * 2)
            
            result = {
                **transcript,
                "score": score
            }
            results.append(result)
    
    # Sort results
    if sortBy == "relevance":
        results.sort(key=lambda x: x["score"], reverse=True)
    elif sortBy == "date":
        results.sort(key=lambda x: x["created_at"], reverse=True)
    elif sortBy == "duration":
        results.sort(key=lambda x: x["duration"], reverse=True)
    elif sortBy == "word_count":
        results.sort(key=lambda x: x["word_count"], reverse=True)
    
    return {
        "success": True,
        "data": {
            "results": results,
            "total_count": len(results),
            "query": q,
            "filters": {
                "dateRange": dateRange,
                "language": language,
                "hasEntities": hasEntities,
                "sortBy": sortBy
            }
        }
    }