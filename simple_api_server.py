"""
Simple API server for testing the search interface
"""

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from datetime import datetime
import uvicorn
import asyncio
import json
import random

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock transcription data
MOCK_TRANSCRIPTIONS = [
    {
        "transcript_id": "t1",
        "title": "Tech Conference 2024 Keynote",
        "full_text": "Welcome to our annual tech conference. Today we'll be discussing artificial intelligence, machine learning, and the future of technology...",
        "snippet": "Welcome to our annual tech conference. Today we'll be discussing artificial intelligence...",
        "created_at": "2024-01-15T10:30:00",
        "duration": 3600,
        "word_count": 8500,
        "language": "en",
        "entities": [
            {"text": "Tech Conference", "label": "EVENT"},
            {"text": "artificial intelligence", "label": "TECHNOLOGY"},
            {"text": "machine learning", "label": "TECHNOLOGY"}
        ]
    },
    {
        "transcript_id": "t2", 
        "title": "Product Team Meeting Q1",
        "full_text": "Let's review our Q1 product roadmap. We have several key features to deliver including the new dashboard, API improvements, and mobile app updates...",
        "snippet": "Let's review our Q1 product roadmap. We have several key features to deliver...",
        "created_at": "2024-02-01T14:00:00",
        "duration": 2400,
        "word_count": 5200,
        "language": "en",
        "entities": [
            {"text": "Q1", "label": "DATE"},
            {"text": "dashboard", "label": "PRODUCT"},
            {"text": "API", "label": "TECHNOLOGY"},
            {"text": "mobile app", "label": "PRODUCT"}
        ]
    },
    {
        "transcript_id": "t3",
        "title": "Customer Interview - Sarah Johnson",
        "full_text": "Thank you for joining us today Sarah. Can you tell us about your experience with our platform? I've been using it for about 6 months now...",
        "snippet": "Thank you for joining us today Sarah. Can you tell us about your experience...",
        "created_at": "2024-02-10T09:15:00",
        "duration": 1800,
        "word_count": 3200,
        "language": "en",
        "entities": [
            {"text": "Sarah Johnson", "label": "PERSON"},
            {"text": "6 months", "label": "DURATION"}
        ]
    },
    {
        "transcript_id": "t4",
        "title": "Engineering Standup - Sprint 23",
        "full_text": "Good morning team. Let's go through our updates for Sprint 23. John, can you start with the API refactoring progress?...",
        "snippet": "Good morning team. Let's go through our updates for Sprint 23...",
        "created_at": "2024-02-20T10:00:00",
        "duration": 900,
        "word_count": 1500,
        "language": "en",
        "entities": [
            {"text": "Sprint 23", "label": "EVENT"},
            {"text": "John", "label": "PERSON"},
            {"text": "API refactoring", "label": "TASK"}
        ]
    },
    {
        "transcript_id": "t5",
        "title": "Marketing Strategy Session",
        "full_text": "Today we'll discuss our Q2 marketing strategy. We need to focus on content marketing, social media engagement, and SEO improvements...",
        "snippet": "Today we'll discuss our Q2 marketing strategy. We need to focus on content marketing...",
        "created_at": "2024-03-01T15:30:00",
        "duration": 3000,
        "word_count": 6000,
        "language": "en",
        "entities": [
            {"text": "Q2", "label": "DATE"},
            {"text": "content marketing", "label": "STRATEGY"},
            {"text": "social media", "label": "PLATFORM"},
            {"text": "SEO", "label": "TECHNOLOGY"}
        ]
    }
]

@app.get("/")
async def root():
    return {"message": "Simple API Server", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/search")
async def search_transcriptions(
    q: str = Query(..., description="Search query"),
    dateRange: Optional[str] = Query("all", description="Date range filter"),
    language: Optional[str] = Query("all", description="Language filter"),
    hasEntities: Optional[bool] = Query(False, description="Has entities filter"),
    sortBy: Optional[str] = Query("relevance", description="Sort by field")
):
    """Search through transcriptions"""
    
    # Filter results based on query
    results = []
    query_lower = q.lower()
    
    for transcript in MOCK_TRANSCRIPTIONS:
        # Simple text matching
        if (query_lower in transcript["title"].lower() or 
            query_lower in transcript["full_text"].lower() or
            any(query_lower in entity["text"].lower() for entity in transcript["entities"])):
            
            # Apply filters
            if language != "all" and transcript["language"] != language:
                continue
            
            if hasEntities and len(transcript["entities"]) == 0:
                continue
            
            # Calculate mock relevance score
            title_matches = transcript["title"].lower().count(query_lower)
            text_matches = transcript["full_text"].lower().count(query_lower)
            entity_matches = sum(1 for e in transcript["entities"] if query_lower in e["text"].lower())
            
            score = (title_matches * 3) + text_matches + (entity_matches * 2)
            
            result = {
                **transcript,
                "score": score
            }
            results.append(result)
    
    # Sort results
    if sortBy == "relevance":
        results.sort(key=lambda x: x["score"], reverse=True)
    elif sortBy == "date":
        results.sort(key=lambda x: x["created_at"], reverse=True)
    elif sortBy == "duration":
        results.sort(key=lambda x: x["duration"], reverse=True)
    elif sortBy == "word_count":
        results.sort(key=lambda x: x["word_count"], reverse=True)
    
    return {
        "success": True,
        "data": {
            "results": results,
            "total_count": len(results),
            "query": q,
            "filters": {
                "dateRange": dateRange,
                "language": language,
                "hasEntities": hasEntities,
                "sortBy": sortBy
            }
        }
    }

@app.get("/api/v1/insights/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        "data": {
            "totalTranscriptions": 1234,
            "hoursProcessed": 842,
            "entitiesFound": 5678,
            "accuracyRate": 98.5
        }
    }

@app.get("/api/v1/transcription/list")
async def get_transcriptions(limit: int = 5):
    """Get recent transcriptions"""
    # Add proper IDs to transcriptions
    items_with_ids = []
    for t in MOCK_TRANSCRIPTIONS[:limit]:
        item = t.copy()
        item["id"] = item["transcript_id"]  # Add id field
        items_with_ids.append(item)
    
    return {
        "data": {
            "items": items_with_ids,
            "total": len(MOCK_TRANSCRIPTIONS),
            "page": 1,
            "pageSize": limit
        }
    }

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for sub_list in self.subscriptions.values():
            if websocket in sub_list:
                sub_list.remove(websocket)

    async def send_to_client(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

    def subscribe(self, transcription_id: str, websocket: WebSocket):
        if transcription_id not in self.subscriptions:
            self.subscriptions[transcription_id] = []
        if websocket not in self.subscriptions[transcription_id]:
            self.subscriptions[transcription_id].append(websocket)

    async def send_to_subscribers(self, transcription_id: str, event: str, data: dict):
        if transcription_id in self.subscriptions:
            message = {
                "event": event,
                "data": {**data, "transcription_id": transcription_id}
            }
            for websocket in self.subscriptions[transcription_id]:
                await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("event") == "subscribe":
                transcription_id = data.get("data", {}).get("transcription_id")
                if transcription_id:
                    manager.subscribe(transcription_id, websocket)
                    # Start simulated transcription progress
                    asyncio.create_task(simulate_transcription(transcription_id))
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def simulate_transcription(transcription_id: str):
    """Simulate transcription progress updates"""
    steps = [
        ("Audio Processing", 25),
        ("Speech Recognition", 50),
        ("Speaker Diarization", 75),
        ("Entity Extraction", 100)
    ]
    
    # Send initial status
    await manager.send_to_subscribers(
        transcription_id,
        "transcription:status",
        {"status": "processing", "step": "Initializing..."}
    )
    
    # Simulate progress through steps
    for step_name, progress in steps:
        await asyncio.sleep(random.uniform(2, 4))  # Random delay
        
        await manager.send_to_subscribers(
            transcription_id,
            "transcription:step",
            {"step": step_name}
        )
        
        await manager.send_to_subscribers(
            transcription_id,
            "transcription:progress",
            {"progress": progress}
        )
    
    # Complete the transcription
    await asyncio.sleep(1)
    await manager.send_to_subscribers(
        transcription_id,
        "transcription:status",
        {
            "status": "completed",
            "step": "Transcription complete",
            "result": {
                "id": transcription_id,
                "duration": 1800,
                "word_count": 3500,
                "entities_count": 15
            }
        }
    )

@app.post("/api/v1/transcription/process")
async def process_transcription(file_id: str):
    """Start transcription processing"""
    transcription_id = f"t_{random.randint(1000, 9999)}"
    
    # Start async processing
    asyncio.create_task(simulate_transcription(transcription_id))
    
    return {
        "success": True,
        "data": {
            "transcription_id": transcription_id,
            "status": "processing",
            "message": "Transcription started"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)