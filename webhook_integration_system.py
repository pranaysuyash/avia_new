"""
Webhook Integration System
Manages webhooks, event delivery, and third-party integrations
"""

import asyncio
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import httpx
import redis.asyncio as redis
from pydantic import BaseModel, HttpUrl, Field
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import logging
from collections import defaultdict
import backoff
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WebhookEvent(str, Enum):
    """Webhook event types"""
    # Transcription events
    TRANSCRIPTION_STARTED = "transcription.started"
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    TRANSCRIPTION_FAILED = "transcription.failed"
    
    # Collaboration events
    COLLABORATION_SESSION_CREATED = "collaboration.session.created"
    COLLABORATION_USER_JOINED = "collaboration.user.joined"
    COLLABORATION_USER_LEFT = "collaboration.user.left"
    COLLABORATION_DOCUMENT_UPDATED = "collaboration.document.updated"
    
    # Analysis events
    ANALYSIS_COMPLETED = "analysis.completed"
    SENTIMENT_DETECTED = "sentiment.detected"
    KEYWORDS_EXTRACTED = "keywords.extracted"
    
    # Media events
    MEDIA_UPLOADED = "media.uploaded"
    MEDIA_PROCESSED = "media.processed"
    HIGHLIGHTS_GENERATED = "highlights.generated"
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # System events
    SYSTEM_ALERT = "system.alert"
    QUOTA_EXCEEDED = "quota.exceeded"
    API_KEY_CREATED = "api.key.created"

class WebhookStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"

class AuthType(str, Enum):
    """Webhook authentication types"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    HMAC_SHA256 = "hmac_sha256"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"

@dataclass
class WebhookConfig:
    """Webhook configuration"""
    id: str
    url: str
    events: List[WebhookEvent]
    active: bool = True
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    retry_config: Dict[str, int] = field(default_factory=lambda: {
        'max_retries': 3,
        'retry_delay': 1,
        'timeout': 30
    })
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'events': [e.value for e in self.events],
            'active': self.active,
            'auth_type': self.auth_type.value,
            'auth_config': self.auth_config,
            'headers': self.headers,
            'retry_config': self.retry_config,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""
    id: str
    webhook_id: str
    event: WebhookEvent
    payload: Dict[str, Any]
    status: WebhookStatus
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'event': self.event.value,
            'payload': self.payload,
            'status': self.status.value,
            'attempts': self.attempts,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'next_retry': self.next_retry.isoformat() if self.next_retry else None,
            'response_code': self.response_code,
            'response_body': self.response_body,
            'error': self.error,
            'created_at': self.created_at.isoformat()
        }

class WebhookIntegrationSystem:
    """Main webhook integration system"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.event_subscriptions: Dict[WebhookEvent, Set[str]] = defaultdict(set)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._running = False
        self._delivery_task = None
        self._retry_task = None
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            'total_webhooks': 0,
            'total_deliveries': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'average_response_time': 0
        }
        
    async def initialize(self):
        """Initialize the webhook system"""
        if not self.redis_client:
            self.redis_client = await redis.from_url("redis://localhost:6379")
            
        # Load existing webhooks from Redis
        await self._load_webhooks()
        
        self._running = True
        self._delivery_task = asyncio.create_task(self._process_delivery_queue())
        self._retry_task = asyncio.create_task(self._process_retries())
        
        logger.info("Webhook integration system initialized")
        
    async def shutdown(self):
        """Shutdown the webhook system"""
        self._running = False
        
        if self._delivery_task:
            self._delivery_task.cancel()
        if self._retry_task:
            self._retry_task.cancel()
            
        await self.http_client.aclose()
        
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Webhook integration system shutdown")
        
    async def _load_webhooks(self):
        """Load webhooks from Redis"""
        if not self.redis_client:
            return
            
        webhook_keys = await self.redis_client.keys("webhook:config:*")
        
        for key in webhook_keys:
            webhook_data = await self.redis_client.hgetall(key)
            if webhook_data:
                webhook_id = key.decode().split(":")[-1]
                events = json.loads(webhook_data.get(b'events', b'[]').decode())
                
                webhook = WebhookConfig(
                    id=webhook_id,
                    url=webhook_data.get(b'url', b'').decode(),
                    events=[WebhookEvent(e) for e in events],
                    active=webhook_data.get(b'active', b'true').decode() == 'true',
                    auth_type=AuthType(webhook_data.get(b'auth_type', b'none').decode()),
                    auth_config=json.loads(webhook_data.get(b'auth_config', b'{}').decode()),
                    headers=json.loads(webhook_data.get(b'headers', b'{}').decode()),
                    retry_config=json.loads(webhook_data.get(b'retry_config', b'{}').decode())
                )
                
                self.webhooks[webhook_id] = webhook
                
                # Update event subscriptions
                for event in webhook.events:
                    self.event_subscriptions[event].add(webhook_id)
                    
        self.metrics['total_webhooks'] = len(self.webhooks)
        logger.info(f"Loaded {len(self.webhooks)} webhooks")
        
    async def create_webhook(
        self,
        url: str,
        events: List[WebhookEvent],
        auth_type: AuthType = AuthType.NONE,
        auth_config: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> str:
        """Create a new webhook"""
        webhook_id = str(uuid.uuid4())
        
        webhook = WebhookConfig(
            id=webhook_id,
            url=url,
            events=events,
            auth_type=auth_type,
            auth_config=auth_config or {},
            headers=headers or {}
        )
        
        self.webhooks[webhook_id] = webhook
        
        # Update event subscriptions
        for event in events:
            self.event_subscriptions[event].add(webhook_id)
            
        # Store in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"webhook:config:{webhook_id}",
                mapping={
                    'url': url,
                    'events': json.dumps([e.value for e in events]),
                    'active': 'true',
                    'auth_type': auth_type.value,
                    'auth_config': json.dumps(auth_config or {}),
                    'headers': json.dumps(headers or {}),
                    'retry_config': json.dumps(webhook.retry_config),
                    'created_at': webhook.created_at.isoformat()
                }
            )
            
        self.metrics['total_webhooks'] = len(self.webhooks)
        logger.info(f"Created webhook {webhook_id} for {url}")
        return webhook_id
        
    async def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        active: Optional[bool] = None,
        auth_config: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> bool:
        """Update an existing webhook"""
        if webhook_id not in self.webhooks:
            return False
            
        webhook = self.webhooks[webhook_id]
        
        # Remove old event subscriptions
        for event in webhook.events:
            self.event_subscriptions[event].discard(webhook_id)
            
        # Update fields
        if url is not None:
            webhook.url = url
        if events is not None:
            webhook.events = events
        if active is not None:
            webhook.active = active
        if auth_config is not None:
            webhook.auth_config = auth_config
        if headers is not None:
            webhook.headers = headers
            
        webhook.updated_at = datetime.utcnow()
        
        # Add new event subscriptions
        for event in webhook.events:
            if webhook.active:
                self.event_subscriptions[event].add(webhook_id)
                
        # Update in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"webhook:config:{webhook_id}",
                mapping={
                    'url': webhook.url,
                    'events': json.dumps([e.value for e in webhook.events]),
                    'active': str(webhook.active).lower(),
                    'auth_config': json.dumps(webhook.auth_config),
                    'headers': json.dumps(webhook.headers),
                    'updated_at': webhook.updated_at.isoformat()
                }
            )
            
        logger.info(f"Updated webhook {webhook_id}")
        return True
        
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        if webhook_id not in self.webhooks:
            return False
            
        webhook = self.webhooks[webhook_id]
        
        # Remove event subscriptions
        for event in webhook.events:
            self.event_subscriptions[event].discard(webhook_id)
            
        del self.webhooks[webhook_id]
        
        # Remove from Redis
        if self.redis_client:
            await self.redis_client.delete(f"webhook:config:{webhook_id}")
            
        self.metrics['total_webhooks'] = len(self.webhooks)
        logger.info(f"Deleted webhook {webhook_id}")
        return True
        
    async def trigger_event(
        self,
        event: WebhookEvent,
        payload: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Trigger a webhook event"""
        # Get subscribed webhooks
        webhook_ids = self.event_subscriptions.get(event, set())
        
        for webhook_id in webhook_ids:
            if webhook_id not in self.webhooks:
                continue
                
            webhook = self.webhooks[webhook_id]
            if not webhook.active:
                continue
                
            # Create delivery
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                webhook_id=webhook_id,
                event=event,
                payload={
                    'event': event.value,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': payload,
                    'user_id': user_id
                },
                status=WebhookStatus.PENDING
            )
            
            self.deliveries[delivery.id] = delivery
            
            # Add to delivery queue
            await self.delivery_queue.put(delivery.id)
            
        logger.info(f"Triggered event {event.value} for {len(webhook_ids)} webhooks")
        
    async def _process_delivery_queue(self):
        """Process webhook deliveries"""
        while self._running:
            try:
                delivery_id = await asyncio.wait_for(
                    self.delivery_queue.get(),
                    timeout=1.0
                )
                
                if delivery_id in self.deliveries:
                    delivery = self.deliveries[delivery_id]
                    await self._deliver_webhook(delivery)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing delivery queue: {e}")
                
    async def _deliver_webhook(self, delivery: WebhookDelivery):
        """Deliver a webhook"""
        if delivery.webhook_id not in self.webhooks:
            delivery.status = WebhookStatus.FAILED
            delivery.error = "Webhook not found"
            return
            
        webhook = self.webhooks[delivery.webhook_id]
        
        try:
            # Prepare request
            headers = webhook.headers.copy()
            headers['Content-Type'] = 'application/json'
            headers['X-Webhook-Event'] = delivery.event.value
            headers['X-Webhook-ID'] = webhook.id
            headers['X-Delivery-ID'] = delivery.id
            
            # Add authentication
            headers = await self._add_authentication(webhook, headers, delivery.payload)
            
            # Add signature
            if webhook.auth_type == AuthType.HMAC_SHA256:
                signature = self._generate_signature(
                    webhook.auth_config.get('secret', ''),
                    json.dumps(delivery.payload)
                )
                headers['X-Webhook-Signature'] = signature
                
            # Send request
            start_time = datetime.utcnow()
            
            response = await self.http_client.post(
                webhook.url,
                json=delivery.payload,
                headers=headers,
                timeout=webhook.retry_config.get('timeout', 30)
            )
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(response_time, response.status_code)
            
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response size
            delivery.attempts += 1
            delivery.last_attempt = datetime.utcnow()
            
            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.DELIVERED
                self.metrics['successful_deliveries'] += 1
                logger.info(f"Webhook delivered: {delivery.id}")
            else:
                await self._handle_delivery_failure(delivery, webhook, f"HTTP {response.status_code}")
                
        except httpx.TimeoutException:
            await self._handle_delivery_failure(delivery, webhook, "Timeout")
        except Exception as e:
            await self._handle_delivery_failure(delivery, webhook, str(e))
            
        # Update delivery in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"webhook:delivery:{delivery.id}",
                mapping={
                    'status': delivery.status.value,
                    'attempts': delivery.attempts,
                    'response_code': delivery.response_code or 0,
                    'error': delivery.error or '',
                    'last_attempt': delivery.last_attempt.isoformat() if delivery.last_attempt else ''
                }
            )
            
    async def _handle_delivery_failure(
        self,
        delivery: WebhookDelivery,
        webhook: WebhookConfig,
        error: str
    ):
        """Handle webhook delivery failure"""
        delivery.error = error
        delivery.attempts += 1
        delivery.last_attempt = datetime.utcnow()
        
        max_retries = webhook.retry_config.get('max_retries', 3)
        
        if delivery.attempts < max_retries:
            # Schedule retry
            retry_delay = webhook.retry_config.get('retry_delay', 1) * (2 ** delivery.attempts)
            delivery.next_retry = datetime.utcnow() + timedelta(seconds=retry_delay)
            delivery.status = WebhookStatus.RETRYING
            logger.warning(f"Webhook delivery failed, will retry: {delivery.id}")
        else:
            delivery.status = WebhookStatus.FAILED
            self.metrics['failed_deliveries'] += 1
            logger.error(f"Webhook delivery failed permanently: {delivery.id}")
            
    async def _process_retries(self):
        """Process webhook retries"""
        while self._running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                current_time = datetime.utcnow()
                
                for delivery_id, delivery in self.deliveries.items():
                    if (delivery.status == WebhookStatus.RETRYING and
                        delivery.next_retry and
                        delivery.next_retry <= current_time):
                        
                        # Re-queue for delivery
                        await self.delivery_queue.put(delivery_id)
                        
            except Exception as e:
                logger.error(f"Error processing retries: {e}")
                
    async def _add_authentication(
        self,
        webhook: WebhookConfig,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> Dict[str, str]:
        """Add authentication to request headers"""
        if webhook.auth_type == AuthType.BASIC:
            username = webhook.auth_config.get('username', '')
            password = webhook.auth_config.get('password', '')
            auth_str = f"{username}:{password}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"
            
        elif webhook.auth_type == AuthType.BEARER:
            token = webhook.auth_config.get('token', '')
            headers['Authorization'] = f"Bearer {token}"
            
        elif webhook.auth_type == AuthType.API_KEY:
            key_name = webhook.auth_config.get('key_name', 'X-API-Key')
            key_value = webhook.auth_config.get('key_value', '')
            headers[key_name] = key_value
            
        elif webhook.auth_type == AuthType.OAUTH2:
            # Get or refresh OAuth2 token
            token = await self._get_oauth2_token(webhook.auth_config)
            headers['Authorization'] = f"Bearer {token}"
            
        return headers
        
    async def _get_oauth2_token(self, auth_config: Dict) -> str:
        """Get or refresh OAuth2 token"""
        # Check if token is cached and valid
        token_key = f"oauth2:token:{auth_config.get('client_id', '')}"
        
        if self.redis_client:
            cached_token = await self.redis_client.get(token_key)
            if cached_token:
                return cached_token.decode()
                
        # Request new token
        token_url = auth_config.get('token_url', '')
        client_id = auth_config.get('client_id', '')
        client_secret = auth_config.get('client_secret', '')
        
        response = await self.http_client.post(
            token_url,
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token', '')
            expires_in = token_data.get('expires_in', 3600)
            
            # Cache token
            if self.redis_client and access_token:
                await self.redis_client.setex(
                    token_key,
                    expires_in - 60,  # Expire 1 minute early
                    access_token
                )
                
            return access_token
            
        return ''
        
    def _generate_signature(self, secret: str, payload: str) -> str:
        """Generate HMAC-SHA256 signature"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
        
    def _update_metrics(self, response_time: float, status_code: int):
        """Update performance metrics"""
        self.metrics['total_deliveries'] += 1
        
        # Update average response time
        current_avg = self.metrics['average_response_time']
        total = self.metrics['total_deliveries']
        self.metrics['average_response_time'] = (
            (current_avg * (total - 1) + response_time) / total
        )
        
    async def get_webhook_status(self, webhook_id: str) -> Dict:
        """Get webhook status and statistics"""
        if webhook_id not in self.webhooks:
            return {}
            
        webhook = self.webhooks[webhook_id]
        
        # Count deliveries
        total_deliveries = sum(
            1 for d in self.deliveries.values()
            if d.webhook_id == webhook_id
        )
        
        successful_deliveries = sum(
            1 for d in self.deliveries.values()
            if d.webhook_id == webhook_id and d.status == WebhookStatus.DELIVERED
        )
        
        failed_deliveries = sum(
            1 for d in self.deliveries.values()
            if d.webhook_id == webhook_id and d.status == WebhookStatus.FAILED
        )
        
        return {
            'webhook_id': webhook_id,
            'url': webhook.url,
            'active': webhook.active,
            'events': [e.value for e in webhook.events],
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'success_rate': (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
            'created_at': webhook.created_at.isoformat(),
            'updated_at': webhook.updated_at.isoformat()
        }
        
    async def get_delivery_history(
        self,
        webhook_id: Optional[str] = None,
        event: Optional[WebhookEvent] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get webhook delivery history"""
        deliveries = []
        
        for delivery in self.deliveries.values():
            if webhook_id and delivery.webhook_id != webhook_id:
                continue
            if event and delivery.event != event:
                continue
            if status and delivery.status != status:
                continue
                
            deliveries.append(delivery.to_dict())
            
            if len(deliveries) >= limit:
                break
                
        # Sort by created_at descending
        deliveries.sort(key=lambda d: d['created_at'], reverse=True)
        
        return deliveries
        
    async def test_webhook(self, webhook_id: str) -> Dict:
        """Test a webhook with sample payload"""
        if webhook_id not in self.webhooks:
            return {'error': 'Webhook not found'}
            
        # Create test payload
        test_payload = {
            'test': True,
            'message': 'This is a test webhook delivery',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Create test delivery
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            webhook_id=webhook_id,
            event=WebhookEvent.SYSTEM_ALERT,
            payload=test_payload,
            status=WebhookStatus.PENDING
        )
        
        # Deliver immediately
        await self._deliver_webhook(delivery)
        
        return {
            'delivery_id': delivery.id,
            'status': delivery.status.value,
            'response_code': delivery.response_code,
            'response_body': delivery.response_body,
            'error': delivery.error
        }

# Third-party integration handlers
class IntegrationHandlers:
    """Handlers for specific third-party integrations"""
    
    @staticmethod
    async def slack_handler(webhook_url: str, event: WebhookEvent, payload: Dict):
        """Format and send to Slack"""
        slack_message = {
            'text': f"Event: {event.value}",
            'attachments': [{
                'color': 'good' if 'completed' in event.value else 'warning',
                'fields': [
                    {'title': k, 'value': str(v), 'short': True}
                    for k, v in payload.items()
                ][:5]  # Limit fields
            }]
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=slack_message)
            
    @staticmethod
    async def teams_handler(webhook_url: str, event: WebhookEvent, payload: Dict):
        """Format and send to Microsoft Teams"""
        teams_message = {
            '@type': 'MessageCard',
            '@context': 'https://schema.org/extensions',
            'title': f"Event: {event.value}",
            'sections': [{
                'facts': [
                    {'name': k, 'value': str(v)}
                    for k, v in payload.items()
                ][:10]  # Limit facts
            }]
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=teams_message)
            
    @staticmethod
    async def discord_handler(webhook_url: str, event: WebhookEvent, payload: Dict):
        """Format and send to Discord"""
        discord_message = {
            'content': f"**Event:** {event.value}",
            'embeds': [{
                'title': 'Event Details',
                'fields': [
                    {'name': k, 'value': str(v)[:100], 'inline': True}
                    for k, v in payload.items()
                ][:25]  # Discord limit
            }]
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=discord_message)

# Usage example
import base64

async def demo_webhooks():
    """Demonstrate webhook system"""
    system = WebhookIntegrationSystem()
    await system.initialize()
    
    # Create webhook
    webhook_id = await system.create_webhook(
        url="https://example.com/webhook",
        events=[
            WebhookEvent.TRANSCRIPTION_COMPLETED,
            WebhookEvent.ANALYSIS_COMPLETED
        ],
        auth_type=AuthType.BEARER,
        auth_config={'token': 'secret-token-123'}
    )
    
    print(f"Created webhook: {webhook_id}")
    
    # Trigger event
    await system.trigger_event(
        WebhookEvent.TRANSCRIPTION_COMPLETED,
        {
            'transcription_id': 'trans_123',
            'duration': 180,
            'word_count': 500,
            'language': 'en'
        }
    )
    
    # Get status
    status = await system.get_webhook_status(webhook_id)
    print(f"Webhook status: {status}")
    
    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_webhooks())