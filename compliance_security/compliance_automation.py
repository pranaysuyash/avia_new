"""
Compliance Automation and Policy Enforcement

Automates compliance requirements for GDPR, HIPAA, SOC2, and other frameworks
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
import asyncio
from collections import defaultdict
import re

class DataCategory(str, Enum):
    """Categories of data for compliance"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_PERSONAL_DATA = "sensitive_personal_data"
    HEALTH_DATA = "health_data"
    FINANCIAL_DATA = "financial_data"
    BIOMETRIC_DATA = "biometric_data"
    GENETIC_DATA = "genetic_data"
    CRIMINAL_DATA = "criminal_data"
    MINORS_DATA = "minors_data"

class LegalBasis(str, Enum):
    """Legal basis for data processing (GDPR)"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

class DataSubjectRight(str, Enum):
    """Data subject rights"""
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"  # Right to be forgotten
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"
    AUTOMATED_DECISION = "automated_decision"

class ConsentRecord(BaseModel):
    """Consent record for data processing"""
    consent_id: str
    data_subject_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Consent details
    purpose: str
    data_categories: List[DataCategory]
    processing_activities: List[str]
    legal_basis: LegalBasis
    
    # Consent properties
    is_explicit: bool = True
    is_freely_given: bool = True
    is_specific: bool = True
    is_informed: bool = True
    is_withdrawn: bool = False
    
    # Validity
    valid_until: Optional[datetime]
    withdrawn_at: Optional[datetime]
    
    # Metadata
    collection_method: str  # web_form, api, import, etc.
    ip_address: Optional[str]
    user_agent: Optional[str]
    version: str = "1.0"

class DataProcessingActivity(BaseModel):
    """Record of processing activities (ROPA)"""
    activity_id: str
    name: str
    description: str
    
    # Processing details
    purposes: List[str]
    legal_basis: List[LegalBasis]
    data_categories: List[DataCategory]
    data_subjects: List[str]  # Types of data subjects
    
    # Data flow
    data_sources: List[str]
    data_recipients: List[str]
    third_countries_transfers: List[str] = []
    
    # Security measures
    technical_measures: List[str]
    organizational_measures: List[str]
    
    # Retention
    retention_period_days: int
    deletion_procedure: str
    
    # Risk assessment
    risk_level: str  # low, medium, high
    dpia_required: bool = False
    dpia_completed: bool = False

class DataSubjectRequest(BaseModel):
    """Data subject request (DSR)"""
    request_id: str
    data_subject_id: str
    request_type: DataSubjectRight
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Request details
    description: str
    verification_method: str
    verification_completed: bool = False
    
    # Processing
    status: str = "pending"  # pending, in_progress, completed, rejected
    assigned_to: Optional[str]
    
    # Timeline (GDPR: 30 days)
    due_date: datetime
    completed_at: Optional[datetime]
    
    # Response
    response_method: str  # email, api, portal
    response_data: Optional[Dict[str, Any]]
    rejection_reason: Optional[str]

class DataBreach(BaseModel):
    """Data breach incident record"""
    breach_id: str
    detected_at: datetime
    occurred_at: Optional[datetime]
    
    # Breach details
    description: str
    data_categories_affected: List[DataCategory]
    records_affected: int
    data_subjects_affected: List[str]
    
    # Risk assessment
    risk_to_rights: str  # low, medium, high
    likely_consequences: List[str]
    
    # Notifications
    dpa_notified: bool = False
    dpa_notified_at: Optional[datetime]
    subjects_notified: bool = False
    subjects_notified_at: Optional[datetime]
    
    # Remediation
    measures_taken: List[str]
    measures_planned: List[str]
    
    # Investigation
    root_cause: Optional[str]
    investigation_status: str = "ongoing"

class CompliancePolicy(BaseModel):
    """Automated compliance policy"""
    policy_id: str
    name: str
    framework: str  # GDPR, HIPAA, SOC2, etc.
    
    # Rules
    rules: List[Dict[str, Any]]
    
    # Actions
    automated_actions: List[str]
    notifications: List[Dict[str, str]]
    
    # Status
    is_active: bool = True
    last_evaluated: Optional[datetime]
    violations_count: int = 0

class ComplianceAutomation:
    """Main compliance automation service"""
    
    def __init__(self):
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.processing_activities: Dict[str, DataProcessingActivity] = {}
        self.data_subject_requests: Dict[str, DataSubjectRequest] = {}
        self.data_breaches: Dict[str, DataBreach] = {}
        self.compliance_policies: Dict[str, CompliancePolicy] = {}
        
        # Indexes
        self.consents_by_subject: Dict[str, List[ConsentRecord]] = defaultdict(list)
        self.active_dsrs: List[DataSubjectRequest] = []
        
        # Configuration
        self.dsr_deadline_days = 30  # GDPR requirement
        self.breach_notification_hours = 72  # GDPR requirement
        
        # Initialize default policies
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default compliance policies"""
        # GDPR consent management
        self.compliance_policies["gdpr_consent"] = CompliancePolicy(
            policy_id="gdpr_consent",
            name="GDPR Consent Management",
            framework="GDPR",
            rules=[
                {
                    "type": "consent_validity",
                    "max_age_days": 365,
                    "action": "request_renewal"
                },
                {
                    "type": "consent_withdrawal",
                    "action": "stop_processing"
                }
            ],
            automated_actions=["pause_processing", "notify_processors"],
            notifications=[
                {"recipient": "dpo", "method": "email"},
                {"recipient": "legal", "method": "slack"}
            ]
        )
        
        # HIPAA PHI handling
        self.compliance_policies["hipaa_phi"] = CompliancePolicy(
            policy_id="hipaa_phi",
            name="HIPAA PHI Protection",
            framework="HIPAA",
            rules=[
                {
                    "type": "encryption_required",
                    "data_category": "health_data",
                    "action": "enforce_encryption"
                },
                {
                    "type": "access_control",
                    "min_auth_level": "mfa",
                    "action": "enforce_mfa"
                }
            ],
            automated_actions=["encrypt_data", "audit_access"],
            notifications=[
                {"recipient": "security_team", "method": "pagerduty"}
            ]
        )
        
        # Data retention
        self.compliance_policies["data_retention"] = CompliancePolicy(
            policy_id="data_retention",
            name="Data Retention Policy",
            framework="GDPR,CCPA",
            rules=[
                {
                    "type": "retention_limit",
                    "category": "personal_data",
                    "max_days": 730,
                    "action": "schedule_deletion"
                },
                {
                    "type": "retention_limit",
                    "category": "sensitive_personal_data",
                    "max_days": 365,
                    "action": "schedule_deletion"
                }
            ],
            automated_actions=["delete_data", "anonymize_data"],
            notifications=[
                {"recipient": "data_owner", "method": "email"}
            ]
        )
    
    async def record_consent(
        self,
        data_subject_id: str,
        purpose: str,
        data_categories: List[DataCategory],
        processing_activities: List[str],
        legal_basis: LegalBasis = LegalBasis.CONSENT,
        valid_days: int = 365,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """Record data subject consent"""
        consent = ConsentRecord(
            consent_id=f"consent_{datetime.utcnow().timestamp()}",
            data_subject_id=data_subject_id,
            purpose=purpose,
            data_categories=data_categories,
            processing_activities=processing_activities,
            legal_basis=legal_basis,
            valid_until=datetime.utcnow() + timedelta(days=valid_days),
            collection_method=metadata.get("collection_method", "api") if metadata else "api",
            ip_address=metadata.get("ip_address") if metadata else None,
            user_agent=metadata.get("user_agent") if metadata else None
        )
        
        # Store consent
        self.consent_records[consent.consent_id] = consent
        self.consents_by_subject[data_subject_id].append(consent)
        
        # Trigger compliance checks
        await self._check_consent_compliance(consent)
        
        return consent
    
    async def withdraw_consent(
        self,
        consent_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Withdraw consent"""
        consent = self.consent_records.get(consent_id)
        if not consent or consent.is_withdrawn:
            return False
        
        consent.is_withdrawn = True
        consent.withdrawn_at = datetime.utcnow()
        
        # Trigger automated actions
        await self._handle_consent_withdrawal(consent)
        
        return True
    
    async def _handle_consent_withdrawal(self, consent: ConsentRecord):
        """Handle consent withdrawal automatically"""
        # Stop processing for this purpose
        # In production, integrate with data processing systems
        
        # Notify relevant systems
        notifications = []
        notifications.append({
            "type": "consent_withdrawn",
            "consent_id": consent.consent_id,
            "data_subject_id": consent.data_subject_id,
            "purpose": consent.purpose,
            "timestamp": consent.withdrawn_at.isoformat()
        })
        
        # Delete or anonymize data if required
        if consent.legal_basis == LegalBasis.CONSENT:
            # Schedule data deletion
            await self._schedule_data_deletion(
                consent.data_subject_id,
                consent.data_categories
            )
    
    async def submit_data_subject_request(
        self,
        data_subject_id: str,
        request_type: DataSubjectRight,
        description: str,
        verification_method: str = "email"
    ) -> DataSubjectRequest:
        """Submit data subject request"""
        dsr = DataSubjectRequest(
            request_id=f"dsr_{datetime.utcnow().timestamp()}",
            data_subject_id=data_subject_id,
            request_type=request_type,
            description=description,
            verification_method=verification_method,
            due_date=datetime.utcnow() + timedelta(days=self.dsr_deadline_days)
        )
        
        # Store request
        self.data_subject_requests[dsr.request_id] = dsr
        self.active_dsrs.append(dsr)
        
        # Start processing
        await self._process_dsr(dsr)
        
        return dsr
    
    async def _process_dsr(self, dsr: DataSubjectRequest):
        """Process data subject request"""
        dsr.status = "in_progress"
        
        if dsr.request_type == DataSubjectRight.ACCESS:
            # Gather all data about subject
            data = await self._gather_subject_data(dsr.data_subject_id)
            dsr.response_data = data
            
        elif dsr.request_type == DataSubjectRight.ERASURE:
            # Right to be forgotten
            deletion_result = await self._delete_subject_data(dsr.data_subject_id)
            dsr.response_data = deletion_result
            
        elif dsr.request_type == DataSubjectRight.PORTABILITY:
            # Export data in portable format
            export_data = await self._export_subject_data(dsr.data_subject_id)
            dsr.response_data = {"download_url": export_data}
            
        elif dsr.request_type == DataSubjectRight.RECTIFICATION:
            # Update incorrect data
            # In production, implement data correction workflow
            pass
        
        dsr.status = "completed"
        dsr.completed_at = datetime.utcnow()
    
    async def _gather_subject_data(self, data_subject_id: str) -> Dict[str, Any]:
        """Gather all data about a data subject"""
        data = {
            "data_subject_id": data_subject_id,
            "collected_at": datetime.utcnow().isoformat(),
            "data_categories": {},
            "processing_activities": [],
            "consents": [],
            "data_sources": []
        }
        
        # Get consent records
        subject_consents = self.consents_by_subject.get(data_subject_id, [])
        data["consents"] = [
            {
                "consent_id": c.consent_id,
                "purpose": c.purpose,
                "given_at": c.timestamp.isoformat(),
                "valid_until": c.valid_until.isoformat() if c.valid_until else None,
                "is_withdrawn": c.is_withdrawn
            }
            for c in subject_consents
        ]
        
        # In production, query all systems for subject data
        # This is a simplified example
        data["data_categories"] = {
            "personal_data": {
                "email": f"user_{data_subject_id}@example.com",
                "name": "Data Subject Name",
                "account_created": "2023-01-01T00:00:00Z"
            },
            "usage_data": {
                "last_login": "2024-01-15T10:30:00Z",
                "total_transcriptions": 42
            }
        }
        
        return data
    
    async def _delete_subject_data(self, data_subject_id: str) -> Dict[str, Any]:
        """Delete all data for a subject (right to be forgotten)"""
        deletion_log = {
            "data_subject_id": data_subject_id,
            "deletion_started": datetime.utcnow().isoformat(),
            "systems_processed": [],
            "records_deleted": 0,
            "errors": []
        }
        
        # Check if deletion is allowed
        active_consents = [
            c for c in self.consents_by_subject.get(data_subject_id, [])
            if not c.is_withdrawn and c.legal_basis != LegalBasis.CONSENT
        ]
        
        if active_consents:
            # Cannot delete if processing is based on legal obligation, etc.
            deletion_log["errors"].append(
                "Cannot delete: Active legal basis for processing exists"
            )
            return deletion_log
        
        # In production, coordinate deletion across all systems
        # This is a simplified example
        systems = ["database", "file_storage", "analytics", "backups"]
        
        for system in systems:
            try:
                # Simulate deletion
                deletion_log["systems_processed"].append(system)
                deletion_log["records_deleted"] += 10  # Example
            except Exception as e:
                deletion_log["errors"].append(f"Error in {system}: {str(e)}")
        
        deletion_log["deletion_completed"] = datetime.utcnow().isoformat()
        
        return deletion_log
    
    async def _export_subject_data(self, data_subject_id: str) -> str:
        """Export subject data in portable format"""
        # Gather all data
        data = await self._gather_subject_data(data_subject_id)
        
        # In production, create downloadable file
        # Return URL or file path
        export_path = f"/exports/{data_subject_id}_{datetime.utcnow().timestamp()}.json"
        
        return export_path
    
    async def record_data_breach(
        self,
        description: str,
        data_categories_affected: List[DataCategory],
        records_affected: int,
        risk_assessment: str = "medium"
    ) -> DataBreach:
        """Record data breach incident"""
        breach = DataBreach(
            breach_id=f"breach_{datetime.utcnow().timestamp()}",
            detected_at=datetime.utcnow(),
            description=description,
            data_categories_affected=data_categories_affected,
            records_affected=records_affected,
            data_subjects_affected=[],  # To be determined
            risk_to_rights=risk_assessment,
            likely_consequences=self._assess_breach_consequences(
                data_categories_affected,
                records_affected
            )
        )
        
        # Store breach
        self.data_breaches[breach.breach_id] = breach
        
        # Start breach response
        await self._handle_data_breach(breach)
        
        return breach
    
    async def _handle_data_breach(self, breach: DataBreach):
        """Handle data breach according to regulations"""
        # Check notification requirements
        hours_since_detection = (datetime.utcnow() - breach.detected_at).total_seconds() / 3600
        
        # GDPR: Notify DPA within 72 hours for high risk
        if breach.risk_to_rights in ["medium", "high"] and hours_since_detection < self.breach_notification_hours:
            await self._notify_dpa(breach)
            breach.dpa_notified = True
            breach.dpa_notified_at = datetime.utcnow()
        
        # Notify affected subjects for high risk
        if breach.risk_to_rights == "high":
            await self._notify_data_subjects(breach)
            breach.subjects_notified = True
            breach.subjects_notified_at = datetime.utcnow()
        
        # Implement containment measures
        breach.measures_taken = [
            "Isolated affected systems",
            "Reset access credentials",
            "Enabled additional monitoring"
        ]
    
    def _assess_breach_consequences(
        self,
        data_categories: List[DataCategory],
        records_affected: int
    ) -> List[str]:
        """Assess likely consequences of breach"""
        consequences = []
        
        if DataCategory.FINANCIAL_DATA in data_categories:
            consequences.append("Financial loss")
            consequences.append("Fraud risk")
        
        if DataCategory.HEALTH_DATA in data_categories:
            consequences.append("Medical privacy violation")
            consequences.append("Insurance discrimination risk")
        
        if any(cat in data_categories for cat in [
            DataCategory.SENSITIVE_PERSONAL_DATA,
            DataCategory.BIOMETRIC_DATA,
            DataCategory.GENETIC_DATA
        ]):
            consequences.append("Identity theft risk")
            consequences.append("Discrimination risk")
        
        if records_affected > 1000:
            consequences.append("Large-scale privacy impact")
        
        return consequences
    
    async def _notify_dpa(self, breach: DataBreach):
        """Notify Data Protection Authority"""
        # In production, integrate with DPA notification systems
        notification = {
            "breach_id": breach.breach_id,
            "organization": "Your Organization",
            "detected_at": breach.detected_at.isoformat(),
            "description": breach.description,
            "categories_affected": [cat.value for cat in breach.data_categories_affected],
            "records_affected": breach.records_affected,
            "risk_assessment": breach.risk_to_rights,
            "measures_taken": breach.measures_taken
        }
        
        # Log notification
        print(f"DPA Notification sent: {json.dumps(notification, indent=2)}")
    
    async def _notify_data_subjects(self, breach: DataBreach):
        """Notify affected data subjects"""
        # In production, send notifications to affected users
        pass
    
    async def evaluate_compliance_policies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Evaluate all compliance policies and return violations"""
        violations = defaultdict(list)
        
        for policy_id, policy in self.compliance_policies.items():
            if not policy.is_active:
                continue
            
            policy_violations = await self._evaluate_policy(policy)
            if policy_violations:
                violations[policy_id] = policy_violations
                policy.violations_count += len(policy_violations)
            
            policy.last_evaluated = datetime.utcnow()
        
        return dict(violations)
    
    async def _evaluate_policy(self, policy: CompliancePolicy) -> List[Dict[str, Any]]:
        """Evaluate single compliance policy"""
        violations = []
        
        for rule in policy.rules:
            if rule["type"] == "consent_validity":
                # Check consent age
                max_age_days = rule["max_age_days"]
                cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
                
                for consent in self.consent_records.values():
                    if not consent.is_withdrawn and consent.timestamp < cutoff_date:
                        violations.append({
                            "rule": "consent_validity",
                            "consent_id": consent.consent_id,
                            "age_days": (datetime.utcnow() - consent.timestamp).days,
                            "action_required": rule["action"]
                        })
            
            elif rule["type"] == "retention_limit":
                # Check data retention
                # In production, query data stores for old records
                pass
            
            elif rule["type"] == "encryption_required":
                # Check encryption status
                # In production, verify encryption on sensitive data
                pass
        
        return violations
    
    async def _schedule_data_deletion(
        self,
        data_subject_id: str,
        data_categories: List[DataCategory]
    ):
        """Schedule data deletion"""
        # In production, create deletion job
        deletion_job = {
            "job_id": f"del_{datetime.utcnow().timestamp()}",
            "data_subject_id": data_subject_id,
            "data_categories": [cat.value for cat in data_categories],
            "scheduled_for": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "status": "scheduled"
        }
        
        # Log deletion job
        print(f"Deletion scheduled: {json.dumps(deletion_job, indent=2)}")
    
    def generate_compliance_report(self, framework: str) -> Dict[str, Any]:
        """Generate compliance report for specific framework"""
        report = {
            "framework": framework,
            "generated_at": datetime.utcnow().isoformat(),
            "compliance_status": "compliant",
            "findings": [],
            "recommendations": []
        }
        
        if framework == "GDPR":
            # Check GDPR requirements
            report["gdpr_compliance"] = {
                "consent_management": self._check_consent_compliance_status(),
                "dsr_handling": self._check_dsr_compliance_status(),
                "breach_notification": self._check_breach_compliance_status(),
                "data_protection": self._check_data_protection_status()
            }
            
            # Add findings
            if not all(report["gdpr_compliance"].values()):
                report["compliance_status"] = "non_compliant"
                report["findings"].append("GDPR compliance issues detected")
        
        elif framework == "HIPAA":
            # Check HIPAA requirements
            report["hipaa_compliance"] = {
                "access_controls": self._check_hipaa_access_controls(),
                "encryption": self._check_hipaa_encryption(),
                "audit_logs": self._check_hipaa_audit_logs(),
                "breach_notification": self._check_hipaa_breach_notification()
            }
        
        return report
    
    def _check_consent_compliance_status(self) -> bool:
        """Check consent management compliance"""
        # Check if all consents are valid and properly documented
        for consent in self.consent_records.values():
            if not consent.is_withdrawn:
                # Check GDPR consent requirements
                if not all([
                    consent.is_explicit,
                    consent.is_freely_given,
                    consent.is_specific,
                    consent.is_informed
                ]):
                    return False
        return True
    
    def _check_dsr_compliance_status(self) -> bool:
        """Check DSR handling compliance"""
        # Check if all DSRs are handled within deadline
        for dsr in self.data_subject_requests.values():
            if dsr.status != "completed" and datetime.utcnow() > dsr.due_date:
                return False
        return True
    
    def _check_breach_compliance_status(self) -> bool:
        """Check breach notification compliance"""
        # Check if breaches are notified on time
        for breach in self.data_breaches.values():
            hours_since = (datetime.utcnow() - breach.detected_at).total_seconds() / 3600
            if breach.risk_to_rights in ["medium", "high"] and not breach.dpa_notified and hours_since > 72:
                return False
        return True
    
    def _check_data_protection_status(self) -> bool:
        """Check data protection measures"""
        # In production, verify encryption, access controls, etc.
        return True
    
    def _check_hipaa_access_controls(self) -> bool:
        """Check HIPAA access control requirements"""
        # In production, verify access controls on PHI
        return True
    
    def _check_hipaa_encryption(self) -> bool:
        """Check HIPAA encryption requirements"""
        # In production, verify encryption of PHI at rest and in transit
        return True
    
    def _check_hipaa_audit_logs(self) -> bool:
        """Check HIPAA audit log requirements"""
        # In production, verify comprehensive audit logging
        return True
    
    def _check_hipaa_breach_notification(self) -> bool:
        """Check HIPAA breach notification requirements"""
        # Similar to GDPR but with different timelines
        return True

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize compliance automation
        compliance = ComplianceAutomation()
        
        # Record consent
        consent = await compliance.record_consent(
            data_subject_id="user_123",
            purpose="Transcription and analysis services",
            data_categories=[DataCategory.PERSONAL_DATA],
            processing_activities=["transcription", "entity_extraction", "storage"],
            legal_basis=LegalBasis.CONSENT,
            metadata={
                "collection_method": "web_form",
                "ip_address": "192.168.1.100"
            }
        )
        print(f"Consent recorded: {consent.consent_id}")
        
        # Submit data subject request
        dsr = await compliance.submit_data_subject_request(
            data_subject_id="user_123",
            request_type=DataSubjectRight.ACCESS,
            description="I want to see all data you have about me"
        )
        print(f"DSR submitted: {dsr.request_id}, Due: {dsr.due_date}")
        
        # Record data breach
        breach = await compliance.record_data_breach(
            description="Unauthorized access to transcription database",
            data_categories_affected=[DataCategory.PERSONAL_DATA],
            records_affected=500,
            risk_assessment="high"
        )
        print(f"Breach recorded: {breach.breach_id}")
        print(f"DPA notified: {breach.dpa_notified}")
        
        # Evaluate compliance policies
        violations = await compliance.evaluate_compliance_policies()
        if violations:
            print(f"\nCompliance violations found:")
            for policy_id, policy_violations in violations.items():
                print(f"  {policy_id}: {len(policy_violations)} violations")
        
        # Generate compliance report
        gdpr_report = compliance.generate_compliance_report("GDPR")
        print(f"\nGDPR Compliance Status: {gdpr_report['compliance_status']}")
        
        # Process DSR
        await compliance._process_dsr(dsr)
        print(f"\nDSR completed: {dsr.status}")
        if dsr.response_data:
            print(f"Data collected: {json.dumps(dsr.response_data, indent=2)}")
    
    asyncio.run(main())