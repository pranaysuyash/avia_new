"""
Quality Assessment Pydantic Schemas
Request and response schemas for quality assessment API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class QualityLevel(str, Enum):
    """Quality level enumeration"""
    EXCELLENT = "EXCELLENT"
    VERY_GOOD = "VERY_GOOD"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class TrendDirection(str, Enum):
    """Trend direction enumeration"""
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    VOLATILE = "VOLATILE"


class CompetitivePosition(str, Enum):
    """Competitive position enumeration"""
    LEADING = "leading"
    COMPETITIVE = "competitive"
    LAGGING = "lagging"


class QualityDimensionScore(BaseModel):
    """Individual quality dimension score"""
    score: float = Field(..., ge=0, le=100, description="Quality score for this dimension (0-100)")
    level: QualityLevel = Field(..., description="Quality level classification")
    details: str = Field(..., description="Detailed explanation of the score")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in the assessment (0-1)")
    evidence_count: int = Field(default=0, description="Number of evidence points collected")

    class Config:
        schema_extra = {
            "example": {
                "score": 87.5,
                "level": "VERY_GOOD",
                "details": "High accuracy with minor terminology inconsistencies",
                "suggestions": ["Review medical abbreviations", "Standardize drug names"],
                "confidence": 0.92,
                "evidence_count": 15
            }
        }


class MedicalSchemaCoverage(BaseModel):
    """Medical schema coverage analysis"""
    patient_information: bool = Field(default=False, description="Patient demographic information covered")
    clinical_data: bool = Field(default=False, description="Clinical findings and diagnoses covered")
    social_determinants: bool = Field(default=False, description="Social determinants of health addressed")
    preventive_care: bool = Field(default=False, description="Preventive care measures documented")
    medication_management: bool = Field(default=False, description="Medication information included")
    care_quality_assessment: bool = Field(default=False, description="Quality of care indicators present")

    @property
    def coverage_percentage(self) -> float:
        """Calculate overall coverage percentage"""
        covered_count = sum([
            self.patient_information,
            self.clinical_data,
            self.social_determinants,
            self.preventive_care,
            self.medication_management,
            self.care_quality_assessment
        ])
        return (covered_count / 6) * 100

    class Config:
        schema_extra = {
            "example": {
                "patient_information": True,
                "clinical_data": True,
                "social_determinants": False,
                "preventive_care": True,
                "medication_management": True,
                "care_quality_assessment": False
            }
        }


class QualityAssessmentCreate(BaseModel):
    """Request schema for creating a quality assessment"""
    transcript: str = Field(..., min_length=1, description="Transcript content to assess")
    transcript_id: str = Field(..., description="Unique identifier for the transcript")
    context: Optional[str] = Field("general", description="Assessment context (general, medical_standard, medical_critical)")
    enable_medical_features: bool = Field(default=False, description="Enable medical-specific quality assessment")
    compliance_level: str = Field(default="standard", description="Compliance level (standard, hipaa, gdpr)")
    
    @validator('transcript')
    def validate_transcript_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Transcript content cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Transcript content too short for meaningful assessment')
        return v.strip()
    
    @validator('context')
    def validate_context(cls, v):
        valid_contexts = ['general', 'medical_standard', 'medical_critical', 'legal', 'research']
        if v not in valid_contexts:
            raise ValueError(f'Context must be one of: {valid_contexts}')
        return v
    
    @validator('compliance_level')
    def validate_compliance_level(cls, v):
        valid_levels = ['standard', 'hipaa', 'gdpr', 'sox', 'pci']
        if v not in valid_levels:
            raise ValueError(f'Compliance level must be one of: {valid_levels}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "transcript": "Patient presented with chest pain and shortness of breath. Vital signs were stable. Prescribed beta-blockers and scheduled follow-up.",
                "transcript_id": "transcript_12345",
                "context": "medical_standard",
                "enable_medical_features": True,
                "compliance_level": "hipaa"
            }
        }


class QualityAssessmentResponse(BaseModel):
    """Response schema for quality assessment"""
    id: str = Field(..., description="Unique assessment identifier")
    transcript_id: str = Field(..., description="Associated transcript identifier")
    overall_score: float = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    overall_level: QualityLevel = Field(..., description="Overall quality level")
    dimension_scores: Dict[str, QualityDimensionScore] = Field(..., description="Scores by quality dimension")
    summary: str = Field(..., description="Executive summary of quality assessment")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas needing improvement")
    medical_schema_coverage: Optional[MedicalSchemaCoverage] = Field(None, description="Medical schema coverage (if enabled)")
    processing_time: float = Field(..., description="Processing time in milliseconds")
    assessment_timestamp: datetime = Field(..., description="When the assessment was performed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "id": "qa_67890",
                "transcript_id": "transcript_12345",
                "overall_score": 87.5,
                "overall_level": "VERY_GOOD",
                "dimension_scores": {
                    "accuracy": {
                        "score": 92.0,
                        "level": "EXCELLENT",
                        "details": "High transcription accuracy with minimal errors",
                        "suggestions": ["Review proper nouns"],
                        "confidence": 0.95,
                        "evidence_count": 23
                    }
                },
                "summary": "High-quality medical transcription with good coverage of clinical information",
                "recommendations": ["Improve medication name accuracy", "Add patient demographics"],
                "strengths": ["Clear clinical documentation", "Proper medical terminology"],
                "weaknesses": ["Missing social history", "Incomplete medication list"],
                "processing_time": 2847.5,
                "assessment_timestamp": "2024-01-15T10:30:45Z"
            }
        }


class QualityTrendResponse(BaseModel):
    """Quality trend analysis response"""
    dimension: str = Field(..., description="Quality dimension name")
    trend_direction: TrendDirection = Field(..., description="Trend direction")
    trend_strength: float = Field(..., ge=0, le=1, description="Strength of the trend (0-1)")
    slope: float = Field(..., description="Rate of change (points per day)")
    projected_score_30_days: float = Field(..., ge=0, le=100, description="Projected score in 30 days")
    prediction_confidence: float = Field(..., ge=0, le=1, description="Confidence in projection (0-1)")
    data_points: int = Field(..., description="Number of data points used for analysis")

    class Config:
        schema_extra = {
            "example": {
                "dimension": "medical_accuracy",
                "trend_direction": "IMPROVING",
                "trend_strength": 0.75,
                "slope": 0.3,
                "projected_score_30_days": 91.2,
                "prediction_confidence": 0.88,
                "data_points": 15
            }
        }


class BenchmarkComparisonResponse(BaseModel):
    """Benchmark comparison response"""
    dimension: str = Field(..., description="Quality dimension name")
    current_score: float = Field(..., ge=0, le=100, description="Current score for this dimension")
    industry_benchmark: float = Field(..., ge=0, le=100, description="Industry benchmark score")
    percentile_rank: float = Field(..., ge=0, le=100, description="Percentile rank compared to industry")
    gap_analysis: str = Field(..., description="Analysis of the performance gap")
    improvement_potential: float = Field(..., ge=0, description="Potential improvement in points")
    competitive_position: CompetitivePosition = Field(..., description="Competitive position")

    @property
    def performance_gap(self) -> float:
        """Calculate performance gap"""
        return self.current_score - self.industry_benchmark

    class Config:
        schema_extra = {
            "example": {
                "dimension": "accuracy",
                "current_score": 87.5,
                "industry_benchmark": 85.0,
                "percentile_rank": 75.0,
                "gap_analysis": "Exceeds benchmark by 2.5 points (2.9%)",
                "improvement_potential": 8.5,
                "competitive_position": "competitive"
            }
        }


class QualityMetricsResponse(BaseModel):
    """Comprehensive quality metrics response"""
    overall_quality_index: float = Field(..., ge=0, le=100, description="Overall quality index")
    dimension_averages: Dict[str, float] = Field(..., description="Average scores by dimension")
    trend_analysis: List[QualityTrendResponse] = Field(default_factory=list, description="Trend analysis results")
    benchmark_comparisons: List[BenchmarkComparisonResponse] = Field(default_factory=list, description="Benchmark comparisons")
    risk_indicators: Dict[str, float] = Field(default_factory=dict, description="Risk indicator scores (0-1)")
    improvement_opportunities: List[str] = Field(default_factory=list, description="Identified improvement opportunities")
    quality_volatility: float = Field(..., ge=0, description="Quality volatility percentage")
    metric_reliability_score: float = Field(..., ge=0, le=100, description="Reliability of metrics")
    assessment_confidence: float = Field(..., ge=0, le=100, description="Confidence in assessments")
    analysis_period_days: int = Field(..., description="Number of days analyzed")
    total_assessments: int = Field(..., description="Total number of assessments analyzed")
    timestamp: datetime = Field(..., description="When metrics were calculated")

    class Config:
        schema_extra = {
            "example": {
                "overall_quality_index": 87.3,
                "dimension_averages": {
                    "accuracy": 89.2,
                    "completeness": 85.7,
                    "medical_accuracy": 91.1
                },
                "trend_analysis": [],
                "benchmark_comparisons": [],
                "risk_indicators": {
                    "overall_quality_risk": 0.2,
                    "medical_accuracy_risk": 0.1
                },
                "improvement_opportunities": [
                    "Focus on completeness improvement",
                    "Standardize medication terminology"
                ],
                "quality_volatility": 12.5,
                "metric_reliability_score": 94.2,
                "assessment_confidence": 91.8,
                "analysis_period_days": 30,
                "total_assessments": 25,
                "timestamp": "2024-01-15T10:30:45Z"
            }
        }


class QualityAssessmentListResponse(BaseModel):
    """Paginated list of quality assessments"""
    assessments: List[QualityAssessmentResponse] = Field(..., description="List of quality assessments")
    total_count: int = Field(..., description="Total number of assessments")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    class Config:
        schema_extra = {
            "example": {
                "assessments": [],
                "total_count": 157,
                "page": 1,
                "page_size": 20,
                "total_pages": 8
            }
        }


class QualityAlertCreate(BaseModel):
    """Schema for creating quality alerts"""
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    title: str = Field(..., max_length=200, description="Alert title")
    message: str = Field(..., description="Alert message")
    trigger_data: Dict[str, Any] = Field(default_factory=dict, description="Data that triggered the alert")
    threshold_values: Dict[str, Any] = Field(default_factory=dict, description="Threshold values used")

    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if v.upper() not in valid_severities:
            raise ValueError(f'Severity must be one of: {valid_severities}')
        return v.upper()

    class Config:
        schema_extra = {
            "example": {
                "alert_type": "score_drop",
                "severity": "MEDIUM",
                "title": "Quality Score Drop Detected",
                "message": "Medical accuracy score dropped by 15 points in the last assessment",
                "trigger_data": {
                    "previous_score": 92.0,
                    "current_score": 77.0,
                    "drop_percentage": 16.3
                },
                "threshold_values": {
                    "max_drop_threshold": 10.0
                }
            }
        }


class QualityAlertResponse(BaseModel):
    """Quality alert response schema"""
    id: str = Field(..., description="Alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    status: str = Field(..., description="Alert status")
    trigger_data: Dict[str, Any] = Field(default_factory=dict, description="Data that triggered the alert")
    threshold_values: Dict[str, Any] = Field(default_factory=dict, description="Threshold values used")
    created_at: datetime = Field(..., description="When the alert was created")
    acknowledged_at: Optional[datetime] = Field(None, description="When the alert was acknowledged")
    resolved_at: Optional[datetime] = Field(None, description="When the alert was resolved")

    class Config:
        schema_extra = {
            "example": {
                "id": "alert_12345",
                "alert_type": "hipaa_violation",
                "severity": "HIGH",
                "title": "Potential PHI Violation Detected",
                "message": "Patient name may be present in transcript",
                "status": "ACTIVE",
                "trigger_data": {
                    "violation_type": "patient_name",
                    "confidence": 0.87
                },
                "threshold_values": {
                    "phi_confidence_threshold": 0.8
                },
                "created_at": "2024-01-15T10:30:45Z",
                "acknowledged_at": None,
                "resolved_at": None
            }
        }


class QualityConfigUpdate(BaseModel):
    """Schema for updating quality configuration"""
    default_context: Optional[str] = Field(None, description="Default assessment context")
    enable_medical_features: Optional[bool] = Field(None, description="Enable medical features")
    compliance_level: Optional[str] = Field(None, description="Compliance level")
    quality_thresholds: Optional[Dict[str, float]] = Field(None, description="Quality score thresholds")
    alert_settings: Optional[Dict[str, Any]] = Field(None, description="Alert configuration")
    dimension_weights: Optional[Dict[str, float]] = Field(None, description="Custom dimension weights")
    processing_settings: Optional[Dict[str, Any]] = Field(None, description="Processing configuration")

    @validator('quality_thresholds')
    def validate_thresholds(cls, v):
        if v:
            for key, value in v.items():
                if not isinstance(value, (int, float)) or value < 0 or value > 100:
                    raise ValueError(f'Threshold {key} must be between 0 and 100')
        return v

    class Config:
        schema_extra = {
            "example": {
                "default_context": "medical_standard",
                "enable_medical_features": True,
                "compliance_level": "hipaa",
                "quality_thresholds": {
                    "overall_score_minimum": 80.0,
                    "medical_accuracy_minimum": 95.0
                },
                "alert_settings": {
                    "enable_score_drop_alerts": True,
                    "score_drop_threshold": 15.0
                }
            }
        }


class QualityConfigResponse(BaseModel):
    """Quality configuration response"""
    id: str = Field(..., description="Configuration identifier")
    user_id: int = Field(..., description="Associated user ID")
    default_context: str = Field(..., description="Default assessment context")
    enable_medical_features: bool = Field(..., description="Medical features enabled")
    compliance_level: str = Field(..., description="Compliance level")
    quality_thresholds: Dict[str, float] = Field(..., description="Quality score thresholds")
    alert_settings: Dict[str, Any] = Field(..., description="Alert configuration")
    dimension_weights: Dict[str, float] = Field(default_factory=dict, description="Custom dimension weights")
    processing_settings: Dict[str, Any] = Field(..., description="Processing configuration")
    created_at: datetime = Field(..., description="Configuration creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        schema_extra = {
            "example": {
                "id": "config_12345",
                "user_id": 42,
                "default_context": "medical_standard",
                "enable_medical_features": True,
                "compliance_level": "hipaa",
                "quality_thresholds": {
                    "overall_score_minimum": 75.0,
                    "accuracy_minimum": 85.0,
                    "medical_accuracy_minimum": 90.0,
                    "hipaa_compliance_minimum": 95.0
                },
                "alert_settings": {
                    "enable_score_drop_alerts": True,
                    "score_drop_threshold": 10.0,
                    "enable_hipaa_violation_alerts": True
                },
                "dimension_weights": {},
                "processing_settings": {
                    "enable_advanced_analytics": True,
                    "cache_duration_hours": 24
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:45Z"
            }
        }