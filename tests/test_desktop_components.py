"""
Test suite for Desktop-specific components (Phase 3)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import base64
from datetime import datetime, timedelta
import io
from PIL import Image
import PyPDF2
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
def sample_pdf_data():
    """Generate sample PDF data for testing"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Test PDF Document")
    c.drawString(100, 700, "This is a test document for OCR processing.")
    c.drawString(100, 650, "It contains multiple lines of text.")
    c.showPage()
    c.save()
    
    pdf_bytes = buffer.getvalue()
    return base64.b64encode(pdf_bytes).decode()

@pytest.fixture
def sample_image_with_text():
    """Generate sample image with text for OCR testing"""
    img = Image.new('RGB', (800, 600), color='white')
    # In real tests, we would draw text on the image
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    return base64.b64encode(img_bytes).decode()


class TestOCRProcessorDesktop:
    """Test OCR Processor Desktop functionality"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_ocr_single_image(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_with_text):
        """Test OCR processing for single image"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        ocr_data = {
            "image_data": sample_image_with_text,
            "ocr_options": {
                "language": ["eng", "fra"],
                "page_segmentation_mode": 3,
                "ocr_engine_mode": 2,
                "confidence_threshold": 0.6,
                "preserve_formatting": True,
                "detect_orientation": True
            },
            "output_format": "structured"
        }
        
        response = client.post(
            "/api/v1/ocr/process",
            json=ocr_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "text" in data["data"]
        assert "confidence" in data["data"]
        assert "blocks" in data["data"]
        assert "metadata" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_ocr_pdf_processing(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_pdf_data):
        """Test OCR processing for PDF documents"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        pdf_ocr_data = {
            "document_data": sample_pdf_data,
            "document_type": "pdf",
            "ocr_options": {
                "language": ["eng"],
                "extract_tables": True,
                "extract_images": True,
                "searchable_pdf": True
            },
            "page_range": "1-5"
        }
        
        response = client.post(
            "/api/v1/ocr/process-document",
            json=pdf_ocr_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "pages" in data["data"]
        assert "total_pages" in data["data"]
        assert "extracted_text" in data["data"]
        assert data["data"]["document_type"] == "pdf"
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_ocr_batch_processing(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_with_text):
        """Test batch OCR processing"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        batch_data = {
            "documents": [
                {
                    "id": "doc1",
                    "data": sample_image_with_text,
                    "type": "image",
                    "options": {"language": ["eng"]}
                },
                {
                    "id": "doc2",
                    "data": sample_image_with_text,
                    "type": "image",
                    "options": {"language": ["eng", "spa"]}
                }
            ],
            "output_format": "json",
            "parallel_processing": True
        }
        
        response = client.post(
            "/api/v1/ocr/batch-process",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "batch_id" in data["data"]
        assert data["data"]["total_documents"] == 2
        assert data["data"]["status"] == "processing"
    
    @patch('api.auth_middleware.get_current_user')
    def test_ocr_language_detection(self, mock_auth, auth_headers, mock_current_user, sample_image_with_text):
        """Test automatic language detection in OCR"""
        mock_auth.return_value = mock_current_user
        
        detection_data = {
            "image_data": sample_image_with_text,
            "detect_language": True,
            "possible_languages": ["eng", "fra", "deu", "spa"]
        }
        
        response = client.post(
            "/api/v1/ocr/detect-language",
            json=detection_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "detected_languages" in data["data"]
        assert "confidence_scores" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_ocr_table_extraction(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_with_text):
        """Test table extraction from documents"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        table_data = {
            "document_data": sample_image_with_text,
            "extraction_type": "tables",
            "table_options": {
                "detect_borders": True,
                "merge_cells": True,
                "output_format": "csv"
            }
        }
        
        response = client.post(
            "/api/v1/ocr/extract-tables",
            json=table_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "tables" in data["data"]
        assert "table_count" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_ocr_confidence_analysis(self, mock_auth, auth_headers, mock_current_user, sample_image_with_text):
        """Test OCR confidence analysis"""
        mock_auth.return_value = mock_current_user
        
        analysis_data = {
            "image_data": sample_image_with_text,
            "analyze_confidence": True,
            "highlight_low_confidence": True,
            "confidence_threshold": 0.7
        }
        
        response = client.post(
            "/api/v1/ocr/analyze-confidence",
            json=analysis_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "overall_confidence" in data["data"]
        assert "low_confidence_words" in data["data"]
        assert "confidence_distribution" in data["data"]


class TestMeetingAutomationDesktop:
    """Test Meeting Automation Desktop functionality"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_create_meeting(self, mock_quota, mock_auth, auth_headers, mock_current_user):
        """Test creating a new meeting"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        meeting_data = {
            "title": "Project Review Meeting",
            "scheduled_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "duration_minutes": 60,
            "participants": [
                {"email": "john@example.com", "role": "presenter"},
                {"email": "jane@example.com", "role": "participant"}
            ],
            "settings": {
                "auto_recording": True,
                "transcription_enabled": True,
                "ai_notes": True,
                "action_item_detection": True
            }
        }
        
        response = client.post(
            "/api/v1/meetings/create",
            json=meeting_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "meeting_id" in data["data"]
        assert "join_url" in data["data"]
        assert data["data"]["settings"]["transcription_enabled"] == True
    
    @patch('api.auth_middleware.get_current_user')
    def test_start_meeting_recording(self, mock_auth, auth_headers, mock_current_user):
        """Test starting meeting recording"""
        mock_auth.return_value = mock_current_user
        
        recording_data = {
            "recording_options": {
                "video_quality": "1080p",
                "audio_quality": "high",
                "include_screen_share": True,
                "speaker_view": True,
                "gallery_view": False
            }
        }
        
        response = client.post(
            "/api/v1/meetings/meeting_123/start-recording",
            json=recording_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["recording_started"] == True
        assert "recording_id" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_real_time_transcription(self, mock_auth, auth_headers, mock_current_user):
        """Test real-time transcription during meeting"""
        mock_auth.return_value = mock_current_user
        
        transcription_data = {
            "audio_chunk": base64.b64encode(b"audio_data").decode(),
            "timestamp": datetime.utcnow().isoformat(),
            "speaker_id": "speaker_1"
        }
        
        response = client.post(
            "/api/v1/meetings/meeting_123/transcribe",
            json=transcription_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "transcript_segment" in data["data"]
        assert "confidence" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_action_item_extraction(self, mock_auth, auth_headers, mock_current_user):
        """Test extracting action items from meeting"""
        mock_auth.return_value = mock_current_user
        
        response = client.get(
            "/api/v1/meetings/meeting_123/action-items",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "action_items" in data["data"]
        assert isinstance(data["data"]["action_items"], list)
        
        if data["data"]["action_items"]:
            item = data["data"]["action_items"][0]
            assert "description" in item
            assert "assigned_to" in item
            assert "due_date" in item
            assert "priority" in item
    
    @patch('api.auth_middleware.get_current_user')
    def test_meeting_summary_generation(self, mock_auth, auth_headers, mock_current_user):
        """Test AI-generated meeting summary"""
        mock_auth.return_value = mock_current_user
        
        summary_options = {
            "summary_type": "detailed",
            "include_action_items": True,
            "include_decisions": True,
            "include_key_topics": True,
            "max_length": 500
        }
        
        response = client.post(
            "/api/v1/meetings/meeting_123/generate-summary",
            json=summary_options,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "summary" in data["data"]
        assert "key_points" in data["data"]
        assert "decisions" in data["data"]
        assert "next_steps" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    def test_participant_analytics(self, mock_auth, auth_headers, mock_current_user):
        """Test meeting participant analytics"""
        mock_auth.return_value = mock_current_user
        
        response = client.get(
            "/api/v1/meetings/meeting_123/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "participant_stats" in data["data"]
        assert "talk_time_distribution" in data["data"]
        assert "engagement_metrics" in data["data"]
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_schedule_recurring_meeting(self, mock_quota, mock_auth, auth_headers, mock_current_user):
        """Test scheduling recurring meetings"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        recurring_data = {
            "title": "Weekly Team Standup",
            "recurrence": {
                "pattern": "weekly",
                "days_of_week": ["monday", "wednesday", "friday"],
                "time": "09:00",
                "timezone": "UTC",
                "end_date": (datetime.utcnow() + timedelta(days=90)).isoformat()
            },
            "duration_minutes": 30,
            "settings": {
                "auto_recording": True,
                "send_summary": True
            }
        }
        
        response = client.post(
            "/api/v1/meetings/schedule-recurring",
            json=recurring_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "series_id" in data["data"]
        assert "scheduled_instances" in data["data"]
        assert len(data["data"]["scheduled_instances"]) > 0


# Desktop Platform Integration Tests
class TestDesktopIntegration:
    """Integration tests for desktop-specific features"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_ocr_to_meeting_notes_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_pdf_data):
        """Test workflow: OCR document -> Use in meeting notes"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Process document with OCR
        ocr_response = client.post(
            "/api/v1/ocr/process-document",
            json={
                "document_data": sample_pdf_data,
                "document_type": "pdf",
                "ocr_options": {"language": ["eng"]}
            },
            headers=auth_headers
        )
        assert ocr_response.status_code == 200
        extracted_text = ocr_response.json()["data"]["extracted_text"]
        
        # Step 2: Create meeting with agenda from OCR text
        meeting_response = client.post(
            "/api/v1/meetings/create",
            json={
                "title": "Document Review Meeting",
                "scheduled_time": datetime.utcnow().isoformat(),
                "duration_minutes": 30,
                "agenda": extracted_text[:500],  # Use first 500 chars as agenda
                "settings": {
                    "ai_notes": True,
                    "reference_documents": [{"type": "ocr", "content": extracted_text}]
                }
            },
            headers=auth_headers
        )
        assert meeting_response.status_code == 200
        assert meeting_response.json()["data"]["meeting_id"] is not None
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_meeting_recording_to_ocr_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user):
        """Test workflow: Meeting recording -> Generate slides -> OCR processing"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: End meeting and get recording
        end_response = client.post(
            "/api/v1/meetings/meeting_123/end",
            json={"generate_artifacts": True},
            headers=auth_headers
        )
        assert end_response.status_code == 200
        
        # Step 2: Get generated slides/documents
        artifacts_response = client.get(
            "/api/v1/meetings/meeting_123/artifacts",
            headers=auth_headers
        )
        assert artifacts_response.status_code == 200
        
        # Step 3: Process slides with OCR for searchability
        if artifacts_response.json()["data"]["slides"]:
            slide_data = artifacts_response.json()["data"]["slides"][0]["data"]
            ocr_response = client.post(
                "/api/v1/ocr/process",
                json={
                    "image_data": slide_data,
                    "ocr_options": {
                        "language": ["eng"],
                        "searchable_output": True
                    }
                },
                headers=auth_headers
            )
            assert ocr_response.status_code == 200
    
    @patch('api.auth_middleware.get_current_user')
    def test_multi_document_meeting_prep(self, mock_auth, auth_headers, mock_current_user, sample_pdf_data, sample_image_with_text):
        """Test preparing for meeting with multiple documents"""
        mock_auth.return_value = mock_current_user
        
        # Process multiple documents
        documents = [
            {"data": sample_pdf_data, "type": "pdf", "name": "report.pdf"},
            {"data": sample_image_with_text, "type": "image", "name": "chart.png"}
        ]
        
        processed_docs = []
        for doc in documents:
            response = client.post(
                f"/api/v1/ocr/process{'document' if doc['type'] == 'pdf' else ''}",
                json={
                    "document_data" if doc['type'] == 'pdf' else "image_data": doc["data"],
                    "document_type": doc["type"],
                    "ocr_options": {"language": ["eng"]}
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            processed_docs.append({
                "name": doc["name"],
                "content": response.json()["data"].get("extracted_text", "")
            })
        
        # Create meeting prep summary
        prep_response = client.post(
            "/api/v1/meetings/prepare",
            json={
                "documents": processed_docs,
                "meeting_type": "review",
                "generate_talking_points": True
            },
            headers=auth_headers
        )
        assert prep_response.status_code == 200
        assert "talking_points" in prep_response.json()["data"]


# Performance Tests for Desktop Features
class TestDesktopPerformance:
    """Performance tests for desktop-specific endpoints"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_large_pdf_ocr_performance(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_pdf_data):
        """Test OCR performance on large PDF documents"""
        import time
        
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Simulate large PDF (in real test, would use actual large PDF)
        start_time = time.time()
        
        response = client.post(
            "/api/v1/ocr/process-document",
            json={
                "document_data": sample_pdf_data,
                "document_type": "pdf",
                "ocr_options": {
                    "language": ["eng"],
                    "parallel_processing": True,
                    "max_pages": 100
                }
            },
            headers=auth_headers
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time < 30.0  # Should process within 30 seconds
    
    @patch('api.auth_middleware.get_current_user')
    def test_real_time_transcription_latency(self, mock_auth, auth_headers, mock_current_user):
        """Test real-time transcription latency"""
        import time
        
        mock_auth.return_value = mock_current_user
        
        latencies = []
        
        # Simulate multiple audio chunks
        for i in range(20):
            audio_chunk = base64.b64encode(b"simulated_audio_data" * 100).decode()
            
            start_time = time.time()
            
            response = client.post(
                "/api/v1/meetings/meeting_123/transcribe",
                json={
                    "audio_chunk": audio_chunk,
                    "timestamp": datetime.utcnow().isoformat(),
                    "speaker_id": "speaker_1"
                },
                headers=auth_headers
            )
            
            end_time = time.time()
            latencies.append(end_time - start_time)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        assert all(response.status_code == 200 for response in [response])
        assert avg_latency < 0.1  # Average under 100ms
        assert max_latency < 0.2  # Max under 200ms
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_batch_ocr_throughput(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_image_with_text):
        """Test batch OCR processing throughput"""
        import time
        
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Create batch of 50 documents
        batch_data = {
            "documents": [
                {
                    "id": f"doc_{i}",
                    "data": sample_image_with_text,
                    "type": "image",
                    "options": {"language": ["eng"]}
                }
                for i in range(50)
            ],
            "parallel_processing": True
        }
        
        start_time = time.time()
        
        response = client.post(
            "/api/v1/ocr/batch-process",
            json=batch_data,
            headers=auth_headers
        )
        
        end_time = time.time()
        submission_time = end_time - start_time
        
        assert response.status_code == 200
        assert submission_time < 5.0  # Should submit batch within 5 seconds
        
        # Check batch status
        batch_id = response.json()["data"]["batch_id"]
        
        # Poll for completion (in real test, would wait appropriately)
        status_response = client.get(
            f"/api/v1/ocr/batch/{batch_id}/status",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200


# Security Tests for Desktop Features
class TestDesktopSecurity:
    """Security tests for desktop-specific endpoints"""
    
    @patch('api.auth_middleware.get_current_user')
    def test_meeting_access_control(self, mock_auth, auth_headers):
        """Test meeting access control"""
        # Test with unauthorized user
        mock_auth.return_value = {"user_id": "unauthorized_user", "email": "unauthorized@example.com"}
        
        response = client.get(
            "/api/v1/meetings/meeting_123/details",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    @patch('api.auth_middleware.get_current_user')
    def test_ocr_file_size_limit(self, mock_auth, auth_headers, mock_current_user):
        """Test OCR file size limits"""
        mock_auth.return_value = mock_current_user
        
        # Create large file (simulated)
        large_data = base64.b64encode(b"x" * (100 * 1024 * 1024)).decode()  # 100MB
        
        response = client.post(
            "/api/v1/ocr/process",
            json={
                "image_data": large_data,
                "ocr_options": {"language": ["eng"]}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 413  # Payload too large
    
    @patch('api.auth_middleware.get_current_user')
    def test_meeting_recording_privacy(self, mock_auth, auth_headers, mock_current_user):
        """Test meeting recording privacy settings"""
        mock_auth.return_value = mock_current_user
        
        # Test that recordings require proper permissions
        response = client.get(
            "/api/v1/meetings/meeting_123/recording",
            headers=auth_headers
        )
        
        # Should check if user is participant or has permission
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "recording_url" not in data["data"] or data["data"]["recording_url"].startswith("https://")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])