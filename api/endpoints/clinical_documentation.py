#!/usr/bin/env python3
"""
Clinical Documentation API Endpoints
RESTful API for automated clinical note generation, medical coding, and quality assessment
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import uuid
import asyncio

# Import clinical documentation system
try:
    from clinical_documentation_system import (
        ClinicalDocumentationSystem,
        ClinicalNoteType,
        ClinicalSpecialty,
        DocumentationQuality,
        ClinicalCode,
        ClinicalNote
    )
except ImportError:
    ClinicalDocumentationSystem = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/clinical", tags=["Clinical Documentation"])
security = HTTPBearer()

# Pydantic models
class ClinicalNoteRequest(BaseModel):
    """Clinical note generation request"""
    transcript_text: str = Field(..., description="Clinical transcript text")
    note_type: str = Field(..., description="Type of clinical note")
    specialty: str = Field(..., description="Medical specialty")
    patient_id: str = Field(..., description="Patient identifier")
    provider_id: str = Field(..., description="Provider identifier")
    encounter_id: str = Field(..., description="Encounter identifier")
    enable_coding: bool = Field(default=True, description="Enable medical coding")
    enable_quality_assessment: bool = Field(default=True, description="Enable quality assessment")
    
    @validator('note_type')
    def validate_note_type(cls, v):
        valid_types = [note_type.value for note_type in ClinicalNoteType]
        if v not in valid_types:
            raise ValueError(f'note_type must be one of {valid_types}')
        return v
    
    @validator('specialty')
    def validate_specialty(cls, v):
        valid_specialties = [specialty.value for specialty in ClinicalSpecialty]
        if v not in valid_specialties:
            raise ValueError(f'specialty must be one of {valid_specialties}')
        return v

class ClinicalCodeResponse(BaseModel):
    """Clinical code response model"""
    code: str
    description: str
    code_type: str
    confidence: float
    context: str
    modifier: Optional[str] = None
    billing_units: Optional[int] = None
    reimbursement_rate: Optional[float] = None

class ClinicalSectionResponse(BaseModel):
    """Clinical section response model"""
    section_name: str
    content: str
    structured_data: Dict[str, Any]
    entity_count: int
    code_count: int
    quality_score: float
    completeness_score: float
    recommendations: List[str]

class ClinicalNoteResponse(BaseModel):
    """Clinical note response model"""
    note_id: str
    note_type: str
    specialty: str
    patient_id: str
    provider_id: str
    encounter_id: str
    created_at: datetime
    sections: Dict[str, ClinicalSectionResponse]
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: List[str]
    procedures: List[str]
    medications: List[str]
    overall_quality: str
    billing_codes: List[ClinicalCodeResponse]
    word_count: int
    estimated_time_saved: float
    compliance_status: str

class QualityMetricsResponse(BaseModel):
    """Quality metrics response model"""
    completeness_score: float
    accuracy_score: float
    specificity_score: float
    coding_accuracy: float
    documentation_time: float
    missing_elements: List[str]
    improvement_suggestions: List[str]

class ClinicalReportResponse(BaseModel):
    """Clinical report response model"""
    note_summary: Dict[str, Any]
    clinical_content: Dict[str, Any]
    coding_information: Dict[str, Any]
    quality_assessment: QualityMetricsResponse
    efficiency_metrics: Dict[str, Any]

class TemplateRequest(BaseModel):
    """Template generation request"""
    note_type: str
    specialty: str
    
    @validator('note_type')
    def validate_note_type(cls, v):
        valid_types = [note_type.value for note_type in ClinicalNoteType]
        if v not in valid_types:
            raise ValueError(f'note_type must be one of {valid_types}')
        return v
    
    @validator('specialty')
    def validate_specialty(cls, v):
        valid_specialties = [specialty.value for specialty in ClinicalSpecialty]
        if v not in valid_specialties:
            raise ValueError(f'specialty must be one of {valid_specialties}')
        return v

class TemplateResponse(BaseModel):
    """Template response model"""
    note_type: str
    specialty: str
    sections: List[str]
    required_elements: Dict[str, List[str]]
    specialty_elements: List[str]
    common_procedures: List[str]
    key_diagnoses: List[str]
    documentation_focus: List[str]
    format: str
    billing_level: str

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    # In production, implement proper JWT token validation
    return {
        "user_id": "demo_user",
        "role": "healthcare_provider",
        "permissions": ["clinical_documentation", "medical_coding"]
    }

async def get_clinical_system():
    """Get clinical documentation system instance"""
    if ClinicalDocumentationSystem is None:
        raise HTTPException(
            status_code=503,
            detail="Clinical documentation system not available"
        )
    
    try:
        return ClinicalDocumentationSystem()
    except Exception as e:
        logger.error(f"Failed to initialize clinical system: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to initialize clinical documentation system"
        )

# API Endpoints
@router.post("/generate-note", response_model=ClinicalNoteResponse)
async def generate_clinical_note(
    request: ClinicalNoteRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    clinical_system: ClinicalDocumentationSystem = Depends(get_clinical_system)
):
    """
    Generate clinical note from transcript
    
    Creates structured clinical documentation from medical transcripts with
    automatic section extraction, medical coding, and quality assessment.
    """
    try:
        # Validate user permissions
        if "clinical_documentation" not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions for clinical documentation"
            )
        
        # Generate clinical note
        clinical_note = await clinical_system.generate_clinical_note(
            transcript_text=request.transcript_text,
            note_type=ClinicalNoteType(request.note_type),
            specialty=ClinicalSpecialty(request.specialty),
            patient_id=request.patient_id,
            provider_id=request.provider_id,
            encounter_id=request.encounter_id
        )
        
        # Convert sections to response format
        sections_response = {}
        for section_name, section in clinical_note.sections.items():
            sections_response[section_name] = ClinicalSectionResponse(
                section_name=section.section_name,
                content=section.content,
                structured_data=section.structured_data,
                entity_count=len(section.entities),
                code_count=len(section.codes),
                quality_score=section.quality_score,
                completeness_score=section.completeness_score,
                recommendations=section.recommendations
            )
        
        # Convert billing codes to response format
        billing_codes_response = []
        for code in clinical_note.billing_codes:
            billing_codes_response.append(ClinicalCodeResponse(
                code=code.code,
                description=code.description,
                code_type=code.code_type,
                confidence=code.confidence,
                context=code.context,
                modifier=code.modifier,
                billing_units=code.billing_units,
                reimbursement_rate=code.reimbursement_rate
            ))
        
        return ClinicalNoteResponse(
            note_id=clinical_note.note_id,
            note_type=clinical_note.note_type.value,
            specialty=clinical_note.specialty.value,
            patient_id=clinical_note.patient_id,
            provider_id=clinical_note.provider_id,
            encounter_id=clinical_note.encounter_id,
            created_at=clinical_note.created_at,
            sections=sections_response,
            primary_diagnosis=clinical_note.primary_diagnosis,
            secondary_diagnoses=clinical_note.secondary_diagnoses,
            procedures=clinical_note.procedures,
            medications=clinical_note.medications,
            overall_quality=clinical_note.overall_quality.value,
            billing_codes=billing_codes_response,
            word_count=clinical_note.word_count,
            estimated_time_saved=clinical_note.estimated_time_saved,
            compliance_status=clinical_note.compliance_status
        )
        
    except Exception as e:
        logger.error(f"Clinical note generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Clinical note generation failed: {str(e)}"
        )

@router.post("/generate-report", response_model=ClinicalReportResponse)
async def generate_clinical_report(
    note_id: str,
    current_user: dict = Depends(get_current_user),
    clinical_system: ClinicalDocumentationSystem = Depends(get_clinical_system)
):
    """
    Generate comprehensive clinical report
    
    Creates detailed clinical report with quality assessment,
    coding analysis, and efficiency metrics.
    """
    try:
        # In a real implementation, retrieve the clinical note from database
        # For demo purposes, we'll create a mock note
        
        # This would typically be: clinical_note = get_clinical_note_by_id(note_id)
        raise HTTPException(
            status_code=501,
            detail="Report generation requires clinical note retrieval from database"
        )
        
    except Exception as e:
        logger.error(f"Clinical report generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Clinical report generation failed: {str(e)}"
        )

@router.post("/get-template", response_model=TemplateResponse)
async def get_clinical_template(
    request: TemplateRequest,
    current_user: dict = Depends(get_current_user),
    clinical_system: ClinicalDocumentationSystem = Depends(get_clinical_system)
):
    """
    Get clinical documentation template
    
    Returns specialty-specific documentation template with
    required sections and elements.
    """
    try:
        # Generate template
        template = clinical_system.template_engine.generate_template(
            ClinicalNoteType(request.note_type),
            ClinicalSpecialty(request.specialty)
        )
        
        return TemplateResponse(
            note_type=template["note_type"],
            specialty=template["specialty"],
            sections=template["sections"],
            required_elements=template["required_elements"],
            specialty_elements=template.get("specialty_elements", []),
            common_procedures=template.get("common_procedures", []),
            key_diagnoses=template.get("key_diagnoses", []),
            documentation_focus=template.get("documentation_focus", []),
            format=template["format"],
            billing_level=template["billing_level"]
        )
        
    except Exception as e:
        logger.error(f"Template generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Template generation failed: {str(e)}"
        )

@router.get("/medical-codes/icd10")
async def get_icd10_codes(
    query: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    clinical_system: ClinicalDocumentationSystem = Depends(get_clinical_system)
):
    """
    Get ICD-10 diagnostic codes
    
    Returns ICD-10 codes matching the query or all codes if no query provided.
    """
    try:
        icd10_database = clinical_system.coding_engine.icd10_database
        
        if query:
            # Filter codes based on query
            matching_codes = []
            query_lower = query.lower()
            
            for code, info in icd10_database.items():
                if (query_lower in info["description"].lower() or 
                    any(query_lower in keyword for keyword in info["keywords"])):
                    matching_codes.append({
                        "code": code,
                        "description": info["description"],
                        "category": info["category"],
                        "keywords": info["keywords"]
                    })
                
                if len(matching_codes) >= limit:
                    break
            
            return {"codes": matching_codes, "total": len(matching_codes)}
        else:
            # Return all codes (limited)
            all_codes = []
            for code, info in list(icd10_database.items())[:limit]:
                all_codes.append({
                    "code": code,
                    "description": info["description"],
                    "category": info["category"],
                    "keywords": info["keywords"]
                })
            
            return {"codes": all_codes, "total": len(icd10_database)}
        
    except Exception as e:
        logger.error(f"ICD-10 code retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ICD-10 code retrieval failed: {str(e)}"
        )

@router.get("/medical-codes/cpt")
async def get_cpt_codes(
    query: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    clinical_system: ClinicalDocumentationSystem = Depends(get_clinical_system)
):
    """
    Get CPT procedure codes
    
    Returns CPT codes matching the query or all codes if no query provided.
    """
    try:
        cpt_database = clinical_system.coding_engine.cpt_database
        
        if query:
            # Filter codes based on query
            matching_codes = []
            query_lower = query.lower()
            
            for code, info in cpt_database.items():
                if (query_lower in info["description"].lower() or 
                    any(query_lower in keyword for keyword in info["keywords"])):
                    matching_codes.append({
                        "code": code,
                        "description": info["description"],
                        "category": info["category"],
                        "work_rvu": info.get("work_rvu", 0),
                        "reimbursement_rate": info.get("reimbursement_rate", 0)
                    })
                
                if len(matching_codes) >= limit:
                    break
            
            return {"codes": matching_codes, "total": len(matching_codes)}
        else:
            # Return all codes (limited)
            all_codes = []
            for code, info in list(cpt_database.items())[:limit]:
                all_codes.append({
                    "code": code,
                    "description": info["description"],
                    "category": info["category"],
                    "work_rvu": info.get("work_rvu", 0),
                    "reimbursement_rate": info.get("reimbursement_rate", 0)
                })
            
            return {"codes": all_codes, "total": len(cpt_database)}
        
    except Exception as e:
        logger.error(f"CPT code retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"CPT code retrieval failed: {str(e)}"
        )

@router.get("/specialties")
async def get_medical_specialties(
    current_user: dict = Depends(get_current_user)
):
    """
    Get available medical specialties
    
    Returns list of supported medical specialties for clinical documentation.
    """
    try:
        specialties = []
        for specialty in ClinicalSpecialty:
            specialties.append({
                "value": specialty.value,
                "name": specialty.value.replace("_", " ").title()
            })
        
        return {"specialties": specialties}
        
    except Exception as e:
        logger.error(f"Specialty retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Specialty retrieval failed: {str(e)}"
        )

@router.get("/note-types")
async def get_note_types(
    current_user: dict = Depends(get_current_user)
):
    """
    Get available clinical note types
    
    Returns list of supported clinical note types.
    """
    try:
        note_types = []
        for note_type in ClinicalNoteType:
            note_types.append({
                "value": note_type.value,
                "name": note_type.value.replace("_", " ").title()
            })
        
        return {"note_types": note_types}
        
    except Exception as e:
        logger.error(f"Note type retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Note type retrieval failed: {str(e)}"
        )

@router.get("/quality-metrics/{note_id}")
async def get_quality_metrics(
    note_id: str,
    current_user: dict = Depends(get_current_user),
    clinical_system: ClinicalDocumentationSystem = Depends(get_clinical_system)
):
    """
    Get quality metrics for clinical note
    
    Returns detailed quality assessment metrics for a specific clinical note.
    """
    try:
        # In a real implementation, retrieve the clinical note from database
        # and assess its quality
        
        raise HTTPException(
            status_code=501,
            detail="Quality metrics require clinical note retrieval from database"
        )
        
    except Exception as e:
        logger.error(f"Quality metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quality metrics retrieval failed: {str(e)}"
        )

@router.get("/analytics/summary")
async def get_analytics_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    specialty: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get clinical documentation analytics summary
    
    Returns summary analytics for clinical documentation performance,
    quality metrics, and efficiency measures.
    """
    try:
        # Mock analytics data for demo
        analytics_summary = {
            "total_notes_generated": 1247,
            "average_quality_score": 0.87,
            "average_time_saved": 18.5,
            "total_time_saved": 23067.5,
            "average_reimbursement": 156.75,
            "total_reimbursement": 195467.25,
            "quality_distribution": {
                "excellent": 312,
                "good": 498,
                "adequate": 287,
                "needs_improvement": 98,
                "incomplete": 52
            },
            "specialty_breakdown": {
                "internal_medicine": 387,
                "cardiology": 234,
                "emergency_medicine": 198,
                "surgery": 156,
                "neurology": 123,
                "other": 149
            },
            "note_type_distribution": {
                "soap_note": 456,
                "progress_note": 298,
                "admission_note": 187,
                "discharge_summary": 134,
                "consultation_note": 98,
                "other": 74
            },
            "coding_accuracy": {
                "icd10_accuracy": 0.92,
                "cpt_accuracy": 0.89,
                "average_codes_per_note": 3.2
            }
        }
        
        return analytics_summary
        
    except Exception as e:
        logger.error(f"Analytics summary retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analytics summary retrieval failed: {str(e)}"
        )

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for clinical documentation service"""
    try:
        # Check if clinical system can be initialized
        clinical_system = await get_clinical_system()
        
        return {
            "status": "healthy",
            "service": "clinical_documentation",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": {
                "note_generation": True,
                "medical_coding": True,
                "quality_assessment": True,
                "template_generation": True,
                "analytics": True
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "clinical_documentation",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }