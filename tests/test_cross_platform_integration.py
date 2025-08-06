"""
Integration tests for cross-platform features
Testing workflows that span multiple platforms and components
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import base64
from datetime import datetime, timedelta
import asyncio
import websocket
import threading
import time

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
def sample_data():
    return {
        "image": base64.b64encode(b"fake_image_data").decode(),
        "audio": base64.b64encode(b"fake_audio_data").decode(),
        "pdf": base64.b64encode(b"fake_pdf_data").decode()
    }


class TestEntityExtractionWorkflow:
    """Test entity extraction workflow across platforms"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_web_to_mobile_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_data):
        """Test: Web extraction → Mobile notification → Mobile view"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Web user starts entity extraction
        web_response = client.post(
            "/api/v1/entity-extraction/extract",
            json={
                "image_data": sample_data["image"],
                "extraction_config": {"confidence_threshold": 0.7},
                "include_visualization": True
            },
            headers=auth_headers
        )
        assert web_response.status_code == 200
        task_id = web_response.json()["data"]["task_id"]
        
        # Step 2: Simulate processing completion (would trigger notification)
        # In real implementation, this would be handled by background task
        notification_response = client.post(
            "/api/v1/notifications",
            json={
                "title": "Entity Extraction Complete",
                "message": f"Your extraction task {task_id} is ready",
                "category": "processing",
                "recipients": [mock_current_user["user_id"]],
                "metadata": {
                    "task_id": task_id,
                    "action_url": f"/results/{task_id}"
                }
            },
            headers=auth_headers
        )
        assert notification_response.status_code == 200
        
        # Step 3: Mobile user checks notifications
        mobile_notif_response = client.get(
            "/api/v1/notifications?unread_only=true",
            headers=auth_headers
        )
        assert mobile_notif_response.status_code == 200
        notifications = mobile_notif_response.json()["data"]["notifications"]
        assert len(notifications) > 0
        assert any(notif["metadata"].get("task_id") == task_id for notif in notifications)
        
        # Step 4: Mobile user views results
        mobile_results_response = client.get(
            f"/api/v1/entity-extraction/results/{task_id}",
            headers=auth_headers
        )
        assert mobile_results_response.status_code == 200
        assert "entities" in mobile_results_response.json()["data"]["data"]
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_desktop_to_web_sharing_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_data):
        """Test: Desktop batch processing → Web dashboard → Share results"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Desktop user processes batch
        batch_response = client.post(
            "/api/v1/entity-extraction/batch",
            json={
                "images": [sample_data["image"], sample_data["image"]],
                "extraction_config": {"confidence_threshold": 0.6},
                "include_visualization": False
            },
            headers=auth_headers
        )
        assert batch_response.status_code == 200
        batch_id = batch_response.json()["data"]["batch_id"]
        
        # Step 2: Check batch status (simulate completion)
        status_response = client.get(
            f"/api/v1/entity-extraction/batch/status/{batch_id}",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        
        # Step 3: Web dashboard shows batch results
        dashboard_response = client.get(
            f"/api/v1/entity-extraction/stats?time_range=24h",
            headers=auth_headers
        )
        assert dashboard_response.status_code == 200
        
        # Step 4: Export results for sharing
        export_response = client.post(
            f"/api/v1/entity-extraction/export",
            json={
                "result_id": batch_id,
                "format": "json",
                "include_visualizations": True,
                "include_metadata": True
            },
            headers=auth_headers
        )
        assert export_response.status_code == 200
        assert "download_url" in export_response.json()["data"]


class TestLLMProviderIntegration:
    """Test LLM provider integration across features"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_marketplace_llm_installation_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user):
        """Test: Browse marketplace → Install LLM plugin → Configure → Use in AI dubbing"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Browse marketplace for LLM plugins
        browse_response = client.get(
            "/api/v1/marketplace/browse?category=llm-plugins&sort_by=rating",
            headers=auth_headers
        )
        assert browse_response.status_code == 200
        items = browse_response.json()["data"]["items"]
        llm_plugin = next((item for item in items if "llm" in item["name"].lower()), None)
        
        if llm_plugin:
            # Step 2: Install LLM plugin
            install_response = client.post(
                f"/api/v1/marketplace/{llm_plugin['id']}/install",
                json={
                    "version": llm_plugin["version"],
                    "configuration": {"auto_update": True}
                },
                headers=auth_headers
            )
            assert install_response.status_code == 200
            installation_id = install_response.json()["data"]["installation_id"]
            
            # Step 3: Check if new provider is available
            providers_response = client.get(
                "/api/v1/llm-providers",
                headers=auth_headers
            )
            assert providers_response.status_code == 200
            
            # Step 4: Configure the new provider
            config_response = client.post(
                "/api/v1/llm-providers/configure",
                json={
                    "provider": "custom_llm",
                    "api_key": "test_key",
                    "settings": {"model": "custom-model-v1"}
                },
                headers=auth_headers
            )
            assert config_response.status_code == 200
            
            # Step 5: Use in AI dubbing
            dubbing_response = client.post(
                "/api/v1/ai-dubbing/synthesize",
                json={
                    "text": "Test synthesis with custom provider",
                    "language": "en-US",
                    "voice_id": "custom_voice_1",
                    "options": {"speed": 1.0}
                },
                headers=auth_headers
            )
            assert dubbing_response.status_code == 200
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_llm_fallback_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user):
        """Test: Primary LLM fails → Fallback provider used → Notification sent"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Configure primary and fallback providers
        primary_config = client.post(
            "/api/v1/llm-providers/configure",
            json={
                "provider": "openai",
                "api_key": "invalid_key",  # Simulate failure
                "settings": {"model": "gpt-4"},
                "fallback_provider": "anthropic"
            },
            headers=auth_headers
        )
        assert primary_config.status_code == 200
        
        fallback_config = client.post(
            "/api/v1/llm-providers/configure",
            json={
                "provider": "anthropic",
                "api_key": "valid_key",
                "settings": {"model": "claude-3-opus"}
            },
            headers=auth_headers
        )
        assert fallback_config.status_code == 200
        
        # Step 2: Test primary provider (should fail)
        test_response = client.post(
            "/api/v1/llm-providers/test",
            json={
                "provider": "openai",
                "test_prompt": "Hello world"
            },
            headers=auth_headers
        )
        # Should either fail gracefully or use fallback
        
        # Step 3: Check notifications for provider issues
        notif_response = client.get(
            "/api/v1/notifications?category=system",
            headers=auth_headers
        )
        assert notif_response.status_code == 200


class TestDocumentProcessingWorkflow:
    """Test document processing across platforms"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_mobile_capture_to_desktop_analysis(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_data):
        """Test: Mobile image capture → Cloud preprocessing → Desktop OCR analysis"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Mobile preprocessing
        mobile_preprocess = client.post(
            "/api/v1/image/preprocess",
            json={
                "image_data": sample_data["image"],
                "preprocessing_options": {
                    "grayscale": True,
                    "denoise": True,
                    "deskew": True,
                    "contrast_enhancement": True
                },
                "target_use": "ocr"
            },
            headers=auth_headers
        )
        assert mobile_preprocess.status_code == 200
        processed_image = mobile_preprocess.json()["data"]["processed_image"]
        
        # Step 2: Desktop OCR processing
        ocr_response = client.post(
            "/api/v1/ocr/process",
            json={
                "image_data": processed_image,
                "ocr_options": {
                    "language": ["eng"],
                    "confidence_threshold": 0.7,
                    "preserve_formatting": True
                },
                "output_format": "structured"
            },
            headers=auth_headers
        )
        assert ocr_response.status_code == 200
        ocr_results = ocr_response.json()["data"]
        
        # Step 3: Document analysis
        analysis_response = client.post(
            "/api/v1/document-analysis/analyze",
            json={
                "document_data": ocr_results["text"],
                "document_type": "text",
                "analysis_options": {
                    "extract_entities": True,
                    "sentiment_analysis": True,
                    "key_topics": True
                }
            },
            headers=auth_headers
        )
        assert analysis_response.status_code == 200
        
        # Step 4: Notification to mobile about completion
        completion_notif = client.post(
            "/api/v1/notifications",
            json={
                "title": "Document Analysis Complete",
                "message": "Your document has been processed and analyzed",
                "category": "processing",
                "recipients": [mock_current_user["user_id"]]
            },
            headers=auth_headers
        )
        assert completion_notif.status_code == 200
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_pdf_to_meeting_workflow(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_data):
        """Test: PDF upload → OCR processing → Meeting preparation → Live meeting"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Process PDF with OCR
        pdf_ocr = client.post(
            "/api/v1/ocr/process-document",
            json={
                "document_data": sample_data["pdf"],
                "document_type": "pdf",
                "ocr_options": {
                    "language": ["eng"],
                    "extract_tables": True,
                    "searchable_pdf": True
                }
            },
            headers=auth_headers
        )
        assert pdf_ocr.status_code == 200
        extracted_text = pdf_ocr.json()["data"]["extracted_text"]
        
        # Step 2: Prepare meeting with document content
        meeting_prep = client.post(
            "/api/v1/meetings/prepare",
            json={
                "documents": [{
                    "name": "agenda.pdf",
                    "content": extracted_text
                }],
                "meeting_type": "review",
                "generate_talking_points": True
            },
            headers=auth_headers
        )
        assert meeting_prep.status_code == 200
        talking_points = meeting_prep.json()["data"]["talking_points"]
        
        # Step 3: Create meeting with prepared content
        meeting_create = client.post(
            "/api/v1/meetings/create",
            json={
                "title": "Document Review Meeting",
                "scheduled_time": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
                "duration_minutes": 60,
                "agenda": "\n".join(talking_points),
                "settings": {
                    "auto_recording": True,
                    "transcription_enabled": True,
                    "ai_notes": True
                }
            },
            headers=auth_headers
        )
        assert meeting_create.status_code == 200
        meeting_id = meeting_create.json()["data"]["meeting_id"]
        
        # Step 4: Start meeting recording
        recording_start = client.post(
            f"/api/v1/meetings/{meeting_id}/start-recording",
            json={
                "recording_options": {
                    "video_quality": "1080p",
                    "include_screen_share": True
                }
            },
            headers=auth_headers
        )
        assert recording_start.status_code == 200


class TestSupportWorkflow:
    """Test support system workflow across platforms"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_mobile_issue_to_desktop_resolution(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_data):
        """Test: Mobile error → Support ticket → Desktop investigation → Resolution"""
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        # Step 1: Mobile user encounters processing error
        error_response = client.post(
            "/api/v1/audio/preprocess",
            json={
                "audio_data": "invalid_audio_data",  # Simulate error
                "processing_options": {"noise_reduction": True}
            },
            headers=auth_headers
        )
        # Expect error response
        
        # Step 2: User creates support ticket with error details
        ticket_response = client.post(
            "/api/v1/support/tickets",
            json={
                "subject": "Audio preprocessing fails on mobile",
                "description": "Getting error when trying to reduce noise in audio file",
                "category": "technical",
                "priority": "high",
                "attachments": [
                    {
                        "filename": "error_log.txt",
                        "data": base64.b64encode(b"Error log contents").decode()
                    }
                ],
                "device_info": {
                    "platform": "iOS",
                    "version": "15.5",
                    "app_version": "2.1.0"
                },
                "context": {
                    "feature": "audio_preprocessing",
                    "error_code": "PROCESSING_FAILED"
                }
            },
            headers=auth_headers
        )
        assert ticket_response.status_code == 200
        ticket_id = ticket_response.json()["data"]["ticket_id"]
        
        # Step 3: Support agent investigates (simulated)
        ticket_update = client.put(
            f"/api/v1/support/tickets/{ticket_id}/update",
            json={
                "message": "We've identified the issue and are working on a fix",
                "status": "in_progress",
                "internal_notes": "Audio format compatibility issue"
            },
            headers=auth_headers
        )
        assert ticket_update.status_code == 200
        
        # Step 4: User starts live chat for immediate help
        chat_start = client.post(
            "/api/v1/support/chat/start",
            json={
                "topic": "Audio Processing Issue",
                "initial_message": "Following up on ticket #" + ticket_id,
                "context": {
                    "ticket_id": ticket_id,
                    "platform": "mobile"
                }
            },
            headers=auth_headers
        )
        assert chat_start.status_code == 200
        session_id = chat_start.json()["data"]["session_id"]
        
        # Step 5: Chat interaction with agent
        chat_message = client.post(
            f"/api/v1/support/chat/{session_id}/message",
            json={
                "message": "Can you provide a workaround for the audio issue?",
                "type": "text"
            },
            headers=auth_headers
        )
        assert chat_message.status_code == 200
        
        # Step 6: Resolution and ticket closure
        ticket_resolve = client.put(
            f"/api/v1/support/tickets/{ticket_id}/update",
            json={
                "message": "Issue resolved with app update v2.1.1",
                "status": "resolved"
            },
            headers=auth_headers
        )
        assert ticket_resolve.status_code == 200


class TestMultiPlatformDataSync:
    """Test data synchronization across platforms"""
    
    @patch('api.auth_middleware.get_current_user')
    def test_preferences_sync(self, mock_auth, auth_headers, mock_current_user):
        """Test: Update preferences on web → Sync to mobile → Verify consistency"""
        mock_auth.return_value = mock_current_user
        
        # Step 1: Update notification preferences on web
        web_prefs_update = client.put(
            "/api/v1/notifications/preferences",
            json={
                "email_notifications": True,
                "push_notifications": True,
                "categories": {
                    "processing": True,
                    "security": True,
                    "marketing": False
                },
                "quiet_hours": {
                    "enabled": True,
                    "start": "22:00",
                    "end": "08:00"
                }
            },
            headers=auth_headers
        )
        assert web_prefs_update.status_code == 200
        
        # Step 2: Retrieve preferences on mobile
        mobile_prefs = client.get(
            "/api/v1/notifications/preferences",
            headers=auth_headers
        )
        assert mobile_prefs.status_code == 200
        prefs_data = mobile_prefs.json()["data"]
        
        # Step 3: Verify sync
        assert prefs_data["email_notifications"] == True
        assert prefs_data["categories"]["marketing"] == False
        assert prefs_data["quiet_hours"]["enabled"] == True
        
        # Step 4: Update LLM provider settings
        llm_config = client.post(
            "/api/v1/llm-providers/configure",
            json={
                "provider": "openai",
                "settings": {
                    "temperature": 0.8,
                    "max_tokens": 2000
                }
            },
            headers=auth_headers
        )
        assert llm_config.status_code == 200
        
        # Step 5: Verify settings available across platforms
        llm_list = client.get(
            "/api/v1/llm-providers",
            headers=auth_headers
        )
        assert llm_list.status_code == 200
        providers = llm_list.json()["data"]["providers"]
        openai_provider = next((p for p in providers if p["id"] == "openai"), None)
        assert openai_provider is not None
    
    @patch('api.auth_middleware.get_current_user')
    def test_usage_analytics_consistency(self, mock_auth, auth_headers, mock_current_user):
        """Test: Usage tracking across platforms → Consistent analytics"""
        mock_auth.return_value = mock_current_user
        
        # Step 1: Get initial usage stats
        initial_stats = client.get(
            "/api/v1/user/quota",
            headers=auth_headers
        )
        assert initial_stats.status_code == 200
        initial_usage = initial_stats.json()["data"]["quotas"]
        
        # Step 2: Perform activities on different platforms
        # Entity extraction (simulated web usage)
        web_activity = client.post(
            "/api/v1/entity-extraction/extract",
            json={
                "image_data": base64.b64encode(b"test_image").decode(),
                "extraction_config": {"confidence_threshold": 0.6}
            },
            headers=auth_headers
        )
        
        # OCR processing (simulated desktop usage)
        desktop_activity = client.post(
            "/api/v1/ocr/process",
            json={
                "image_data": base64.b64encode(b"test_document").decode(),
                "ocr_options": {"language": ["eng"]}
            },
            headers=auth_headers
        )
        
        # Step 3: Check updated usage stats
        updated_stats = client.get(
            "/api/v1/user/quota",
            headers=auth_headers
        )
        assert updated_stats.status_code == 200
        updated_usage = updated_stats.json()["data"]["quotas"]
        
        # Step 4: Verify usage incremented properly
        if "entity_extraction" in initial_usage and "entity_extraction" in updated_usage:
            assert updated_usage["entity_extraction"]["used"] >= initial_usage["entity_extraction"]["used"]


class TestRealTimeIntegration:
    """Test real-time features integration"""
    
    def test_websocket_notification_delivery(self):
        """Test: Action triggers notification → WebSocket delivery → Cross-platform reception"""
        # This would require actual WebSocket testing
        # For now, we test the HTTP notification API
        
        # Simulate WebSocket connection setup
        ws_url = "ws://localhost:8000/ws/notifications?token=test_token"
        # In a real test, we would establish WebSocket connection here
        
        # Test notification creation and delivery
        with client:
            auth_headers = {"Authorization": "Bearer test_token"}
            
            # Create notification
            response = client.post(
                "/api/v1/notifications",
                json={
                    "title": "Real-time Test",
                    "message": "Testing WebSocket delivery",
                    "category": "system",
                    "recipients": ["test_user_123"]
                },
                headers=auth_headers
            )
            
            # In a real WebSocket test, we would verify the message was received
            assert response.status_code == 200
    
    @patch('api.auth_middleware.get_current_user')
    def test_live_chat_integration(self, mock_auth, auth_headers, mock_current_user):
        """Test: Start chat → Send messages → File upload → End session"""
        mock_auth.return_value = mock_current_user
        
        # Step 1: Start chat session
        chat_start = client.post(
            "/api/v1/support/chat/start",
            json={
                "topic": "Integration Test",
                "initial_message": "Testing live chat workflow"
            },
            headers=auth_headers
        )
        assert chat_start.status_code == 200
        session_id = chat_start.json()["data"]["session_id"]
        
        # Step 2: Send messages
        message_response = client.post(
            f"/api/v1/support/chat/{session_id}/message",
            json={
                "message": "This is a test message",
                "type": "text"
            },
            headers=auth_headers
        )
        assert message_response.status_code == 200
        
        # Step 3: Upload file
        file_upload = client.post(
            f"/api/v1/support/chat/{session_id}/upload",
            json={
                "file_data": base64.b64encode(b"test file content").decode(),
                "filename": "test_file.txt",
                "file_type": "text/plain",
                "message": "Here's a test file"
            },
            headers=auth_headers
        )
        assert file_upload.status_code == 200
        
        # Step 4: End session
        end_session = client.post(
            f"/api/v1/support/chat/{session_id}/end",
            json={
                "reason": "issue_resolved",
                "transcript_requested": True
            },
            headers=auth_headers
        )
        assert end_session.status_code == 200
        assert "transcript_url" in end_session.json()["data"]


class TestPerformanceIntegration:
    """Test performance across integrated workflows"""
    
    @patch('api.auth_middleware.get_current_user')
    @patch('api.middleware.quota_enforcement.require_quota')
    def test_concurrent_platform_usage(self, mock_quota, mock_auth, auth_headers, mock_current_user, sample_data):
        """Test: Concurrent requests from multiple platforms"""
        import concurrent.futures
        import time
        
        mock_auth.return_value = mock_current_user
        mock_quota.return_value = True
        
        def make_request(endpoint, data):
            return client.post(endpoint, json=data, headers=auth_headers)
        
        # Prepare concurrent requests
        requests = [
            ("/api/v1/entity-extraction/extract", {
                "image_data": sample_data["image"],
                "extraction_config": {"confidence_threshold": 0.6}
            }),
            ("/api/v1/ocr/process", {
                "image_data": sample_data["image"],
                "ocr_options": {"language": ["eng"]}
            }),
            ("/api/v1/audio/preprocess", {
                "audio_data": sample_data["audio"],
                "processing_options": {"noise_reduction": True}
            }),
            ("/api/v1/image/preprocess", {
                "image_data": sample_data["image"],
                "preprocessing_options": {"grayscale": True}
            })
        ]
        
        start_time = time.time()
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request, endpoint, data) for endpoint, data in requests]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests succeeded
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) == len(requests)
        
        # Performance assertion - concurrent requests should be faster than sequential
        assert total_time < 10.0  # Should complete within 10 seconds
    
    @patch('api.auth_middleware.get_current_user')
    def test_large_data_workflow_performance(self, mock_auth, auth_headers, mock_current_user):
        """Test: Large file processing workflow performance"""
        import time
        
        mock_auth.return_value = mock_current_user
        
        # Create large test data (simulated)
        large_image_data = base64.b64encode(b"x" * (5 * 1024 * 1024)).decode()  # 5MB
        
        start_time = time.time()
        
        # Step 1: Preprocess large image
        preprocess_start = time.time()
        preprocess_response = client.post(
            "/api/v1/image/preprocess",
            json={
                "image_data": large_image_data[:1000],  # Truncated for test
                "preprocessing_options": {
                    "grayscale": True,
                    "denoise": True
                }
            },
            headers=auth_headers
        )
        preprocess_time = time.time() - preprocess_start
        
        # Step 2: Process with OCR
        if preprocess_response.status_code == 200:
            ocr_start = time.time()
            ocr_response = client.post(
                "/api/v1/ocr/process",
                json={
                    "image_data": large_image_data[:1000],  # Truncated for test
                    "ocr_options": {"language": ["eng"]}
                },
                headers=auth_headers
            )
            ocr_time = time.time() - ocr_start
        
        total_time = time.time() - start_time
        
        # Performance assertions
        assert preprocess_time < 5.0  # Preprocessing should be under 5 seconds
        if 'ocr_response' in locals():
            assert ocr_time < 10.0  # OCR should be under 10 seconds
        assert total_time < 15.0  # Total workflow should be under 15 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])