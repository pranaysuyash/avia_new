#!/usr/bin/env python3
"""
Test script to demonstrate API functionality
"""

import requests
import json
import time
import os
from typing import Dict, Any


class APIClient:
    """Simple API client for testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        # Add auth header if token available
        if self.token and "headers" not in kwargs:
            kwargs["headers"] = {}
        if self.token:
            kwargs.get("headers", {})["Authorization"] = f"Bearer {self.token}"
        
        response = self.session.request(method, url, **kwargs)
        
        # Print request details
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"Error: {response.text}")
            response.raise_for_status()
        
        return response.json() if response.text else {}
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and store token"""
        data = self._make_request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        self.token = data["access_token"]
        return data
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return self._make_request("GET", "/api/v1/users/profile")
    
    def list_transcripts(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """List transcripts"""
        return self._make_request(
            "GET",
            "/api/v1/transcripts/",
            params={"page": page, "per_page": per_page}
        )
    
    def create_transcript(self, title: str, content: str, team_id: int = None) -> Dict[str, Any]:
        """Create transcript"""
        data = {
            "title": title,
            "content": content,
            "metadata": {"source": "api_test"}
        }
        if team_id:
            data["team_id"] = team_id
        
        return self._make_request("POST", "/api/v1/transcripts/", json=data)
    
    def share_transcript(self, transcript_id: int, permission: str = "view") -> Dict[str, Any]:
        """Share transcript"""
        return self._make_request(
            "POST",
            f"/api/v1/transcripts/{transcript_id}/share",
            json={"permission": permission}
        )
    
    def list_teams(self) -> Dict[str, Any]:
        """List teams"""
        return self._make_request("GET", "/api/v1/teams/")
    
    def create_team(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create team"""
        return self._make_request(
            "POST",
            "/api/v1/teams/",
            json={"name": name, "description": description}
        )
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Upload file for transcription"""
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
            return self._make_request(
                "POST",
                "/api/v1/media/upload",
                files=files,
                params={"language": "en", "model": "base"}
            )
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check job status"""
        return self._make_request("GET", f"/api/v1/media/status/{job_id}")


def main():
    """Run API tests"""
    print("🚀 Audio/Video Transcription API Test Suite")
    print("=" * 50)
    
    # Initialize client
    client = APIClient()
    
    # Test 1: Health check
    print("\n📋 Test 1: Health Check")
    try:
        response = requests.get(f"{client.base_url}/api/v1/health")
        print(f"Health check: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: API documentation
    print("\n📋 Test 2: API Documentation")
    print(f"OpenAPI docs available at: {client.base_url}/api/docs")
    print(f"ReDoc available at: {client.base_url}/api/redoc")
    
    # Test 3: User registration
    print("\n📋 Test 3: User Registration")
    try:
        user_data = client._make_request(
            "POST",
            "/api/v1/users/register",
            json={
                "email": f"test_{int(time.time())}@example.com",
                "username": f"testuser_{int(time.time())}",
                "password": "TestPassword123!"
            }
        )
        print(f"Created user: {user_data}")
        
        # Login with new user
        login_data = client.login(
            user_data["email"],
            "TestPassword123!"
        )
        print(f"Login successful! Token: {login_data['access_token'][:20]}...")
        
    except Exception as e:
        print(f"Registration failed (user may already exist): {e}")
        # Try login with existing user
        client.login("test@example.com", "password")
    
    # Test 4: Get profile
    print("\n📋 Test 4: Get User Profile")
    try:
        profile = client.get_profile()
        print(f"User profile: {json.dumps(profile, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Create transcript
    print("\n📋 Test 5: Create Transcript")
    try:
        transcript = client.create_transcript(
            title="API Test Transcript",
            content="This is a test transcript created via the API. It contains sample text for testing purposes."
        )
        print(f"Created transcript: {transcript}")
        transcript_id = transcript["id"]
    except Exception as e:
        print(f"Error: {e}")
        transcript_id = None
    
    # Test 6: List transcripts
    print("\n📋 Test 6: List Transcripts")
    try:
        transcripts = client.list_transcripts()
        print(f"Found {transcripts['total']} transcripts")
        for t in transcripts["transcripts"][:3]:
            print(f"  - {t['title']} (ID: {t['id']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 7: Share transcript
    if transcript_id:
        print("\n📋 Test 7: Share Transcript")
        try:
            share = client.share_transcript(transcript_id)
            print(f"Share created: {share}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 8: Create team
    print("\n📋 Test 8: Create Team")
    try:
        team = client.create_team(
            name=f"API Test Team {int(time.time())}",
            description="Team created via API testing"
        )
        print(f"Created team: {team}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 9: List teams
    print("\n📋 Test 9: List Teams")
    try:
        teams = client.list_teams()
        print(f"Found {teams['total']} teams")
        for t in teams["teams"]:
            print(f"  - {t['name']} (Role: {t['your_role']})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 10: File upload simulation
    print("\n📋 Test 10: File Upload (Simulation)")
    print("Note: Actual file upload requires a real audio file")
    print("Example command:")
    print('  curl -X POST "http://localhost:8000/api/v1/media/upload" \\')
    print('    -H "Authorization: Bearer YOUR_TOKEN" \\')
    print('    -F "file=@audio.mp3" \\')
    print('    -F "language=en" \\')
    print('    -F "model=base"')
    
    # Test 11: Rate limiting
    print("\n📋 Test 11: Rate Limiting")
    print("Making rapid requests to test rate limiting...")
    for i in range(5):
        try:
            client.get_profile()
            print(f"  Request {i+1}: Success")
        except Exception as e:
            print(f"  Request {i+1}: {e}")
        time.sleep(0.1)
    
    print("\n✅ API testing completed!")
    print(f"\nAPI is running at: {client.base_url}")
    print(f"Documentation: {client.base_url}/api/docs")


if __name__ == "__main__":
    main()