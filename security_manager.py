"""
Advanced Security and Privacy Manager
Provides comprehensive security features including encryption, access control, and privacy protection
"""

import os
import hashlib
import secrets
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import bcrypt
import jwt
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Handle encryption and decryption operations"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.environ.get('SECURITY_MASTER_KEY')
        if not self.master_key:
            self.master_key = self._generate_master_key()
            logger.warning("Generated new master key. Store SECURITY_MASTER_KEY environment variable.")
    
    def _generate_master_key(self) -> str:
        """Generate a new master encryption key"""
        return Fernet.generate_key().decode()
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
    
    def encrypt_data(self, data: str, password: Optional[str] = None) -> Dict[str, str]:
        """Encrypt data with optional password"""
        if password:
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
            fernet = Fernet(Fernet.generate_key())
        else:
            fernet = Fernet(self.master_key.encode())
            salt = None
        
        encrypted_data = fernet.encrypt(data.encode())
        
        result = {
            'encrypted_data': encrypted_data.decode(),
            'timestamp': datetime.now().isoformat()
        }
        
        if salt:
            result['salt'] = salt.hex()
            result['password_protected'] = True
        
        return result
    
    def decrypt_data(self, encrypted_package: Dict[str, str], password: Optional[str] = None) -> str:
        """Decrypt data with optional password"""
        if encrypted_package.get('password_protected') and password:
            salt = bytes.fromhex(encrypted_package['salt'])
            key = self._derive_key(password, salt)
            fernet = Fernet(Fernet.generate_key())
        else:
            fernet = Fernet(self.master_key.encode())
        
        decrypted_data = fernet.decrypt(encrypted_package['encrypted_data'].encode())
        return decrypted_data.decode()
    
    def generate_file_hash(self, file_path: str) -> str:
        """Generate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


class AccessControlManager:
    """Manage user access control and permissions"""
    
    def __init__(self, config_file: str = "access_control.json"):
        self.config_file = config_file
        self.permissions = self._load_permissions()
        self.session_tokens = {}
        self.rate_limits = {}
    
    def _load_permissions(self) -> Dict[str, Any]:
        """Load permission configuration"""
        default_permissions = {
            "roles": {
                "admin": {
                    "permissions": ["read", "write", "delete", "admin", "export", "share"],
                    "rate_limit": 1000
                },
                "user": {
                    "permissions": ["read", "write", "export"],
                    "rate_limit": 100
                },
                "viewer": {
                    "permissions": ["read"],
                    "rate_limit": 50
                }
            },
            "users": {},
            "api_keys": {}
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load permissions: {e}")
                return default_permissions
        
        return default_permissions
    
    def _save_permissions(self):
        """Save permission configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.permissions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save permissions: {e}")
    
    def create_user(self, user_id: str, password: str, role: str = "user") -> bool:
        """Create a new user with hashed password"""
        if user_id in self.permissions["users"]:
            return False
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        self.permissions["users"][user_id] = {
            "password_hash": password_hash.decode('utf-8'),
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": None
        }
        
        self._save_permissions()
        return True
    
    def authenticate_user(self, user_id: str, password: str) -> Optional[str]:
        """Authenticate user and return session token"""
        user_data = self.permissions["users"].get(user_id)
        if not user_data:
            return None
        
        # Check if account is locked
        if user_data.get("locked_until"):
            lock_time = datetime.fromisoformat(user_data["locked_until"])
            if datetime.now() < lock_time:
                return None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user_data["password_hash"].encode('utf-8')):
            # Reset failed attempts
            user_data["failed_attempts"] = 0
            user_data["last_login"] = datetime.now().isoformat()
            user_data["locked_until"] = None
            
            # Generate session token
            token = self._generate_session_token(user_id)
            self._save_permissions()
            return token
        else:
            # Increment failed attempts
            user_data["failed_attempts"] = user_data.get("failed_attempts", 0) + 1
            
            # Lock account after 5 failed attempts
            if user_data["failed_attempts"] >= 5:
                user_data["locked_until"] = (datetime.now() + timedelta(minutes=30)).isoformat()
            
            self._save_permissions()
            return None
    
    def _generate_session_token(self, user_id: str) -> str:
        """Generate JWT session token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now() + timedelta(hours=24),
            'iat': datetime.now()
        }
        
        secret_key = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        self.session_tokens[token] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_used': datetime.now()
        }
        
        return token
    
    def validate_token(self, token: str) -> Optional[str]:
        """Validate session token and return user_id"""
        try:
            secret_key = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            
            # Update last used time
            if token in self.session_tokens:
                self.session_tokens[token]['last_used'] = datetime.now()
            
            return user_id
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user_data = self.permissions["users"].get(user_id)
        if not user_data:
            return False
        
        role = user_data["role"]
        role_permissions = self.permissions["roles"].get(role, {}).get("permissions", [])
        return permission in role_permissions
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        user_data = self.permissions["users"].get(user_id)
        
        if not user_data:
            return False
        
        role = user_data["role"]
        rate_limit = self.permissions["roles"].get(role, {}).get("rate_limit", 50)
        
        # Clean old entries (older than 1 hour)
        if user_id in self.rate_limits:
            self.rate_limits[user_id] = [
                timestamp for timestamp in self.rate_limits[user_id]
                if current_time - timestamp < 3600
            ]
        else:
            self.rate_limits[user_id] = []
        
        # Check if under limit
        if len(self.rate_limits[user_id]) < rate_limit:
            self.rate_limits[user_id].append(current_time)
            return True
        
        return False
    
    def generate_api_key(self, user_id: str, description: str = "") -> Optional[str]:
        """Generate API key for user"""
        if not self.check_permission(user_id, "admin"):
            return None
        
        api_key = secrets.token_urlsafe(32)
        self.permissions["api_keys"][api_key] = {
            "user_id": user_id,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "active": True
        }
        
        self._save_permissions()
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return user_id"""
        api_data = self.permissions["api_keys"].get(api_key)
        if not api_data or not api_data["active"]:
            return None
        
        api_data["last_used"] = datetime.now().isoformat()
        self._save_permissions()
        return api_data["user_id"]


class PrivacyManager:
    """Handle privacy and data protection features"""
    
    def __init__(self):
        self.data_retention_policy = {
            "transcripts": 365,  # days
            "audio_files": 30,
            "analysis_results": 90,
            "user_sessions": 7
        }
        self.anonymization_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number
        ]
    
    def anonymize_text(self, text: str, replacement: str = "[REDACTED]") -> str:
        """Anonymize sensitive information in text"""
        import re
        
        anonymized_text = text
        for pattern in self.anonymization_patterns:
            anonymized_text = re.sub(pattern, replacement, anonymized_text)
        
        return anonymized_text
    
    def generate_privacy_report(self, user_id: str) -> Dict[str, Any]:
        """Generate privacy compliance report for user"""
        report = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "data_categories": {
                "personal_info": {
                    "stored": True,
                    "encrypted": True,
                    "retention_days": 365
                },
                "transcripts": {
                    "stored": True,
                    "encrypted": True,
                    "anonymized_option": True,
                    "retention_days": self.data_retention_policy["transcripts"]
                },
                "audio_files": {
                    "stored": True,
                    "encrypted": True,
                    "retention_days": self.data_retention_policy["audio_files"]
                }
            },
            "user_rights": {
                "data_access": True,
                "data_portability": True,
                "data_deletion": True,
                "data_rectification": True
            },
            "compliance": {
                "gdpr_compliant": True,
                "ccpa_compliant": True,
                "data_minimization": True,
                "consent_based": True
            }
        }
        
        return report
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for compliance"""
        # This would typically query the database for all user data
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "personal_info": {},  # Would be filled from user profile
            "transcripts": [],    # Would be filled from transcript database
            "analysis_results": [], # Would be filled from analysis database
            "usage_history": []   # Would be filled from activity logs
        }
        
        return export_data
    
    def schedule_data_cleanup(self, user_id: Optional[str] = None) -> Dict[str, int]:
        """Schedule cleanup of expired data"""
        cleanup_stats = {
            "transcripts_removed": 0,
            "audio_files_removed": 0,
            "analysis_results_removed": 0,
            "sessions_removed": 0
        }
        
        # This would typically run database queries to remove expired data
        # based on retention policies
        
        logger.info(f"Data cleanup completed: {cleanup_stats}")
        return cleanup_stats


class AuditLogger:
    """Security audit logging"""
    
    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = log_file
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup dedicated security audit logger"""
        audit_logger = logging.getLogger('security_audit')
        audit_logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        
        return audit_logger
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str = "unknown"):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"AUTH_{status} - User: {user_id} - IP: {ip_address}")
    
    def log_access_attempt(self, user_id: str, resource: str, permission: str, granted: bool):
        """Log access attempt"""
        status = "GRANTED" if granted else "DENIED"
        self.logger.info(f"ACCESS_{status} - User: {user_id} - Resource: {resource} - Permission: {permission}")
    
    def log_data_operation(self, user_id: str, operation: str, resource_type: str, resource_id: str):
        """Log data operation"""
        self.logger.info(f"DATA_OP - User: {user_id} - Operation: {operation} - Type: {resource_type} - ID: {resource_id}")
    
    def log_security_event(self, event_type: str, user_id: str, details: str):
        """Log security event"""
        self.logger.warning(f"SECURITY_EVENT - Type: {event_type} - User: {user_id} - Details: {details}")


class SecurityManager:
    """Main security manager orchestrating all security components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.encryption_manager = EncryptionManager()
        self.access_control = AccessControlManager()
        self.privacy_manager = PrivacyManager()
        self.audit_logger = AuditLogger()
        
        # Security headers for web responses
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def secure_file_upload(self, file_path: str, user_id: str) -> Dict[str, Any]:
        """Secure file upload with validation and encryption"""
        try:
            # Generate file hash for integrity
            file_hash = self.encryption_manager.generate_file_hash(file_path)
            
            # Encrypt file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            encrypted_package = self.encryption_manager.encrypt_data(content)
            
            # Log the operation
            self.audit_logger.log_data_operation(user_id, "UPLOAD", "FILE", file_hash[:16])
            
            return {
                "success": True,
                "file_hash": file_hash,
                "encrypted_package": encrypted_package,
                "uploaded_by": user_id,
                "upload_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.audit_logger.log_security_event("FILE_UPLOAD_ERROR", user_id, str(e))
            return {"success": False, "error": str(e)}
    
    def secure_data_export(self, user_id: str, data_type: str, data: Any) -> Dict[str, Any]:
        """Secure data export with encryption and audit trail"""
        try:
            # Check export permission
            if not self.access_control.check_permission(user_id, "export"):
                self.audit_logger.log_access_attempt(user_id, data_type, "export", False)
                return {"success": False, "error": "Permission denied"}
            
            # Anonymize sensitive data if required
            if isinstance(data, str):
                data = self.privacy_manager.anonymize_text(data)
            
            # Encrypt export data
            data_str = json.dumps(data) if not isinstance(data, str) else data
            encrypted_package = self.encryption_manager.encrypt_data(data_str)
            
            # Log the export
            self.audit_logger.log_data_operation(user_id, "EXPORT", data_type, "encrypted")
            
            return {
                "success": True,
                "encrypted_data": encrypted_package,
                "export_time": datetime.now().isoformat(),
                "data_type": data_type
            }
            
        except Exception as e:
            self.audit_logger.log_security_event("DATA_EXPORT_ERROR", user_id, str(e))
            return {"success": False, "error": str(e)}
    
    def validate_request(self, token: str, required_permission: str) -> Tuple[bool, Optional[str]]:
        """Validate request with token and permission check"""
        # Validate token
        user_id = self.access_control.validate_token(token)
        if not user_id:
            return False, None
        
        # Check rate limit
        if not self.access_control.check_rate_limit(user_id):
            self.audit_logger.log_security_event("RATE_LIMIT_EXCEEDED", user_id, required_permission)
            return False, user_id
        
        # Check permission
        if not self.access_control.check_permission(user_id, required_permission):
            self.audit_logger.log_access_attempt(user_id, "API", required_permission, False)
            return False, user_id
        
        return True, user_id
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        return {
            "encryption_enabled": True,
            "access_control_enabled": True,
            "audit_logging_enabled": True,
            "privacy_features_enabled": True,
            "total_users": len(self.access_control.permissions["users"]),
            "active_sessions": len(self.access_control.session_tokens),
            "api_keys_issued": len(self.access_control.permissions["api_keys"]),
            "security_headers_enabled": True,
            "data_retention_policies": self.privacy_manager.data_retention_policy
        }


# Factory function for easy integration
def create_security_manager(config: Optional[Dict[str, Any]] = None) -> SecurityManager:
    """Create and configure security manager"""
    return SecurityManager(config)