"""
Live Chat and Real-time Support System

Real-time chat support with agent routing, canned responses, and co-browsing
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import asyncio
from collections import defaultdict, deque
import json
import uuid
from dataclasses import dataclass
import websockets

class ChatStatus(str, Enum):
    """Chat session status"""
    WAITING = "waiting"
    CONNECTED = "connected"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    TRANSFERRING = "transferring"
    ENDED = "ended"
    ABANDONED = "abandoned"

class MessageType(str, Enum):
    """Chat message types"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    TYPING = "typing"
    READ_RECEIPT = "read_receipt"
    AGENT_JOIN = "agent_join"
    AGENT_LEAVE = "agent_leave"
    TRANSFER = "transfer"
    RATING_REQUEST = "rating_request"

class AgentStatus(str, Enum):
    """Agent availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    AWAY = "away"
    OFFLINE = "offline"

class CustomerInfo(BaseModel):
    """Customer information"""
    customer_id: Optional[str]
    name: str
    email: Optional[str]
    phone: Optional[str]
    
    # Context
    page_url: Optional[str]
    referrer: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    ip_address: Optional[str]
    
    # Customer data
    account_type: Optional[str]
    previous_chats: int = 0
    total_spent: float = 0

class ChatMessage(BaseModel):
    """Chat message"""
    message_id: str
    chat_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Sender
    sender_id: str
    sender_type: str  # customer, agent, system
    sender_name: str
    
    # Content
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = {}
    
    # Status
    delivered: bool = False
    read: bool = False
    
    # Attachments
    attachments: List[str] = []

class ChatSession(BaseModel):
    """Live chat session"""
    chat_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Participants
    customer: CustomerInfo
    agent_id: Optional[str]
    agent_name: Optional[str]
    
    # Status
    status: ChatStatus = ChatStatus.WAITING
    queue_position: Optional[int]
    
    # Timing
    connected_at: Optional[datetime]
    first_response_at: Optional[datetime]
    ended_at: Optional[datetime]
    
    # Metrics
    wait_time_seconds: Optional[int]
    duration_seconds: Optional[int]
    message_count: int = 0
    
    # Routing
    department: Optional[str]
    priority: int = 0  # Higher = more urgent
    tags: List[str] = []
    
    # Satisfaction
    rating: Optional[int]  # 1-5
    feedback: Optional[str]
    
    # Transfer history
    transfer_history: List[Dict[str, Any]] = []

class CannedResponse(BaseModel):
    """Pre-written response template"""
    response_id: str
    title: str
    content: str
    category: str
    
    # Usage
    shortcuts: List[str] = []  # e.g., ["/hello", "/hi"]
    placeholders: List[str] = []  # e.g., ["{{customer_name}}", "{{agent_name}}"]
    
    # Metadata
    usage_count: int = 0
    last_used: Optional[datetime]

class ChatAgent(BaseModel):
    """Chat support agent"""
    agent_id: str
    name: str
    email: str
    avatar_url: Optional[str]
    
    # Status
    status: AgentStatus = AgentStatus.OFFLINE
    status_message: Optional[str]
    
    # Capacity
    max_concurrent_chats: int = 5
    current_chat_count: int = 0
    
    # Skills and routing
    departments: List[str] = []
    languages: List[str] = ["en"]
    skills: List[str] = []
    
    # Performance
    avg_response_time: float = 0
    avg_chat_duration: float = 0
    satisfaction_rating: float = 0
    total_chats_handled: int = 0

class ChatQueue:
    """Chat queue management"""
    
    def __init__(self):
        self.queue: deque = deque()
        self.priority_queue: deque = deque()
        
    def add_to_queue(self, chat_session: ChatSession):
        """Add chat to appropriate queue"""
        if chat_session.priority > 0:
            self.priority_queue.append(chat_session)
        else:
            self.queue.append(chat_session)
    
    def get_next_chat(self) -> Optional[ChatSession]:
        """Get next chat from queue"""
        if self.priority_queue:
            return self.priority_queue.popleft()
        elif self.queue:
            return self.queue.popleft()
        return None
    
    def get_queue_position(self, chat_id: str) -> Optional[int]:
        """Get position in queue"""
        position = 1
        
        # Check priority queue
        for chat in self.priority_queue:
            if chat.chat_id == chat_id:
                return position
            position += 1
        
        # Check regular queue
        for chat in self.queue:
            if chat.chat_id == chat_id:
                return position
            position += 1
        
        return None
    
    def remove_from_queue(self, chat_id: str) -> bool:
        """Remove chat from queue"""
        # Try priority queue
        for i, chat in enumerate(self.priority_queue):
            if chat.chat_id == chat_id:
                del self.priority_queue[i]
                return True
        
        # Try regular queue
        for i, chat in enumerate(self.queue):
            if chat.chat_id == chat_id:
                del self.queue[i]
                return True
        
        return False

class LiveChatSystem:
    """Main live chat system"""
    
    def __init__(self):
        self.chat_sessions: Dict[str, ChatSession] = {}
        self.messages: Dict[str, List[ChatMessage]] = defaultdict(list)
        self.agents: Dict[str, ChatAgent] = {}
        self.canned_responses: Dict[str, CannedResponse] = {}
        
        # Queues by department
        self.queues: Dict[str, ChatQueue] = defaultdict(ChatQueue)
        
        # Active connections (WebSocket connections in production)
        self.connections: Dict[str, Any] = {}  # chat_id -> connection
        
        # Routing rules
        self.routing_rules: List[Dict[str, Any]] = []
        
        # Metrics
        self.metrics = {
            "total_chats": 0,
            "active_chats": 0,
            "queued_chats": 0,
            "avg_wait_time": 0,
            "avg_chat_duration": 0
        }
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample data"""
        # Sample canned responses
        self.canned_responses["greeting"] = CannedResponse(
            response_id="greeting",
            title="Greeting",
            content="Hello {{customer_name}}! I'm {{agent_name}} and I'll be happy to help you today. How can I assist you?",
            category="Greetings",
            shortcuts=["/hello", "/hi"],
            placeholders=["{{customer_name}}", "{{agent_name}}"]
        )
        
        self.canned_responses["check_order"] = CannedResponse(
            response_id="check_order",
            title="Check Order Status",
            content="I'd be happy to check your order status. Could you please provide your order number?",
            category="Orders",
            shortcuts=["/order", "/status"]
        )
    
    async def start_chat(
        self,
        customer_info: CustomerInfo,
        initial_message: str,
        department: Optional[str] = None
    ) -> ChatSession:
        """Start new chat session"""
        # Create chat session
        chat_session = ChatSession(
            chat_id=str(uuid.uuid4()),
            customer=customer_info,
            department=department or "general"
        )
        
        # Determine priority
        if customer_info.account_type == "premium":
            chat_session.priority = 1
        
        # Store session
        self.chat_sessions[chat_session.chat_id] = chat_session
        
        # Create initial message
        initial_msg = ChatMessage(
            message_id=str(uuid.uuid4()),
            chat_id=chat_session.chat_id,
            sender_id=customer_info.customer_id or "anonymous",
            sender_type="customer",
            sender_name=customer_info.name,
            message_type=MessageType.TEXT,
            content=initial_message
        )
        self.messages[chat_session.chat_id].append(initial_msg)
        
        # Try to assign agent
        agent = await self._find_available_agent(chat_session)
        
        if agent:
            await self._assign_agent_to_chat(chat_session, agent)
        else:
            # Add to queue
            self.queues[department or "general"].add_to_queue(chat_session)
            chat_session.queue_position = self.queues[department or "general"].get_queue_position(chat_session.chat_id)
            
            # Send queue notification
            await self._send_system_message(
                chat_session.chat_id,
                f"Thank you for contacting us. You are currently number {chat_session.queue_position} in the queue. An agent will be with you shortly."
            )
        
        # Update metrics
        self.metrics["total_chats"] += 1
        if chat_session.status == ChatStatus.ACTIVE:
            self.metrics["active_chats"] += 1
        else:
            self.metrics["queued_chats"] += 1
        
        return chat_session
    
    async def _find_available_agent(self, chat_session: ChatSession) -> Optional[ChatAgent]:
        """Find available agent for chat"""
        available_agents = []
        
        for agent in self.agents.values():
            # Check availability
            if agent.status != AgentStatus.AVAILABLE:
                continue
            
            if agent.current_chat_count >= agent.max_concurrent_chats:
                continue
            
            # Check department match
            if chat_session.department and chat_session.department not in agent.departments:
                continue
            
            # Check language match
            if chat_session.customer.browser:  # Simplified language detection
                # In production, detect language from browser/customer preferences
                pass
            
            available_agents.append(agent)
        
        if available_agents:
            # Sort by current load (ascending) and rating (descending)
            available_agents.sort(
                key=lambda a: (a.current_chat_count, -a.satisfaction_rating)
            )
            return available_agents[0]
        
        return None
    
    async def _assign_agent_to_chat(self, chat_session: ChatSession, agent: ChatAgent):
        """Assign agent to chat session"""
        chat_session.agent_id = agent.agent_id
        chat_session.agent_name = agent.name
        chat_session.status = ChatStatus.CONNECTED
        chat_session.connected_at = datetime.utcnow()
        
        # Update agent load
        agent.current_chat_count += 1
        
        # Remove from queue if queued
        if chat_session.queue_position:
            self.queues[chat_session.department or "general"].remove_from_queue(chat_session.chat_id)
            chat_session.queue_position = None
        
        # Send agent join notification
        await self._send_system_message(
            chat_session.chat_id,
            f"{agent.name} has joined the chat",
            MessageType.AGENT_JOIN
        )
        
        # Mark as active
        chat_session.status = ChatStatus.ACTIVE
    
    async def send_message(
        self,
        chat_id: str,
        sender_id: str,
        sender_type: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        attachments: List[str] = None
    ) -> ChatMessage:
        """Send message in chat"""
        chat_session = self.chat_sessions.get(chat_id)
        if not chat_session:
            raise ValueError(f"Chat session {chat_id} not found")
        
        # Get sender name
        sender_name = "System"
        if sender_type == "customer":
            sender_name = chat_session.customer.name
        elif sender_type == "agent" and chat_session.agent_name:
            sender_name = chat_session.agent_name
        
        # Create message
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_id=sender_id,
            sender_type=sender_type,
            sender_name=sender_name,
            message_type=message_type,
            content=content,
            attachments=attachments or []
        )
        
        # Process canned responses for agents
        if sender_type == "agent":
            message.content = self._process_canned_response(message.content, chat_session)
        
        # Store message
        self.messages[chat_id].append(message)
        chat_session.message_count += 1
        
        # Track first response time
        if sender_type == "agent" and not chat_session.first_response_at:
            chat_session.first_response_at = datetime.utcnow()
            chat_session.wait_time_seconds = int(
                (chat_session.first_response_at - chat_session.created_at).total_seconds()
            )
        
        # Broadcast to connected clients
        await self._broadcast_message(chat_id, message)
        
        return message
    
    def _process_canned_response(self, content: str, chat_session: ChatSession) -> str:
        """Process canned response shortcuts and placeholders"""
        # Check for shortcuts
        for response in self.canned_responses.values():
            for shortcut in response.shortcuts:
                if content.strip() == shortcut:
                    content = response.content
                    response.usage_count += 1
                    response.last_used = datetime.utcnow()
                    break
        
        # Replace placeholders
        replacements = {
            "{{customer_name}}": chat_session.customer.name,
            "{{agent_name}}": chat_session.agent_name or "Agent",
            "{{date}}": datetime.now().strftime("%B %d, %Y"),
            "{{time}}": datetime.now().strftime("%I:%M %p")
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        return content
    
    async def _send_system_message(
        self,
        chat_id: str,
        content: str,
        message_type: MessageType = MessageType.SYSTEM
    ):
        """Send system message"""
        await self.send_message(
            chat_id,
            "system",
            "system",
            content,
            message_type
        )
    
    async def _broadcast_message(self, chat_id: str, message: ChatMessage):
        """Broadcast message to connected clients"""
        # In production, send via WebSocket to connected clients
        # This is a simplified version
        if chat_id in self.connections:
            # Send to all participants
            pass
    
    async def send_typing_indicator(self, chat_id: str, sender_id: str, is_typing: bool):
        """Send typing indicator"""
        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_id=sender_id,
            sender_type="agent" if sender_id in self.agents else "customer",
            sender_name="",
            message_type=MessageType.TYPING,
            content=str(is_typing)
        )
        
        await self._broadcast_message(chat_id, message)
    
    async def transfer_chat(
        self,
        chat_id: str,
        from_agent_id: str,
        to_agent_id: Optional[str] = None,
        to_department: Optional[str] = None,
        reason: str = ""
    ) -> bool:
        """Transfer chat to another agent or department"""
        chat_session = self.chat_sessions.get(chat_id)
        if not chat_session:
            return False
        
        # Record transfer
        transfer_record = {
            "from_agent": from_agent_id,
            "to_agent": to_agent_id,
            "to_department": to_department,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        }
        chat_session.transfer_history.append(transfer_record)
        
        # Update status
        chat_session.status = ChatStatus.TRANSFERRING
        
        # Release current agent
        if from_agent_id in self.agents:
            self.agents[from_agent_id].current_chat_count -= 1
        
        # Notify transfer
        await self._send_system_message(
            chat_id,
            f"Chat is being transferred. {reason}",
            MessageType.TRANSFER
        )
        
        # Assign to specific agent or queue
        if to_agent_id and to_agent_id in self.agents:
            agent = self.agents[to_agent_id]
            if agent.status == AgentStatus.AVAILABLE and agent.current_chat_count < agent.max_concurrent_chats:
                await self._assign_agent_to_chat(chat_session, agent)
                return True
        
        # Add to department queue
        department = to_department or chat_session.department or "general"
        chat_session.department = department
        self.queues[department].add_to_queue(chat_session)
        chat_session.status = ChatStatus.WAITING
        
        return True
    
    async def end_chat(
        self,
        chat_id: str,
        ended_by: str,
        reason: Optional[str] = None
    ) -> bool:
        """End chat session"""
        chat_session = self.chat_sessions.get(chat_id)
        if not chat_session:
            return False
        
        # Update status
        chat_session.status = ChatStatus.ENDED
        chat_session.ended_at = datetime.utcnow()
        
        # Calculate duration
        if chat_session.connected_at:
            chat_session.duration_seconds = int(
                (chat_session.ended_at - chat_session.connected_at).total_seconds()
            )
        
        # Release agent
        if chat_session.agent_id and chat_session.agent_id in self.agents:
            self.agents[chat_session.agent_id].current_chat_count -= 1
        
        # Send end notification
        await self._send_system_message(
            chat_id,
            f"Chat ended by {ended_by}. {reason or ''}"
        )
        
        # Request rating
        await self._send_system_message(
            chat_id,
            "Please rate your chat experience on a scale of 1-5 stars.",
            MessageType.RATING_REQUEST
        )
        
        # Update metrics
        self.metrics["active_chats"] -= 1
        
        return True
    
    def submit_chat_rating(
        self,
        chat_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """Submit chat rating"""
        chat_session = self.chat_sessions.get(chat_id)
        if not chat_session:
            return False
        
        chat_session.rating = rating
        chat_session.feedback = feedback
        
        # Update agent rating
        if chat_session.agent_id and chat_session.agent_id in self.agents:
            agent = self.agents[chat_session.agent_id]
            # Update average rating
            total_rating = agent.satisfaction_rating * agent.total_chats_handled + rating
            agent.total_chats_handled += 1
            agent.satisfaction_rating = total_rating / agent.total_chats_handled
        
        return True
    
    def get_chat_transcript(self, chat_id: str) -> List[ChatMessage]:
        """Get full chat transcript"""
        return self.messages.get(chat_id, [])
    
    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get agent performance metrics"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {}
        
        # Calculate metrics from handled chats
        handled_chats = [
            chat for chat in self.chat_sessions.values()
            if chat.agent_id == agent_id
        ]
        
        response_times = []
        chat_durations = []
        ratings = []
        
        for chat in handled_chats:
            if chat.wait_time_seconds:
                response_times.append(chat.wait_time_seconds)
            if chat.duration_seconds:
                chat_durations.append(chat.duration_seconds)
            if chat.rating:
                ratings.append(chat.rating)
        
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": agent.status.value,
            "current_chats": agent.current_chat_count,
            "total_chats_handled": agent.total_chats_handled,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "avg_chat_duration": sum(chat_durations) / len(chat_durations) if chat_durations else 0,
            "satisfaction_rating": agent.satisfaction_rating,
            "ratings_breakdown": {
                "5_star": len([r for r in ratings if r == 5]),
                "4_star": len([r for r in ratings if r == 4]),
                "3_star": len([r for r in ratings if r == 3]),
                "2_star": len([r for r in ratings if r == 2]),
                "1_star": len([r for r in ratings if r == 1])
            }
        }
    
    def get_queue_status(self, department: Optional[str] = None) -> Dict[str, Any]:
        """Get queue status"""
        if department:
            queue = self.queues[department]
            return {
                "department": department,
                "queue_length": len(queue.queue) + len(queue.priority_queue),
                "priority_queue_length": len(queue.priority_queue),
                "estimated_wait_time": self._estimate_wait_time(department)
            }
        
        # All queues
        all_queues = {}
        for dept, queue in self.queues.items():
            all_queues[dept] = {
                "queue_length": len(queue.queue) + len(queue.priority_queue),
                "priority_queue_length": len(queue.priority_queue),
                "estimated_wait_time": self._estimate_wait_time(dept)
            }
        
        return all_queues
    
    def _estimate_wait_time(self, department: str) -> int:
        """Estimate wait time in seconds"""
        # Simple estimation based on queue length and average chat duration
        queue = self.queues[department]
        queue_length = len(queue.queue) + len(queue.priority_queue)
        
        # Get available agents for department
        available_agents = len([
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.AVAILABLE
            and department in agent.departments
            and agent.current_chat_count < agent.max_concurrent_chats
        ])
        
        if available_agents == 0:
            return queue_length * 300  # 5 minutes per chat if no agents
        
        # Estimate based on queue and agents
        avg_chat_duration = 600  # 10 minutes average
        return int((queue_length / available_agents) * avg_chat_duration)

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize live chat system
        chat_system = LiveChatSystem()
        
        # Create sample agent
        agent = ChatAgent(
            agent_id="agent_jane",
            name="Jane Smith",
            email="jane@support.com",
            status=AgentStatus.AVAILABLE,
            departments=["sales", "general"],
            languages=["en", "es"]
        )
        chat_system.agents[agent.agent_id] = agent
        
        # Start chat
        customer = CustomerInfo(
            customer_id="cust_456",
            name="John Doe",
            email="john@example.com",
            page_url="https://example.com/pricing",
            account_type="premium"
        )
        
        chat = await chat_system.start_chat(
            customer,
            "Hi, I have a question about your pricing plans.",
            department="sales"
        )
        
        print(f"Chat started: {chat.chat_id}")
        print(f"Status: {chat.status.value}")
        print(f"Agent: {chat.agent_name}")
        
        # Send agent message
        if chat.agent_id:
            await chat_system.send_message(
                chat.chat_id,
                chat.agent_id,
                "agent",
                "/hello"  # Using canned response
            )
            
            # Send follow-up
            await chat_system.send_message(
                chat.chat_id,
                chat.agent_id,
                "agent",
                "I see you're looking at our pricing page. Our premium plan includes unlimited transcriptions and priority support. What specific features are you interested in?"
            )
        
        # Customer response
        await chat_system.send_message(
            chat.chat_id,
            customer.customer_id,
            "customer",
            "I need API access and team collaboration features."
        )
        
        # Get transcript
        transcript = chat_system.get_chat_transcript(chat.chat_id)
        print(f"\nChat transcript ({len(transcript)} messages):")
        for msg in transcript:
            print(f"[{msg.sender_name}]: {msg.content}")
        
        # End chat
        await chat_system.end_chat(chat.chat_id, "customer")
        
        # Submit rating
        chat_system.submit_chat_rating(chat.chat_id, 5, "Very helpful!")
        
        # Get agent metrics
        metrics = chat_system.get_agent_metrics(agent.agent_id)
        print(f"\nAgent metrics:")
        print(f"Total chats: {metrics['total_chats_handled']}")
        print(f"Satisfaction: {metrics['satisfaction_rating']:.1f}/5")
    
    asyncio.run(main())