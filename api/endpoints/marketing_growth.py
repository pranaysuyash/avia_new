"""
Marketing and Growth API Endpoints

Endpoints for campaigns, referrals, analytics, and growth tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field, EmailStr, HttpUrl
import uuid

from database.connection import get_db
from api.dependencies import get_current_user, get_admin_user
from database.models_extended import (
    Campaign, CampaignMetrics, ReferralProgram, Referral,
    EmailCampaign, ContentMarketing
)
from auth.email_service import EmailService
from services.usage_analytics_service import UsageAnalyticsService as AnalyticsService
# from marketing_growth import (
#     ReferralSystem, ReferralReward,
#     MarketingAutomation, CampaignStatus,
#     GrowthAnalytics, Channel,
#     ABTestingEngine, TestStatus
# )

# Placeholder classes
class ReferralSystem: pass
class ReferralReward: pass
class MarketingAutomation: pass
class CampaignStatus: pass
class GrowthAnalytics: pass
class Channel: pass
class ABTestingEngine: pass
class TestStatus: pass

router = APIRouter(prefix="/api/v1/marketing", tags=["Marketing & Growth"])

# Request/Response Models
class CampaignCreate(BaseModel):
    name: str
    type: str  # email, social, content, referral
    description: str
    target_audience: Dict[str, Any]
    budget: Optional[float]
    start_date: datetime
    end_date: Optional[datetime]
    goals: Dict[str, float]  # e.g., {"conversions": 100, "signups": 500}

class EmailCampaignCreate(BaseModel):
    subject: str
    content_html: str
    content_text: str
    segment_filters: Dict[str, Any]
    send_time: Optional[datetime]
    test_percentage: Optional[float] = 0

class ReferralProgramCreate(BaseModel):
    name: str
    reward_type: str  # credit, discount, feature
    referrer_reward: Dict[str, Any]
    referee_reward: Dict[str, Any]
    max_referrals: Optional[int]
    valid_days: int = 90

class ABTestCreate(BaseModel):
    name: str
    feature: str
    variants: List[Dict[str, Any]]
    traffic_allocation: Dict[str, float]
    success_metrics: List[str]
    minimum_sample_size: int = 1000

class ContentCreate(BaseModel):
    title: str
    type: str  # blog, video, podcast, webinar
    content_url: HttpUrl
    description: str
    tags: List[str]
    target_personas: List[str]
    cta_url: Optional[HttpUrl]

# Campaign Management
@router.post("/campaigns", response_model=Dict[str, Any])
async def create_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create marketing campaign"""
    # Create campaign record
    db_campaign = Campaign(
        id=str(uuid.uuid4()),
        name=campaign.name,
        type=campaign.type,
        description=campaign.description,
        target_audience=campaign.target_audience,
        budget=campaign.budget,
        spent=0,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        goals=campaign.goals,
        created_by=current_user["id"]
    )
    
    db.add(db_campaign)
    
    # Initialize campaign metrics
    metrics = CampaignMetrics(
        campaign_id=db_campaign.id,
        impressions=0,
        clicks=0,
        conversions=0,
        revenue=0
    )
    db.add(metrics)
    
    db.commit()
    
    # Start automation workflows
    automation = MarketingAutomation()
    automation.create_campaign(
        campaign_id=db_campaign.id,
        campaign_type=campaign.type,
        automation_rules=[]  # Default rules based on type
    )
    
    return {
        "campaign_id": db_campaign.id,
        "status": "created",
        "message": f"{campaign.type} campaign created successfully"
    }

@router.get("/campaigns")
async def list_campaigns(
    status: Optional[str] = None,
    type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List marketing campaigns"""
    query = db.query(Campaign)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    if type:
        query = query.filter(Campaign.type == type)
    
    # Non-admins only see their campaigns
    if not current_user.get("is_admin"):
        query = query.filter(Campaign.created_by == current_user["id"])
    
    campaigns = query.order_by(Campaign.created_at.desc()).all()
    
    # Get metrics for each campaign
    results = []
    for campaign in campaigns:
        metrics = db.query(CampaignMetrics).filter(
            CampaignMetrics.campaign_id == campaign.id
        ).first()
        
        results.append({
            "id": campaign.id,
            "name": campaign.name,
            "type": campaign.type,
            "status": campaign.status,
            "budget": campaign.budget,
            "spent": campaign.spent,
            "metrics": {
                "impressions": metrics.impressions if metrics else 0,
                "clicks": metrics.clicks if metrics else 0,
                "conversions": metrics.conversions if metrics else 0,
                "roi": calculate_roi(campaign.spent, metrics.revenue if metrics else 0)
            } if metrics else {},
            "start_date": campaign.start_date,
            "end_date": campaign.end_date
        })
    
    return results

@router.put("/campaigns/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status: str = Body(...),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update campaign status"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Map status
    status_map = {
        "draft": CampaignStatus.DRAFT,
        "scheduled": CampaignStatus.SCHEDULED,
        "running": CampaignStatus.RUNNING,
        "paused": CampaignStatus.PAUSED,
        "completed": CampaignStatus.COMPLETED
    }
    
    if status not in status_map:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    campaign.status = status
    campaign.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Update automation
    automation = MarketingAutomation()
    automation.update_campaign_status(campaign_id, status_map[status])
    
    return {"campaign_id": campaign_id, "status": status}

# Email Marketing
@router.post("/email-campaigns")
async def create_email_campaign(
    email_campaign: EmailCampaignCreate,
    campaign_id: str = Body(...),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create email campaign"""
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Create email campaign
    db_email = EmailCampaign(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        subject=email_campaign.subject,
        content_html=email_campaign.content_html,
        content_text=email_campaign.content_text,
        segment_filters=email_campaign.segment_filters,
        send_time=email_campaign.send_time or datetime.utcnow()
    )
    
    db.add(db_email)
    db.commit()
    
    # Schedule sending
    automation = MarketingAutomation()
    if email_campaign.test_percentage > 0:
        # A/B test
        automation.schedule_ab_test_email(
            db_email.id,
            test_percentage=email_campaign.test_percentage
        )
    else:
        automation.schedule_email_campaign(db_email.id)
    
    return {
        "email_campaign_id": db_email.id,
        "status": "scheduled" if email_campaign.send_time else "sending",
        "estimated_recipients": estimate_recipients(email_campaign.segment_filters)
    }

@router.get("/email-campaigns/{campaign_id}/preview")
async def preview_email_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview email campaign"""
    email_campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id
    ).first()
    
    if not email_campaign:
        raise HTTPException(status_code=404, detail="Email campaign not found")
    
    # Generate preview with personalization
    preview_data = {
        "name": "John Doe",
        "company": "Example Corp",
        "email": "john@example.com"
    }
    
    return {
        "subject": personalize_content(email_campaign.subject, preview_data),
        "content_html": personalize_content(email_campaign.content_html, preview_data),
        "content_text": personalize_content(email_campaign.content_text, preview_data)
    }

# Referral Program
@router.post("/referral-programs")
async def create_referral_program(
    program: ReferralProgramCreate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create referral program"""
    # Create program
    db_program = ReferralProgram(
        id=str(uuid.uuid4()),
        name=program.name,
        reward_type=program.reward_type,
        referrer_reward=program.referrer_reward,
        referee_reward=program.referee_reward,
        max_referrals=program.max_referrals,
        valid_until=datetime.utcnow() + timedelta(days=program.valid_days)
    )
    
    db.add(db_program)
    db.commit()
    
    # Initialize referral system
    referral_system = ReferralSystem()
    referral_system.create_program(
        program_id=db_program.id,
        reward_config={
            "referrer": program.referrer_reward,
            "referee": program.referee_reward
        }
    )
    
    return {
        "program_id": db_program.id,
        "status": "active",
        "valid_until": db_program.valid_until
    }

@router.post("/referrals/generate")
async def generate_referral_code(
    program_id: str = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate referral code for user"""
    # Verify program exists and is active
    program = db.query(ReferralProgram).filter(
        ReferralProgram.id == program_id,
        ReferralProgram.is_active == True
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Referral program not found")
    
    # Generate unique code
    referral_system = ReferralSystem()
    referral = referral_system.generate_referral_code(
        referrer_id=current_user["id"],
        referrer_email=current_user["email"],
        program_id=program_id
    )
    
    # Save to database
    db_referral = Referral(
        id=str(uuid.uuid4()),
        program_id=program_id,
        referrer_id=current_user["id"],
        code=referral.code,
        status="active"
    )
    
    db.add(db_referral)
    db.commit()
    
    return {
        "referral_code": referral.code,
        "share_url": f"https://app.example.com/signup?ref={referral.code}",
        "program_name": program.name,
        "rewards": {
            "referrer": program.referrer_reward,
            "referee": program.referee_reward
        }
    }

@router.post("/referrals/track")
async def track_referral(
    referral_code: str = Body(...),
    referee_email: EmailStr = Body(...),
    action: str = Body(...),
    db: Session = Depends(get_db)
):
    """Track referral conversion"""
    # Find referral
    referral = db.query(Referral).filter(
        Referral.code == referral_code,
        Referral.status == "active"
    ).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    # Track conversion
    referral_system = ReferralSystem()
    result = referral_system.track_referral(referral_code, referee_email, action)
    
    if result.get("converted"):
        # Update referral status
        referral.referee_email = referee_email
        referral.converted_at = datetime.utcnow()
        referral.status = "converted"
        
        # Process rewards
        if result.get("rewards_granted"):
            # Send reward notifications
            email_service = EmailService()
            await email_service.send_template_email(
                to=referral.referrer_email,
                template="referral_reward",
                data=result["rewards"]
            )
        
        db.commit()
    
    return result

@router.get("/referrals/stats")
async def get_referral_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's referral statistics"""
    # Get user's referrals
    referrals = db.query(Referral).filter(
        Referral.referrer_id == current_user["id"]
    ).all()
    
    total_referrals = len(referrals)
    successful_referrals = len([r for r in referrals if r.status == "converted"])
    pending_referrals = len([r for r in referrals if r.status == "active"])
    
    # Calculate rewards earned
    total_rewards = calculate_total_rewards(referrals)
    
    return {
        "total_referrals": total_referrals,
        "successful_referrals": successful_referrals,
        "pending_referrals": pending_referrals,
        "total_rewards": total_rewards,
        "referrals": [{
            "code": r.code,
            "status": r.status,
            "created_at": r.created_at,
            "converted_at": r.converted_at
        } for r in referrals]
    }

# Growth Analytics
@router.get("/analytics/growth")
async def get_growth_metrics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    channel: Optional[str] = None,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get growth analytics metrics"""
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()
    
    analytics = GrowthAnalytics()
    
    # Get metrics
    metrics = analytics.calculate_growth_metrics(
        start_date=date_from,
        end_date=date_to,
        channel=Channel[channel.upper()] if channel else None
    )
    
    # Get funnel analysis
    funnel = analytics.analyze_conversion_funnel({
        "date_range": (date_from, date_to),
        "channel": channel
    })
    
    # Get cohort analysis
    cohorts = analytics.perform_cohort_analysis(
        start_date=date_from,
        cohort_size="week"
    )
    
    return {
        "metrics": metrics,
        "funnel": funnel,
        "cohorts": cohorts,
        "period": {
            "from": date_from,
            "to": date_to
        }
    }

@router.get("/analytics/attribution")
async def get_attribution_analysis(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    model: str = Query("last_touch", pattern="^(last_touch|first_touch|linear|time_decay)$"),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get marketing attribution analysis"""
    analytics = GrowthAnalytics()
    
    attribution = analytics.calculate_attribution(
        model=model,
        date_from=date_from,
        date_to=date_to
    )
    
    return attribution

# A/B Testing
@router.post("/ab-tests")
async def create_ab_test(
    test: ABTestCreate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create A/B test"""
    ab_engine = ABTestingEngine()
    
    # Create test
    ab_test = ab_engine.create_test(
        test_name=test.name,
        variants=test.variants,
        traffic_allocation=test.traffic_allocation,
        success_metrics=test.success_metrics
    )
    
    return {
        "test_id": ab_test.test_id,
        "status": "created",
        "variants": test.variants,
        "estimated_duration": estimate_test_duration(test.minimum_sample_size)
    }

@router.get("/ab-tests/{test_id}")
async def get_ab_test_results(
    test_id: str,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get A/B test results"""
    ab_engine = ABTestingEngine()
    
    results = ab_engine.get_test_results(test_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Calculate statistical significance
    significance = ab_engine.calculate_significance(test_id)
    
    return {
        "test_id": test_id,
        "status": results["status"],
        "results": results["variant_results"],
        "winner": results.get("winner"),
        "significance": significance,
        "recommendation": generate_test_recommendation(results, significance)
    }

@router.put("/ab-tests/{test_id}/stop")
async def stop_ab_test(
    test_id: str,
    winner: Optional[str] = Body(None),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Stop A/B test and optionally declare winner"""
    ab_engine = ABTestingEngine()
    
    result = ab_engine.stop_test(test_id, winner)
    
    return result

# Content Marketing
@router.post("/content")
async def create_content(
    content: ContentCreate,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create marketing content"""
    db_content = ContentMarketing(
        id=str(uuid.uuid4()),
        title=content.title,
        type=content.type,
        content_url=str(content.content_url),
        description=content.description,
        tags=content.tags,
        target_personas=content.target_personas,
        cta_url=str(content.cta_url) if content.cta_url else None,
        created_by=current_user["id"]
    )
    
    db.add(db_content)
    db.commit()
    
    return {
        "content_id": db_content.id,
        "status": "published",
        "tracking_url": generate_tracking_url(db_content.id, str(content.content_url))
    }

@router.get("/content/performance")
async def get_content_performance(
    content_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get content marketing performance"""
    query = db.query(ContentMarketing)
    
    if content_type:
        query = query.filter(ContentMarketing.type == content_type)
    
    if date_from:
        query = query.filter(ContentMarketing.created_at >= date_from)
    
    content_items = query.all()
    
    # Get performance metrics
    performance = []
    for content in content_items:
        metrics = get_content_metrics(content.id)
        performance.append({
            "id": content.id,
            "title": content.title,
            "type": content.type,
            "published_at": content.created_at,
            "metrics": metrics,
            "engagement_score": calculate_engagement_score(metrics)
        })
    
    return sorted(performance, key=lambda x: x["engagement_score"], reverse=True)

# Marketing Automation
@router.get("/automation/workflows")
async def list_automation_workflows(
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List marketing automation workflows"""
    automation = MarketingAutomation()
    workflows = automation.list_workflows()
    
    return workflows

@router.post("/automation/workflows")
async def create_automation_workflow(
    name: str = Body(...),
    trigger: Dict[str, Any] = Body(...),
    actions: List[Dict[str, Any]] = Body(...),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create marketing automation workflow"""
    automation = MarketingAutomation()
    
    workflow = automation.create_workflow(
        name=name,
        trigger=trigger,
        actions=actions
    )
    
    return {
        "workflow_id": workflow["id"],
        "status": "active",
        "message": "Automation workflow created"
    }

# Helper functions
def calculate_roi(spent: float, revenue: float) -> float:
    """Calculate ROI percentage"""
    if spent == 0:
        return 0
    return ((revenue - spent) / spent) * 100

def estimate_recipients(segment_filters: Dict[str, Any]) -> int:
    """Estimate email recipients based on segment filters"""
    # Simplified estimation
    base_audience = 10000
    
    # Apply filters
    if segment_filters.get("plan") == "premium":
        base_audience *= 0.3
    if segment_filters.get("activity") == "active":
        base_audience *= 0.6
    
    return int(base_audience)

def personalize_content(content: str, data: Dict[str, str]) -> str:
    """Personalize content with merge tags"""
    for key, value in data.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content

def calculate_total_rewards(referrals: List[Referral]) -> Dict[str, Any]:
    """Calculate total rewards earned from referrals"""
    total_credits = 0
    total_discounts = 0
    
    for referral in referrals:
        if referral.status == "converted" and referral.reward_granted:
            # Parse rewards based on program
            # Simplified for now
            total_credits += 10  # $10 per referral
    
    return {
        "credits": total_credits,
        "discounts": total_discounts
    }

def estimate_test_duration(sample_size: int) -> str:
    """Estimate A/B test duration"""
    daily_traffic = 1000  # Estimated
    days_needed = sample_size / daily_traffic
    
    if days_needed < 7:
        return f"{int(days_needed)} days"
    elif days_needed < 30:
        return f"{int(days_needed / 7)} weeks"
    else:
        return f"{int(days_needed / 30)} months"

def generate_test_recommendation(results: Dict, significance: Dict) -> str:
    """Generate A/B test recommendation"""
    if significance.get("is_significant"):
        winner = results.get("winner")
        lift = significance.get("lift", 0)
        return f"Variant {winner} is the clear winner with {lift:.1f}% lift. Recommend implementing."
    else:
        return "Test has not reached statistical significance. Continue running or increase sample size."

def generate_tracking_url(content_id: str, original_url: str) -> str:
    """Generate tracking URL for content"""
    return f"https://app.example.com/track/content/{content_id}?url={original_url}"

def get_content_metrics(content_id: str) -> Dict[str, int]:
    """Get content performance metrics"""
    # Simplified - would query analytics database
    return {
        "views": 1250,
        "unique_views": 890,
        "avg_time_on_page": 180,  # seconds
        "shares": 45,
        "conversions": 12
    }

def calculate_engagement_score(metrics: Dict[str, int]) -> float:
    """Calculate content engagement score"""
    # Weighted scoring
    score = (
        metrics.get("unique_views", 0) * 0.2 +
        metrics.get("avg_time_on_page", 0) * 0.3 +
        metrics.get("shares", 0) * 10 +
        metrics.get("conversions", 0) * 50
    )
    return min(100, score / 10)  # Normalize to 0-100