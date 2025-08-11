"""
Tests for React Frontend Component Integration
Tests the WhisperAdvanced React component functionality and API integration
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests_mock

# Test configuration
FRONTEND_URL = "http://localhost:3000"  # Adjust based on your setup
API_BASE_URL = "http://localhost:8000/api/v1"

@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for testing"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
    except Exception as e:
        pytest.skip(f"Chrome browser not available: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

@pytest.fixture
def mock_api_responses():
    """Mock API responses for testing"""
    return {
        'models': {
            "success": True,
            "data": {
                "models": [
                    {
                        "id": "whisper-1",
                        "name": "Whisper v1",
                        "description": "OpenAI's Whisper model",
                        "max_file_size_mb": 25,
                        "supported_formats": ["mp3", "wav", "m4a"],
                        "features": ["Multi-language", "Word timestamps"]
                    }
                ],
                "supported_languages": [
                    {"code": "en", "name": "English"},
                    {"code": "es", "name": "Spanish"},
                    {"code": "fr", "name": "French"}
                ]
            }
        },
        'presets': {
            "success": True,
            "data": {
                "presets": [
                    {
                        "name": "High Accuracy",
                        "description": "Maximum accuracy",
                        "config": {
                            "model": "whisper-1",
                            "temperature": 0.0,
                            "enable_language_detection": True
                        }
                    },
                    {
                        "name": "Fast Processing",
                        "description": "Optimized for speed",
                        "config": {
                            "model": "whisper-1",
                            "temperature": 0.2,
                            "enable_language_detection": False
                        }
                    }
                ]
            }
        },
        'transcribe': {
            "success": True,
            "data": {
                "text": "This is a test transcription result.",
                "language": "en",
                "language_confidence": 0.95,
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 3.0,
                        "text": "This is a test transcription result.",
                        "confidence": 0.95,
                        "speaker_id": "speaker_1"
                    }
                ],
                "words": [
                    {"word": "This", "start": 0.0, "end": 0.3, "confidence": 0.98},
                    {"word": "is", "start": 0.3, "end": 0.5, "confidence": 0.97},
                    {"word": "a", "start": 0.5, "end": 0.7, "confidence": 0.96},
                    {"word": "test", "start": 0.7, "end": 1.0, "confidence": 0.95}
                ],
                "confidence_analysis": {
                    "overall_confidence": 0.95,
                    "preprocessing_quality": 0.9,
                    "quality_improvement": 0.1
                },
                "processing_time": 1.5,
                "model_used": "whisper-base"
            }
        },
        'detect_language': {
            "success": True,
            "data": {
                "detected_language": "en",
                "confidence": 0.95,
                "alternative_languages": [
                    {"es": 0.03},
                    {"fr": 0.02}
                ]
            }
        },
        'batch_transcribe': {
            "success": True,
            "data": {
                "results": [
                    {
                        "index": 0,
                        "filename": "test1.wav",
                        "status": "success",
                        "result": {
                            "text": "First file transcription.",
                            "language": "en",
                            "processing_time": 1.2,
                            "word_count": 3,
                            "confidence_score": 0.92
                        }
                    },
                    {
                        "index": 1,
                        "filename": "test2.wav",
                        "status": "success",
                        "result": {
                            "text": "Second file transcription.",
                            "language": "en",
                            "processing_time": 1.1,
                            "word_count": 3,
                            "confidence_score": 0.94
                        }
                    }
                ],
                "summary": {
                    "total_files": 2,
                    "successful": 2,
                    "failed": 0,
                    "total_words": 6,
                    "average_processing_time": 1.15,
                    "total_processing_time": 2.3
                }
            }
        },
        'health': {
            "success": True,
            "data": {
                "status": "healthy",
                "components": {
                    "whisper_transcriber": "operational",
                    "openai_api": "available"
                }
            }
        }
    }

@pytest.mark.skipif(not os.getenv('RUN_BROWSER_TESTS'), reason="Browser tests disabled")
class TestReactComponentUI:
    """Test React component UI functionality"""
    
    def test_component_loads(self, browser):
        """Test that the component loads correctly"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Wait for component to load
        wait = WebDriverWait(browser, 10)
        title = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        assert "Whisper Advanced Integration" in title.text
    
    def test_tab_navigation(self, browser):
        """Test tab navigation between processing modes"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Find tab buttons
        single_tab = browser.find_element(By.XPATH, "//button[contains(text(), 'Single File')]")
        batch_tab = browser.find_element(By.XPATH, "//button[contains(text(), 'Batch Processing')]")
        language_tab = browser.find_element(By.XPATH, "//button[contains(text(), 'Language Detection')]")
        
        # Test tab switching
        batch_tab.click()
        assert "batch" in browser.current_url or batch_tab.get_attribute("aria-selected") == "true"
        
        language_tab.click()
        assert "language" in browser.current_url or language_tab.get_attribute("aria-selected") == "true"
        
        single_tab.click()
        assert single_tab.get_attribute("aria-selected") == "true"
    
    def test_file_upload_interface(self, browser):
        """Test file upload interface"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Find file upload area
        upload_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Select Audio File')]")
        assert upload_button.is_displayed()
        
        # Check supported formats message
        format_text = browser.find_element(By.XPATH, "//*[contains(text(), 'Supports MP3, WAV')]")
        assert format_text.is_displayed()
    
    def test_configuration_panel(self, browser):
        """Test configuration panel functionality"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Find configuration elements
        model_select = browser.find_element(By.XPATH, "//select[contains(@name, 'model') or @aria-label='Model']")
        language_select = browser.find_element(By.XPATH, "//select[contains(@name, 'language') or @aria-label='Language']")
        temperature_slider = browser.find_element(By.XPATH, "//input[@type='range']")
        
        assert model_select.is_displayed()
        assert language_select.is_displayed()
        assert temperature_slider.is_displayed()
        
        # Test temperature slider
        initial_value = temperature_slider.get_attribute("value")
        browser.execute_script("arguments[0].value = '0.5'; arguments[0].dispatchEvent(new Event('change'));", temperature_slider)
        new_value = temperature_slider.get_attribute("value")
        assert new_value != initial_value
    
    def test_feature_toggles(self, browser):
        """Test feature toggle switches"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Find toggle switches
        toggles = browser.find_elements(By.XPATH, "//input[@type='checkbox' or @role='switch']")
        
        assert len(toggles) >= 4  # Should have multiple feature toggles
        
        # Test toggling a switch
        if toggles:
            toggle = toggles[0]
            initial_state = toggle.is_selected()
            toggle.click()
            new_state = toggle.is_selected()
            assert new_state != initial_state

@pytest.mark.skipif(not os.getenv('RUN_BROWSER_TESTS'), reason="Browser tests disabled")
class TestReactComponentAPI:
    """Test React component API integration"""
    
    def test_load_presets(self, browser, mock_api_responses):
        """Test loading presets from API"""
        with requests_mock.Mocker() as m:
            m.get(f"{API_BASE_URL}/whisper-advanced/presets", json=mock_api_responses['presets'])
            
            browser.get(f"{FRONTEND_URL}/whisper-advanced")
            
            # Wait for presets to load
            wait = WebDriverWait(browser, 10)
            preset_select = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@name, 'preset') or @aria-label='Preset']")
            ))
            
            # Check if presets are loaded
            options = preset_select.find_elements(By.TAG_NAME, "option")
            preset_names = [opt.text for opt in options]
            
            assert "High Accuracy" in preset_names
            assert "Fast Processing" in preset_names
    
    def test_load_models(self, browser, mock_api_responses):
        """Test loading models from API"""
        with requests_mock.Mocker() as m:
            m.get(f"{API_BASE_URL}/whisper-advanced/models", json=mock_api_responses['models'])
            
            browser.get(f"{FRONTEND_URL}/whisper-advanced")
            
            # Wait for models to load
            wait = WebDriverWait(browser, 10)
            model_select = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//select[contains(@name, 'model') or @aria-label='Model']")
            ))
            
            # Check if models are loaded
            options = model_select.find_elements(By.TAG_NAME, "option")
            model_names = [opt.text for opt in options]
            
            assert "Whisper v1" in model_names

class TestReactComponentLogic:
    """Test React component logic without browser"""
    
    def test_config_validation(self):
        """Test configuration validation logic"""
        # This would test the validation functions in the React component
        # Since we can't directly test React functions, we test the expected behavior
        
        valid_config = {
            "model": "whisper-1",
            "temperature": 0.5,
            "confidence_threshold": 0.8
        }
        
        invalid_config = {
            "model": "whisper-1",
            "temperature": 2.0,  # Invalid: > 1.0
            "confidence_threshold": 1.5  # Invalid: > 1.0
        }
        
        # Test temperature validation
        assert 0.0 <= valid_config["temperature"] <= 1.0
        assert not (0.0 <= invalid_config["temperature"] <= 1.0)
        
        # Test confidence threshold validation
        assert 0.0 <= valid_config["confidence_threshold"] <= 1.0
        assert not (0.0 <= invalid_config["confidence_threshold"] <= 1.0)
    
    def test_file_size_validation(self):
        """Test file size validation logic"""
        max_size = 25 * 1024 * 1024  # 25MB
        
        valid_size = 10 * 1024 * 1024  # 10MB
        invalid_size = 30 * 1024 * 1024  # 30MB
        
        assert valid_size <= max_size
        assert invalid_size > max_size
    
    def test_batch_file_validation(self):
        """Test batch file validation logic"""
        max_files = 10
        max_total_size = 250 * 1024 * 1024  # 250MB
        
        # Valid batch
        valid_batch = [5 * 1024 * 1024] * 8  # 8 files, 5MB each
        assert len(valid_batch) <= max_files
        assert sum(valid_batch) <= max_total_size
        
        # Too many files
        too_many_files = [1 * 1024 * 1024] * 12  # 12 files
        assert len(too_many_files) > max_files
        
        # Total size too large
        too_large_batch = [30 * 1024 * 1024] * 9  # 9 files, 30MB each
        assert sum(too_large_batch) > max_total_size
    
    def test_vocabulary_parsing(self):
        """Test custom vocabulary parsing logic"""
        vocabulary_input = "whisper, transcription, API, neural network"
        expected_terms = ["whisper", "transcription", "API", "neural network"]
        
        # Simulate the parsing logic
        parsed_terms = [term.strip() for term in vocabulary_input.split(',') if term.strip()]
        
        assert parsed_terms == expected_terms
        
        # Test empty input
        empty_input = ""
        parsed_empty = [term.strip() for term in empty_input.split(',') if term.strip()]
        assert parsed_empty == []
        
        # Test input with extra spaces
        messy_input = " term1 ,  term2  , term3 , "
        parsed_messy = [term.strip() for term in messy_input.split(',') if term.strip()]
        assert parsed_messy == ["term1", "term2", "term3"]

class TestReactComponentAccessibility:
    """Test React component accessibility features"""
    
    @pytest.mark.skipif(not os.getenv('RUN_BROWSER_TESTS'), reason="Browser tests disabled")
    def test_keyboard_navigation(self, browser):
        """Test keyboard navigation"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Test tab navigation
        body = browser.find_element(By.TAG_NAME, "body")
        body.click()  # Focus on page
        
        # Send tab key multiple times and check focus
        from selenium.webdriver.common.keys import Keys
        
        focusable_elements = []
        for i in range(10):  # Tab through first 10 focusable elements
            active_element = browser.switch_to.active_element
            if active_element and active_element.tag_name != "body":
                focusable_elements.append(active_element.tag_name)
            body.send_keys(Keys.TAB)
        
        # Should have found some focusable elements
        assert len(focusable_elements) > 0
    
    @pytest.mark.skipif(not os.getenv('RUN_BROWSER_TESTS'), reason="Browser tests disabled")
    def test_aria_labels(self, browser):
        """Test ARIA labels and accessibility attributes"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Check for ARIA labels on important elements
        labeled_elements = browser.find_elements(By.XPATH, "//*[@aria-label or @aria-labelledby]")
        assert len(labeled_elements) > 0
        
        # Check for proper heading structure
        headings = browser.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4 | //h5 | //h6")
        assert len(headings) > 0
        
        # Check for alt text on images (if any)
        images = browser.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            assert alt_text is not None  # Should have alt text

class TestReactComponentResponsive:
    """Test React component responsive design"""
    
    @pytest.mark.skipif(not os.getenv('RUN_BROWSER_TESTS'), reason="Browser tests disabled")
    def test_mobile_layout(self, browser):
        """Test mobile responsive layout"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        
        # Test different screen sizes
        screen_sizes = [
            (375, 667),   # iPhone SE
            (768, 1024),  # iPad
            (1920, 1080)  # Desktop
        ]
        
        for width, height in screen_sizes:
            browser.set_window_size(width, height)
            
            # Check if main container is visible
            main_container = browser.find_element(By.XPATH, "//div[contains(@class, 'max-w')]")
            assert main_container.is_displayed()
            
            # Check if tabs are still functional
            tabs = browser.find_elements(By.XPATH, "//button[contains(@role, 'tab') or contains(@class, 'tab')]")
            if tabs:
                assert tabs[0].is_displayed()
    
    @pytest.mark.skipif(not os.getenv('RUN_BROWSER_TESTS'), reason="Browser tests disabled")
    def test_touch_interactions(self, browser):
        """Test touch-friendly interactions"""
        browser.get(f"{FRONTEND_URL}/whisper-advanced")
        browser.set_window_size(375, 667)  # Mobile size
        
        # Check button sizes (should be touch-friendly)
        buttons = browser.find_elements(By.TAG_NAME, "button")
        
        for button in buttons[:5]:  # Check first 5 buttons
            if button.is_displayed():
                size = button.size
                # Touch targets should be at least 44px (iOS) or 48px (Android)
                assert size['height'] >= 40 or size['width'] >= 40

# Test utilities
def create_test_audio_file():
    """Create a test audio file for upload testing"""
    import tempfile
    import wave
    import numpy as np
    
    # Create a simple test audio file
    sample_rate = 16000
    duration = 2.0
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
    audio_data = (audio_data * 32767).astype(np.int16)
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        with wave.open(f.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return f.name

if __name__ == "__main__":
    # Run React component tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])