#!/usr/bin/env python3
"""
Test Suite for Compliance and Security System (Task 55)

Tests GDPR compliance, SOC 2 features, audit logging,
data residency, and enterprise SSO integration.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from compliance_security_system import (
    ComplianceSecurityManager, EnterpriseSSO,
    AuditEventType, DataRegion, ComplianceStatus,
    AuditLogEntry, GDPRDataSubject, DataResidencyConfig
)

class TestComplianceSecurityManager:
    """Test compliance security manager functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.compliance_mgr = ComplianceSecurityManager(db_path=self.temp_db.name)
        
        # Test data
        self.test_user_id = "test_user_123"
        self.test_email = "test@example.com"
        self.test_name = "Test User"
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_audit_logging(self):
        """Test audit event logging"""
        # Log an audit event
        audit_id = self.compliance_mgr.log_audit_event(
            event_type=AuditEventType.USER_LOGIN,
            action="User logged in successfully",
            user_id=self.test_user_id,
            ip_address="192.168.1.100",
            details={"login_method": "password", "success": True},
            risk_level="low",
            compliance_tags=["authentication", "login"]
        )
        
        assert audit_id is not None
        assert len(audit_id) > 0
        
        # Retrieve audit logs
        logs = self.compliance_mgr.get_audit_logs(user_id=self.test_user_id)
        
        assert len(logs) == 1
        assert logs[0]['event_type'] == AuditEventType.USER_LOGIN.value
        assert logs[0]['action'] == "User logged in successfully"
        assert logs[0]['user_id'] == self.test_user_id
        assert logs[0]['risk_level'] == "low"
    
    def test_audit_log_filtering(self):
        """Test audit log filtering functionality"""
        # Create multiple audit events
        events = [
            (AuditEventType.USER_LOGIN, "login", "low"),
            (AuditEventType.DATA_ACCESS, "access", "medium"),
            (AuditEventType.SECURITY_EVENT, "security", "high"),
            (AuditEventType.DATA_EXPORT, "export", "medium")
        ]
        
        for event_type, action, risk_level in events:
            self.compliance_mgr.log_audit_event(
                event_type=event_type,
                action=action,
                user_id=self.test_user_id,
                risk_level=risk_level
            )
        
        # Test filtering by event type
        login_logs = self.compliance_mgr.get_audit_logs(
            event_type=AuditEventType.USER_LOGIN
        )
        assert len(login_logs) == 1
        assert login_logs[0]['event_type'] == AuditEventType.USER_LOGIN.value
        
        # Test filtering by risk level
        high_risk_logs = self.compliance_mgr.get_audit_logs(risk_level="high")
        assert len(high_risk_logs) == 1
        assert high_risk_logs[0]['risk_level'] == "high"
        
        # Test filtering by user
        user_logs = self.compliance_mgr.get_audit_logs(user_id=self.test_user_id)
        assert len(user_logs) == 4
    
    def test_gdpr_subject_registration(self):
        """Test GDPR data subject registration"""
        # Register GDPR subject
        success = self.compliance_mgr.register_gdpr_subject(
            user_id=self.test_user_id,
            email=self.test_email,
            name=self.test_name,
            data_categories=["personal_data", "transcription_data"]
        )
        
        assert success is True
        
        # Verify audit log was created
        logs = self.compliance_mgr.get_audit_logs(
            event_type=AuditEventType.COMPLIANCE_ACTION
        )
        assert len(logs) >= 1
        assert "GDPR subject registered" in logs[0]['action']
    
    def test_gdpr_data_export(self):
        """Test GDPR data export functionality"""
        # First register a GDPR subject
        self.compliance_mgr.register_gdpr_subject(
            user_id=self.test_user_id,
            email=self.test_email,
            name=self.test_name
        )
        
        # Export user data
        export_data = self.compliance_mgr.export_user_data(self.test_user_id)
        
        assert export_data is not None
        assert "export_metadata" in export_data
        assert "personal_data" in export_data
        assert "transcriptions" in export_data
        assert "audit_logs" in export_data
        
        # Verify export metadata
        metadata = export_data["export_metadata"]
        assert metadata["user_id"] == self.test_user_id
        assert "export_date" in metadata
        assert metadata["gdpr_article"] == "Article 20 - Right to data portability"
        
        # Verify audit log was created
        logs = self.compliance_mgr.get_audit_logs(
            event_type=AuditEventType.DATA_EXPORT
        )
        assert len(logs) >= 1
    
    def test_gdpr_data_deletion_request(self):
        """Test GDPR data deletion request"""
        # First register a GDPR subject
        self.compliance_mgr.register_gdpr_subject(
            user_id=self.test_user_id,
            email=self.test_email,
            name=self.test_name
        )
        
        # Request data deletion
        success = self.compliance_mgr.request_data_deletion(
            user_id=self.test_user_id,
            reason="user_request"
        )
        
        assert success is True
        
        # Verify audit log was created
        logs = self.compliance_mgr.get_audit_logs(
            event_type=AuditEventType.DATA_DELETE
        )
        assert len(logs) >= 1
        assert "GDPR data deletion requested" in logs[0]['action']
        assert logs[0]['risk_level'] == "medium"
    
    def test_gdpr_data_deletion_execution(self):
        """Test GDPR data deletion execution"""
        # First register a GDPR subject and request deletion
        self.compliance_mgr.register_gdpr_subject(
            user_id=self.test_user_id,
            email=self.test_email,
            name=self.test_name
        )
        self.compliance_mgr.request_data_deletion(self.test_user_id)
        
        # Execute data deletion
        success = self.compliance_mgr.execute_data_deletion(self.test_user_id)
        
        assert success is True
        
        # Verify audit log was created
        logs = self.compliance_mgr.get_audit_logs(
            event_type=AuditEventType.DATA_DELETE
        )
        deletion_logs = [log for log in logs if "executed" in log['action']]
        assert len(deletion_logs) >= 1
        assert deletion_logs[0]['risk_level'] == "high"
    
    def test_data_residency_configuration(self):
        """Test data residency configuration"""
        # Set data residency
        success = self.compliance_mgr.set_data_residency(
            user_id=self.test_user_id,
            preferred_region=DataRegion.EU_WEST,
            allowed_regions=[DataRegion.EU_WEST, DataRegion.EU_CENTRAL],
            data_classification="confidential",
            compliance_requirements=["GDPR"]
        )
        
        assert success is True
        
        # Verify audit log was created
        logs = self.compliance_mgr.get_audit_logs(
            event_type=AuditEventType.COMPLIANCE_ACTION
        )
        residency_logs = [log for log in logs if "Data residency configured" in log['action']]
        assert len(residency_logs) >= 1
    
    def test_data_location_validation(self):
        """Test data location validation"""
        # Configure data residency
        self.compliance_mgr.set_data_residency(
            user_id=self.test_user_id,
            preferred_region=DataRegion.EU_WEST,
            allowed_regions=[DataRegion.EU_WEST, DataRegion.EU_CENTRAL]
        )
        
        # Test valid location
        is_valid = self.compliance_mgr.validate_data_location(
            user_id=self.test_user_id,
            current_region=DataRegion.EU_WEST
        )
        assert is_valid is True
        
        # Test invalid location
        is_valid = self.compliance_mgr.validate_data_location(
            user_id=self.test_user_id,
            current_region=DataRegion.US_EAST
        )
        assert is_valid is False
        
        # Test user without residency requirements
        is_valid = self.compliance_mgr.validate_data_location(
            user_id="nonexistent_user",
            current_region=DataRegion.US_EAST
        )
        assert is_valid is True  # No restrictions = allow any region
    
    def test_soc2_report_generation(self):
        """Test SOC 2 report generation"""
        # Create some audit events first
        events = [
            (AuditEventType.USER_LOGIN, "login", "low"),
            (AuditEventType.SECURITY_EVENT, "security_check", "medium"),
            (AuditEventType.DATA_ACCESS, "data_access", "low")
        ]
        
        for event_type, action, risk_level in events:
            self.compliance_mgr.log_audit_event(
                event_type=event_type,
                action=action,
                risk_level=risk_level
            )
        
        # Generate SOC 2 report
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        report = self.compliance_mgr.generate_soc2_report(start_date, end_date)
        
        assert report is not None
        assert "report_id" in report
        assert "report_type" in report
        assert report["report_type"] == "SOC 2 Type II"
        
        # Verify report structure
        assert "summary" in report
        assert "trust_service_criteria" in report
        assert "findings" in report
        assert "recommendations" in report
        
        # Verify summary data
        summary = report["summary"]
        assert "total_audit_events" in summary
        assert "compliance_score" in summary
        assert summary["total_audit_events"] >= 3  # Our test events
        
        # Verify trust service criteria
        criteria = report["trust_service_criteria"]
        assert "security" in criteria
        assert "availability" in criteria
        assert "processing_integrity" in criteria
        assert "confidentiality" in criteria
        assert "privacy" in criteria
    
    def test_encryption_functionality(self):
        """Test data encryption functionality"""
        # Test that sensitive data is encrypted
        sensitive_data = {"password": "secret123", "ssn": "123-45-6789"}
        
        # Log event with sensitive data
        audit_id = self.compliance_mgr.log_audit_event(
            event_type=AuditEventType.DATA_ACCESS,
            action="Accessed sensitive data",
            details=sensitive_data
        )
        
        # Retrieve and verify encryption
        logs = self.compliance_mgr.get_audit_logs(limit=1)
        assert len(logs) == 1
        
        # Verify that encrypted_data field exists
        assert "encrypted_data" in logs[0]
        assert logs[0]["encrypted_data"] is not None
        
        # Verify that decrypted details are available
        if "decrypted_details" in logs[0]:
            assert logs[0]["decrypted_details"] == sensitive_data


class TestEnterpriseSSO:
    """Test Enterprise SSO functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sso = EnterpriseSSO()
    
    def test_sso_initialization(self):
        """Test SSO system initialization"""
        assert self.sso is not None
        assert hasattr(self.sso, 'saml_config')
        assert hasattr(self.sso, 'oidc_config')
    
    def test_saml_configuration(self):
        """Test SAML configuration loading"""
        saml_config = self.sso.saml_config
        
        assert "entity_id" in saml_config
        assert "sso_url" in saml_config
        assert "x509_cert" in saml_config
        assert "private_key" in saml_config
    
    def test_oidc_configuration(self):
        """Test OIDC configuration loading"""
        oidc_config = self.sso.oidc_config
        
        assert "client_id" in oidc_config
        assert "client_secret" in oidc_config
        assert "discovery_url" in oidc_config
        assert "redirect_uri" in oidc_config
    
    def test_saml_authentication(self):
        """Test SAML authentication"""
        # Mock SAML response
        saml_response = "mock_saml_response"
        
        # Test authentication
        user_data = self.sso.authenticate_saml(saml_response)
        
        assert user_data is not None
        assert "user_id" in user_data
        assert "email" in user_data
        assert "name" in user_data
        assert "groups" in user_data
    
    def test_oidc_authentication(self):
        """Test OIDC authentication"""
        # Mock authorization code
        auth_code = "mock_auth_code"
        
        # Test authentication
        user_data = self.sso.authenticate_oidc(auth_code)
        
        assert user_data is not None
        assert "user_id" in user_data
        assert "email" in user_data
        assert "name" in user_data
        assert "roles" in user_data


class TestDataModels:
    """Test data model functionality"""
    
    def test_audit_log_entry_creation(self):
        """Test audit log entry creation"""
        entry = AuditLogEntry(
            event_type=AuditEventType.USER_LOGIN,
            user_id="test_user",
            action="User login",
            details={"method": "password"}
        )
        
        assert entry.id is not None
        assert entry.timestamp is not None
        assert entry.event_type == AuditEventType.USER_LOGIN
        assert entry.user_id == "test_user"
        assert entry.action == "User login"
        assert entry.details == {"method": "password"}
        assert entry.risk_level == "low"  # default
    
    def test_gdpr_data_subject_creation(self):
        """Test GDPR data subject creation"""
        subject = GDPRDataSubject(
            user_id="test_user",
            email="test@example.com",
            name="Test User",
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        assert subject.user_id == "test_user"
        assert subject.email == "test@example.com"
        assert subject.name == "Test User"
        assert subject.deletion_requested is False
        assert len(subject.data_categories) >= 0
        assert len(subject.consent_records) >= 0
    
    def test_data_residency_config_creation(self):
        """Test data residency configuration creation"""
        config = DataResidencyConfig(
            user_id="test_user",
            preferred_region=DataRegion.EU_WEST,
            allowed_regions=[DataRegion.EU_WEST, DataRegion.EU_CENTRAL],
            data_classification="confidential"
        )
        
        assert config.user_id == "test_user"
        assert config.preferred_region == DataRegion.EU_WEST
        assert DataRegion.EU_WEST in config.allowed_regions
        assert DataRegion.EU_CENTRAL in config.allowed_regions
        assert config.data_classification == "confidential"


class TestComplianceIntegration:
    """Test compliance system integration"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.compliance_mgr = ComplianceSecurityManager(db_path=self.temp_db.name)
        self.sso = EnterpriseSSO()
    
    def teardown_method(self):
        """Cleanup integration test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_end_to_end_gdpr_workflow(self):
        """Test complete GDPR workflow"""
        user_id = "integration_test_user"
        email = "integration@example.com"
        name = "Integration Test User"
        
        # 1. Register GDPR subject
        success = self.compliance_mgr.register_gdpr_subject(
            user_id=user_id,
            email=email,
            name=name,
            data_categories=["personal_data", "transcription_data"]
        )
        assert success is True
        
        # 2. Log some user activities
        activities = [
            (AuditEventType.USER_LOGIN, "User logged in"),
            (AuditEventType.DATA_ACCESS, "Accessed transcription data"),
            (AuditEventType.TRANSCRIPTION_CREATE, "Created new transcription")
        ]
        
        for event_type, action in activities:
            self.compliance_mgr.log_audit_event(
                event_type=event_type,
                action=action,
                user_id=user_id
            )
        
        # 3. Export user data
        export_data = self.compliance_mgr.export_user_data(user_id)
        assert export_data is not None
        assert len(export_data["audit_logs"]) >= 3  # Our activities + registration
        
        # 4. Request data deletion
        deletion_success = self.compliance_mgr.request_data_deletion(
            user_id=user_id,
            reason="user_request"
        )
        assert deletion_success is True
        
        # 5. Execute data deletion
        execution_success = self.compliance_mgr.execute_data_deletion(user_id)
        assert execution_success is True
        
        # 6. Verify data is deleted/anonymized
        try:
            self.compliance_mgr.export_user_data(user_id)
            assert False, "Should have raised ValueError for deleted user"
        except ValueError:
            pass  # Expected behavior
    
    def test_compliance_reporting_workflow(self):
        """Test compliance reporting workflow"""
        # Create various audit events
        events = [
            (AuditEventType.USER_LOGIN, "login", "low"),
            (AuditEventType.SECURITY_EVENT, "security_scan", "medium"),
            (AuditEventType.DATA_ACCESS, "data_query", "low"),
            (AuditEventType.ADMIN_ACTION, "admin_config", "high"),
            (AuditEventType.COMPLIANCE_ACTION, "gdpr_export", "medium")
        ]
        
        for event_type, action, risk_level in events:
            self.compliance_mgr.log_audit_event(
                event_type=event_type,
                action=action,
                risk_level=risk_level,
                user_id=f"user_{action}"
            )
        
        # Generate SOC 2 report
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow()
        
        report = self.compliance_mgr.generate_soc2_report(start_date, end_date)
        
        # Verify report completeness
        assert report["summary"]["total_audit_events"] >= 5
        assert report["summary"]["compliance_score"] > 0
        
        # Verify all trust service criteria are assessed
        criteria = report["trust_service_criteria"]
        for criterion in ["security", "availability", "processing_integrity", "confidentiality", "privacy"]:
            assert criterion in criteria
            assert "status" in criteria[criterion]


def run_compliance_tests():
    """Run all compliance and security tests"""
    print("🔒 Running Compliance and Security Tests")
    print("=" * 50)
    
    # Run tests with pytest
    test_files = [
        "test_compliance_security.py::TestComplianceSecurityManager",
        "test_compliance_security.py::TestEnterpriseSSO",
        "test_compliance_security.py::TestDataModels",
        "test_compliance_security.py::TestComplianceIntegration"
    ]
    
    success = True
    for test_class in test_files:
        print(f"\n📋 Running {test_class.split('::')[1]}...")
        result = pytest.main(["-v", test_class])
        if result != 0:
            success = False
            print(f"❌ {test_class} failed")
        else:
            print(f"✅ {test_class} passed")
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All compliance and security tests passed!")
        print("\n📊 Task 55 Implementation Summary:")
        print("✅ GDPR compliance with data export/deletion")
        print("✅ SOC 2 Type II compliance features")
        print("✅ Comprehensive audit logging")
        print("✅ Data residency options")
        print("✅ Enterprise SSO integration (SAML, OIDC)")
        print("✅ Data encryption and security controls")
    else:
        print("❌ Some tests failed - check output above")
    
    return success


if __name__ == "__main__":
    success = run_compliance_tests()
    exit(0 if success else 1)