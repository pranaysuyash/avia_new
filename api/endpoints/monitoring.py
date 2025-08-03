"""
Monitoring API endpoints
Provides access to metrics, logs, and system health information
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import psutil
import os

from api.auth_middleware import get_current_active_user, require_admin
from monitoring.metrics_collector import metrics_collector, app_metrics
from monitoring.audit_logger import audit_logger, AuditEventType
from monitoring.logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    Returns system status and basic metrics
    """
    try:
        # Check database connection
        from database import get_db_session
        db = next(get_db_session())
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_status,
            "api": "healthy"
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
    }


@router.get("/health/detailed", dependencies=[Depends(require_admin)])
async def detailed_health_check(current_user: dict = Depends(get_current_active_user)):
    """
    Detailed health check with comprehensive system information
    Requires admin access
    """
    health_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "system": {},
        "application": {}
    }
    
    # Check services
    services_status = {}
    
    # Database
    try:
        from database import get_db_session
        db = next(get_db_session())
        result = db.execute("SELECT COUNT(*) FROM users").scalar()
        db.close()
        services_status["database"] = {
            "status": "healthy",
            "user_count": result
        }
    except Exception as e:
        services_status["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Redis (if configured)
    if os.getenv('REDIS_URL'):
        try:
            import redis
            r = redis.from_url(os.getenv('REDIS_URL'))
            r.ping()
            services_status["redis"] = {"status": "healthy"}
        except Exception as e:
            services_status["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    health_data["services"] = services_status
    
    # System metrics
    cpu_info = {
        "percent": psutil.cpu_percent(interval=1),
        "count": psutil.cpu_count(),
        "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }
    
    memory = psutil.virtual_memory()
    memory_info = {
        "total": memory.total,
        "available": memory.available,
        "percent": memory.percent,
        "used": memory.used
    }
    
    disk = psutil.disk_usage('/')
    disk_info = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent
    }
    
    # Network
    net_io = psutil.net_io_counters()
    network_info = {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv
    }
    
    health_data["system"] = {
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "network": network_info,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }
    
    # Application metrics
    app_summary = metrics_collector.get_metrics_summary()
    health_data["application"] = app_summary
    
    # Log access
    audit_logger.log_event(
        event_type=AuditEventType.DATA_VIEW,
        user_id=current_user['user_id'],
        username=current_user['username'],
        resource_type='monitoring',
        resource_id='health_detailed',
        action='view'
    )
    
    return health_data


@router.get("/metrics")
async def get_metrics(
    format: str = Query("json", description="Output format: json or prometheus")
):
    """
    Get application metrics
    Supports JSON and Prometheus formats
    """
    if format == "prometheus":
        # Return Prometheus format
        content = metrics_collector.export_prometheus_format()
        return content
    else:
        # Return JSON format
        return metrics_collector.get_metrics_summary()


@router.get("/metrics/history/{metric_name}")
async def get_metric_history(
    metric_name: str,
    minutes: int = Query(60, description="Number of minutes of history")
):
    """Get historical data for a specific metric"""
    history = metrics_collector.get_metric_history(metric_name, minutes)
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"Metric '{metric_name}' not found"
        )
    
    return {
        "metric": metric_name,
        "period_minutes": minutes,
        "data_points": len(history),
        "history": history
    }


@router.get("/logs/audit", dependencies=[Depends(require_admin)])
async def get_audit_logs(
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Query audit logs with filters
    Requires admin access
    """
    # Convert event_type string to enum if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event_type}"
            )
    
    # Default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    # Query logs
    logs = audit_logger.query_logs(
        user_id=user_id,
        event_type=event_type_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    # Log access
    audit_logger.log_event(
        event_type=AuditEventType.DATA_VIEW,
        user_id=current_user['user_id'],
        username=current_user['username'],
        resource_type='audit_logs',
        action='query',
        details={
            'filters': {
                'user_id': user_id,
                'event_type': event_type,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'date_range': f"{start_date.isoformat()} to {end_date.isoformat()}"
            },
            'results_count': len(logs)
        }
    )
    
    return {
        "total": len(logs),
        "limit": limit,
        "filters": {
            "user_id": user_id,
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "logs": logs
    }


@router.get("/logs/compliance-report", dependencies=[Depends(require_admin)])
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Generate compliance report from audit logs
    Requires admin access
    """
    report = audit_logger.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )
    
    # Log report generation
    audit_logger.log_event(
        event_type=AuditEventType.DATA_EXPORT,
        user_id=current_user['user_id'],
        username=current_user['username'],
        resource_type='compliance_report',
        action='generate',
        details={
            'date_range': f"{start_date.isoformat()} to {end_date.isoformat()}",
            'filter_user_id': user_id
        }
    )
    
    return report


@router.get("/errors/recent", dependencies=[Depends(require_admin)])
async def get_recent_errors(current_user: dict = Depends(get_current_active_user)):
    """
    Get recent application errors
    Requires admin access
    """
    # Get error stats from logger handlers
    from monitoring.logger_config import setup_logging
    handlers = setup_logging(
        enable_error_tracking=True,
        enable_performance_tracking=True
    )
    
    error_stats = {}
    if 'error_handler' in handlers:
        error_stats = handlers['error_handler'].get_error_stats()
    
    return error_stats


@router.get("/performance/stats", dependencies=[Depends(require_admin)])
async def get_performance_stats(current_user: dict = Depends(get_current_active_user)):
    """
    Get application performance statistics
    Requires admin access
    """
    # Get performance stats from logger handlers
    from monitoring.logger_config import setup_logging
    handlers = setup_logging(
        enable_error_tracking=True,
        enable_performance_tracking=True
    )
    
    perf_stats = {}
    if 'performance_handler' in handlers:
        perf_stats = handlers['performance_handler'].get_performance_stats()
    
    return perf_stats


@router.post("/test/error")
async def test_error_logging(current_user: dict = Depends(get_current_active_user)):
    """
    Test endpoint to trigger error logging
    For development/testing only
    """
    if os.getenv('ENVIRONMENT', 'production') == 'production':
        raise HTTPException(
            status_code=403,
            detail="Test endpoints disabled in production"
        )
    
    # Log test error
    logger.error(
        "Test error triggered by user",
        extra={
            'user_id': current_user['user_id'],
            'test': True
        }
    )
    
    # Trigger audit log
    audit_logger.log_event(
        event_type=AuditEventType.DATA_CREATE,
        user_id=current_user['user_id'],
        username=current_user['username'],
        resource_type='test',
        resource_id='error_log',
        action='test_error'
    )
    
    # Record test metrics
    app_metrics.track_request(
        method='POST',
        path='/monitoring/test/error',
        status_code=200,
        duration_ms=100
    )
    
    return {
        "message": "Test error logged successfully",
        "check_logs": True
    }