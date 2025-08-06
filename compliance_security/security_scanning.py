"""
Security Scanning and Vulnerability Management

Automated security scanning, vulnerability detection, and remediation
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import re
import hashlib
import asyncio
from collections import defaultdict
import subprocess
import json

class ScanType(str, Enum):
    """Types of security scans"""
    STATIC_CODE = "static_code"
    DEPENDENCY = "dependency"
    CONTAINER = "container"
    INFRASTRUCTURE = "infrastructure"
    API = "api"
    CONFIGURATION = "configuration"
    SECRETS = "secrets"
    PENETRATION = "penetration"

class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels (CVSS based)"""
    CRITICAL = "critical"  # 9.0-10.0
    HIGH = "high"         # 7.0-8.9
    MEDIUM = "medium"     # 4.0-6.9
    LOW = "low"           # 0.1-3.9
    INFO = "info"         # 0.0

class RemediationStatus(str, Enum):
    """Remediation status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"  # Risk accepted
    FALSE_POSITIVE = "false_positive"

class Vulnerability(BaseModel):
    """Security vulnerability"""
    vuln_id: str
    scan_id: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Vulnerability details
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: Optional[float]
    cve_id: Optional[str]
    cwe_id: Optional[str]
    
    # Location
    component: str
    file_path: Optional[str]
    line_number: Optional[int]
    
    # Impact
    affected_systems: List[str] = []
    data_at_risk: List[str] = []
    
    # Remediation
    remediation_status: RemediationStatus = RemediationStatus.OPEN
    remediation_steps: List[str] = []
    patch_available: bool = False
    patch_version: Optional[str]
    
    # Risk assessment
    exploitability: str = "medium"  # low, medium, high
    business_impact: str = "medium"
    
    # Tracking
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    resolved_at: Optional[datetime]

class SecurityScan(BaseModel):
    """Security scan record"""
    scan_id: str
    scan_type: ScanType
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime]
    
    # Scan configuration
    target: str
    scan_profile: str = "default"
    
    # Results
    vulnerabilities_found: int = 0
    vulnerabilities_by_severity: Dict[str, int] = Field(default_factory=dict)
    
    # Status
    status: str = "running"  # running, completed, failed
    error_message: Optional[str]

class SecurityPolicy(BaseModel):
    """Security policy definition"""
    policy_id: str
    name: str
    description: str
    
    # Rules
    rules: List[Dict[str, Any]]
    
    # Enforcement
    enforcement_level: str = "block"  # warn, block
    exceptions: List[str] = []
    
    # Status
    is_active: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class ComplianceCheck(BaseModel):
    """Security compliance check"""
    check_id: str
    framework: str  # CIS, NIST, PCI-DSS, etc.
    control_id: str
    description: str
    
    # Check details
    check_type: str
    automated: bool = True
    
    # Results
    status: str = "pending"  # pending, passed, failed
    evidence: List[Dict[str, Any]] = []
    last_checked: Optional[datetime]

class SecurityScanner:
    """Main security scanning service"""
    
    def __init__(self):
        self.scans: Dict[str, SecurityScan] = {}
        self.vulnerabilities: Dict[str, Vulnerability] = {}
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.compliance_checks: Dict[str, ComplianceCheck] = {}
        
        # Vulnerability database (simplified)
        self.vuln_patterns = self._init_vulnerability_patterns()
        
        # Security baselines
        self.security_baselines = self._init_security_baselines()
        
        # Initialize policies
        self._init_default_policies()
    
    def _init_vulnerability_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize vulnerability detection patterns"""
        return {
            "secrets": [
                {
                    "pattern": r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']([^"\']+)["\']',
                    "severity": VulnerabilitySeverity.HIGH,
                    "title": "Hardcoded API Key",
                    "cwe_id": "CWE-798"
                },
                {
                    "pattern": r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\']+)["\']',
                    "severity": VulnerabilitySeverity.CRITICAL,
                    "title": "Hardcoded Password",
                    "cwe_id": "CWE-259"
                },
                {
                    "pattern": r'(?i)aws_access_key_id\s*[:=]\s*["\']([^"\']+)["\']',
                    "severity": VulnerabilitySeverity.CRITICAL,
                    "title": "AWS Access Key Exposed",
                    "cwe_id": "CWE-798"
                }
            ],
            "sql_injection": [
                {
                    "pattern": r'(query|execute)\s*\(\s*["\'].*\+.*["\']',
                    "severity": VulnerabilitySeverity.HIGH,
                    "title": "Potential SQL Injection",
                    "cwe_id": "CWE-89"
                }
            ],
            "xss": [
                {
                    "pattern": r'innerHTML\s*=\s*[^"\']*\+',
                    "severity": VulnerabilitySeverity.HIGH,
                    "title": "Potential XSS Vulnerability",
                    "cwe_id": "CWE-79"
                }
            ],
            "insecure_crypto": [
                {
                    "pattern": r'(?i)(md5|sha1)\s*\(',
                    "severity": VulnerabilitySeverity.MEDIUM,
                    "title": "Weak Cryptographic Algorithm",
                    "cwe_id": "CWE-327"
                }
            ]
        }
    
    def _init_security_baselines(self) -> Dict[str, Dict[str, Any]]:
        """Initialize security baselines"""
        return {
            "tls_configuration": {
                "min_version": "1.2",
                "required_ciphers": [
                    "TLS_AES_256_GCM_SHA384",
                    "TLS_CHACHA20_POLY1305_SHA256"
                ],
                "forbidden_ciphers": ["DES", "3DES", "RC4"]
            },
            "authentication": {
                "min_password_length": 12,
                "require_mfa": True,
                "session_timeout_minutes": 30,
                "max_failed_attempts": 5
            },
            "api_security": {
                "require_authentication": True,
                "rate_limiting": True,
                "require_https": True,
                "cors_enabled": False
            }
        }
    
    def _init_default_policies(self):
        """Initialize default security policies"""
        self.security_policies["no_hardcoded_secrets"] = SecurityPolicy(
            policy_id="no_hardcoded_secrets",
            name="No Hardcoded Secrets",
            description="Prevent hardcoded credentials in code",
            rules=[
                {
                    "type": "pattern_match",
                    "patterns": ["password", "api_key", "secret"],
                    "action": "block"
                }
            ],
            enforcement_level="block"
        )
        
        self.security_policies["secure_dependencies"] = SecurityPolicy(
            policy_id="secure_dependencies",
            name="Secure Dependencies",
            description="No known vulnerabilities in dependencies",
            rules=[
                {
                    "type": "dependency_check",
                    "max_severity": "high",
                    "action": "warn"
                }
            ],
            enforcement_level="warn"
        )
    
    async def run_security_scan(
        self,
        scan_type: ScanType,
        target: str,
        scan_profile: str = "default"
    ) -> SecurityScan:
        """Run security scan"""
        scan = SecurityScan(
            scan_id=f"scan_{datetime.utcnow().timestamp()}",
            scan_type=scan_type,
            target=target,
            scan_profile=scan_profile
        )
        
        self.scans[scan.scan_id] = scan
        
        try:
            # Run appropriate scanner
            if scan_type == ScanType.STATIC_CODE:
                vulnerabilities = await self._run_static_code_scan(target)
            elif scan_type == ScanType.DEPENDENCY:
                vulnerabilities = await self._run_dependency_scan(target)
            elif scan_type == ScanType.SECRETS:
                vulnerabilities = await self._run_secrets_scan(target)
            elif scan_type == ScanType.API:
                vulnerabilities = await self._run_api_scan(target)
            else:
                vulnerabilities = []
            
            # Process results
            for vuln in vulnerabilities:
                vuln.scan_id = scan.scan_id
                self.vulnerabilities[vuln.vuln_id] = vuln
                
                # Update scan statistics
                scan.vulnerabilities_found += 1
                severity = vuln.severity.value
                scan.vulnerabilities_by_severity[severity] = scan.vulnerabilities_by_severity.get(severity, 0) + 1
            
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            
        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
        
        return scan
    
    async def _run_static_code_scan(self, target: str) -> List[Vulnerability]:
        """Run static code analysis"""
        vulnerabilities = []
        
        # Simulate scanning files
        # In production, integrate with tools like Semgrep, SonarQube, etc.
        
        # Example: Check for hardcoded secrets
        for category, patterns in self.vuln_patterns.items():
            for pattern_def in patterns:
                # Simulate finding vulnerability
                if category == "secrets":  # Demo: always find one secret
                    vuln = Vulnerability(
                        vuln_id=f"vuln_{hashlib.sha256(f'{target}{pattern_def["title"]}'.encode()).hexdigest()[:12]}",
                        scan_id="",  # Will be set by caller
                        title=pattern_def["title"],
                        description=f"Found {pattern_def['title']} in source code",
                        severity=pattern_def["severity"],
                        cwe_id=pattern_def.get("cwe_id"),
                        component=target,
                        file_path="config/settings.py",
                        line_number=42,
                        remediation_steps=[
                            "Remove hardcoded secret from code",
                            "Use environment variables or secure key management",
                            "Rotate the exposed credential"
                        ]
                    )
                    vulnerabilities.append(vuln)
                    break
        
        return vulnerabilities
    
    async def _run_dependency_scan(self, target: str) -> List[Vulnerability]:
        """Run dependency vulnerability scan"""
        vulnerabilities = []
        
        # In production, integrate with tools like Safety, Snyk, etc.
        # Simulate finding vulnerable dependency
        
        vuln = Vulnerability(
            vuln_id=f"vuln_dep_{datetime.utcnow().timestamp()}",
            scan_id="",
            title="Vulnerable dependency: requests < 2.28.0",
            description="Known vulnerability in HTTP library",
            severity=VulnerabilitySeverity.HIGH,
            cvss_score=7.5,
            cve_id="CVE-2023-12345",
            component="requests==2.27.1",
            patch_available=True,
            patch_version="2.28.0",
            remediation_steps=[
                "Update requests to version 2.28.0 or higher",
                "Run: pip install --upgrade requests>=2.28.0"
            ]
        )
        vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_secrets_scan(self, target: str) -> List[Vulnerability]:
        """Scan for exposed secrets"""
        vulnerabilities = []
        
        # In production, use tools like TruffleHog, GitLeaks, etc.
        secret_patterns = self.vuln_patterns.get("secrets", [])
        
        for pattern_def in secret_patterns[:1]:  # Demo: find one secret
            vuln = Vulnerability(
                vuln_id=f"vuln_secret_{hashlib.sha256(pattern_def['title'].encode()).hexdigest()[:12]}",
                scan_id="",
                title=f"Exposed Secret: {pattern_def['title']}",
                description="Sensitive credential found in codebase",
                severity=pattern_def["severity"],
                cwe_id=pattern_def.get("cwe_id"),
                component=target,
                file_path=".env.example",
                line_number=5,
                exploitability="high",
                business_impact="high",
                remediation_steps=[
                    "Remove secret from version control",
                    "Rotate the exposed credential immediately",
                    "Use secure secret management solution",
                    "Add file to .gitignore"
                ]
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def _run_api_scan(self, target: str) -> List[Vulnerability]:
        """Run API security scan"""
        vulnerabilities = []
        
        # In production, integrate with tools like OWASP ZAP, Burp Suite, etc.
        # Check for common API vulnerabilities
        
        api_checks = [
            {
                "title": "Missing Rate Limiting",
                "severity": VulnerabilitySeverity.MEDIUM,
                "description": "API endpoint lacks rate limiting",
                "cwe_id": "CWE-770"
            },
            {
                "title": "No Authentication Required",
                "severity": VulnerabilitySeverity.HIGH,
                "description": "API endpoint accessible without authentication",
                "cwe_id": "CWE-306"
            }
        ]
        
        for check in api_checks[:1]:  # Demo: find one issue
            vuln = Vulnerability(
                vuln_id=f"vuln_api_{hashlib.sha256(check['title'].encode()).hexdigest()[:12]}",
                scan_id="",
                title=check["title"],
                description=check["description"],
                severity=check["severity"],
                cwe_id=check["cwe_id"],
                component=f"API: {target}",
                remediation_steps=[
                    "Implement proper authentication",
                    "Add rate limiting middleware",
                    "Review API security configuration"
                ]
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def remediate_vulnerability(
        self,
        vuln_id: str,
        action: str = "patch",
        assigned_to: Optional[str] = None
    ) -> bool:
        """Initiate vulnerability remediation"""
        vuln = self.vulnerabilities.get(vuln_id)
        if not vuln:
            return False
        
        vuln.remediation_status = RemediationStatus.IN_PROGRESS
        vuln.assigned_to = assigned_to
        
        if action == "patch" and vuln.patch_available:
            # In production, automate patching process
            # For demo, simulate patching
            await asyncio.sleep(1)  # Simulate work
            vuln.remediation_status = RemediationStatus.RESOLVED
            vuln.resolved_at = datetime.utcnow()
            return True
        
        elif action == "mitigate":
            # Apply mitigation controls
            vuln.remediation_status = RemediationStatus.MITIGATED
            return True
        
        elif action == "accept":
            # Accept risk
            vuln.remediation_status = RemediationStatus.ACCEPTED
            return True
        
        return False
    
    def assess_security_posture(self) -> Dict[str, Any]:
        """Assess overall security posture"""
        # Count vulnerabilities by status and severity
        vuln_stats = {
            "total": len(self.vulnerabilities),
            "by_severity": defaultdict(int),
            "by_status": defaultdict(int),
            "critical_open": 0,
            "mean_time_to_remediate": None
        }
        
        remediation_times = []
        
        for vuln in self.vulnerabilities.values():
            vuln_stats["by_severity"][vuln.severity.value] += 1
            vuln_stats["by_status"][vuln.remediation_status.value] += 1
            
            if vuln.severity == VulnerabilitySeverity.CRITICAL and vuln.remediation_status == RemediationStatus.OPEN:
                vuln_stats["critical_open"] += 1
            
            if vuln.resolved_at and vuln.detected_at:
                remediation_times.append((vuln.resolved_at - vuln.detected_at).total_seconds() / 86400)  # Days
        
        if remediation_times:
            vuln_stats["mean_time_to_remediate"] = sum(remediation_times) / len(remediation_times)
        
        # Calculate security score (0-100)
        security_score = 100
        
        # Deduct points for vulnerabilities
        severity_weights = {
            VulnerabilitySeverity.CRITICAL: 20,
            VulnerabilitySeverity.HIGH: 10,
            VulnerabilitySeverity.MEDIUM: 5,
            VulnerabilitySeverity.LOW: 2,
            VulnerabilitySeverity.INFO: 0
        }
        
        for vuln in self.vulnerabilities.values():
            if vuln.remediation_status in [RemediationStatus.OPEN, RemediationStatus.IN_PROGRESS]:
                security_score -= severity_weights.get(vuln.severity, 0)
        
        security_score = max(0, security_score)
        
        # Determine posture
        if security_score >= 90:
            posture = "excellent"
        elif security_score >= 70:
            posture = "good"
        elif security_score >= 50:
            posture = "fair"
        else:
            posture = "poor"
        
        return {
            "security_score": security_score,
            "posture": posture,
            "vulnerabilities": dict(vuln_stats),
            "recent_scans": len([s for s in self.scans.values() if s.completed_at and (datetime.utcnow() - s.completed_at).days <= 7]),
            "compliance_status": self._assess_compliance()
        }
    
    def _assess_compliance(self) -> Dict[str, Any]:
        """Assess compliance with security standards"""
        compliance_stats = {
            "frameworks": defaultdict(lambda: {"total": 0, "passed": 0}),
            "overall_compliance": 0
        }
        
        for check in self.compliance_checks.values():
            framework = check.framework
            compliance_stats["frameworks"][framework]["total"] += 1
            if check.status == "passed":
                compliance_stats["frameworks"][framework]["passed"] += 1
        
        # Calculate overall compliance
        total_checks = sum(f["total"] for f in compliance_stats["frameworks"].values())
        passed_checks = sum(f["passed"] for f in compliance_stats["frameworks"].values())
        
        if total_checks > 0:
            compliance_stats["overall_compliance"] = (passed_checks / total_checks) * 100
        
        return dict(compliance_stats)
    
    async def run_compliance_scan(self, framework: str) -> List[ComplianceCheck]:
        """Run compliance scan for specific framework"""
        checks = []
        
        if framework == "CIS":
            # CIS Benchmarks
            cis_checks = [
                ComplianceCheck(
                    check_id=f"cis_1_1",
                    framework="CIS",
                    control_id="1.1",
                    description="Ensure authentication is required for all API endpoints",
                    check_type="api_authentication"
                ),
                ComplianceCheck(
                    check_id=f"cis_2_1",
                    framework="CIS",
                    control_id="2.1",
                    description="Ensure data is encrypted in transit",
                    check_type="encryption_transit"
                )
            ]
            
            for check in cis_checks:
                # Simulate running check
                check.status = "passed" if check.control_id == "2.1" else "failed"
                check.last_checked = datetime.utcnow()
                self.compliance_checks[check.check_id] = check
                checks.append(check)
        
        return checks
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": {},
            "vulnerability_summary": {},
            "compliance_summary": {},
            "recommendations": []
        }
        
        # Get security posture
        posture = self.assess_security_posture()
        
        # Executive summary
        report["executive_summary"] = {
            "security_score": posture["security_score"],
            "posture": posture["posture"],
            "critical_vulnerabilities": posture["vulnerabilities"]["by_severity"].get("critical", 0),
            "high_vulnerabilities": posture["vulnerabilities"]["by_severity"].get("high", 0),
            "open_vulnerabilities": posture["vulnerabilities"]["by_status"].get("open", 0)
        }
        
        # Vulnerability details
        report["vulnerability_summary"] = {
            "total_found": posture["vulnerabilities"]["total"],
            "by_severity": dict(posture["vulnerabilities"]["by_severity"]),
            "by_status": dict(posture["vulnerabilities"]["by_status"]),
            "mean_remediation_time_days": posture["vulnerabilities"]["mean_time_to_remediate"]
        }
        
        # Compliance summary
        report["compliance_summary"] = posture["compliance_status"]
        
        # Generate recommendations
        if posture["vulnerabilities"]["critical_open"] > 0:
            report["recommendations"].append({
                "priority": "critical",
                "recommendation": f"Immediately address {posture['vulnerabilities']['critical_open']} critical vulnerabilities",
                "impact": "Prevents potential security breaches"
            })
        
        if posture["security_score"] < 70:
            report["recommendations"].append({
                "priority": "high",
                "recommendation": "Implement automated security scanning in CI/CD pipeline",
                "impact": "Catch vulnerabilities before production"
            })
        
        # Add specific vulnerability recommendations
        for vuln_id, vuln in list(self.vulnerabilities.items())[:5]:  # Top 5
            if vuln.remediation_status == RemediationStatus.OPEN and vuln.severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]:
                report["recommendations"].append({
                    "priority": vuln.severity.value,
                    "recommendation": f"Fix: {vuln.title}",
                    "impact": vuln.description,
                    "steps": vuln.remediation_steps
                })
        
        return report

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize security scanner
        scanner = SecurityScanner()
        
        # Run different types of scans
        print("Running security scans...")
        
        # Static code analysis
        code_scan = await scanner.run_security_scan(
            ScanType.STATIC_CODE,
            "/app/src"
        )
        print(f"Code scan completed: {code_scan.vulnerabilities_found} vulnerabilities found")
        
        # Dependency scan
        dep_scan = await scanner.run_security_scan(
            ScanType.DEPENDENCY,
            "requirements.txt"
        )
        print(f"Dependency scan completed: {dep_scan.vulnerabilities_found} vulnerabilities found")
        
        # Secrets scan
        secrets_scan = await scanner.run_security_scan(
            ScanType.SECRETS,
            "/app"
        )
        print(f"Secrets scan completed: {secrets_scan.vulnerabilities_found} vulnerabilities found")
        
        # API security scan
        api_scan = await scanner.run_security_scan(
            ScanType.API,
            "https://api.example.com"
        )
        print(f"API scan completed: {api_scan.vulnerabilities_found} vulnerabilities found")
        
        # Assess security posture
        posture = scanner.assess_security_posture()
        print(f"\nSecurity Score: {posture['security_score']}/100")
        print(f"Security Posture: {posture['posture']}")
        print(f"Open Vulnerabilities: {posture['vulnerabilities']['by_status'].get('open', 0)}")
        
        # Remediate a vulnerability
        vulns = list(scanner.vulnerabilities.values())
        if vulns:
            vuln = vulns[0]
            print(f"\nRemediating vulnerability: {vuln.title}")
            success = await scanner.remediate_vulnerability(
                vuln.vuln_id,
                action="patch" if vuln.patch_available else "mitigate"
            )
            print(f"Remediation {'successful' if success else 'failed'}")
        
        # Run compliance scan
        compliance_checks = await scanner.run_compliance_scan("CIS")
        print(f"\nCompliance checks run: {len(compliance_checks)}")
        
        # Generate security report
        report = scanner.generate_security_report()
        print(f"\nSecurity Report Generated:")
        print(f"  Security Score: {report['executive_summary']['security_score']}")
        print(f"  Critical Vulnerabilities: {report['executive_summary']['critical_vulnerabilities']}")
        print(f"  Recommendations: {len(report['recommendations'])}")
        
        for rec in report["recommendations"][:3]:
            print(f"\n  [{rec['priority'].upper()}] {rec['recommendation']}")
            print(f"    Impact: {rec['impact']}")
    
    asyncio.run(main())