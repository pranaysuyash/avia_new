#!/usr/bin/env python3
"""
Customer Call Analysis and Insights System
Task 146: Comprehensive analysis of customer service calls for quality,
sentiment, compliance, and business insights.
"""

import asyncio
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
import hashlib
import logging
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallType(Enum):
    """Types of customer calls."""
    SUPPORT = "support"
    SALES = "sales"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"
    FOLLOW_UP = "follow_up"
    BILLING = "billing"
    TECHNICAL = "technical"
    CANCELLATION = "cancellation"
    RETENTION = "retention"
    FEEDBACK = "feedback"

class SentimentLevel(Enum):
    """Customer sentiment levels."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class CallOutcome(Enum):
    """Call resolution outcomes."""
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    PENDING = "pending"
    UNRESOLVED = "unresolved"
    CALLBACK_REQUIRED = "callback_required"
    TRANSFERRED = "transferred"

class ComplianceStatus(Enum):
    """Compliance check status."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL_VIOLATION = "critical_violation"

class QualityScore(Enum):
    """Quality assessment scores."""
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"

@dataclass
class CallParticipant:
    """Information about a call participant."""
    id: str
    name: str
    role: str  # agent, customer, supervisor, etc.
    department: Optional[str] = None
    employee_id: Optional[str] = None
    speaking_time: float = 0.0
    statement_count: int = 0
    interruption_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CustomerProfile:
    """Customer information and history."""
    customer_id: str
    name: Optional[str] = None
    account_type: Optional[str] = None
    tenure: Optional[int] = None  # months
    previous_calls: int = 0
    satisfaction_history: List[float] = field(default_factory=list)
    value_segment: Optional[str] = None  # high, medium, low
    risk_level: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallSegment:
    """A segment of the call with analysis."""
    id: str
    speaker: CallParticipant
    text: str
    start_time: float
    end_time: float
    sentiment: SentimentLevel
    sentiment_confidence: float
    topics: List[str]
    intent: Optional[str] = None
    emotional_indicators: List[str] = field(default_factory=list)
    compliance_flags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallIssue:
    """An issue or problem identified in the call."""
    issue_id: str
    category: str
    description: str
    severity: str  # low, medium, high, critical
    mentioned_by: str  # participant_id
    timestamp: float
    resolution_status: str
    subcategory: Optional[str] = None
    resolution_time: Optional[float] = None
    escalation_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallInsight:
    """Business insight derived from call analysis."""
    insight_id: str
    category: str  # process_improvement, training_need, product_feedback, etc.
    insight_text: str
    confidence: float
    impact_level: str  # low, medium, high
    actionable: bool
    recommended_actions: List[str] = field(default_factory=list)
    affected_areas: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallAnalysisResult:
    """Complete call analysis result."""
    call_id: str
    call_type: CallType
    call_outcome: CallOutcome
    duration: float  # seconds
    participants: List[CallParticipant]
    customer_profile: Optional[CustomerProfile]
    segments: List[CallSegment]
    issues: List[CallIssue]
    insights: List[CallInsight]
    overall_sentiment: SentimentLevel
    quality_score: QualityScore
    compliance_status: ComplianceStatus
    key_topics: List[str]
    summary: str
    recommendations: List[str]
    processing_metadata: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class SentimentAnalyzer:
    """Analyzes sentiment in customer calls."""
    
    def __init__(self):
        self.sentiment_patterns = self._initialize_sentiment_patterns()
        self.emotional_indicators = self._initialize_emotional_indicators()
    
    def _initialize_sentiment_patterns(self) -> Dict[SentimentLevel, List[str]]:
        """Initialize sentiment detection patterns."""
        return {
            SentimentLevel.VERY_POSITIVE: [
                r'\b(excellent|amazing|fantastic|wonderful|outstanding|perfect|love it)\b',
                r'\b(very satisfied|extremely happy|absolutely great)\b'
            ],
            SentimentLevel.POSITIVE: [
                r'\b(good|great|nice|happy|satisfied|pleased|thank you|appreciate)\b',
                r'\b(helpful|resolved|working well)\b'
            ],
            SentimentLevel.NEUTRAL: [
                r'\b(okay|fine|understand|noted|alright)\b',
                r'\b(maybe|perhaps|possibly)\b'
            ],
            SentimentLevel.NEGATIVE: [
                r'\b(bad|poor|disappointed|unhappy|frustrated|annoyed)\b',
                r'\b(not working|broken|issue|problem)\b'
            ],
            SentimentLevel.VERY_NEGATIVE: [
                r'\b(terrible|awful|horrible|disgusting|hate|furious|angry)\b',
                r'\b(cancel|cancellation|refund|lawsuit|complaint)\b'
            ]
        }
    
    def _initialize_emotional_indicators(self) -> Dict[str, List[str]]:
        """Initialize emotional indicator patterns."""
        return {
            'frustration': ['sigh', 'ugh', 'seriously', 'ridiculous', 'unbelievable'],
            'confusion': ['confused', 'don\'t understand', 'what do you mean', 'huh'],
            'impatience': ['hurry up', 'taking too long', 'been waiting', 'quickly'],
            'satisfaction': ['perfect', 'exactly', 'great job', 'thank you so much'],
            'concern': ['worried', 'concerned', 'nervous', 'anxious'],
            'anger': ['angry', 'mad', 'furious', 'outraged', 'livid']
        }
    
    def analyze_sentiment(self, text: str) -> Tuple[SentimentLevel, float, List[str]]:
        """Analyze sentiment of text segment."""
        text_lower = text.lower()
        sentiment_scores = {}
        emotional_indicators = []
        
        # Calculate sentiment scores
        for sentiment, patterns in self.sentiment_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            sentiment_scores[sentiment] = score
        
        # Find emotional indicators
        for emotion, indicators in self.emotional_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    emotional_indicators.append(emotion)
                    break
        
        # Determine primary sentiment
        if not any(sentiment_scores.values()):
            return SentimentLevel.NEUTRAL, 0.5, emotional_indicators
        
        primary_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        max_score = sentiment_scores[primary_sentiment]
        
        # Calculate confidence based on score and text length
        word_count = len(text.split())
        confidence = min((max_score / max(word_count * 0.1, 1)) * 0.8 + 0.2, 1.0)
        
        return primary_sentiment, confidence, emotional_indicators

class TopicExtractor:
    """Extracts topics and intents from call segments."""
    
    def __init__(self):
        self.topic_patterns = self._initialize_topic_patterns()
        self.intent_patterns = self._initialize_intent_patterns()
    
    def _initialize_topic_patterns(self) -> Dict[str, List[str]]:
        """Initialize topic detection patterns."""
        return {
            'billing': ['bill', 'charge', 'payment', 'invoice', 'fee', 'cost', 'price'],
            'technical_support': ['not working', 'broken', 'error', 'bug', 'issue', 'problem', 'fix'],
            'account_management': ['account', 'profile', 'settings', 'password', 'login', 'access'],
            'product_features': ['feature', 'functionality', 'capability', 'option', 'setting'],
            'service_quality': ['quality', 'service', 'experience', 'satisfaction', 'feedback'],
            'cancellation': ['cancel', 'close', 'terminate', 'stop', 'end service'],
            'upgrade_downgrade': ['upgrade', 'downgrade', 'change plan', 'switch', 'modify'],
            'delivery_shipping': ['delivery', 'shipping', 'arrived', 'package', 'order'],
            'warranty_returns': ['warranty', 'return', 'exchange', 'defective', 'replacement'],
            'pricing_discounts': ['discount', 'promo', 'coupon', 'deal', 'offer', 'price match']
        }
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent detection patterns."""
        return {
            'get_information': ['what is', 'how do', 'can you tell me', 'i want to know', 'explain'],
            'report_problem': ['have a problem', 'not working', 'broken', 'issue with', 'error'],
            'request_service': ['need help', 'can you help', 'assistance', 'support', 'service'],
            'make_complaint': ['complaint', 'complain', 'not happy', 'dissatisfied', 'upset'],
            'request_refund': ['refund', 'money back', 'return', 'reimburse', 'credit'],
            'change_service': ['change', 'modify', 'update', 'switch', 'upgrade', 'downgrade'],
            'cancel_service': ['cancel', 'close account', 'terminate', 'stop service'],
            'provide_feedback': ['feedback', 'suggestion', 'recommend', 'improve', 'better']
        }
    
    def extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in self.topic_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def extract_intent(self, text: str) -> Optional[str]:
        """Extract primary intent from text."""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    score += 1
            intent_scores[intent] = score
        
        if not any(intent_scores.values()):
            return None
        
        return max(intent_scores, key=intent_scores.get)

class ComplianceChecker:
    """Checks compliance with customer service standards."""
    
    def __init__(self):
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_compliance_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance checking rules."""
        return {
            'greeting_check': {
                'patterns': [r'hello|hi|good morning|good afternoon|thank you for calling'],
                'required': True,
                'severity': 'medium',
                'description': 'Agent must provide proper greeting'
            },
            'identification_check': {
                'patterns': [r'my name is|this is|speaking with'],
                'required': True,
                'severity': 'high',
                'description': 'Agent must identify themselves'
            },
            'privacy_verification': {
                'patterns': [r'verify|confirm|security|account number|ssn'],
                'required': False,
                'severity': 'high',
                'description': 'Customer identity verification when handling sensitive info'
            },
            'hold_permission': {
                'patterns': [r'hold|just a moment|bear with me'],
                'follow_up': [r'may i|can i|permission|okay to'],
                'severity': 'medium',
                'description': 'Must ask permission before placing on hold'
            },
            'profanity_check': {
                'patterns': [r'\b(damn|hell|crap)\b'],  # Mild examples
                'prohibited': True,
                'severity': 'high',
                'description': 'Professional language required'
            },
            'closing_check': {
                'patterns': [r'anything else|help you with|have a great|thank you'],
                'required': True,
                'severity': 'medium',
                'description': 'Proper call closure required'
            }
        }
    
    def check_compliance(self, transcript: str, participants: List[CallParticipant]) -> Tuple[ComplianceStatus, List[str]]:
        """Check compliance issues in call transcript."""
        flags = []
        violations = 0
        warnings = 0
        
        transcript_lower = transcript.lower()
        
        for rule_name, rule in self.compliance_rules.items():
            if rule.get('required', False):
                found = any(re.search(pattern, transcript_lower) for pattern in rule['patterns'])
                if not found:
                    flags.append(f"{rule_name}: {rule['description']}")
                    if rule['severity'] == 'high':
                        violations += 1
                    else:
                        warnings += 1
            
            elif rule.get('prohibited', False):
                for pattern in rule['patterns']:
                    if re.search(pattern, transcript_lower):
                        flags.append(f"{rule_name}: {rule['description']} - Found: '{pattern}'")
                        violations += 1
            
            # Check follow-up requirements
            if 'follow_up' in rule:
                for pattern in rule['patterns']:
                    matches = list(re.finditer(pattern, transcript_lower))
                    for match in matches:
                        # Check context around match for follow-up
                        context_start = max(0, match.start() - 100)
                        context_end = min(len(transcript), match.end() + 100)
                        context = transcript[context_start:context_end].lower()
                        
                        if not any(re.search(follow_up, context) for follow_up in rule['follow_up']):
                            flags.append(f"{rule_name}: {rule['description']}")
                            if rule['severity'] == 'high':
                                violations += 1
                            else:
                                warnings += 1
        
        # Determine overall status
        if violations > 0:
            if violations >= 3:
                status = ComplianceStatus.CRITICAL_VIOLATION
            else:
                status = ComplianceStatus.VIOLATION
        elif warnings > 0:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.COMPLIANT
        
        return status, flags

class QualityAssessment:
    """Assesses call quality based on multiple factors."""
    
    def __init__(self):
        self.quality_metrics = self._initialize_quality_metrics()
    
    def _initialize_quality_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality assessment metrics."""
        return {
            'resolution_effectiveness': {
                'weight': 0.3,
                'factors': ['issue_resolved', 'customer_satisfaction', 'follow_up_needed']
            },
            'communication_skills': {
                'weight': 0.25,
                'factors': ['clarity', 'empathy', 'professionalism', 'active_listening']
            },
            'process_adherence': {
                'weight': 0.2,
                'factors': ['compliance_score', 'procedure_followed', 'documentation']
            },
            'customer_experience': {
                'weight': 0.15,
                'factors': ['wait_time', 'transfers', 'call_duration', 'satisfaction']
            },
            'product_knowledge': {
                'weight': 0.1,
                'factors': ['accuracy', 'completeness', 'confidence']
            }
        }
    
    def assess_quality(self, call_data: Dict[str, Any]) -> Tuple[QualityScore, float, Dict[str, float]]:
        """Assess overall call quality."""
        metric_scores = {}
        
        # Calculate scores for each metric
        for metric, config in self.quality_metrics.items():
            score = self._calculate_metric_score(metric, call_data)
            metric_scores[metric] = score
        
        # Calculate weighted overall score
        overall_score = sum(
            metric_scores[metric] * config['weight']
            for metric, config in self.quality_metrics.items()
        )
        
        # Convert to quality score
        if overall_score >= 0.9:
            quality = QualityScore.EXCELLENT
        elif overall_score >= 0.8:
            quality = QualityScore.GOOD
        elif overall_score >= 0.7:
            quality = QualityScore.SATISFACTORY
        elif overall_score >= 0.6:
            quality = QualityScore.NEEDS_IMPROVEMENT
        else:
            quality = QualityScore.POOR
        
        return quality, overall_score, metric_scores
    
    def _calculate_metric_score(self, metric: str, call_data: Dict[str, Any]) -> float:
        """Calculate score for a specific metric."""
        # Mock scoring logic - in real implementation, this would be more sophisticated
        base_score = 0.75
        
        if metric == 'resolution_effectiveness':
            outcome = call_data.get('outcome', CallOutcome.UNRESOLVED)
            if outcome == CallOutcome.RESOLVED:
                base_score = 0.9
            elif outcome == CallOutcome.PENDING:
                base_score = 0.7
            else:
                base_score = 0.5
        
        elif metric == 'communication_skills':
            sentiment = call_data.get('overall_sentiment', SentimentLevel.NEUTRAL)
            if sentiment in [SentimentLevel.POSITIVE, SentimentLevel.VERY_POSITIVE]:
                base_score = 0.85
            elif sentiment == SentimentLevel.NEUTRAL:
                base_score = 0.75
            else:
                base_score = 0.6
        
        elif metric == 'process_adherence':
            compliance = call_data.get('compliance_status', ComplianceStatus.WARNING)
            if compliance == ComplianceStatus.COMPLIANT:
                base_score = 0.9
            elif compliance == ComplianceStatus.WARNING:
                base_score = 0.7
            else:
                base_score = 0.5
        
        elif metric == 'customer_experience':
            duration = call_data.get('duration', 600)  # seconds
            # Optimal duration is 5-10 minutes
            if 300 <= duration <= 600:
                base_score = 0.85
            elif duration < 300:
                base_score = 0.7  # Possibly rushed
            else:
                base_score = 0.6  # Too long
        
        return min(base_score, 1.0)

class InsightGenerator:
    """Generates business insights from call analysis."""
    
    def __init__(self):
        self.insight_patterns = self._initialize_insight_patterns()
    
    def _initialize_insight_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize insight generation patterns."""
        return {
            'training_needs': {
                'triggers': ['compliance_violation', 'poor_quality', 'knowledge_gap'],
                'impact': 'high',
                'actionable': True
            },
            'process_improvement': {
                'triggers': ['long_duration', 'multiple_transfers', 'escalation'],
                'impact': 'medium',
                'actionable': True
            },
            'product_feedback': {
                'triggers': ['feature_request', 'bug_report', 'usability_issue'],
                'impact': 'medium',
                'actionable': True
            },
            'customer_retention': {
                'triggers': ['cancellation_intent', 'dissatisfaction', 'competitor_mention'],
                'impact': 'high',
                'actionable': True
            },
            'upsell_opportunity': {
                'triggers': ['feature_inquiry', 'capacity_issue', 'positive_sentiment'],
                'impact': 'medium',
                'actionable': True
            }
        }
    
    def generate_insights(self, call_analysis: CallAnalysisResult) -> List[CallInsight]:
        """Generate insights from call analysis."""
        insights = []
        
        # Analyze for training needs
        if call_analysis.quality_score in [QualityScore.POOR, QualityScore.NEEDS_IMPROVEMENT]:
            insights.append(CallInsight(
                insight_id=str(uuid.uuid4()),
                category='training_needs',
                insight_text=f"Agent requires additional training based on {call_analysis.quality_score.value} quality score",
                confidence=0.8,
                impact_level='high',
                actionable=True,
                recommended_actions=['Schedule coaching session', 'Review quality guidelines'],
                affected_areas=['agent_development', 'quality_management']
            ))
        
        # Analyze for process improvements
        if call_analysis.duration > 900:  # 15 minutes
            insights.append(CallInsight(
                insight_id=str(uuid.uuid4()),
                category='process_improvement',
                insight_text=f"Call duration ({call_analysis.duration/60:.1f} minutes) exceeds optimal range",
                confidence=0.7,
                impact_level='medium',
                actionable=True,
                recommended_actions=['Review call handling procedures', 'Implement time management training'],
                affected_areas=['operational_efficiency', 'customer_experience']
            ))
        
        # Analyze for product feedback
        product_topics = [topic for topic in call_analysis.key_topics 
                         if topic in ['product_features', 'technical_support', 'warranty_returns']]
        if product_topics and call_analysis.overall_sentiment in [SentimentLevel.NEGATIVE, SentimentLevel.VERY_NEGATIVE]:
            insights.append(CallInsight(
                insight_id=str(uuid.uuid4()),
                category='product_feedback',
                insight_text=f"Negative feedback on product areas: {', '.join(product_topics)}",
                confidence=0.75,
                impact_level='medium',
                actionable=True,
                recommended_actions=['Forward to product team', 'Analyze similar calls', 'Consider product improvements'],
                affected_areas=['product_development', 'quality_assurance']
            ))
        
        # Analyze for retention opportunities
        if any(issue.category == 'cancellation' for issue in call_analysis.issues):
            insights.append(CallInsight(
                insight_id=str(uuid.uuid4()),
                category='customer_retention',
                insight_text="Customer expressing cancellation intent - retention opportunity",
                confidence=0.9,
                impact_level='high',
                actionable=True,
                recommended_actions=['Immediate retention specialist contact', 'Review account value', 'Offer retention incentives'],
                affected_areas=['customer_retention', 'revenue_protection']
            ))
        
        return insights

class CustomerCallAnalysisSystem:
    """Main system for customer call analysis."""
    
    def __init__(self, db_path: str = "customer_calls.db"):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.compliance_checker = ComplianceChecker()
        self.quality_assessor = QualityAssessment()
        self.insight_generator = InsightGenerator()
        self.db_path = db_path
        self.init_database()
        
        logger.info("Customer Call Analysis System initialized")
    
    def init_database(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    call_type TEXT,
                    outcome TEXT,
                    duration REAL,
                    overall_sentiment TEXT,
                    quality_score TEXT,
                    compliance_status TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Issues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_issues (
                    issue_id TEXT PRIMARY KEY,
                    call_id TEXT,
                    category TEXT,
                    severity TEXT,
                    description TEXT,
                    resolution_status TEXT,
                    FOREIGN KEY (call_id) REFERENCES calls (call_id)
                )
            """)
            
            # Insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS call_insights (
                    insight_id TEXT PRIMARY KEY,
                    call_id TEXT,
                    category TEXT,
                    insight_text TEXT,
                    confidence REAL,
                    impact_level TEXT,
                    actionable BOOLEAN,
                    FOREIGN KEY (call_id) REFERENCES calls (call_id)
                )
            """)
            
            conn.commit()
    
    async def analyze_call(self, transcript: str, call_metadata: Dict[str, Any] = None) -> CallAnalysisResult:
        """Perform comprehensive call analysis."""
        try:
            call_id = str(uuid.uuid4())
            logger.info(f"Analyzing customer call: {call_id}")
            
            # 1. Parse participants and segments
            participants = self._parse_participants(transcript)
            segments = self._parse_segments(transcript, participants)
            
            # 2. Analyze sentiment for each segment
            overall_sentiments = []
            for segment in segments:
                sentiment, confidence, emotions = self.sentiment_analyzer.analyze_sentiment(segment.text)
                segment.sentiment = sentiment
                segment.sentiment_confidence = confidence
                segment.emotional_indicators = emotions
                overall_sentiments.append(sentiment)
            
            # 3. Extract topics and intents
            all_topics = []
            for segment in segments:
                topics = self.topic_extractor.extract_topics(segment.text)
                intent = self.topic_extractor.extract_intent(segment.text)
                segment.topics = topics
                segment.intent = intent
                all_topics.extend(topics)
            
            # 4. Determine overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(overall_sentiments)
            
            # 5. Identify issues
            issues = self._identify_issues(segments, call_metadata)
            
            # 6. Check compliance
            compliance_status, compliance_flags = self.compliance_checker.check_compliance(transcript, participants)
            
            # 7. Assess quality
            call_data = {
                'outcome': call_metadata.get('outcome', CallOutcome.UNRESOLVED),
                'overall_sentiment': overall_sentiment,
                'compliance_status': compliance_status,
                'duration': call_metadata.get('duration', 300)
            }
            quality_score, quality_value, quality_metrics = self.quality_assessor.assess_quality(call_data)
            
            # 8. Determine call type and outcome
            call_type = self._determine_call_type(all_topics, segments)
            call_outcome = call_metadata.get('outcome', CallOutcome.PENDING)
            
            # 9. Generate summary
            summary = self._generate_summary(call_type, overall_sentiment, issues, quality_score)
            
            # 10. Create analysis result
            analysis = CallAnalysisResult(
                call_id=call_id,
                call_type=call_type,
                call_outcome=call_outcome,
                duration=call_metadata.get('duration', len(transcript.split()) * 0.5),  # Estimate
                participants=participants,
                customer_profile=call_metadata.get('customer_profile'),
                segments=segments,
                issues=issues,
                insights=[],  # Will be filled by insight generator
                overall_sentiment=overall_sentiment,
                quality_score=quality_score,
                compliance_status=compliance_status,
                key_topics=list(set(all_topics)),
                summary=summary,
                recommendations=self._generate_recommendations(quality_score, compliance_status, issues),
                processing_metadata={
                    'segments_count': len(segments),
                    'participants_count': len(participants),
                    'quality_value': quality_value,
                    'quality_metrics': quality_metrics,
                    'compliance_flags': compliance_flags
                }
            )
            
            # 11. Generate insights
            analysis.insights = self.insight_generator.generate_insights(analysis)
            
            # 12. Store in database
            self._store_analysis(analysis)
            
            logger.info("Customer call analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in customer call analysis: {str(e)}")
            # Return minimal analysis with error
            return CallAnalysisResult(
                call_id=str(uuid.uuid4()),
                call_type=CallType.SUPPORT,
                call_outcome=CallOutcome.UNRESOLVED,
                duration=0,
                participants=[],
                customer_profile=None,
                segments=[],
                issues=[],
                insights=[],
                overall_sentiment=SentimentLevel.NEUTRAL,
                quality_score=QualityScore.NEEDS_IMPROVEMENT,
                compliance_status=ComplianceStatus.WARNING,
                key_topics=[],
                summary="Analysis failed due to error.",
                recommendations=[],
                processing_metadata={'error': str(e)}
            )
    
    def _parse_participants(self, transcript: str) -> List[CallParticipant]:
        """Parse participants from transcript."""
        participants = {}
        lines = transcript.split('\n')
        
        for line in lines:
            line = line.strip()
            speaker_match = re.match(r'^([A-Z_]+):\s', line)
            if speaker_match:
                speaker_name = speaker_match.group(1)
                
                if speaker_name not in participants:
                    # Determine role
                    if any(role in speaker_name.lower() for role in ['agent', 'rep', 'support']):
                        role = 'agent'
                    elif any(role in speaker_name.lower() for role in ['customer', 'caller', 'client']):
                        role = 'customer'
                    else:
                        role = 'participant'
                    
                    participants[speaker_name] = CallParticipant(
                        id=hashlib.md5(speaker_name.encode()).hexdigest()[:8],
                        name=speaker_name,
                        role=role
                    )
                
                participants[speaker_name].statement_count += 1
        
        return list(participants.values())
    
    def _parse_segments(self, transcript: str, participants: List[CallParticipant]) -> List[CallSegment]:
        """Parse segments from transcript."""
        segments = []
        lines = transcript.split('\n')
        participant_lookup = {p.name: p for p in participants}
        current_time = 0.0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            speaker_match = re.match(r'^([A-Z_]+):\s*(.*)$', line)
            if speaker_match:
                speaker_name = speaker_match.group(1)
                text = speaker_match.group(2).strip()
                
                if speaker_name in participant_lookup and text:
                    duration = len(text.split()) * 0.5  # Estimate 0.5 seconds per word
                    
                    segment = CallSegment(
                        id=str(uuid.uuid4()),
                        speaker=participant_lookup[speaker_name],
                        text=text,
                        start_time=current_time,
                        end_time=current_time + duration,
                        sentiment=SentimentLevel.NEUTRAL,  # Will be updated
                        sentiment_confidence=0.0,
                        topics=[]
                    )
                    segments.append(segment)
                    current_time += duration
        
        return segments
    
    def _calculate_overall_sentiment(self, sentiments: List[SentimentLevel]) -> SentimentLevel:
        """Calculate overall sentiment from segment sentiments."""
        if not sentiments:
            return SentimentLevel.NEUTRAL
        
        # Map sentiments to numeric values
        sentiment_values = {
            SentimentLevel.VERY_NEGATIVE: -2,
            SentimentLevel.NEGATIVE: -1,
            SentimentLevel.NEUTRAL: 0,
            SentimentLevel.POSITIVE: 1,
            SentimentLevel.VERY_POSITIVE: 2
        }
        
        # Calculate average
        values = [sentiment_values[s] for s in sentiments]
        avg_value = statistics.mean(values)
        
        # Map back to sentiment level
        if avg_value <= -1.5:
            return SentimentLevel.VERY_NEGATIVE
        elif avg_value <= -0.5:
            return SentimentLevel.NEGATIVE
        elif avg_value <= 0.5:
            return SentimentLevel.NEUTRAL
        elif avg_value <= 1.5:
            return SentimentLevel.POSITIVE
        else:
            return SentimentLevel.VERY_POSITIVE
    
    def _identify_issues(self, segments: List[CallSegment], metadata: Dict[str, Any]) -> List[CallIssue]:
        """Identify issues mentioned in the call."""
        issues = []
        
        for segment in segments:
            text_lower = segment.text.lower()
            
            # Check for common issue patterns
            if any(word in text_lower for word in ['problem', 'issue', 'broken', 'not working']):
                severity = 'medium'
                if segment.sentiment in [SentimentLevel.NEGATIVE, SentimentLevel.VERY_NEGATIVE]:
                    severity = 'high'
                
                issue = CallIssue(
                    issue_id=str(uuid.uuid4()),
                    category='technical',
                    description=f"Technical issue reported: {segment.text[:100]}...",
                    severity=severity,
                    mentioned_by=segment.speaker.id,
                    timestamp=segment.start_time,
                    resolution_status='identified'
                )
                issues.append(issue)
            
            if any(word in text_lower for word in ['bill', 'charge', 'payment', 'invoice']):
                issue = CallIssue(
                    issue_id=str(uuid.uuid4()),
                    category='billing',
                    description=f"Billing inquiry: {segment.text[:100]}...",
                    severity='medium',
                    mentioned_by=segment.speaker.id,
                    timestamp=segment.start_time,
                    resolution_status='identified'
                )
                issues.append(issue)
        
        return issues
    
    def _determine_call_type(self, topics: List[str], segments: List[CallSegment]) -> CallType:
        """Determine the primary call type."""
        topic_counts = {}
        for topic in topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        if not topic_counts:
            return CallType.INQUIRY
        
        primary_topic = max(topic_counts, key=topic_counts.get)
        
        # Map topics to call types
        topic_to_type = {
            'billing': CallType.BILLING,
            'technical_support': CallType.TECHNICAL,
            'cancellation': CallType.CANCELLATION,
            'account_management': CallType.SUPPORT,
            'service_quality': CallType.COMPLAINT
        }
        
        return topic_to_type.get(primary_topic, CallType.INQUIRY)
    
    def _generate_summary(self, call_type: CallType, sentiment: SentimentLevel, 
                         issues: List[CallIssue], quality: QualityScore) -> str:
        """Generate call summary."""
        summary_parts = [
            f"{call_type.value.replace('_', ' ').title()} call",
            f"Customer sentiment: {sentiment.value.replace('_', ' ')}",
            f"Quality: {quality.value.replace('_', ' ')}"
        ]
        
        if issues:
            summary_parts.append(f"{len(issues)} issues identified")
        
        return ". ".join(summary_parts) + "."
    
    def _generate_recommendations(self, quality: QualityScore, compliance: ComplianceStatus, 
                                 issues: List[CallIssue]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if quality in [QualityScore.POOR, QualityScore.NEEDS_IMPROVEMENT]:
            recommendations.append("Schedule agent coaching session to improve call quality")
        
        if compliance != ComplianceStatus.COMPLIANT:
            recommendations.append("Review compliance training with agent")
        
        if len(issues) > 2:
            recommendations.append("Consider escalating to supervisor for complex issue resolution")
        
        if not recommendations:
            recommendations.append("Continue monitoring for quality assurance")
        
        return recommendations
    
    def _store_analysis(self, analysis: CallAnalysisResult):
        """Store analysis in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store main call record
            cursor.execute("""
                INSERT OR REPLACE INTO calls 
                (call_id, call_type, outcome, duration, overall_sentiment, quality_score, compliance_status, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.call_id,
                analysis.call_type.value,
                analysis.call_outcome.value,
                analysis.duration,
                analysis.overall_sentiment.value,
                analysis.quality_score.value,
                analysis.compliance_status.value,
                analysis.summary
            ))
            
            # Store issues
            for issue in analysis.issues:
                cursor.execute("""
                    INSERT INTO call_issues 
                    (issue_id, call_id, category, severity, description, resolution_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    issue.issue_id,
                    analysis.call_id,
                    issue.category,
                    issue.severity,
                    issue.description,
                    issue.resolution_status
                ))
            
            # Store insights
            for insight in analysis.insights:
                cursor.execute("""
                    INSERT INTO call_insights 
                    (insight_id, call_id, category, insight_text, confidence, impact_level, actionable)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight.insight_id,
                    analysis.call_id,
                    insight.category,
                    insight.insight_text,
                    insight.confidence,
                    insight.impact_level,
                    insight.actionable
                ))
            
            conn.commit()
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system analysis statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total calls
                cursor.execute("SELECT COUNT(*) FROM calls")
                total_calls = cursor.fetchone()[0]
                
                # Call type distribution
                cursor.execute("""
                    SELECT call_type, COUNT(*) 
                    FROM calls 
                    GROUP BY call_type 
                    ORDER BY COUNT(*) DESC
                """)
                call_type_distribution = cursor.fetchall()
                
                # Quality distribution
                cursor.execute("""
                    SELECT quality_score, COUNT(*) 
                    FROM calls 
                    GROUP BY quality_score
                """)
                quality_distribution = cursor.fetchall()
                
                # Sentiment distribution
                cursor.execute("""
                    SELECT overall_sentiment, COUNT(*) 
                    FROM calls 
                    GROUP BY overall_sentiment
                """)
                sentiment_distribution = cursor.fetchall()
                
                return {
                    'total_calls': total_calls,
                    'call_type_distribution': call_type_distribution,
                    'quality_distribution': quality_distribution,
                    'sentiment_distribution': sentiment_distribution,
                    'system_status': 'operational'
                }
        except Exception as e:
            return {
                'error': str(e),
                'system_status': 'error'
            }

# Demo function
async def demo_customer_call_analysis():
    """Demonstrate customer call analysis capabilities."""
    system = CustomerCallAnalysisSystem()
    
    print("📞 Customer Call Analysis System Demo")
    print("=" * 45)
    
    # Test cases for different call scenarios
    test_cases = [
        {
            'transcript': """
AGENT: Thank you for calling TechCorp support, my name is Sarah. How can I help you today?
CUSTOMER: Hi Sarah, I'm having trouble with my internet connection. It's been down for two hours.
AGENT: I'm sorry to hear that. Let me look into this for you. Can I get your account number?
CUSTOMER: Sure, it's 12345678.
AGENT: Thank you. I can see there's an outage in your area. We're working to fix it and expect service to be restored within the next hour.
CUSTOMER: That's frustrating but I appreciate you checking. Will I get a credit for the downtime?
AGENT: Absolutely, I'll apply a credit to your account for today's service interruption. Is there anything else I can help you with?
CUSTOMER: No, that covers it. Thank you for your help.
AGENT: You're welcome! Have a great day.
            """,
            'metadata': {
                'duration': 420,  # 7 minutes
                'outcome': CallOutcome.RESOLVED
            }
        },
        {
            'transcript': """
AGENT: Support line, this is Mike.
CUSTOMER: Finally! I've been on hold for 30 minutes. This is ridiculous!
AGENT: I apologize for the wait. What seems to be the problem?
CUSTOMER: My bill is completely wrong. You charged me twice for the same service.
AGENT: Let me look at that. What's your account number?
CUSTOMER: Why do I need to give you my account number again? I already entered it!
AGENT: I understand your frustration. The system doesn't always transfer that information.
CUSTOMER: This is terrible service. I want to cancel my account.
AGENT: I can help resolve the billing issue. Let me transfer you to our billing department.
CUSTOMER: More transfers? Forget it, I'm done with this company.
            """,
            'metadata': {
                'duration': 600,  # 10 minutes
                'outcome': CallOutcome.ESCALATED
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Call {i}:")
        print("-" * 30)
        
        # Analyze call
        analysis = await system.analyze_call(
            test_case['transcript'], 
            test_case['metadata']
        )
        
        # Display results
        print(f"Call ID: {analysis.call_id}")
        print(f"Call Type: {analysis.call_type.value}")
        print(f"Outcome: {analysis.call_outcome.value}")
        print(f"Duration: {analysis.duration/60:.1f} minutes")
        print(f"Overall Sentiment: {analysis.overall_sentiment.value}")
        print(f"Quality Score: {analysis.quality_score.value}")
        print(f"Compliance Status: {analysis.compliance_status.value}")
        
        # Participants
        print(f"\nParticipants:")
        for participant in analysis.participants:
            print(f"  - {participant.name} ({participant.role})")
        
        # Key topics
        if analysis.key_topics:
            print(f"\nKey Topics: {', '.join(analysis.key_topics)}")
        
        # Issues
        if analysis.issues:
            print(f"\nIssues Identified ({len(analysis.issues)}):")
            for issue in analysis.issues:
                print(f"  - {issue.category}: {issue.description[:50]}...")
        
        # Insights
        if analysis.insights:
            print(f"\nBusiness Insights ({len(analysis.insights)}):")
            for insight in analysis.insights:
                print(f"  - {insight.category}: {insight.insight_text}")
        
        # Recommendations
        if analysis.recommendations:
            print(f"\nRecommendations:")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        print(f"\nSummary: {analysis.summary}")
    
    # System statistics
    print(f"\n📊 System Statistics:")
    stats = system.get_system_statistics()
    print(f"Total Calls Analyzed: {stats.get('total_calls', 0)}")
    print(f"System Status: {stats.get('system_status', 'unknown')}")
    
    print(f"\n✅ Customer call analysis demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_customer_call_analysis())