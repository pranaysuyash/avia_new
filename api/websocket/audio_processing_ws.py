"""
WebSocket support for real-time audio processing updates
Provides real-time progress updates during audio enhancement
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
import json
import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Processing status enum"""
    QUEUED = "queued"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    ENHANCING = "enhancing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MessageType(Enum):
    """WebSocket message types"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    STATUS_UPDATE = "status_update"
    PROGRESS_UPDATE = "progress_update"
    METRICS_UPDATE = "metrics_update"
    WAVEFORM_UPDATE = "waveform_update"
    SPECTRUM_UPDATE = "spectrum_update"
    ERROR = "error"
    COMPLETE = "complete"
    CANCEL = "cancel"
    PING = "ping"
    PONG = "pong"

class AudioProcessingWebSocketManager:
    """Manager for WebSocket connections during audio processing"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.processing_tasks: Dict[str, Dict[str, Any]] = {}
        self.client_tasks: Dict[str, str] = {}  # client_id -> task_id mapping
        
    async def connect(self, websocket: WebSocket, client_id: str, task_id: Optional[str] = None):
        """Connect a client to WebSocket"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Add to active connections
        if task_id:
            self.active_connections[task_id].append(websocket)
            self.client_tasks[client_id] = task_id
        else:
            self.active_connections[client_id].append(websocket)
        
        # Send connection confirmation
        await self.send_message(websocket, {
            "type": MessageType.CONNECT.value,
            "client_id": client_id,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to audio processing WebSocket"
        })
        
        logger.info(f"Client {client_id} connected to WebSocket for task {task_id}")
        return client_id
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Disconnect a client from WebSocket"""
        # Remove from active connections
        task_id = self.client_tasks.get(client_id)
        
        if task_id and task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        if client_id in self.client_tasks:
            del self.client_tasks[client_id]
        
        logger.info(f"Client {client_id} disconnected from WebSocket")
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        """Broadcast message to all clients connected to a task"""
        if task_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.active_connections[task_id].remove(ws)
    
    async def send_status_update(self, task_id: str, status: ProcessingStatus, 
                                message: str = "", details: Dict[str, Any] = None):
        """Send status update for a processing task"""
        update = {
            "type": MessageType.STATUS_UPDATE.value,
            "task_id": task_id,
            "status": status.value,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Update task status
        if task_id not in self.processing_tasks:
            self.processing_tasks[task_id] = {}
        self.processing_tasks[task_id]["status"] = status.value
        self.processing_tasks[task_id]["last_update"] = datetime.now()
        
        await self.broadcast_to_task(task_id, update)
    
    async def send_progress_update(self, task_id: str, progress: float, 
                                  stage: str = "", eta_seconds: Optional[int] = None):
        """Send progress update for a processing task"""
        update = {
            "type": MessageType.PROGRESS_UPDATE.value,
            "task_id": task_id,
            "progress": min(max(progress, 0), 100),  # Clamp between 0-100
            "stage": stage,
            "eta_seconds": eta_seconds,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update task progress
        if task_id not in self.processing_tasks:
            self.processing_tasks[task_id] = {}
        self.processing_tasks[task_id]["progress"] = progress
        self.processing_tasks[task_id]["stage"] = stage
        
        await self.broadcast_to_task(task_id, update)
    
    async def send_metrics_update(self, task_id: str, metrics: Dict[str, Any]):
        """Send real-time metrics update"""
        update = {
            "type": MessageType.METRICS_UPDATE.value,
            "task_id": task_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_task(task_id, update)
    
    async def send_waveform_update(self, task_id: str, waveform_data: List[float], 
                                  sample_rate: int = 44100):
        """Send waveform visualization data"""
        # Downsample for visualization
        max_points = 1000
        if len(waveform_data) > max_points:
            indices = np.linspace(0, len(waveform_data)-1, max_points, dtype=int)
            waveform_data = [waveform_data[i] for i in indices]
        
        update = {
            "type": MessageType.WAVEFORM_UPDATE.value,
            "task_id": task_id,
            "waveform": waveform_data,
            "sample_rate": sample_rate,
            "duration": len(waveform_data) / sample_rate,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_task(task_id, update)
    
    async def send_spectrum_update(self, task_id: str, frequencies: List[float], 
                                  magnitudes: List[float]):
        """Send spectrum visualization data"""
        # Limit data points for visualization
        max_points = 500
        if len(frequencies) > max_points:
            step = len(frequencies) // max_points
            frequencies = frequencies[::step]
            magnitudes = magnitudes[::step]
        
        update = {
            "type": MessageType.SPECTRUM_UPDATE.value,
            "task_id": task_id,
            "frequencies": frequencies,
            "magnitudes": magnitudes,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_task(task_id, update)
    
    async def send_error(self, task_id: str, error_message: str, 
                        error_code: Optional[str] = None):
        """Send error message"""
        update = {
            "type": MessageType.ERROR.value,
            "task_id": task_id,
            "error_message": error_message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update task status
        if task_id in self.processing_tasks:
            self.processing_tasks[task_id]["status"] = ProcessingStatus.FAILED.value
            self.processing_tasks[task_id]["error"] = error_message
        
        await self.broadcast_to_task(task_id, update)
    
    async def send_completion(self, task_id: str, result: Dict[str, Any]):
        """Send completion message with results"""
        update = {
            "type": MessageType.COMPLETE.value,
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update task status
        if task_id in self.processing_tasks:
            self.processing_tasks[task_id]["status"] = ProcessingStatus.COMPLETED.value
            self.processing_tasks[task_id]["completed_at"] = datetime.now()
            self.processing_tasks[task_id]["result"] = result
        
        await self.broadcast_to_task(task_id, update)
    
    async def handle_client_message(self, websocket: WebSocket, client_id: str, 
                                   message: Dict[str, Any]):
        """Handle incoming message from client"""
        msg_type = message.get("type")
        
        if msg_type == MessageType.PING.value:
            # Respond to ping
            await self.send_message(websocket, {
                "type": MessageType.PONG.value,
                "timestamp": datetime.now().isoformat()
            })
        
        elif msg_type == MessageType.CANCEL.value:
            # Handle cancellation request
            task_id = message.get("task_id")
            if task_id and task_id in self.processing_tasks:
                await self.cancel_task(task_id)
        
        else:
            logger.warning(f"Unknown message type from client {client_id}: {msg_type}")
    
    async def cancel_task(self, task_id: str):
        """Cancel a processing task"""
        if task_id in self.processing_tasks:
            self.processing_tasks[task_id]["status"] = ProcessingStatus.CANCELLED.value
            
            await self.send_status_update(
                task_id, 
                ProcessingStatus.CANCELLED,
                "Task cancelled by user"
            )
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        return self.processing_tasks.get(task_id)
    
    async def simulate_audio_processing(self, task_id: str, duration: int = 10):
        """Simulate audio processing with progress updates (for testing)"""
        stages = [
            ("Initializing", 0, 10),
            ("Analyzing audio quality", 10, 25),
            ("Applying noise reduction", 25, 45),
            ("Normalizing audio levels", 45, 60),
            ("Enhancing frequencies", 60, 80),
            ("Finalizing output", 80, 95),
            ("Saving enhanced audio", 95, 100)
        ]
        
        await self.send_status_update(task_id, ProcessingStatus.PROCESSING)
        
        for stage_name, start_progress, end_progress in stages:
            # Check if cancelled
            if self.processing_tasks.get(task_id, {}).get("status") == ProcessingStatus.CANCELLED.value:
                return
            
            steps = 5
            for i in range(steps):
                progress = start_progress + (end_progress - start_progress) * (i / steps)
                eta = int((100 - progress) * duration / 100)
                
                await self.send_progress_update(task_id, progress, stage_name, eta)
                
                # Send mock metrics
                if progress > 20:
                    await self.send_metrics_update(task_id, {
                        "snr_improvement": progress * 0.3,
                        "quality_score": 50 + progress * 0.5,
                        "processing_speed": f"{progress/duration:.1f}x"
                    })
                
                await asyncio.sleep(duration / len(stages) / steps)
        
        # Send completion
        await self.send_completion(task_id, {
            "enhanced_file": f"/downloads/enhanced_{task_id}.wav",
            "original_metrics": {
                "snr_db": 15.2,
                "quality_score": 65
            },
            "enhanced_metrics": {
                "snr_db": 28.5,
                "quality_score": 92
            },
            "improvement_score": 27
        })

# Global WebSocket manager instance
ws_manager = AudioProcessingWebSocketManager()

# WebSocket endpoint
async def audio_processing_websocket(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for audio processing updates"""
    client_id = str(uuid.uuid4())
    
    try:
        # Connect client
        client_id = await ws_manager.connect(websocket, client_id, task_id)
        
        # Listen for messages
        while True:
            try:
                message = await websocket.receive_json()
                await ws_manager.handle_client_message(websocket, client_id, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await ws_manager.send_error(task_id, str(e))
                break
    
    finally:
        # Disconnect client
        ws_manager.disconnect(websocket, client_id)

# Integration with audio enhancement processing
async def process_audio_with_updates(task_id: str, file_path: str, settings: Dict[str, Any]):
    """Process audio with real-time WebSocket updates"""
    try:
        # Send initial status
        await ws_manager.send_status_update(
            task_id, 
            ProcessingStatus.ANALYZING,
            "Starting audio analysis..."
        )
        
        # Import audio processor
        from audio_enhancement_pipeline import AudioEnhancementPipeline
        from advanced_audio_processing import AdvancedAudioProcessor
        
        processor = AudioEnhancementPipeline()
        advanced = AdvancedAudioProcessor()
        
        # Step 1: Analyze original audio
        await ws_manager.send_progress_update(task_id, 10, "Analyzing original audio")
        original_metrics = processor.analyze_audio_quality(file_path)
        
        await ws_manager.send_metrics_update(task_id, {
            "original_snr": original_metrics.snr_db,
            "original_quality": original_metrics.quality_score
        })
        
        # Step 2: Apply noise reduction if enabled
        if settings.get("enable_noise_reduction"):
            await ws_manager.send_progress_update(task_id, 30, "Applying noise reduction")
            await ws_manager.send_status_update(
                task_id,
                ProcessingStatus.PROCESSING,
                f"Reducing noise with {settings.get('noise_reduction_strength', 0.7)*100:.0f}% strength"
            )
            # Process...
            await asyncio.sleep(2)  # Simulate processing
        
        # Step 3: Apply normalization if enabled
        if settings.get("enable_normalization"):
            await ws_manager.send_progress_update(task_id, 50, "Normalizing audio levels")
            await ws_manager.send_status_update(
                task_id,
                ProcessingStatus.PROCESSING,
                f"Normalizing to {settings.get('target_loudness_lufs', -16)} LUFS"
            )
            # Process...
            await asyncio.sleep(2)  # Simulate processing
        
        # Step 4: Apply advanced enhancements
        await ws_manager.send_progress_update(task_id, 70, "Applying advanced enhancements")
        
        # Spectral analysis
        spectral = advanced.spectral_analysis(file_path)
        await ws_manager.send_spectrum_update(
            task_id, 
            spectral.frequency_spectrum.tolist()[:500],
            spectral.magnitude_spectrum.tolist()[:500]
        )
        
        # Step 5: Finalize
        await ws_manager.send_progress_update(task_id, 90, "Finalizing enhanced audio")
        
        # Complete
        await ws_manager.send_progress_update(task_id, 100, "Processing complete")
        await ws_manager.send_completion(task_id, {
            "status": "success",
            "enhanced_file": f"/api/v1/audio-enhancement/download/{task_id}",
            "processing_time": 10.5,
            "improvements": {
                "snr_improvement": 12.3,
                "quality_improvement": 25.0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in audio processing: {e}")
        await ws_manager.send_error(task_id, str(e), "PROCESSING_ERROR")

# Export for use in FastAPI app
__all__ = [
    'ws_manager',
    'audio_processing_websocket',
    'process_audio_with_updates',
    'ProcessingStatus',
    'MessageType'
]