"""
Data encryption system for securing sensitive information at rest
"""

import os
import base64
import json
import hashlib
from typing import Union, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import secrets

# Optional cryptography dependencies - graceful fallback
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    hashes = None
    PBKDF2HMAC = None
    Cipher = None
    algorithms = None
    modes = None
    default_backend = None

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitoring import get_logger

logger = get_logger(__name__, "security")


class EncryptionError(Exception):
    """Base exception for encryption errors"""
    pass


class KeyManager:
    """Manages encryption keys with rotation and secure storage"""
    
    def __init__(self, key_file: str = "encryption.key", salt_file: str = "encryption.salt"):
        self.key_file = key_file
        self.salt_file = salt_file
        self.master_key = None
        self.data_keys = {}
        self._load_or_create_master_key()
        
    def _load_or_create_master_key(self):
        """Load existing master key or create new one"""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography library not available - encryption features disabled")
            # Create a simple key for basic functionality
            self.master_key = secrets.token_bytes(32)
            return
            
        try:
            if os.path.exists(self.key_file) and os.path.exists(self.salt_file):
                self._load_master_key()
                logger.info("Loaded existing master encryption key")
            else:
                self._create_master_key()
                logger.info("Created new master encryption key")
        except Exception as e:
            logger.error(f"Failed to initialize master key: {e}")
            raise EncryptionError(f"Key initialization failed: {e}")
            
    def _create_master_key(self):
        """Create new master key and salt"""
        # Generate a random salt
        salt = os.urandom(16)
        
        # Use environment variable or generate random password
        password = os.environ.get('ENCRYPTION_PASSWORD')
        if not password:
            password = secrets.token_urlsafe(32)
            logger.warning("No ENCRYPTION_PASSWORD environment variable set. Generated random password.")
            print(f"Generated encryption password: {password}")
            print("Please save this password securely and set ENCRYPTION_PASSWORD environment variable")
            
        # Derive key from password and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Save salt and key (key is derived, we save the derived key)
        with open(self.salt_file, 'wb') as f:
            f.write(salt)
            
        with open(self.key_file, 'wb') as f:
            f.write(key)
            
        # Set restrictive permissions
        os.chmod(self.key_file, 0o600)
        os.chmod(self.salt_file, 0o600)
        
        self.master_key = key
        
    def _load_master_key(self):
        """Load existing master key"""
        password = os.environ.get('ENCRYPTION_PASSWORD')
        if not password:
            raise EncryptionError("ENCRYPTION_PASSWORD environment variable not set")
            
        # Load salt
        with open(self.salt_file, 'rb') as f:
            salt = f.read()
            
        # Derive key from password and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Load and verify stored key
        with open(self.key_file, 'rb') as f:
            stored_key = f.read()
            
        if derived_key != stored_key:
            raise EncryptionError("Invalid encryption password")
            
        self.master_key = stored_key
        
    def get_master_key(self) -> bytes:
        """Get the master encryption key"""
        if not self.master_key:
            raise EncryptionError("Master key not initialized")
        return self.master_key
        
    def generate_data_key(self, purpose: str = "default") -> bytes:
        """Generate a new data encryption key"""
        if purpose in self.data_keys:
            return self.data_keys[purpose]
            
        # Generate random key for data encryption
        data_key = Fernet.generate_key()
        self.data_keys[purpose] = data_key
        
        logger.info(f"Generated new data key for purpose: {purpose}")
        return data_key
        
    def rotate_data_key(self, purpose: str = "default") -> bytes:
        """Rotate a data encryption key"""
        new_key = Fernet.generate_key()
        old_key = self.data_keys.get(purpose)
        
        self.data_keys[purpose] = new_key
        
        logger.info(f"Rotated data key for purpose: {purpose}")
        return new_key
        
    def get_data_key(self, purpose: str = "default") -> bytes:
        """Get data encryption key for specific purpose"""
        if purpose not in self.data_keys:
            return self.generate_data_key(purpose)
        return self.data_keys[purpose]


class FieldEncryption:
    """Handles field-level encryption for sensitive data"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.fernet_cache = {}
        
    def _get_fernet(self, purpose: str = "default") -> Fernet:
        """Get Fernet instance for specific purpose"""
        if purpose not in self.fernet_cache:
            key = self.key_manager.get_data_key(purpose)
            self.fernet_cache[purpose] = Fernet(key)
        return self.fernet_cache[purpose]
        
    def encrypt_field(self, data: Union[str, bytes], purpose: str = "default") -> str:
        """Encrypt a single field"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            fernet = self._get_fernet(purpose)
            encrypted = fernet.encrypt(data)
            
            # Return as base64 string for storage
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Field encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")
            
    def decrypt_field(self, encrypted_data: str, purpose: str = "default") -> str:
        """Decrypt a single field"""
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            fernet = self._get_fernet(purpose)
            decrypted = fernet.decrypt(encrypted_bytes)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Field decryption failed: {e}")
            raise EncryptionError(f"Decryption failed: {e}")
            
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: list, 
                    purpose: str = "default") -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                # Convert to JSON string if not already string
                if not isinstance(encrypted_data[field], str):
                    field_data = json.dumps(encrypted_data[field])
                else:
                    field_data = encrypted_data[field]
                    
                encrypted_data[field] = self.encrypt_field(field_data, purpose)
                encrypted_data[f"{field}_encrypted"] = True
                
        return encrypted_data
        
    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: list,
                    purpose: str = "default") -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                try:
                    decrypted_value = self.decrypt_field(decrypted_data[field], purpose)
                    
                    # Try to parse as JSON if it looks like JSON
                    try:
                        decrypted_data[field] = json.loads(decrypted_value)
                    except (json.JSONDecodeError, TypeError):
                        decrypted_data[field] = decrypted_value
                        
                    # Remove encryption flag
                    decrypted_data.pop(f"{field}_encrypted", None)
                    
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    # Keep encrypted data if decryption fails
                    
        return decrypted_data


class FileEncryption:
    """Handles file-level encryption for large data"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        
    def encrypt_file(self, file_path: str, output_path: str = None, 
                    purpose: str = "files") -> str:
        """Encrypt a file"""
        if not output_path:
            output_path = f"{file_path}.encrypted"
            
        try:
            key = self.key_manager.get_data_key(purpose)[:32]  # AES-256 needs 32 bytes
            iv = os.urandom(16)  # AES block size
            
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            encryptor = cipher.encryptor()
            
            with open(file_path, 'rb') as infile, open(output_path, 'wb') as outfile:
                # Write IV at the beginning
                outfile.write(iv)
                
                # Encrypt file in chunks
                while True:
                    chunk = infile.read(8192)
                    if not chunk:
                        break
                        
                    # Pad the last chunk
                    if len(chunk) % 16 != 0:
                        chunk += b' ' * (16 - len(chunk) % 16)
                        
                    encrypted_chunk = encryptor.update(chunk)
                    outfile.write(encrypted_chunk)
                    
                # Finalize encryption
                outfile.write(encryptor.finalize())
                
            logger.info(f"File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise EncryptionError(f"File encryption failed: {e}")
            
    def decrypt_file(self, encrypted_path: str, output_path: str = None,
                    purpose: str = "files") -> str:
        """Decrypt a file"""
        if not output_path:
            output_path = encrypted_path.replace('.encrypted', '')
            
        try:
            key = self.key_manager.get_data_key(purpose)[:32]
            
            with open(encrypted_path, 'rb') as infile:
                # Read IV from the beginning
                iv = infile.read(16)
                
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend()
                )
                
                decryptor = cipher.decryptor()
                
                with open(output_path, 'wb') as outfile:
                    while True:
                        chunk = infile.read(8192)
                        if not chunk:
                            break
                            
                        decrypted_chunk = decryptor.update(chunk)
                        outfile.write(decrypted_chunk)
                        
                    # Finalize decryption
                    final_chunk = decryptor.finalize()
                    outfile.write(final_chunk)
                    
            # Remove padding from the last chunk
            with open(output_path, 'rb') as f:
                content = f.read()
                
            # Remove trailing spaces (padding)
            content = content.rstrip(b' ')
            
            with open(output_path, 'wb') as f:
                f.write(content)
                
            logger.info(f"File decrypted: {encrypted_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise EncryptionError(f"File decryption failed: {e}")


class DatabaseEncryption:
    """Handles database encryption integration"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.field_encryption = FieldEncryption(key_manager)
        
        # Define which fields should be encrypted for each model
        self.encryption_config = {
            'users': ['email', 'phone', 'address'],
            'transcripts': ['content', 'metadata'],
            'teams': ['settings', 'billing_info'],
            'api_keys': ['key_hash', 'secret'],
        }
        
    def encrypt_model_data(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in model data"""
        fields_to_encrypt = self.encryption_config.get(model_name, [])
        if not fields_to_encrypt:
            return data
            
        return self.field_encryption.encrypt_dict(
            data, 
            fields_to_encrypt, 
            purpose=f"db_{model_name}"
        )
        
    def decrypt_model_data(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in model data"""
        fields_to_decrypt = self.encryption_config.get(model_name, [])
        if not fields_to_decrypt:
            return data
            
        return self.field_encryption.decrypt_dict(
            data,
            fields_to_decrypt,
            purpose=f"db_{model_name}"
        )
        
    def add_encryption_fields(self, model_name: str, fields: list):
        """Add fields to encryption configuration"""
        if model_name not in self.encryption_config:
            self.encryption_config[model_name] = []
        self.encryption_config[model_name].extend(fields)
        logger.info(f"Added encryption fields for {model_name}: {fields}")


class TokenEncryption:
    """Handles encryption of tokens and session data"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.field_encryption = FieldEncryption(key_manager)
        
    def encrypt_token(self, token_data: Dict[str, Any]) -> str:
        """Encrypt token data for secure storage"""
        # Add timestamp
        token_data['created_at'] = datetime.utcnow().isoformat()
        
        # Convert to JSON and encrypt
        json_data = json.dumps(token_data)
        return self.field_encryption.encrypt_field(json_data, "tokens")
        
    def decrypt_token(self, encrypted_token: str) -> Dict[str, Any]:
        """Decrypt and validate token data"""
        try:
            json_data = self.field_encryption.decrypt_field(encrypted_token, "tokens")
            token_data = json.loads(json_data)
            
            # Check if token has expired (if expiry is set)
            if 'expires_at' in token_data:
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    raise EncryptionError("Token has expired")
                    
            return token_data
            
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise EncryptionError(f"Invalid token: {e}")
            
    def create_session_token(self, user_id: int, expires_hours: int = 24) -> str:
        """Create encrypted session token"""
        token_data = {
            'user_id': user_id,
            'type': 'session',
            'expires_at': (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat(),
            'issued_at': datetime.utcnow().isoformat()
        }
        
        return self.encrypt_token(token_data)


# Main encryption service
class EncryptionService:
    """Main encryption service that coordinates all encryption operations"""
    
    def __init__(self, key_file: str = "encryption.key", salt_file: str = "encryption.salt"):
        self.key_manager = KeyManager(key_file, salt_file)
        self.field_encryption = FieldEncryption(self.key_manager)
        self.file_encryption = FileEncryption(self.key_manager)
        self.database_encryption = DatabaseEncryption(self.key_manager)
        self.token_encryption = TokenEncryption(self.key_manager)
        
        logger.info("Encryption service initialized")
        
    def encrypt_sensitive_data(self, data: str, purpose: str = "default") -> str:
        """Encrypt sensitive string data"""
        return self.field_encryption.encrypt_field(data, purpose)
        
    def decrypt_sensitive_data(self, encrypted_data: str, purpose: str = "default") -> str:
        """Decrypt sensitive string data"""
        return self.field_encryption.decrypt_field(encrypted_data, purpose)
        
    def encrypt_file(self, file_path: str, purpose: str = "files") -> str:
        """Encrypt a file"""
        return self.file_encryption.encrypt_file(file_path, purpose=purpose)
        
    def decrypt_file(self, encrypted_path: str, purpose: str = "files") -> str:
        """Decrypt a file"""
        return self.file_encryption.decrypt_file(encrypted_path, purpose=purpose)
        
    def encrypt_database_record(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt database record"""
        return self.database_encryption.encrypt_model_data(model_name, data)
        
    def decrypt_database_record(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt database record"""
        return self.database_encryption.decrypt_model_data(model_name, data)
        
    def create_secure_token(self, token_data: Dict[str, Any]) -> str:
        """Create secure encrypted token"""
        return self.token_encryption.encrypt_token(token_data)
        
    def validate_secure_token(self, encrypted_token: str) -> Dict[str, Any]:
        """Validate and decrypt secure token"""
        return self.token_encryption.decrypt_token(encrypted_token)
        
    def rotate_keys(self, purpose: str = None):
        """Rotate encryption keys"""
        if purpose:
            self.key_manager.rotate_data_key(purpose)
            # Clear cached Fernet instances
            self.field_encryption.fernet_cache.pop(purpose, None)
        else:
            # Rotate all data keys
            for purpose in list(self.key_manager.data_keys.keys()):
                self.key_manager.rotate_data_key(purpose)
            self.field_encryption.fernet_cache.clear()
            
        logger.info(f"Rotated encryption keys for purpose: {purpose or 'all'}")


# Global encryption service instance
encryption_service = EncryptionService()