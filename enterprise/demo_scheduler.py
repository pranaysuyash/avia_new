"""
Demo Scheduling and Trial Management System

Manages enterprise demo scheduling, trial accounts, and onboarding
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date, time
from enum import Enum
import uuid
import asyncio
from pydantic import BaseModel, EmailStr, Field, validator
import calendar

from database.models import User, Organization
from notifications.api import notify_api

class DemoStatus(str, Enum):
    """Demo appointment status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class TrialStatus(str, Enum):
    """Trial account status"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CONVERTED = "converted"
    CANCELLED = "cancelled"

class DemoType(str, Enum):
    """Types of demos"""
    DISCOVERY = "discovery"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    TRAINING = "training"
    FOLLOW_UP = "follow_up"

class TimeSlot(BaseModel):
    """Available time slot"""
    date: date
    start_time: time
    end_time: time
    available: bool = True
    timezone: str = "UTC"

class DemoRequest(BaseModel):
    """Demo scheduling request"""
    company_name: str
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str]
    
    # Demo details
    demo_type: DemoType = DemoType.DISCOVERY
    preferred_dates: List[date]
    preferred_time_range: Optional[str] = "9am-5pm"
    timezone: str = "America/New_York"
    
    # Context
    company_size: Optional[str]
    use_case: Optional[str]
    current_solution: Optional[str]
    budget_range: Optional[str]
    
    # Additional info
    questions: Optional[str]
    how_heard_about_us: Optional[str]

class DemoAppointment(BaseModel):
    """Scheduled demo appointment"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: DemoRequest
    
    # Scheduling
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int = 45
    timezone: str
    
    # Meeting details
    meeting_link: str
    calendar_invite_sent: bool = False
    reminder_sent: bool = False
    
    # Status
    status: DemoStatus = DemoStatus.SCHEDULED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Notes
    internal_notes: Optional[str]
    demo_notes: Optional[str]
    follow_up_required: bool = False

class TrialAccount(BaseModel):
    """Trial account information"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Trial details
    start_date: datetime
    end_date: datetime
    duration_days: int = 14
    
    # Limits
    user_limit: int = 5
    processing_hours_limit: float = 10.0
    storage_gb_limit: float = 5.0
    
    # Features
    enabled_features: List[str]
    
    # Usage tracking
    users_created: int = 0
    processing_hours_used: float = 0.0
    storage_gb_used: float = 0.0
    
    # Status
    status: TrialStatus = TrialStatus.PENDING
    activation_date: Optional[datetime]
    conversion_date: Optional[datetime]
    
    # Engagement
    last_activity: Optional[datetime]
    engagement_score: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OnboardingStep(BaseModel):
    """Onboarding workflow step"""
    id: str
    name: str
    description: str
    order: int
    required: bool = True
    completed: bool = False
    completed_at: Optional[datetime]
    
    # Step details
    action_type: str  # "video", "document", "task", "meeting"
    content_url: Optional[str]
    estimated_minutes: int = 10

class OnboardingWorkflow(BaseModel):
    """Customer onboarding workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    trial_id: Optional[str]
    
    # Workflow
    steps: List[OnboardingStep]
    current_step: int = 0
    
    # Progress
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    completion_percentage: float = 0.0
    
    # Assignment
    assigned_to: Optional[str]  # Customer success manager ID
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DemoScheduler:
    """Manages demo scheduling and availability"""
    
    def __init__(self):
        self.business_hours = {
            "start": time(9, 0),  # 9 AM
            "end": time(17, 0),   # 5 PM
        }
        self.demo_duration = timedelta(minutes=45)
        self.buffer_time = timedelta(minutes=15)
        self.appointments: Dict[str, DemoAppointment] = {}
    
    def get_available_slots(
        self,
        start_date: date,
        end_date: date,
        timezone: str = "UTC"
    ) -> List[TimeSlot]:
        """Get available demo slots for date range"""
        slots = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                daily_slots = self._get_daily_slots(current_date, timezone)
                slots.extend(daily_slots)
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _get_daily_slots(self, date: date, timezone: str) -> List[TimeSlot]:
        """Get available slots for a specific day"""
        slots = []
        current_time = datetime.combine(date, self.business_hours["start"])
        end_time = datetime.combine(date, self.business_hours["end"])
        
        while current_time + self.demo_duration <= end_time:
            # Check if slot is available
            if self._is_slot_available(date, current_time.time()):
                slot = TimeSlot(
                    date=date,
                    start_time=current_time.time(),
                    end_time=(current_time + self.demo_duration).time(),
                    available=True,
                    timezone=timezone
                )
                slots.append(slot)
            
            current_time += self.demo_duration + self.buffer_time
        
        return slots
    
    def _is_slot_available(self, date: date, start_time: time) -> bool:
        """Check if a time slot is available"""
        # Check against existing appointments
        for appointment in self.appointments.values():
            if (appointment.scheduled_date == date and
                appointment.scheduled_time == start_time and
                appointment.status in [DemoStatus.SCHEDULED, DemoStatus.CONFIRMED]):
                return False
        
        return True
    
    async def schedule_demo(
        self,
        request: DemoRequest,
        preferred_slot: TimeSlot
    ) -> DemoAppointment:
        """Schedule a demo appointment"""
        # Create appointment
        appointment = DemoAppointment(
            request=request,
            scheduled_date=preferred_slot.date,
            scheduled_time=preferred_slot.start_time,
            timezone=preferred_slot.timezone,
            meeting_link=self._generate_meeting_link(),
            internal_notes=f"Demo type: {request.demo_type}, Use case: {request.use_case}"
        )
        
        # Store appointment
        self.appointments[appointment.id] = appointment
        
        # Send confirmation email
        await self._send_demo_confirmation(appointment)
        
        # Schedule reminder
        await self._schedule_reminder(appointment)
        
        return appointment
    
    def _generate_meeting_link(self) -> str:
        """Generate unique meeting link"""
        meeting_id = str(uuid.uuid4())[:8]
        return f"https://meet.transcription-platform.com/demo/{meeting_id}"
    
    async def _send_demo_confirmation(self, appointment: DemoAppointment):
        """Send demo confirmation email"""
        await notify_api.send_email(
            user_id="system",
            notification_type="demo_scheduled",
            data={
                "contact_name": appointment.request.contact_name,
                "company_name": appointment.request.company_name,
                "demo_date": appointment.scheduled_date.strftime("%B %d, %Y"),
                "demo_time": appointment.scheduled_time.strftime("%I:%M %p"),
                "timezone": appointment.timezone,
                "meeting_link": appointment.meeting_link,
                "demo_type": appointment.request.demo_type
            }
        )
        
        appointment.calendar_invite_sent = True
        appointment.updated_at = datetime.utcnow()
    
    async def _schedule_reminder(self, appointment: DemoAppointment):
        """Schedule demo reminder"""
        # Calculate reminder time (1 day before)
        reminder_datetime = datetime.combine(
            appointment.scheduled_date - timedelta(days=1),
            time(10, 0)  # 10 AM day before
        )
        
        # In production, this would use a task scheduler
        # For now, we'll just mark it
        appointment.reminder_sent = False
    
    async def complete_demo(
        self,
        appointment_id: str,
        notes: str,
        follow_up_required: bool = True
    ):
        """Mark demo as completed"""
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        appointment.status = DemoStatus.COMPLETED
        appointment.demo_notes = notes
        appointment.follow_up_required = follow_up_required
        appointment.updated_at = datetime.utcnow()
        
        # Send follow-up email
        if follow_up_required:
            await self._send_follow_up_email(appointment)
    
    async def _send_follow_up_email(self, appointment: DemoAppointment):
        """Send post-demo follow-up"""
        await notify_api.send_email(
            user_id="system",
            notification_type="demo_follow_up",
            data={
                "contact_name": appointment.request.contact_name,
                "company_name": appointment.request.company_name,
                "demo_date": appointment.scheduled_date.strftime("%B %d, %Y"),
                "next_steps": "Schedule a technical deep-dive or start your trial"
            }
        )

class TrialManager:
    """Manages trial accounts"""
    
    def __init__(self):
        self.trials: Dict[str, TrialAccount] = {}
        self.default_trial_features = [
            "transcription",
            "entity_extraction",
            "summarization",
            "export",
            "api_access_limited"
        ]
    
    async def create_trial(
        self,
        organization_id: str,
        duration_days: int = 14,
        custom_limits: Optional[Dict[str, Any]] = None
    ) -> TrialAccount:
        """Create a new trial account"""
        # Calculate dates
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)
        
        # Create trial
        trial = TrialAccount(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            enabled_features=self.default_trial_features,
            status=TrialStatus.PENDING
        )
        
        # Apply custom limits if provided
        if custom_limits:
            if "user_limit" in custom_limits:
                trial.user_limit = custom_limits["user_limit"]
            if "processing_hours_limit" in custom_limits:
                trial.processing_hours_limit = custom_limits["processing_hours_limit"]
            if "storage_gb_limit" in custom_limits:
                trial.storage_gb_limit = custom_limits["storage_gb_limit"]
        
        # Store trial
        self.trials[trial.id] = trial
        
        # Send welcome email
        await self._send_trial_welcome(trial)
        
        return trial
    
    async def activate_trial(self, trial_id: str) -> TrialAccount:
        """Activate a trial account"""
        trial = self.trials.get(trial_id)
        if not trial:
            raise ValueError("Trial not found")
        
        trial.status = TrialStatus.ACTIVE
        trial.activation_date = datetime.utcnow()
        trial.updated_at = datetime.utcnow()
        
        # Schedule expiration reminder
        await self._schedule_expiration_reminders(trial)
        
        return trial
    
    async def check_trial_limits(self, trial_id: str) -> Dict[str, Any]:
        """Check trial usage against limits"""
        trial = self.trials.get(trial_id)
        if not trial:
            raise ValueError("Trial not found")
        
        return {
            "users": {
                "used": trial.users_created,
                "limit": trial.user_limit,
                "percentage": (trial.users_created / trial.user_limit) * 100
            },
            "processing_hours": {
                "used": trial.processing_hours_used,
                "limit": trial.processing_hours_limit,
                "percentage": (trial.processing_hours_used / trial.processing_hours_limit) * 100
            },
            "storage_gb": {
                "used": trial.storage_gb_used,
                "limit": trial.storage_gb_limit,
                "percentage": (trial.storage_gb_used / trial.storage_gb_limit) * 100
            },
            "days_remaining": (trial.end_date - datetime.utcnow()).days
        }
    
    async def update_trial_usage(
        self,
        trial_id: str,
        processing_hours: float = 0,
        storage_gb: float = 0,
        new_users: int = 0
    ):
        """Update trial usage metrics"""
        trial = self.trials.get(trial_id)
        if not trial:
            raise ValueError("Trial not found")
        
        trial.processing_hours_used += processing_hours
        trial.storage_gb_used += storage_gb
        trial.users_created += new_users
        trial.last_activity = datetime.utcnow()
        trial.updated_at = datetime.utcnow()
        
        # Update engagement score
        trial.engagement_score = self._calculate_engagement_score(trial)
        
        # Check if limits exceeded
        await self._check_limit_warnings(trial)
    
    def _calculate_engagement_score(self, trial: TrialAccount) -> float:
        """Calculate trial engagement score (0-100)"""
        score = 0.0
        
        # Usage percentage (40 points)
        usage_percentage = (trial.processing_hours_used / trial.processing_hours_limit) * 100
        score += min(usage_percentage * 0.4, 40)
        
        # User adoption (30 points)
        user_percentage = (trial.users_created / trial.user_limit) * 100
        score += min(user_percentage * 0.3, 30)
        
        # Activity recency (20 points)
        if trial.last_activity:
            days_since_activity = (datetime.utcnow() - trial.last_activity).days
            if days_since_activity == 0:
                score += 20
            elif days_since_activity == 1:
                score += 15
            elif days_since_activity <= 3:
                score += 10
            elif days_since_activity <= 7:
                score += 5
        
        # Trial duration usage (10 points)
        if trial.activation_date:
            days_active = (datetime.utcnow() - trial.activation_date).days
            trial_progress = (days_active / trial.duration_days) * 100
            if trial_progress >= 50:
                score += 10
            elif trial_progress >= 25:
                score += 5
        
        return min(score, 100.0)
    
    async def _check_limit_warnings(self, trial: TrialAccount):
        """Check and send warnings for approaching limits"""
        limits = await self.check_trial_limits(trial.id)
        
        # Check each limit
        for resource, usage in limits.items():
            if resource == "days_remaining":
                if usage <= 3 and usage > 0:
                    await self._send_expiration_warning(trial, usage)
            else:
                if usage["percentage"] >= 80:
                    await self._send_limit_warning(trial, resource, usage)
    
    async def _send_trial_welcome(self, trial: TrialAccount):
        """Send trial welcome email"""
        # Implementation would send actual email
        pass
    
    async def _schedule_expiration_reminders(self, trial: TrialAccount):
        """Schedule trial expiration reminders"""
        # Would schedule reminders at 7 days, 3 days, 1 day before expiration
        pass
    
    async def _send_limit_warning(self, trial: TrialAccount, resource: str, usage: Dict):
        """Send limit warning notification"""
        # Implementation would send actual notification
        pass
    
    async def _send_expiration_warning(self, trial: TrialAccount, days_remaining: int):
        """Send trial expiration warning"""
        # Implementation would send actual notification
        pass

class OnboardingManager:
    """Manages customer onboarding workflows"""
    
    def __init__(self):
        self.workflows: Dict[str, OnboardingWorkflow] = {}
        self.default_steps = self._create_default_steps()
    
    def _create_default_steps(self) -> List[OnboardingStep]:
        """Create default onboarding steps"""
        return [
            OnboardingStep(
                id="welcome",
                name="Welcome & Overview",
                description="Introduction to the platform and key features",
                order=1,
                action_type="video",
                content_url="/onboarding/welcome-video",
                estimated_minutes=5
            ),
            OnboardingStep(
                id="account_setup",
                name="Account Setup",
                description="Complete your organization profile and preferences",
                order=2,
                action_type="task",
                estimated_minutes=10
            ),
            OnboardingStep(
                id="first_transcription",
                name="Your First Transcription",
                description="Upload and transcribe your first audio/video file",
                order=3,
                action_type="task",
                estimated_minutes=15
            ),
            OnboardingStep(
                id="team_invites",
                name="Invite Your Team",
                description="Add team members and set permissions",
                order=4,
                action_type="task",
                required=False,
                estimated_minutes=10
            ),
            OnboardingStep(
                id="api_setup",
                name="API Integration",
                description="Set up API access and test integration",
                order=5,
                action_type="document",
                content_url="/docs/api-quickstart",
                required=False,
                estimated_minutes=20
            ),
            OnboardingStep(
                id="training_session",
                name="Training Session",
                description="Schedule a personalized training with our team",
                order=6,
                action_type="meeting",
                required=False,
                estimated_minutes=45
            )
        ]
    
    def create_workflow(
        self,
        organization_id: str,
        trial_id: Optional[str] = None,
        custom_steps: Optional[List[OnboardingStep]] = None
    ) -> OnboardingWorkflow:
        """Create onboarding workflow for organization"""
        steps = custom_steps or self.default_steps.copy()
        
        workflow = OnboardingWorkflow(
            organization_id=organization_id,
            trial_id=trial_id,
            steps=steps
        )
        
        self.workflows[workflow.id] = workflow
        return workflow
    
    def complete_step(
        self,
        workflow_id: str,
        step_id: str
    ) -> OnboardingWorkflow:
        """Mark a step as completed"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")
        
        # Find and complete the step
        for step in workflow.steps:
            if step.id == step_id:
                step.completed = True
                step.completed_at = datetime.utcnow()
                break
        
        # Update workflow progress
        workflow.updated_at = datetime.utcnow()
        workflow.completion_percentage = self._calculate_completion(workflow)
        
        # Check if all required steps are complete
        if self._all_required_complete(workflow):
            workflow.completed_at = datetime.utcnow()
        
        return workflow
    
    def _calculate_completion(self, workflow: OnboardingWorkflow) -> float:
        """Calculate workflow completion percentage"""
        total_steps = len([s for s in workflow.steps if s.required])
        completed_steps = len([s for s in workflow.steps if s.required and s.completed])
        
        return (completed_steps / total_steps * 100) if total_steps > 0 else 0
    
    def _all_required_complete(self, workflow: OnboardingWorkflow) -> bool:
        """Check if all required steps are complete"""
        return all(step.completed for step in workflow.steps if step.required)
    
    def get_next_step(self, workflow_id: str) -> Optional[OnboardingStep]:
        """Get the next uncompleted step"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        for step in workflow.steps:
            if not step.completed:
                return step
        
        return None

# Example usage
if __name__ == "__main__":
    # Demo scheduler example
    scheduler = DemoScheduler()
    
    # Get available slots
    slots = scheduler.get_available_slots(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        timezone="America/New_York"
    )
    
    print(f"Available slots: {len(slots)}")
    
    # Trial manager example
    trial_manager = TrialManager()
    
    # Onboarding manager example
    onboarding_manager = OnboardingManager()
    workflow = onboarding_manager.create_workflow(
        organization_id="org_123",
        trial_id="trial_123"
    )
    
    print(f"Created onboarding workflow with {len(workflow.steps)} steps")