"""
Customer Support and Help System
Provides comprehensive support features including help documentation, chat support,
tutorials, community forum, and feedback collection.
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import asyncio
from enum import Enum
import logging
from dataclasses import dataclass, asdict
import hashlib
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TicketStatus(Enum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(Enum):
    """Support ticket priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ArticleCategory(Enum):
    """Help article categories"""
    GETTING_STARTED = "getting_started"
    TRANSCRIPTION = "transcription"
    FEATURES = "features"
    BILLING = "billing"
    TECHNICAL = "technical"
    TROUBLESHOOTING = "troubleshooting"
    API = "api"
    SECURITY = "security"

class TutorialType(Enum):
    """Tutorial content types"""
    VIDEO = "video"
    INTERACTIVE = "interactive"
    ARTICLE = "article"
    WEBINAR = "webinar"

@dataclass
class SupportTicket:
    """Support ticket data structure"""
    id: str
    user_id: str
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    assigned_to: Optional[str]
    tags: List[str]
    attachments: List[Dict[str, str]]
    conversation: List[Dict[str, Any]]
    satisfaction_rating: Optional[int]

@dataclass
class HelpArticle:
    """Help documentation article"""
    id: str
    title: str
    slug: str
    content: str
    category: ArticleCategory
    tags: List[str]
    views: int
    helpful_count: int
    not_helpful_count: int
    created_at: datetime
    updated_at: datetime
    author: str
    related_articles: List[str]
    search_keywords: List[str]

@dataclass
class Tutorial:
    """Tutorial content"""
    id: str
    title: str
    description: str
    type: TutorialType
    duration_minutes: int
    difficulty: str  # beginner, intermediate, advanced
    content_url: str
    thumbnail_url: str
    tags: List[str]
    prerequisites: List[str]
    learning_objectives: List[str]
    views: int
    completion_rate: float
    rating: float
    created_at: datetime

@dataclass
class ForumPost:
    """Community forum post"""
    id: str
    author_id: str
    title: str
    content: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    views: int
    upvotes: int
    replies: List[Dict[str, Any]]
    is_solved: bool
    accepted_answer_id: Optional[str]

class SupportTicketManager:
    """Manages support tickets and customer inquiries"""
    
    def __init__(self):
        self.tickets: Dict[str, SupportTicket] = {}
        self.ticket_queue: List[str] = []
        self.agent_assignments: Dict[str, List[str]] = defaultdict(list)
        
    def create_ticket(self, user_id: str, subject: str, description: str,
                     category: str, priority: Optional[TicketPriority] = None,
                     attachments: Optional[List[Dict[str, str]]] = None) -> SupportTicket:
        """Create a new support ticket"""
        # Auto-detect priority if not provided
        if not priority:
            priority = self._detect_priority(subject, description)
        
        ticket = SupportTicket(
            id=f"TICKET-{str(uuid.uuid4())[:8].upper()}",
            user_id=user_id,
            subject=subject,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            category=category,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            resolved_at=None,
            assigned_to=None,
            tags=self._extract_tags(subject, description),
            attachments=attachments or [],
            conversation=[{
                "type": "customer",
                "message": description,
                "timestamp": datetime.utcnow().isoformat(),
                "attachments": attachments or []
            }],
            satisfaction_rating=None
        )
        
        self.tickets[ticket.id] = ticket
        self.ticket_queue.append(ticket.id)
        
        logger.info(f"Created ticket {ticket.id} with priority {priority.value}")
        return ticket
    
    def _detect_priority(self, subject: str, description: str) -> TicketPriority:
        """Auto-detect ticket priority based on content"""
        text = f"{subject} {description}".lower()
        
        urgent_keywords = ["urgent", "critical", "emergency", "down", "broken", "cannot access"]
        high_keywords = ["error", "bug", "not working", "failed", "issue"]
        
        if any(keyword in text for keyword in urgent_keywords):
            return TicketPriority.URGENT
        elif any(keyword in text for keyword in high_keywords):
            return TicketPriority.HIGH
        else:
            return TicketPriority.MEDIUM
    
    def _extract_tags(self, subject: str, description: str) -> List[str]:
        """Extract relevant tags from ticket content"""
        text = f"{subject} {description}".lower()
        tags = []
        
        # Common issue tags
        tag_patterns = {
            "transcription": ["transcription", "transcript", "audio", "video"],
            "billing": ["billing", "payment", "subscription", "charge", "invoice"],
            "api": ["api", "integration", "webhook", "endpoint"],
            "performance": ["slow", "performance", "speed", "loading"],
            "bug": ["bug", "error", "issue", "problem"]
        }
        
        for tag, keywords in tag_patterns.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def assign_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """Assign ticket to support agent"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        ticket.assigned_to = agent_id
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.updated_at = datetime.utcnow()
        
        self.agent_assignments[agent_id].append(ticket_id)
        
        # Add assignment note
        ticket.conversation.append({
            "type": "system",
            "message": f"Ticket assigned to agent {agent_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Assigned ticket {ticket_id} to agent {agent_id}")
        return True
    
    def add_reply(self, ticket_id: str, message: str, is_agent: bool,
                  attachments: Optional[List[Dict[str, str]]] = None) -> bool:
        """Add reply to ticket conversation"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        
        reply = {
            "type": "agent" if is_agent else "customer",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "attachments": attachments or []
        }
        
        ticket.conversation.append(reply)
        ticket.updated_at = datetime.utcnow()
        
        # Update status based on reply
        if is_agent and ticket.status == TicketStatus.WAITING_CUSTOMER:
            ticket.status = TicketStatus.IN_PROGRESS
        elif not is_agent and ticket.status == TicketStatus.IN_PROGRESS:
            ticket.status = TicketStatus.WAITING_CUSTOMER
        
        return True
    
    def resolve_ticket(self, ticket_id: str, resolution: str,
                      satisfaction_rating: Optional[int] = None) -> bool:
        """Mark ticket as resolved"""
        if ticket_id not in self.tickets:
            return False
        
        ticket = self.tickets[ticket_id]
        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = datetime.utcnow()
        ticket.updated_at = datetime.utcnow()
        
        if satisfaction_rating:
            ticket.satisfaction_rating = satisfaction_rating
        
        # Add resolution note
        ticket.conversation.append({
            "type": "system",
            "message": f"Ticket resolved: {resolution}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Resolved ticket {ticket_id}")
        return True
    
    def get_ticket_metrics(self) -> Dict[str, Any]:
        """Get support ticket metrics"""
        total_tickets = len(self.tickets)
        
        if total_tickets == 0:
            return {
                "total_tickets": 0,
                "open_tickets": 0,
                "avg_resolution_time": 0,
                "satisfaction_score": 0
            }
        
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        resolution_times = []
        satisfaction_ratings = []
        
        for ticket in self.tickets.values():
            status_counts[ticket.status.value] += 1
            priority_counts[ticket.priority.value] += 1
            
            if ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                resolution_times.append(resolution_time)
            
            if ticket.satisfaction_rating:
                satisfaction_ratings.append(ticket.satisfaction_rating)
        
        return {
            "total_tickets": total_tickets,
            "status_distribution": dict(status_counts),
            "priority_distribution": dict(priority_counts),
            "open_tickets": status_counts[TicketStatus.OPEN.value] + 
                           status_counts[TicketStatus.IN_PROGRESS.value],
            "avg_resolution_time_hours": sum(resolution_times) / len(resolution_times) if resolution_times else 0,
            "satisfaction_score": sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 0
        }

class HelpDocumentationSystem:
    """Manages help documentation and FAQ"""
    
    def __init__(self):
        self.articles: Dict[str, HelpArticle] = {}
        self.faq_items: List[Dict[str, str]] = []
        self._initialize_default_content()
    
    def _initialize_default_content(self):
        """Initialize with default help content"""
        # Add default FAQ items
        self.faq_items = [
            {
                "question": "How accurate is the transcription?",
                "answer": "Our transcription accuracy typically ranges from 95-98% for clear audio. Accuracy depends on audio quality, background noise, and speaker clarity.",
                "category": "transcription"
            },
            {
                "question": "What file formats are supported?",
                "answer": "We support MP3, WAV, MP4, M4A, FLAC, OGG, WebM, and many other audio/video formats up to 2GB in size.",
                "category": "technical"
            },
            {
                "question": "How long does transcription take?",
                "answer": "Transcription typically takes 1-2 minutes per 10 minutes of audio. Longer files may take proportionally more time.",
                "category": "transcription"
            },
            {
                "question": "Is my data secure?",
                "answer": "Yes, all data is encrypted in transit and at rest. We are SOC 2 Type II certified and GDPR compliant. Your files are automatically deleted after 30 days unless you specify otherwise.",
                "category": "security"
            },
            {
                "question": "Can I edit transcripts?",
                "answer": "Yes, you can edit transcripts directly in our editor. We also support collaborative editing and version history.",
                "category": "features"
            }
        ]
        
        # Add default articles
        self._create_default_articles()
    
    def _create_default_articles(self):
        """Create default help articles"""
        articles_data = [
            {
                "title": "Getting Started with Video NER",
                "content": """# Getting Started with Video NER

Welcome to Video NER! This guide will help you get started with transcribing your audio and video files.

## Quick Start

1. **Upload Your File**: Click the upload button and select your audio or video file
2. **Choose Settings**: Select language and any processing options
3. **Start Transcription**: Click 'Transcribe' and wait for processing
4. **Review Results**: View and edit your transcript with timestamps

## Supported Formats

- Audio: MP3, WAV, M4A, FLAC, OGG, AAC
- Video: MP4, MOV, AVI, MKV, WebM

## Tips for Best Results

- Use high-quality recordings with minimal background noise
- Ensure speakers are clearly audible
- For multiple speakers, use our speaker diarization feature
""",
                "category": ArticleCategory.GETTING_STARTED,
                "tags": ["beginner", "quickstart", "upload"]
            },
            {
                "title": "Advanced Transcription Features",
                "content": """# Advanced Transcription Features

## Speaker Diarization
Automatically identify and label different speakers in your recording.

## Custom Vocabulary
Add industry-specific terms, names, or acronyms for better accuracy.

## Real-time Transcription
Transcribe live audio streams in real-time for meetings or broadcasts.

## Batch Processing
Process multiple files simultaneously with our batch upload feature.
""",
                "category": ArticleCategory.FEATURES,
                "tags": ["advanced", "diarization", "batch", "realtime"]
            }
        ]
        
        for article_data in articles_data:
            self.create_article(
                title=article_data["title"],
                content=article_data["content"],
                category=article_data["category"],
                tags=article_data["tags"],
                author="System"
            )
    
    def create_article(self, title: str, content: str, category: ArticleCategory,
                      tags: List[str], author: str,
                      related_articles: Optional[List[str]] = None) -> HelpArticle:
        """Create a new help article"""
        # Generate slug from title
        slug = re.sub(r'[^a-z0-9-]', '-', title.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Extract search keywords
        keywords = self._extract_keywords(title, content)
        
        article = HelpArticle(
            id=str(uuid.uuid4()),
            title=title,
            slug=slug,
            content=content,
            category=category,
            tags=tags,
            views=0,
            helpful_count=0,
            not_helpful_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            author=author,
            related_articles=related_articles or [],
            search_keywords=keywords
        )
        
        self.articles[article.id] = article
        logger.info(f"Created help article: {title}")
        
        return article
    
    def _extract_keywords(self, title: str, content: str) -> List[str]:
        """Extract search keywords from article"""
        # Simple keyword extraction - in production, use NLP
        text = f"{title} {content}".lower()
        
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text)
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Get unique keywords
        return list(set(keywords))[:20]
    
    def search_articles(self, query: str, category: Optional[ArticleCategory] = None) -> List[HelpArticle]:
        """Search help articles"""
        query_lower = query.lower()
        results = []
        
        for article in self.articles.values():
            # Filter by category if specified
            if category and article.category != category:
                continue
            
            # Calculate relevance score
            score = 0
            
            # Title match (highest weight)
            if query_lower in article.title.lower():
                score += 10
            
            # Tag match
            for tag in article.tags:
                if query_lower in tag.lower():
                    score += 5
            
            # Keyword match
            for keyword in article.search_keywords:
                if query_lower in keyword:
                    score += 2
            
            # Content match (lowest weight)
            if query_lower in article.content.lower():
                score += 1
            
            if score > 0:
                results.append((score, article))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [article for _, article in results]
    
    def mark_article_helpful(self, article_id: str, is_helpful: bool) -> bool:
        """Mark article as helpful or not helpful"""
        if article_id not in self.articles:
            return False
        
        article = self.articles[article_id]
        
        if is_helpful:
            article.helpful_count += 1
        else:
            article.not_helpful_count += 1
        
        article.updated_at = datetime.utcnow()
        return True

class ChatSupportSystem:
    """AI-powered chat support system"""
    
    def __init__(self):
        self.chat_sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.ai_responses = self._load_ai_responses()
        self.escalation_triggers = ["human", "agent", "support", "help", "speak to"]
    
    def _load_ai_responses(self) -> Dict[str, List[str]]:
        """Load predefined AI responses"""
        return {
            "greeting": [
                "Hello! I'm the Video NER support assistant. How can I help you today?",
                "Hi there! I'm here to help with any questions about Video NER. What can I assist you with?"
            ],
            "transcription_help": [
                "I can help you with transcription! Are you having issues with uploading, processing, or the accuracy of your transcripts?",
                "For transcription support, I can help with file formats, processing times, accuracy, or editing. What specific issue are you experiencing?"
            ],
            "billing_help": [
                "I can help with billing questions. Are you asking about pricing, subscriptions, or a specific charge?",
                "For billing support, I can explain our plans, help with subscription changes, or address payment issues. What do you need help with?"
            ],
            "technical_help": [
                "I can assist with technical issues. Are you experiencing errors, performance problems, or integration challenges?",
                "For technical support, please describe the issue you're facing, including any error messages you're seeing."
            ],
            "escalation": [
                "I'll connect you with a human support agent who can better assist you. Please hold while I transfer your chat.",
                "I understand you'd like to speak with a support agent. Let me transfer you to our support team."
            ]
        }
    
    def start_chat_session(self, user_id: str) -> str:
        """Start a new chat session"""
        session_id = str(uuid.uuid4())
        self.chat_sessions[session_id] = [
            {
                "role": "assistant",
                "message": self.ai_responses["greeting"][0],
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        logger.info(f"Started chat session {session_id} for user {user_id}")
        return session_id
    
    def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process user message and generate response"""
        if session_id not in self.chat_sessions:
            return {"error": "Invalid session"}
        
        # Add user message to history
        self.chat_sessions[session_id].append({
            "role": "user",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check for escalation triggers
        if any(trigger in message.lower() for trigger in self.escalation_triggers):
            response = self._escalate_to_human(session_id)
        else:
            response = self._generate_ai_response(message)
        
        # Add AI response to history
        self.chat_sessions[session_id].append({
            "role": "assistant",
            "message": response["message"],
            "timestamp": datetime.utcnow().isoformat(),
            "suggested_articles": response.get("suggested_articles", [])
        })
        
        return response
    
    def _generate_ai_response(self, message: str) -> Dict[str, Any]:
        """Generate AI response based on message content"""
        message_lower = message.lower()
        
        # Categorize the query
        if any(word in message_lower for word in ["transcription", "transcript", "audio", "video"]):
            category = "transcription_help"
        elif any(word in message_lower for word in ["billing", "payment", "subscription", "price"]):
            category = "billing_help"
        elif any(word in message_lower for word in ["error", "bug", "issue", "problem", "not working"]):
            category = "technical_help"
        else:
            category = "greeting"
        
        # Get response
        response = {
            "message": self.ai_responses[category][0],
            "suggested_articles": self._get_suggested_articles(message),
            "category": category
        }
        
        return response
    
    def _get_suggested_articles(self, message: str) -> List[Dict[str, str]]:
        """Get suggested help articles based on message"""
        # In production, this would use the HelpDocumentationSystem search
        suggestions = []
        
        if "transcription" in message.lower():
            suggestions.append({
                "title": "Getting Started with Transcription",
                "url": "/help/getting-started-transcription"
            })
        
        if "billing" in message.lower():
            suggestions.append({
                "title": "Understanding Your Bill",
                "url": "/help/billing-explained"
            })
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _escalate_to_human(self, session_id: str) -> Dict[str, Any]:
        """Escalate chat to human agent"""
        return {
            "message": self.ai_responses["escalation"][0],
            "escalated": True,
            "agent_available": self._check_agent_availability()
        }
    
    def _check_agent_availability(self) -> bool:
        """Check if human agents are available"""
        # Simple business hours check - in production, check actual agent status
        current_hour = datetime.utcnow().hour
        return 13 <= current_hour <= 22  # 9 AM - 6 PM EST

class TutorialSystem:
    """Manages video tutorials and onboarding"""
    
    def __init__(self):
        self.tutorials: Dict[str, Tutorial] = {}
        self.learning_paths: Dict[str, List[str]] = {}
        self._initialize_tutorials()
    
    def _initialize_tutorials(self):
        """Initialize with default tutorials"""
        tutorials_data = [
            {
                "title": "Getting Started with Video NER",
                "description": "Learn the basics of uploading and transcribing your first file",
                "type": TutorialType.VIDEO,
                "duration_minutes": 5,
                "difficulty": "beginner",
                "content_url": "https://example.com/tutorials/getting-started.mp4",
                "learning_objectives": [
                    "Upload your first file",
                    "Understand transcription settings",
                    "Download your transcript"
                ]
            },
            {
                "title": "Advanced Transcription Features",
                "description": "Master speaker diarization, custom vocabulary, and batch processing",
                "type": TutorialType.VIDEO,
                "duration_minutes": 12,
                "difficulty": "intermediate",
                "content_url": "https://example.com/tutorials/advanced-features.mp4",
                "learning_objectives": [
                    "Configure speaker diarization",
                    "Add custom vocabulary",
                    "Use batch processing"
                ]
            },
            {
                "title": "API Integration Guide",
                "description": "Step-by-step guide to integrating our API into your application",
                "type": TutorialType.INTERACTIVE,
                "duration_minutes": 20,
                "difficulty": "advanced",
                "content_url": "https://example.com/tutorials/api-integration",
                "learning_objectives": [
                    "Authenticate with the API",
                    "Submit transcription jobs",
                    "Handle webhooks"
                ]
            }
        ]
        
        for tutorial_data in tutorials_data:
            self.create_tutorial(
                title=tutorial_data["title"],
                description=tutorial_data["description"],
                type=tutorial_data["type"],
                duration_minutes=tutorial_data["duration_minutes"],
                difficulty=tutorial_data["difficulty"],
                content_url=tutorial_data["content_url"],
                learning_objectives=tutorial_data["learning_objectives"]
            )
        
        # Create learning paths
        self.learning_paths = {
            "beginner": ["Getting Started with Video NER"],
            "developer": ["Getting Started with Video NER", "API Integration Guide"],
            "power_user": ["Getting Started with Video NER", "Advanced Transcription Features"]
        }
    
    def create_tutorial(self, title: str, description: str, type: TutorialType,
                       duration_minutes: int, difficulty: str, content_url: str,
                       learning_objectives: List[str],
                       tags: Optional[List[str]] = None,
                       prerequisites: Optional[List[str]] = None) -> Tutorial:
        """Create a new tutorial"""
        tutorial = Tutorial(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            type=type,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            content_url=content_url,
            thumbnail_url=f"{content_url}/thumbnail.jpg",
            tags=tags or [],
            prerequisites=prerequisites or [],
            learning_objectives=learning_objectives,
            views=0,
            completion_rate=0.0,
            rating=0.0,
            created_at=datetime.utcnow()
        )
        
        self.tutorials[tutorial.id] = tutorial
        logger.info(f"Created tutorial: {title}")
        
        return tutorial
    
    def get_learning_path(self, user_type: str) -> List[Tutorial]:
        """Get recommended learning path for user type"""
        if user_type not in self.learning_paths:
            user_type = "beginner"
        
        tutorial_titles = self.learning_paths[user_type]
        tutorials = []
        
        for title in tutorial_titles:
            for tutorial in self.tutorials.values():
                if tutorial.title == title:
                    tutorials.append(tutorial)
                    break
        
        return tutorials
    
    def track_progress(self, user_id: str, tutorial_id: str, 
                      progress_percent: float) -> bool:
        """Track user progress on tutorial"""
        if tutorial_id not in self.tutorials:
            return False
        
        # In production, store in database
        logger.info(f"User {user_id} completed {progress_percent}% of tutorial {tutorial_id}")
        
        # Update completion rate
        tutorial = self.tutorials[tutorial_id]
        if progress_percent >= 90:  # Consider 90% as completed
            # Update completion rate (simplified - in production, track per user)
            tutorial.completion_rate = min(100, tutorial.completion_rate + 1)
        
        return True

class CommunityForumSystem:
    """Manages community forum and discussions"""
    
    def __init__(self):
        self.posts: Dict[str, ForumPost] = {}
        self.categories = [
            "General Discussion",
            "Feature Requests",
            "Tips & Tricks",
            "API & Development",
            "Bug Reports",
            "Show & Tell"
        ]
        self.user_reputation: Dict[str, int] = defaultdict(int)
    
    def create_post(self, author_id: str, title: str, content: str,
                   category: str, tags: List[str]) -> ForumPost:
        """Create a new forum post"""
        post = ForumPost(
            id=str(uuid.uuid4()),
            author_id=author_id,
            title=title,
            content=content,
            category=category,
            tags=tags,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            views=0,
            upvotes=0,
            replies=[],
            is_solved=False,
            accepted_answer_id=None
        )
        
        self.posts[post.id] = post
        
        # Award reputation for creating post
        self.user_reputation[author_id] += 5
        
        logger.info(f"Created forum post: {title}")
        return post
    
    def add_reply(self, post_id: str, author_id: str, content: str) -> Optional[str]:
        """Add reply to forum post"""
        if post_id not in self.posts:
            return None
        
        post = self.posts[post_id]
        reply_id = str(uuid.uuid4())
        
        reply = {
            "id": reply_id,
            "author_id": author_id,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
            "upvotes": 0
        }
        
        post.replies.append(reply)
        post.updated_at = datetime.utcnow()
        
        # Award reputation for replying
        self.user_reputation[author_id] += 2
        
        return reply_id
    
    def upvote_post(self, post_id: str, user_id: str) -> bool:
        """Upvote a forum post"""
        if post_id not in self.posts:
            return False
        
        post = self.posts[post_id]
        post.upvotes += 1
        
        # Award reputation to post author
        self.user_reputation[post.author_id] += 10
        
        return True
    
    def mark_as_solved(self, post_id: str, answer_id: str) -> bool:
        """Mark post as solved with accepted answer"""
        if post_id not in self.posts:
            return False
        
        post = self.posts[post_id]
        post.is_solved = True
        post.accepted_answer_id = answer_id
        
        # Award reputation to answer author
        for reply in post.replies:
            if reply["id"] == answer_id:
                self.user_reputation[reply["author_id"]] += 25
                break
        
        return True
    
    def search_posts(self, query: str, category: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    solved_only: bool = False) -> List[ForumPost]:
        """Search forum posts"""
        results = []
        query_lower = query.lower()
        
        for post in self.posts.values():
            # Filter by solved status
            if solved_only and not post.is_solved:
                continue
            
            # Filter by category
            if category and post.category != category:
                continue
            
            # Filter by tags
            if tags and not any(tag in post.tags for tag in tags):
                continue
            
            # Search in title and content
            if (query_lower in post.title.lower() or 
                query_lower in post.content.lower()):
                results.append(post)
        
        # Sort by relevance (upvotes and recency)
        results.sort(key=lambda p: (p.upvotes, p.created_at), reverse=True)
        
        return results

class FeedbackSystem:
    """Manages feedback collection and feature requests"""
    
    def __init__(self):
        self.feedback_items: List[Dict[str, Any]] = []
        self.feature_requests: Dict[str, Dict[str, Any]] = {}
        self.feedback_categories = [
            "Bug Report",
            "Feature Request",
            "User Experience",
            "Performance",
            "Documentation",
            "Other"
        ]
    
    def submit_feedback(self, user_id: str, category: str,
                       subject: str, description: str,
                       rating: Optional[int] = None) -> str:
        """Submit user feedback"""
        feedback_id = str(uuid.uuid4())
        
        feedback = {
            "id": feedback_id,
            "user_id": user_id,
            "category": category,
            "subject": subject,
            "description": description,
            "rating": rating,
            "created_at": datetime.utcnow().isoformat(),
            "status": "new",
            "priority": self._calculate_priority(category, description)
        }
        
        self.feedback_items.append(feedback)
        
        # If it's a feature request, add to feature requests
        if category == "Feature Request":
            self.create_feature_request(user_id, subject, description)
        
        logger.info(f"Received feedback: {subject}")
        return feedback_id
    
    def _calculate_priority(self, category: str, description: str) -> str:
        """Calculate feedback priority"""
        # Bug reports get higher priority
        if category == "Bug Report":
            if any(word in description.lower() for word in ["crash", "error", "broken"]):
                return "high"
            return "medium"
        
        return "low"
    
    def create_feature_request(self, user_id: str, title: str,
                              description: str) -> str:
        """Create a feature request"""
        request_id = str(uuid.uuid4())
        
        self.feature_requests[request_id] = {
            "id": request_id,
            "title": title,
            "description": description,
            "requested_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "upvotes": 1,  # Creator automatically upvotes
            "status": "under_review",  # under_review, planned, in_progress, completed
            "comments": [],
            "tags": self._extract_feature_tags(title, description)
        }
        
        return request_id
    
    def _extract_feature_tags(self, title: str, description: str) -> List[str]:
        """Extract tags from feature request"""
        text = f"{title} {description}".lower()
        tags = []
        
        tag_keywords = {
            "api": ["api", "integration", "webhook"],
            "ui": ["interface", "design", "ui", "ux"],
            "performance": ["speed", "fast", "slow", "performance"],
            "mobile": ["mobile", "ios", "android", "app"],
            "export": ["export", "download", "format"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def upvote_feature_request(self, request_id: str, user_id: str) -> bool:
        """Upvote a feature request"""
        if request_id not in self.feature_requests:
            return False
        
        self.feature_requests[request_id]["upvotes"] += 1
        return True
    
    def get_trending_features(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending feature requests"""
        # Sort by upvotes
        sorted_requests = sorted(
            self.feature_requests.values(),
            key=lambda x: x["upvotes"],
            reverse=True
        )
        
        return sorted_requests[:limit]
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get feedback summary statistics"""
        total_feedback = len(self.feedback_items)
        
        if total_feedback == 0:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "category_distribution": {},
                "trending_features": []
            }
        
        # Category distribution
        category_counts = defaultdict(int)
        ratings = []
        
        for feedback in self.feedback_items:
            category_counts[feedback["category"]] += 1
            if feedback["rating"]:
                ratings.append(feedback["rating"])
        
        return {
            "total_feedback": total_feedback,
            "average_rating": sum(ratings) / len(ratings) if ratings else 0,
            "category_distribution": dict(category_counts),
            "trending_features": self.get_trending_features(5),
            "total_feature_requests": len(self.feature_requests)
        }

class CustomerSupportSystem:
    """Main customer support system integrating all components"""
    
    def __init__(self):
        self.ticket_manager = SupportTicketManager()
        self.help_docs = HelpDocumentationSystem()
        self.chat_support = ChatSupportSystem()
        self.tutorials = TutorialSystem()
        self.forum = CommunityForumSystem()
        self.feedback = FeedbackSystem()
        
        # Support metrics
        self.response_times: List[float] = []
        self.resolution_times: List[float] = []
    
    def get_support_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive support dashboard data"""
        return {
            "tickets": self.ticket_manager.get_ticket_metrics(),
            "help_articles": {
                "total": len(self.help_docs.articles),
                "categories": len(ArticleCategory),
                "faq_items": len(self.help_docs.faq_items)
            },
            "tutorials": {
                "total": len(self.tutorials.tutorials),
                "learning_paths": len(self.tutorials.learning_paths)
            },
            "forum": {
                "total_posts": len(self.forum.posts),
                "active_users": len(self.forum.user_reputation),
                "categories": len(self.forum.categories)
            },
            "feedback": self.feedback.get_feedback_summary(),
            "chat_sessions": len(self.chat_support.chat_sessions),
            "average_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "average_resolution_time": sum(self.resolution_times) / len(self.resolution_times) if self.resolution_times else 0
        }
    
    def search_all_resources(self, query: str) -> Dict[str, List[Any]]:
        """Search across all support resources"""
        return {
            "help_articles": self.help_docs.search_articles(query),
            "faq": [faq for faq in self.help_docs.faq_items 
                   if query.lower() in faq["question"].lower() or 
                   query.lower() in faq["answer"].lower()],
            "forum_posts": self.forum.search_posts(query),
            "tutorials": [t for t in self.tutorials.tutorials.values()
                         if query.lower() in t.title.lower() or
                         query.lower() in t.description.lower()]
        }
    
    def get_user_support_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's support interaction history"""
        # Get user's tickets
        user_tickets = [t for t in self.ticket_manager.tickets.values()
                       if t.user_id == user_id]
        
        # Get user's forum activity
        user_posts = [p for p in self.forum.posts.values()
                     if p.author_id == user_id]
        
        # Get user's feedback
        user_feedback = [f for f in self.feedback.feedback_items
                        if f["user_id"] == user_id]
        
        return {
            "tickets": len(user_tickets),
            "forum_posts": len(user_posts),
            "forum_reputation": self.forum.user_reputation.get(user_id, 0),
            "feedback_submitted": len(user_feedback),
            "last_interaction": self._get_last_interaction(user_id)
        }
    
    def _get_last_interaction(self, user_id: str) -> Optional[str]:
        """Get user's last support interaction"""
        interactions = []
        
        # Check tickets
        for ticket in self.ticket_manager.tickets.values():
            if ticket.user_id == user_id:
                interactions.append(ticket.updated_at)
        
        # Check forum posts
        for post in self.forum.posts.values():
            if post.author_id == user_id:
                interactions.append(post.updated_at)
        
        if interactions:
            return max(interactions).isoformat()
        
        return None

if __name__ == "__main__":
    # Example usage
    support_system = CustomerSupportSystem()
    
    # Create a support ticket
    ticket = support_system.ticket_manager.create_ticket(
        user_id="user123",
        subject="Transcription not working",
        description="I uploaded an MP3 file but the transcription is stuck at 0%",
        category="technical"
    )
    print(f"Created ticket: {ticket.id}")
    
    # Start chat session
    chat_session = support_system.chat_support.start_chat_session("user123")
    response = support_system.chat_support.process_message(
        chat_session,
        "My transcription is stuck"
    )
    print(f"Chat response: {response['message']}")
    
    # Search help articles
    articles = support_system.help_docs.search_articles("transcription")
    print(f"Found {len(articles)} help articles")
    
    # Get support dashboard
    dashboard = support_system.get_support_dashboard()
    print(f"Support Dashboard: {json.dumps(dashboard, indent=2, default=str)}")