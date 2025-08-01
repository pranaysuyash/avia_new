"""
Webhook management system for processing notifications
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import aiohttp
import hashlib
import hmac
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Types of webhook events"""
    TRANSCRIPTION_STARTED = "transcription.started"
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    TRANSCRIPTION_FAILED = "transcription.failed"
    ENTITY_EXTRACTION_COMPLETED = "entity_extraction.completed"
    BATCH_JOB_STARTED = "batch_job.started"
    BATCH_JOB_COMPLETED = "batch_job.completed"
    BATCH_JOB_FAILED = "batch_job.failed"
    USER_REGISTERED = "user.registered"
    TEAM_MEMBER_ADDED = "team.member_added"
    TRANSCRIPT_SHARED = "transcript.shared"
    ANNOTATION_ADDED = "annotation.added"
    EXPORT_COMPLETED = "export.completed"


@dataclass
class WebhookEvent:
    """Webhook event data structure"""
    id: str
    event_type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    resource_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'resource_id': self.resource_id
        }


@dataclass
class WebhookSubscription:
    """Webhook subscription configuration"""
    id: str
    url: str
    event_types: List[WebhookEventType]
    secret: str
    active: bool = True
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 5
    timeout: int = 30
    retry_count: int = 3
    headers: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.headers is None:
            self.headers = {}


class WebhookManager:
    """Manages webhook subscriptions and event delivery"""
    
    def __init__(self):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.event_queue: List[WebhookEvent] = []
        self.delivery_workers = 3
        self.is_running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        logger.info("Webhook manager initialized")
    
    def add_subscription(
        self,
        url: str,
        event_types: List[WebhookEventType],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_count: int = 3
    ) -> str:
        """Add a new webhook subscription"""
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid webhook URL")
        
        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError("Webhook URL must use HTTP or HTTPS")
        
        # Generate subscription ID and secret
        subscription_id = str(uuid.uuid4())
        if not secret:
            secret = str(uuid.uuid4())
        
        subscription = WebhookSubscription(
            id=subscription_id,
            url=url,
            event_types=event_types,
            secret=secret,
            headers=headers or {},
            timeout=timeout,
            retry_count=retry_count
        )
        
        self.subscriptions[subscription_id] = subscription
        
        logger.info(f"Added webhook subscription {subscription_id} for {url}")
        return subscription_id
    
    def remove_subscription(self, subscription_id: str) -> bool:
        """Remove a webhook subscription"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Removed webhook subscription {subscription_id}")
            return True
        return False
    
    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get a webhook subscription by ID"""
        return self.subscriptions.get(subscription_id)
    
    def list_subscriptions(self, active_only: bool = True) -> List[WebhookSubscription]:
        """List all webhook subscriptions"""
        subscriptions = list(self.subscriptions.values())
        if active_only:
            subscriptions = [s for s in subscriptions if s.active]
        return subscriptions
    
    def update_subscription(
        self,
        subscription_id: str,
        url: Optional[str] = None,
        event_types: Optional[List[WebhookEventType]] = None,
        active: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Update a webhook subscription"""
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            return False
        
        if url is not None:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid webhook URL")
            subscription.url = url
        
        if event_types is not None:
            subscription.event_types = event_types
        
        if active is not None:
            subscription.active = active
        
        if headers is not None:
            subscription.headers = headers
        
        logger.info(f"Updated webhook subscription {subscription_id}")
        return True
    
    async def trigger_event(
        self,
        event_type: WebhookEventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> str:
        """Trigger a webhook event"""
        
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
            user_id=user_id,
            team_id=team_id,
            resource_id=resource_id
        )
        
        # Add to queue for processing
        self.event_queue.append(event)
        
        logger.info(f"Triggered webhook event {event_type.value} with ID {event.id}")
        return event.id
    
    async def start_workers(self):
        """Start webhook delivery workers"""
        if self.is_running:
            return
        
        self.is_running = True
        self._worker_tasks = []
        
        for i in range(self.delivery_workers):
            task = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        logger.info(f"Started {self.delivery_workers} webhook delivery workers")
    
    async def stop_workers(self):
        """Stop webhook delivery workers"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks = []
        
        logger.info("Stopped webhook delivery workers")
    
    async def _delivery_worker(self, worker_name: str):
        """Worker process for delivering webhook events"""
        logger.info(f"Webhook delivery worker {worker_name} started")
        
        while self.is_running:
            try:
                # Check for events to process
                if not self.event_queue:
                    await asyncio.sleep(1)
                    continue
                
                # Get next event
                event = self.event_queue.pop(0)
                
                # Find matching subscriptions
                matching_subscriptions = [
                    sub for sub in self.subscriptions.values()
                    if sub.active and event.event_type in sub.event_types
                ]
                
                if not matching_subscriptions:
                    logger.debug(f"No subscriptions for event {event.event_type.value}")
                    continue
                
                # Deliver to all matching subscriptions
                delivery_tasks = [
                    self._deliver_event(event, subscription)
                    for subscription in matching_subscriptions
                ]
                
                await asyncio.gather(*delivery_tasks, return_exceptions=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook delivery worker {worker_name}: {e}")
                await asyncio.sleep(5)  # Back off on error
        
        logger.info(f"Webhook delivery worker {worker_name} stopped")
    
    async def _deliver_event(self, event: WebhookEvent, subscription: WebhookSubscription):
        """Deliver a single event to a subscription"""
        
        # Check if subscription is disabled due to failures
        if subscription.failure_count >= subscription.max_failures:
            logger.warning(f"Subscription {subscription.id} disabled due to failures")
            subscription.active = False
            return
        
        # Prepare payload
        payload = event.to_dict()
        payload_json = json.dumps(payload, separators=(',', ':'))
        
        # Generate signature
        signature = self._generate_signature(payload_json, subscription.secret)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AudioTranscription-Webhook/1.0',
            'X-Webhook-Event': event.event_type.value,
            'X-Webhook-ID': event.id,
            'X-Webhook-Timestamp': str(int(event.timestamp.timestamp())),
            'X-Webhook-Signature': signature,
            **subscription.headers
        }
        
        # Attempt delivery with retries
        for attempt in range(subscription.retry_count + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=subscription.timeout)) as session:
                    async with session.post(
                        subscription.url,
                        data=payload_json,
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            # Success
                            subscription.last_triggered = datetime.utcnow()
                            subscription.failure_count = 0
                            logger.info(f"Successfully delivered event {event.id} to {subscription.url}")
                            return
                        else:
                            # HTTP error
                            response_text = await response.text()
                            logger.warning(
                                f"Webhook delivery failed for {subscription.url}: "
                                f"HTTP {response.status} - {response_text}"
                            )
                            
                            if attempt < subscription.retry_count:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            
            except asyncio.TimeoutError:
                logger.warning(f"Webhook delivery timeout for {subscription.url} (attempt {attempt + 1})")
                if attempt < subscription.retry_count:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"Webhook delivery error for {subscription.url}: {e}")
                if attempt < subscription.retry_count:
                    await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
        subscription.failure_count += 1
        logger.error(
            f"Failed to deliver event {event.id} to {subscription.url} "
            f"after {subscription.retry_count + 1} attempts"
        )
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected_signature = self._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook system statistics"""
        active_subscriptions = len([s for s in self.subscriptions.values() if s.active])
        total_subscriptions = len(self.subscriptions)
        
        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'inactive_subscriptions': total_subscriptions - active_subscriptions,
            'events_in_queue': len(self.event_queue),
            'workers_running': len(self._worker_tasks),
            'is_running': self.is_running
        }


# Global webhook manager instance
webhook_manager = WebhookManager()