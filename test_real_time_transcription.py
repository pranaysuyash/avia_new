"""
Test Suite for Real-Time Transcription System
Comprehensive tests for real-time transcription functionality, WebSocket communication,
and streaming capabilities
"""

import pytest
import asyncio
import numpy as np
import tempfile
import os
import json
import sqlite3
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import threading
import time
import websockets
from fastapi.testclient import TestClient

from real_time_transcription import (
    RealTimeTranscriptionSystem, StreamingConfig, TranscriptionEngine,
    StreamingMode, AudioBuffer, WhisperTranscriber, VoskTranscriber,
    TranscriptionSegment, StreamingStats, app
)

class TestAudioBuffer:
    """Test cases for AudioBuffer class"""
    
    def test_audio_buffer_initialization(self):
        """Test audio buffer initialization"""
        buffer = AudioBuffer(max_duration=5.0, sample_rate=16000, overlap_duration=0.5)
        
        assert buffer.max_duration == 5.0
        assert buffer.sample_rate == 16000
        assert buffer.overlap_duration == 0.5
        assert buffer.max_samples == 80000  # 5.0 * 16000
        assert buffer.overlap_samples == 8000  # 0.5 * 16000
        assert buffer.write_pos == 0
        assert buffer.total_samples == 0
        assert len(buffer.buffer) == 80000
    
    def test_add_audio_data(self):
        """Test adding audio data to buffer"""
        buffer = AudioBuffer(max_duration=2.0, sample_rate=16000)
        
        # Add small chunk
        audio_chunk = np.random.randn(8000).astype(np.float32)  # 0.5 seconds
        buffer.add_audio(audio_chunk)
        
        assert buffer.total_samples == 8000
        assert buffer.write_pos == 8000
        
        # Add another chunk
        buffer.add_audio(audio_chunk)
        assert buffer.total_samples == 16000
        assert buffer.write_pos == 16000
    
    def test_circular_buffer_wrap(self):
        """Test circular buffer wrap-around"""
        buffer = AudioBuffer(max_duration=1.0, sample_rate=16000)  # Small buffer
        
        # Fill buffer completely
        audio_chunk = np.random.randn(16000).astype(np.float32)
        buffer.add_audio(audio_chunk)
        
        assert buffer.write_pos == 0  # Should wrap to 0
        assert buffer.total_samples == 16000
        
        # Add more data to test wrap-around
        small_chunk = np.random.randn(8000).astype(np.float32)
        buffer.add_audio(small_chunk)
        
        assert buffer.write_pos == 8000
        assert buffer.total_samples == 24000
    
    def test_get_audio_chunk(self):
        """Test retrieving audio chunks"""
        buffer = AudioBuffer(max_duration=2.0, sample_rate=16000)
        
        # Add known data
        test_data = np.arange(16000, dtype=np.float32)  # 1 second of incrementing values
        buffer.add_audio(test_data)
        
        # Get chunk
        retrieved = buffer.get_audio_chunk(0.5)  # 0.5 seconds
        
        assert len(retrieved) == 8000
        # Should get the last 8000 samples
        np.testing.assert_array_equal(retrieved, test_data[8000:])
    
    def test_get_overlapped_chunk(self):
        """Test retrieving overlapped audio chunks"""
        buffer = AudioBuffer(max_duration=3.0, sample_rate=16000, overlap_duration=0.5)
        
        # Add test data
        test_data = np.arange(32000, dtype=np.float32)  # 2 seconds
        buffer.add_audio(test_data)
        
        # Get overlapped chunk
        overlapped = buffer.get_overlapped_chunk(1.0)  # 1 second + 0.5 overlap = 1.5 seconds
        
        assert len(overlapped) == 24000  # 1.5 * 16000
    
    def test_empty_buffer(self):
        """Test behavior with empty buffer"""
        buffer = AudioBuffer(max_duration=1.0, sample_rate=16000)
        
        chunk = buffer.get_audio_chunk(0.5)
        assert len(chunk) == 0

class TestStreamingConfig:
    """Test cases for StreamingConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = StreamingConfig(engine=TranscriptionEngine.WHISPER_API)
        
        assert config.engine == TranscriptionEngine.WHISPER_API
        assert config.language == "en"
        assert config.sample_rate == 16000
        assert config.chunk_duration == 1.0
        assert config.buffer_duration == 5.0
        assert config.overlap_duration == 0.5
        assert config.confidence_threshold == 0.7
        assert config.enable_vad is True
        assert config.enable_speaker_diarization is False
        assert config.streaming_mode == StreamingMode.CONTINUOUS
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = StreamingConfig(
            engine=TranscriptionEngine.VOSK,
            language="es",
            sample_rate=22050,
            chunk_duration=2.0,
            confidence_threshold=0.8
        )
        
        assert config.engine == TranscriptionEngine.VOSK
        assert config.language == "es"
        assert config.sample_rate == 22050
        assert config.chunk_duration == 2.0
        assert config.confidence_threshold == 0.8

class TestTranscriptionSegment:
    """Test cases for TranscriptionSegment dataclass"""
    
    def test_segment_creation(self):
        """Test transcription segment creation"""
        segment = TranscriptionSegment(
            text="Hello world",
            start_time=0.0,
            end_time=2.0,
            confidence=0.95,
            is_final=True,
            speaker_id="speaker_1",
            language="en",
            engine="whisper"
        )
        
        assert segment.text == "Hello world"
        assert segment.start_time == 0.0
        assert segment.end_time == 2.0
        assert segment.confidence == 0.95
        assert segment.is_final is True
        assert segment.speaker_id == "speaker_1"
        assert segment.language == "en"
        assert segment.engine == "whisper"

class TestWhisperTranscriber:
    """Test cases for WhisperTranscriber class"""
    
    def test_whisper_transcriber_initialization_api(self):
        """Test Whisper transcriber initialization with API"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            transcriber = WhisperTranscriber(use_api=True)
            
            assert transcriber.use_api is True
            assert transcriber.model_name == "whisper-1"
            assert transcriber.client is not None
            assert transcriber.local_model is None
    
    def test_whisper_transcriber_initialization_local(self):
        """Test Whisper transcriber initialization with local model"""
        with patch('real_time_transcription.whisper') as mock_whisper:
            mock_model = Mock()
            mock_whisper.load_model.return_value = mock_model
            
            transcriber = WhisperTranscriber(use_api=False, model_name="base")
            
            assert transcriber.use_api is False
            assert transcriber.model_name == "base"
            assert transcriber.client is None
            assert transcriber.local_model == mock_model
    
    @pytest.mark.asyncio
    async def test_transcribe_chunk_api(self):
        """Test transcribing audio chunk with API"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            transcriber = WhisperTranscriber(use_api=True)
            
            # Mock the OpenAI client
            mock_response = Mock()
            mock_response.text = "Hello world"
            mock_response.confidence = 0.95
            
            transcriber.client = Mock()
            transcriber.client.audio.transcriptions.create = Mock(return_value=mock_response)
            
            # Test audio data
            audio_data = np.random.randn(16000).astype(np.float32)
            
            with patch('asyncio.to_thread') as mock_to_thread:
                mock_to_thread.return_value = mock_response
                
                segment = await transcriber.transcribe_chunk(audio_data, 16000, "en")
                
                assert isinstance(segment, TranscriptionSegment)
                assert segment.text == "Hello world"
                assert segment.confidence == 0.95
                assert segment.engine == "whisper_api"
    
    @pytest.mark.asyncio
    async def test_transcribe_chunk_local(self):
        """Test transcribing audio chunk with local model"""
        transcriber = WhisperTranscriber(use_api=False)
        
        # Mock local model
        mock_model = Mock()
        mock_result = {"text": "Local transcription"}
        mock_model.transcribe.return_value = mock_result
        transcriber.local_model = mock_model
        
        audio_data = np.random.randn(16000).astype(np.float32)
        
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_to_thread.return_value = mock_result
            
            segment = await transcriber.transcribe_chunk(audio_data, 16000, "en")
            
            assert isinstance(segment, TranscriptionSegment)
            assert segment.text == "Local transcription"
            assert segment.engine == "whisper_local"

class TestVoskTranscriber:
    """Test cases for VoskTranscriber class"""
    
    def test_vosk_transcriber_initialization(self):
        """Test Vosk transcriber initialization"""
        with patch('real_time_transcription.vosk') as mock_vosk:
            mock_model = Mock()
            mock_vosk.Model.return_value = mock_model
            
            transcriber = VoskTranscriber(model_path="/path/to/model")
            
            assert transcriber.model == mock_model
            mock_vosk.Model.assert_called_once_with("/path/to/model")
    
    def test_vosk_transcriber_no_model(self):
        """Test Vosk transcriber with no model"""
        transcriber = VoskTranscriber(model_path=None)
        
        assert transcriber.model is None
        assert transcriber.recognizer is None
    
    def test_initialize_recognizer(self):
        """Test initializing Vosk recognizer"""
        with patch('real_time_transcription.vosk') as mock_vosk:
            mock_model = Mock()
            mock_recognizer = Mock()
            mock_vosk.Model.return_value = mock_model
            mock_vosk.KaldiRecognizer.return_value = mock_recognizer
            
            transcriber = VoskTranscriber(model_path="/path/to/model")
            transcriber.initialize_recognizer(16000)
            
            assert transcriber.recognizer == mock_recognizer
            mock_vosk.KaldiRecognizer.assert_called_once_with(mock_model, 16000)
    
    @pytest.mark.asyncio
    async def test_transcribe_chunk(self):
        """Test transcribing audio chunk with Vosk"""
        with patch('real_time_transcription.vosk') as mock_vosk:
            mock_model = Mock()
            mock_recognizer = Mock()
            mock_vosk.Model.return_value = mock_model
            mock_vosk.KaldiRecognizer.return_value = mock_recognizer
            
            # Mock recognizer responses
            mock_recognizer.AcceptWaveform.return_value = True
            mock_recognizer.Result.return_value = '{"text": "Vosk result", "confidence": 0.85}'
            
            transcriber = VoskTranscriber(model_path="/path/to/model")
            transcriber.initialize_recognizer(16000)
            
            audio_data = np.random.randn(8000).astype(np.float32)
            segment = await transcriber.transcribe_chunk(audio_data, 16000, is_final=False)
            
            assert isinstance(segment, TranscriptionSegment)
            assert segment.text == "Vosk result"
            assert segment.confidence == 0.85
            assert segment.engine == "vosk"

class TestRealTimeTranscriptionSystem:
    """Test cases for RealTimeTranscriptionSystem class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            yield tmp_db.name
            try:
                os.unlink(tmp_db.name)
            except:
                pass
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return StreamingConfig(
            engine=TranscriptionEngine.WHISPER_API,
            language="en",
            sample_rate=16000,
            chunk_duration=1.0,
            confidence_threshold=0.5
        )
    
    @pytest.fixture
    def transcription_system(self, config, temp_db):
        """Create transcription system for testing"""
        return RealTimeTranscriptionSystem(config, db_path=temp_db)
    
    def test_system_initialization(self, transcription_system, config):
        """Test transcription system initialization"""
        assert transcription_system.config == config
        assert transcription_system.audio_buffer is not None
        assert transcription_system.whisper_transcriber is not None
        assert transcription_system.vosk_transcriber is not None
        assert transcription_system.active_connections == []
        assert transcription_system.is_streaming is False
        assert transcription_system.processing_task is None
    
    def test_database_initialization(self, transcription_system):
        """Test database initialization"""
        conn = sqlite3.connect(transcription_system.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'transcription_sessions',
            'transcription_segments', 
            'performance_metrics'
        ]
        
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    @pytest.mark.asyncio
    async def test_start_streaming(self, transcription_system):
        """Test starting streaming session"""
        session_id = "test_session"
        
        await transcription_system.start_streaming(session_id)
        
        assert transcription_system.is_streaming is True
        assert transcription_system.session_id == session_id
        assert transcription_system.processing_task is not None
    
    @pytest.mark.asyncio
    async def test_stop_streaming(self, transcription_system):
        """Test stopping streaming session"""
        # Start streaming first
        await transcription_system.start_streaming("test_session")
        
        # Stop streaming
        await transcription_system.stop_streaming()
        
        assert transcription_system.is_streaming is False
    
    @pytest.mark.asyncio
    async def test_add_audio_data(self, transcription_system):
        """Test adding audio data"""
        await transcription_system.start_streaming("test_session")
        
        audio_data = np.random.randn(8000).astype(np.float32)
        initial_duration = transcription_system.stats.total_audio_duration
        
        await transcription_system.add_audio_data(audio_data)
        
        assert transcription_system.stats.total_audio_duration > initial_duration
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, transcription_system):
        """Test WebSocket connection management"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        
        await transcription_system.connect_websocket(mock_websocket)
        
        assert mock_websocket in transcription_system.active_connections
        mock_websocket.accept.assert_called_once()
        
        # Test disconnection
        await transcription_system.disconnect_websocket(mock_websocket)
        assert mock_websocket not in transcription_system.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_transcription(self, transcription_system):
        """Test broadcasting transcription to WebSocket clients"""
        # Add mock WebSocket connections
        mock_ws1 = Mock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.send_text = AsyncMock()
        
        transcription_system.active_connections = [mock_ws1, mock_ws2]
        
        # Create test segment
        segment = TranscriptionSegment(
            text="Test message",
            start_time=0.0,
            end_time=1.0,
            confidence=0.9,
            is_final=True,
            engine="test"
        )
        
        await transcription_system.broadcast_transcription(segment)
        
        # Verify both clients received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()
        
        # Check message content
        call_args = mock_ws1.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "transcription"
        assert message["data"]["text"] == "Test message"
        assert message["data"]["confidence"] == 0.9
    
    def test_store_session_start(self, transcription_system):
        """Test storing session start in database"""
        transcription_system.session_id = "test_session"
        transcription_system.store_session_start()
        
        # Verify in database
        conn = sqlite3.connect(transcription_system.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcription_sessions WHERE id = ?", ("test_session",))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[0] == "test_session"  # id column
    
    def test_store_transcription_segment(self, transcription_system):
        """Test storing transcription segment"""
        transcription_system.session_id = "test_session"
        
        segment = TranscriptionSegment(
            text="Test segment",
            start_time=0.0,
            end_time=2.0,
            confidence=0.85,
            is_final=True,
            engine="test"
        )
        
        transcription_system.store_transcription_segment(segment)
        
        # Verify in database
        conn = sqlite3.connect(transcription_system.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcription_segments WHERE session_id = ?", ("test_session",))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[2] == "Test segment"  # text column
        assert row[5] == 0.85  # confidence column
    
    def test_get_session_statistics(self, transcription_system):
        """Test getting session statistics"""
        session_id = "test_session"
        transcription_system.session_id = session_id
        
        # Store some test data
        transcription_system.store_session_start()
        
        segment = TranscriptionSegment(
            text="Test", start_time=0.0, end_time=1.0,
            confidence=0.8, is_final=True, engine="test"
        )
        transcription_system.store_transcription_segment(segment)
        
        stats = transcription_system.get_session_statistics(session_id)
        
        assert isinstance(stats, dict)
        assert stats["session_id"] == session_id
        assert "session_data" in stats
        assert "total_segments" in stats

class TestStreamingStats:
    """Test cases for StreamingStats dataclass"""
    
    def test_stats_initialization(self):
        """Test streaming stats initialization"""
        stats = StreamingStats()
        
        assert stats.total_audio_duration == 0.0
        assert stats.total_processing_time == 0.0
        assert stats.segments_processed == 0
        assert stats.average_latency == 0.0
        assert stats.confidence_scores == []
        assert stats.error_count == 0
    
    def test_stats_with_data(self):
        """Test streaming stats with data"""
        stats = StreamingStats(
            total_audio_duration=10.0,
            segments_processed=5,
            confidence_scores=[0.8, 0.9, 0.7, 0.85, 0.92]
        )
        
        assert stats.total_audio_duration == 10.0
        assert stats.segments_processed == 5
        assert len(stats.confidence_scores) == 5

class TestFastAPIIntegration:
    """Test cases for FastAPI integration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/transcription/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "is_streaming" in data
        assert "active_connections" in data
    
    def test_start_transcription_session(self, client):
        """Test starting transcription session"""
        response = client.post("/api/transcription/start")
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "started"
    
    def test_stop_transcription_session(self, client):
        """Test stopping transcription session"""
        response = client.post("/api/transcription/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"

class TestPerformance:
    """Performance and stress tests"""
    
    @pytest.fixture
    def config(self):
        return StreamingConfig(
            engine=TranscriptionEngine.WHISPER_API,
            chunk_duration=0.5,  # Faster processing for tests
            confidence_threshold=0.5
        )
    
    @pytest.fixture
    def transcription_system(self, config):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            system = RealTimeTranscriptionSystem(config, db_path=tmp_db.name)
            yield system
            try:
                os.unlink(tmp_db.name)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_audio_buffer_performance(self):
        """Test audio buffer performance with large data"""
        buffer = AudioBuffer(max_duration=10.0, sample_rate=16000)
        
        # Add large chunks of audio
        large_chunk = np.random.randn(160000).astype(np.float32)  # 10 seconds
        
        start_time = time.time()
        for _ in range(10):
            buffer.add_audio(large_chunk)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should be fast
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self, transcription_system):
        """Test handling multiple WebSocket connections"""
        mock_websockets = []
        
        # Create multiple mock WebSocket connections
        for i in range(10):
            mock_ws = Mock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()
            mock_websockets.append(mock_ws)
        
        # Connect all WebSockets
        for ws in mock_websockets:
            await transcription_system.connect_websocket(ws)
        
        assert len(transcription_system.active_connections) == 10
        
        # Test broadcasting to all connections
        segment = TranscriptionSegment(
            text="Broadcast test", start_time=0.0, end_time=1.0,
            confidence=0.8, is_final=True, engine="test"
        )
        
        await transcription_system.broadcast_transcription(segment)
        
        # Verify all connections received the message
        for ws in mock_websockets:
            ws.send_text.assert_called_once()

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def transcription_system(self):
        config = StreamingConfig(engine=TranscriptionEngine.WHISPER_API)
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            system = RealTimeTranscriptionSystem(config, db_path=tmp_db.name)
            yield system
            try:
                os.unlink(tmp_db.name)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_websocket_disconnection_handling(self, transcription_system):
        """Test handling WebSocket disconnections during broadcast"""
        # Create mock WebSockets, one that will fail
        good_ws = Mock()
        good_ws.send_text = AsyncMock()
        
        bad_ws = Mock()
        bad_ws.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        
        transcription_system.active_connections = [good_ws, bad_ws]
        
        segment = TranscriptionSegment(
            text="Test", start_time=0.0, end_time=1.0,
            confidence=0.8, is_final=True, engine="test"
        )
        
        # Should handle the error gracefully
        await transcription_system.broadcast_transcription(segment)
        
        # Good connection should still be active, bad one should be removed
        assert good_ws in transcription_system.active_connections
        assert bad_ws not in transcription_system.active_connections
    
    @pytest.mark.asyncio
    async def test_invalid_audio_data(self, transcription_system):
        """Test handling invalid audio data"""
        await transcription_system.start_streaming("test_session")
        
        # Test with invalid data types
        invalid_data = [
            None,
            "invalid_string",
            [],
            np.array([])  # Empty array
        ]
        
        for data in invalid_data:
            try:
                if data is not None:
                    await transcription_system.add_audio_data(data)
            except Exception:
                pass  # Expected to fail gracefully
        
        # System should still be running
        assert transcription_system.is_streaming is True
    
    def test_database_error_handling(self):
        """Test database error handling"""
        config = StreamingConfig(engine=TranscriptionEngine.WHISPER_API)
        
        # Try to create system with invalid database path
        invalid_db_path = "/invalid/path/database.db"
        
        try:
            system = RealTimeTranscriptionSystem(config, db_path=invalid_db_path)
            # Should handle gracefully or raise appropriate exception
        except Exception as e:
            # Should be a specific database-related exception
            assert "database" in str(e).lower() or "permission" in str(e).lower()

def test_transcription_engines_enum():
    """Test TranscriptionEngine enum"""
    assert TranscriptionEngine.WHISPER_API.value == "whisper_api"
    assert TranscriptionEngine.WHISPER_LOCAL.value == "whisper_local"
    assert TranscriptionEngine.VOSK.value == "vosk"
    assert TranscriptionEngine.DEEPSPEECH.value == "deepspeech"

def test_streaming_mode_enum():
    """Test StreamingMode enum"""
    assert StreamingMode.CONTINUOUS.value == "continuous"
    assert StreamingMode.PUSH_TO_TALK.value == "push_to_talk"
    assert StreamingMode.VOICE_ACTIVITY.value == "voice_activity"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])