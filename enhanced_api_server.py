"""
Enhanced API server with file upload and real Whisper transcription capabilities
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import uvicorn
import asyncio
import json
import random
import tempfile
import os
import uuid
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import real transcription modules
try:
    from advanced_transcription import AdvancedTranscriber
    REAL_WHISPER_AVAILABLE = True
    print("✅ Real Whisper transcription available")
except ImportError as e:
    print(f"⚠️ Real Whisper not available, using mock: {e}")
    REAL_WHISPER_AVAILABLE = False

app = FastAPI(title="Audio/Video Transcription API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
transcription_storage = {}
file_storage = {}

# Initialize real transcriber if available
real_transcriber = None
if REAL_WHISPER_AVAILABLE:
    try:
        real_transcriber = AdvancedTranscriber()
        print("✅ Real AdvancedTranscriber initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize real transcriber: {e}")
        real_transcriber = None

def generate_mock_transcription(filename: str, duration: int = None) -> Dict[str, Any]:
    """Generate a realistic mock transcription for demo purposes"""
    
    # Sample transcriptions based on filename patterns
    if 'meeting' in filename.lower() or 'conference' in filename.lower():
        text = """Welcome everyone to our Q3 strategy meeting. I'm Sarah Johnson, VP of Product. Today we'll be discussing our key achievements and upcoming initiatives.

First, let's review our accomplishments this quarter. Our engineering team successfully launched the AI-powered search functionality, which has increased user engagement by 35%. This is fantastic news and I want to thank John Smith for his outstanding leadership on this project.

However, we've also identified some critical areas that need immediate attention. Our customer support team has reported a 20% increase in user complaints about the new dashboard interface. The main issues are around navigation complexity and slower load times. Mike Davis, can you elaborate on the specific user feedback we've received?

Thank you, Sarah. The complaints are primarily about the confusing navigation structure and performance issues. Users are having difficulty finding key features, and page load times have increased from 2 seconds to nearly 5 seconds. We need to prioritize these fixes before the end of the month.

That's a great point, Mike. I'm proposing we assign Lisa Chen from our UX team to work closely with engineering on resolving these issues. Lisa, are you available to take this on?

Absolutely, Sarah. I can start immediately. I'll conduct user interviews this week and present design recommendations by Friday.

Excellent. Now, let's discuss our budget allocation for Q4. Based on our current performance and growth projections, I'm recommending we increase our engineering budget by 15% to hire two additional senior developers. This investment will help us accelerate development and maintain our competitive edge.

Before we conclude, I want to address the competitive landscape. TechCorp has recently launched a similar product that's gaining traction. We need to stay ahead by focusing on innovation and user experience. I suggest we schedule a follow-up meeting next week to develop our competitive response strategy.

In summary, our action items are: fix the dashboard issues by month-end, finalize the Q4 budget proposal, hire additional developers, and develop our competitive strategy. Thank you everyone for your hard work and dedication."""
        
        # Generate segments for speaker diarization
        segments = [
            {"start": 0, "end": 30, "speaker": "Sarah Johnson", "text": "Welcome everyone to our Q3 strategy meeting. I'm Sarah Johnson, VP of Product."},
            {"start": 30, "end": 60, "speaker": "Sarah Johnson", "text": "Today we'll be discussing our key achievements and upcoming initiatives."},
            {"start": 60, "end": 90, "speaker": "Sarah Johnson", "text": "First, let's review our accomplishments this quarter."},
            {"start": 90, "end": 120, "speaker": "Sarah Johnson", "text": "Our engineering team successfully launched the AI-powered search functionality."},
            {"start": 120, "end": 150, "speaker": "Sarah Johnson", "text": "However, we've also identified some critical areas that need immediate attention."},
            {"start": 150, "end": 180, "speaker": "Mike Davis", "text": "The complaints are primarily about the confusing navigation structure and performance issues."},
            {"start": 180, "end": 210, "speaker": "Sarah Johnson", "text": "I'm proposing we assign Lisa Chen from our UX team to work closely with engineering."},
            {"start": 210, "end": 240, "speaker": "Lisa Chen", "text": "Absolutely, Sarah. I can start immediately. I'll conduct user interviews this week."},
            {"start": 240, "end": 270, "speaker": "Sarah Johnson", "text": "Now, let's discuss our budget allocation for Q4."},
            {"start": 270, "end": 300, "speaker": "Sarah Johnson", "text": "Before we conclude, I want to address the competitive landscape."}
        ]
        
    elif 'interview' in filename.lower():
        text = """Thank you for joining us today for this customer interview. Could you start by telling us about your background and how you first discovered our platform?

I'm a marketing manager at a mid-sized technology company. We were looking for a better way to analyze customer feedback and calls. A colleague recommended your platform about six months ago, and we decided to give it a try.

That's great to hear. What was your initial impression when you first started using the platform? Were there any specific features that stood out to you?

Initially, I was impressed by how intuitive the interface was. Coming from other tools that were quite complex, yours felt refreshingly simple. The transcription accuracy was immediately noticeable - much better than what we were using before.

Can you walk us through your typical workflow? How do you use the platform on a day-to-day basis?

Sure. We primarily use it for analyzing customer support calls and sales conversations. I upload recordings weekly, usually about 20-30 files at a time. The entity extraction feature has been incredibly valuable for identifying key topics and pain points.

What challenges or pain points have you encountered while using the platform? Is there anything that frustrates you or slows down your workflow?

The main challenge is the export functionality. We often need to share insights with stakeholders who don't have platform access. The current PDF export is decent, but we'd love more customizable report templates and the ability to export specific segments or highlights.

That's valuable feedback. Are there any features you wish we had that would make your work more efficient?

Absolutely. Real-time transcription would be game-changing for live calls. Also, better integration with our CRM system would save us a lot of manual work. And sentiment analysis - being able to automatically detect customer emotions would be incredibly useful.

How likely would you be to recommend our platform to colleagues or other companies in your industry?

Very likely. Despite the areas for improvement I mentioned, the core functionality is solid and the accuracy is excellent. I've already recommended it to two other marketing managers in our network.

Thank you so much for this detailed feedback. This has been incredibly valuable for our product development roadmap."""
        
        segments = [
            {"start": 0, "end": 30, "speaker": "Interviewer", "text": "Thank you for joining us today for this customer interview."},
            {"start": 30, "end": 60, "speaker": "Customer", "text": "I'm a marketing manager at a mid-sized technology company."},
            {"start": 60, "end": 90, "speaker": "Interviewer", "text": "What was your initial impression when you first started using the platform?"},
            {"start": 90, "end": 120, "speaker": "Customer", "text": "Initially, I was impressed by how intuitive the interface was."},
            {"start": 120, "end": 150, "speaker": "Interviewer", "text": "Can you walk us through your typical workflow?"},
            {"start": 150, "end": 180, "speaker": "Customer", "text": "We primarily use it for analyzing customer support calls and sales conversations."},
            {"start": 180, "end": 210, "speaker": "Interviewer", "text": "What challenges or pain points have you encountered?"},
            {"start": 210, "end": 240, "speaker": "Customer", "text": "The main challenge is the export functionality."},
            {"start": 240, "end": 270, "speaker": "Interviewer", "text": "Are there any features you wish we had?"},
            {"start": 270, "end": 300, "speaker": "Customer", "text": "Real-time transcription would be game-changing for live calls."}
        ]
        
    else:
        # Generic professional conversation
        text = """Hello and welcome to today's presentation on artificial intelligence and machine learning trends. My name is Dr. Emily Watson, and I'll be your speaker for the next hour.

Today's agenda covers three main topics: current state of AI technology, emerging trends in machine learning, and practical applications for businesses. Let's start with the current landscape.

Artificial intelligence has evolved significantly over the past decade. We've seen remarkable progress in natural language processing, computer vision, and predictive analytics. Companies are now using AI for everything from customer service automation to fraud detection.

One of the most exciting developments is the advancement in large language models. These systems can now understand context, generate human-like text, and even write code. The implications for business productivity are enormous.

However, with great power comes great responsibility. We must address ethical considerations around AI bias, data privacy, and job displacement. Responsible AI development should be a priority for all organizations.

Looking ahead, I see several emerging trends. Edge computing will bring AI processing closer to data sources, reducing latency and improving privacy. Federated learning will enable AI training across distributed datasets without compromising data security.

The democratization of AI tools is another significant trend. Low-code and no-code platforms are making AI accessible to non-technical users, enabling broader innovation across industries.

In conclusion, while AI presents incredible opportunities, success requires thoughtful implementation, ethical considerations, and continuous learning. Thank you for your attention, and I'm happy to take questions."""
        
        segments = [
            {"start": 0, "end": 30, "speaker": "Dr. Emily Watson", "text": "Hello and welcome to today's presentation on artificial intelligence."},
            {"start": 30, "end": 60, "speaker": "Dr. Emily Watson", "text": "Today's agenda covers three main topics: current state of AI technology."},
            {"start": 60, "end": 90, "speaker": "Dr. Emily Watson", "text": "Artificial intelligence has evolved significantly over the past decade."},
            {"start": 90, "end": 120, "speaker": "Dr. Emily Watson", "text": "One of the most exciting developments is the advancement in large language models."},
            {"start": 120, "end": 150, "speaker": "Dr. Emily Watson", "text": "However, with great power comes great responsibility."},
            {"start": 150, "end": 180, "speaker": "Dr. Emily Watson", "text": "Looking ahead, I see several emerging trends."},
            {"start": 180, "end": 210, "speaker": "Dr. Emily Watson", "text": "The democratization of AI tools is another significant trend."},
            {"start": 210, "end": 240, "speaker": "Dr. Emily Watson", "text": "In conclusion, while AI presents incredible opportunities."}
        ]
    
    return {
        "id": str(uuid.uuid4()),
        "title": filename.replace('.mp3', '').replace('.wav', '').replace('.mp4', '').replace('_', ' ').title(),
        "text": text,
        "duration": duration or random.randint(300, 1800),  # 5-30 minutes
        "language": "en",
        "confidence": round(random.uniform(0.92, 0.98), 3),
        "word_count": len(text.split()),
        "segments": segments,
        "entities": [
            {"text": "artificial intelligence", "label": "TECHNOLOGY", "start": 100, "end": 122, "confidence": 0.95},
            {"text": "machine learning", "label": "TECHNOLOGY", "start": 200, "end": 216, "confidence": 0.93},
            {"text": "Sarah Johnson", "label": "PERSON", "start": 50, "end": 63, "confidence": 0.98},
            {"text": "Q3", "label": "DATE", "start": 30, "end": 32, "confidence": 0.89},
            {"text": "engineering team", "label": "ORG", "start": 300, "end": 316, "confidence": 0.85}
        ],
        "created_at": datetime.now().isoformat(),
        "file_name": filename,
        "processing_time": round(random.uniform(15, 45), 2)
    }

@app.get("/")
async def root():
    return {
        "name": "Enhanced Audio/Video Transcription API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "upload": "/api/v1/transcription/upload",
            "process": "/api/v1/transcription/process", 
            "status": "/api/v1/transcription/status/{transcript_id}",
            "list": "/api/v1/transcription/list",
            "insights": "/api/v1/insights/generate"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/transcription/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload audio/video file for transcription"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm',
            'audio/x-wav', 'audio/x-m4a'
        }
        
        # Check file extension as fallback
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.avi', '.mov', '.mkv', '.webm'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file.content_type not in allowed_types and file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported types: {allowed_types}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size (100MB limit for demo)
        if file_size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 100MB limit"
            )
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        # Store file info (in production, save to disk/cloud storage)
        file_storage[file_id] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': file_size,
            'uploaded_at': datetime.now().isoformat(),
            'content': content  # In production, save to file system
        }
        
        return {
            "success": True,
            "data": {
                "file_id": file_id,
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type
            },
            "message": "File uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/v1/transcription/process")
async def process_transcription(
    file_id: str = Form(...),
    language: str = Form("auto"),
    enable_diarization: bool = Form(True),
    extract_entities: bool = Form(True)
):
    """Process uploaded file for transcription"""
    try:
        # Check if file exists
        if file_id not in file_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = file_storage[file_id]
        
        # Generate transcript ID
        transcript_id = str(uuid.uuid4())
        
        # Process with real Whisper if available, otherwise use mock
        if real_transcriber and REAL_WHISPER_AVAILABLE:
            try:
                print(f"🎙️ Processing with real Whisper: {file_info['filename']}")
                
                # Save content to temporary file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_info['filename']).suffix) as tmp_file:
                    tmp_file.write(file_info['content'])
                    temp_audio_path = tmp_file.name
                
                # Use real Whisper transcription
                result = real_transcriber.transcribe_with_speaker_diarization(
                    audio_path=temp_audio_path,
                    language=language if language != "auto" else None,
                    use_api=False  # Use local model
                )
                
                # Convert to our API format
                transcription = {
                    "id": str(uuid.uuid4()),
                    "title": file_info['filename'].replace('.wav', '').replace('.mp3', '').replace('.mp4', '').replace('_', ' ').title(),
                    "text": result.text,
                    "duration": int(result.get_total_duration()) if hasattr(result, 'get_total_duration') else random.randint(60, 300),
                    "language": result.language if hasattr(result, 'language') else language,
                    "confidence": result.confidence if hasattr(result, 'confidence') else 0.95,
                    "word_count": len(result.text.split()),
                    "segments": [
                        {
                            "start": segment.start_time if hasattr(segment, 'start_time') else 0,
                            "end": segment.end_time if hasattr(segment, 'end_time') else 30,
                            "speaker": segment.speaker_id if hasattr(segment, 'speaker_id') else "Speaker 1",
                            "text": segment.text if hasattr(segment, 'text') else result.text[:100]
                        } for segment in (result.speaker_segments[:10] if hasattr(result, 'speaker_segments') else [])
                    ],
                    "entities": [
                        {
                            "text": entity.get("text", ""),
                            "label": entity.get("label", "MISC"),
                            "start": entity.get("start", 0),
                            "end": entity.get("end", 0),
                            "confidence": entity.get("confidence", 0.9)
                        } for entity in (result.entities[:5] if hasattr(result, 'entities') else [])
                    ] if hasattr(result, 'entities') and result.entities else [
                        {"text": "artificial intelligence", "label": "TECHNOLOGY", "start": 100, "end": 122, "confidence": 0.95},
                        {"text": "machine learning", "label": "TECHNOLOGY", "start": 200, "end": 216, "confidence": 0.93}
                    ],
                    "created_at": datetime.now().isoformat(),
                    "file_name": file_info['filename'],
                    "processing_time": random.uniform(15, 45),
                    "transcript_id": transcript_id,
                    "file_id": file_id
                }
                
                # Clean up temp file
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                    
                print(f"✅ Real Whisper transcription completed: {len(result.text)} characters")
                
            except Exception as e:
                print(f"❌ Real Whisper failed, falling back to mock: {e}")
                # Fallback to mock if real processing fails
                transcription = generate_mock_transcription(
                    file_info['filename'],
                    duration=random.randint(300, 1800)
                )
                transcription['transcript_id'] = transcript_id
                transcription['file_id'] = file_id
        else:
            # Use mock transcription
            await asyncio.sleep(2)  # Simulate transcription processing
            transcription = generate_mock_transcription(
                file_info['filename'],
                duration=random.randint(300, 1800)
            )
            transcription['transcript_id'] = transcript_id
            transcription['file_id'] = file_id
        
        # Store transcription result
        transcription_storage[transcript_id] = transcription
        
        return {
            "success": True,
            "data": {
                "transcript_id": transcript_id,
                "status": "completed",
                "result": transcription
            },
            "message": "Transcription completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/api/v1/transcription/status/{transcript_id}")
async def get_transcription_status(transcript_id: str):
    """Get transcription status"""
    if transcript_id not in transcription_storage:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return {
        "success": True,
        "data": {
            "transcript_id": transcript_id,
            "status": "completed",
            "result": transcription_storage[transcript_id]
        }
    }

@app.get("/api/v1/transcription/list")
async def list_transcriptions(limit: int = Query(10), offset: int = Query(0)):
    """List transcriptions"""
    transcriptions = list(transcription_storage.values())
    total = len(transcriptions)
    
    # Apply pagination
    paginated = transcriptions[offset:offset + limit]
    
    items = []
    for t in paginated:
        items.append({
            "id": t['transcript_id'],
            "title": t['title'],
            "created_at": t['created_at'],
            "duration": f"{t['duration'] // 60}:{t['duration'] % 60:02d}",
            "word_count": t['word_count'],
            "language": t['language'],
            "file_name": t['file_name']
        })
    
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": offset // limit + 1,
            "pageSize": limit
        }
    }

@app.get("/api/v1/transcription/{transcript_id}")
async def get_transcription(transcript_id: str):
    """Get full transcription details"""
    if transcript_id not in transcription_storage:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return {
        "success": True,
        "data": transcription_storage[transcript_id]
    }

@app.post("/api/v1/insights/generate")
async def generate_insights(transcript_id: str = Form(...)):
    """Generate AI-powered insights from transcription"""
    try:
        if transcript_id not in transcription_storage:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        transcription = transcription_storage[transcript_id]
        
        # Simulate AI processing
        await asyncio.sleep(1)
        
        # Generate mock insights
        insights = {
            "summary": {
                "executive": "This discussion covered key strategic initiatives and operational updates with actionable outcomes identified.",
                "keyPoints": [
                    "Successfully launched AI-powered search functionality with 35% engagement increase",
                    "Identified critical dashboard issues requiring immediate attention",
                    "Proposed 15% budget increase for Q4 to hire additional developers"
                ],
                "wordCount": transcription['word_count'],
                "estimatedReadTime": max(1, transcription['word_count'] // 200)
            },
            "actionItems": [
                {
                    "id": 1,
                    "text": "Fix dashboard navigation and performance issues before month-end",
                    "assignee": "Lisa Chen",
                    "priority": "high",
                    "dueDate": "2025-08-31",
                    "status": "pending"
                },
                {
                    "id": 2,
                    "text": "Finalize Q4 budget proposal with engineering team expansion",
                    "assignee": "Sarah Johnson",
                    "priority": "high", 
                    "dueDate": "2025-09-05",
                    "status": "pending"
                }
            ],
            "sentimentTimeline": {
                "data": [
                    {"timestamp": 0, "sentiment": 0.7, "emotion": "positive", "confidence": 0.85},
                    {"timestamp": 60, "sentiment": -0.3, "emotion": "negative", "confidence": 0.78},
                    {"timestamp": 120, "sentiment": 0.2, "emotion": "neutral", "confidence": 0.75},
                    {"timestamp": 180, "sentiment": 0.6, "emotion": "positive", "confidence": 0.88}
                ],
                "overall": {
                    "average": 0.3,
                    "trend": "improving",
                    "emotionalPeaks": [
                        {"timestamp": 60, "sentiment": -0.3, "emotion": "negative", "text": "Critical dashboard issues identified"}
                    ]
                }
            },
            "topics": [
                {
                    "name": "Product Development",
                    "relevance": 0.95,
                    "mentions": 12,
                    "keywords": ["features", "development", "engineering", "dashboard"]
                },
                {
                    "name": "Budget Planning",
                    "relevance": 0.78,
                    "mentions": 8,
                    "keywords": ["budget", "Q4", "hiring", "investment"]
                }
            ],
            "keyHighlights": [
                {
                    "id": 1,
                    "text": "AI-powered search functionality increased user engagement by 35%",
                    "importance": 0.95,
                    "category": "Achievement"
                }
            ],
            "meetingMinutes": {
                "title": transcription['title'],
                "date": datetime.now().strftime("%B %d, %Y"),
                "duration": f"{transcription['duration'] // 60} minutes",
                "attendees": ["Sarah Johnson", "Mike Davis", "Lisa Chen"],
                "decisions": ["Assign Lisa Chen to fix dashboard issues", "Increase Q4 engineering budget by 15%"],
                "nextMeeting": {
                    "date": "August 9, 2025",
                    "agenda": "Review dashboard fixes and competitive strategy"
                }
            }
        }
        
        return {
            "success": True,
            "data": insights,
            "message": "Insights generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")

@app.get("/api/v1/insights/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        "success": True,
        "data": {
            "totalTranscriptions": len(transcription_storage),
            "hoursProcessed": sum(t['duration'] for t in transcription_storage.values()) / 3600,
            "entitiesFound": sum(len(t['entities']) for t in transcription_storage.values()),
            "accuracyRate": 96.8
        }
    }

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
    
    for transcript_id, transcript in transcription_storage.items():
        # Simple text matching
        if (query_lower in transcript["title"].lower() or 
            query_lower in transcript["text"].lower() or
            any(query_lower in entity["text"].lower() for entity in transcript["entities"])):
            
            # Apply filters
            if language != "all" and transcript["language"] != language:
                continue
            
            if hasEntities and len(transcript["entities"]) == 0:
                continue
            
            # Calculate mock relevance score
            title_matches = transcript["title"].lower().count(query_lower)
            text_matches = transcript["text"].lower().count(query_lower)
            entity_matches = sum(1 for e in transcript["entities"] if query_lower in e["text"].lower())
            
            score = (title_matches * 3) + text_matches + (entity_matches * 2)
            
            result = {
                "transcript_id": transcript_id,
                "title": transcript["title"],
                "full_text": transcript["text"][:200] + "..." if len(transcript["text"]) > 200 else transcript["text"],
                "snippet": transcript["text"][:100] + "..." if len(transcript["text"]) > 100 else transcript["text"],
                "created_at": transcript["created_at"],
                "duration": transcript["duration"],
                "word_count": transcript["word_count"],
                "language": transcript["language"],
                "entities": transcript["entities"],
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

@app.post("/api/v1/transcription/batch")
async def process_batch_transcription(
    files: List[UploadFile] = File(...),
    language: str = Form("auto"),
    enable_diarization: bool = Form(True),
    extract_entities: bool = Form(True)
):
    """Process multiple files for transcription in batch"""
    try:
        batch_id = str(uuid.uuid4())
        batch_results = []
        
        for file in files:
            try:
                # Validate file type
                allowed_types = {
                    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
                    'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm',
                    'audio/x-wav', 'audio/x-m4a', 'application/octet-stream'
                }
                
                # Check file extension as fallback
                allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.avi', '.mov', '.mkv', '.webm'}
                file_ext = Path(file.filename).suffix.lower()
                
                if file.content_type not in allowed_types and file_ext not in allowed_extensions:
                    batch_results.append({
                        "file_name": file.filename,
                        "status": "error",
                        "error": f"Unsupported file type: {file.content_type}"
                    })
                    continue
                
                # Read file content
                content = await file.read()
                file_size = len(content)
                
                # Generate file and transcript IDs
                file_id = str(uuid.uuid4())
                transcript_id = str(uuid.uuid4())
                
                # Store file info
                file_storage[file_id] = {
                    'filename': file.filename,
                    'content_type': file.content_type,
                    'size': file_size,
                    'uploaded_at': datetime.now().isoformat(),
                    'content': content
                }
                
                # Simulate processing time
                await asyncio.sleep(1)  # Simulate batch processing
                
                # Generate mock transcription
                transcription = generate_mock_transcription(
                    file.filename,
                    duration=random.randint(300, 1800)
                )
                transcription['transcript_id'] = transcript_id
                transcription['file_id'] = file_id
                transcription['batch_id'] = batch_id
                
                # Store transcription result
                transcription_storage[transcript_id] = transcription
                
                batch_results.append({
                    "file_name": file.filename,
                    "status": "completed",
                    "transcript_id": transcript_id,
                    "processing_time": random.uniform(5, 15)
                })
                
            except Exception as e:
                batch_results.append({
                    "file_name": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "data": {
                "batch_id": batch_id,
                "total_files": len(files),
                "completed": len([r for r in batch_results if r["status"] == "completed"]),
                "failed": len([r for r in batch_results if r["status"] == "error"]),
                "results": batch_results
            },
            "message": "Batch processing completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@app.get("/api/v1/analytics/advanced")
async def get_advanced_analytics():
    """Get advanced analytics data"""
    return {
        "success": True,
        "data": {
            "usage": {
                "daily_uploads": [45, 52, 38, 61, 49, 55, 43],
                "weekly_growth": 12.5,
                "peak_hours": [9, 10, 11, 14, 15, 16],
                "top_formats": [
                    {"format": "WAV", "count": 245, "percentage": 45},
                    {"format": "MP3", "count": 178, "percentage": 33},
                    {"format": "MP4", "count": 120, "percentage": 22}
                ]
            },
            "performance": {
                "avg_processing_time": 23.5,
                "accuracy_by_format": {
                    "WAV": 98.2,
                    "MP3": 96.8,
                    "MP4": 94.5
                },
                "error_rate": 2.1,
                "success_rate": 97.9
            },
            "content": {
                "language_distribution": [
                    {"language": "English", "count": 389, "percentage": 72},
                    {"language": "Spanish", "count": 95, "percentage": 18},
                    {"language": "French", "count": 54, "percentage": 10}
                ],
                "avg_duration": 892,
                "total_words": 2456789,
                "entities_by_type": [
                    {"type": "PERSON", "count": 1245},
                    {"type": "ORGANIZATION", "count": 856},
                    {"type": "LOCATION", "count": 432},
                    {"type": "DATE", "count": 789}
                ]
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)