"""
Comprehensive Audit Logging and Compliance Reporting

Tracks all system activities for compliance and security audits
"""

from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta, date
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
import hashlib
import uuid
from collections import defaultdict
import asyncio
from dataclasses import dataclass
import re

class EventType(str, Enum):
    """Types of audit events"""
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    MFA_ENABLED = "auth.mfa.enabled"
    MFA_DISABLED = "auth.mfa.disabled"
    PASSWORD_CHANGED = "auth.password.changed"
    
    # Data Access
    DATA_READ = "data.read"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    DATA_SHARED = "data.shared"
    
    # Transcription
    TRANSCRIPTION_STARTED = "transcription.started"
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    TRANSCRIPTION_FAILED = "transcription.failed"
    TRANSCRIPTION_ACCESSED = "transcription.accessed"
    
    # API
    API_KEY_CREATED = "api.key.created"
    API_KEY_REVOKED = "api.key.revoked"
    API_CALL = "api.call"
    API_RATE_LIMITED = "api.rate_limited"
    
    # Security
    PERMISSION_GRANTED = "security.permission.granted"
    PERMISSION_DENIED = "security.permission.denied"
    ROLE_ASSIGNED = "security.role.assigned"
    ROLE_REVOKED = "security.role.revoked"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    
    # Compliance
    DATA_RETENTION_APPLIED = "compliance.retention.applied"
    DATA_PURGED = "compliance.data.purged"
    CONSENT_GRANTED = "compliance.consent.granted"
    CONSENT_REVOKED = "compliance.consent.revoked"
    DATA_SUBJECT_REQUEST = "compliance.dsr"
    
    # System
    SYSTEM_CONFIG_CHANGED = "system.config.changed"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"

class EventSeverity(str, Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComplianceFramework(str, Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    CCPA = "ccpa"
    PCI_DSS = "pci_dss"

class AuditEvent(BaseModel):
    """Audit event record"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Event details
    event_type: EventType
    severity: EventSeverity = EventSeverity.INFO
    description: str
    
    # Actor information
    actor_id: Optional[str]
    actor_type: str = "user"  # user, system, api
    actor_ip: Optional[str]
    actor_user_agent: Optional[str]
    
    # Target information
    target_id: Optional[str]
    target_type: Optional[str]
    target_owner: Optional[str]
    
    # Context
    organization_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    
    # Additional data
    metadata: Dict[str, Any] = {}
    
    # Compliance
    compliance_frameworks: List[ComplianceFramework] = []
    data_classification: Optional[str]
    
    # Security
    risk_score: int = 0  # 0-100
    requires_investigation: bool = False
    
    # Integrity
    event_hash: Optional[str]
    
    def calculate_hash(self) -> str:
        """Calculate event hash for integrity verification"""
        data = f"{self.event_id}{self.timestamp.isoformat()}{self.event_type}{self.actor_id}{self.target_id}"
        return hashlib.sha256(data.encode()).hexdigest()

class AuditRetentionPolicy(BaseModel):
    """Retention policy for audit logs"""
    event_type_pattern: str  # Regex pattern
    retention_days: int
    compliance_framework: Optional[ComplianceFramework]
    
    # Actions
    archive_after_days: Optional[int]
    compress_after_days: Optional[int]
    
    # Conditions
    keep_if_investigation: bool = True
    keep_if_legal_hold: bool = True

class ComplianceReport(BaseModel):
    """Compliance report structure"""
    report_id: str
    framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Summary
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    
    # Compliance metrics
    compliance_score: float  # 0-100
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    
    # Details
    high_risk_events: List[AuditEvent]
    data_access_summary: Dict[str, Any]
    security_incidents: List[Dict[str, Any]]

class AuditLogger:
    """Main audit logging service"""
    
    def __init__(self, storage_backend: Optional[Any] = None):
        self.events: List[AuditEvent] = []
        self.storage_backend = storage_backend
        self.retention_policies: List[AuditRetentionPolicy] = self._init_retention_policies()
        
        # Indexes for fast lookup
        self.events_by_actor: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.events_by_target: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.events_by_type: Dict[EventType, List[AuditEvent]] = defaultdict(list)
        
        # Real-time monitoring
        self.alert_rules: List[Dict[str, Any]] = []
        self.alert_callbacks: List[Any] = []
        
        # Legal holds
        self.legal_holds: Set[str] = set()
    
    def _init_retention_policies(self) -> List[AuditRetentionPolicy]:
        """Initialize default retention policies"""
        return [
            # GDPR compliance
            AuditRetentionPolicy(
                event_type_pattern="auth.*",
                retention_days=365,
                compliance_framework=ComplianceFramework.GDPR,
                archive_after_days=90
            ),
            AuditRetentionPolicy(
                event_type_pattern="data.*",
                retention_days=2555,  # 7 years
                compliance_framework=ComplianceFramework.GDPR,
                archive_after_days=365
            ),
            
            # HIPAA compliance
            AuditRetentionPolicy(
                event_type_pattern=".*",
                retention_days=2190,  # 6 years
                compliance_framework=ComplianceFramework.HIPAA,
                archive_after_days=365
            ),
            
            # SOC2 compliance
            AuditRetentionPolicy(
                event_type_pattern="security.*",
                retention_days=365,
                compliance_framework=ComplianceFramework.SOC2
            ),
            
            # Default
            AuditRetentionPolicy(
                event_type_pattern=".*",
                retention_days=90,
                archive_after_days=30
            )
        ]
    
    async def log_event(
        self,
        event_type: EventType,
        description: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        severity: EventSeverity = EventSeverity.INFO,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditEvent:
        """Log an audit event"""
        event = AuditEvent(
            event_type=event_type,
            description=description,
            severity=severity,
            actor_id=actor_id,
            target_id=target_id,
            metadata=metadata or {},
            **kwargs
        )
        
        # Calculate hash
        event.event_hash = event.calculate_hash()
        
        # Determine compliance frameworks
        event.compliance_frameworks = self._determine_compliance_frameworks(event)
        
        # Calculate risk score
        event.risk_score = self._calculate_risk_score(event)
        
        # Check if investigation needed
        event.requires_investigation = self._check_investigation_needed(event)
        
        # Store event
        self.events.append(event)
        
        # Update indexes
        if actor_id:
            self.events_by_actor[actor_id].append(event)
        if target_id:
            self.events_by_target[target_id].append(event)
        self.events_by_type[event_type].append(event)
        
        # Check alerts
        await self._check_alerts(event)
        
        # Persist to storage
        if self.storage_backend:
            await self._persist_event(event)
        
        return event
    
    def _determine_compliance_frameworks(self, event: AuditEvent) -> List[ComplianceFramework]:
        """Determine applicable compliance frameworks"""
        frameworks = []
        
        # GDPR - Personal data handling
        if any(keyword in event.event_type.value for keyword in ["data", "consent", "dsr"]):
            frameworks.append(ComplianceFramework.GDPR)
        
        # HIPAA - Healthcare data
        if event.metadata.get("contains_phi") or event.data_classification == "phi":
            frameworks.append(ComplianceFramework.HIPAA)
        
        # SOC2 - Security events
        if "security" in event.event_type.value or event.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]:
            frameworks.append(ComplianceFramework.SOC2)
        
        # PCI DSS - Payment data
        if event.metadata.get("contains_payment_data"):
            frameworks.append(ComplianceFramework.PCI_DSS)
        
        return frameworks
    
    def _calculate_risk_score(self, event: AuditEvent) -> int:
        """Calculate risk score for event"""
        score = 0
        
        # Base score by severity
        severity_scores = {
            EventSeverity.INFO: 0,
            EventSeverity.WARNING: 25,
            EventSeverity.ERROR: 50,
            EventSeverity.CRITICAL: 75
        }
        score += severity_scores.get(event.severity, 0)
        
        # Event type risks
        high_risk_events = [
            EventType.DATA_DELETED,
            EventType.DATA_EXPORTED,
            EventType.PERMISSION_DENIED,
            EventType.LOGIN_FAILED,
            EventType.SUSPICIOUS_ACTIVITY
        ]
        
        if event.event_type in high_risk_events:
            score += 25
        
        # Failed authentication attempts
        if event.event_type == EventType.LOGIN_FAILED:
            # Check recent failures
            recent_failures = self._get_recent_login_failures(event.actor_id)
            if len(recent_failures) > 5:
                score = min(100, score + 50)
        
        # Unusual access patterns
        if event.event_type == EventType.DATA_READ:
            if self._is_unusual_access(event):
                score += 30
        
        # Sensitive data
        if event.data_classification in ["restricted", "confidential", "phi"]:
            score += 20
        
        return min(100, score)
    
    def _check_investigation_needed(self, event: AuditEvent) -> bool:
        """Check if event requires investigation"""
        # High risk events
        if event.risk_score >= 70:
            return True
        
        # Critical severity
        if event.severity == EventSeverity.CRITICAL:
            return True
        
        # Specific event types
        investigation_events = [
            EventType.SUSPICIOUS_ACTIVITY,
            EventType.DATA_DELETED,
            EventType.API_KEY_CREATED,
            EventType.ROLE_ASSIGNED
        ]
        
        if event.event_type in investigation_events:
            return True
        
        # Multiple failed logins
        if event.event_type == EventType.LOGIN_FAILED:
            recent_failures = self._get_recent_login_failures(event.actor_id)
            if len(recent_failures) >= 3:
                return True
        
        return False
    
    def _get_recent_login_failures(self, actor_id: Optional[str], minutes: int = 15) -> List[AuditEvent]:
        """Get recent login failures for actor"""
        if not actor_id:
            return []
        
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        return [
            e for e in self.events_by_actor.get(actor_id, [])
            if e.event_type == EventType.LOGIN_FAILED and e.timestamp >= cutoff
        ]
    
    def _is_unusual_access(self, event: AuditEvent) -> bool:
        """Check if data access is unusual"""
        if not event.actor_id or not event.target_id:
            return False
        
        # Check access history
        user_accesses = [
            e for e in self.events_by_actor.get(event.actor_id, [])
            if e.event_type == EventType.DATA_READ
        ]
        
        # First time accessing this type of data
        if not any(e.target_type == event.target_type for e in user_accesses):
            return True
        
        # Unusual time (outside business hours)
        hour = event.timestamp.hour
        if hour < 6 or hour > 22:
            return True
        
        # Unusual location
        if event.actor_ip:
            # Check if IP is different from usual
            usual_ips = set(e.actor_ip for e in user_accesses[-10:] if e.actor_ip)
            if event.actor_ip not in usual_ips:
                return True
        
        return False
    
    async def _check_alerts(self, event: AuditEvent):
        """Check alert rules and trigger notifications"""
        for rule in self.alert_rules:
            if self._match_alert_rule(event, rule):
                for callback in self.alert_callbacks:
                    await callback(event, rule)
    
    def _match_alert_rule(self, event: AuditEvent, rule: Dict[str, Any]) -> bool:
        """Check if event matches alert rule"""
        # Event type pattern
        if "event_pattern" in rule:
            pattern = re.compile(rule["event_pattern"])
            if not pattern.match(event.event_type.value):
                return False
        
        # Severity threshold
        if "min_severity" in rule:
            severities = [EventSeverity.INFO, EventSeverity.WARNING, EventSeverity.ERROR, EventSeverity.CRITICAL]
            event_idx = severities.index(event.severity)
            threshold_idx = severities.index(rule["min_severity"])
            if event_idx < threshold_idx:
                return False
        
        # Risk score threshold
        if "min_risk_score" in rule:
            if event.risk_score < rule["min_risk_score"]:
                return False
        
        return True
    
    async def _persist_event(self, event: AuditEvent):
        """Persist event to storage backend"""
        if self.storage_backend:
            await self.storage_backend.store_event(event.dict())
    
    def search_events(
        self,
        event_types: Optional[List[EventType]] = None,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[EventSeverity] = None,
        requires_investigation: Optional[bool] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """Search audit events"""
        results = self.events
        
        if event_types:
            results = [e for e in results if e.event_type in event_types]
        
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        
        if target_id:
            results = [e for e in results if e.target_id == target_id]
        
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        if severity:
            results = [e for e in results if e.severity == severity]
        
        if requires_investigation is not None:
            results = [e for e in results if e.requires_investigation == requires_investigation]
        
        # Sort by timestamp descending
        results.sort(key=lambda e: e.timestamp, reverse=True)
        
        return results[:limit]
    
    def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """Generate compliance report"""
        # Filter events for period
        period_events = [
            e for e in self.events
            if start_date <= e.timestamp <= end_date and framework in e.compliance_frameworks
        ]
        
        # Calculate statistics
        events_by_type = defaultdict(int)
        events_by_severity = defaultdict(int)
        violations = []
        high_risk_events = []
        
        for event in period_events:
            events_by_type[event.event_type.value] += 1
            events_by_severity[event.severity.value] += 1
            
            if event.risk_score >= 70:
                high_risk_events.append(event)
            
            # Check for violations
            if event.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]:
                violations.append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.description,
                    "risk_score": event.risk_score
                })
        
        # Calculate compliance score
        total_events = len(period_events)
        violation_count = len(violations)
        compliance_score = ((total_events - violation_count) / total_events * 100) if total_events > 0 else 100
        
        # Generate recommendations
        recommendations = self._generate_recommendations(framework, period_events)
        
        # Data access summary
        data_access_summary = self._generate_data_access_summary(period_events)
        
        # Security incidents
        security_incidents = self._identify_security_incidents(period_events)
        
        report = ComplianceReport(
            report_id=f"report_{uuid.uuid4()}",
            framework=framework,
            period_start=start_date,
            period_end=end_date,
            total_events=total_events,
            events_by_type=dict(events_by_type),
            events_by_severity=dict(events_by_severity),
            compliance_score=compliance_score,
            violations=violations,
            recommendations=recommendations,
            high_risk_events=high_risk_events[:10],  # Top 10
            data_access_summary=data_access_summary,
            security_incidents=security_incidents
        )
        
        return report
    
    def _generate_recommendations(
        self,
        framework: ComplianceFramework,
        events: List[AuditEvent]
    ) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Framework-specific recommendations
        if framework == ComplianceFramework.GDPR:
            # Check consent management
            consent_events = [e for e in events if e.event_type in [EventType.CONSENT_GRANTED, EventType.CONSENT_REVOKED]]
            if len(consent_events) == 0:
                recommendations.append("Implement consent tracking for GDPR compliance")
            
            # Check data subject requests
            dsr_events = [e for e in events if e.event_type == EventType.DATA_SUBJECT_REQUEST]
            if len(dsr_events) == 0:
                recommendations.append("Implement data subject request handling procedures")
        
        elif framework == ComplianceFramework.HIPAA:
            # Check encryption
            unencrypted_access = [e for e in events if not e.metadata.get("encrypted", True)]
            if unencrypted_access:
                recommendations.append("Ensure all PHI access is encrypted")
            
            # Check access controls
            unauthorized_attempts = [e for e in events if e.event_type == EventType.PERMISSION_DENIED]
            if len(unauthorized_attempts) > 10:
                recommendations.append("Review and strengthen access control policies")
        
        elif framework == ComplianceFramework.SOC2:
            # Check security monitoring
            security_events = [e for e in events if "security" in e.event_type.value]
            if len(security_events) < 10:
                recommendations.append("Increase security event monitoring coverage")
            
            # Check incident response
            unresolved_incidents = [e for e in events if e.requires_investigation and not e.metadata.get("resolved")]
            if unresolved_incidents:
                recommendations.append(f"Address {len(unresolved_incidents)} unresolved security incidents")
        
        # General recommendations
        high_risk_events = [e for e in events if e.risk_score >= 70]
        if len(high_risk_events) > 50:
            recommendations.append("Implement additional controls to reduce high-risk activities")
        
        failed_logins = [e for e in events if e.event_type == EventType.LOGIN_FAILED]
        if len(failed_logins) > 100:
            recommendations.append("Consider implementing additional authentication controls")
        
        return recommendations
    
    def _generate_data_access_summary(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate data access summary"""
        data_events = [e for e in events if e.event_type in [
            EventType.DATA_READ, EventType.DATA_CREATED,
            EventType.DATA_UPDATED, EventType.DATA_DELETED
        ]]
        
        summary = {
            "total_accesses": len(data_events),
            "unique_users": len(set(e.actor_id for e in data_events if e.actor_id)),
            "by_operation": defaultdict(int),
            "by_classification": defaultdict(int),
            "sensitive_data_access": []
        }
        
        for event in data_events:
            operation = event.event_type.value.split(".")[-1]
            summary["by_operation"][operation] += 1
            
            if event.data_classification:
                summary["by_classification"][event.data_classification] += 1
            
            if event.data_classification in ["restricted", "confidential", "phi"]:
                summary["sensitive_data_access"].append({
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor_id,
                    "target": event.target_id,
                    "classification": event.data_classification
                })
        
        summary["by_operation"] = dict(summary["by_operation"])
        summary["by_classification"] = dict(summary["by_classification"])
        summary["sensitive_data_access"] = summary["sensitive_data_access"][:20]  # Top 20
        
        return summary
    
    def _identify_security_incidents(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """Identify security incidents from events"""
        incidents = []
        
        # Group related events
        suspicious_events = [e for e in events if e.risk_score >= 60 or e.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]]
        
        # Simple incident detection (in production, use more sophisticated correlation)
        for event in suspicious_events:
            if event.event_type == EventType.LOGIN_FAILED:
                # Check for brute force
                actor_failures = [
                    e for e in events
                    if e.actor_id == event.actor_id and e.event_type == EventType.LOGIN_FAILED
                    and abs((e.timestamp - event.timestamp).total_seconds()) < 300  # 5 minutes
                ]
                
                if len(actor_failures) >= 5:
                    incidents.append({
                        "type": "brute_force_attempt",
                        "severity": "high",
                        "actor": event.actor_id,
                        "timestamp": event.timestamp.isoformat(),
                        "details": f"{len(actor_failures)} failed login attempts in 5 minutes"
                    })
            
            elif event.event_type == EventType.DATA_EXPORTED:
                # Check for data exfiltration
                actor_exports = [
                    e for e in events
                    if e.actor_id == event.actor_id and e.event_type == EventType.DATA_EXPORTED
                    and (event.timestamp - e.timestamp).days == 0  # Same day
                ]
                
                if len(actor_exports) > 10:
                    incidents.append({
                        "type": "potential_data_exfiltration",
                        "severity": "critical",
                        "actor": event.actor_id,
                        "timestamp": event.timestamp.isoformat(),
                        "details": f"{len(actor_exports)} data exports in one day"
                    })
        
        return incidents[:10]  # Top 10 incidents
    
    def apply_retention_policies(self) -> Dict[str, int]:
        """Apply retention policies to audit logs"""
        now = datetime.utcnow()
        stats = {
            "archived": 0,
            "deleted": 0,
            "retained": 0
        }
        
        events_to_remove = []
        
        for event in self.events:
            # Skip if under legal hold
            if event.event_id in self.legal_holds:
                stats["retained"] += 1
                continue
            
            # Find applicable retention policy
            policy = self._find_retention_policy(event)
            if not policy:
                continue
            
            event_age_days = (now - event.timestamp).days
            
            # Check if should be deleted
            if event_age_days > policy.retention_days:
                if not (policy.keep_if_investigation and event.requires_investigation):
                    events_to_remove.append(event)
                    stats["deleted"] += 1
                else:
                    stats["retained"] += 1
            
            # Check if should be archived
            elif policy.archive_after_days and event_age_days > policy.archive_after_days:
                # In production, move to archive storage
                stats["archived"] += 1
        
        # Remove events
        for event in events_to_remove:
            self.events.remove(event)
            # Clean up indexes
            if event.actor_id and event in self.events_by_actor[event.actor_id]:
                self.events_by_actor[event.actor_id].remove(event)
            if event.target_id and event in self.events_by_target[event.target_id]:
                self.events_by_target[event.target_id].remove(event)
            if event in self.events_by_type[event.event_type]:
                self.events_by_type[event.event_type].remove(event)
        
        return stats
    
    def _find_retention_policy(self, event: AuditEvent) -> Optional[AuditRetentionPolicy]:
        """Find applicable retention policy for event"""
        for policy in self.retention_policies:
            pattern = re.compile(policy.event_type_pattern)
            if pattern.match(event.event_type.value):
                # Check if compliance framework matches
                if policy.compliance_framework:
                    if policy.compliance_framework not in event.compliance_frameworks:
                        continue
                return policy
        return None
    
    def add_legal_hold(self, event_ids: List[str]):
        """Add legal hold to prevent deletion"""
        self.legal_holds.update(event_ids)
    
    def remove_legal_hold(self, event_ids: List[str]):
        """Remove legal hold"""
        for event_id in event_ids:
            self.legal_holds.discard(event_id)
    
    def export_audit_trail(
        self,
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> Union[str, bytes]:
        """Export audit trail for external review"""
        events = self.search_events(**(filters or {}))
        
        if format == "json":
            return json.dumps([e.dict() for e in events], indent=2, default=str)
        
        elif format == "csv":
            # Simplified CSV export
            lines = ["timestamp,event_type,actor_id,target_id,severity,description"]
            for event in events:
                lines.append(
                    f"{event.timestamp.isoformat()},{event.event_type.value},"
                    f"{event.actor_id or ''},{event.target_id or ''},"
                    f"{event.severity.value},{event.description}"
                )
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize audit logger
        logger = AuditLogger()
        
        # Configure alert rule
        logger.alert_rules.append({
            "name": "Failed Login Alert",
            "event_pattern": "auth.login.failed",
            "min_risk_score": 50
        })
        
        # Log some events
        await logger.log_event(
            EventType.LOGIN_SUCCESS,
            "User logged in successfully",
            actor_id="user_123",
            actor_ip="192.168.1.100",
            organization_id="org_abc"
        )
        
        # Failed login attempts
        for i in range(5):
            await logger.log_event(
                EventType.LOGIN_FAILED,
                f"Failed login attempt {i+1}",
                actor_id="user_456",
                actor_ip="10.0.0.50",
                severity=EventSeverity.WARNING
            )
        
        # Data access
        await logger.log_event(
            EventType.DATA_READ,
            "Accessed sensitive transcription",
            actor_id="user_123",
            target_id="trans_789",
            target_type="transcription",
            data_classification="confidential",
            metadata={"file_size": 1024000, "contains_pii": True}
        )
        
        # Generate compliance report
        report = logger.generate_compliance_report(
            ComplianceFramework.SOC2,
            datetime.utcnow() - timedelta(days=30),
            datetime.utcnow()
        )
        
        print(f"Compliance Score: {report.compliance_score:.1f}%")
        print(f"Total Events: {report.total_events}")
        print(f"Violations: {len(report.violations)}")
        print(f"Recommendations: {len(report.recommendations)}")
        
        # Search events
        investigation_events = logger.search_events(
            requires_investigation=True,
            limit=10
        )
        
        print(f"\nEvents requiring investigation: {len(investigation_events)}")
        for event in investigation_events:
            print(f"  - {event.event_type.value}: {event.description} (Risk: {event.risk_score})")
        
        # Apply retention
        retention_stats = logger.apply_retention_policies()
        print(f"\nRetention applied: {retention_stats}")
        
        # Export audit trail
        audit_export = logger.export_audit_trail(format="json", filters={"severity": EventSeverity.WARNING})
        print(f"\nExported {len(json.loads(audit_export))} warning/error events")
    
    asyncio.run(main())