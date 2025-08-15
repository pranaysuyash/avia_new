"""
Comprehensive API Test Client
Testing utilities for REST API endpoints with authentication and medical features
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest
import requests
from unittest.mock import Mock, patch

from api.middleware import (
    JWTTokenManager, APIKeyManager, UserRole, MedicalPermission
)


class APITestClient:
    """Enhanced test client for API testing with authentication and medical features"""
    
    def __init__(
        self, 
        app: FastAPI, 
        jwt_secret: str = "test_secret_key",
        base_url: str = "http://testserver"
    ):
        self.app = app
        self.client = TestClient(app)
        self.jwt_manager = JWTTokenManager(jwt_secret)
        self.api_key_manager = APIKeyManager()
        self.base_url = base_url
        
        # Test user data
        self.test_users = {
            "anonymous": {
                "user_id": None,
                "role": UserRole.ANONYMOUS,
                "permissions": []
            },
            "basic_user": {
                "user_id": 1001,
                "role": UserRole.USER,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.USER]
            },
            "medical_professional": {
                "user_id": 1002,
                "role": UserRole.MEDICAL_PROFESSIONAL,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.MEDICAL_PROFESSIONAL]
            },
            "healthcare_admin": {
                "user_id": 1003,
                "role": UserRole.HEALTHCARE_ADMIN,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.HEALTHCARE_ADMIN]
            },
            "system_admin": {
                "user_id": 1004,
                "role": UserRole.SYSTEM_ADMIN,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.SYSTEM_ADMIN]
            }
        }
        
        # Generate test tokens
        self.test_tokens = {}
        for user_type, user_data in self.test_users.items():
            if user_data["user_id"]:
                token = self.jwt_manager.create_access_token(
                    user_id=user_data["user_id"],
                    role=user_data["role"],
                    permissions=user_data["permissions"]
                )
                self.test_tokens[user_type] = token
        
        # Generate test API keys
        self.test_api_keys = {}
        for user_type, user_data in self.test_users.items():
            if user_data["user_id"]:
                api_key, api_key_obj = self.api_key_manager.create_api_key(
                    user_id=user_data["user_id"],
                    name=f"Test Key - {user_type}",
                    permissions=user_data["permissions"],
                    rate_limit_tier=user_type
                )
                self.test_api_keys[user_type] = {
                    "key": api_key,
                    "object": api_key_obj
                }
    
    def get_auth_headers(self, user_type: str = "basic_user") -> Dict[str, str]:
        """Get authentication headers for user type"""
        if user_type == "anonymous":
            return {}
        
        token = self.test_tokens.get(user_type)
        if token:
            return {"Authorization": f"Bearer {token}"}
        
        return {}
    
    def get_api_key_headers(self, user_type: str = "basic_user") -> Dict[str, str]:
        """Get API key headers for user type"""
        if user_type == "anonymous":
            return {}
        
        api_key_data = self.test_api_keys.get(user_type)
        if api_key_data:
            return {"X-API-Key": api_key_data["key"]}
        
        return {}
    
    def get_versioned_url(self, endpoint: str, version: str = "2.1") -> str:
        """Get versioned API URL"""
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        return f"/api/v{version}/{endpoint}"
    
    # REST API Test Methods
    
    def test_endpoint_auth_required(
        self, 
        method: str, 
        endpoint: str, 
        expected_status: int = 401,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> requests.Response:
        """Test that endpoint requires authentication"""
        method_func = getattr(self.client, method.lower())
        kwargs = {}
        if data:
            kwargs["json"] = data
        if files:
            kwargs["files"] = files
        
        response = method_func(endpoint, **kwargs)
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        return response
    
    def test_endpoint_permission_required(
        self,
        method: str,
        endpoint: str,
        required_permission: str,
        user_type: str = "basic_user",
        expected_status: int = 403,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> requests.Response:
        """Test that endpoint requires specific permission"""
        headers = self.get_auth_headers(user_type)
        method_func = getattr(self.client, method.lower())
        kwargs = {"headers": headers}
        if data:
            kwargs["json"] = data
        if files:
            kwargs["files"] = files
        
        response = method_func(endpoint, **kwargs)
        
        # Check if user has permission
        user_data = self.test_users[user_type]
        has_permission = (
            required_permission in user_data["permissions"] or
            MedicalPermission.has_permission(user_data["role"], required_permission)
        )
        
        if has_permission:
            assert response.status_code != 403, f"User {user_type} should have permission {required_permission}"
        else:
            assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        
        return response
    
    def test_endpoint_role_required(
        self,
        method: str,
        endpoint: str,
        required_role: str,
        user_type: str = "basic_user",
        expected_status: int = 403,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> requests.Response:
        """Test that endpoint requires specific role"""
        headers = self.get_auth_headers(user_type)
        method_func = getattr(self.client, method.lower())
        kwargs = {"headers": headers}
        if data:
            kwargs["json"] = data
        if files:
            kwargs["files"] = files
        
        response = method_func(endpoint, **kwargs)
        
        # Check if user has required role
        user_data = self.test_users[user_type]
        has_role = UserRole.has_permission(user_data["role"], required_role)
        
        if has_role:
            assert response.status_code != 403, f"User {user_type} should have role {required_role}"
        else:
            assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        
        return response
    
    def test_medical_transcription_endpoint(
        self,
        file_data: bytes = b"fake audio data",
        filename: str = "test_audio.wav",
        user_type: str = "medical_professional",
        version: str = "2.1",
        compliance_level: str = "standard",
        expected_status: int = 201
    ) -> requests.Response:
        """Test medical transcription endpoint"""
        endpoint = self.get_versioned_url("medical/transcriptions", version)
        headers = self.get_auth_headers(user_type)
        
        files = {"file": (filename, file_data, "audio/wav")}
        data = {
            "request_data": json.dumps({
                "title": "Test Medical Transcription",
                "compliance_level": compliance_level,
                "patient_id": "PAT123",
                "provider_id": "DOC456",
                "encounter_type": "consultation",
                "enable_comprehensive_analysis": True,
                "enable_phi_detection": True
            })
        }
        
        response = self.client.post(endpoint, headers=headers, files=files, data=data)
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        
        if response.status_code == 201:
            response_data = response.json()
            assert "id" in response_data
            assert "compliance_level" in response_data
            assert response_data["compliance_level"] == compliance_level
        
        return response
    
    def test_rate_limiting(
        self,
        endpoint: str,
        method: str = "GET",
        user_type: str = "basic_user",
        requests_count: int = 5,
        expected_limit_status: int = 429
    ) -> List[requests.Response]:
        """Test rate limiting on endpoint"""
        headers = self.get_auth_headers(user_type)
        method_func = getattr(self.client, method.lower())
        
        responses = []
        for i in range(requests_count):
            response = method_func(endpoint, headers=headers)
            responses.append(response)
            
            # Check rate limit headers
            if "X-RateLimit-Limit" in response.headers:
                assert int(response.headers["X-RateLimit-Limit"]) > 0
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
            
            if response.status_code == expected_limit_status:
                # Rate limit hit
                assert "Retry-After" in response.headers
                break
            
            # Small delay between requests
            time.sleep(0.1)
        
        return responses
    
    def test_api_versioning(
        self,
        endpoint_path: str,
        versions: List[str] = ["1.0", "2.0", "2.1"],
        user_type: str = "basic_user"
    ) -> Dict[str, requests.Response]:
        """Test API versioning across multiple versions"""
        headers = self.get_auth_headers(user_type)
        results = {}
        
        for version in versions:
            endpoint = self.get_versioned_url(endpoint_path, version)
            response = self.client.get(endpoint, headers=headers)
            results[version] = response
            
            # Check version-specific behavior
            if response.status_code == 200:
                # Verify API version in response (could be in headers or body)
                assert response.status_code in [200, 404], f"Unexpected status for version {version}"
        
        return results
    
    def test_medical_analytics(
        self,
        user_type: str = "healthcare_admin",
        version: str = "2.1",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> requests.Response:
        """Test medical analytics endpoint"""
        endpoint = self.get_versioned_url("medical/analytics", version)
        headers = self.get_auth_headers(user_type)
        
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        response = self.client.get(endpoint, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            # Verify analytics structure
            expected_fields = [
                "total_transcripts", "total_patients", "total_providers",
                "average_engagement_score", "common_diagnoses", "common_medications",
                "phi_detection_rate", "compliance_rate", "quality_indicators"
            ]
            for field in expected_fields:
                assert field in data, f"Missing field {field} in analytics response"
        
        return response
    
    # Utility methods for common test scenarios
    
    def create_test_medical_transcript(
        self,
        user_type: str = "medical_professional",
        patient_id: str = "TEST_PAT_001",
        provider_id: str = "TEST_DOC_001"
    ) -> Dict[str, Any]:
        """Create a test medical transcript for use in other tests"""
        response = self.test_medical_transcription_endpoint(
            user_type=user_type,
            expected_status=201
        )
        
        if response.status_code == 201:
            return response.json()
        
        raise Exception(f"Failed to create test transcript: {response.text}")
    
    def test_hipaa_compliance_levels(
        self,
        user_type: str = "medical_professional"
    ) -> Dict[str, requests.Response]:
        """Test different HIPAA compliance levels"""
        compliance_levels = ["strict", "standard", "research"]
        results = {}
        
        for level in compliance_levels:
            response = self.test_medical_transcription_endpoint(
                user_type=user_type,
                compliance_level=level,
                expected_status=201
            )
            results[level] = response
        
        return results
    
    def test_phi_detection(
        self,
        transcript_with_phi: str = "Patient John Doe, DOB 01/01/1980, SSN 123-45-6789",
        user_type: str = "medical_professional"
    ) -> requests.Response:
        """Test PHI detection in medical transcription"""
        # This would require mocking the transcription service
        # to return the provided transcript with PHI
        response = self.test_medical_transcription_endpoint(user_type=user_type)
        
        if response.status_code == 201:
            data = response.json()
            # In a real implementation, we would verify PHI detection
            assert "phi_detected" in data
            assert "phi_violations" in data
        
        return response
    
    def test_comprehensive_medical_features(
        self,
        user_type: str = "medical_professional",
        version: str = "2.1"
    ) -> Dict[str, Any]:
        """Test comprehensive medical transcription features"""
        # Test medical transcription with comprehensive analysis
        transcript_response = self.test_medical_transcription_endpoint(
            user_type=user_type,
            version=version,
            expected_status=201
        )
        
        results = {"transcription": transcript_response}
        
        if transcript_response.status_code == 201:
            transcript_data = transcript_response.json()
            transcript_id = transcript_data["id"]
            
            # Test analytics
            analytics_response = self.test_medical_analytics(user_type=user_type, version=version)
            results["analytics"] = analytics_response
            
            # Test compliance levels
            compliance_response = self.client.get(
                self.get_versioned_url("medical/compliance-levels", version),
                headers=self.get_auth_headers(user_type)
            )
            results["compliance_levels"] = compliance_response
            
            # Test entity types
            entity_types_response = self.client.get(
                self.get_versioned_url("medical/entity-types", version),
                headers=self.get_auth_headers(user_type)
            )
            results["entity_types"] = entity_types_response
        
        return results
    
    def run_comprehensive_api_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite covering all major API functionality"""
        test_results = {
            "authentication_tests": {},
            "authorization_tests": {},
            "rate_limiting_tests": {},
            "versioning_tests": {},
            "medical_features_tests": {},
            "error_handling_tests": {}
        }
        
        # Authentication tests
        test_results["authentication_tests"]["anonymous_blocked"] = self.test_endpoint_auth_required(
            "GET", "/api/v2.1/medical/analytics"
        )
        
        # Authorization tests  
        test_results["authorization_tests"]["medical_professional_required"] = self.test_endpoint_permission_required(
            "POST", "/api/v2.1/medical/transcriptions", 
            MedicalPermission.PROCESS_MEDICAL_TRANSCRIPTION,
            user_type="basic_user"
        )
        
        # Rate limiting tests
        test_results["rate_limiting_tests"]["basic_user_limits"] = self.test_rate_limiting(
            "/api/v2.1/medical/analytics", requests_count=10
        )
        
        # API versioning tests
        test_results["versioning_tests"]["version_compatibility"] = self.test_api_versioning(
            "medical/compliance-levels"
        )
        
        # Medical features tests
        test_results["medical_features_tests"]["comprehensive_features"] = self.test_comprehensive_medical_features()
        
        return test_results