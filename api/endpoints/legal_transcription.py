#!/usr/bin/env python3
"""
FastAPI endpoints for legal transcription and analysis services.
Provides comprehensive legal document processing with compliance features.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import tempfile
import os
import json
from datetime import datetime
import logging

from legal_transcription_system import LegalTranscriptionSystem
from legal_schema_processor import LegalSchemaProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/legal", tags=["legal-transcription"])

# Initialize legal transcription system
legal_system = LegalTranscriptionSystem()
schema_processor = LegalSchemaProcessor()


# Pydantic models for request/response
class LegalTranscriptionRequest(BaseModel):
    """Request model for legal transcription."""
    case_number: Optional[str] = Field(None, description="Case number for the proceeding")
    proceeding_type: str = Field(..., description="Type of legal proceeding")
    participants: List[str] = Field(default=[], description="List of participants")
    confidentiality_level: str = Field("standard", description="Confidentiality level")
    court_jurisdiction: Optional[str] = Field(None, description="Court jurisdiction")
    attorney_client_privilege: bool = Field(False, description="Contains privileged communications")


class LegalAnalysisRequest(BaseModel):
    """Request model for legal text analysis."""
    text: str = Field(..., description="Legal text to analyze")
    document_type: Optional[str] = Field(None, description="Type of legal document")
    case_context: Optional[Dict[str, Any]] = Field(None, description="Case context information")


class LegalSearchRequest(BaseModel):
    """Request model for legal document search."""
    query: str = Field(..., description="Search query")
    case_number: Optional[str] = Field(None, description="Filter by case number")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")


class ExportRequest(BaseModel):
    """Request model for legal document export."""
    transcript_id: str = Field(..., description="Transcript ID to export")
    format: str = Field(..., description="Export format (court, brief, discovery)")
    include_analysis: bool = Field(True, description="Include legal analysis")
    redact_privileged: bool = Field(True, description="Redact privileged content")


@router.post("/transcribe")
async def transcribe_legal_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_number: Optional[str] = None,
    proceeding_type: str = "hearing",
    participants: str = "[]",
    confidentiality_level: str = "standard",
    court_jurisdiction: Optional[str] = None,
    attorney_client_privilege: bool = False
):
    """
    Transcribe legal audio with specialized processing.
    
    Args:
        file: Audio file to transcribe
        case_number: Case number for the proceeding
        proceeding_type: Type of legal proceeding
        participants: JSON string of participant names
        confidentiality_level: Confidentiality level (standard, confidential, privileged)
        court_jurisdiction: Court jurisdiction
        attorney_client_privilege: Whether content contains privileged communications
    
    Returns:
        Legal transcription with analysis and compliance information
    """
    try:
        # Validate file type
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Parse participants
        try:
            participants_list = json.loads(participants)
        except json.JSONDecodeError:
            participants_list = []
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process legal transcription
            result = legal_system.process_legal_recording(
                temp_file_path,
                case_number=case_number,
                proceeding_type=proceeding_type,
                participants=participants_list,
                confidentiality_level=confidentiality_level,
                court_jurisdiction=court_jurisdiction,
                attorney_client_privilege=attorney_client_privilege
            )
            
            # Add processing metadata
            result['processing_info'] = {
                'file_name': file.filename,
                'file_size': len(content),
                'processing_time': result.get('processing_time', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Log successful processing
            logger.info(f"Legal transcription completed for case {case_number}")
            
            return JSONResponse(content=result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Legal transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/analyze")
async def analyze_legal_text(request: LegalAnalysisRequest):
    """
    Analyze legal text for entities, compliance, and structure.
    
    Args:
        request: Legal analysis request with text and context
    
    Returns:
        Comprehensive legal analysis results
    """
    try:
        # Perform legal analysis
        analysis_result = legal_system.analyze_legal_content(
            request.text,
            document_type=request.document_type,
            case_context=request.case_context
        )
        
        # Extract legal entities
        entities = schema_processor.extract_legal_entities(request.text)
        
        # Detect privilege markers
        privilege_markers = schema_processor.detect_privilege_markers(request.text)
        
        # Generate redaction suggestions
        redaction_suggestions = schema_processor.suggest_redactions(request.text)
        
        # Compile comprehensive analysis
        result = {
            'status': 'success',
            'analysis': analysis_result,
            'entities': entities,
            'privilege_markers': privilege_markers,
            'redaction_suggestions': redaction_suggestions,
            'document_classification': schema_processor.classify_document_type(request.text),
            'compliance_score': legal_system.calculate_compliance_score(request.text),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Legal analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/search")
async def search_legal_documents(request: LegalSearchRequest):
    """
    Search legal documents with advanced filtering.
    
    Args:
        request: Search request with query and filters
    
    Returns:
        Search results with relevance scoring
    """
    try:
        # Perform legal document search
        search_results = legal_system.search_legal_documents(
            query=request.query,
            case_number=request.case_number,
            document_type=request.document_type,
            date_range=request.date_range
        )
        
        # Enhance results with legal context
        enhanced_results = []
        for result in search_results:
            enhanced_result = {
                **result,
                'legal_entities': schema_processor.extract_legal_entities(result.get('content', '')),
                'document_classification': schema_processor.classify_document_type(result.get('content', '')),
                'relevance_explanation': legal_system.explain_relevance(result, request.query)
            }
            enhanced_results.append(enhanced_result)
        
        return JSONResponse(content={
            'status': 'success',
            'results': enhanced_results,
            'total_count': len(enhanced_results),
            'search_metadata': {
                'query': request.query,
                'filters_applied': {
                    'case_number': request.case_number,
                    'document_type': request.document_type,
                    'date_range': request.date_range
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Legal search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/export")
async def export_legal_document(request: ExportRequest):
    """
    Export legal transcript in specified format.
    
    Args:
        request: Export request with format and options
    
    Returns:
        Exported document file
    """
    try:
        # Get transcript data
        transcript_data = legal_system.get_transcript(request.transcript_id)
        if not transcript_data:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Apply redaction if requested
        if request.redact_privileged:
            transcript_data = legal_system.redact_privileged_content(transcript_data)
        
        # Export in requested format
        if request.format == 'court':
            exported_content = legal_system.export_court_format(
                transcript_data, 
                include_analysis=request.include_analysis
            )
            filename = f"court_transcript_{request.transcript_id}.txt"
            
        elif request.format == 'brief':
            exported_content = legal_system.export_legal_brief_format(
                transcript_data,
                include_analysis=request.include_analysis
            )
            filename = f"legal_brief_{request.transcript_id}.txt"
            
        elif request.format == 'discovery':
            exported_content = legal_system.export_discovery_format(
                transcript_data,
                include_analysis=request.include_analysis
            )
            filename = f"discovery_doc_{request.transcript_id}.txt"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(exported_content)
            temp_file_path = temp_file.name
        
        return FileResponse(
            path=temp_file_path,
            filename=filename,
            media_type='text/plain'
        )
        
    except Exception as e:
        logger.error(f"Legal export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/cases/{case_number}/documents")
async def get_case_documents(case_number: str):
    """
    Get all documents for a specific case.
    
    Args:
        case_number: Case number to retrieve documents for
    
    Returns:
        List of documents associated with the case
    """
    try:
        documents = legal_system.get_case_documents(case_number)
        
        # Enhance with metadata
        enhanced_documents = []
        for doc in documents:
            enhanced_doc = {
                **doc,
                'entity_count': len(schema_processor.extract_legal_entities(doc.get('content', ''))),
                'document_type': schema_processor.classify_document_type(doc.get('content', '')),
                'privilege_markers': len(schema_processor.detect_privilege_markers(doc.get('content', '')))
            }
            enhanced_documents.append(enhanced_doc)
        
        return JSONResponse(content={
            'status': 'success',
            'case_number': case_number,
            'documents': enhanced_documents,
            'total_count': len(enhanced_documents),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Case documents retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.post("/compliance/validate")
async def validate_compliance(
    transcript_id: str,
    compliance_standards: List[str] = ["federal", "state", "court_rules"]
):
    """
    Validate transcript compliance with legal standards.
    
    Args:
        transcript_id: ID of transcript to validate
        compliance_standards: List of compliance standards to check
    
    Returns:
        Compliance validation results
    """
    try:
        # Get transcript data
        transcript_data = legal_system.get_transcript(transcript_id)
        if not transcript_data:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Perform compliance validation
        compliance_results = legal_system.validate_comprehensive_compliance(
            transcript_data,
            standards=compliance_standards
        )
        
        return JSONResponse(content={
            'status': 'success',
            'transcript_id': transcript_id,
            'compliance_results': compliance_results,
            'overall_score': compliance_results.get('overall_score', 0),
            'recommendations': compliance_results.get('recommendations', []),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Compliance validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/entities/types")
async def get_legal_entity_types():
    """
    Get available legal entity types for extraction.
    
    Returns:
        List of supported legal entity types
    """
    try:
        entity_types = schema_processor.get_supported_entity_types()
        
        return JSONResponse(content={
            'status': 'success',
            'entity_types': entity_types,
            'total_count': len(entity_types),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Entity types retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.post("/redaction/preview")
async def preview_redactions(
    text: str,
    redaction_categories: List[str] = ["pii", "financial", "privileged"]
):
    """
    Preview redaction suggestions for legal text.
    
    Args:
        text: Text to analyze for redaction
        redaction_categories: Categories of information to redact
    
    Returns:
        Redaction preview with suggestions
    """
    try:
        # Generate redaction suggestions
        redaction_suggestions = schema_processor.suggest_redactions(
            text,
            categories=redaction_categories
        )
        
        # Create preview with redacted text
        redacted_preview = legal_system.apply_redaction_preview(
            text,
            redaction_suggestions
        )
        
        return JSONResponse(content={
            'status': 'success',
            'original_text': text,
            'redacted_preview': redacted_preview,
            'redaction_suggestions': redaction_suggestions,
            'categories_applied': redaction_categories,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Redaction preview error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for legal transcription service."""
    try:
        # Check system components
        system_status = legal_system.health_check()
        schema_status = schema_processor.health_check()
        
        overall_status = "healthy" if (
            system_status.get('status') == 'healthy' and 
            schema_status.get('status') == 'healthy'
        ) else "degraded"
        
        return JSONResponse(content={
            'status': overall_status,
            'components': {
                'legal_system': system_status,
                'schema_processor': schema_status
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )


# Include router in main application
def get_router():
    """Get the legal transcription router."""
    return router