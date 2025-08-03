"""
Settings API Endpoints
REST API for user settings and configuration management
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel

from api.auth import auth_required, create_api_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

# Data models
class UserPreferences(BaseModel):
    language: str = "en"
    theme: str = "light"  # light, dark, auto
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "24h"  # 12h, 24h
    notifications_enabled: bool = True
    email_notifications: bool = True
    auto_save: bool = True
    default_transcription_language: str = "auto"
    audio_quality: str = "high"  # low, medium, high
    max_file_size_mb: int = 100
    retention_days: int = 30

class TranscriptionSettings(BaseModel):
    default_language: str = "auto"
    detect_code_switching: bool = False
    confidence_threshold: float = 0.8
    speaker_diarization: bool = False
    noise_reduction: bool = True
    auto_punctuation: bool = True
    profanity_filter: bool = False
    custom_vocabulary: List[str] = []
    model_preference: str = "balanced"  # fast, balanced, accurate

class ExportSettings(BaseModel):
    default_format: str = "json"  # json, csv, txt, srt, vtt
    include_timestamps: bool = True
    include_confidence: bool = False
    include_speaker_labels: bool = False
    entity_format: str = "grouped"  # grouped, inline, separate

class SecuritySettings(BaseModel):
    two_factor_enabled: bool = False
    session_timeout_minutes: int = 480  # 8 hours
    require_password_change: bool = False
    allowed_ip_addresses: List[str] = []
    data_encryption: bool = True
    audit_logging: bool = True

class SystemSettings(BaseModel):
    concurrent_transcriptions: int = 2
    queue_priority: str = "fifo"  # fifo, priority, round_robin
    cleanup_temp_files: bool = True
    backup_enabled: bool = True
    backup_frequency: str = "daily"  # daily, weekly, monthly
    storage_limit_gb: int = 10

class AllSettings(BaseModel):
    user_preferences: UserPreferences
    transcription: TranscriptionSettings
    export: ExportSettings
    security: SecuritySettings
    system: SystemSettings

def get_default_settings() -> AllSettings:
    """Get default settings configuration"""
    return AllSettings(
        user_preferences=UserPreferences(),
        transcription=TranscriptionSettings(),
        export=ExportSettings(),
        security=SecuritySettings(),
        system=SystemSettings()
    )

@router.get("/user", response_model=UserPreferences)
async def get_user_preferences(
    user_id: str = "test_user"
):
    """Get user preferences"""
    try:
        # In real implementation, fetch from database
        preferences = UserPreferences()
        
        return preferences
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user preferences")

@router.put("/user")
async def update_user_preferences(
    preferences: UserPreferences,
    user_id: str = "test_user"
):
    """Update user preferences"""
    try:
        # Validate settings
        if preferences.theme not in ["light", "dark", "auto"]:
            raise HTTPException(status_code=400, detail="Invalid theme setting")
        
        if preferences.max_file_size_mb < 1 or preferences.max_file_size_mb > 1000:
            raise HTTPException(status_code=400, detail="File size limit must be between 1MB and 1000MB")
        
        # In real implementation, save to database
        logger.info(f"Updated user preferences for {user_id}")
        
        return create_api_response(
            preferences.dict(),
            "User preferences updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user preferences")

@router.get("/transcription", response_model=TranscriptionSettings)
async def get_transcription_settings(
    user_id: str = "test_user"
):
    """Get transcription settings"""
    try:
        settings = TranscriptionSettings()
        return settings
        
    except Exception as e:
        logger.error(f"Failed to get transcription settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transcription settings")

@router.put("/transcription")
async def update_transcription_settings(
    settings: TranscriptionSettings,
    user_id: str = "test_user"
):
    """Update transcription settings"""
    try:
        # Validate settings
        if settings.confidence_threshold < 0.1 or settings.confidence_threshold > 1.0:
            raise HTTPException(status_code=400, detail="Confidence threshold must be between 0.1 and 1.0")
        
        if settings.model_preference not in ["fast", "balanced", "accurate"]:
            raise HTTPException(status_code=400, detail="Invalid model preference")
        
        logger.info(f"Updated transcription settings for {user_id}")
        
        return create_api_response(
            settings.dict(),
            "Transcription settings updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update transcription settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update transcription settings")

@router.get("/export", response_model=ExportSettings)
async def get_export_settings(
    user_id: str = "test_user"
):
    """Get export settings"""
    try:
        settings = ExportSettings()
        return settings
        
    except Exception as e:
        logger.error(f"Failed to get export settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export settings")

@router.put("/export")
async def update_export_settings(
    settings: ExportSettings,
    user_id: str = "test_user"
):
    """Update export settings"""
    try:
        # Validate settings
        valid_formats = ["json", "csv", "txt", "srt", "vtt"]
        if settings.default_format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid export format. Must be one of: {valid_formats}")
        
        logger.info(f"Updated export settings for {user_id}")
        
        return create_api_response(
            settings.dict(),
            "Export settings updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update export settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update export settings")

@router.get("/all", response_model=AllSettings)
async def get_all_settings(
    user_id: str = "test_user"
):
    """Get all user settings"""
    try:
        settings = get_default_settings()
        
        return settings
        
    except Exception as e:
        logger.error(f"Failed to get all settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve settings")

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages for transcription"""
    try:
        # This would come from the language_support.py module
        languages = [
            {"code": "auto", "name": "Auto-detect", "has_ner": True, "is_rtl": False},
            {"code": "en", "name": "English", "has_ner": True, "is_rtl": False},
            {"code": "es", "name": "Spanish", "has_ner": True, "is_rtl": False},
            {"code": "fr", "name": "French", "has_ner": True, "is_rtl": False},
            {"code": "de", "name": "German", "has_ner": True, "is_rtl": False},
            {"code": "it", "name": "Italian", "has_ner": True, "is_rtl": False},
            {"code": "pt", "name": "Portuguese", "has_ner": True, "is_rtl": False},
            {"code": "ja", "name": "Japanese", "has_ner": False, "is_rtl": False},
            {"code": "ko", "name": "Korean", "has_ner": False, "is_rtl": False},
            {"code": "zh", "name": "Chinese", "has_ner": False, "is_rtl": False},
            {"code": "ar", "name": "Arabic", "has_ner": False, "is_rtl": True},
            {"code": "he", "name": "Hebrew", "has_ner": False, "is_rtl": True},
            {"code": "ru", "name": "Russian", "has_ner": False, "is_rtl": False},
            {"code": "hi", "name": "Hindi", "has_ner": False, "is_rtl": False},
            {"code": "th", "name": "Thai", "has_ner": False, "is_rtl": False}
        ]
        
        return create_api_response(languages, "Supported languages retrieved successfully")
        
    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve supported languages")

@router.get("/models")
async def get_available_models():
    """Get list of available transcription models"""
    try:
        models = [
            {
                "id": "whisper-tiny",
                "name": "Whisper Tiny",
                "description": "Fastest processing, lower accuracy",
                "size": "39 MB",
                "languages": 99,
                "speed": "~32x realtime",
                "accuracy": "Good"
            },
            {
                "id": "whisper-base",
                "name": "Whisper Base",
                "description": "Balanced speed and accuracy",
                "size": "74 MB",
                "languages": 99,
                "speed": "~16x realtime",
                "accuracy": "Better"
            },
            {
                "id": "whisper-small",
                "name": "Whisper Small",
                "description": "Good accuracy, moderate speed",
                "size": "244 MB",
                "languages": 99,
                "speed": "~6x realtime",
                "accuracy": "Good"
            },
            {
                "id": "whisper-medium",
                "name": "Whisper Medium",
                "description": "High accuracy, slower processing",
                "size": "769 MB",
                "languages": 99,
                "speed": "~2x realtime",
                "accuracy": "Very Good"
            },
            {
                "id": "whisper-large-v2",
                "name": "Whisper Large v2",
                "description": "Highest accuracy, slowest processing",
                "size": "1550 MB",
                "languages": 99,
                "speed": "~1x realtime",
                "accuracy": "Excellent"
            }
        ]
        
        return create_api_response(models, "Available models retrieved successfully")
        
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available models")

@router.post("/reset")
async def reset_settings_to_default(
    category: Optional[str] = None,
    user_id: str = "test_user"
):
    """Reset settings to default values"""
    try:
        if category:
            # Reset specific category
            if category not in ["user_preferences", "transcription", "export", "security", "system"]:
                raise HTTPException(status_code=400, detail="Invalid settings category")
            
            message = f"{category.replace('_', ' ').title()} settings reset to default"
        else:
            # Reset all settings
            message = "All settings reset to default"
        
        # In real implementation, reset to defaults in database
        logger.info(f"Reset settings for {user_id}: {category or 'all'}")
        
        return create_api_response(
            {"category": category, "reset_at": datetime.now().isoformat()},
            message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset settings")

@router.post("/export")
async def export_settings(
    user_id: str = "test_user"
):
    """Export user settings as JSON for backup"""
    try:
        settings = get_default_settings()
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "user_id": user_id,
            "settings": settings.dict(),
            "version": "1.0"
        }
        
        return create_api_response(export_data, "Settings exported successfully")
        
    except Exception as e:
        logger.error(f"Failed to export settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to export settings")

@router.post("/import")
async def import_settings(
    settings_data: dict,
    user_id: str = "test_user"
):
    """Import settings from backup JSON"""
    try:
        # Validate import data structure
        if "settings" not in settings_data:
            raise HTTPException(status_code=400, detail="Invalid settings data format")
        
        # In real implementation, validate and save imported settings
        logger.info(f"Imported settings for {user_id}")
        
        return create_api_response(
            {"imported_at": datetime.now().isoformat()},
            "Settings imported successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to import settings")