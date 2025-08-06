"""
Extended Database Models for New Features

Models for enterprise sales, API platform, compliance, customer support, and marketing
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()

# ============= ENTERPRISE SALES MODELS =============

class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class SalesLead(Base):
    __tablename__ = "sales_leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=False)
    contact_name = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    
    # Lead details
    company_size = Column(String)
    industry = Column(String)
    use_case = Column(Text)
    budget_range = Column(String)
    
    # Status
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW)
    score = Column(Integer, default=0)
    priority = Column(String, default="medium")
    
    # Assignment
    assigned_to = Column(String, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = relationship("SalesActivity", back_populates="lead")
    opportunities = relationship("SalesOpportunity", back_populates="lead")

class SalesActivity(Base):
    __tablename__ = "sales_activities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("sales_leads.id"))
    activity_type = Column(String)  # email, call, meeting, demo
    subject = Column(String)
    notes = Column(Text)
    
    # Outcome
    outcome = Column(String)
    next_steps = Column(Text)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Created by
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lead = relationship("SalesLead", back_populates="activities")

class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("sales_leads.id"))
    name = Column(String, nullable=False)
    
    # Deal details
    amount = Column(Float)
    probability = Column(Integer)  # 0-100
    expected_close_date = Column(DateTime)
    
    # Product details
    products = Column(JSON)  # List of products/licenses
    custom_terms = Column(JSON)
    
    # Status
    stage = Column(String)
    is_won = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("SalesLead", back_populates="opportunities")

# ============= API PLATFORM MODELS =============

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Owner
    user_id = Column(String, ForeignKey("users.id"))
    organization_id = Column(String, ForeignKey("organizations.id"))
    
    # Permissions
    scopes = Column(JSON)  # List of allowed scopes
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime)
    
    # Relationships
    usage_logs = relationship("APIUsageLog", back_populates="api_key")

class APIUsageLog(Base):
    __tablename__ = "api_usage_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(String, ForeignKey("api_keys.id"))
    
    # Request details
    endpoint = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    
    # Metrics
    response_time_ms = Column(Integer)
    request_size = Column(Integer)
    response_size = Column(Integer)
    
    # Metadata
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")

class Webhook(Base):
    __tablename__ = "webhooks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Configuration
    url = Column(String, nullable=False)
    events = Column(JSON)  # List of event types
    secret = Column(String)  # For signature verification
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime)
    failure_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============= COMPLIANCE & SECURITY MODELS =============

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event details
    event_type = Column(String, nullable=False)
    event_category = Column(String)
    description = Column(Text)
    
    # Actor
    actor_id = Column(String)
    actor_type = Column(String)  # user, system, api
    actor_email = Column(String)
    
    # Target
    target_id = Column(String)
    target_type = Column(String)
    
    # Context
    ip_address = Column(String)
    user_agent = Column(String)
    session_id = Column(String)
    
    # Compliance
    compliance_frameworks = Column(JSON)  # [GDPR, HIPAA, SOC2]
    risk_score = Column(Integer)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Immutable hash for integrity
    event_hash = Column(String)

class DataRetentionPolicy(Base):
    __tablename__ = "data_retention_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Policy details
    data_type = Column(String, nullable=False)
    retention_days = Column(Integer, nullable=False)
    
    # Actions
    action_on_expiry = Column(String)  # delete, anonymize, archive
    
    # Compliance
    legal_basis = Column(String)
    compliance_frameworks = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConsentRecord(Base):
    __tablename__ = "consent_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Consent details
    purpose = Column(String, nullable=False)
    data_categories = Column(JSON)
    processing_activities = Column(JSON)
    
    # Legal basis
    legal_basis = Column(String)
    
    # Status
    is_given = Column(Boolean, default=True)
    is_withdrawn = Column(Boolean, default=False)
    
    # Validity
    valid_until = Column(DateTime)
    
    # Timestamps
    given_at = Column(DateTime, default=datetime.utcnow)
    withdrawn_at = Column(DateTime)
    
    # Metadata
    collection_method = Column(String)
    ip_address = Column(String)
    version = Column(String)

# ============= CUSTOMER SUPPORT MODELS =============

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_number = Column(String, unique=True, nullable=False)
    
    # Customer info
    customer_id = Column(String, ForeignKey("users.id"))
    customer_email = Column(String)
    customer_name = Column(String)
    
    # Ticket details
    subject = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    priority = Column(String, default="medium")
    
    # Status
    status = Column(String, default="new")
    sentiment = Column(String)  # positive, neutral, negative
    
    # Assignment
    assigned_to = Column(String, ForeignKey("users.id"))
    assigned_team = Column(String)
    
    # SLA
    sla_deadline = Column(DateTime)
    first_response_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Metrics
    response_count = Column(Integer, default=0)
    satisfaction_rating = Column(Integer)  # 1-5
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String, ForeignKey("support_tickets.id"))
    
    # Sender
    sender_id = Column(String)
    sender_type = Column(String)  # customer, agent, system
    sender_name = Column(String)
    
    # Content
    content = Column(Text)
    is_internal_note = Column(Boolean, default=False)
    
    # Attachments
    attachments = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content
    title = Column(String, nullable=False)
    slug = Column(String, unique=True)
    summary = Column(Text)
    content = Column(Text)
    
    # Metadata
    article_type = Column(String)
    category = Column(String)
    tags = Column(JSON)
    
    # Author
    author_id = Column(String, ForeignKey("users.id"))
    author_name = Column(String)
    
    # Status
    status = Column(String, default="draft")
    
    # Analytics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # SEO
    meta_description = Column(Text)
    keywords = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

# ============= MARKETING & GROWTH MODELS =============

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Type and channel
    campaign_type = Column(String)  # email, social, content, event
    channels = Column(JSON)
    
    # Targeting
    target_audience = Column(JSON)
    segment_criteria = Column(JSON)
    
    # Content
    content = Column(JSON)
    
    # Schedule
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Budget
    budget = Column(Float)
    spent = Column(Float, default=0)
    
    # Status
    status = Column(String, default="draft")
    
    # Metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analytics = relationship("CampaignAnalytics", back_populates="campaign")

class CampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Metrics
    date = Column(DateTime)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    
    # Engagement
    engagement_rate = Column(Float)
    click_through_rate = Column(Float)
    conversion_rate = Column(Float)
    
    # Cost
    cost = Column(Float)
    cost_per_click = Column(Float)
    cost_per_conversion = Column(Float)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="analytics")

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Referrer
    referrer_id = Column(String, ForeignKey("users.id"))
    referrer_email = Column(String)
    referral_code = Column(String, unique=True)
    code = Column(String, unique=True)  # Alternative field name
    
    # Referred user
    referred_email = Column(String)
    referee_email = Column(String)  # Alternative field name
    referred_user_id = Column(String, ForeignKey("users.id"))
    referee_id = Column(String, ForeignKey("users.id"))  # Alternative field name
    
    # Program/Campaign
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    program_id = Column(String, ForeignKey("referral_programs.id"))
    
    # Status
    status = Column(String, default="pending")  # pending, active, converted, expired
    
    # Rewards
    referrer_reward = Column(JSON)
    referred_reward = Column(JSON)
    referee_reward = Column(JSON)  # Alternative field name
    reward_granted = Column(Boolean, default=False)
    referrer_reward_granted = Column(Boolean, default=False)
    referee_reward_granted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    converted_at = Column(DateTime)
    expires_at = Column(DateTime)

class ReferralProgram(Base):
    __tablename__ = "referral_programs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Rewards
    reward_type = Column(String)  # credit, discount, feature
    referrer_reward = Column(JSON)
    referee_reward = Column(JSON)
    
    # Limits
    max_referrals = Column(Integer)
    max_rewards_per_user = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Validity
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignMetrics(Base):
    __tablename__ = "campaign_metrics"
    
    campaign_id = Column(String, ForeignKey("campaigns.id"), primary_key=True)
    
    # Basic metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0)
    
    # Email specific
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)
    
    # Social specific
    shares = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Calculated rates
    open_rate = Column(Float)
    click_rate = Column(Float)
    conversion_rate = Column(Float)
    bounce_rate = Column(Float)
    
    # Updated timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailCampaign(Base):
    __tablename__ = "email_campaigns"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # Email content
    subject = Column(String, nullable=False)
    preview_text = Column(String)
    content_html = Column(Text)
    content_text = Column(Text)
    
    # Targeting
    segment_filters = Column(JSON)
    recipient_count = Column(Integer)
    
    # Schedule
    send_time = Column(DateTime)
    sent_at = Column(DateTime)
    
    # A/B Testing
    is_ab_test = Column(Boolean, default=False)
    test_percentage = Column(Float)
    winning_variant = Column(String)
    
    # Status
    status = Column(String, default="draft")  # draft, scheduled, sending, sent
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContentMarketing(Base):
    __tablename__ = "content_marketing"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content details
    title = Column(String, nullable=False)
    type = Column(String)  # blog, video, podcast, webinar, ebook
    content_url = Column(String)
    description = Column(Text)
    
    # Categorization
    tags = Column(JSON)
    categories = Column(JSON)
    target_personas = Column(JSON)
    
    # Performance
    views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    avg_time_on_page = Column(Integer)  # seconds
    shares = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    
    # CTAs
    cta_url = Column(String)
    cta_clicks = Column(Integer, default=0)
    
    # Attribution
    created_by = Column(String, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Association tables for many-to-many relationships
lead_tags = Table('lead_tags', Base.metadata,
    Column('lead_id', String, ForeignKey('sales_leads.id')),
    Column('tag_id', String, ForeignKey('tags.id'))
)

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    category = Column(String)
    color = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)