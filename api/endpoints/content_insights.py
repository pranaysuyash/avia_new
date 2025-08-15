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
        # Import database connection and models
        from database.connection import get_db_context
        from database.models import Transcript
        
        # Use current_user for authorization check
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        with get_db_context() as db:
            # Query transcript with insights
            transcript = db.query(Transcript).filter(
                Transcript.id == transcription_id,
                Transcript.user_id == user_id
            ).first()
            
            if not transcript:
                raise HTTPException(status_code=404, detail="Transcript not found")
            
            # Return stored insights or generate new ones if not available
            entities = transcript.entities or {}
            summary = transcript.summary or ""
            
            if entities and summary:
                return {
                    "transcription_id": transcription_id,
                    "entities": entities,
                    "summary": summary,
                    "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                    "status": "completed"
                }
            else:
                # Generate new insights if not available
                try:
                    insights = await content_analyzer.analyze_content(transcript.content)
                    
                    # Update transcript with insights
                    transcript.entities = insights.get("entities", {})
                    transcript.summary = insights.get("summary", "")
                    db.commit()
                    
                    return {
                        "transcription_id": transcription_id,
                        "entities": insights.get("entities", {}),
                        "summary": insights.get("summary", ""),
                        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                        "generated_at": datetime.now().isoformat(),
                        "status": "generated"
                    }
                except Exception as analysis_error:
                    logger.error(f"Error generating insights for transcript {transcription_id}: {analysis_error}")
                    return {
                        "transcription_id": transcription_id,
                        "entities": {},
                        "summary": "",
                        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                        "status": "error",
                        "error": str(analysis_error)
                    }
                
    except HTTPException:
        raise
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
        # Implement comparison logic using existing insights
        from database.connection import get_db_context
        from database.models import Transcript
        
        if len(transcription_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 transcription IDs required for comparison")
        
        # Get all transcripts
        transcripts = []
        with get_db_context() as db:
            for transcript_id in transcription_ids:
                transcript = db.query(Transcript).filter(
                    Transcript.id == transcript_id,
                    Transcript.user_id == current_user.get("user_id")
                ).first()
                
                if transcript:
                    transcripts.append(transcript)
        
        if len(transcripts) < 2:
            raise HTTPException(status_code=404, detail="Not enough transcripts found for comparison")
        
        # Analyze similarities and differences
        comparison_results = []
        
        # Extract key metrics for comparison
        for transcript in transcripts:
            # Generate insights if not available
            if not transcript.entities or not transcript.summary:
                insights = await content_analyzer.analyze_content(transcript.content)
                transcript.entities = insights.get("entities", {})
                transcript.summary = insights.get("summary", "")
            
            # Extract comparison metrics
            entities = transcript.entities or {}
            topics = entities.get("topics", [])
            sentiment = entities.get("sentiment", {})
            
            comparison_results.append({
                "transcription_id": transcript.id,
                "title": transcript.title,
                "word_count": transcript.word_count or len(transcript.content.split()),
                "topics_count": len(topics),
                "sentiment_score": sentiment.get("compound", 0) if isinstance(sentiment, dict) else 0,
                "entities_count": sum(len(v) for v in entities.values() if isinstance(v, list)),
                "summary_length": len(transcript.summary) if transcript.summary else 0
            })
        
        # Calculate comparison metrics
        if comparison_results:
            # Generate comparison insights
            insights = {
                "largest_transcript": max(comparison_results, key=lambda x: x["word_count"]),
                "smallest_transcript": min(comparison_results, key=lambda x: x["word_count"]),
                "most_topics": max(comparison_results, key=lambda x: x["topics_count"]),
                "least_topics": min(comparison_results, key=lambda x: x["topics_count"]),
                "most_positive": max(comparison_results, key=lambda x: x["sentiment_score"]),
                "most_negative": min(comparison_results, key=lambda x: x["sentiment_score"]),
                "most_entities": max(comparison_results, key=lambda x: x["entities_count"]),
                "least_entities": min(comparison_results, key=lambda x: x["entities_count"]),
                "longest_summary": max(comparison_results, key=lambda x: x["summary_length"]),
                "shortest_summary": min(comparison_results, key=lambda x: x["summary_length"])
            }
            
            return {
                "message": "Comparison completed successfully",
                "transcription_ids": transcription_ids,
                "comparisons": comparison_results,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
        else:
            return {
                "message": "No comparable data found",
                "transcription_ids": transcription_ids
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def store_insights(transcription_id: str, insights: Dict[str, Any], user_id: str):
    """Store insights in database (background task)"""
    try:
        # Import database connection and models
        from database.connection import get_db_context
        from database.models import Transcript
        
        with get_db_context() as db:
            # Find the transcript
            transcript = db.query(Transcript).filter(
                Transcript.id == transcription_id,
                Transcript.user_id == user_id
            ).first()
            
            if not transcript:
                logger.warning(f"Transcript {transcription_id} not found for user {user_id}")
                return False
            
            # Update transcript with insights
            transcript.entities = insights.get("entities", {})
            transcript.summary = insights.get("summary", "")
            
            # Update other insight fields if they exist
            if "sentiment" in insights:
                transcript.sentiment_analysis = insights["sentiment"]
            
            if "keywords" in insights:
                transcript.keywords = insights["keywords"]
            
            if "topics" in insights:
                transcript.topics = insights["topics"]
            
            # Commit changes
            db.commit()
            
            logger.info(f"Stored insights for transcription {transcription_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error storing insights for transcription {transcription_id}: {e}")
        return False

def generate_pdf_report(insights: Dict[str, Any]) -> bytes:
    """Generate PDF report from insights"""
    try:
        # Import reportlab for PDF generation
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        # Create a buffer to hold the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        title = Paragraph("Content Insights Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Generated timestamp
        generated_text = f"Generated: {insights.get('analyzed_at', datetime.now().isoformat())}"
        generated_para = Paragraph(generated_text, styles['Normal'])
        story.append(generated_para)
        story.append(Spacer(1, 24))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        summary_text = insights.get('summary', 'No summary available')
        summary_para = Paragraph(summary_text, styles['Normal'])
        story.append(summary_para)
        story.append(Spacer(1, 24))
        
        # Sentiment Analysis
        story.append(Paragraph("Sentiment Analysis", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        sentiment = insights.get('sentiment', {})
        if isinstance(sentiment, dict):
            sentiment_data = [
                ['Metric', 'Value'],
                ['Overall Sentiment', sentiment.get('overall', 'N/A')],
                ['Score', f"{sentiment.get('score', 0) * 100:.1f}%"],
                ['Positive', f"{sentiment.get('distribution', {}).get('positive', 0)}%"],
                ['Neutral', f"{sentiment.get('distribution', {}).get('neutral', 0)}%"],
                ['Negative', f"{sentiment.get('distribution', {}).get('negative', 0)}%"]
            ]
            
            # Create sentiment table
            sentiment_table = Table(sentiment_data)
            sentiment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(sentiment_table)
            story.append(Spacer(1, 24))
        
        # Key Topics
        story.append(Paragraph("Key Topics", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        topics = insights.get('topics', [])
        if topics:
            for i, topic in enumerate(topics[:10]):  # Limit to top 10 topics
                topic_text = f"<b>{topic.get('topic', f'Topic {i+1}')}</b><br/>"
                topic_text += f"Relevance: {topic.get('relevance', 0) * 100:.0f}%<br/>"
                topic_text += f"Keywords: {', '.join(topic.get('keywords', []))}<br/>"
                topic_para = Paragraph(topic_text, styles['Normal'])
                story.append(topic_para)
                story.append(Spacer(1, 12))
        else:
            story.append(Paragraph("No topics identified", styles['Normal']))
            story.append(Spacer(1, 24))
        
        # Entities
        story.append(Paragraph("Entities Detected", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        entities = insights.get('entities', {})
        if entities:
            for entity_type, entity_list in entities.items():
                if entity_list:
                    story.append(Paragraph(f"<b>{entity_type.title()}</b>", styles['Heading3']))
                    entity_text = ", ".join(str(entity) for entity in entity_list[:20])  # Limit to 20 entities
                    entity_para = Paragraph(entity_text, styles['Normal'])
                    story.append(entity_para)
                    story.append(Spacer(1, 12))
        else:
            story.append(Paragraph("No entities detected", styles['Normal']))
            story.append(Spacer(1, 24))
        
        # Recommendations
        story.append(Paragraph("Recommendations", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        recommendations = insights.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                rec_para = Paragraph(f"• {rec}", styles['Normal'])
                story.append(rec_para)
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No recommendations available", styles['Normal']))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        # Return a simple PDF with error message
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        _, height = letter  # Only need height for positioning
        c.drawString(100, height - 100, "Content Insights Report")
        c.drawString(100, height - 120, f"Error: {str(e)}")
        c.drawString(100, height - 140, "PDF generation failed. Please try again.")
        c.save()
        
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content

def generate_markdown_report(insights: Dict[str, Any]) -> str:
    """Generate markdown report from insights"""
    try:
        # Create markdown report
        md = f"""# Content Insights Report

Generated: {insights.get('analyzed_at', datetime.now().isoformat())}

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
        topics = insights.get('topics', [])
        if topics:
            for topic in topics[:10]:  # Limit to top 10 topics
                md += f"\n### {topic.get('topic', 'Unknown Topic')}\n"
                md += f"- Relevance: {topic.get('relevance', 0) * 100:.0f}%\n"
                md += f"- Keywords: {', '.join(topic.get('keywords', []))}\n"
        else:
            md += "\nNo topics identified\n"
        
        # Add entities
        md += "\n## Entities Detected\n"
        entities = insights.get('entities', {})
        if entities:
            for entity_type, entity_list in entities.items():
                if entity_list:
                    md += f"\n### {entity_type.title()}\n"
                    for entity in entity_list[:20]:  # Limit to 20 entities
                        md += f"- {entity}\n"
        else:
            md += "\nNo entities detected\n"
        
        # Add recommendations
        md += "\n## Recommendations\n"
        recommendations = insights.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                md += f"- {rec}\n"
        else:
            md += "No recommendations available\n"
        
        return md
        
    except Exception as e:
        logger.error(f"Error generating markdown report: {e}")
        return f"# Content Insights Report\n\nError generating report: {str(e)}\n\nPlease try again."

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