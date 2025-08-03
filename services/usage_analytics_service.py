#!/usr/bin/env python3
"""
Usage Analytics Service
Provides detailed analytics and insights on usage patterns
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from sqlalchemy import func, and_, or_, case, extract
from sqlalchemy.orm import Session

from database.models import User, Transcript, Team
from database.subscription_models import (
    UsageRecord, Subscription, PricingPlan, PricingTier
)

logger = logging.getLogger(__name__)

class UsageAnalyticsService:
    """Service for usage analytics and reporting"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def get_usage_trends(
        self,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        days: int = 30,
        usage_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage trends over time"""
        db = self._get_db()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Base query
            query = db.query(
                func.date(UsageRecord.created_at).label('date'),
                UsageRecord.usage_type,
                func.sum(UsageRecord.quantity).label('total')
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date
            )
            
            # Apply filters
            if user_id:
                query = query.filter(UsageRecord.user_id == user_id)
            if team_id:
                query = query.filter(UsageRecord.team_id == team_id)
            if usage_type:
                query = query.filter(UsageRecord.usage_type == usage_type)
            
            # Group by date and usage type
            query = query.group_by(
                func.date(UsageRecord.created_at),
                UsageRecord.usage_type
            ).order_by(func.date(UsageRecord.created_at))
            
            results = query.all()
            
            # Format results
            trends = {}
            for row in results:
                date_str = row.date.isoformat()
                if date_str not in trends:
                    trends[date_str] = {}
                trends[date_str][row.usage_type] = float(row.total)
            
            # Fill missing dates
            current_date = start_date.date()
            while current_date <= end_date.date():
                date_str = current_date.isoformat()
                if date_str not in trends:
                    trends[date_str] = {
                        'transcripts': 0,
                        'minutes': 0,
                        'storage': 0,
                        'api_calls': 0
                    }
                current_date += timedelta(days=1)
            
            return {
                'period': f'{days} days',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'trends': trends
            }
            
        finally:
            db.close()
    
    def get_usage_by_hour(
        self,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get usage patterns by hour of day"""
        db = self._get_db()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = db.query(
                extract('hour', UsageRecord.created_at).label('hour'),
                UsageRecord.usage_type,
                func.count(UsageRecord.id).label('count'),
                func.sum(UsageRecord.quantity).label('total')
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date
            )
            
            if user_id:
                query = query.filter(UsageRecord.user_id == user_id)
            if team_id:
                query = query.filter(UsageRecord.team_id == team_id)
            
            query = query.group_by(
                extract('hour', UsageRecord.created_at),
                UsageRecord.usage_type
            ).order_by('hour')
            
            results = query.all()
            
            # Format results
            hourly_usage = {}
            for row in results:
                hour = int(row.hour)
                if hour not in hourly_usage:
                    hourly_usage[hour] = {}
                hourly_usage[hour][row.usage_type] = {
                    'count': row.count,
                    'total': float(row.total)
                }
            
            # Fill missing hours
            for hour in range(24):
                if hour not in hourly_usage:
                    hourly_usage[hour] = {
                        'transcripts': {'count': 0, 'total': 0},
                        'minutes': {'count': 0, 'total': 0},
                        'api_calls': {'count': 0, 'total': 0}
                    }
            
            return {
                'period': f'{days} days',
                'hourly_usage': hourly_usage
            }
            
        finally:
            db.close()
    
    def get_top_users(
        self,
        usage_type: str,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top users by usage"""
        db = self._get_db()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = db.query(
                User.id,
                User.username,
                User.full_name,
                func.sum(UsageRecord.quantity).label('total_usage')
            ).join(
                UsageRecord, User.id == UsageRecord.user_id
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date,
                UsageRecord.usage_type == usage_type
            ).group_by(
                User.id, User.username, User.full_name
            ).order_by(
                func.sum(UsageRecord.quantity).desc()
            ).limit(limit)
            
            results = query.all()
            
            return [
                {
                    'user_id': row.id,
                    'username': row.username,
                    'full_name': row.full_name,
                    'total_usage': float(row.total_usage),
                    'usage_type': usage_type
                }
                for row in results
            ]
            
        finally:
            db.close()
    
    def get_usage_by_plan(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage statistics by pricing plan"""
        db = self._get_db()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Query usage by plan
            query = db.query(
                PricingPlan.tier,
                PricingPlan.name,
                UsageRecord.usage_type,
                func.count(func.distinct(UsageRecord.user_id)).label('unique_users'),
                func.count(UsageRecord.id).label('total_records'),
                func.sum(UsageRecord.quantity).label('total_usage')
            ).select_from(UsageRecord).join(
                User, UsageRecord.user_id == User.id
            ).outerjoin(
                Subscription, User.id == Subscription.user_id
            ).join(
                PricingPlan,
                or_(
                    Subscription.plan_id == PricingPlan.id,
                    and_(
                        Subscription.id.is_(None),
                        PricingPlan.tier == PricingTier.FREE
                    )
                )
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date
            ).group_by(
                PricingPlan.tier,
                PricingPlan.name,
                UsageRecord.usage_type
            )
            
            results = query.all()
            
            # Format results
            usage_by_plan = {}
            for row in results:
                plan_name = row.name
                if plan_name not in usage_by_plan:
                    usage_by_plan[plan_name] = {
                        'tier': row.tier.value,
                        'unique_users': 0,
                        'usage': {}
                    }
                
                usage_by_plan[plan_name]['unique_users'] = max(
                    usage_by_plan[plan_name]['unique_users'],
                    row.unique_users
                )
                usage_by_plan[plan_name]['usage'][row.usage_type] = {
                    'records': row.total_records,
                    'total': float(row.total_usage)
                }
            
            return {
                'period': f'{days} days',
                'usage_by_plan': usage_by_plan
            }
            
        finally:
            db.close()
    
    def get_resource_distribution(
        self,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get distribution of resource usage"""
        db = self._get_db()
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = db.query(
                UsageRecord.resource_type,
                func.count(func.distinct(UsageRecord.resource_id)).label('unique_resources'),
                func.count(UsageRecord.id).label('total_records'),
                func.sum(UsageRecord.quantity).label('total_usage')
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date,
                UsageRecord.resource_type.isnot(None)
            )
            
            if user_id:
                query = query.filter(UsageRecord.user_id == user_id)
            if team_id:
                query = query.filter(UsageRecord.team_id == team_id)
            
            query = query.group_by(UsageRecord.resource_type)
            
            results = query.all()
            
            return {
                'period': f'{days} days',
                'distribution': [
                    {
                        'resource_type': row.resource_type,
                        'unique_resources': row.unique_resources,
                        'total_records': row.total_records,
                        'total_usage': float(row.total_usage)
                    }
                    for row in results
                ]
            }
            
        finally:
            db.close()
    
    def get_usage_forecast(
        self,
        user_id: int,
        usage_type: str
    ) -> Dict[str, Any]:
        """Forecast usage based on historical data"""
        db = self._get_db()
        try:
            # Get last 30 days of usage
            trends = self.get_usage_trends(
                user_id=user_id,
                days=30,
                usage_type=usage_type
            )
            
            # Calculate daily average
            total_usage = 0
            days_with_usage = 0
            
            for date_data in trends['trends'].values():
                usage = date_data.get(usage_type, 0)
                if usage > 0:
                    total_usage += usage
                    days_with_usage += 1
            
            daily_average = total_usage / days_with_usage if days_with_usage > 0 else 0
            
            # Get current month usage
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
            days_in_month = 30  # Simplified
            days_elapsed = (datetime.utcnow() - current_month_start).days + 1
            days_remaining = days_in_month - days_elapsed
            
            # Get current month actual usage
            current_month_usage = db.query(
                func.sum(UsageRecord.quantity)
            ).filter(
                UsageRecord.user_id == user_id,
                UsageRecord.usage_type == usage_type,
                UsageRecord.created_at >= current_month_start
            ).scalar() or 0
            
            # Forecast
            projected_usage = float(current_month_usage) + (daily_average * days_remaining)
            
            # Get user's limit
            from services.subscription_service import SubscriptionService
            subscription_service = SubscriptionService(self.db_session_factory)
            plan = subscription_service.get_user_plan(user_id)
            
            limit_map = {
                'transcripts': plan.max_transcripts_per_month,
                'minutes': plan.max_minutes_per_month,
                'storage': plan.max_storage_gb,
                'api_calls': plan.max_api_calls_per_month
            }
            
            limit = limit_map.get(usage_type, 0)
            
            return {
                'usage_type': usage_type,
                'current_usage': float(current_month_usage),
                'daily_average': daily_average,
                'projected_usage': projected_usage,
                'limit': limit,
                'projected_percentage': (projected_usage / limit * 100) if limit > 0 else 0,
                'days_until_limit': int((limit - current_month_usage) / daily_average) if daily_average > 0 else None
            }
            
        finally:
            db.close()
    
    def get_usage_alerts(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get usage alerts for user"""
        alerts = []
        
        # Check each usage type
        for usage_type in ['transcripts', 'minutes', 'storage', 'api_calls']:
            forecast = self.get_usage_forecast(user_id, usage_type)
            
            # Alert if projected to exceed limit
            if forecast['limit'] > 0 and forecast['projected_percentage'] > 90:
                alerts.append({
                    'type': 'usage_warning',
                    'severity': 'high' if forecast['projected_percentage'] > 100 else 'medium',
                    'usage_type': usage_type,
                    'message': f"Projected to use {forecast['projected_percentage']:.0f}% of {usage_type} limit",
                    'current_usage': forecast['current_usage'],
                    'projected_usage': forecast['projected_usage'],
                    'limit': forecast['limit']
                })
            
            # Alert if approaching limit soon
            if forecast['days_until_limit'] and forecast['days_until_limit'] < 7:
                alerts.append({
                    'type': 'limit_approaching',
                    'severity': 'medium',
                    'usage_type': usage_type,
                    'message': f"Will reach {usage_type} limit in {forecast['days_until_limit']} days",
                    'days_remaining': forecast['days_until_limit']
                })
        
        return alerts
    
    def generate_usage_report(
        self,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive usage report"""
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        db = self._get_db()
        try:
            # Get usage summary
            query = db.query(
                UsageRecord.usage_type,
                func.count(UsageRecord.id).label('record_count'),
                func.sum(UsageRecord.quantity).label('total_quantity'),
                func.min(UsageRecord.created_at).label('first_usage'),
                func.max(UsageRecord.created_at).label('last_usage')
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date
            )
            
            if user_id:
                query = query.filter(UsageRecord.user_id == user_id)
            if team_id:
                query = query.filter(UsageRecord.team_id == team_id)
            
            query = query.group_by(UsageRecord.usage_type)
            
            usage_summary = {}
            for row in query.all():
                usage_summary[row.usage_type] = {
                    'record_count': row.record_count,
                    'total_quantity': float(row.total_quantity),
                    'first_usage': row.first_usage.isoformat(),
                    'last_usage': row.last_usage.isoformat()
                }
            
            # Get resource breakdown
            resource_query = db.query(
                UsageRecord.resource_type,
                func.count(func.distinct(UsageRecord.resource_id)).label('unique_count'),
                func.sum(UsageRecord.quantity).label('total_quantity')
            ).filter(
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date,
                UsageRecord.resource_type.isnot(None)
            )
            
            if user_id:
                resource_query = resource_query.filter(UsageRecord.user_id == user_id)
            if team_id:
                resource_query = resource_query.filter(UsageRecord.team_id == team_id)
            
            resource_query = resource_query.group_by(UsageRecord.resource_type)
            
            resource_breakdown = {}
            for row in resource_query.all():
                resource_breakdown[row.resource_type] = {
                    'unique_count': row.unique_count,
                    'total_quantity': float(row.total_quantity)
                }
            
            # Get user details if specific user
            user_info = None
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.full_name
                    }
            
            # Get team details if specific team
            team_info = None
            if team_id:
                team = db.query(Team).filter(Team.id == team_id).first()
                if team:
                    team_info = {
                        'id': team.id,
                        'name': team.name
                    }
            
            return {
                'report_generated': datetime.utcnow().isoformat(),
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'user': user_info,
                'team': team_info,
                'usage_summary': usage_summary,
                'resource_breakdown': resource_breakdown,
                'trends': self.get_usage_trends(
                    user_id=user_id,
                    team_id=team_id,
                    days=(end_date - start_date).days
                )['trends']
            }
            
        finally:
            db.close()