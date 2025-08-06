#!/usr/bin/env python3
"""
Test script for enterprise features
Tests quota enforcement, audit logging, and data retention
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Test configuration
API_BASE = "http://localhost:8000/api/v1"
ADMIN_TOKEN = "your-admin-token"  # Replace with actual admin token
USER_TOKEN = "your-user-token"    # Replace with actual limited user token

async def test_quota_enforcement():
    """Test quota enforcement on API endpoints"""
    print("\n=== Testing Quota Enforcement ===")
    
    async with aiohttp.ClientSession() as session:
        # Make multiple API calls to trigger quota
        for i in range(5):
            async with session.post(
                f"{API_BASE}/audio/enhance/quality",
                headers={"Authorization": f"Bearer {USER_TOKEN}"},
                json={"audio_data": "base64_encoded_audio", "format": "wav"}
            ) as response:
                if response.status == 402:
                    print(f"✓ Quota exceeded on call {i+1} - Got 402 Payment Required")
                    usage_info = response.headers.get('X-Usage-Info')
                    if usage_info:
                        print(f"  Usage Info: {json.loads(usage_info)}")
                    break
                elif response.status == 200:
                    print(f"  Call {i+1} successful")
                else:
                    print(f"  Call {i+1} failed with status {response.status}")

async def test_audit_logging():
    """Test audit logging system"""
    print("\n=== Testing Audit Logging ===")
    
    async with aiohttp.ClientSession() as session:
        # Perform an action that should be audited
        async with session.post(
            f"{API_BASE}/transcripts",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
            json={"title": "Test Transcript", "content": "Test content"}
        ) as response:
            transcript_id = None
            if response.status == 201:
                data = await response.json()
                transcript_id = data.get('id')
                print(f"✓ Created transcript: {transcript_id}")
        
        # Check audit logs (requires admin)
        async with session.get(
            f"{API_BASE}/audit/logs?limit=5",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Found {data['total']} audit logs")
                for log in data['logs'][:3]:
                    print(f"  - {log['timestamp']}: {log['action']} on {log['resource_type']} "
                          f"(Risk: {log.get('risk_score', 'N/A')})")

async def test_data_retention():
    """Test data retention policies"""
    print("\n=== Testing Data Retention ===")
    
    async with aiohttp.ClientSession() as session:
        # Initialize default policies
        async with session.post(
            f"{API_BASE}/data-retention/initialize",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Initialized {data['policies_created']} retention policies")
        
        # Get retention policies
        async with session.get(
            f"{API_BASE}/data-retention/policies",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Found {len(data)} retention policies:")
                for policy in data[:3]:
                    print(f"  - {policy['data_type']}: {policy['retention_days']} days "
                          f"(auto_delete: {policy['auto_delete']})")
        
        # Check expired data
        async with session.get(
            f"{API_BASE}/data-retention/policies/temp_files/expired?limit=10",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ Found {data['expired_count']} expired temp files")

async def test_usage_dashboard():
    """Test usage tracking dashboard"""
    print("\n=== Testing Usage Dashboard ===")
    
    async with aiohttp.ClientSession() as session:
        # Get usage dashboard
        async with session.get(
            f"{API_BASE}/usage/dashboard",
            headers={"Authorization": f"Bearer {USER_TOKEN}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✓ Usage Dashboard:")
                print(f"  Plan: {data['subscription']['plan_name']}")
                print(f"  Current Usage:")
                for usage_type, usage in data['current_usage'].items():
                    limit = data['limits'].get(usage_type, 'unlimited')
                    print(f"    - {usage_type}: {usage}/{limit}")
                
                if data['alerts']:
                    print("  Alerts:")
                    for alert in data['alerts']:
                        print(f"    ! {alert['message']}")

async def test_feature_gating():
    """Test feature gating based on subscription"""
    print("\n=== Testing Feature Gating ===")
    
    async with aiohttp.ClientSession() as session:
        # Try to access premium feature with basic plan
        async with session.post(
            f"{API_BASE}/ai/models/config",
            headers={"Authorization": f"Bearer {USER_TOKEN}"},
            json={"model_name": "custom-model", "parameters": {}}
        ) as response:
            if response.status == 403:
                print("✓ Premium feature blocked for basic user - Got 403 Forbidden")
                data = await response.json()
                print(f"  Message: {data.get('detail', 'Feature not available')}")
            elif response.status == 200:
                print("  User has access to premium features")

async def main():
    """Run all tests"""
    print("Enterprise Features Test Suite")
    print("==============================")
    print(f"API Base: {API_BASE}")
    print(f"Testing at: {datetime.now().isoformat()}")
    
    try:
        await test_quota_enforcement()
        await test_audit_logging()
        await test_data_retention()
        await test_usage_dashboard()
        await test_feature_gating()
        
        print("\n✅ All tests completed!")
        print("\nNote: Some tests may fail if:")
        print("- API server is not running on localhost:8000")
        print("- Tokens are not valid")
        print("- User doesn't have appropriate permissions")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    # Note: Replace ADMIN_TOKEN and USER_TOKEN with actual tokens
    # You can get tokens by:
    # 1. Creating users via API or UI
    # 2. Logging in to get access tokens
    # 3. Or using test tokens if available
    
    asyncio.run(main())