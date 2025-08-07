"""
Backup Management API Endpoints
Provides REST API for backup operations and monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from api.database import get_db, User
from api.auth import get_current_active_user, get_current_admin_user
from services.backup_service import backup_service
from services.automated_backup_scheduler import automated_backup_scheduler
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/backup",
    tags=["backup"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models
class BackupRequest(BaseModel):
    """Request model for backup creation"""
    backup_type: str = Field(default="manual", pattern="^(manual|daily|weekly|monthly|full|incremental)$")
    include_files: bool = Field(default=True, description="Include user files in backup")
    compress: bool = Field(default=True, description="Compress backup archive")
    components: Optional[List[str]] = Field(default=None, description="Specific components to backup")


class BackupResponse(BaseModel):
    """Response model for backup operations"""
    backup_id: str
    status: str
    size: Optional[int] = None
    components: List[str]
    location: Optional[str] = None
    s3_location: Optional[str] = None
    created_at: str
    duration: Optional[float] = None
    error: Optional[str] = None


class RestoreRequest(BaseModel):
    """Request model for backup restoration"""
    backup_id: str = Field(..., description="ID of backup to restore")
    components: Optional[List[str]] = Field(default=None, description="Specific components to restore")
    confirm: bool = Field(default=False, description="Confirmation flag for destructive operation")


class BackupStatusResponse(BaseModel):
    """Response model for backup scheduler status"""
    scheduler_running: bool
    next_daily: Optional[str] = None
    recent_backups: int
    last_backup: Optional[Dict[str, Any]] = None
    success_rate: float
    configuration: Dict[str, Any]


class BackupHistoryResponse(BaseModel):
    """Response model for backup history"""
    backups: List[Dict[str, Any]]
    total_count: int
    success_count: int
    failure_count: int


# Backup creation endpoints
@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new backup
    
    Requires admin privileges. Backup creation runs in the background.
    """
    try:
        logger.info(f"Backup creation requested by user {current_user.id}")
        
        # Log backup request
        audit_service.log_event(
            event_type=AuditEventType.BACKUP_CREATE,
            action=f"Backup creation requested: {request.backup_type}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "backup_type": request.backup_type,
                "include_files": request.include_files,
                "compress": request.compress,
                "components": request.components
            }
        )
        
        # Create backup
        backup_result = await backup_service.create_backup(
            backup_type=request.backup_type,
            include_files=request.include_files,
            compress=request.compress,
            user_id=current_user.id,
            username=current_user.username
        )
        
        return BackupResponse(
            backup_id=backup_result["backup_id"],
            status=backup_result["status"],
            size=backup_result.get("size"),
            components=backup_result.get("components", []),
            location=backup_result.get("location"),
            s3_location=backup_result.get("s3_location"),
            created_at=backup_result.get("created_at", datetime.utcnow().isoformat()),
            duration=backup_result.get("duration"),
            error=backup_result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}"
        )


@router.post("/create-comprehensive", response_model=BackupResponse)
async def create_comprehensive_backup(
    backup_type: str = "manual",
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a comprehensive backup including all system components
    
    This includes database, Redis, user data, system metrics, and cache statistics.
    """
    try:
        logger.info(f"Comprehensive backup requested by user {current_user.id}")
        
        # Create comprehensive backup
        backup_result = await automated_backup_scheduler.create_comprehensive_backup(
            backup_type=backup_type
        )
        
        return BackupResponse(
            backup_id=backup_result["backup_id"],
            status=backup_result["status"],
            size=backup_result.get("total_size"),
            components=list(backup_result.get("components", {}).keys()),
            created_at=backup_result.get("start_time", datetime.utcnow().isoformat()),
            duration=backup_result.get("duration"),
            error=backup_result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Comprehensive backup creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive backup creation failed: {str(e)}"
        )


# Backup listing and status endpoints
@router.get("/list", response_model=List[BackupResponse])
async def list_backups(
    current_user: User = Depends(get_current_admin_user)
):
    """
    List all available backups
    
    Requires admin privileges.
    """
    try:
        backups = backup_service.list_backups()
        
        return [
            BackupResponse(
                backup_id=backup["backup_id"],
                status="completed",
                size=backup.get("size"),
                components=backup.get("components", []),
                location=backup.get("location", "local"),
                s3_location=backup.get("s3_location"),
                created_at=backup["created_at"]
            )
            for backup in backups
        ]
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.get("/status", response_model=BackupStatusResponse)
async def get_backup_status(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get backup scheduler status and recent backup history
    """
    try:
        status_info = automated_backup_scheduler.get_backup_status()
        
        return BackupStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup status: {str(e)}"
        )


@router.get("/history", response_model=BackupHistoryResponse)
async def get_backup_history(
    limit: int = 20,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get backup history with statistics
    """
    try:
        history = automated_backup_scheduler.get_backup_history(limit)
        
        success_count = sum(1 for b in history if b.get("status") == "completed")
        failure_count = len(history) - success_count
        
        return BackupHistoryResponse(
            backups=history,
            total_count=len(history),
            success_count=success_count,
            failure_count=failure_count
        )
        
    except Exception as e:
        logger.error(f"Failed to get backup history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup history: {str(e)}"
        )


# Backup restoration endpoints
@router.post("/restore", response_model=Dict[str, Any])
async def restore_backup(
    request: RestoreRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Restore from backup
    
    WARNING: This is a destructive operation that may overwrite existing data.
    Requires admin privileges and explicit confirmation.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restoration requires explicit confirmation. Set 'confirm' to true."
        )
    
    try:
        logger.warning(f"Backup restoration initiated by user {current_user.id}")
        
        # Log restore request
        audit_service.log_event(
            event_type=AuditEventType.BACKUP_RESTORE,
            action=f"Backup restoration requested: {request.backup_id}",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "backup_id": request.backup_id,
                "components": request.components
            }
        )
        
        # Perform restoration
        restore_result = await backup_service.restore_backup(
            backup_id=request.backup_id,
            components=request.components,
            user_id=current_user.id,
            username=current_user.username
        )
        
        return restore_result
        
    except Exception as e:
        logger.error(f"Backup restoration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup restoration failed: {str(e)}"
        )


# Scheduler management endpoints
@router.post("/scheduler/start")
async def start_backup_scheduler(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Start the automated backup scheduler
    """
    try:
        automated_backup_scheduler.start()
        
        # Log scheduler start
        audit_service.log_event(
            event_type=AuditEventType.SYSTEM_START,
            action="Backup scheduler started",
            user_id=current_user.id,
            username=current_user.username
        )
        
        return {"message": "Backup scheduler started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start backup scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start backup scheduler: {str(e)}"
        )


@router.post("/scheduler/stop")
async def stop_backup_scheduler(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Stop the automated backup scheduler
    """
    try:
        automated_backup_scheduler.stop()
        
        # Log scheduler stop
        audit_service.log_event(
            event_type=AuditEventType.SYSTEM_STOP,
            action="Backup scheduler stopped",
            user_id=current_user.id,
            username=current_user.username
        )
        
        return {"message": "Backup scheduler stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop backup scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop backup scheduler: {str(e)}"
        )


# Backup verification endpoint
@router.get("/verify/{backup_id}")
async def verify_backup(
    backup_id: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Verify backup integrity and completeness
    """
    try:
        # Find backup in history
        history = automated_backup_scheduler.get_backup_history(100)
        backup_info = next((b for b in history if b["backup_id"] == backup_id), None)
        
        if not backup_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup {backup_id} not found"
            )
        
        # Verify backup components
        verification_result = {
            "backup_id": backup_id,
            "verification_time": datetime.utcnow().isoformat(),
            "status": "verified",
            "components": {},
            "issues": []
        }
        
        # Check if backup components exist and are valid
        components = backup_info.get("components", {})
        for component_name, component_info in components.items():
            if isinstance(component_info, dict) and "file_path" in component_info:
                import os
                file_path = component_info["file_path"]
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    expected_size = component_info.get("size", 0)
                    
                    verification_result["components"][component_name] = {
                        "exists": True,
                        "size": file_size,
                        "expected_size": expected_size,
                        "size_match": file_size == expected_size
                    }
                    
                    if file_size != expected_size:
                        verification_result["issues"].append(
                            f"{component_name}: size mismatch (expected {expected_size}, got {file_size})"
                        )
                else:
                    verification_result["components"][component_name] = {"exists": False}
                    verification_result["issues"].append(f"{component_name}: file not found")
        
        if verification_result["issues"]:
            verification_result["status"] = "issues_found"
        
        return verification_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup verification failed: {str(e)}"
        )


# Cleanup endpoint
@router.post("/cleanup")
async def cleanup_old_backups(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Manually trigger cleanup of old backups
    """
    try:
        removed_count = backup_service.cleanup_old_backups()
        
        # Log cleanup
        audit_service.log_event(
            event_type=AuditEventType.BACKUP_CLEANUP,
            action="Manual backup cleanup",
            user_id=current_user.id,
            username=current_user.username,
            details={"removed_backups": removed_count}
        )
        
        return {
            "message": f"Cleanup completed: {removed_count} old backups removed",
            "removed_count": removed_count
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup cleanup failed: {str(e)}"
        )