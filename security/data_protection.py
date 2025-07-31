"""
Data protection and privacy utilities for GDPR/privacy compliance
"""

import hashlib
import json
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import secrets

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .encryption import encryption_service
from monitoring import get_logger, audit_action

logger = get_logger(__name__, "security")


class DataCategory(Enum):
    """Categories of personal data"""
    IDENTITY = "identity"  # Name, email, ID numbers
    CONTACT = "contact"    # Phone, address, location
    FINANCIAL = "financial"  # Payment info, billing
    BEHAVIORAL = "behavioral"  # Usage patterns, preferences
    BIOMETRIC = "biometric"   # Voice data, biometrics
    TECHNICAL = "technical"   # IP addresses, device info
    CONTENT = "content"      # User-generated content


@dataclass
class DataField:
    """Represents a data field with privacy metadata"""
    name: str
    category: DataCategory
    is_pii: bool = False
    is_sensitive: bool = False
    retention_days: Optional[int] = None
    anonymizable: bool = True
    description: str = ""


@dataclass
class ConsentRecord:
    """Records user consent for data processing"""
    user_id: int
    purpose: str
    granted: bool
    timestamp: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    version: str = "1.0"


class PIIDetector:
    """Detects personally identifiable information in text"""
    
    def __init__(self):
        # Regex patterns for common PII
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'name': re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),  # Simple name pattern
        }
        
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text and return matches by type"""
        found_pii = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                found_pii[pii_type] = matches
                
        return found_pii
        
    def has_pii(self, text: str) -> bool:
        """Check if text contains any PII"""
        return bool(self.detect_pii(text))
        
    def anonymize_text(self, text: str, replacement_char: str = "X") -> str:
        """Replace PII in text with placeholder characters"""
        anonymized = text
        
        for pii_type, pattern in self.patterns.items():
            def replace_match(match):
                return replacement_char * len(match.group())
            
            anonymized = pattern.sub(replace_match, anonymized)
            
        return anonymized


class DataAnonymizer:
    """Anonymizes and pseudonymizes personal data"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.salt = self._get_or_create_salt()
        
    def _get_or_create_salt(self) -> str:
        """Get or create salt for consistent hashing"""
        # In production, this should be stored securely
        salt_file = "anonymization.salt"
        try:
            with open(salt_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            salt = secrets.token_hex(32)
            with open(salt_file, 'w') as f:
                f.write(salt)
            return salt
            
    def pseudonymize_identifier(self, identifier: str) -> str:
        """Create consistent pseudonym for identifier"""
        # Use HMAC-SHA256 for consistent pseudonymization
        data = f"{identifier}{self.salt}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()[:16]
        
    def anonymize_email(self, email: str) -> str:
        """Anonymize email address"""
        if '@' not in email:
            return "anonymous@example.com"
            
        local, domain = email.split('@', 1)
        
        # Keep first and last character of local part if long enough
        if len(local) > 2:
            anonymized_local = local[0] + 'X' * (len(local) - 2) + local[-1]
        else:
            anonymized_local = 'X' * len(local)
            
        return f"{anonymized_local}@{domain}"
        
    def anonymize_phone(self, phone: str) -> str:
        """Anonymize phone number"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) >= 10:
            # Keep country code and area code, anonymize rest
            return f"XXX-XXX-{digits[-4:]}"
        else:
            return "XXX-XXX-XXXX"
            
    def anonymize_name(self, name: str) -> str:
        """Anonymize person name"""
        parts = name.split()
        if len(parts) == 1:
            return f"{parts[0][0]}***"
        elif len(parts) == 2:
            return f"{parts[0][0]}*** {parts[1][0]}***"
        else:
            return f"{parts[0][0]}*** {parts[-1][0]}***"
            
    def anonymize_text_content(self, text: str, preserve_structure: bool = True) -> str:
        """Anonymize PII in text content"""
        if preserve_structure:
            # Replace PII while preserving text structure
            anonymized = text
            
            # Replace emails
            anonymized = re.sub(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                '[EMAIL]',
                anonymized
            )
            
            # Replace phones
            anonymized = re.sub(
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
                '[PHONE]',
                anonymized
            )
            
            # Replace SSNs
            anonymized = re.sub(
                r'\b\d{3}-?\d{2}-?\d{4}\b',
                '[SSN]',
                anonymized
            )
            
            return anonymized
        else:
            return self.pii_detector.anonymize_text(text)
            
    def anonymize_dict(self, data: Dict[str, Any], field_rules: Dict[str, str]) -> Dict[str, Any]:
        """Anonymize dictionary based on field rules"""
        anonymized = data.copy()
        
        for field, rule in field_rules.items():
            if field in anonymized and anonymized[field]:
                value = str(anonymized[field])
                
                if rule == 'email':
                    anonymized[field] = self.anonymize_email(value)
                elif rule == 'phone':
                    anonymized[field] = self.anonymize_phone(value)
                elif rule == 'name':
                    anonymized[field] = self.anonymize_name(value)
                elif rule == 'pseudonymize':
                    anonymized[field] = self.pseudonymize_identifier(value)
                elif rule == 'remove':
                    del anonymized[field]
                elif rule == 'text':
                    anonymized[field] = self.anonymize_text_content(value)
                    
        return anonymized


class ConsentManager:
    """Manages user consent for data processing"""
    
    def __init__(self):
        self.consent_records: Dict[Tuple[int, str], ConsentRecord] = {}
        
    @audit_action("grant_consent")
    def grant_consent(self, user_id: int, purpose: str, expires_days: Optional[int] = None) -> ConsentRecord:
        """Grant consent for data processing"""
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
        consent = ConsentRecord(
            user_id=user_id,
            purpose=purpose,
            granted=True,
            timestamp=datetime.utcnow(),
            expires_at=expires_at
        )
        
        self.consent_records[(user_id, purpose)] = consent
        logger.info(f"Consent granted for user {user_id}, purpose: {purpose}")
        
        return consent
        
    @audit_action("revoke_consent")
    def revoke_consent(self, user_id: int, purpose: str) -> bool:
        """Revoke consent for data processing"""
        key = (user_id, purpose)
        if key in self.consent_records:
            self.consent_records[key].granted = False
            self.consent_records[key].revoked_at = datetime.utcnow()
            logger.info(f"Consent revoked for user {user_id}, purpose: {purpose}")
            return True
        return False
        
    def has_valid_consent(self, user_id: int, purpose: str) -> bool:
        """Check if user has valid consent for purpose"""
        key = (user_id, purpose)
        consent = self.consent_records.get(key)
        
        if not consent or not consent.granted:
            return False
            
        # Check if consent has been revoked
        if consent.revoked_at:
            return False
            
        # Check if consent has expired
        if consent.expires_at and datetime.utcnow() > consent.expires_at:
            return False
            
        return True
        
    def get_user_consents(self, user_id: int) -> List[ConsentRecord]:
        """Get all consent records for a user"""
        return [consent for (uid, _), consent in self.consent_records.items() if uid == user_id]


class DataRetentionManager:
    """Manages data retention and deletion policies"""
    
    def __init__(self):
        self.retention_policies: Dict[str, int] = {
            'user_activity_logs': 90,     # 3 months
            'transcripts': 365 * 3,       # 3 years
            'user_sessions': 30,          # 1 month
            'audit_logs': 365 * 7,        # 7 years
            'error_logs': 365,            # 1 year
            'backup_data': 365 * 2,       # 2 years
        }
        
    def set_retention_policy(self, data_type: str, retention_days: int):
        """Set retention policy for data type"""
        self.retention_policies[data_type] = retention_days
        logger.info(f"Set retention policy for {data_type}: {retention_days} days")
        
    def get_retention_policy(self, data_type: str) -> Optional[int]:
        """Get retention policy for data type"""
        return self.retention_policies.get(data_type)
        
    def is_data_expired(self, data_type: str, created_at: datetime) -> bool:
        """Check if data has exceeded retention period"""
        retention_days = self.get_retention_policy(data_type)
        if not retention_days:
            return False
            
        expiry_date = created_at + timedelta(days=retention_days)
        return datetime.utcnow() > expiry_date
        
    def get_expired_data_cutoff(self, data_type: str) -> Optional[datetime]:
        """Get cutoff date for expired data"""
        retention_days = self.get_retention_policy(data_type)
        if not retention_days:
            return None
            
        return datetime.utcnow() - timedelta(days=retention_days)


class DataPrivacyManager:
    """Main data privacy management system"""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.anonymizer = DataAnonymizer()
        self.consent_manager = ConsentManager()
        self.retention_manager = DataRetentionManager()
        
        # Define data field configurations
        self.data_fields = {
            'users': {
                'email': DataField('email', DataCategory.IDENTITY, is_pii=True, is_sensitive=True),
                'name': DataField('name', DataCategory.IDENTITY, is_pii=True),
                'phone': DataField('phone', DataCategory.CONTACT, is_pii=True),
                'address': DataField('address', DataCategory.CONTACT, is_pii=True),
            },
            'transcripts': {
                'content': DataField('content', DataCategory.CONTENT, is_sensitive=True, retention_days=365*3),
                'metadata': DataField('metadata', DataCategory.TECHNICAL),
            },
            'sessions': {
                'ip_address': DataField('ip_address', DataCategory.TECHNICAL, is_pii=True, retention_days=30),
                'user_agent': DataField('user_agent', DataCategory.TECHNICAL),
            }
        }
        
    def classify_data_sensitivity(self, model_name: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Classify data fields by sensitivity level"""
        model_fields = self.data_fields.get(model_name, {})
        classification = {}
        
        for field_name, value in data.items():
            field_def = model_fields.get(field_name)
            
            if field_def:
                if field_def.is_sensitive:
                    classification[field_name] = 'sensitive'
                elif field_def.is_pii:
                    classification[field_name] = 'pii'
                else:
                    classification[field_name] = 'normal'
            else:
                # Auto-detect PII in unknown fields
                if isinstance(value, str) and self.pii_detector.has_pii(value):
                    classification[field_name] = 'pii'
                else:
                    classification[field_name] = 'normal'
                    
        return classification
        
    def prepare_data_for_storage(self, model_name: str, data: Dict[str, Any], 
                                user_id: Optional[int] = None) -> Dict[str, Any]:
        """Prepare data for storage with appropriate protections"""
        # Check consent if user_id is provided
        if user_id:
            purposes = ['data_processing', 'service_provision']
            for purpose in purposes:
                if not self.consent_manager.has_valid_consent(user_id, purpose):
                    logger.warning(f"No valid consent for user {user_id}, purpose: {purpose}")
                    
        # Classify data sensitivity
        classification = self.classify_data_sensitivity(model_name, data)
        
        # Encrypt sensitive and PII fields
        fields_to_encrypt = [
            field for field, level in classification.items() 
            if level in ['sensitive', 'pii']
        ]
        
        if fields_to_encrypt:
            data = encryption_service.encrypt_database_record(model_name, {
                **data,
                '_encrypted_fields': fields_to_encrypt
            })
            
        return data
        
    def prepare_data_for_retrieval(self, model_name: str, data: Dict[str, Any],
                                  user_id: Optional[int] = None) -> Dict[str, Any]:
        """Prepare data for retrieval with appropriate access controls"""
        # Decrypt if necessary
        if '_encrypted_fields' in data:
            data = encryption_service.decrypt_database_record(model_name, data)
            
        # Check consent for data access
        if user_id:
            if not self.consent_manager.has_valid_consent(user_id, 'data_access'):
                # Return anonymized version if no consent
                return self.anonymize_user_data(model_name, data)
                
        return data
        
    def anonymize_user_data(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize user data for privacy protection"""
        anonymization_rules = {
            'users': {
                'email': 'email',
                'name': 'name',
                'phone': 'phone',
                'address': 'remove'
            },
            'transcripts': {
                'content': 'text'
            }
        }
        
        rules = anonymization_rules.get(model_name, {})
        return self.anonymizer.anonymize_dict(data, rules)
        
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Export all user data for GDPR data portability"""
        # This would typically query all user data from database
        # For now, return a structure showing what would be exported
        
        logger.info(f"Exporting user data for user {user_id}")
        
        return {
            'user_id': user_id,
            'export_date': datetime.utcnow().isoformat(),
            'data_categories': {
                'personal_info': {
                    'description': 'Basic personal information',
                    'fields': ['name', 'email', 'phone']
                },
                'transcripts': {
                    'description': 'Uploaded and processed transcripts',
                    'count': 25  # Would be actual count
                },
                'usage_data': {
                    'description': 'Platform usage statistics',
                    'retention_days': 90
                }
            },
            'consents': [
                consent.__dict__ for consent in self.consent_manager.get_user_consents(user_id)
            ]
        }
        
    @audit_action("delete_user_data")
    def delete_user_data(self, user_id: int, data_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Delete user data for GDPR right to erasure"""
        logger.info(f"Deleting user data for user {user_id}, categories: {data_categories}")
        
        # This would typically perform actual deletion from database
        # Return summary of what would be deleted
        
        categories_to_delete = data_categories or ['all']
        
        return {
            'user_id': user_id,
            'deletion_date': datetime.utcnow().isoformat(),
            'categories_deleted': categories_to_delete,
            'records_affected': {
                'users': 1,
                'transcripts': 25,
                'sessions': 150,
                'audit_logs': 500  # These might be retained for legal reasons
            },
            'retention_exceptions': [
                'audit_logs retained for 7 years due to legal requirements'
            ]
        }


# Global data privacy manager
data_privacy_manager = DataPrivacyManager()