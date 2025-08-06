"""
Data Encryption and Key Management System

Provides comprehensive encryption for data at rest and in transit
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import json
import secrets
from pydantic import BaseModel, Field, validator
import hashlib
import hmac

class EncryptionLevel(str, Enum):
    """Encryption levels for different data types"""
    STANDARD = "standard"      # AES-256
    HIGH = "high"             # AES-256 + RSA
    MAXIMUM = "maximum"       # AES-256 + RSA + HSM

class KeyType(str, Enum):
    """Types of encryption keys"""
    MASTER = "master"
    DATA_ENCRYPTION = "data_encryption"
    KEY_ENCRYPTION = "key_encryption"
    SIGNING = "signing"
    CUSTOMER_MANAGED = "customer_managed"

class KeyStatus(str, Enum):
    """Key lifecycle status"""
    ACTIVE = "active"
    ROTATING = "rotating"
    DISABLED = "disabled"
    DESTROYED = "destroyed"

class DataClassification(str, Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

class EncryptionKey(BaseModel):
    """Encryption key metadata"""
    key_id: str
    key_type: KeyType
    algorithm: str
    key_size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rotated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: KeyStatus = KeyStatus.ACTIVE
    
    # Key material (encrypted)
    encrypted_key: str
    key_check_value: str
    
    # Metadata
    purpose: str
    owner: str
    classification: DataClassification
    
    # Audit
    created_by: str
    last_used_at: Optional[datetime] = None
    usage_count: int = 0

class EncryptedData(BaseModel):
    """Encrypted data container"""
    data_id: str
    encrypted_data: str
    encryption_metadata: Dict[str, Any]
    key_id: str
    algorithm: str
    iv: Optional[str]  # Initialization vector
    aad: Optional[str]  # Additional authenticated data
    tag: Optional[str]  # Authentication tag
    encrypted_at: datetime = Field(default_factory=datetime.utcnow)

class KeyRotationPolicy(BaseModel):
    """Key rotation policy"""
    key_type: KeyType
    rotation_period_days: int
    grace_period_days: int = 7
    automatic_rotation: bool = True
    notification_days_before: int = 30

class DataEncryptionService:
    """Main data encryption service"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        """Initialize encryption service with master key"""
        if master_key:
            self.master_key = master_key
        else:
            # Generate master key (in production, retrieve from HSM/KMS)
            self.master_key = Fernet.generate_key()
        
        self.master_fernet = Fernet(self.master_key)
        self.keys: Dict[str, EncryptionKey] = {}
        self.rotation_policies: Dict[KeyType, KeyRotationPolicy] = self._init_rotation_policies()
        
        # Initialize key encryption keys
        self._initialize_kek()
    
    def _initialize_kek(self):
        """Initialize key encryption keys"""
        # Generate RSA key pair for key encryption
        self.kek_private = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        self.kek_public = self.kek_private.public_key()
    
    def _init_rotation_policies(self) -> Dict[KeyType, KeyRotationPolicy]:
        """Initialize default key rotation policies"""
        return {
            KeyType.MASTER: KeyRotationPolicy(
                key_type=KeyType.MASTER,
                rotation_period_days=365,
                automatic_rotation=False,
                notification_days_before=60
            ),
            KeyType.DATA_ENCRYPTION: KeyRotationPolicy(
                key_type=KeyType.DATA_ENCRYPTION,
                rotation_period_days=90,
                automatic_rotation=True
            ),
            KeyType.KEY_ENCRYPTION: KeyRotationPolicy(
                key_type=KeyType.KEY_ENCRYPTION,
                rotation_period_days=180,
                automatic_rotation=True
            ),
            KeyType.SIGNING: KeyRotationPolicy(
                key_type=KeyType.SIGNING,
                rotation_period_days=90,
                automatic_rotation=True
            )
        }
    
    def generate_data_key(
        self,
        purpose: str,
        owner: str,
        classification: DataClassification = DataClassification.CONFIDENTIAL,
        key_type: KeyType = KeyType.DATA_ENCRYPTION
    ) -> Tuple[str, bytes]:
        """Generate new data encryption key"""
        # Generate AES-256 key
        key = os.urandom(32)  # 256 bits
        
        # Create key metadata
        key_id = f"key_{secrets.token_urlsafe(16)}"
        
        # Encrypt key with KEK
        encrypted_key = self.kek_public.encrypt(
            key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Calculate key check value
        key_check_value = hashlib.sha256(key).hexdigest()[:8]
        
        # Store key metadata
        encryption_key = EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            algorithm="AES-256-GCM",
            key_size=256,
            encrypted_key=base64.b64encode(encrypted_key).decode(),
            key_check_value=key_check_value,
            purpose=purpose,
            owner=owner,
            classification=classification,
            created_by=owner
        )
        
        self.keys[key_id] = encryption_key
        
        return key_id, key
    
    def encrypt_data(
        self,
        data: bytes,
        classification: DataClassification = DataClassification.CONFIDENTIAL,
        owner: str = "system",
        purpose: str = "data_encryption"
    ) -> EncryptedData:
        """Encrypt data with appropriate encryption level"""
        # Generate or get data key
        key_id, key = self.generate_data_key(purpose, owner, classification)
        
        # Use AES-256-GCM for authenticated encryption
        iv = os.urandom(12)  # 96-bit IV for GCM
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # Add metadata as additional authenticated data
        aad = json.dumps({
            "key_id": key_id,
            "classification": classification.value,
            "owner": owner,
            "timestamp": datetime.utcnow().isoformat()
        }).encode()
        
        encryptor.authenticate_additional_data(aad)
        
        # Encrypt data
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Get authentication tag
        tag = encryptor.tag
        
        # Create encrypted data object
        encrypted_data = EncryptedData(
            data_id=f"data_{secrets.token_urlsafe(16)}",
            encrypted_data=base64.b64encode(ciphertext).decode(),
            encryption_metadata={
                "algorithm": "AES-256-GCM",
                "key_size": 256,
                "classification": classification.value
            },
            key_id=key_id,
            algorithm="AES-256-GCM",
            iv=base64.b64encode(iv).decode(),
            aad=base64.b64encode(aad).decode(),
            tag=base64.b64encode(tag).decode()
        )
        
        # Update key usage
        self.keys[key_id].last_used_at = datetime.utcnow()
        self.keys[key_id].usage_count += 1
        
        # Clean up key from memory
        key = b'\x00' * len(key)
        
        return encrypted_data
    
    def decrypt_data(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt encrypted data"""
        # Get key
        key_metadata = self.keys.get(encrypted_data.key_id)
        if not key_metadata:
            raise ValueError(f"Key {encrypted_data.key_id} not found")
        
        if key_metadata.status != KeyStatus.ACTIVE:
            raise ValueError(f"Key {encrypted_data.key_id} is not active")
        
        # Decrypt key
        encrypted_key = base64.b64decode(key_metadata.encrypted_key)
        key = self.kek_private.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Verify key check value
        if hashlib.sha256(key).hexdigest()[:8] != key_metadata.key_check_value:
            raise ValueError("Key check value mismatch")
        
        # Decrypt data
        iv = base64.b64decode(encrypted_data.iv)
        ciphertext = base64.b64decode(encrypted_data.encrypted_data)
        tag = base64.b64decode(encrypted_data.tag)
        aad = base64.b64decode(encrypted_data.aad)
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Update key usage
        key_metadata.last_used_at = datetime.utcnow()
        key_metadata.usage_count += 1
        
        # Clean up key from memory
        key = b'\x00' * len(key)
        
        return plaintext
    
    def rotate_key(self, key_id: str) -> str:
        """Rotate encryption key"""
        old_key = self.keys.get(key_id)
        if not old_key:
            raise ValueError(f"Key {key_id} not found")
        
        # Mark old key as rotating
        old_key.status = KeyStatus.ROTATING
        
        # Generate new key
        new_key_id, _ = self.generate_data_key(
            purpose=old_key.purpose,
            owner=old_key.owner,
            classification=old_key.classification,
            key_type=old_key.key_type
        )
        
        # Link keys for migration
        new_key = self.keys[new_key_id]
        new_key.rotated_at = datetime.utcnow()
        
        return new_key_id
    
    def check_key_rotation_needed(self) -> List[str]:
        """Check which keys need rotation"""
        keys_needing_rotation = []
        now = datetime.utcnow()
        
        for key_id, key in self.keys.items():
            if key.status != KeyStatus.ACTIVE:
                continue
            
            policy = self.rotation_policies.get(key.key_type)
            if not policy or not policy.automatic_rotation:
                continue
            
            # Check if rotation is needed
            key_age = now - key.created_at
            if key_age.days >= policy.rotation_period_days:
                keys_needing_rotation.append(key_id)
        
        return keys_needing_rotation
    
    def create_secure_token(
        self,
        data: Dict[str, Any],
        expiry_hours: int = 24
    ) -> str:
        """Create secure, signed token"""
        # Add expiry
        data["exp"] = (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat()
        
        # Serialize data
        payload = json.dumps(data, sort_keys=True).encode()
        
        # Encrypt with Fernet (includes HMAC)
        token = self.master_fernet.encrypt(payload)
        
        return base64.urlsafe_b64encode(token).decode()
    
    def verify_secure_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decrypt secure token"""
        try:
            # Decode token
            encrypted_token = base64.urlsafe_b64decode(token.encode())
            
            # Decrypt
            payload = self.master_fernet.decrypt(encrypted_token)
            
            # Parse data
            data = json.loads(payload.decode())
            
            # Check expiry
            exp_str = data.get("exp")
            if exp_str:
                exp = datetime.fromisoformat(exp_str)
                if datetime.utcnow() > exp:
                    return None
            
            return data
            
        except Exception:
            return None
    
    def encrypt_field(
        self,
        field_value: str,
        field_name: str,
        record_id: str
    ) -> str:
        """Encrypt individual field (for database field-level encryption)"""
        # Create deterministic key for searchable encryption
        field_key = hashlib.pbkdf2_hmac(
            'sha256',
            f"{field_name}:{record_id}".encode(),
            self.master_key[:16],  # Use part of master key as salt
            100000
        )[:32]
        
        # Encrypt field
        fernet = Fernet(base64.urlsafe_b64encode(field_key))
        encrypted = fernet.encrypt(field_value.encode())
        
        return base64.b64encode(encrypted).decode()
    
    def decrypt_field(
        self,
        encrypted_value: str,
        field_name: str,
        record_id: str
    ) -> str:
        """Decrypt individual field"""
        # Recreate field key
        field_key = hashlib.pbkdf2_hmac(
            'sha256',
            f"{field_name}:{record_id}".encode(),
            self.master_key[:16],
            100000
        )[:32]
        
        # Decrypt field
        fernet = Fernet(base64.urlsafe_b64encode(field_key))
        encrypted = base64.b64decode(encrypted_value)
        decrypted = fernet.decrypt(encrypted)
        
        return decrypted.decode()
    
    def create_encryption_envelope(
        self,
        data: bytes,
        recipients: List[str]
    ) -> Dict[str, Any]:
        """Create encryption envelope for multiple recipients"""
        # Generate data encryption key
        dek = os.urandom(32)
        
        # Encrypt data with DEK
        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(dek),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Encrypt DEK for each recipient
        recipient_keys = {}
        for recipient in recipients:
            # In production, get recipient's public key
            encrypted_dek = self.kek_public.encrypt(
                dek,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            recipient_keys[recipient] = base64.b64encode(encrypted_dek).decode()
        
        # Create envelope
        envelope = {
            "version": "1.0",
            "algorithm": "AES-256-GCM",
            "iv": base64.b64encode(iv).decode(),
            "tag": base64.b64encode(encryptor.tag).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "recipients": recipient_keys,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return envelope
    
    def export_key_audit_log(self) -> List[Dict[str, Any]]:
        """Export key usage audit log"""
        audit_log = []
        
        for key_id, key in self.keys.items():
            audit_log.append({
                "key_id": key_id,
                "key_type": key.key_type.value,
                "status": key.status.value,
                "created_at": key.created_at.isoformat(),
                "created_by": key.created_by,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "usage_count": key.usage_count,
                "classification": key.classification.value,
                "purpose": key.purpose
            })
        
        return audit_log

class FieldEncryption:
    """Helper for field-level encryption in databases"""
    
    def __init__(self, encryption_service: DataEncryptionService):
        self.encryption_service = encryption_service
    
    def encrypt_pii_fields(self, record: Dict[str, Any], record_id: str) -> Dict[str, Any]:
        """Encrypt PII fields in a record"""
        pii_fields = [
            'ssn', 'social_security_number',
            'credit_card', 'bank_account',
            'email', 'phone_number',
            'date_of_birth', 'drivers_license',
            'passport_number', 'tax_id'
        ]
        
        encrypted_record = record.copy()
        
        for field, value in record.items():
            if any(pii in field.lower() for pii in pii_fields):
                if isinstance(value, str) and value:
                    encrypted_record[field] = self.encryption_service.encrypt_field(
                        value, field, record_id
                    )
                    encrypted_record[f"{field}_encrypted"] = True
        
        return encrypted_record
    
    def decrypt_pii_fields(self, record: Dict[str, Any], record_id: str) -> Dict[str, Any]:
        """Decrypt PII fields in a record"""
        decrypted_record = record.copy()
        
        for field, value in record.items():
            if field.endswith("_encrypted") and record.get(field):
                actual_field = field.replace("_encrypted", "")
                if actual_field in record:
                    decrypted_record[actual_field] = self.encryption_service.decrypt_field(
                        record[actual_field], actual_field, record_id
                    )
                    del decrypted_record[field]
        
        return decrypted_record

class TransparentEncryption:
    """Transparent encryption for files and data streams"""
    
    def __init__(self, encryption_service: DataEncryptionService):
        self.encryption_service = encryption_service
    
    def encrypt_file(
        self,
        input_path: str,
        output_path: str,
        classification: DataClassification = DataClassification.CONFIDENTIAL
    ):
        """Encrypt file with streaming encryption"""
        chunk_size = 64 * 1024  # 64KB chunks
        
        # Generate data key
        key_id, key = self.encryption_service.generate_data_key(
            purpose="file_encryption",
            owner="system",
            classification=classification
        )
        
        # Initialize cipher
        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Write header
        header = {
            "version": "1.0",
            "key_id": key_id,
            "algorithm": "AES-256-GCM",
            "iv": base64.b64encode(iv).decode(),
            "original_size": os.path.getsize(input_path)
        }
        
        with open(output_path, 'wb') as outfile:
            # Write header length and header
            header_bytes = json.dumps(header).encode()
            outfile.write(len(header_bytes).to_bytes(4, 'big'))
            outfile.write(header_bytes)
            
            # Encrypt file content
            with open(input_path, 'rb') as infile:
                while chunk := infile.read(chunk_size):
                    outfile.write(encryptor.update(chunk))
            
            outfile.write(encryptor.finalize())
            outfile.write(encryptor.tag)
    
    def decrypt_file(self, input_path: str, output_path: str):
        """Decrypt file with streaming decryption"""
        with open(input_path, 'rb') as infile:
            # Read header
            header_length = int.from_bytes(infile.read(4), 'big')
            header = json.loads(infile.read(header_length).decode())
            
            # Get decryption key
            key_metadata = self.encryption_service.keys.get(header["key_id"])
            if not key_metadata:
                raise ValueError(f"Key {header['key_id']} not found")
            
            # Decrypt key
            encrypted_key = base64.b64decode(key_metadata.encrypted_key)
            key = self.encryption_service.kek_private.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Initialize cipher
            iv = base64.b64decode(header["iv"])
            
            # Read all remaining data
            remaining_data = infile.read()
            ciphertext = remaining_data[:-16]  # Last 16 bytes are tag
            tag = remaining_data[-16:]
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            with open(output_path, 'wb') as outfile:
                outfile.write(decryptor.update(ciphertext))
                outfile.write(decryptor.finalize())

# Example usage
if __name__ == "__main__":
    # Initialize encryption service
    encryption_service = DataEncryptionService()
    
    # Encrypt sensitive data
    sensitive_data = b"This is highly confidential information"
    encrypted = encryption_service.encrypt_data(
        sensitive_data,
        classification=DataClassification.RESTRICTED,
        owner="admin",
        purpose="demo"
    )
    
    print(f"Encrypted data ID: {encrypted.data_id}")
    print(f"Key ID: {encrypted.key_id}")
    print(f"Algorithm: {encrypted.algorithm}")
    
    # Decrypt data
    decrypted = encryption_service.decrypt_data(encrypted)
    print(f"Decrypted: {decrypted.decode()}")
    
    # Field-level encryption
    field_encryption = FieldEncryption(encryption_service)
    
    user_record = {
        "id": "user_123",
        "name": "John Doe",
        "email": "john@example.com",
        "ssn": "123-45-6789",
        "phone_number": "+1-555-0123"
    }
    
    # Encrypt PII fields
    encrypted_record = field_encryption.encrypt_pii_fields(user_record, "user_123")
    print(f"\nEncrypted record: {encrypted_record}")
    
    # Decrypt PII fields
    decrypted_record = field_encryption.decrypt_pii_fields(encrypted_record, "user_123")
    print(f"\nDecrypted record: {decrypted_record}")
    
    # Check key rotation
    keys_to_rotate = encryption_service.check_key_rotation_needed()
    print(f"\nKeys needing rotation: {keys_to_rotate}")
    
    # Export audit log
    audit_log = encryption_service.export_key_audit_log()
    print(f"\nKey audit log entries: {len(audit_log)}")