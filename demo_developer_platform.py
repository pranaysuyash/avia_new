"""
Demo script for Developer Platform and API Management
Shows API key management, webhook configuration, SDK generation, and analytics.
"""
import requests
import json
import time
from datetime import datetime, timedelta
import hashlib
import hmac
from typing import Dict, List, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = None  # Will be set after login

# Headers for authenticated requests
def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def print_result(operation: str, result: Dict, success: bool = True):
    """Print operation result"""
    status = "✓" if success else "✗"
    print(f"\n{status} {operation}")
    print(json.dumps(result, indent=2, default=str))

def authenticate():
    """Authenticate and get access token"""
    global API_KEY
    
    print_section("Authentication")
    
    # Register new user
    register_data = {
        "email": "developer@example.com",
        "password": "SecurePassword123!",
        "full_name": "Developer User"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    if response.status_code == 200:
        print_result("User Registration", response.json())
    else:
        # Try login if already registered
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print_result("User Login", response.json())
    
    API_KEY = response.json()["access_token"]
    return API_KEY

def demo_api_key_management():
    """Demonstrate API key management"""
    print_section("API Key Management")
    
    # Create API key
    print("\n1. Creating API Key...")
    create_key_data = {
        "name": "Production API Key",
        "description": "Main API key for production application",
        "scopes": ["transcription.create", "transcription.read", "entities.read"],
        "rate_limit": 5000,
        "expires_in_days": 365
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/developer/api-keys",
        json=create_key_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        key_data = response.json()
        print_result("API Key Created", key_data)
        api_key_id = key_data["key_id"]
        secret_key = key_data["key"]
        
        # List API keys
        print("\n2. Listing API Keys...")
        response = requests.get(
            f"{BASE_URL}/api/v1/developer/api-keys",
            headers=get_headers()
        )
        print_result("API Keys List", response.json())
        
        # Test rate limits
        print("\n3. Testing Rate Limits...")
        test_headers = {
            "X-Api-Key": secret_key,
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/api/v1/developer/rate-limit-test",
            headers=test_headers
        )
        
        if response.status_code == 200:
            print_result("Rate Limit Status", response.json())
        
        return api_key_id, secret_key
    
    return None, None

def demo_webhook_management():
    """Demonstrate webhook management"""
    print_section("Webhook Management")
    
    # Create webhook
    print("\n1. Creating Webhook...")
    webhook_data = {
        "url": "https://example.com/webhooks/transcription",
        "events": ["transcription.completed", "transcription.failed", "entities.extracted"],
        "description": "Production webhook endpoint",
        "headers": {
            "X-Custom-Header": "CustomValue"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/developer/webhooks",
        json=webhook_data,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        webhook_info = response.json()
        print_result("Webhook Created", webhook_info)
        webhook_id = webhook_info["webhook_id"]
        webhook_secret = webhook_info["secret"]
        
        # List webhooks
        print("\n2. Listing Webhooks...")
        response = requests.get(
            f"{BASE_URL}/api/v1/developer/webhooks",
            headers=get_headers()
        )
        print_result("Webhooks List", response.json())
        
        # Test webhook
        print("\n3. Testing Webhook...")
        test_payload = {
            "event_type": "transcription.completed",
            "payload": {
                "transcription_id": "test_123",
                "status": "completed",
                "duration": 120.5,
                "word_count": 450
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/developer/webhooks/{webhook_id}/test",
            json=test_payload,
            headers=get_headers()
        )
        
        if response.status_code == 200:
            print_result("Webhook Test Result", response.json())
        
        # Demonstrate webhook signature verification
        print("\n4. Webhook Signature Verification Example...")
        payload = json.dumps(test_payload["payload"])
        signature = hmac.new(
            webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        print(f"Payload: {payload}")
        print(f"Secret: {webhook_secret}")
        print(f"Signature: {signature}")
        
        return webhook_id
    
    return None

def demo_sdk_and_documentation():
    """Demonstrate SDK and documentation access"""
    print_section("SDK and Documentation")
    
    # List available SDKs
    print("\n1. Available SDKs...")
    response = requests.get(
        f"{BASE_URL}/api/v1/developer/sdks",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        print_result("Available SDKs", response.json())
    
    # Get code examples
    print("\n2. Code Examples...")
    languages = ["python", "javascript"]
    
    for lang in languages:
        response = requests.get(
            f"{BASE_URL}/api/v1/developer/examples/{lang}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            examples = response.json()
            print(f"\n{lang.capitalize()} Examples Available:")
            for example in examples.get("examples", []):
                print(f"  - {example}")
    
    # Get specific example
    print("\n3. Python Authentication Example...")
    response = requests.get(
        f"{BASE_URL}/api/v1/developer/examples/python?operation=authentication",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        example = response.json()
        print(f"\nLanguage: {example['language']}")
        print(f"Operation: {example['operation']}")
        print("\nCode:")
        print(example['code'])
    
    # Get OpenAPI spec
    print("\n4. OpenAPI Specification...")
    response = requests.get(
        f"{BASE_URL}/api/v1/developer/openapi",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        openapi_spec = response.json()
        print(f"API Title: {openapi_spec.get('info', {}).get('title')}")
        print(f"API Version: {openapi_spec.get('info', {}).get('version')}")
        print(f"Available Endpoints: {len(openapi_spec.get('paths', {}))}")

def demo_api_usage_analytics():
    """Demonstrate API usage analytics"""
    print_section("API Usage Analytics")
    
    # Get usage statistics
    print("\n1. API Usage Statistics (Last 30 Days)...")
    response = requests.get(
        f"{BASE_URL}/api/v1/developer/usage?group_by=day",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        usage_stats = response.json()
        print(f"Total Requests: {usage_stats['total_requests']}")
        print(f"Total Errors: {usage_stats['total_errors']}")
        print(f"Error Rate: {usage_stats['error_rate']:.2f}%")
        
        print("\nTop Endpoints:")
        for endpoint, stats in list(usage_stats.get("top_endpoints", {}).items())[:5]:
            print(f"  {endpoint}:")
            print(f"    - Requests: {stats['count']}")
            print(f"    - Errors: {stats['errors']}")
            print(f"    - Avg Response Time: {stats['avg_response_time']:.2f}ms")
    
    # Get usage quota
    print("\n2. Current Usage Quota...")
    response = requests.get(
        f"{BASE_URL}/api/v1/developer/usage/quota",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        quota = response.json()
        print_result("Usage Quota", quota)

def demo_api_platform_integration():
    """Demonstrate full platform integration"""
    print_section("API Platform Integration Demo")
    
    # Use the platform API
    print("\n1. Using Platform API...")
    
    # Get platform analytics
    response = requests.get(
        f"{BASE_URL}/api/v1/platform/analytics/overview?time_range=24h",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        analytics = response.json()
        print_result("Platform Analytics", analytics)
    
    # Get supported languages for SDK
    print("\n2. SDK Language Support...")
    response = requests.get(
        f"{BASE_URL}/api/v1/platform/sdk/languages",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        languages = response.json()
        print_result("Supported SDK Languages", languages)
    
    # Generate SDK
    print("\n3. Generating Python SDK...")
    sdk_request = {
        "language": "python",
        "package_name": "vidner-python",
        "version": "1.0.0",
        "include_examples": True,
        "include_tests": True,
        "async_support": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/platform/sdk/generate",
        json=sdk_request,
        headers=get_headers()
    )
    
    if response.status_code == 200:
        sdk_info = response.json()
        print_result("SDK Generation Result", sdk_info)
    
    # Get community stats
    print("\n4. Developer Community Stats...")
    response = requests.get(
        f"{BASE_URL}/api/v1/platform/community/stats",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        community_stats = response.json()
        print_result("Community Statistics", community_stats)
    
    # Get community projects
    print("\n5. Community Showcase Projects...")
    response = requests.get(
        f"{BASE_URL}/api/v1/platform/community/showcase?sort_by=stars",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        projects = response.json()
        print("\nTop Community Projects:")
        for project in projects.get("projects", [])[:3]:
            print(f"\n  {project['name']} ⭐ {project['stars']}")
            print(f"  by @{project['author']}")
            print(f"  {project['description']}")
            print(f"  {project['github_url']}")

def demo_error_handling():
    """Demonstrate error handling"""
    print_section("Error Handling Examples")
    
    # Invalid API key
    print("\n1. Invalid API Key...")
    invalid_headers = {
        "X-Api-Key": "invalid_key_12345",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/developer/rate-limit-test",
        headers=invalid_headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Error: {response.json()}")
    
    # Rate limit exceeded simulation
    print("\n2. Rate Limit Handling...")
    print("(In production, this would demonstrate rate limit errors)")
    
    # Webhook failure handling
    print("\n3. Webhook Failure Handling...")
    print("Best practices for webhook failures:")
    print("  - Implement exponential backoff")
    print("  - Store failed webhooks for retry")
    print("  - Monitor webhook health")
    print("  - Implement circuit breakers")

def main():
    """Run the developer platform demo"""
    print("="*60)
    print("Video NER Developer Platform Demo")
    print("="*60)
    
    try:
        # Authenticate
        authenticate()
        
        # Demo API key management
        api_key_id, secret_key = demo_api_key_management()
        
        # Demo webhook management
        webhook_id = demo_webhook_management()
        
        # Demo SDK and documentation
        demo_sdk_and_documentation()
        
        # Demo API usage analytics
        demo_api_usage_analytics()
        
        # Demo platform integration
        demo_api_platform_integration()
        
        # Demo error handling
        demo_error_handling()
        
        print_section("Demo Completed Successfully!")
        
        print("\n📚 Next Steps:")
        print("1. Check out the full documentation at /docs")
        print("2. Download SDKs for your preferred language")
        print("3. Set up webhooks for real-time updates")
        print("4. Monitor your API usage and analytics")
        print("5. Join the developer community")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure the API server is running:")
        print("python run_api.py")

if __name__ == "__main__":
    main()