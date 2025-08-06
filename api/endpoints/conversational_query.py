"""
Conversational Query Bot API Endpoints
FastAPI endpoints for conversational querying of media libraries
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from ...conversational_query_bot import (
    ConversationalQueryBot, MediaContent, QueryResult, 
    ConversationContext
)
from ..auth import get_current_user
from ..models import User
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/query", tags=["conversational-query"])

# Pydantic models
class MediaContentInput(BaseModel):
    title: str
    content_type: str = Field(..., pattern="^(transcript|document|image_text|video)$")
    text_content: str
    timestamp: Optional[float] = None
    speaker: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    max_results: int = Field(default=5, ge=1, le=20)
    include_context: bool = True
    filters: Optional[Dict[str, Any]] = {}

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    answer: Optional[str] = None
    conversation_id: str
    processing_time: float

class BatchQueryRequest(BaseModel):
    queries: List[str]
    conversation_id: Optional[str] = None
    max_results_per_query: int = Field(default=3, ge=1, le=10)

class ContentUpdateRequest(BaseModel):
    content_id: str
    updates: Dict[str, Any]

class ConversationExportRequest(BaseModel):
    conversation_id: str
    format: str = Field(default="json", pattern="^(json|markdown|pdf)$")
    include_sources: bool = True

# Initialize query bot
query_bot = ConversationalQueryBot()

@router.post("/query")
async def query_content(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query the media library using natural language"""
    try:
        start_time = datetime.now()
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Perform query
        results = query_bot.query(
            request.query,
            conversation_id=conversation_id,
            max_results=request.max_results
        )
        
        # Generate answer if requested
        answer = None
        if results and request.include_context:
            answer = query_bot.generate_answer(request.query, results)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Convert results to dict format
        results_dict = []
        for result in results:
            result_dict = {
                "content": {
                    "id": result.content.id,
                    "title": result.content.title,
                    "content_type": result.content.content_type,
                    "snippet": result.snippet,
                    "speaker": result.content.speaker,
                    "timestamp": result.content.timestamp
                },
                "relevance_score": result.relevance_score,
                "timestamp_citation": result.timestamp_citation,
                "context_window": result.context_window
            }
            results_dict.append(result_dict)
        
        return QueryResponse(
            results=results_dict,
            answer=answer,
            conversation_id=conversation_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-query")
async def batch_query(
    request: BatchQueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process multiple queries in batch"""
    try:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        
        # Process queries in background
        background_tasks.add_task(
            process_batch_queries,
            batch_id,
            request.queries,
            conversation_id,
            request.max_results_per_query,
            current_user.id
        )
        
        return {
            "batch_id": batch_id,
            "conversation_id": conversation_id,
            "status": "processing",
            "query_count": len(request.queries)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-content")
async def add_content(
    content: MediaContentInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add new content to the searchable index"""
    try:
        # Create MediaContent object
        media_content = MediaContent(
            id=str(uuid.uuid4()),
            title=content.title,
            content_type=content.content_type,
            text_content=content.text_content,
            timestamp=content.timestamp,
            speaker=content.speaker,
            file_path=content.file_path,
            metadata=content.metadata
        )
        
        # Add to index
        query_bot.add_content(media_content)
        
        return {
            "status": "success",
            "content_id": media_content.id,
            "message": "Content added to index successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-add-content")
async def bulk_add_content(
    contents: List[MediaContentInput],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add multiple content items in bulk"""
    try:
        batch_id = str(uuid.uuid4())
        
        # Process in background
        background_tasks.add_task(
            process_bulk_content,
            batch_id,
            contents,
            current_user.id
        )
        
        return {
            "batch_id": batch_id,
            "status": "processing",
            "content_count": len(contents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update-content")
async def update_content(
    request: ContentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update existing content in the index"""
    try:
        # Update content
        success = query_bot.update_content(request.content_id, request.updates)
        
        if success:
            return {
                "status": "success",
                "content_id": request.content_id,
                "message": "Content updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Content not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove-content/{content_id}")
async def remove_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove content from the index"""
    try:
        # Remove content
        success = query_bot.remove_content(content_id)
        
        if success:
            return {
                "status": "success",
                "content_id": content_id,
                "message": "Content removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Content not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    try:
        # Get conversation
        conversation = query_bot.get_conversation(conversation_id)
        
        if conversation:
            return {
                "conversation_id": conversation.conversation_id,
                "query_history": conversation.query_history,
                "created_at": conversation.created_at,
                "query_count": len(conversation.query_history)
            }
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-conversation")
async def export_conversation(
    request: ConversationExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export conversation history"""
    try:
        # Get conversation
        conversation = query_bot.get_conversation(request.conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Export based on format
        if request.format == "json":
            return {
                "conversation_id": conversation.conversation_id,
                "queries": conversation.query_history,
                "created_at": conversation.created_at,
                "export_date": datetime.now()
            }
        elif request.format == "markdown":
            # Generate markdown
            markdown = generate_conversation_markdown(conversation, request.include_sources)
            return {"content": markdown, "format": "markdown"}
        elif request.format == "pdf":
            # Generate PDF URL
            pdf_url = generate_conversation_pdf(conversation, request.include_sources)
            return {"download_url": pdf_url, "format": "pdf"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get query system statistics"""
    try:
        stats = query_bot.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear conversation history"""
    try:
        success = query_bot.clear_conversation(conversation_id)
        
        if success:
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "message": "Conversation cleared"
            }
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-suggestions")
async def get_search_suggestions(
    query: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on partial query"""
    try:
        suggestions = query_bot.get_search_suggestions(query, limit)
        
        return {
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def process_batch_queries(batch_id: str, queries: List[str], 
                               conversation_id: str, max_results: int, user_id: int):
    """Process batch queries in background"""
    # Implementation for batch processing
    pass

async def process_bulk_content(batch_id: str, contents: List[MediaContentInput], user_id: int):
    """Process bulk content addition in background"""
    # Implementation for bulk content processing
    pass

def generate_conversation_markdown(conversation: ConversationContext, include_sources: bool) -> str:
    """Generate markdown export of conversation"""
    markdown = f"# Conversation Export\n\n"
    markdown += f"**ID:** {conversation.conversation_id}\n"
    markdown += f"**Created:** {conversation.created_at}\n\n"
    
    for i, query in enumerate(conversation.query_history):
        markdown += f"## Query {i+1}: {query}\n\n"
        # Add results if available
        if i < len(conversation.result_history):
            for j, result in enumerate(conversation.result_history[i][:3]):
                markdown += f"### Result {j+1}\n"
                markdown += f"- **Title:** {result.content.title}\n"
                markdown += f"- **Relevance:** {result.relevance_score:.2f}\n"
                markdown += f"- **Snippet:** {result.snippet}\n\n"
    
    return markdown

def generate_conversation_pdf(conversation: ConversationContext, include_sources: bool) -> str:
    """Generate PDF export of conversation"""
    # Implementation for PDF generation
    # Return URL to generated PDF
    return f"/api/query/download/conversation_{conversation.conversation_id}.pdf"