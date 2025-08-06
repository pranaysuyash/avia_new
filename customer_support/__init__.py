"""
Customer Support and Help System Package

Comprehensive customer support solution including:
- Support ticket management
- Knowledge base and self-service
- Live chat support
- Customer feedback and surveys
"""

from .support_ticket import (
    TicketManagementSystem,
    SupportTicket,
    TicketMessage,
    TicketPriority,
    TicketStatus,
    TicketCategory,
    TicketChannel,
    CustomerSentiment,
    SLAPolicy,
    Agent
)

from .knowledge_base import (
    KnowledgeBase,
    KnowledgeArticle,
    FAQ,
    VideoTutorial,
    SearchResult,
    ArticleType,
    ArticleStatus,
    ContentDifficulty
)

from .live_chat import (
    LiveChatSystem,
    ChatSession,
    ChatMessage,
    ChatAgent,
    CustomerInfo,
    CannedResponse,
    ChatStatus,
    MessageType,
    AgentStatus
)

from .feedback_system import (
    FeedbackSystem,
    FeedbackItem,
    SurveyTemplate,
    SurveyResponse,
    NPSResponse,
    FeedbackType,
    SurveyType,
    QuestionType,
    ResponseStatus,
    FeedbackAnalytics
)

__version__ = "1.0.0"

__all__ = [
    # Ticket Management
    "TicketManagementSystem",
    "SupportTicket",
    "TicketMessage",
    "TicketPriority",
    "TicketStatus",
    "TicketCategory",
    "TicketChannel",
    "CustomerSentiment",
    "SLAPolicy",
    "Agent",
    
    # Knowledge Base
    "KnowledgeBase",
    "KnowledgeArticle",
    "FAQ",
    "VideoTutorial",
    "SearchResult",
    "ArticleType",
    "ArticleStatus",
    "ContentDifficulty",
    
    # Live Chat
    "LiveChatSystem",
    "ChatSession",
    "ChatMessage",
    "ChatAgent",
    "CustomerInfo",
    "CannedResponse",
    "ChatStatus",
    "MessageType",
    "AgentStatus",
    
    # Feedback System
    "FeedbackSystem",
    "FeedbackItem",
    "SurveyTemplate",
    "SurveyResponse",
    "NPSResponse",
    "FeedbackType",
    "SurveyType",
    "QuestionType",
    "ResponseStatus",
    "FeedbackAnalytics"
]