"""
Internationalization API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from api.database import get_db
from api.auth import get_current_user
from services.internationalization_service import i18n_service, TranslationContext
from api.database import User

router = APIRouter(prefix="/api/v1/i18n")


class TranslationRequest(BaseModel):
    key: str = Field(..., description="Translation key")
    language_code: str = Field(..., description="Target language code")
    namespace: str = Field(default="general", description="Translation namespace")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variables for substitution")


class TranslationResponse(BaseModel):
    key: str
    value: str
    language_code: str
    namespace: str


class SetTranslationRequest(BaseModel):
    key: str = Field(..., description="Translation key")
    language_code: str = Field(..., description="Language code")
    value: str = Field(..., description="Translation value")
    namespace: str = Field(default="general", description="Translation namespace")


class BulkTranslationRequest(BaseModel):
    keys: List[str] = Field(..., description="Translation keys to fetch")
    language_code: str = Field(..., description="Target language code")
    namespace: str = Field(default="general", description="Translation namespace")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variables for substitution")


class LanguagePreferenceRequest(BaseModel):
    language_code: str = Field(..., description="Preferred language code")
    timezone: Optional[str] = Field(None, description="User timezone")
    date_format: Optional[str] = Field(None, description="Preferred date format")
    number_format: Optional[str] = Field(None, description="Preferred number format")


class FormatRequest(BaseModel):
    value: Any = Field(..., description="Value to format")
    language_code: str = Field(..., description="Language code for formatting")
    type: str = Field(..., description="Format type: date, time, number, currency")


class BulkTranslateRequest(BaseModel):
    texts: Dict[str, str] = Field(..., description="Texts to translate (key-value pairs)")
    target_language: str = Field(..., description="Target language code")
    source_language: str = Field(default="en", description="Source language code")


@router.get("/languages", response_model=List[Dict[str, Any]])
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        languages = await i18n_service.get_supported_languages()
        return languages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")


@router.post("/translate", response_model=TranslationResponse)
async def get_translation(
    request: TranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get translation for a specific key"""
    try:
        context = TranslationContext(
            namespace=request.namespace,
            user_id=current_user.id,
            variables=request.variables
        )
        
        translation = await i18n_service.get_translation(
            key=request.key,
            language_code=request.language_code,
            context=context
        )
        
        return TranslationResponse(
            key=request.key,
            value=translation,
            language_code=request.language_code,
            namespace=request.namespace
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/translate/bulk", response_model=Dict[str, str])
async def get_bulk_translations(
    request: BulkTranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get multiple translations at once"""
    try:
        context = TranslationContext(
            namespace=request.namespace,
            user_id=current_user.id,
            variables=request.variables
        )
        
        translations = {}
        for key in request.keys:
            translation = await i18n_service.get_translation(
                key=key,
                language_code=request.language_code,
                context=context
            )
            translations[key] = translation
        
        return translations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk translation failed: {str(e)}")


@router.post("/translate/set")
async def set_translation(
    request: SetTranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set or update a translation"""
    try:
        # Check if user has admin privileges (in production, implement proper role checking)
        # For now, allow all authenticated users to set translations
        
        success = await i18n_service.set_translation(
            db=db,
            key=request.key,
            language_code=request.language_code,
            value=request.value,
            namespace=request.namespace,
            user_id=current_user.id
        )
        
        if success:
            return {"success": True, "message": "Translation set successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to set translation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set translation: {str(e)}")


@router.get("/detect-language")
async def detect_language(
    text: str = Query(..., description="Text to analyze for language detection")
):
    """Detect language from text content"""
    try:
        detected_language = i18n_service.detect_language_from_text(text)
        
        # Get language info
        languages = await i18n_service.get_supported_languages()
        language_info = next((lang for lang in languages if lang["code"] == detected_language), None)
        
        return {
            "detected_language": detected_language,
            "confidence": 0.8,  # Mock confidence score
            "language_info": language_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.get("/user/preference")
async def get_user_language_preference(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's language preference"""
    try:
        language_code = i18n_service.get_user_language_preference(db, current_user.id)
        
        # Get additional locale info
        languages = await i18n_service.get_supported_languages()
        language_info = next((lang for lang in languages if lang["code"] == language_code), None)
        
        return {
            "language_code": language_code,
            "language_info": language_info,
            "text_direction": i18n_service.get_text_direction(language_code),
            "is_rtl": i18n_service.is_rtl_language(language_code)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preference: {str(e)}")


@router.post("/user/preference")
async def set_user_language_preference(
    request: LanguagePreferenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set user's language preference"""
    try:
        success = await i18n_service.set_user_language_preference(
            db=db,
            user_id=current_user.id,
            language_code=request.language_code,
            timezone=request.timezone,
            date_format=request.date_format,
            number_format=request.number_format
        )
        
        if success:
            return {
                "success": True,
                "message": "Language preference updated",
                "language_code": request.language_code,
                "text_direction": i18n_service.get_text_direction(request.language_code),
                "is_rtl": i18n_service.is_rtl_language(request.language_code)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to set preference")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set preference: {str(e)}")


@router.post("/format")
async def format_value(request: FormatRequest):
    """Format a value according to locale"""
    try:
        from datetime import datetime, date
        from decimal import Decimal
        
        if request.type == "date":
            if isinstance(request.value, str):
                # Parse date string
                try:
                    date_obj = datetime.fromisoformat(request.value.replace('Z', '+00:00')).date()
                except:
                    date_obj = datetime.strptime(request.value, "%Y-%m-%d").date()
            else:
                date_obj = request.value
            
            formatted = i18n_service.format_date(date_obj, request.language_code)
            
        elif request.type == "time":
            if isinstance(request.value, str):
                datetime_obj = datetime.fromisoformat(request.value.replace('Z', '+00:00'))
            else:
                datetime_obj = request.value
            
            formatted = i18n_service.format_time(datetime_obj, request.language_code)
            
        elif request.type == "number":
            number = float(request.value) if isinstance(request.value, str) else request.value
            formatted = i18n_service.format_number(number, request.language_code)
            
        elif request.type == "currency":
            amount = float(request.value) if isinstance(request.value, str) else request.value
            formatted = i18n_service.format_currency(amount, request.language_code)
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported format type")
        
        return {
            "original": request.value,
            "formatted": formatted,
            "language_code": request.language_code,
            "type": request.type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formatting failed: {str(e)}")


@router.post("/translate/ai")
async def ai_bulk_translate(
    request: BulkTranslateRequest,
    current_user: User = Depends(get_current_user)
):
    """Translate texts using AI translation service"""
    try:
        translated_texts = await i18n_service.bulk_translate(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        return {
            "success": True,
            "source_language": request.source_language,
            "target_language": request.target_language,
            "translations": translated_texts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI translation failed: {str(e)}")


@router.get("/export/{language_code}")
async def export_translations(
    language_code: str,
    db: Session = Depends(get_db),
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    format: str = Query("json", description="Export format: json, csv"),
    current_user: User = Depends(get_current_user)
):
    """Export translations for a language"""
    try:
        data = await i18n_service.export_translations(
            db=db,
            language_code=language_code,
            namespace=namespace,
            format=format
        )
        
        # Set appropriate content type and filename
        if format == "json":
            content_type = "application/json"
            filename = f"translations_{language_code}_{namespace or 'all'}.json"
        elif format == "csv":
            content_type = "text/csv"
            filename = f"translations_{language_code}_{namespace or 'all'}.csv"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        return Response(
            content=data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import/{language_code}")
async def import_translations(
    language_code: str,
    file: UploadFile = File(...),
    format: str = Query("json", description="Import format: json, csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import translations from file"""
    try:
        data = await file.read()
        
        result = await i18n_service.import_translations(
            db=db,
            data=data,
            language_code=language_code,
            format=format,
            user_id=current_user.id
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/namespaces")
async def get_translation_namespaces(
    db: Session = Depends(get_db),
    language_code: Optional[str] = Query(None, description="Filter by language")
):
    """Get list of translation namespaces"""
    try:
        # This would query the database for unique namespaces
        # For now, return common namespaces
        namespaces = [
            {
                "name": "general",
                "description": "General application translations",
                "key_count": 150
            },
            {
                "name": "navigation",
                "description": "Navigation and menu items",
                "key_count": 45
            },
            {
                "name": "forms",
                "description": "Form labels and validation messages",
                "key_count": 80
            },
            {
                "name": "errors",
                "description": "Error messages and notifications",
                "key_count": 60
            },
            {
                "name": "dashboard",
                "description": "Dashboard and analytics",
                "key_count": 120
            },
            {
                "name": "transcription",
                "description": "Transcription-related terms",
                "key_count": 90
            }
        ]
        
        return {"namespaces": namespaces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get namespaces: {str(e)}")


@router.get("/stats")
async def get_translation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get translation statistics"""
    try:
        # Mock statistics - in production, query the actual database
        stats = {
            "total_keys": 545,
            "languages": 10,
            "namespaces": 6,
            "completion_rate": {
                "en": 100,
                "es": 85,
                "fr": 80,
                "de": 75,
                "zh-CN": 60,
                "ja": 55,
                "ar": 40,
                "he": 35,
                "ru": 70,
                "pt": 65
            },
            "recent_updates": [
                {
                    "key": "dashboard.title",
                    "language": "es",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "updated_by": "translator_user"
                },
                {
                    "key": "forms.validation.email",
                    "language": "fr",
                    "updated_at": "2024-01-15T09:15:00Z",
                    "updated_by": "admin_user"
                }
            ]
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/missing")
async def get_missing_translations(
    language_code: str = Query(..., description="Target language code"),
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get missing translations for a language"""
    try:
        # This would compare against English (base language) keys
        # For now, return mock missing translations
        missing_translations = [
            {
                "key": "new_feature.title",
                "namespace": "general",
                "english_value": "New Feature",
                "priority": "high"
            },
            {
                "key": "settings.advanced.option",
                "namespace": "settings",
                "english_value": "Advanced Option",
                "priority": "medium"
            },
            {
                "key": "dashboard.chart.tooltip",
                "namespace": "dashboard",
                "english_value": "Click for details",
                "priority": "low"
            }
        ]
        
        if namespace:
            missing_translations = [
                t for t in missing_translations if t["namespace"] == namespace
            ]
        
        return {
            "language_code": language_code,
            "namespace": namespace,
            "missing_count": len(missing_translations),
            "missing_translations": missing_translations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get missing translations: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for i18n service"""
    return {
        "status": "healthy",
        "service": "internationalization",
        "supported_languages": len(i18n_service.locales_info),
        "cache_status": "active"
    }