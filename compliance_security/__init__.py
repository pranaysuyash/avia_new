"""
Compliance and Enterprise Security Package

Comprehensive security and compliance features including:
- Data encryption and key management
- Role-based access control (RBAC)
- Audit logging and compliance reporting
- Automated compliance management (GDPR, HIPAA, SOC2)
- Security scanning and vulnerability management
"""

from .data_encryption import (
    DataEncryptionService,
    EncryptionLevel,
    KeyType,
    KeyStatus,
    DataClassification,
    EncryptionKey,
    EncryptedData,
    KeyRotationPolicy,
    FieldEncryption,
    TransparentEncryption
)

from .access_control import (
    AccessControlService,
    ResourceType,
    Action,
    PermissionScope,
    Role,
    User,
    Resource,
    AccessRequest,
    PolicyRule
)

from .audit_logging import (
    AuditLogger,
    EventType,
    EventSeverity,
    ComplianceFramework,
    AuditEvent,
    AuditRetentionPolicy,
    ComplianceReport
)

from .compliance_automation import (
    ComplianceAutomation,
    DataCategory,
    LegalBasis,
    DataSubjectRight,
    ConsentRecord,
    DataProcessingActivity,
    DataSubjectRequest,
    DataBreach,
    CompliancePolicy
)

from .security_scanning import (
    SecurityScanner,
    ScanType,
    VulnerabilitySeverity,
    RemediationStatus,
    Vulnerability,
    SecurityScan,
    SecurityPolicy,
    ComplianceCheck
)

__version__ = "1.0.0"

__all__ = [
    # Data Encryption
    "DataEncryptionService",
    "EncryptionLevel",
    "KeyType",
    "KeyStatus",
    "DataClassification",
    "EncryptionKey",
    "EncryptedData",
    "KeyRotationPolicy",
    "FieldEncryption",
    "TransparentEncryption",
    
    # Access Control
    "AccessControlService",
    "ResourceType",
    "Action",
    "PermissionScope",
    "Role",
    "User",
    "Resource",
    "AccessRequest",
    "PolicyRule",
    
    # Audit Logging
    "AuditLogger",
    "EventType",
    "EventSeverity",
    "ComplianceFramework",
    "AuditEvent",
    "AuditRetentionPolicy",
    "ComplianceReport",
    
    # Compliance Automation
    "ComplianceAutomation",
    "DataCategory",
    "LegalBasis",
    "DataSubjectRight",
    "ConsentRecord",
    "DataProcessingActivity",
    "DataSubjectRequest",
    "DataBreach",
    "CompliancePolicy",
    
    # Security Scanning
    "SecurityScanner",
    "ScanType",
    "VulnerabilitySeverity",
    "RemediationStatus",
    "Vulnerability",
    "SecurityScan",
    "SecurityPolicy",
    "ComplianceCheck"
]