"""
Comprehensive Test Suite for Whisper Advanced Integration
Tests for all implemented components including API endpoints, processors, and frontend integration
"""

import pytest
import asyncio
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Import the components we're testing
from whisper_advanced_processor import (
    WhisperAdvancedProcessor, WhisperConfig, WhisperModel,
    TranscriptionResult, LanguageDetectionResult, Segment, Word
)
from whisper_audio_preprocessor import (
    AudioPreprocessor, AudioConfig, ProcessingMode,
    PreprocessingResult, AudioMetrics
)
from whisper_advanced_exceptions import (
    WhisperAdvancedException, ConfigurationError, ProcessingError,
    AudioFormatError, ModelLoadError
)
from api.endpoints.whisper_advanced import router

# Test fixtures
@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Create a simple sine wave audio file
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV header and data (simplified)
        f.write(b'RIFF')
        f.write((36 + len(audio_data) * 2).to_bytes(4, 'little'))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))  # PCM
        f.write((1).to_bytes(2, 'little'))  # Mono
        f.write(sample_rate.to_bytes(4, 'little'))
        f.write((sample_rate * 2).to_bytes(4, 'little'))
        f.write((2).to_bytes(2, 'little'))
        f.write((16).to_bytes(2, 'little'))
        f.write(b'data')
        f.write((len(audio_data) * 2).to_bytes(4, 'little'))
        f.write(audio_data.tobytes())
        
        yield f.name
    
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)

@pytest.fixture
def whisper_config():
    """Create a standard Whisper configuration for testing"""
    return WhisperConfig(
        model_size=WhisperModel.BASE,
        language="en",
        task="transcribe",
        temperature=0.0,
        word_timestamps=True,
        enable_diarization=False,
        initial_prompt="Test transcription",
        custom_vocabulary=["test", "whisper", "integration"]
    )

@pytest.fixture
def audio_config():
    """Create a standard audio preprocessing configuration"""
    return AudioConfig(
        processing_mode=ProcessingMode.BALANCED,
        enable_noise_reduction=True,
        enable_enhancement=True,
        enable_normalization=True,
        target_sample_rate=16000,
        target_channels=1
    )

@pytest.fixture
def mock_transcription_result():
    """Create a mock transcription result for testing"""
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=2.0,
            text="This is a test transcription.",
            confidence=0.95,
            speaker_id="speaker_1",
            words=[
                Word(word="This", start=0.0, end=0.2, confidence=0.98),
                Word(word="is", start=0.2, end=0.3, confidence=0.97),
                Word(word="a", start=0.3, end=0.4, confidence=0.96),
                Word(word="test", start=0.4, end=0.7, confidence=0.95),
                Word(word="transcription", start=0.7, end=1.5, confidence=0.94),
            ]
        )
    ]
    
    return TranscriptionResult(
        text="This is a test transcription.",
        language="en",
        segments=segments,
        confidence_score=0.95,
        processing_time=1.5,
        model_used="whisper-base",
        word_count=5,
        language_detection=LanguageDetectionResult(
            detected_language="en",
            language_probability=0.98,
            all_language_probs={"en": 0.98, "es": 0.01, "fr": 0.01}
        )
    )

class TestWhisperAdvancedProcessor:
    """Test suite for WhisperAdvancedProcessor"""
    
    def test_processor_initialization(self):
        """Test processor initialization with default settings"""
        processor = WhisperAdvancedProcessor()
        assert processor is not None
        assert processor.current_model is None
        assert processor.model_cache == {}
    
    def test_config_validation(self, whisper_config):
        """Test configuration validation"""
        processor = WhisperAdvancedProcessor()
        
        # Valid config should pass
        assert processor._validate_config(whisper_config) is True
        
        # Invalid config should raise error
        invalid_config = WhisperConfig(
            model_size=WhisperModel.BASE,
            temperature=2.0  # Invalid temperature > 1.0
        )
        
        with pytest.raises(ConfigurationError):
            processor._validate_config(invalid_config)
    
    @patch('whisper.load_model')
    def test_model_loading(self, mock_load_model, whisper_config):
        """Test model loading and caching"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        model = processor._load_model(whisper_config)
        
        assert model == mock_model
        assert processor.current_model == mock_model
        assert WhisperModel.BASE in processor.model_cache
        mock_load_model.assert_called_once()
    
    @patch('whisper.load_model')
    async def test_transcribe_success(self, mock_load_model, sample_audio_file, whisper_config, mock_transcription_result):
        """Test successful transcription"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': mock_transcription_result.text,
            'language': mock_transcription_result.language,
            'segments': [
                {
                    'id': seg.id,
                    'start': seg.start,
                    'end': seg.end,
                    'text': seg.text,
                    'words': [
                        {'word': w.word, 'start': w.start, 'end': w.end, 'probability': w.confidence}
                        for w in seg.words
                    ]
                }
                for seg in mock_transcription_result.segments
            ]
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        result = await processor.transcribe(sample_audio_file, whisper_config)
        
        assert result is not None
        assert result.text == mock_transcription_result.text
        assert result.language == mock_transcription_result.language
        assert len(result.segments) > 0
        assert result.processing_time > 0
    
    async def test_transcribe_file_not_found(self, whisper_config):
        """Test transcription with non-existent file"""
        processor = WhisperAdvancedProcessor()
        
        with pytest.raises(ProcessingError):
            await processor.transcribe("nonexistent_file.wav", whisper_config)
    
    @patch('whisper.load_model')
    async def test_detect_language(self, mock_load_model, sample_audio_file):
        """Test language detection"""
        mock_model = Mock()
        mock_model.detect_language.return_value = ("en", 0.98)
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        result = await processor.detect_language(sample_audio_file)
        
        assert result.detected_language == "en"
        assert result.language_probability == 0.98
        assert "en" in result.all_language_probs

class TestAudioPreprocessor:
    """Test suite for AudioPreprocessor"""
    
    def test_preprocessor_initialization(self):
        """Test audio preprocessor initialization"""
        preprocessor = AudioPreprocessor()
        assert preprocessor is not None
    
    def test_config_validation(self, audio_config):
        """Test audio configuration validation"""
        preprocessor = AudioPreprocessor()
        
        # Valid config should pass
        assert preprocessor._validate_config(audio_config) is True
        
        # Invalid config should raise error
        invalid_config = AudioConfig(
            processing_mode=ProcessingMode.BALANCED,
            target_sample_rate=-1  # Invalid sample rate
        )
        
        with pytest.raises(ConfigurationError):
            preprocessor._validate_config(invalid_config)
    
    @patch('librosa.load')
    @patch('librosa.resample')
    @patch('noisereduce.reduce_noise')
    def test_preprocess_audio_success(self, mock_noise_reduce, mock_resample, mock_load, sample_audio_file, audio_config):
        """Test successful audio preprocessing"""
        # Mock librosa functions
        mock_audio_data = np.random.randn(16000)  # 1 second of audio at 16kHz
        mock_load.return_value = (mock_audio_data, 16000)
        mock_resample.return_value = mock_audio_data
        mock_noise_reduce.return_value = mock_audio_data
        
        preprocessor = AudioPreprocessor()
        result = preprocessor.preprocess_audio(sample_audio_file, audio_config)
        
        assert result is not None
        assert isinstance(result, PreprocessingResult)
        assert result.processed_audio_path is not None
        assert result.processing_time > 0
        assert result.processed_metrics is not None
        assert 0 <= result.quality_improvement <= 1
    
    def test_preprocess_audio_file_not_found(self, audio_config):
        """Test preprocessing with non-existent file"""
        preprocessor = AudioPreprocessor()
        
        with pytest.raises(AudioFormatError):
            preprocessor.preprocess_audio("nonexistent_file.wav", audio_config)
    
    @patch('librosa.load')
    def test_calculate_audio_metrics(self, mock_load, sample_audio_file):
        """Test audio metrics calculation"""
        mock_audio_data = np.random.randn(16000)
        mock_load.return_value = (mock_audio_data, 16000)
        
        preprocessor = AudioPreprocessor()
        metrics = preprocessor._calculate_audio_metrics(mock_audio_data, 16000)
        
        assert isinstance(metrics, AudioMetrics)
        assert metrics.snr_db is not None
        assert metrics.dynamic_range_db is not None
        assert 0 <= metrics.quality_score <= 1

class TestWhisperAdvancedExceptions:
    """Test suite for custom exceptions"""
    
    def test_base_exception(self):
        """Test base WhisperAdvancedException"""
        error = WhisperAdvancedException("Test error", "TEST_001")
        assert str(error) == "Test error"
        assert error.error_code == "TEST_001"
        assert error.details is None
    
    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Invalid config", "CONFIG_001", {"field": "temperature"})
        assert str(error) == "Invalid config"
        assert error.error_code == "CONFIG_001"
        assert error.details == {"field": "temperature"}
    
    def test_processing_error(self):
        """Test ProcessingError"""
        error = ProcessingError("Processing failed", "PROC_001")
        assert str(error) == "Processing failed"
        assert error.error_code == "PROC_001"
    
    def test_audio_format_error(self):
        """Test AudioFormatError"""
        error = AudioFormatError("Unsupported format", "AUDIO_001")
        assert str(error) == "Unsupported format"
        assert error.error_code == "AUDIO_001"
    
    def test_model_load_error(self):
        """Test ModelLoadError"""
        error = ModelLoadError("Model not found", "MODEL_001")
        assert str(error) == "Model not found"
        assert error.error_code == "MODEL_001"

class TestWhisperAdvancedAPI:
    """Test suite for FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for API testing"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {"user_id": "test_user", "username": "testuser"}
    
    def create_test_file(self, filename="test.wav", content=b"fake audio data"):
        """Create a test file for upload"""
        return ("audio_file", (filename, io.BytesIO(content), "audio/wav"))
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    @patch('api.endpoints.whisper_advanced.audio_preprocessor')
    def test_transcribe_endpoint_success(self, mock_audio_preprocessor, mock_whisper_processor, mock_auth, client, mock_user, mock_transcription_result):
        """Test successful transcription endpoint"""
        mock_auth.return_value = mock_user
        
        # Mock preprocessing result
        mock_preprocessing_result = Mock()
        mock_preprocessing_result.processed_audio_path = "/tmp/processed.wav"
        mock_preprocessing_result.processing_time = 0.5
        mock_preprocessing_result.processed_metrics.quality_score = 0.9
        mock_preprocessing_result.quality_improvement = 0.1
        mock_audio_preprocessor.preprocess_audio.return_value = mock_preprocessing_result
        
        # Mock transcription result
        mock_whisper_processor.transcribe = AsyncMock(return_value=mock_transcription_result)
        
        # Prepare request data
        config = {
            "model": "whisper-1",
            "language": "en",
            "temperature": 0.0,
            "enable_language_detection": True,
            "enable_confidence_analysis": True,
            "enable_word_timestamps": True,
            "enable_speaker_detection": False,
            "confidence_threshold": 0.8,
            "chunk_length_s": 30
        }
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": json.dumps(config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["text"] == mock_transcription_result.text
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_transcribe_endpoint_no_file(self, mock_auth, client, mock_user):
        """Test transcription endpoint without file"""
        mock_auth.return_value = mock_user
        
        config = {"model": "whisper-1"}
        data = {"config": json.dumps(config)}
        
        response = client.post("/whisper-advanced/transcribe", data=data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_transcribe_endpoint_invalid_file_type(self, mock_auth, client, mock_user):
        """Test transcription endpoint with invalid file type"""
        mock_auth.return_value = mock_user
        
        config = {"model": "whisper-1"}
        files = {"audio_file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}
        data = {"config": json.dumps(config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    def test_detect_language_endpoint_success(self, mock_whisper_processor, mock_auth, client, mock_user):
        """Test successful language detection endpoint"""
        mock_auth.return_value = mock_user
        
        # Mock language detection result
        mock_detection_result = LanguageDetectionResult(
            detected_language="en",
            language_probability=0.95,
            all_language_probs={"en": 0.95, "es": 0.03, "fr": 0.02}
        )
        mock_whisper_processor.detect_language = AsyncMock(return_value=mock_detection_result)
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        
        response = client.post("/whisper-advanced/detect-language", files=files)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["detected_language"] == "en"
        assert result["data"]["confidence"] == 0.95
    
    def test_get_models_endpoint(self, client):
        """Test get models endpoint"""
        response = client.get("/whisper-advanced/models")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "models" in result["data"]
        assert "supported_languages" in result["data"]
    
    def test_get_presets_endpoint(self, client):
        """Test get presets endpoint"""
        response = client.get("/whisper-advanced/presets")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "presets" in result["data"]
        assert len(result["data"]["presets"]) > 0
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/whisper-advanced/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["status"] == "healthy"

class TestIntegrationWorkflows:
    """Integration tests for complete workflows"""
    
    @patch('whisper.load_model')
    @patch('librosa.load')
    async def test_complete_transcription_workflow(self, mock_load, mock_load_model, sample_audio_file):
        """Test complete transcription workflow from audio to result"""
        # Mock dependencies
        mock_audio_data = np.random.randn(16000)
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'This is a test transcription.',
            'language': 'en',
            'segments': [{
                'id': 0,
                'start': 0.0,
                'end': 2.0,
                'text': 'This is a test transcription.',
                'words': [
                    {'word': 'This', 'start': 0.0, 'end': 0.2, 'probability': 0.98},
                    {'word': 'is', 'start': 0.2, 'end': 0.3, 'probability': 0.97},
                    {'word': 'a', 'start': 0.3, 'end': 0.4, 'probability': 0.96},
                    {'word': 'test', 'start': 0.4, 'end': 0.7, 'probability': 0.95},
                    {'word': 'transcription', 'start': 0.7, 'end': 1.5, 'probability': 0.94},
                ]
            }]
        }
        mock_load_model.return_value = mock_model
        
        # Initialize components
        audio_preprocessor = AudioPreprocessor()
        whisper_processor = WhisperAdvancedProcessor()
        
        # Create configurations
        audio_config = AudioConfig(
            processing_mode=ProcessingMode.BALANCED,
            enable_noise_reduction=True,
            enable_enhancement=True
        )
        
        whisper_config = WhisperConfig(
            model_size=WhisperModel.BASE,
            language="en",
            word_timestamps=True
        )
        
        # Execute workflow
        preprocessing_result = audio_preprocessor.preprocess_audio(sample_audio_file, audio_config)
        transcription_result = await whisper_processor.transcribe(
            preprocessing_result.processed_audio_path, 
            whisper_config
        )
        
        # Verify results
        assert preprocessing_result is not None
        assert transcription_result is not None
        assert transcription_result.text == 'This is a test transcription.'
        assert transcription_result.language == 'en'
        assert len(transcription_result.segments) == 1
        assert len(transcription_result.segments[0].words) == 5

class TestPerformanceBenchmarks:
    """Performance and load testing"""
    
    @pytest.mark.performance
    @patch('whisper.load_model')
    @patch('librosa.load')
    async def test_transcription_performance(self, mock_load, mock_load_model, sample_audio_file):
        """Test transcription performance benchmarks"""
        import time
        
        # Mock dependencies for consistent timing
        mock_audio_data = np.random.randn(16000)
        mock_load.return_value = (mock_audio_data, 16000)
        
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'text': 'Performance test transcription.',
            'language': 'en',
            'segments': []
        }
        mock_load_model.return_value = mock_model
        
        processor = WhisperAdvancedProcessor()
        config = WhisperConfig(model_size=WhisperModel.BASE)
        
        # Measure performance
        start_time = time.time()
        result = await processor.transcribe(sample_audio_file, config)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert result.processing_time > 0
        
        # Log performance metrics
        print(f"Transcription completed in {processing_time:.2f} seconds")
        print(f"Reported processing time: {result.processing_time:.2f} seconds")
    
    @pytest.mark.performance
    async def test_concurrent_transcriptions(self, sample_audio_file):
        """Test concurrent transcription processing"""
        import asyncio
        
        with patch('whisper.load_model') as mock_load_model, \
             patch('librosa.load') as mock_load:
            
            mock_audio_data = np.random.randn(16000)
            mock_load.return_value = (mock_audio_data, 16000)
            
            mock_model = Mock()
            mock_model.transcribe.return_value = {
                'text': 'Concurrent test transcription.',
                'language': 'en',
                'segments': []
            }
            mock_load_model.return_value = mock_model
            
            processor = WhisperAdvancedProcessor()
            config = WhisperConfig(model_size=WhisperModel.BASE)
            
            # Run multiple concurrent transcriptions
            tasks = []
            for i in range(3):
                task = processor.transcribe(sample_audio_file, config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Verify all transcriptions completed successfully
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert result.text == 'Concurrent test transcription.'

# Test configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=whisper_advanced_processor",
        "--cov=whisper_audio_preprocessor", 
        "--cov=whisper_advanced_exceptions",
        "--cov=api.endpoints.whisper_advanced",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])