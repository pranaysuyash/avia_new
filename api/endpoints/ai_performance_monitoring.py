#!/usr/bin/env python3
"""
FastAPI endpoints for AI Performance Monitoring System
RESTful API for performance monitoring and analytics
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json

from ai_performance_monitoring import (
    PerformanceMonitor, RequestMetrics, AlertThreshold, PerformanceAlert,
    MetricType, AlertSeverity, ResourceUsage, TrendAnalysis
)

# Global monitor instance
monitor = PerformanceMonitor()
monitor.start_monitoring()

# Create router
router = APIRouter(prefix="/api/v1/performance", tags=["Performance Monitoring"])

# Pydantic models for API
class RequestMetricsCreate(BaseModel):
    """Request metrics creation model"""
    request_id: str
    model_id: str
    provider: str
    start_time: datetime
    end_time: datetime
    latency_ms: float
    success: bool
    error_type: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    quality_score: float = 0.0
    resource_usage: Optional[Dict[str, float]] = None

class AlertThresholdCreate(BaseModel):
    """Alert threshold creation model"""
    metric_type: str
    threshold_value: float
    comparison: str = Field(..., regex="^(gt|lt|eq)$")
    severity: str
    enabled: bool = True

class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model"""
    model_id: str
    provider: str
    timeframe_start: datetime
    timeframe_end: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    avg_quality_score: float
    total_cost: float
    avg_cost_per_request: float

class TrendAnalysisResponse(BaseModel):
    """Trend analysis response model"""
    model_id: str
    metric_type: str
    trend_direction: str
    trend_strength: float
    prediction: float
    confidence: float
    analysis_period_hours: float
    data_points: int

class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    timestamp: datetime
    model_id: str
    provider: str
    metric_type: str
    current_value: float
    threshold_value: float
    severity: str
    message: str
    resolved: bool

@router.post("/requests", response_model=Dict[str, str])
async def track_request(request_data: RequestMetricsCreate):
    """Track a new AI request for performance monitoring"""
    try:
        # Convert resource usage
        resource_usage = ResourceUsage()
        if request_data.resource_usage:
            resource_usage = ResourceUsage(
                cpu_percent=request_data.resource_usage.get("cpu_percent", 0.0),
                memory_mb=request_data.resource_usage.get("memory_mb", 0.0),
                gpu_percent=request_data.resource_usage.get("gpu_percent", 0.0),
                network_mbps=request_data.resource_usage.get("network_mbps", 0.0),
                storage_mb=request_data.resource_usage.get("storage_mb", 0.0)
            )
        
        # Create request metrics
        metrics = RequestMetrics(
            request_id=request_data.request_id,
            model_id=request_data.model_id,
            provider=request_data.provider,
            start_time=request_data.start_time,
            end_time=request_data.end_time,
            latency_ms=request_data.latency_ms,
            success=request_data.success,
            error_type=request_data.error_type,
            input_tokens=request_data.input_tokens,
            output_tokens=request_data.output_tokens,
            cost=request_data.cost,
            quality_score=request_data.quality_score,
            resource_usage=resource_usage
        )
        
        # Track the request
        monitor.track_request(metrics)
        
        return {"status": "success", "message": "Request tracked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking request: {str(e)}")

@router.get("/metrics/{model_id}", response_model=Optional[PerformanceMetricsResponse])
async def get_performance_metrics(
    model_id: str,
    provider: Optional[str] = None,
    timeframe_hours: float = Query(1.0, ge=0.1, le=168.0)
):
    """Get performance metrics for a specific model"""
    try:
        timeframe = timedelta(hours=timeframe_hours)
        metrics = monitor.get_performance_metrics(model_id, provider, timeframe)
        
        if not metrics:
            return None
        
        return PerformanceMetricsResponse(
            model_id=metrics.model_id,
            provider=metrics.provider,
            timeframe_start=metrics.timeframe_start,
            timeframe_end=metrics.timeframe_end,
            total_requests=metrics.total_requests,
            successful_requests=metrics.successful_requests,
            failed_requests=metrics.failed_requests,
            avg_latency_ms=metrics.avg_latency_ms,
            p95_latency_ms=metrics.p95_latency_ms,
            p99_latency_ms=metrics.p99_latency_ms,
            throughput_rps=metrics.throughput_rps,
            error_rate=metrics.error_rate,
            avg_quality_score=metrics.avg_quality_score,
            total_cost=metrics.total_cost,
            avg_cost_per_request=metrics.avg_cost_per_request
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@router.get("/realtime/{model_id}")
async def get_realtime_metrics(model_id: str):
    """Get real-time performance metrics for a model"""
    try:
        metrics = monitor.get_realtime_metrics(model_id)
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting real-time metrics: {str(e)}")

@router.get("/trends/{model_id}", response_model=Optional[TrendAnalysisResponse])
async def analyze_trends(
    model_id: str,
    metric_type: str = Query(..., regex="^(latency|throughput|accuracy|error_rate|resource_usage|cost|availability)$"),
    period_hours: float = Query(24.0, ge=1.0, le=720.0)
):
    """Analyze performance trends for a model and metric"""
    try:
        # Convert string to MetricType enum
        metric_enum = MetricType(metric_type)
        period = timedelta(hours=period_hours)
        
        trend = monitor.analyze_trends(model_id, metric_enum, period)
        
        if not trend:
            return None
        
        return TrendAnalysisResponse(
            model_id=trend.model_id,
            metric_type=trend.metric_type.value,
            trend_direction=trend.trend_direction,
            trend_strength=trend.trend_strength,
            prediction=trend.prediction,
            confidence=trend.confidence,
            analysis_period_hours=trend.analysis_period.total_seconds() / 3600,
            data_points=trend.data_points
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trends: {str(e)}")

@router.post("/alerts/{model_id}")
async def set_alert_threshold(model_id: str, threshold_data: AlertThresholdCreate):
    """Set an alert threshold for a model"""
    try:
        # Convert strings to enums
        metric_type = MetricType(threshold_data.metric_type)
        severity = AlertSeverity(threshold_data.severity)
        
        threshold = AlertThreshold(
            metric_type=metric_type,
            threshold_value=threshold_data.threshold_value,
            comparison=threshold_data.comparison,
            severity=severity,
            enabled=threshold_data.enabled
        )
        
        monitor.set_alert_threshold(model_id, threshold)
        
        return {"status": "success", "message": f"Alert threshold set for {model_id}"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting alert threshold: {str(e)}")

@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(model_id: Optional[str] = None):
    """Get active performance alerts"""
    try:
        alerts = monitor.get_active_alerts(model_id)
        
        return [
            AlertResponse(
                id=alert.id,
                timestamp=alert.timestamp,
                model_id=alert.model_id,
                provider=alert.provider,
                metric_type=alert.metric_type.value,
                current_value=alert.current_value,
                threshold_value=alert.threshold_value,
                severity=alert.severity.value,
                message=alert.message,
                resolved=alert.resolved
            )
            for alert in alerts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve a performance alert"""
    try:
        resolved = monitor.resolve_alert(alert_id)
        
        if resolved:
            return {"status": "success", "message": f"Alert {alert_id} resolved"}
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")

@router.get("/compare")
async def compare_models(
    model_ids: List[str] = Query(...),
    metric_type: str = Query("latency", regex="^(latency|throughput|accuracy|error_rate|resource_usage|cost|availability)$"),
    timeframe_hours: float = Query(1.0, ge=0.1, le=168.0)
):
    """Compare performance metrics across multiple models"""
    try:
        metric_enum = MetricType(metric_type)
        timeframe = timedelta(hours=timeframe_hours)
        
        comparison = monitor.get_model_comparison(model_ids, metric_enum, timeframe)
        
        return comparison
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing models: {str(e)}")

@router.get("/export")
async def export_metrics(format_type: str = Query("json", regex="^(json)$")):
    """Export performance metrics"""
    try:
        export_data = monitor.export_metrics(format_type)
        
        if format_type == "json":
            return JSONResponse(
                content=json.loads(export_data),
                headers={"Content-Disposition": f"attachment; filename=performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")

@router.get("/models")
async def get_monitored_models():
    """Get list of models being monitored"""
    try:
        models = set()
        
        # Get models from request history
        if hasattr(monitor, 'request_history'):
            for req in monitor.request_history:
                models.add(req.model_id)
        
        return {"models": sorted(list(models))}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitored models: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring system"""
    try:
        return {
            "status": "healthy",
            "monitoring_active": monitor._monitoring_active,
            "total_requests_tracked": len(monitor.request_history),
            "active_alerts": len([a for a in monitor.active_alerts.values() if not a.resolved]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.delete("/data")
async def clear_monitoring_data():
    """Clear all monitoring data (use with caution)"""
    try:
        # Create new monitor instance to clear data
        global monitor
        old_monitor = monitor
        old_monitor.stop_monitoring()
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        return {"status": "success", "message": "All monitoring data cleared"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")

# Include router in main app
def get_router():
    """Get the performance monitoring router"""
    return router