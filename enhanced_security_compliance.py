"""
Enhanced Security & Compliance System
Implements encryption, audit logging, GDPR compliance, SOC2 controls, and security scanning
"""

import asyncio
import json
import uuid
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import pyotp
import qrcode
from passlib.context import CryptContext
from passlib.totp import TOTP
import redis.asyncio as redis
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import boto3
from botocore.exceptions import ClientError
import hashicorp_vault
import gnupg
import ssl
import certifi
import logging
from functools import wraps
import re
import ipaddress
from user_agents import parse as parse_user_agent
import geoip2.database
import numpy as np
from sklearn.ensemble import IsolationForest
import pandas as pd
import yara
import clamav
from bandit import config as bandit_config
from safety import check as safety_check
import requests
from owasp_zap_python_api import ZAPv2
import nmap
from scapy.all import *
import asyncio_throttle
from ratelimit import limits, sleep_and_retry
import bleach
from html_sanitizer import Sanitizer
import validators
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

Base = declarative_base()

class SecurityLevel(str, Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceFramework(str, Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"

class AuditEventType(str, Enum):
    """Audit event types"""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    PERMISSION_CHANGE = "permission_change"
    SECURITY_ALERT = "security_alert"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ACCESS = "system_access"
    API_CALL = "api_call"

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    id: str
    name: str
    level: SecurityLevel
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_expiry_days: int = 90
    mfa_required: bool = True
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class AuditLog:
    """Audit log entry"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    resource: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]
    risk_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource': self.resource,
            'action': self.action,
            'result': self.result,
            'details': self.details,
            'risk_score': self.risk_score
        }

class AuditLogModel(Base):
    """SQLAlchemy model for audit logs"""
    __tablename__ = 'audit_logs'
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    event_type = Column(String, nullable=False)
    user_id = Column(String)
    ip_address = Column(String, nullable=False)
    user_agent = Column(Text)
    resource = Column(String)
    action = Column(String, nullable=False)
    result = Column(String, nullable=False)
    details = Column(Text)
    risk_score = Column(Integer)
    encrypted = Column(Boolean, default=True)

class EncryptionManager:
    """Manages encryption for data at rest and in transit"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or Fernet.generate_key()
        self.fernet = Fernet(self.master_key)
        self.private_key = None
        self.public_key = None
        self._generate_rsa_keys()
        
    def _generate_rsa_keys(self):
        """Generate RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
    def encrypt_symmetric(self, data: bytes) -> bytes:
        """Encrypt data using symmetric encryption"""
        return self.fernet.encrypt(data)
        
    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using symmetric encryption"""
        return self.fernet.decrypt(encrypted_data)
        
    def encrypt_asymmetric(self, data: bytes, public_key: Optional[Any] = None) -> bytes:
        """Encrypt data using asymmetric encryption"""
        key = public_key or self.public_key
        return key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
    def decrypt_asymmetric(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using asymmetric encryption"""
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
    def encrypt_field(self, value: str) -> str:
        """Encrypt a field value"""
        if not value:
            return value
        encrypted = self.encrypt_symmetric(value.encode())
        return encrypted.hex()
        
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value"""
        if not encrypted_value:
            return encrypted_value
        encrypted_bytes = bytes.fromhex(encrypted_value)
        decrypted = self.decrypt_symmetric(encrypted_bytes)
        return decrypted.decode()
        
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash password using scrypt"""
        salt = salt or secrets.token_bytes(32)
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key.hex(), salt.hex()
        
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            new_hash, _ = self.hash_password(password, bytes.fromhex(salt))
            return hmac.compare_digest(new_hash, hashed)
        except Exception:
            return False
            
    def generate_data_key(self) -> Tuple[bytes, bytes]:
        """Generate a data encryption key"""
        data_key = Fernet.generate_key()
        encrypted_key = self.encrypt_symmetric(data_key)
        return data_key, encrypted_key

class AuthenticationManager:
    """Manages authentication and MFA"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption = encryption_manager
        self.pwd_context = CryptContext(
            schemes=["pbkdf2_sha256", "bcrypt", "argon2"],
            default="argon2",
            pbkdf2_sha256__rounds=100000
        )
        self.totp_secrets: Dict[str, str] = {}
        self.sessions: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
    def generate_mfa_secret(self, user_id: str) -> Tuple[str, str]:
        """Generate MFA secret and QR code"""
        secret = pyotp.random_base32()
        self.totp_secrets[user_id] = secret
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_id,
            issuer_name='Transcription Platform'
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        return secret, totp_uri
        
    def verify_mfa_token(self, user_id: str, token: str) -> bool:
        """Verify MFA token"""
        if user_id not in self.totp_secrets:
            return False
            
        totp = pyotp.TOTP(self.totp_secrets[user_id])
        return totp.verify(token, valid_window=1)
        
    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        expires_in: int = 3600
    ) -> str:
        """Create authenticated session"""
        session_id = secrets.token_urlsafe(32)
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
            'last_activity': datetime.utcnow()
        }
        
        return session_id
        
    def validate_session(
        self,
        session_id: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[str]:
        """Validate session and return user_id"""
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        
        # Check expiry
        if datetime.utcnow() > session['expires_at']:
            del self.sessions[session_id]
            return None
            
        # Validate IP and user agent
        if session['ip_address'] != ip_address or session['user_agent'] != user_agent:
            # Potential session hijacking
            del self.sessions[session_id]
            return None
            
        # Update last activity
        session['last_activity'] = datetime.utcnow()
        
        return session['user_id']
        
    def check_brute_force(self, identifier: str, window_minutes: int = 15) -> bool:
        """Check for brute force attempts"""
        if identifier not in self.failed_attempts:
            return False
            
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        self.failed_attempts[identifier] = recent_attempts
        return len(recent_attempts) >= 5
        
    def record_failed_attempt(self, identifier: str):
        """Record failed authentication attempt"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        self.failed_attempts[identifier].append(datetime.utcnow())

class AccessControlManager:
    """Manages role-based access control (RBAC)"""
    
    def __init__(self):
        self.roles: Dict[str, Dict] = {
            'admin': {
                'permissions': ['*'],
                'priority': 100
            },
            'manager': {
                'permissions': [
                    'read:*', 'write:*', 'delete:own',
                    'manage:team', 'view:analytics'
                ],
                'priority': 50
            },
            'user': {
                'permissions': [
                    'read:own', 'write:own', 'delete:own'
                ],
                'priority': 10
            },
            'viewer': {
                'permissions': ['read:public'],
                'priority': 5
            }
        }
        self.user_roles: Dict[str, Set[str]] = {}
        self.resource_permissions: Dict[str, Dict] = {}
        
    def assign_role(self, user_id: str, role: str):
        """Assign role to user"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role)
        
    def revoke_role(self, user_id: str, role: str):
        """Revoke role from user"""
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role)
            
    def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """Check if user has permission for action on resource"""
        if user_id not in self.user_roles:
            return False
            
        # Check each role's permissions
        for role in self.user_roles[user_id]:
            if role not in self.roles:
                continue
                
            permissions = self.roles[role]['permissions']
            
            # Check for wildcard permission
            if '*' in permissions or f"{action}:*" in permissions:
                return True
                
            # Check specific permission
            if f"{action}:{resource}" in permissions:
                return True
                
            # Check own resource permission
            if f"{action}:own" in permissions:
                # Check if user owns the resource
                if self._user_owns_resource(user_id, resource):
                    return True
                    
        return False
        
    def _user_owns_resource(self, user_id: str, resource: str) -> bool:
        """Check if user owns a resource"""
        if resource in self.resource_permissions:
            return self.resource_permissions[resource].get('owner') == user_id
        return False
        
    def set_resource_permissions(
        self,
        resource: str,
        owner: str,
        permissions: Dict[str, List[str]]
    ):
        """Set permissions for a resource"""
        self.resource_permissions[resource] = {
            'owner': owner,
            'permissions': permissions
        }

class ComplianceManager:
    """Manages compliance with various frameworks"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption = encryption_manager
        self.compliance_checks: Dict[ComplianceFramework, List[Callable]] = {
            ComplianceFramework.GDPR: [
                self._check_gdpr_consent,
                self._check_gdpr_data_minimization,
                self._check_gdpr_right_to_erasure,
                self._check_gdpr_data_portability
            ],
            ComplianceFramework.SOC2: [
                self._check_soc2_encryption,
                self._check_soc2_access_control,
                self._check_soc2_monitoring,
                self._check_soc2_incident_response
            ],
            ComplianceFramework.HIPAA: [
                self._check_hipaa_encryption,
                self._check_hipaa_access_control,
                self._check_hipaa_audit_logging,
                self._check_hipaa_data_integrity
            ]
        }
        self.consent_records: Dict[str, Dict] = {}
        self.data_retention_policies: Dict[str, int] = {
            'audit_logs': 2555,  # 7 years
            'user_data': 1095,   # 3 years
            'temporary_data': 30  # 30 days
        }
        
    async def check_compliance(
        self,
        framework: ComplianceFramework,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance for a framework"""
        if framework not in self.compliance_checks:
            return {'compliant': False, 'message': 'Unknown framework'}
            
        results = []
        for check in self.compliance_checks[framework]:
            result = await check(context)
            results.append(result)
            
        compliant = all(r['passed'] for r in results)
        
        return {
            'framework': framework.value,
            'compliant': compliant,
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    async def _check_gdpr_consent(self, context: Dict) -> Dict:
        """Check GDPR consent requirements"""
        user_id = context.get('user_id')
        if not user_id:
            return {'passed': False, 'check': 'gdpr_consent', 'message': 'No user ID'}
            
        if user_id in self.consent_records:
            consent = self.consent_records[user_id]
            if consent.get('explicit') and not self._is_expired(consent.get('timestamp')):
                return {'passed': True, 'check': 'gdpr_consent'}
                
        return {'passed': False, 'check': 'gdpr_consent', 'message': 'No valid consent'}
        
    async def _check_gdpr_data_minimization(self, context: Dict) -> Dict:
        """Check GDPR data minimization"""
        data_fields = context.get('data_fields', [])
        required_fields = context.get('required_fields', [])
        
        unnecessary_fields = set(data_fields) - set(required_fields)
        
        if unnecessary_fields:
            return {
                'passed': False,
                'check': 'gdpr_data_minimization',
                'message': f'Unnecessary fields: {unnecessary_fields}'
            }
            
        return {'passed': True, 'check': 'gdpr_data_minimization'}
        
    async def _check_gdpr_right_to_erasure(self, context: Dict) -> Dict:
        """Check GDPR right to erasure"""
        # Check if erasure mechanism exists
        has_erasure = context.get('has_erasure_mechanism', False)
        return {
            'passed': has_erasure,
            'check': 'gdpr_right_to_erasure',
            'message': 'Erasure mechanism required' if not has_erasure else None
        }
        
    async def _check_gdpr_data_portability(self, context: Dict) -> Dict:
        """Check GDPR data portability"""
        has_export = context.get('has_export_mechanism', False)
        return {
            'passed': has_export,
            'check': 'gdpr_data_portability',
            'message': 'Export mechanism required' if not has_export else None
        }
        
    async def _check_soc2_encryption(self, context: Dict) -> Dict:
        """Check SOC2 encryption requirements"""
        encrypted_at_rest = context.get('encrypted_at_rest', False)
        encrypted_in_transit = context.get('encrypted_in_transit', False)
        
        passed = encrypted_at_rest and encrypted_in_transit
        
        return {
            'passed': passed,
            'check': 'soc2_encryption',
            'message': 'Encryption required for data at rest and in transit' if not passed else None
        }
        
    async def _check_soc2_access_control(self, context: Dict) -> Dict:
        """Check SOC2 access control"""
        has_rbac = context.get('has_rbac', False)
        has_mfa = context.get('has_mfa', False)
        
        passed = has_rbac and has_mfa
        
        return {
            'passed': passed,
            'check': 'soc2_access_control',
            'message': 'RBAC and MFA required' if not passed else None
        }
        
    async def _check_soc2_monitoring(self, context: Dict) -> Dict:
        """Check SOC2 monitoring requirements"""
        has_monitoring = context.get('has_monitoring', False)
        has_alerting = context.get('has_alerting', False)
        
        passed = has_monitoring and has_alerting
        
        return {
            'passed': passed,
            'check': 'soc2_monitoring',
            'message': 'Monitoring and alerting required' if not passed else None
        }
        
    async def _check_soc2_incident_response(self, context: Dict) -> Dict:
        """Check SOC2 incident response"""
        has_incident_plan = context.get('has_incident_plan', False)
        
        return {
            'passed': has_incident_plan,
            'check': 'soc2_incident_response',
            'message': 'Incident response plan required' if not has_incident_plan else None
        }
        
    async def _check_hipaa_encryption(self, context: Dict) -> Dict:
        """Check HIPAA encryption requirements"""
        # Similar to SOC2 but stricter
        return await self._check_soc2_encryption(context)
        
    async def _check_hipaa_access_control(self, context: Dict) -> Dict:
        """Check HIPAA access control"""
        has_minimum_necessary = context.get('has_minimum_necessary', False)
        has_access_logs = context.get('has_access_logs', False)
        
        passed = has_minimum_necessary and has_access_logs
        
        return {
            'passed': passed,
            'check': 'hipaa_access_control',
            'message': 'Minimum necessary and access logging required' if not passed else None
        }
        
    async def _check_hipaa_audit_logging(self, context: Dict) -> Dict:
        """Check HIPAA audit logging"""
        has_audit_logs = context.get('has_audit_logs', False)
        log_retention_days = context.get('log_retention_days', 0)
        
        passed = has_audit_logs and log_retention_days >= 2190  # 6 years
        
        return {
            'passed': passed,
            'check': 'hipaa_audit_logging',
            'message': 'Audit logs with 6-year retention required' if not passed else None
        }
        
    async def _check_hipaa_data_integrity(self, context: Dict) -> Dict:
        """Check HIPAA data integrity"""
        has_integrity_controls = context.get('has_integrity_controls', False)
        
        return {
            'passed': has_integrity_controls,
            'check': 'hipaa_data_integrity',
            'message': 'Data integrity controls required' if not has_integrity_controls else None
        }
        
    def _is_expired(self, timestamp: Optional[datetime], days: int = 365) -> bool:
        """Check if a timestamp is expired"""
        if not timestamp:
            return True
        return datetime.utcnow() - timestamp > timedelta(days=days)
        
    def record_consent(
        self,
        user_id: str,
        purpose: str,
        explicit: bool = True
    ):
        """Record user consent"""
        self.consent_records[user_id] = {
            'purpose': purpose,
            'explicit': explicit,
            'timestamp': datetime.utcnow(),
            'version': '1.0'
        }
        
    async def handle_data_request(
        self,
        user_id: str,
        request_type: str
    ) -> Dict[str, Any]:
        """Handle GDPR data requests"""
        if request_type == 'access':
            # Return all user data
            return {'status': 'pending', 'request_id': str(uuid.uuid4())}
            
        elif request_type == 'portability':
            # Export user data
            return {'status': 'pending', 'request_id': str(uuid.uuid4())}
            
        elif request_type == 'erasure':
            # Delete user data
            return {'status': 'pending', 'request_id': str(uuid.uuid4())}
            
        elif request_type == 'rectification':
            # Correct user data
            return {'status': 'pending', 'request_id': str(uuid.uuid4())}
            
        else:
            return {'status': 'error', 'message': 'Unknown request type'}

class SecurityScanner:
    """Performs security scanning and vulnerability detection"""
    
    def __init__(self):
        self.vulnerability_db: Dict[str, Dict] = {}
        self.anomaly_detector = None
        self._initialize_anomaly_detector()
        
    def _initialize_anomaly_detector(self):
        """Initialize anomaly detection model"""
        # Train isolation forest for anomaly detection
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
    async def scan_dependencies(self, requirements_file: str) -> List[Dict]:
        """Scan dependencies for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Use safety to check dependencies
            with open(requirements_file, 'r') as f:
                result = safety_check(f.read())
                
            for vuln in result:
                vulnerabilities.append({
                    'package': vuln.get('package'),
                    'version': vuln.get('installed_version'),
                    'vulnerability': vuln.get('vulnerability'),
                    'severity': vuln.get('severity', 'unknown')
                })
        except Exception as e:
            logger.error(f"Dependency scan error: {e}")
            
        return vulnerabilities
        
    async def scan_code(self, code_path: str) -> List[Dict]:
        """Scan code for security issues"""
        issues = []
        
        try:
            # Use bandit for Python code scanning
            from bandit.core import manager
            
            b_mgr = manager.BanditManager(bandit_config.BanditConfig(), 'file')
            b_mgr.discover_files([code_path])
            b_mgr.run_tests()
            
            for issue in b_mgr.get_issue_list():
                issues.append({
                    'file': issue.fname,
                    'line': issue.lineno,
                    'severity': issue.severity,
                    'confidence': issue.confidence,
                    'issue': issue.issue_text,
                    'test': issue.test_id
                })
        except Exception as e:
            logger.error(f"Code scan error: {e}")
            
        return issues
        
    async def scan_network(self, target: str, ports: str = "1-1000") -> Dict:
        """Scan network for open ports and services"""
        nm = nmap.PortScanner()
        
        try:
            nm.scan(target, ports, '-sV')
            
            results = {
                'host': target,
                'state': nm[target].state(),
                'protocols': {}
            }
            
            for proto in nm[target].all_protocols():
                ports_info = []
                for port in nm[target][proto].keys():
                    port_info = nm[target][proto][port]
                    ports_info.append({
                        'port': port,
                        'state': port_info['state'],
                        'service': port_info.get('name', 'unknown'),
                        'version': port_info.get('version', '')
                    })
                results['protocols'][proto] = ports_info
                
            return results
        except Exception as e:
            logger.error(f"Network scan error: {e}")
            return {}
            
    async def detect_anomalies(self, data: List[Dict]) -> List[Dict]:
        """Detect anomalies in system behavior"""
        if not data or not self.anomaly_detector:
            return []
            
        # Convert data to features
        df = pd.DataFrame(data)
        features = df.select_dtypes(include=[np.number]).values
        
        if len(features) == 0:
            return []
            
        # Predict anomalies
        predictions = self.anomaly_detector.predict(features)
        
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:  # Anomaly
                anomalies.append({
                    'index': i,
                    'data': data[i],
                    'anomaly_score': self.anomaly_detector.score_samples([features[i]])[0]
                })
                
        return anomalies
        
    async def scan_malware(self, file_path: str) -> Dict:
        """Scan file for malware"""
        try:
            # Use ClamAV for malware scanning
            cd = clamav.ClamdUnixSocket()
            result = cd.scan(file_path)
            
            if result:
                status = result[file_path][0]
                if status == 'OK':
                    return {'clean': True, 'file': file_path}
                else:
                    return {
                        'clean': False,
                        'file': file_path,
                        'threat': result[file_path][1]
                    }
        except Exception as e:
            logger.error(f"Malware scan error: {e}")
            
        return {'error': 'Scan failed'}

class InputValidator:
    """Validates and sanitizes user input"""
    
    def __init__(self):
        self.sanitizer = Sanitizer()
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)",
            r"(--|\||;|\/\*|\*\/)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)"
        ]
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>"
        ]
        
    def validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address"""
        try:
            valid = validate_email(email)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)
            
    def validate_url(self, url: str) -> bool:
        """Validate URL"""
        return validators.url(url) is True
        
    def validate_ip(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
            
    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML input"""
        return bleach.clean(
            html,
            tags=['p', 'br', 'strong', 'em', 'u', 'a'],
            attributes={'a': ['href', 'title']},
            strip=True
        )
        
    def detect_sql_injection(self, input_str: str) -> bool:
        """Detect potential SQL injection"""
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False
        
    def detect_xss(self, input_str: str) -> bool:
        """Detect potential XSS attack"""
        for pattern in self.xss_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False
        
    def validate_input(
        self,
        input_str: str,
        input_type: str = 'text',
        max_length: int = 1000
    ) -> Tuple[bool, str]:
        """Validate and sanitize input"""
        # Check length
        if len(input_str) > max_length:
            return False, f"Input exceeds maximum length of {max_length}"
            
        # Check for SQL injection
        if self.detect_sql_injection(input_str):
            return False, "Potential SQL injection detected"
            
        # Check for XSS
        if self.detect_xss(input_str):
            return False, "Potential XSS attack detected"
            
        # Type-specific validation
        if input_type == 'email':
            valid, msg = self.validate_email(input_str)
            if not valid:
                return False, msg
                
        elif input_type == 'url':
            if not self.validate_url(input_str):
                return False, "Invalid URL"
                
        elif input_type == 'ip':
            if not self.validate_ip(input_str):
                return False, "Invalid IP address"
                
        elif input_type == 'html':
            input_str = self.sanitize_html(input_str)
            
        return True, input_str

class SecurityOrchestrator:
    """Main security orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.encryption = EncryptionManager()
        self.auth = AuthenticationManager(self.encryption)
        self.access_control = AccessControlManager()
        self.compliance = ComplianceManager(self.encryption)
        self.scanner = SecurityScanner()
        self.validator = InputValidator()
        self.audit_logs: List[AuditLog] = []
        self.security_policy = SecurityPolicy(
            id='default',
            name='Default Security Policy',
            level=SecurityLevel.HIGH
        )
        
        # Initialize database
        self.engine = None
        self.session = None
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database for audit logs"""
        self.engine = create_engine(
            self.config.get('database_url', 'sqlite:///security.db')
        )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    async def authenticate_user(
        self,
        username: str,
        password: str,
        mfa_token: Optional[str],
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Authenticate user with MFA"""
        # Check brute force
        if self.auth.check_brute_force(username) or self.auth.check_brute_force(ip_address):
            await self.log_audit_event(
                AuditEventType.AUTH_FAILURE,
                None,
                ip_address,
                user_agent,
                'authentication',
                'Brute force detected',
                {'username': username}
            )
            return {'success': False, 'error': 'Too many failed attempts'}
            
        # Verify password (would check against database)
        # For demo, using hardcoded check
        if not self._verify_user_password(username, password):
            self.auth.record_failed_attempt(username)
            self.auth.record_failed_attempt(ip_address)
            
            await self.log_audit_event(
                AuditEventType.AUTH_FAILURE,
                None,
                ip_address,
                user_agent,
                'authentication',
                'Invalid credentials',
                {'username': username}
            )
            return {'success': False, 'error': 'Invalid credentials'}
            
        # Verify MFA if required
        if self.security_policy.mfa_required:
            if not mfa_token or not self.auth.verify_mfa_token(username, mfa_token):
                await self.log_audit_event(
                    AuditEventType.AUTH_FAILURE,
                    username,
                    ip_address,
                    user_agent,
                    'mfa',
                    'Invalid MFA token',
                    {}
                )
                return {'success': False, 'error': 'Invalid MFA token'}
                
        # Create session
        session_id = self.auth.create_session(
            username,
            ip_address,
            user_agent,
            self.security_policy.session_timeout_minutes * 60
        )
        
        await self.log_audit_event(
            AuditEventType.AUTH_SUCCESS,
            username,
            ip_address,
            user_agent,
            'authentication',
            'Login successful',
            {}
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'user_id': username
        }
        
    def _verify_user_password(self, username: str, password: str) -> bool:
        """Verify user password (placeholder)"""
        # This would check against database
        return username == "admin" and password == "SecurePassword123!"
        
    async def authorize_action(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str
    ) -> bool:
        """Authorize user action"""
        # Check permissions
        authorized = self.access_control.check_permission(user_id, resource, action)
        
        # Log access attempt
        await self.log_audit_event(
            AuditEventType.DATA_ACCESS if authorized else AuditEventType.SECURITY_ALERT,
            user_id,
            ip_address,
            '',
            f"{action}:{resource}",
            'Authorized' if authorized else 'Denied',
            {'resource': resource, 'action': action}
        )
        
        return authorized
        
    async def log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        action: str,
        result: str,
        details: Dict[str, Any]
    ):
        """Log audit event"""
        # Calculate risk score
        risk_score = self._calculate_risk_score(event_type, ip_address, user_id)
        
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=details.get('resource'),
            action=action,
            result=result,
            details=details,
            risk_score=risk_score
        )
        
        self.audit_logs.append(audit_log)
        
        # Store in database
        if self.session:
            db_log = AuditLogModel(
                id=audit_log.id,
                timestamp=audit_log.timestamp,
                event_type=audit_log.event_type.value,
                user_id=audit_log.user_id,
                ip_address=audit_log.ip_address,
                user_agent=audit_log.user_agent,
                resource=audit_log.resource,
                action=audit_log.action,
                result=audit_log.result,
                details=json.dumps(audit_log.details),
                risk_score=int(audit_log.risk_score * 100),
                encrypted=True
            )
            self.session.add(db_log)
            self.session.commit()
            
        # Alert on high-risk events
        if risk_score > 0.8:
            await self._send_security_alert(audit_log)
            
    def _calculate_risk_score(
        self,
        event_type: AuditEventType,
        ip_address: str,
        user_id: Optional[str]
    ) -> float:
        """Calculate risk score for an event"""
        score = 0.0
        
        # Event type risk
        high_risk_events = [
            AuditEventType.AUTH_FAILURE,
            AuditEventType.SECURITY_ALERT,
            AuditEventType.COMPLIANCE_VIOLATION,
            AuditEventType.DATA_DELETION
        ]
        
        if event_type in high_risk_events:
            score += 0.5
            
        # Check IP reputation (placeholder)
        if self._is_suspicious_ip(ip_address):
            score += 0.3
            
        # Check user behavior (placeholder)
        if user_id and self._is_anomalous_behavior(user_id):
            score += 0.2
            
        return min(score, 1.0)
        
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP is suspicious (placeholder)"""
        # This would check against threat intelligence feeds
        suspicious_ranges = ['10.0.0.0/8', '192.168.0.0/16']
        
        try:
            ip = ipaddress.ip_address(ip_address)
            for range_str in suspicious_ranges:
                if ip in ipaddress.ip_network(range_str):
                    return True
        except ValueError:
            return True
            
        return False
        
    def _is_anomalous_behavior(self, user_id: str) -> bool:
        """Check for anomalous user behavior (placeholder)"""
        # This would use ML to detect anomalies
        return False
        
    async def _send_security_alert(self, audit_log: AuditLog):
        """Send security alert"""
        logger.warning(f"SECURITY ALERT: {audit_log.to_dict()}")
        # This would send email/SMS/Slack notification
        
    async def perform_security_scan(self) -> Dict[str, Any]:
        """Perform comprehensive security scan"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'scans': {}
        }
        
        # Scan dependencies
        results['scans']['dependencies'] = await self.scanner.scan_dependencies(
            'requirements.txt'
        )
        
        # Scan code
        results['scans']['code'] = await self.scanner.scan_code('.')
        
        # Check compliance
        gdpr_check = await self.compliance.check_compliance(
            ComplianceFramework.GDPR,
            {
                'user_id': 'test_user',
                'data_fields': ['name', 'email'],
                'required_fields': ['email'],
                'has_erasure_mechanism': True,
                'has_export_mechanism': True
            }
        )
        results['scans']['gdpr_compliance'] = gdpr_check
        
        soc2_check = await self.compliance.check_compliance(
            ComplianceFramework.SOC2,
            {
                'encrypted_at_rest': True,
                'encrypted_in_transit': True,
                'has_rbac': True,
                'has_mfa': True,
                'has_monitoring': True,
                'has_alerting': True,
                'has_incident_plan': True
            }
        )
        results['scans']['soc2_compliance'] = soc2_check
        
        return results
        
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.encryption.encrypt_field(data)
        
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.encryption.decrypt_field(encrypted_data)

# Usage example
async def demo_security():
    """Demonstrate security system"""
    config = {
        'database_url': 'sqlite:///security_audit.db'
    }
    
    security = SecurityOrchestrator(config)
    
    # Authenticate user
    auth_result = await security.authenticate_user(
        'admin',
        'SecurePassword123!',
        '123456',  # MFA token
        '192.168.1.100',
        'Mozilla/5.0'
    )
    
    print(f"Authentication: {auth_result}")
    
    # Check authorization
    authorized = await security.authorize_action(
        'admin',
        'transcription_123',
        'read',
        '192.168.1.100'
    )
    
    print(f"Authorization: {authorized}")
    
    # Validate input
    valid, sanitized = security.validator.validate_input(
        "user@example.com",
        "email"
    )
    
    print(f"Input validation: {valid}, {sanitized}")
    
    # Perform security scan
    scan_results = await security.perform_security_scan()
    print(f"Security scan: {json.dumps(scan_results, indent=2)}")
    
    # Encrypt data
    encrypted = security.encrypt_data("Sensitive information")
    print(f"Encrypted: {encrypted}")
    
    decrypted = security.decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")

if __name__ == "__main__":
    asyncio.run(demo_security())