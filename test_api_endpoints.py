"""
Specialized API endpoint tests for Whisper Advanced Integration
Tests all FastAPI endpoints with various scenarios and edge cases
"""

import pytest
import json
import io
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the API router
from api.endpoints.whisper_advanced import router

@pytest.fixture
def app():
    """Create FastAPI app with the router"""
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {"user_id": "test_user_123", "username": "testuser", "email": "test@example.com"}

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
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

@pytest.fixture
def sample_vocabulary():
    """Sample custom vocabulary for testing"""
    return {
        "vocabulary_terms": ["whisper", "transcription", "API"],
        "domain_specific_terms": ["neural", "network", "transformer"],
        "proper_nouns": ["OpenAI", "GPT", "Whisper"],
        "technical_terms": ["endpoint", "authentication", "processing"],
        "boost_factor": 1.5
    }

@pytest.fixture
def sample_prompts():
    """Sample prompt configuration for testing"""
    return {
        "context_prompt": "This is a technical discussion about AI",
        "style_prompt": "Use formal language",
        "domain_prompt": "Machine learning and AI domain",
        "format_prompt": "Include technical terminology"
    }

class TestTranscribeEndpoint:
    """Test the /transcribe endpoint"""
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    @patch('api.endpoints.whisper_advanced.audio_preprocessor')
    def test_transcribe_success(self, mock_audio_preprocessor, mock_whisper_processor, mock_auth, client, mock_user, sample_config):
        """Test successful transcription"""
        mock_auth.return_value = mock_user
        
        # Mock preprocessing result
        mock_preprocessing_result = Mock()
        mock_preprocessing_result.processed_audio_path = "/tmp/processed.wav"
        mock_preprocessing_result.processing_time = 0.5
        mock_preprocessing_result.processed_metrics.quality_score = 0.9
        mock_preprocessing_result.quality_improvement = 0.1
        mock_audio_preprocessor.preprocess_audio.return_value = mock_preprocessing_result
        
        # Mock transcription result
        mock_transcription_result = Mock()
        mock_transcription_result.text = "This is a test transcription."
        mock_transcription_result.language = "en"
        mock_transcription_result.segments = [
            Mock(id=0, start=0.0, end=2.0, text="This is a test transcription.", 
                 confidence=0.95, speaker_id="speaker_1")
        ]
        mock_transcription_result.confidence_score = 0.95
        mock_transcription_result.processing_time = 1.0
        mock_transcription_result.model_used = "whisper-base"
        mock_transcription_result.language_detection.language_probability = 0.98
        mock_whisper_processor.transcribe = AsyncMock(return_value=mock_transcription_result)
        
        # Prepare request
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["text"] == "This is a test transcription."
        assert result["data"]["language"] == "en"
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_transcribe_missing_file(self, mock_auth, client, mock_user, sample_config):
        """Test transcription without audio file"""
        mock_auth.return_value = mock_user
        
        data = {"config": json.dumps(sample_config)}
        response = client.post("/whisper-advanced/transcribe", data=data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_transcribe_invalid_file_type(self, mock_auth, client, mock_user, sample_config):
        """Test transcription with invalid file type"""
        mock_auth.return_value = mock_user
        
        files = {"audio_file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_transcribe_file_too_large(self, mock_auth, client, mock_user, sample_config):
        """Test transcription with file exceeding size limit"""
        mock_auth.return_value = mock_user
        
        # Create a large file (simulate 26MB)
        large_data = b"x" * (26 * 1024 * 1024)
        files = {"audio_file": ("large.wav", io.BytesIO(large_data), "audio/wav")}
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 400
        assert "exceeds 25MB limit" in response.json()["detail"]
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_transcribe_invalid_config(self, mock_auth, client, mock_user):
        """Test transcription with invalid configuration"""
        mock_auth.return_value = mock_user
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": "invalid json"}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 400
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    @patch('api.endpoints.whisper_advanced.audio_preprocessor')
    def test_transcribe_with_custom_vocabulary(self, mock_audio_preprocessor, mock_whisper_processor, mock_auth, client, mock_user, sample_config, sample_vocabulary):
        """Test transcription with custom vocabulary"""
        mock_auth.return_value = mock_user
        
        # Mock preprocessing and transcription
        mock_preprocessing_result = Mock()
        mock_preprocessing_result.processed_audio_path = "/tmp/processed.wav"
        mock_preprocessing_result.processing_time = 0.5
        mock_preprocessing_result.processed_metrics.quality_score = 0.9
        mock_preprocessing_result.quality_improvement = 0.1
        mock_audio_preprocessor.preprocess_audio.return_value = mock_preprocessing_result
        
        mock_transcription_result = Mock()
        mock_transcription_result.text = "This is a whisper transcription API test."
        mock_transcription_result.language = "en"
        mock_transcription_result.segments = []
        mock_transcription_result.confidence_score = 0.95
        mock_transcription_result.processing_time = 1.0
        mock_transcription_result.model_used = "whisper-base"
        mock_transcription_result.language_detection.language_probability = 0.98
        mock_whisper_processor.transcribe = AsyncMock(return_value=mock_transcription_result)
        
        # Enable custom vocabulary in config
        config_with_vocab = sample_config.copy()
        config_with_vocab["enable_custom_vocabulary"] = True
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {
            "config": json.dumps(config_with_vocab),
            "custom_vocabulary": json.dumps(sample_vocabulary)
        }
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    @patch('api.endpoints.whisper_advanced.audio_preprocessor')
    def test_transcribe_with_prompts(self, mock_audio_preprocessor, mock_whisper_processor, mock_auth, client, mock_user, sample_config, sample_prompts):
        """Test transcription with prompt configuration"""
        mock_auth.return_value = mock_user
        
        # Mock preprocessing and transcription
        mock_preprocessing_result = Mock()
        mock_preprocessing_result.processed_audio_path = "/tmp/processed.wav"
        mock_preprocessing_result.processing_time = 0.5
        mock_preprocessing_result.processed_metrics.quality_score = 0.9
        mock_preprocessing_result.quality_improvement = 0.1
        mock_audio_preprocessor.preprocess_audio.return_value = mock_preprocessing_result
        
        mock_transcription_result = Mock()
        mock_transcription_result.text = "Technical discussion about machine learning."
        mock_transcription_result.language = "en"
        mock_transcription_result.segments = []
        mock_transcription_result.confidence_score = 0.95
        mock_transcription_result.processing_time = 1.0
        mock_transcription_result.model_used = "whisper-base"
        mock_transcription_result.language_detection.language_probability = 0.98
        mock_whisper_processor.transcribe = AsyncMock(return_value=mock_transcription_result)
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {
            "config": json.dumps(sample_config),
            "prompt_config": json.dumps(sample_prompts)
        }
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

class TestLanguageDetectionEndpoint:
    """Test the /detect-language endpoint"""
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    def test_detect_language_success(self, mock_whisper_processor, mock_auth, client, mock_user):
        """Test successful language detection"""
        mock_auth.return_value = mock_user
        
        # Mock language detection result
        mock_detection_result = Mock()
        mock_detection_result.detected_language = "en"
        mock_detection_result.language_probability = 0.95
        mock_detection_result.all_language_probs = {"en": 0.95, "es": 0.03, "fr": 0.02}
        mock_whisper_processor.detect_language = AsyncMock(return_value=mock_detection_result)
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        
        response = client.post("/whisper-advanced/detect-language", files=files)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["detected_language"] == "en"
        assert result["data"]["confidence"] == 0.95
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_detect_language_missing_file(self, mock_auth, client, mock_user):
        """Test language detection without audio file"""
        mock_auth.return_value = mock_user
        
        response = client.post("/whisper-advanced/detect-language")
        
        assert response.status_code == 422  # Validation error
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_detect_language_invalid_file_type(self, mock_auth, client, mock_user):
        """Test language detection with invalid file type"""
        mock_auth.return_value = mock_user
        
        files = {"audio_file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}
        
        response = client.post("/whisper-advanced/detect-language", files=files)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

class TestBatchTranscribeEndpoint:
    """Test the /batch-transcribe endpoint"""
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    @patch('api.endpoints.whisper_advanced.audio_preprocessor')
    def test_batch_transcribe_success(self, mock_audio_preprocessor, mock_whisper_processor, mock_auth, client, mock_user, sample_config):
        """Test successful batch transcription"""
        mock_auth.return_value = mock_user
        
        # Mock preprocessing result
        mock_preprocessing_result = Mock()
        mock_preprocessing_result.processed_audio_path = "/tmp/processed.wav"
        mock_preprocessing_result.processing_time = 0.5
        mock_preprocessing_result.quality_improvement = 0.1
        mock_audio_preprocessor.preprocess_audio.return_value = mock_preprocessing_result
        
        # Mock transcription result
        mock_transcription_result = Mock()
        mock_transcription_result.text = "Batch transcription test."
        mock_transcription_result.language = "en"
        mock_transcription_result.processing_time = 1.0
        mock_transcription_result.word_count = 3
        mock_transcription_result.segments = []
        mock_transcription_result.confidence_score = 0.9
        mock_transcription_result.language_detection.language_probability = 0.95
        mock_whisper_processor.transcribe = AsyncMock(return_value=mock_transcription_result)
        
        # Prepare multiple files
        files = [
            ("files", ("test1.wav", io.BytesIO(b"fake audio data 1"), "audio/wav")),
            ("files", ("test2.wav", io.BytesIO(b"fake audio data 2"), "audio/wav"))
        ]
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/batch-transcribe", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["summary"]["total_files"] == 2
        assert result["data"]["summary"]["successful"] == 2
        assert result["data"]["summary"]["failed"] == 0
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_batch_transcribe_too_many_files(self, mock_auth, client, mock_user, sample_config):
        """Test batch transcription with too many files"""
        mock_auth.return_value = mock_user
        
        # Create 11 files (exceeds limit of 10)
        files = []
        for i in range(11):
            files.append(("files", (f"test{i}.wav", io.BytesIO(b"fake audio data"), "audio/wav")))
        
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/batch-transcribe", files=files, data=data)
        
        assert response.status_code == 400
        assert "cannot exceed 10 files" in response.json()["detail"]
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_batch_transcribe_no_files(self, mock_auth, client, mock_user, sample_config):
        """Test batch transcription without files"""
        mock_auth.return_value = mock_user
        
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/batch-transcribe", data=data)
        
        assert response.status_code == 422  # Validation error

class TestUtilityEndpoints:
    """Test utility endpoints (models, presets, health)"""
    
    def test_get_models(self, client):
        """Test get models endpoint"""
        response = client.get("/whisper-advanced/models")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "models" in result["data"]
        assert "supported_languages" in result["data"]
        assert "response_formats" in result["data"]
        
        # Check model structure
        models = result["data"]["models"]
        assert len(models) > 0
        assert "id" in models[0]
        assert "name" in models[0]
        assert "features" in models[0]
    
    def test_get_presets(self, client):
        """Test get presets endpoint"""
        response = client.get("/whisper-advanced/presets")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "presets" in result["data"]
        
        # Check preset structure
        presets = result["data"]["presets"]
        assert len(presets) > 0
        
        preset_names = [p["name"] for p in presets]
        expected_presets = ["High Accuracy", "Fast Processing", "Multi-language", "Technical Content", "Podcast/Interview"]
        
        for expected in expected_presets:
            assert expected in preset_names
        
        # Check preset structure
        for preset in presets:
            assert "name" in preset
            assert "description" in preset
            assert "config" in preset
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/whisper-advanced/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["status"] == "healthy"
        assert "components" in result["data"]
        assert "supported_models" in result["data"]
        assert "supported_languages" in result["data"]

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    def test_transcribe_processing_error(self, mock_whisper_processor, mock_auth, client, mock_user, sample_config):
        """Test handling of processing errors"""
        mock_auth.return_value = mock_user
        mock_whisper_processor.transcribe = AsyncMock(side_effect=Exception("Processing failed"))
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": json.dumps(sample_config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 500
        assert "Failed to transcribe audio" in response.json()["detail"]
    
    def test_unauthenticated_request(self, client, sample_config):
        """Test request without authentication"""
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": json.dumps(sample_config)}
        
        # This should fail due to missing authentication
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        # The exact status code depends on the auth middleware implementation
        assert response.status_code in [401, 403, 422]

class TestRequestValidation:
    """Test request validation and sanitization"""
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_config_validation(self, mock_auth, client, mock_user):
        """Test configuration validation"""
        mock_auth.return_value = mock_user
        
        # Test with invalid temperature
        invalid_config = {
            "model": "whisper-1",
            "temperature": 2.0  # Invalid: should be 0.0-1.0
        }
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": json.dumps(invalid_config)}
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 400
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    def test_vocabulary_validation(self, mock_auth, client, mock_user, sample_config):
        """Test custom vocabulary validation"""
        mock_auth.return_value = mock_user
        
        # Test with invalid boost factor
        invalid_vocabulary = {
            "vocabulary_terms": ["test"],
            "boost_factor": 5.0  # Invalid: should be 1.0-3.0
        }
        
        config_with_vocab = sample_config.copy()
        config_with_vocab["enable_custom_vocabulary"] = True
        
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {
            "config": json.dumps(config_with_vocab),
            "custom_vocabulary": json.dumps(invalid_vocabulary)
        }
        
        response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        
        assert response.status_code == 400

@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for API workflows"""
    
    @patch('api.endpoints.whisper_advanced.get_current_active_user')
    @patch('api.endpoints.whisper_advanced.whisper_processor')
    @patch('api.endpoints.whisper_advanced.audio_preprocessor')
    def test_complete_api_workflow(self, mock_audio_preprocessor, mock_whisper_processor, mock_auth, client, mock_user, sample_config):
        """Test complete API workflow from upload to result"""
        mock_auth.return_value = mock_user
        
        # Mock all dependencies
        mock_preprocessing_result = Mock()
        mock_preprocessing_result.processed_audio_path = "/tmp/processed.wav"
        mock_preprocessing_result.processing_time = 0.5
        mock_preprocessing_result.processed_metrics.quality_score = 0.9
        mock_preprocessing_result.quality_improvement = 0.1
        mock_audio_preprocessor.preprocess_audio.return_value = mock_preprocessing_result
        
        mock_transcription_result = Mock()
        mock_transcription_result.text = "Complete workflow test transcription."
        mock_transcription_result.language = "en"
        mock_transcription_result.segments = [
            Mock(id=0, start=0.0, end=3.0, text="Complete workflow test transcription.", 
                 confidence=0.95, speaker_id=None)
        ]
        mock_transcription_result.confidence_score = 0.95
        mock_transcription_result.processing_time = 1.5
        mock_transcription_result.model_used = "whisper-base"
        mock_transcription_result.word_count = 4
        mock_transcription_result.language_detection.language_probability = 0.98
        mock_whisper_processor.transcribe = AsyncMock(return_value=mock_transcription_result)
        
        # 1. Check health
        health_response = client.get("/whisper-advanced/health")
        assert health_response.status_code == 200
        
        # 2. Get available models
        models_response = client.get("/whisper-advanced/models")
        assert models_response.status_code == 200
        
        # 3. Get presets
        presets_response = client.get("/whisper-advanced/presets")
        assert presets_response.status_code == 200
        
        # 4. Transcribe audio
        files = {"audio_file": ("test.wav", io.BytesIO(b"fake audio data"), "audio/wav")}
        data = {"config": json.dumps(sample_config)}
        
        transcribe_response = client.post("/whisper-advanced/transcribe", files=files, data=data)
        assert transcribe_response.status_code == 200
        
        result = transcribe_response.json()
        assert result["success"] is True
        assert result["data"]["text"] == "Complete workflow test transcription."
        assert result["data"]["processing_time"] > 0
        assert result["data"]["confidence_analysis"]["overall_confidence"] == 0.95