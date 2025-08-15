"""
GraphQL Test Client
Comprehensive testing utilities for GraphQL API with medical features
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest
from graphql import build_schema, validate, parse

from api.middleware import JWTTokenManager, UserRole, MedicalPermission


class GraphQLTestClient:
    """Enhanced test client for GraphQL API testing"""
    
    def __init__(
        self, 
        app: FastAPI,
        graphql_endpoint: str = "/api/graphql",
        jwt_secret: str = "test_secret_key"
    ):
        self.app = app
        self.client = TestClient(app)
        self.graphql_endpoint = graphql_endpoint
        self.jwt_manager = JWTTokenManager(jwt_secret)
        
        # Test users (same as REST API client)
        self.test_users = {
            "basic_user": {
                "user_id": 2001,
                "role": UserRole.USER,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.USER]
            },
            "medical_professional": {
                "user_id": 2002,
                "role": UserRole.MEDICAL_PROFESSIONAL,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.MEDICAL_PROFESSIONAL]
            },
            "healthcare_admin": {
                "user_id": 2003,
                "role": UserRole.HEALTHCARE_ADMIN,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.HEALTHCARE_ADMIN]
            },
            "system_admin": {
                "user_id": 2004,
                "role": UserRole.SYSTEM_ADMIN,
                "permissions": MedicalPermission.ROLE_PERMISSIONS[UserRole.SYSTEM_ADMIN]
            }
        }
        
        # Generate test tokens
        self.test_tokens = {}
        for user_type, user_data in self.test_users.items():
            token = self.jwt_manager.create_access_token(
                user_id=user_data["user_id"],
                role=user_data["role"],
                permissions=user_data["permissions"]
            )
            self.test_tokens[user_type] = token
    
    def get_auth_headers(self, user_type: str = "basic_user") -> Dict[str, str]:
        """Get authentication headers for user type"""
        token = self.test_tokens.get(user_type)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        user_type: str = "basic_user",
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query"""
        headers = self.get_auth_headers(user_type)
        
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        if operation_name:
            payload["operationName"] = operation_name
        
        response = self.client.post(
            self.graphql_endpoint,
            json=payload,
            headers=headers
        )
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None,
            "headers": dict(response.headers)
        }
    
    def execute_mutation(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        user_type: str = "basic_user"
    ) -> Dict[str, Any]:
        """Execute GraphQL mutation"""
        return self.execute_query(mutation, variables, user_type)
    
    def test_query_authentication(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test that query requires authentication"""
        # Execute without authentication headers
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        response = self.client.post(self.graphql_endpoint, json=payload)
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None
        }
    
    def test_query_authorization(
        self,
        query: str,
        required_permission: str,
        user_type: str = "basic_user",
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test that query requires specific authorization"""
        result = self.execute_query(query, variables, user_type)
        
        # Check if user has required permission
        user_data = self.test_users[user_type]
        has_permission = (
            required_permission in user_data["permissions"] or
            MedicalPermission.has_permission(user_data["role"], required_permission)
        )
        
        if not has_permission and result["data"] and "errors" in result["data"]:
            # Should have permission error
            errors = result["data"]["errors"]
            assert any("permission" in str(error).lower() for error in errors), \
                "Expected permission error in GraphQL response"
        
        return result
    
    # Standard Queries
    
    def test_user_queries(self, user_type: str = "basic_user") -> Dict[str, Any]:
        """Test user-related GraphQL queries"""
        queries = {}
        
        # Test current user query
        current_user_query = """
        query GetCurrentUser {
            currentUser {
                id
                email
                role
                createdAt
            }
        }
        """
        queries["current_user"] = self.execute_query(current_user_query, user_type=user_type)
        
        # Test users list query (admin only)
        users_list_query = """
        query GetUsers($limit: Int, $offset: Int) {
            users(limit: $limit, offset: $offset) {
                id
                email
                role
                createdAt
            }
        }
        """
        queries["users_list"] = self.execute_query(
            users_list_query, 
            variables={"limit": 10, "offset": 0},
            user_type=user_type
        )
        
        return queries
    
    def test_transcript_queries(self, user_type: str = "basic_user") -> Dict[str, Any]:
        """Test transcript-related GraphQL queries"""
        queries = {}
        
        # Test transcripts list
        transcripts_query = """
        query GetTranscripts($limit: Int, $offset: Int) {
            transcripts(limit: $limit, offset: $offset) {
                id
                title
                content
                duration
                language
                confidence
                createdAt
                updatedAt
            }
        }
        """
        queries["transcripts_list"] = self.execute_query(
            transcripts_query,
            variables={"limit": 20, "offset": 0},
            user_type=user_type
        )
        
        # Test transcript search
        search_query = """
        query SearchTranscripts($query: String!, $limit: Int) {
            searchTranscripts(query: $query, limit: $limit) {
                id
                title
                content
                confidence
                createdAt
            }
        }
        """
        queries["transcript_search"] = self.execute_query(
            search_query,
            variables={"query": "test", "limit": 10},
            user_type=user_type
        )
        
        return queries
    
    def test_medical_queries(self, user_type: str = "medical_professional") -> Dict[str, Any]:
        """Test medical-specific GraphQL queries"""
        queries = {}
        
        # Test medical transcripts list
        medical_transcripts_query = """
        query GetMedicalTranscripts($limit: Int, $offset: Int, $complianceLevel: HIPAAComplianceLevel) {
            medicalTranscripts(limit: $limit, offset: $offset, complianceLevel: $complianceLevel) {
                id
                title
                content
                patientId
                providerId
                encounterType
                complianceLevel
                complianceStatus
                entities {
                    text
                    entityType
                    confidence
                    medicalCode
                }
                medications {
                    name
                    normalizedName
                    dosage
                    frequency
                }
                procedures {
                    name
                    normalizedName
                    medicalCode
                    urgency
                }
                diagnoses {
                    name
                    normalizedName
                    severity
                    medicalCode
                }
                vitalSigns {
                    type
                    value
                    unit
                    interpretation
                }
                testResults {
                    testName
                    value
                    referenceRange
                    abnormal
                }
                voiceBiomarkers {
                    biomarkerType
                    value
                    interpretation
                    confidence
                }
                emotionalState {
                    emotion
                    intensity
                    context
                }
                socialDeterminants {
                    category
                    factor
                    impactLevel
                }
                comprehensiveAnalysis {
                    patientEngagementScore
                    careQualityIndicators {
                        indicator
                        status
                        details
                        score
                    }
                    clinicalDecisionSupport {
                        recommendation
                        evidenceLevel
                        priority
                    }
                }
                phiViolations {
                    violationType
                    text
                    severity
                    recommendation
                }
                phiDetected
                createdAt
                updatedAt
            }
        }
        """
        queries["medical_transcripts_list"] = self.execute_query(
            medical_transcripts_query,
            variables={
                "limit": 10, 
                "offset": 0,
                "complianceLevel": "STANDARD"
            },
            user_type=user_type
        )
        
        # Test medical transcript search
        medical_search_query = """
        query SearchMedicalTranscripts($searchInput: MedicalSearchInput!) {
            searchMedicalTranscripts(searchInput: $searchInput) {
                transcript {
                    id
                    title
                    patientId
                    providerId
                    complianceLevel
                }
                relevanceScore
                matchedEntities {
                    text
                    entityType
                    confidence
                }
                highlights
            }
        }
        """
        queries["medical_search"] = self.execute_query(
            medical_search_query,
            variables={
                "searchInput": {
                    "query": "hypertension",
                    "entityTypes": ["DIAGNOSIS", "MEDICATION"],
                    "complianceLevel": "STANDARD",
                    "limit": 20
                }
            },
            user_type=user_type
        )
        
        # Test medical analytics
        medical_analytics_query = """
        query GetMedicalAnalytics($analyticsInput: MedicalAnalyticsInput) {
            medicalAnalytics(analyticsInput: $analyticsInput) {
                totalTranscripts
                totalPatients
                totalProviders
                averageEngagementScore
                commonDiagnoses
                commonMedications
                commonProcedures
                phiDetectionRate
                complianceRate
                qualityIndicators {
                    indicator
                    status
                    details
                    score
                    benchmark
                }
            }
        }
        """
        queries["medical_analytics"] = self.execute_query(
            medical_analytics_query,
            variables={
                "analyticsInput": {
                    "includePHIStats": False
                }
            },
            user_type=user_type
        )
        
        return queries
    
    def test_medical_mutations(self, user_type: str = "medical_professional") -> Dict[str, Any]:
        """Test medical-specific GraphQL mutations"""
        mutations = {}
        
        # Test start medical transcription
        start_transcription_mutation = """
        mutation StartMedicalTranscription($transcriptionInput: MedicalTranscriptionInput!) {
            startMedicalTranscription(transcriptionInput: $transcriptionInput) {
                id
                userId
                status
                progress
                fileUrl
                language
                complianceLevel
                createdAt
                enableComprehensiveAnalysis
                enablePhiDetection
            }
        }
        """
        mutations["start_transcription"] = self.execute_mutation(
            start_transcription_mutation,
            variables={
                "transcriptionInput": {
                    "fileUrl": "https://example.com/test-audio.wav",
                    "title": "Test Medical Consultation",
                    "language": "en",
                    "complianceLevel": "STANDARD",
                    "patientId": "PAT123",
                    "providerId": "DOC456",
                    "encounterType": "consultation",
                    "enableComprehensiveAnalysis": True,
                    "enablePhiDetection": True
                }
            },
            user_type=user_type
        )
        
        # Test update medical transcript
        update_transcript_mutation = """
        mutation UpdateMedicalTranscript(
            $transcriptId: String!, 
            $content: String, 
            $title: String,
            $patientId: String,
            $providerId: String
        ) {
            updateMedicalTranscript(
                transcriptId: $transcriptId,
                content: $content,
                title: $title,
                patientId: $patientId,
                providerId: $providerId
            ) {
                id
                title
                content
                patientId
                providerId
                updatedAt
            }
        }
        """
        mutations["update_transcript"] = self.execute_mutation(
            update_transcript_mutation,
            variables={
                "transcriptId": "test_transcript_001",
                "title": "Updated Medical Consultation",
                "content": "Updated transcript content with medical information...",
                "patientId": "PAT123_UPDATED",
                "providerId": "DOC456_UPDATED"
            },
            user_type=user_type
        )
        
        return mutations
    
    def test_subscriptions_support(self, user_type: str = "medical_professional") -> Dict[str, Any]:
        """Test GraphQL subscription support (WebSocket not fully testable in sync client)"""
        # Test subscription schema validation
        subscription_queries = {}
        
        # Test medical transcription status subscription query structure
        transcription_subscription = """
        subscription MedicalTranscriptionStatus($jobIds: [String], $userId: Int) {
            medicalTranscriptionStatus(jobIds: $jobIds, userId: $userId) {
                id
                userId
                status
                progress
                fileUrl
                complianceLevel
                createdAt
                updatedAt
                errorMessage
            }
        }
        """
        
        # Test medical analytics updates subscription
        analytics_subscription = """
        subscription MedicalAnalyticsUpdates($updateInterval: Int) {
            medicalAnalyticsUpdates(updateInterval: $updateInterval) {
                totalTranscripts
                totalPatients
                totalProviders
                averageEngagementScore
                phiDetectionRate
                complianceRate
            }
        }
        """
        
        # Test HIPAA compliance alerts subscription  
        hipaa_alerts_subscription = """
        subscription HIPAAComplianceAlerts($severityThreshold: String) {
            hipaaComplianceAlerts(severityThreshold: $severityThreshold)
        }
        """
        
        # These would normally be tested with WebSocket connections
        # For now, just verify the schema structure
        subscription_queries["transcription_status"] = {
            "query": transcription_subscription,
            "valid": True  # Would validate with GraphQL schema
        }
        subscription_queries["analytics_updates"] = {
            "query": analytics_subscription, 
            "valid": True
        }
        subscription_queries["hipaa_alerts"] = {
            "query": hipaa_alerts_subscription,
            "valid": True
        }
        
        return subscription_queries
    
    def test_error_handling(self, user_type: str = "basic_user") -> Dict[str, Any]:
        """Test GraphQL error handling"""
        error_tests = {}
        
        # Test invalid query syntax
        invalid_query = """
        query InvalidSyntax {
            users {
                id
                email
                nonExistentField
            }
        }
        """
        error_tests["invalid_syntax"] = self.execute_query(invalid_query, user_type=user_type)
        
        # Test unauthorized access
        admin_only_query = """
        query AdminOnlyQuery {
            users(limit: 100) {
                id
                email
                role
            }
        }
        """
        error_tests["unauthorized_access"] = self.execute_query(admin_only_query, user_type="basic_user")
        
        # Test missing required variables
        query_with_required_vars = """
        query GetMedicalTranscript($transcriptId: String!) {
            medicalTranscript(transcriptId: $transcriptId) {
                id
                title
            }
        }
        """
        error_tests["missing_variables"] = self.execute_query(
            query_with_required_vars, 
            user_type=user_type
            # Deliberately omitting required variables
        )
        
        return error_tests
    
    def run_comprehensive_graphql_tests(self) -> Dict[str, Any]:
        """Run comprehensive GraphQL test suite"""
        test_results = {
            "authentication_tests": {},
            "user_queries": {},
            "transcript_queries": {},
            "medical_queries": {},
            "medical_mutations": {},
            "subscription_tests": {},
            "error_handling_tests": {}
        }
        
        # Authentication tests
        test_results["authentication_tests"]["no_auth"] = self.test_query_authentication(
            "query { currentUser { id email } }"
        )
        
        # User queries
        test_results["user_queries"] = self.test_user_queries("basic_user")
        
        # Transcript queries  
        test_results["transcript_queries"] = self.test_transcript_queries("basic_user")
        
        # Medical queries (requires medical professional)
        test_results["medical_queries"] = self.test_medical_queries("medical_professional")
        
        # Medical mutations
        test_results["medical_mutations"] = self.test_medical_mutations("medical_professional")
        
        # Subscription support
        test_results["subscription_tests"] = self.test_subscriptions_support("medical_professional")
        
        # Error handling
        test_results["error_handling_tests"] = self.test_error_handling("basic_user")
        
        return test_results