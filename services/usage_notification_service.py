#!/usr/bin/env python3
"""
Usage Notification Service
Sends alerts and notifications for usage thresholds
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session
from database.models import User, Notification
from database.subscription_models import UsageRecord, Subscription
from services.usage_analytics_service import UsageAnalyticsService
from auth.email_service import EmailService

logger = logging.getLogger(__name__)

class UsageNotificationService:
    """Service for usage notifications and alerts"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.analytics_service = UsageAnalyticsService(db_session_factory)
        self.email_service = EmailService()
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def check_and_send_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Check usage and send alerts if needed"""
        sent_alerts = []
        
        # Get usage alerts
        alerts = self.analytics_service.get_usage_alerts(user_id)
        
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return sent_alerts
            
            for alert in alerts:
                # Check if similar alert was sent recently (within 24 hours)
                recent_notification = db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.type == 'usage_alert',
                    Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).first()
                
                if recent_notification:
                    # Check if it's the same alert type
                    if recent_notification.data and recent_notification.data.get('usage_type') == alert['usage_type']:
                        continue  # Skip this alert
                
                # Send notification
                if self._send_usage_alert(user, alert):
                    # Create notification record
                    notification = Notification(
                        user_id=user_id,
                        type='usage_alert',
                        title=f"Usage Alert: {alert['usage_type'].title()}",
                        message=alert['message'],
                        data=alert,
                        priority=alert['severity']
                    )
                    db.add(notification)
                    sent_alerts.append(alert)
            
            db.commit()
            
        finally:
            db.close()
        
        return sent_alerts
    
    def _send_usage_alert(self, user: User, alert: Dict[str, Any]) -> bool:
        """Send usage alert to user"""
        try:
            # Prepare email content
            subject = f"Usage Alert: {alert['usage_type'].title()}"
            
            if alert['type'] == 'usage_warning':
                body = f"""
                <h2>Usage Warning</h2>
                <p>Hello {user.full_name or user.username},</p>
                
                <p>You are projected to exceed your {alert['usage_type']} limit this month.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>{alert['usage_type'].title()}</h3>
                    <p><strong>Current Usage:</strong> {alert['current_usage']:.0f}</p>
                    <p><strong>Projected Usage:</strong> {alert['projected_usage']:.0f}</p>
                    <p><strong>Monthly Limit:</strong> {alert['limit']}</p>
                    <p><strong>Projected:</strong> {alert['projected_usage'] / alert['limit'] * 100:.0f}% of limit</p>
                </div>
                
                <p>To avoid service interruption, consider:</p>
                <ul>
                    <li>Upgrading your subscription plan</li>
                    <li>Optimizing your usage</li>
                    <li>Purchasing additional capacity</li>
                </ul>
                
                <p><a href="{self._get_app_url()}/subscription" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Manage Subscription</a></p>
                """
            
            elif alert['type'] == 'limit_approaching':
                body = f"""
                <h2>Approaching Usage Limit</h2>
                <p>Hello {user.full_name or user.username},</p>
                
                <p>At your current usage rate, you will reach your {alert['usage_type']} limit in <strong>{alert['days_remaining']} days</strong>.</p>
                
                <p>Consider upgrading your plan to ensure uninterrupted service.</p>
                
                <p><a href="{self._get_app_url()}/subscription" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Plans</a></p>
                """
            
            else:
                body = f"<p>{alert['message']}</p>"
            
            # Send email
            return self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send usage alert: {e}")
            return False
    
    def send_usage_summary(
        self,
        user_id: int,
        period: str = 'monthly'
    ) -> bool:
        """Send usage summary report"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Generate report
            if period == 'monthly':
                start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
                end_date = datetime.utcnow()
                period_name = start_date.strftime('%B %Y')
            else:  # weekly
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)
                period_name = f"Week of {start_date.strftime('%b %d, %Y')}"
            
            report = self.analytics_service.generate_usage_report(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format email
            subject = f"Your {period_name} Usage Summary"
            
            usage_html = ""
            for usage_type, data in report['usage_summary'].items():
                usage_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{usage_type.title()}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{data['total_quantity']:.0f}</td>
                </tr>
                """
            
            body = f"""
            <h2>{period_name} Usage Summary</h2>
            <p>Hello {user.full_name or user.username},</p>
            
            <p>Here's your usage summary for {period_name}:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; text-align: left;">Metric</th>
                        <th style="padding: 10px; text-align: left;">Usage</th>
                    </tr>
                </thead>
                <tbody>
                    {usage_html}
                </tbody>
            </table>
            
            <p><a href="{self._get_app_url()}/usage" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Detailed Analytics</a></p>
            
            <p>Thank you for using our service!</p>
            """
            
            # Send email
            success = self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_body=body
            )
            
            if success:
                # Create notification record
                notification = Notification(
                    user_id=user_id,
                    type='usage_summary',
                    title=subject,
                    message=f"Your {period} usage summary is available",
                    data={'report_id': report.get('report_id')}
                )
                db.add(notification)
                db.commit()
            
            return success
            
        finally:
            db.close()
    
    def send_limit_exceeded_notification(
        self,
        user_id: int,
        usage_type: str,
        current_usage: float,
        limit: float
    ) -> bool:
        """Send notification when limit is exceeded"""
        db = self._get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Create notification
            notification = Notification(
                user_id=user_id,
                type='limit_exceeded',
                title=f"{usage_type.title()} Limit Exceeded",
                message=f"You have exceeded your {usage_type} limit ({current_usage:.0f}/{limit})",
                priority='high',
                data={
                    'usage_type': usage_type,
                    'current_usage': current_usage,
                    'limit': limit
                }
            )
            db.add(notification)
            db.commit()
            
            # Send email
            subject = f"Action Required: {usage_type.title()} Limit Exceeded"
            body = f"""
            <h2>Usage Limit Exceeded</h2>
            <p>Hello {user.full_name or user.username},</p>
            
            <p style="color: #dc3545;"><strong>You have exceeded your {usage_type} limit.</strong></p>
            
            <div style="background-color: #f8d7da; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Usage Type:</strong> {usage_type.title()}</p>
                <p><strong>Current Usage:</strong> {current_usage:.0f}</p>
                <p><strong>Monthly Limit:</strong> {limit}</p>
                <p><strong>Overage:</strong> {current_usage - limit:.0f}</p>
            </div>
            
            <p><strong>Immediate Action Required:</strong></p>
            <ul>
                <li>Upgrade your subscription to continue using this service</li>
                <li>Or wait until next billing cycle for limit reset</li>
            </ul>
            
            <p><a href="{self._get_app_url()}/subscription" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Upgrade Now</a></p>
            """
            
            return self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_body=body
            )
            
        finally:
            db.close()
    
    def schedule_periodic_summaries(self):
        """Schedule periodic usage summaries for all users"""
        db = self._get_db()
        try:
            # Get all active users with subscriptions
            users = db.query(User).join(
                Subscription,
                User.id == Subscription.user_id
            ).filter(
                Subscription.status.in_(['active', 'trialing']),
                User.is_active == True
            ).all()
            
            sent_count = 0
            for user in users:
                # Check if monthly summary should be sent (on 1st of month)
                if datetime.utcnow().day == 1:
                    if self.send_usage_summary(user.id, 'monthly'):
                        sent_count += 1
                
                # Check for usage alerts
                alerts = self.check_and_send_alerts(user.id)
                if alerts:
                    logger.info(f"Sent {len(alerts)} alerts to user {user.id}")
            
            logger.info(f"Sent usage summaries to {sent_count} users")
            
        finally:
            db.close()
    
    def _get_app_url(self) -> str:
        """Get application URL"""
        import os
        return os.getenv('APP_URL', 'http://localhost:8501')