"""
Enhanced GraphQL Types for Medical Transcription System
Comprehensive medical schema support with HIPAA compliance
"""

import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


@strawberry.enum
class HIPAAComplianceLevel(Enum):
    STRICT = "strict"
    STANDARD = "standard"
    RESEARCH = "research"


@strawberry.enum
class MedicalEntityType(Enum):
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    DIAGNOSIS = "diagnosis"
    ANATOMY = "anatomy"
    DOSAGE = "dosage"
    MEASUREMENT = "measurement"
    CONDITION = "condition"
    PROVIDER = "provider"
    FACILITY = "facility"
    VITAL_SIGN = "vital_sign"
    TEST_RESULT = "test_result"
    VOICE_BIOMARKER = "voice_biomarker"
    AMBIENT_SOUND = "ambient_sound"
    EMOTION = "emotion"
    SOCIAL_DETERMINANT = "social_determinant"


@strawberry.enum
class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@strawberry.enum
class CareQualityStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CONCERNING = "concerning"


@strawberry.enum
class RecommendationPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@strawberry.type
class MedicalEntity:
    """Medical entity extracted from transcription"""
    text: str
    entity_type: MedicalEntityType
    confidence: float
    start_pos: int
    end_pos: int
    normalized_form: str
    medical_code: Optional[str] = None
    context: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    timestamp: Optional[datetime] = None


@strawberry.type
class HIPAAViolation:
    """HIPAA compliance violation detected in transcript"""
    violation_type: str
    text: str
    position: List[int]  # [start, end]
    severity: str
    recommendation: str
    confidence: float


@strawberry.type
class VitalSign:
    """Vital sign measurement"""
    type: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None
    interpretation: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal: Optional[bool] = None


@strawberry.type
class TestResult:
    """Laboratory or diagnostic test result"""
    test_name: str
    value: str
    reference_range: Optional[str] = None
    interpretation: Optional[str] = None
    abnormal: Optional[bool] = None
    timestamp: Optional[datetime] = None
    ordering_provider: Optional[str] = None


@strawberry.type
class VoiceBiomarker:
    """Voice pattern analysis for health indicators"""
    biomarker_type: str
    value: float
    interpretation: str
    confidence: float
    timestamp: Optional[datetime] = None
    clinical_relevance: Optional[str] = None


@strawberry.type
class AmbientSound:
    """Environmental sound analysis"""
    sound_type: str
    duration: float
    context: str
    clinical_relevance: Optional[str] = None
    intensity: Optional[float] = None
    timestamp: Optional[datetime] = None


@strawberry.type
class EmotionalState:
    """Patient emotional analysis"""
    emotion: str
    intensity: float  # 0-10 scale
    context: str
    timestamp: Optional[datetime] = None
    confidence: Optional[float] = None


@strawberry.type
class SocialDeterminant:
    """Social determinants of health"""
    category: str  # housing, employment, education, etc.
    factor: str
    impact_level: str  # high, medium, low
    notes: Optional[str] = None
    confidence: Optional[float] = None


@strawberry.type
class CareQualityIndicator:
    """Care quality assessment indicator"""
    indicator: str
    status: CareQualityStatus
    details: str
    score: Optional[float] = None
    benchmark: Optional[float] = None


@strawberry.type
class ClinicalRecommendation:
    """Clinical decision support recommendation"""
    recommendation: str
    evidence_level: str
    priority: RecommendationPriority
    supporting_data: Optional[str] = None
    implementation_timeline: Optional[str] = None


@strawberry.type
class ComprehensiveAnalysis:
    """Comprehensive clinical analysis results"""
    patient_engagement_score: float
    care_quality_indicators: List[CareQualityIndicator]
    clinical_decision_support: List[ClinicalRecommendation]
    risk_assessment: Optional[str] = None
    care_gaps: Optional[List[str]] = None


@strawberry.type
class Medication:
    """Medication information"""
    name: str
    normalized_name: str
    confidence: float
    context: Optional[str] = None
    medical_code: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@strawberry.type
class Procedure:
    """Medical procedure information"""
    name: str
    normalized_name: str
    confidence: float
    context: Optional[str] = None
    medical_code: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    provider: Optional[str] = None


@strawberry.type
class Diagnosis:
    """Medical diagnosis information"""
    name: str
    normalized_name: str
    confidence: float
    context: Optional[str] = None
    medical_code: Optional[str] = None
    severity: Optional[str] = None
    stage: Optional[str] = None
    onset_date: Optional[datetime] = None
    status: Optional[str] = None


@strawberry.type
class MedicalTranscript:
    """Medical transcription with comprehensive analysis"""
    id: str
    user_id: int
    title: str
    content: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    language: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    # Medical-specific fields
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    encounter_type: Optional[str] = None
    compliance_level: Optional[HIPAAComplianceLevel] = None
    compliance_status: Optional[str] = None
    
    # Analysis results
    entities: List[MedicalEntity]
    medications: List[Medication]
    procedures: List[Procedure]
    diagnoses: List[Diagnosis]
    vital_signs: List[VitalSign]
    test_results: List[TestResult]
    voice_biomarkers: List[VoiceBiomarker]
    ambient_sounds: List[AmbientSound]
    emotional_state: List[EmotionalState]
    social_determinants: List[SocialDeterminant]
    comprehensive_analysis: Optional[ComprehensiveAnalysis] = None
    
    # HIPAA compliance
    phi_violations: List[HIPAAViolation]
    phi_detected: bool
    anonymized_content: Optional[str] = None
    
    # Report sections
    sections: Dict[str, str] = strawberry.field(default_factory=dict)


@strawberry.type
class MedicalTranscriptionJob:
    """Medical transcription processing job"""
    id: str
    user_id: int
    transcript_id: Optional[str] = None
    status: ProcessingStatus
    progress: float
    file_url: str
    language: Optional[str] = None
    compliance_level: HIPAAComplianceLevel
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Processing options
    enable_comprehensive_analysis: bool = True
    enable_phi_detection: bool = True
    custom_vocabulary: Optional[List[str]] = None


@strawberry.type
class MedicalSearchResult:
    """Medical transcription search result"""
    transcript: MedicalTranscript
    relevance_score: float
    matched_entities: List[MedicalEntity]
    matched_sections: List[str]
    highlights: List[str]


@strawberry.type
class MedicalAnalytics:
    """Medical transcription analytics"""
    total_transcripts: int
    total_patients: int
    total_providers: int
    average_engagement_score: float
    common_diagnoses: List[str]
    common_medications: List[str]
    common_procedures: List[str]
    phi_detection_rate: float
    compliance_rate: float
    quality_indicators: List[CareQualityIndicator]


@strawberry.input
class MedicalTranscriptionInput:
    """Input for creating medical transcription"""
    file_url: str
    title: Optional[str] = None
    language: Optional[str] = "auto"
    compliance_level: HIPAAComplianceLevel = HIPAAComplianceLevel.STANDARD
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    encounter_type: Optional[str] = None
    enable_comprehensive_analysis: bool = True
    enable_phi_detection: bool = True
    custom_vocabulary: Optional[List[str]] = None


@strawberry.input
class MedicalSearchInput:
    """Input for medical transcription search"""
    query: str
    entity_types: Optional[List[MedicalEntityType]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    patient_ids: Optional[List[str]] = None
    provider_ids: Optional[List[str]] = None
    compliance_level: Optional[HIPAAComplianceLevel] = None
    min_confidence: Optional[float] = None
    limit: int = 20
    offset: int = 0


@strawberry.input
class MedicalAnalyticsInput:
    """Input for medical analytics query"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    patient_ids: Optional[List[str]] = None
    provider_ids: Optional[List[str]] = None
    entity_types: Optional[List[MedicalEntityType]] = None
    include_phi_stats: bool = False