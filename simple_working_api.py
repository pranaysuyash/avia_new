#!/usr/bin/env python3
"""
Simple working API server for testing the React frontend
This bypasses all the complex imports and focuses on getting the APIs working
"""

from fastapi import FastAPI, HTTPException, Path, Query, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
import random
from datetime import datetime, timedelta

app = FastAPI(title="NER Transcription API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple response helper
def create_response(data, message="Success"):
    return {"data": data, "message": message, "success": True}

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "service": "api"}

# Analytics endpoints
@app.get("/api/analytics/usage/weekly")
async def get_weekly_usage():
    data = []
    for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
        data.append({
            "day": day,
            "hours": round(random.uniform(1.0, 8.5), 1),
            "transcriptions": random.randint(2, 15),
            "entities": random.randint(10, 80)
        })
    
    total_hours = sum(item["hours"] for item in data)
    stats = {
        "total_hours": total_hours,
        "total_transcriptions": sum(item["transcriptions"] for item in data),
        "total_entities": sum(item["entities"] for item in data),
        "avg_accuracy": 94.5,
        "period": "week"
    }
    
    return {"data": data, "stats": stats}

# History endpoints
@app.get("/api/history/transcriptions")
async def get_transcription_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100)
):
    # Generate mock history
    items = []
    for i in range(1, 21):
        items.append({
            "id": f"transcript_{i:03d}",
            "title": f"Transcription {i}",
            "filename": f"audio_{i}.wav",
            "duration": round(random.uniform(30, 3600), 1),
            "status": random.choice(["completed", "processing", "failed"]),
            "accuracy": round(random.uniform(0.85, 0.99), 2),
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "language": random.choice(["en", "es", "fr"]),
            "entities_count": random.randint(5, 50)
        })
    
    stats = {
        "total_items": len(items),
        "completed": len([i for i in items if i["status"] == "completed"]),
        "processing": len([i for i in items if i["status"] == "processing"]),
        "failed": len([i for i in items if i["status"] == "failed"])
    }
    
    return {"items": items, "stats": stats, "total_pages": 1, "current_page": 1}

@app.delete("/api/history/transcriptions/{transcription_id}")
async def delete_transcription(transcription_id: str):
    return create_response(
        {"transcription_id": transcription_id, "deleted_at": datetime.now().isoformat()},
        "Transcription deleted successfully"
    )

# Queue endpoints
@app.get("/api/queue/status")
async def get_queue_status():
    items = []
    for i in range(1, 6):
        items.append({
            "id": f"queue_{i:03d}",
            "filename": f"audio_{i}.wav",
            "file_size": random.randint(1000000, 50000000),
            "status": random.choice(["pending", "processing", "completed", "failed"]),
            "progress": random.uniform(0, 100),
            "created_at": datetime.now().isoformat()
        })
    
    stats = {
        "total_items": len(items),
        "pending": len([i for i in items if i["status"] == "pending"]),
        "processing": len([i for i in items if i["status"] == "processing"]),
        "completed": len([i for i in items if i["status"] == "completed"]),
        "failed": len([i for i in items if i["status"] == "failed"]),
        "cancelled": 0,
        "estimated_queue_time": 300
    }
    
    return {"items": items, "stats": stats}

@app.post("/api/queue/{queue_id}/cancel")
async def cancel_queue_item(queue_id: str):
    return create_response(
        {"queue_id": queue_id, "status": "cancelled", "cancelled_at": datetime.now().isoformat()},
        "Queue item cancelled successfully"
    )

# Settings endpoints
@app.get("/api/settings/user")
async def get_user_preferences():
    return {
        "language": "en",
        "theme": "light",
        "timezone": "UTC",
        "notifications_enabled": True,
        "auto_save": True,
        "max_file_size_mb": 100,
        "retention_days": 30
    }

@app.put("/api/settings/user")
async def update_user_preferences(settings: dict):
    return create_response(settings, "User preferences updated successfully")

@app.get("/api/settings/transcription")
async def get_transcription_settings():
    return {
        "default_language": "auto",
        "detect_code_switching": False,
        "confidence_threshold": 0.8,
        "speaker_diarization": False,
        "noise_reduction": True,
        "auto_punctuation": True,
        "profanity_filter": False,
        "model_preference": "balanced"
    }

@app.put("/api/settings/transcription")
async def update_transcription_settings(settings: dict):
    return create_response(settings, "Transcription settings updated successfully")

@app.get("/api/settings/languages")
async def get_supported_languages():
    languages = [
        {"code": "auto", "name": "Auto-detect", "has_ner": True, "is_rtl": False},
        {"code": "en", "name": "English", "has_ner": True, "is_rtl": False},
        {"code": "es", "name": "Spanish", "has_ner": True, "is_rtl": False},
        {"code": "fr", "name": "French", "has_ner": True, "is_rtl": False},
        {"code": "de", "name": "German", "has_ner": True, "is_rtl": False}
    ]
    return create_response(languages, "Supported languages retrieved successfully")

@app.get("/api/settings/models")
async def get_available_models():
    models = [
        {
            "id": "whisper-tiny",
            "name": "Whisper Tiny",
            "description": "Fastest processing, lower accuracy",
            "size": "39 MB",
            "languages": 99,
            "speed": "~32x realtime",
            "accuracy": "Good"
        },
        {
            "id": "whisper-base",
            "name": "Whisper Base",
            "description": "Balanced speed and accuracy",
            "size": "74 MB",
            "languages": 99,
            "speed": "~16x realtime",
            "accuracy": "Better"
        },
        {
            "id": "whisper-small",
            "name": "Whisper Small",
            "description": "Good accuracy, moderate speed",
            "size": "244 MB",
            "languages": 99,
            "speed": "~6x realtime",
            "accuracy": "Good"
        },
        {
            "id": "whisper-medium",
            "name": "Whisper Medium",
            "description": "High accuracy, slower processing",
            "size": "769 MB",
            "languages": 99,
            "speed": "~2x realtime",
            "accuracy": "Very Good"
        },
        {
            "id": "whisper-large-v2",
            "name": "Whisper Large v2",
            "description": "Highest accuracy, slowest processing",
            "size": "1550 MB",
            "languages": 99,
            "speed": "~1x realtime",
            "accuracy": "Excellent"
        }
    ]
    return create_response(models, "Available models retrieved successfully")

# Export endpoints
@app.post("/api/export/transcription/{transcription_id}")
async def export_transcription(transcription_id: str, export_request: dict):
    if export_request.get("format") == "json":
        content = json.dumps({
            "id": transcription_id,
            "title": f"Transcription {transcription_id}",
            "text": "Sample transcription content",
            "entities": {"PERSON": ["John Smith"], "ORG": ["Company"]}
        }, indent=2)
        return Response(content=content, media_type="application/json")
    else:
        return HTTPException(status_code=400, detail="Unsupported format")

# Search endpoints
@app.get("/api/search/transcriptions")
async def search_transcriptions(q: str):
    results = [
        {
            "id": "transcript_001",
            "title": f"Search result for '{q}'",
            "relevance_score": 0.95,
            "matched_text": f"...{q} mentioned in context...",
            "created_at": datetime.now().isoformat()
        }
    ]
    return create_response({
        "results": results,
        "total_results": len(results),
        "query": q
    }, "Search completed successfully")

# Files endpoints
@app.get("/api/files/recent")
async def get_recent_files():
    files = [
        {
            "id": f"file_{i:03d}",
            "filename": f"audio_{i}.wav",
            "size": 1024000 * (i + 1),
            "content_type": "audio/wav",
            "uploaded_at": (datetime.now() - timedelta(hours=i)).isoformat(),
            "status": "completed"
        }
        for i in range(1, 6)
    ]
    return create_response({"files": files, "total_files": len(files)}, "Recent files retrieved")

# Visual Search endpoints
@app.get("/api/visual-search/timeline")
async def get_content_timeline():
    """Get visual timeline with content density mapping"""
    timeline_data = []
    
    # Generate mock timeline data showing content density over time
    for hour in range(24):
        density = random.randint(0, 100)
        topics = random.sample(['Technology', 'Science', 'Business', 'Education', 'Health'], 
                             random.randint(1, 3))
        
        timeline_data.append({
            "hour": hour,
            "content_density": density,
            "transcription_count": random.randint(0, 15),
            "dominant_topics": topics,
            "avg_confidence": round(random.uniform(0.8, 0.99), 2),
            "languages": random.sample(['en', 'es', 'fr'], random.randint(1, 2))
        })
    
    stats = {
        "total_hours": 24,
        "peak_hour": max(timeline_data, key=lambda x: x["content_density"])["hour"],
        "avg_density": round(sum(item["content_density"] for item in timeline_data) / 24, 1),
        "total_transcriptions": sum(item["transcription_count"] for item in timeline_data)
    }
    
    return create_response({
        "timeline": timeline_data,
        "stats": stats
    }, "Content timeline retrieved successfully")

@app.get("/api/visual-search/content-map")
async def get_content_map():
    """Get interactive content map with clustering"""
    clusters = []
    
    # Generate topic-based clusters
    topics = ['Technology', 'Science', 'Business', 'Education', 'Health', 'Entertainment']
    
    for i, topic in enumerate(topics):
        cluster = {
            "id": f"cluster_{i}",
            "topic": topic,
            "center_x": random.uniform(10, 90),
            "center_y": random.uniform(10, 90),
            "size": random.randint(20, 80),
            "transcription_count": random.randint(5, 50),
            "avg_similarity": round(random.uniform(0.7, 0.95), 2),
            "keywords": random.sample([
                'machine learning', 'artificial intelligence', 'data science', 
                'research', 'innovation', 'development', 'analysis', 'optimization'
            ], random.randint(3, 5)),
            "color": f"hsl({i * 60}, 70%, 60%)",
            "transcriptions": [
                {
                    "id": f"transcript_{j:03d}",
                    "title": f"{topic} Discussion {j}",
                    "x": random.uniform(-10, 10),
                    "y": random.uniform(-10, 10),
                    "similarity": round(random.uniform(0.6, 0.99), 2)
                }
                for j in range(1, random.randint(3, 8))
            ]
        }
        clusters.append(cluster)
    
    return create_response({
        "clusters": clusters,
        "total_clusters": len(clusters),
        "total_transcriptions": sum(c["transcription_count"] for c in clusters)
    }, "Content map retrieved successfully")

@app.post("/api/visual-search/similarity")
async def search_visual_similarity(search_request: dict):
    """Search for visually similar content using embeddings"""
    query = search_request.get("query", "")
    limit = search_request.get("limit", 10)
    
    # Mock similarity search results
    results = []
    for i in range(min(limit, 8)):
        similarity_score = random.uniform(0.6, 0.95)
        
        result = {
            "transcript_id": f"transcript_{i:03d}",
            "title": f"Similar Content {i + 1}",
            "similarity_score": round(similarity_score, 3),
            "preview": f"This transcript discusses topics similar to '{query[:50]}...' with high relevance.",
            "duration": round(random.uniform(30, 3600), 1),
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "topics": random.sample(['AI', 'Technology', 'Research', 'Analysis'], random.randint(1, 3)),
            "confidence": round(random.uniform(0.8, 0.99), 2),
            "matching_segments": [
                {
                    "start_time": round(random.uniform(0, 1800), 1),
                    "end_time": round(random.uniform(1800, 3600), 1),
                    "text": f"Segment mentioning concepts similar to '{query[:30]}...'",
                    "similarity": round(similarity_score * random.uniform(0.9, 1.1), 3)
                }
                for _ in range(random.randint(1, 3))
            ]
        }
        results.append(result)
    
    # Sort by similarity
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return create_response({
        "query": query,
        "results": results,
        "total_results": len(results),
        "search_time_ms": random.randint(50, 200)
    }, "Visual similarity search completed")

@app.post("/api/visual-search/image-to-text")
async def image_to_text_search(search_request: dict):
    """Search for audio content using uploaded image"""
    image_description = search_request.get("image_description", "")
    limit = search_request.get("limit", 5)
    
    # Mock image-to-text search results
    results = []
    for i in range(min(limit, 5)):
        relevance = random.uniform(0.5, 0.9)
        
        result = {
            "transcript_id": f"image_match_{i:03d}",
            "title": f"Audio Content Related to Image {i + 1}",
            "relevance_score": round(relevance, 3),
            "description": f"Content discussing visual concepts related to: {image_description}",
            "duration": round(random.uniform(60, 1800), 1),
            "visual_concepts": random.sample([
                'charts', 'diagrams', 'presentations', 'visual data', 
                'screenshots', 'illustrations', 'graphics'
            ], random.randint(2, 4)),
            "matched_keywords": random.sample([
                'visual', 'display', 'show', 'demonstrate', 'chart', 'graph'
            ], random.randint(1, 3)),
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 15))).isoformat()
        }
        results.append(result)
    
    return create_response({
        "image_description": image_description,
        "results": results,
        "total_results": len(results),
        "processing_time_ms": random.randint(100, 500)
    }, "Image-to-text search completed")

@app.get("/api/visual-search/recommendations")
async def get_content_recommendations():
    """Get smart content recommendations"""
    recommendations = []
    
    recommendation_types = ['trending', 'similar_to_recent', 'topic_based', 'collaborative']
    
    for i, rec_type in enumerate(recommendation_types):
        for j in range(random.randint(2, 4)):
            rec = {
                "id": f"rec_{i}_{j}",
                "transcript_id": f"transcript_{i:03d}_{j:03d}",
                "title": f"Recommended: {rec_type.replace('_', ' ').title()} {j + 1}",
                "type": rec_type,
                "score": round(random.uniform(0.7, 0.95), 3),
                "reason": f"Recommended because of {rec_type.replace('_', ' ')} patterns",
                "duration": round(random.uniform(120, 2400), 1),
                "topics": random.sample(['Technology', 'Science', 'Research'], random.randint(1, 2)),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
                "view_count": random.randint(10, 1000),
                "rating": round(random.uniform(3.5, 5.0), 1)
            }
            recommendations.append(rec)
    
    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return create_response({
        "recommendations": recommendations[:15],  # Top 15
        "total_recommendations": len(recommendations),
        "recommendation_types": recommendation_types
    }, "Content recommendations retrieved successfully")

# Recommendation endpoints
@app.post("/api/recommendations/track-interaction")
async def track_interaction(interaction_data: dict):
    """Track user interaction with content"""
    user_id = interaction_data.get("user_id", "test_user")
    transcript_id = interaction_data.get("transcript_id")
    action_type = interaction_data.get("action_type", "view")
    duration = interaction_data.get("duration_seconds")
    
    # In production, this would call the recommendation engine
    return create_response({
        "tracked": True,
        "user_id": user_id,
        "transcript_id": transcript_id,
        "action_type": action_type
    }, "Interaction tracked successfully")

@app.get("/api/recommendations/personalized")
async def get_personalized_recommendations(
    user_id: str = "test_user",
    limit: int = 10
):
    """Get personalized recommendations for a user"""
    recommendations = []
    
    # Mix of different recommendation types
    rec_types = [
        ('content_based', 'Based on your viewing history'),
        ('collaborative', 'Popular with users like you'),
        ('trending', 'Trending this week'),
        ('personalized', 'Matches your interests')
    ]
    
    for i in range(min(limit, 10)):
        rec_type, reason = rec_types[i % len(rec_types)]
        
        rec = {
            "transcript_id": f"rec_{i:03d}",
            "title": f"Recommended Content {i + 1}",
            "score": round(random.uniform(0.7, 0.98), 3),
            "recommendation_type": rec_type,
            "reason": reason,
            "duration": round(random.uniform(300, 3600), 1),
            "topics": random.sample(['AI', 'Technology', 'Science', 'Research'], random.randint(1, 3)),
            "language": random.choice(['en', 'es', 'fr']),
            "thumbnail_url": f"/api/thumbnails/rec_{i:03d}.jpg",
            "metadata": {
                "view_count": random.randint(100, 10000),
                "completion_rate": round(random.uniform(0.6, 0.95), 2),
                "created_days_ago": random.randint(1, 30)
            }
        }
        recommendations.append(rec)
    
    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return create_response({
        "user_id": user_id,
        "recommendations": recommendations,
        "total_count": len(recommendations)
    }, "Personalized recommendations retrieved")

@app.get("/api/recommendations/similar/{transcript_id}")
async def get_similar_content(
    transcript_id: str,
    limit: int = 5
):
    """Get content similar to a specific transcript"""
    similar_content = []
    
    for i in range(min(limit, 5)):
        content = {
            "transcript_id": f"similar_{i:03d}",
            "title": f"Similar to {transcript_id} - Item {i + 1}",
            "similarity_score": round(random.uniform(0.65, 0.95), 3),
            "preview": f"Content with similar themes and topics...",
            "common_topics": random.sample(['AI', 'ML', 'Data Science'], random.randint(1, 2)),
            "duration": round(random.uniform(300, 2400), 1),
            "language": "en",
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()
        }
        similar_content.append(content)
    
    similar_content.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return create_response({
        "source_transcript_id": transcript_id,
        "similar_content": similar_content,
        "total_count": len(similar_content)
    }, "Similar content retrieved successfully")

@app.get("/api/recommendations/trending-topics")
async def get_trending_topics(
    time_window: str = "daily",
    limit: int = 10
):
    """Get trending topics across all content"""
    topics = []
    
    topic_names = [
        'Artificial Intelligence', 'Machine Learning', 'Data Science',
        'Cloud Computing', 'Cybersecurity', 'Blockchain', 'IoT',
        'Quantum Computing', 'Edge Computing', 'DevOps'
    ]
    
    for i, topic in enumerate(topic_names[:limit]):
        trend = random.choice(['up', 'down', 'stable', 'new'])
        
        topic_data = {
            "topic": topic,
            "score": round(random.uniform(50, 100), 1),
            "transcript_count": random.randint(5, 50),
            "view_count": random.randint(100, 5000),
            "trend": trend,
            "trend_percentage": round(random.uniform(-20, 50), 1) if trend != 'stable' else 0,
            "time_window": time_window,
            "top_transcripts": [
                {
                    "id": f"trend_{i}_{j}",
                    "title": f"{topic} - Example {j + 1}",
                    "views": random.randint(50, 1000)
                }
                for j in range(3)
            ]
        }
        topics.append(topic_data)
    
    topics.sort(key=lambda x: x["score"], reverse=True)
    
    return create_response({
        "time_window": time_window,
        "trending_topics": topics,
        "total_count": len(topics),
        "last_updated": datetime.now().isoformat()
    }, "Trending topics retrieved successfully")

@app.get("/api/recommendations/content-gaps")
async def analyze_content_gaps(limit: int = 10):
    """Analyze gaps in content coverage"""
    gaps = []
    
    gap_combinations = [
        (['AI', 'Healthcare'], 'AI applications in healthcare'),
        (['Blockchain', 'Finance'], 'Blockchain in financial services'),
        (['IoT', 'Security'], 'IoT security best practices'),
        (['Cloud', 'Migration'], 'Cloud migration strategies'),
        (['Data Science', 'Ethics'], 'Ethical considerations in data science'),
        (['ML', 'Edge Computing'], 'Machine learning at the edge'),
        (['Quantum', 'Cryptography'], 'Quantum-safe cryptography'),
        (['DevOps', 'Security'], 'DevSecOps practices'),
        (['AI', 'Sustainability'], 'AI for environmental sustainability'),
        (['Robotics', 'Healthcare'], 'Medical robotics applications')
    ]
    
    for i, (topics, description) in enumerate(gap_combinations[:limit]):
        gap = {
            "gap_id": f"gap_{i:03d}",
            "topics": topics,
            "description": description,
            "gap_score": round(random.uniform(60, 95), 1),
            "current_count": random.randint(0, 3),
            "recommended_count": random.randint(5, 15),
            "potential_audience": random.randint(500, 5000),
            "priority": random.choice(['high', 'medium', 'low']),
            "suggested_formats": random.sample(['tutorial', 'case study', 'interview', 'workshop'], 2)
        }
        gaps.append(gap)
    
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    
    return create_response({
        "content_gaps": gaps,
        "total_gaps": len(gaps),
        "analysis_date": datetime.now().isoformat()
    }, "Content gap analysis completed")

@app.post("/api/recommendations/smart-tags")
async def get_smart_tag_suggestions(tag_request: dict):
    """Get smart tag suggestions for content"""
    transcript_id = tag_request.get("transcript_id")
    content_preview = tag_request.get("content_preview", "")
    
    # Generate smart tags
    all_tags = [
        'Machine Learning', 'Deep Learning', 'Neural Networks',
        'Computer Vision', 'Natural Language Processing', 'Data Analysis',
        'Algorithm Design', 'System Architecture', 'Cloud Infrastructure',
        'Best Practices', 'Tutorial', 'Case Study', 'Research',
        'Beginner Friendly', 'Advanced Topics', 'Industry Insights'
    ]
    
    # Simulate tag extraction and scoring
    suggested_tags = []
    for tag in random.sample(all_tags, min(12, len(all_tags))):
        confidence = random.uniform(0.5, 0.95)
        source = random.choice(['content_analysis', 'similar_content', 'trending', 'user_behavior'])
        
        suggested_tags.append({
            "tag": tag,
            "confidence": round(confidence, 3),
            "source": source,
            "relevance_reason": f"Detected from {source.replace('_', ' ')}"
        })
    
    # Sort by confidence
    suggested_tags.sort(key=lambda x: x["confidence"], reverse=True)
    
    return create_response({
        "transcript_id": transcript_id,
        "suggested_tags": suggested_tags[:10],
        "existing_tags": random.sample(['Technology', 'Education'], random.randint(0, 2))
    }, "Smart tag suggestions generated")

@app.get("/api/recommendations/user-profile/{user_id}")
async def get_user_recommendation_profile(user_id: str):
    """Get user's recommendation profile"""
    profile = {
        "user_id": user_id,
        "favorite_topics": random.sample([
            'Artificial Intelligence', 'Machine Learning', 'Data Science',
            'Cloud Computing', 'Cybersecurity'
        ], random.randint(2, 4)),
        "language_preferences": random.sample(['en', 'es', 'fr'], random.randint(1, 2)),
        "avg_session_duration": round(random.uniform(300, 1800), 1),
        "total_viewed": random.randint(10, 200),
        "completion_rate": round(random.uniform(0.5, 0.9), 2),
        "last_active": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
        "interaction_stats": {
            "views": random.randint(50, 500),
            "likes": random.randint(10, 100),
            "shares": random.randint(5, 50),
            "completions": random.randint(20, 200)
        },
        "content_preferences": {
            "preferred_duration": "medium",  # short, medium, long
            "preferred_difficulty": "intermediate",  # beginner, intermediate, advanced
            "preferred_format": random.choice(['tutorial', 'lecture', 'discussion'])
        }
    }
    
    return create_response(profile, "User recommendation profile retrieved")


# Content Analysis endpoints
@app.post("/api/content-analysis/analyze")
async def analyze_content(request: dict):
    """Perform comprehensive AI-powered content analysis"""
    transcript_id = request.get("transcript_id", "test_transcript_001")
    
    # Get transcript text (mock for now)
    text = """
    Welcome everyone to today's presentation about artificial intelligence. I'm really excited to share 
    these insights with you. AI is transforming how we work and live. Let me start by saying that 
    everyone, regardless of their background, can benefit from understanding AI.
    
    Um, so basically, the first thing we need to understand is that AI is not just for technical people.
    It's actually becoming part of our daily lives. You know, from voice assistants to recommendation 
    systems. 
    
    Now, I want to address a common misconception. Many people think AI will replace all jobs. That's 
    not entirely true! AI is more about augmentation than replacement. It helps us work smarter, not 
    harder.
    
    Let's look at some examples. In healthcare, AI helps doctors diagnose diseases faster. In education,
    it personalizes learning experiences. These are exciting developments that benefit everyone.
    
    However, we must be careful about bias in AI systems. It's crucial that we build inclusive AI that 
    works for all people, regardless of their gender, age, or background. This is something I'm 
    particularly passionate about.
    
    In conclusion, AI is a powerful tool that can help us solve complex problems. But we need to use it
    responsibly and ensure it benefits everyone equally. Thank you for your attention, and I'm happy to
    answer any questions!
    """
    
    # Mock analysis results
    analysis_result = {
        "transcript_id": transcript_id,
        "emotion_analysis": {
            "dominant_emotion": "joy",
            "emotion_scores": {
                "joy": 0.45,
                "surprise": 0.15,
                "fear": 0.05,
                "sadness": 0.02,
                "anger": 0.03,
                "disgust": 0.01
            },
            "emotion_timeline": [
                {"time": 0, "emotion": "joy", "sentiment": 0.8, "confidence": 0.85},
                {"time": 20, "emotion": "neutral", "sentiment": 0.2, "confidence": 0.7},
                {"time": 40, "emotion": "concern", "sentiment": -0.1, "confidence": 0.6},
                {"time": 60, "emotion": "excitement", "sentiment": 0.6, "confidence": 0.8},
                {"time": 80, "emotion": "determination", "sentiment": 0.4, "confidence": 0.75}
            ],
            "overall_sentiment": "positive",
            "sentiment_score": 0.68,
            "mood_changes": [
                {"time": 40, "from": "positive", "to": "neutral", "intensity": 0.3},
                {"time": 60, "from": "neutral", "to": "positive", "intensity": 0.5}
            ]
        },
        "speaking_patterns": {
            "speaking_rate": 145.5,
            "pace_variation": 12.3,
            "pause_frequency": 2.1,
            "pause_duration_avg": 0.8,
            "filler_word_count": 6,
            "filler_word_ratio": 0.048,
            "emphasis_patterns": [
                {"type": "capitalization", "word": "AI", "position": 15, "context": "how AI is transforming"},
                {"type": "intensity", "word": "really", "position": 8, "context": "I'm really excited"},
                {"type": "repetition", "word": "everyone", "position": 45, "context": "benefit everyone"}
            ],
            "fluency_score": 0.72
        },
        "complexity_analysis": {
            "readability_score": 65.3,
            "grade_level": 8.2,
            "vocabulary_diversity": 0.274,
            "sentence_complexity": 0.45,
            "technical_term_ratio": 0.08,
            "jargon_score": 0.12,
            "clarity_score": 0.78
        },
        "bias_analysis": {
            "bias_detected": True,
            "bias_types": ["gender", "age"],
            "bias_instances": [
                {
                    "type": "gender",
                    "term": "he",
                    "count": 8,
                    "category": "male-specific"
                },
                {
                    "type": "age",
                    "term": "young",
                    "context": "especially for young people",
                    "suggestion": "Consider using age-neutral terms"
                }
            ],
            "inclusivity_score": 0.78,
            "suggestions": [
                "Consider using more gender-neutral language (they/them) instead of he/she",
                "Balance gender representation in examples and references",
                "Use age-neutral terminology"
            ],
            "gender_balance": {
                "male": 0.73,
                "female": 0.27,
                "neutral_ratio": 0.15
            }
        },
        "key_insights": [
            "Content has a strongly positive tone (joy)",
            "Speaking pace is optimal for comprehension",
            "Content is easily accessible to general audience",
            "Detected 2 types of potential bias",
            "High technical jargon detected - may need simplification"
        ],
        "recommendations": [
            "Reduce filler words for more professional delivery",
            "Increase use of gender-neutral pronouns (they/them)",
            "Define technical terms when first introduced",
            "Add diverse examples to represent various backgrounds"
        ],
        "metadata": {
            "analyzed_at": datetime.now().isoformat(),
            "text_length": len(text),
            "word_count": len(text.split()),
            "has_audio": False,
            "has_timestamps": True
        }
    }
    
    return create_response(analysis_result, "Content analysis completed successfully")


@app.get("/api/content-analysis/emotion-timeline/{transcript_id}")
async def get_emotion_timeline(transcript_id: str):
    """Get emotion timeline visualization data"""
    # Mock emotion timeline data
    timeline_data = []
    emotions = ["joy", "surprise", "neutral", "fear", "sadness"]
    
    for i in range(20):
        time = i * 5  # Every 5 seconds
        emotion = emotions[i % len(emotions)]
        sentiment = 0.5 - (i * 0.05) + (0.1 if i % 3 == 0 else -0.1)
        
        timeline_data.append({
            "time": time,
            "emotion": emotion,
            "sentiment": max(-1, min(1, sentiment)),
            "confidence": 0.7 + (i % 3) * 0.1
        })
    
    return create_response({
        "transcript_id": transcript_id,
        "timeline": timeline_data,
        "duration": 100,
        "mood_shifts": 3
    }, "Emotion timeline retrieved")


@app.get("/api/content-analysis/speaking-insights/{transcript_id}")
async def get_speaking_insights(transcript_id: str):
    """Get detailed speaking pattern insights"""
    insights = {
        "pace_analysis": {
            "average_wpm": 145,
            "pace_segments": [
                {"start": 0, "end": 30, "wpm": 120, "label": "slow"},
                {"start": 30, "end": 60, "wpm": 150, "label": "normal"},
                {"start": 60, "end": 90, "wpm": 180, "label": "fast"}
            ],
            "recommendation": "Consider slowing down during technical explanations"
        },
        "pause_analysis": {
            "total_pauses": 24,
            "average_duration": 0.8,
            "strategic_pauses": 8,
            "filler_pauses": 16,
            "pause_distribution": [
                {"duration": "0-0.5s", "count": 10},
                {"duration": "0.5-1s", "count": 8},
                {"duration": "1-2s", "count": 4},
                {"duration": ">2s", "count": 2}
            ]
        },
        "emphasis_analysis": {
            "emphasized_words": [
                {"word": "CRUCIAL", "timestamp": 73.0, "type": "capitalization"},
                {"word": "everyone", "timestamp": 13.0, "type": "repetition"},
                {"word": "really", "timestamp": 5.5, "type": "intensity"}
            ],
            "emphasis_frequency": 0.05
        },
        "fluency_metrics": {
            "fluency_score": 0.72,
            "filler_words": {
                "um": 3,
                "uh": 1,
                "you know": 2,
                "basically": 2,
                "actually": 1
            },
            "repetitions": 4,
            "self_corrections": 2
        }
    }
    
    return create_response(insights, "Speaking insights retrieved")


@app.get("/api/content-analysis/readability/{transcript_id}")
async def get_readability_analysis(transcript_id: str):
    """Get detailed readability and complexity analysis"""
    analysis = {
        "readability_scores": {
            "flesch_reading_ease": 65.3,
            "flesch_kincaid_grade": 8.2,
            "gunning_fog": 10.5,
            "smog_index": 9.8,
            "automated_readability": 7.9
        },
        "complexity_breakdown": {
            "simple_sentences": 45,
            "compound_sentences": 25,
            "complex_sentences": 20,
            "compound_complex": 10
        },
        "vocabulary_analysis": {
            "unique_words": 342,
            "total_words": 1250,
            "diversity_ratio": 0.274,
            "technical_terms": [
                "artificial intelligence", "augmentation", "personalization",
                "recommendation systems", "bias", "inclusive AI"
            ],
            "jargon_density": 0.08
        },
        "audience_suitability": {
            "general_public": 0.85,
            "high_school": 0.92,
            "college": 0.98,
            "expert": 0.65
        },
        "improvement_suggestions": [
            "Define technical terms when first introduced",
            "Break down complex sentences for clarity",
            "Use more concrete examples for abstract concepts"
        ]
    }
    
    return create_response(analysis, "Readability analysis completed")


@app.get("/api/content-analysis/bias-report/{transcript_id}")
async def get_bias_report(transcript_id: str):
    """Get comprehensive bias analysis report"""
    report = {
        "overall_inclusivity_score": 0.78,
        "bias_summary": {
            "total_instances": 5,
            "bias_types_found": ["gender", "age"],
            "severity": "low"
        },
        "detailed_findings": [
            {
                "type": "gender",
                "instance": "he/she imbalance",
                "location": "paragraph 3",
                "suggestion": "Consider using gender-neutral pronouns (they/them)",
                "impact": "medium"
            },
            {
                "type": "age",
                "instance": "young people",
                "location": "paragraph 5",
                "suggestion": "Use 'early-career professionals' or 'newer to the field'",
                "impact": "low"
            }
        ],
        "gender_representation": {
            "male_pronouns": 8,
            "female_pronouns": 3,
            "neutral_pronouns": 15,
            "balance_score": 0.65
        },
        "language_inclusivity": {
            "inclusive_phrases": 12,
            "exclusive_phrases": 2,
            "score": 0.86
        },
        "recommendations": [
            "Increase use of gender-neutral language throughout",
            "Replace age-specific terms with inclusive alternatives",
            "Add diverse examples to represent various backgrounds"
        ]
    }
    
    return create_response(report, "Bias analysis report generated")


# Advanced Search endpoints
@app.post("/api/search/advanced")
async def advanced_search(request: Request):
    """Perform advanced search with operators"""
    try:
        data = await request.json()
        query = data.get("query", "")
        filters = data.get("filters", {})
        limit = data.get("limit", 50)
        offset = data.get("offset", 0)
        
        # Import search engine
        from search.advanced_search import AdvancedSearchEngine, SearchFilter
        
        # Create search engine
        search_engine = AdvancedSearchEngine()
        
        # Parse filters
        search_filter = SearchFilter()
        if filters.get("date_from"):
            search_filter.date_from = datetime.fromisoformat(filters["date_from"])
        if filters.get("date_to"):
            search_filter.date_to = datetime.fromisoformat(filters["date_to"])
        search_filter.languages = filters.get("languages", [])
        search_filter.speakers = filters.get("speakers", [])
        search_filter.duration_min = filters.get("duration_min")
        search_filter.duration_max = filters.get("duration_max")
        search_filter.entities = filters.get("entities", [])
        search_filter.topics = filters.get("topics", [])
        search_filter.tags = filters.get("tags", [])
        
        # Perform search
        results = search_engine.search(query, search_filter, limit, offset)
        
        return JSONResponse(content={
            "status": "success",
            "data": results
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/search/operators")
async def get_search_operators():
    """Get available search operators and syntax help"""
    operators = {
        "operators": [
            {
                "operator": "AND",
                "description": "Both terms must be present",
                "example": "machine AND learning",
                "aliases": ["&", "&&"]
            },
            {
                "operator": "OR",
                "description": "Either term must be present",
                "example": "python OR javascript",
                "aliases": ["|", "||"]
            },
            {
                "operator": "NOT",
                "description": "Exclude terms",
                "example": "machine NOT bias",
                "aliases": ["-", "!"]
            },
            {
                "operator": "\"\"",
                "description": "Exact phrase match",
                "example": "\"artificial intelligence\"",
                "aliases": ["''"]
            },
            {
                "operator": "*",
                "description": "Wildcard (any characters)",
                "example": "neuro*",
                "aliases": []
            },
            {
                "operator": "?",
                "description": "Single character wildcard",
                "example": "te?t",
                "aliases": []
            },
            {
                "operator": "NEAR",
                "description": "Terms near each other",
                "example": "python NEAR django",
                "aliases": ["~"]
            }
        ],
        "fields": [
            {
                "field": "title",
                "description": "Search in transcript titles",
                "example": "title:introduction",
                "type": "text"
            },
            {
                "field": "content",
                "description": "Search in transcript content",
                "example": "content:machine learning",
                "type": "text",
                "aliases": ["text"]
            },
            {
                "field": "speaker",
                "description": "Search by speaker name",
                "example": "speaker:john",
                "type": "text"
            },
            {
                "field": "entity",
                "description": "Search by entity (person, org, etc)",
                "example": "entity:Google",
                "type": "text",
                "aliases": ["person"]
            },
            {
                "field": "topic",
                "description": "Search by topic",
                "example": "topic:AI",
                "type": "text",
                "aliases": ["subject"]
            },
            {
                "field": "language",
                "description": "Filter by language",
                "example": "language:en",
                "type": "enum",
                "values": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "ko", "zh"],
                "aliases": ["lang"]
            },
            {
                "field": "date",
                "description": "Filter by date",
                "example": "date:last-7-days",
                "type": "date",
                "formats": ["today", "yesterday", "last-7-days", "last-30-days", "this-week", "last-week", "this-month", "YYYY-MM-DD", "YYYY-MM-DD..YYYY-MM-DD"]
            },
            {
                "field": "duration",
                "description": "Filter by duration (seconds)",
                "example": "duration:300-600",
                "type": "range"
            },
            {
                "field": "tag",
                "description": "Search by tag",
                "example": "tag:tutorial",
                "type": "text"
            }
        ],
        "examples": [
            {
                "query": "machine learning AND python",
                "description": "Find transcripts about machine learning with Python"
            },
            {
                "query": "\"artificial intelligence\" NOT bias",
                "description": "Find AI content without bias discussions"
            },
            {
                "query": "speaker:john OR speaker:jane",
                "description": "Find transcripts by John or Jane"
            },
            {
                "query": "topic:AI language:en date:last-7-days",
                "description": "Recent English AI content"
            },
            {
                "query": "neural* AND (python OR tensorflow)",
                "description": "Neural networks with Python or TensorFlow"
            },
            {
                "query": "entity:Google NEAR entity:AI",
                "description": "Content mentioning Google near AI"
            }
        ],
        "tips": [
            "Use quotes for exact phrases",
            "Combine multiple filters for precise results",
            "Use wildcards for partial matches",
            "Operators are case-insensitive",
            "Parentheses can group terms: (A OR B) AND C"
        ]
    }
    
    return create_response(operators, "Search operators retrieved")


@app.get("/api/search/suggestions")
async def get_search_suggestions(q: str = Query(..., description="Partial search query")):
    """Get search suggestions based on partial query"""
    # Mock suggestions based on query
    suggestions = []
    
    # Common search terms
    common_terms = [
        "machine learning", "artificial intelligence", "neural networks",
        "deep learning", "python", "data science", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "algorithms",
        "bias", "ethics", "automation", "robotics"
    ]
    
    # Filter suggestions based on query
    q_lower = q.lower()
    for term in common_terms:
        if term.startswith(q_lower):
            suggestions.append({
                "type": "term",
                "value": term,
                "display": term
            })
    
    # Add field suggestions
    if ':' in q:
        field, value = q.split(':', 1)
        if field.lower() in ['speaker', 'entity', 'topic', 'tag']:
            # Mock field values
            if field.lower() == 'speaker':
                values = ["John Smith", "Jane Doe", "Dr. Johnson", "Prof. Williams"]
            elif field.lower() == 'entity':
                values = ["Google", "Microsoft", "OpenAI", "MIT", "Stanford"]
            elif field.lower() == 'topic':
                values = ["AI", "Machine Learning", "Data Science", "Ethics", "Healthcare"]
            else:
                values = ["tutorial", "advanced", "beginner", "research", "case-study"]
            
            for v in values:
                if v.lower().startswith(value.lower()):
                    suggestions.append({
                        "type": "field",
                        "value": f"{field}:{v}",
                        "display": f"{field}: {v}"
                    })
    
    # Add operator suggestions
    if len(q.split()) >= 1 and not any(op in q.upper() for op in ['AND', 'OR', 'NOT']):
        last_word = q.split()[-1]
        suggestions.extend([
            {
                "type": "operator",
                "value": f"{q} AND ",
                "display": f"{q} AND ..."
            },
            {
                "type": "operator",
                "value": f"{q} OR ",
                "display": f"{q} OR ..."
            }
        ])
    
    # Add filter suggestions
    if 'date:' not in q:
        suggestions.append({
            "type": "filter",
            "value": f"{q} date:last-7-days",
            "display": "Last 7 days"
        })
    
    return create_response({
        "suggestions": suggestions[:10],
        "query": q
    }, "Search suggestions generated")


@app.get("/api/search/history")
async def get_search_history(user_id: str = "test_user"):
    """Get user's search history"""
    # Mock search history
    history = [
        {
            "id": "search_001",
            "query": "machine learning python",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "result_count": 15,
            "clicked_results": 3
        },
        {
            "id": "search_002", 
            "query": "speaker:john topic:AI",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "result_count": 8,
            "clicked_results": 2
        },
        {
            "id": "search_003",
            "query": "\"neural networks\" date:last-7-days",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "result_count": 23,
            "clicked_results": 5
        },
        {
            "id": "search_004",
            "query": "ethics AND bias NOT discrimination",
            "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
            "result_count": 12,
            "clicked_results": 1
        }
    ]
    
    return create_response({
        "user_id": user_id,
        "history": history,
        "total_searches": len(history)
    }, "Search history retrieved")


@app.post("/api/search/save")
async def save_search(request: Request):
    """Save a search query for later use"""
    data = await request.json()
    
    saved_search = {
        "id": f"saved_{random.randint(1000, 9999)}",
        "name": data.get("name", "Untitled Search"),
        "query": data.get("query"),
        "filters": data.get("filters", {}),
        "created_at": datetime.now().isoformat(),
        "notification_enabled": data.get("notification_enabled", False)
    }
    
    return create_response({
        "saved_search": saved_search,
        "message": "Search saved successfully"
    }, "Search saved")


@app.get("/api/search/saved")
async def get_saved_searches(user_id: str = "test_user"):
    """Get user's saved searches"""
    saved_searches = [
        {
            "id": "saved_001",
            "name": "AI Ethics Research",
            "query": "ethics AND (AI OR \"artificial intelligence\")",
            "filters": {"language": ["en"], "date": "last-30-days"},
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "notification_enabled": True,
            "last_run": (datetime.now() - timedelta(hours=12)).isoformat(),
            "new_results": 3
        },
        {
            "id": "saved_002",
            "name": "Python ML Tutorials",
            "query": "python machine learning tag:tutorial",
            "filters": {"duration_max": 3600},
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "notification_enabled": False,
            "last_run": (datetime.now() - timedelta(days=2)).isoformat(),
            "new_results": 0
        }
    ]
    
    return create_response({
        "user_id": user_id,
        "saved_searches": saved_searches,
        "total": len(saved_searches)
    }, "Saved searches retrieved")


# Transcription endpoints
@app.post("/api/transcription/upload")
async def upload_file_for_transcription(file: UploadFile = File(...)):
    """Handle file upload for transcription"""
    try:
        # Read file content (in real app, this would be saved to disk/S3)
        contents = await file.read()
        file_size = len(contents)
        
        # Generate a unique file ID
        file_id = f"file_{random.randint(10000, 99999)}"
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "file_id": file_id,
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type,
                "message": "File uploaded successfully"
            }
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/transcription/transcribe")
async def transcribe_file(request: Request):
    """Process transcription for uploaded file - matching frontend expectation"""
    data = await request.json()
    file_id = data.get("file_id")
    
    # Mock transcription result
    result = {
        "id": f"transcript_{random.randint(10000, 99999)}",
        "status": "completed",
        "text": """
        Welcome to our presentation on artificial intelligence and machine learning.
        Today we'll explore how AI is transforming various industries and the
        implications for the future of work. We'll cover neural networks,
        deep learning, and practical applications in healthcare, finance, and education.
        """,
        "segments": [
            {
                "start": 0.0,
                "end": 5.2,
                "text": "Welcome to our presentation on artificial intelligence and machine learning.",
                "speaker": "Speaker 1"
            },
            {
                "start": 5.2,
                "end": 10.5,
                "text": "Today we'll explore how AI is transforming various industries and the implications for the future of work.",
                "speaker": "Speaker 1"
            },
            {
                "start": 10.5,
                "end": 16.0,
                "text": "We'll cover neural networks, deep learning, and practical applications in healthcare, finance, and education.",
                "speaker": "Speaker 1"
            }
        ],
        "entities": [
            {"text": "artificial intelligence", "type": "TECHNOLOGY", "start": 35, "end": 57},
            {"text": "machine learning", "type": "TECHNOLOGY", "start": 62, "end": 78},
            {"text": "AI", "type": "TECHNOLOGY", "start": 97, "end": 99},
            {"text": "neural networks", "type": "TECHNOLOGY", "start": 180, "end": 195},
            {"text": "deep learning", "type": "TECHNOLOGY", "start": 197, "end": 210}
        ],
        "speakers": ["Speaker 1"],
        "language": data.get("language", "en"),
        "duration": 16.0,
        "confidence": 0.95
    }
    
    return JSONResponse(content={
        "status": "success",
        "data": result
    })


@app.post("/api/transcription/process")
async def process_transcription(request: Request):
    """Process transcription for uploaded file"""
    data = await request.json()
    file_id = data.get("file_id")
    
    # Mock transcription result
    result = {
        "transcript_id": f"transcript_{random.randint(10000, 99999)}",
        "status": "completed",
        "text": """
        Welcome to our presentation on artificial intelligence and machine learning.
        Today we'll explore how AI is transforming various industries and the
        implications for the future of work. We'll cover neural networks,
        deep learning, and practical applications in healthcare, finance, and education.
        """,
        "segments": [
            {
                "start": 0.0,
                "end": 5.2,
                "text": "Welcome to our presentation on artificial intelligence and machine learning.",
                "speaker": "Speaker 1"
            },
            {
                "start": 5.2,
                "end": 10.5,
                "text": "Today we'll explore how AI is transforming various industries and the implications for the future of work.",
                "speaker": "Speaker 1"
            },
            {
                "start": 10.5,
                "end": 16.0,
                "text": "We'll cover neural networks, deep learning, and practical applications in healthcare, finance, and education.",
                "speaker": "Speaker 1"
            }
        ],
        "entities": [
            {"text": "artificial intelligence", "type": "TECHNOLOGY", "start": 35, "end": 57},
            {"text": "machine learning", "type": "TECHNOLOGY", "start": 62, "end": 78},
            {"text": "AI", "type": "TECHNOLOGY", "start": 97, "end": 99},
            {"text": "neural networks", "type": "TECHNOLOGY", "start": 180, "end": 195},
            {"text": "deep learning", "type": "TECHNOLOGY", "start": 197, "end": 210}
        ],
        "speakers": ["Speaker 1"],
        "language": "en",
        "duration": 16.0,
        "word_count": 45
    }
    
    return create_response(result, "Transcription processed successfully")


@app.get("/api/transcription/status/{transcript_id}")
async def get_transcription_status(transcript_id: str):
    """Get transcription status"""
    # Mock status
    status = {
        "transcript_id": transcript_id,
        "status": "completed",
        "progress": 100,
        "message": "Transcription completed successfully",
        "created_at": datetime.now().isoformat(),
        "completed_at": (datetime.now() + timedelta(seconds=30)).isoformat()
    }
    
    return create_response(status, "Status retrieved")


@app.get("/api/transcription/{transcript_id}")
async def get_transcription(transcript_id: str):
    """Get transcription details"""
    # Return the same mock data as process_transcription
    result = {
        "transcript_id": transcript_id,
        "status": "completed",
        "text": """
        Welcome to our presentation on artificial intelligence and machine learning.
        Today we'll explore how AI is transforming various industries and the
        implications for the future of work. We'll cover neural networks,
        deep learning, and practical applications in healthcare, finance, and education.
        """,
        "segments": [
            {
                "start": 0.0,
                "end": 5.2,
                "text": "Welcome to our presentation on artificial intelligence and machine learning.",
                "speaker": "Speaker 1"
            },
            {
                "start": 5.2,
                "end": 10.5,
                "text": "Today we'll explore how AI is transforming various industries and the implications for the future of work.",
                "speaker": "Speaker 1"
            },
            {
                "start": 10.5,
                "end": 16.0,
                "text": "We'll cover neural networks, deep learning, and practical applications in healthcare, finance, and education.",
                "speaker": "Speaker 1"
            }
        ],
        "entities": [
            {"text": "artificial intelligence", "type": "TECHNOLOGY", "start": 35, "end": 57},
            {"text": "machine learning", "type": "TECHNOLOGY", "start": 62, "end": 78},
            {"text": "AI", "type": "TECHNOLOGY", "start": 97, "end": 99},
            {"text": "neural networks", "type": "TECHNOLOGY", "start": 180, "end": 195},
            {"text": "deep learning", "type": "TECHNOLOGY", "start": 197, "end": 210}
        ],
        "speakers": ["Speaker 1"],
        "language": "en",
        "duration": 16.0,
        "word_count": 45,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return create_response(result, "Transcription retrieved")


@app.delete("/api/transcription/{transcript_id}")
async def delete_transcription(transcript_id: str):
    """Delete a transcription"""
    return create_response({
        "transcript_id": transcript_id,
        "message": "Transcription deleted successfully"
    }, "Deleted successfully")


if __name__ == "__main__":
    print("🚀 Starting Simple FastAPI server on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")