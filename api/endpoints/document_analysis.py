"""
Document Analysis API Endpoints
Provides REST API interface for the Document Analysis System
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import base64
import io
import logging
import os
import sys
import json
import uuid
from datetime import datetime
import tempfile
from pathlib import Path
import mimetypes

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from api.middleware.audit_logging import audit_log
from database.connection import get_db
from sqlalchemy.orm import Session

# Import the document analysis system
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from document_analysis_system import DocumentAnalysisSystem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/document-analysis")

# Global system instance
analysis_system = DocumentAnalysisSystem()

# In-memory task storage (replace with database in production)
analysis_tasks = {}

# Pydantic models
class AnalysisConfig(BaseModel):
    enable_ocr: bool = Field(True, description="Enable OCR for text extraction")
    enable_nlp: bool = Field(True, description="Enable NLP analysis")
    enable_entity_extraction: bool = Field(True, description="Enable entity extraction")
    enable_summarization: bool = Field(True, description="Enable document summarization")
    enable_sentiment_analysis: bool = Field(True, description="Enable sentiment analysis")
    enable_key_phrases: bool = Field(True, description="Enable key phrase extraction")
    enable_language_detection: bool = Field(True, description="Enable language detection")
    max_pages: Optional[int] = Field(None, description="Maximum pages to analyze")
    languages: List[str] = Field(default_factory=lambda: ["en"], description="Target languages for analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_ocr": True,
                "enable_nlp": True,
                "enable_entity_extraction": True,
                "enable_summarization": True,
                "enable_sentiment_analysis": True,
                "enable_key_phrases": True,
                "enable_language_detection": True,
                "max_pages": 50,
                "languages": ["en", "es", "fr"]
            }
        }

class DocumentAnalysisRequest(BaseModel):
    document_data: Optional[str] = Field(None, description="Base64 encoded document data")
    document_url: Optional[str] = Field(None, description="URL to document")
    analysis_config: AnalysisConfig = Field(default_factory=AnalysisConfig)
    output_format: str = Field("json", description="Output format: json, pdf, docx")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for completion notification")

class DocumentMetadata(BaseModel):
    filename: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    author: Optional[str] = None
    title: Optional[str] = None

class AnalysisResults(BaseModel):
    task_id: str
    status: str
    metadata: Optional[DocumentMetadata] = None
    text_content: Optional[str] = None
    summary: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    key_phrases: Optional[List[str]] = None
    sentiment: Optional[Dict[str, float]] = None
    language: Optional[str] = None
    topics: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None
    processing_time: Optional[float] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

class BatchAnalysisRequest(BaseModel):
    documents: List[Dict[str, str]] = Field(..., description="List of documents with data or URLs")
    analysis_config: AnalysisConfig = Field(default_factory=AnalysisConfig)
    output_format: str = Field("json")

class AnalysisStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    result: Optional[AnalysisResults] = None

@router.post("/analyze", response_model=AnalysisResults)
async def analyze_document(
    request: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("document_analysis"))
):
    """
    Analyze a document with advanced NLP and extraction capabilities
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Validate input
        if not request.document_data and not request.document_url:
            raise HTTPException(status_code=400, detail="Either document_data or document_url must be provided")
        
        # Initialize task
        analysis_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "user_id": current_user.get("user_id") if current_user else "anonymous",
            "config": request.analysis_config.dict()
        }
        
        # Start background processing
        background_tasks.add_task(
            process_document_analysis,
            task_id,
            request.document_data,
            request.document_url,
            request.analysis_config,
            request.output_format,
            request.webhook_url
        )
        
        # Track API usage
        await track_api_call("document_analysis", current_user)
        
        # Audit log
        await audit_log(
            user_id=current_user.get("user_id") if current_user else None,
            action="document_analysis_initiated",
            details={"task_id": task_id, "config": request.analysis_config.dict()}
        )
        
        return AnalysisResults(
            task_id=task_id,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/upload")
async def analyze_document_upload(
    file: UploadFile = File(...),
    analysis_config: str = Query("{}"),
    output_format: str = Query("json"),
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("document_analysis"))
):
    """
    Analyze an uploaded document file
    """
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "text/html",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        # Read file
        document_data = await file.read()
        if len(document_data) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")
        
        # Convert to base64
        document_base64 = base64.b64encode(document_data).decode('utf-8')
        
        # Parse config
        try:
            config_dict = json.loads(analysis_config) if analysis_config else {}
            config = AnalysisConfig(**config_dict)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in analysis_config")
        
        # Create request
        request = DocumentAnalysisRequest(
            document_data=document_base64,
            analysis_config=config,
            output_format=output_format
        )
        
        # Store metadata
        analysis_tasks[task_id] = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(document_data)
        }
        
        return await analyze_document(request, background_tasks, current_user, quota_check)
        
    except Exception as e:
        logger.error(f"File upload analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=Dict[str, Any])
async def batch_analyze_documents(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("batch_document_analysis"))
):
    """
    Analyze multiple documents in batch
    """
    try:
        if len(request.documents) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large. Maximum 10 documents.")
        
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # Process each document
        for i, doc in enumerate(request.documents):
            task_id = f"{batch_id}_doc_{i:03d}"
            task_ids.append(task_id)
            
            # Initialize task
            analysis_tasks[task_id] = {
                "status": "processing",
                "started_at": datetime.now().isoformat(),
                "batch_id": batch_id,
                "user_id": current_user.get("user_id") if current_user else "anonymous"
            }
            
            # Start processing
            background_tasks.add_task(
                process_document_analysis,
                task_id,
                doc.get("document_data"),
                doc.get("document_url"),
                request.analysis_config,
                request.output_format,
                None
            )
        
        await track_api_call("batch_document_analysis", current_user)
        
        return {
            "batch_id": batch_id,
            "task_ids": task_ids,
            "status": "processing",
            "total_documents": len(task_ids)
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of a document analysis task
    """
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    response = AnalysisStatusResponse(
        task_id=task_id,
        status=task.get("status"),
        progress=task.get("progress"),
        message=task.get("message")
    )
    
    # Include results if completed
    if task.get("status") == "completed":
        response.result = AnalysisResults(
            task_id=task_id,
            status="completed",
            metadata=task.get("metadata"),
            text_content=task.get("text_content"),
            summary=task.get("summary"),
            entities=task.get("entities"),
            key_phrases=task.get("key_phrases"),
            sentiment=task.get("sentiment"),
            language=task.get("language"),
            topics=task.get("topics"),
            tables=task.get("tables"),
            images=task.get("images"),
            processing_time=task.get("processing_time"),
            timestamp=task.get("timestamp")
        )
    
    return response

@router.get("/report/{task_id}")
async def get_analysis_report(
    task_id: str,
    format: str = Query("json", description="Report format: json, pdf, html"),
    current_user=Depends(get_current_user)
):
    """
    Get formatted analysis report
    """
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    if format == "json":
        return {
            "format": "json",
            "report": {
                "metadata": task.get("metadata"),
                "summary": task.get("summary"),
                "entities": task.get("entities"),
                "key_phrases": task.get("key_phrases"),
                "sentiment": task.get("sentiment"),
                "language": task.get("language"),
                "topics": task.get("topics"),
                "statistics": {
                    "total_entities": len(task.get("entities", [])),
                    "total_key_phrases": len(task.get("key_phrases", [])),
                    "total_topics": len(task.get("topics", [])),
                    "processing_time": task.get("processing_time")
                }
            }
        }
    elif format == "html":
        # Generate HTML report
        html_content = generate_html_report(task)
        return {
            "format": "html",
            "content": html_content
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

@router.post("/export/{task_id}")
async def export_analysis(
    task_id: str,
    export_format: str = Query("json", description="Export format: json, csv, xlsx"),
    include_sections: List[str] = Query(
        default=["all"],
        description="Sections to include: summary, entities, sentiment, etc."
    ),
    current_user=Depends(get_current_user)
):
    """
    Export analysis results in various formats
    """
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    # Prepare export data
    export_data = {}
    
    if "all" in include_sections or "metadata" in include_sections:
        export_data["metadata"] = task.get("metadata")
    
    if "all" in include_sections or "summary" in include_sections:
        export_data["summary"] = task.get("summary")
    
    if "all" in include_sections or "entities" in include_sections:
        export_data["entities"] = task.get("entities")
    
    if "all" in include_sections or "sentiment" in include_sections:
        export_data["sentiment"] = task.get("sentiment")
    
    if "all" in include_sections or "key_phrases" in include_sections:
        export_data["key_phrases"] = task.get("key_phrases")
    
    # Format export
    if export_format == "json":
        return {
            "format": "json",
            "data": export_data,
            "filename": f"analysis_{task_id}.json"
        }
    elif export_format == "csv":
        # Convert to CSV format
        csv_data = convert_to_csv(export_data)
        return {
            "format": "csv",
            "data": csv_data,
            "filename": f"analysis_{task_id}.csv"
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {export_format}")

@router.get("/batch/status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of a batch analysis job
    """
    batch_tasks = {k: v for k, v in analysis_tasks.items() 
                   if v.get("batch_id") == batch_id}
    
    if not batch_tasks:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    total = len(batch_tasks)
    completed = sum(1 for task in batch_tasks.values() if task["status"] == "completed")
    failed = sum(1 for task in batch_tasks.values() if task["status"] == "failed")
    processing = total - completed - failed
    
    return {
        "batch_id": batch_id,
        "total": total,
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "progress": completed / total * 100 if total > 0 else 0,
        "tasks": {task_id: task["status"] for task_id, task in batch_tasks.items()}
    }

@router.get("/templates")
async def get_analysis_templates(
    current_user=Depends(get_current_user)
):
    """
    Get available analysis templates
    """
    templates = [
        {
            "id": "legal_contract",
            "name": "Legal Contract Analysis",
            "description": "Analyze legal contracts for key terms, obligations, and risks",
            "config": {
                "enable_entity_extraction": True,
                "enable_key_phrases": True,
                "enable_summarization": True,
                "entity_types": ["organization", "person", "date", "money", "location"]
            }
        },
        {
            "id": "research_paper",
            "name": "Research Paper Analysis",
            "description": "Extract key findings, methodology, and citations from research papers",
            "config": {
                "enable_summarization": True,
                "enable_key_phrases": True,
                "enable_entity_extraction": True,
                "enable_sentiment_analysis": False
            }
        },
        {
            "id": "financial_report",
            "name": "Financial Report Analysis",
            "description": "Analyze financial reports for key metrics and insights",
            "config": {
                "enable_entity_extraction": True,
                "enable_tables": True,
                "enable_sentiment_analysis": True,
                "entity_types": ["money", "percentage", "organization", "date"]
            }
        },
        {
            "id": "resume",
            "name": "Resume Analysis",
            "description": "Extract skills, experience, and qualifications from resumes",
            "config": {
                "enable_entity_extraction": True,
                "enable_key_phrases": True,
                "entity_types": ["person", "organization", "skill", "education", "date"]
            }
        }
    ]
    
    return {"templates": templates}

@router.delete("/task/{task_id}")
async def delete_task(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Delete a task and its results
    """
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check ownership
    task = analysis_tasks[task_id]
    if task.get("user_id") != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    
    del analysis_tasks[task_id]
    
    return {"message": "Task deleted successfully"}

@router.get("/stats")
async def get_analysis_stats(
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    current_user=Depends(get_current_user)
):
    """
    Get document analysis statistics
    """
    from datetime import timedelta
    
    # Calculate time cutoff
    now = datetime.now()
    if time_range == "1h":
        cutoff = now - timedelta(hours=1)
    elif time_range == "24h":
        cutoff = now - timedelta(days=1)
    elif time_range == "7d":
        cutoff = now - timedelta(days=7)
    elif time_range == "30d":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = now - timedelta(days=1)
    
    # Filter tasks by time and user
    user_tasks = [
        task for task in analysis_tasks.values()
        if task.get("user_id") == current_user.get("user_id") and
           datetime.fromisoformat(task.get("started_at", "2000-01-01")) > cutoff
    ]
    
    # Calculate statistics
    total_tasks = len(user_tasks)
    completed_tasks = sum(1 for task in user_tasks if task.get("status") == "completed")
    failed_tasks = sum(1 for task in user_tasks if task.get("status") == "failed")
    
    # Document type statistics
    doc_types = {}
    total_pages = 0
    total_entities = 0
    
    for task in user_tasks:
        if task.get("status") == "completed":
            metadata = task.get("metadata", {})
            doc_type = metadata.get("file_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            total_pages += metadata.get("page_count", 0)
            total_entities += len(task.get("entities", []))
    
    avg_processing_time = sum(task.get("processing_time", 0) for task in user_tasks if task.get("status") == "completed") / completed_tasks if completed_tasks > 0 else 0
    
    return {
        "time_range": time_range,
        "total_documents": total_tasks,
        "completed_documents": completed_tasks,
        "failed_documents": failed_tasks,
        "success_rate": completed_tasks / total_tasks * 100 if total_tasks > 0 else 0,
        "total_pages_analyzed": total_pages,
        "total_entities_extracted": total_entities,
        "average_processing_time": round(avg_processing_time, 2),
        "document_types": doc_types,
        "timestamp": datetime.now().isoformat()
    }

# Background processing function
async def process_document_analysis(
    task_id: str,
    document_data: Optional[str],
    document_url: Optional[str],
    config: AnalysisConfig,
    output_format: str,
    webhook_url: Optional[str]
):
    """
    Background task for document analysis processing
    """
    try:
        # Update task status
        analysis_tasks[task_id]["status"] = "processing"
        analysis_tasks[task_id]["progress"] = 0.1
        
        # Get document data
        if document_data:
            # Decode base64
            doc_bytes = base64.b64decode(document_data)
        elif document_url:
            # Download from URL
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(document_url) as response:
                    doc_bytes = await response.read()
        else:
            raise ValueError("No document data provided")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(doc_bytes)
            tmp_path = tmp_file.name
        
        # Update progress
        analysis_tasks[task_id]["progress"] = 0.3
        
        # Perform analysis
        start_time = datetime.now()
        results = analysis_system.analyze_document(tmp_path, config.dict())
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Update progress
        analysis_tasks[task_id]["progress"] = 0.8
        
        # Process results
        metadata = DocumentMetadata(
            filename=analysis_tasks[task_id].get("filename", "document"),
            file_type=analysis_tasks[task_id].get("content_type", "unknown"),
            file_size=len(doc_bytes),
            page_count=results.get("page_count"),
            creation_date=results.get("creation_date"),
            modification_date=results.get("modification_date"),
            author=results.get("author"),
            title=results.get("title")
        )
        
        # Update task with results
        analysis_tasks[task_id].update({
            "status": "completed",
            "progress": 1.0,
            "metadata": metadata.dict(),
            "text_content": results.get("text_content"),
            "summary": results.get("summary"),
            "entities": results.get("entities", []),
            "key_phrases": results.get("key_phrases", []),
            "sentiment": results.get("sentiment"),
            "language": results.get("language"),
            "topics": results.get("topics", []),
            "tables": results.get("tables", []),
            "images": results.get("images", []),
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        })
        
        # Clean up
        os.unlink(tmp_path)
        
        # Send webhook notification if provided
        if webhook_url:
            await send_webhook_notification(webhook_url, task_id, "completed")
        
    except Exception as e:
        # Update task with error
        analysis_tasks[task_id].update({
            "status": "failed",
            "progress": 0,
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })
        logger.error(f"Document analysis failed for task {task_id}: {e}")
        
        # Send webhook notification if provided
        if webhook_url:
            await send_webhook_notification(webhook_url, task_id, "failed", str(e))

async def send_webhook_notification(webhook_url: str, task_id: str, status: str, error: str = None):
    """
    Send webhook notification
    """
    try:
        import aiohttp
        payload = {
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        if error:
            payload["error"] = error
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=payload)
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {e}")

def generate_html_report(task_data: Dict[str, Any]) -> str:
    """
    Generate HTML report
    """
    # Simple HTML template
    html = f"""
    <html>
    <head>
        <title>Document Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            .metadata {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
            .entity {{ display: inline-block; background: #e3f2fd; padding: 5px 10px; margin: 5px; border-radius: 3px; }}
            .sentiment {{ font-weight: bold; }}
            .positive {{ color: green; }}
            .negative {{ color: red; }}
            .neutral {{ color: gray; }}
        </style>
    </head>
    <body>
        <h1>Document Analysis Report</h1>
        
        <div class="section metadata">
            <h2>Document Metadata</h2>
            <p><strong>Filename:</strong> {task_data['metadata']['filename']}</p>
            <p><strong>Type:</strong> {task_data['metadata']['file_type']}</p>
            <p><strong>Pages:</strong> {task_data['metadata'].get('page_count', 'N/A')}</p>
            <p><strong>Language:</strong> {task_data.get('language', 'Unknown')}</p>
        </div>
        
        <div class="section">
            <h2>Summary</h2>
            <p>{task_data.get('summary', 'No summary available')}</p>
        </div>
        
        <div class="section">
            <h2>Key Phrases</h2>
            {' '.join(f'<span class="entity">{phrase}</span>' for phrase in task_data.get('key_phrases', []))}
        </div>
        
        <div class="section">
            <h2>Entities</h2>
            {' '.join(f'<span class="entity">{entity["text"]} ({entity["type"]})</span>' for entity in task_data.get('entities', []))}
        </div>
        
        <div class="section">
            <h2>Sentiment Analysis</h2>
            <p class="sentiment {get_sentiment_class(task_data.get('sentiment', {}))}">
                {format_sentiment(task_data.get('sentiment', {}))}
            </p>
        </div>
    </body>
    </html>
    """
    return html

def get_sentiment_class(sentiment: Dict[str, float]) -> str:
    """Get CSS class for sentiment"""
    if not sentiment:
        return "neutral"
    
    max_sentiment = max(sentiment.items(), key=lambda x: x[1])
    return max_sentiment[0].lower()

def format_sentiment(sentiment: Dict[str, float]) -> str:
    """Format sentiment for display"""
    if not sentiment:
        return "No sentiment data"
    
    return ", ".join(f"{k}: {v:.2%}" for k, v in sentiment.items())

def convert_to_csv(data: Dict[str, Any]) -> str:
    """Convert analysis data to CSV format"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write entities
    if "entities" in data and data["entities"]:
        writer.writerow(["Entity Type", "Entity Text", "Confidence"])
        for entity in data["entities"]:
            writer.writerow([entity.get("type"), entity.get("text"), entity.get("confidence", "")])
        writer.writerow([])
    
    # Write key phrases
    if "key_phrases" in data and data["key_phrases"]:
        writer.writerow(["Key Phrases"])
        for phrase in data["key_phrases"]:
            writer.writerow([phrase])
    
    return output.getvalue()

@router.get("/health")
async def health_check():
    """
    Health check for document analysis service
    """
    return {
        "status": "healthy",
        "service": "document_analysis",
        "active_tasks": len([t for t in analysis_tasks.values() if t["status"] == "processing"]),
        "total_tasks": len(analysis_tasks),
        "timestamp": datetime.now().isoformat()
    }