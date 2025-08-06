"""
Meeting Automation API Endpoints (Task 64)
FastAPI endpoints for meeting processing and automation
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import json
import io
import logging

from ...meeting_automation_system import (
    MeetingAutomationSystem, MeetingMinutes, MeetingType,
    TaskPriority, ActionItem, Attendee
)
from ..auth import get_current_user
from ..models import User
from database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meetings", tags=["meeting-automation"])

# Pydantic models
class MeetingTranscript(BaseModel):
    segments: List[Dict[str, Any]]
    speakers: Optional[Dict[str, str]] = {}
    metadata: Optional[Dict[str, Any]] = {}

class ProcessingOptions(BaseModel):
    send_email: bool = False
    email_recipients: List[str] = []
    create_calendar_event: bool = False
    calendar_type: str = "google"
    create_tasks: bool = False
    pm_platform: str = "jira"
    share_to_collaboration: bool = False
    collab_platform: str = "slack"
    collab_channel: Optional[str] = None

class MeetingProcessRequest(BaseModel):
    transcript: MeetingTranscript
    options: ProcessingOptions = ProcessingOptions()

class ActionItemUpdate(BaseModel):
    action_id: str
    status: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None

class MeetingTemplate(BaseModel):
    name: str
    meeting_type: str
    agenda: List[str]
    description: Optional[str] = None

# Initialize meeting system
meeting_system = MeetingAutomationSystem()

@router.post("/process")
async def process_meeting(
    request: MeetingProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a meeting transcript and generate minutes"""
    try:
        # Convert request to dict format
        transcript_data = request.transcript.dict()
        options = request.options.dict()
        
        # Add user context
        transcript_data['metadata'] = transcript_data.get('metadata', {})
        transcript_data['metadata']['user_id'] = current_user.id
        transcript_data['metadata']['user_email'] = current_user.email
        
        # Process meeting
        results = meeting_system.process_meeting(
            transcript_data,
            transcript_data.get('metadata'),
            options
        )
        
        # Store in database (if implemented)
        # db_meeting = store_meeting_minutes(db, results, current_user.id)
        
        # Background tasks for integrations
        if options['send_email'] and results.get('meeting_minutes'):
            background_tasks.add_task(
                send_email_async,
                results['meeting_minutes'],
                options['email_recipients']
            )
        
        return {
            "status": "success",
            "meeting_id": results['meeting_minutes']['meeting_id'] if results.get('meeting_minutes') else None,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a transcript file for processing"""
    try:
        # Validate file type
        allowed_types = ['application/json', 'text/plain', 'text/vtt', 'text/srt']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Parse based on file type
        if file.content_type == 'application/json':
            transcript_data = json.loads(text)
        else:
            # Convert text formats to transcript format
            lines = text.strip().split('\n')
            segments = []
            
            for i, line in enumerate(lines):
                if line.strip():
                    # Simple parsing - can be enhanced for specific formats
                    segments.append({
                        'text': line.strip(),
                        'speaker': 'Speaker',
                        'start': i * 5,
                        'end': (i + 1) * 5
                    })
            
            transcript_data = {
                'segments': segments,
                'metadata': {
                    'filename': file.filename,
                    'uploaded_by': current_user.email
                }
            }
        
        return {
            "status": "success",
            "transcript": transcript_data,
            "filename": file.filename
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error uploading transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_meeting_history(
    skip: int = 0,
    limit: int = 20,
    meeting_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's meeting history"""
    try:
        # In a real implementation, would query from database
        # For now, return mock data
        meetings = []
        
        return {
            "status": "success",
            "meetings": meetings,
            "total": len(meetings),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching meeting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meeting/{meeting_id}")
async def get_meeting_details(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed meeting information"""
    try:
        # In a real implementation, would fetch from database
        # For now, return mock data
        
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    except Exception as e:
        logger.error(f"Error fetching meeting details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meeting/{meeting_id}/action-items")
async def update_action_items(
    meeting_id: str,
    updates: List[ActionItemUpdate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update action items for a meeting"""
    try:
        # In a real implementation, would update in database
        updated_items = []
        
        for update in updates:
            # Update logic here
            updated_items.append({
                "action_id": update.action_id,
                "status": "updated"
            })
        
        return {
            "status": "success",
            "updated_items": updated_items
        }
        
    except Exception as e:
        logger.error(f"Error updating action items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meeting/{meeting_id}/export/{format}")
async def export_meeting(
    meeting_id: str,
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export meeting in specified format (html, markdown, pdf)"""
    try:
        # Validate format
        if format not in ['html', 'markdown', 'pdf']:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Supported: html, markdown, pdf"
            )
        
        # In a real implementation, would fetch meeting from database
        # For now, use mock data
        mock_minutes = MeetingMinutes(
            meeting_id=meeting_id,
            title="Sample Meeting",
            date=datetime.now(),
            duration=3600,
            meeting_type=MeetingType.GENERAL,
            attendees=[],
            agenda=[],
            discussion_points=[],
            decisions=[],
            action_items=[],
            key_insights=[]
        )
        
        # Generate report
        report = meeting_system.generate_meeting_report(mock_minutes, format)
        
        # Set appropriate content type
        content_types = {
            'html': 'text/html',
            'markdown': 'text/markdown',
            'pdf': 'application/pdf'
        }
        
        return StreamingResponse(
            io.StringIO(report),
            media_type=content_types[format],
            headers={
                "Content-Disposition": f"attachment; filename=meeting_{meeting_id}.{format}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates")
async def create_template(
    template: MeetingTemplate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a meeting template"""
    try:
        # In a real implementation, would save to database
        template_data = template.dict()
        template_data['created_by'] = current_user.id
        template_data['created_at'] = datetime.now()
        
        return {
            "status": "success",
            "template_id": "TMPL-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "template": template_data
        }
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available meeting templates"""
    try:
        # Default templates
        templates = [
            {
                "id": "default-sprint-planning",
                "name": "Sprint Planning",
                "meeting_type": "planning",
                "agenda": [
                    "Review previous sprint",
                    "Discuss sprint goals",
                    "Review backlog items",
                    "Estimate story points",
                    "Assign tasks"
                ]
            },
            {
                "id": "default-standup",
                "name": "Daily Standup",
                "meeting_type": "standup",
                "agenda": [
                    "What did you complete yesterday?",
                    "What will you work on today?",
                    "Are there any blockers?"
                ]
            },
            {
                "id": "default-retrospective",
                "name": "Retrospective",
                "meeting_type": "retrospective",
                "agenda": [
                    "What went well?",
                    "What could be improved?",
                    "Action items for next sprint"
                ]
            }
        ]
        
        return {
            "status": "success",
            "templates": templates
        }
        
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/test")
async def test_integration(
    service: str,
    config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Test integration with external service"""
    try:
        # Validate service
        valid_services = ['email', 'calendar', 'jira', 'asana', 'trello', 'slack', 'teams']
        if service not in valid_services:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service. Valid services: {', '.join(valid_services)}"
            )
        
        # Test connection (mock implementation)
        # In real implementation, would actually test the service
        test_results = {
            'email': {'status': 'success', 'message': 'SMTP connection successful'},
            'calendar': {'status': 'success', 'message': 'Calendar API connected'},
            'jira': {'status': 'success', 'message': 'Jira API connected'},
            'asana': {'status': 'error', 'message': 'Invalid access token'},
            'trello': {'status': 'success', 'message': 'Trello board accessible'},
            'slack': {'status': 'success', 'message': 'Slack webhook verified'},
            'teams': {'status': 'success', 'message': 'Teams webhook verified'}
        }
        
        result = test_results.get(service, {'status': 'error', 'message': 'Unknown service'})
        
        return {
            "service": service,
            "test_result": result,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error testing integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_meeting_stats(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meeting statistics for the user"""
    try:
        # In real implementation, would calculate from database
        stats = {
            "total_meetings": 42,
            "total_duration_hours": 67.5,
            "average_duration_minutes": 45,
            "meetings_by_type": {
                "standup": 20,
                "planning": 8,
                "review": 6,
                "retrospective": 4,
                "general": 4
            },
            "action_items": {
                "total": 126,
                "completed": 89,
                "pending": 37,
                "completion_rate": 0.706
            },
            "top_attendees": [
                {"name": "John Smith", "meetings": 35},
                {"name": "Sarah Johnson", "meetings": 28},
                {"name": "Mike Wilson", "meetings": 24}
            ],
            "busiest_days": [
                {"day": "Monday", "meetings": 12},
                {"day": "Wednesday", "meetings": 10},
                {"day": "Friday", "meetings": 8}
            ]
        }
        
        return {
            "status": "success",
            "stats": stats,
            "period": {
                "from": date_from or "all_time",
                "to": date_to or "current"
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching meeting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def send_email_async(meeting_minutes: Dict[str, Any], recipients: List[str]):
    """Send email in background"""
    try:
        # Convert dict back to MeetingMinutes object
        # In real implementation, would use the email integration
        logger.info(f"Sending email to {len(recipients)} recipients")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

# Helper functions
def store_meeting_minutes(db: Session, results: Dict[str, Any], user_id: int):
    """Store meeting minutes in database"""
    # Implementation would store in database
    pass