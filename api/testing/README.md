# API Testing Suite

Comprehensive testing framework for the Medical Transcription API ecosystem with support for both REST and GraphQL APIs.

## Overview

This testing suite provides utilities and fixtures for testing:
- REST API endpoints with versioning
- GraphQL queries, mutations, and subscriptions  
- Authentication and authorization
- Rate limiting
- Medical transcription features
- HIPAA compliance
- PHI detection and handling
- API versioning compatibility

## Components

### Test Clients

- **`APITestClient`** - Enhanced REST API test client with medical features
- **`GraphQLTestClient`** - GraphQL API test client with subscription support
- **`MedicalTestHelpers`** - Specialized utilities for medical transcription testing

### Test Data & Fixtures

- **`test_fixtures.py`** - Pytest fixtures for database, authentication, and mocking
- **`test_data.py`** - Comprehensive test data for various scenarios
- **`TestDataTypes`** - Enumerated test data categories

### Key Features

#### Authentication Testing
- JWT token validation
- API key authentication
- Role-based access control
- Permission checking
- Multi-user scenarios

#### Medical Features Testing
- HIPAA compliance levels (strict/standard/research)  
- PHI detection and anonymization
- Medical entity extraction
- Voice biomarker analysis
- Social determinants of health
- Comprehensive clinical analysis

#### API Versioning Testing
- Cross-version compatibility
- Endpoint deprecation handling
- Breaking change validation
- Feature availability by version

## Usage

### Basic REST API Testing

```python
from api.testing import APITestClient, TestDataTypes, get_test_data

# Initialize test client
client = APITestClient(app, jwt_secret="test_secret")

# Test authentication
client.test_endpoint_auth_required("GET", "/api/v2.1/medical/analytics")

# Test medical transcription
response = client.test_medical_transcription_endpoint(
    user_type="medical_professional",
    compliance_level="standard"
)

# Test rate limiting
responses = client.test_rate_limiting(
    "/api/v2.1/medical/transcriptions", 
    requests_count=10
)
```

### GraphQL Testing

```python
from api.testing import GraphQLTestClient

# Initialize GraphQL client
gql_client = GraphQLTestClient(app)

# Test medical queries
results = gql_client.test_medical_queries("medical_professional")

# Test mutations
mutations = gql_client.test_medical_mutations("healthcare_admin")

# Test error handling
errors = gql_client.test_error_handling()
```

### Using Test Fixtures

```python
import pytest
from api.testing import create_test_fixtures

@pytest.fixture
def api_client(test_app, auth_headers):
    return APITestClient(test_app)

def test_medical_transcription(api_client, sample_medical_data, mock_medical_transcription_service):
    with patch('medical_transcription_system.MedicalTranscriptionSystem') as mock_system:
        mock_system.return_value = mock_medical_transcription_service
        
        response = api_client.test_medical_transcription_endpoint()
        assert response.status_code == 201
```

### Test Data Access

```python
from api.testing import get_test_data, TestDataTypes

# Get medical transcripts test data
medical_data = get_test_data(TestDataTypes.MEDICAL_TRANSCRIPTS)

# Get PHI test data
phi_data = get_test_data(TestDataTypes.PHI_DATA)

# Get compliance test data
compliance_data = get_test_data(TestDataTypes.COMPLIANCE_DATA)
```

## Test Categories

### 1. Authentication & Authorization Tests

```python
def test_auth_scenarios(client):
    # Test missing authentication
    client.test_endpoint_auth_required("GET", "/protected/endpoint")
    
    # Test insufficient permissions
    client.test_endpoint_permission_required(
        "POST", "/medical/transcriptions",
        required_permission="process_medical_transcription",
        user_type="basic_user"
    )
    
    # Test role requirements
    client.test_endpoint_role_required(
        "GET", "/admin/analytics",
        required_role="healthcare_admin"
    )
```

### 2. Medical Features Tests

```python
def test_medical_features(client):
    # Test HIPAA compliance levels
    compliance_results = client.test_hipaa_compliance_levels()
    
    # Test PHI detection
    phi_response = client.test_phi_detection(
        transcript_with_phi="Patient John Doe, SSN 123-45-6789..."
    )
    
    # Test comprehensive medical analysis
    comprehensive = client.test_comprehensive_medical_features()
```

### 3. Rate Limiting Tests

```python
def test_rate_limits(client):
    # Test general rate limiting
    responses = client.test_rate_limiting("/api/v2.1/analytics")
    
    # Test medical-specific limits
    medical_responses = client.test_rate_limiting(
        "/api/v2.1/medical/transcriptions",
        user_type="medical_professional",
        requests_count=20
    )
```

### 4. API Versioning Tests

```python
def test_versioning(client):
    # Test cross-version compatibility
    version_results = client.test_api_versioning(
        "medical/compliance-levels",
        versions=["2.0", "2.1"]
    )
    
    # Verify version-specific features
    assert version_results["2.1"].status_code == 200
    assert "comprehensive_analysis" in version_results["2.1"].json()
```

### 5. GraphQL Tests

```python
def test_graphql_features(gql_client):
    # Test query authentication
    auth_result = gql_client.test_query_authentication(
        "query { currentUser { id email } }"
    )
    
    # Test medical queries
    medical_queries = gql_client.test_medical_queries("medical_professional")
    
    # Test subscription support
    subscriptions = gql_client.test_subscriptions_support()
```

## Mock Services

The suite includes comprehensive mocking for external services:

```python
from api.testing.medical_test_helpers import MedicalTestHelpers

# Mock medical transcription service
mock_service = MedicalTestHelpers.mock_medical_transcription_service()

# Mock PHI detection service  
mock_phi_service = MedicalTestHelpers.mock_phi_detection_service()

# Use in tests
with patch('medical_system.MedicalTranscriptionSystem') as mock:
    mock.return_value = mock_service
    # Run tests
```

## Test Data Generation

### Medical Test Data

```python
# Generate sample medical entities
entities = MedicalTestHelpers.create_sample_medical_entities()

# Generate voice biomarkers
biomarkers = MedicalTestHelpers.create_sample_voice_biomarkers()

# Generate social determinants
social_factors = MedicalTestHelpers.create_sample_social_determinants()

# Generate comprehensive analysis
analysis = MedicalTestHelpers.create_comprehensive_analysis()
```

### HIPAA Compliance Scenarios

```python
# Get compliance test cases
test_cases = MedicalTestHelpers.create_hipaa_compliance_test_cases()

for case in test_cases:
    print(f"Level: {case['compliance_level']}")
    print(f"Description: {case['description']}")
    print(f"Expected PHI violations: {len(case['expected_violations'])}")
```

## Running Tests

### Full Test Suite

```python
# Run comprehensive API tests
def test_full_api_suite():
    client = APITestClient(app)
    
    results = client.run_comprehensive_api_tests()
    
    # Verify all test categories passed
    assert results["authentication_tests"]["anonymous_blocked"].status_code == 401
    assert results["medical_features_tests"]["comprehensive_features"]["transcription"].status_code == 201
    
    gql_client = GraphQLTestClient(app)
    gql_results = gql_client.run_comprehensive_graphql_tests()
    
    # Verify GraphQL tests passed
    assert "errors" not in gql_results["user_queries"]["current_user"]["data"]
```

### Individual Test Categories

```bash
# Run only authentication tests
pytest tests/test_authentication.py

# Run only medical feature tests  
pytest tests/test_medical_features.py

# Run only GraphQL tests
pytest tests/test_graphql.py

# Run with specific markers
pytest -m "medical" -v
pytest -m "hipaa_compliance" -v
pytest -m "rate_limiting" -v
```

## Configuration

### Environment Variables for Testing

```bash
# Test database
TEST_DATABASE_URL=sqlite:///test_medical_transcription.db

# Test Redis
TEST_REDIS_URL=redis://localhost:6379/1

# JWT testing
TEST_JWT_SECRET=test_jwt_secret_key_for_medical_transcription

# API testing
TEST_API_BASE_URL=http://testserver
TEST_RATE_LIMIT_ENABLED=true

# Medical service mocking
MOCK_MEDICAL_TRANSCRIPTION_SERVICE=true
MOCK_PHI_DETECTION_SERVICE=true
```

### Test Configuration

```python
# conftest.py
pytest_plugins = ["api.testing.test_fixtures"]

@pytest.fixture(autouse=True)
def setup_test_environment():
    os.environ.update({
        "TESTING": "true",
        "MOCK_EXTERNAL_SERVICES": "true",
        "LOG_LEVEL": "DEBUG"
    })
```

## Best Practices

### 1. Test Isolation
- Each test uses fresh database state
- Mock external services consistently
- Clean up test data after each test

### 2. Comprehensive Coverage
- Test both success and failure scenarios
- Cover all user roles and permissions
- Test edge cases and boundary conditions

### 3. Medical Data Handling
- Use realistic but anonymized test data
- Test all HIPAA compliance levels
- Verify PHI detection accuracy

### 4. Performance Testing
- Test rate limiting thresholds
- Verify API response times
- Test with various payload sizes

### 5. Security Testing
- Verify authentication requirements
- Test authorization boundaries
- Validate input sanitization

This testing suite ensures comprehensive coverage of all API functionality while maintaining security, compliance, and performance standards required for medical transcription applications.