"""
Security & Compliance Testing Suite
Comprehensive tests for security features and compliance requirements
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
from enhanced_security_compliance import (
    SecurityOrchestrator,
    EncryptionManager,
    AuthenticationManager,
    AccessControlManager,
    ComplianceManager,
    SecurityScanner,
    InputValidator,
    SecurityLevel,
    ComplianceFramework,
    AuditEventType,
    SecurityPolicy
)

class TestEncryptionManager:
    """Test encryption functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.encryption = EncryptionManager()
        
    def test_symmetric_encryption(self):
        """Test symmetric encryption and decryption"""
        data = b"Sensitive data"
        encrypted = self.encryption.encrypt_symmetric(data)
        
        assert encrypted != data
        assert isinstance(encrypted, bytes)
        
        decrypted = self.encryption.decrypt_symmetric(encrypted)
        assert decrypted == data
        
    def test_asymmetric_encryption(self):
        """Test asymmetric encryption and decryption"""
        data = b"Secret message"
        encrypted = self.encryption.encrypt_asymmetric(data)
        
        assert encrypted != data
        assert isinstance(encrypted, bytes)
        
        decrypted = self.encryption.decrypt_asymmetric(encrypted)
        assert decrypted == data
        
    def test_field_encryption(self):
        """Test field-level encryption"""
        value = "user@example.com"
        encrypted = self.encryption.encrypt_field(value)
        
        assert encrypted != value
        assert isinstance(encrypted, str)
        
        decrypted = self.encryption.decrypt_field(encrypted)
        assert decrypted == value
        
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        
        hashed, salt = self.encryption.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert isinstance(salt, str)
        
        # Verify correct password
        assert self.encryption.verify_password(password, hashed, salt)
        
        # Verify incorrect password
        assert not self.encryption.verify_password("WrongPassword", hashed, salt)
        
    def test_data_key_generation(self):
        """Test data key generation"""
        data_key, encrypted_key = self.encryption.generate_data_key()
        
        assert isinstance(data_key, bytes)
        assert isinstance(encrypted_key, bytes)
        assert data_key != encrypted_key
        
        # Verify we can decrypt the key
        decrypted_key = self.encryption.decrypt_symmetric(encrypted_key)
        assert decrypted_key == data_key

class TestAuthenticationManager:
    """Test authentication functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        encryption = EncryptionManager()
        self.auth = AuthenticationManager(encryption)
        
    def test_mfa_generation(self):
        """Test MFA secret generation"""
        user_id = "test_user"
        secret, uri = self.auth.generate_mfa_secret(user_id)
        
        assert isinstance(secret, str)
        assert isinstance(uri, str)
        assert "otpauth://" in uri
        assert user_id in uri
        
    def test_mfa_verification(self):
        """Test MFA token verification"""
        user_id = "test_user"
        secret, _ = self.auth.generate_mfa_secret(user_id)
        
        # Generate valid token
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        assert self.auth.verify_mfa_token(user_id, valid_token)
        assert not self.auth.verify_mfa_token(user_id, "000000")
        assert not self.auth.verify_mfa_token("unknown_user", valid_token)
        
    def test_session_management(self):
        """Test session creation and validation"""
        user_id = "test_user"
        ip = "192.168.1.1"
        user_agent = "TestAgent"
        
        # Create session
        session_id = self.auth.create_session(user_id, ip, user_agent)
        assert isinstance(session_id, str)
        
        # Validate session
        validated_user = self.auth.validate_session(session_id, ip, user_agent)
        assert validated_user == user_id
        
        # Invalid session
        assert self.auth.validate_session("invalid_id", ip, user_agent) is None
        
        # Wrong IP
        assert self.auth.validate_session(session_id, "192.168.1.2", user_agent) is None
        
    def test_brute_force_detection(self):
        """Test brute force attack detection"""
        identifier = "test_user"
        
        # No attempts yet
        assert not self.auth.check_brute_force(identifier)
        
        # Record failed attempts
        for _ in range(5):
            self.auth.record_failed_attempt(identifier)
            
        # Should detect brute force
        assert self.auth.check_brute_force(identifier)
        
    def test_session_expiry(self):
        """Test session expiration"""
        user_id = "test_user"
        ip = "192.168.1.1"
        user_agent = "TestAgent"
        
        # Create session with short expiry
        session_id = self.auth.create_session(user_id, ip, user_agent, expires_in=1)
        
        # Valid immediately
        assert self.auth.validate_session(session_id, ip, user_agent) == user_id
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Should be expired
        assert self.auth.validate_session(session_id, ip, user_agent) is None

class TestAccessControlManager:
    """Test access control functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.acl = AccessControlManager()
        
    def test_role_assignment(self):
        """Test role assignment and revocation"""
        user_id = "test_user"
        
        # Assign role
        self.acl.assign_role(user_id, "user")
        assert "user" in self.acl.user_roles[user_id]
        
        # Assign another role
        self.acl.assign_role(user_id, "manager")
        assert "manager" in self.acl.user_roles[user_id]
        assert len(self.acl.user_roles[user_id]) == 2
        
        # Revoke role
        self.acl.revoke_role(user_id, "user")
        assert "user" not in self.acl.user_roles[user_id]
        assert "manager" in self.acl.user_roles[user_id]
        
    def test_permission_checking(self):
        """Test permission validation"""
        user_id = "test_user"
        admin_id = "admin_user"
        
        # Assign roles
        self.acl.assign_role(user_id, "user")
        self.acl.assign_role(admin_id, "admin")
        
        # Admin has all permissions
        assert self.acl.check_permission(admin_id, "any_resource", "any_action")
        
        # User has limited permissions
        assert not self.acl.check_permission(user_id, "admin_resource", "write")
        
        # Set resource ownership
        self.acl.set_resource_permissions(
            "doc_123",
            user_id,
            {"read": ["public"], "write": [user_id]}
        )
        
        # User can access own resource
        assert self.acl.check_permission(user_id, "doc_123", "read")
        
    def test_hierarchical_permissions(self):
        """Test hierarchical permission system"""
        manager_id = "manager_user"
        
        # Assign manager role
        self.acl.assign_role(manager_id, "manager")
        
        # Manager permissions
        assert self.acl.check_permission(manager_id, "team_resource", "read")
        assert self.acl.check_permission(manager_id, "team_resource", "write")
        assert not self.acl.check_permission(manager_id, "other_team", "delete")

class TestComplianceManager:
    """Test compliance functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        encryption = EncryptionManager()
        self.compliance = ComplianceManager(encryption)
        
    @pytest.mark.asyncio
    async def test_gdpr_compliance(self):
        """Test GDPR compliance checks"""
        # Record consent
        self.compliance.record_consent("user_123", "data_processing", explicit=True)
        
        context = {
            'user_id': 'user_123',
            'data_fields': ['email', 'name'],
            'required_fields': ['email'],
            'has_erasure_mechanism': True,
            'has_export_mechanism': True
        }
        
        result = await self.compliance.check_compliance(
            ComplianceFramework.GDPR,
            context
        )
        
        assert result['framework'] == 'gdpr'
        assert result['compliant'] is True
        assert len(result['checks']) == 4
        
    @pytest.mark.asyncio
    async def test_soc2_compliance(self):
        """Test SOC2 compliance checks"""
        context = {
            'encrypted_at_rest': True,
            'encrypted_in_transit': True,
            'has_rbac': True,
            'has_mfa': True,
            'has_monitoring': True,
            'has_alerting': True,
            'has_incident_plan': True
        }
        
        result = await self.compliance.check_compliance(
            ComplianceFramework.SOC2,
            context
        )
        
        assert result['framework'] == 'soc2'
        assert result['compliant'] is True
        
    @pytest.mark.asyncio
    async def test_hipaa_compliance(self):
        """Test HIPAA compliance checks"""
        context = {
            'encrypted_at_rest': True,
            'encrypted_in_transit': True,
            'has_minimum_necessary': True,
            'has_access_logs': True,
            'has_audit_logs': True,
            'log_retention_days': 2200,
            'has_integrity_controls': True
        }
        
        result = await self.compliance.check_compliance(
            ComplianceFramework.HIPAA,
            context
        )
        
        assert result['framework'] == 'hipaa'
        assert result['compliant'] is True
        
    @pytest.mark.asyncio
    async def test_data_requests(self):
        """Test GDPR data request handling"""
        user_id = "user_123"
        
        # Test access request
        result = await self.compliance.handle_data_request(user_id, 'access')
        assert result['status'] == 'pending'
        assert 'request_id' in result
        
        # Test portability request
        result = await self.compliance.handle_data_request(user_id, 'portability')
        assert result['status'] == 'pending'
        
        # Test erasure request
        result = await self.compliance.handle_data_request(user_id, 'erasure')
        assert result['status'] == 'pending'
        
        # Test invalid request
        result = await self.compliance.handle_data_request(user_id, 'invalid')
        assert result['status'] == 'error'

class TestInputValidator:
    """Test input validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = InputValidator()
        
    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        valid, email = self.validator.validate_email("user@example.com")
        assert valid is True
        assert email == "user@example.com"
        
        valid, email = self.validator.validate_email("test.user+tag@domain.co.uk")
        assert valid is True
        
        # Invalid emails
        valid, msg = self.validator.validate_email("invalid.email")
        assert valid is False
        
        valid, msg = self.validator.validate_email("@example.com")
        assert valid is False
        
    def test_url_validation(self):
        """Test URL validation"""
        assert self.validator.validate_url("https://example.com")
        assert self.validator.validate_url("http://sub.domain.com/path")
        assert not self.validator.validate_url("not a url")
        assert not self.validator.validate_url("ftp://invalid")
        
    def test_ip_validation(self):
        """Test IP address validation"""
        assert self.validator.validate_ip("192.168.1.1")
        assert self.validator.validate_ip("10.0.0.1")
        assert self.validator.validate_ip("::1")
        assert self.validator.validate_ip("2001:db8::1")
        assert not self.validator.validate_ip("999.999.999.999")
        assert not self.validator.validate_ip("not.an.ip")
        
    def test_sql_injection_detection(self):
        """Test SQL injection detection"""
        # Detect SQL injection attempts
        assert self.validator.detect_sql_injection("SELECT * FROM users")
        assert self.validator.detect_sql_injection("1' OR '1'='1")
        assert self.validator.detect_sql_injection("'; DROP TABLE users--")
        assert self.validator.detect_sql_injection("UNION SELECT password")
        
        # Normal input should pass
        assert not self.validator.detect_sql_injection("This is normal text")
        assert not self.validator.detect_sql_injection("user@example.com")
        
    def test_xss_detection(self):
        """Test XSS attack detection"""
        # Detect XSS attempts
        assert self.validator.detect_xss("<script>alert('XSS')</script>")
        assert self.validator.detect_xss("javascript:alert(1)")
        assert self.validator.detect_xss("<img onerror='alert(1)' src='x'>")
        assert self.validator.detect_xss("<iframe src='evil.com'></iframe>")
        
        # Normal HTML should pass
        assert not self.validator.detect_xss("<p>Normal paragraph</p>")
        assert not self.validator.detect_xss("Plain text content")
        
    def test_html_sanitization(self):
        """Test HTML sanitization"""
        # Sanitize dangerous HTML
        dirty = "<script>alert('XSS')</script><p>Content</p>"
        clean = self.validator.sanitize_html(dirty)
        assert "<script>" not in clean
        assert "<p>" in clean
        
        # Preserve safe tags
        safe = "<p>Text with <strong>bold</strong> and <a href='#'>link</a></p>"
        sanitized = self.validator.sanitize_html(safe)
        assert "<strong>" in sanitized
        assert "<a" in sanitized

class TestSecurityScanner:
    """Test security scanning functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.scanner = SecurityScanner()
        
    @pytest.mark.asyncio
    async def test_dependency_scanning(self):
        """Test dependency vulnerability scanning"""
        # Create temporary requirements file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("requests==2.25.0\n")
            f.write("flask==1.1.0\n")
            temp_file = f.name
            
        try:
            # Mock safety check
            with patch('enhanced_security_compliance.safety_check') as mock_safety:
                mock_safety.return_value = [
                    {
                        'package': 'flask',
                        'installed_version': '1.1.0',
                        'vulnerability': 'CVE-2021-12345',
                        'severity': 'high'
                    }
                ]
                
                vulnerabilities = await self.scanner.scan_dependencies(temp_file)
                
                assert len(vulnerabilities) == 1
                assert vulnerabilities[0]['package'] == 'flask'
                assert vulnerabilities[0]['severity'] == 'high'
        finally:
            os.unlink(temp_file)
            
    @pytest.mark.asyncio
    async def test_anomaly_detection(self):
        """Test anomaly detection"""
        # Normal data
        normal_data = [
            {'cpu': 50, 'memory': 60, 'requests': 100},
            {'cpu': 55, 'memory': 62, 'requests': 110},
            {'cpu': 48, 'memory': 58, 'requests': 95}
        ]
        
        # Add anomalous data
        anomalous_data = normal_data + [
            {'cpu': 95, 'memory': 98, 'requests': 1000}  # Anomaly
        ]
        
        # Train detector on normal data
        import pandas as pd
        df = pd.DataFrame(normal_data)
        self.scanner.anomaly_detector.fit(df.values)
        
        # Detect anomalies
        anomalies = await self.scanner.detect_anomalies(anomalous_data)
        
        # Should detect at least one anomaly
        assert len(anomalies) > 0

class TestSecurityOrchestrator:
    """Test security orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator fixture"""
        config = {'database_url': 'sqlite:///:memory:'}
        return SecurityOrchestrator(config)
        
    @pytest.mark.asyncio
    async def test_authentication_flow(self, orchestrator):
        """Test complete authentication flow"""
        # Mock password verification
        orchestrator._verify_user_password = Mock(return_value=True)
        
        # Generate MFA secret for user
        orchestrator.auth.generate_mfa_secret("admin")
        
        # Mock MFA verification
        orchestrator.auth.verify_mfa_token = Mock(return_value=True)
        
        result = await orchestrator.authenticate_user(
            "admin",
            "password",
            "123456",
            "192.168.1.1",
            "TestAgent"
        )
        
        assert result['success'] is True
        assert 'session_id' in result
        assert result['user_id'] == 'admin'
        
        # Verify audit log was created
        assert len(orchestrator.audit_logs) == 1
        assert orchestrator.audit_logs[0].event_type == AuditEventType.AUTH_SUCCESS
        
    @pytest.mark.asyncio
    async def test_authorization_flow(self, orchestrator):
        """Test authorization flow"""
        # Setup user with role
        orchestrator.access_control.assign_role("user_123", "user")
        orchestrator.access_control.set_resource_permissions(
            "doc_456",
            "user_123",
            {}
        )
        
        # Test authorization
        authorized = await orchestrator.authorize_action(
            "user_123",
            "doc_456",
            "read",
            "192.168.1.1"
        )
        
        assert authorized is True
        
        # Verify audit log
        assert len(orchestrator.audit_logs) == 1
        assert orchestrator.audit_logs[0].event_type == AuditEventType.DATA_ACCESS
        
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, orchestrator):
        """Test brute force protection"""
        # Record multiple failed attempts
        for i in range(6):
            orchestrator.auth.record_failed_attempt("attacker")
            
        result = await orchestrator.authenticate_user(
            "attacker",
            "password",
            None,
            "192.168.1.1",
            "TestAgent"
        )
        
        assert result['success'] is False
        assert 'Too many failed attempts' in result['error']
        
    def test_data_encryption(self, orchestrator):
        """Test data encryption and decryption"""
        sensitive_data = "SSN: 123-45-6789"
        
        # Encrypt
        encrypted = orchestrator.encrypt_data(sensitive_data)
        assert encrypted != sensitive_data
        
        # Decrypt
        decrypted = orchestrator.decrypt_data(encrypted)
        assert decrypted == sensitive_data
        
    @pytest.mark.asyncio
    async def test_security_scanning(self, orchestrator):
        """Test security scanning"""
        # Mock scanner methods
        orchestrator.scanner.scan_dependencies = AsyncMock(return_value=[])
        orchestrator.scanner.scan_code = AsyncMock(return_value=[])
        
        results = await orchestrator.perform_security_scan()
        
        assert 'timestamp' in results
        assert 'scans' in results
        assert 'gdpr_compliance' in results['scans']
        assert 'soc2_compliance' in results['scans']
        
    def test_input_validation_integration(self, orchestrator):
        """Test input validation integration"""
        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE users--"
        valid, msg = orchestrator.validator.validate_input(malicious_input)
        assert valid is False
        assert "SQL injection" in msg
        
        # Test XSS prevention
        xss_input = "<script>alert('XSS')</script>"
        valid, msg = orchestrator.validator.validate_input(xss_input)
        assert valid is False
        assert "XSS" in msg
        
        # Test valid input
        safe_input = "Normal user input"
        valid, cleaned = orchestrator.validator.validate_input(safe_input)
        assert valid is True
        assert cleaned == safe_input

# Performance and Load Testing
class TestSecurityPerformance:
    """Test security system performance"""
    
    @pytest.mark.asyncio
    async def test_encryption_performance(self):
        """Test encryption performance"""
        encryption = EncryptionManager()
        
        # Test bulk encryption
        start = datetime.utcnow()
        for _ in range(1000):
            data = b"Test data " * 100
            encrypted = encryption.encrypt_symmetric(data)
            decrypted = encryption.decrypt_symmetric(encrypted)
            
        duration = (datetime.utcnow() - start).total_seconds()
        
        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 1000 operations
        
    @pytest.mark.asyncio
    async def test_authentication_performance(self):
        """Test authentication performance"""
        encryption = EncryptionManager()
        auth = AuthenticationManager(encryption)
        
        # Create multiple sessions
        start = datetime.utcnow()
        sessions = []
        
        for i in range(100):
            session_id = auth.create_session(
                f"user_{i}",
                f"192.168.1.{i}",
                "TestAgent"
            )
            sessions.append(session_id)
            
        # Validate all sessions
        for session_id in sessions:
            auth.validate_session(session_id, "192.168.1.0", "TestAgent")
            
        duration = (datetime.utcnow() - start).total_seconds()
        
        # Should handle 100 sessions quickly
        assert duration < 1.0

# Integration Testing
@pytest.mark.integration
class TestSecurityIntegration:
    """Integration tests for security system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_flow(self):
        """Test complete security flow"""
        config = {'database_url': 'sqlite:///:memory:'}
        orchestrator = SecurityOrchestrator(config)
        
        # 1. User registration (mock)
        user_id = "new_user"
        password = "SecurePass123!"
        
        # 2. Generate MFA
        secret, uri = orchestrator.auth.generate_mfa_secret(user_id)
        
        # 3. Authenticate
        orchestrator._verify_user_password = Mock(return_value=True)
        orchestrator.auth.verify_mfa_token = Mock(return_value=True)
        
        auth_result = await orchestrator.authenticate_user(
            user_id,
            password,
            "123456",
            "192.168.1.1",
            "Mozilla/5.0"
        )
        
        assert auth_result['success']
        session_id = auth_result['session_id']
        
        # 4. Assign role
        orchestrator.access_control.assign_role(user_id, "user")
        
        # 5. Create resource
        resource_id = "doc_789"
        orchestrator.access_control.set_resource_permissions(
            resource_id,
            user_id,
            {}
        )
        
        # 6. Access resource
        authorized = await orchestrator.authorize_action(
            user_id,
            resource_id,
            "read",
            "192.168.1.1"
        )
        
        assert authorized
        
        # 7. Encrypt sensitive data
        sensitive = "Credit Card: 1234-5678-9012-3456"
        encrypted = orchestrator.encrypt_data(sensitive)
        
        # 8. Check compliance
        gdpr_result = await orchestrator.compliance.check_compliance(
            ComplianceFramework.GDPR,
            {
                'user_id': user_id,
                'data_fields': ['email'],
                'required_fields': ['email'],
                'has_erasure_mechanism': True,
                'has_export_mechanism': True
            }
        )
        
        # Verify no consent recorded yet
        assert not gdpr_result['compliant']
        
        # 9. Record consent
        orchestrator.compliance.record_consent(user_id, "data_processing")
        
        # 10. Verify audit trail
        assert len(orchestrator.audit_logs) > 0
        
        # Verify all components worked together
        assert session_id in orchestrator.auth.sessions
        assert user_id in orchestrator.access_control.user_roles
        assert resource_id in orchestrator.access_control.resource_permissions

if __name__ == "__main__":
    pytest.main([__file__, "-v"])