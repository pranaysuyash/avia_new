"""
Compliance and Security API Endpoints

Endpoints for audit logs, data privacy, encryption, and compliance management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid
import hashlib
import json

from database.connection import get_db
from api.dependencies import get_current_user, get_admin_user
from database.models_extended import (
    AuditLog, DataRetentionPolicy, ConsentRecord
)
from compliance_security import (
    DataEncryptionService, DataClassification,
    AuditLogger, EventType, EventSeverity,
    ComplianceAutomation, DataSubjectRight
)

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance & Security"])

# Request/Response Models
class ConsentRequest(BaseModel):
    purpose: str
    data_categories: List[str]
    processing_activities: List[str]
    valid_days: int = 365

class DataSubjectRequest(BaseModel):
    request_type: str  # access, erasure, portability, rectification
    description: str
    data_categories: Optional[List[str]]

class EncryptionRequest(BaseModel):
    data: str
    classification: str = "confidential"
    purpose: str = "storage"

class AuditLogQuery(BaseModel):
    event_type: Optional[str]
    actor_id: Optional[str]
    target_id: Optional[str]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    severity: Optional[str]
    limit: int = 100

class SecurityScanRequest(BaseModel):
    scan_type: str  # static_code, dependency, secrets, api
    target: str
    profile: str = "default"

# Consent Management Endpoints
@router.post("/consent")
async def record_consent(
    consent: ConsentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record user consent for data processing"""
    # Create consent record
    db_consent = ConsentRecord(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        purpose=consent.purpose,
        data_categories=consent.data_categories,
        processing_activities=consent.processing_activities,
        legal_basis="consent",
        valid_until=datetime.utcnow() + timedelta(days=consent.valid_days),
        collection_method="api",
        ip_address=current_user.get("ip_address"),
        version="1.0"
    )
    
    db.add(db_consent)
    db.commit()
    
    # Log audit event
    audit_logger = AuditLogger()
    await audit_logger.log_event(
        EventType.DATA_ACCESS,
        f"Consent recorded for {consent.purpose}",
        actor_id=current_user["id"],
        metadata={
            "consent_id": db_consent.id,
            "data_categories": consent.data_categories
        }
    )
    
    return {
        "consent_id": db_consent.id,
        "status": "recorded",
        "valid_until": db_consent.valid_until
    }

@router.get("/consent")
async def get_my_consents(
    active_only: bool = True,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's consent records"""
    query = db.query(ConsentRecord).filter(ConsentRecord.user_id == current_user["id"])
    
    if active_only:
        query = query.filter(
            ConsentRecord.is_given == True,
            ConsentRecord.is_withdrawn == False,
            ConsentRecord.valid_until > datetime.utcnow()
        )
    
    consents = query.order_by(ConsentRecord.given_at.desc()).all()
    
    return consents

@router.delete("/consent/{consent_id}")
async def withdraw_consent(
    consent_id: str,
    reason: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Withdraw previously given consent"""
    consent = db.query(ConsentRecord).filter(
        ConsentRecord.id == consent_id,
        ConsentRecord.user_id == current_user["id"]
    ).first()
    
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")
    
    if consent.is_withdrawn:
        raise HTTPException(status_code=400, detail="Consent already withdrawn")
    
    # Withdraw consent
    consent.is_withdrawn = True
    consent.withdrawn_at = datetime.utcnow()
    
    db.commit()
    
    # Trigger compliance automation
    compliance = ComplianceAutomation()
    await compliance.withdraw_consent(consent_id, reason)
    
    # Log audit event
    audit_logger = AuditLogger()
    await audit_logger.log_event(
        EventType.DATA_ACCESS,
        f"Consent withdrawn: {reason or 'No reason provided'}",
        actor_id=current_user["id"],
        metadata={"consent_id": consent_id}
    )
    
    return {"status": "withdrawn", "consent_id": consent_id}

# Data Subject Rights Endpoints
@router.post("/data-subject-request")
async def submit_data_subject_request(
    request: DataSubjectRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit GDPR data subject request"""
    # Map request types to enum
    request_type_map = {
        "access": DataSubjectRight.ACCESS,
        "erasure": DataSubjectRight.ERASURE,
        "portability": DataSubjectRight.PORTABILITY,
        "rectification": DataSubjectRight.RECTIFICATION
    }
    
    if request.request_type not in request_type_map:
        raise HTTPException(status_code=400, detail="Invalid request type")
    
    # Submit request
    compliance = ComplianceAutomation()
    dsr = await compliance.submit_data_subject_request(
        current_user["id"],
        request_type_map[request.request_type],
        request.description,
        verification_method="authenticated_user"
    )
    
    return {
        "request_id": dsr.request_id,
        "type": request.request_type,
        "status": "submitted",
        "due_date": dsr.due_date,
        "message": f"Your {request.request_type} request will be processed within 30 days"
    }

@router.get("/data-subject-request/{request_id}")
async def get_data_subject_request_status(
    request_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check status of data subject request"""
    compliance = ComplianceAutomation()
    
    # Verify ownership
    dsr = compliance.data_subject_requests.get(request_id)
    if not dsr or dsr.data_subject_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        "request_id": dsr.request_id,
        "type": dsr.request_type.value,
        "status": dsr.status,
        "submitted_at": dsr.submitted_at,
        "due_date": dsr.due_date,
        "completed_at": dsr.completed_at
    }

@router.get("/my-data")
async def export_my_data(
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user data (GDPR right to data portability)"""
    compliance = ComplianceAutomation()
    
    # Gather all user data
    user_data = await compliance._gather_subject_data(current_user["id"])
    
    # Add additional data from various services
    # ... (transcripts, settings, usage history, etc.)
    
    if format == "json":
        return Response(
            content=json.dumps(user_data, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=my_data_{current_user['id']}.json"
            }
        )
    
    # For CSV/PDF, implement conversion
    # ... (simplified for now)
    
    return user_data

# Encryption Endpoints
@router.post("/encrypt")
async def encrypt_data(
    request: EncryptionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Encrypt sensitive data"""
    encryption_service = DataEncryptionService()
    
    # Map classification
    classification_map = {
        "public": DataClassification.PUBLIC,
        "internal": DataClassification.INTERNAL,
        "confidential": DataClassification.CONFIDENTIAL,
        "restricted": DataClassification.RESTRICTED
    }
    
    classification = classification_map.get(request.classification, DataClassification.CONFIDENTIAL)
    
    # Encrypt data
    encrypted = encryption_service.encrypt_data(
        request.data.encode(),
        classification=classification,
        owner=current_user["id"],
        purpose=request.purpose
    )
    
    # Log encryption event
    audit_logger = AuditLogger()
    await audit_logger.log_event(
        EventType.DATA_ACCESS,
        "Data encrypted",
        actor_id=current_user["id"],
        metadata={
            "data_id": encrypted.data_id,
            "classification": classification.value
        }
    )
    
    return {
        "data_id": encrypted.data_id,
        "key_id": encrypted.key_id,
        "algorithm": encrypted.algorithm,
        "encrypted_data": encrypted.encrypted_data.hex()
    }

# Audit Log Endpoints
@router.get("/audit-logs")
async def get_audit_logs(
    query: AuditLogQuery = Depends(),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Query audit logs (admin only)"""
    logs_query = db.query(AuditLog)
    
    # Apply filters
    if query.event_type:
        logs_query = logs_query.filter(AuditLog.event_type == query.event_type)
    
    if query.actor_id:
        logs_query = logs_query.filter(AuditLog.actor_id == query.actor_id)
    
    if query.target_id:
        logs_query = logs_query.filter(AuditLog.target_id == query.target_id)
    
    if query.date_from:
        logs_query = logs_query.filter(AuditLog.timestamp >= query.date_from)
    
    if query.date_to:
        logs_query = logs_query.filter(AuditLog.timestamp <= query.date_to)
    
    if query.severity:
        logs_query = logs_query.filter(AuditLog.risk_score >= severity_to_risk_score(query.severity))
    
    # Get results
    total = logs_query.count()
    logs = logs_query.order_by(AuditLog.timestamp.desc()).limit(query.limit).all()
    
    return {
        "total": total,
        "logs": logs
    }

@router.get("/audit-logs/export")
async def export_audit_logs(
    date_from: datetime,
    date_to: datetime,
    format: str = Query("csv", pattern="^(csv|json|pdf)$"),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Export audit logs for compliance reporting"""
    logs = db.query(AuditLog).filter(
        AuditLog.timestamp.between(date_from, date_to)
    ).order_by(AuditLog.timestamp).all()
    
    if format == "json":
        return Response(
            content=json.dumps([log_to_dict(log) for log in logs], indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{date_from.date()}_{date_to.date()}.json"
            }
        )
    
    # For CSV/PDF, implement conversion
    # ... (simplified for now)
    
    return {"total": len(logs), "format": format}

# Security Scanning Endpoints
@router.post("/security-scan")
async def run_security_scan(
    request: SecurityScanRequest,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Run security scan (admin only)"""
    from compliance_security import SecurityScanner, ScanType
    
    scanner = SecurityScanner()
    
    # Map scan types
    scan_type_map = {
        "static_code": ScanType.STATIC_CODE,
        "dependency": ScanType.DEPENDENCY,
        "secrets": ScanType.SECRETS,
        "api": ScanType.API
    }
    
    if request.scan_type not in scan_type_map:
        raise HTTPException(status_code=400, detail="Invalid scan type")
    
    # Run scan
    scan = await scanner.run_security_scan(
        scan_type_map[request.scan_type],
        request.target,
        request.profile
    )
    
    return {
        "scan_id": scan.scan_id,
        "status": scan.status,
        "vulnerabilities_found": scan.vulnerabilities_found,
        "vulnerabilities_by_severity": scan.vulnerabilities_by_severity
    }

@router.get("/security-posture")
async def get_security_posture(
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get current security posture assessment"""
    from compliance_security import SecurityScanner
    
    scanner = SecurityScanner()
    posture = scanner.assess_security_posture()
    
    return posture

# Data Retention Endpoints
@router.get("/retention-policies")
async def get_retention_policies(
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get data retention policies"""
    policies = db.query(DataRetentionPolicy).filter(
        DataRetentionPolicy.is_active == True
    ).all()
    
    return policies

@router.post("/retention-policies")
async def create_retention_policy(
    data_type: str = Body(...),
    retention_days: int = Body(...),
    action_on_expiry: str = Body(...),
    legal_basis: str = Body(...),
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create data retention policy"""
    policy = DataRetentionPolicy(
        id=str(uuid.uuid4()),
        data_type=data_type,
        retention_days=retention_days,
        action_on_expiry=action_on_expiry,
        legal_basis=legal_basis,
        compliance_frameworks=["GDPR", "CCPA"]
    )
    
    db.add(policy)
    db.commit()
    
    return policy

# Compliance Reports
@router.get("/compliance-report/{framework}")
async def generate_compliance_report(
    framework: str,
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Generate compliance report for specific framework"""
    compliance = ComplianceAutomation()
    report = compliance.generate_compliance_report(framework.upper())
    
    return report

@router.get("/gdpr-dashboard")
async def get_gdpr_dashboard(
    current_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get GDPR compliance dashboard data"""
    # Consent metrics
    total_consents = db.query(ConsentRecord).count()
    active_consents = db.query(ConsentRecord).filter(
        ConsentRecord.is_given == True,
        ConsentRecord.is_withdrawn == False
    ).count()
    
    # Data subject requests
    compliance = ComplianceAutomation()
    pending_dsrs = len([
        dsr for dsr in compliance.data_subject_requests.values()
        if dsr.status == "pending"
    ])
    
    # Recent audit events
    recent_events = db.query(AuditLog).filter(
        AuditLog.compliance_frameworks.contains(["GDPR"])
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return {
        "consent_metrics": {
            "total": total_consents,
            "active": active_consents,
            "withdrawn": total_consents - active_consents
        },
        "data_subject_requests": {
            "pending": pending_dsrs,
            "average_processing_time": "25 days"  # Calculate from completed requests
        },
        "recent_events": recent_events,
        "compliance_score": 92.5  # Calculate based on various factors
    }

# Helper functions
def severity_to_risk_score(severity: str) -> int:
    """Convert severity to risk score threshold"""
    severity_map = {
        "low": 30,
        "medium": 50,
        "high": 70,
        "critical": 90
    }
    return severity_map.get(severity, 0)

def log_to_dict(log: AuditLog) -> dict:
    """Convert audit log to dictionary"""
    return {
        "id": log.id,
        "timestamp": log.timestamp,
        "event_type": log.event_type,
        "description": log.description,
        "actor_id": log.actor_id,
        "target_id": log.target_id,
        "risk_score": log.risk_score,
        "compliance_frameworks": log.compliance_frameworks
    }