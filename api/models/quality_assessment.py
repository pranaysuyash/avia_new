"""
Quality Assessment Database Models
SQLAlchemy models for storing comprehensive quality assessment data
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from api.database import Base

class QualityAssessment(Base):
    """
    Quality Assessment model for storing comprehensive quality analysis results
    """
    __tablename__ = "quality_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transcript_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Overall quality metrics
    overall_score = Column(Float, nullable=False, index=True)
    overall_level = Column(String(20), nullable=False, index=True)  # EXCELLENT, VERY_GOOD, GOOD, FAIR, POOR
    
    # Dimension-specific scores (stored as JSONB for efficient querying)
    dimension_scores = Column(JSONB, nullable=False, default=dict)
    
    # Assessment results
    summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True, default=list)
    strengths = Column(JSON, nullable=True, default=list)
    weaknesses = Column(JSON, nullable=True, default=list)
    
    # Metadata and context
    metadata = Column(JSONB, nullable=True, default=dict)
    
    # Performance metrics
    processing_time = Column(Float, nullable=False)  # Processing time in milliseconds
    assessment_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quality_assessments")
    transcript = relationship("Transcript", back_populates="quality_assessments")

    # Indexes for performance
    __table_args__ = (
        Index('idx_quality_user_timestamp', 'user_id', 'assessment_timestamp'),
        Index('idx_quality_transcript_timestamp', 'transcript_id', 'assessment_timestamp'),
        Index('idx_quality_score_level', 'overall_score', 'overall_level'),
        Index('idx_quality_metadata_gin', 'metadata', postgresql_using='gin'),
        Index('idx_quality_dimensions_gin', 'dimension_scores', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<QualityAssessment(id={self.id}, score={self.overall_score:.1f}%, level={self.overall_level})>"


class QualityMetricsCache(Base):
    """
    Cached quality metrics for improved performance
    """
    __tablename__ = "quality_metrics_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Cache parameters
    context = Column(String(50), nullable=False, default="medical_standard")
    industry_type = Column(String(50), nullable=False, default="medical_transcription")
    days_back = Column(Integer, nullable=False, default=30)
    
    # Cached metrics data
    overall_quality_index = Column(Float, nullable=False)
    dimension_averages = Column(JSONB, nullable=False, default=dict)
    trend_analysis = Column(JSONB, nullable=False, default=list)
    benchmark_comparisons = Column(JSONB, nullable=False, default=list)
    risk_indicators = Column(JSONB, nullable=False, default=dict)
    improvement_opportunities = Column(JSON, nullable=False, default=list)
    
    # Metrics metadata
    quality_volatility = Column(Float, nullable=False, default=0.0)
    metric_reliability_score = Column(Float, nullable=False, default=0.0)
    assessment_confidence = Column(Float, nullable=False, default=0.0)
    
    # Analysis parameters
    total_assessments = Column(Integer, nullable=False, default=0)
    analysis_period_days = Column(Integer, nullable=False, default=30)
    
    # Cache management
    cache_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_valid = Column(Boolean, nullable=False, default=True, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quality_metrics_cache")

    # Indexes
    __table_args__ = (
        Index('idx_metrics_cache_user_context', 'user_id', 'context', 'industry_type'),
        Index('idx_metrics_cache_expiry', 'expires_at', 'is_valid'),
        Index('idx_metrics_cache_timestamp', 'cache_timestamp'),
    )

    def __repr__(self):
        return f"<QualityMetricsCache(user_id={self.user_id}, quality_index={self.overall_quality_index:.1f}%)>"


class QualityBenchmark(Base):
    """
    Industry quality benchmarks for comparison
    """
    __tablename__ = "quality_benchmarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Benchmark identification
    industry_type = Column(String(50), nullable=False, index=True)  # medical_transcription, legal_transcription, etc.
    benchmark_version = Column(String(20), nullable=False, default="1.0")
    
    # Benchmark data
    dimension_benchmarks = Column(JSONB, nullable=False, default=dict)
    percentile_data = Column(JSONB, nullable=False, default=dict)  # 25th, 50th, 75th, 90th percentiles
    
    # Metadata
    data_source = Column(String(100), nullable=True)
    sample_size = Column(Integer, nullable=True)
    collection_date = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    effective_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_benchmarks_industry_active', 'industry_type', 'is_active'),
        Index('idx_benchmarks_version', 'benchmark_version', 'effective_date'),
    )

    def __repr__(self):
        return f"<QualityBenchmark(industry={self.industry_type}, version={self.benchmark_version})>"


class QualityAlert(Base):
    """
    Quality alerts for monitoring and notifications
    """
    __tablename__ = "quality_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(String, ForeignKey("quality_assessments.id"), nullable=True, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # score_drop, hipaa_violation, consistency_issue
    severity = Column(String(20), nullable=False, index=True)    # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert data
    trigger_data = Column(JSONB, nullable=True, default=dict)
    threshold_values = Column(JSONB, nullable=True, default=dict)
    
    # Status
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quality_alerts")
    assessment = relationship("QualityAssessment", backref="alerts")

    # Indexes
    __table_args__ = (
        Index('idx_alerts_user_status', 'user_id', 'status'),
        Index('idx_alerts_type_severity', 'alert_type', 'severity'),
        Index('idx_alerts_created', 'created_at'),
    )

    def __repr__(self):
        return f"<QualityAlert(type={self.alert_type}, severity={self.severity}, status={self.status})>"


class QualityConfig(Base):
    """
    User-specific quality assessment configuration
    """
    __tablename__ = "quality_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Configuration settings
    default_context = Column(String(50), nullable=False, default="medical_standard")
    enable_medical_features = Column(Boolean, nullable=False, default=False)
    compliance_level = Column(String(20), nullable=False, default="standard")
    
    # Quality thresholds
    quality_thresholds = Column(JSONB, nullable=False, default={
        'overall_score_minimum': 75.0,
        'accuracy_minimum': 85.0,
        'medical_accuracy_minimum': 90.0,
        'hipaa_compliance_minimum': 95.0
    })
    
    # Alert settings
    alert_settings = Column(JSONB, nullable=False, default={
        'enable_score_drop_alerts': True,
        'score_drop_threshold': 10.0,
        'enable_hipaa_violation_alerts': True,
        'enable_consistency_alerts': True,
        'notification_channels': ['email']
    })
    
    # Weight configurations
    dimension_weights = Column(JSONB, nullable=True, default=dict)
    
    # Processing settings
    processing_settings = Column(JSONB, nullable=False, default={
        'enable_advanced_analytics': True,
        'enable_trend_analysis': True,
        'enable_benchmark_comparison': True,
        'cache_duration_hours': 24
    })
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quality_config")

    def __repr__(self):
        return f"<QualityConfig(user_id={self.user_id}, context={self.default_context})>"


# Update existing models to include quality assessment relationships
def update_user_model():
    """
    Update User model to include quality assessment relationships
    This would be added to the existing User model
    """
    # Add to User model:
    # quality_assessments = relationship("QualityAssessment", back_populates="user", cascade="all, delete-orphan")
    # quality_metrics_cache = relationship("QualityMetricsCache", back_populates="user", cascade="all, delete-orphan")
    # quality_alerts = relationship("QualityAlert", back_populates="user", cascade="all, delete-orphan")
    # quality_config = relationship("QualityConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    pass


def update_transcript_model():
    """
    Update Transcript model to include quality assessment relationships
    This would be added to the existing Transcript model
    """
    # Add to Transcript model:
    # quality_assessments = relationship("QualityAssessment", back_populates="transcript", cascade="all, delete-orphan")
    pass