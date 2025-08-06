#!/usr/bin/env python3
"""
Integration Tests for Image and Audio Preprocessing Systems
Tests the full stack: API endpoints, core processing, and expected outputs
"""

import pytest
import requests
import base64
import json
import time
import os
import numpy as np
import cv2
import soundfile as sf
from pathlib import Path
from typing import Dict, Any, Optional

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TIMEOUT_SECONDS = 120

class PreprocessingIntegrationTests:
    """Integration test suite for preprocessing systems"""
    
    @classmethod
    def setup_class(cls):
        """Set up test data and verify API availability"""
        cls.setup_test_data()
        cls.verify_api_health()
    
    @classmethod
    def setup_test_data(cls):
        """Create test images and audio files"""
        TEST_DATA_DIR.mkdir(exist_ok=True)
        
        # Create test image
        test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
        # Add some noise to make preprocessing meaningful
        noise = np.random.normal(0, 25, test_image.shape).astype(np.uint8)
        test_image = np.clip(test_image + noise, 0, 255)
        
        cls.test_image_path = TEST_DATA_DIR / "test_image.png"
        cv2.imwrite(str(cls.test_image_path), test_image)
        
        # Create test audio
        sample_rate = 44100
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create audio with speech-like characteristics
        speech_signal = (
            0.3 * np.sin(2 * np.pi * 200 * t) +  # Fundamental frequency
            0.2 * np.sin(2 * np.pi * 400 * t) +  # First harmonic
            0.1 * np.sin(2 * np.pi * 600 * t)    # Second harmonic
        )
        
        # Add noise to simulate real-world conditions
        noise = 0.05 * np.random.normal(0, 1, len(speech_signal))
        test_audio = speech_signal + noise
        
        # Add silence periods
        silence_start = int(0.5 * sample_rate)
        silence_end = int(1.0 * sample_rate)
        test_audio[silence_start:silence_end] *= 0.01  # Very quiet
        
        cls.test_audio_path = TEST_DATA_DIR / "test_audio.wav"
        sf.write(str(cls.test_audio_path), test_audio, sample_rate)
        
        print(f"Created test data in {TEST_DATA_DIR}")
    
    @classmethod
    def verify_api_health(cls):
        """Verify API endpoints are available"""
        try:
            # Check image preprocessing health
            response = requests.get(f"{API_BASE_URL}/api/v1/image/health", timeout=5)
            assert response.status_code == 200
            
            # Check audio preprocessing health  
            response = requests.get(f"{API_BASE_URL}/api/v1/audio/health", timeout=5)
            assert response.status_code == 200
            
            print("✓ API health checks passed")
        except Exception as e:
            pytest.skip(f"API not available: {e}")
    
    def encode_file_to_base64(self, file_path: Path) -> str:
        """Encode file to base64 for API requests"""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def wait_for_task_completion(self, task_id: str, endpoint_type: str) -> Dict[str, Any]:
        """Poll task status until completion"""
        start_time = time.time()
        
        while time.time() - start_time < TIMEOUT_SECONDS:
            try:
                response = requests.get(f"{API_BASE_URL}/api/v1/{endpoint_type}/status/{task_id}")
                
                if response.status_code != 200:
                    time.sleep(1)
                    continue
                
                result = response.json()
                
                if result['status'] == 'completed':
                    return result
                elif result['status'] == 'failed':
                    raise Exception(f"Task failed: {result.get('message', 'Unknown error')}")
                
                time.sleep(1)
                
            except requests.RequestException:
                time.sleep(1)
                continue
        
        raise TimeoutError(f"Task {task_id} did not complete within {TIMEOUT_SECONDS} seconds")

class TestImagePreprocessing(PreprocessingIntegrationTests):
    """Test image preprocessing integration"""
    
    def test_image_presets_endpoint(self):
        """Test image preprocessing presets endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/v1/image/presets")
        assert response.status_code == 200
        
        data = response.json()
        assert 'presets' in data
        assert 'default' in data['presets']
        assert 'ocr_optimized' in data['presets']
        
        print("✓ Image presets endpoint working")
    
    def test_image_config_validation(self):
        """Test image config validation endpoint"""
        valid_config = {
            "enable_denoising": True,
            "denoise_method": "bilateral",
            "auto_contrast": True,
            "upscale_factor": 2.0
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/image/config/validate",
            json=valid_config
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['valid'] is True
        
        print("✓ Image config validation working")
    
    def test_image_preprocessing_basic(self):
        """Test basic image preprocessing workflow"""
        # Encode test image
        image_base64 = self.encode_file_to_base64(self.test_image_path)
        
        # Create request
        request_data = {
            "image_data": image_base64,
            "config": {
                "enable_denoising": True,
                "denoise_method": "bilateral",
                "auto_contrast": True,
                "enable_sharpening": True,
                "upscale_factor": 1.5
            }
        }
        
        # Submit processing request
        response = requests.post(
            f"{API_BASE_URL}/api/v1/image/preprocess",
            json=request_data
        )
        assert response.status_code == 200
        
        task_data = response.json()
        assert 'task_id' in task_data
        assert task_data['status'] == 'processing'
        
        # Wait for completion
        result = self.wait_for_task_completion(task_data['task_id'], 'image')
        
        # Verify results
        assert result['status'] == 'completed'
        assert 'processed_image' in result
        assert 'operations_applied' in result
        assert len(result['operations_applied']) > 0
        assert 'processing_time' in result
        assert result['processing_time'] > 0
        
        # Verify processed image is valid base64
        try:
            processed_image_data = base64.b64decode(result['processed_image'])
            assert len(processed_image_data) > 0
        except Exception as e:
            pytest.fail(f"Invalid processed image data: {e}")
        
        print(f"✓ Basic image preprocessing completed in {result['processing_time']:.2f}s")
        print(f"  Applied operations: {', '.join(result['operations_applied'])}")
    
    def test_image_preprocessing_presets(self):
        """Test image preprocessing with different presets"""
        image_base64 = self.encode_file_to_base64(self.test_image_path)
        
        # Get available presets
        presets_response = requests.get(f"{API_BASE_URL}/api/v1/image/presets")
        presets = presets_response.json()['presets']
        
        for preset_name, preset_config in presets.items():
            print(f"Testing preset: {preset_name}")
            
            request_data = {
                "image_data": image_base64,
                "config": preset_config
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/image/preprocess",
                json=request_data
            )
            assert response.status_code == 200
            
            task_data = response.json()
            result = self.wait_for_task_completion(task_data['task_id'], 'image')
            
            assert result['status'] == 'completed'
            assert 'processed_image' in result
            
            print(f"  ✓ {preset_name} preset completed")
    
    def test_image_batch_processing(self):
        """Test batch image processing"""
        image_base64 = self.encode_file_to_base64(self.test_image_path)
        
        # Create batch with 3 copies of the same image
        batch_request = {
            "images": [image_base64, image_base64, image_base64],
            "config": {
                "enable_denoising": True,
                "auto_contrast": True
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/image/batch/preprocess",
            json=batch_request
        )
        assert response.status_code == 200
        
        batch_data = response.json()
        assert 'batch_id' in batch_data
        assert 'task_ids' in batch_data
        assert len(batch_data['task_ids']) == 3
        
        # Wait for batch completion
        batch_id = batch_data['batch_id']
        start_time = time.time()
        
        while time.time() - start_time < TIMEOUT_SECONDS:
            status_response = requests.get(f"{API_BASE_URL}/api/v1/image/batch/status/{batch_id}")
            status_data = status_response.json()
            
            if status_data['completed'] == status_data['total']:
                break
            
            time.sleep(2)
        
        # Verify all tasks completed
        final_status = requests.get(f"{API_BASE_URL}/api/v1/image/batch/status/{batch_id}")
        final_data = final_status.json()
        
        assert final_data['completed'] == 3
        assert final_data['failed'] == 0
        
        print("✓ Batch image processing completed")

class TestAudioPreprocessing(PreprocessingIntegrationTests):
    """Test audio preprocessing integration"""
    
    def test_audio_presets_endpoint(self):
        """Test audio preprocessing presets endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/v1/audio/presets")
        assert response.status_code == 200
        
        data = response.json()
        assert 'presets' in data
        assert 'transcription_optimized' in data['presets']
        assert 'podcast_quality' in data['presets']
        
        print("✓ Audio presets endpoint working")
    
    def test_audio_analysis(self):
        """Test audio analysis endpoint"""
        audio_base64 = self.encode_file_to_base64(self.test_audio_path)
        
        request_data = {
            "audio_data": audio_base64,
            "analysis_type": "quality"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/audio/analyze",
            json=request_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'quality_metrics' in data
        assert 'duration' in data
        assert 'sample_rate' in data
        assert 'recommendations' in data
        
        # Verify quality metrics structure
        metrics = data['quality_metrics']
        assert 'snr' in metrics
        assert 'dynamic_range' in metrics
        assert 'energy' in metrics
        
        print("✓ Audio analysis working")
        print(f"  Duration: {data['duration']:.2f}s")
        print(f"  Sample rate: {data['sample_rate']} Hz")
        print(f"  SNR: {metrics['snr']:.1f} dB")
    
    def test_audio_vad_analysis(self):
        """Test Voice Activity Detection analysis"""
        audio_base64 = self.encode_file_to_base64(self.test_audio_path)
        
        request_data = {
            "audio_data": audio_base64,
            "analysis_type": "vad"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/audio/analyze",
            json=request_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'voice_duration' in data
        assert 'silence_duration' in data
        assert 'voice_ratio' in data
        assert 'voice_segments' in data
        
        print("✓ Audio VAD analysis working")
        print(f"  Voice ratio: {data['voice_ratio']:.1f}%")
        print(f"  Voice segments: {data['segment_count']}")
    
    def test_audio_preprocessing_basic(self):
        """Test basic audio preprocessing workflow"""
        audio_base64 = self.encode_file_to_base64(self.test_audio_path)
        
        request_data = {
            "audio_data": audio_base64,
            "config": {
                "target_sample_rate": 16000,
                "enable_noise_reduction": True,
                "noise_reduction_strength": 0.7,
                "enable_normalization": True,
                "remove_silence": True,
                "silence_threshold": -40.0
            }
        }
        
        # Submit processing request
        response = requests.post(
            f"{API_BASE_URL}/api/v1/audio/preprocess",
            json=request_data
        )
        assert response.status_code == 200
        
        task_data = response.json()
        assert 'task_id' in task_data
        assert task_data['status'] == 'processing'
        
        # Wait for completion
        result = self.wait_for_task_completion(task_data['task_id'], 'audio')
        
        # Verify results
        assert result['status'] == 'completed'
        assert 'processed_audio' in result
        assert 'operations_applied' in result
        assert len(result['operations_applied']) > 0
        assert 'processing_time' in result
        assert result['processing_time'] > 0
        assert 'duration' in result
        assert result['sample_rate'] == 16000
        
        # Verify duration reduction (silence removal)
        original_duration = result['duration']['original']
        processed_duration = result['duration']['processed']
        assert processed_duration <= original_duration
        
        # Verify processed audio is valid base64
        try:
            processed_audio_data = base64.b64decode(result['processed_audio'])
            assert len(processed_audio_data) > 0
        except Exception as e:
            pytest.fail(f"Invalid processed audio data: {e}")
        
        reduction_pct = (original_duration - processed_duration) / original_duration * 100
        print(f"✓ Basic audio preprocessing completed in {result['processing_time']:.2f}s")
        print(f"  Duration reduction: {reduction_pct:.1f}%")
        print(f"  Applied operations: {', '.join(result['operations_applied'])}")
    
    def test_audio_preprocessing_presets(self):
        """Test audio preprocessing with different presets"""
        audio_base64 = self.encode_file_to_base64(self.test_audio_path)
        
        # Get available presets
        presets_response = requests.get(f"{API_BASE_URL}/api/v1/audio/presets")
        presets = presets_response.json()['presets']
        
        for preset_name, preset_config in presets.items():
            print(f"Testing preset: {preset_name}")
            
            request_data = {
                "audio_data": audio_base64,
                "config": preset_config
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/audio/preprocess",
                json=request_data
            )
            assert response.status_code == 200
            
            task_data = response.json()
            result = self.wait_for_task_completion(task_data['task_id'], 'audio')
            
            assert result['status'] == 'completed'
            assert 'processed_audio' in result
            assert result['sample_rate'] == preset_config['target_sample_rate']
            
            print(f"  ✓ {preset_name} preset completed")

class TestCrossSystemIntegration(PreprocessingIntegrationTests):
    """Test integration between image and audio systems"""
    
    def test_concurrent_processing(self):
        """Test concurrent image and audio processing"""
        image_base64 = self.encode_file_to_base64(self.test_image_path)
        audio_base64 = self.encode_file_to_base64(self.test_audio_path)
        
        # Submit both requests simultaneously
        image_request = {
            "image_data": image_base64,
            "config": {"enable_denoising": True, "auto_contrast": True}
        }
        
        audio_request = {
            "audio_data": audio_base64,
            "config": {"enable_noise_reduction": True, "remove_silence": True}
        }
        
        # Start both processes
        image_response = requests.post(f"{API_BASE_URL}/api/v1/image/preprocess", json=image_request)
        audio_response = requests.post(f"{API_BASE_URL}/api/v1/audio/preprocess", json=audio_request)
        
        assert image_response.status_code == 200
        assert audio_response.status_code == 200
        
        image_task_id = image_response.json()['task_id']
        audio_task_id = audio_response.json()['task_id']
        
        # Wait for both to complete
        image_result = self.wait_for_task_completion(image_task_id, 'image')
        audio_result = self.wait_for_task_completion(audio_task_id, 'audio')
        
        assert image_result['status'] == 'completed'
        assert audio_result['status'] == 'completed'
        
        print("✓ Concurrent processing completed successfully")
    
    def test_system_health_monitoring(self):
        """Test health monitoring across both systems"""
        # Check image system health
        image_health = requests.get(f"{API_BASE_URL}/api/v1/image/health")
        assert image_health.status_code == 200
        
        image_data = image_health.json()
        assert image_data['status'] == 'healthy'
        assert 'active_tasks' in image_data
        assert 'total_tasks' in image_data
        
        # Check audio system health
        audio_health = requests.get(f"{API_BASE_URL}/api/v1/audio/health")
        assert audio_health.status_code == 200
        
        audio_data = audio_health.json()
        assert audio_data['status'] == 'healthy'
        assert 'active_tasks' in audio_data
        assert 'total_tasks' in audio_data
        
        print("✓ System health monitoring working")
        print(f"  Image system: {image_data['total_tasks']} total tasks")
        print(f"  Audio system: {audio_data['total_tasks']} total tasks")

def run_integration_tests():
    """Run all integration tests"""
    print("Starting Preprocessing Systems Integration Tests")
    print("=" * 60)
    
    try:
        # Test image preprocessing
        print("\n📷 Testing Image Preprocessing System...")
        image_tests = TestImagePreprocessing()
        image_tests.test_image_presets_endpoint()
        image_tests.test_image_config_validation()
        image_tests.test_image_preprocessing_basic()
        image_tests.test_image_preprocessing_presets()
        image_tests.test_image_batch_processing()
        
        # Test audio preprocessing
        print("\n🎵 Testing Audio Preprocessing System...")
        audio_tests = TestAudioPreprocessing()
        audio_tests.test_audio_presets_endpoint()
        audio_tests.test_audio_analysis()
        audio_tests.test_audio_vad_analysis()
        audio_tests.test_audio_preprocessing_basic()
        audio_tests.test_audio_preprocessing_presets()
        
        # Test cross-system integration
        print("\n🔗 Testing Cross-System Integration...")
        cross_tests = TestCrossSystemIntegration()
        cross_tests.test_concurrent_processing()
        cross_tests.test_system_health_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("🎉 Full-stack preprocessing implementation verified")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise

if __name__ == "__main__":
    run_integration_tests()