"""
Quality Assessment API Endpoints
RESTful API endpoints for comprehensive quality assessment functionality
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
import logging
from io import BytesIO
import pandas as pd

from api.database import get_db
from api.models.quality_assessment import QualityAssessment as QualityAssessmentModel
from api.schemas.quality_assessment import (
    QualityAssessmentCreate,
    QualityAssessmentResponse,
    QualityMetricsResponse,
    QualityTrendResponse,
    BenchmarkComparisonResponse,
    QualityAssessmentListResponse
)
from api.dependencies import get_current_user, get_api_key_user
from api.middleware.rate_limiting import rate_limit
from api.middleware.audit_logging import log_api_call
from quality_assessment_system import QualityAssessmentEngine, QualityDimension
from quality_metrics_engine import QualityMetricsEngine
from services.audit_logging_service import audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/quality", tags=["Quality Assessment"])

# Initialize engines
quality_engine = QualityAssessmentEngine()
metrics_engine = QualityMetricsEngine()

@router.post(
    "/assess",
    response_model=QualityAssessmentResponse,
    summary="Run Quality Assessment",
    description="Perform comprehensive quality assessment on a transcript with medical schema integration"
)
@rate_limit(requests=50, window=3600)  # 50 requests per hour
@log_api_call(operation="quality_assessment")
async def assess_transcript_quality(
    assessment_data: QualityAssessmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> QualityAssessmentResponse:
    """
    Run comprehensive quality assessment on a transcript.
    
    Features:
    - Multi-dimensional quality scoring
    - Medical schema coverage analysis (if enabled)
    - HIPAA compliance checking
    - Detailed recommendations and suggestions
    - Confidence scoring and evidence collection
    """
    try:
        logger.info(f"Starting quality assessment for user {current_user.id}")
        
        # Validate input
        if not assessment_data.transcript.strip():
            raise HTTPException(status_code=400, detail="Transcript content cannot be empty")
        
        # Prepare metadata
        metadata = {
            'user_id': current_user.id,
            'medical_features_enabled': assessment_data.enable_medical_features,
            'compliance_level': assessment_data.compliance_level,
            'context': assessment_data.context or 'general'
        }
        
        # Run quality assessment
        assessment_result = quality_engine.assess_transcript_quality(
            transcript=assessment_data.transcript,
            transcript_id=assessment_data.transcript_id,
            metadata=metadata
        )
        
        # Save to database
        db_assessment = QualityAssessmentModel(
            id=assessment_result.id,
            transcript_id=assessment_result.transcript_id,
            user_id=current_user.id,
            overall_score=assessment_result.overall_score,
            overall_level=assessment_result.overall_level.value,
            dimension_scores=_serialize_dimension_scores(assessment_result.dimension_scores),
            summary=assessment_result.summary,
            recommendations=assessment_result.recommendations,
            strengths=assessment_result.strengths,
            weaknesses=assessment_result.weaknesses,
            metadata=assessment_result.metadata,
            processing_time=assessment_result.processing_time,
            assessment_timestamp=assessment_result.assessment_timestamp
        )
        
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)
        
        # Background task for metrics calculation
        background_tasks.add_task(
            _update_quality_metrics,
            current_user.id,
            db_assessment.id
        )
        
        # Audit log
        await audit_log(
            db,
            user_id=current_user.id,
            action="quality_assessment_completed",
            resource_type="transcript",
            resource_id=assessment_data.transcript_id,
            metadata={
                "overall_score": assessment_result.overall_score,
                "medical_features_enabled": assessment_data.enable_medical_features,
                "processing_time_ms": assessment_result.processing_time
            }
        )
        
        logger.info(f"Quality assessment completed: {assessment_result.overall_score:.1f}%")
        
        return QualityAssessmentResponse(
            id=assessment_result.id,
            transcript_id=assessment_result.transcript_id,
            overall_score=assessment_result.overall_score,
            overall_level=assessment_result.overall_level.value,
            dimension_scores=_format_dimension_scores(assessment_result.dimension_scores),
            summary=assessment_result.summary,
            recommendations=assessment_result.recommendations,
            strengths=assessment_result.strengths,
            weaknesses=assessment_result.weaknesses,
            medical_schema_coverage=assessment_result.metadata.get('medical_schema_coverage'),
            processing_time=assessment_result.processing_time,
            assessment_timestamp=assessment_result.assessment_timestamp,
            metadata=assessment_result.metadata
        )
        
    except Exception as e:
        logger.error(f"Quality assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quality assessment failed: {str(e)}")


@router.get(
    "/assessments",
    response_model=QualityAssessmentListResponse,
    summary="List Quality Assessments",
    description="Get paginated list of quality assessments with filtering options"
)
@rate_limit(requests=100, window=3600)
@log_api_call(operation="list_quality_assessments")
async def list_quality_assessments(
    transcript_id: Optional[str] = Query(None, description="Filter by transcript ID"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum quality score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum quality score"),
    quality_level: Optional[str] = Query(None, description="Filter by quality level"),
    days_back: Optional[int] = Query(30, ge=1, le=365, description="Number of days to look back"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> QualityAssessmentListResponse:
    """
    Get paginated list of quality assessments with comprehensive filtering.
    """
    try:
        # Build query
        query = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.user_id == current_user.id
        )
        
        # Apply filters
        if transcript_id:
            query = query.filter(QualityAssessmentModel.transcript_id == transcript_id)
        
        if min_score is not None:
            query = query.filter(QualityAssessmentModel.overall_score >= min_score)
        
        if max_score is not None:
            query = query.filter(QualityAssessmentModel.overall_score <= max_score)
        
        if quality_level:
            query = query.filter(QualityAssessmentModel.overall_level == quality_level)
        
        # Time filter
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(QualityAssessmentModel.assessment_timestamp >= cutoff_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        assessments = query.order_by(
            QualityAssessmentModel.assessment_timestamp.desc()
        ).offset(offset).limit(page_size).all()
        
        # Format response
        assessment_list = []
        for assessment in assessments:
            assessment_list.append(QualityAssessmentResponse(
                id=assessment.id,
                transcript_id=assessment.transcript_id,
                overall_score=assessment.overall_score,
                overall_level=assessment.overall_level,
                dimension_scores=assessment.dimension_scores,
                summary=assessment.summary,
                recommendations=assessment.recommendations,
                strengths=assessment.strengths,
                weaknesses=assessment.weaknesses,
                medical_schema_coverage=assessment.metadata.get('medical_schema_coverage'),
                processing_time=assessment.processing_time,
                assessment_timestamp=assessment.assessment_timestamp,
                metadata=assessment.metadata
            ))
        
        return QualityAssessmentListResponse(
            assessments=assessment_list,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list quality assessments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assessments: {str(e)}")


@router.get(
    "/assessments/{assessment_id}",
    response_model=QualityAssessmentResponse,
    summary="Get Quality Assessment",
    description="Get detailed quality assessment by ID"
)
@rate_limit(requests=200, window=3600)
@log_api_call(operation="get_quality_assessment")
async def get_quality_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> QualityAssessmentResponse:
    """
    Get detailed quality assessment by ID.
    """
    try:
        assessment = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.id == assessment_id,
            QualityAssessmentModel.user_id == current_user.id
        ).first()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Quality assessment not found")
        
        return QualityAssessmentResponse(
            id=assessment.id,
            transcript_id=assessment.transcript_id,
            overall_score=assessment.overall_score,
            overall_level=assessment.overall_level,
            dimension_scores=assessment.dimension_scores,
            summary=assessment.summary,
            recommendations=assessment.recommendations,
            strengths=assessment.strengths,
            weaknesses=assessment.weaknesses,
            medical_schema_coverage=assessment.metadata.get('medical_schema_coverage'),
            processing_time=assessment.processing_time,
            assessment_timestamp=assessment.assessment_timestamp,
            metadata=assessment.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assessment: {str(e)}")


@router.get(
    "/metrics",
    response_model=QualityMetricsResponse,
    summary="Get Quality Metrics",
    description="Get comprehensive quality metrics and analytics"
)
@rate_limit(requests=50, window=3600)
@log_api_call(operation="get_quality_metrics")
async def get_quality_metrics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days for metrics calculation"),
    context: str = Query("medical_standard", description="Quality assessment context"),
    industry_type: str = Query("medical_transcription", description="Industry benchmark type"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> QualityMetricsResponse:
    """
    Get comprehensive quality metrics including trends, benchmarks, and risk indicators.
    """
    try:
        # Get assessments for metrics calculation
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        assessments = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.user_id == current_user.id,
            QualityAssessmentModel.assessment_timestamp >= cutoff_date
        ).order_by(QualityAssessmentModel.assessment_timestamp.asc()).all()
        
        if not assessments:
            raise HTTPException(status_code=404, detail="No quality assessments found for metrics calculation")
        
        # Convert to quality results format
        quality_results = []
        for assessment in assessments:
            dimension_scores = _deserialize_dimension_scores(assessment.dimension_scores)
            
            quality_result = type('QualityResult', (), {
                'id': assessment.id,
                'transcript_id': assessment.transcript_id,
                'overall_score': assessment.overall_score,
                'overall_level': assessment.overall_level,
                'dimension_scores': dimension_scores,
                'summary': assessment.summary,
                'recommendations': assessment.recommendations,
                'strengths': assessment.strengths,
                'weaknesses': assessment.weaknesses,
                'metadata': assessment.metadata,
                'assessment_timestamp': assessment.assessment_timestamp,
                'processing_time': assessment.processing_time
            })()
            
            quality_results.append(quality_result)
        
        # Calculate comprehensive metrics
        metrics_summary = metrics_engine.calculate_comprehensive_metrics(
            quality_results,
            context=context,
            industry_type=industry_type
        )
        
        # Format response
        return QualityMetricsResponse(
            overall_quality_index=metrics_summary.overall_quality_index,
            dimension_averages={k.value: v for k, v in metrics_summary.dimension_scores.items()},
            trend_analysis=[
                QualityTrendResponse(
                    dimension=trend.dimension.value,
                    trend_direction=trend.trend_direction.value,
                    trend_strength=trend.trend_strength,
                    slope=trend.slope,
                    projected_score_30_days=trend.projected_score_30_days,
                    prediction_confidence=trend.prediction_confidence,
                    data_points=trend.data_points
                ) for trend in metrics_summary.trend_analysis
            ],
            benchmark_comparisons=[
                BenchmarkComparisonResponse(
                    dimension=comp.dimension.value,
                    current_score=comp.current_score,
                    industry_benchmark=comp.industry_benchmark,
                    percentile_rank=comp.percentile_rank,
                    gap_analysis=comp.gap_analysis,
                    improvement_potential=comp.improvement_potential,
                    competitive_position=comp.competitive_position
                ) for comp in metrics_summary.benchmark_comparisons
            ],
            risk_indicators=metrics_summary.risk_indicators,
            improvement_opportunities=metrics_summary.improvement_opportunities,
            quality_volatility=metrics_summary.quality_volatility,
            metric_reliability_score=metrics_summary.metric_reliability_score,
            assessment_confidence=metrics_summary.assessment_confidence,
            analysis_period_days=days_back,
            total_assessments=len(quality_results),
            timestamp=metrics_summary.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate quality metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")


@router.get(
    "/trends/{dimension}",
    response_model=List[Dict[str, Any]],
    summary="Get Quality Dimension Trends",
    description="Get historical trends for a specific quality dimension"
)
@rate_limit(requests=100, window=3600)
@log_api_call(operation="get_dimension_trends")
async def get_dimension_trends(
    dimension: str,
    days_back: int = Query(90, ge=7, le=365, description="Number of days for trend analysis"),
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$", description="Data granularity"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get historical trends for a specific quality dimension with configurable granularity.
    """
    try:
        # Validate dimension
        valid_dimensions = [dim.value for dim in QualityDimension]
        if dimension not in valid_dimensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid dimension. Valid options: {valid_dimensions}"
            )
        
        # Get assessments
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        assessments = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.user_id == current_user.id,
            QualityAssessmentModel.assessment_timestamp >= cutoff_date
        ).order_by(QualityAssessmentModel.assessment_timestamp.asc()).all()
        
        if not assessments:
            return []
        
        # Extract dimension data
        trend_data = []
        for assessment in assessments:
            dimension_scores = assessment.dimension_scores
            if dimension in dimension_scores:
                trend_data.append({
                    'timestamp': assessment.assessment_timestamp.isoformat(),
                    'date': assessment.assessment_timestamp.strftime('%Y-%m-%d'),
                    'score': dimension_scores[dimension]['score'],
                    'level': dimension_scores[dimension]['level'],
                    'confidence': dimension_scores[dimension]['confidence']
                })
        
        # Group by granularity if needed
        if granularity != "daily" and len(trend_data) > 7:
            grouped_data = _group_trend_data(trend_data, granularity)
            return grouped_data
        
        return trend_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dimension trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")


@router.get(
    "/export",
    summary="Export Quality Data",
    description="Export quality assessment data in various formats (CSV, JSON, Excel)"
)
@rate_limit(requests=10, window=3600)
@log_api_call(operation="export_quality_data")
async def export_quality_data(
    format: str = Query("csv", regex="^(csv|json|excel)$", description="Export format"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to export"),
    include_details: bool = Query(True, description="Include detailed dimension scores"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Export quality assessment data in CSV, JSON, or Excel format.
    """
    try:
        # Get assessments
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        assessments = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.user_id == current_user.id,
            QualityAssessmentModel.assessment_timestamp >= cutoff_date
        ).order_by(QualityAssessmentModel.assessment_timestamp.desc()).all()
        
        if not assessments:
            raise HTTPException(status_code=404, detail="No quality assessments found for export")
        
        # Prepare data for export
        export_data = []
        for assessment in assessments:
            row = {
                'assessment_id': assessment.id,
                'transcript_id': assessment.transcript_id,
                'overall_score': assessment.overall_score,
                'overall_level': assessment.overall_level,
                'summary': assessment.summary,
                'processing_time_ms': assessment.processing_time,
                'assessment_timestamp': assessment.assessment_timestamp.isoformat()
            }
            
            if include_details:
                # Add dimension scores
                dimension_scores = assessment.dimension_scores
                for dim, scores in dimension_scores.items():
                    row[f'{dim}_score'] = scores['score']
                    row[f'{dim}_level'] = scores['level']
                    row[f'{dim}_confidence'] = scores['confidence']
            
            export_data.append(row)
        
        # Generate export based on format
        if format == "json":
            # JSON export
            content = json.dumps(export_data, indent=2, default=str)
            return StreamingResponse(
                BytesIO(content.encode()),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=quality_assessments_{datetime.utcnow().strftime('%Y%m%d')}.json"}
            )
        
        elif format == "csv":
            # CSV export
            df = pd.DataFrame(export_data)
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            return StreamingResponse(
                csv_buffer,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=quality_assessments_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
            )
        
        elif format == "excel":
            # Excel export
            df = pd.DataFrame(export_data)
            excel_buffer = BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Quality Assessments', index=False)
                
                # Add summary sheet
                if len(assessments) > 1:
                    summary_data = {
                        'Metric': ['Total Assessments', 'Average Score', 'Highest Score', 'Lowest Score'],
                        'Value': [
                            len(assessments),
                            sum(a.overall_score for a in assessments) / len(assessments),
                            max(a.overall_score for a in assessments),
                            min(a.overall_score for a in assessments)
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            excel_buffer.seek(0)
            return StreamingResponse(
                excel_buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=quality_assessments_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export quality data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.delete(
    "/assessments/{assessment_id}",
    summary="Delete Quality Assessment",
    description="Delete a quality assessment by ID"
)
@rate_limit(requests=50, window=3600)
@log_api_call(operation="delete_quality_assessment")
async def delete_quality_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a quality assessment by ID.
    """
    try:
        assessment = db.query(QualityAssessmentModel).filter(
            QualityAssessmentModel.id == assessment_id,
            QualityAssessmentModel.user_id == current_user.id
        ).first()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Quality assessment not found")
        
        # Audit log before deletion
        await audit_log(
            db,
            user_id=current_user.id,
            action="quality_assessment_deleted",
            resource_type="quality_assessment",
            resource_id=assessment_id,
            metadata={"overall_score": assessment.overall_score}
        )
        
        db.delete(assessment)
        db.commit()
        
        return {"message": "Quality assessment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete quality assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


# Helper functions
def _serialize_dimension_scores(dimension_scores: Dict[QualityDimension, Any]) -> Dict[str, Dict[str, Any]]:
    """Serialize dimension scores for database storage"""
    serialized = {}
    for dimension, metric in dimension_scores.items():
        serialized[dimension.value] = {
            'score': metric.score,
            'level': metric.level.value if hasattr(metric.level, 'value') else str(metric.level),
            'details': metric.details,
            'suggestions': metric.suggestions,
            'evidence': metric.evidence,
            'confidence': metric.confidence
        }
    return serialized


def _deserialize_dimension_scores(dimension_scores: Dict[str, Dict[str, Any]]) -> Dict[QualityDimension, Any]:
    """Deserialize dimension scores from database"""
    deserialized = {}
    for dimension_str, scores in dimension_scores.items():
        dimension = next((d for d in QualityDimension if d.value == dimension_str), None)
        if dimension:
            metric = type('DimensionMetric', (), {
                'score': scores['score'],
                'level': scores['level'],
                'details': scores['details'],
                'suggestions': scores['suggestions'],
                'evidence': scores['evidence'],
                'confidence': scores['confidence']
            })()
            deserialized[dimension] = metric
    return deserialized


def _format_dimension_scores(dimension_scores: Dict[QualityDimension, Any]) -> Dict[str, Dict[str, Any]]:
    """Format dimension scores for API response"""
    formatted = {}
    for dimension, metric in dimension_scores.items():
        formatted[dimension.value] = {
            'score': metric.score,
            'level': metric.level.value if hasattr(metric.level, 'value') else str(metric.level),
            'details': metric.details,
            'suggestions': metric.suggestions[:3],  # Limit suggestions for API response
            'confidence': metric.confidence,
            'evidence_count': len(metric.evidence) if isinstance(metric.evidence, dict) else 0
        }
    return formatted


def _group_trend_data(data: List[Dict[str, Any]], granularity: str) -> List[Dict[str, Any]]:
    """Group trend data by specified granularity"""
    if granularity == "daily":
        return data
    
    grouped = {}
    for item in data:
        date = datetime.fromisoformat(item['timestamp'])
        
        if granularity == "weekly":
            # Group by week (Monday as start of week)
            week_start = date - timedelta(days=date.weekday())
            key = week_start.strftime('%Y-%W')
            display_date = week_start.strftime('%Y-%m-%d')
        elif granularity == "monthly":
            # Group by month
            key = date.strftime('%Y-%m')
            display_date = date.strftime('%Y-%m-01')
        else:
            continue
        
        if key not in grouped:
            grouped[key] = {
                'scores': [],
                'confidences': [],
                'date': display_date
            }
        
        grouped[key]['scores'].append(item['score'])
        grouped[key]['confidences'].append(item['confidence'])
    
    # Calculate averages
    result = []
    for key, group in sorted(grouped.items()):
        avg_score = sum(group['scores']) / len(group['scores'])
        avg_confidence = sum(group['confidences']) / len(group['confidences'])
        
        # Determine level based on average score
        if avg_score >= 90:
            level = "EXCELLENT"
        elif avg_score >= 80:
            level = "VERY_GOOD"
        elif avg_score >= 70:
            level = "GOOD"
        elif avg_score >= 60:
            level = "FAIR"
        else:
            level = "POOR"
        
        result.append({
            'date': group['date'],
            'score': round(avg_score, 1),
            'level': level,
            'confidence': round(avg_confidence, 2),
            'data_points': len(group['scores'])
        })
    
    return result


async def _update_quality_metrics(user_id: int, assessment_id: str):
    """Background task to update quality metrics"""
    try:
        # This would typically update cached metrics or trigger analytics updates
        logger.info(f"Updating quality metrics for user {user_id} after assessment {assessment_id}")
        
        # In a production system, this might:
        # - Update cached metrics in Redis
        # - Trigger analytics pipelines
        # - Send notifications if quality drops significantly
        # - Update quality dashboards
        
    except Exception as e:
        logger.error(f"Failed to update quality metrics: {str(e)}")


# API Key endpoints (for programmatic access)
@router.post(
    "/api-key/assess",
    response_model=QualityAssessmentResponse,
    summary="API Key Quality Assessment",
    description="Run quality assessment using API key authentication"
)
@rate_limit(requests=100, window=3600)
async def api_key_assess_quality(
    assessment_data: QualityAssessmentCreate,
    db: Session = Depends(get_db),
    api_user = Depends(get_api_key_user)
):
    """
    API key version of quality assessment endpoint for programmatic access.
    """
    # Reuse the main assessment logic but with API key authentication
    return await assess_transcript_quality(
        assessment_data=assessment_data,
        background_tasks=BackgroundTasks(),
        db=db,
        current_user=api_user
    )