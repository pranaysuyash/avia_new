"""
Enterprise Sales API Endpoints

Endpoints for managing sales leads, opportunities, and activities
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid

from database.connection import get_db
from api.dependencies import get_current_user
from database.models_extended import SalesLead, SalesActivity, SalesOpportunity, LeadStatus
from notifications.notification_manager import NotificationManager as NotificationService
from services.usage_analytics_service import UsageAnalyticsService as AnalyticsService

router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])

# Request/Response Models
class LeadCreate(BaseModel):
    company_name: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    use_case: Optional[str]
    budget_range: Optional[str]
    source: Optional[str]

class LeadUpdate(BaseModel):
    status: Optional[LeadStatus]
    score: Optional[int]
    priority: Optional[str]
    assigned_to: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    use_case: Optional[str]
    budget_range: Optional[str]

class ActivityCreate(BaseModel):
    lead_id: str
    activity_type: str  # email, call, meeting, demo
    subject: str
    notes: Optional[str]
    scheduled_at: Optional[datetime]
    outcome: Optional[str]
    next_steps: Optional[str]

class OpportunityCreate(BaseModel):
    lead_id: str
    name: str
    amount: float
    probability: int = Field(ge=0, le=100)
    expected_close_date: datetime
    products: List[Dict[str, Any]]
    custom_terms: Optional[Dict[str, Any]]
    stage: str

class LeadResponse(BaseModel):
    id: str
    company_name: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    status: str
    score: int
    priority: str
    assigned_to: Optional[str]
    created_at: datetime
    activities_count: int
    opportunities_count: int
    total_value: float

class PipelineMetrics(BaseModel):
    total_leads: int
    qualified_leads: int
    opportunities: int
    total_pipeline_value: float
    average_deal_size: float
    conversion_rate: float
    leads_by_status: Dict[str, int]
    opportunities_by_stage: Dict[str, int]
    top_industries: List[Dict[str, Any]]
    forecast: Dict[str, float]

# Endpoints
@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sales lead"""
    # Create lead
    db_lead = SalesLead(
        id=str(uuid.uuid4()),
        **lead.dict(),
        created_by=current_user["id"]
    )
    
    # Auto-score lead based on criteria
    score = calculate_lead_score(lead)
    db_lead.score = score
    
    # Auto-assign based on round-robin or territory
    db_lead.assigned_to = assign_lead_to_rep(lead, db)
    
    db.add(db_lead)
    db.commit()
    
    # Send notification to assigned rep
    if db_lead.assigned_to:
        notification_service = NotificationService(db)
        await notification_service.send_notification(
            user_id=db_lead.assigned_to,
            title="New Lead Assigned",
            message=f"New lead from {db_lead.company_name} has been assigned to you",
            type="sales_lead",
            data={"lead_id": db_lead.id}
        )
    
    # Track analytics
    analytics = AnalyticsService(db)
    analytics.track_event("lead_created", {
        "lead_id": db_lead.id,
        "source": lead.source,
        "score": score,
        "user_id": current_user["id"]
    })
    
    return format_lead_response(db_lead, db)

@router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    status: Optional[LeadStatus] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales leads with filters"""
    query = db.query(SalesLead)
    
    # Apply filters
    if status:
        query = query.filter(SalesLead.status == status)
    
    if assigned_to:
        query = query.filter(SalesLead.assigned_to == assigned_to)
    elif not current_user.get("is_admin"):
        # Non-admins only see their own leads
        query = query.filter(SalesLead.assigned_to == current_user["id"])
    
    if priority:
        query = query.filter(SalesLead.priority == priority)
    
    if min_score is not None:
        query = query.filter(SalesLead.score >= min_score)
    
    if search:
        query = query.filter(
            db.or_(
                SalesLead.company_name.ilike(f"%{search}%"),
                SalesLead.contact_name.ilike(f"%{search}%"),
                SalesLead.contact_email.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    leads = query.order_by(SalesLead.created_at.desc()).offset(skip).limit(limit).all()
    
    return [format_lead_response(lead, db) for lead in leads]

@router.get("/leads/{lead_id}")
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get lead details with full history"""
    lead = db.query(SalesLead).filter(SalesLead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check access
    if not current_user.get("is_admin") and lead.assigned_to != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get full details including activities and opportunities
    activities = db.query(SalesActivity).filter(
        SalesActivity.lead_id == lead_id
    ).order_by(SalesActivity.created_at.desc()).all()
    
    opportunities = db.query(SalesOpportunity).filter(
        SalesOpportunity.lead_id == lead_id
    ).all()
    
    response = format_lead_response(lead, db)
    response["activities"] = activities
    response["opportunities"] = opportunities
    
    return response

@router.put("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    update: LeadUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update lead information"""
    lead = db.query(SalesLead).filter(SalesLead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check access
    if not current_user.get("is_admin") and lead.assigned_to != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    for field, value in update.dict(exclude_unset=True).items():
        setattr(lead, field, value)
    
    lead.updated_at = datetime.utcnow()
    db.commit()
    
    # Log activity
    activity = SalesActivity(
        id=str(uuid.uuid4()),
        lead_id=lead_id,
        activity_type="status_change",
        subject=f"Lead status updated to {lead.status.value}",
        notes=f"Updated by {current_user['email']}",
        created_by=current_user["id"]
    )
    db.add(activity)
    db.commit()
    
    return format_lead_response(lead, db)

@router.post("/activities")
async def create_activity(
    activity: ActivityCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log sales activity"""
    # Verify lead exists and user has access
    lead = db.query(SalesLead).filter(SalesLead.id == activity.lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not current_user.get("is_admin") and lead.assigned_to != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create activity
    db_activity = SalesActivity(
        id=str(uuid.uuid4()),
        **activity.dict(),
        created_by=current_user["id"]
    )
    
    if activity.outcome:
        db_activity.completed_at = datetime.utcnow()
    
    db.add(db_activity)
    
    # Update lead's last activity
    lead.updated_at = datetime.utcnow()
    
    db.commit()
    
    return db_activity

@router.post("/opportunities")
async def create_opportunity(
    opportunity: OpportunityCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create sales opportunity"""
    # Verify lead exists and user has access
    lead = db.query(SalesLead).filter(SalesLead.id == opportunity.lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not current_user.get("is_admin") and lead.assigned_to != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create opportunity
    db_opportunity = SalesOpportunity(
        id=str(uuid.uuid4()),
        **opportunity.dict()
    )
    
    db.add(db_opportunity)
    
    # Update lead status
    lead.status = LeadStatus.PROPOSAL
    lead.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Send notification
    notification_service = NotificationService(db)
    await notification_service.send_notification(
        user_id=lead.assigned_to,
        title="New Opportunity Created",
        message=f"${opportunity.amount:,.2f} opportunity for {lead.company_name}",
        type="opportunity",
        data={"opportunity_id": db_opportunity.id}
    )
    
    return db_opportunity

@router.get("/pipeline/metrics")
async def get_pipeline_metrics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales pipeline metrics and forecasts"""
    # Default to last 90 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=90)
    if not date_to:
        date_to = datetime.utcnow()
    
    # Get leads
    query = db.query(SalesLead).filter(
        SalesLead.created_at.between(date_from, date_to)
    )
    
    if not current_user.get("is_admin"):
        query = query.filter(SalesLead.assigned_to == current_user["id"])
    
    leads = query.all()
    
    # Calculate metrics
    metrics = PipelineMetrics(
        total_leads=len(leads),
        qualified_leads=len([l for l in leads if l.status in [LeadStatus.QUALIFIED, LeadStatus.PROPOSAL]]),
        opportunities=0,
        total_pipeline_value=0,
        average_deal_size=0,
        conversion_rate=0,
        leads_by_status={},
        opportunities_by_stage={},
        top_industries=[],
        forecast={}
    )
    
    # Leads by status
    for lead in leads:
        status = lead.status.value
        metrics.leads_by_status[status] = metrics.leads_by_status.get(status, 0) + 1
    
    # Get opportunities
    opportunity_query = db.query(SalesOpportunity)
    
    if not current_user.get("is_admin"):
        # Join with leads to check ownership
        opportunity_query = opportunity_query.join(SalesLead).filter(
            SalesLead.assigned_to == current_user["id"]
        )
    
    opportunities = opportunity_query.all()
    
    metrics.opportunities = len(opportunities)
    
    # Calculate pipeline value and stages
    for opp in opportunities:
        if not opp.is_won and not opp.closed_at:
            metrics.total_pipeline_value += opp.amount * (opp.probability / 100)
        
        stage = opp.stage
        metrics.opportunities_by_stage[stage] = metrics.opportunities_by_stage.get(stage, 0) + 1
    
    # Average deal size
    if opportunities:
        metrics.average_deal_size = sum(o.amount for o in opportunities) / len(opportunities)
    
    # Conversion rate
    closed_won = len([l for l in leads if l.status == LeadStatus.CLOSED_WON])
    if leads:
        metrics.conversion_rate = (closed_won / len(leads)) * 100
    
    # Top industries
    industry_counts = {}
    for lead in leads:
        if lead.industry:
            industry_counts[lead.industry] = industry_counts.get(lead.industry, 0) + 1
    
    metrics.top_industries = [
        {"industry": k, "count": v}
        for k, v in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Forecast (simplified)
    current_month_value = sum(
        o.amount * (o.probability / 100)
        for o in opportunities
        if o.expected_close_date.month == datetime.utcnow().month
    )
    
    metrics.forecast = {
        "current_month": current_month_value,
        "next_month": current_month_value * 1.1,  # Simple growth projection
        "quarter": current_month_value * 3.2
    }
    
    return metrics

@router.post("/leads/{lead_id}/convert")
async def convert_lead(
    lead_id: str,
    won: bool = Body(...),
    notes: str = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convert lead to won/lost"""
    lead = db.query(SalesLead).filter(SalesLead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not current_user.get("is_admin") and lead.assigned_to != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update lead status
    lead.status = LeadStatus.CLOSED_WON if won else LeadStatus.CLOSED_LOST
    lead.updated_at = datetime.utcnow()
    
    # Close opportunities
    opportunities = db.query(SalesOpportunity).filter(
        SalesOpportunity.lead_id == lead_id
    ).all()
    
    for opp in opportunities:
        opp.is_won = won
        opp.closed_at = datetime.utcnow()
    
    # Log activity
    activity = SalesActivity(
        id=str(uuid.uuid4()),
        lead_id=lead_id,
        activity_type="conversion",
        subject=f"Lead {'won' if won else 'lost'}",
        notes=notes or f"Converted by {current_user['email']}",
        created_by=current_user["id"],
        completed_at=datetime.utcnow()
    )
    db.add(activity)
    
    db.commit()
    
    # Track analytics
    analytics = AnalyticsService(db)
    analytics.track_event("lead_converted", {
        "lead_id": lead_id,
        "won": won,
        "value": sum(o.amount for o in opportunities) if won else 0,
        "user_id": current_user["id"]
    })
    
    return {"status": "success", "lead_status": lead.status.value}

# Helper functions
def calculate_lead_score(lead: LeadCreate) -> int:
    """Calculate lead score based on various factors"""
    score = 50  # Base score
    
    # Company size scoring
    size_scores = {
        "1-10": 10,
        "11-50": 20,
        "51-200": 30,
        "201-1000": 40,
        "1000+": 50
    }
    score += size_scores.get(lead.company_size, 0)
    
    # Budget scoring
    budget_scores = {
        "< $10k": 10,
        "$10k-$50k": 20,
        "$50k-$100k": 30,
        "$100k-$500k": 40,
        "> $500k": 50
    }
    score += budget_scores.get(lead.budget_range, 0)
    
    # Contact info completeness
    if lead.contact_email:
        score += 10
    if lead.contact_phone:
        score += 5
    
    # Use case provided
    if lead.use_case:
        score += 15
    
    return min(score, 100)  # Cap at 100

def assign_lead_to_rep(lead: LeadCreate, db: Session) -> Optional[str]:
    """Assign lead to sales rep based on rules"""
    # Simple round-robin assignment
    # In production, implement territory-based or skill-based routing
    
    # Get all active sales reps
    # For now, return None (manual assignment)
    return None

def format_lead_response(lead: SalesLead, db: Session) -> dict:
    """Format lead data for response"""
    # Get counts
    activities_count = db.query(SalesActivity).filter(
        SalesActivity.lead_id == lead.id
    ).count()
    
    opportunities = db.query(SalesOpportunity).filter(
        SalesOpportunity.lead_id == lead.id
    ).all()
    
    opportunities_count = len(opportunities)
    total_value = sum(o.amount for o in opportunities)
    
    return {
        "id": lead.id,
        "company_name": lead.company_name,
        "contact_name": lead.contact_name,
        "contact_email": lead.contact_email,
        "status": lead.status.value,
        "score": lead.score,
        "priority": lead.priority,
        "assigned_to": lead.assigned_to,
        "created_at": lead.created_at,
        "activities_count": activities_count,
        "opportunities_count": opportunities_count,
        "total_value": total_value
    }