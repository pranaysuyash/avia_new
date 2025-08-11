"""
Pytest configuration and shared fixtures for Whisper Advanced Integration tests
"""

import pytest
import asyncio
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(TEST_DATA_DIR, exist_ok=True)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_audio_samples():
    """Create various test audio samples for different test scenarios"""
    samples = {}
    
    # Short audio sample (2 seconds)
    samples['short'] = create_test_audio_file("short_test.wav", duration=2.0, frequency=440)
    
    # Medium audio sample (10 seconds)
    samples['medium'] = create_test_audio_file("medium_test.wav", duration=10.0, frequency=880)
    
    # Long audio sample (30 seconds)
    samples['long'] = create_test_audio_file("long_test.wav", duration=30.0, frequency=220)
    
    # Multi-tone audio (simulating speech-like patterns)
    samples['multi_tone'] = create_multi_tone_audio_file("multi_tone_test.wav")
    
    # Noisy audio sample
    samples['noisy'] = create_noisy_audio_file("noisy_test.wav")
    
    yield samples
    
    # Cleanup
    for sample_path in samples.values():
        if os.path.exists(sample_path):
            os.unlink(sample_path)

def create_test_audio_file(filename, duration=2.0, frequency=440, sample_rate=16000):
    """Create a test audio file with specified parameters"""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
    
    # Add some variation to make it more realistic
    audio_data += np.sin(2 * np.pi * frequency * 1.5 * t) * 0.1
    audio_data += np.random.normal(0, 0.01, len(audio_data))  # Add slight noise
    
    # Convert to 16-bit PCM
    audio_data = np.clip(audio_data, -1, 1)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Write WAV file
    write_wav_file(filepath, audio_data, sample_rate)
    
    return filepath

def create_multi_tone_audio_file(filename, duration=5.0, sample_rate=16000):
    """Create audio with multiple tones to simulate speech patterns"""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.zeros_like(t)
    
    # Add multiple frequency components
    frequencies = [200, 400, 800, 1200, 1600]  # Simulate formants
    for i, freq in enumerate(frequencies):
        amplitude = 0.2 / (i + 1)  # Decreasing amplitude
        audio_data += np.sin(2 * np.pi * freq * t) * amplitude
    
    # Add envelope to simulate speech segments
    envelope = np.ones_like(t)
    segment_length = int(sample_rate * 0.5)  # 0.5 second segments
    for i in range(0, len(envelope), segment_length * 2):
        end_idx = min(i + segment_length, len(envelope))
        envelope[i:end_idx] *= np.linspace(0, 1, end_idx - i)
        
        if end_idx < len(envelope):
            silence_end = min(end_idx + segment_length, len(envelope))
            envelope[end_idx:silence_end] *= np.linspace(1, 0, silence_end - end_idx)
    
    audio_data *= envelope
    
    # Convert to 16-bit PCM
    audio_data = np.clip(audio_data, -1, 1)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    write_wav_file(filepath, audio_data, sample_rate)
    
    return filepath

def create_noisy_audio_file(filename, duration=3.0, sample_rate=16000, snr_db=10):
    """Create audio with added noise for testing noise reduction"""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create signal (speech-like)
    signal = np.sin(2 * np.pi * 440 * t) * 0.5
    signal += np.sin(2 * np.pi * 880 * t) * 0.3
    
    # Add noise
    noise = np.random.normal(0, 1, len(signal))
    
    # Calculate noise level for desired SNR
    signal_power = np.mean(signal ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = noise * np.sqrt(noise_power / np.mean(noise ** 2))
    
    # Combine signal and noise
    audio_data = signal + noise
    
    # Convert to 16-bit PCM
    audio_data = np.clip(audio_data, -1, 1)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    write_wav_file(filepath, audio_data, sample_rate)
    
    return filepath

def write_wav_file(filepath, audio_data, sample_rate):
    """Write audio data to WAV file"""
    import struct
    
    with open(filepath, 'wb') as f:
        # WAV header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + len(audio_data) * 2))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # PCM format chunk size
        f.write(struct.pack('<H', 1))   # PCM format
        f.write(struct.pack('<H', 1))   # Mono
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))  # Byte rate
        f.write(struct.pack('<H', 2))   # Block align
        f.write(struct.pack('<H', 16))  # Bits per sample
        f.write(b'data')
        f.write(struct.pack('<I', len(audio_data) * 2))
        
        # Audio data
        for sample in audio_data:
            f.write(struct.pack('<h', sample))

@pytest.fixture
def mock_whisper_model():
    """Create a mock Whisper model for testing"""
    model = Mock()
    
    # Mock transcribe method
    model.transcribe.return_value = {
        'text': 'This is a mock transcription result.',
        'language': 'en',
        'segments': [
            {
                'id': 0,
                'start': 0.0,
                'end': 3.0,
                'text': 'This is a mock transcription result.',
                'words': [
                    {'word': 'This', 'start': 0.0, 'end': 0.3, 'probability': 0.98},
                    {'word': 'is', 'start': 0.3, 'end': 0.5, 'probability': 0.97},
                    {'word': 'a', 'start': 0.5, 'end': 0.6, 'probability': 0.96},
                    {'word': 'mock', 'start': 0.6, 'end': 1.0, 'probability': 0.95},
                    {'word': 'transcription', 'start': 1.0, 'end': 1.8, 'probability': 0.94},
                    {'word': 'result', 'start': 1.8, 'end': 2.3, 'probability': 0.93},
                ]
            }
        ]
    }
    
    # Mock detect_language method
    model.detect_language.return_value = ('en', 0.95)
    
    return model

@pytest.fixture
def mock_audio_data():
    """Create mock audio data for testing"""
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * 440 * t) * 0.5
    return audio_data, sample_rate

@pytest.fixture
def test_configurations():
    """Provide various test configurations"""
    return {
        'minimal': {
            'model': 'whisper-1',
            'temperature': 0.0
        },
        'standard': {
            'model': 'whisper-1',
            'language': 'en',
            'temperature': 0.0,
            'enable_language_detection': True,
            'enable_confidence_analysis': True,
            'enable_word_timestamps': True,
            'confidence_threshold': 0.8,
            'chunk_length_s': 30
        },
        'advanced': {
            'model': 'whisper-1',
            'language': 'en',
            'temperature': 0.1,
            'enable_language_detection': True,
            'enable_confidence_analysis': True,
            'enable_word_timestamps': True,
            'enable_speaker_detection': True,
            'enable_custom_vocabulary': True,
            'confidence_threshold': 0.85,
            'chunk_length_s': 25
        }
    }

@pytest.fixture
def mock_preprocessing_result():
    """Create a mock preprocessing result"""
    from whisper_audio_preprocessor import PreprocessingResult, AudioMetrics
    
    metrics = AudioMetrics(
        snr_db=15.5,
        dynamic_range_db=45.2,
        spectral_centroid=2500.0,
        zero_crossing_rate=0.1,
        quality_score=0.85
    )
    
    return PreprocessingResult(
        processed_audio_path="/tmp/processed_test.wav",
        original_metrics=metrics,
        processed_metrics=metrics,
        processing_time=0.5,
        quality_improvement=0.15,
        applied_filters=['noise_reduction', 'normalization']
    )

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically cleanup temporary files after each test"""
    temp_files = []
    
    def track_temp_file(filepath):
        temp_files.append(filepath)
        return filepath
    
    # Provide the tracking function to tests
    yield track_temp_file
    
    # Cleanup
    for filepath in temp_files:
        if os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except OSError:
                pass  # File might already be deleted

# Performance testing utilities
@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests"""
    import time
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.cpu_usage = []
            self.memory_usage = []
            self.monitoring = False
            self.monitor_thread = None
        
        def start(self):
            self.start_time = time.time()
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)
            self.monitor_thread.start()
        
        def stop(self):
            self.end_time = time.time()
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
        
        def _monitor(self):
            while self.monitoring:
                self.cpu_usage.append(psutil.cpu_percent())
                self.memory_usage.append(psutil.virtual_memory().percent)
                time.sleep(0.1)
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
        
        @property
        def avg_cpu_usage(self):
            return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        
        @property
        def avg_memory_usage(self):
            return sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
    
    return PerformanceMonitor()

# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_model: Tests requiring actual models")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "test_unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker for tests that might take longer
        if any(keyword in item.nodeid.lower() for keyword in ['batch', 'concurrent', 'load']):
            item.add_marker(pytest.mark.slow)

# Test data cleanup
def pytest_sessionfinish(session, exitstatus):
    """Clean up test data after session"""
    if os.path.exists(TEST_DATA_DIR):
        import shutil
        try:
            shutil.rmtree(TEST_DATA_DIR)
        except OSError:
            pass  # Directory might not be empty or accessible