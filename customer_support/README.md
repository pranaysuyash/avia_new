# Customer Support and Help System

A comprehensive customer support solution providing ticket management, knowledge base, live chat, and feedback collection capabilities for exceptional customer service.

## Features

### 1. **Support Ticket Management**
- Multi-channel ticket creation (email, chat, web form, API)
- Intelligent ticket routing and prioritization
- SLA management and tracking
- Agent assignment and workload balancing
- Ticket escalation workflows
- Merge and link related tickets
- Customer sentiment analysis
- Comprehensive ticket analytics

### 2. **Knowledge Base & Self-Service**
- Article creation and management
- Multiple content types (guides, FAQs, videos, troubleshooting)
- AI-powered search with relevance scoring
- Related content suggestions
- Article analytics and feedback
- Version control and change tracking
- Multi-language support ready

### 3. **Live Chat Support**
- Real-time messaging with WebSocket support
- Intelligent agent routing
- Queue management with priority handling
- Canned responses with placeholders
- File and image sharing
- Chat transfer between agents
- Typing indicators and read receipts
- Post-chat surveys

### 4. **Customer Feedback System**
- Survey creation and distribution
- Net Promoter Score (NPS) tracking
- Feature request management with voting
- Bug report collection
- Customer testimonials
- Feedback categorization and tagging
- Response tracking and analytics

## Installation

```bash
# The customer support package is included with the main application
pip install -r requirements.txt
```

## Quick Start

### Setting Up Support Tickets

```python
from customer_support import TicketManagementSystem, TicketCategory, Agent

# Initialize ticket system
ticket_system = TicketManagementSystem()

# Create support agent
agent = Agent(
    agent_id="agent_001",
    name="Sarah Johnson",
    email="sarah@support.com",
    skills=["technical", "billing"],
    specializations=[TicketCategory.TECHNICAL, TicketCategory.BUG_REPORT]
)
ticket_system.agents[agent.agent_id] = agent

# Create support ticket
ticket = await ticket_system.create_ticket(
    customer_id="cust_123",
    customer_email="customer@example.com",
    customer_name="John Doe",
    subject="Unable to upload large files",
    description="Getting timeout errors when uploading files over 100MB",
    category=TicketCategory.BUG_REPORT,
    attachments=[{"filename": "error_log.txt", "size": 1024}]
)

print(f"Ticket created: {ticket.ticket_number}")
print(f"Priority: {ticket.priority}")
print(f"SLA deadline: {ticket.sla_deadline}")

# Add agent response
await ticket_system.add_message(
    ticket.ticket_id,
    agent.agent_id,
    "agent",
    "I understand you're having issues with large file uploads. Let me investigate this for you."
)

# Search tickets
bug_tickets = ticket_system.search_tickets(
    category=[TicketCategory.BUG_REPORT],
    status=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS]
)
```

### Building Knowledge Base

```python
from customer_support import KnowledgeBase, ArticleType

# Initialize knowledge base
kb = KnowledgeBase()

# Create help article
article = kb.create_article(
    title="How to Upload Large Files",
    content="""
    # Uploading Large Files
    
    Our platform supports files up to 2GB. Follow these steps:
    
    1. Ensure stable internet connection
    2. Use supported formats (MP4, MOV, AVI)
    3. Consider compressing files over 1GB
    
    ## Troubleshooting
    - Clear browser cache
    - Try different browser
    - Check firewall settings
    """,
    article_type=ArticleType.GUIDE,
    category="File Management",
    author_id="doc_team",
    author_name="Documentation Team",
    tags=["upload", "files", "troubleshooting"]
)

# Search knowledge base
results = kb.search("upload large files", limit=5)

for result in results:
    print(f"{result.title} - Score: {result.relevance_score:.2f}")

# Track article performance
kb.record_article_view(article.article_id, "session_123", time_on_page=45.5)
kb.record_article_feedback(article.article_id, helpful=True)
```

### Implementing Live Chat

```python
from customer_support import LiveChatSystem, CustomerInfo, ChatAgent, AgentStatus

# Initialize chat system
chat_system = LiveChatSystem()

# Create chat agent
chat_agent = ChatAgent(
    agent_id="agent_jane",
    name="Jane Smith",
    email="jane@support.com",
    status=AgentStatus.AVAILABLE,
    departments=["sales", "support"],
    max_concurrent_chats=5
)
chat_system.agents[chat_agent.agent_id] = chat_agent

# Start chat session
customer = CustomerInfo(
    customer_id="cust_456",
    name="Alice Brown",
    email="alice@example.com",
    page_url="https://example.com/pricing",
    account_type="premium"
)

chat = await chat_system.start_chat(
    customer,
    "Hi, I need help choosing the right plan.",
    department="sales"
)

# Send messages
await chat_system.send_message(
    chat.chat_id,
    chat_agent.agent_id,
    "agent",
    "Hello Alice! I'd be happy to help you choose the perfect plan. What are your main requirements?"
)

# Use canned response
await chat_system.send_message(
    chat.chat_id,
    chat_agent.agent_id,
    "agent",
    "/pricing_info"  # Triggers canned response
)

# End chat and collect rating
await chat_system.end_chat(chat.chat_id, "customer")
chat_system.submit_chat_rating(chat.chat_id, 5, "Very helpful agent!")
```

### Collecting Customer Feedback

```python
from customer_support import FeedbackSystem, FeedbackType, SurveyTemplate, QuestionType

# Initialize feedback system
feedback_system = FeedbackSystem()

# Submit feature request
feature = feedback_system.submit_feedback(
    FeedbackType.FEATURE_REQUEST,
    "Add support for real-time collaboration on transcripts",
    title="Real-time collaboration",
    user_id="user_789",
    tags=["collaboration", "real-time", "enhancement"]
)

# Vote on feature
feedback_system.vote_on_feedback(feature.feedback_id, "user_890", upvote=True)

# Create custom survey
from customer_support import SurveyQuestion

survey = feedback_system.create_survey(
    name="Product Satisfaction Survey",
    description="Help us improve our service",
    survey_type=SurveyType.SATISFACTION,
    questions=[
        SurveyQuestion(
            question_id="overall",
            text="Overall, how satisfied are you with our service?",
            question_type=QuestionType.RATING,
            min_value=1,
            max_value=10
        ),
        SurveyQuestion(
            question_id="features",
            text="Which features do you find most valuable?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["Accuracy", "Speed", "API", "Integrations", "Support"],
            required=False
        )
    ]
)

# Submit survey response
response = feedback_system.submit_survey_response(
    survey.template_id,
    {
        "overall": 9,
        "features": ["Accuracy", "API"]
    },
    respondent_id="user_789"
)

# Get analytics
analytics = feedback_system.get_feedback_analytics()
print(f"NPS Score: {analytics.nps_score:.1f}")
print(f"Feature requests: {analytics.feature_requests}")
```

## Configuration

### Environment Variables

```bash
# Support ticket settings
TICKET_AUTO_ASSIGN=true
TICKET_SLA_WARNING_HOURS=2
MAX_TICKETS_PER_AGENT=10

# Knowledge base
KB_SEARCH_RESULTS_LIMIT=20
KB_CACHE_DURATION_MINUTES=60
KB_AUTO_SUGGEST=true

# Live chat
CHAT_MAX_QUEUE_SIZE=100
CHAT_IDLE_TIMEOUT_MINUTES=30
CHAT_TRANSCRIPT_RETENTION_DAYS=90

# Feedback
SURVEY_REMINDER_DAYS=3
NPS_SURVEY_FREQUENCY_DAYS=90
FEEDBACK_MODERATION=true
```

### SLA Configuration

```python
from customer_support import SLAPolicy, TicketPriority

# Configure SLA policies
critical_sla = SLAPolicy(
    policy_id="critical_sla",
    name="Critical Issues",
    description="For system outages and data loss",
    priority=TicketPriority.CRITICAL,
    first_response_time=15,  # minutes
    resolution_time=240,     # 4 hours
    business_hours_only=False,
    escalation_rules=[
        {
            "after_minutes": 30,
            "notify": ["managers", "on_call"],
            "escalate_to": "senior_support"
        }
    ]
)
```

## Analytics and Reporting

### Ticket Metrics

```python
# Get support metrics
metrics = ticket_system.get_ticket_metrics(time_period_days=30)

print(f"Total tickets: {metrics['total_tickets']}")
print(f"Avg first response: {metrics['avg_first_response_time']:.1f} min")
print(f"Avg resolution time: {metrics['avg_resolution_time']:.1f} hours")
print(f"SLA compliance: {metrics['sla_compliance']['percentage']:.1f}%")

# Tickets by category
for category, count in metrics['tickets_by_category'].items():
    print(f"{category}: {count} tickets")
```

### Knowledge Base Analytics

```python
# Get KB metrics
kb_metrics = kb.generate_help_metrics()

print(f"Total articles: {kb_metrics['total_articles']}")
print(f"Published articles: {kb_metrics['published_articles']}")
print(f"Search success rate: {kb_metrics['search_success_rate']:.1f}%")
print(f"Avg helpfulness: {kb_metrics['avg_helpfulness_score']:.1f}%")

# Popular search terms
print("\nPopular searches:")
for term in kb_metrics['popular_search_terms']:
    print(f"- {term}")
```

### Agent Performance

```python
# Get agent metrics
agent_metrics = chat_system.get_agent_metrics("agent_jane")

print(f"Agent: {agent_metrics['name']}")
print(f"Total chats: {agent_metrics['total_chats_handled']}")
print(f"Avg response time: {agent_metrics['avg_response_time']:.1f} sec")
print(f"Satisfaction rating: {agent_metrics['satisfaction_rating']:.1f}/5")

# Rating breakdown
for stars, count in agent_metrics['ratings_breakdown'].items():
    print(f"{stars}: {count} ratings")
```

## Integration Examples

### Email Integration

```python
# Process email to create ticket
async def process_support_email(email_data):
    ticket = await ticket_system.create_ticket(
        customer_email=email_data['from'],
        customer_name=email_data['from_name'],
        subject=email_data['subject'],
        description=email_data['body'],
        category=TicketCategory.TECHNICAL,  # Auto-categorize
        channel=TicketChannel.EMAIL,
        attachments=email_data.get('attachments', [])
    )
    
    # Auto-reply
    send_email(
        to=email_data['from'],
        subject=f"Re: {email_data['subject']} [Ticket #{ticket.ticket_number}]",
        body=f"Thank you for contacting support. Your ticket {ticket.ticket_number} has been created."
    )
```

### Slack Integration

```python
# Handle Slack commands
async def handle_slack_command(command, user_id, channel):
    if command.startswith('/ticket'):
        # Create ticket from Slack
        _, description = command.split(' ', 1)
        ticket = await ticket_system.create_ticket(
            customer_id=user_id,
            customer_email=f"{user_id}@slack",
            customer_name=get_slack_username(user_id),
            subject="Slack Support Request",
            description=description,
            category=TicketCategory.TECHNICAL,
            channel=TicketChannel.CHAT
        )
        
        return f"Ticket {ticket.ticket_number} created!"
```

### API Webhook

```python
# Webhook for external events
@app.post("/webhooks/support")
async def support_webhook(event: dict):
    if event['type'] == 'user.subscription.cancelled':
        # Create high-priority ticket
        ticket = await ticket_system.create_ticket(
            customer_id=event['user_id'],
            customer_email=event['user_email'],
            customer_name=event['user_name'],
            subject="Subscription Cancellation - Retention Opportunity",
            description=f"User cancelled subscription. Reason: {event.get('reason', 'Not specified')}",
            category=TicketCategory.ACCOUNT,
            priority=TicketPriority.HIGH
        )
```

## Best Practices

### 1. **Ticket Management**
- Set up automatic routing rules based on keywords
- Use tags for better organization
- Regularly review and update SLA policies
- Train agents on using canned responses
- Monitor ticket trends for proactive support

### 2. **Knowledge Base**
- Keep articles up-to-date with product changes
- Use clear, simple language
- Include visuals and examples
- Monitor search queries for content gaps
- Encourage feedback on articles

### 3. **Live Chat**
- Set realistic agent capacity limits
- Use department-based routing
- Prepare canned responses for common questions
- Train agents on empathy and communication
- Monitor chat transcripts for quality

### 4. **Feedback Collection**
- Time surveys appropriately (post-interaction)
- Keep surveys short and focused
- Act on feedback and communicate changes
- Track NPS trends over time
- Respond to negative feedback quickly

## Security Considerations

- All customer data is encrypted at rest
- PII is automatically masked in logs
- Agent access is role-based
- Chat transcripts are retained per policy
- Feedback can be anonymized
- API access requires authentication
- File uploads are scanned for security

## Troubleshooting

### Common Issues

1. **Tickets not auto-assigning**
   - Check agent availability status
   - Verify agent skills match ticket category
   - Ensure agents haven't exceeded capacity

2. **Search returning poor results**
   - Rebuild search index
   - Check for typos in content
   - Add more keywords to articles

3. **Chat queue growing**
   - Add more agents
   - Adjust routing rules
   - Enable self-service deflection

4. **Low survey response rates**
   - Reduce survey frequency
   - Shorten surveys
   - Offer incentives

## Future Enhancements

- [ ] AI-powered ticket categorization
- [ ] Automated response suggestions
- [ ] Video chat support
- [ ] Social media integration
- [ ] Predictive customer satisfaction
- [ ] Multi-language chat translation
- [ ] Voice support integration
- [ ] Advanced analytics dashboard

## Support

For technical support:
- Documentation: https://docs.example.com/support
- API Reference: https://api.example.com/support
- Contact: support-team@example.com