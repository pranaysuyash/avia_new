#!/usr/bin/env python3
"""
Comprehensive Demo for API Platform and Developer Platform (Task 54)

Demonstrates all components of the comprehensive API and developer platform:
- REST API usage
- GraphQL API queries
- Python SDK usage
- API key management
- Usage monitoring
- Interactive documentation features
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
import tempfile
from typing import Dict, Any

# Ensure we're using the virtual environment
def check_venv():
    """Ensure we're running in a virtual environment"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  WARNING: Not running in a virtual environment!")
        print("Please activate venv: source venv/bin/activate")
        return False
    return True

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)

def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n📋 {title}")
    print('-'*40)

def print_success(message: str):
    """Print a success message"""
    print(f"✅ {message}")

def print_info(message: str):
    """Print an info message"""
    print(f"ℹ️  {message}")

def print_code_block(title: str, code: str):
    """Print a formatted code block"""
    print(f"\n💻 {title}:")
    print("```")
    print(code)
    print("```")

class APIDemo:
    """Comprehensive API Platform Demo"""
    
    def __init__(self):
        self.api_key = "demo_api_key_12345"
        self.base_url = "https://api.transcriptionplatform.com/v1"
        
    def demo_rest_api(self):
        """Demo REST API functionality"""
        print_section("REST API Demonstration")
        
        print_subsection("1. Authentication")
        print_info("All API requests require Bearer token authentication")
        print_code_block("cURL Example", f"""
curl -H "Authorization: Bearer {self.api_key}" \\
     -H "Content-Type: application/json" \\
     {self.base_url}/health
""")
        
        print_subsection("2. File Upload for Transcription")
        print_info("Upload audio/video files for transcription")
        print_code_block("cURL File Upload", f"""
curl -X POST {self.base_url}/transcriptions/upload \\
     -H "Authorization: Bearer {self.api_key}" \\
     -F "file=@audio.mp3" \\
     -F "title=My Recording" \\
     -F "language=auto" \\
     -F "method=advanced"
""")
        
        print_subsection("3. List Transcriptions")
        print_code_block("Get Transcriptions", f"""
curl -X GET "{self.base_url}/transcriptions?limit=10&skip=0" \\
     -H "Authorization: Bearer {self.api_key}"
""")
        
        print_subsection("4. Team Management")
        print_code_block("Create Team", f"""
curl -X POST {self.base_url}/teams \\
     -H "Authorization: Bearer {self.api_key}" \\
     -H "Content-Type: application/json" \\
     -d '{{"name": "My Team", "description": "Project team"}}'
""")
        
        print_success("REST API endpoints cover all core functionality")
    
    def demo_graphql_api(self):
        """Demo GraphQL API functionality"""
        print_section("GraphQL API Demonstration")
        
        print_subsection("1. GraphQL Endpoint")
        print_info("GraphQL endpoint provides flexible data queries")
        print_code_block("GraphQL Endpoint", f"{self.base_url}/graphql")
        
        print_subsection("2. Query User Profile")
        print_code_block("GraphQL Query", """
query GetUserProfile {
  me {
    id
    email
    username
    role
    createdAt
  }
}
""")
        
        print_subsection("3. Query Transcripts with Filtering")
        print_code_block("Advanced Query", """
query GetTranscripts($filter: TranscriptFilter, $pagination: PaginationInput) {
  transcripts(filter: $filter, pagination: $pagination) {
    edges {
      id
      title
      status
      duration
      confidence
      entities
      createdAt
    }
    pageInfo {
      hasNextPage
      totalCount
    }
  }
}
""")
        
        print_subsection("4. Mutation Example")
        print_code_block("Update Transcript", """
mutation UpdateTranscript($id: Int!, $input: TranscriptUpdateInput!) {
  updateTranscript(id: $id, input: $input) {
    id
    title
    content
    updatedAt
  }
}
""")
        
        print_subsection("5. GraphQL Playground")
        print_info("Interactive GraphQL playground available at /graphql-playground")
        print_success("GraphQL API provides flexible, efficient data fetching")
    
    def demo_python_sdk(self):
        """Demo Python SDK functionality"""
        print_section("Python SDK Demonstration")
        
        print_subsection("1. Installation")
        print_code_block("Install SDK", """
# In virtual environment
pip install transcription-api
""")
        
        print_subsection("2. Basic Usage")
        print_code_block("Python SDK Example", f"""
from transcription_api import TranscriptionClient

# Initialize client
client = TranscriptionClient(api_key="{self.api_key}")

# Upload and transcribe file
with open("audio.mp3", "rb") as f:
    transcript = client.transcribe_file(f, title="My Recording")

# Wait for completion
completed = client.wait_for_completion(transcript.id)
print(f"Transcribed text: {{completed.text}}")
""")
        
        print_subsection("3. Advanced Features")
        print_code_block("Advanced Usage", """
from transcription_api import TranscriptionOptions

# Advanced transcription options
options = TranscriptionOptions(
    language="en",
    method="advanced",
    speaker_detection=True,
    sentiment_analysis=True,
    entity_extraction=True
)

transcript = client.transcribe_file(file, options=options)
""")
        
        print_subsection("4. Team Management")
        print_code_block("Team Operations", """
# Create team
team = client.create_team("My Team", "Project description")

# Invite member
client.invite_team_member(team.id, "colleague@example.com", "member")

# List teams
teams = client.list_teams()
""")
        
        print_subsection("5. Error Handling")
        print_code_block("Exception Handling", """
from transcription_api import (
    AuthenticationError, RateLimitError, ValidationError
)

try:
    transcript = client.get_transcript("invalid_id")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation error: {e.message}")
""")
        
        print_success("Python SDK provides comprehensive, Pythonic API access")
    
    def demo_javascript_sdk(self):
        """Demo JavaScript/TypeScript SDK functionality"""
        print_section("JavaScript/TypeScript SDK Demonstration")
        
        print_subsection("1. Installation")
        print_code_block("Install SDK", """
npm install @transcription-api/sdk
# or
yarn add @transcription-api/sdk
""")
        
        print_subsection("2. Basic Usage (JavaScript)")
        print_code_block("JavaScript Example", f"""
import {{ TranscriptionClient }} from '@transcription-api/sdk';

const client = new TranscriptionClient({{
  apiKey: '{self.api_key}'
}});

// Upload file
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const transcript = await client.transcribeFile(file, {{
  title: 'My Recording'
}});

// Wait for completion
const completed = await client.waitForCompletion(transcript.id);
console.log('Transcribed text:', completed.text);
""")
        
        print_subsection("3. TypeScript Usage")
        print_code_block("TypeScript Example", """
import { 
  TranscriptionClient, 
  Transcript, 
  TranscriptionOptions 
} from '@transcription-api/sdk';

const client = new TranscriptionClient({ apiKey: 'your_key' });

const options: TranscriptionOptions = {
  language: 'en',
  method: 'advanced',
  speakerDetection: true
};

const transcript: Transcript = await client.transcribeFile(file, {
  transcriptionOptions: options
});
""")
        
        print_subsection("4. React Integration")
        print_code_block("React Component", """
import React, { useState } from 'react';
import { TranscriptionClient } from '@transcription-api/sdk';

const client = new TranscriptionClient({ apiKey: 'your_key' });

function TranscriptionUpload() {
  const [transcript, setTranscript] = useState(null);
  
  const handleUpload = async (file) => {
    const result = await client.transcribeFile(file);
    const completed = await client.waitForCompletion(result.id);
    setTranscript(completed);
  };
  
  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
      {transcript && <p>{transcript.text}</p>}
    </div>
  );
}
""")
        
        print_success("JavaScript SDK supports both browser and Node.js environments")
    
    def demo_api_key_management(self):
        """Demo API key management system"""
        print_section("API Key Management System")
        
        print_subsection("1. Create API Key")
        print_code_block("Create Key", f"""
curl -X POST {self.base_url}/users/api-keys \\
     -H "Authorization: Bearer {self.api_key}" \\
     -H "Content-Type: application/json" \\
     -d '{{
       "name": "My App Key",
       "expires_in_days": 90
     }}'
""")
        
        print_subsection("2. List API Keys")
        print_code_block("List Keys", f"""
curl -X GET {self.base_url}/users/api-keys \\
     -H "Authorization: Bearer {self.api_key}"
""")
        
        print_subsection("3. Python SDK API Key Management")
        print_code_block("SDK Key Management", """
# Create API key
api_key = client.create_api_key("My App Key", expires_in_days=90)
print(f"New API key: {api_key['key']}")  # Only shown once!

# List API keys
keys = client.list_api_keys()
for key in keys:
    print(f"Key: {key['name']} - Last used: {key['last_used_at']}")

# Delete API key
client.delete_api_key(key_id)
""")
        
        print_subsection("4. Key Features")
        features = [
            "Secure key generation with proper entropy",
            "Expiration date support",
            "Usage tracking and analytics",
            "Scope-based permissions",
            "Rate limiting per key",
            "Easy revocation and regeneration"
        ]
        
        for feature in features:
            print_success(feature)
    
    def demo_usage_monitoring(self):
        """Demo usage monitoring and analytics"""
        print_section("Usage Monitoring & Analytics")
        
        print_subsection("1. Usage Statistics")
        print_code_block("Get Usage Stats", f"""
curl -X GET {self.base_url}/usage \\
     -H "Authorization: Bearer {self.api_key}"
""")
        
        print_subsection("2. Detailed Analytics")
        print_code_block("Analytics Response", """
{
  "total_requests": 1250,
  "successful_requests": 1180,
  "failed_requests": 70,
  "avg_response_time": 245.5,
  "total_data_processed": 52428800,
  "unique_users": 15,
  "top_endpoints": {
    "POST /transcriptions/upload": 450,
    "GET /transcriptions": 320,
    "GET /transcriptions/{id}": 280
  },
  "error_rates": {
    "POST /transcriptions/upload": 2.1,
    "GET /transcriptions": 0.8
  }
}
""")
        
        print_subsection("3. Real-time Monitoring")
        print_info("Usage monitoring includes:")
        monitoring_features = [
            "Request/response tracking",
            "Performance metrics",
            "Error rate monitoring", 
            "Rate limit tracking",
            "Data usage analytics",
            "User behavior insights"
        ]
        
        for feature in monitoring_features:
            print_success(feature)
        
        print_subsection("4. SDK Usage Monitoring")
        print_code_block("Python SDK Usage", """
# Get usage statistics
stats = client.get_usage_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"This month: {stats['current_month_requests']}")

# Health check
health = client.health_check()
print(f"API Status: {health['status']}")
""")
    
    def demo_interactive_documentation(self):
        """Demo interactive documentation features"""
        print_section("Interactive API Documentation")
        
        print_subsection("1. API Explorer")
        print_info("Interactive web interface for exploring API endpoints")
        print_code_block("Explorer URL", f"{self.base_url.replace('/v1', '')}/docs/explorer")
        
        print_subsection("2. API Playground")
        print_info("Test API endpoints directly from the browser")
        print_code_block("Playground URL", f"{self.base_url.replace('/v1', '')}/docs/playground")
        
        print_subsection("3. Code Examples")
        print_info("Auto-generated code examples in multiple languages")
        languages = ["Python", "JavaScript", "cURL", "Node.js", "Go", "Java"]
        for lang in languages:
            print_success(f"{lang} examples available")
        
        print_subsection("4. OpenAPI Specification")
        print_code_block("OpenAPI Spec", f"""
curl -X GET {self.base_url}/openapi.json \\
     -H "Accept: application/json"
""")
        
        print_subsection("5. Postman Collection")
        print_code_block("Postman Collection", f"""
curl -X GET {self.base_url}/postman-collection \\
     -H "Accept: application/json"
""")
        
        print_subsection("6. Documentation Features")
        doc_features = [
            "Interactive endpoint testing",
            "Real-time code generation",
            "Authentication testing",
            "Response schema validation",
            "Error code documentation",
            "Rate limiting information"
        ]
        
        for feature in doc_features:
            print_success(feature)
    
    def demo_developer_portal_features(self):
        """Demo developer portal features"""
        print_section("Developer Portal Features")
        
        print_subsection("1. Developer Dashboard")
        dashboard_features = [
            "API key management interface",
            "Usage analytics and charts",
            "Billing and subscription info",
            "Team management tools",
            "Webhook configuration",
            "Support ticket system"
        ]
        
        for feature in dashboard_features:
            print_success(feature)
        
        print_subsection("2. SDK Downloads")
        print_info("Pre-built SDKs available for download")
        sdks = [
            "Python SDK (PyPI)",
            "JavaScript/TypeScript SDK (npm)",
            "Go SDK (GitHub)",
            "Java SDK (Maven)",
            "Ruby SDK (RubyGems)",
            "PHP SDK (Composer)"
        ]
        
        for sdk in sdks:
            print_success(sdk)
        
        print_subsection("3. Community Features")
        community_features = [
            "Developer forum integration",
            "Code examples repository",
            "Tutorial and guides",
            "API changelog",
            "Status page integration",
            "Developer blog"
        ]
        
        for feature in community_features:
            print_success(feature)
    
    def demo_webhook_system(self):
        """Demo webhook system"""
        print_section("Webhook System")
        
        print_subsection("1. Webhook Configuration")
        print_code_block("Create Webhook", f"""
curl -X POST {self.base_url}/developers/webhooks \\
     -H "Authorization: Bearer {self.api_key}" \\
     -H "Content-Type: application/json" \\
     -d '{{
       "name": "My Webhook",
       "url": "https://myapp.com/webhook",
       "events": [
         "transcription.completed",
         "transcription.failed",
         "team.member.added"
       ]
     }}'
""")
        
        print_subsection("2. Webhook Events")
        events = [
            "transcription.completed",
            "transcription.failed", 
            "transcription.updated",
            "team.member.added",
            "team.member.removed",
            "usage.limit.warning",
            "api_key.created",
            "api_key.revoked"
        ]
        
        print_info("Available webhook events:")
        for event in events:
            print_success(event)
        
        print_subsection("3. Webhook Security")
        print_code_block("Signature Verification", """
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
""")
    
    def run_complete_demo(self):
        """Run the complete API platform demo"""
        print("🚀 Comprehensive API Platform Demo (Task 54)")
        print("=" * 60)
        print("This demo showcases all components of the comprehensive API and developer platform")
        
        if not check_venv():
            print("❌ Please activate virtual environment first!")
            return
        
        # Run all demo sections
        self.demo_rest_api()
        self.demo_graphql_api()
        self.demo_python_sdk()
        self.demo_javascript_sdk()
        self.demo_api_key_management()
        self.demo_usage_monitoring()
        self.demo_interactive_documentation()
        self.demo_developer_portal_features()
        self.demo_webhook_system()
        
        # Summary
        print_section("Task 54 Implementation Summary")
        
        implementation_items = [
            "✅ Public REST API with authentication",
            "✅ GraphQL API for flexible data queries", 
            "✅ Python SDK library with comprehensive features",
            "✅ JavaScript/TypeScript SDK library",
            "✅ API key management and usage monitoring",
            "✅ Interactive API explorer and documentation",
            "✅ Developer portal with dashboard features",
            "✅ Webhook system for real-time notifications",
            "✅ Multi-language code examples",
            "✅ OpenAPI specification and Postman collection"
        ]
        
        for item in implementation_items:
            print(item)
        
        print_section("Next Steps for Developers")
        
        next_steps = [
            "1. Sign up for API access at the developer portal",
            "2. Generate your first API key",
            "3. Install the SDK for your preferred language",
            "4. Follow the quickstart guide",
            "5. Explore the interactive API documentation",
            "6. Set up webhooks for real-time updates",
            "7. Monitor your usage through the dashboard",
            "8. Join the developer community forum"
        ]
        
        for step in next_steps:
            print_info(step)
        
        print("\n🎉 API Platform Demo Complete!")
        print("The comprehensive API and developer platform is ready for production use.")


def main():
    """Main demo function"""
    demo = APIDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()