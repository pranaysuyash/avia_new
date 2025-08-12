"""
Customer Support Service

Business logic for customer support operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid

from database.models_extended import (
    SupportTicket, TicketMessage, KnowledgeArticle
)
from services.notification_service import NotificationService
from services.email_service import EmailService
from services.ai_service import AIService
from customer_support import (
    TicketManagementSystem, KnowledgeBase, LiveChatSystem,
    FeedbackSystem, TicketPriority, TicketStatus
)

class SupportService:
    """Service for managing customer support"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()
        self.ai_service = AIService()
        
        # Initialize support systems
        self.ticket_system = TicketManagementSystem()
        self.knowledge_base = KnowledgeBase()
        self.chat_system = LiveChatSystem()
        self.feedback_system = FeedbackSystem()
    
    async def create_ticket(
        self,
        customer_id: str,
        customer_email: str,
        customer_name: str,
        subject: str,
        description: str,
        category: str,
        priority: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> SupportTicket:
        """Create support ticket with auto-routing"""
        # Generate ticket number
        ticket_count = self.db.query(SupportTicket).count()
        ticket_number = f"SUP-{ticket_count + 1:06d}"
        
        # Auto-detect priority if not provided
        if not priority:
            priority = await self._detect_priority(subject, description)
        
        # Analyze sentiment
        sentiment = await self.ai_service.analyze_sentiment(description)
        
        # Create ticket
        ticket = SupportTicket(
            id=str(uuid.uuid4()),
            ticket_number=ticket_number,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_name=customer_name,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            sentiment=sentiment,
            created_at=datetime.utcnow()
        )
        
        # Set SLA deadline
        sla_hours = {"low": 48, "medium": 24, "high": 4, "critical": 1}
        ticket.sla_deadline = datetime.utcnow() + timedelta(
            hours=sla_hours.get(priority, 24)
        )
        
        # Auto-assign to agent
        assigned_agent = await self._find_best_agent(category, priority)
        if assigned_agent:
            ticket.assigned_to = assigned_agent["id"]
            ticket.assigned_team = assigned_agent["team"]
        
        self.db.add(ticket)
        
        # Create initial message
        initial_message = TicketMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            sender_id=customer_id,
            sender_type="customer",
            sender_name=customer_name,
            content=description,
            attachments=attachments or [],
            created_at=datetime.utcnow()
        )
        self.db.add(initial_message)
        
        self.db.commit()
        
        # Send notifications
        await self._send_ticket_notifications(ticket)
        
        # Check for similar issues
        similar_tickets = await self._find_similar_tickets(description)
        if similar_tickets:
            # Suggest solutions from resolved tickets
            await self._suggest_solutions(ticket.id, similar_tickets)
        
        return ticket
    
    async def add_ticket_reply(
        self,
        ticket_id: str,
        sender_id: str,
        sender_type: str,
        content: str,
        is_internal_note: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> TicketMessage:
        """Add reply to ticket"""
        ticket = self.db.query(SupportTicket).filter(
            SupportTicket.id == ticket_id
        ).first()
        
        if not ticket:
            raise ValueError("Ticket not found")
        
        # Create message
        message = TicketMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            sender_name=self._get_sender_name(sender_id, sender_type),
            content=content,
            is_internal_note=is_internal_note,
            attachments=attachments or [],
            created_at=datetime.utcnow()
        )
        
        self.db.add(message)
        
        # Update ticket
        ticket.updated_at = datetime.utcnow()
        ticket.response_count += 1
        
        # Track first response time
        if sender_type == "agent" and not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
        
        # Update status based on sender
        if sender_type == "customer" and ticket.status == "waiting_customer":
            ticket.status = "open"
        elif sender_type == "agent" and not is_internal_note:
            ticket.status = "waiting_customer"
        
        self.db.commit()
        
        # Send notifications
        if not is_internal_note:
            await self._send_reply_notifications(ticket, message, sender_type)
        
        return message
    
    async def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search knowledge base articles"""
        # Use AI for semantic search
        search_results = self.knowledge_base.search(
            query,
            filters={"category": category} if category else None,
            limit=limit
        )
        
        # Enhance with AI-powered relevance
        enhanced_results = []
        for result in search_results:
            relevance = await self.ai_service.calculate_relevance(
                query,
                result.title + " " + result.excerpt
            )
            
            enhanced_results.append({
                "article_id": result.article_id,
                "title": result.title,
                "excerpt": result.excerpt,
                "category": self._get_article_category(result.article_id),
                "relevance_score": relevance,
                "url": result.url,
                "helpful_count": self._get_article_stats(result.article_id)["helpful"]
            })
        
        # Sort by relevance
        enhanced_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return enhanced_results
    
    async def start_live_chat(
        self,
        customer_id: str,
        customer_info: Dict[str, Any],
        initial_message: str,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start live chat session"""
        from customer_support import CustomerInfo
        
        # Create customer info
        customer = CustomerInfo(
            customer_id=customer_id,
            name=customer_info["name"],
            email=customer_info.get("email"),
            page_url=customer_info.get("page_url"),
            account_type=customer_info.get("account_type", "free")
        )
        
        # Start chat
        chat_session = await self.chat_system.start_chat(
            customer,
            initial_message,
            department
        )
        
        # Get chat status
        status = {
            "chat_id": chat_session.chat_id,
            "status": chat_session.status.value,
            "queue_position": chat_session.queue_position,
            "estimated_wait": self._estimate_wait_time(department),
            "agent": None
        }
        
        if chat_session.agent_id:
            agent = self._get_agent_info(chat_session.agent_id)
            status["agent"] = {
                "name": agent["name"],
                "avatar": agent.get("avatar_url")
            }
        
        return status
    
    async def submit_feedback(
        self,
        user_id: str,
        feedback_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit customer feedback"""
        from customer_support import FeedbackType
        
        # Map feedback type
        type_map = {
            "feature": FeedbackType.FEATURE_REQUEST,
            "bug": FeedbackType.BUG_REPORT,
            "complaint": FeedbackType.COMPLAINT,
            "testimonial": FeedbackType.TESTIMONIAL
        }
        
        feedback_enum = type_map.get(feedback_type, FeedbackType.SUGGESTION)
        
        # Submit feedback
        feedback = self.feedback_system.submit_feedback(
            feedback_type=feedback_enum,
            description=content,
            title=metadata.get("title") if metadata else None,
            user_id=user_id,
            user_email=metadata.get("email") if metadata else None,
            category=metadata.get("category") if metadata else None,
            tags=metadata.get("tags", []) if metadata else []
        )
        
        # Handle special cases
        if feedback_enum == FeedbackType.BUG_REPORT:
            # Create high-priority ticket
            ticket = await self.create_ticket(
                customer_id=user_id,
                customer_email=metadata.get("email", ""),
                customer_name=metadata.get("name", "User"),
                subject=f"Bug Report: {metadata.get('title', 'Reported Issue')}",
                description=content,
                category="bug",
                priority="high"
            )
            
            return {
                "feedback_id": feedback.feedback_id,
                "ticket_number": ticket.ticket_number,
                "message": "Bug report submitted and ticket created"
            }
        
        return {
            "feedback_id": feedback.feedback_id,
            "message": "Thank you for your feedback!"
        }
    
    def get_support_metrics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get support performance metrics"""
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Query tickets in period
        tickets = self.db.query(SupportTicket).filter(
            SupportTicket.created_at.between(date_from, date_to)
        ).all()
        
        # Calculate metrics
        total_tickets = len(tickets)
        resolved_tickets = len([t for t in tickets if t.status == "resolved"])
        
        # Response times
        response_times = []
        for ticket in tickets:
            if ticket.first_response_at:
                response_time = (
                    ticket.first_response_at - ticket.created_at
                ).total_seconds() / 60
                response_times.append(response_time)
        
        avg_response_time = (
            sum(response_times) / len(response_times) 
            if response_times else 0
        )
        
        # Resolution times
        resolution_times = []
        for ticket in tickets:
            if ticket.resolved_at:
                resolution_time = (
                    ticket.resolved_at - ticket.created_at
                ).total_seconds() / 3600
                resolution_times.append(resolution_time)
        
        avg_resolution_time = (
            sum(resolution_times) / len(resolution_times)
            if resolution_times else 0
        )
        
        # SLA compliance
        sla_met = len([
            t for t in tickets
            if t.resolved_at and t.sla_deadline 
            and t.resolved_at <= t.sla_deadline
        ])
        sla_total = len([t for t in tickets if t.sla_deadline])
        sla_compliance = (sla_met / sla_total * 100) if sla_total else 100
        
        # Satisfaction
        rated_tickets = [t for t in tickets if t.satisfaction_rating]
        avg_satisfaction = (
            sum(t.satisfaction_rating for t in rated_tickets) / len(rated_tickets)
            if rated_tickets else 0
        )
        
        # Categories
        tickets_by_category = {}
        for ticket in tickets:
            category = ticket.category or "uncategorized"
            tickets_by_category[category] = tickets_by_category.get(category, 0) + 1
        
        # Get chat metrics
        chat_metrics = self.chat_system.get_queue_status()
        
        # Get knowledge base metrics
        kb_metrics = self.knowledge_base.generate_help_metrics()
        
        return {
            "tickets": {
                "total": total_tickets,
                "resolved": resolved_tickets,
                "resolution_rate": (resolved_tickets / total_tickets * 100) if total_tickets else 0,
                "avg_response_time_min": avg_response_time,
                "avg_resolution_time_hours": avg_resolution_time,
                "sla_compliance": sla_compliance,
                "satisfaction_rating": avg_satisfaction,
                "by_category": tickets_by_category
            },
            "chat": {
                "active_chats": sum(
                    q["queue_length"] for q in chat_metrics.values()
                ),
                "avg_wait_time": self._calculate_avg_wait_time(chat_metrics)
            },
            "knowledge_base": {
                "total_articles": kb_metrics["total_articles"],
                "search_success_rate": kb_metrics["search_success_rate"],
                "avg_helpfulness": kb_metrics["avg_helpfulness_score"]
            }
        }
    
    async def _detect_priority(self, subject: str, description: str) -> str:
        """Auto-detect ticket priority using AI"""
        # Combine text
        text = f"{subject} {description}".lower()
        
        # Critical indicators
        critical_keywords = [
            "down", "outage", "critical", "urgent", "emergency",
            "data loss", "security breach", "cannot access", "broken"
        ]
        
        # High priority indicators
        high_keywords = [
            "error", "bug", "issue", "problem", "fail",
            "not working", "incorrect", "wrong"
        ]
        
        # Check keywords
        if any(keyword in text for keyword in critical_keywords):
            return "critical"
        
        if any(keyword in text for keyword in high_keywords):
            return "high"
        
        # Use AI for better classification
        priority_score = await self.ai_service.classify_priority(text)
        
        if priority_score > 0.8:
            return "critical"
        elif priority_score > 0.6:
            return "high"
        elif priority_score > 0.4:
            return "medium"
        else:
            return "low"
    
    async def _find_best_agent(
        self, 
        category: str, 
        priority: str
    ) -> Optional[Dict[str, Any]]:
        """Find best available agent for ticket"""
        # Get available agents
        available_agents = self._get_available_agents()
        
        if not available_agents:
            return None
        
        # Score agents based on:
        # - Specialization match
        # - Current workload
        # - Performance metrics
        
        best_agent = None
        best_score = 0
        
        for agent in available_agents:
            score = 0
            
            # Category match
            if category in agent.get("specializations", []):
                score += 30
            
            # Workload (inverse)
            workload = agent.get("current_tickets", 0)
            max_tickets = agent.get("max_tickets", 10)
            score += (1 - workload / max_tickets) * 20
            
            # Performance
            score += agent.get("satisfaction_rating", 0) * 10
            
            # Priority handling
            if priority in ["critical", "high"]:
                if agent.get("handles_priority", False):
                    score += 20
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    async def _find_similar_tickets(
        self, 
        description: str, 
        limit: int = 5
    ) -> List[SupportTicket]:
        """Find similar resolved tickets"""
        # Use AI for semantic similarity
        resolved_tickets = self.db.query(SupportTicket).filter(
            SupportTicket.status == "resolved"
        ).order_by(SupportTicket.resolved_at.desc()).limit(100).all()
        
        similar_tickets = []
        
        for ticket in resolved_tickets:
            similarity = await self.ai_service.calculate_similarity(
                description,
                ticket.description
            )
            
            if similarity > 0.7:  # 70% similarity threshold
                similar_tickets.append((ticket, similarity))
        
        # Sort by similarity
        similar_tickets.sort(key=lambda x: x[1], reverse=True)
        
        return [ticket for ticket, _ in similar_tickets[:limit]]
    
    async def _suggest_solutions(
        self, 
        ticket_id: str, 
        similar_tickets: List[SupportTicket]
    ):
        """Suggest solutions from similar resolved tickets"""
        suggestions = []
        
        for similar_ticket in similar_tickets:
            # Get resolution message
            resolution_message = self.db.query(TicketMessage).filter(
                TicketMessage.ticket_id == similar_ticket.id,
                TicketMessage.sender_type == "agent"
            ).order_by(TicketMessage.created_at.desc()).first()
            
            if resolution_message:
                suggestions.append({
                    "ticket_number": similar_ticket.ticket_number,
                    "solution": resolution_message.content,
                    "resolved_at": similar_ticket.resolved_at
                })
        
        if suggestions:
            # Add automatic suggestion message
            suggestion_content = "Based on similar issues, here are some potential solutions:\n\n"
            
            for i, suggestion in enumerate(suggestions[:3], 1):
                suggestion_content += f"{i}. From ticket {suggestion['ticket_number']}:\n"
                suggestion_content += f"   {suggestion['solution'][:200]}...\n\n"
            
            await self.add_ticket_reply(
                ticket_id=ticket_id,
                sender_id="system",
                sender_type="system",
                content=suggestion_content
            )
    
    async def _send_ticket_notifications(self, ticket: SupportTicket):
        """Send notifications for new ticket"""
        # Email confirmation to customer
        await self.email_service.send_template_email(
            to=ticket.customer_email,
            template="ticket_created",
            data={
                "ticket_number": ticket.ticket_number,
                "subject": ticket.subject,
                "sla_deadline": ticket.sla_deadline
            }
        )
        
        # Notify assigned agent
        if ticket.assigned_to:
            await self.notification_service.send_notification(
                user_id=ticket.assigned_to,
                title=f"New {ticket.priority} ticket assigned",
                message=f"{ticket.subject} - {ticket.ticket_number}",
                type="support_ticket",
                data={"ticket_id": ticket.id}
            )
        
        # Alert for critical tickets
        if ticket.priority == "critical":
            await self.notification_service.notify_team(
                team="support_managers",
                title="Critical ticket created",
                message=f"{ticket.ticket_number}: {ticket.subject}",
                data={"ticket_id": ticket.id}
            )
    
    async def _send_reply_notifications(
        self, 
        ticket: SupportTicket, 
        message: TicketMessage,
        sender_type: str
    ):
        """Send notifications for ticket replies"""
        if sender_type == "customer" and ticket.assigned_to:
            # Notify agent
            await self.notification_service.send_notification(
                user_id=ticket.assigned_to,
                title=f"Customer replied to {ticket.ticket_number}",
                message=message.content[:100] + "...",
                type="ticket_reply",
                data={"ticket_id": ticket.id}
            )
        elif sender_type == "agent":
            # Email customer
            await self.email_service.send_template_email(
                to=ticket.customer_email,
                template="ticket_reply",
                data={
                    "ticket_number": ticket.ticket_number,
                    "message": message.content,
                    "agent_name": message.sender_name
                }
            )
    
    def _get_sender_name(self, sender_id: str, sender_type: str) -> str:
        """Get sender name"""
        if sender_type == "system":
            return "System"
        
        # Lookup user/agent name from database
        # Simplified for now
        return f"User {sender_id}"
    
    def _get_article_category(self, article_id: str) -> str:
        """Get article category"""
        article = self.knowledge_base.articles.get(article_id)
        return article.category if article else "General"
    
    def _get_article_stats(self, article_id: str) -> Dict[str, int]:
        """Get article statistics"""
        article = self.knowledge_base.articles.get(article_id)
        if article:
            return {
                "views": article.view_count,
                "helpful": article.helpful_count,
                "not_helpful": article.not_helpful_count
            }
        return {"views": 0, "helpful": 0, "not_helpful": 0}
    
    def _estimate_wait_time(self, department: Optional[str]) -> int:
        """Estimate chat wait time in seconds"""
        if department:
            return self.chat_system._estimate_wait_time(department)
        return 300  # Default 5 minutes
    
    def _get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Get agent information"""
        agent = self.chat_system.agents.get(agent_id)
        if agent:
            return {
                "id": agent.agent_id,
                "name": agent.name,
                "avatar_url": agent.avatar_url,
                "status": agent.status.value
            }
        return {"id": agent_id, "name": "Support Agent"}
    
    def _get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents"""
        try:
            from database.models import User, Team
            from sqlalchemy import text
            
            # Query agents with support role
            agents_query = self.db.query(User).filter(
                or_(
                    User.role == 'support_agent',
                    User.role == 'admin',
                    User.metadata.op('->>')('is_support_agent') == 'true'
                )
            ).all()
            
            available_agents = []
            
            for agent in agents_query:
                # Count current tickets
                current_tickets = self.db.query(SupportTicket).filter(
                    and_(
                        SupportTicket.assigned_to == str(agent.id),
                        SupportTicket.status.in_(['open', 'in_progress'])
                    )
                ).count()
                
                # Get agent's specializations from metadata
                specializations = []
                if hasattr(agent, 'metadata') and agent.metadata:
                    agent_metadata = agent.metadata if isinstance(agent.metadata, dict) else {}
                    specializations = agent_metadata.get('specializations', [])
                    
                    # Default specializations based on team
                    if not specializations:
                        team_name = agent_metadata.get('team', 'general')
                        if team_name == 'technical':
                            specializations = ['technical', 'api', 'bug', 'integration']
                        elif team_name == 'billing':
                            specializations = ['billing', 'subscription', 'payment']
                        elif team_name == 'onboarding':
                            specializations = ['onboarding', 'setup', 'training']
                        else:
                            specializations = ['general', 'account', 'feature']
                
                # Calculate satisfaction rating
                try:
                    rating_query = text("""
                        SELECT AVG(rating) as avg_rating
                        FROM ticket_feedback
                        WHERE agent_id = :agent_id
                        AND created_at > :since_date
                    """)
                    
                    result = self.db.execute(
                        rating_query,
                        {
                            'agent_id': str(agent.id),
                            'since_date': datetime.utcnow() - timedelta(days=90)
                        }
                    ).first()
                    
                    satisfaction_rating = result.avg_rating if result and result.avg_rating else 4.5
                except:
                    satisfaction_rating = 4.5  # Default rating
                
                # Determine if agent is available
                max_tickets = agent_metadata.get('max_tickets', 10) if hasattr(agent, 'metadata') and agent.metadata else 10
                is_available = current_tickets < max_tickets
                
                # Check if agent is online/active
                is_online = True  # Default to online
                if hasattr(agent, 'last_activity'):
                    is_online = (datetime.utcnow() - agent.last_activity).seconds < 600  # Active in last 10 mins
                
                if is_available and is_online:
                    available_agents.append({
                        "id": str(agent.id),
                        "name": agent.full_name or agent.username,
                        "team": agent_metadata.get('team', 'general') if hasattr(agent, 'metadata') and agent.metadata else 'general',
                        "specializations": specializations,
                        "current_tickets": current_tickets,
                        "max_tickets": max_tickets,
                        "satisfaction_rating": round(satisfaction_rating, 1),
                        "handles_priority": agent_metadata.get('handles_priority', True) if hasattr(agent, 'metadata') and agent.metadata else True,
                        "email": agent.email,
                        "experience_level": agent_metadata.get('experience_level', 'intermediate') if hasattr(agent, 'metadata') and agent.metadata else 'intermediate'
                    })
            
            # If no agents available, return default agent
            if not available_agents:
                # Create a system agent for assignment
                available_agents.append({
                    "id": "system_agent",
                    "name": "Support Team",
                    "team": "general",
                    "specializations": ["general"],
                    "current_tickets": 0,
                    "max_tickets": 100,
                    "satisfaction_rating": 4.5,
                    "handles_priority": True,
                    "email": "support@example.com",
                    "experience_level": "senior"
                })
            
            return available_agents
            
        except Exception as e:
            # Return default agent on error
            import logging
            logging.error(f"Error getting available agents: {e}")
            
            return [
                {
                    "id": "default_agent",
                    "name": "Support Team",
                    "team": "general",
                    "specializations": ["general"],
                    "current_tickets": 0,
                    "max_tickets": 100,
                    "satisfaction_rating": 4.5,
                    "handles_priority": True,
                    "email": "support@example.com",
                    "experience_level": "senior"
                }
            ]
    
    def _calculate_avg_wait_time(self, chat_metrics: Dict[str, Any]) -> float:
        """Calculate average wait time across departments"""
        wait_times = []
        for dept, metrics in chat_metrics.items():
            if isinstance(metrics, dict) and "estimated_wait_time" in metrics:
                wait_times.append(metrics["estimated_wait_time"])
        
        return sum(wait_times) / len(wait_times) if wait_times else 0