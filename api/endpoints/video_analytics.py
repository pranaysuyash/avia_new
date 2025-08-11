"""
Real-time Video Analytics API Endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import tempfile
import os
import io
import json
import asyncio
from datetime import datetime
import cv2
import numpy as np
import base64

from ...realtime_video_analytics import (
    RealtimeVideoAnalytics,
    AnalyticsType,
    VideoSource,
    AnalyticsResult,
    DetectedObject
)

router = APIRouter(prefix="/api/video-analytics", tags=["video-analytics"])

# Initialize analytics system
analytics_system = RealtimeVideoAnalytics()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis"""
    source: str = Field(..., description="Video source (file path, URL, or device ID)")
    source_type: str = Field(default="file", pattern="^(file|webcam|rtsp|http_stream|youtube)$")
    analytics_types: List[str] = Field(
        default=["object_detection", "scene_understanding"],
        description="Types of analytics to perform"
    )
    real_time: bool = Field(default=True, description="Enable real-time processing")
    save_output: Optional[str] = Field(default=None, description="Path to save annotated video")


class HeatmapRequest(BaseModel):
    """Request model for heatmap generation"""
    video_path: str
    heatmap_type: str = Field(default="motion", pattern="^(motion|presence)$")


class KeyFrameRequest(BaseModel):
    """Request model for key frame extraction"""
    video_path: str
    num_frames: int = Field(default=10, ge=1, le=100)
    method: str = Field(default="uniform", pattern="^(uniform|scene_change)$")


class LiveStreamRequest(BaseModel):
    """Request model for live stream analysis"""
    stream_url: str
    analytics_types: List[str] = Field(default=["object_detection"])
    duration: Optional[int] = Field(default=None, description="Analysis duration in seconds")


@router.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    video_file: Optional[UploadFile] = File(None, description="Video file to analyze"),
    source: Optional[str] = Form(None, description="Video source URL or device ID"),
    source_type: str = Form("file"),
    analytics_types: str = Form("object_detection,scene_understanding"),
    real_time: bool = Form(True),
    save_output: bool = Form(False)
):
    """
    Analyze video with AI-powered analytics
    
    - **video_file**: Upload video file for analysis
    - **source**: Alternative video source (URL or device ID)
    - **source_type**: Type of video source
    - **analytics_types**: Comma-separated list of analytics to perform
    - **real_time**: Enable real-time processing
    - **save_output**: Save annotated video output
    """
    
    if not video_file and not source:
        raise HTTPException(status_code=400, detail="Either video_file or source must be provided")
    
    temp_file = None
    output_file = None
    
    try:
        # Handle uploaded file
        if video_file:
            if not video_file.content_type.startswith('video/'):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {video_file.content_type}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                content = await video_file.read()
                tmp_file.write(content)
                temp_file = tmp_file.name
                video_source = temp_file
        else:
            video_source = source
        
        # Parse analytics types
        analytics_type_list = [
            AnalyticsType[t.upper()] for t in analytics_types.split(',')
        ]
        
        # Set output file if requested
        if save_output:
            output_file = tempfile.mktemp(suffix='_annotated.mp4')
        
        # Parse source type
        source_type_enum = VideoSource[source_type.upper()]
        
        # Perform analysis
        result = await analytics_system.analyze_video(
            video_source=video_source,
            source_type=source_type_enum,
            analytics_types=analytics_type_list,
            real_time=real_time,
            save_output=output_file
        )
        
        # Prepare response
        response = {
            "video_id": result.video_id,
            "timestamp": result.timestamp.isoformat(),
            "frame_count": result.frame_count,
            "duration": result.duration,
            "statistics": result.statistics,
            "objects_detected": len(result.detected_objects),
            "scenes_analyzed": len(result.scenes),
            "activities_recognized": len(result.activities),
            "anomalies_detected": len(result.anomalies)
        }
        
        # Include sample results
        if result.detected_objects:
            response["sample_objects"] = [
                {
                    "class": obj.class_name,
                    "confidence": obj.confidence,
                    "frame": obj.frame_number
                }
                for obj in result.detected_objects[:10]
            ]
        
        if output_file and os.path.exists(output_file):
            response["output_video"] = f"/api/video-analytics/download/{os.path.basename(output_file)}"
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


@router.post("/analyze-stream")
async def analyze_stream(request: LiveStreamRequest):
    """
    Analyze live video stream
    
    - **stream_url**: URL of the video stream (RTSP, HTTP, etc.)
    - **analytics_types**: Types of analytics to perform
    - **duration**: Analysis duration in seconds (None for continuous)
    """
    
    try:
        analytics_type_list = [
            AnalyticsType[t.upper()] for t in request.analytics_types
        ]
        
        # Determine source type from URL
        if request.stream_url.startswith('rtsp://'):
            source_type = VideoSource.RTSP
        elif request.stream_url.startswith('http'):
            source_type = VideoSource.HTTP_STREAM
        else:
            source_type = VideoSource.FILE
        
        # Start analysis with duration limit
        task = asyncio.create_task(
            analytics_system.analyze_video(
                video_source=request.stream_url,
                source_type=source_type,
                analytics_types=analytics_type_list,
                real_time=True
            )
        )
        
        if request.duration:
            await asyncio.sleep(request.duration)
            task.cancel()
        
        return {
            "status": "analysis_started",
            "stream_url": request.stream_url,
            "analytics_types": request.analytics_types
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream analysis failed: {str(e)}")


@router.websocket("/ws/{client_id}")
async def websocket_analytics(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time video analytics streaming
    """
    await websocket.accept()
    active_connections[client_id] = websocket
    
    try:
        # Callback for real-time results
        async def send_results(frame_num: int, results: Dict[str, Any]):
            # Convert results to JSON-serializable format
            message = {
                "frame": frame_num,
                "timestamp": datetime.now().isoformat(),
                "objects": []
            }
            
            if 'objects' in results:
                for obj in results['objects']:
                    message["objects"].append({
                        "class": obj.class_name,
                        "confidence": obj.confidence,
                        "bbox": obj.bbox,
                        "tracking_id": obj.tracking_id
                    })
            
            if 'activities' in results:
                message["activities"] = results['activities']
            
            if 'scene' in results:
                message["scene"] = {
                    "type": results['scene'].scene_type,
                    "confidence": results['scene'].confidence
                }
            
            if 'anomaly' in results:
                message["anomaly"] = results['anomaly']
            
            await websocket.send_json(message)
        
        analytics_system.add_result_callback(send_results)
        
        while True:
            # Receive commands from client
            data = await websocket.receive_json()
            
            if data.get("command") == "start_analysis":
                # Start video analysis
                source = data.get("source")
                source_type = VideoSource[data.get("source_type", "FILE").upper()]
                analytics_types = [
                    AnalyticsType[t.upper()] for t in data.get("analytics_types", ["object_detection"])
                ]
                
                asyncio.create_task(
                    analytics_system.analyze_video(
                        video_source=source,
                        source_type=source_type,
                        analytics_types=analytics_types,
                        real_time=True
                    )
                )
                
                await websocket.send_json({"status": "analysis_started"})
            
            elif data.get("command") == "stop_analysis":
                # Stop analysis
                await websocket.send_json({"status": "analysis_stopped"})
                break
                
    except WebSocketDisconnect:
        del active_connections[client_id]
        analytics_system.remove_result_callback(send_results)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()


@router.post("/heatmap")
async def generate_heatmap(request: HeatmapRequest):
    """
    Generate heatmap visualization for video
    
    - **video_path**: Path to video file
    - **heatmap_type**: Type of heatmap (motion or presence)
    """
    
    try:
        heatmap = await analytics_system.generate_heatmap(
            video_path=request.video_path,
            heatmap_type=request.heatmap_type
        )
        
        # Convert heatmap to colormap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Encode as PNG
        _, buffer = cv2.imencode('.png', heatmap_colored)
        
        return StreamingResponse(
            io.BytesIO(buffer),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=heatmap_{request.heatmap_type}.png"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")


@router.post("/keyframes")
async def extract_keyframes(request: KeyFrameRequest):
    """
    Extract key frames from video
    
    - **video_path**: Path to video file
    - **num_frames**: Number of key frames to extract
    - **method**: Extraction method (uniform or scene_change)
    """
    
    try:
        key_frames = await analytics_system.extract_key_frames(
            video_path=request.video_path,
            num_frames=request.num_frames,
            method=request.method
        )
        
        # Convert frames to base64
        frames_data = []
        for frame_idx, frame in key_frames:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            frames_data.append({
                "frame_index": frame_idx,
                "image": f"data:image/jpeg;base64,{frame_base64}"
            })
        
        return {
            "total_frames": len(key_frames),
            "extraction_method": request.method,
            "frames": frames_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key frame extraction failed: {str(e)}")


@router.get("/stats/{video_id}")
async def get_video_stats(video_id: str):
    """
    Get detailed statistics for analyzed video
    """
    
    # In production, retrieve from database
    # For now, return sample statistics
    return {
        "video_id": video_id,
        "statistics": {
            "total_objects": 150,
            "unique_objects": 12,
            "object_breakdown": {
                "person": 45,
                "car": 30,
                "bicycle": 15,
                "dog": 10,
                "others": 50
            },
            "activities": {
                "walking": 25,
                "running": 5,
                "standing": 20,
                "sitting": 10
            },
            "scenes": {
                "outdoor": 60,
                "indoor": 40
            },
            "anomalies": {
                "high_motion": 3,
                "unusual_object": 1
            },
            "processing_metrics": {
                "fps": 25.5,
                "processing_time": 120.5,
                "frames_processed": 3000
            }
        }
    }


@router.post("/compare")
async def compare_videos(
    video1: UploadFile = File(..., description="First video file"),
    video2: UploadFile = File(..., description="Second video file")
):
    """
    Compare two videos for similarity and differences
    """
    
    temp_files = []
    
    try:
        # Save uploaded files
        for video_file in [video1, video2]:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                content = await video_file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)
        
        # Analyze both videos
        results = []
        for video_path in temp_files:
            result = await analytics_system.analyze_video(
                video_source=video_path,
                source_type=VideoSource.FILE,
                analytics_types=[AnalyticsType.OBJECT_DETECTION, AnalyticsType.SCENE_UNDERSTANDING],
                real_time=False
            )
            results.append(result)
        
        # Compare results
        comparison = {
            "video1": {
                "filename": video1.filename,
                "frame_count": results[0].frame_count,
                "objects_detected": len(results[0].detected_objects),
                "object_types": list(set(obj.class_name for obj in results[0].detected_objects))
            },
            "video2": {
                "filename": video2.filename,
                "frame_count": results[1].frame_count,
                "objects_detected": len(results[1].detected_objects),
                "object_types": list(set(obj.class_name for obj in results[1].detected_objects))
            },
            "similarity": {
                "common_objects": list(
                    set(obj.class_name for obj in results[0].detected_objects) &
                    set(obj.class_name for obj in results[1].detected_objects)
                ),
                "frame_count_difference": abs(results[0].frame_count - results[1].frame_count),
                "duration_difference": abs(results[0].duration - results[1].duration)
            }
        }
        
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video comparison failed: {str(e)}")
    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


@router.get("/download/{filename}")
async def download_output(filename: str):
    """
    Download processed video output
    """
    
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )


@router.get("/models")
async def list_available_models():
    """
    List available AI models for video analytics
    """
    
    return {
        "object_detection": [
            {"name": "DETR ResNet-50", "id": "facebook/detr-resnet-50", "accuracy": "high"},
            {"name": "YOLO v5", "id": "yolov5", "accuracy": "medium", "speed": "fast"}
        ],
        "activity_recognition": [
            {"name": "MediaPipe Pose", "id": "mediapipe-pose", "accuracy": "high"},
            {"name": "OpenPose", "id": "openpose", "accuracy": "very_high", "speed": "slow"}
        ],
        "scene_understanding": [
            {"name": "ResNet-50", "id": "resnet50", "accuracy": "high"},
            {"name": "EfficientNet", "id": "efficientnet", "accuracy": "very_high"}
        ]
    }


@router.post("/configure")
async def configure_analytics(config: Dict[str, Any]):
    """
    Configure analytics system settings
    """
    
    try:
        # Update analytics system configuration
        analytics_system.config.update(config)
        
        return {
            "status": "configured",
            "config": analytics_system.config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")


@router.get("/active-streams")
async def get_active_streams():
    """
    Get list of active video analysis streams
    """
    
    return {
        "active_connections": len(active_connections),
        "clients": list(active_connections.keys())
    }