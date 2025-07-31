#!/usr/bin/env python3
"""
HIPAA Compliance and Security Module
Implements healthcare data security, encryption, and audit logging
"""

import os
import logging
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

@dataclass
class AuditLogEntry:
    """HIPAA audit log entry"""
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: str
    user_agent: str
    success: bool
    details: Optional[Dict[str, Any]] = None
    phi_accessed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'details': self.details or {},
            'phi_accessed': self.phi_accessed
        }

@dataclass
class AccessControlEntry:
    """Access control entry for HIPAA compliance"""
    user_id: str
    role: str
    permissions: List[str]
    patient_access: List[str]  # Patient IDs user can access
    expiry_date: Optional[datetime] = None
    active: bool = True

class EncryptionManager:
    """Handles encryption/decryption for PHI data"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or self._generate_master_key()
        self.fernet = Fernet(self.master_key)
    
    def _generate_master_key(self) -> bytes:
        """Generate a new master encryption key"""
        return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
            
            encrypted_data = self.fernet.encrypt(data)
            logger.debug("Data encrypted successfully")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise SecurityError(f"Failed to encrypt data: {e}")
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise SecurityError(f"Failed to decrypt data: {e}")
    
    def encrypt_file(self, file_path: str, output_path: str) -> bool:
        """Encrypt a file"""
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.fernet.encrypt(file_data)
            
            with open(output_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            logger.info(f"File encrypted: {file_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            return False
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> bool:
        """Decrypt a file"""
        try:
            with open(encrypted_file_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            logger.info(f"File decrypted: {encrypted_file_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            return False

class AuditLogger:
    """HIPAA-compliant audit logging system"""
    
    def __init__(self, log_file_path: str = "hipaa_audit.log"):
        self.log_file_path = log_file_path
        self.encryption_manager = EncryptionManager()
        self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Setup secure audit logging"""
        # Create audit log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file_path) if os.path.dirname(self.log_file_path) else '.', exist_ok=True)
        
        # Setup file handler with appropriate permissions
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w') as f:
                f.write("")  # Create empty file
            os.chmod(self.log_file_path, 0o600)  # Read/write for owner only
    
    def log_access(self, user_id: str, action: str, resource_type: str, 
                   resource_id: str, ip_address: str = "unknown", 
                   user_agent: str = "unknown", success: bool = True,
                   details: Optional[Dict[str, Any]] = None, 
                   phi_accessed: bool = False) -> str:
        """Log access to PHI or system resources"""
        
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details,
            phi_accessed=phi_accessed
        )
        
        # Generate unique audit ID
        audit_id = str(uuid.uuid4())
        
        try:
            # Encrypt audit log entry
            log_data = {
                'audit_id': audit_id,
                'entry': audit_entry.to_dict()
            }
            
            encrypted_log = self.encryption_manager.encrypt_data(json.dumps(log_data))
            
            # Write to audit log file
            with open(self.log_file_path, 'ab') as log_file:
                log_file.write(encrypted_log + b'\n')
            
            # Also log to application logger for immediate visibility
            logger.info(f"AUDIT: {action} on {resource_type}:{resource_id} by {user_id} - {'SUCCESS' if success else 'FAILED'}")
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            # This is critical - audit logging failure should be escalated
            raise SecurityError(f"Critical: Audit logging failed: {e}")
    
    def get_audit_logs(self, start_date: datetime, end_date: datetime, 
                      user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve audit logs for compliance reporting"""
        try:
            audit_logs = []
            
            if not os.path.exists(self.log_file_path):
                return audit_logs
            
            with open(self.log_file_path, 'rb') as log_file:
                for line in log_file:
                    if line.strip():
                        try:
                            decrypted_data = self.encryption_manager.decrypt_data(line.strip())
                            log_entry = json.loads(decrypted_data)
                            
                            entry_timestamp = datetime.fromisoformat(log_entry['entry']['timestamp'])
                            
                            # Filter by date range
                            if start_date <= entry_timestamp <= end_date:
                                # Filter by user if specified
                                if user_id is None or log_entry['entry']['user_id'] == user_id:
                                    audit_logs.append(log_entry)
                                    
                        except Exception as e:
                            logger.warning(f"Failed to decrypt audit log entry: {e}")
                            continue
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []

class AccessController:
    """HIPAA access control management"""
    
    def __init__(self):
        self.access_entries: Dict[str, AccessControlEntry] = {}
        self.audit_logger = AuditLogger()
    
    def add_user(self, user_id: str, role: str, permissions: List[str], 
                patient_access: List[str] = None) -> bool:
        """Add user with specific permissions"""
        try:
            access_entry = AccessControlEntry(
                user_id=user_id,
                role=role,
                permissions=permissions,
                patient_access=patient_access or [],
                active=True
            )
            
            self.access_entries[user_id] = access_entry
            
            self.audit_logger.log_access(
                user_id="system",
                action="USER_CREATED",
                resource_type="USER",
                resource_id=user_id,
                details={"role": role, "permissions": permissions}
            )
            
            logger.info(f"User {user_id} added with role {role}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
            return False
    
    def check_permission(self, user_id: str, permission: str, 
                        patient_id: Optional[str] = None) -> bool:
        """Check if user has specific permission"""
        try:
            if user_id not in self.access_entries:
                self.audit_logger.log_access(
                    user_id=user_id,
                    action="ACCESS_DENIED",
                    resource_type="PERMISSION",
                    resource_id=permission,
                    success=False,
                    details={"reason": "user_not_found"}
                )
                return False
            
            access_entry = self.access_entries[user_id]
            
            # Check if user is active
            if not access_entry.active:
                self.audit_logger.log_access(
                    user_id=user_id,
                    action="ACCESS_DENIED",
                    resource_type="PERMISSION",
                    resource_id=permission,
                    success=False,
                    details={"reason": "user_inactive"}
                )
                return False
            
            # Check expiry date
            if access_entry.expiry_date and datetime.now() > access_entry.expiry_date:
                self.audit_logger.log_access(
                    user_id=user_id,
                    action="ACCESS_DENIED",
                    resource_type="PERMISSION",
                    resource_id=permission,
                    success=False,
                    details={"reason": "access_expired"}
                )
                return False
            
            # Check permission
            has_permission = permission in access_entry.permissions
            
            # Check patient access if specified
            if patient_id and has_permission:
                has_patient_access = (
                    patient_id in access_entry.patient_access or 
                    "ALL_PATIENTS" in access_entry.permissions
                )
                has_permission = has_permission and has_patient_access
            
            # Log access attempt
            self.audit_logger.log_access(
                user_id=user_id,
                action="PERMISSION_CHECK",
                resource_type="PERMISSION",
                resource_id=permission,
                success=has_permission,
                details={"patient_id": patient_id} if patient_id else None,
                phi_accessed=patient_id is not None
            )
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Permission check failed for {user_id}: {e}")
            return False
    
    def revoke_access(self, user_id: str, admin_user_id: str) -> bool:
        """Revoke user access"""
        try:
            if user_id in self.access_entries:
                self.access_entries[user_id].active = False
                
                self.audit_logger.log_access(
                    user_id=admin_user_id,
                    action="ACCESS_REVOKED",
                    resource_type="USER",
                    resource_id=user_id,
                    details={"revoked_by": admin_user_id}
                )
                
                logger.info(f"Access revoked for user {user_id} by {admin_user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to revoke access for {user_id}: {e}")
            return False

class PHIAnonymizer:
    """Anonymize PHI data for compliance"""
    
    def __init__(self):
        self.phi_patterns = self._load_phi_patterns()
    
    def _load_phi_patterns(self) -> Dict[str, str]:
        """Load PHI identification patterns"""
        return {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'date_of_birth': r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            'medical_record': r'\bMRN:?\s*\d+\b',
            'account_number': r'\bAccount:?\s*\d+\b'
        }
    
    def anonymize_text(self, text: str, replacement_map: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, List[str]]]:
        """
        Anonymize PHI in text
        
        Returns:
            Tuple of (anonymized_text, detected_phi_map)
        """
        import re
        
        anonymized_text = text
        detected_phi = {}
        
        for phi_type, pattern in self.phi_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                detected_phi[phi_type] = matches
                
                # Replace with anonymized versions
                for match in matches:
                    if replacement_map and match in replacement_map:
                        replacement = replacement_map[match]
                    else:
                        replacement = self._generate_replacement(phi_type)
                    
                    anonymized_text = anonymized_text.replace(match, replacement)
        
        return anonymized_text, detected_phi
    
    def _generate_replacement(self, phi_type: str) -> str:
        """Generate appropriate replacement for PHI type"""
        replacements = {
            'ssn': '[SSN-REDACTED]',
            'phone': '[PHONE-REDACTED]',
            'email': '[EMAIL-REDACTED]',
            'date_of_birth': '[DOB-REDACTED]',
            'medical_record': '[MRN-REDACTED]',
            'account_number': '[ACCOUNT-REDACTED]'
        }
        
        return replacements.get(phi_type, '[PHI-REDACTED]')
    
    def create_anonymization_map(self, original_text: str) -> Dict[str, str]:
        """Create consistent anonymization mapping"""
        import re
        
        anonymization_map = {}
        counter = {}
        
        for phi_type, pattern in self.phi_patterns.items():
            matches = re.findall(pattern, original_text, re.IGNORECASE)
            
            for match in matches:
                if match not in anonymization_map:
                    counter[phi_type] = counter.get(phi_type, 0) + 1
                    anonymization_map[match] = f"[{phi_type.upper()}-{counter[phi_type]}]"
        
        return anonymization_map

class HIPAACompliance:
    """Main HIPAA compliance manager"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.audit_logger = AuditLogger()
        self.access_controller = AccessController()
        self.phi_anonymizer = PHIAnonymizer()
        
        # Initialize default admin user
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Initialize default system users"""
        # System admin
        self.access_controller.add_user(
            user_id="system_admin",
            role="ADMIN",
            permissions=["ALL_PERMISSIONS", "USER_MANAGEMENT", "AUDIT_ACCESS", "ALL_PATIENTS"]
        )
        
        # Healthcare provider
        self.access_controller.add_user(
            user_id="healthcare_provider",
            role="PROVIDER",
            permissions=["TRANSCRIPTION_ACCESS", "PHI_ACCESS", "PATIENT_DATA"]
        )
        
        # Basic user
        self.access_controller.add_user(
            user_id="basic_user",
            role="USER",
            permissions=["TRANSCRIPTION_ACCESS"]
        )
    
    def process_healthcare_audio(self, audio_data: bytes, user_id: str, 
                                patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Process healthcare audio with HIPAA compliance"""
        
        # Check permissions
        if not self.access_controller.check_permission(user_id, "TRANSCRIPTION_ACCESS", patient_id):
            raise SecurityError("Access denied: Insufficient permissions")
        
        # Log access
        audit_id = self.audit_logger.log_access(
            user_id=user_id,
            action="AUDIO_PROCESSING",
            resource_type="AUDIO_FILE",
            resource_id=patient_id or "unknown",
            phi_accessed=patient_id is not None,
            details={"file_size": len(audio_data)}
        )
        
        try:
            # Encrypt audio data
            encrypted_audio = self.encryption_manager.encrypt_data(audio_data.decode('latin-1'))
            
            # Process (placeholder - would integrate with actual transcription)
            processing_result = {
                'audit_id': audit_id,
                'encrypted_data': encrypted_audio,
                'patient_id': patient_id,
                'processed_by': user_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Log successful processing
            self.audit_logger.log_access(
                user_id=user_id,
                action="AUDIO_PROCESSED",
                resource_type="PROCESSING_RESULT",
                resource_id=audit_id,
                success=True,
                phi_accessed=patient_id is not None
            )
            
            return processing_result
            
        except Exception as e:
            # Log processing failure
            self.audit_logger.log_access(
                user_id=user_id,
                action="AUDIO_PROCESSING",
                resource_type="AUDIO_FILE",
                resource_id=patient_id or "unknown",
                success=False,
                details={"error": str(e)},
                phi_accessed=patient_id is not None
            )
            raise
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report"""
        
        audit_logs = self.audit_logger.get_audit_logs(start_date, end_date)
        
        report = {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_access_attempts': len(audit_logs),
            'successful_accesses': len([log for log in audit_logs if log['entry']['success']]),
            'failed_accesses': len([log for log in audit_logs if not log['entry']['success']]),
            'phi_accesses': len([log for log in audit_logs if log['entry']['phi_accessed']]),
            'unique_users': len(set(log['entry']['user_id'] for log in audit_logs)),
            'access_by_action': {},
            'access_by_user': {},
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Aggregate by action
        for log in audit_logs:
            action = log['entry']['action']
            report['access_by_action'][action] = report['access_by_action'].get(action, 0) + 1
        
        # Aggregate by user
        for log in audit_logs:
            user_id = log['entry']['user_id']
            report['access_by_user'][user_id] = report['access_by_user'].get(user_id, 0) + 1
        
        return report

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass

# Global HIPAA compliance instance
_hipaa_compliance = None

def get_hipaa_compliance() -> HIPAACompliance:
    """Get or create global HIPAA compliance instance"""
    global _hipaa_compliance
    if _hipaa_compliance is None:
        _hipaa_compliance = HIPAACompliance()
    return _hipaa_compliance

# Public API functions
def encrypt_phi_data(data: str) -> bytes:
    """Encrypt PHI data"""
    compliance = get_hipaa_compliance()
    return compliance.encryption_manager.encrypt_data(data)

def decrypt_phi_data(encrypted_data: bytes) -> str:
    """Decrypt PHI data"""
    compliance = get_hipaa_compliance()
    return compliance.encryption_manager.decrypt_data(encrypted_data)

def log_phi_access(user_id: str, action: str, patient_id: str, success: bool = True) -> str:
    """Log PHI access for audit trail"""
    compliance = get_hipaa_compliance()
    return compliance.audit_logger.log_access(
        user_id=user_id,
        action=action,
        resource_type="PHI",
        resource_id=patient_id,
        success=success,
        phi_accessed=True
    )

def anonymize_transcript(text: str) -> Tuple[str, Dict[str, List[str]]]:
    """Anonymize PHI in transcript"""
    compliance = get_hipaa_compliance()
    return compliance.phi_anonymizer.anonymize_text(text)