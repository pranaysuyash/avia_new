"""
Content Insights API Endpoints
REST API for AI-powered content analysis and insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Dict, Any
import os
import sys
import logging
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..auth import auth_required, read_required, create_api_response
from ..models import (
    InsightRequest, InsightResponse, InsightResult,
    SentimentAnalysis, TopicAnalysis, ContentSummary
)

# Import insights modules
from content_insights import ContentInsightsAnalyzer, ContentInsights
from session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["Content Insights"])

# Initialize components
insights_analyzer = ContentInsightsAnalyzer()
session_manager = SessionManager()


@router.post("/analyze/{transcript_id}", response_model=InsightResponse)
async def analyze_content(
    transcript_id: str,
    request: InsightRequest,
    user_id: str = Depends(read_required)
):
    """Analyze transcript content for insights"""
    try:
        # Get transcript data from session
        results = session_manager.get_stored_results(user_id)
        transcript_data = None
        
        for result in results:
            if result.get('transcript_id') == transcript_id:
                transcript_data = result['result']
                break
        
        if not transcript_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )
        
        start_time = datetime.now()
        
        # Prepare speaker segments if available
        speaker_segments = None
        if transcript_data.get('speakers'):
            speaker_segments = [
                {
                    'speaker_id': speaker['speaker_id'],
                    'start_time': speaker['start_time'],
                    'end_time': speaker['end_time'],
                    'text': speaker.get('text', ''),
                    'duration': speaker['end_time'] - speaker['start_time']
                }
                for speaker in transcript_data['speakers']
            ]
        
        # Run content analysis
        insights = await insights_analyzer.analyze_content(
            transcript=transcript_data['text'],
            transcript_id=transcript_id,
            speaker_segments=speaker_segments
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Convert to API models
        result = InsightResult(
            transcript_id=transcript_id,
            processing_time=processing_time,
            generated_at=datetime.now()
        )
        
        # Add requested analysis results
        if "sentiment" in request.analysis_types and insights.sentiment:
            result.sentiment = SentimentAnalysis(
                overall_sentiment=insights.sentiment.overall_sentiment,
                confidence=insights.sentiment.confidence,
                positive_score=insights.sentiment.positive_score,
                negative_score=insights.sentiment.negative_score,
                neutral_score=insights.sentiment.neutral_score
            )
        
        if "topics" in request.analysis_types and insights.topics:
            result.topics = TopicAnalysis(
                topics=insights.topics.topics,
                main_topic=insights.topics.main_topic,
                topic_distribution=insights.topics.topic_distribution
            )
        
        if "summary" in request.analysis_types and insights.summary:
            result.summary = ContentSummary(
                brief=insights.summary.brief,
                detailed=insights.summary.detailed,
                key_points=insights.summary.key_points,
                word_count=len(insights.summary.detailed.split())
            )
        
        # Store insights in session for future retrieval
        session_data = session_manager.get_session_data(user_id) or {}
        if 'insights' not in session_data:
            session_data['insights'] = {}
        
        session_data['insights'][transcript_id] = {
            'result': result.dict(),
            'generated_at': datetime.now().isoformat(),
            'analysis_types': request.analysis_types
        }
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(result, "Content analysis completed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content analysis failed"
        )


@router.get("/sentiment/{transcript_id}")
async def get_sentiment_analysis(
    transcript_id: str,
    user_id: str = Depends(read_required)
):
    """Get sentiment analysis for specific transcript"""
    try:
        # Check if insights already exist
        session_data = session_manager.get_session_data(user_id) or {}
        insights = session_data.get('insights', {})
        
        if transcript_id in insights:
            stored_result = insights[transcript_id]['result']
            if stored_result.get('sentiment'):
                return create_api_response(
                    stored_result['sentiment'],
                    "Sentiment analysis retrieved from cache"
                )
        
        # If not cached, run analysis
        request = InsightRequest(transcript_id=transcript_id, analysis_types=["sentiment"])
        response = await analyze_content(transcript_id, request, user_id)
        
        if response.get('data') and response['data'].get('sentiment'):
            return create_api_response(
                response['data']['sentiment'],
                "Sentiment analysis completed"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Sentiment analysis could not be completed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sentiment analysis failed"
        )


@router.get("/topics/{transcript_id}")
async def get_topic_analysis(
    transcript_id: str,
    user_id: str = Depends(read_required)
):
    """Get topic analysis for specific transcript"""
    try:
        # Check if insights already exist
        session_data = session_manager.get_session_data(user_id) or {}
        insights = session_data.get('insights', {})
        
        if transcript_id in insights:
            stored_result = insights[transcript_id]['result']
            if stored_result.get('topics'):
                return create_api_response(
                    stored_result['topics'],
                    "Topic analysis retrieved from cache"
                )
        
        # If not cached, run analysis
        request = InsightRequest(transcript_id=transcript_id, analysis_types=["topics"])
        response = await analyze_content(transcript_id, request, user_id)
        
        if response.get('data') and response['data'].get('topics'):
            return create_api_response(
                response['data']['topics'],
                "Topic analysis completed"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Topic analysis could not be completed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topic analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Topic analysis failed"
        )


@router.get("/summary/{transcript_id}")
async def get_content_summary(
    transcript_id: str,
    summary_type: str = Query(default="detailed", regex="^(brief|detailed|key_points)$"),
    user_id: str = Depends(read_required)
):
    """Get content summary for specific transcript"""
    try:
        # Check if insights already exist
        session_data = session_manager.get_session_data(user_id) or {}
        insights = session_data.get('insights', {})
        
        if transcript_id in insights:
            stored_result = insights[transcript_id]['result']
            if stored_result.get('summary'):
                summary_data = stored_result['summary']
                
                if summary_type == "brief":
                    return create_api_response(
                        {"summary": summary_data['brief']},
                        "Brief summary retrieved"
                    )
                elif summary_type == "key_points":
                    return create_api_response(
                        {"key_points": summary_data['key_points']},
                        "Key points retrieved"
                    )
                else:
                    return create_api_response(
                        summary_data,
                        "Detailed summary retrieved"
                    )
        
        # If not cached, run analysis
        request = InsightRequest(transcript_id=transcript_id, analysis_types=["summary"])
        response = await analyze_content(transcript_id, request, user_id)
        
        if response.get('data') and response['data'].get('summary'):
            summary_data = response['data']['summary']
            
            if summary_type == "brief":
                return create_api_response(
                    {"summary": summary_data['brief']},
                    "Brief summary completed"
                )
            elif summary_type == "key_points":
                return create_api_response(
                    {"key_points": summary_data['key_points']},
                    "Key points extracted"
                )
            else:
                return create_api_response(
                    summary_data,
                    "Content summary completed"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Content summary could not be completed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content summary failed"
        )


@router.get("/speakers/{transcript_id}")
async def get_speaker_insights(
    transcript_id: str,
    user_id: str = Depends(read_required)
):
    """Get speaker-specific insights"""
    try:
        # Get transcript data
        results = session_manager.get_stored_results(user_id)
        transcript_data = None
        
        for result in results:
            if result.get('transcript_id') == transcript_id:
                transcript_data = result['result']
                break
        
        if not transcript_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )
        
        speakers = transcript_data.get('speakers', [])
        if not speakers:
            return create_api_response({
                "speakers": [],
                "total_speakers": 0,
                "message": "No speaker diarization data available"
            }, "No speaker data found")
        
        # Analyze each speaker
        speaker_insights = []
        for speaker in speakers:
            speaker_text = speaker.get('text', '')
            if speaker_text:
                # Run sentiment analysis on speaker text
                try:
                    speaker_sentiment = await insights_analyzer._analyze_sentiment(speaker_text)
                    
                    speaker_insights.append({
                        "speaker_id": speaker['speaker_id'],
                        "speaking_time": speaker['end_time'] - speaker['start_time'],
                        "word_count": len(speaker_text.split()),
                        "sentiment": {
                            "overall": speaker_sentiment.get('overall_sentiment', 'neutral'),
                            "confidence": speaker_sentiment.get('confidence', 0.5),
                            "positive_score": speaker_sentiment.get('positive_score', 0.5),
                            "negative_score": speaker_sentiment.get('negative_score', 0.5)
                        } if speaker_sentiment else None,
                        "text_sample": speaker_text[:200] + "..." if len(speaker_text) > 200 else speaker_text
                    })
                except Exception as e:
                    logger.warning(f"Speaker sentiment analysis failed: {e}")
                    speaker_insights.append({
                        "speaker_id": speaker['speaker_id'],
                        "speaking_time": speaker['end_time'] - speaker['start_time'],
                        "word_count": len(speaker_text.split()),
                        "sentiment": None,
                        "text_sample": speaker_text[:200] + "..." if len(speaker_text) > 200 else speaker_text
                    })
        
        return create_api_response({
            "speakers": speaker_insights,
            "total_speakers": len(speaker_insights),
            "total_speaking_time": sum(s['speaking_time'] for s in speaker_insights)
        }, "Speaker insights generated")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speaker insights error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speaker insights analysis failed"
        )


@router.get("/compare")
async def compare_transcripts(
    transcript_ids: List[str] = Query(..., min_items=2, max_items=10),
    user_id: str = Depends(read_required)
):
    """Compare insights across multiple transcripts"""
    try:
        if len(transcript_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 transcripts required for comparison"
            )
        
        # Get transcript data
        results = session_manager.get_stored_results(user_id)
        transcripts = []
        
        for transcript_id in transcript_ids:
            found = False
            for result in results:
                if result.get('transcript_id') == transcript_id:
                    transcripts.append({
                        'id': transcript_id,
                        'data': result['result']
                    })
                    found = True
                    break
            
            if not found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Transcript {transcript_id} not found"
                )
        
        # Generate comparison insights
        comparison_results = []
        
        for transcript in transcripts:
            transcript_id = transcript['id']
            transcript_data = transcript['data']
            
            # Quick analysis for comparison
            word_count = transcript_data.get('word_count', 0)
            duration = transcript_data.get('duration', 0)
            speaking_rate = word_count / (duration / 60) if duration > 0 else 0
            
            # Get cached insights if available
            session_data = session_manager.get_session_data(user_id) or {}
            cached_insights = session_data.get('insights', {}).get(transcript_id)
            
            comparison_results.append({
                "transcript_id": transcript_id,
                "word_count": word_count,
                "duration_minutes": round(duration / 60, 2),
                "speaking_rate_wpm": round(speaking_rate, 1),
                "language": transcript_data.get('language', 'unknown'),
                "has_speakers": len(transcript_data.get('speakers', [])) > 0,
                "speaker_count": len(transcript_data.get('speakers', [])),
                "entity_count": len(transcript_data.get('entities', [])),
                "cached_sentiment": cached_insights['result'].get('sentiment') if cached_insights else None,
                "created_at": transcript_data.get('created_at')
            })
        
        # Generate comparison statistics
        word_counts = [r['word_count'] for r in comparison_results]
        durations = [r['duration_minutes'] for r in comparison_results]
        speaking_rates = [r['speaking_rate_wpm'] for r in comparison_results]
        
        comparison_stats = {
            "transcript_count": len(comparison_results),
            "average_word_count": round(sum(word_counts) / len(word_counts), 1),
            "average_duration_minutes": round(sum(durations) / len(durations), 2),
            "average_speaking_rate_wpm": round(sum(speaking_rates) / len(speaking_rates), 1),
            "languages": list(set(r['language'] for r in comparison_results)),
            "total_speakers": sum(r['speaker_count'] for r in comparison_results)
        }
        
        return create_api_response({
            "transcripts": comparison_results,
            "comparison_stats": comparison_stats,
            "generated_at": datetime.now().isoformat()
        }, f"Comparison generated for {len(transcript_ids)} transcripts")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcript comparison failed"
        )


@router.get("/capabilities")
async def get_analysis_capabilities():
    """Get available analysis capabilities and requirements"""
    return create_api_response({
        "analysis_types": [
            {
                "name": "sentiment",
                "description": "Sentiment analysis with positive/negative/neutral scoring",
                "requirements": ["transcript_text"],
                "output": "overall_sentiment, confidence, scores"
            },
            {
                "name": "topics",
                "description": "Topic extraction and classification",
                "requirements": ["transcript_text"],
                "output": "topics_list, main_topic, distribution"
            },
            {
                "name": "summary",
                "description": "Content summarization at multiple levels",
                "requirements": ["transcript_text"],
                "output": "brief, detailed, key_points"
            },
            {
                "name": "speakers",
                "description": "Speaker-specific insights and analysis",
                "requirements": ["transcript_text", "speaker_diarization"],
                "output": "per_speaker_sentiment, speaking_time, patterns"
            },
            {
                "name": "key_moments",
                "description": "Important moments and highlights detection",
                "requirements": ["transcript_text"],
                "output": "timestamps, importance_scores, descriptions"
            },
            {
                "name": "action_items",
                "description": "Action items and task extraction",
                "requirements": ["transcript_text"],
                "output": "action_list, assignees, priorities"
            }
        ],
        "supported_languages": [
            "English", "Spanish", "French", "German", "Italian", 
            "Portuguese", "Russian", "Japanese", "Korean", "Chinese"
        ],
        "ai_providers": [
            {
                "name": "OpenAI GPT-3.5",
                "capabilities": ["all"],
                "cost": "API usage based"
            },
            {
                "name": "Fallback Methods",
                "capabilities": ["sentiment", "basic_summary"],
                "cost": "free"
            }
        ]
    }, "Analysis capabilities retrieved")


@router.delete("/cache/{transcript_id}")
async def clear_insights_cache(
    transcript_id: str,
    user_id: str = Depends(auth_required)
):
    """Clear cached insights for a transcript"""
    try:
        session_data = session_manager.get_session_data(user_id) or {}
        insights = session_data.get('insights', {})
        
        if transcript_id in insights:
            del insights[transcript_id]
            session_manager.set_session_data(user_id, session_data)
            
            return create_api_response(
                {"transcript_id": transcript_id},
                "Insights cache cleared successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cached insights found for this transcript"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear insights cache"
        )