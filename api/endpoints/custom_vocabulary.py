"""
Custom Vocabulary System API Endpoints
REST API for domain-specific vocabulary management and adaptation
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any, Union
import os
import sys
import asyncio
import logging
import tempfile
from datetime import datetime
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_middleware import get_current_active_user, require_write
from api.dependencies import create_api_response, create_error_response

# Import custom vocabulary system
from custom_vocabulary_system import (
    CustomVocabularyManager, VocabularyEntry, VocabularyDomain, 
    VocabularyStatus, PronunciationGuide, VocabularyValidation,
    DomainAdaptationConfig, VocabularyAnalytics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-vocabulary", tags=["Custom Vocabulary"])

# Initialize components
vocabulary_manager = CustomVocabularyManager()

# Pydantic models for API
class VocabularyEntryAPI(BaseModel):
    """API model for vocabulary entries"""
    word: str = Field(..., description="The vocabulary word", min_length=1, max_length=100)
    definition: str = Field(..., description="Definition of the word", min_length=1)
    domain: str = Field(..., description="Domain/category of the word")
    pronunciation: Optional[str] = Field(None, description="Phonetic pronunciation")
    phonetic_transcription: Optional[str] = Field(None, description="IPA transcription")
    example_usage: Optional[str] = Field(None, description="Example sentence")
    synonyms: List[str] = Field(default=[], description="List of synonyms")
    related_terms: List[str] = Field(default=[], description="Related terminology")
    difficulty_level: str = Field(default="intermediate", description="Difficulty level")
    language: str = Field(default="en", description="Language code")
    tags: List[str] = Field(default=[], description="Additional tags")

class VocabularyEntryResponse(BaseModel):
    """API response model for vocabulary entries"""
    id: str
    word: str
    definition: str
    domain: str
    pronunciation: Optional[str]
    phonetic_transcription: Optional[str]
    example_usage: Optional[str]
    synonyms: List[str]
    related_terms: List[str]
    difficulty_level: str
    language: str
    tags: List[str]
    status: str
    confidence_score: float
    usage_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str

class DomainConfigAPI(BaseModel):
    """API model for domain configuration"""
    domain_name: str = Field(..., description="Name of the domain")
    description: str = Field(..., description="Domain description")
    keywords: List[str] = Field(default=[], description="Domain keywords")
    priority_level: str = Field(default="medium", description="Priority level")
    auto_validation: bool = Field(default=False, description="Enable auto-validation")
    min_confidence_threshold: float = Field(default=0.7, description="Minimum confidence", ge=0.0, le=1.0)
    language: str = Field(default="en", description="Primary language")

class VocabularySearchAPI(BaseModel):
    """API model for vocabulary search"""
    query: str = Field(..., description="Search query", min_length=1)
    domain: Optional[str] = Field(None, description="Filter by domain")
    language: Optional[str] = Field(None, description="Filter by language")
    status: Optional[str] = Field(None, description="Filter by status")
    limit: int = Field(default=20, description="Maximum results", ge=1, le=100)
    include_similar: bool = Field(default=True, description="Include similar words")

class BulkImportAPI(BaseModel):
    """API model for bulk vocabulary import"""
    entries: List[VocabularyEntryAPI] = Field(..., description="List of vocabulary entries")
    domain: str = Field(..., description="Target domain")
    auto_validate: bool = Field(default=False, description="Auto-validate entries")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing entries")

class VocabularyAnalyticsAPI(BaseModel):
    """API response model for vocabulary analytics"""
    total_entries: int
    entries_by_domain: Dict[str, int]
    entries_by_status: Dict[str, int]
    entries_by_language: Dict[str, int]
    most_used_words: List[Dict[str, Any]]
    recent_additions: List[Dict[str, Any]]
    validation_statistics: Dict[str, Any]
    domain_coverage: Dict[str, float]

@router.post("/entries", response_model=VocabularyEntryResponse)
async def create_vocabulary_entry(
    entry: VocabularyEntryAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new vocabulary entry"""
    try:
        # Create vocabulary entry
        vocab_entry = VocabularyEntry(
            word=entry.word.lower().strip(),
            definition=entry.definition.strip(),
            domain=entry.domain,
            pronunciation=entry.pronunciation,
            phonetic_transcription=entry.phonetic_transcription,
            example_usage=entry.example_usage,
            synonyms=entry.synonyms,
            related_terms=entry.related_terms,
            difficulty_level=entry.difficulty_level,
            language=entry.language,
            tags=entry.tags,
            created_by=current_user.get('user_id', 'unknown')
        )
        
        # Add to vocabulary manager
        result = await vocabulary_manager.add_entry(vocab_entry)
        
        # Convert to API response
        api_result = VocabularyEntryResponse(
            id=result.id,
            word=result.word,
            definition=result.definition,
            domain=result.domain,
            pronunciation=result.pronunciation,
            phonetic_transcription=result.phonetic_transcription,
            example_usage=result.example_usage,
            synonyms=result.synonyms,
            related_terms=result.related_terms,
            difficulty_level=result.difficulty_level,
            language=result.language,
            tags=result.tags,
            status=result.status.value,
            confidence_score=float(result.confidence_score),
            usage_count=result.usage_count,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by
        )
        
        logger.info(f"Vocabulary entry created: {entry.word} by user {current_user.get('user_id', 'unknown')}")
        
        return create_api_response(
            data=api_result,
            message="Vocabulary entry created successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error creating vocabulary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entry: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating vocabulary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vocabulary entry"
        )

@router.get("/entries/{entry_id}", response_model=VocabularyEntryResponse)
async def get_vocabulary_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get a specific vocabulary entry"""
    try:
        entry = await vocabulary_manager.get_entry(entry_id)
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary entry not found"
            )
        
        # Convert to API response
        api_result = VocabularyEntryResponse(
            id=entry.id,
            word=entry.word,
            definition=entry.definition,
            domain=entry.domain,
            pronunciation=entry.pronunciation,
            phonetic_transcription=entry.phonetic_transcription,
            example_usage=entry.example_usage,
            synonyms=entry.synonyms,
            related_terms=entry.related_terms,
            difficulty_level=entry.difficulty_level,
            language=entry.language,
            tags=entry.tags,
            status=entry.status.value,
            confidence_score=float(entry.confidence_score),
            usage_count=entry.usage_count,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            created_by=entry.created_by
        )
        
        return create_api_response(
            data=api_result,
            message="Vocabulary entry retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vocabulary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vocabulary entry"
        )

@router.put("/entries/{entry_id}", response_model=VocabularyEntryResponse)
async def update_vocabulary_entry(
    entry_id: str,
    entry: VocabularyEntryAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Update an existing vocabulary entry"""
    try:
        # Get existing entry
        existing_entry = await vocabulary_manager.get_entry(entry_id)
        
        if not existing_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary entry not found"
            )
        
        # Update entry
        updated_entry = VocabularyEntry(
            id=entry_id,
            word=entry.word.lower().strip(),
            definition=entry.definition.strip(),
            domain=entry.domain,
            pronunciation=entry.pronunciation,
            phonetic_transcription=entry.phonetic_transcription,
            example_usage=entry.example_usage,
            synonyms=entry.synonyms,
            related_terms=entry.related_terms,
            difficulty_level=entry.difficulty_level,
            language=entry.language,
            tags=entry.tags,
            updated_by=current_user.get('user_id', 'unknown')
        )
        
        result = await vocabulary_manager.update_entry(updated_entry)
        
        # Convert to API response
        api_result = VocabularyEntryResponse(
            id=result.id,
            word=result.word,
            definition=result.definition,
            domain=result.domain,
            pronunciation=result.pronunciation,
            phonetic_transcription=result.phonetic_transcription,
            example_usage=result.example_usage,
            synonyms=result.synonyms,
            related_terms=result.related_terms,
            difficulty_level=result.difficulty_level,
            language=result.language,
            tags=result.tags,
            status=result.status.value,
            confidence_score=float(result.confidence_score),
            usage_count=result.usage_count,
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by
        )
        
        logger.info(f"Vocabulary entry updated: {entry.word} by user {current_user.get('user_id', 'unknown')}")
        
        return create_api_response(
            data=api_result,
            message="Vocabulary entry updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error updating vocabulary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vocabulary entry"
        )

@router.delete("/entries/{entry_id}")
async def delete_vocabulary_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a vocabulary entry"""
    try:
        success = await vocabulary_manager.delete_entry(entry_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary entry not found"
            )
        
        logger.info(f"Vocabulary entry deleted: {entry_id} by user {current_user.get('user_id', 'unknown')}")
        
        return create_api_response(
            data={"deleted": True},
            message="Vocabulary entry deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deleting vocabulary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vocabulary entry"
        )

@router.post("/search", response_model=List[VocabularyEntryResponse])
async def search_vocabulary(
    search: VocabularySearchAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Search vocabulary entries"""
    try:
        results = await vocabulary_manager.search_entries(
            query=search.query,
            domain=search.domain,
            language=search.language,
            status=search.status,
            limit=search.limit,
            include_similar=search.include_similar
        )
        
        # Convert to API response
        api_results = []
        for entry in results:
            api_results.append(VocabularyEntryResponse(
                id=entry.id,
                word=entry.word,
                definition=entry.definition,
                domain=entry.domain,
                pronunciation=entry.pronunciation,
                phonetic_transcription=entry.phonetic_transcription,
                example_usage=entry.example_usage,
                synonyms=entry.synonyms,
                related_terms=entry.related_terms,
                difficulty_level=entry.difficulty_level,
                language=entry.language,
                tags=entry.tags,
                status=entry.status.value,
                confidence_score=float(entry.confidence_score),
                usage_count=entry.usage_count,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                created_by=entry.created_by
            ))
        
        logger.info(f"Vocabulary search completed: '{search.query}' returned {len(api_results)} results")
        
        return create_api_response(
            data=api_results,
            message=f"Found {len(api_results)} vocabulary entries"
        )
        
    except Exception as e:
        logger.error(f"Error searching vocabulary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search vocabulary"
        )

@router.post("/bulk-import")
async def bulk_import_vocabulary(
    import_data: BulkImportAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Bulk import vocabulary entries"""
    try:
        if len(import_data.entries) > 1000:  # Limit bulk import size
            raise ValueError("Bulk import cannot exceed 1000 entries")
        
        results = []
        successful = 0
        failed = 0
        
        for i, entry_data in enumerate(import_data.entries):
            try:
                # Create vocabulary entry
                vocab_entry = VocabularyEntry(
                    word=entry_data.word.lower().strip(),
                    definition=entry_data.definition.strip(),
                    domain=import_data.domain,
                    pronunciation=entry_data.pronunciation,
                    phonetic_transcription=entry_data.phonetic_transcription,
                    example_usage=entry_data.example_usage,
                    synonyms=entry_data.synonyms,
                    related_terms=entry_data.related_terms,
                    difficulty_level=entry_data.difficulty_level,
                    language=entry_data.language,
                    tags=entry_data.tags,
                    created_by=current_user.get('user_id', 'unknown')
                )
                
                # Add to vocabulary manager
                result = await vocabulary_manager.add_entry(
                    vocab_entry,
                    auto_validate=import_data.auto_validate,
                    overwrite_existing=import_data.overwrite_existing
                )
                
                results.append({
                    "index": i,
                    "word": entry_data.word,
                    "status": "success",
                    "entry_id": result.id
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "word": entry_data.word,
                    "status": "error",
                    "error": str(e)
                })
                failed += 1
        
        logger.info(f"Bulk vocabulary import completed: {successful} successful, {failed} failed")
        
        return create_api_response(
            data={
                "results": results,
                "summary": {
                    "total": len(import_data.entries),
                    "successful": successful,
                    "failed": failed
                }
            },
            message=f"Bulk import completed: {successful} successful, {failed} failed"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in bulk import: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid import data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in bulk import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk import"
        )

@router.post("/domains", response_model=Dict[str, Any])
async def create_domain(
    domain: DomainConfigAPI,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new vocabulary domain"""
    try:
        domain_config = DomainAdaptationConfig(
            domain_name=domain.domain_name,
            description=domain.description,
            keywords=domain.keywords,
            priority_level=domain.priority_level,
            auto_validation=domain.auto_validation,
            min_confidence_threshold=domain.min_confidence_threshold,
            language=domain.language,
            created_by=current_user.get('user_id', 'unknown')
        )
        
        result = await vocabulary_manager.create_domain(domain_config)
        
        logger.info(f"Vocabulary domain created: {domain.domain_name} by user {current_user.get('user_id', 'unknown')}")
        
        return create_api_response(
            data=result,
            message="Vocabulary domain created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating vocabulary domain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vocabulary domain"
        )

@router.get("/domains")
async def get_domains(
    current_user: dict = Depends(get_current_active_user)
):
    """Get all vocabulary domains"""
    try:
        domains = await vocabulary_manager.get_domains()
        
        return create_api_response(
            data=domains,
            message="Vocabulary domains retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vocabulary domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vocabulary domains"
        )

@router.post("/validate/{entry_id}")
async def validate_vocabulary_entry(
    entry_id: str,
    validation_status: str = Form(...),
    validation_notes: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_active_user)
):
    """Validate a vocabulary entry"""
    try:
        if validation_status not in ['approved', 'rejected', 'pending']:
            raise ValueError("Invalid validation status")
        
        result = await vocabulary_manager.validate_entry(
            entry_id=entry_id,
            status=validation_status,
            notes=validation_notes,
            validator=current_user.get('user_id', 'unknown')
        )
        
        logger.info(f"Vocabulary entry validated: {entry_id} -> {validation_status}")
        
        return create_api_response(
            data=result,
            message=f"Vocabulary entry {validation_status} successfully"
        )
        
    except Exception as e:
        logger.error(f"Error validating vocabulary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate vocabulary entry"
        )

@router.post("/pronunciation/{entry_id}")
async def add_pronunciation(
    entry_id: str,
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Add pronunciation audio for a vocabulary entry"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process pronunciation
            result = await vocabulary_manager.add_pronunciation(
                entry_id=entry_id,
                audio_file_path=temp_file_path,
                uploaded_by=current_user.get('user_id', 'unknown')
            )
            
            logger.info(f"Pronunciation added for vocabulary entry: {entry_id}")
            
            return create_api_response(
                data=result,
                message="Pronunciation added successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error adding pronunciation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add pronunciation"
        )

@router.get("/analytics", response_model=VocabularyAnalyticsAPI)
async def get_vocabulary_analytics(
    domain: Optional[str] = None,
    language: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get vocabulary analytics and statistics"""
    try:
        analytics = await vocabulary_manager.get_analytics(
            domain=domain,
            language=language
        )
        
        api_analytics = VocabularyAnalyticsAPI(
            total_entries=analytics.total_entries,
            entries_by_domain=analytics.entries_by_domain,
            entries_by_status=analytics.entries_by_status,
            entries_by_language=analytics.entries_by_language,
            most_used_words=analytics.most_used_words,
            recent_additions=analytics.recent_additions,
            validation_statistics=analytics.validation_statistics,
            domain_coverage=analytics.domain_coverage
        )
        
        return create_api_response(
            data=api_analytics,
            message="Vocabulary analytics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vocabulary analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vocabulary analytics"
        )

@router.post("/export")
async def export_vocabulary(
    domain: Optional[str] = None,
    language: Optional[str] = None,
    format: str = "json",
    current_user: dict = Depends(get_current_active_user)
):
    """Export vocabulary entries"""
    try:
        if format not in ['json', 'csv', 'xlsx']:
            raise ValueError("Invalid export format")
        
        export_data = await vocabulary_manager.export_vocabulary(
            domain=domain,
            language=language,
            format=format
        )
        
        logger.info(f"Vocabulary export completed: {format} format")
        
        return create_api_response(
            data={
                "export_data": export_data,
                "format": format,
                "exported_at": datetime.now().isoformat()
            },
            message="Vocabulary exported successfully"
        )
        
    except Exception as e:
        logger.error(f"Error exporting vocabulary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export vocabulary"
        )

@router.get("/suggestions/{word}")
async def get_word_suggestions(
    word: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_active_user)
):
    """Get word suggestions and similar terms"""
    try:
        suggestions = await vocabulary_manager.get_suggestions(
            word=word.lower().strip(),
            limit=limit
        )
        
        return create_api_response(
            data=suggestions,
            message=f"Found {len(suggestions)} suggestions for '{word}'"
        )
        
    except Exception as e:
        logger.error(f"Error getting word suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get word suggestions"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "vocabulary_manager": "operational",
                "database": "connected",
                "nlp_processor": "available",
                "pronunciation_engine": "available"
            },
            "total_entries": await vocabulary_manager.get_total_entries(),
            "active_domains": await vocabulary_manager.get_active_domains_count()
        }
        
        return create_api_response(
            data=health_status,
            message="Custom vocabulary service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=create_error_response(
                error="Service unhealthy",
                details=str(e)
            )
        )