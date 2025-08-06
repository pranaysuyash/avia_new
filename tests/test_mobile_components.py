"""
Test suite for Mobile-specific components (Phase 3)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import base64
from datetime import datetime
import io
from PIL import Image
import numpy as np

from api.app import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_current_user():
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "role": "user"
    }

@pytest.fixture
def sample_audio_data():
    """Generate sample audio data for testing"""
    # Generate a simple sine wave
    sample_rate = 44100
    duration = 1.0
    frequency = 440.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(frequency * 2 * np.pi * t) * 0.5
    
    # Convert to bytes (16-bit PCM)
    audio_bytes = (audio * 32767).astype(np.int16).tobytes()
    return base64.b64encode(audio_bytes).decode()

@pytest.fixture
def sample_image_data():
    """Generate sample image data for testing"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    return base64.b64encode(img_bytes).decode()


class TestAudioPreprocessingMobile:
    """Test Audio Preprocessing Mobile functionality"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_audio_noise_reduction(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_audio_data):
        """Test audio noise reduction preprocessing"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        preprocessing_data = {
            "audio_data": sample_audio_data,
            "processing_options": {
                "noise_reduction": True,
                "noise_reduction_level": 0.8,
                "normalize": True,
                "trim_silence": True
            },
            "format": "wav",
            "sample_rate": 44100
        }
        
        response = client.post(
            "/api/v1/audio/preprocess",
            json=preprocessing_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "processed_audio" in data["data"]
        assert "metadata" in data["data"]
        assert data["data"]["metadata"]["noise_reduced"] == True
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_audio_enhancement(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_audio_data):
        """Test audio enhancement features"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        enhancement_data = {
            "audio_data": sample_audio_data,
            "enhancements": {
                "eq_preset": "voice_clarity",
                "compression": {
                    "threshold": -20,
                    "ratio": 4,
                    "attack": 5,
                    "release": 50
                },
                "reverb": {
                    "enabled": False
                }
            }
        }
        
        response = client.post(
            "/api/v1/audio/enhance",
            json=enhancement_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "enhanced_audio" in data["data"]
        assert "applied_effects" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_audio_format_conversion(self, mock_auth, auth_headers, mock_current_user, sample_audio_data):
        """Test audio format conversion"""
        mock_auth.return_value = mock_current_user
        
        conversion_data = {
            "audio_data": sample_audio_data,
            "source_format": "wav",
            "target_format": "mp3",
            "bitrate": 192000,
            "sample_rate": 44100
        }
        
        response = client.post(
            "/api/v1/audio/convert",
            json=conversion_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "converted_audio" in data["data"]
        assert data["data"]["format"] == "mp3"
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_batch_audio_processing(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_audio_data):
        """Test batch audio processing"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        batch_data = {
            "audio_files": [
                {
                    "id": "audio1",
                    "data": sample_audio_data,
                    "processing_options": {"noise_reduction": True}
                },
                {
                    "id": "audio2", 
                    "data": sample_audio_data,
                    "processing_options": {"normalize": True}
                }
            ]
        }
        
        response = client.post(
            "/api/v1/audio/batch-preprocess",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "batch_id" in data["data"]
        assert data["data"]["total_files"] == 2


class TestImagePreprocessingMobile:
    """Test Image Preprocessing Mobile functionality"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_image_ocr_preprocessing(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_data):
        """Test image preprocessing for OCR"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        preprocessing_data = {
            "image_data": sample_image_data,
            "preprocessing_options": {
                "grayscale": True,
                "denoise": True,
                "deskew": True,
                "contrast_enhancement": True,
                "binarization": {
                    "method": "otsu",
                    "threshold": None
                }
            },
            "target_use": "ocr"
        }
        
        response = client.post(
            "/api/v1/image/preprocess",
            json=preprocessing_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "processed_image" in data["data"]
        assert "preprocessing_steps" in data["data"]
        assert "grayscale" in data["data"]["preprocessing_steps"]
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_image_enhancement(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_data):
        """Test image enhancement features"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        enhancement_data = {
            "image_data": sample_image_data,
            "enhancements": {
                "brightness": 1.2,
                "contrast": 1.1,
                "saturation": 0.9,
                "sharpness": 1.5,
                "auto_enhance": True
            }
        }
        
        response = client.post(
            "/api/v1/image/enhance",
            json=enhancement_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "enhanced_image" in data["data"]
        assert "applied_enhancements" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_image_filters(self, mock_auth, auth_headers, mock_current_user, sample_image_data):
        """Test image filter application"""
        mock_auth.return_value = mock_current_user
        
        filter_data = {
            "image_data": sample_image_data,
            "filters": [
                {"type": "blur", "intensity": 5},
                {"type": "edge_detection", "method": "canny"},
                {"type": "morphology", "operation": "opening", "kernel_size": 3}
            ]
        }
        
        response = client.post(
            "/api/v1/image/apply-filters",
            json=filter_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "filtered_image" in data["data"]
        assert len(data["data"]["applied_filters"]) == 3
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_batch_image_processing(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_data):
        """Test batch image processing"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        batch_data = {
            "images": [
                {
                    "id": "img1",
                    "data": sample_image_data,
                    "operations": {"grayscale": True, "resize": {"width": 800, "height": 600}}
                },
                {
                    "id": "img2",
                    "data": sample_image_data,
                    "operations": {"rotate": 90, "flip": "horizontal"}
                }
            ],
            "output_format": "png"
        }
        
        response = client.post(
            "/api/v1/image/batch-process",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "batch_id" in data["data"]
        assert data["data"]["total_images"] == 2


class TestSupportTicketMobile:
    """Test Support Ticket Mobile functionality"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_create_support_ticket(self, mock_quota, mock_auth, auth_headers, mock_current_user):
        """Test creating a support ticket"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        ticket_data = {
            "subject": "Mobile app issue",
            "description": "App crashes when processing large images",
            "category": "technical",
            "priority": "high",
            "attachments": [
                {
                    "filename": "crash_log.txt",
                    "data": base64.b64encode(b"Crash log contents").decode()
                }
            ],
            "device_info": {
                "platform": "iOS",
                "version": "15.5",
                "app_version": "2.1.0",
                "device_model": "iPhone 13"
            }
        }
        
        response = client.post(
            "/api/v1/support/tickets",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "ticket_id" in data["data"]
        assert data["data"]["status"] == "open"
        assert data["data"]["priority"] == "high"
    
    @patch('api.auth_middleware.get_current_user')
    def test_get_user_tickets(self, mock_auth, auth_headers, mock_current_user):
        """Test getting user's support tickets"""
        mock_auth.return_value = mock_current_user
        
        response = client.get(
            "/api/v1/support/tickets?status=open&sort_by=created_at",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "tickets" in data["data"]
        assert "total" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_update_ticket(self, mock_auth, auth_headers, mock_current_user):
        """Test updating a support ticket"""
        mock_auth.return_value = mock_current_user
        
        update_data = {
            "message": "I found a workaround for the issue",
            "attachments": []
        }
        
        response = client.put(
            "/api/v1/support/tickets/ticket_123/update",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message_id" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_ticket_satisfaction_rating(self, mock_auth, auth_headers, mock_current_user):
        """Test submitting satisfaction rating"""
        mock_auth.return_value = mock_current_user
        
        rating_data = {
            "rating": 5,
            "feedback": "Very helpful support!",
            "resolution_quality": "excellent"
        }
        
        response = client.post(
            "/api/v1/support/tickets/ticket_123/rate",
            json=rating_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["rating_submitted"] == True


class TestLiveChatMobile:
    """Test Live Chat Mobile functionality"""
    
    @patch('api.auth_middleware.get_current_user')
    def test_initiate_chat_session(self, mock_auth, auth_headers, mock_current_user):
        """Test initiating a live chat session"""
        mock_auth.return_value = mock_current_user
        
        chat_data = {
            "topic": "Technical Support",
            "initial_message": "Need help with video processing",
            "preferred_language": "en"
        }
        
        response = client.post(
            "/api/v1/support/chat/start",
            json=chat_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data["data"]
        assert "agent_info" in data["data"]
        assert "estimated_wait_time" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_send_chat_message(self, mock_auth, auth_headers, mock_current_user):
        """Test sending a chat message"""
        mock_auth.return_value = mock_current_user
        
        message_data = {
            "message": "The app freezes when I try to export",
            "type": "text",
            "metadata": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = client.post(
            "/api/v1/support/chat/session_123/message",
            json=message_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message_id" in data["data"]
        assert "delivered" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_chat_file_upload(self, mock_auth, auth_headers, mock_current_user, sample_image_data):
        """Test uploading files in chat"""
        mock_auth.return_value = mock_current_user
        
        file_data = {
            "file_data": sample_image_data,
            "filename": "screenshot.png",
            "file_type": "image/png",
            "message": "Here's a screenshot of the error"
        }
        
        response = client.post(
            "/api/v1/support/chat/session_123/upload",
            json=file_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "file_id" in data["data"]
        assert "message_id" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_end_chat_session(self, mock_auth, auth_headers, mock_current_user):
        """Test ending a chat session"""
        mock_auth.return_value = mock_current_user
        
        end_data = {
            "reason": "issue_resolved",
            "transcript_requested": True
        }
        
        response = client.post(
            "/api/v1/support/chat/session_123/end",
            json=end_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "transcript_url" in data["data"]
        assert data["data"]["session_ended"] == True
    
    @patch('api.auth_middleware.get_current_user')
    def test_chat_typing_indicator(self, mock_auth, auth_headers, mock_current_user):
        """Test typing indicator functionality"""
        mock_auth.return_value = mock_current_user
        
        typing_data = {
            "is_typing": True
        }
        
        response = client.post(
            "/api/v1/support/chat/session_123/typing",
            json=typing_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["indicator_sent"] == True


# Mobile Platform Integration Tests
class TestMobileIntegration:
    """Integration tests for mobile-specific features"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_audio_to_support_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_audio_data):
        """Test workflow: preprocess audio -> encounter issue -> create support ticket"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Preprocess audio
        response = client.post(
            "/api/v1/audio/preprocess",
            json={
                "audio_data": sample_audio_data,
                "processing_options": {"noise_reduction": True}
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Step 2: Simulate issue and create support ticket
        ticket_response = client.post(
            "/api/v1/support/tickets",
            json={
                "subject": "Audio preprocessing failed",
                "description": "Noise reduction produced distorted output",
                "category": "technical",
                "context": {
                    "feature": "audio_preprocessing",
                    "session_id": response.json()["data"].get("session_id")
                }
            },
            headers=auth_headers
        )
        assert ticket_response.status_code == 200
        assert ticket_response.json()["data"]["ticket_id"] is not None
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_image_preprocessing_to_chat(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_data):
        """Test workflow: preprocess image -> need help -> start live chat"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Preprocess image
        response = client.post(
            "/api/v1/image/preprocess",
            json={
                "image_data": sample_image_data,
                "preprocessing_options": {"grayscale": True}
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Step 2: Start live chat for help
        chat_response = client.post(
            "/api/v1/support/chat/start",
            json={
                "topic": "Image Processing Help",
                "initial_message": "How do I improve OCR accuracy?",
                "context": {
                    "feature": "image_preprocessing",
                    "last_operation": "grayscale_conversion"
                }
            },
            headers=auth_headers
        )
        assert chat_response.status_code == 200
        assert chat_response.json()["data"]["session_id"] is not None


# Performance Tests for Mobile Features
class TestMobilePerformance:
    """Performance tests for mobile-specific endpoints"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_audio_processing_performance(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_audio_data):
        """Test audio processing performance for mobile constraints"""
        import time
        
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        start_time = time.time()
        
        response = client.post(
            "/api/v1/audio/preprocess",
            json={
                "audio_data": sample_audio_data,
                "processing_options": {
                    "noise_reduction": True,
                    "normalize": True
                }
            },
            headers=auth_headers
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time < 5.0  # Should process within 5 seconds for mobile
    
    @patch('api.auth_middleware.get_current_user')
    def test_chat_message_latency(self, mock_auth, auth_headers, mock_current_user):
        """Test live chat message latency"""
        import time
        
        mock_auth.return_value = mock_current_user
        
        message_times = []
        
        for i in range(10):
            start_time = time.time()
            
            response = client.post(
                "/api/v1/support/chat/session_123/message",
                json={
                    "message": f"Test message {i}",
                    "type": "text"
                },
                headers=auth_headers
            )
            
            end_time = time.time()
            message_times.append(end_time - start_time)
        
        avg_latency = sum(message_times) / len(message_times)
        
        assert all(response.status_code == 200 for response in [response])
        assert avg_latency < 0.5  # Average latency should be under 500ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])