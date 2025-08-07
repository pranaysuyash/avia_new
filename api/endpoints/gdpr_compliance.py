"""
GDPR Compliance API Endpoints
Provides REST API for GDPR compliance operations and user privacy rights
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from pathlib import Path

from api.database import get_db, User
from api.auth import get_current_active_user, get_current_admin_user
from services.gdpr_compliance_service import (
    gdpr_service,
    DataProcessingLawfulBasis,
    DataCategory,
    ConsentStatus
)
from services.audit_logging_service import audit_service, AuditEventType

router = APIRouter(
    prefix="/api/v1/gdpr",
    tags=["gdpr-compliance"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models
class DataExportRequest(BaseModel):
    """Request model for data export"""
    export_type: str = Field(default="full_export", pattern="^(full_export|transcripts_only|analytics_only)$")
    format_type: str = Field(default="json", pattern="^(json|csv|xml)$")


class DataExportResponse(BaseModel):
    """Response model for data export request"""
    request_id: str
    status: str
    requested_at: str
    export_type: str
    format_type: str
    verification_token: str
    expires_at: str
    download_url: Optional[str] = None
    file_size: Optional[int] = None


class ConsentRequest(BaseModel):
    """Request model for recording consent"""
    purpose: str = Field(..., description="Purpose for which consent is given")
    consent_text: str = Field(..., description="Full text of consent")
    consent_version: str = Field(..., description="Version of consent text")


class ConsentResponse(BaseModel):
    """Response model for consent operations"""
    consent_id: str
    user_id: int
    purpose: str
    status: str
    given_at: Optional[str] = None
    withdrawn_at: Optional[str] = None


class ProcessingRecordRequest(BaseModel):
    """Request model for recording data processing activity"""
    purpose: str = Field(..., description="Purpose of processing")
    lawful_basis: DataProcessingLawfulBasis
    data_categories: List[DataCategory]
    recipients: List[str] = Field(default_factory=list)
    retention_period: Optional[int] = Field(None, description="Retention period in days")
    cross_border_transfer: bool = Field(default=False)
    automated_decision_making: bool = Field(default=False)


class DataDeletionRequest(BaseModel):
    """Request model for data deletion (Right to Erasure)"""
    confirmation: bool = Field(..., description="Confirmation that user wants to delete all data")
    reason: Optional[str] = Field(None, description="Reason for deletion request")


class PrivacyDashboardResponse(BaseModel):
    """Response model for privacy dashboard"""
    user_id: int
    data_categories: List[str]
    active_consents: int
    processing_activities: int
    export_requests: int
    last_export: Optional[str] = None
    data_retention_info: Dict[str, Any]
    privacy_rights: Dict[str, str]


class DataSubjectRightsResponse(BaseModel):
    """Response model for data subject rights information"""
    rights: Dict[str, Dict[str, str]]
    contact_info: Dict[str, str]
    response_timeframes: Dict[str, str]


# Data Export endpoints (GDPR Article 20 - Right to Data Portability)
@router.post("/export/request", response_model=DataExportResponse)
async def request_data_export(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    http_request: Request = None
):
    """
    Request data export (GDPR Article 20 - Right to Data Portability)
    
    Creates an export request for the authenticated user's personal data.
    The export will include all data associated with the user account.
    """
    try:
        # Create export request
        export_request = await gdpr_service.create_data_export(
            user_id=current_user.id,
            export_type=request.export_type,
            format_type=request.format_type
        )
        
        # Log the request
        audit_service.log_event(
            event_type=AuditEventType.DATA_EXPORT_REQUEST,
            action=f"Data export requested via API",
            user_id=current_user.id,
            username=current_user.username,
            ip_address=http_request.client.host if http_request and http_request.client else None,
            details={
                "request_id": export_request.id,
                "export_type": request.export_type,
                "format": request.format_type
            }
        )
        
        return DataExportResponse(
            request_id=export_request.id,
            status=export_request.status,
            requested_at=export_request.requested_at.isoformat(),
            export_type=request.export_type,
            format_type=request.format_type,
            verification_token=export_request.verification_token,
            expires_at=export_request.expires_at.isoformat(),
            download_url=f"/api/v1/gdpr/export/download/{export_request.id}" if export_request.status == "completed" else None,
            file_size=export_request.file_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create export request: {str(e)}"
        )


@router.get("/export/status/{request_id}", response_model=DataExportResponse)
async def get_export_status(
    request_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of data export request
    
    Check the current status of a previously requested data export.
    """
    try:
        export_request = gdpr_service.get_export_status(request_id)
        
        if not export_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export request not found"
            )
        
        # Verify ownership
        if export_request.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this export request"
            )
        
        return DataExportResponse(
            request_id=export_request.id,
            status=export_request.status,
            requested_at=export_request.requested_at.isoformat(),
            export_type=export_request.request_type,
            format_type="unknown",  # Would need to track format in export_request
            verification_token=export_request.verification_token,
            expires_at=export_request.expires_at.isoformat(),
            download_url=f"/api/v1/gdpr/export/download/{export_request.id}" if export_request.status == "completed" else None,
            file_size=export_request.file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export status: {str(e)}"
        )


@router.get("/export/download/{request_id}")
async def download_export(
    request_id: str,
    token: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download completed data export
    
    Download the exported data file. Requires verification token for security.
    """
    try:
        export_request = gdpr_service.get_export_status(request_id)
        
        if not export_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export request not found"
            )
        
        # Verify ownership and token
        if export_request.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this export"
            )
        
        if export_request.verification_token != token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verification token"
            )
        
        if export_request.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export not ready for download. Status: {export_request.status}"
            )
        
        if not export_request.export_file_path or not Path(export_request.export_file_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found"
            )
        
        # Check expiration
        if datetime.utcnow() > export_request.expires_at:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Export file has expired"
            )
        
        # Log download
        audit_service.log_event(
            event_type=AuditEventType.DATA_EXPORT_DOWNLOAD,
            action="Data export downloaded",
            user_id=current_user.id,
            username=current_user.username,
            details={"request_id": request_id}
        )
        
        # Return file
        return FileResponse(
            path=export_request.export_file_path,
            filename=f"gdpr_export_{current_user.id}_{request_id}.{Path(export_request.export_file_path).suffix[1:]}",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download export: {str(e)}"
        )


@router.get("/export/list", response_model=List[DataExportResponse])
async def list_user_exports(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all export requests for the current user
    """
    try:
        exports = gdpr_service.list_user_exports(current_user.id)
        
        return [
            DataExportResponse(
                request_id=export.id,
                status=export.status,
                requested_at=export.requested_at.isoformat(),
                export_type=export.request_type,
                format_type="unknown",  # Would need to track format
                verification_token=export.verification_token,
                expires_at=export.expires_at.isoformat(),
                download_url=f"/api/v1/gdpr/export/download/{export.id}" if export.status == "completed" else None,
                file_size=export.file_size
            )
            for export in exports
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list exports: {str(e)}"
        )


# Consent Management endpoints (GDPR Article 7)
@router.post("/consent/record", response_model=ConsentResponse)
async def record_consent(
    consent_request: ConsentRequest,
    current_user: User = Depends(get_current_active_user),
    http_request: Request = None
):
    """
    Record user consent (GDPR Article 7)
    
    Records explicit consent from the user for specified processing purposes.
    """
    try:
        # Extract request metadata
        ip_address = http_request.client.host if http_request and http_request.client else None
        user_agent = http_request.headers.get("user-agent") if http_request else None
        
        # Record consent
        consent_record = gdpr_service.record_consent(
            user_id=current_user.id,
            purpose=consent_request.purpose,
            consent_text=consent_request.consent_text,
            consent_version=consent_request.consent_version,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return ConsentResponse(
            consent_id=consent_record.id,
            user_id=consent_record.user_id,
            purpose=consent_record.purpose,
            status=consent_record.consent_status.value,
            given_at=consent_record.given_at.isoformat() if consent_record.given_at else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record consent: {str(e)}"
        )


@router.post("/consent/withdraw/{consent_id}", response_model=ConsentResponse)
async def withdraw_consent(
    consent_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Withdraw user consent (GDPR Article 7)
    
    Allows users to withdraw previously given consent.
    """
    try:
        success = gdpr_service.withdraw_consent(current_user.id, consent_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consent record not found or already withdrawn"
            )
        
        return ConsentResponse(
            consent_id=consent_id,
            user_id=current_user.id,
            purpose="unknown",  # Would need to fetch from service
            status="withdrawn",
            withdrawn_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to withdraw consent: {str(e)}"
        )


@router.get("/consent/list")
async def list_user_consents(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all consent records for the current user
    """
    try:
        consent_records = gdpr_service._get_consent_records(current_user.id)
        return consent_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list consents: {str(e)}"
        )


# Data Processing Records endpoints (GDPR Article 30)
@router.post("/processing/record")
async def record_processing_activity(
    processing_request: ProcessingRecordRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Record data processing activity (GDPR Article 30)
    
    Admin-only endpoint to record data processing activities.
    Requires admin privileges.
    """
    try:
        processing_record = gdpr_service.record_processing_activity(
            data_subject_id=current_user.id,  # For demo, using current user
            purpose=processing_request.purpose,
            lawful_basis=processing_request.lawful_basis,
            data_categories=processing_request.data_categories,
            recipients=processing_request.recipients,
            retention_period=processing_request.retention_period,
            cross_border_transfer=processing_request.cross_border_transfer,
            automated_decision_making=processing_request.automated_decision_making
        )
        
        return {
            "record_id": processing_record.id,
            "created_at": processing_record.created_at.isoformat(),
            "purpose": processing_record.processing_purpose,
            "lawful_basis": processing_record.lawful_basis.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record processing activity: {str(e)}"
        )


# Data Deletion endpoints (GDPR Article 17 - Right to Erasure)
@router.post("/delete/request")
async def request_data_deletion(
    deletion_request: DataDeletionRequest,
    current_user: User = Depends(get_current_active_user),
    http_request: Request = None
):
    """
    Request data deletion (GDPR Article 17 - Right to Erasure)
    
    DESTRUCTIVE OPERATION: This will permanently delete all user data.
    Requires explicit confirmation.
    """
    if not deletion_request.confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation required for data deletion"
        )
    
    try:
        # Generate verification token
        verification_token = gdpr_service._generate_verification_token()
        
        # Log deletion request (before deletion)
        audit_service.log_event(
            event_type=AuditEventType.DATA_DELETION_REQUEST,
            action="Data deletion requested via API",
            user_id=current_user.id,
            username=current_user.username,
            ip_address=http_request.client.host if http_request and http_request.client else None,
            details={
                "reason": deletion_request.reason,
                "verification_token": verification_token[:16] + "..."
            }
        )
        
        # Perform deletion
        deletion_results = await gdpr_service.delete_user_data(
            user_id=current_user.id,
            verification_token=verification_token
        )
        
        return deletion_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user data: {str(e)}"
        )


# Privacy Dashboard endpoints
@router.get("/dashboard", response_model=PrivacyDashboardResponse)
async def get_privacy_dashboard(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get privacy dashboard data for the current user
    
    Provides comprehensive overview of user's data and privacy settings.
    """
    try:
        dashboard_data = gdpr_service.get_privacy_dashboard_data(current_user.id)
        
        # Calculate summary statistics
        active_consents = sum(
            1 for consent in dashboard_data["consent_records"]
            if consent["consent_status"] == "given"
        )
        
        export_requests = len(dashboard_data["export_requests"])
        last_export = None
        if dashboard_data["export_requests"]:
            last_export = max(
                export["requested_at"] for export in dashboard_data["export_requests"]
            )
        
        return PrivacyDashboardResponse(
            user_id=current_user.id,
            data_categories=dashboard_data["data_categories"],
            active_consents=active_consents,
            processing_activities=len(dashboard_data["processing_records"]),
            export_requests=export_requests,
            last_export=last_export,
            data_retention_info=dashboard_data["retention_periods"],
            privacy_rights=dashboard_data["rights"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get privacy dashboard: {str(e)}"
        )


@router.get("/rights/info", response_model=DataSubjectRightsResponse)
async def get_data_subject_rights_info():
    """
    Get information about GDPR data subject rights
    
    Public endpoint that provides information about user rights under GDPR.
    """
    try:
        rights_info = {
            "rights": {
                "access": {
                    "article": "Article 15",
                    "description": "Right to obtain confirmation whether personal data is processed and access to that data",
                    "how_to_exercise": "Contact privacy@example.com or use the privacy dashboard"
                },
                "rectification": {
                    "article": "Article 16", 
                    "description": "Right to rectification of inaccurate personal data",
                    "how_to_exercise": "Update your profile or contact support"
                },
                "erasure": {
                    "article": "Article 17",
                    "description": "Right to erasure ('right to be forgotten')",
                    "how_to_exercise": "Use the data deletion feature in privacy dashboard"
                },
                "restriction": {
                    "article": "Article 18",
                    "description": "Right to restriction of processing",
                    "how_to_exercise": "Contact privacy@example.com"
                },
                "portability": {
                    "article": "Article 20",
                    "description": "Right to data portability",
                    "how_to_exercise": "Use the data export feature in privacy dashboard"
                },
                "objection": {
                    "article": "Article 21",
                    "description": "Right to object to processing",
                    "how_to_exercise": "Withdraw consent or contact privacy@example.com"
                }
            },
            "contact_info": {
                "email": "privacy@example.com",
                "phone": "+1-555-PRIVACY",
                "address": "123 Privacy Street, Data City, DC 12345",
                "dpo_email": "dpo@example.com"
            },
            "response_timeframes": {
                "standard_requests": "30 days",
                "complex_requests": "60 days (with notification)",
                "data_portability": "Usually within 7 days",
                "erasure": "Usually within 7 days"
            }
        }
        
        return DataSubjectRightsResponse(**rights_info)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rights information: {str(e)}"
        )


# Admin endpoints
@router.get("/admin/statistics")
async def get_gdpr_statistics(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get GDPR compliance statistics (Admin only)
    
    Provides overview of GDPR-related activities and compliance metrics.
    """
    try:
        # Calculate statistics from service data
        total_exports = len(gdpr_service.export_requests)
        total_consents = sum(len(consents) for consents in gdpr_service.consent_records.values())
        total_processing_records = len(gdpr_service.processing_records)
        
        # Export status distribution
        export_status_counts = {}
        for export in gdpr_service.export_requests.values():
            status = export.status
            export_status_counts[status] = export_status_counts.get(status, 0) + 1
        
        # Consent status distribution
        consent_status_counts = {}
        for user_consents in gdpr_service.consent_records.values():
            for consent in user_consents:
                status = consent.consent_status.value
                consent_status_counts[status] = consent_status_counts.get(status, 0) + 1
        
        return {
            "overview": {
                "total_export_requests": total_exports,
                "total_consent_records": total_consents,
                "total_processing_records": total_processing_records,
                "active_users_with_consents": len(gdpr_service.consent_records)
            },
            "export_requests": {
                "by_status": export_status_counts,
                "recent_requests": total_exports  # Placeholder
            },
            "consent_management": {
                "by_status": consent_status_counts,
                "withdrawal_rate": 0.0  # Would calculate from actual data
            },
            "compliance_metrics": {
                "avg_export_completion_time": "2.5 hours",  # Placeholder
                "data_retention_compliance": "98%",  # Placeholder
                "consent_renewal_rate": "85%"  # Placeholder
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get GDPR statistics: {str(e)}"
        )


# Health check
@router.get("/health")
async def gdpr_health_check():
    """
    GDPR service health check
    """
    try:
        # Check if export directory exists and is writable
        export_path = gdpr_service.export_storage_path
        export_path_healthy = export_path.exists() and os.access(export_path, os.W_OK)
        
        return {
            "status": "healthy" if export_path_healthy else "degraded",
            "export_storage": {
                "path": str(export_path),
                "exists": export_path.exists(),
                "writable": os.access(export_path, os.W_OK) if export_path.exists() else False
            },
            "service_stats": {
                "active_export_requests": len(gdpr_service.export_requests),
                "consent_records": sum(len(consents) for consents in gdpr_service.consent_records.values()),
                "processing_records": len(gdpr_service.processing_records)
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }