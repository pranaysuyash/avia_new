#!/usr/bin/env python3
"""
Transcription Platform Client
Main client class for interacting with the API
"""

import os
import time
import json
from typing import Dict, Any, Optional, List, Union, BinaryIO
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .exceptions import (
    TranscriptionError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)
from .models import (
    Transcript,
    Team,
    Usage,
    Webhook,
    WebhookEvent
)

class TranscriptionClient:
    """Main client for the Transcription Platform API"""
    
    DEFAULT_BASE_URL = "https://api.example.com/v1"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES
    ):
        """
        Initialize the client
        
        Args:
            api_key: API key for authentication (can also use TRANSCRIPTION_API_KEY env var)
            base_url: Base URL for the API (can also use TRANSCRIPTION_BASE_URL env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key or os.environ.get('TRANSCRIPTION_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Set it directly or via TRANSCRIPTION_API_KEY environment variable")
        
        self.base_url = (base_url or os.environ.get('TRANSCRIPTION_BASE_URL', self.DEFAULT_BASE_URL)).rstrip('/')
        self.timeout = timeout
        
        # Set up session with retries
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': f'transcription-platform-python/{__import__("transcription_platform").__version__}',
            'Content-Type': 'application/json'
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, BinaryIO]] = None
    ) -> Dict[str, Any]:
        """Make an API request"""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Remove Content-Type for file uploads
        headers = self.session.headers.copy()
        if files:
            headers.pop('Content-Type', None)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            
            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + retry_after))
                
                raise RateLimitError(
                    message="Rate limit exceeded",
                    retry_after=retry_after,
                    reset_time=reset_time
                )
            
            # Handle errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Unknown error')
                    error_code = error_data.get('error', 'unknown')
                except:
                    error_message = response.text or 'Unknown error'
                    error_code = 'unknown'
                
                if response.status_code == 401:
                    raise AuthenticationError(error_message)
                elif response.status_code == 404:
                    raise NotFoundError(error_message)
                elif response.status_code in [400, 422]:
                    raise ValidationError(error_message)
                elif response.status_code >= 500:
                    raise ServerError(error_message)
                else:
                    raise TranscriptionError(error_message)
            
            # Parse response
            if response.content:
                return response.json()
            else:
                return {}
                
        except requests.exceptions.Timeout:
            raise TranscriptionError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise TranscriptionError("Failed to connect to API")
        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(f"Unexpected error: {str(e)}")
    
    # Transcript methods
    
    def create_transcript(
        self,
        audio_url: Optional[str] = None,
        audio_file: Optional[BinaryIO] = None,
        language: str = "en",
        enable_diarization: bool = False,
        max_speakers: Optional[int] = None,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transcript:
        """
        Create a new transcript
        
        Args:
            audio_url: URL of audio/video file to transcribe
            audio_file: File object to upload (alternative to audio_url)
            language: Language code (ISO 639-1)
            enable_diarization: Enable speaker diarization
            max_speakers: Maximum number of speakers (2-10)
            webhook_url: Webhook URL for completion notification
            metadata: Custom metadata
        
        Returns:
            Transcript object
        """
        if not audio_url and not audio_file:
            raise ValueError("Either audio_url or audio_file must be provided")
        
        if audio_file:
            # Upload file
            files = {'file': audio_file}
            data = {
                'language': language,
                'enable_diarization': enable_diarization
            }
            if max_speakers:
                data['max_speakers'] = max_speakers
            if webhook_url:
                data['webhook_url'] = webhook_url
            if metadata:
                data['metadata'] = json.dumps(metadata)
            
            response = self._request('POST', '/transcripts/upload', files=files, json_data=data)
        else:
            # Use URL
            data = {
                'audio_url': audio_url,
                'language': language,
                'enable_diarization': enable_diarization
            }
            if max_speakers:
                data['max_speakers'] = max_speakers
            if webhook_url:
                data['webhook_url'] = webhook_url
            if metadata:
                data['metadata'] = metadata
            
            response = self._request('POST', '/transcripts', json_data=data)
        
        return Transcript(**response)
    
    def get_transcript(self, transcript_id: str) -> Transcript:
        """Get a transcript by ID"""
        response = self._request('GET', f'/transcripts/{transcript_id}')
        return Transcript(**response)
    
    def list_transcripts(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        language: Optional[str] = None,
        team_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List transcripts
        
        Args:
            page: Page number (1-based)
            per_page: Items per page (max 100)
            status: Filter by status
            language: Filter by language
            team_id: Filter by team
        
        Returns:
            Dictionary with 'data' (list of transcripts) and 'pagination' info
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }
        
        if status:
            params['status'] = status
        if language:
            params['language'] = language
        if team_id:
            params['team_id'] = team_id
        
        response = self._request('GET', '/transcripts', params=params)
        
        # Convert transcript data to objects
        response['data'] = [Transcript(**t) for t in response.get('data', [])]
        
        return response
    
    def update_transcript(
        self,
        transcript_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transcript:
        """Update a transcript"""
        data = {}
        if title is not None:
            data['title'] = title
        if metadata is not None:
            data['metadata'] = metadata
        
        response = self._request('PUT', f'/transcripts/{transcript_id}', json_data=data)
        return Transcript(**response)
    
    def delete_transcript(self, transcript_id: str) -> Dict[str, str]:
        """Delete a transcript"""
        return self._request('DELETE', f'/transcripts/{transcript_id}')
    
    def export_transcript(
        self,
        transcript_id: str,
        format: str = "txt",
        include_timestamps: bool = False,
        include_speakers: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """
        Export a transcript
        
        Args:
            transcript_id: Transcript ID
            format: Export format (txt, srt, vtt, json, pdf)
            include_timestamps: Include timestamps in export
            include_speakers: Include speaker labels
        
        Returns:
            Exported content (string for text formats, dict for JSON)
        """
        params = {
            'format': format,
            'include_timestamps': include_timestamps,
            'include_speakers': include_speakers
        }
        
        response = self._request('GET', f'/transcripts/{transcript_id}/export', params=params)
        
        if format == 'json':
            return response
        else:
            return response.get('content', '')
    
    # Team methods
    
    def list_teams(self) -> List[Team]:
        """List teams the user belongs to"""
        response = self._request('GET', '/teams')
        return [Team(**t) for t in response.get('data', [])]
    
    def get_team(self, team_id: int) -> Team:
        """Get team details"""
        response = self._request('GET', f'/teams/{team_id}')
        return Team(**response)
    
    def create_team(self, name: str, description: Optional[str] = None) -> Team:
        """Create a new team"""
        data = {'name': name}
        if description:
            data['description'] = description
        
        response = self._request('POST', '/teams', json_data=data)
        return Team(**response)
    
    # Analytics methods
    
    def get_usage(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        usage_type: Optional[str] = None
    ) -> Usage:
        """
        Get usage statistics
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            usage_type: Filter by usage type
        
        Returns:
            Usage object with statistics
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if usage_type:
            params['usage_type'] = usage_type
        
        response = self._request('GET', '/analytics/usage', params=params)
        return Usage(**response)
    
    # Webhook methods
    
    def list_webhooks(self) -> List[Webhook]:
        """List configured webhooks"""
        response = self._request('GET', '/developers/webhooks')
        return [Webhook(**w) for w in response]
    
    def create_webhook(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Webhook:
        """
        Create a webhook
        
        Args:
            name: Webhook name
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Optional secret for signature verification
        
        Returns:
            Webhook object
        """
        data = {
            'name': name,
            'url': url,
            'events': events
        }
        if secret:
            data['secret'] = secret
        
        response = self._request('POST', '/developers/webhooks', json_data=data)
        return Webhook(**response)
    
    def delete_webhook(self, webhook_id: int) -> Dict[str, str]:
        """Delete a webhook"""
        return self._request('DELETE', f'/developers/webhooks/{webhook_id}')
    
    def verify_webhook_signature(
        self,
        payload: Union[str, bytes],
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Webhook payload (as string or bytes)
            signature: Signature from X-Webhook-Signature header
            secret: Webhook secret
        
        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib
        
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    # Utility methods
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        response = self._request('GET', '/languages')
        return response.get('languages', [])