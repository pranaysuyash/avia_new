"""
Test Fixtures
Common test data and fixtures for API testing
"""

import pytest
import redis
from typing import Dict, Any, Optional, Generator
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from api.database import Base, get_db
from api.middleware import MedicalAuthenticationMiddleware, RateLimitingMiddleware
from api.middleware import JWTTokenManager, APIKeyManager


@pytest.fixture
def test_engine():
    """Create test database engine (SQLite in-memory)"""
    engine = create_engine(
        "sqlite:///test_medical_transcription.db",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture 
def test_db_session(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(test_db_session):
    """Override database dependency for testing"""
    def _override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    return _override_get_db


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = Mock(spec=redis.Redis)
    
    # Mock Redis operations
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.pipeline.return_value.execute.return_value = [1, True]
    
    return mock_redis


@pytest.fixture
def jwt_secret():
    """JWT secret key for testing"""
    return "test_jwt_secret_key_for_medical_transcription_api"


@pytest.fixture
def jwt_token_manager(jwt_secret):
    """JWT token manager for testing"""
    return JWTTokenManager(jwt_secret)


@pytest.fixture
def api_key_manager(mock_redis):
    """API key manager for testing"""
    return APIKeyManager(mock_redis)


@pytest.fixture
def test_app(override_get_db, mock_redis, jwt_secret):
    """Create test FastAPI application"""
    from api.main import app
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Add test middleware
    app.add_middleware(
        MedicalAuthenticationMiddleware,
        jwt_secret=jwt_secret,
        redis_client=mock_redis
    )
    
    app.add_middleware(
        RateLimitingMiddleware,
        redis_client=mock_redis
    )
    
    return app


@pytest.fixture
def test_client(test_app):
    """Test client for API testing"""
    return TestClient(test_app)


@pytest.fixture
def test_users():
    """Test user data"""
    return {
        "basic_user": {
            "id": 1001,
            "email": "basic.user@test.com",
            "role": "user",
            "is_active": True
        },
        "medical_professional": {
            "id": 1002,
            "email": "doctor@hospital.com",
            "role": "medical_professional",
            "is_active": True
        },
        "healthcare_admin": {
            "id": 1003,
            "email": "admin@healthcare.com", 
            "role": "healthcare_admin",
            "is_active": True
        },
        "system_admin": {
            "id": 1004,
            "email": "admin@system.com",
            "role": "system_admin",
            "is_active": True
        }
    }


@pytest.fixture
def test_tokens(jwt_token_manager, test_users):
    """Generate test JWT tokens"""
    from api.middleware import UserRole, MedicalPermission
    
    tokens = {}
    role_mapping = {
        "user": UserRole.USER,
        "medical_professional": UserRole.MEDICAL_PROFESSIONAL,
        "healthcare_admin": UserRole.HEALTHCARE_ADMIN,
        "system_admin": UserRole.SYSTEM_ADMIN
    }
    
    for user_type, user_data in test_users.items():
        role = role_mapping[user_data["role"]]
        permissions = MedicalPermission.ROLE_PERMISSIONS.get(role, [])
        
        token = jwt_token_manager.create_access_token(
            user_id=user_data["id"],
            role=role,
            permissions=permissions
        )
        tokens[user_type] = token
    
    return tokens


@pytest.fixture
def test_api_keys(api_key_manager, test_users):
    """Generate test API keys"""
    from api.middleware import MedicalPermission, UserRole
    
    api_keys = {}
    role_mapping = {
        "user": UserRole.USER,
        "medical_professional": UserRole.MEDICAL_PROFESSIONAL,
        "healthcare_admin": UserRole.HEALTHCARE_ADMIN,
        "system_admin": UserRole.SYSTEM_ADMIN
    }
    
    for user_type, user_data in test_users.items():
        role = role_mapping[user_data["role"]]
        permissions = MedicalPermission.ROLE_PERMISSIONS.get(role, [])
        
        api_key, api_key_obj = api_key_manager.create_api_key(
            user_id=user_data["id"],
            name=f"Test API Key - {user_type}",
            permissions=permissions,
            rate_limit_tier=user_type
        )
        
        api_keys[user_type] = {
            "key": api_key,
            "object": api_key_obj
        }
    
    return api_keys


@pytest.fixture
def auth_headers(test_tokens):
    """Authentication headers for different user types"""
    headers = {}
    for user_type, token in test_tokens.items():
        headers[user_type] = {"Authorization": f"Bearer {token}"}
    
    headers["anonymous"] = {}  # No auth headers
    return headers


@pytest.fixture
def api_key_headers(test_api_keys):
    """API key headers for different user types"""
    headers = {}
    for user_type, api_key_data in test_api_keys.items():
        headers[user_type] = {"X-API-Key": api_key_data["key"]}
    
    headers["anonymous"] = {}  # No API key
    return headers


@pytest.fixture
def sample_medical_data():
    """Sample medical data for testing"""
    from api.testing.medical_test_helpers import MedicalTestHelpers
    
    return {
        "transcript": MedicalTestHelpers.create_sample_medical_transcript(),
        "entities": MedicalTestHelpers.create_sample_medical_entities(),
        "voice_biomarkers": MedicalTestHelpers.create_sample_voice_biomarkers(),
        "social_determinants": MedicalTestHelpers.create_sample_social_determinants(),
        "phi_violations": MedicalTestHelpers.create_sample_phi_violations(),
        "comprehensive_analysis": MedicalTestHelpers.create_comprehensive_analysis()
    }


@pytest.fixture
def sample_audio_file():
    """Sample audio file for testing"""
    from api.testing.medical_test_helpers import MedicalTestHelpers
    return MedicalTestHelpers.create_test_audio_file()


@pytest.fixture
def mock_medical_transcription_service():
    """Mock medical transcription service"""
    from api.testing.medical_test_helpers import MedicalTestHelpers
    return MedicalTestHelpers.mock_medical_transcription_service()


@pytest.fixture
def mock_phi_detection_service():
    """Mock PHI detection service"""
    from api.testing.medical_test_helpers import MedicalTestHelpers
    return MedicalTestHelpers.mock_phi_detection_service()


@pytest.fixture
def hipaa_test_cases():
    """HIPAA compliance test cases"""
    from api.testing.medical_test_helpers import MedicalTestHelpers
    return MedicalTestHelpers.create_hipaa_compliance_test_cases()


@pytest.fixture
def medical_test_scenarios():
    """Medical test scenarios"""
    from api.testing.medical_test_helpers import MedicalTestHelpers
    return MedicalTestHelpers.generate_medical_test_scenarios()


@pytest.fixture 
def versioned_endpoints():
    """API versioned endpoints for testing"""
    return {
        "v1.0": {
            "transcriptions": "/api/v1.0/transcriptions",
            "users": "/api/v1.0/users",
            "analytics": "/api/v1.0/analytics"
        },
        "v2.0": {
            "transcriptions": "/api/v2.0/transcriptions", 
            "medical_transcriptions": "/api/v2.0/medical/transcriptions",
            "medical_compliance": "/api/v2.0/medical/compliance-levels",
            "users": "/api/v2.0/users",
            "analytics": "/api/v2.0/analytics"
        },
        "v2.1": {
            "transcriptions": "/api/v2.1/transcriptions",
            "medical_transcriptions": "/api/v2.1/medical/transcriptions",
            "medical_analytics": "/api/v2.1/medical/analytics", 
            "medical_compliance": "/api/v2.1/medical/compliance-levels",
            "medical_entity_types": "/api/v2.1/medical/entity-types",
            "users": "/api/v2.1/users",
            "analytics": "/api/v2.1/analytics"
        }
    }


@pytest.fixture
def graphql_test_queries():
    """GraphQL test queries"""
    return {
        "current_user": """
            query GetCurrentUser {
                currentUser {
                    id
                    email
                    role
                    createdAt
                }
            }
        """,
        "medical_transcripts": """
            query GetMedicalTranscripts($limit: Int, $offset: Int) {
                medicalTranscripts(limit: $limit, offset: $offset) {
                    id
                    title
                    content
                    patientId
                    providerId
                    complianceLevel
                    entities {
                        text
                        entityType
                        confidence
                    }
                    createdAt
                }
            }
        """,
        "medical_search": """
            query SearchMedicalTranscripts($searchInput: MedicalSearchInput!) {
                searchMedicalTranscripts(searchInput: $searchInput) {
                    transcript {
                        id
                        title
                        patientId
                    }
                    relevanceScore
                    matchedEntities {
                        text
                        entityType
                    }
                }
            }
        """,
        "medical_analytics": """
            query GetMedicalAnalytics {
                medicalAnalytics {
                    totalTranscripts
                    totalPatients
                    averageEngagementScore
                    phiDetectionRate
                    complianceRate
                }
            }
        """
    }


@pytest.fixture
def graphql_test_mutations():
    """GraphQL test mutations"""
    return {
        "start_medical_transcription": """
            mutation StartMedicalTranscription($transcriptionInput: MedicalTranscriptionInput!) {
                startMedicalTranscription(transcriptionInput: $transcriptionInput) {
                    id
                    userId
                    status
                    complianceLevel
                    createdAt
                }
            }
        """,
        "update_medical_transcript": """
            mutation UpdateMedicalTranscript($transcriptId: String!, $content: String, $title: String) {
                updateMedicalTranscript(transcriptId: $transcriptId, content: $content, title: $title) {
                    id
                    title
                    content
                    updatedAt
                }
            }
        """
    }


def create_test_fixtures():
    """Factory function to create all test fixtures programmatically"""
    fixtures = {
        "test_engine": test_engine,
        "test_db_session": test_db_session,
        "override_get_db": override_get_db,
        "mock_redis": mock_redis,
        "jwt_secret": jwt_secret,
        "jwt_token_manager": jwt_token_manager,
        "api_key_manager": api_key_manager,
        "test_app": test_app,
        "test_client": test_client,
        "test_users": test_users,
        "test_tokens": test_tokens,
        "test_api_keys": test_api_keys,
        "auth_headers": auth_headers,
        "api_key_headers": api_key_headers,
        "sample_medical_data": sample_medical_data,
        "sample_audio_file": sample_audio_file,
        "mock_medical_transcription_service": mock_medical_transcription_service,
        "mock_phi_detection_service": mock_phi_detection_service,
        "hipaa_test_cases": hipaa_test_cases,
        "medical_test_scenarios": medical_test_scenarios,
        "versioned_endpoints": versioned_endpoints,
        "graphql_test_queries": graphql_test_queries,
        "graphql_test_mutations": graphql_test_mutations
    }
    
    return fixtures


# Utility functions for test setup

def setup_test_database(engine):
    """Set up test database with sample data"""
    Base.metadata.create_all(bind=engine)
    # Add any initial test data here
    pass


def cleanup_test_database(engine):
    """Clean up test database"""
    Base.metadata.drop_all(bind=engine)


def create_test_user(session, user_data: Dict[str, Any]):
    """Create test user in database"""
    from api.database import User
    
    user = User(
        email=user_data["email"],
        role=user_data["role"],
        is_active=user_data.get("is_active", True)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_test_transcript(session, user_id: int, transcript_data: Dict[str, Any]):
    """Create test transcript in database"""
    from api.database import Transcript
    
    transcript = Transcript(
        user_id=user_id,
        title=transcript_data.get("title", "Test Transcript"),
        content=transcript_data.get("content", "Test transcript content"),
        file_name=transcript_data.get("file_name", "test.wav"),
        language=transcript_data.get("language", "en"),
        confidence=transcript_data.get("confidence", 0.95),
        metadata=transcript_data.get("metadata", {})
    )
    session.add(transcript)
    session.commit()
    session.refresh(transcript)
    return transcript