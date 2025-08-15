"""
Medical Transcription API Endpoints - Version 2.x
HIPAA-compliant medical transcription with comprehensive schema support
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from api.database import get_db, User
from api.auth import get_current_active_user, get_api_key_user
from api.versioning.api_versions import (
    APIVersion, require_version, register_versioned_endpoint
)

# Import medical system components
try:
    from medical_transcription_system import (
        MedicalTranscriptionSystem, HIPAACompliance, MedicalEntityType
    )
    from comprehensive_medical_schema import ComprehensiveSchemaProcessor
    MEDICAL_SYSTEM_AVAILABLE = True
except ImportError:
    MEDICAL_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)

# ==================
# Pydantic Models for API v2.x
# ==================

class HIPAAComplianceLevelModel(BaseModel):
    """HIPAA compliance level configuration"""
    level: str = Field(..., pattern="^(strict|standard|research)$")
    description: str


class MedicalEntityModel(BaseModel):
    """Medical entity extracted from transcription"""
    text: str
    entity_type: str
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


class VitalSignModel(BaseModel):
    """Vital sign measurement"""
    type: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None
    interpretation: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal: Optional[bool] = None


class TestResultModel(BaseModel):
    """Laboratory or diagnostic test result"""
    test_name: str
    value: str
    reference_range: Optional[str] = None
    interpretation: Optional[str] = None
    abnormal: Optional[bool] = None
    timestamp: Optional[datetime] = None


class VoiceBiomarkerModel(BaseModel):
    """Voice pattern analysis for health indicators"""
    biomarker_type: str
    value: float
    interpretation: str
    confidence: float
    clinical_relevance: Optional[str] = None


class EmotionalStateModel(BaseModel):
    """Patient emotional analysis"""
    emotion: str
    intensity: float  # 0-10 scale
    context: str
    confidence: Optional[float] = None


class SocialDeterminantModel(BaseModel):
    """Social determinants of health"""
    category: str
    factor: str
    impact_level: str  # high, medium, low
    notes: Optional[str] = None
    confidence: Optional[float] = None


class AmbientSoundModel(BaseModel):
    """Environmental sound analysis"""
    sound_type: str
    duration: float
    context: str
    clinical_relevance: Optional[str] = None


class CareQualityIndicatorModel(BaseModel):
    """Care quality assessment indicator"""
    indicator: str
    status: str  # excellent, good, needs_improvement, concerning
    details: str
    score: Optional[float] = None


class ClinicalRecommendationModel(BaseModel):
    """Clinical decision support recommendation"""
    recommendation: str
    evidence_level: str
    priority: str  # high, medium, low
    supporting_data: Optional[str] = None


class ComprehensiveAnalysisModel(BaseModel):
    """Comprehensive clinical analysis results"""
    patient_engagement_score: float
    care_quality_indicators: List[CareQualityIndicatorModel]
    clinical_decision_support: List[ClinicalRecommendationModel]
    risk_assessment: Optional[str] = None


class HIPAAViolationModel(BaseModel):
    """HIPAA compliance violation"""
    violation_type: str
    text: str
    position: List[int]  # [start, end]
    severity: str
    recommendation: str
    confidence: float


class MedicalTranscriptionRequest(BaseModel):
    """Request to create medical transcription"""
    title: Optional[str] = None
    language: str = Field(default="auto", pattern="^(auto|en|es|fr|de|it|pt|zh|ja|ko)$")
    compliance_level: str = Field(default="standard", pattern="^(strict|standard|research)$")
    patient_id: Optional[str] = Field(None, max_length=50)
    provider_id: Optional[str] = Field(None, max_length=50)
    encounter_type: Optional[str] = Field(None, max_length=50)
    enable_comprehensive_analysis: bool = True
    enable_phi_detection: bool = True
    custom_vocabulary: Optional[List[str]] = None


class MedicalTranscriptionResponse(BaseModel):
    """Medical transcription processing result"""
    id: str
    user_id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Medical metadata
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    encounter_type: Optional[str] = None
    compliance_level: str
    compliance_status: str
    
    # Processing results
    content: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None
    
    # Medical analysis
    entities: List[MedicalEntityModel] = []
    medications: List[Dict[str, Any]] = []
    procedures: List[Dict[str, Any]] = []
    diagnoses: List[Dict[str, Any]] = []
    vital_signs: List[VitalSignModel] = []
    test_results: List[TestResultModel] = []
    voice_biomarkers: List[VoiceBiomarkerModel] = []
    emotional_state: List[EmotionalStateModel] = []
    social_determinants: List[SocialDeterminantModel] = []
    ambient_sounds: List[AmbientSoundModel] = []
    comprehensive_analysis: Optional[ComprehensiveAnalysisModel] = None
    
    # HIPAA compliance
    phi_violations: List[HIPAAViolationModel] = []
    phi_detected: bool = False
    anonymized_content: Optional[str] = None
    
    # Report sections
    sections: Dict[str, str] = {}


class MedicalSearchRequest(BaseModel):
    """Medical transcription search request"""
    query: str = Field(..., min_length=1, max_length=500)
    entity_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    patient_ids: Optional[List[str]] = None
    provider_ids: Optional[List[str]] = None
    compliance_level: Optional[str] = Field(None, pattern="^(strict|standard|research)$")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class MedicalAnalyticsResponse(BaseModel):
    """Medical transcription analytics"""
    time_period: Dict[str, str]
    total_transcripts: int
    total_patients: int
    total_providers: int
    average_engagement_score: float
    common_diagnoses: List[str]
    common_medications: List[str]
    common_procedures: List[str]
    phi_detection_rate: float
    compliance_rate: float
    quality_indicators: List[CareQualityIndicatorModel]


# ==================
# Router Setup
# ==================

# Create versioned routers
v2_0_router = APIRouter(prefix="/api/v2.0", tags=["Medical Transcription v2.0"])
v2_1_router = APIRouter(prefix="/api/v2.1", tags=["Medical Transcription v2.1"])

# ==================
# API v2.0 Endpoints (Basic Medical Support)
# ==================

@v2_0_router.post("/medical/transcriptions", 
                  response_model=MedicalTranscriptionResponse,
                  status_code=status.HTTP_201_CREATED)
async def create_medical_transcription_v2_0(
    file: UploadFile = File(...),
    request_data: str = None,  # JSON string due to file upload limitation
    current_user: User = Depends(get_current_active_user),
    api_version: APIVersion = Depends(require_version(APIVersion.V2_0)),
    db: Session = Depends(get_db)
):
    """Create medical transcription with basic HIPAA compliance (v2.0)"""
    if not MEDICAL_SYSTEM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Medical transcription system is not available"
        )
    
    # Parse request data
    try:
        import json
        if request_data:
            request_dict = json.loads(request_data)
            request = MedicalTranscriptionRequest(**request_dict)
        else:
            request = MedicalTranscriptionRequest()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {e}")
    
    # Validate file
    allowed_extensions = {'.mp3', '.wav', '.mp4', '.mov', '.m4a', '.ogg', '.webm'}
    file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
    
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Initialize medical transcription system
        compliance_level = HIPAACompliance[request.compliance_level.upper()]
        medical_system = MedicalTranscriptionSystem(compliance_level)
        
        # Read file content
        file_content = await file.read()
        
        # Create temporary file path (in production, use proper file handling)
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Process transcription
        metadata = {
            'user_id': current_user.id,
            'patient_id': request.patient_id,
            'provider_id': request.provider_id,
            'encounter_type': request.encounter_type,
            'compliance_level': request.compliance_level,
            'file_name': file.filename
        }
        
        result = medical_system.process_medical_transcription(
            audio_file_path=temp_file_path,
            metadata=metadata
        )
        
        # Clean up temporary file
        import os
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Convert result to response model
        response = MedicalTranscriptionResponse(
            id=result.get('processing_id', f'med_{datetime.utcnow().timestamp()}'),
            user_id=current_user.id,
            title=request.title or file.filename,
            status="completed" if result.get('success') else "failed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            patient_id=request.patient_id,
            provider_id=request.provider_id,
            encounter_type=request.encounter_type,
            compliance_level=request.compliance_level,
            compliance_status=result.get('compliance_status', 'pending'),
            content=result.get('transcript', ''),
            confidence=result.get('confidence', 0.0),
            entities=[
                MedicalEntityModel(**entity) for entity in result.get('entities', [])
            ],
            medications=result.get('medications', []),
            procedures=result.get('procedures', []),
            diagnoses=result.get('diagnoses', []),
            phi_violations=[
                HIPAAViolationModel(**violation) for violation in result.get('phi_violations', [])
            ],
            phi_detected=bool(result.get('phi_violations')),
            sections=result.get('sections', {})
        )
        
        logger.info(f"Created medical transcription for user {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing medical transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process medical transcription: {str(e)}"
        )

# ==================
# API v2.1 Endpoints (Comprehensive Medical Schema)
# ==================

@v2_1_router.post("/medical/transcriptions", 
                  response_model=MedicalTranscriptionResponse,
                  status_code=status.HTTP_201_CREATED)
async def create_comprehensive_medical_transcription_v2_1(
    file: UploadFile = File(...),
    request_data: str = None,
    current_user: User = Depends(get_current_active_user),
    api_version: APIVersion = Depends(require_version(APIVersion.V2_1)),
    db: Session = Depends(get_db)
):
    """Create medical transcription with comprehensive schema support (v2.1)"""
    if not MEDICAL_SYSTEM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Medical transcription system is not available"
        )
    
    # Parse request data
    try:
        import json
        if request_data:
            request_dict = json.loads(request_data)
            request = MedicalTranscriptionRequest(**request_dict)
        else:
            request = MedicalTranscriptionRequest()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {e}")
    
    # Process with comprehensive schema
    try:
        # Initialize systems
        compliance_level = HIPAACompliance[request.compliance_level.upper()]
        medical_system = MedicalTranscriptionSystem(compliance_level)
        comprehensive_processor = ComprehensiveSchemaProcessor()
        
        # Read and save file
        file_content = await file.read()
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Basic medical processing
        metadata = {
            'user_id': current_user.id,
            'patient_id': request.patient_id,
            'provider_id': request.provider_id,
            'encounter_type': request.encounter_type,
            'compliance_level': request.compliance_level,
            'file_name': file.filename
        }
        
        result = medical_system.process_medical_transcription(
            audio_file_path=temp_file_path,
            metadata=metadata
        )
        
        # Enhanced processing with comprehensive schema
        if request.enable_comprehensive_analysis and result.get('success'):
            try:
                comprehensive_data = comprehensive_processor.process_comprehensive_transcript(
                    transcript_text=result.get('transcript', ''),
                    entities=result.get('entities', []),
                    metadata=metadata
                )
                
                # Merge comprehensive data
                result.update(comprehensive_data)
                
            except Exception as e:
                logger.warning(f"Comprehensive analysis failed: {e}")
                # Continue with basic processing
        
        # Clean up
        import os
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Convert to response with comprehensive data
        response = MedicalTranscriptionResponse(
            id=result.get('processing_id', f'med_{datetime.utcnow().timestamp()}'),
            user_id=current_user.id,
            title=request.title or file.filename,
            status="completed" if result.get('success') else "failed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            patient_id=request.patient_id,
            provider_id=request.provider_id,
            encounter_type=request.encounter_type,
            compliance_level=request.compliance_level,
            compliance_status=result.get('compliance_status', 'pending'),
            content=result.get('transcript', ''),
            confidence=result.get('confidence', 0.0),
            entities=[
                MedicalEntityModel(**entity) for entity in result.get('entities', [])
            ],
            medications=result.get('medications', []),
            procedures=result.get('procedures', []),
            diagnoses=result.get('diagnoses', []),
            # v2.1 comprehensive features
            vital_signs=[
                VitalSignModel(**vs) for vs in result.get('vital_signs', [])
            ],
            test_results=[
                TestResultModel(**tr) for tr in result.get('test_results', [])
            ],
            voice_biomarkers=[
                VoiceBiomarkerModel(**vb) for vb in result.get('voice_biomarkers', [])
            ],
            emotional_state=[
                EmotionalStateModel(**es) for es in result.get('emotional_state', [])
            ],
            social_determinants=[
                SocialDeterminantModel(**sd) for sd in result.get('social_determinants', [])
            ],
            ambient_sounds=[
                AmbientSoundModel(**amb) for amb in result.get('ambient_sounds', [])
            ],
            comprehensive_analysis=ComprehensiveAnalysisModel(
                **result['comprehensive_analysis']
            ) if result.get('comprehensive_analysis') else None,
            phi_violations=[
                HIPAAViolationModel(**violation) for violation in result.get('phi_violations', [])
            ],
            phi_detected=bool(result.get('phi_violations')),
            sections=result.get('sections', {})
        )
        
        logger.info(f"Created comprehensive medical transcription for user {current_user.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing comprehensive medical transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process medical transcription: {str(e)}"
        )


@v2_1_router.get("/medical/analytics", response_model=MedicalAnalyticsResponse)
async def get_medical_analytics_v2_1(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    patient_ids: Optional[List[str]] = Query(None),
    provider_ids: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    api_version: APIVersion = Depends(require_version(APIVersion.V2_1)),
    db: Session = Depends(get_db)
):
    """Get comprehensive medical transcription analytics (v2.1)"""
    try:
        # Mock analytics data - in production, this would query the database
        time_period = {
            "from": (date_from or datetime.now()).isoformat(),
            "to": (date_to or datetime.now()).isoformat()
        }
        
        analytics = MedicalAnalyticsResponse(
            time_period=time_period,
            total_transcripts=150,
            total_patients=75,
            total_providers=12,
            average_engagement_score=8.2,
            common_diagnoses=["Hypertension", "Type 2 Diabetes", "Anxiety Disorder"],
            common_medications=["Lisinopril", "Metformin", "Sertraline"],
            common_procedures=["Blood pressure check", "Blood glucose test", "ECG"],
            phi_detection_rate=0.12,
            compliance_rate=0.94,
            quality_indicators=[
                CareQualityIndicatorModel(
                    indicator="Patient Communication Quality",
                    status="excellent",
                    details="Clear communication observed in 94% of encounters",
                    score=9.4
                ),
                CareQualityIndicatorModel(
                    indicator="Clinical Documentation Completeness",
                    status="good",
                    details="All required fields documented in 89% of cases",
                    score=8.9
                )
            ]
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error retrieving medical analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


# ==================
# Common Endpoints (Both Versions)
# ==================

for router in [v2_0_router, v2_1_router]:
    
    @router.get("/medical/compliance-levels", response_model=List[HIPAAComplianceLevelModel])
    async def get_compliance_levels():
        """Get available HIPAA compliance levels"""
        return [
            HIPAAComplianceLevelModel(
                level="strict",
                description="No PHI allowed - all personal information is removed"
            ),
            HIPAAComplianceLevelModel(
                level="standard",
                description="PHI is anonymized using secure tokens"
            ),
            HIPAAComplianceLevelModel(
                level="research",
                description="Limited PHI allowed for research purposes with consent"
            )
        ]
    
    @router.get("/medical/entity-types", response_model=List[str])
    async def get_medical_entity_types():
        """Get supported medical entity types"""
        return [
            "symptom", "medication", "procedure", "diagnosis", "anatomy",
            "dosage", "measurement", "condition", "provider", "facility",
            "vital_sign", "test_result", "voice_biomarker", "ambient_sound",
            "emotion", "social_determinant"
        ]


# ==================
# Register Endpoints with Version Manager
# ==================

# Register v2.0 endpoints
register_versioned_endpoint(
    "/medical/transcriptions", "POST", APIVersion.V2_0,
    changes={
        APIVersion.V2_0: ["Added HIPAA compliance support", "Medical entity extraction"]
    }
)

# Register v2.1 endpoints  
register_versioned_endpoint(
    "/medical/transcriptions", "POST", APIVersion.V2_1,
    changes={
        APIVersion.V2_1: [
            "Added comprehensive medical schema support",
            "Voice biomarker analysis",
            "Social determinants extraction",
            "Enhanced clinical decision support"
        ]
    }
)

register_versioned_endpoint(
    "/medical/analytics", "GET", APIVersion.V2_1,
    changes={
        APIVersion.V2_1: ["New comprehensive analytics endpoint"]
    }
)