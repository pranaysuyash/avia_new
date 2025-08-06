# Compliance and Enterprise Security

A comprehensive security and compliance framework providing data protection, access control, audit logging, and automated compliance management for enterprise deployments.

## Features

### 1. **Data Encryption and Key Management**
- AES-256-GCM encryption for data at rest
- RSA-4096 for key encryption
- Automated key rotation policies
- Field-level encryption for databases
- Transparent file encryption
- Hardware Security Module (HSM) support ready
- Multiple encryption levels based on data classification

### 2. **Role-Based Access Control (RBAC)**
- Fine-grained permission management
- Hierarchical role inheritance
- Dynamic policy-based access control
- Resource-level permissions
- Attribute-based access control (ABAC) support
- Time-based and context-aware permissions
- Delegation and impersonation controls

### 3. **Comprehensive Audit Logging**
- Immutable audit trail
- Real-time event streaming
- Compliance-aware log retention
- Automated alerting for suspicious activities
- Multiple compliance framework support
- Forensic investigation capabilities
- Legal hold functionality

### 4. **Compliance Automation**
- **GDPR Compliance**
  - Consent management
  - Data Subject Rights (DSR) handling
  - Right to be forgotten automation
  - Data portability
  - Breach notification (72-hour)
  
- **HIPAA Compliance**
  - PHI encryption enforcement
  - Access controls for healthcare data
  - Audit logs for all PHI access
  - Breach notification procedures
  
- **SOC2 Compliance**
  - Security control monitoring
  - Availability tracking
  - Change management
  - Incident response automation

### 5. **Security Scanning and Vulnerability Management**
- Static Application Security Testing (SAST)
- Dependency vulnerability scanning
- Container security scanning
- API security testing
- Secret detection and prevention
- Automated remediation workflows
- Compliance scanning (CIS, NIST, PCI-DSS)

## Installation

```bash
# The compliance security package is included with the main application
pip install -r requirements.txt
```

## Quick Start

### Data Encryption

```python
from compliance_security import DataEncryptionService, DataClassification

# Initialize encryption service
encryption_service = DataEncryptionService()

# Encrypt sensitive data
sensitive_data = b"Patient medical records"
encrypted = encryption_service.encrypt_data(
    sensitive_data,
    classification=DataClassification.HEALTH_DATA,
    owner="healthcare_dept"
)

print(f"Encrypted data ID: {encrypted.data_id}")
print(f"Encryption key ID: {encrypted.key_id}")

# Decrypt data
decrypted = encryption_service.decrypt_data(encrypted)
print(f"Decrypted: {decrypted.decode()}")

# Field-level encryption for databases
from compliance_security import FieldEncryption

field_encryption = FieldEncryption(encryption_service)

# Encrypt PII fields
user_record = {
    "id": "user_123",
    "name": "John Doe",
    "ssn": "123-45-6789",
    "email": "john@example.com"
}

encrypted_record = field_encryption.encrypt_pii_fields(user_record, "user_123")
# SSN and email are now encrypted
```

### Access Control

```python
from compliance_security import AccessControlService, Action, ResourceType

# Initialize access control
ac_service = AccessControlService()

# Create custom role
custom_role = ac_service.create_custom_role(
    name="Data Analyst",
    description="Can read and analyze data but not modify",
    permissions=[
        "transcription:read:organization",
        "analytics:read:organization",
        "export:create:user"
    ],
    created_by="admin"
)

# Assign role to user
ac_service.assign_role("user_456", custom_role.role_id)

# Check permissions
allowed, reason = ac_service.check_permission(
    user_id="user_456",
    resource_id="trans_789",
    action=Action.READ,
    context={"ip_address": "192.168.1.100"}
)

if allowed:
    print("Access granted")
else:
    print(f"Access denied: {reason}")

# Create dynamic policy
policy = ac_service.create_policy_rule(
    name="Business Hours Only",
    description="Allow access only during business hours",
    conditions={
        "time_of_day": "09:00-17:00",
        "mfa_required": True
    },
    effect="allow",
    actions=[Action.READ, Action.UPDATE],
    resources=["trans_*"]
)
```

### Audit Logging

```python
from compliance_security import AuditLogger, EventType, EventSeverity
import asyncio

async def log_events():
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    # Log security event
    await audit_logger.log_event(
        EventType.DATA_ACCESS,
        "User accessed sensitive transcription",
        actor_id="user_123",
        target_id="trans_456",
        severity=EventSeverity.INFO,
        metadata={
            "data_classification": "confidential",
            "access_reason": "customer_support"
        }
    )
    
    # Log failed login attempt
    await audit_logger.log_event(
        EventType.LOGIN_FAILED,
        "Failed login attempt from unknown IP",
        actor_id="user_unknown",
        severity=EventSeverity.WARNING,
        metadata={"ip_address": "203.0.113.45"}
    )
    
    # Generate compliance report
    from compliance_security import ComplianceFramework
    
    report = audit_logger.generate_compliance_report(
        ComplianceFramework.GDPR,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    
    print(f"GDPR Compliance Score: {report.compliance_score:.1f}%")

asyncio.run(log_events())
```

### Compliance Automation

```python
from compliance_security import ComplianceAutomation, DataCategory, LegalBasis
import asyncio

async def manage_compliance():
    # Initialize compliance automation
    compliance = ComplianceAutomation()
    
    # Record consent
    consent = await compliance.record_consent(
        data_subject_id="user_123",
        purpose="Audio transcription and analysis",
        data_categories=[DataCategory.PERSONAL_DATA],
        processing_activities=["transcription", "storage", "analysis"],
        legal_basis=LegalBasis.CONSENT,
        valid_days=365
    )
    
    print(f"Consent recorded: {consent.consent_id}")
    
    # Handle data subject request
    from compliance_security import DataSubjectRight
    
    dsr = await compliance.submit_data_subject_request(
        data_subject_id="user_123",
        request_type=DataSubjectRight.ACCESS,
        description="I want to see all my data"
    )
    
    print(f"DSR submitted: {dsr.request_id}")
    print(f"Due date: {dsr.due_date}")
    
    # Record data breach (if applicable)
    breach = await compliance.record_data_breach(
        description="Unauthorized access detected",
        data_categories_affected=[DataCategory.PERSONAL_DATA],
        records_affected=100,
        risk_assessment="high"
    )
    
    print(f"Breach recorded: {breach.breach_id}")
    print(f"DPA notification required: {breach.risk_to_rights == 'high'}")

asyncio.run(manage_compliance())
```

### Security Scanning

```python
from compliance_security import SecurityScanner, ScanType
import asyncio

async def run_security_scans():
    # Initialize scanner
    scanner = SecurityScanner()
    
    # Run static code analysis
    code_scan = await scanner.run_security_scan(
        ScanType.STATIC_CODE,
        target="/app/src"
    )
    
    print(f"Code scan found {code_scan.vulnerabilities_found} vulnerabilities")
    
    # Run dependency scan
    dep_scan = await scanner.run_security_scan(
        ScanType.DEPENDENCY,
        target="requirements.txt"
    )
    
    # Check for exposed secrets
    secrets_scan = await scanner.run_security_scan(
        ScanType.SECRETS,
        target="/app"
    )
    
    # Assess security posture
    posture = scanner.assess_security_posture()
    print(f"Security Score: {posture['security_score']}/100")
    print(f"Security Posture: {posture['posture']}")
    
    # Generate security report
    report = scanner.generate_security_report()
    print(f"Critical vulnerabilities: {report['executive_summary']['critical_vulnerabilities']}")

asyncio.run(run_security_scans())
```

## Configuration

### Environment Variables

```bash
# Encryption settings
MASTER_KEY_PATH=/secure/keys/master.key
KEY_ROTATION_DAYS=90
ENCRYPTION_LEVEL=maximum  # standard, high, maximum

# Access control
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
REQUIRE_MFA=true

# Audit logging
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years for GDPR
AUDIT_LOG_STORAGE=s3://audit-logs
ENABLE_REAL_TIME_ALERTS=true

# Compliance
GDPR_DPO_EMAIL=dpo@company.com
GDPR_DSR_DEADLINE_DAYS=30
BREACH_NOTIFICATION_HOURS=72

# Security scanning
SCAN_ON_COMMIT=true
VULNERABILITY_THRESHOLD=high
AUTO_REMEDIATE=false
```

### Security Policies

```python
# Configure security policies
from compliance_security import SecurityPolicy

# No hardcoded secrets policy
no_secrets_policy = SecurityPolicy(
    policy_id="no_secrets",
    name="No Hardcoded Secrets",
    description="Prevent secrets in code",
    rules=[
        {
            "type": "pattern_match",
            "patterns": ["password", "api_key", "secret"],
            "action": "block"
        }
    ],
    enforcement_level="block"
)

# Secure API policy
api_security_policy = SecurityPolicy(
    policy_id="api_security",
    name="API Security Requirements",
    description="Enforce API security standards",
    rules=[
        {
            "type": "require_authentication",
            "action": "block"
        },
        {
            "type": "require_https",
            "action": "block"
        },
        {
            "type": "rate_limiting",
            "max_requests_per_hour": 1000,
            "action": "throttle"
        }
    ]
)
```

## Compliance Dashboards

### GDPR Dashboard
- Consent management overview
- Data subject request queue
- Data retention compliance
- Breach notification status
- Privacy impact assessments

### HIPAA Dashboard
- PHI access logs
- Encryption status
- User access reviews
- Incident response metrics
- Training compliance

### SOC2 Dashboard
- Security control status
- Availability metrics
- Change management log
- Vulnerability trends
- Incident response times

## Best Practices

### 1. **Encryption**
- Use appropriate encryption levels for data classification
- Rotate encryption keys regularly
- Store keys separately from encrypted data
- Use HSM for production environments
- Implement key escrow for recovery

### 2. **Access Control**
- Follow principle of least privilege
- Regularly review and audit permissions
- Implement segregation of duties
- Use time-based access for temporary needs
- Enable MFA for all privileged accounts

### 3. **Audit Logging**
- Never disable audit logging
- Protect audit logs from tampering
- Regularly review logs for anomalies
- Set up automated alerts for critical events
- Maintain logs per compliance requirements

### 4. **Compliance**
- Regularly update consent records
- Process DSRs within legal timeframes
- Test breach notification procedures
- Maintain compliance documentation
- Conduct regular compliance audits

### 5. **Security Scanning**
- Integrate scanning into CI/CD pipeline
- Address critical vulnerabilities immediately
- Track remediation metrics
- Maintain vulnerability database
- Perform regular penetration testing

## Architecture

```
compliance_security/
├── data_encryption.py      # Encryption and key management
├── access_control.py       # RBAC and permission management
├── audit_logging.py        # Audit trail and compliance reporting
├── compliance_automation.py # GDPR, HIPAA, SOC2 automation
├── security_scanning.py    # Vulnerability scanning and management
├── __init__.py            # Package initialization
└── README.md              # This file

Integration Points:
├── Database              # Encrypted field storage
├── API Gateway          # Access control enforcement
├── Message Queue        # Audit event streaming
├── Object Storage       # Encrypted file storage
├── Monitoring           # Security metrics and alerts
└── CI/CD Pipeline       # Security scanning integration
```

## Compliance Certifications

This module helps achieve compliance with:

- **GDPR** (General Data Protection Regulation)
- **HIPAA** (Health Insurance Portability and Accountability Act)
- **SOC2** Type II
- **ISO 27001** Information Security Management
- **PCI DSS** (Payment Card Industry Data Security Standard)
- **CCPA** (California Consumer Privacy Act)
- **NIST** Cybersecurity Framework

## Troubleshooting

### Common Issues

1. **Encryption Key Not Found**
   - Verify key exists in key store
   - Check key rotation status
   - Ensure proper key permissions

2. **Access Denied Errors**
   - Review user permissions
   - Check policy rules
   - Verify resource ownership
   - Review audit logs

3. **Compliance Report Failures**
   - Ensure sufficient audit data
   - Check retention policies
   - Verify time range parameters

4. **Security Scan Timeouts**
   - Reduce scan scope
   - Increase timeout values
   - Check scanner resources

5. **Audit Log Storage Full**
   - Archive old logs
   - Increase storage capacity
   - Review retention policies

## Security Considerations

- All encryption keys are encrypted at rest
- Audit logs are immutable and tamper-evident
- Access control decisions are logged
- Compliance data is backed up regularly
- Security scans run in isolated environments
- Vulnerability data is encrypted
- All communications use TLS 1.2+

## Future Enhancements

- [ ] Homomorphic encryption for processing encrypted data
- [ ] Blockchain-based audit trail
- [ ] AI-powered anomaly detection
- [ ] Automated compliance evidence collection
- [ ] Zero-trust architecture support
- [ ] Quantum-resistant cryptography
- [ ] Privacy-preserving analytics

## Support

For security and compliance support:
- Security incidents: security@company.com
- Compliance questions: compliance@company.com
- Documentation: https://docs.company.com/security

## License

This compliance and security module is part of the Transcription Platform and follows the same license terms.