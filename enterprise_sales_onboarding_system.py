"""
Task 201: Enterprise Sales and Onboarding System
Comprehensive system for managing enterprise sales pipeline, demo scheduling,
trial management, and customer onboarding workflows
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import pandas as pd
from pydantic import BaseModel, EmailStr, HttpUrl, validator
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    JSON, String, Text, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


# Enums
class LeadStatus(Enum):
    """Lead pipeline status"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURING = "nurturing"


class LeadSource(Enum):
    """Lead acquisition source"""
    WEBSITE = "website"
    REFERRAL = "referral"
    PARTNER = "partner"
    EVENT = "event"
    CONTENT = "content"
    OUTBOUND = "outbound"
    SOCIAL = "social"
    PAID_AD = "paid_ad"


class CompanySize(Enum):
    """Company size categories"""
    STARTUP = "1-10"
    SMALL = "11-50"
    MEDIUM = "51-200"
    LARGE = "201-1000"
    ENTERPRISE = "1000+"


class TrialStatus(Enum):
    """Trial account status"""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    EXTENDED = "extended"
    EXPIRED = "expired"
    CONVERTED = "converted"
    CANCELLED = "cancelled"


class OnboardingStatus(Enum):
    """Customer onboarding status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CHURNED = "churned"


class ContractType(Enum):
    """Enterprise contract types"""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    MULTI_YEAR = "multi_year"
    CUSTOM = "custom"
    PILOT = "pilot"


class DemoType(Enum):
    """Demo session types"""
    DISCOVERY = "discovery"
    PRODUCT = "product"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    PROOF_OF_CONCEPT = "poc"


# Database Models
class Lead(Base):
    """Enterprise lead/opportunity"""
    __tablename__ = 'leads'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    company_domain = Column(String(255))
    company_size = Column(String(20))
    industry = Column(String(100))
    
    # Contact information
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    contact_title = Column(String(100))
    contact_linkedin = Column(String(255))
    
    # Lead details
    status = Column(String(20), default=LeadStatus.NEW.value)
    source = Column(String(20))
    score = Column(Integer, default=0)
    
    # Deal information
    deal_size = Column(Float)
    expected_close_date = Column(DateTime)
    probability = Column(Integer, default=20)
    
    # Assignment
    owner_id = Column(String(36))
    team_id = Column(String(36))
    
    # Requirements
    requirements = Column(JSON)
    use_cases = Column(JSON)
    competitors = Column(JSON)
    
    # Metadata
    tags = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = relationship("SalesActivity", back_populates="lead")
    demos = relationship("DemoSession", back_populates="lead")
    trials = relationship("Trial", back_populates="lead")
    contracts = relationship("Contract", back_populates="lead")


class SalesActivity(Base):
    """Sales activity tracking"""
    __tablename__ = 'sales_activities'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(String(36), ForeignKey('leads.id'))
    activity_type = Column(String(50))  # email, call, meeting, demo, etc.
    subject = Column(String(255))
    description = Column(Text)
    outcome = Column(String(100))
    next_action = Column(String(255))
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    lead = relationship("Lead", back_populates="activities")


class DemoSession(Base):
    """Demo session scheduling and tracking"""
    __tablename__ = 'demo_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), ForeignKey('leads.id'))
    demo_type = Column(String(20))
    
    # Scheduling
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer, default=60)
    timezone = Column(String(50))
    meeting_link = Column(String(255))
    
    # Participants
    attendees = Column(JSON)  # List of attendee emails
    presenter_id = Column(String(36))
    
    # Content
    agenda = Column(Text)
    demo_environment = Column(String(255))
    custom_demo_data = Column(JSON)
    
    # Outcomes
    status = Column(String(20))  # scheduled, completed, no_show, cancelled
    recording_url = Column(String(255))
    feedback = Column(JSON)
    next_steps = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lead = relationship("Lead", back_populates="demos")


class Trial(Base):
    """Enterprise trial management"""
    __tablename__ = 'trials'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), ForeignKey('leads.id'))
    
    # Trial details
    status = Column(String(20), default=TrialStatus.SCHEDULED.value)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    extended_until = Column(DateTime)
    
    # Configuration
    trial_type = Column(String(50))  # standard, custom, poc
    features_enabled = Column(JSON)
    user_limit = Column(Integer)
    usage_limit = Column(JSON)
    
    # Success criteria
    success_criteria = Column(JSON)
    evaluation_metrics = Column(JSON)
    
    # Usage tracking
    active_users = Column(Integer, default=0)
    total_usage = Column(JSON)
    last_activity = Column(DateTime)
    
    # Conversion
    converted = Column(Boolean, default=False)
    conversion_date = Column(DateTime)
    conversion_value = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lead = relationship("Lead", back_populates="trials")


class Contract(Base):
    """Enterprise contract management"""
    __tablename__ = 'contracts'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), ForeignKey('leads.id'))
    contract_number = Column(String(50), unique=True)
    
    # Contract details
    contract_type = Column(String(20))
    status = Column(String(20))  # draft, pending, active, expired, terminated
    
    # Terms
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    auto_renew = Column(Boolean, default=False)
    renewal_notice_days = Column(Integer, default=30)
    
    # Pricing
    contract_value = Column(Float)
    billing_frequency = Column(String(20))  # monthly, quarterly, annual
    payment_terms = Column(String(50))  # net30, net60, etc.
    discount_percentage = Column(Float)
    
    # Licensing
    user_seats = Column(Integer)
    usage_limits = Column(JSON)
    features = Column(JSON)
    sla_terms = Column(JSON)
    
    # Documents
    contract_url = Column(String(255))
    signed_date = Column(DateTime)
    signed_by = Column(String(255))
    
    # Metadata
    custom_terms = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    lead = relationship("Lead", back_populates="contracts")


class OnboardingWorkflow(Base):
    """Customer onboarding workflow"""
    __tablename__ = 'onboarding_workflows'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36))
    contract_id = Column(String(36), ForeignKey('contracts.id'))
    
    # Status
    status = Column(String(20), default=OnboardingStatus.NOT_STARTED.value)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Assignment
    customer_success_manager = Column(String(36))
    technical_contact = Column(String(36))
    
    # Checklist
    checklist = Column(JSON)  # List of onboarding tasks
    completed_tasks = Column(JSON)
    blocked_tasks = Column(JSON)
    
    # Training
    training_scheduled = Column(Boolean, default=False)
    training_dates = Column(JSON)
    training_attendees = Column(JSON)
    training_materials = Column(JSON)
    
    # Integration
    integration_requirements = Column(JSON)
    api_keys_provisioned = Column(Boolean, default=False)
    sso_configured = Column(Boolean, default=False)
    
    # Success metrics
    adoption_metrics = Column(JSON)
    health_score = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models for API
class LeadCreate(BaseModel):
    """Create new lead request"""
    company_name: str
    company_domain: Optional[str]
    company_size: Optional[CompanySize]
    industry: Optional[str]
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str]
    contact_title: Optional[str]
    source: Optional[LeadSource]
    requirements: Optional[Dict[str, Any]]
    use_cases: Optional[List[str]]
    deal_size: Optional[float]
    
    @validator('deal_size')
    def validate_deal_size(cls, v):
        if v and v < 0:
            raise ValueError('Deal size must be positive')
        return v


class DemoScheduleRequest(BaseModel):
    """Schedule demo request"""
    lead_id: str
    demo_type: DemoType
    scheduled_at: datetime
    duration_minutes: int = 60
    timezone: str = "UTC"
    attendees: List[EmailStr]
    agenda: Optional[str]
    custom_demo_data: Optional[Dict[str, Any]]


class TrialRequest(BaseModel):
    """Enterprise trial request"""
    lead_id: str
    trial_type: str = "standard"
    duration_days: int = 30
    user_limit: int = 10
    features_enabled: List[str]
    success_criteria: Optional[Dict[str, Any]]


class ContractCreate(BaseModel):
    """Create enterprise contract"""
    lead_id: str
    contract_type: ContractType
    start_date: datetime
    end_date: datetime
    contract_value: float
    user_seats: int
    billing_frequency: str = "annual"
    features: List[str]
    custom_terms: Optional[Dict[str, Any]]


# Service Classes
class EnterpriseSalesService:
    """Main enterprise sales service"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # CRM integration placeholders
        self.salesforce_client = None
        self.hubspot_client = None
        self.pipedrive_client = None
    
    async def create_lead(self, lead_data: LeadCreate) -> Lead:
        """Create new enterprise lead"""
        db = self.SessionLocal()
        try:
            lead = Lead(
                **lead_data.dict(),
                score=self._calculate_lead_score(lead_data)
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            
            # Create initial activity
            activity = SalesActivity(
                lead_id=lead.id,
                activity_type="lead_created",
                subject="New lead created",
                description=f"Lead from {lead_data.source or 'unknown source'}"
            )
            db.add(activity)
            db.commit()
            
            # Sync with CRM if configured
            await self._sync_lead_to_crm(lead)
            
            return lead
        finally:
            db.close()
    
    def _calculate_lead_score(self, lead_data: LeadCreate) -> int:
        """Calculate lead score based on attributes"""
        score = 0
        
        # Company size scoring
        if lead_data.company_size:
            size_scores = {
                CompanySize.ENTERPRISE: 30,
                CompanySize.LARGE: 25,
                CompanySize.MEDIUM: 20,
                CompanySize.SMALL: 15,
                CompanySize.STARTUP: 10
            }
            score += size_scores.get(lead_data.company_size, 0)
        
        # Deal size scoring
        if lead_data.deal_size:
            if lead_data.deal_size >= 100000:
                score += 30
            elif lead_data.deal_size >= 50000:
                score += 20
            elif lead_data.deal_size >= 10000:
                score += 10
        
        # Source scoring
        if lead_data.source:
            source_scores = {
                LeadSource.REFERRAL: 20,
                LeadSource.PARTNER: 15,
                LeadSource.OUTBOUND: 10,
                LeadSource.WEBSITE: 5
            }
            score += source_scores.get(lead_data.source, 0)
        
        # Requirements completeness
        if lead_data.requirements:
            score += min(len(lead_data.requirements) * 2, 10)
        
        return min(score, 100)  # Cap at 100
    
    async def update_lead_status(
        self,
        lead_id: str,
        new_status: LeadStatus,
        notes: Optional[str] = None
    ) -> Lead:
        """Update lead pipeline status"""
        db = self.SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            old_status = lead.status
            lead.status = new_status.value
            lead.updated_at = datetime.utcnow()
            
            # Update probability based on status
            status_probability = {
                LeadStatus.NEW: 10,
                LeadStatus.CONTACTED: 20,
                LeadStatus.QUALIFIED: 30,
                LeadStatus.PROPOSAL: 50,
                LeadStatus.NEGOTIATION: 75,
                LeadStatus.CLOSED_WON: 100,
                LeadStatus.CLOSED_LOST: 0
            }
            lead.probability = status_probability.get(new_status, 20)
            
            # Log activity
            activity = SalesActivity(
                lead_id=lead_id,
                activity_type="status_change",
                subject=f"Status changed from {old_status} to {new_status.value}",
                description=notes or "",
                completed_at=datetime.utcnow()
            )
            db.add(activity)
            
            db.commit()
            db.refresh(lead)
            
            return lead
        finally:
            db.close()
    
    async def schedule_demo(self, request: DemoScheduleRequest) -> DemoSession:
        """Schedule enterprise demo"""
        db = self.SessionLocal()
        try:
            # Create demo session
            demo = DemoSession(
                lead_id=request.lead_id,
                demo_type=request.demo_type.value,
                scheduled_at=request.scheduled_at,
                duration_minutes=request.duration_minutes,
                timezone=request.timezone,
                attendees=request.attendees,
                agenda=request.agenda,
                custom_demo_data=request.custom_demo_data,
                status="scheduled",
                meeting_link=self._generate_meeting_link()
            )
            db.add(demo)
            
            # Log activity
            activity = SalesActivity(
                lead_id=request.lead_id,
                activity_type="demo_scheduled",
                subject=f"{request.demo_type.value} demo scheduled",
                description=f"Demo scheduled for {request.scheduled_at}",
                scheduled_at=request.scheduled_at
            )
            db.add(activity)
            
            # Update lead status if needed
            lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
            if lead and lead.status == LeadStatus.NEW.value:
                lead.status = LeadStatus.CONTACTED.value
            
            db.commit()
            db.refresh(demo)
            
            # Send calendar invites
            await self._send_demo_invites(demo)
            
            return demo
        finally:
            db.close()
    
    def _generate_meeting_link(self) -> str:
        """Generate unique meeting link"""
        meeting_id = str(uuid.uuid4())[:8]
        return f"https://meet.platform.com/demo/{meeting_id}"
    
    async def start_trial(self, request: TrialRequest) -> Trial:
        """Start enterprise trial"""
        db = self.SessionLocal()
        try:
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=request.duration_days)
            
            trial = Trial(
                lead_id=request.lead_id,
                status=TrialStatus.ACTIVE.value,
                start_date=start_date,
                end_date=end_date,
                trial_type=request.trial_type,
                user_limit=request.user_limit,
                features_enabled=request.features_enabled,
                success_criteria=request.success_criteria
            )
            db.add(trial)
            
            # Update lead status
            lead = db.query(Lead).filter(Lead.id == request.lead_id).first()
            if lead:
                lead.status = LeadStatus.PROPOSAL.value
                lead.probability = 50
            
            # Log activity
            activity = SalesActivity(
                lead_id=request.lead_id,
                activity_type="trial_started",
                subject=f"{request.trial_type} trial started",
                description=f"Trial active until {end_date.date()}",
                completed_at=datetime.utcnow()
            )
            db.add(activity)
            
            db.commit()
            db.refresh(trial)
            
            # Provision trial environment
            await self._provision_trial_environment(trial)
            
            return trial
        finally:
            db.close()
    
    async def create_contract(self, contract_data: ContractCreate) -> Contract:
        """Create enterprise contract"""
        db = self.SessionLocal()
        try:
            contract_number = self._generate_contract_number()
            
            contract = Contract(
                **contract_data.dict(),
                contract_number=contract_number,
                status="draft"
            )
            db.add(contract)
            
            # Update lead status
            lead = db.query(Lead).filter(Lead.id == contract_data.lead_id).first()
            if lead:
                lead.status = LeadStatus.NEGOTIATION.value
                lead.probability = 75
                lead.deal_size = contract_data.contract_value
            
            # Log activity
            activity = SalesActivity(
                lead_id=contract_data.lead_id,
                activity_type="contract_created",
                subject=f"Contract {contract_number} created",
                description=f"Contract value: ${contract_data.contract_value:,.2f}",
                completed_at=datetime.utcnow()
            )
            db.add(activity)
            
            db.commit()
            db.refresh(contract)
            
            return contract
        finally:
            db.close()
    
    def _generate_contract_number(self) -> str:
        """Generate unique contract number"""
        year = datetime.utcnow().year
        random_suffix = str(uuid.uuid4())[:6].upper()
        return f"ENT-{year}-{random_suffix}"
    
    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get sales pipeline metrics"""
        db = self.SessionLocal()
        try:
            # Pipeline summary
            pipeline = db.query(
                Lead.status,
                func.count(Lead.id).label('count'),
                func.sum(Lead.deal_size).label('total_value')
            ).group_by(Lead.status).all()
            
            # Conversion rates
            total_leads = db.query(Lead).count()
            won_leads = db.query(Lead).filter(
                Lead.status == LeadStatus.CLOSED_WON.value
            ).count()
            
            # Average deal size
            avg_deal = db.query(func.avg(Lead.deal_size)).filter(
                Lead.deal_size.isnot(None)
            ).scalar()
            
            # Trial conversion
            total_trials = db.query(Trial).count()
            converted_trials = db.query(Trial).filter(
                Trial.converted == True
            ).count()
            
            return {
                "pipeline": [
                    {
                        "status": p.status,
                        "count": p.count,
                        "value": float(p.total_value or 0)
                    }
                    for p in pipeline
                ],
                "conversion_rate": (won_leads / total_leads * 100) if total_leads > 0 else 0,
                "average_deal_size": float(avg_deal or 0),
                "trial_conversion_rate": (converted_trials / total_trials * 100) if total_trials > 0 else 0,
                "total_pipeline_value": sum(
                    p.total_value or 0 for p in pipeline 
                    if p.status not in [LeadStatus.CLOSED_WON.value, LeadStatus.CLOSED_LOST.value]
                )
            }
        finally:
            db.close()
    
    async def _sync_lead_to_crm(self, lead: Lead):
        """Sync lead to external CRM"""
        # Placeholder for CRM integration
        if self.salesforce_client:
            # Sync to Salesforce
            pass
        elif self.hubspot_client:
            # Sync to HubSpot
            pass
        elif self.pipedrive_client:
            # Sync to Pipedrive
            pass
    
    async def _send_demo_invites(self, demo: DemoSession):
        """Send calendar invites for demo"""
        # Integration with calendar service
        pass
    
    async def _provision_trial_environment(self, trial: Trial):
        """Provision trial environment and credentials"""
        # Create trial workspace
        # Set up features and limits
        # Generate API keys
        pass


class OnboardingService:
    """Customer onboarding service"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Default onboarding checklist
        self.default_checklist = [
            {"task": "Contract signed", "required": True, "owner": "sales"},
            {"task": "Payment received", "required": True, "owner": "finance"},
            {"task": "Account provisioned", "required": True, "owner": "ops"},
            {"task": "Admin users created", "required": True, "owner": "customer"},
            {"task": "SSO configured", "required": False, "owner": "it"},
            {"task": "API keys generated", "required": False, "owner": "ops"},
            {"task": "Initial training scheduled", "required": True, "owner": "cs"},
            {"task": "Documentation shared", "required": True, "owner": "cs"},
            {"task": "Success criteria defined", "required": True, "owner": "cs"},
            {"task": "First use case implemented", "required": True, "owner": "customer"},
            {"task": "Go-live checkpoint", "required": True, "owner": "cs"}
        ]
    
    async def start_onboarding(
        self,
        contract_id: str,
        customer_id: str,
        csm_id: str
    ) -> OnboardingWorkflow:
        """Start customer onboarding workflow"""
        db = self.SessionLocal()
        try:
            workflow = OnboardingWorkflow(
                customer_id=customer_id,
                contract_id=contract_id,
                customer_success_manager=csm_id,
                status=OnboardingStatus.IN_PROGRESS.value,
                started_at=datetime.utcnow(),
                checklist=self.default_checklist,
                completed_tasks=[],
                health_score=100
            )
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            
            # Send welcome email
            await self._send_welcome_package(workflow)
            
            return workflow
        finally:
            db.close()
    
    async def update_task_status(
        self,
        workflow_id: str,
        task_name: str,
        completed: bool
    ) -> OnboardingWorkflow:
        """Update onboarding task status"""
        db = self.SessionLocal()
        try:
            workflow = db.query(OnboardingWorkflow).filter(
                OnboardingWorkflow.id == workflow_id
            ).first()
            
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            completed_tasks = workflow.completed_tasks or []
            
            if completed and task_name not in completed_tasks:
                completed_tasks.append(task_name)
            elif not completed and task_name in completed_tasks:
                completed_tasks.remove(task_name)
            
            workflow.completed_tasks = completed_tasks
            workflow.updated_at = datetime.utcnow()
            
            # Update health score
            workflow.health_score = self._calculate_health_score(workflow)
            
            # Check if onboarding is complete
            required_tasks = [
                t['task'] for t in workflow.checklist 
                if t.get('required', False)
            ]
            if all(task in completed_tasks for task in required_tasks):
                workflow.status = OnboardingStatus.COMPLETED.value
                workflow.completed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(workflow)
            
            return workflow
        finally:
            db.close()
    
    def _calculate_health_score(self, workflow: OnboardingWorkflow) -> int:
        """Calculate customer health score"""
        score = 100
        
        # Deduct points for incomplete required tasks
        required_tasks = [
            t['task'] for t in workflow.checklist 
            if t.get('required', False)
        ]
        completed = workflow.completed_tasks or []
        incomplete_required = len([t for t in required_tasks if t not in completed])
        score -= incomplete_required * 10
        
        # Deduct points for delayed onboarding
        if workflow.started_at:
            days_elapsed = (datetime.utcnow() - workflow.started_at).days
            if days_elapsed > 30:
                score -= min((days_elapsed - 30) * 2, 20)
        
        # Deduct points for blocked tasks
        if workflow.blocked_tasks:
            score -= len(workflow.blocked_tasks) * 5
        
        return max(score, 0)
    
    async def _send_welcome_package(self, workflow: OnboardingWorkflow):
        """Send welcome package to new customer"""
        # Email templates, documentation links, etc.
        pass


class SalesAnalytics:
    """Sales analytics and reporting"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_sales_forecast(self, months: int = 3) -> pd.DataFrame:
        """Generate sales forecast"""
        db = self.SessionLocal()
        try:
            # Get pipeline data
            query = """
                SELECT 
                    expected_close_date,
                    deal_size,
                    probability,
                    status
                FROM leads
                WHERE status NOT IN ('closed_won', 'closed_lost')
                AND expected_close_date IS NOT NULL
                AND deal_size IS NOT NULL
            """
            
            df = pd.read_sql(query, self.engine)
            
            if df.empty:
                return pd.DataFrame()
            
            # Calculate weighted pipeline
            df['weighted_value'] = df['deal_size'] * df['probability'] / 100
            
            # Group by month
            df['month'] = pd.to_datetime(df['expected_close_date']).dt.to_period('M')
            
            forecast = df.groupby('month').agg({
                'deal_size': 'sum',
                'weighted_value': 'sum',
                'status': 'count'
            }).rename(columns={'status': 'deal_count'})
            
            # Add cumulative values
            forecast['cumulative_pipeline'] = forecast['deal_size'].cumsum()
            forecast['cumulative_weighted'] = forecast['weighted_value'].cumsum()
            
            return forecast
        finally:
            db.close()
    
    def get_conversion_funnel(self) -> Dict[str, Any]:
        """Get conversion funnel metrics"""
        db = self.SessionLocal()
        try:
            # Get funnel stages
            stages = [
                LeadStatus.NEW,
                LeadStatus.CONTACTED,
                LeadStatus.QUALIFIED,
                LeadStatus.PROPOSAL,
                LeadStatus.NEGOTIATION,
                LeadStatus.CLOSED_WON
            ]
            
            funnel_data = []
            for i, stage in enumerate(stages):
                count = db.query(Lead).filter(
                    Lead.status.in_([s.value for s in stages[i:]])
                ).count()
                
                funnel_data.append({
                    "stage": stage.value,
                    "count": count,
                    "conversion_rate": 0 if i == 0 else (count / funnel_data[0]['count'] * 100)
                })
            
            # Calculate stage-to-stage conversion
            for i in range(len(funnel_data) - 1):
                current = funnel_data[i]['count']
                next_stage = funnel_data[i + 1]['count']
                funnel_data[i]['next_stage_conversion'] = (
                    (next_stage / current * 100) if current > 0 else 0
                )
            
            return {
                "funnel": funnel_data,
                "overall_conversion": funnel_data[-1]['conversion_rate'],
                "average_stage_conversion": sum(
                    f.get('next_stage_conversion', 0) for f in funnel_data[:-1]
                ) / (len(funnel_data) - 1)
            }
        finally:
            db.close()
    
    def get_sales_velocity(self) -> Dict[str, Any]:
        """Calculate sales velocity metrics"""
        db = self.SessionLocal()
        try:
            # Get closed won deals from last 90 days
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            
            closed_deals = db.query(Lead).filter(
                Lead.status == LeadStatus.CLOSED_WON.value,
                Lead.updated_at >= ninety_days_ago
            ).all()
            
            if not closed_deals:
                return {
                    "average_deal_size": 0,
                    "average_sales_cycle": 0,
                    "win_rate": 0,
                    "sales_velocity": 0
                }
            
            # Calculate metrics
            total_value = sum(d.deal_size or 0 for d in closed_deals)
            avg_deal_size = total_value / len(closed_deals)
            
            # Calculate average sales cycle
            sales_cycles = []
            for deal in closed_deals:
                if deal.created_at and deal.updated_at:
                    cycle_days = (deal.updated_at - deal.created_at).days
                    sales_cycles.append(cycle_days)
            
            avg_sales_cycle = sum(sales_cycles) / len(sales_cycles) if sales_cycles else 0
            
            # Calculate win rate
            total_closed = db.query(Lead).filter(
                Lead.status.in_([LeadStatus.CLOSED_WON.value, LeadStatus.CLOSED_LOST.value]),
                Lead.updated_at >= ninety_days_ago
            ).count()
            
            win_rate = (len(closed_deals) / total_closed * 100) if total_closed > 0 else 0
            
            # Sales velocity = (Opportunities × Deal Size × Win Rate) / Sales Cycle
            active_opportunities = db.query(Lead).filter(
                Lead.status.in_([
                    LeadStatus.QUALIFIED.value,
                    LeadStatus.PROPOSAL.value,
                    LeadStatus.NEGOTIATION.value
                ])
            ).count()
            
            sales_velocity = (
                (active_opportunities * avg_deal_size * win_rate / 100) / avg_sales_cycle
            ) if avg_sales_cycle > 0 else 0
            
            return {
                "average_deal_size": avg_deal_size,
                "average_sales_cycle": avg_sales_cycle,
                "win_rate": win_rate,
                "sales_velocity": sales_velocity,
                "active_opportunities": active_opportunities
            }
        finally:
            db.close()


# Demo Environment Manager
class DemoEnvironmentManager:
    """Manage demo environments for prospects"""
    
    def __init__(self):
        self.demo_instances = {}
        self.demo_data_templates = {
            "financial": self._load_financial_demo_data(),
            "healthcare": self._load_healthcare_demo_data(),
            "education": self._load_education_demo_data(),
            "technology": self._load_technology_demo_data(),
            "retail": self._load_retail_demo_data()
        }
    
    async def provision_demo_environment(
        self,
        demo_id: str,
        industry: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Provision a demo environment"""
        # Select appropriate demo data
        demo_data = self.demo_data_templates.get(
            industry.lower(),
            self.demo_data_templates["technology"]
        )
        
        if custom_data:
            demo_data.update(custom_data)
        
        # Create demo instance
        instance = {
            "id": demo_id,
            "url": f"https://demo.platform.com/{demo_id}",
            "credentials": {
                "username": f"demo_{demo_id[:8]}",
                "password": self._generate_demo_password()
            },
            "data": demo_data,
            "features": self._get_demo_features(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        
        self.demo_instances[demo_id] = instance
        
        return instance
    
    def _generate_demo_password(self) -> str:
        """Generate secure demo password"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(12))
    
    def _get_demo_features(self) -> List[str]:
        """Get features enabled for demo"""
        return [
            "transcription",
            "real_time_processing",
            "multi_language",
            "speaker_diarization",
            "sentiment_analysis",
            "entity_extraction",
            "custom_vocabulary",
            "api_access",
            "team_collaboration",
            "advanced_analytics"
        ]
    
    def _load_financial_demo_data(self) -> Dict[str, Any]:
        """Load financial industry demo data"""
        return {
            "sample_transcripts": [
                "Q4 Earnings Call",
                "Investment Committee Meeting",
                "Risk Assessment Review"
            ],
            "custom_entities": ["ticker_symbols", "financial_metrics", "regulations"],
            "vocabulary": ["EBITDA", "ROI", "P/E ratio", "market cap"]
        }
    
    def _load_healthcare_demo_data(self) -> Dict[str, Any]:
        """Load healthcare industry demo data"""
        return {
            "sample_transcripts": [
                "Patient Consultation",
                "Medical Team Briefing",
                "Clinical Trial Discussion"
            ],
            "custom_entities": ["medications", "conditions", "procedures"],
            "vocabulary": ["diagnosis", "treatment", "symptoms", "prescription"]
        }
    
    def _load_education_demo_data(self) -> Dict[str, Any]:
        """Load education industry demo data"""
        return {
            "sample_transcripts": [
                "Lecture Recording",
                "Student Presentation",
                "Faculty Meeting"
            ],
            "custom_entities": ["courses", "assignments", "departments"],
            "vocabulary": ["curriculum", "assessment", "pedagogy", "enrollment"]
        }
    
    def _load_technology_demo_data(self) -> Dict[str, Any]:
        """Load technology industry demo data"""
        return {
            "sample_transcripts": [
                "Sprint Planning",
                "Architecture Review",
                "Product Demo"
            ],
            "custom_entities": ["technologies", "features", "bugs"],
            "vocabulary": ["API", "deployment", "scalability", "microservices"]
        }
    
    def _load_retail_demo_data(self) -> Dict[str, Any]:
        """Load retail industry demo data"""
        return {
            "sample_transcripts": [
                "Sales Team Meeting",
                "Customer Feedback Session",
                "Inventory Planning"
            ],
            "custom_entities": ["products", "brands", "promotions"],
            "vocabulary": ["SKU", "inventory", "conversion", "merchandising"]
        }


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Initialize services
    sales_service = EnterpriseSalesService("sqlite:///enterprise_sales.db")
    onboarding_service = OnboardingService("sqlite:///enterprise_sales.db")
    analytics = SalesAnalytics("sqlite:///enterprise_sales.db")
    demo_manager = DemoEnvironmentManager()
    
    async def example_workflow():
        # Create a new lead
        lead_data = LeadCreate(
            company_name="Acme Corp",
            company_domain="acme.com",
            company_size=CompanySize.ENTERPRISE,
            industry="Technology",
            contact_name="John Smith",
            contact_email="john.smith@acme.com",
            contact_title="VP of Engineering",
            source=LeadSource.WEBSITE,
            deal_size=150000
        )
        
        lead = await sales_service.create_lead(lead_data)
        print(f"Created lead: {lead.id}")
        
        # Schedule a demo
        demo_request = DemoScheduleRequest(
            lead_id=lead.id,
            demo_type=DemoType.PRODUCT,
            scheduled_at=datetime.utcnow() + timedelta(days=3),
            attendees=["john.smith@acme.com", "sarah.jones@acme.com"]
        )
        
        demo = await sales_service.schedule_demo(demo_request)
        print(f"Scheduled demo: {demo.id}")
        
        # Provision demo environment
        demo_env = await demo_manager.provision_demo_environment(
            demo.id,
            "technology"
        )
        print(f"Demo environment: {demo_env['url']}")
        
        # Start trial
        trial_request = TrialRequest(
            lead_id=lead.id,
            trial_type="enterprise",
            duration_days=30,
            user_limit=50,
            features_enabled=["all"]
        )
        
        trial = await sales_service.start_trial(trial_request)
        print(f"Started trial: {trial.id}")
        
        # Get analytics
        metrics = await sales_service.get_pipeline_metrics()
        print(f"Pipeline metrics: {metrics}")
    
    # Run example
    asyncio.run(example_workflow())