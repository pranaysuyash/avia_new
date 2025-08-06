"""
Customer Support API Endpoints

Endpoints for support tickets, knowledge base, live chat, and feedback
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid
import json

from database.connection import get_db
from api.dependencies import get_current_user
from database.models_extended import (
    SupportTicket, TicketMessage, KnowledgeArticle,
    ConsentRecord, Campaign, CampaignAnalytics, Referral
)
from notifications.notification_manager import NotificationManager as NotificationService
from auth.email_service import EmailService
# from services.ai_service import AIService

router = APIRouter(prefix="/api/v1/support", tags=["Support"])

# Request/Response Models
class TicketCreate(BaseModel):
    subject: str
    description: str
    category: str
    priority: str = "medium"
    attachments: Optional[List[Dict[str, Any]]] = []

class TicketUpdate(BaseModel):
    status: Optional[str]
    priority: Optional[str]
    assigned_to: Optional[str]
    category: Optional[str]

class MessageCreate(BaseModel):
    content: str
    is_internal_note: bool = False
    attachments: Optional[List[Dict[str, Any]]] = []

class ArticleCreate(BaseModel):
    title: str
    content: str
    summary: Optional[str]
    article_type: str
    category: str
    tags: List[str] = []
    meta_description: Optional[str]
    keywords: List[str] = []

class ArticleUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]
    summary: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    status: Optional[str]

class FeedbackCreate(BaseModel):
    type: str  # feature_request, bug_report, testimonial, complaint
    title: Optional[str]
    description: str
    category: Optional[str]
    tags: List[str] = []

class SurveyResponse(BaseModel):
    survey_id: str
    answers: Dict[str, Any]

# Support Ticket Endpoints
@router.post("/tickets")
async def create_ticket(
    ticket: TicketCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new support ticket"""
    # Generate ticket number
    ticket_count = db.query(SupportTicket).count()
    ticket_number = f"SUP-{ticket_count + 1:06d}"
    
    # Create ticket
    db_ticket = SupportTicket(
        id=str(uuid.uuid4()),
        ticket_number=ticket_number,
        customer_id=current_user["id"],
        customer_email=current_user["email"],
        customer_name=current_user.get("name", current_user["email"]),
        **ticket.dict(exclude={"attachments"})
    )
    
    # Auto-detect sentiment
    # ai_service = AIService()
    # sentiment = await ai_service.analyze_sentiment(ticket.description)
    sentiment = {"sentiment": "neutral", "score": 0.5}  # Placeholder
    db_ticket.sentiment = sentiment
    
    # Set SLA deadline based on priority
    sla_hours = {"low": 48, "medium": 24, "high": 4, "critical": 1}
    db_ticket.sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours.get(ticket.priority, 24))
    
    db.add(db_ticket)
    db.flush()
    
    # Create initial message
    initial_message = TicketMessage(
        id=str(uuid.uuid4()),
        ticket_id=db_ticket.id,
        sender_id=current_user["id"],
        sender_type="customer",
        sender_name=current_user.get("name", current_user["email"]),
        content=ticket.description
    )
    db.add(initial_message)
    
    # Handle attachments
    if ticket.attachments:
        initial_message.attachments = ticket.attachments
    
    db.commit()
    
    # Send confirmation email
    email_service = EmailService()
    await email_service.send_template_email(
        to=current_user["email"],
        template="ticket_created",
        data={
            "ticket_number": ticket_number,
            "subject": ticket.subject,
            "sla_deadline": db_ticket.sla_deadline
        }
    )
    
    # Notify support team
    notification_service = NotificationService(db)
    await notification_service.notify_team(
        team="support",
        title=f"New {ticket.priority} priority ticket",
        message=f"{ticket.subject} - {ticket_number}",
        data={"ticket_id": db_ticket.id}
    )
    
    return db_ticket

@router.get("/tickets")
async def get_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    assigned_to_me: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get support tickets with filters"""
    query = db.query(SupportTicket)
    
    # For customers, only show their own tickets
    if current_user.get("role") == "customer":
        query = query.filter(SupportTicket.customer_id == current_user["id"])
    else:
        # For support agents
        if assigned_to_me:
            query = query.filter(SupportTicket.assigned_to == current_user["id"])
    
    # Apply filters
    if status:
        query = query.filter(SupportTicket.status == status)
    
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    
    if category:
        query = query.filter(SupportTicket.category == category)
    
    if search:
        query = query.filter(
            db.or_(
                SupportTicket.subject.ilike(f"%{search}%"),
                SupportTicket.description.ilike(f"%{search}%"),
                SupportTicket.ticket_number.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    tickets = query.order_by(
        SupportTicket.priority.desc(),
        SupportTicket.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "tickets": tickets
    }

@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ticket details with messages"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check access
    if current_user.get("role") == "customer" and ticket.customer_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get messages
    messages = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id
    ).order_by(TicketMessage.created_at).all()
    
    # Filter internal notes for customers
    if current_user.get("role") == "customer":
        messages = [m for m in messages if not m.is_internal_note]
    
    return {
        "ticket": ticket,
        "messages": messages
    }

@router.post("/tickets/{ticket_id}/messages")
async def add_ticket_message(
    ticket_id: str,
    message: MessageCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add message to ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check access
    if current_user.get("role") == "customer" and ticket.customer_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Customers can't create internal notes
    if current_user.get("role") == "customer" and message.is_internal_note:
        raise HTTPException(status_code=403, detail="Customers cannot create internal notes")
    
    # Create message
    sender_type = "agent" if current_user.get("role") in ["admin", "support"] else "customer"
    
    db_message = TicketMessage(
        id=str(uuid.uuid4()),
        ticket_id=ticket_id,
        sender_id=current_user["id"],
        sender_type=sender_type,
        sender_name=current_user.get("name", current_user["email"]),
        **message.dict()
    )
    
    db.add(db_message)
    
    # Update ticket
    ticket.updated_at = datetime.utcnow()
    ticket.response_count += 1
    
    # Track first response time for agents
    if sender_type == "agent" and not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()
    
    # Update status
    if ticket.status == "waiting_customer" and sender_type == "customer":
        ticket.status = "open"
    elif ticket.status == "open" and sender_type == "agent":
        ticket.status = "waiting_customer"
    
    db.commit()
    
    # Send notifications
    notification_service = NotificationService(db)
    
    if sender_type == "customer" and ticket.assigned_to:
        # Notify assigned agent
        await notification_service.send_notification(
            user_id=ticket.assigned_to,
            title=f"New message on ticket {ticket.ticket_number}",
            message=message.content[:100] + "...",
            type="ticket_message",
            data={"ticket_id": ticket_id}
        )
    elif sender_type == "agent":
        # Notify customer
        email_service = EmailService()
        await email_service.send_template_email(
            to=ticket.customer_email,
            template="ticket_reply",
            data={
                "ticket_number": ticket.ticket_number,
                "message": message.content,
                "agent_name": current_user.get("name")
            }
        )
    
    return db_message

@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    update: TicketUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ticket (agents only)"""
    if current_user.get("role") not in ["admin", "support"]:
        raise HTTPException(status_code=403, detail="Only support agents can update tickets")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update fields
    for field, value in update.dict(exclude_unset=True).items():
        setattr(ticket, field, value)
    
    ticket.updated_at = datetime.utcnow()
    
    # Track resolution
    if update.status == "resolved" and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
    
    db.commit()
    
    return ticket

# Knowledge Base Endpoints
@router.get("/articles")
async def search_articles(
    q: Optional[str] = None,
    category: Optional[str] = None,
    type: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search knowledge base articles"""
    query = db.query(KnowledgeArticle).filter(KnowledgeArticle.status == "published")
    
    if category:
        query = query.filter(KnowledgeArticle.category == category)
    
    if type:
        query = query.filter(KnowledgeArticle.article_type == type)
    
    if tags:
        # Filter by any of the provided tags
        query = query.filter(
            db.or_(*[KnowledgeArticle.tags.contains([tag]) for tag in tags])
        )
    
    if q:
        # Full-text search
        query = query.filter(
            db.or_(
                KnowledgeArticle.title.ilike(f"%{q}%"),
                KnowledgeArticle.content.ilike(f"%{q}%"),
                KnowledgeArticle.summary.ilike(f"%{q}%")
            )
        )
    
    # Order by relevance (view count for now)
    query = query.order_by(KnowledgeArticle.view_count.desc())
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    articles = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "articles": articles
    }

@router.get("/articles/{article_id}")
async def get_article(
    article_id: str,
    db: Session = Depends(get_db)
):
    """Get article details"""
    article = db.query(KnowledgeArticle).filter(
        KnowledgeArticle.id == article_id,
        KnowledgeArticle.status == "published"
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    article.view_count += 1
    db.commit()
    
    # Get related articles
    related = db.query(KnowledgeArticle).filter(
        KnowledgeArticle.id != article_id,
        KnowledgeArticle.status == "published",
        db.or_(
            KnowledgeArticle.category == article.category,
            KnowledgeArticle.tags.overlap(article.tags)
        )
    ).limit(5).all()
    
    return {
        "article": article,
        "related": related
    }

@router.post("/articles/{article_id}/feedback")
async def submit_article_feedback(
    article_id: str,
    helpful: bool = Body(...),
    comments: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit article feedback"""
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Update counters
    if helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1
    
    db.commit()
    
    # Log feedback for analysis
    if comments:
        # Store in feedback table or analytics
        pass
    
    return {"status": "success"}

# Live Chat WebSocket
@router.websocket("/chat/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for live chat"""
    await websocket.accept()
    
    # Store connection
    chat_connections = getattr(chat_websocket, "connections", {})
    if chat_id not in chat_connections:
        chat_connections[chat_id] = []
    chat_connections[chat_id].append(websocket)
    chat_websocket.connections = chat_connections
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Broadcast to all participants in the chat
            for connection in chat_connections.get(chat_id, []):
                if connection != websocket:
                    await connection.send_json(data)
            
            # Store message in database
            # ... (implementation depends on chat storage model)
            
    except WebSocketDisconnect:
        # Remove connection
        chat_connections[chat_id].remove(websocket)
        if not chat_connections[chat_id]:
            del chat_connections[chat_id]

# Feedback Endpoints
@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit customer feedback"""
    # Store feedback (using a simplified model for now)
    # In production, use proper feedback model
    
    # For feature requests, create in product backlog
    if feedback.type == "feature_request":
        # Create feature request
        pass
    
    # For bugs, create ticket
    elif feedback.type == "bug_report":
        ticket = TicketCreate(
            subject=feedback.title or "Bug Report",
            description=feedback.description,
            category="bug",
            priority="high"
        )
        return await create_ticket(ticket, current_user, db)
    
    return {"status": "success", "message": "Feedback submitted"}

@router.get("/surveys/active")
async def get_active_surveys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active surveys for user"""
    # Return active surveys based on user segment, recent activity, etc.
    # Simplified for now
    
    surveys = [
        {
            "id": "nps_q4_2024",
            "title": "How likely are you to recommend us?",
            "type": "nps",
            "questions": [
                {
                    "id": "nps_score",
                    "type": "scale",
                    "text": "On a scale of 0-10, how likely are you to recommend our service?",
                    "min": 0,
                    "max": 10
                },
                {
                    "id": "nps_reason",
                    "type": "text",
                    "text": "What's the primary reason for your score?",
                    "required": False
                }
            ]
        }
    ]
    
    return surveys

@router.post("/surveys/{survey_id}/responses")
async def submit_survey_response(
    survey_id: str,
    response: SurveyResponse,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit survey response"""
    # Store survey response
    # Calculate NPS if applicable
    
    # Thank user
    notification_service = NotificationService(db)
    await notification_service.send_notification(
        user_id=current_user["id"],
        title="Thank you for your feedback!",
        message="Your response helps us improve our service.",
        type="survey_complete"
    )
    
    return {"status": "success"}

# Support Metrics Endpoint
@router.get("/metrics")
async def get_support_metrics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get support metrics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Default to last 30 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()
    
    # Get tickets in period
    tickets = db.query(SupportTicket).filter(
        SupportTicket.created_at.between(date_from, date_to)
    ).all()
    
    # Calculate metrics
    total_tickets = len(tickets)
    resolved_tickets = len([t for t in tickets if t.status == "resolved"])
    
    # Average response time
    response_times = []
    for ticket in tickets:
        if ticket.first_response_at:
            response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 60
            response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Average resolution time
    resolution_times = []
    for ticket in tickets:
        if ticket.resolved_at:
            resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            resolution_times.append(resolution_time)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # SLA compliance
    sla_met = len([
        t for t in tickets
        if t.resolved_at and t.sla_deadline and t.resolved_at <= t.sla_deadline
    ])
    sla_total = len([t for t in tickets if t.sla_deadline])
    sla_compliance = (sla_met / sla_total * 100) if sla_total else 100
    
    # Satisfaction scores
    rated_tickets = [t for t in tickets if t.satisfaction_rating]
    avg_satisfaction = sum(t.satisfaction_rating for t in rated_tickets) / len(rated_tickets) if rated_tickets else 0
    
    # Tickets by category
    tickets_by_category = {}
    for ticket in tickets:
        category = ticket.category or "uncategorized"
        tickets_by_category[category] = tickets_by_category.get(category, 0) + 1
    
    # Tickets by priority
    tickets_by_priority = {}
    for ticket in tickets:
        priority = ticket.priority
        tickets_by_priority[priority] = tickets_by_priority.get(priority, 0) + 1
    
    return {
        "total_tickets": total_tickets,
        "resolved_tickets": resolved_tickets,
        "resolution_rate": (resolved_tickets / total_tickets * 100) if total_tickets else 0,
        "avg_response_time_minutes": avg_response_time,
        "avg_resolution_time_hours": avg_resolution_time,
        "sla_compliance_percentage": sla_compliance,
        "avg_satisfaction_rating": avg_satisfaction,
        "tickets_by_category": tickets_by_category,
        "tickets_by_priority": tickets_by_priority
    }