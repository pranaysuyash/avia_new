#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# Set up test environment variables
os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'
os.environ['ELEVENLABS_API_KEY'] = 'test-key-for-testing'
os.environ['LOG_LEVEL'] = 'WARNING'

@pytest.fixture(scope="session")
def test_data_dir():
    """Create and provide test data directory"""
    temp_dir = tempfile.mkdtemp(prefix="test_data_")
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def generated_test_data(test_data_dir):
    """Generate test data for the session"""
    try:
        from test_data_generator import TestDataGenerator
        generator = TestDataGenerator(test_data_dir)
        dataset = generator.generate_all_test_data()
        return dataset
    except Exception as e:
        pytest.skip(f"Could not generate test data: {e}")

@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing"""
    import wave
    import numpy as np
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file.close()
    
    # Generate simple sine wave
    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('openai.OpenAI') as mock_client:
        yield mock_client

@pytest.fixture
def mock_elevenlabs_client():
    """Mock ElevenLabs client for testing"""
    with patch('elevenlabs.client.ElevenLabs') as mock_client:
        yield mock_client

@pytest.fixture
def sample_transcript():
    """Provide sample transcript for testing"""
    return """
    Good morning everyone. This is John Smith, CEO of TechCorp Industries. 
    Today is January 15th, 2024, and we're here in our Seattle headquarters 
    for the quarterly board meeting. We'll be discussing our Q4 results 
    with Sarah Johnson from the finance team.
    
    Our revenue for this quarter reached $2.5 million, which represents 
    a 25% increase from last year. We've successfully expanded to 
    New York City, hiring 150 new employees.
    """.strip()

@pytest.fixture
def sample_entities():
    """Provide sample entities for testing"""
    return {
        "persons": ["John Smith", "Sarah Johnson"],
        "organizations": ["TechCorp Industries"],
        "locations": ["Seattle", "New York City"],
        "dates": ["January 15th, 2024", "Q4"],
        "money": ["$2.5 million"],
        "numbers": ["25%", "150"]
    }

def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "error_handling: Error handling tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file names
    for item in items:
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "error" in item.nodeid:
            item.add_marker(pytest.mark.error_handling)
        else:
            item.add_marker(pytest.mark.unit)

def pytest_runtest_setup(item):
    """Setup for each test"""
    # Skip tests that require specific conditions
    if "api" in item.keywords and not os.getenv("RUN_API_TESTS"):
        pytest.skip("API tests disabled (set RUN_API_TESTS=1 to enable)")

def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    print("\n🧪 Starting comprehensive test session...")
    print("Environment: Test mode with mocked external services")

def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    if exitstatus == 0:
        print("\n🎉 All tests completed successfully!")
    else:
        print(f"\n❌ Tests completed with exit status: {exitstatus}")

# Custom pytest hooks for better reporting
def pytest_runtest_logreport(report):
    """Called for each test report"""
    if report.when == "call":
        if report.outcome == "passed":
            print(f"✅ {report.nodeid}")
        elif report.outcome == "failed":
            print(f"❌ {report.nodeid}")
        elif report.outcome == "skipped":
            print(f"⏭️ {report.nodeid}")

# Performance test configuration
@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        "max_processing_time": 30.0,  # seconds
        "max_memory_usage": 500,      # MB
        "min_throughput": 100,        # words per second
        "timeout": 60                 # seconds
    }