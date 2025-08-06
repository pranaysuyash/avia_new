"""
Support Ticket Management System

Handles customer support tickets, issue tracking, and resolution workflows
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import asyncio
from collections import defaultdict
import json
import hashlib

class TicketPriority(str, Enum):
    """Ticket priority levels"""
    CRITICAL = "critical"  # System down, data loss
    HIGH = "high"         # Major functionality broken
    MEDIUM = "medium"     # Partial functionality affected
    LOW = "low"           # Minor issues, questions
    TRIVIAL = "trivial"   # Cosmetic, nice-to-have

class TicketStatus(str, Enum):
    """Ticket lifecycle status"""
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_INTERNAL = "waiting_internal"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class TicketCategory(str, Enum):
    """Support ticket categories"""
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    OTHER = "other"

class TicketChannel(str, Enum):
    """Support channels"""
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    API = "api"
    WEB_FORM = "web_form"
    SOCIAL_MEDIA = "social_media"
    IN_APP = "in_app"

class CustomerSentiment(str, Enum):
    """Customer sentiment analysis"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class TicketAttachment(BaseModel):
    """Ticket attachment"""
    attachment_id: str
    filename: str
    size_bytes: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: str
    storage_path: str
    is_public: bool = False

class TicketMessage(BaseModel):
    """Message in ticket thread"""
    message_id: str
    ticket_id: str
    sender_id: str
    sender_type: str  # customer, agent, system
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Message content
    content: str
    content_html: Optional[str]
    
    # Metadata
    is_internal_note: bool = False
    sentiment: Optional[CustomerSentiment]
    attachments: List[str] = []  # Attachment IDs
    
    # Actions
    status_change: Optional[TicketStatus]
    priority_change: Optional[TicketPriority]
    assigned_to_change: Optional[str]

class SupportTicket(BaseModel):
    """Support ticket model"""
    ticket_id: str
    ticket_number: str  # Human-readable number
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Customer information
    customer_id: str
    customer_email: str
    customer_name: str
    organization_id: Optional[str]
    
    # Ticket details
    subject: str
    description: str
    category: TicketCategory
    subcategory: Optional[str]
    tags: List[str] = []
    
    # Status and priority
    status: TicketStatus = TicketStatus.NEW
    priority: TicketPriority = TicketPriority.MEDIUM
    sentiment: Optional[CustomerSentiment]
    
    # Assignment
    assigned_to: Optional[str]
    assigned_team: Optional[str]
    
    # Channel and source
    channel: TicketChannel
    source_reference: Optional[str]  # Email ID, chat session, etc.
    
    # SLA tracking
    sla_deadline: Optional[datetime]
    first_response_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    # Metrics
    response_count: int = 0
    reopen_count: int = 0
    escalation_count: int = 0
    
    # Related items
    related_tickets: List[str] = []
    related_incidents: List[str] = []
    
    # Custom fields
    custom_fields: Dict[str, Any] = {}

class SLAPolicy(BaseModel):
    """Service Level Agreement policy"""
    policy_id: str
    name: str
    description: str
    
    # Conditions
    priority: Optional[TicketPriority]
    category: Optional[TicketCategory]
    customer_tier: Optional[str]
    
    # Targets (in minutes)
    first_response_time: int
    resolution_time: int
    
    # Business hours
    business_hours_only: bool = True
    
    # Escalation
    escalation_rules: List[Dict[str, Any]] = []

class EscalationRule(BaseModel):
    """Ticket escalation rule"""
    rule_id: str
    name: str
    
    # Conditions
    time_threshold_minutes: int
    status_conditions: List[TicketStatus]
    
    # Actions
    notify_users: List[str] = []
    notify_teams: List[str] = []
    change_priority: Optional[TicketPriority]
    auto_assign_to: Optional[str]

class Agent(BaseModel):
    """Support agent"""
    agent_id: str
    name: str
    email: str
    
    # Capabilities
    skills: List[str] = []
    languages: List[str] = ["en"]
    specializations: List[TicketCategory] = []
    
    # Availability
    is_available: bool = True
    current_load: int = 0
    max_concurrent_tickets: int = 10
    
    # Performance
    avg_response_time_minutes: float = 0
    avg_resolution_time_hours: float = 0
    satisfaction_rating: float = 0

class TicketManagementSystem:
    """Main ticket management system"""
    
    def __init__(self):
        self.tickets: Dict[str, SupportTicket] = {}
        self.messages: Dict[str, List[TicketMessage]] = defaultdict(list)
        self.attachments: Dict[str, TicketAttachment] = {}
        self.agents: Dict[str, Agent] = {}
        self.sla_policies: Dict[str, SLAPolicy] = {}
        self.escalation_rules: Dict[str, EscalationRule] = {}
        
        # Indexes
        self.tickets_by_customer: Dict[str, List[str]] = defaultdict(list)
        self.tickets_by_status: Dict[TicketStatus, Set[str]] = defaultdict(set)
        self.tickets_by_agent: Dict[str, Set[str]] = defaultdict(set)
        
        # Counters
        self.ticket_counter = 1000
        
        # Initialize default policies
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default SLA policies"""
        # Critical priority SLA
        self.sla_policies["critical_sla"] = SLAPolicy(
            policy_id="critical_sla",
            name="Critical Priority SLA",
            description="SLA for critical issues",
            priority=TicketPriority.CRITICAL,
            first_response_time=15,  # 15 minutes
            resolution_time=240,     # 4 hours
            business_hours_only=False
        )
        
        # Standard SLA
        self.sla_policies["standard_sla"] = SLAPolicy(
            policy_id="standard_sla",
            name="Standard SLA",
            description="Default SLA for all tickets",
            first_response_time=120,  # 2 hours
            resolution_time=1440,     # 24 hours
            business_hours_only=True
        )
        
        # Escalation rules
        self.escalation_rules["no_response"] = EscalationRule(
            rule_id="no_response",
            name="No First Response",
            time_threshold_minutes=60,
            status_conditions=[TicketStatus.NEW, TicketStatus.OPEN],
            change_priority=TicketPriority.HIGH,
            notify_teams=["support_managers"]
        )
    
    async def create_ticket(
        self,
        customer_id: str,
        customer_email: str,
        customer_name: str,
        subject: str,
        description: str,
        category: TicketCategory,
        channel: TicketChannel = TicketChannel.WEB_FORM,
        priority: Optional[TicketPriority] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> SupportTicket:
        """Create new support ticket"""
        # Generate ticket ID and number
        ticket_id = f"ticket_{datetime.utcnow().timestamp()}"
        ticket_number = f"SUP-{self.ticket_counter:06d}"
        self.ticket_counter += 1
        
        # Auto-detect priority if not provided
        if not priority:
            priority = self._detect_priority(subject, description, category)
        
        # Create ticket
        ticket = SupportTicket(
            ticket_id=ticket_id,
            ticket_number=ticket_number,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            subject=subject,
            description=description,
            category=category,
            channel=channel,
            priority=priority
        )
        
        # Apply SLA
        ticket.sla_deadline = self._calculate_sla_deadline(ticket)
        
        # Analyze sentiment
        ticket.sentiment = self._analyze_sentiment(description)
        
        # Store ticket
        self.tickets[ticket_id] = ticket
        self.tickets_by_customer[customer_id].append(ticket_id)
        self.tickets_by_status[TicketStatus.NEW].add(ticket_id)
        
        # Create initial message
        initial_message = TicketMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            ticket_id=ticket_id,
            sender_id=customer_id,
            sender_type="customer",
            content=description,
            sentiment=ticket.sentiment
        )
        self.messages[ticket_id].append(initial_message)
        
        # Handle attachments
        if attachments:
            for att_data in attachments:
                attachment = await self._store_attachment(ticket_id, customer_id, att_data)
                initial_message.attachments.append(attachment.attachment_id)
        
        # Auto-assignment
        await self._auto_assign_ticket(ticket)
        
        # Trigger notifications
        await self._notify_ticket_created(ticket)
        
        return ticket
    
    def _detect_priority(
        self,
        subject: str,
        description: str,
        category: TicketCategory
    ) -> TicketPriority:
        """Auto-detect ticket priority"""
        text = f"{subject} {description}".lower()
        
        # Critical keywords
        critical_keywords = [
            "down", "outage", "emergency", "urgent", "critical",
            "data loss", "security breach", "cannot access", "broken"
        ]
        
        # High priority keywords
        high_keywords = [
            "error", "fail", "bug", "issue", "problem",
            "not working", "incorrect", "wrong"
        ]
        
        # Check for critical issues
        if any(keyword in text for keyword in critical_keywords):
            return TicketPriority.CRITICAL
        
        if category == TicketCategory.SECURITY:
            return TicketPriority.HIGH
        
        if any(keyword in text for keyword in high_keywords):
            return TicketPriority.HIGH
        
        if category in [TicketCategory.BILLING, TicketCategory.ACCOUNT]:
            return TicketPriority.MEDIUM
        
        return TicketPriority.MEDIUM
    
    def _analyze_sentiment(self, text: str) -> CustomerSentiment:
        """Analyze customer sentiment from text"""
        # In production, use NLP/ML models
        # This is a simplified version
        
        text_lower = text.lower()
        
        # Negative indicators
        negative_words = [
            "frustrated", "angry", "disappointed", "unacceptable",
            "terrible", "horrible", "worst", "hate", "annoyed"
        ]
        
        # Positive indicators
        positive_words = [
            "thank", "appreciate", "great", "excellent", "happy",
            "pleased", "wonderful", "love", "best"
        ]
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count >= 3:
            return CustomerSentiment.VERY_NEGATIVE
        elif negative_count >= 1:
            return CustomerSentiment.NEGATIVE
        elif positive_count >= 2:
            return CustomerSentiment.VERY_POSITIVE
        elif positive_count >= 1:
            return CustomerSentiment.POSITIVE
        else:
            return CustomerSentiment.NEUTRAL
    
    def _calculate_sla_deadline(self, ticket: SupportTicket) -> datetime:
        """Calculate SLA deadline for ticket"""
        # Find applicable SLA policy
        applicable_sla = None
        
        for policy in self.sla_policies.values():
            if policy.priority and policy.priority == ticket.priority:
                applicable_sla = policy
                break
        
        if not applicable_sla:
            applicable_sla = self.sla_policies.get("standard_sla")
        
        if not applicable_sla:
            return ticket.created_at + timedelta(hours=24)
        
        # Calculate deadline
        if applicable_sla.business_hours_only:
            # In production, calculate based on business hours
            return ticket.created_at + timedelta(minutes=applicable_sla.resolution_time)
        else:
            return ticket.created_at + timedelta(minutes=applicable_sla.resolution_time)
    
    async def _auto_assign_ticket(self, ticket: SupportTicket):
        """Auto-assign ticket to best available agent"""
        # Find available agents with matching skills
        available_agents = []
        
        for agent in self.agents.values():
            if not agent.is_available:
                continue
            
            if agent.current_load >= agent.max_concurrent_tickets:
                continue
            
            # Check specialization match
            if ticket.category in agent.specializations:
                available_agents.append((agent, 3))  # High priority
            elif ticket.category in [TicketCategory.TECHNICAL, TicketCategory.BUG_REPORT] and "technical" in agent.skills:
                available_agents.append((agent, 2))  # Medium priority
            else:
                available_agents.append((agent, 1))  # Low priority
        
        if available_agents:
            # Sort by priority and load
            available_agents.sort(key=lambda x: (-x[1], x[0].current_load))
            best_agent = available_agents[0][0]
            
            # Assign ticket
            ticket.assigned_to = best_agent.agent_id
            ticket.status = TicketStatus.OPEN
            best_agent.current_load += 1
            
            self.tickets_by_agent[best_agent.agent_id].add(ticket.ticket_id)
            self.tickets_by_status[TicketStatus.NEW].discard(ticket.ticket_id)
            self.tickets_by_status[TicketStatus.OPEN].add(ticket.ticket_id)
    
    async def _store_attachment(
        self,
        ticket_id: str,
        uploaded_by: str,
        attachment_data: Dict[str, Any]
    ) -> TicketAttachment:
        """Store ticket attachment"""
        attachment = TicketAttachment(
            attachment_id=f"att_{datetime.utcnow().timestamp()}",
            filename=attachment_data["filename"],
            size_bytes=attachment_data["size"],
            mime_type=attachment_data.get("mime_type", "application/octet-stream"),
            uploaded_by=uploaded_by,
            storage_path=f"/attachments/{ticket_id}/{attachment_data['filename']}"
        )
        
        self.attachments[attachment.attachment_id] = attachment
        
        # In production, upload to storage service
        
        return attachment
    
    async def add_message(
        self,
        ticket_id: str,
        sender_id: str,
        sender_type: str,
        content: str,
        is_internal_note: bool = False,
        attachments: List[Dict[str, Any]] = None
    ) -> TicketMessage:
        """Add message to ticket"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Create message
        message = TicketMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            is_internal_note=is_internal_note
        )
        
        # Analyze sentiment for customer messages
        if sender_type == "customer":
            message.sentiment = self._analyze_sentiment(content)
            ticket.response_count += 1
        
        # Handle attachments
        if attachments:
            for att_data in attachments:
                attachment = await self._store_attachment(ticket_id, sender_id, att_data)
                message.attachments.append(attachment.attachment_id)
        
        # Store message
        self.messages[ticket_id].append(message)
        
        # Update ticket
        ticket.updated_at = datetime.utcnow()
        
        # Track first response
        if sender_type == "agent" and not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
        
        # Update status if needed
        if ticket.status == TicketStatus.WAITING_CUSTOMER and sender_type == "customer":
            await self.update_ticket_status(ticket_id, TicketStatus.OPEN, sender_id)
        
        return message
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        updated_by: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Update ticket status"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False
        
        old_status = ticket.status
        
        # Update indexes
        self.tickets_by_status[old_status].discard(ticket_id)
        self.tickets_by_status[new_status].add(ticket_id)
        
        # Update ticket
        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()
        
        # Track resolution
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
            if resolution_notes:
                await self.add_message(
                    ticket_id,
                    updated_by,
                    "agent",
                    f"Resolution: {resolution_notes}",
                    is_internal_note=False
                )
        
        # Track closure
        if new_status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()
        
        # Track reopening
        if old_status in [TicketStatus.RESOLVED, TicketStatus.CLOSED] and new_status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
            ticket.reopen_count += 1
        
        # Create status change message
        status_message = TicketMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            ticket_id=ticket_id,
            sender_id=updated_by,
            sender_type="system",
            content=f"Status changed from {old_status.value} to {new_status.value}",
            status_change=new_status
        )
        self.messages[ticket_id].append(status_message)
        
        return True
    
    async def escalate_ticket(
        self,
        ticket_id: str,
        reason: str,
        escalated_by: str
    ) -> bool:
        """Escalate ticket"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False
        
        # Increase priority
        old_priority = ticket.priority
        if ticket.priority == TicketPriority.LOW:
            ticket.priority = TicketPriority.MEDIUM
        elif ticket.priority == TicketPriority.MEDIUM:
            ticket.priority = TicketPriority.HIGH
        elif ticket.priority == TicketPriority.HIGH:
            ticket.priority = TicketPriority.CRITICAL
        
        ticket.escalation_count += 1
        
        # Create escalation message
        escalation_message = TicketMessage(
            message_id=f"msg_{datetime.utcnow().timestamp()}",
            ticket_id=ticket_id,
            sender_id=escalated_by,
            sender_type="system",
            content=f"Ticket escalated: {reason}. Priority changed from {old_priority.value} to {ticket.priority.value}",
            priority_change=ticket.priority
        )
        self.messages[ticket_id].append(escalation_message)
        
        # Notify managers
        await self._notify_escalation(ticket, reason)
        
        return True
    
    async def merge_tickets(
        self,
        primary_ticket_id: str,
        secondary_ticket_ids: List[str],
        merged_by: str
    ) -> bool:
        """Merge multiple tickets into one"""
        primary = self.tickets.get(primary_ticket_id)
        if not primary:
            return False
        
        for secondary_id in secondary_ticket_ids:
            secondary = self.tickets.get(secondary_id)
            if not secondary:
                continue
            
            # Copy messages
            for message in self.messages[secondary_id]:
                message.ticket_id = primary_ticket_id
                self.messages[primary_ticket_id].append(message)
            
            # Update status
            secondary.status = TicketStatus.CLOSED
            secondary.closed_at = datetime.utcnow()
            
            # Add reference
            primary.related_tickets.append(secondary_id)
            
            # Add merge note
            merge_note = f"Merged ticket {secondary.ticket_number} into this ticket"
            await self.add_message(
                primary_ticket_id,
                merged_by,
                "system",
                merge_note,
                is_internal_note=True
            )
        
        return True
    
    def search_tickets(
        self,
        query: Optional[str] = None,
        status: Optional[List[TicketStatus]] = None,
        priority: Optional[List[TicketPriority]] = None,
        category: Optional[List[TicketCategory]] = None,
        assigned_to: Optional[str] = None,
        customer_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SupportTicket]:
        """Search tickets with filters"""
        results = []
        
        for ticket in self.tickets.values():
            # Apply filters
            if status and ticket.status not in status:
                continue
            
            if priority and ticket.priority not in priority:
                continue
            
            if category and ticket.category not in category:
                continue
            
            if assigned_to and ticket.assigned_to != assigned_to:
                continue
            
            if customer_id and ticket.customer_id != customer_id:
                continue
            
            if date_from and ticket.created_at < date_from:
                continue
            
            if date_to and ticket.created_at > date_to:
                continue
            
            # Text search
            if query:
                query_lower = query.lower()
                if not any([
                    query_lower in ticket.subject.lower(),
                    query_lower in ticket.description.lower(),
                    query_lower in ticket.ticket_number.lower(),
                    any(query_lower in tag for tag in ticket.tags)
                ]):
                    continue
            
            results.append(ticket)
            
            if len(results) >= limit:
                break
        
        # Sort by priority and date
        results.sort(key=lambda t: (
            -list(TicketPriority).index(t.priority),
            -t.created_at.timestamp()
        ))
        
        return results
    
    def get_ticket_metrics(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Get support metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        
        metrics = {
            "total_tickets": 0,
            "tickets_by_status": defaultdict(int),
            "tickets_by_priority": defaultdict(int),
            "tickets_by_category": defaultdict(int),
            "avg_first_response_time": [],
            "avg_resolution_time": [],
            "customer_satisfaction": [],
            "sla_compliance": {"met": 0, "breached": 0}
        }
        
        for ticket in self.tickets.values():
            if ticket.created_at < cutoff_date:
                continue
            
            metrics["total_tickets"] += 1
            metrics["tickets_by_status"][ticket.status.value] += 1
            metrics["tickets_by_priority"][ticket.priority.value] += 1
            metrics["tickets_by_category"][ticket.category.value] += 1
            
            # Response time
            if ticket.first_response_at:
                response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 60
                metrics["avg_first_response_time"].append(response_time)
            
            # Resolution time
            if ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                metrics["avg_resolution_time"].append(resolution_time)
            
            # SLA compliance
            if ticket.sla_deadline:
                if ticket.resolved_at and ticket.resolved_at <= ticket.sla_deadline:
                    metrics["sla_compliance"]["met"] += 1
                elif datetime.utcnow() > ticket.sla_deadline and ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                    metrics["sla_compliance"]["breached"] += 1
        
        # Calculate averages
        if metrics["avg_first_response_time"]:
            metrics["avg_first_response_time"] = sum(metrics["avg_first_response_time"]) / len(metrics["avg_first_response_time"])
        else:
            metrics["avg_first_response_time"] = 0
        
        if metrics["avg_resolution_time"]:
            metrics["avg_resolution_time"] = sum(metrics["avg_resolution_time"]) / len(metrics["avg_resolution_time"])
        else:
            metrics["avg_resolution_time"] = 0
        
        # SLA percentage
        total_sla = metrics["sla_compliance"]["met"] + metrics["sla_compliance"]["breached"]
        if total_sla > 0:
            metrics["sla_compliance"]["percentage"] = (metrics["sla_compliance"]["met"] / total_sla) * 100
        else:
            metrics["sla_compliance"]["percentage"] = 100
        
        return dict(metrics)
    
    async def _notify_ticket_created(self, ticket: SupportTicket):
        """Send notifications for new ticket"""
        # In production, integrate with notification services
        pass
    
    async def _notify_escalation(self, ticket: SupportTicket, reason: str):
        """Send escalation notifications"""
        # In production, integrate with notification services
        pass

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize ticket system
        ticket_system = TicketManagementSystem()
        
        # Create sample agent
        agent = Agent(
            agent_id="agent_001",
            name="John Doe",
            email="john@support.com",
            skills=["technical", "billing"],
            specializations=[TicketCategory.TECHNICAL, TicketCategory.BUG_REPORT]
        )
        ticket_system.agents[agent.agent_id] = agent
        
        # Create ticket
        ticket = await ticket_system.create_ticket(
            customer_id="cust_123",
            customer_email="customer@example.com",
            customer_name="Jane Smith",
            subject="Application crashes when uploading large files",
            description="The application freezes and crashes when I try to upload files larger than 100MB. This is urgent as it's blocking our work.",
            category=TicketCategory.BUG_REPORT,
            channel=TicketChannel.EMAIL
        )
        
        print(f"Created ticket: {ticket.ticket_number}")
        print(f"Priority: {ticket.priority.value}")
        print(f"Status: {ticket.status.value}")
        print(f"Assigned to: {ticket.assigned_to}")
        print(f"SLA deadline: {ticket.sla_deadline}")
        
        # Add agent response
        await ticket_system.add_message(
            ticket.ticket_id,
            "agent_001",
            "agent",
            "Thank you for reporting this issue. I can see this is affecting your work. Let me investigate this right away. Can you please provide the following information:\n1. What browser and version are you using?\n2. What is the exact file size that causes the crash?\n3. Are there any error messages displayed?"
        )
        
        # Customer response
        await ticket_system.add_message(
            ticket.ticket_id,
            "cust_123",
            "customer",
            "I'm using Chrome version 120. The file is exactly 125MB. No error message, the whole application just freezes."
        )
        
        # Update status
        await ticket_system.update_ticket_status(
            ticket.ticket_id,
            TicketStatus.IN_PROGRESS,
            "agent_001"
        )
        
        # Search tickets
        print("\nSearching for bug reports...")
        bug_tickets = ticket_system.search_tickets(
            category=[TicketCategory.BUG_REPORT],
            status=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS]
        )
        
        for bug_ticket in bug_tickets:
            print(f"- {bug_ticket.ticket_number}: {bug_ticket.subject}")
        
        # Get metrics
        metrics = ticket_system.get_ticket_metrics(30)
        print(f"\nSupport Metrics (Last 30 days):")
        print(f"Total tickets: {metrics['total_tickets']}")
        print(f"Avg first response time: {metrics['avg_first_response_time']:.1f} minutes")
        print(f"SLA compliance: {metrics['sla_compliance']['percentage']:.1f}%")
    
    asyncio.run(main())