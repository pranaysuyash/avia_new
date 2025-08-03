#!/usr/bin/env python3
"""
Usage Analytics API Endpoints
Provides analytics and insights on usage patterns
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from database.models import User
from api.auth_routes_enhanced import get_current_user
from services.usage_analytics_service import UsageAnalyticsService
from services.usage_notification_service import UsageNotificationService
from database.connection import get_db
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usage/analytics", tags=["usage-analytics"])

# Initialize services
analytics_service = UsageAnalyticsService(get_db)
notification_service = UsageNotificationService(get_db)

# Request/Response Models

class UsageTrendsRequest(BaseModel):
    days: int = Field(30, ge=1, le=365)
    usage_type: Optional[str] = None
    team_id: Optional[int] = None

class UsageReportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_id: Optional[int] = None
    format: str = Field("json", pattern="^(json|csv|pdf)$")

class UsageAlertSettings(BaseModel):
    email_alerts: bool = True
    alert_threshold: int = Field(90, ge=50, le=100)
    weekly_summary: bool = True
    monthly_summary: bool = True

# Endpoints

@router.get("/trends", response_model=Dict[str, Any])
async def get_usage_trends(
    days: int = Query(30, ge=1, le=365),
    usage_type: Optional[str] = Query(None),
    team_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get usage trends over time"""
    # Admin can view any user/team, others only their own
    if current_user.role != 'admin':
        team_id = None  # Regular users can only see their own data
        
    trends = analytics_service.get_usage_trends(
        user_id=current_user.id if current_user.role != 'admin' else None,
        team_id=team_id,
        days=days,
        usage_type=usage_type
    )
    
    return trends

@router.get("/hourly", response_model=Dict[str, Any])
async def get_hourly_usage(
    days: int = Query(7, ge=1, le=30),
    team_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get usage patterns by hour of day"""
    if current_user.role != 'admin':
        team_id = None
    
    hourly_data = analytics_service.get_usage_by_hour(
        user_id=current_user.id if current_user.role != 'admin' else None,
        team_id=team_id,
        days=days
    )
    
    return hourly_data

@router.get("/top-users", response_model=List[Dict[str, Any]])
async def get_top_users(
    usage_type: str = Query(..., pattern="^(transcripts|minutes|storage|api_calls)$"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get top users by usage (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    top_users = analytics_service.get_top_users(
        usage_type=usage_type,
        days=days,
        limit=limit
    )
    
    return top_users

@router.get("/by-plan", response_model=Dict[str, Any])
async def get_usage_by_plan(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics by pricing plan (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    usage_by_plan = analytics_service.get_usage_by_plan(days=days)
    
    return usage_by_plan

@router.get("/resource-distribution", response_model=Dict[str, Any])
async def get_resource_distribution(
    days: int = Query(30, ge=1, le=365),
    team_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get distribution of resource usage"""
    if current_user.role != 'admin':
        team_id = None
    
    distribution = analytics_service.get_resource_distribution(
        user_id=current_user.id if current_user.role != 'admin' else None,
        team_id=team_id,
        days=days
    )
    
    return distribution

@router.get("/forecast/{usage_type}", response_model=Dict[str, Any])
async def get_usage_forecast(
    usage_type: str,
    current_user: User = Depends(get_current_user)
):
    """Get usage forecast for current month"""
    if usage_type not in ['transcripts', 'minutes', 'storage', 'api_calls']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid usage type"
        )
    
    forecast = analytics_service.get_usage_forecast(
        user_id=current_user.id,
        usage_type=usage_type
    )
    
    return forecast

@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_usage_alerts(
    current_user: User = Depends(get_current_user)
):
    """Get current usage alerts"""
    alerts = analytics_service.get_usage_alerts(user_id=current_user.id)
    return alerts

@router.post("/alerts/send")
async def send_usage_alerts(
    current_user: User = Depends(get_current_user)
):
    """Manually trigger usage alert check"""
    sent_alerts = notification_service.check_and_send_alerts(user_id=current_user.id)
    
    return {
        'sent_count': len(sent_alerts),
        'alerts': sent_alerts
    }

@router.post("/report", response_model=Dict[str, Any])
async def generate_usage_report(
    request: UsageReportRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive usage report"""
    report = analytics_service.generate_usage_report(
        user_id=current_user.id,
        team_id=request.team_id if current_user.role == 'admin' else None,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    if request.format == 'csv':
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Date', 'Usage Type', 'Quantity'])
        
        # Write data
        for date, usage_data in report['trends'].items():
            for usage_type, quantity in usage_data.items():
                writer.writerow([date, usage_type, quantity])
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=usage_report_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    
    elif request.format == 'pdf':
        # PDF generation would go here
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF export not yet implemented"
        )
    
    return report

@router.get("/alert-settings", response_model=UsageAlertSettings)
async def get_alert_settings(
    current_user: User = Depends(get_current_user)
):
    """Get user's alert settings"""
    # This would fetch from user preferences
    return UsageAlertSettings(
        email_alerts=True,
        alert_threshold=90,
        weekly_summary=True,
        monthly_summary=True
    )

@router.put("/alert-settings")
async def update_alert_settings(
    settings: UsageAlertSettings,
    current_user: User = Depends(get_current_user)
):
    """Update user's alert settings"""
    # This would save to user preferences
    return {
        'message': 'Alert settings updated',
        'settings': settings
    }

@router.post("/summary/{period}")
async def send_usage_summary(
    period: str = Query(..., pattern="^(weekly|monthly)$"),
    current_user: User = Depends(get_current_user)
):
    """Send usage summary email"""
    success = notification_service.send_usage_summary(
        user_id=current_user.id,
        period=period
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send usage summary"
        )
    
    return {
        'message': f'{period.title()} usage summary sent to your email'
    }

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_usage_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard data"""
    # Get various analytics
    trends = analytics_service.get_usage_trends(
        user_id=current_user.id,
        days=30
    )
    
    hourly = analytics_service.get_usage_by_hour(
        user_id=current_user.id,
        days=7
    )
    
    alerts = analytics_service.get_usage_alerts(user_id=current_user.id)
    
    # Get forecasts
    forecasts = {}
    for usage_type in ['transcripts', 'minutes', 'storage', 'api_calls']:
        try:
            forecasts[usage_type] = analytics_service.get_usage_forecast(
                user_id=current_user.id,
                usage_type=usage_type
            )
        except Exception as e:
            logger.warning(f"Failed to get forecast for {usage_type}: {e}")
            forecasts[usage_type] = None
    
    return {
        'trends': trends,
        'hourly_patterns': hourly,
        'alerts': alerts,
        'forecasts': forecasts,
        'generated_at': datetime.utcnow().isoformat()
    }