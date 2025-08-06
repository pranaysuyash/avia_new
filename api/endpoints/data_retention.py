"""
Data Retention API Endpoints
Manage data retention policies and cleanup operations
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from api.dependencies import get_current_user, require_roles
from api.middleware.quota_enforcement import require_quota
from api.middleware.audit_logging import audit_action
from services.data_retention_service import data_retention_service
from database.connection import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-retention")

# Pydantic models
class RetentionPolicyCreate(BaseModel):
    data_type: str = Field(..., description="Type of data (transcripts, audit_logs, etc.)")
    retention_days: int = Field(..., ge=30, le=2555, description="Retention period in days")
    auto_delete: bool = Field(False, description="Enable automatic deletion")
    archive_before_delete: bool = Field(True, description="Archive data before deletion")
    metadata: Optional[Dict[str, Any]] = None

class RetentionPolicyResponse(BaseModel):
    id: str
    data_type: str
    retention_days: int
    auto_delete: bool
    archive_before_delete: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    metadata: Dict[str, Any]

class RetentionJobResponse(BaseModel):
    id: str
    policy_id: str
    job_type: str
    status: str
    records_processed: int
    records_deleted: int
    records_archived: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

class CleanupSummary(BaseModel):
    total_policies: int
    successful_jobs: int
    failed_jobs: int
    results: List[Dict[str, Any]]
    executed_at: str

@router.get("/policies", response_model=List[RetentionPolicyResponse])
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('READ', 'retention_policies')
async def get_retention_policies(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active retention policies"""
    try:
        db_policies = db.query(data_retention_service._get_db().query(
            data_retention_service.RetentionPolicy
        ).filter(
            data_retention_service.RetentionPolicy.is_active == True
        )).all()
        
        return [
            RetentionPolicyResponse(
                id=policy.id,
                data_type=policy.data_type,
                retention_days=policy.retention_days,
                auto_delete=policy.auto_delete,
                archive_before_delete=policy.archive_before_delete,
                created_by=policy.created_by,
                created_at=policy.created_at,
                updated_at=policy.updated_at,
                is_active=policy.is_active,
                metadata=policy.metadata or {}
            )
            for policy in db_policies
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving retention policies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve retention policies: {str(e)}"
        )

@router.post("/policies", response_model=RetentionPolicyResponse)
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('CREATE', 'retention_policy', include_request_data=True)
async def create_retention_policy(
    policy: RetentionPolicyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new retention policy"""
    try:
        created_policy = data_retention_service.create_policy(
            data_type=policy.data_type,
            retention_days=policy.retention_days,
            created_by=current_user['id'],
            auto_delete=policy.auto_delete,
            archive_before_delete=policy.archive_before_delete,
            metadata=policy.metadata
        )
        
        return RetentionPolicyResponse(
            id=created_policy.id,
            data_type=created_policy.data_type,
            retention_days=created_policy.retention_days,
            auto_delete=created_policy.auto_delete,
            archive_before_delete=created_policy.archive_before_delete,
            created_by=created_policy.created_by,
            created_at=created_policy.created_at,
            updated_at=created_policy.updated_at,
            is_active=created_policy.is_active,
            metadata=created_policy.metadata or {}
        )
        
    except Exception as e:
        logger.error(f"Error creating retention policy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create retention policy: {str(e)}"
        )

@router.put("/policies/{policy_id}")
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('UPDATE', 'retention_policy', include_request_data=True)
async def update_retention_policy(
    policy_id: str,
    retention_days: Optional[int] = Query(None, ge=30, le=2555),
    auto_delete: Optional[bool] = None,
    archive_before_delete: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing retention policy"""
    try:
        success = data_retention_service.update_policy(
            policy_id=policy_id,
            retention_days=retention_days,
            auto_delete=auto_delete,
            archive_before_delete=archive_before_delete
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Retention policy not found")
        
        return {"message": "Retention policy updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retention policy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update retention policy: {str(e)}"
        )

@router.get("/policies/{data_type}/expired")
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('READ', 'expired_data')
async def get_expired_data(
    data_type: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get data that has exceeded retention period for a specific data type"""
    try:
        expired_data = data_retention_service.get_expired_data(data_type, limit)
        
        return {
            'data_type': data_type,
            'expired_count': len(expired_data),
            'limit': limit,
            'expired_records': expired_data
        }
        
    except Exception as e:
        logger.error(f"Error getting expired data for {data_type}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get expired data: {str(e)}"
        )

@router.post("/cleanup/manual")
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('CREATE', 'manual_cleanup', include_request_data=True)
async def manual_cleanup(
    data_type: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger cleanup for a specific data type"""
    try:
        # Get policy for data type
        policy = data_retention_service.get_policy(data_type)
        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"No retention policy found for data type: {data_type}"
            )
        
        # Create cleanup job
        job = data_retention_service.create_retention_job(
            policy_id=policy.id,
            job_type='manual_cleanup',
            metadata={
                'triggered_by': current_user['id'],
                'data_type': data_type
            }
        )
        
        # Execute cleanup in background
        background_tasks.add_task(
            data_retention_service.execute_cleanup_job,
            job.id
        )
        
        return {
            'message': f'Manual cleanup initiated for {data_type}',
            'job_id': job.id,
            'policy_id': policy.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating manual cleanup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate cleanup: {str(e)}"
        )

@router.post("/cleanup/automated", response_model=CleanupSummary)
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('CREATE', 'automated_cleanup')
async def run_automated_cleanup(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Run automated cleanup for all policies with auto_delete enabled"""
    try:
        # Run cleanup in background and return immediate response
        background_tasks.add_task(data_retention_service.run_automated_cleanup)
        
        return {
            'message': 'Automated cleanup initiated',
            'initiated_by': current_user['id'],
            'initiated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error initiating automated cleanup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate automated cleanup: {str(e)}"
        )

@router.get("/jobs", response_model=List[RetentionJobResponse])
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('READ', 'retention_jobs')
async def get_retention_jobs(
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|failed)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get retention job history"""
    try:
        from services.data_retention_service import RetentionJob
        
        query = db.query(RetentionJob)
        
        if status:
            query = query.filter(RetentionJob.status == status)
        
        jobs = query.order_by(RetentionJob.created_at.desc()).limit(limit).all()
        
        return [
            RetentionJobResponse(
                id=job.id,
                policy_id=job.policy_id,
                job_type=job.job_type,
                status=job.status,
                records_processed=job.records_processed,
                records_deleted=job.records_deleted,
                records_archived=job.records_archived,
                error_message=job.error_message,
                started_at=job.started_at,
                completed_at=job.completed_at,
                created_at=job.created_at
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving retention jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve retention jobs: {str(e)}"
        )

@router.get("/status")
@require_roles(['admin'])
@require_quota('api_calls', 1, 'audit_logs')
@audit_action('READ', 'retention_status')
async def get_retention_status(
    current_user: dict = Depends(get_current_user)
):
    """Get overall retention system status and statistics"""
    try:
        status = data_retention_service.get_retention_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting retention status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get retention status: {str(e)}"
        )

@router.post("/initialize")
@require_roles(['admin'])
@audit_action('ADMIN_ACTION', 'retention_initialization')
async def initialize_default_policies(
    current_user: dict = Depends(get_current_user)
):
    """Initialize default retention policies"""
    try:
        success = data_retention_service.initialize_default_policies(
            created_by=current_user['id']
        )
        
        if success:
            return {
                'message': 'Default retention policies initialized successfully',
                'policies_created': len(data_retention_service.DEFAULT_RETENTION_POLICIES)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize default policies"
            )
        
    except Exception as e:
        logger.error(f"Error initializing default policies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize policies: {str(e)}"
        )

@router.get("/data-types")
async def get_supported_data_types(
    current_user: dict = Depends(get_current_user)
):
    """Get list of supported data types and their default retention periods"""
    return {
        'supported_data_types': list(data_retention_service.DEFAULT_RETENTION_POLICIES.keys()),
        'default_policies': data_retention_service.DEFAULT_RETENTION_POLICIES,
        'descriptions': {
            'transcripts': 'User transcription data and associated files',
            'audit_logs': 'System audit logs and security events',
            'user_data': 'User account data and preferences',
            'session_logs': 'User session and authentication logs',
            'temp_files': 'Temporary files and uploads',
            'api_logs': 'API access logs and request history',
            'backups': 'System backup files',
            'exports': 'Data export files and archives',
            'notifications': 'User notifications and messages',
            'webhooks': 'Webhook delivery logs and responses'
        }
    }