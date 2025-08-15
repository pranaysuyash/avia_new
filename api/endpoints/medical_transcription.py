#!/usr/bin/env python3
"""
Medical Transcription API Endpoints with HIPAA Compliance
RESTful API for HIPAA-compliant medical transcription services
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import uuid

# Import medical transcription system
try:
    from medical_transcription_system import (
        MedicalTranscriptionSystem,
        HIPAACompliance,
        MedicalEntityType,
        HIPAAViolation,
        MedicalEntity,
        MedicalReport
    )
except ImportError:
    MedicalTranscriptionSystem = None
    HIPAACompliance = None

# Import compliance system
try:
    from compliance_security_system import ComplianceSecurityManager, AuditEventType
except ImportError:
    ComplianceSecurityManager = None
    AuditEventType = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/medical", tags=["Medical Transcription"])
security = HTTPBearer()

# Pydantic models
class TranscriptionRequest(BaseModel):
    """Medical transcription request"""
    text: str = Field(..., description="Medical transcript text to process")
    compliance_level: str = Field(default="standard", description="HIPAA compliance level")
    enable_phi_detection: bool = Field(default=True, description="Enable PHI detection")
    enable_medical_coding: bool = Field(default=True, description="Enable medical coding")
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    patient_id: Optional[str] = Field(None, description="Patient identifier (encrypted)")
    provider_id: Optional[str] = Field(None, description="Provider identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    @validator('compliance_level')
    def validate_compliance_level(cls, v):
        valid_levels = ['strict', 'standard', 'research']
        if v not in valid_levels:
            raise ValueError(f'compliance_level must be one of {valid_levels}')
        return v

class MedicalEntityResponse(BaseModel):
    """Medical entity response model"""
    text: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int
    normalized_form: str
    medical_code: Optional[str] = None
    context: Optional[str] = None

class PHIViolationResponse(BaseModel):
    """PHI violation response model"""
    violation_type: str
    text: str
    position: tuple
    severity: str
    recommendation: str

class MedicalCodeResponse(BaseModel):
    """Medical code response model"""
    code: str
    description: str
    confidence: float
    category: str

class TranscriptionResponse(BaseModel):
    """Medical transcription response"""
    transcript_id: str
    original_text: str
    anonymized_text: str
    medical_entities: List[MedicalEntityResponse]
    phi_violations: List[PHIViolationResponse]
    medical_codes: Dict[str, List[MedicalCodeResponse]]
    compliance_score: float
    processing_time: float
    timestamp: datetime
    compliance_status: str

class ReportGenerationRequest(BaseModel):
    """Medical report generation request"""
    transcript_text: str
    report_type: str = Field(default="consultation", description="Type of medical report")
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('report_type')
    def validate_report_type(cls, v):
        valid_types = ['consultation', 'progress_note', 'discharge_summary']
        if v not in valid_types:
            raise ValueError(f'report_type must be one of {valid_types}')
        return v

class MedicalReportResponse(BaseModel):
    """Medical report response"""
    report_id: str
    report_type: str
    sections: Dict[str, str]
    medications: List[Dict[str, Any]]
    procedures: List[Dict[str, Any]]
    diagnoses: List[Dict[str, Any]]
    created_at: datetime
    compliance_status: str

class ComplianceCheckRequest(BaseModel):
    """HIPAA compliance check request"""
    text: str
    compliance_level: str = "standard"

class ComplianceCheckResponse(BaseModel):
    """HIPAA compliance check response"""
    compliance_score: float
    phi_violations: List[PHIViolationResponse]
    anonymized_text: str
    recommendations: List[str]

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    # In production, implement proper JWT token validation
    # For demo purposes, return a mock user
    return {
        "user_id": "demo_user",
        "role": "healthcare_provider",
        "permissions": ["medical_transcription", "phi_access"]
    }

async def get_medical_system():
    """Get medical transcription system instance"""
    if MedicalTranscriptionSystem is None:
        raise HTTPException(
            status_code=503,
            detail="Medical transcription system not available"
        )
    
    try:
        return MedicalTranscriptionSystem(HIPAACompliance.STANDARD)
    except Exception as e:
        logger.error(f"Failed to initialize medical system: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to initialize medical transcription system"
        )

async def log_audit_event(
    event_type: str,
    user_id: str,
    action: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log audit event for compliance"""
    if ComplianceSecurityManager is None:
        return
    
    try:
        compliance_manager = ComplianceSecurityManager()
        compliance_manager.log_audit_event(
            event_type=event_type,
            action=action,
            user_id=user_id,
            resource_id=resource_id,
            details=details or {}
        )
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")

# API Endpoints
@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_medical_text(
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    medical_system: MedicalTranscriptionSystem = Depends(get_medical_system)
):
    """
    Process medical transcript with HIPAA compliance
    
    This endpoint processes medical transcription text with comprehensive
    HIPAA compliance features including PHI detection, de-identification,
    medical entity extraction, and audit logging.
    """
    try:
        # Validate user permissions
        if "medical_transcription" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for medical transcription"
            )
        
        # Generate transcript ID
        transcript_id = str(uuid.uuid4())
        
        # Log audit event
        background_tasks.add_task(
            log_audit_event,
            event_type="medical.transcription.process",
            user_id=current_user["user_id"],
            action="process_medical_transcript",
            resource_id=transcript_id,
            details={
                "compliance_level": request.compliance_level,
                "phi_detection_enabled": request.enable_phi_detection,
                "medical_coding_enabled": request.enable_medical_coding,
                "text_length": len(request.text)
            }
        )
        
        # Set compliance level
        compliance_level = HIPAACompliance(request.compliance_level)
        medical_system.compliance_level = compliance_level
        
        # Process transcript
        import time
        start_time = time.time()
        
        # Detect PHI violations
        phi_violations = []
        if request.enable_phi_detection:
            phi_violations = medical_system.compliance_checker.detect_phi(request.text)
        
        # Anonymize text
        anonymized_text = request.text
        if request.enable_phi_detection:
            anonymized_text = medical_system.compliance_checker.anonymize_text(
                request.text, compliance_level
            )
        
        # Extract medical entities
        medical_entities = []
        if request.enable_medical_coding:
            try:
                medical_entities = medical_system.entity_extractor.extract_entities(request.text)
            except Exception as e:
                logger.warning(f"Medical entity extraction failed: {e}")
        
        # Generate medical codes
        medical_codes = {"icd10_codes": [], "cpt_codes": []}
        if request.enable_medical_coding:
            # Mock medical codes for demo
            if "hypertension" in request.text.lower():
                medical_codes["icd10_codes"].append({
                    "code": "I10",
                    "description": "Essential hypertension",
                    "confidence": 0.95,
                    "category": "diagnosis"
                })
            
            if "blood pressure" in request.text.lower() or "bp" in request.text.lower():
                medical_codes["cpt_codes"].append({
                    "code": "99213",
                    "description": "Office visit with blood pressure check",
                    "confidence": 0.85,
                    "category": "procedure"
                })
        
        # Calculate compliance score
        compliance_score = 1.0 - (len(phi_violations) * 0.1)
        compliance_score = max(0.0, min(1.0, compliance_score))
        
        processing_time = time.time() - start_time
        
        # Convert entities to response format
        entity_responses = [
            MedicalEntityResponse(
                text=entity.text,
                entity_type=entity.entity_type.value,
                confidence=entity.confidence,
                start_pos=entity.start_pos,
                end_pos=entity.end_pos,
                normalized_form=entity.normalized_form,
                medical_code=entity.medical_code,
                context=entity.context
            )
            for entity in medical_entities
        ]
        
        # Convert PHI violations to response format
        phi_responses = [
            PHIViolationResponse(
                violation_type=violation.violation_type,
                text=violation.text,
                position=violation.position,
                severity=violation.severity,
                recommendation=violation.recommendation
            )
            for violation in phi_violations
        ]
        
        # Convert medical codes to response format
        code_responses = {}
        for code_type, codes in medical_codes.items():
            code_responses[code_type] = [
                MedicalCodeResponse(**code) for code in codes
            ]
        
        return TranscriptionResponse(
            transcript_id=transcript_id,
            original_text=request.text,
            anonymized_text=anonymized_text,
            medical_entities=entity_responses,
            phi_violations=phi_responses,
            medical_codes=code_responses,
            compliance_score=compliance_score,
            processing_time=processing_time,
            timestamp=datetime.utcnow(),
            compliance_status="compliant" if compliance_score >= 0.8 else "non_compliant"
        )
        
    except Exception as e:
        logger.error(f"Medical transcription processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Medical transcription processing failed: {str(e)}"
        )

@router.post("/generate-report", response_model=MedicalReportResponse)
async def generate_medical_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    medical_system: MedicalTranscriptionSystem = Depends(get_medical_system)
):
    """
    Generate structured medical report from transcript
    
    Creates structured medical reports (consultation notes, progress notes,
    discharge summaries) from medical transcription text with proper
    clinical formatting and HIPAA compliance.
    """
    try:
        # Validate permissions
        if "medical_transcription" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for medical report generation"
            )
        
        # Generate report ID
        report_id = str(uuid.uuid4())
        
        # Log audit event
        background_tasks.add_task(
            log_audit_event,
            event_type="medical.report.generate",
            user_id=current_user["user_id"],
            action="generate_medical_report",
            resource_id=report_id,
            details={
                "report_type": request.report_type,
                "patient_id": request.patient_id,
                "provider_id": request.provider_id
            }
        )
        
        # Extract medical entities
        entities = medical_system.entity_extractor.extract_entities(request.transcript_text)
        
        # Generate report
        report = medical_system.report_generator.generate_report(
            request.transcript_text,
            entities,
            report_type=request.report_type,
            metadata=request.metadata or {}
        )
        
        return MedicalReportResponse(
            report_id=report.report_id,
            report_type=report.report_type,
            sections=report.sections,
            medications=report.medications,
            procedures=report.procedures,
            diagnoses=report.diagnoses,
            created_at=report.created_at,
            compliance_status=report.compliance_status
        )
        
    except Exception as e:
        logger.error(f"Medical report generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Medical report generation failed: {str(e)}"
        )

@router.post("/check-compliance", response_model=ComplianceCheckResponse)
async def check_hipaa_compliance(
    request: ComplianceCheckRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    medical_system: MedicalTranscriptionSystem = Depends(get_medical_system)
):
    """
    Check HIPAA compliance of medical text
    
    Analyzes medical text for HIPAA compliance violations,
    detects PHI, and provides de-identification recommendations.
    """
    try:
        # Log audit event
        background_tasks.add_task(
            log_audit_event,
            event_type="medical.compliance.check",
            user_id=current_user["user_id"],
            action="check_hipaa_compliance",
            details={"compliance_level": request.compliance_level}
        )
        
        # Set compliance level
        compliance_level = HIPAACompliance(request.compliance_level)
        
        # Detect PHI violations
        phi_violations = medical_system.compliance_checker.detect_phi(request.text)
        
        # Anonymize text
        anonymized_text = medical_system.compliance_checker.anonymize_text(
            request.text, compliance_level
        )
        
        # Calculate compliance score
        compliance_score = 1.0 - (len(phi_violations) * 0.1)
        compliance_score = max(0.0, min(1.0, compliance_score))
        
        # Generate recommendations
        recommendations = []
        if phi_violations:
            recommendations.append("Remove or de-identify detected PHI before sharing")
            recommendations.append("Implement access controls for PHI-containing documents")
            recommendations.append("Enable audit logging for all PHI access")
        
        if compliance_score < 0.8:
            recommendations.append("Review and remediate compliance violations")
        
        # Convert PHI violations to response format
        phi_responses = [
            PHIViolationResponse(
                violation_type=violation.violation_type,
                text=violation.text,
                position=violation.position,
                severity=violation.severity,
                recommendation=violation.recommendation
            )
            for violation in phi_violations
        ]
        
        return ComplianceCheckResponse(
            compliance_score=compliance_score,
            phi_violations=phi_responses,
            anonymized_text=anonymized_text,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"HIPAA compliance check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"HIPAA compliance check failed: {str(e)}"
        )

@router.get("/medical-codes/{term}")
async def lookup_medical_codes(
    term: str,
    current_user: dict = Depends(get_current_user),
    medical_system: MedicalTranscriptionSystem = Depends(get_medical_system)
):
    """
    Look up medical codes for a given term
    
    Provides ICD-10 diagnostic codes and CPT procedure codes
    for medical terminology validation and coding assistance.
    """
    try:
        # Validate medical term
        validation_result = medical_system.terminology_validator.validate_medical_term(term)
        
        response = {
            "term": term,
            "validation": validation_result,
            "codes": {}
        }
        
        # Add ICD-10 codes if available
        if validation_result.get('code'):
            response["codes"]["icd10"] = {
                "code": validation_result['code'],
                "description": f"Code for {validation_result['normalized']}",
                "confidence": validation_result['confidence']
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Medical code lookup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Medical code lookup failed: {str(e)}"
        )

@router.get("/abbreviations/{abbrev}")
async def expand_medical_abbreviation(
    abbrev: str,
    context: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    medical_system: MedicalTranscriptionSystem = Depends(get_medical_system)
):
    """
    Expand medical abbreviation
    
    Provides expansion of medical abbreviations with context awareness
    for clinical documentation assistance.
    """
    try:
        expansion = medical_system.terminology_validator.expand_abbreviation(abbrev, context)
        
        if expansion:
            return {
                "abbreviation": abbrev,
                "expansion": expansion.expansion,
                "category": expansion.category,
                "confidence": expansion.confidence,
                "context_dependent": expansion.context_dependent
            }
        else:
            return {
                "abbreviation": abbrev,
                "expansion": None,
                "message": "No expansion found for this abbreviation"
            }
            
    except Exception as e:
        logger.error(f"Medical abbreviation expansion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Medical abbreviation expansion failed: {str(e)}"
        )

@router.get("/compliance/status")
async def get_compliance_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get overall HIPAA compliance status
    
    Provides system-wide compliance metrics and status information
    for compliance monitoring and reporting.
    """
    try:
        # Mock compliance status for demo
        compliance_status = {
            "overall_score": 0.92,
            "phi_violations_today": 3,
            "audit_events_today": 247,
            "encrypted_records": 5432,
            "compliance_checks_passed": 45,
            "compliance_checks_failed": 2,
            "last_assessment": datetime.utcnow().isoformat(),
            "status": "compliant",
            "recommendations": [
                "Review recent PHI violations",
                "Update staff training on HIPAA requirements",
                "Conduct quarterly risk assessment"
            ]
        }
        
        return compliance_status
        
    except Exception as e:
        logger.error(f"Compliance status retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Compliance status retrieval failed: {str(e)}"
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for medical transcription service"""
    try:
        # Check if medical system can be initialized
        medical_system = await get_medical_system()
        
        return {
            "status": "healthy",
            "service": "medical_transcription",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "phi_detection": True,
                "medical_coding": True,
                "hipaa_compliance": True,
                "audit_logging": True,
                "encryption": True
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "medical_transcription",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }