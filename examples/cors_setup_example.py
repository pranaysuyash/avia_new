"""
Example: Setting up CORS for the API
This example shows different ways to configure CORS for various deployment scenarios
"""

import os
from fastapi import FastAPI
from api.middleware.cors_config import setup_cors, create_cors_config, CORSPresets

# Example 1: Basic setup with environment-based configuration
def setup_basic_cors():
    """Use default configuration based on ENVIRONMENT variable"""
    app = FastAPI(title="Audio/Video Transcription API")
    
    # This will automatically configure CORS based on ENVIRONMENT
    # - development: allows localhost origins
    # - staging: allows staging domains + localhost
    # - production: restricts to production domains only
    setup_cors(app)
    
    return app


# Example 2: Custom configuration for specific domains
def setup_custom_cors():
    """Configure CORS with specific allowed origins"""
    app = FastAPI(title="Audio/Video Transcription API")
    
    # Create custom configuration
    cors_config = create_cors_config(
        allowed_origins=[
            "https://app.yourdomain.com",
            "https://admin.yourdomain.com",
            "https://mobile.yourdomain.com"
        ],
        allow_credentials=True,
        max_age=86400  # Cache preflight for 24 hours
    )
    
    setup_cors(app, cors_config)
    
    return app


# Example 3: Using presets for common scenarios
def setup_public_api_cors():
    """Configure CORS for a public API (no authentication)"""
    app = FastAPI(title="Public Transcription API")
    
    # Use public API preset
    cors_config = CORSPresets.public_api()
    setup_cors(app, cors_config)
    
    return app


# Example 4: Environment-specific configuration
def setup_environment_specific_cors():
    """Configure CORS differently for each environment"""
    app = FastAPI(title="Audio/Video Transcription API")
    
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Production: Strict configuration
        cors_config = create_cors_config(
            allowed_origins=[
                "https://app.transcription.com",
                "https://www.transcription.com"
            ],
            allow_credentials=True,
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
            max_age=86400  # 24 hours
        )
    elif environment == "staging":
        # Staging: Allow staging domains and some localhost for testing
        cors_config = create_cors_config(
            allowed_origins=[
                "https://staging.transcription.com",
                "https://app-staging.transcription.com",
                "http://localhost:3000",  # For local testing
                "http://localhost:8501"   # Streamlit
            ],
            allow_credentials=True,
            max_age=3600  # 1 hour
        )
    else:
        # Development: Permissive configuration
        cors_config = CORSPresets.development()
    
    setup_cors(app, cors_config)
    
    return app


# Example 5: Multi-tenant CORS configuration
def setup_multitenant_cors():
    """Configure CORS for multi-tenant application"""
    from api.middleware.cors_config import DynamicCORSConfig
    
    app = FastAPI(title="Multi-tenant Transcription API")
    
    # Define how to extract tenant from request
    def resolve_tenant(request):
        # Extract from subdomain
        host = request.headers.get("host", "")
        if ".transcription.com" in host:
            tenant = host.split(".")[0]
            return tenant
        return "default"
    
    # Create dynamic configuration
    dynamic_cors = DynamicCORSConfig(resolve_tenant)
    
    # Add tenant-specific configurations
    dynamic_cors.add_tenant_config("acme", create_cors_config(
        allowed_origins=["https://acme.app.com", "https://admin.acme.com"]
    ))
    
    dynamic_cors.add_tenant_config("globex", create_cors_config(
        allowed_origins=["https://globex.enterprise.com"]
    ))
    
    # Default configuration for unknown tenants
    dynamic_cors.add_tenant_config("default", create_cors_config(
        allowed_origins=["https://app.transcription.com"]
    ))
    
    # Note: For dynamic CORS, you'd need custom middleware implementation
    # This is just an example of the configuration approach
    
    return app


# Example 6: Using environment variables
def setup_cors_from_env():
    """Configure CORS entirely from environment variables"""
    app = FastAPI(title="Audio/Video Transcription API")
    
    # Set these environment variables:
    # CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
    # CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE
    # CORS_ALLOWED_HEADERS=Content-Type,Authorization,X-API-Key
    # CORS_ALLOW_CREDENTIALS=true
    # CORS_MAX_AGE=86400
    
    # The CORSConfig class will automatically read these
    setup_cors(app)
    
    return app


# Example 7: Testing CORS configuration
def test_cors_headers():
    """Example of testing CORS configuration"""
    from fastapi.testclient import TestClient
    
    app = setup_custom_cors()
    
    @app.get("/api/test")
    def test_endpoint():
        return {"message": "CORS test successful"}
    
    client = TestClient(app)
    
    # Test preflight request
    response = client.options(
        "/api/test",
        headers={
            "Origin": "https://app.yourdomain.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
    )
    
    print(f"Preflight Status: {response.status_code}")
    print(f"Allowed Origin: {response.headers.get('access-control-allow-origin')}")
    print(f"Allowed Methods: {response.headers.get('access-control-allow-methods')}")
    print(f"Allowed Headers: {response.headers.get('access-control-allow-headers')}")
    print(f"Max Age: {response.headers.get('access-control-max-age')}")
    
    # Test actual request
    response = client.get(
        "/api/test",
        headers={
            "Origin": "https://app.yourdomain.com",
            "Authorization": "Bearer test-token"
        }
    )
    
    print(f"\nActual Request Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"CORS Headers: {response.headers.get('access-control-allow-origin')}")


if __name__ == "__main__":
    # Example: Run the appropriate setup based on use case
    
    # For production deployment
    # app = setup_environment_specific_cors()
    
    # For public API
    # app = setup_public_api_cors()
    
    # For testing
    test_cors_headers()
    
    print("\nCORS configuration examples completed!")
    print("Choose the appropriate setup method for your deployment scenario.")