"""
Main client for the Transcription API Python SDK
"""

import os
import json
import time
from typing import Dict, List, Optional, Union, BinaryIO, Any
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    Transcript, Team, TeamMember, User, TranscriptionOptions,
    AnalysisOptions, WebhookEvent, TranscriptStatus
)
from .exceptions import (
    TranscriptionAPIError, AuthenticationError, RateLimitError,
    ValidationError, NotFoundError, ServerError
)


class TranscriptionClient:
    """
    Main client for interacting with the Transcription API
    
    Example:
        client = TranscriptionClient(api_key="your_api_key")
        
        # Upload and transcribe a file
        with open("audio.mp3", "rb") as f:
            transcript = client.transcribe_file(f, title="My Recording")
        
        # Wait for completion
        transcript = client.wait_for_completion(transcript.id)
        print(transcript.text)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.transcriptionplatform.com/v1",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the client
        
        Args:
            api_key: API key for authentication. If not provided, will look for
                    TRANSCRIPTION_API_KEY environment variable
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key or os.getenv("TRANSCRIPTION_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Provide it directly or set TRANSCRIPTION_API_KEY environment variable."
            )
        
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"transcription-api-python/1.0.0",
            "Accept": "application/json"
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an API request with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                files=files,
                params=params,
                json=json_data,
                timeout=self.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or authentication failed.")
            
            # Handle validation errors
            if response.status_code == 400:
                error_detail = response.json().get("detail", "Validation error")
                raise ValidationError(error_detail)
            
            # Handle not found
            if response.status_code == 404:
                raise NotFoundError("Resource not found.")
            
            # Handle server errors
            if response.status_code >= 500:
                raise ServerError(f"Server error: {response.status_code}")
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise TranscriptionAPIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise TranscriptionAPIError("Connection error")
        except requests.exceptions.RequestException as e:
            raise TranscriptionAPIError(f"Request failed: {str(e)}")
    
    # Transcription methods
    def transcribe_file(
        self,
        file: Union[str, Path, BinaryIO],
        title: Optional[str] = None,
        options: Optional[TranscriptionOptions] = None
    ) -> Transcript:
        """
        Upload and transcribe an audio/video file
        
        Args:
            file: File path, Path object, or file-like object
            title: Optional title for the transcription
            options: Transcription options
            
        Returns:
            Transcript object with initial status
        """
        options = options or TranscriptionOptions()
        
        # Handle different file input types
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise ValidationError(f"File not found: {file_path}")
            
            with open(file_path, "rb") as f:
                return self._upload_file(f, title or file_path.name, options)
        else:
            # Assume it's a file-like object
            filename = getattr(file, 'name', 'audio_file')
            return self._upload_file(file, title or filename, options)
    
    def _upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        options: TranscriptionOptions
    ) -> Transcript:
        """Internal method to upload file"""
        files = {"file": (filename, file_obj)}
        data = {
            "title": filename,
            "language": options.language,
            "method": options.method,
            "team_id": options.team_id
        }
        
        response = self._request("POST", "/transcriptions/upload", data=data, files=files)
        return Transcript.from_dict(response)
    
    def get_transcript(self, transcript_id: str) -> Transcript:
        """Get a transcript by ID"""
        response = self._request("GET", f"/transcriptions/{transcript_id}")
        return Transcript.from_dict(response)
    
    def list_transcripts(
        self,
        skip: int = 0,
        limit: int = 20,
        team_id: Optional[int] = None
    ) -> List[Transcript]:
        """List user's transcripts"""
        params = {"skip": skip, "limit": limit}
        if team_id:
            params["team_id"] = team_id
        
        response = self._request("GET", "/transcriptions", params=params)
        return [Transcript.from_dict(t) for t in response]
    
    def delete_transcript(self, transcript_id: str) -> bool:
        """Delete a transcript"""
        self._request("DELETE", f"/transcriptions/{transcript_id}")
        return True
    
    def wait_for_completion(
        self,
        transcript_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Transcript:
        """
        Wait for a transcript to complete processing
        
        Args:
            transcript_id: ID of the transcript
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds
            
        Returns:
            Completed transcript
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            transcript = self.get_transcript(transcript_id)
            
            if transcript.status == TranscriptStatus.COMPLETED:
                return transcript
            elif transcript.status == TranscriptStatus.FAILED:
                raise TranscriptionAPIError("Transcription failed")
            
            time.sleep(poll_interval)
        
        raise TranscriptionAPIError("Transcription timed out")
    
    # Team methods
    def create_team(self, name: str, description: Optional[str] = None) -> Team:
        """Create a new team"""
        data = {"name": name}
        if description:
            data["description"] = description
        
        response = self._request("POST", "/teams", json_data=data)
        return Team.from_dict(response)
    
    def list_teams(self) -> List[Team]:
        """List user's teams"""
        response = self._request("GET", "/teams")
        return [Team.from_dict(t) for t in response]
    
    def get_team(self, team_id: int) -> Team:
        """Get team details"""
        response = self._request("GET", f"/teams/{team_id}")
        return Team.from_dict(response)
    
    def invite_team_member(
        self,
        team_id: int,
        email: str,
        role: str = "member"
    ) -> Dict[str, Any]:
        """Invite a member to a team"""
        data = {"email": email, "role": role}
        return self._request("POST", f"/teams/{team_id}/members", json_data=data)
    
    def remove_team_member(self, team_id: int, user_id: int) -> bool:
        """Remove a member from a team"""
        self._request("DELETE", f"/teams/{team_id}/members/{user_id}")
        return True
    
    # User methods
    def get_profile(self) -> User:
        """Get current user profile"""
        response = self._request("GET", "/users/profile")
        return User.from_dict(response)
    
    def update_profile(self, name: Optional[str] = None) -> User:
        """Update user profile"""
        data = {}
        if name:
            data["name"] = name
        
        response = self._request("PUT", "/users/profile", json_data=data)
        return User.from_dict(response)
    
    # API Key methods
    def create_api_key(
        self,
        name: str,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        data = {"name": name}
        if expires_in_days:
            data["expires_in_days"] = expires_in_days
        
        return self._request("POST", "/users/api-keys", json_data=data)
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List user's API keys"""
        return self._request("GET", "/users/api-keys")
    
    def delete_api_key(self, key_id: int) -> bool:
        """Delete an API key"""
        self._request("DELETE", f"/users/api-keys/{key_id}")
        return True
    
    # Utility methods
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._request("GET", "/health")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self._request("GET", "/usage")


# Async client for advanced use cases
class AsyncTranscriptionClient:
    """
    Async version of the TranscriptionClient
    
    Example:
        import asyncio
        
        async def main():
            client = AsyncTranscriptionClient(api_key="your_api_key")
            
            with open("audio.mp3", "rb") as f:
                transcript = await client.transcribe_file(f)
            
            transcript = await client.wait_for_completion(transcript.id)
            print(transcript.text)
        
        asyncio.run(main())
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.transcriptionplatform.com/v1",
        timeout: int = 30
    ):
        """Initialize async client"""
        self.api_key = api_key or os.getenv("TRANSCRIPTION_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Provide it directly or set TRANSCRIPTION_API_KEY environment variable."
            )
        
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"transcription-api-python-async/1.0.0",
            "Accept": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an async API request"""
        import aiohttp
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    data=data,
                    params=params,
                    json=json_data
                ) as response:
                    
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")
                    
                    if response.status == 401:
                        raise AuthenticationError("Invalid API key or authentication failed.")
                    
                    if response.status == 400:
                        error_data = await response.json()
                        error_detail = error_data.get("detail", "Validation error")
                        raise ValidationError(error_detail)
                    
                    if response.status == 404:
                        raise NotFoundError("Resource not found.")
                    
                    if response.status >= 500:
                        raise ServerError(f"Server error: {response.status}")
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                raise TranscriptionAPIError(f"Request failed: {str(e)}")
    
    async def transcribe_file(
        self,
        file: Union[str, Path, BinaryIO],
        title: Optional[str] = None,
        options: Optional[TranscriptionOptions] = None
    ) -> Transcript:
        """Async version of transcribe_file"""
        # Implementation similar to sync version but with async/await
        # This is a simplified version - full implementation would handle file uploads properly
        options = options or TranscriptionOptions()
        
        # For now, delegate to sync version
        # In a full implementation, this would use aiofiles and proper async file handling
        sync_client = TranscriptionClient(self.api_key, self.base_url)
        return sync_client.transcribe_file(file, title, options)
    
    async def get_transcript(self, transcript_id: str) -> Transcript:
        """Async get transcript"""
        response = await self._request("GET", f"/transcriptions/{transcript_id}")
        return Transcript.from_dict(response)
    
    async def wait_for_completion(
        self,
        transcript_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Transcript:
        """Async wait for completion"""
        import asyncio
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            transcript = await self.get_transcript(transcript_id)
            
            if transcript.status == TranscriptStatus.COMPLETED:
                return transcript
            elif transcript.status == TranscriptStatus.FAILED:
                raise TranscriptionAPIError("Transcription failed")
            
            await asyncio.sleep(poll_interval)
        
        raise TranscriptionAPIError("Transcription timed out")