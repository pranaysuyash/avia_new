#!/usr/bin/env python3
"""
Usage Tracking and Quota Management System (Task 48)
Real-time usage monitoring with subscription-based quota enforcement
"""

import os
import json
import logging
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class UsageMetric(Enum):
    """Usage metrics that can be tracked"""
    TRANSCRIPTION_HOURS = "transcription_hours"
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    TEAM_MEMBERS = "team_members"
    WORKSPACES = "workspaces"

class QuotaStatus(Enum):
    """Quota status indicators"""
    WITHIN_LIMITS = "within_limits"
    APPROACHING_LIMIT = "approaching_limit"
    NEAR_LIMIT = "near_limit"
    EXCEEDED = "exceeded"

@dataclass
class UsageEvent:
    """Individual usage event record"""
    event_id: str
    user_id: str
    team_id: Optional[str]
    metric: str
    quantity: float
    timestamp: str
    metadata: Dict[str, Any]

class UsageTracker:
    """Core usage tracking functionality"""
    
    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
        self.init_database()
        self._usage_cache = defaultdict(lambda: defaultdict(float))
        self._cache_lock = threading.Lock()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usage_events (
                        event_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        team_id TEXT,
                        metric TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise    
  
  def track_usage(self, user_id: str, metric: UsageMetric, quantity: float,
                   team_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Track usage event and check quotas"""
        try:
            # Create usage event
            event = UsageEvent(
                event_id=f"event_{secrets.token_urlsafe(16)}",
                user_id=user_id,
                team_id=team_id,
                metric=metric.value,
                quantity=quantity,
                timestamp=datetime.now().isoformat(),
                metadata=metadata or {}
            )
            
            # Check quota before recording
            quota_check = self.check_quota(user_id, metric, quantity, team_id)
            
            if not quota_check['allowed']:
                return False, quota_check['message'], quota_check
            
            # Record the usage event
            self._record_usage_event(event)
            
            # Update cache
            with self._cache_lock:
                cache_key = f"{user_id}:{team_id or 'personal'}"
                self._usage_cache[cache_key][metric.value] += quantity
            
            return True, "Usage tracked successfully", quota_check
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            return False, "Failed to track usage", {}
    
    def check_quota(self, user_id: str, metric: UsageMetric, requested_quantity: float,
                   team_id: Optional[str] = None) -> Dict[str, Any]:
        """Check if usage is within quota limits"""
        try:
            # Get current usage
            current_usage = self.get_current_usage(user_id, metric, team_id=team_id)
            
            # Get limit for this metric (mock limits for demo)
            limits = {
                UsageMetric.TRANSCRIPTION_HOURS.value: 5,  # Free tier: 5 hours
                UsageMetric.API_CALLS.value: 1000,  # Free tier: 1000 calls
                UsageMetric.STORAGE_GB.value: 1,  # Free tier: 1GB
                UsageMetric.TEAM_MEMBERS.value: 1,  # Free tier: 1 member
                UsageMetric.WORKSPACES.value: 3  # Free tier: 3 workspaces
            }
            
            limit = limits.get(metric.value, 0)
            total_usage = current_usage + requested_quantity
            
            # Calculate percentage
            percentage = (total_usage / limit * 100) if limit > 0 else 100
            
            # Determine status
            if percentage <= 80:
                status = QuotaStatus.WITHIN_LIMITS
            elif percentage <= 90:
                status = QuotaStatus.APPROACHING_LIMIT
            elif percentage <= 100:
                status = QuotaStatus.NEAR_LIMIT
            else:
                status = QuotaStatus.EXCEEDED
            
            # Check if allowed
            allowed = total_usage <= limit
            
            # Calculate overage
            overage = max(0, total_usage - limit)
            overage_cost = self._calculate_overage_cost(metric, overage)
            
            message = "Within limits"
            if status == QuotaStatus.APPROACHING_LIMIT:
                message = f"Approaching limit ({percentage:.1f}% used)"
            elif status == QuotaStatus.NEAR_LIMIT:
                message = f"Near limit ({percentage:.1f}% used)"
            elif status == QuotaStatus.EXCEEDED:
                message = f"Quota exceeded. Overage cost: ${overage_cost/100:.2f}"
                allowed = False
            
            return {
                'allowed': allowed,
                'message': message,
                'current_usage': current_usage,
                'requested_usage': requested_quantity,
                'total_usage': total_usage,
                'limit': limit,
                'status': status.value,
                'percentage': percentage,
                'overage': overage,
                'overage_cost': overage_cost
            }
            
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            return {
                'allowed': False,
                'message': 'Quota check failed',
                'current_usage': 0,
                'limit': 0,
                'status': QuotaStatus.EXCEEDED.value
            }
    
    def get_current_usage(self, user_id: str, metric: UsageMetric, 
                         period_start: Optional[str] = None, 
                         period_end: Optional[str] = None,
                         team_id: Optional[str] = None) -> float:
        """Get current usage for a metric in the specified period"""
        try:
            # Default to current month if no period specified
            if not period_start:
                now = datetime.now()
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            if not period_end:
                period_end = datetime.now().isoformat()
            
            # Query database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT COALESCE(SUM(quantity), 0) as total_usage
                    FROM usage_events
                    WHERE user_id = ? AND metric = ? AND timestamp BETWEEN ? AND ?
                """
                params = [user_id, metric.value, period_start, period_end]
                
                if team_id:
                    query += " AND team_id = ?"
                    params.append(team_id)
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                return result[0] if result else 0.0
                
        except Exception as e:
            logger.error(f"Error getting current usage: {e}")
            return 0.0
    
    def get_usage_analytics(self, user_id: str, team_id: Optional[str] = None,
                           days: int = 30) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            analytics = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                },
                'metrics': {},
                'recommendations': []
            }
            
            # Get usage for each metric
            for metric in UsageMetric:
                usage_data = self._get_metric_analytics(
                    user_id, metric, start_date, end_date, team_id
                )
                analytics['metrics'][metric.value] = usage_data
            
            # Generate recommendations
            analytics['recommendations'] = self._generate_usage_recommendations(
                user_id, analytics['metrics']
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting usage analytics: {e}")
            return {}
    
    def _record_usage_event(self, event: UsageEvent):
        """Record usage event to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usage_events (
                        event_id, user_id, team_id, metric, quantity,
                        timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.user_id, event.team_id, event.metric,
                    event.quantity, event.timestamp, json.dumps(event.metadata)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording usage event: {e}")
            raise
    
    def _calculate_overage_cost(self, metric: UsageMetric, overage: float) -> float:
        """Calculate overage cost in cents"""
        overage_rates = {
            UsageMetric.TRANSCRIPTION_HOURS.value: 500,  # $5.00 per hour
            UsageMetric.API_CALLS.value: 1,  # $0.01 per 100 calls
            UsageMetric.STORAGE_GB.value: 200,  # $2.00 per GB
        }
        
        rate = overage_rates.get(metric.value, 0)
        
        if metric == UsageMetric.API_CALLS:
            return int((overage / 100) * rate)
        
        return int(overage * rate)
    
    def _get_metric_analytics(self, user_id: str, metric: UsageMetric, 
                             start_date: datetime, end_date: datetime,
                             team_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics for a specific metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        DATE(timestamp) as date,
                        SUM(quantity) as daily_usage,
                        COUNT(*) as events_count
                    FROM usage_events
                    WHERE user_id = ? AND metric = ? AND timestamp BETWEEN ? AND ?
                """
                params = [user_id, metric.value, start_date.isoformat(), end_date.isoformat()]
                
                if team_id:
                    query += " AND team_id = ?"
                    params.append(team_id)
                
                query += " GROUP BY DATE(timestamp) ORDER BY date"
                
                cursor.execute(query, params)
                daily_data = cursor.fetchall()
                
                # Calculate totals
                total_usage = sum(row[1] for row in daily_data)
                total_events = sum(row[2] for row in daily_data)
                
                # Calculate average daily usage
                days_with_usage = len(daily_data)
                avg_daily_usage = total_usage / max(days_with_usage, 1)
                
                return {
                    'total_usage': total_usage,
                    'total_events': total_events,
                    'avg_daily_usage': avg_daily_usage,
                    'days_with_usage': days_with_usage
                }
                
        except Exception as e:
            logger.error(f"Error getting metric analytics: {e}")
            return {}
    
    def _generate_usage_recommendations(self, user_id: str, metrics: Dict[str, Any]) -> List[str]:
        """Generate usage optimization recommendations"""
        recommendations = []
        
        try:
            # Analyze transcription usage
            transcription_data = metrics.get('transcription_hours', {})
            if transcription_data.get('total_usage', 0) > 3:
                recommendations.append(
                    "Consider upgrading to Pro for 50 hours of transcription per month"
                )
            
            # Analyze API usage
            api_data = metrics.get('api_calls', {})
            if api_data.get('avg_daily_usage', 0) > 50:
                recommendations.append(
                    "Consider implementing API call caching to reduce usage"
                )
            
            # Storage recommendations
            storage_data = metrics.get('storage_gb', {})
            if storage_data.get('total_usage', 0) > 0.8:
                recommendations.append(
                    "Storage nearly full. Upgrade to Pro for 50GB storage"
                )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations

def main():
    """Demo function"""
    print("🚀 Usage Tracking and Quota Management Demo")
    print("=" * 50)
    
    # Initialize system
    tracker = UsageTracker()
    
    # Demo user
    user_id = "user_demo_usage"
    team_id = "team_demo"
    
    print(f"\n1. Tracking transcription usage for user {user_id}")
    
    # Track some usage
    success, message, quota_info = tracker.track_usage(
        user_id=user_id,
        metric=UsageMetric.TRANSCRIPTION_HOURS,
        quantity=2.5,
        team_id=team_id,
        metadata={"file_name": "meeting.mp4", "duration": 150}
    )
    
    print(f"   Result: {message}")
    print(f"   Quota Status: {quota_info.get('status', 'unknown')}")
    print(f"   Usage: {quota_info.get('current_usage', 0):.1f} / {quota_info.get('limit', 0)} hours")
    
    print(f"\n2. Tracking API calls")
    tracker.track_usage(
        user_id=user_id,
        metric=UsageMetric.API_CALLS,
        quantity=150,
        team_id=team_id,
        metadata={"endpoint": "/api/transcribe", "method": "POST"}
    )
    
    print(f"\n3. Checking quota for large transcription request")
    quota_check = tracker.check_quota(
        user_id=user_id,
        metric=UsageMetric.TRANSCRIPTION_HOURS,
        requested_quantity=10.0,
        team_id=team_id
    )
    
    print(f"   Can process 10 hours: {quota_check['allowed']}")
    print(f"   Message: {quota_check['message']}")
    print(f"   Current percentage: {quota_check.get('percentage', 0):.1f}%")
    
    print(f"\n4. Getting usage analytics")
    analytics = tracker.get_usage_analytics(user_id, team_id, days=30)
    
    if analytics:
        print(f"   Period: {analytics['period']['days']} days")
        for metric, data in analytics['metrics'].items():
            if data and data.get('total_usage', 0) > 0:
                print(f"   {metric}: {data['total_usage']:.1f} total, {data['avg_daily_usage']:.1f} avg/day")
        
        if analytics['recommendations']:
            print(f"\n   Recommendations:")
            for rec in analytics['recommendations']:
                print(f"   - {rec}")
    
    print(f"\n✅ Demo completed successfully!")

if __name__ == "__main__":
    main()