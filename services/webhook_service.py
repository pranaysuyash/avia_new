#!/usr/bin/env python3
"""
Webhook Service
Manages webhooks and event delivery
"""

import logging
import httpx
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.api_models import Webhook, WebhookLog, WebhookStatus
from database.models import User

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for managing webhooks and delivering events"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.valid_events = [
            # Transcript events
            "transcript.created",
            "transcript.updated",
            "transcript.deleted",
            "transcript.completed",
            "transcript.failed",
            "transcript.shared",
            
            # Team events
            "team.created",
            "team.updated",
            "team.deleted",
            "team.member.added",
            "team.member.removed",
            "team.member.updated",
            
            # Usage events
            "usage.limit.warning",
            "usage.limit.exceeded",
            "usage.quota.reset",
            
            # Subscription events
            "subscription.created",
            "subscription.updated",
            "subscription.cancelled",
            "subscription.expired",
            
            # Payment events
            "payment.succeeded",
            "payment.failed",
            
            # API events
            "api_key.created",
            "api_key.revoked",
            "api_key.usage.warning"
        ]
    
    def get_valid_events(self) -> List[str]:
        """Get list of valid webhook events"""
        return self.valid_events
    
    def create_webhook(
        self,
        user_id: int,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        api_key_id: Optional[int] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Create a new webhook"""
        try:
            # Generate secret if not provided
            if not secret:
                secret = Webhook.generate_secret()
            
            webhook = Webhook(
                user_id=user_id,
                api_key_id=api_key_id,
                name=name,
                url=url,
                secret=secret,
                events=events,
                custom_headers=custom_headers or {},
                max_retries=max_retries,
                timeout_seconds=timeout_seconds
            )
            
            self.db.add(webhook)
            self.db.commit()
            self.db.refresh(webhook)
            
            return {
                'id': webhook.id,
                'name': webhook.name,
                'url': webhook.url,
                'events': webhook.events,
                'secret': secret,  # Only returned on creation
                'status': webhook.status.value,
                'success_count': 0,
                'failure_count': 0,
                'created_at': webhook.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create webhook: {e}")
            self.db.rollback()
            raise
    
    def list_webhooks(
        self,
        user_id: int,
        api_key_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """List user's webhooks"""
        query = self.db.query(Webhook).filter(
            Webhook.user_id == user_id
        )
        
        if api_key_id:
            query = query.filter(Webhook.api_key_id == api_key_id)
        
        if not include_inactive:
            query = query.filter(Webhook.status == WebhookStatus.ACTIVE)
        
        webhooks = query.order_by(Webhook.created_at.desc()).all()
        
        return [
            {
                'id': w.id,
                'name': w.name,
                'url': w.url,
                'events': w.events,
                'status': w.status.value,
                'last_triggered_at': w.last_triggered_at.isoformat() if w.last_triggered_at else None,
                'success_count': w.success_count,
                'failure_count': w.failure_count,
                'created_at': w.created_at.isoformat()
            }
            for w in webhooks
        ]
    
    def get_webhook(
        self,
        webhook_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get webhook details"""
        webhook = self.db.query(Webhook).filter(
            and_(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            )
        ).first()
        
        if not webhook:
            return None
        
        # Get recent logs
        recent_logs = self.db.query(WebhookLog).filter(
            WebhookLog.webhook_id == webhook_id
        ).order_by(WebhookLog.delivered_at.desc()).limit(10).all()
        
        return {
            'id': webhook.id,
            'name': webhook.name,
            'url': webhook.url,
            'events': webhook.events,
            'status': webhook.status.value,
            'custom_headers': webhook.custom_headers,
            'max_retries': webhook.max_retries,
            'timeout_seconds': webhook.timeout_seconds,
            'last_triggered_at': webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
            'last_success_at': webhook.last_success_at.isoformat() if webhook.last_success_at else None,
            'last_failure_at': webhook.last_failure_at.isoformat() if webhook.last_failure_at else None,
            'success_count': webhook.success_count,
            'failure_count': webhook.failure_count,
            'created_at': webhook.created_at.isoformat(),
            'recent_deliveries': [
                {
                    'id': log.id,
                    'event_type': log.event_type,
                    'status_code': log.status_code,
                    'response_time_ms': log.response_time_ms,
                    'error_message': log.error_message,
                    'delivered_at': log.delivered_at.isoformat()
                }
                for log in recent_logs
            ]
        }
    
    def update_webhook(
        self,
        webhook_id: int,
        user_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        status: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None
    ) -> bool:
        """Update webhook settings"""
        webhook = self.db.query(Webhook).filter(
            and_(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            )
        ).first()
        
        if not webhook:
            return False
        
        # Update fields
        if name is not None:
            webhook.name = name
        if url is not None:
            webhook.url = url
        if events is not None:
            webhook.events = events
        if status is not None:
            webhook.status = WebhookStatus(status)
        if custom_headers is not None:
            webhook.custom_headers = custom_headers
        if max_retries is not None:
            webhook.max_retries = max_retries
        if timeout_seconds is not None:
            webhook.timeout_seconds = timeout_seconds
        
        webhook.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    def delete_webhook(
        self,
        webhook_id: int,
        user_id: int
    ) -> bool:
        """Delete a webhook"""
        webhook = self.db.query(Webhook).filter(
            and_(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            )
        ).first()
        
        if not webhook:
            return False
        
        self.db.delete(webhook)
        self.db.commit()
        
        return True
    
    async def trigger_event(
        self,
        event_type: str,
        user_id: int,
        event_data: Dict[str, Any],
        event_id: Optional[str] = None
    ):
        """Trigger webhook event for all matching webhooks"""
        # Find all active webhooks that listen for this event
        webhooks = self.db.query(Webhook).filter(
            and_(
                Webhook.user_id == user_id,
                Webhook.status == WebhookStatus.ACTIVE,
                Webhook.events.contains([event_type])
            )
        ).all()
        
        # Send to each webhook
        for webhook in webhooks:
            await self._deliver_event(
                webhook=webhook,
                event_type=event_type,
                event_data=event_data,
                event_id=event_id
            )
    
    async def _deliver_event(
        self,
        webhook: Webhook,
        event_type: str,
        event_data: Dict[str, Any],
        event_id: Optional[str] = None,
        attempt_number: int = 1
    ):
        """Deliver event to a webhook"""
        # Prepare payload
        payload = {
            'id': event_id or f"evt_{datetime.utcnow().timestamp()}",
            'type': event_type,
            'created': datetime.utcnow().isoformat(),
            'data': event_data
        }
        
        payload_json = json.dumps(payload)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TranscriptionPlatform/1.0',
            'X-Webhook-Event': event_type,
            'X-Webhook-ID': str(webhook.id),
            'X-Webhook-Signature': webhook.compute_signature(payload_json)
        }
        
        # Add custom headers
        if webhook.custom_headers:
            headers.update(webhook.custom_headers)
        
        # Create log entry
        log = WebhookLog(
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=payload['id'],
            payload=payload,
            attempt_number=attempt_number
        )
        
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout_seconds
                )
                
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                log.status_code = response.status_code
                log.response_body = response.text[:1000]  # Store first 1000 chars
                log.response_time_ms = int(response_time)
                
                if response.status_code >= 200 and response.status_code < 300:
                    # Success
                    webhook.last_triggered_at = datetime.utcnow()
                    webhook.last_success_at = datetime.utcnow()
                    webhook.success_count += 1
                    
                    self.db.add(log)
                    self.db.commit()
                    
                    logger.info(f"Webhook {webhook.id} delivered successfully")
                    
                else:
                    # HTTP error
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            # Delivery failed
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            log.error_message = str(e)
            log.response_time_ms = int(response_time)
            
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_failure_at = datetime.utcnow()
            webhook.failure_count += 1
            
            # Check if we should retry
            if attempt_number < webhook.max_retries:
                # Schedule retry
                retry_delay = webhook.retry_delay_seconds * attempt_number
                log.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                # Schedule retry (in production, use a task queue)
                asyncio.create_task(
                    self._retry_delivery(
                        webhook=webhook,
                        event_type=event_type,
                        event_data=event_data,
                        event_id=event_id,
                        attempt_number=attempt_number + 1,
                        delay=retry_delay
                    )
                )
            
            else:
                # Max retries reached, mark webhook as failed
                if webhook.failure_count >= 10:
                    webhook.status = WebhookStatus.FAILED
                    logger.error(f"Webhook {webhook.id} marked as failed after 10 failures")
            
            self.db.add(log)
            self.db.commit()
            
            logger.error(f"Webhook {webhook.id} delivery failed: {e}")
    
    async def _retry_delivery(
        self,
        webhook: Webhook,
        event_type: str,
        event_data: Dict[str, Any],
        event_id: str,
        attempt_number: int,
        delay: int
    ):
        """Retry webhook delivery after delay"""
        await asyncio.sleep(delay)
        
        await self._deliver_event(
            webhook=webhook,
            event_type=event_type,
            event_data=event_data,
            event_id=event_id,
            attempt_number=attempt_number
        )
    
    async def send_test_event(
        self,
        webhook_id: int,
        user_id: int
    ) -> Optional[bool]:
        """Send a test event to webhook"""
        webhook = self.db.query(Webhook).filter(
            and_(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            )
        ).first()
        
        if not webhook:
            return None
        
        # Send test event
        test_data = {
            'test': True,
            'message': 'This is a test webhook event',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self._deliver_event(
            webhook=webhook,
            event_type='test.webhook',
            event_data=test_data,
            event_id=f"test_{datetime.utcnow().timestamp()}"
        )
        
        return True
    
    def get_delivery_logs(
        self,
        webhook_id: int,
        user_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery logs"""
        # Verify ownership
        webhook = self.db.query(Webhook).filter(
            and_(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            )
        ).first()
        
        if not webhook:
            return []
        
        logs = self.db.query(WebhookLog).filter(
            WebhookLog.webhook_id == webhook_id
        ).order_by(WebhookLog.delivered_at.desc()).limit(limit).all()
        
        return [
            {
                'id': log.id,
                'event_type': log.event_type,
                'event_id': log.event_id,
                'attempt_number': log.attempt_number,
                'status_code': log.status_code,
                'response_time_ms': log.response_time_ms,
                'error_message': log.error_message,
                'delivered_at': log.delivered_at.isoformat(),
                'next_retry_at': log.next_retry_at.isoformat() if log.next_retry_at else None
            }
            for log in logs
        ]
    
    def cleanup_old_logs(self, retention_days: int = 30):
        """Clean up old webhook logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted = self.db.query(WebhookLog).filter(
            WebhookLog.delivered_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Cleaned up {deleted} old webhook logs")
        
        return deleted