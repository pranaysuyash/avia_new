"""
GraphQL Subscription Manager
Manages real-time subscriptions and event publishing
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, AsyncGenerator, Set, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import weakref

from api.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Subscription metadata"""
    id: str
    subscription_type: str
    user_id: Optional[int]
    filters: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()


@dataclass
class SubscriptionEvent:
    """Event to be published to subscriptions"""
    event_type: str
    data: Dict[str, Any]
    user_id: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SubscriptionManager:
    """
    Manages GraphQL subscriptions and real-time event publishing
    Uses Redis for distributed subscription management across multiple servers
    """
    
    def __init__(self):
        self.active_subscriptions: Dict[str, Subscription] = {}
        self.subscription_queues: Dict[str, asyncio.Queue] = {}
        self.user_subscriptions: Dict[int, Set[str]] = {}
        self.type_subscriptions: Dict[str, Set[str]] = {}
        
        # Redis channels for different subscription types
        self.redis_channels = {
            "transcription_status": "graphql:transcription:*",
            "system_metrics": "graphql:system:metrics",
            "user_notifications": "graphql:notifications:*",
            "cache_updates": "graphql:cache:updates",
            "backup_status": "graphql:backup:status",
            "rate_limit_alerts": "graphql:ratelimit:alerts"
        }
        
        # Background tasks
        self._cleanup_task = None
        self._redis_listener_task = None
        self._metrics_publisher_task = None
        
        # Start background services
        self._start_background_services()
    
    def _start_background_services(self):
        """Start background services for subscription management"""
        
        # Cleanup inactive subscriptions
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_subscriptions())
        
        # Listen to Redis pub/sub for distributed events
        self._redis_listener_task = asyncio.create_task(self._redis_event_listener())
        
        # Publish system metrics periodically
        self._metrics_publisher_task = asyncio.create_task(self._system_metrics_publisher())
    
    async def subscribe(
        self, 
        subscription_type: str, 
        user_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new subscription
        
        Args:
            subscription_type: Type of subscription (e.g., 'transcription_status')
            user_id: Optional user ID for user-specific subscriptions
            filters: Optional filters for the subscription
        
        Returns:
            Subscription ID
        """
        
        subscription_id = str(uuid.uuid4())
        
        subscription = Subscription(
            id=subscription_id,
            subscription_type=subscription_type,
            user_id=user_id,
            filters=filters
        )
        
        # Store subscription
        self.active_subscriptions[subscription_id] = subscription
        
        # Create event queue for this subscription
        self.subscription_queues[subscription_id] = asyncio.Queue(maxsize=1000)
        
        # Index by user ID
        if user_id:
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(subscription_id)
        
        # Index by subscription type
        if subscription_type not in self.type_subscriptions:
            self.type_subscriptions[subscription_type] = set()
        self.type_subscriptions[subscription_type].add(subscription_id)
        
        # Subscribe to Redis channel if using Redis
        if redis_cache.is_connected():
            await self._subscribe_redis_channel(subscription_type, subscription_id)
        
        logger.info(f"Created subscription {subscription_id} for type {subscription_type}")
        
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str):
        """Remove a subscription"""
        
        if subscription_id not in self.active_subscriptions:
            return
        
        subscription = self.active_subscriptions[subscription_id]
        
        # Remove from indexes
        if subscription.user_id and subscription.user_id in self.user_subscriptions:
            self.user_subscriptions[subscription.user_id].discard(subscription_id)
            
            # Clean up empty user subscription sets
            if not self.user_subscriptions[subscription.user_id]:
                del self.user_subscriptions[subscription.user_id]
        
        if subscription.subscription_type in self.type_subscriptions:
            self.type_subscriptions[subscription.subscription_type].discard(subscription_id)
            
            # Clean up empty type subscription sets
            if not self.type_subscriptions[subscription.subscription_type]:
                del self.type_subscriptions[subscription.subscription_type]
        
        # Unsubscribe from Redis channel
        if redis_cache.is_connected():
            await self._unsubscribe_redis_channel(subscription.subscription_type, subscription_id)
        
        # Clean up subscription data
        del self.active_subscriptions[subscription_id]
        
        if subscription_id in self.subscription_queues:
            # Signal end of queue
            try:
                await self.subscription_queues[subscription_id].put(None)
            except asyncio.QueueFull:
                pass
            del self.subscription_queues[subscription_id]
        
        logger.info(f"Removed subscription {subscription_id}")
    
    async def get_updates(self, subscription_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get real-time updates for a subscription
        
        Args:
            subscription_id: Subscription ID
            
        Yields:
            Event data dictionaries
        """
        
        if subscription_id not in self.subscription_queues:
            logger.warning(f"No queue found for subscription {subscription_id}")
            return
        
        queue = self.subscription_queues[subscription_id]
        subscription = self.active_subscriptions.get(subscription_id)
        
        if not subscription:
            logger.warning(f"No subscription found for ID {subscription_id}")
            return
        
        try:
            while True:
                # Update last activity
                subscription.last_activity = datetime.utcnow()
                
                # Get event from queue (blocks until available)
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"type": "keepalive", "timestamp": datetime.utcnow().isoformat()}
                    continue
                
                # None signals end of subscription
                if event is None:
                    break
                
                yield event
                
        except asyncio.CancelledError:
            logger.info(f"Subscription {subscription_id} cancelled")
        except Exception as e:
            logger.error(f"Error in subscription {subscription_id}: {e}")
        finally:
            # Clean up when generator exits
            await self.unsubscribe(subscription_id)
    
    async def publish_event(self, event: SubscriptionEvent):
        """
        Publish an event to relevant subscriptions
        
        Args:
            event: Event to publish
        """
        
        # Get subscriptions that should receive this event
        target_subscriptions = self._get_target_subscriptions(event)
        
        # Prepare event data
        event_data = {
            "type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }
        
        # Send to local subscriptions
        for subscription_id in target_subscriptions:
            if subscription_id in self.subscription_queues:
                try:
                    await self.subscription_queues[subscription_id].put(event_data)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for subscription {subscription_id}, dropping event")
        
        # Publish to Redis for other server instances
        if redis_cache.is_connected():
            await self._publish_to_redis(event)
        
        logger.debug(f"Published event {event.event_type} to {len(target_subscriptions)} subscriptions")
    
    def _get_target_subscriptions(self, event: SubscriptionEvent) -> Set[str]:
        """Get subscription IDs that should receive the event"""
        
        target_subscriptions = set()
        
        # Find subscriptions by type
        subscription_type = self._map_event_to_subscription_type(event.event_type)
        if subscription_type in self.type_subscriptions:
            for subscription_id in self.type_subscriptions[subscription_type]:
                subscription = self.active_subscriptions.get(subscription_id)
                if subscription and self._matches_filters(subscription, event):
                    target_subscriptions.add(subscription_id)
        
        # Find user-specific subscriptions
        if event.user_id and event.user_id in self.user_subscriptions:
            for subscription_id in self.user_subscriptions[event.user_id]:
                subscription = self.active_subscriptions.get(subscription_id)
                if subscription and self._matches_filters(subscription, event):
                    target_subscriptions.add(subscription_id)
        
        return target_subscriptions
    
    def _map_event_to_subscription_type(self, event_type: str) -> str:
        """Map event type to subscription type"""
        
        mapping = {
            "transcription_job": "transcription_status",
            "system_metrics": "system_metrics",
            "notification": "user_notifications",
            "cache_stats": "cache_updates",
            "backup_info": "backup_status",
            "rate_limit_alert": "rate_limit_alerts"
        }
        
        return mapping.get(event_type, event_type)
    
    def _matches_filters(self, subscription: Subscription, event: SubscriptionEvent) -> bool:
        """Check if event matches subscription filters"""
        
        if not subscription.filters:
            return True
        
        # User-specific filtering
        if subscription.user_id and event.user_id:
            if subscription.user_id != event.user_id:
                return False
        
        # Job ID filtering for transcription events
        if event.event_type == "transcription_job":
            job_ids = subscription.filters.get("job_ids")
            if job_ids and event.data.get("id") not in job_ids:
                return False
        
        # Custom filter matching
        event_filters = event.filters or {}
        for key, value in subscription.filters.items():
            if key in event_filters and event_filters[key] != value:
                return False
        
        return True
    
    async def _subscribe_redis_channel(self, subscription_type: str, subscription_id: str):
        """Subscribe to Redis pub/sub channel"""
        
        if subscription_type in self.redis_channels:
            channel = self.redis_channels[subscription_type]
            try:
                # Note: Actual Redis pub/sub implementation would go here
                # For now, we'll use a placeholder
                logger.debug(f"Would subscribe to Redis channel {channel} for {subscription_id}")
            except Exception as e:
                logger.error(f"Failed to subscribe to Redis channel {channel}: {e}")
    
    async def _unsubscribe_redis_channel(self, subscription_type: str, subscription_id: str):
        """Unsubscribe from Redis pub/sub channel"""
        
        if subscription_type in self.redis_channels:
            channel = self.redis_channels[subscription_type]
            try:
                # Note: Actual Redis pub/sub implementation would go here
                logger.debug(f"Would unsubscribe from Redis channel {channel} for {subscription_id}")
            except Exception as e:
                logger.error(f"Failed to unsubscribe from Redis channel {channel}: {e}")
    
    async def _publish_to_redis(self, event: SubscriptionEvent):
        """Publish event to Redis for distribution to other servers"""
        
        subscription_type = self._map_event_to_subscription_type(event.event_type)
        
        if subscription_type in self.redis_channels:
            channel = self.redis_channels[subscription_type]
            
            try:
                event_data = {
                    "event_type": event.event_type,
                    "data": event.data,
                    "user_id": event.user_id,
                    "filters": event.filters,
                    "timestamp": event.timestamp.isoformat()
                }
                
                await redis_cache.client.publish(channel, json.dumps(event_data))
                logger.debug(f"Published event to Redis channel {channel}")
                
            except Exception as e:
                logger.error(f"Failed to publish to Redis channel {channel}: {e}")
    
    async def _redis_event_listener(self):
        """Listen for events from Redis pub/sub"""
        
        if not redis_cache.is_connected():
            return
        
        try:
            pubsub = redis_cache.client.pubsub()
            
            # Subscribe to all channels
            for channel in self.redis_channels.values():
                await pubsub.subscribe(channel)
            
            logger.info("Started Redis event listener")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        
                        # Reconstruct event
                        event = SubscriptionEvent(
                            event_type=event_data["event_type"],
                            data=event_data["data"],
                            user_id=event_data.get("user_id"),
                            filters=event_data.get("filters"),
                            timestamp=datetime.fromisoformat(event_data["timestamp"])
                        )
                        
                        # Process event locally (don't re-publish to avoid loops)
                        await self._process_redis_event(event)
                        
                    except Exception as e:
                        logger.error(f"Error processing Redis event: {e}")
                        
        except Exception as e:
            logger.error(f"Redis event listener error: {e}")
    
    async def _process_redis_event(self, event: SubscriptionEvent):
        """Process event received from Redis"""
        
        # Get local subscriptions that should receive this event
        target_subscriptions = self._get_target_subscriptions(event)
        
        # Prepare event data
        event_data = {
            "type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }
        
        # Send to local subscriptions only
        for subscription_id in target_subscriptions:
            if subscription_id in self.subscription_queues:
                try:
                    await self.subscription_queues[subscription_id].put(event_data)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for subscription {subscription_id}, dropping Redis event")
    
    async def _system_metrics_publisher(self):
        """Publish system metrics periodically"""
        
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                # Check if anyone is subscribed to system metrics
                if "system_metrics" in self.type_subscriptions and self.type_subscriptions["system_metrics"]:
                    
                    # Get system metrics (placeholder - would integrate with actual metrics)
                    metrics_data = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "cpu_usage": 45.2,  # Placeholder
                        "memory_usage": 68.7,
                        "disk_usage": 32.1,
                        "active_connections": len(self.active_subscriptions),
                        "request_rate": 127.5,
                        "error_rate": 0.02
                    }
                    
                    event = SubscriptionEvent(
                        event_type="system_metrics",
                        data=metrics_data
                    )
                    
                    await self.publish_event(event)
                    
            except Exception as e:
                logger.error(f"Error publishing system metrics: {e}")
    
    async def _cleanup_inactive_subscriptions(self):
        """Clean up inactive subscriptions periodically"""
        
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                current_time = datetime.utcnow()
                inactive_threshold = current_time - timedelta(hours=1)
                
                inactive_subscriptions = []
                
                for subscription_id, subscription in self.active_subscriptions.items():
                    if subscription.last_activity < inactive_threshold:
                        inactive_subscriptions.append(subscription_id)
                
                for subscription_id in inactive_subscriptions:
                    logger.info(f"Cleaning up inactive subscription {subscription_id}")
                    await self.unsubscribe(subscription_id)
                
                if inactive_subscriptions:
                    logger.info(f"Cleaned up {len(inactive_subscriptions)} inactive subscriptions")
                    
            except Exception as e:
                logger.error(f"Error cleaning up subscriptions: {e}")
    
    async def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics"""
        
        stats = {
            "total_subscriptions": len(self.active_subscriptions),
            "by_type": {},
            "by_user_count": len(self.user_subscriptions),
            "queue_sizes": {},
            "redis_connected": redis_cache.is_connected()
        }
        
        # Count by type
        for subscription_type, subscription_ids in self.type_subscriptions.items():
            stats["by_type"][subscription_type] = len(subscription_ids)
        
        # Queue sizes
        for subscription_id, queue in self.subscription_queues.items():
            stats["queue_sizes"][subscription_id] = queue.qsize()
        
        return stats
    
    async def shutdown(self):
        """Shutdown the subscription manager"""
        
        logger.info("Shutting down subscription manager")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._redis_listener_task:
            self._redis_listener_task.cancel()
        if self._metrics_publisher_task:
            self._metrics_publisher_task.cancel()
        
        # Close all subscriptions
        subscription_ids = list(self.active_subscriptions.keys())
        for subscription_id in subscription_ids:
            await self.unsubscribe(subscription_id)
        
        logger.info("Subscription manager shutdown complete")


# Global subscription manager instance
subscription_manager = SubscriptionManager()