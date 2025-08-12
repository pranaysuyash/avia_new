"""
GDPR Compliance Service
Provides comprehensive data protection and privacy compliance tools
"""

import json
import logging
import os
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db, User, Transcript
from services.audit_logging_service import audit_service, AuditEventType
from api.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class DataProcessingLawfulBasis(Enum):
    """GDPR Article 6 lawful bases for processing"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataCategory(Enum):
    """Categories of personal data"""
    IDENTITY = "identity"
    CONTACT = "contact"
    TECHNICAL = "technical"
    USAGE = "usage"
    CONTENT = "content"
    BEHAVIORAL = "behavioral"
    BIOMETRIC = "biometric"
    SPECIAL_CATEGORY = "special_category"


class ConsentStatus(Enum):
    """Consent status options"""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    EXPIRED = "expired"


@dataclass
class DataProcessingRecord:
    """Record of data processing activity"""
    id: str
    data_subject_id: int
    processing_purpose: str
    lawful_basis: DataProcessingLawfulBasis
    data_categories: List[DataCategory]
    recipients: List[str]
    retention_period: Optional[int]  # days
    cross_border_transfer: bool
    automated_decision_making: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class ConsentRecord:
    """User consent record"""
    id: str
    user_id: int
    purpose: str
    consent_status: ConsentStatus
    consent_text: str
    consent_version: str
    given_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    expires_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]


@dataclass
class DataExportRequest:
    """Data portability request"""
    id: str
    user_id: int
    request_type: str  # full_export, specific_data, etc.
    status: str  # pending, processing, completed, failed
    requested_at: datetime
    completed_at: Optional[datetime]
    export_file_path: Optional[str]
    file_size: Optional[int]
    expires_at: datetime
    verification_token: str


class GDPRComplianceService:
    """Service for GDPR compliance operations"""
    
    def __init__(self):
        self.export_storage_path = Path(os.getenv('GDPR_EXPORT_PATH', '/tmp/gdpr_exports'))
        self.export_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Retention periods (in days) for different data types
        self.retention_periods = {
            DataCategory.IDENTITY: 2555,  # 7 years
            DataCategory.CONTACT: 1095,   # 3 years
            DataCategory.TECHNICAL: 365,  # 1 year
            DataCategory.USAGE: 365,      # 1 year
            DataCategory.CONTENT: 2555,   # 7 years (user-generated content)
            DataCategory.BEHAVIORAL: 365, # 1 year
            DataCategory.BIOMETRIC: 30,   # 30 days (voice data)
            DataCategory.SPECIAL_CATEGORY: 90  # 90 days
        }
        
        # Initialize processing records storage
        self.processing_records: Dict[str, DataProcessingRecord] = {}
        self.consent_records: Dict[str, List[ConsentRecord]] = {}
        self.export_requests: Dict[str, DataExportRequest] = {}
    
    async def create_data_export(
        self, 
        user_id: int, 
        export_type: str = "full_export",
        format_type: str = "json"
    ) -> DataExportRequest:
        """
        Create a data portability export for a user (GDPR Article 20)
        
        Args:
            user_id: User ID to export data for
            export_type: Type of export (full_export, transcripts_only, etc.)
            format_type: Export format (json, csv, xml)
        
        Returns:
            DataExportRequest object
        """
        
        request_id = str(uuid.uuid4())
        verification_token = self._generate_verification_token()
        
        export_request = DataExportRequest(
            id=request_id,
            user_id=user_id,
            request_type=export_type,
            status="pending",
            requested_at=datetime.utcnow(),
            completed_at=None,
            export_file_path=None,
            file_size=None,
            expires_at=datetime.utcnow() + timedelta(days=30),  # Export valid for 30 days
            verification_token=verification_token
        )
        
        self.export_requests[request_id] = export_request
        
        # Log the export request
        audit_service.log_event(
            event_type=AuditEventType.DATA_EXPORT_REQUEST,
            action=f"Data export requested: {export_type}",
            user_id=user_id,
            details={
                "request_id": request_id,
                "export_type": export_type,
                "format": format_type
            }
        )
        
        # Start export process asynchronously
        await self._process_data_export(export_request, format_type)
        
        return export_request
    
    async def _process_data_export(self, export_request: DataExportRequest, format_type: str):
        """Process the data export request"""
        
        try:
            export_request.status = "processing"
            
            # Collect user data
            user_data = await self._collect_user_data(export_request.user_id, export_request.request_type)
            
            # Create export file
            export_file_path = await self._create_export_file(
                user_data, 
                export_request.user_id,
                export_request.id,
                format_type
            )
            
            # Update export request
            export_request.status = "completed"
            export_request.completed_at = datetime.utcnow()
            export_request.export_file_path = str(export_file_path)
            export_request.file_size = export_file_path.stat().st_size
            
            # Log completion
            audit_service.log_event(
                event_type=AuditEventType.DATA_EXPORT_COMPLETED,
                action="Data export completed",
                user_id=export_request.user_id,
                details={
                    "request_id": export_request.id,
                    "file_size": export_request.file_size,
                    "format": format_type
                }
            )
            
        except Exception as e:
            export_request.status = "failed"
            logger.error(f"Data export failed for user {export_request.user_id}: {e}")
            
            # Log failure
            audit_service.log_event(
                event_type=AuditEventType.DATA_EXPORT_FAILED,
                action="Data export failed",
                user_id=export_request.user_id,
                error_message=str(e),
                details={"request_id": export_request.id}
            )
    
    async def _collect_user_data(self, user_id: int, export_type: str) -> Dict[str, Any]:
        """Collect all user data for export"""
        
        db = next(get_db())
        user_data = {
            "export_info": {
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "export_type": export_type,
                "gdpr_article": "Article 20 - Right to data portability"
            }
        }
        
        try:
            # 1. User account information
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user_data["account"] = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "is_active": user.is_active,
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                    "subscription_tier": getattr(user, 'subscription_tier', None)
                }
            
            # 2. Transcripts and content
            if export_type in ["full_export", "transcripts_only"]:
                transcripts = db.query(Transcript).filter(Transcript.user_id == user_id).all()
                user_data["transcripts"] = []
                
                for transcript in transcripts:
                    transcript_data = {
                        "id": transcript.id,
                        "title": transcript.title,
                        "content": transcript.content,
                        "language": transcript.language,
                        "duration": transcript.duration,
                        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                        "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None,
                        "file_url": getattr(transcript, 'file_url', None),
                        "file_size": getattr(transcript, 'file_size', None)
                    }
                    
                    # Include segments if available
                    if hasattr(transcript, 'segments') and transcript.segments:
                        try:
                            segments = json.loads(transcript.segments) if isinstance(transcript.segments, str) else transcript.segments
                            transcript_data["segments"] = segments
                        except json.JSONDecodeError:
                            pass
                    
                    user_data["transcripts"].append(transcript_data)
            
            # 3. Usage analytics and behavioral data
            if export_type == "full_export":
                user_data["analytics"] = await self._collect_analytics_data(user_id, db)
                user_data["preferences"] = await self._collect_user_preferences(user_id, db)
                user_data["consent_records"] = self._get_consent_records(user_id)
                user_data["processing_records"] = self._get_processing_records(user_id)
            
            # 4. Cached data
            if redis_cache.is_connected():
                user_data["cached_data"] = await self._collect_cached_data(user_id)
            
            # 5. File metadata
            user_data["files"] = await self._collect_file_metadata(user_id)
            
        finally:
            db.close()
        
        return user_data
    
    async def _collect_analytics_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Collect user analytics data"""
        
        try:
            # Import models dynamically to avoid circular imports
            from sqlalchemy import func, text
            
            analytics_data = {
                "transcription_stats": {},
                "api_usage": {},
                "activity_patterns": {},
                "feature_usage": {}
            }
            
            # 1. Transcription statistics
            transcripts = db.query(Transcript).filter(Transcript.user_id == user_id).all()
            if transcripts:
                total_duration = sum(t.duration or 0 for t in transcripts)
                languages = list(set(t.language for t in transcripts if t.language))
                
                analytics_data["transcription_stats"] = {
                    "total_transcripts": len(transcripts),
                    "total_duration_seconds": total_duration,
                    "languages_used": languages,
                    "average_duration": total_duration / len(transcripts) if transcripts else 0,
                    "first_transcript": min(t.created_at for t in transcripts).isoformat() if transcripts else None,
                    "last_transcript": max(t.created_at for t in transcripts).isoformat() if transcripts else None
                }
            
            # 2. API usage patterns (from audit logs)
            try:
                # Query audit logs for API activity
                api_logs_query = text("""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(DISTINCT action) as unique_actions,
                        MAX(created_at) as last_api_call
                    FROM audit_logs 
                    WHERE user_id = :user_id 
                    AND event_type LIKE 'api_%'
                """)
                
                api_result = db.execute(api_logs_query, {"user_id": user_id}).first()
                
                if api_result:
                    analytics_data["api_usage"] = {
                        "total_requests": api_result.total_requests or 0,
                        "unique_actions": api_result.unique_actions or 0,
                        "last_api_call": api_result.last_api_call.isoformat() if api_result.last_api_call else None
                    }
            except Exception as e:
                logger.warning(f"Could not collect API usage data: {e}")
                analytics_data["api_usage"] = {"error": "Could not retrieve API usage"}
            
            # 3. Activity patterns
            try:
                # Get login activity from audit logs
                login_query = text("""
                    SELECT 
                        COUNT(*) as login_count,
                        MAX(created_at) as last_login,
                        MIN(created_at) as first_login
                    FROM audit_logs
                    WHERE user_id = :user_id
                    AND event_type = 'login'
                """)
                
                login_result = db.execute(login_query, {"user_id": user_id}).first()
                
                if login_result:
                    analytics_data["activity_patterns"] = {
                        "login_count": login_result.login_count or 0,
                        "first_login": login_result.first_login.isoformat() if login_result.first_login else None,
                        "last_login": login_result.last_login.isoformat() if login_result.last_login else None
                    }
            except Exception as e:
                logger.warning(f"Could not collect activity patterns: {e}")
                analytics_data["activity_patterns"] = {"error": "Could not retrieve activity patterns"}
            
            # 4. Feature usage
            try:
                # Analyze transcript metadata for feature usage
                features_used = set()
                for transcript in transcripts:
                    if hasattr(transcript, 'metadata') and transcript.metadata:
                        metadata = transcript.metadata if isinstance(transcript.metadata, dict) else {}
                        if metadata.get('speaker_detection'):
                            features_used.add('speaker_detection')
                        if metadata.get('noise_reduction'):
                            features_used.add('noise_reduction')
                        if metadata.get('punctuation_restoration'):
                            features_used.add('punctuation_restoration')
                        if metadata.get('translation'):
                            features_used.add('translation')
                
                analytics_data["feature_usage"] = {
                    "features_used": list(features_used),
                    "feature_count": len(features_used)
                }
            except Exception as e:
                logger.warning(f"Could not collect feature usage: {e}")
                analytics_data["feature_usage"] = {"error": "Could not retrieve feature usage"}
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error collecting analytics data for user {user_id}: {e}")
            return {
                "error": "Failed to collect analytics data",
                "message": str(e)
            }
    
    async def _collect_user_preferences(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Collect user preferences and settings"""
        
        try:
            preferences = {
                "general_settings": {},
                "notification_preferences": {},
                "privacy_preferences": {},
                "ui_preferences": {}
            }
            
            # 1. Get user's general settings
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # Extract preferences from user metadata or settings
                preferences["general_settings"] = {
                    "language": getattr(user, 'language_preference', 'en'),
                    "timezone": getattr(user, 'timezone', 'UTC'),
                    "date_format": getattr(user, 'date_format', 'YYYY-MM-DD'),
                    "time_format": getattr(user, 'time_format', '24h')
                }
                
                # Check for user metadata
                if hasattr(user, 'metadata') and user.metadata:
                    user_metadata = user.metadata if isinstance(user.metadata, dict) else {}
                    
                    # Extract notification preferences
                    preferences["notification_preferences"] = {
                        "email_enabled": user_metadata.get('email_notifications', True),
                        "transcription_complete": user_metadata.get('notify_transcription_complete', True),
                        "weekly_digest": user_metadata.get('weekly_digest', False),
                        "product_updates": user_metadata.get('product_updates', False),
                        "marketing_emails": user_metadata.get('marketing_emails', False)
                    }
                    
                    # Extract privacy preferences
                    preferences["privacy_preferences"] = {
                        "data_collection": user_metadata.get('allow_data_collection', True),
                        "usage_analytics": user_metadata.get('allow_analytics', True),
                        "error_reporting": user_metadata.get('allow_error_reporting', True),
                        "personalization": user_metadata.get('allow_personalization', False),
                        "third_party_sharing": user_metadata.get('allow_third_party_sharing', False)
                    }
                    
                    # Extract UI preferences
                    preferences["ui_preferences"] = {
                        "theme": user_metadata.get('theme', 'light'),
                        "sidebar_collapsed": user_metadata.get('sidebar_collapsed', False),
                        "default_view": user_metadata.get('default_view', 'dashboard'),
                        "items_per_page": user_metadata.get('items_per_page', 25)
                    }
            
            # 2. Check for dedicated preferences table (if exists)
            try:
                # Try to query a preferences table if it exists
                prefs_query = text("""
                    SELECT * FROM user_preferences 
                    WHERE user_id = :user_id
                    LIMIT 1
                """)
                
                pref_result = db.execute(prefs_query, {"user_id": user_id}).first()
                if pref_result:
                    # Override with values from preferences table
                    if hasattr(pref_result, 'language'):
                        preferences["general_settings"]["language"] = pref_result.language
                    if hasattr(pref_result, 'timezone'):
                        preferences["general_settings"]["timezone"] = pref_result.timezone
            except Exception:
                # Preferences table might not exist
                pass
            
            # 3. Get consent records
            consent_records = self._get_consent_records(user_id)
            if consent_records:
                preferences["consent_history"] = [
                    {
                        "purpose": record.get('purpose'),
                        "status": record.get('consent_status'),
                        "given_at": record.get('given_at'),
                        "version": record.get('consent_version')
                    }
                    for record in consent_records
                ]
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error collecting user preferences for user {user_id}: {e}")
            return {
                "error": "Failed to collect user preferences",
                "message": str(e)
            }
    
    async def _collect_cached_data(self, user_id: int) -> Dict[str, Any]:
        """Collect user data from Redis cache"""
        
        cached_data = {
            "transcription_cache": [],
            "session_data": {},
            "preferences_cache": {}
        }
        
        try:
            # Collect user-specific cache keys
            pattern = f"user:{user_id}:*"
            keys = []
            
            # Use SCAN to find keys (more efficient than KEYS for large datasets)
            async for key in redis_cache.client.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                keys.append(key_str)
            
            # Get cached values (anonymize sensitive data)
            for key in keys:
                try:
                    value = await redis_cache.get(key)
                    if value:
                        # Anonymize or exclude sensitive cached data
                        if "session" in key:
                            cached_data["session_data"][key] = "<session_data_anonymized>"
                        elif "transcription" in key:
                            cached_data["transcription_cache"].append({
                                "key": key,
                                "cached_at": "unknown",  # Would need timestamp from Redis
                                "size": len(str(value)) if value else 0
                            })
                        else:
                            cached_data["preferences_cache"][key] = value
                            
                except Exception as e:
                    logger.warning(f"Could not retrieve cached data for key {key}: {e}")
        
        except Exception as e:
            logger.error(f"Error collecting cached data for user {user_id}: {e}")
        
        return cached_data
    
    async def _collect_file_metadata(self, user_id: int) -> List[Dict[str, Any]]:
        """Collect metadata about user's uploaded files"""
        
        file_metadata = []
        
        try:
            # Get database session
            db = next(get_db())
            
            # Query transcripts for file information
            transcripts = db.query(Transcript).filter(Transcript.user_id == user_id).all()
            
            for transcript in transcripts:
                file_info = {
                    "transcript_id": transcript.id,
                    "filename": transcript.title or "Untitled",
                    "upload_date": transcript.created_at.isoformat() if transcript.created_at else None,
                    "processing_status": "completed",
                    "retention_until": None
                }
                
                # Extract file metadata from transcript
                if hasattr(transcript, 'file_url') and transcript.file_url:
                    file_info["file_url"] = transcript.file_url
                    # Extract filename from URL if not in title
                    if not transcript.title and '/' in transcript.file_url:
                        file_info["filename"] = transcript.file_url.split('/')[-1]
                
                if hasattr(transcript, 'file_size') and transcript.file_size:
                    file_info["file_size"] = transcript.file_size
                
                # Determine MIME type from metadata or filename
                if hasattr(transcript, 'metadata') and transcript.metadata:
                    metadata = transcript.metadata if isinstance(transcript.metadata, dict) else {}
                    file_info["mime_type"] = metadata.get('mime_type', 'audio/mpeg')
                    file_info["original_format"] = metadata.get('format')
                    file_info["sample_rate"] = metadata.get('sample_rate')
                    file_info["channels"] = metadata.get('channels')
                else:
                    # Guess MIME type from extension
                    filename = file_info["filename"].lower()
                    if filename.endswith('.mp3'):
                        file_info["mime_type"] = "audio/mpeg"
                    elif filename.endswith('.wav'):
                        file_info["mime_type"] = "audio/wav"
                    elif filename.endswith('.m4a'):
                        file_info["mime_type"] = "audio/mp4"
                    elif filename.endswith('.mp4'):
                        file_info["mime_type"] = "video/mp4"
                    elif filename.endswith('.webm'):
                        file_info["mime_type"] = "video/webm"
                    else:
                        file_info["mime_type"] = "application/octet-stream"
                
                # Calculate retention date based on data category
                if transcript.created_at:
                    # Content files retained for 7 years by default
                    retention_days = self.retention_periods.get(DataCategory.CONTENT, 2555)
                    retention_date = transcript.created_at + timedelta(days=retention_days)
                    file_info["retention_until"] = retention_date.isoformat()
                
                file_metadata.append(file_info)
            
            # Also check for files in storage service
            try:
                from services.storage_service import StorageService
                storage = StorageService()
                
                # List user files from storage
                user_files = await storage.list_files(prefix=f"user_{user_id}/")
                
                for file_path in user_files:
                    # Check if file is already in transcript metadata
                    if not any(f.get('file_url', '').endswith(file_path) for f in file_metadata):
                        file_stat = await storage.get_file_info(file_path)
                        if file_stat:
                            file_metadata.append({
                                "filename": file_path.split('/')[-1],
                                "file_path": file_path,
                                "file_size": file_stat.get('size', 0),
                                "upload_date": file_stat.get('last_modified', datetime.utcnow()).isoformat(),
                                "mime_type": file_stat.get('content_type', 'application/octet-stream'),
                                "processing_status": "stored",
                                "retention_until": (
                                    datetime.utcnow() + timedelta(days=self.retention_periods.get(DataCategory.CONTENT, 2555))
                                ).isoformat()
                            })
            except Exception as e:
                logger.warning(f"Could not retrieve files from storage service: {e}")
            
        except Exception as e:
            logger.error(f"Error collecting file metadata for user {user_id}: {e}")
            # Return at least the metadata we could collect
            pass
        
        finally:
            if 'db' in locals():
                db.close()
        
        return file_metadata
    
    async def _create_export_file(
        self, 
        user_data: Dict[str, Any], 
        user_id: int, 
        request_id: str,
        format_type: str
    ) -> Path:
        """Create export file in requested format"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"gdpr_export_{user_id}_{request_id}_{timestamp}"
        
        if format_type == "json":
            export_file = self.export_storage_path / f"{filename}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False, default=str)
                
        elif format_type == "csv":
            export_file = self.export_storage_path / f"{filename}.zip"
            await self._create_csv_export(user_data, export_file)
            
        elif format_type == "xml":
            export_file = self.export_storage_path / f"{filename}.xml"
            await self._create_xml_export(user_data, export_file)
            
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        return export_file
    
    async def _create_csv_export(self, user_data: Dict[str, Any], export_file: Path):
        """Create CSV export with multiple files in ZIP"""
        
        import csv
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Export info
            with open(temp_path / "export_info.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Field", "Value"])
                for key, value in user_data.get("export_info", {}).items():
                    writer.writerow([key, value])
            
            # Account data
            if "account" in user_data:
                with open(temp_path / "account.csv", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Field", "Value"])
                    for key, value in user_data["account"].items():
                        writer.writerow([key, value])
            
            # Transcripts
            if "transcripts" in user_data:
                with open(temp_path / "transcripts.csv", 'w', newline='', encoding='utf-8') as f:
                    if user_data["transcripts"]:
                        writer = csv.DictWriter(f, fieldnames=user_data["transcripts"][0].keys())
                        writer.writeheader()
                        writer.writerows(user_data["transcripts"])
            
            # Create ZIP file
            with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.iterdir():
                    zipf.write(file_path, file_path.name)
    
    async def _create_xml_export(self, user_data: Dict[str, Any], export_file: Path):
        """Create XML export"""
        
        import xml.etree.ElementTree as ET
        
        def dict_to_xml(data, parent=None, root_name="gdpr_export"):
            if parent is None:
                parent = ET.Element(root_name)
            
            for key, value in data.items():
                if isinstance(value, dict):
                    child = ET.SubElement(parent, key)
                    dict_to_xml(value, child)
                elif isinstance(value, list):
                    child = ET.SubElement(parent, key)
                    for i, item in enumerate(value):
                        item_elem = ET.SubElement(child, f"item_{i}")
                        if isinstance(item, dict):
                            dict_to_xml(item, item_elem)
                        else:
                            item_elem.text = str(item)
                else:
                    child = ET.SubElement(parent, key)
                    child.text = str(value) if value is not None else ""
            
            return parent
        
        root = dict_to_xml(user_data)
        tree = ET.ElementTree(root)
        tree.write(export_file, encoding='utf-8', xml_declaration=True)
    
    def record_consent(
        self,
        user_id: int,
        purpose: str,
        consent_text: str,
        consent_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConsentRecord:
        """Record user consent (GDPR Article 7)"""
        
        consent_id = str(uuid.uuid4())
        
        consent_record = ConsentRecord(
            id=consent_id,
            user_id=user_id,
            purpose=purpose,
            consent_status=ConsentStatus.GIVEN,
            consent_text=consent_text,
            consent_version=consent_version,
            given_at=datetime.utcnow(),
            withdrawn_at=None,
            expires_at=None,  # Could set expiration based on purpose
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if user_id not in self.consent_records:
            self.consent_records[user_id] = []
        
        self.consent_records[user_id].append(consent_record)
        
        # Log consent
        audit_service.log_event(
            event_type=AuditEventType.CONSENT_GIVEN,
            action=f"Consent recorded: {purpose}",
            user_id=user_id,
            ip_address=ip_address,
            details={
                "consent_id": consent_id,
                "purpose": purpose,
                "version": consent_version
            }
        )
        
        return consent_record
    
    def withdraw_consent(self, user_id: int, consent_id: str) -> bool:
        """Withdraw user consent (GDPR Article 7)"""
        
        if user_id not in self.consent_records:
            return False
        
        for consent in self.consent_records[user_id]:
            if consent.id == consent_id and consent.consent_status == ConsentStatus.GIVEN:
                consent.consent_status = ConsentStatus.WITHDRAWN
                consent.withdrawn_at = datetime.utcnow()
                
                # Log consent withdrawal
                audit_service.log_event(
                    event_type=AuditEventType.CONSENT_WITHDRAWN,
                    action=f"Consent withdrawn: {consent.purpose}",
                    user_id=user_id,
                    details={
                        "consent_id": consent_id,
                        "purpose": consent.purpose
                    }
                )
                
                return True
        
        return False
    
    def _get_consent_records(self, user_id: int) -> List[Dict[str, Any]]:
        """Get consent records for user"""
        
        if user_id not in self.consent_records:
            return []
        
        return [asdict(consent) for consent in self.consent_records[user_id]]
    
    def record_processing_activity(
        self,
        data_subject_id: int,
        purpose: str,
        lawful_basis: DataProcessingLawfulBasis,
        data_categories: List[DataCategory],
        recipients: List[str] = None,
        retention_period: int = None,
        cross_border_transfer: bool = False,
        automated_decision_making: bool = False
    ) -> DataProcessingRecord:
        """Record data processing activity (GDPR Article 30)"""
        
        record_id = str(uuid.uuid4())
        
        processing_record = DataProcessingRecord(
            id=record_id,
            data_subject_id=data_subject_id,
            processing_purpose=purpose,
            lawful_basis=lawful_basis,
            data_categories=data_categories,
            recipients=recipients or [],
            retention_period=retention_period,
            cross_border_transfer=cross_border_transfer,
            automated_decision_making=automated_decision_making,
            created_at=datetime.utcnow()
        )
        
        self.processing_records[record_id] = processing_record
        
        # Log processing record
        audit_service.log_event(
            event_type=AuditEventType.DATA_PROCESSING_RECORDED,
            action=f"Processing activity recorded: {purpose}",
            user_id=data_subject_id,
            details={
                "record_id": record_id,
                "purpose": purpose,
                "lawful_basis": lawful_basis.value,
                "data_categories": [cat.value for cat in data_categories]
            }
        )
        
        return processing_record
    
    def _get_processing_records(self, user_id: int) -> List[Dict[str, Any]]:
        """Get processing records for user"""
        
        records = []
        for record in self.processing_records.values():
            if record.data_subject_id == user_id:
                record_dict = asdict(record)
                # Convert enums to strings for JSON serialization
                record_dict['lawful_basis'] = record.lawful_basis.value
                record_dict['data_categories'] = [cat.value for cat in record.data_categories]
                records.append(record_dict)
        
        return records
    
    def _generate_verification_token(self) -> str:
        """Generate verification token for secure access"""
        return hashlib.sha256(f"{uuid.uuid4()}{datetime.utcnow()}".encode()).hexdigest()
    
    async def delete_user_data(self, user_id: int, verification_token: str) -> Dict[str, Any]:
        """
        Delete all user data (Right to Erasure - GDPR Article 17)
        
        Args:
            user_id: User ID to delete data for
            verification_token: Security token to verify the request
        
        Returns:
            Dictionary with deletion results
        """
        
        deletion_results = {
            "user_id": user_id,
            "initiated_at": datetime.utcnow().isoformat(),
            "verification_token": verification_token,
            "deleted_data": {},
            "errors": []
        }
        
        db = next(get_db())
        
        try:
            # Log deletion request
            audit_service.log_event(
                event_type=AuditEventType.DATA_DELETION_REQUEST,
                action="User data deletion requested",
                user_id=user_id,
                details={"verification_token": verification_token[:16] + "..."}
            )
            
            # 1. Delete transcripts
            deleted_transcripts = db.query(Transcript).filter(
                Transcript.user_id == user_id
            ).delete()
            deletion_results["deleted_data"]["transcripts"] = deleted_transcripts
            
            # 2. Delete user account
            deleted_user = db.query(User).filter(User.id == user_id).delete()
            deletion_results["deleted_data"]["user_account"] = deleted_user
            
            # 3. Clear cached data
            if redis_cache.is_connected():
                try:
                    pattern = f"user:{user_id}:*"
                    deleted_cache_keys = 0
                    async for key in redis_cache.client.scan_iter(match=pattern):
                        await redis_cache.client.delete(key)
                        deleted_cache_keys += 1
                    deletion_results["deleted_data"]["cache_keys"] = deleted_cache_keys
                except Exception as e:
                    deletion_results["errors"].append(f"Cache deletion error: {str(e)}")
            
            # 4. Remove processing records
            deleted_processing = len([
                self.processing_records.pop(record_id) 
                for record_id, record in list(self.processing_records.items())
                if record.data_subject_id == user_id
            ])
            deletion_results["deleted_data"]["processing_records"] = deleted_processing
            
            # 5. Remove consent records
            deleted_consents = 0
            if user_id in self.consent_records:
                deleted_consents = len(self.consent_records[user_id])
                del self.consent_records[user_id]
            deletion_results["deleted_data"]["consent_records"] = deleted_consents
            
            # 6. Delete export files
            deleted_exports = await self._delete_user_export_files(user_id)
            deletion_results["deleted_data"]["export_files"] = deleted_exports
            
            db.commit()
            
            deletion_results["status"] = "completed"
            deletion_results["completed_at"] = datetime.utcnow().isoformat()
            
            # Log successful deletion
            audit_service.log_event(
                event_type=AuditEventType.DATA_DELETION_COMPLETED,
                action="User data deletion completed",
                user_id=user_id,
                details=deletion_results["deleted_data"]
            )
            
        except Exception as e:
            db.rollback()
            deletion_results["status"] = "failed"
            deletion_results["error"] = str(e)
            deletion_results["errors"].append(str(e))
            
            # Log deletion failure
            audit_service.log_event(
                event_type=AuditEventType.DATA_DELETION_FAILED,
                action="User data deletion failed",
                user_id=user_id,
                error_message=str(e)
            )
            
        finally:
            db.close()
        
        return deletion_results
    
    async def _delete_user_export_files(self, user_id: int) -> int:
        """Delete user's export files"""
        
        deleted_count = 0
        
        # Find and delete export files for this user
        for export_request in list(self.export_requests.values()):
            if export_request.user_id == user_id:
                if export_request.export_file_path and os.path.exists(export_request.export_file_path):
                    try:
                        os.remove(export_request.export_file_path)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Could not delete export file {export_request.export_file_path}: {e}")
                
                # Remove from tracking
                del self.export_requests[export_request.id]
        
        return deleted_count
    
    def get_export_status(self, request_id: str) -> Optional[DataExportRequest]:
        """Get export request status"""
        return self.export_requests.get(request_id)
    
    def list_user_exports(self, user_id: int) -> List[DataExportRequest]:
        """List all export requests for a user"""
        return [
            export for export in self.export_requests.values()
            if export.user_id == user_id
        ]
    
    def get_privacy_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive privacy dashboard data for user"""
        
        return {
            "user_id": user_id,
            "data_categories": [cat.value for cat in DataCategory],
            "consent_records": self._get_consent_records(user_id),
            "processing_records": self._get_processing_records(user_id),
            "export_requests": [
                asdict(export) for export in self.list_user_exports(user_id)
            ],
            "retention_periods": {
                cat.value: days for cat, days in self.retention_periods.items()
            },
            "rights": {
                "data_portability": "Article 20",
                "erasure": "Article 17", 
                "rectification": "Article 16",
                "access": "Article 15",
                "restriction": "Article 18",
                "objection": "Article 21"
            }
        }


# Global GDPR service instance
gdpr_service = GDPRComplianceService()