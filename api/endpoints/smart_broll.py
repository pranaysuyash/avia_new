"""
Smart B-Roll Suggestions API Endpoints
Provides AI-powered suggestions for supplementary video content based on transcript analysis
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body, UploadFile, File
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio
import json
import hashlib
import uuid
from enum import Enum

router = APIRouter(prefix="/api/v1/smart-broll", tags=["Smart B-Roll"])

class ContentType(str, Enum):
    """Types of B-roll content"""
    STOCK_VIDEO = "stock_video"
    STOCK_IMAGE = "stock_image"
    ANIMATION = "animation"
    INFOGRAPHIC = "infographic"
    MAP = "map"
    CHART = "chart"
    SCREENSHOT = "screenshot"
    ARCHIVE_FOOTAGE = "archive_footage"
    NATURE = "nature"
    TECHNOLOGY = "technology"
    PEOPLE = "people"
    ABSTRACT = "abstract"

class SuggestionPriority(str, Enum):
    """Priority levels for B-roll suggestions"""
    CRITICAL = "critical"  # Essential for understanding
    HIGH = "high"          # Strongly recommended
    MEDIUM = "medium"      # Would enhance content
    LOW = "low"           # Optional enhancement

class BRollSuggestion(BaseModel):
    """Individual B-roll suggestion"""
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_start: float = Field(..., description="Start time in seconds")
    timestamp_end: float = Field(..., description="End time in seconds")
    content_type: ContentType
    priority: SuggestionPriority
    keywords: List[str] = Field(..., description="Keywords for searching content")
    description: str = Field(..., description="Description of suggested content")
    rationale: str = Field(..., description="Why this B-roll is suggested")
    search_query: str = Field(..., description="Optimized search query for stock libraries")
    duration: float = Field(..., description="Suggested duration in seconds")
    transition_type: Optional[str] = Field(None, description="Suggested transition effect")
    mood: Optional[str] = Field(None, description="Mood/tone of the content")
    color_scheme: Optional[List[str]] = Field(None, description="Suggested color palette")
    alternatives: Optional[List[str]] = Field(None, description="Alternative content types")
    confidence: float = Field(..., ge=0, le=1, description="AI confidence score")

class AnalysisSettings(BaseModel):
    """Settings for B-roll analysis"""
    enable_context_analysis: bool = Field(default=True)
    enable_emotion_detection: bool = Field(default=True)
    enable_topic_modeling: bool = Field(default=True)
    enable_visual_metaphors: bool = Field(default=True)
    enable_pacing_analysis: bool = Field(default=True)
    min_suggestion_duration: float = Field(default=2.0, description="Minimum B-roll duration in seconds")
    max_suggestion_duration: float = Field(default=10.0, description="Maximum B-roll duration in seconds")
    suggestion_density: str = Field(default="medium", description="low, medium, high")
    target_audience: Optional[str] = Field(None, description="Target audience for content")
    content_style: Optional[str] = Field(None, description="documentary, educational, entertainment, corporate")
    brand_guidelines: Optional[Dict[str, Any]] = Field(None, description="Brand-specific requirements")
    excluded_content_types: Optional[List[ContentType]] = Field(None)
    preferred_sources: Optional[List[str]] = Field(None, description="Preferred stock libraries")
    budget_tier: Optional[str] = Field(None, description="free, budget, premium")

class TranscriptSegment(BaseModel):
    """Segment of transcript for analysis"""
    text: str
    timestamp_start: float
    timestamp_end: float
    speaker: Optional[str] = None
    emotion: Optional[str] = None
    topics: Optional[List[str]] = None

class BRollAnalysisRequest(BaseModel):
    """Request for B-roll analysis"""
    transcript_segments: List[TranscriptSegment]
    video_duration: float
    settings: AnalysisSettings = Field(default_factory=AnalysisSettings)
    metadata: Optional[Dict[str, Any]] = None

class BRollAnalysisResponse(BaseModel):
    """Response with B-roll suggestions"""
    analysis_id: str
    suggestions: List[BRollSuggestion]
    summary: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    estimated_cost: Optional[Dict[str, float]] = None
    processing_time: float
    created_at: datetime

class StockLibrarySearch(BaseModel):
    """Search parameters for stock libraries"""
    query: str
    content_type: ContentType
    duration_range: Optional[Tuple[float, float]] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None
    license_type: Optional[str] = None
    max_results: int = Field(default=10, le=100)

class TemplateLibrary(BaseModel):
    """Template for common B-roll patterns"""
    template_id: str
    name: str
    description: str
    category: str
    patterns: List[Dict[str, Any]]
    applicable_topics: List[str]
    example_videos: Optional[List[str]] = None

# In-memory storage for demo
analysis_cache: Dict[str, BRollAnalysisResponse] = {}
template_library: Dict[str, TemplateLibrary] = {}

@router.get("/health")
async def health_check():
    """Check if Smart B-Roll service is healthy"""
    return {
        "status": "healthy",
        "service": "smart-broll",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": [
            "context_analysis",
            "emotion_detection",
            "topic_modeling",
            "visual_metaphors",
            "pacing_analysis",
            "stock_library_search",
            "template_matching"
        ]
    }

@router.post("/analyze", response_model=BRollAnalysisResponse)
async def analyze_transcript(
    request: BRollAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze transcript and generate B-roll suggestions
    """
    analysis_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    # Simulate AI analysis
    suggestions = []
    
    for segment in request.transcript_segments:
        # Analyze each segment for B-roll opportunities
        if _needs_broll(segment, request.settings):
            suggestion = _generate_suggestion(segment, request.settings)
            suggestions.append(suggestion)
    
    # Sort suggestions by timestamp
    suggestions.sort(key=lambda x: x.timestamp_start)
    
    # Generate timeline
    timeline = _generate_timeline(suggestions, request.video_duration)
    
    # Create summary
    summary = {
        "total_suggestions": len(suggestions),
        "coverage_percentage": _calculate_coverage(suggestions, request.video_duration),
        "priority_breakdown": _get_priority_breakdown(suggestions),
        "content_type_distribution": _get_content_distribution(suggestions),
        "estimated_enhancement_score": _calculate_enhancement_score(suggestions),
        "key_moments": _identify_key_moments(suggestions)
    }
    
    # Estimate costs if budget tier is specified
    estimated_cost = None
    if request.settings.budget_tier:
        estimated_cost = _estimate_costs(suggestions, request.settings.budget_tier)
    
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    
    response = BRollAnalysisResponse(
        analysis_id=analysis_id,
        suggestions=suggestions,
        summary=summary,
        timeline=timeline,
        estimated_cost=estimated_cost,
        processing_time=processing_time,
        created_at=datetime.utcnow()
    )
    
    # Cache the analysis
    analysis_cache[analysis_id] = response
    
    # Trigger async post-processing
    background_tasks.add_task(_enhance_suggestions, analysis_id)
    
    return response

@router.get("/analysis/{analysis_id}", response_model=BRollAnalysisResponse)
async def get_analysis(analysis_id: str):
    """Get previous B-roll analysis by ID"""
    if analysis_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis_cache[analysis_id]

@router.post("/search-stock")
async def search_stock_libraries(search: StockLibrarySearch):
    """
    Search stock libraries for B-roll content
    """
    # Simulate searching multiple stock libraries
    results = {
        "query": search.query,
        "total_results": 42,
        "sources": {
            "pexels": _search_pexels(search),
            "unsplash": _search_unsplash(search),
            "pixabay": _search_pixabay(search),
            "shutterstock": _search_shutterstock(search) if search.license_type != "free" else []
        },
        "filters_applied": {
            "content_type": search.content_type,
            "duration_range": search.duration_range,
            "aspect_ratio": search.aspect_ratio,
            "resolution": search.resolution,
            "license_type": search.license_type
        }
    }
    
    return results

@router.get("/templates")
async def get_templates(
    category: Optional[str] = None,
    topic: Optional[str] = None
):
    """Get B-roll templates"""
    templates = list(template_library.values())
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    if topic:
        templates = [t for t in templates if topic in t.applicable_topics]
    
    return {
        "templates": templates,
        "total": len(templates),
        "categories": list(set(t.category for t in template_library.values()))
    }

@router.post("/apply-template")
async def apply_template(
    template_id: str = Body(...),
    transcript_segments: List[TranscriptSegment] = Body(...),
    video_duration: float = Body(...)
):
    """Apply a B-roll template to transcript"""
    if template_id not in template_library:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = template_library[template_id]
    
    # Apply template patterns to generate suggestions
    suggestions = _apply_template_patterns(template, transcript_segments, video_duration)
    
    return {
        "template_applied": template.name,
        "suggestions": suggestions,
        "total_suggestions": len(suggestions)
    }

@router.post("/optimize-pacing")
async def optimize_pacing(
    suggestions: List[BRollSuggestion] = Body(...),
    target_pace: str = Body("medium", description="slow, medium, fast"),
    video_duration: float = Body(...)
):
    """
    Optimize B-roll pacing for better flow
    """
    optimized = _optimize_pacing(suggestions, target_pace, video_duration)
    
    return {
        "original_count": len(suggestions),
        "optimized_count": len(optimized),
        "pacing_score": _calculate_pacing_score(optimized, video_duration),
        "suggestions": optimized,
        "adjustments_made": _get_pacing_adjustments(suggestions, optimized)
    }

@router.post("/generate-shopping-list")
async def generate_shopping_list(
    suggestions: List[BRollSuggestion] = Body(...),
    budget: Optional[float] = Body(None),
    preferred_sources: Optional[List[str]] = Body(None)
):
    """
    Generate a shopping list for B-roll content
    """
    shopping_list = []
    total_cost = 0.0
    
    for suggestion in suggestions:
        item = {
            "suggestion_id": suggestion.suggestion_id,
            "search_query": suggestion.search_query,
            "content_type": suggestion.content_type,
            "duration": suggestion.duration,
            "priority": suggestion.priority,
            "estimated_cost": _estimate_item_cost(suggestion),
            "recommended_sources": _get_recommended_sources(suggestion, preferred_sources),
            "alternatives": suggestion.alternatives
        }
        shopping_list.append(item)
        total_cost += item["estimated_cost"]
    
    # Apply budget constraints if specified
    if budget and total_cost > budget:
        shopping_list = _prioritize_within_budget(shopping_list, budget)
        total_cost = sum(item["estimated_cost"] for item in shopping_list)
    
    return {
        "shopping_list": shopping_list,
        "total_items": len(shopping_list),
        "estimated_total_cost": total_cost,
        "budget": budget,
        "savings_tips": _get_savings_tips(shopping_list)
    }

@router.post("/validate-suggestions")
async def validate_suggestions(
    suggestions: List[BRollSuggestion] = Body(...),
    video_metadata: Dict[str, Any] = Body(...)
):
    """
    Validate B-roll suggestions against video requirements
    """
    validation_results = []
    
    for suggestion in suggestions:
        result = {
            "suggestion_id": suggestion.suggestion_id,
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "improvements": []
        }
        
        # Check duration constraints
        if suggestion.duration < 1.0:
            result["issues"].append("Duration too short (minimum 1 second)")
            result["is_valid"] = False
        
        # Check overlap with other suggestions
        overlaps = _check_overlaps(suggestion, suggestions)
        if overlaps:
            result["warnings"].append(f"Overlaps with {len(overlaps)} other suggestions")
        
        # Check content appropriateness
        if not _is_content_appropriate(suggestion, video_metadata):
            result["warnings"].append("Content may not match video tone/style")
        
        validation_results.append(result)
    
    return {
        "validation_results": validation_results,
        "valid_count": sum(1 for r in validation_results if r["is_valid"]),
        "total_count": len(validation_results),
        "overall_quality_score": _calculate_quality_score(validation_results)
    }

# Helper functions
def _needs_broll(segment: TranscriptSegment, settings: AnalysisSettings) -> bool:
    """Determine if a segment needs B-roll"""
    # Simplified logic - would use AI in production
    duration = segment.timestamp_end - segment.timestamp_start
    
    # Check if segment is long enough
    if duration < settings.min_suggestion_duration:
        return False
    
    # Check for keywords that suggest visual content
    visual_keywords = ["imagine", "picture", "look", "see", "show", "example", "demonstrate"]
    if any(keyword in segment.text.lower() for keyword in visual_keywords):
        return True
    
    # Check for statistical or factual content
    if any(char.isdigit() for char in segment.text):
        return True
    
    # Random chance based on density setting
    import random
    density_chance = {"low": 0.2, "medium": 0.4, "high": 0.6}
    return random.random() < density_chance.get(settings.suggestion_density, 0.4)

def _generate_suggestion(segment: TranscriptSegment, settings: AnalysisSettings) -> BRollSuggestion:
    """Generate a B-roll suggestion for a segment"""
    import random
    
    # Extract keywords (simplified)
    words = segment.text.split()
    keywords = [w.lower() for w in words if len(w) > 4][:5]
    
    # Determine content type based on context
    content_type = _determine_content_type(segment.text, settings)
    
    # Calculate priority
    priority = _calculate_priority(segment, settings)
    
    # Generate search query
    search_query = " ".join(keywords[:3])
    
    # Calculate duration
    max_duration = min(
        segment.timestamp_end - segment.timestamp_start,
        settings.max_suggestion_duration
    )
    duration = max(settings.min_suggestion_duration, max_duration * 0.7)
    
    return BRollSuggestion(
        timestamp_start=segment.timestamp_start,
        timestamp_end=segment.timestamp_start + duration,
        content_type=content_type,
        priority=priority,
        keywords=keywords,
        description=f"B-roll suggestion for: {segment.text[:100]}...",
        rationale=f"Visual support for {segment.emotion or 'narrative'} content",
        search_query=search_query,
        duration=duration,
        transition_type=random.choice(["fade", "cut", "dissolve"]),
        mood=segment.emotion,
        confidence=random.uniform(0.7, 0.95)
    )

def _determine_content_type(text: str, settings: AnalysisSettings) -> ContentType:
    """Determine appropriate content type based on text"""
    text_lower = text.lower()
    
    if "chart" in text_lower or "graph" in text_lower or "data" in text_lower:
        return ContentType.CHART
    elif "map" in text_lower or "location" in text_lower or "place" in text_lower:
        return ContentType.MAP
    elif "technology" in text_lower or "computer" in text_lower or "software" in text_lower:
        return ContentType.TECHNOLOGY
    elif "nature" in text_lower or "environment" in text_lower:
        return ContentType.NATURE
    elif "people" in text_lower or "team" in text_lower or "person" in text_lower:
        return ContentType.PEOPLE
    else:
        import random
        return random.choice([ContentType.STOCK_VIDEO, ContentType.STOCK_IMAGE, ContentType.ABSTRACT])

def _calculate_priority(segment: TranscriptSegment, settings: AnalysisSettings) -> SuggestionPriority:
    """Calculate suggestion priority"""
    # Simplified priority calculation
    if "important" in segment.text.lower() or "critical" in segment.text.lower():
        return SuggestionPriority.CRITICAL
    elif segment.emotion in ["excitement", "surprise"]:
        return SuggestionPriority.HIGH
    elif len(segment.text) > 200:
        return SuggestionPriority.MEDIUM
    else:
        return SuggestionPriority.LOW

def _generate_timeline(suggestions: List[BRollSuggestion], video_duration: float) -> List[Dict[str, Any]]:
    """Generate visual timeline of suggestions"""
    timeline = []
    
    for suggestion in suggestions:
        timeline.append({
            "start": suggestion.timestamp_start,
            "end": suggestion.timestamp_end,
            "type": suggestion.content_type,
            "priority": suggestion.priority,
            "label": suggestion.keywords[0] if suggestion.keywords else "B-roll"
        })
    
    return timeline

def _calculate_coverage(suggestions: List[BRollSuggestion], video_duration: float) -> float:
    """Calculate percentage of video covered by B-roll"""
    if not suggestions or video_duration == 0:
        return 0.0
    
    total_coverage = sum(s.duration for s in suggestions)
    return min(100.0, (total_coverage / video_duration) * 100)

def _get_priority_breakdown(suggestions: List[BRollSuggestion]) -> Dict[str, int]:
    """Get breakdown of suggestions by priority"""
    breakdown = {p.value: 0 for p in SuggestionPriority}
    for suggestion in suggestions:
        breakdown[suggestion.priority] += 1
    return breakdown

def _get_content_distribution(suggestions: List[BRollSuggestion]) -> Dict[str, int]:
    """Get distribution of content types"""
    distribution = {}
    for suggestion in suggestions:
        content_type = suggestion.content_type
        distribution[content_type] = distribution.get(content_type, 0) + 1
    return distribution

def _calculate_enhancement_score(suggestions: List[BRollSuggestion]) -> float:
    """Calculate overall enhancement score"""
    if not suggestions:
        return 0.0
    
    # Weight by priority and confidence
    priority_weights = {
        SuggestionPriority.CRITICAL: 1.0,
        SuggestionPriority.HIGH: 0.8,
        SuggestionPriority.MEDIUM: 0.5,
        SuggestionPriority.LOW: 0.3
    }
    
    total_score = sum(
        priority_weights.get(s.priority, 0.5) * s.confidence
        for s in suggestions
    )
    
    return min(100.0, (total_score / len(suggestions)) * 100)

def _identify_key_moments(suggestions: List[BRollSuggestion]) -> List[Dict[str, Any]]:
    """Identify key moments that need B-roll"""
    key_moments = []
    
    for suggestion in suggestions:
        if suggestion.priority in [SuggestionPriority.CRITICAL, SuggestionPriority.HIGH]:
            key_moments.append({
                "timestamp": suggestion.timestamp_start,
                "duration": suggestion.duration,
                "type": suggestion.content_type,
                "description": suggestion.description[:100]
            })
    
    return key_moments[:5]  # Return top 5 key moments

def _estimate_costs(suggestions: List[BRollSuggestion], budget_tier: str) -> Dict[str, float]:
    """Estimate costs for B-roll content"""
    tier_costs = {
        "free": 0.0,
        "budget": 5.0,  # Per clip
        "premium": 25.0  # Per clip
    }
    
    cost_per_clip = tier_costs.get(budget_tier, 10.0)
    total_cost = len(suggestions) * cost_per_clip
    
    return {
        "per_clip": cost_per_clip,
        "total": total_cost,
        "currency": "USD"
    }

async def _enhance_suggestions(analysis_id: str):
    """Post-processing to enhance suggestions"""
    # Simulate async enhancement
    await asyncio.sleep(1)
    
    if analysis_id in analysis_cache:
        analysis = analysis_cache[analysis_id]
        # Could add more sophisticated enhancements here
        analysis.summary["enhanced"] = True

def _search_pexels(search: StockLibrarySearch) -> List[Dict[str, Any]]:
    """Mock Pexels search results"""
    return [
        {
            "id": f"pexels_{i}",
            "url": f"https://pexels.com/video/{i}",
            "thumbnail": f"https://pexels.com/thumb/{i}.jpg",
            "duration": 8.5,
            "license": "free"
        }
        for i in range(min(5, search.max_results))
    ]

def _search_unsplash(search: StockLibrarySearch) -> List[Dict[str, Any]]:
    """Mock Unsplash search results"""
    return [
        {
            "id": f"unsplash_{i}",
            "url": f"https://unsplash.com/photo/{i}",
            "thumbnail": f"https://unsplash.com/thumb/{i}.jpg",
            "license": "free"
        }
        for i in range(min(3, search.max_results))
    ]

def _search_pixabay(search: StockLibrarySearch) -> List[Dict[str, Any]]:
    """Mock Pixabay search results"""
    return [
        {
            "id": f"pixabay_{i}",
            "url": f"https://pixabay.com/video/{i}",
            "thumbnail": f"https://pixabay.com/thumb/{i}.jpg",
            "duration": 6.0,
            "license": "free"
        }
        for i in range(min(4, search.max_results))
    ]

def _search_shutterstock(search: StockLibrarySearch) -> List[Dict[str, Any]]:
    """Mock Shutterstock search results"""
    return [
        {
            "id": f"shutterstock_{i}",
            "url": f"https://shutterstock.com/video/{i}",
            "thumbnail": f"https://shutterstock.com/thumb/{i}.jpg",
            "duration": 10.0,
            "license": "premium",
            "price": 79.0
        }
        for i in range(min(10, search.max_results))
    ]

def _apply_template_patterns(
    template: TemplateLibrary,
    segments: List[TranscriptSegment],
    video_duration: float
) -> List[BRollSuggestion]:
    """Apply template patterns to generate suggestions"""
    suggestions = []
    
    for pattern in template.patterns:
        # Simplified pattern matching
        for segment in segments:
            if _matches_pattern(segment, pattern):
                suggestion = _generate_suggestion(segment, AnalysisSettings())
                suggestions.append(suggestion)
    
    return suggestions

def _matches_pattern(segment: TranscriptSegment, pattern: Dict[str, Any]) -> bool:
    """Check if segment matches pattern"""
    # Simplified pattern matching
    return True  # Would implement actual pattern matching

def _optimize_pacing(
    suggestions: List[BRollSuggestion],
    target_pace: str,
    video_duration: float
) -> List[BRollSuggestion]:
    """Optimize B-roll pacing"""
    # Simplified pacing optimization
    pace_intervals = {"slow": 15.0, "medium": 10.0, "fast": 5.0}
    interval = pace_intervals.get(target_pace, 10.0)
    
    optimized = []
    last_time = 0.0
    
    for suggestion in suggestions:
        if suggestion.timestamp_start - last_time >= interval:
            optimized.append(suggestion)
            last_time = suggestion.timestamp_end
    
    return optimized

def _calculate_pacing_score(suggestions: List[BRollSuggestion], video_duration: float) -> float:
    """Calculate pacing score"""
    if not suggestions or video_duration == 0:
        return 0.0
    
    # Calculate average interval between suggestions
    intervals = []
    for i in range(1, len(suggestions)):
        interval = suggestions[i].timestamp_start - suggestions[i-1].timestamp_end
        intervals.append(interval)
    
    if not intervals:
        return 50.0
    
    avg_interval = sum(intervals) / len(intervals)
    ideal_interval = 10.0  # Ideal interval in seconds
    
    # Score based on how close to ideal
    deviation = abs(avg_interval - ideal_interval)
    score = max(0, 100 - (deviation * 5))
    
    return score

def _get_pacing_adjustments(
    original: List[BRollSuggestion],
    optimized: List[BRollSuggestion]
) -> Dict[str, Any]:
    """Get pacing adjustments made"""
    return {
        "removed_count": len(original) - len(optimized),
        "removed_ids": [s.suggestion_id for s in original if s not in optimized],
        "optimization_ratio": len(optimized) / len(original) if original else 0
    }

def _estimate_item_cost(suggestion: BRollSuggestion) -> float:
    """Estimate cost for a single B-roll item"""
    # Simplified cost estimation
    base_costs = {
        ContentType.STOCK_VIDEO: 25.0,
        ContentType.STOCK_IMAGE: 10.0,
        ContentType.ANIMATION: 50.0,
        ContentType.INFOGRAPHIC: 30.0,
    }
    
    base = base_costs.get(suggestion.content_type, 15.0)
    
    # Adjust for priority
    if suggestion.priority == SuggestionPriority.CRITICAL:
        base *= 1.5
    
    return base

def _get_recommended_sources(
    suggestion: BRollSuggestion,
    preferred_sources: Optional[List[str]]
) -> List[str]:
    """Get recommended sources for B-roll content"""
    default_sources = ["pexels", "unsplash", "pixabay"]
    
    if preferred_sources:
        return preferred_sources
    
    if suggestion.content_type == ContentType.STOCK_VIDEO:
        return ["pexels", "pixabay", "shutterstock"]
    elif suggestion.content_type == ContentType.STOCK_IMAGE:
        return ["unsplash", "pexels", "pixabay"]
    else:
        return default_sources

def _prioritize_within_budget(shopping_list: List[Dict], budget: float) -> List[Dict]:
    """Prioritize items within budget constraint"""
    # Sort by priority and cost-effectiveness
    sorted_list = sorted(
        shopping_list,
        key=lambda x: (x["priority"], -x["estimated_cost"])
    )
    
    selected = []
    total = 0.0
    
    for item in sorted_list:
        if total + item["estimated_cost"] <= budget:
            selected.append(item)
            total += item["estimated_cost"]
    
    return selected

def _get_savings_tips(shopping_list: List[Dict]) -> List[str]:
    """Get tips for saving on B-roll costs"""
    tips = [
        "Use free stock libraries like Pexels and Unsplash for non-critical content",
        "Buy subscription packages for frequent use",
        "Create custom animations for recurring themes",
        "Batch purchase similar content types",
        "Consider creating your own B-roll library"
    ]
    
    if len(shopping_list) > 20:
        tips.append("Consider hiring a videographer for custom B-roll")
    
    return tips

def _check_overlaps(
    suggestion: BRollSuggestion,
    all_suggestions: List[BRollSuggestion]
) -> List[str]:
    """Check for overlapping suggestions"""
    overlaps = []
    
    for other in all_suggestions:
        if other.suggestion_id == suggestion.suggestion_id:
            continue
        
        # Check for time overlap
        if (suggestion.timestamp_start < other.timestamp_end and 
            suggestion.timestamp_end > other.timestamp_start):
            overlaps.append(other.suggestion_id)
    
    return overlaps

def _is_content_appropriate(
    suggestion: BRollSuggestion,
    video_metadata: Dict[str, Any]
) -> bool:
    """Check if content is appropriate for video"""
    # Simplified appropriateness check
    return True

def _calculate_quality_score(validation_results: List[Dict]) -> float:
    """Calculate overall quality score"""
    if not validation_results:
        return 0.0
    
    valid_count = sum(1 for r in validation_results if r["is_valid"])
    warning_count = sum(len(r["warnings"]) for r in validation_results)
    
    base_score = (valid_count / len(validation_results)) * 100
    warning_penalty = min(30, warning_count * 2)
    
    return max(0, base_score - warning_penalty)

# Initialize some default templates
template_library["documentary_standard"] = TemplateLibrary(
    template_id="documentary_standard",
    name="Documentary Standard",
    description="Standard B-roll pattern for documentary-style videos",
    category="documentary",
    patterns=[
        {"type": "establishing_shot", "duration": 5.0},
        {"type": "detail_shots", "duration": 3.0},
        {"type": "transition", "duration": 2.0}
    ],
    applicable_topics=["history", "science", "nature", "culture"]
)

template_library["educational_engaging"] = TemplateLibrary(
    template_id="educational_engaging",
    name="Educational Engaging",
    description="Engaging B-roll for educational content",
    category="educational",
    patterns=[
        {"type": "concept_visualization", "duration": 4.0},
        {"type": "example", "duration": 3.0},
        {"type": "infographic", "duration": 5.0}
    ],
    applicable_topics=["education", "tutorial", "explainer", "howto"]
)