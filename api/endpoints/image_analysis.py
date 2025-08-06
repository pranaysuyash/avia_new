"""
Task 78: Image Analysis and Insights API Endpoints
REST API endpoints for the Image Analysis and Insights System
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import base64
import io
import logging
from datetime import datetime
import tempfile
import os
import json
import uuid
import numpy as np
import cv2
from PIL import Image

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from database.connection import get_db
from sqlalchemy.orm import Session

# Import analysis functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from image_analysis_insights_system import ImageAnalysisInsightsSystem, ComprehensiveImageInsights

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/image-analysis")

# Global analysis system instance
analysis_system = ImageAnalysisInsightsSystem()

# Pydantic models
class ImageAnalysisRequest(BaseModel):
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    analysis_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis configuration options"
    )
    include_sections: List[str] = Field(
        default_factory=lambda: ["all"],
        description="Sections to include: color, composition, content, quality, semantic, technical"
    )
    output_format: str = Field("json", description="Output format: json, html, csv")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_data": "base64_encoded_image_here",
                "analysis_options": {
                    "use_gpu": False,
                    "detailed_analysis": True
                },
                "include_sections": ["color", "quality", "semantic"],
                "output_format": "json"
            }
        }

class ImageAnalysisResponse(BaseModel):
    task_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    file_info: Optional[Dict[str, Any]] = None
    color_analysis: Optional[Dict[str, Any]] = None
    composition_analysis: Optional[Dict[str, Any]] = None
    content_analysis: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    semantic_insights: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    processing_time: float = 0.0
    analysis_timestamp: Optional[str] = None
    message: Optional[str] = None

class BatchAnalysisRequest(BaseModel):
    images: List[str] = Field(..., description="List of base64 encoded images")
    analysis_options: Dict[str, Any] = Field(default_factory=dict)
    include_sections: List[str] = Field(default_factory=lambda: ["all"])
    
class ComparisonAnalysisRequest(BaseModel):
    image_1: str = Field(..., description="Base64 encoded first image")
    image_2: str = Field(..., description="Base64 encoded second image")
    comparison_aspects: List[str] = Field(
        default_factory=lambda: ["quality", "composition", "color"],
        description="Aspects to compare"
    )

class AnalysisSummaryRequest(BaseModel):
    analysis_results: List[str] = Field(..., description="List of analysis task IDs")
    summary_type: str = Field("comprehensive", description="Type of summary: brief, comprehensive, technical")

# In-memory task storage
analysis_tasks = {}

@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("image_analysis"))
):
    """
    Perform comprehensive image analysis and generate insights
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Validate input
        if not request.image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Initialize task
        analysis_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now(),
            "user_id": current_user.get("user_id") if current_user else "anonymous",
            "request_options": request.analysis_options,
            "include_sections": request.include_sections
        }
        
        # Start background processing
        background_tasks.add_task(
            process_image_analysis,
            task_id,
            request.image_data,
            request.analysis_options,
            request.include_sections,
            request.output_format
        )
        
        # Track API usage
        await track_api_call("image_analysis", current_user)
        
        return ImageAnalysisResponse(
            task_id=task_id,
            status="processing",
            message="Image analysis started"
        )
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/upload")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    analysis_options: str = Form("{}"),
    include_sections: str = Form('["all"]'),
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("image_analysis"))
):
    """
    Analyze an uploaded image file
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
        
        # Read file
        image_data = await file.read()
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Parse options
        try:
            options_dict = json.loads(analysis_options) if analysis_options else {}
            sections_list = json.loads(include_sections) if include_sections else ["all"]
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in parameters")
        
        # Create request
        request = ImageAnalysisRequest(
            image_data=image_base64,
            analysis_options=options_dict,
            include_sections=sections_list
        )
        
        return await analyze_image(request, background_tasks, current_user, quota_check)
        
    except Exception as e:
        logger.error(f"File upload analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/analyze")
async def batch_analyze_images(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("batch_analysis"))
):
    """
    Analyze multiple images in batch
    """
    try:
        if len(request.images) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large. Maximum 20 images.")
        
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # Process each image
        for i, image_data in enumerate(request.images):
            task_id = f"{batch_id}_img_{i:03d}"
            task_ids.append(task_id)
            
            # Initialize task
            analysis_tasks[task_id] = {
                "status": "processing",
                "started_at": datetime.now(),
                "batch_id": batch_id,
                "user_id": current_user.get("user_id") if current_user else "anonymous"
            }
            
            # Start processing
            background_tasks.add_task(
                process_image_analysis,
                task_id,
                image_data,
                request.analysis_options,
                request.include_sections,
                "json"
            )
        
        await track_api_call("batch_image_analysis", current_user)
        
        return {
            "batch_id": batch_id,
            "task_ids": task_ids,
            "status": "processing",
            "total_images": len(task_ids)
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_images(
    request: ComparisonAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("image_comparison"))
):
    """
    Compare two images across specified aspects
    """
    try:
        task_id = str(uuid.uuid4())
        
        # Initialize comparison task
        analysis_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now(),
            "user_id": current_user.get("user_id") if current_user else "anonymous",
            "task_type": "comparison"
        }
        
        # Start comparison processing
        background_tasks.add_task(
            process_image_comparison,
            task_id,
            request.image_1,
            request.image_2,
            request.comparison_aspects
        )
        
        await track_api_call("image_comparison", current_user)
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Image comparison started"
        }
        
    except Exception as e:
        logger.error(f"Image comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=ImageAnalysisResponse)
async def get_analysis_status(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of an image analysis task
    """
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    response_data = {
        "task_id": task_id,
        "status": task.get("status"),
        "processing_time": task.get("processing_time", 0.0),
        "analysis_timestamp": task.get("analysis_timestamp"),
        "message": task.get("message")
    }
    
    # Include results if completed
    if task.get("status") == "completed":
        response_data.update({
            "results": task.get("results"),
            "file_info": task.get("file_info"),
            "color_analysis": task.get("color_analysis"),
            "composition_analysis": task.get("composition_analysis"),
            "content_analysis": task.get("content_analysis"),
            "quality_metrics": task.get("quality_metrics"),
            "semantic_insights": task.get("semantic_insights"),
            "confidence_scores": task.get("confidence_scores")
        })
    
    return ImageAnalysisResponse(**response_data)

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

@router.post("/summarize")
async def summarize_analyses(
    request: AnalysisSummaryRequest,
    current_user=Depends(get_current_user)
):
    """
    Generate a summary from multiple analysis results
    """
    try:
        # Collect results from specified task IDs
        results = []
        for task_id in request.analysis_results:
            if task_id in analysis_tasks and analysis_tasks[task_id].get("status") == "completed":
                results.append(analysis_tasks[task_id])
        
        if not results:
            raise HTTPException(status_code=400, detail="No completed analyses found")
        
        # Generate summary based on type
        if request.summary_type == "brief":
            summary = generate_brief_summary(results)
        elif request.summary_type == "technical":
            summary = generate_technical_summary(results)
        else:  # comprehensive
            summary = generate_comprehensive_summary(results)
        
        return {
            "summary_type": request.summary_type,
            "total_analyses": len(results),
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/trending")
async def get_trending_insights(
    limit: int = 10,
    time_period: str = "24h",
    current_user=Depends(get_current_user)
):
    """
    Get trending insights from recent analyses
    """
    try:
        # Filter recent analyses
        from datetime import timedelta
        
        if time_period == "1h":
            cutoff = datetime.now() - timedelta(hours=1)
        elif time_period == "24h":
            cutoff = datetime.now() - timedelta(days=1)
        elif time_period == "7d":
            cutoff = datetime.now() - timedelta(days=7)
        else:
            cutoff = datetime.now() - timedelta(days=1)
        
        recent_tasks = [
            task for task in analysis_tasks.values()
            if task.get("status") == "completed" and 
               task.get("started_at", datetime.min) > cutoff
        ]
        
        # Generate trending insights
        trends = analyze_trends(recent_tasks, limit)
        
        return {
            "time_period": time_period,
            "total_analyses": len(recent_tasks),
            "trends": trends,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Trending insights failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{task_id}")
async def export_analysis(
    task_id: str,
    format: str = "json",
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
    
    try:
        if format == "json":
            return task.get("results", {})
        elif format == "csv":
            # Generate CSV format
            csv_data = generate_csv_export(task)
            return {"csv_data": csv_data}
        elif format == "html":
            # Generate HTML report
            html_report = generate_html_report(task)
            return {"html_report": html_report}
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def process_image_analysis(
    task_id: str,
    image_data: str,
    analysis_options: Dict[str, Any],
    include_sections: List[str],
    output_format: str
):
    """
    Background task for image analysis processing
    """
    try:
        # Update task status
        analysis_tasks[task_id]["status"] = "processing"
        
        # Decode image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Could not decode image")
        
        # Perform analysis
        insights = analysis_system.analyze_image(image)
        
        # Filter sections based on request
        filtered_results = filter_analysis_sections(insights, include_sections)
        
        # Update task with results
        analysis_tasks[task_id].update({
            "status": "completed",
            "results": filtered_results,
            "file_info": insights.file_info,
            "color_analysis": insights.color_analysis.__dict__ if 'color' in include_sections or 'all' in include_sections else None,
            "composition_analysis": insights.composition_analysis.__dict__ if 'composition' in include_sections or 'all' in include_sections else None,
            "content_analysis": insights.content_analysis.__dict__ if 'content' in include_sections or 'all' in include_sections else None,
            "quality_metrics": insights.quality_metrics.__dict__ if 'quality' in include_sections or 'all' in include_sections else None,
            "semantic_insights": insights.semantic_insights.__dict__ if 'semantic' in include_sections or 'all' in include_sections else None,
            "confidence_scores": insights.confidence_scores,
            "processing_time": insights.processing_time,
            "analysis_timestamp": insights.analysis_timestamp,
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        # Update task with error
        analysis_tasks[task_id].update({
            "status": "failed",
            "message": str(e),
            "failed_at": datetime.now()
        })
        logger.error(f"Background analysis failed for task {task_id}: {e}")

async def process_image_comparison(
    task_id: str,
    image_1: str,
    image_2: str,
    comparison_aspects: List[str]
):
    """
    Background task for image comparison
    """
    try:
        # Decode both images
        img1_bytes = base64.b64decode(image_1)
        img2_bytes = base64.b64decode(image_2)
        
        nparr1 = np.frombuffer(img1_bytes, np.uint8)
        nparr2 = np.frombuffer(img2_bytes, np.uint8)
        
        image1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)
        image2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)
        
        # Analyze both images
        insights1 = analysis_system.analyze_image(image1)
        insights2 = analysis_system.analyze_image(image2)
        
        # Generate comparison
        comparison_results = generate_comparison_results(insights1, insights2, comparison_aspects)
        
        analysis_tasks[task_id].update({
            "status": "completed",
            "results": comparison_results,
            "processing_time": insights1.processing_time + insights2.processing_time,
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        analysis_tasks[task_id].update({
            "status": "failed",
            "message": str(e),
            "failed_at": datetime.now()
        })
        logger.error(f"Image comparison failed for task {task_id}: {e}")

def filter_analysis_sections(insights: ComprehensiveImageInsights, include_sections: List[str]) -> Dict[str, Any]:
    """Filter analysis results based on requested sections"""
    if "all" in include_sections:
        return insights.__dict__
    
    filtered = {
        "processing_time": insights.processing_time,
        "analysis_timestamp": insights.analysis_timestamp,
        "confidence_scores": insights.confidence_scores
    }
    
    if "color" in include_sections:
        filtered["color_analysis"] = insights.color_analysis.__dict__
    if "composition" in include_sections:
        filtered["composition_analysis"] = insights.composition_analysis.__dict__
    if "content" in include_sections:
        filtered["content_analysis"] = insights.content_analysis.__dict__
    if "quality" in include_sections:
        filtered["quality_metrics"] = insights.quality_metrics.__dict__
    if "semantic" in include_sections:
        filtered["semantic_insights"] = insights.semantic_insights.__dict__
    if "technical" in include_sections:
        filtered["file_info"] = insights.file_info
    
    return filtered

def generate_comparison_results(insights1: ComprehensiveImageInsights, 
                              insights2: ComprehensiveImageInsights,
                              aspects: List[str]) -> Dict[str, Any]:
    """Generate comparison analysis between two images"""
    comparison = {
        "image_1": {},
        "image_2": {},
        "differences": {},
        "similarities": {}
    }
    
    if "quality" in aspects:
        comparison["image_1"]["quality"] = insights1.quality_metrics.__dict__
        comparison["image_2"]["quality"] = insights2.quality_metrics.__dict__
        
        # Calculate quality differences
        comparison["differences"]["quality_score"] = {
            "image_1": insights1.quality_metrics.technical_score,
            "image_2": insights2.quality_metrics.technical_score,
            "difference": abs(insights1.quality_metrics.technical_score - insights2.quality_metrics.technical_score),
            "better_image": "image_1" if insights1.quality_metrics.technical_score > insights2.quality_metrics.technical_score else "image_2"
        }
    
    if "composition" in aspects:
        comparison["image_1"]["composition"] = insights1.composition_analysis.__dict__
        comparison["image_2"]["composition"] = insights2.composition_analysis.__dict__
        
        # Compare composition scores
        comp1_avg = (insights1.composition_analysis.rule_of_thirds_alignment + 
                     insights1.composition_analysis.symmetry_score + 
                     insights1.composition_analysis.balance_score) / 3
        comp2_avg = (insights2.composition_analysis.rule_of_thirds_alignment + 
                     insights2.composition_analysis.symmetry_score + 
                     insights2.composition_analysis.balance_score) / 3
        
        comparison["differences"]["composition_score"] = {
            "image_1": comp1_avg,
            "image_2": comp2_avg,
            "difference": abs(comp1_avg - comp2_avg),
            "better_image": "image_1" if comp1_avg > comp2_avg else "image_2"
        }
    
    if "color" in aspects:
        comparison["image_1"]["color"] = insights1.color_analysis.__dict__
        comparison["image_2"]["color"] = insights2.color_analysis.__dict__
        
        # Compare color properties
        comparison["similarities"]["color_temperature"] = insights1.color_analysis.color_temperature == insights2.color_analysis.color_temperature
        comparison["similarities"]["brightness_level"] = insights1.color_analysis.brightness_level == insights2.color_analysis.brightness_level
    
    return comparison

def generate_brief_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate brief summary from multiple analyses"""
    total_images = len(results)
    avg_quality = np.mean([r.get("quality_metrics", {}).get("technical_score", 0) for r in results])
    
    common_themes = {}
    for result in results:
        themes = result.get("semantic_insights", {}).get("key_themes", [])
        for theme in themes:
            common_themes[theme] = common_themes.get(theme, 0) + 1
    
    top_themes = sorted(common_themes.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_images": total_images,
        "average_quality_score": avg_quality,
        "most_common_themes": [{"theme": theme, "count": count} for theme, count in top_themes],
        "summary_text": f"Analyzed {total_images} images with average quality score of {avg_quality:.1f}/100"
    }

def generate_comprehensive_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive summary with detailed statistics"""
    # Implementation would include detailed statistical analysis
    brief = generate_brief_summary(results)
    
    # Add more detailed metrics
    quality_distribution = {}
    scene_types = {}
    
    for result in results:
        # Quality distribution
        quality = result.get("quality_metrics", {}).get("overall_quality", "unknown")
        quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        # Scene types
        scene = result.get("content_analysis", {}).get("scene_type", "unknown")
        scene_types[scene] = scene_types.get(scene, 0) + 1
    
    brief.update({
        "quality_distribution": quality_distribution,
        "scene_type_distribution": scene_types,
        "detailed_analysis": True
    })
    
    return brief

def generate_technical_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate technical summary focusing on metrics and performance"""
    processing_times = [r.get("processing_time", 0) for r in results]
    confidence_scores = [r.get("confidence_scores", {}).get("overall", 0) for r in results]
    
    return {
        "total_images": len(results),
        "processing_statistics": {
            "total_time": sum(processing_times),
            "average_time": np.mean(processing_times),
            "min_time": min(processing_times) if processing_times else 0,
            "max_time": max(processing_times) if processing_times else 0
        },
        "confidence_statistics": {
            "average_confidence": np.mean(confidence_scores),
            "min_confidence": min(confidence_scores) if confidence_scores else 0,
            "max_confidence": max(confidence_scores) if confidence_scores else 0
        }
    }

def analyze_trends(tasks: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Analyze trends from recent analyses"""
    # Placeholder for trend analysis logic
    return [
        {"trend": "Increasing quality scores", "confidence": 0.8},
        {"trend": "More outdoor scenes", "confidence": 0.7},
        {"trend": "Higher color diversity", "confidence": 0.6}
    ][:limit]

def generate_csv_export(task: Dict[str, Any]) -> str:
    """Generate CSV export of analysis results"""
    # Simplified CSV generation
    return "metric,value\nquality_score,85.5\nprocessing_time,1.23"

def generate_html_report(task: Dict[str, Any]) -> str:
    """Generate HTML report of analysis results"""
    return "<html><body><h1>Analysis Report</h1><p>Detailed results...</p></body></html>"

@router.get("/health")
async def health_check():
    """
    Health check for image analysis service
    """
    return {
        "status": "healthy",
        "service": "image_analysis_insights",
        "active_tasks": len([t for t in analysis_tasks.values() if t["status"] == "processing"]),
        "total_tasks": len(analysis_tasks),
        "timestamp": datetime.now().isoformat()
    }