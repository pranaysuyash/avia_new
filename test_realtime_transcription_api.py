#!/usr/bin/env python3
"""
Test suite for Real-Time Transcription API endpoints
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the API app
from api.app import app
from real_time_transcription import (
    StreamingConfig, TranscriptionEngine, StreamingMode,
    TranscriptionSegment, StreamingStats
)

# Create test client
client = TestClient(app)

class TestRealTimeTranscriptionAPI:
    """Test cases for real-time transcription API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.test_config = {
            "engine": "whisper_api",
            "language": "en",
            "sample_rate": 16000,
            "chunk_duration": 1.0,
            "buffer_duration": 5.0,
            "overlap_duration": 0.5,
            "confidence_threshold": 0.7,
            "enable_vad": True,
            "enable_speaker_diarization": False,
            "streaming_mode": "continuous"
        }
        
        self.mock_segment = TranscriptionSegment(
            text="Hello world",
            start_time=0.0,
            end_time=1.0,
            confidence=0.95,
            is_final=True,
            speaker_id="speaker_1",
            language="en",
            engine="whisper_api"
        )
        
        self.mock_stats = StreamingStats(
            total_audio_duration=10.0,
            total_processing_time=2.0,
            segments_processed=5,
            average_latency=400.0,
            confidence_scores=[0.9, 0.85, 0.92, 0.88, 0.95],
            error_count=0
        )

    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_create_session_success(self, mock_transcriber):
        """Test successful session creation"""
        # Mock the transcriber
        mock_transcriber.create_session = AsyncMock(return_value="session_123")
        
        # Test data
        request_data = {
            "config": self.test_config,
            "session_name": "Test Session"
        }
        
        # Make request
        response = client.post("/api/v1/realtime-transcription/sessions", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["session_id"] == "session_123"
        assert data["data"]["status"] == "created"

    def test_create_session_invalid_config(self):
        """Test session creation with invalid configuration"""
        request_data = {
            "config": {
                **self.test_config,
                "sample_rate": 100000,  # Invalid sample rate
                "confidence_threshold": 1.5  # Invalid threshold
            }
        }
        
        response = client.post("/api/v1/realtime-transcription/sessions", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_create_session_missing_config(self):
        """Test session creation with missing config"""
        request_data = {
            "session_name": "Test Session"
            # Missing config field
        }
        
        response = client.post("/api/v1/realtime-transcription/sessions", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch('api.endpoints.realtime_transcription.active_sessions')
    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_get_session_success(self, mock_transcriber, mock_active_sessions):
        """Test successful session retrieval"""
        session_id = "session_123"
        
        # Mock active sessions
        mock_active_sessions.__contains__ = Mock(return_value=True)
        mock_active_sessions.__getitem__ = Mock(return_value={
            'user_id': 'test_user',
            'config': self.test_config,
            'created_at': '2024-01-01T12:00:00',
            'status': 'active'
        })
        
        # Mock transcriber stats
        mock_transcriber.get_session_stats = AsyncMock(return_value=self.mock_stats)
        
        response = client.get(f"/api/v1/realtime-transcription/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == session_id

    def test_get_session_not_found(self):
        """Test getting non-existent session"""
        session_id = "nonexistent_session"
        
        response = client.get(f"/api/v1/realtime-transcription/sessions/{session_id}")
        assert response.status_code == 404

    @patch('api.endpoints.realtime_transcription.active_sessions')
    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_delete_session_success(self, mock_transcriber, mock_active_sessions):
        """Test successful session deletion"""
        session_id = "session_123"
        
        # Mock active sessions
        mock_active_sessions.__contains__ = Mock(return_value=True)
        mock_active_sessions.__getitem__ = Mock(return_value={
            'user_id': 'test_user',
            'config': self.test_config,
            'created_at': '2024-01-01T12:00:00',
            'status': 'active'
        })
        mock_active_sessions.__delitem__ = Mock()
        
        # Mock transcriber
        mock_transcriber.stop_session = AsyncMock()
        
        response = client.delete(f"/api/v1/realtime-transcription/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == session_id

    @patch('api.endpoints.realtime_transcription.active_sessions')
    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_list_sessions(self, mock_transcriber, mock_active_sessions):
        """Test listing user sessions"""
        # Mock active sessions
        mock_active_sessions.items = Mock(return_value=[
            ("session_1", {
                'user_id': 'test_user',
                'config': self.test_config,
                'created_at': '2024-01-01T12:00:00',
                'status': 'active'
            }),
            ("session_2", {
                'user_id': 'other_user',
                'config': self.test_config,
                'created_at': '2024-01-01T12:00:00',
                'status': 'active'
            })
        ])
        
        # Mock transcriber stats
        mock_transcriber.get_session_stats = AsyncMock(return_value=self.mock_stats)
        
        response = client.get("/api/v1/realtime-transcription/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "sessions" in data["data"]
        assert data["data"]["total"] == 1  # Only user's own sessions

    def test_get_engines(self):
        """Test getting available engines"""
        response = client.get("/api/v1/realtime-transcription/engines")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "engines" in data["data"]
        assert "streaming_modes" in data["data"]
        
        # Check that we have expected engines
        engines = [e["value"] for e in data["data"]["engines"]]
        assert "whisper_api" in engines
        assert "whisper_local" in engines
        assert "vosk" in engines

    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_health_check(self, mock_transcriber):
        """Test health check endpoint"""
        response = client.get("/api/v1/realtime-transcription/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert "components" in data["data"]
        assert "active_sessions" in data["data"]
        assert "active_connections" in data["data"]

    def test_websocket_connection_invalid_session(self):
        """Test WebSocket connection with invalid session"""
        with client.websocket_connect("/api/v1/realtime-transcription/ws/invalid_session") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "not found" in data["message"].lower()

    @patch('api.endpoints.realtime_transcription.active_sessions')
    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_websocket_connection_valid_session(self, mock_transcriber, mock_active_sessions):
        """Test WebSocket connection with valid session"""
        session_id = "session_123"
        
        # Mock active sessions
        mock_active_sessions.__contains__ = Mock(return_value=True)
        mock_active_sessions.__getitem__ = Mock(return_value={
            'user_id': 'test_user',
            'config': self.test_config,
            'created_at': '2024-01-01T12:00:00',
            'status': 'created'
        })
        mock_active_sessions.__setitem__ = Mock()
        
        # Mock transcriber
        mock_transcriber.start_session = AsyncMock()
        mock_transcriber.stop_session = AsyncMock()
        
        with client.websocket_connect(f"/api/v1/realtime-transcription/ws/{session_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["session_id"] == session_id

    @patch('api.endpoints.realtime_transcription.active_sessions')
    @patch('api.endpoints.realtime_transcription.real_time_transcriber')
    def test_websocket_audio_data_message(self, mock_transcriber, mock_active_sessions):
        """Test WebSocket audio data processing"""
        session_id = "session_123"
        
        # Mock active sessions
        mock_active_sessions.__contains__ = Mock(return_value=True)
        mock_active_sessions.__getitem__ = Mock(return_value={
            'user_id': 'test_user',
            'config': self.test_config,
            'created_at': '2024-01-01T12:00:00',
            'status': 'created'
        })
        mock_active_sessions.__setitem__ = Mock()
        
        # Mock transcriber
        mock_transcriber.start_session = AsyncMock()
        mock_transcriber.stop_session = AsyncMock()
        mock_transcriber.process_audio_chunk = AsyncMock(return_value=[self.mock_segment])
        
        with client.websocket_connect(f"/api/v1/realtime-transcription/ws/{session_id}") as websocket:
            # Receive connection confirmation
            websocket.receive_json()
            
            # Send audio data
            websocket.send_json({
                "type": "audio_data",
                "data": "base64_encoded_audio_data"
            })
            
            # Should receive transcription result
            data = websocket.receive_json()
            assert data["type"] == "transcription"
            assert "data" in data
            assert data["data"]["text"] == "Hello world"

    def test_enum_conversion_functions(self):
        """Test enum conversion utility functions"""
        from api.endpoints.realtime_transcription import (
            _convert_engine_enum, _convert_streaming_mode_enum
        )
        
        # Test engine conversion
        assert _convert_engine_enum("whisper_api") == TranscriptionEngine.WHISPER_API
        assert _convert_engine_enum("vosk") == TranscriptionEngine.VOSK
        assert _convert_engine_enum("invalid") == TranscriptionEngine.WHISPER_API  # Default
        
        # Test streaming mode conversion
        assert _convert_streaming_mode_enum("continuous") == StreamingMode.CONTINUOUS
        assert _convert_streaming_mode_enum("push_to_talk") == StreamingMode.PUSH_TO_TALK
        assert _convert_streaming_mode_enum("invalid") == StreamingMode.CONTINUOUS  # Default

    def test_config_conversion(self):
        """Test configuration conversion"""
        from api.endpoints.realtime_transcription import _convert_config_to_internal
        from api.endpoints.realtime_transcription import StreamingConfigAPI
        
        # Create API config
        api_config = StreamingConfigAPI(**self.test_config)
        
        # Convert to internal config
        internal_config = _convert_config_to_internal(api_config)
        
        assert internal_config.engine == TranscriptionEngine.WHISPER_API
        assert internal_config.language == "en"
        assert internal_config.sample_rate == 16000
        assert internal_config.streaming_mode == StreamingMode.CONTINUOUS

    def test_segment_conversion(self):
        """Test segment conversion"""
        from api.endpoints.realtime_transcription import _convert_segment_to_api
        
        api_segment = _convert_segment_to_api(self.mock_segment)
        
        assert api_segment.text == "Hello world"
        assert api_segment.start_time == 0.0
        assert api_segment.end_time == 1.0
        assert api_segment.confidence == 0.95
        assert api_segment.is_final is True

    def test_stats_conversion(self):
        """Test stats conversion"""
        from api.endpoints.realtime_transcription import _convert_stats_to_api
        
        api_stats = _convert_stats_to_api(self.mock_stats)
        
        assert api_stats.total_audio_duration == 10.0
        assert api_stats.segments_processed == 5
        assert api_stats.average_latency == 400.0
        assert len(api_stats.confidence_scores) == 5

    def test_invalid_websocket_message_type(self):
        """Test WebSocket with invalid message type"""
        session_id = "session_123"
        
        with patch('api.endpoints.realtime_transcription.active_sessions') as mock_active_sessions:
            mock_active_sessions.__contains__ = Mock(return_value=True)
            mock_active_sessions.__getitem__ = Mock(return_value={
                'user_id': 'test_user',
                'config': self.test_config,
                'created_at': '2024-01-01T12:00:00',
                'status': 'created'
            })
            mock_active_sessions.__setitem__ = Mock()
            
            with patch('api.endpoints.realtime_transcription.real_time_transcriber') as mock_transcriber:
                mock_transcriber.start_session = AsyncMock()
                mock_transcriber.stop_session = AsyncMock()
                
                with client.websocket_connect(f"/api/v1/realtime-transcription/ws/{session_id}") as websocket:
                    # Receive connection confirmation
                    websocket.receive_json()
                    
                    # Send invalid message type
                    websocket.send_json({
                        "type": "invalid_type",
                        "data": "some_data"
                    })
                    
                    # Should receive error response
                    data = websocket.receive_json()
                    assert data["type"] == "error"
                    assert "Unknown message type" in data["message"]

class TestRealTimeTranscriptionUtils:
    """Test utility functions"""
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Valid config should pass
        valid_config = {
            "engine": "whisper_api",
            "language": "en",
            "sample_rate": 16000,
            "chunk_duration": 1.0,
            "buffer_duration": 5.0,
            "overlap_duration": 0.5,
            "confidence_threshold": 0.7,
            "enable_vad": True,
            "enable_speaker_diarization": False,
            "streaming_mode": "continuous"
        }
        
        response = client.post("/api/v1/realtime-transcription/sessions", json={
            "config": valid_config
        })
        assert response.status_code == 200

    def test_session_lifecycle(self):
        """Test complete session lifecycle"""
        with patch('api.endpoints.realtime_transcription.real_time_transcriber') as mock_transcriber:
            mock_transcriber.create_session = AsyncMock(return_value="session_123")
            mock_transcriber.get_session_stats = AsyncMock(return_value=None)
            mock_transcriber.stop_session = AsyncMock()
            
            # Create session
            create_response = client.post("/api/v1/realtime-transcription/sessions", json={
                "config": {
                    "engine": "whisper_api",
                    "language": "en",
                    "sample_rate": 16000,
                    "chunk_duration": 1.0,
                    "buffer_duration": 5.0,
                    "overlap_duration": 0.5,
                    "confidence_threshold": 0.7,
                    "enable_vad": True,
                    "enable_speaker_diarization": False,
                    "streaming_mode": "continuous"
                }
            })
            assert create_response.status_code == 200
            session_id = create_response.json()["data"]["session_id"]
            
            # Get session
            get_response = client.get(f"/api/v1/realtime-transcription/sessions/{session_id}")
            assert get_response.status_code == 200
            
            # Delete session
            delete_response = client.delete(f"/api/v1/realtime-transcription/sessions/{session_id}")
            assert delete_response.status_code == 200

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])