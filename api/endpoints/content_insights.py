# API endpoints for content insights functionality
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from api.dependencies import get_current_user
from content_analysis.advanced_analyzer import AdvancedContentAnalyzer as ContentAnalyzer

router = APIRouter(prefix="/content-insights", tags=["content-insights"])

# Initialize content analyzer
content_analyzer = ContentAnalyzer()

class InsightsRequest(BaseModel):
    text: str
    transcription_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class InsightsExportRequest(BaseModel):
    insights: Dict[str, Any]
    transcription_id: Optional[str] = None
    format: str = "pdf"

@router.post("/analyze")
async def generate_insights(
    request: InsightsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Generate content insights from text"""
    try:
        # Perform content analysis
        insights = await content_analyzer.analyze_content_async(
            request.text,
            options=request.options
        )
        
        # Add metadata
        insights["analyzed_at"] = datetime.now().isoformat()
        insights["transcription_id"] = request.transcription_id
        
        # Store insights in background if transcription_id provided
        if request.transcription_id:
            background_tasks.add_task(
                store_insights,
                request.transcription_id,
                insights,
                current_user["id"]
            )
        
        return insights
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transcription/{transcription_id}")
async def get_transcription_insights(
    transcription_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get stored insights for a transcription"""
    try:
        # TODO: Implement database retrieval
        # For now, return mock data
        return {
            "message": "Insights retrieval not yet implemented",
            "transcription_id": transcription_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_insights(
    request: InsightsExportRequest,
    current_user: dict = Depends(get_current_user)
):
    """Export insights in various formats"""
    try:
        if request.format == "pdf":
            # Generate PDF report
            pdf_content = generate_pdf_report(request.insights)
            return pdf_content
        
        elif request.format == "json":
            return json.dumps(request.insights, indent=2)
        
        elif request.format == "markdown":
            md_content = generate_markdown_report(request.insights)
            return md_content
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_insights(
    transcription_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Compare insights across multiple transcriptions"""
    try:
        # TODO: Implement comparison logic
        return {
            "message": "Comparison feature not yet implemented",
            "transcription_ids": transcription_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def store_insights(transcription_id: str, insights: Dict[str, Any], user_id: str):
    """Store insights in database (background task)"""
    # TODO: Implement database storage
    pass

def generate_pdf_report(insights: Dict[str, Any]) -> bytes:
    """Generate PDF report from insights"""
    # TODO: Implement PDF generation using reportlab or similar
    # For now, return a placeholder
    return b"PDF report generation not yet implemented"

def generate_markdown_report(insights: Dict[str, Any]) -> str:
    """Generate markdown report from insights"""
    md = f"""# Content Insights Report

Generated: {insights.get('analyzed_at', 'N/A')}

## Executive Summary
{insights.get('summary', 'No summary available')}

## Sentiment Analysis
- Overall: {insights.get('sentiment', {}).get('overall', 'N/A')}
- Score: {insights.get('sentiment', {}).get('score', 0) * 100:.1f}%

### Sentiment Distribution
- Positive: {insights.get('sentiment', {}).get('distribution', {}).get('positive', 0)}%
- Neutral: {insights.get('sentiment', {}).get('distribution', {}).get('neutral', 0)}%
- Negative: {insights.get('sentiment', {}).get('distribution', {}).get('negative', 0)}%

## Key Topics
"""
    
    # Add topics
    for topic in insights.get('topics', []):
        md += f"\n### {topic.get('topic', 'Unknown Topic')}\n"
        md += f"- Relevance: {topic.get('relevance', 0) * 100:.0f}%\n"
        md += f"- Keywords: {', '.join(topic.get('keywords', []))}\n"
    
    # Add entities
    md += "\n## Entities Detected\n"
    entities = insights.get('entities', {})
    for entity_type, entity_list in entities.items():
        if entity_list:
            md += f"\n### {entity_type.title()}\n"
            for entity in entity_list[:10]:  # Limit to 10
                md += f"- {entity}\n"
    
    # Add recommendations
    md += "\n## Recommendations\n"
    for rec in insights.get('recommendations', []):
        md += f"- {rec}\n"
    
    return md