"""
Customer Feedback and Survey System

Collect and analyze customer feedback through surveys, NPS, and feature requests
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import asyncio
from collections import defaultdict
import statistics
import json

class FeedbackType(str, Enum):
    """Types of feedback"""
    SURVEY = "survey"
    NPS = "nps"  # Net Promoter Score
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    TESTIMONIAL = "testimonial"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"

class SurveyType(str, Enum):
    """Survey types"""
    SATISFACTION = "satisfaction"
    PRODUCT_FEEDBACK = "product_feedback"
    ONBOARDING = "onboarding"
    CHURN = "churn"
    FEATURE_USAGE = "feature_usage"
    CUSTOM = "custom"

class QuestionType(str, Enum):
    """Survey question types"""
    RATING = "rating"  # 1-5 or 1-10 scale
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    TEXT = "text"
    YES_NO = "yes_no"
    NPS = "nps"  # 0-10 scale
    MATRIX = "matrix"  # Grid of questions

class ResponseStatus(str, Enum):
    """Feedback response status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESPONDED = "responded"
    CLOSED = "closed"
    ESCALATED = "escalated"

class SurveyQuestion(BaseModel):
    """Survey question definition"""
    question_id: str
    text: str
    question_type: QuestionType
    
    # Options for choice questions
    options: List[str] = []
    
    # Settings
    required: bool = True
    
    # For rating questions
    min_value: Optional[int] = 1
    max_value: Optional[int] = 5
    
    # For matrix questions
    rows: List[str] = []
    columns: List[str] = []
    
    # Logic
    conditional_on: Optional[str]  # question_id
    conditional_value: Optional[Any]  # Show if previous answer matches

class SurveyTemplate(BaseModel):
    """Survey template"""
    template_id: str
    name: str
    description: str
    survey_type: SurveyType
    
    # Questions
    questions: List[SurveyQuestion]
    
    # Settings
    is_active: bool = True
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Targeting
    target_audience: Optional[str]  # all, new_users, premium, etc.
    trigger_event: Optional[str]  # signup, purchase, support_ticket_closed
    
    # Display settings
    display_delay_seconds: int = 0
    allow_anonymous: bool = True

class SurveyResponse(BaseModel):
    """Individual survey response"""
    response_id: str
    survey_id: str
    respondent_id: Optional[str]
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime]
    
    # Answers
    answers: Dict[str, Any] = {}  # question_id -> answer
    
    # Metadata
    ip_address: Optional[str]
    user_agent: Optional[str]
    referrer: Optional[str]
    
    # Completion
    is_complete: bool = False
    completion_rate: float = 0

class FeedbackItem(BaseModel):
    """General feedback item"""
    feedback_id: str
    feedback_type: FeedbackType
    
    # Submitter
    user_id: Optional[str]
    user_email: Optional[str]
    user_name: Optional[str]
    
    # Content
    title: Optional[str]
    description: str
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Categorization
    category: Optional[str]
    tags: List[str] = []
    priority: int = 0  # Higher = more important
    
    # Status
    status: ResponseStatus = ResponseStatus.PENDING
    assigned_to: Optional[str]
    
    # Response
    response: Optional[str]
    responded_at: Optional[datetime]
    responded_by: Optional[str]
    
    # Voting (for feature requests)
    upvotes: int = 0
    downvotes: int = 0
    voters: Set[str] = set()
    
    # Related items
    related_feedback: List[str] = []
    attachments: List[str] = []

class NPSResponse(BaseModel):
    """Net Promoter Score response"""
    nps_id: str
    user_id: str
    score: int  # 0-10
    
    # Follow-up
    reason: Optional[str]
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Context
    trigger_event: Optional[str]
    user_segment: Optional[str]

class FeedbackAnalytics(BaseModel):
    """Feedback analytics summary"""
    period_start: datetime
    period_end: datetime
    
    # Volume metrics
    total_feedback: int = 0
    feedback_by_type: Dict[str, int] = {}
    
    # NPS metrics
    nps_score: Optional[float]
    nps_responses: int = 0
    promoters: int = 0
    passives: int = 0
    detractors: int = 0
    
    # Survey metrics
    survey_responses: int = 0
    avg_completion_rate: float = 0
    satisfaction_score: Optional[float]
    
    # Feature requests
    feature_requests: int = 0
    most_requested_features: List[Dict[str, Any]] = []
    
    # Response metrics
    avg_response_time_hours: Optional[float]
    response_rate: float = 0

class FeedbackSystem:
    """Main feedback management system"""
    
    def __init__(self):
        self.survey_templates: Dict[str, SurveyTemplate] = {}
        self.survey_responses: Dict[str, List[SurveyResponse]] = defaultdict(list)
        self.feedback_items: Dict[str, FeedbackItem] = {}
        self.nps_responses: List[NPSResponse] = []
        
        # Indexes
        self.feedback_by_type: Dict[FeedbackType, Set[str]] = defaultdict(set)
        self.feedback_by_user: Dict[str, Set[str]] = defaultdict(set)
        self.feedback_by_status: Dict[ResponseStatus, Set[str]] = defaultdict(set)
        
        # Initialize sample templates
        self._init_sample_templates()
    
    def _init_sample_templates(self):
        """Initialize sample survey templates"""
        # Customer satisfaction survey
        csat_template = SurveyTemplate(
            template_id="csat_default",
            name="Customer Satisfaction Survey",
            description="Measure customer satisfaction with our service",
            survey_type=SurveyType.SATISFACTION,
            questions=[
                SurveyQuestion(
                    question_id="q1",
                    text="How satisfied are you with our transcription service?",
                    question_type=QuestionType.RATING,
                    min_value=1,
                    max_value=5
                ),
                SurveyQuestion(
                    question_id="q2",
                    text="How likely are you to recommend us to a colleague?",
                    question_type=QuestionType.NPS,
                    min_value=0,
                    max_value=10
                ),
                SurveyQuestion(
                    question_id="q3",
                    text="What features do you use most?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["Transcription", "Speaker Diarization", "Entity Recognition", "API", "Integrations"],
                    required=False
                ),
                SurveyQuestion(
                    question_id="q4",
                    text="Any suggestions for improvement?",
                    question_type=QuestionType.TEXT,
                    required=False
                )
            ]
        )
        self.survey_templates[csat_template.template_id] = csat_template
    
    def create_survey(
        self,
        name: str,
        description: str,
        survey_type: SurveyType,
        questions: List[SurveyQuestion],
        target_audience: Optional[str] = None
    ) -> SurveyTemplate:
        """Create new survey template"""
        template = SurveyTemplate(
            template_id=f"survey_{datetime.utcnow().timestamp()}",
            name=name,
            description=description,
            survey_type=survey_type,
            questions=questions,
            target_audience=target_audience
        )
        
        self.survey_templates[template.template_id] = template
        
        return template
    
    def submit_survey_response(
        self,
        survey_id: str,
        answers: Dict[str, Any],
        respondent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SurveyResponse:
        """Submit survey response"""
        template = self.survey_templates.get(survey_id)
        if not template:
            raise ValueError(f"Survey template {survey_id} not found")
        
        # Create response
        response = SurveyResponse(
            response_id=f"resp_{datetime.utcnow().timestamp()}",
            survey_id=survey_id,
            respondent_id=respondent_id,
            answers=answers,
            ip_address=metadata.get("ip_address") if metadata else None,
            user_agent=metadata.get("user_agent") if metadata else None
        )
        
        # Calculate completion rate
        required_questions = [q for q in template.questions if q.required]
        answered_required = sum(1 for q in required_questions if q.question_id in answers)
        response.completion_rate = answered_required / len(required_questions) if required_questions else 1.0
        
        if response.completion_rate >= 1.0:
            response.is_complete = True
            response.completed_at = datetime.utcnow()
        
        # Store response
        self.survey_responses[survey_id].append(response)
        
        # Extract NPS if present
        for question in template.questions:
            if question.question_type == QuestionType.NPS and question.question_id in answers:
                self._record_nps_response(
                    respondent_id or "anonymous",
                    answers[question.question_id],
                    answers.get(f"{question.question_id}_reason")
                )
        
        return response
    
    def submit_feedback(
        self,
        feedback_type: FeedbackType,
        description: str,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        category: Optional[str] = None,
        tags: List[str] = None
    ) -> FeedbackItem:
        """Submit general feedback"""
        feedback = FeedbackItem(
            feedback_id=f"feedback_{datetime.utcnow().timestamp()}",
            feedback_type=feedback_type,
            title=title,
            description=description,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            category=category,
            tags=tags or []
        )
        
        # Auto-categorize if not provided
        if not category:
            feedback.category = self._auto_categorize_feedback(description)
        
        # Set priority based on type
        if feedback_type == FeedbackType.BUG_REPORT:
            feedback.priority = 2
        elif feedback_type == FeedbackType.COMPLAINT:
            feedback.priority = 1
        
        # Store feedback
        self.feedback_items[feedback.feedback_id] = feedback
        
        # Update indexes
        self.feedback_by_type[feedback_type].add(feedback.feedback_id)
        if user_id:
            self.feedback_by_user[user_id].add(feedback.feedback_id)
        self.feedback_by_status[ResponseStatus.PENDING].add(feedback.feedback_id)
        
        return feedback
    
    def _auto_categorize_feedback(self, description: str) -> str:
        """Auto-categorize feedback based on content"""
        description_lower = description.lower()
        
        # Simple keyword-based categorization
        if any(word in description_lower for word in ["api", "integration", "webhook"]):
            return "API"
        elif any(word in description_lower for word in ["transcription", "accuracy", "audio"]):
            return "Transcription"
        elif any(word in description_lower for word in ["bill", "payment", "subscription", "price"]):
            return "Billing"
        elif any(word in description_lower for word in ["login", "password", "account", "email"]):
            return "Account"
        else:
            return "General"
    
    def _record_nps_response(
        self,
        user_id: str,
        score: int,
        reason: Optional[str] = None
    ):
        """Record NPS response"""
        nps = NPSResponse(
            nps_id=f"nps_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            score=score,
            reason=reason
        )
        
        self.nps_responses.append(nps)
    
    def vote_on_feedback(
        self,
        feedback_id: str,
        user_id: str,
        upvote: bool = True
    ) -> bool:
        """Vote on feedback (for feature requests)"""
        feedback = self.feedback_items.get(feedback_id)
        if not feedback:
            return False
        
        # Check if already voted
        if user_id in feedback.voters:
            return False
        
        # Record vote
        if upvote:
            feedback.upvotes += 1
        else:
            feedback.downvotes += 1
        
        feedback.voters.add(user_id)
        feedback.updated_at = datetime.utcnow()
        
        return True
    
    def respond_to_feedback(
        self,
        feedback_id: str,
        response: str,
        responder_id: str,
        close: bool = True
    ) -> bool:
        """Respond to feedback"""
        feedback = self.feedback_items.get(feedback_id)
        if not feedback:
            return False
        
        # Update feedback
        feedback.response = response
        feedback.responded_at = datetime.utcnow()
        feedback.responded_by = responder_id
        
        # Update status
        if close:
            feedback.status = ResponseStatus.CLOSED
            self.feedback_by_status[ResponseStatus.PENDING].discard(feedback_id)
            self.feedback_by_status[ResponseStatus.CLOSED].add(feedback_id)
        else:
            feedback.status = ResponseStatus.RESPONDED
            self.feedback_by_status[ResponseStatus.PENDING].discard(feedback_id)
            self.feedback_by_status[ResponseStatus.RESPONDED].add(feedback_id)
        
        feedback.updated_at = datetime.utcnow()
        
        return True
    
    def get_survey_analytics(
        self,
        survey_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get survey analytics"""
        template = self.survey_templates.get(survey_id)
        if not template:
            return {}
        
        responses = self.survey_responses.get(survey_id, [])
        
        # Filter by date
        if date_from:
            responses = [r for r in responses if r.started_at >= date_from]
        if date_to:
            responses = [r for r in responses if r.started_at <= date_to]
        
        if not responses:
            return {
                "survey_id": survey_id,
                "survey_name": template.name,
                "total_responses": 0
            }
        
        # Calculate analytics
        analytics = {
            "survey_id": survey_id,
            "survey_name": template.name,
            "total_responses": len(responses),
            "complete_responses": len([r for r in responses if r.is_complete]),
            "completion_rate": len([r for r in responses if r.is_complete]) / len(responses) * 100,
            "avg_completion_time": self._calculate_avg_completion_time(responses),
            "question_analytics": {}
        }
        
        # Analyze each question
        for question in template.questions:
            q_id = question.question_id
            answers = [r.answers.get(q_id) for r in responses if q_id in r.answers]
            
            if not answers:
                continue
            
            if question.question_type == QuestionType.RATING:
                analytics["question_analytics"][q_id] = {
                    "question": question.text,
                    "type": "rating",
                    "avg_rating": statistics.mean(answers),
                    "distribution": self._calculate_distribution(answers, question.min_value, question.max_value)
                }
            
            elif question.question_type == QuestionType.NPS:
                nps_score = self._calculate_nps_score(answers)
                analytics["question_analytics"][q_id] = {
                    "question": question.text,
                    "type": "nps",
                    "nps_score": nps_score,
                    "promoters": len([a for a in answers if a >= 9]),
                    "passives": len([a for a in answers if 7 <= a <= 8]),
                    "detractors": len([a for a in answers if a <= 6])
                }
            
            elif question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
                # Flatten multiple choice answers
                all_choices = []
                for answer in answers:
                    if isinstance(answer, list):
                        all_choices.extend(answer)
                    else:
                        all_choices.append(answer)
                
                analytics["question_analytics"][q_id] = {
                    "question": question.text,
                    "type": "choice",
                    "response_counts": dict(defaultdict(int, {
                        choice: all_choices.count(choice) for choice in set(all_choices)
                    }))
                }
            
            elif question.question_type == QuestionType.YES_NO:
                analytics["question_analytics"][q_id] = {
                    "question": question.text,
                    "type": "yes_no",
                    "yes_count": len([a for a in answers if a]),
                    "no_count": len([a for a in answers if not a])
                }
        
        return analytics
    
    def _calculate_avg_completion_time(self, responses: List[SurveyResponse]) -> float:
        """Calculate average survey completion time in seconds"""
        completion_times = []
        
        for response in responses:
            if response.completed_at:
                time_diff = (response.completed_at - response.started_at).total_seconds()
                if time_diff < 3600:  # Exclude outliers (> 1 hour)
                    completion_times.append(time_diff)
        
        return statistics.mean(completion_times) if completion_times else 0
    
    def _calculate_distribution(self, values: List[int], min_val: int, max_val: int) -> Dict[int, int]:
        """Calculate distribution of rating values"""
        distribution = {i: 0 for i in range(min_val, max_val + 1)}
        
        for value in values:
            if min_val <= value <= max_val:
                distribution[value] += 1
        
        return distribution
    
    def _calculate_nps_score(self, scores: List[int]) -> float:
        """Calculate Net Promoter Score"""
        if not scores:
            return 0
        
        promoters = len([s for s in scores if s >= 9])
        detractors = len([s for s in scores if s <= 6])
        
        return ((promoters - detractors) / len(scores)) * 100
    
    def get_feedback_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> FeedbackAnalytics:
        """Get overall feedback analytics"""
        # Set date range
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        analytics = FeedbackAnalytics(
            period_start=date_from,
            period_end=date_to
        )
        
        # Filter feedback by date
        filtered_feedback = [
            f for f in self.feedback_items.values()
            if date_from <= f.created_at <= date_to
        ]
        
        analytics.total_feedback = len(filtered_feedback)
        
        # Feedback by type
        for feedback in filtered_feedback:
            feedback_type = feedback.feedback_type.value
            analytics.feedback_by_type[feedback_type] = analytics.feedback_by_type.get(feedback_type, 0) + 1
        
        # NPS metrics
        filtered_nps = [
            nps for nps in self.nps_responses
            if date_from <= nps.created_at <= date_to
        ]
        
        if filtered_nps:
            scores = [nps.score for nps in filtered_nps]
            analytics.nps_score = self._calculate_nps_score(scores)
            analytics.nps_responses = len(filtered_nps)
            analytics.promoters = len([s for s in scores if s >= 9])
            analytics.passives = len([s for s in scores if 7 <= s <= 8])
            analytics.detractors = len([s for s in scores if s <= 6])
        
        # Survey metrics
        all_survey_responses = []
        for responses in self.survey_responses.values():
            filtered_responses = [
                r for r in responses
                if date_from <= r.started_at <= date_to
            ]
            all_survey_responses.extend(filtered_responses)
        
        if all_survey_responses:
            analytics.survey_responses = len(all_survey_responses)
            analytics.avg_completion_rate = statistics.mean([
                r.completion_rate for r in all_survey_responses
            ]) * 100
        
        # Feature requests
        feature_requests = [
            f for f in filtered_feedback
            if f.feedback_type == FeedbackType.FEATURE_REQUEST
        ]
        
        analytics.feature_requests = len(feature_requests)
        
        # Most requested features (top 5)
        if feature_requests:
            feature_requests.sort(key=lambda f: f.upvotes, reverse=True)
            analytics.most_requested_features = [
                {
                    "title": f.title or f.description[:50],
                    "votes": f.upvotes,
                    "category": f.category
                }
                for f in feature_requests[:5]
            ]
        
        # Response metrics
        responded_feedback = [
            f for f in filtered_feedback
            if f.responded_at
        ]
        
        if responded_feedback:
            response_times = [
                (f.responded_at - f.created_at).total_seconds() / 3600
                for f in responded_feedback
            ]
            analytics.avg_response_time_hours = statistics.mean(response_times)
            analytics.response_rate = (len(responded_feedback) / len(filtered_feedback)) * 100
        
        return analytics
    
    def search_feedback(
        self,
        query: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        status: Optional[ResponseStatus] = None,
        user_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[FeedbackItem]:
        """Search feedback items"""
        results = []
        
        # Start with all feedback
        feedback_items = list(self.feedback_items.values())
        
        # Apply filters
        if feedback_type:
            feedback_items = [
                f for f in feedback_items
                if f.feedback_type == feedback_type
            ]
        
        if status:
            feedback_items = [
                f for f in feedback_items
                if f.status == status
            ]
        
        if user_id:
            feedback_items = [
                f for f in feedback_items
                if f.user_id == user_id
            ]
        
        if date_from:
            feedback_items = [
                f for f in feedback_items
                if f.created_at >= date_from
            ]
        
        if date_to:
            feedback_items = [
                f for f in feedback_items
                if f.created_at <= date_to
            ]
        
        # Text search
        if query:
            query_lower = query.lower()
            feedback_items = [
                f for f in feedback_items
                if query_lower in (f.title or "").lower()
                or query_lower in f.description.lower()
                or any(query_lower in tag for tag in f.tags)
            ]
        
        # Sort by priority and date
        feedback_items.sort(
            key=lambda f: (-f.priority, -f.created_at.timestamp())
        )
        
        return feedback_items[:limit]

# Example usage
if __name__ == "__main__":
    # Initialize feedback system
    feedback_system = FeedbackSystem()
    
    # Submit survey response
    survey_response = feedback_system.submit_survey_response(
        "csat_default",
        {
            "q1": 5,  # Very satisfied
            "q2": 9,  # Likely to recommend (promoter)
            "q3": ["Transcription", "API"],
            "q4": "Great service! Would love to see real-time transcription."
        },
        respondent_id="user_123"
    )
    
    print(f"Survey response submitted: {survey_response.response_id}")
    print(f"Completion rate: {survey_response.completion_rate * 100}%")
    
    # Submit feature request
    feature_request = feedback_system.submit_feedback(
        FeedbackType.FEATURE_REQUEST,
        "It would be great to have real-time transcription capabilities for live events and meetings.",
        title="Real-time transcription",
        user_id="user_456",
        user_email="user@example.com",
        tags=["transcription", "real-time", "live"]
    )
    
    print(f"\nFeature request submitted: {feature_request.feedback_id}")
    
    # Vote on feature request
    feedback_system.vote_on_feedback(feature_request.feedback_id, "user_789", upvote=True)
    
    # Get survey analytics
    survey_analytics = feedback_system.get_survey_analytics("csat_default")
    print(f"\nSurvey Analytics:")
    print(f"Total responses: {survey_analytics['total_responses']}")
    print(f"Completion rate: {survey_analytics['completion_rate']:.1f}%")
    
    # Get overall analytics
    overall_analytics = feedback_system.get_feedback_analytics()
    print(f"\nFeedback Analytics (Last 30 days):")
    print(f"Total feedback: {overall_analytics.total_feedback}")
    if overall_analytics.nps_score:
        print(f"NPS Score: {overall_analytics.nps_score:.1f}")
    print(f"Feature requests: {overall_analytics.feature_requests}")