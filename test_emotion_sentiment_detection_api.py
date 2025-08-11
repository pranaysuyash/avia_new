#!/usr/bin/env python3
"""
Comprehensive test suite for Emotion/Sentiment Detection API endpoints
Tests all API functionality including audio analysis, text analysis, and configuration
"""

import os
import sys
import asyncio
import tempfile
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import numpy as np
import soundfile as sf

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app
from api.app import app
from emotion_sentiment_detection import EmotionSentimentDetector

client = TestClient(app)

class TestEmotionSentimentDetectionAPI:
    """Test suite for Emotion/Sentiment Detection API endpoints"""
    
    @classmethod
    def setup_class(cls):
        """Set up test fixtures"""
        cls.test_audio_file = cls.create_test_audio_file()
        cls.test_config = {
            "detection_mode": "both",
            "model_type": "transformer",
            "language": "en",
            "confidence_threshold": 0.5,
            "enable_audio_analysis": True,
            "enable_text_analysis": True,
            "enable_temporal_analysis": True,
            "segment_duration": 2.0,
            "overlap_duration": 0.5,
            "enable_speaker_emotion": True
        }
        cls.test_text = "I am very happy today! This is wonderful news."
    
    @classmethod
    def teardown_class(cls):
        """Clean up test fixtures"""
        if os.path.exists(cls.test_audio_file):
            os.unlink(cls.test_audio_file)
    
    @staticmethod
    def create_test_audio_file():
        """Create a test audio file for testing"""
        # Generate 5 seconds of test audio (sine wave)
        sample_rate = 16000
        duration = 5.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Add some noise to make it more realistic
        noise = 0.05 * np.random.randn(len(audio_data))
        audio_data += noise
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        sf.write(temp_file.name, audio_data, sample_rate)
        temp_file.close()
        
        return temp_file.name
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/api/v1/emotion-sentiment/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert "components" in data["data"]
        assert data["data"]["supported_models"] > 0
        assert data["data"]["supported_languages"] > 0
    
    def test_get_available_models(self):
        """Test getting available models"""
        response = client.get("/api/v1/emotion-sentiment/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        
        models_data = data["data"]
        assert "emotion_models" in models_data
        assert "sentiment_models" in models_data
        assert "detection_modes" in models_data
        assert "supported_languages" in models_data
        
        # Check emotion models
        assert len(models_data["emotion_models"]) > 0
        emotion_model = models_data["emotion_models"][0]
        assert "value" in emotion_model
        assert "label" in emotion_model
        assert "description" in emotion_model
        assert "emotions" in emotion_model
        
        # Check sentiment models
        assert len(models_data["sentiment_models"]) > 0
        sentiment_model = models_data["sentiment_models"][0]
        assert "value" in sentiment_model
        assert "label" in sentiment_model
        assert "description" in sentiment_model
        assert "polarities" in sentiment_model
        
        # Check detection modes
        assert len(models_data["detection_modes"]) == 3
        mode_values = [mode["value"] for mode in models_data["detection_modes"]]
        assert "emotion" in mode_values
        assert "sentiment" in mode_values
        assert "both" in mode_values
        
        # Check supported languages
        assert len(models_data["supported_languages"]) > 0
        language = models_data["supported_languages"][0]
        assert "code" in language
        assert "name" in language
    
    def test_analyze_audio_file_success(self):
        """Test successful audio file analysis"""
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(self.test_config),
                "transcript_text": "This is a test transcript",
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "data" in result
        
        analysis_data = result["data"]
        assert "emotions" in analysis_data
        assert "sentiments" in analysis_data
        assert "overall_emotion" in analysis_data
        assert "overall_sentiment" in analysis_data
        assert "emotion_timeline" in analysis_data
        assert "sentiment_timeline" in analysis_data
        assert "statistics" in analysis_data
        assert "processing_time" in analysis_data
        assert "total_duration" in analysis_data
        assert "config_used" in analysis_data
        
        # Check emotions structure
        if analysis_data["emotions"]:
            emotion = analysis_data["emotions"][0]
            assert "timestamp" in emotion
            assert "duration" in emotion
            assert "primary_emotion" in emotion
            assert "emotion_scores" in emotion
            assert "confidence" in emotion
            assert "intensity" in emotion
        
        # Check sentiments structure
        if analysis_data["sentiments"]:
            sentiment = analysis_data["sentiments"][0]
            assert "timestamp" in sentiment
            assert "duration" in sentiment
            assert "polarity" in sentiment
            assert "sentiment_score" in sentiment
            assert "confidence" in sentiment
            assert "subjectivity" in sentiment
            assert "keywords" in sentiment
    
    def test_analyze_audio_file_invalid_format(self):
        """Test audio file analysis with invalid file format"""
        # Create a fake text file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"This is not an audio file")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as fake_audio:
                files = {"audio_file": ("test.txt", fake_audio, "text/plain")}
                data = {
                    "config": json.dumps(self.test_config),
                    "include_timeline": "true",
                    "include_statistics": "true"
                }
                
                response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
            
            assert response.status_code == 400
            error_data = response.json()
            assert "detail" in error_data
            assert "Unsupported file type" in error_data["detail"]
        
        finally:
            os.unlink(temp_file_path)
    
    def test_analyze_audio_file_missing_file(self):
        """Test audio file analysis without providing a file"""
        data = {
            "config": json.dumps(self.test_config),
            "include_timeline": "true",
            "include_statistics": "true"
        }
        
        response = client.post("/api/v1/emotion-sentiment/analyze", data=data)
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_audio_file_invalid_config(self):
        """Test audio file analysis with invalid configuration"""
        invalid_config = self.test_config.copy()
        invalid_config["detection_mode"] = "invalid_mode"
        
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(invalid_config),
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
    
    def test_analyze_text_sentiment_success(self):
        """Test successful text sentiment analysis"""
        data = {
            "text": self.test_text,
            "language": "en",
            "model_type": "transformer"
        }
        
        response = client.post("/api/v1/emotion-sentiment/analyze-text", data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "data" in result
        
        sentiments = result["data"]
        assert isinstance(sentiments, list)
        
        if sentiments:
            sentiment = sentiments[0]
            assert "timestamp" in sentiment
            assert "duration" in sentiment
            assert "polarity" in sentiment
            assert "sentiment_score" in sentiment
            assert "confidence" in sentiment
            assert "subjectivity" in sentiment
            assert "keywords" in sentiment
            
            # Check that sentiment score is in valid range
            assert -1 <= sentiment["sentiment_score"] <= 1
            assert 0 <= sentiment["confidence"] <= 1
            assert 0 <= sentiment["subjectivity"] <= 1
    
    def test_analyze_text_sentiment_empty_text(self):
        """Test text sentiment analysis with empty text"""
        data = {
            "text": "",
            "language": "en",
            "model_type": "transformer"
        }
        
        response = client.post("/api/v1/emotion-sentiment/analyze-text", data=data)
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_text_sentiment_different_languages(self):
        """Test text sentiment analysis with different languages"""
        test_texts = {
            "en": "I am very happy today!",
            "es": "Estoy muy feliz hoy!",
            "fr": "Je suis très heureux aujourd'hui!",
            "de": "Ich bin heute sehr glücklich!",
        }
        
        for lang, text in test_texts.items():
            data = {
                "text": text,
                "language": lang,
                "model_type": "transformer"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze-text", data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
    
    def test_analyze_text_sentiment_different_models(self):
        """Test text sentiment analysis with different models"""
        models = ["transformer", "vader", "textblob"]
        
        for model in models:
            data = {
                "text": self.test_text,
                "language": "en",
                "model_type": model
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze-text", data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
    
    def test_emotion_only_mode(self):
        """Test analysis with emotion-only mode"""
        emotion_config = self.test_config.copy()
        emotion_config["detection_mode"] = "emotion"
        
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(emotion_config),
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        analysis_data = result["data"]
        
        # Should have emotions but may have limited sentiments
        assert "emotions" in analysis_data
        assert "overall_emotion" in analysis_data
    
    def test_sentiment_only_mode(self):
        """Test analysis with sentiment-only mode"""
        sentiment_config = self.test_config.copy()
        sentiment_config["detection_mode"] = "sentiment"
        
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(sentiment_config),
                "transcript_text": self.test_text,
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        analysis_data = result["data"]
        
        # Should have sentiments but may have limited emotions
        assert "sentiments" in analysis_data
        assert "overall_sentiment" in analysis_data
    
    def test_different_model_types(self):
        """Test analysis with different model types"""
        model_types = ["transformer", "cnn", "svm"]
        
        for model_type in model_types:
            config = self.test_config.copy()
            config["model_type"] = model_type
            
            with open(self.test_audio_file, 'rb') as audio_file:
                files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
                data = {
                    "config": json.dumps(config),
                    "include_timeline": "true",
                    "include_statistics": "true"
                }
                
                response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
    
    def test_confidence_threshold_variations(self):
        """Test analysis with different confidence thresholds"""
        thresholds = [0.1, 0.5, 0.9]
        
        for threshold in thresholds:
            config = self.test_config.copy()
            config["confidence_threshold"] = threshold
            
            with open(self.test_audio_file, 'rb') as audio_file:
                files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
                data = {
                    "config": json.dumps(config),
                    "include_timeline": "true",
                    "include_statistics": "true"
                }
                
                response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
    
    def test_segment_duration_variations(self):
        """Test analysis with different segment durations"""
        durations = [1.0, 2.0, 5.0]
        
        for duration in durations:
            config = self.test_config.copy()
            config["segment_duration"] = duration
            
            with open(self.test_audio_file, 'rb') as audio_file:
                files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
                data = {
                    "config": json.dumps(config),
                    "include_timeline": "true",
                    "include_statistics": "true"
                }
                
                response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
    
    def test_disabled_features(self):
        """Test analysis with various features disabled"""
        # Test with audio analysis disabled
        config = self.test_config.copy()
        config["enable_audio_analysis"] = False
        
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(config),
                "transcript_text": self.test_text,
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # Test with text analysis disabled
        config["enable_audio_analysis"] = True
        config["enable_text_analysis"] = False
        
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(config),
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_timeline_and_statistics_options(self):
        """Test analysis with timeline and statistics options"""
        # Test without timeline
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(self.test_config),
                "include_timeline": "false",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # Test without statistics
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(self.test_config),
                "include_timeline": "true",
                "include_statistics": "false"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
    
    def test_performance_metrics(self):
        """Test that performance metrics are reasonable"""
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(self.test_config),
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        analysis_data = result["data"]
        
        # Check that processing time is reasonable (should be less than 60 seconds for test file)
        assert analysis_data["processing_time"] < 60.0
        
        # Check that total duration matches approximately the test file duration
        assert 4.0 <= analysis_data["total_duration"] <= 6.0  # 5 second test file with some tolerance
    
    def test_error_handling(self):
        """Test various error conditions"""
        # Test with malformed JSON config
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": "invalid json",
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 400
        
        # Test with missing required config fields
        incomplete_config = {"detection_mode": "both"}
        
        with open(self.test_audio_file, 'rb') as audio_file:
            files = {"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            data = {
                "config": json.dumps(incomplete_config),
                "include_timeline": "true",
                "include_statistics": "true"
            }
            
            response = client.post("/api/v1/emotion-sentiment/analyze", files=files, data=data)
        
        assert response.status_code == 400


def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🧪 Starting Emotion/Sentiment Detection API Test Suite...")
    print("=" * 60)
    
    # Create test instance
    test_instance = TestEmotionSentimentDetectionAPI()
    test_instance.setup_class()
    
    try:
        # Run all tests
        tests = [
            ("Health Check", test_instance.test_health_check),
            ("Get Available Models", test_instance.test_get_available_models),
            ("Audio Analysis Success", test_instance.test_analyze_audio_file_success),
            ("Audio Analysis Invalid Format", test_instance.test_analyze_audio_file_invalid_format),
            ("Audio Analysis Missing File", test_instance.test_analyze_audio_file_missing_file),
            ("Audio Analysis Invalid Config", test_instance.test_analyze_audio_file_invalid_config),
            ("Text Sentiment Success", test_instance.test_analyze_text_sentiment_success),
            ("Text Sentiment Empty Text", test_instance.test_analyze_text_sentiment_empty_text),
            ("Text Sentiment Different Languages", test_instance.test_analyze_text_sentiment_different_languages),
            ("Text Sentiment Different Models", test_instance.test_analyze_text_sentiment_different_models),
            ("Emotion Only Mode", test_instance.test_emotion_only_mode),
            ("Sentiment Only Mode", test_instance.test_sentiment_only_mode),
            ("Different Model Types", test_instance.test_different_model_types),
            ("Confidence Threshold Variations", test_instance.test_confidence_threshold_variations),
            ("Segment Duration Variations", test_instance.test_segment_duration_variations),
            ("Disabled Features", test_instance.test_disabled_features),
            ("Timeline and Statistics Options", test_instance.test_timeline_and_statistics_options),
            ("Performance Metrics", test_instance.test_performance_metrics),
            ("Error Handling", test_instance.test_error_handling),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"Running: {test_name}...")
                test_func()
                print(f"✅ {test_name} - PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name} - FAILED: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Emotion/Sentiment Detection API is working correctly.")
        else:
            print(f"⚠️  {failed} test(s) failed. Please check the implementation.")
        
        return failed == 0
        
    finally:
        test_instance.teardown_class()


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)