"""
Analytics Service
Simple event tracking interface that leverages existing comprehensive analytics services
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from services.usage_analytics_service import UsageAnalyticsService
# Note: not importing advanced_analytics_service due to import conflicts
# from services.advanced_analytics_service import AdvancedAnalyticsService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Simple analytics service for event tracking
    Provides a simplified interface while leveraging existing comprehensive services
    """
    
    def __init__(self, db=None):
        """Initialize analytics service with database connection"""
        self.db = db
        
        # Initialize comprehensive analytics services
        if db and hasattr(db, 'bind'):
            # Create session factory from existing session
            self.usage_analytics = UsageAnalyticsService(lambda: db)
        else:
            self.usage_analytics = None
            
        # Note: advanced_analytics not initialized due to import conflicts
        # self.advanced_analytics = AdvancedAnalyticsService()
        
        # In-memory event store for simple tracking
        self.events = []
        
        logger.info("AnalyticsService initialized")
    
    def track_event(self, event_name: str, properties: Dict[str, Any] = None, 
                   user_id: Optional[int] = None) -> None:
        """
        Track an event with properties
        
        Args:
            event_name: Name of the event
            properties: Event properties/metadata
            user_id: Optional user ID associated with the event
        """
        try:
            # Create event record
            event = {
                'event_name': event_name,
                'properties': properties or {},
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                'session_id': None  # Could be enhanced with session tracking
            }
            
            # Store event (in production, this would go to a database or analytics platform)
            self.events.append(event)
            
            # Log the event for debugging
            logger.info(f"Event tracked: {event_name} with properties: {properties}")
            
            # Optional: Send to external analytics platform (Google Analytics, Mixpanel, etc.)
            # self._send_to_external_analytics(event)
            
        except Exception as e:
            logger.error(f"Error tracking event '{event_name}': {e}")
    
    def track_user_action(self, user_id: int, action: str, metadata: Dict[str, Any] = None) -> None:
        """
        Track a user action
        
        Args:
            user_id: User ID
            action: Action performed
            metadata: Additional metadata
        """
        self.track_event(f"user_{action}", metadata, user_id=user_id)
    
    def track_marketing_event(self, event_type: str, campaign_data: Dict[str, Any] = None) -> None:
        """
        Track marketing-specific events
        
        Args:
            event_type: Type of marketing event
            campaign_data: Campaign-related data
        """
        self.track_event(f"marketing_{event_type}", campaign_data)
    
    def get_event_count(self, event_name: str = None, 
                       start_date: datetime = None, 
                       end_date: datetime = None) -> int:
        """
        Get count of events
        
        Args:
            event_name: Filter by event name (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            Count of matching events
        """
        try:
            filtered_events = self.events
            
            # Filter by event name
            if event_name:
                filtered_events = [e for e in filtered_events if e['event_name'] == event_name]
            
            # Filter by date range
            if start_date:
                filtered_events = [e for e in filtered_events if e['timestamp'] >= start_date]
            
            if end_date:
                filtered_events = [e for e in filtered_events if e['timestamp'] <= end_date]
            
            return len(filtered_events)
            
        except Exception as e:
            logger.error(f"Error getting event count: {e}")
            return 0
    
    def get_events(self, event_name: str = None, limit: int = 100) -> list:
        """
        Get recent events
        
        Args:
            event_name: Filter by event name (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        try:
            filtered_events = self.events
            
            # Filter by event name
            if event_name:
                filtered_events = [e for e in filtered_events if e['event_name'] == event_name]
            
            # Sort by timestamp (most recent first) and limit
            sorted_events = sorted(filtered_events, key=lambda x: x['timestamp'], reverse=True)
            
            return sorted_events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def generate_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate analytics summary for the last N days
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            Summary statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_events = [e for e in self.events if e['timestamp'] >= cutoff_date]
            
            # Count events by type
            event_counts = {}
            unique_users = set()
            
            for event in recent_events:
                event_name = event['event_name']
                event_counts[event_name] = event_counts.get(event_name, 0) + 1
                
                if event['user_id']:
                    unique_users.add(event['user_id'])
            
            return {
                'total_events': len(recent_events),
                'unique_users': len(unique_users),
                'event_types': len(event_counts),
                'event_breakdown': event_counts,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
    
    def _send_to_external_analytics(self, event: Dict[str, Any]) -> None:
        """
        Send event to external analytics platform
        This would be implemented based on the chosen analytics platform
        """
        # Example implementations:
        # - Google Analytics 4 Measurement Protocol
        # - Mixpanel API
        # - Amplitude API
        # - Custom analytics endpoint
        pass