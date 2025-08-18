"""
Marketing Service

Business logic for marketing and growth operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid
import hashlib

from database.models_extended import (
    Campaign, CampaignMetrics, EmailCampaign,
    ReferralProgram, Referral, ContentMarketing
)
from services.notification_service import NotificationService
from services.email_service import EmailService
from services.analytics_service import AnalyticsService
from marketing_growth_system import (
    ReferralSystem, EmailMarketingPlatform, MarketingAutomation,
    GrowthAnalytics, ABTestingEngine, ContentDistribution,
    CampaignType, CampaignStatus, Channel
)

class MarketingService:
    """Service for managing marketing and growth operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()
        self.analytics_service = AnalyticsService(db)
        
        # Initialize marketing systems
        self.referral_system = ReferralSystem()
        self.email_marketing = EmailMarketingPlatform()
        self.marketing_automation = MarketingAutomation()
        self.growth_analytics = GrowthAnalytics()
        self.ab_testing = ABTestingEngine()
        self.content_distribution = ContentDistribution()
    
    async def create_campaign(
        self,
        name: str,
        campaign_type: str,
        config: Dict[str, Any],
        user_id: str
    ) -> Campaign:
        """Create and launch marketing campaign"""
        # Map campaign type
        type_map = {
            "email": CampaignType.EMAIL,
            "social": CampaignType.SOCIAL,
            "content": CampaignType.CONTENT,
            "referral": CampaignType.REFERRAL,
            "paid": CampaignType.PAID_ADS
        }
        
        campaign_enum = type_map.get(campaign_type, CampaignType.EMAIL)
        
        # Create campaign record
        campaign = Campaign(
            id=str(uuid.uuid4()),
            name=name,
            type=campaign_type,
            description=config.get("description", ""),
            target_audience=config.get("target_audience", {}),
            budget=config.get("budget", 0),
            spent=0,
            start_date=config.get("start_date", datetime.utcnow()),
            end_date=config.get("end_date"),
            goals=config.get("goals", {}),
            created_by=user_id,
            status="draft"
        )
        
        self.db.add(campaign)
        
        # Initialize metrics
        metrics = CampaignMetrics(
            campaign_id=campaign.id,
            impressions=0,
            clicks=0,
            conversions=0,
            revenue=0
        )
        self.db.add(metrics)
        
        self.db.commit()
        
        # Setup campaign in marketing automation
        self.marketing_automation.create_campaign(
            campaign_id=campaign.id,
            campaign_type=campaign_enum,
            automation_rules=self._get_default_automation_rules(campaign_enum)
        )
        
        # Track analytics
        self.analytics_service.track_event("campaign_created", {
            "campaign_id": campaign.id,
            "type": campaign_type,
            "budget": campaign.budget,
            "user_id": user_id
        })
        
        return campaign
    
    async def launch_email_campaign(
        self,
        campaign_id: str,
        subject: str,
        content: Dict[str, str],
        segment: Dict[str, Any],
        schedule: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Launch email marketing campaign"""
        # Get campaign
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Create email campaign
        email_campaign = EmailCampaign(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            subject=subject,
            content_html=content.get("html", ""),
            content_text=content.get("text", ""),
            segment_filters=segment,
            send_time=schedule or datetime.utcnow()
        )
        
        self.db.add(email_campaign)
        
        # Get recipient list
        recipients = await self._get_email_recipients(segment)
        
        # Schedule or send immediately
        if schedule and schedule > datetime.utcnow():
            # Schedule for later
            campaign_info = self.email_marketing.schedule_campaign(
                campaign_id=email_campaign.id,
                recipients=recipients,
                send_time=schedule
            )
            campaign.status = "scheduled"
        else:
            # Send immediately
            campaign_info = await self._send_email_campaign(
                email_campaign,
                recipients
            )
            campaign.status = "running"
        
        self.db.commit()
        
        # Track analytics
        self.analytics_service.track_event("email_campaign_launched", {
            "campaign_id": campaign_id,
            "email_campaign_id": email_campaign.id,
            "recipient_count": len(recipients),
            "scheduled": schedule is not None
        })
        
        return {
            "email_campaign_id": email_campaign.id,
            "status": campaign.status,
            "recipients": len(recipients),
            "send_time": schedule or datetime.utcnow()
        }
    
    async def process_referral(
        self,
        referral_code: str,
        referee_info: Dict[str, Any],
        action: str = "signup"
    ) -> Dict[str, Any]:
        """Process referral conversion"""
        # Find referral
        referral = self.db.query(Referral).filter(
            Referral.code == referral_code,
            Referral.status == "active"
        ).first()
        
        if not referral:
            return {"success": False, "error": "Invalid referral code"}
        
        # Get program
        program = self.db.query(ReferralProgram).filter(
            ReferralProgram.id == referral.program_id,
            ReferralProgram.is_active == True
        ).first()
        
        if not program:
            return {"success": False, "error": "Referral program not active"}
        
        # Check if already converted
        if referral.status == "converted":
            return {"success": False, "error": "Referral already used"}
        
        # Process conversion
        result = self.referral_system.track_referral(
            referral_code,
            referee_info["email"],
            action
        )
        
        if result.get("converted"):
            # Update referral
            referral.referee_email = referee_info["email"]
            referral.converted_at = datetime.utcnow()
            referral.status = "converted"
            
            # Grant rewards
            await self._grant_referral_rewards(referral, program)
            
            self.db.commit()
            
            # Send notifications
            await self._send_referral_notifications(referral, program)
            
            # Track analytics
            self.analytics_service.track_event("referral_converted", {
                "referral_id": referral.id,
                "program_id": program.id,
                "referrer_id": referral.referrer_id,
                "action": action
            })
        
        return result
    
    async def run_ab_test(
        self,
        feature: str,
        variants: List[Dict[str, Any]],
        traffic_split: Dict[str, float],
        success_metrics: List[str]
    ) -> Dict[str, Any]:
        """Run A/B test"""
        # Create test
        test = self.ab_testing.create_test(
            test_name=f"{feature}_test_{datetime.utcnow().strftime('%Y%m%d')}",
            variants=variants,
            traffic_allocation=traffic_split,
            success_metrics=success_metrics
        )
        
        # Track test creation
        self.analytics_service.track_event("ab_test_created", {
            "test_id": test.test_id,
            "feature": feature,
            "variants": len(variants)
        })
        
        return {
            "test_id": test.test_id,
            "status": "running",
            "variants": [v["name"] for v in variants],
            "traffic_split": traffic_split
        }
    
    def get_growth_metrics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive growth metrics"""
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Get campaigns in period
        campaigns = self.db.query(Campaign).filter(
            Campaign.created_at.between(date_from, date_to)
        ).all()
        
        # Calculate metrics by channel
        channel_metrics = {}
        total_spent = 0
        total_revenue = 0
        
        for campaign in campaigns:
            metrics = self.db.query(CampaignMetrics).filter(
                CampaignMetrics.campaign_id == campaign.id
            ).first()
            
            if metrics:
                channel = campaign.type
                if channel not in channel_metrics:
                    channel_metrics[channel] = {
                        "campaigns": 0,
                        "spent": 0,
                        "impressions": 0,
                        "clicks": 0,
                        "conversions": 0,
                        "revenue": 0
                    }
                
                channel_metrics[channel]["campaigns"] += 1
                channel_metrics[channel]["spent"] += campaign.spent
                channel_metrics[channel]["impressions"] += metrics.impressions
                channel_metrics[channel]["clicks"] += metrics.clicks
                channel_metrics[channel]["conversions"] += metrics.conversions
                channel_metrics[channel]["revenue"] += metrics.revenue
                
                total_spent += campaign.spent
                total_revenue += metrics.revenue
        
        # Calculate ROI and other metrics
        for channel_data in channel_metrics.values():
            if channel_data["spent"] > 0:
                channel_data["roi"] = (
                    (channel_data["revenue"] - channel_data["spent"]) / 
                    channel_data["spent"] * 100
                )
            else:
                channel_data["roi"] = 0
            
            if channel_data["impressions"] > 0:
                channel_data["ctr"] = (
                    channel_data["clicks"] / channel_data["impressions"] * 100
                )
            else:
                channel_data["ctr"] = 0
            
            if channel_data["clicks"] > 0:
                channel_data["conversion_rate"] = (
                    channel_data["conversions"] / channel_data["clicks"] * 100
                )
            else:
                channel_data["conversion_rate"] = 0
        
        # Get growth analytics
        growth_metrics = self.growth_analytics.calculate_growth_metrics(
            start_date=date_from,
            end_date=date_to
        )
        
        # Get funnel metrics
        funnel = self.growth_analytics.analyze_conversion_funnel({
            "date_range": (date_from, date_to)
        })
        
        return {
            "summary": {
                "total_campaigns": len(campaigns),
                "total_spent": total_spent,
                "total_revenue": total_revenue,
                "overall_roi": ((total_revenue - total_spent) / total_spent * 100) if total_spent > 0 else 0
            },
            "by_channel": channel_metrics,
            "growth_metrics": growth_metrics,
            "funnel": funnel,
            "period": {
                "from": date_from,
                "to": date_to
            }
        }
    
    async def distribute_content(
        self,
        content_id: str,
        channels: List[str],
        schedule: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """Distribute content across channels"""
        # Get content
        content = self.db.query(ContentMarketing).filter(
            ContentMarketing.id == content_id
        ).first()
        
        if not content:
            raise ValueError("Content not found")
        
        # Prepare distribution
        distribution_plan = []
        
        for channel in channels:
            channel_config = {
                "channel": channel,
                "content_id": content_id,
                "scheduled_at": schedule.get(channel) if schedule else datetime.utcnow()
            }
            
            # Channel-specific configuration
            if channel == "email":
                channel_config["subject"] = content.title
                channel_config["preview_text"] = content.description[:100]
            elif channel == "social":
                channel_config["platforms"] = ["twitter", "linkedin", "facebook"]
                channel_config["hashtags"] = content.tags
            elif channel == "blog":
                channel_config["categories"] = content.tags
                channel_config["author"] = content.created_by
            
            distribution_plan.append(channel_config)
        
        # Execute distribution
        results = await self.content_distribution.distribute(
            content_id,
            distribution_plan
        )
        
        # Track analytics
        self.analytics_service.track_event("content_distributed", {
            "content_id": content_id,
            "channels": channels,
            "scheduled": schedule is not None
        })
        
        return results
    
    async def _get_email_recipients(self, segment: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get email recipients based on segment"""
        from database.models import User
        from sqlalchemy import text
        
        recipients = []
        
        try:
            # Build query based on segment criteria
            query = self.db.query(User)
            
            # Apply segment filters
            if segment.get('subscription_tier'):
                query = query.filter(User.subscription_tier == segment['subscription_tier'])
            
            if segment.get('created_after'):
                query = query.filter(User.created_at >= segment['created_after'])
            
            if segment.get('created_before'):
                query = query.filter(User.created_at <= segment['created_before'])
            
            if segment.get('last_active_days'):
                cutoff_date = datetime.utcnow() - timedelta(days=segment['last_active_days'])
                query = query.filter(User.last_login >= cutoff_date)
            
            if segment.get('country'):
                # Assuming country is stored in user metadata
                query = query.filter(
                    User.metadata.op('->>')('country') == segment['country']
                )
            
            if segment.get('language'):
                query = query.filter(
                    User.metadata.op('->>')('language') == segment['language']
                )
            
            if segment.get('has_transcripts'):
                # Join with transcripts to find users with transcripts
                from database.models import Transcript
                query = query.join(Transcript, User.id == Transcript.user_id).distinct()
            
            if segment.get('min_transcripts'):
                # Users with minimum number of transcripts
                from database.models import Transcript
                subquery = self.db.query(
                    Transcript.user_id,
                    func.count(Transcript.id).label('transcript_count')
                ).group_by(Transcript.user_id).having(
                    func.count(Transcript.id) >= segment['min_transcripts']
                ).subquery()
                
                query = query.join(subquery, User.id == subquery.c.user_id)
            
            # Check email preferences
            if segment.get('email_opted_in', True):
                # Only include users who haven't opted out
                query = query.filter(
                    or_(
                        User.metadata.op('->>')('email_opted_out') != 'true',
                        User.metadata.op('->>')('email_opted_out').is_(None)
                    )
                )
            
            # Apply custom SQL filter if provided
            if segment.get('custom_filter'):
                query = query.filter(text(segment['custom_filter']))
            
            # Limit results for safety
            max_recipients = segment.get('max_recipients', 10000)
            query = query.limit(max_recipients)
            
            # Execute query
            users = query.all()
            
            # Format recipients
            for user in users:
                # Check if user has valid email
                if user.email and '@' in user.email:
                    recipient = {
                        "email": user.email,
                        "name": user.full_name or user.username or "User",
                        "user_id": str(user.id),
                        "subscription_tier": getattr(user, 'subscription_tier', 'free'),
                        "language": user.metadata.get('language', 'en') if hasattr(user, 'metadata') and user.metadata else 'en'
                    }
                    
                    # Add custom fields from metadata
                    if hasattr(user, 'metadata') and user.metadata:
                        metadata = user.metadata if isinstance(user.metadata, dict) else {}
                        recipient["first_name"] = metadata.get('first_name', user.full_name.split()[0] if user.full_name else "User")
                        recipient["last_name"] = metadata.get('last_name', user.full_name.split()[-1] if user.full_name and len(user.full_name.split()) > 1 else "")
                        recipient["company"] = metadata.get('company', '')
                        recipient["role"] = metadata.get('role', '')
                    
                    recipients.append(recipient)
            
            # Log segment query results
            import logging
            logging.info(f"Email segment query returned {len(recipients)} recipients")
            
        except Exception as e:
            import logging
            logging.error(f"Error getting email recipients: {e}")
            
            # Return empty list on error
            recipients = []
        
        return recipients
    
    def _matches_segment(self, user: Dict[str, Any], segment: Dict[str, Any]) -> bool:
        """Check if user matches segment criteria"""
        
        # Check each segment criterion
        if segment.get('subscription_tier'):
            if user.get('subscription_tier') != segment['subscription_tier']:
                return False
        
        if segment.get('country'):
            if user.get('country') != segment['country']:
                return False
        
        if segment.get('language'):
            if user.get('language') != segment['language']:
                return False
        
        if segment.get('min_activity_score'):
            if user.get('activity_score', 0) < segment['min_activity_score']:
                return False
        
        if segment.get('has_subscription'):
            if not user.get('subscription_tier') or user.get('subscription_tier') == 'free':
                return False
        
        if segment.get('email_verified'):
            if not user.get('email_verified'):
                return False
        
        if segment.get('tags'):
            user_tags = user.get('tags', [])
            for required_tag in segment['tags']:
                if required_tag not in user_tags:
                    return False
        
        if segment.get('exclude_tags'):
            user_tags = user.get('tags', [])
            for excluded_tag in segment['exclude_tags']:
                if excluded_tag in user_tags:
                    return False
        
        # All criteria matched
        return True
    
    async def _send_email_campaign(
        self,
        campaign: EmailCampaign,
        recipients: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send email campaign"""
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                # Personalize content
                personalized_subject = self._personalize_content(
                    campaign.subject,
                    recipient
                )
                personalized_html = self._personalize_content(
                    campaign.content_html,
                    recipient
                )
                
                # Send email
                await self.email_service.send_email(
                    to=recipient["email"],
                    subject=personalized_subject,
                    html_content=personalized_html,
                    text_content=campaign.content_text,
                    campaign_id=campaign.id
                )
                
                sent_count += 1
            except Exception as e:
                failed_count += 1
                # Log error
        
        # Update metrics
        metrics = self.db.query(CampaignMetrics).filter(
            CampaignMetrics.campaign_id == campaign.campaign_id
        ).first()
        
        if metrics:
            metrics.emails_sent = sent_count
            metrics.emails_failed = failed_count
            self.db.commit()
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "success_rate": (sent_count / len(recipients) * 100) if recipients else 0
        }
    
    def _personalize_content(self, content: str, recipient: Dict[str, str]) -> str:
        """Personalize content for recipient"""
        # Simple merge tag replacement
        for key, value in recipient.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content
    
    async def _grant_referral_rewards(
        self,
        referral: Referral,
        program: ReferralProgram
    ):
        """Grant rewards for successful referral"""
        # Grant referrer reward
        if program.referrer_reward:
            await self._apply_reward(
                referral.referrer_id,
                program.referrer_reward,
                "referrer"
            )
        
        # Grant referee reward
        if program.referee_reward:
            await self._apply_reward(
                referral.referee_email,
                program.referee_reward,
                "referee"
            )
        
        # Mark rewards as granted
        referral.referrer_reward_granted = True
        referral.referee_reward_granted = True
    
    async def _apply_reward(
        self,
        recipient_id: str,
        reward: Dict[str, Any],
        reward_type: str
    ):
        """Apply reward to user"""
        # Simplified - would integrate with billing/subscription system
        if reward.get("type") == "credit":
            # Add account credit
            pass
        elif reward.get("type") == "discount":
            # Create discount code
            pass
        elif reward.get("type") == "feature":
            # Unlock feature
            pass
    
    async def _send_referral_notifications(
        self,
        referral: Referral,
        program: ReferralProgram
    ):
        """Send notifications for successful referral"""
        # Notify referrer
        await self.notification_service.send_notification(
            user_id=referral.referrer_id,
            title="Referral Successful!",
            message=f"Your referral has signed up. You've earned your reward!",
            type="referral_success",
            data={
                "referral_id": referral.id,
                "reward": program.referrer_reward
            }
        )
        
        # Email referrer
        await self.email_service.send_template_email(
            to=referral.referrer_email,
            template="referral_success",
            data={
                "program_name": program.name,
                "reward": program.referrer_reward
            }
        )
    
    def _get_default_automation_rules(
        self,
        campaign_type: CampaignType
    ) -> List[Dict[str, Any]]:
        """Get default automation rules for campaign type"""
        if campaign_type == CampaignType.EMAIL:
            return [
                {
                    "trigger": "email_opened",
                    "action": "track_engagement",
                    "delay": 0
                },
                {
                    "trigger": "link_clicked",
                    "action": "segment_engaged_users",
                    "delay": 0
                },
                {
                    "trigger": "no_open_3_days",
                    "action": "send_reminder",
                    "delay": 72  # hours
                }
            ]
        elif campaign_type == CampaignType.REFERRAL:
            return [
                {
                    "trigger": "referral_shared",
                    "action": "track_share",
                    "delay": 0
                },
                {
                    "trigger": "referral_converted",
                    "action": "grant_rewards",
                    "delay": 0
                }
            ]
        else:
            return []