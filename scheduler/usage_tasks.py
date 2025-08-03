#!/usr/bin/env python3
"""
Scheduled Usage Tasks
Periodic tasks for usage tracking and notifications
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from database.connection import SessionLocal
from services.usage_notification_service import UsageNotificationService
from services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class UsageScheduler:
    """Scheduler for usage-related tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notification_service = UsageNotificationService(SessionLocal)
        self.subscription_service = SubscriptionService(SessionLocal)
    
    def start(self):
        """Start the scheduler"""
        # Daily usage check at 9 AM
        self.scheduler.add_job(
            func=self.check_daily_usage,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_usage_check',
            name='Check daily usage and send alerts',
            replace_existing=True
        )
        
        # Weekly summary on Mondays at 10 AM
        self.scheduler.add_job(
            func=self.send_weekly_summaries,
            trigger=CronTrigger(day_of_week='mon', hour=10, minute=0),
            id='weekly_summaries',
            name='Send weekly usage summaries',
            replace_existing=True
        )
        
        # Monthly summary on 1st of month at 10 AM
        self.scheduler.add_job(
            func=self.send_monthly_summaries,
            trigger=CronTrigger(day=1, hour=10, minute=0),
            id='monthly_summaries',
            name='Send monthly usage summaries',
            replace_existing=True
        )
        
        # Reset monthly counters on 1st of month at midnight
        self.scheduler.add_job(
            func=self.reset_monthly_counters,
            trigger=CronTrigger(day=1, hour=0, minute=0),
            id='reset_counters',
            name='Reset monthly usage counters',
            replace_existing=True
        )
        
        # Cleanup old usage records monthly
        self.scheduler.add_job(
            func=self.cleanup_old_records,
            trigger=CronTrigger(day=15, hour=2, minute=0),
            id='cleanup_records',
            name='Cleanup old usage records',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Usage scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Usage scheduler stopped")
    
    def check_daily_usage(self):
        """Check all users' usage and send alerts"""
        logger.info("Running daily usage check...")
        
        try:
            self.notification_service.schedule_periodic_summaries()
            logger.info("Daily usage check completed")
        except Exception as e:
            logger.error(f"Daily usage check failed: {e}")
    
    def send_weekly_summaries(self):
        """Send weekly usage summaries"""
        logger.info("Sending weekly summaries...")
        
        db = SessionLocal()
        try:
            from database.models import User
            from database.subscription_models import Subscription
            
            # Get users with weekly summary enabled
            users = db.query(User).filter(
                User.is_active == True,
                User.preferences['usage_alerts']['weekly_summary'] == True
            ).all()
            
            sent_count = 0
            for user in users:
                try:
                    if self.notification_service.send_usage_summary(user.id, 'weekly'):
                        sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send weekly summary to user {user.id}: {e}")
            
            logger.info(f"Sent {sent_count} weekly summaries")
            
        finally:
            db.close()
    
    def send_monthly_summaries(self):
        """Send monthly usage summaries"""
        logger.info("Sending monthly summaries...")
        
        db = SessionLocal()
        try:
            from database.models import User
            from database.subscription_models import Subscription
            
            # Get all active users with subscriptions
            users = db.query(User).join(
                Subscription,
                User.id == Subscription.user_id
            ).filter(
                User.is_active == True,
                Subscription.status.in_(['active', 'trialing'])
            ).all()
            
            sent_count = 0
            for user in users:
                try:
                    if self.notification_service.send_usage_summary(user.id, 'monthly'):
                        sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send monthly summary to user {user.id}: {e}")
            
            logger.info(f"Sent {sent_count} monthly summaries")
            
        finally:
            db.close()
    
    def reset_monthly_counters(self):
        """Reset monthly usage counters for subscriptions"""
        logger.info("Resetting monthly usage counters...")
        
        db = SessionLocal()
        try:
            from database.subscription_models import Subscription, SubscriptionStatus
            
            # Reset counters for active subscriptions
            subscriptions = db.query(Subscription).filter(
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING
                ])
            ).all()
            
            for subscription in subscriptions:
                subscription.transcripts_used = 0
                subscription.minutes_used = 0
                subscription.api_calls_used = 0
                # Note: storage_used_gb is not reset as it's cumulative
            
            db.commit()
            logger.info(f"Reset counters for {len(subscriptions)} subscriptions")
            
        except Exception as e:
            logger.error(f"Failed to reset counters: {e}")
            db.rollback()
        finally:
            db.close()
    
    def cleanup_old_records(self):
        """Cleanup old usage records"""
        logger.info("Cleaning up old usage records...")
        
        db = SessionLocal()
        try:
            from database.subscription_models import UsageRecord
            from datetime import timedelta
            
            # Keep records for 6 months
            cutoff_date = datetime.utcnow() - timedelta(days=180)
            
            # Delete old records
            deleted_count = db.query(UsageRecord).filter(
                UsageRecord.created_at < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Deleted {deleted_count} old usage records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup records: {e}")
            db.rollback()
        finally:
            db.close()

# Global scheduler instance
usage_scheduler = UsageScheduler()

def start_usage_scheduler():
    """Start the usage scheduler"""
    usage_scheduler.start()

def stop_usage_scheduler():
    """Stop the usage scheduler"""
    usage_scheduler.stop()