"""
Test Suite for Voice Activity Detection (VAD) System
Comprehensive tests for VAD functionality, methods, and performance
"""

import pytest
import numpy as np
import librosa
import soundfile as sf
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import time

from voice_activity_detection import (
    VoiceActivityDetector, VADMethod, VADMode, VADSegment, VADResult,
    AudioQualityMetrics, DeepVADModel
)

class TestVoiceActivityDetector:
    """Test cases for VoiceActivityDetector class"""
    
    @pytest.fixture
    def vad_detector(self):
        """Create a VAD detector instance for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            detector = VoiceActivityDetector(db_path=tmp_db.name)
            yield detector
            # Cleanup
            try:
                os.unlink(tmp_db.name)
            except:
                pass
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample audio file for testing"""
        # Create synthetic audio with speech and silence
        sr = 16000
        duration = 5  # 5 seconds
        t = np.linspace(0, duration, int(sr * duration))
        
        # Create audio with alternating speech and silence
        audio = np.zeros_like(t)
        
        # Add speech segments (sine waves)
        speech_segments = [(0.5, 1.5), (2.5, 3.5), (4.0, 4.8)]
        for start, end in speech_segments:
            start_idx = int(start * sr)
            end_idx = int(end * sr)
            audio[start_idx:end_idx] = 0.5 * np.sin(2 * np.pi * 440 * t[start_idx:end_idx])
        
        # Add noise
        audio += 0.05 * np.random.randn(len(audio))
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio, sr)
            yield tmp_file.name
            # Cleanup
            try:
                os.unlink(tmp_file.name)
            except:
                pass
    
    def test_initialization(self, vad_detector):
        """Test VAD detector initialization"""
        assert vad_detector is not None
        assert vad_detector.webrtc_vad is not None
        assert vad_detector.ml_classifier is not None
        assert vad_detector.scaler is not None
        assert vad_detector.deep_model is not None
        assert os.path.exists(vad_detector.db_path)
    
    def test_database_initialization(self, vad_detector):
        """Test database initialization"""
        conn = sqlite3.connect(vad_detector.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['vad_results', 'audio_quality', 'vad_performance']
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_extract_audio_features(self, vad_detector):
        """Test audio feature extraction"""
        # Create test audio
        sr = 16000
        duration = 1
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        features = vad_detector.extract_audio_features(audio, sr)
        
        assert isinstance(features, dict)
        assert len(features) > 0
        
        # Check for expected features
        expected_features = [
            'energy', 'log_energy', 'zcr_mean', 'spectral_centroid_mean',
            'spectral_rolloff_mean', 'mfcc_0_mean', 'spectral_entropy_mean'
        ]
        
        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], (int, float))
    
    def test_webrtc_vad_detection(self, vad_detector, sample_audio_file):
        """Test WebRTC VAD detection"""
        audio, sr = librosa.load(sample_audio_file, sr=None)
        
        segments = vad_detector.webrtc_vad_detection(audio, sr)
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        for segment in segments:
            assert isinstance(segment, VADSegment)
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
            assert segment.duration > 0
            assert isinstance(segment.is_speech, bool)
            assert 0 <= segment.confidence <= 1
            assert segment.method == "webrtc"
    
    def test_energy_based_vad(self, vad_detector, sample_audio_file):
        """Test energy-based VAD detection"""
        audio, sr = librosa.load(sample_audio_file, sr=None)
        
        segments = vad_detector.energy_based_vad(audio, sr)
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        for segment in segments:
            assert isinstance(segment, VADSegment)
            assert segment.method == "energy_based"
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
    
    def test_ensemble_vad(self, vad_detector, sample_audio_file):
        """Test ensemble VAD detection"""
        audio, sr = librosa.load(sample_audio_file, sr=None)
        
        segments = vad_detector.ensemble_vad(audio, sr, sample_audio_file)
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        for segment in segments:
            assert isinstance(segment, VADSegment)
            assert segment.method == "ensemble"
    
    def test_detect_voice_activity(self, vad_detector, sample_audio_file):
        """Test main voice activity detection method"""
        result = vad_detector.detect_voice_activity(sample_audio_file, VADMethod.ENSEMBLE)
        
        assert isinstance(result, VADResult)
        assert result.total_duration > 0
        assert result.speech_duration >= 0
        assert result.silence_duration >= 0
        assert 0 <= result.speech_ratio <= 1
        assert 0 <= result.quality_score <= 100
        assert result.method_used == VADMethod.ENSEMBLE.value
        assert result.processing_time > 0
        assert len(result.segments) > 0
    
    def test_assess_audio_quality(self, vad_detector, sample_audio_file):
        """Test audio quality assessment"""
        audio, sr = librosa.load(sample_audio_file, sr=None)
        
        quality_metrics = vad_detector.assess_audio_quality(audio, sr)
        
        assert isinstance(quality_metrics, AudioQualityMetrics)
        assert isinstance(quality_metrics.snr_db, float)
        assert isinstance(quality_metrics.thd_percent, float)
        assert isinstance(quality_metrics.dynamic_range_db, float)
        assert isinstance(quality_metrics.spectral_centroid_hz, float)
        assert isinstance(quality_metrics.spectral_rolloff_hz, float)
        assert isinstance(quality_metrics.zero_crossing_rate, float)
        assert isinstance(quality_metrics.mfcc_features, list)
        assert len(quality_metrics.mfcc_features) == 13
        assert isinstance(quality_metrics.energy_entropy, float)
        assert isinstance(quality_metrics.spectral_entropy, float)
    
    def test_remove_silence(self, vad_detector, sample_audio_file):
        """Test silence removal functionality"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            result_path = vad_detector.remove_silence(
                sample_audio_file, output_path, VADMethod.ENSEMBLE, padding_ms=100
            )
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            
            # Check that output file is valid
            processed_audio, sr = librosa.load(output_path, sr=None)
            assert len(processed_audio) > 0
            
        finally:
            try:
                os.unlink(output_path)
            except:
                pass
    
    def test_store_vad_result(self, vad_detector, sample_audio_file):
        """Test storing VAD results in database"""
        # Create a sample VAD result
        segments = [
            VADSegment(0.0, 1.0, 1.0, True, 0.8, "test"),
            VADSegment(1.0, 2.0, 1.0, False, 0.6, "test")
        ]
        
        result = VADResult(
            segments=segments,
            total_duration=2.0,
            speech_duration=1.0,
            silence_duration=1.0,
            speech_ratio=0.5,
            quality_score=75.0,
            method_used="test",
            processing_time=0.1
        )
        
        vad_detector.store_vad_result(sample_audio_file, result)
        
        # Verify storage
        conn = sqlite3.connect(vad_detector.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vad_results WHERE file_path = ?", (sample_audio_file,))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[1] == sample_audio_file  # file_path
        assert row[2] == "test"  # method
        assert row[3] == 2.0  # total_duration
    
    def test_store_quality_metrics(self, vad_detector, sample_audio_file):
        """Test storing quality metrics in database"""
        metrics = AudioQualityMetrics(
            snr_db=20.0,
            thd_percent=1.5,
            dynamic_range_db=40.0,
            spectral_centroid_hz=1500.0,
            spectral_rolloff_hz=3000.0,
            zero_crossing_rate=0.1,
            mfcc_features=[1.0, 2.0, 3.0],
            energy_entropy=2.5,
            spectral_entropy=3.0
        )
        
        vad_detector.store_quality_metrics(sample_audio_file, metrics)
        
        # Verify storage
        conn = sqlite3.connect(vad_detector.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audio_quality WHERE file_path = ?", (sample_audio_file,))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[1] == sample_audio_file  # file_path
        assert row[2] == 20.0  # snr_db
    
    def test_get_vad_statistics(self, vad_detector, sample_audio_file):
        """Test getting VAD statistics"""
        # First process a file to have some data
        vad_detector.detect_voice_activity(sample_audio_file, VADMethod.ENSEMBLE)
        
        stats = vad_detector.get_vad_statistics()
        
        assert isinstance(stats, dict)
        assert 'method_statistics' in stats
        assert 'recent_activity' in stats
        assert 'total_processed_files' in stats
        
        assert stats['total_processed_files'] > 0
    
    def test_different_vad_methods(self, vad_detector, sample_audio_file):
        """Test different VAD methods produce different results"""
        methods = [VADMethod.WEBRTC, VADMethod.ENERGY_BASED, VADMethod.ENSEMBLE]
        results = {}
        
        for method in methods:
            result = vad_detector.detect_voice_activity(sample_audio_file, method)
            results[method] = result
            
            assert isinstance(result, VADResult)
            assert result.method_used == method.value
        
        # Results should be different (at least in processing approach)
        assert len(results) == len(methods)
    
    def test_error_handling_invalid_file(self, vad_detector):
        """Test error handling with invalid audio file"""
        invalid_file = "nonexistent_file.wav"
        
        result = vad_detector.detect_voice_activity(invalid_file, VADMethod.ENSEMBLE)
        
        # Should return empty result without crashing
        assert isinstance(result, VADResult)
        assert result.total_duration == 0
        assert len(result.segments) == 0
    
    def test_visualization_creation(self, vad_detector, sample_audio_file):
        """Test VAD visualization creation"""
        # First get VAD result
        vad_result = vad_detector.detect_voice_activity(sample_audio_file, VADMethod.ENSEMBLE)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            result_path = vad_detector.visualize_vad_result(
                sample_audio_file, vad_result, output_path
            )
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            
            # Check file size (should be non-zero for a valid image)
            assert os.path.getsize(output_path) > 0
            
        finally:
            try:
                os.unlink(output_path)
            except:
                pass

class TestVADSegment:
    """Test cases for VADSegment dataclass"""
    
    def test_vad_segment_creation(self):
        """Test VADSegment creation and properties"""
        segment = VADSegment(
            start_time=1.0,
            end_time=2.5,
            duration=1.5,
            is_speech=True,
            confidence=0.85,
            method="test"
        )
        
        assert segment.start_time == 1.0
        assert segment.end_time == 2.5
        assert segment.duration == 1.5
        assert segment.is_speech is True
        assert segment.confidence == 0.85
        assert segment.method == "test"

class TestVADResult:
    """Test cases for VADResult dataclass"""
    
    def test_vad_result_creation(self):
        """Test VADResult creation and properties"""
        segments = [
            VADSegment(0.0, 1.0, 1.0, True, 0.8, "test"),
            VADSegment(1.0, 2.0, 1.0, False, 0.6, "test")
        ]
        
        result = VADResult(
            segments=segments,
            total_duration=2.0,
            speech_duration=1.0,
            silence_duration=1.0,
            speech_ratio=0.5,
            quality_score=75.0,
            method_used="test",
            processing_time=0.1
        )
        
        assert len(result.segments) == 2
        assert result.total_duration == 2.0
        assert result.speech_duration == 1.0
        assert result.silence_duration == 1.0
        assert result.speech_ratio == 0.5
        assert result.quality_score == 75.0
        assert result.method_used == "test"
        assert result.processing_time == 0.1

class TestAudioQualityMetrics:
    """Test cases for AudioQualityMetrics dataclass"""
    
    def test_audio_quality_metrics_creation(self):
        """Test AudioQualityMetrics creation and properties"""
        metrics = AudioQualityMetrics(
            snr_db=20.0,
            thd_percent=1.5,
            dynamic_range_db=40.0,
            spectral_centroid_hz=1500.0,
            spectral_rolloff_hz=3000.0,
            zero_crossing_rate=0.1,
            mfcc_features=[1.0, 2.0, 3.0],
            energy_entropy=2.5,
            spectral_entropy=3.0
        )
        
        assert metrics.snr_db == 20.0
        assert metrics.thd_percent == 1.5
        assert metrics.dynamic_range_db == 40.0
        assert metrics.spectral_centroid_hz == 1500.0
        assert metrics.spectral_rolloff_hz == 3000.0
        assert metrics.zero_crossing_rate == 0.1
        assert metrics.mfcc_features == [1.0, 2.0, 3.0]
        assert metrics.energy_entropy == 2.5
        assert metrics.spectral_entropy == 3.0

class TestDeepVADModel:
    """Test cases for Deep Learning VAD Model"""
    
    def test_model_creation(self):
        """Test deep VAD model creation"""
        model = DeepVADModel(input_size=13, hidden_size=64, num_layers=2)
        
        assert model is not None
        assert hasattr(model, 'lstm')
        assert hasattr(model, 'fc1')
        assert hasattr(model, 'fc2')
        assert hasattr(model, 'fc3')
    
    def test_model_forward_pass(self):
        """Test model forward pass"""
        model = DeepVADModel(input_size=13, hidden_size=64, num_layers=2)
        
        # Create dummy input
        batch_size = 4
        sequence_length = 10
        input_size = 13
        
        dummy_input = torch.randn(batch_size, sequence_length, input_size)
        
        with torch.no_grad():
            output = model(dummy_input)
        
        assert output.shape == (batch_size, 1)
        assert torch.all(output >= 0) and torch.all(output <= 1)  # Sigmoid output

class TestPerformance:
    """Performance and stress tests"""
    
    def test_processing_speed(self, vad_detector, sample_audio_file):
        """Test VAD processing speed"""
        start_time = time.time()
        result = vad_detector.detect_voice_activity(sample_audio_file, VADMethod.ENSEMBLE)
        processing_time = time.time() - start_time
        
        # Should process faster than real-time for short audio
        audio, sr = librosa.load(sample_audio_file, sr=None)
        audio_duration = len(audio) / sr
        
        # Processing should be reasonably fast (less than 10x real-time)
        assert processing_time < audio_duration * 10
        assert result.processing_time > 0
    
    def test_memory_usage(self, vad_detector, sample_audio_file):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple times
        for _ in range(5):
            vad_detector.detect_voice_activity(sample_audio_file, VADMethod.ENSEMBLE)
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100 * 1024 * 1024  # 100MB

class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_workflow(self, vad_detector, sample_audio_file):
        """Test complete end-to-end workflow"""
        # 1. Detect voice activity
        vad_result = vad_detector.detect_voice_activity(sample_audio_file, VADMethod.ENSEMBLE)
        assert isinstance(vad_result, VADResult)
        
        # 2. Remove silence
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            processed_file = vad_detector.remove_silence(
                sample_audio_file, output_path, VADMethod.ENSEMBLE
            )
            assert os.path.exists(processed_file)
            
            # 3. Assess quality
            audio, sr = librosa.load(sample_audio_file, sr=None)
            quality_metrics = vad_detector.assess_audio_quality(audio, sr)
            assert isinstance(quality_metrics, AudioQualityMetrics)
            
            # 4. Get statistics
            stats = vad_detector.get_vad_statistics()
            assert isinstance(stats, dict)
            assert stats['total_processed_files'] > 0
            
        finally:
            try:
                os.unlink(output_path)
            except:
                pass
    
    def test_multiple_file_processing(self, vad_detector):
        """Test processing multiple files"""
        # Create multiple test files
        test_files = []
        
        for i in range(3):
            sr = 16000
            duration = 2
            t = np.linspace(0, duration, int(sr * duration))
            audio = 0.5 * np.sin(2 * np.pi * (440 + i * 100) * t)
            audio += 0.05 * np.random.randn(len(audio))
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, audio, sr)
                test_files.append(tmp_file.name)
        
        try:
            results = []
            for file in test_files:
                result = vad_detector.detect_voice_activity(file, VADMethod.ENSEMBLE)
                results.append(result)
            
            assert len(results) == len(test_files)
            
            # All results should be valid
            for result in results:
                assert isinstance(result, VADResult)
                assert result.total_duration > 0
            
            # Statistics should reflect multiple files
            stats = vad_detector.get_vad_statistics()
            assert stats['total_processed_files'] >= len(test_files)
            
        finally:
            for file in test_files:
                try:
                    os.unlink(file)
                except:
                    pass

def test_vad_methods_enum():
    """Test VADMethod enum"""
    assert VADMethod.WEBRTC.value == "webrtc"
    assert VADMethod.ENSEMBLE.value == "ensemble"
    assert VADMethod.ENERGY_BASED.value == "energy_based"

def test_vad_mode_enum():
    """Test VADMode enum"""
    assert VADMode.QUALITY.value == 0
    assert VADMode.NORMAL.value == 2
    assert VADMode.VERY_AGGRESSIVE.value == 3

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])