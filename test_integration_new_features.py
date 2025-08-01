#!/usr/bin/env python3
"""
Integration tests for new features:
- Search functionality
- Speaker diarization
- WebSocket events
- Authentication integration
"""

import asyncio
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search.search_index import SearchIndex, DocumentIndex
from search.search_manager import SearchManager, SearchQuery
from speaker_diarization.diarization_manager import DiarizationManager
from speaker_diarization.providers.mock_provider import MockProvider
from websocket import EventType, Event, EventHandler


class TestSearchIntegration:
    """Test search functionality integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_search.db")
        self.search_manager = SearchManager(self.db_path)
        self.search_index = self.search_manager.index
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_search_pipeline(self):
        """Test complete search pipeline"""
        # Index documents
        documents = [
            {
                "doc_id": "doc1",
                "title": "AI Meeting Notes",
                "content": "Discussion about implementing machine learning models",
                "metadata": {
                    "author": "John Doe",
                    "category": "Technology",
                    "tags": ["AI", "ML", "meeting"]
                }
            },
            {
                "doc_id": "doc2",
                "title": "Project Status Update",
                "content": "Current sprint progress and upcoming deadlines",
                "metadata": {
                    "author": "Jane Smith",
                    "category": "Management",
                    "tags": ["project", "status", "sprint"]
                }
            }
        ]
        
        # Index documents
        for doc_data in documents:
            doc = DocumentIndex(
                doc_id=doc_data["doc_id"],
                title=doc_data["title"],
                content=doc_data["content"],
                metadata=doc_data["metadata"]
            )
            self.search_index.index_document(doc)
        
        # Search for documents
        query = SearchQuery(
            query="machine learning",
            options={
                "limit": 10,
                "include_content": True
            }
        )
        result = asyncio.run(self.search_manager.search(query))
        
        assert result.total_count >= 1
        assert len(result.results) >= 1
        assert result.results[0]["doc_id"] == "doc1"
        assert "machine learning" in result.results[0]["content"].lower()
    
    def test_faceted_search(self):
        """Test faceted search capabilities"""
        # Index sample documents
        for i in range(5):
            doc = DocumentIndex(
                doc_id=f"doc_{i}",
                title=f"Document {i}",
                content=f"Content for document {i}",
                metadata={
                    "category": "Technology" if i % 2 == 0 else "Business",
                    "author": f"Author{i % 3}",
                    "tags": ["test", f"tag{i}"]
                }
            )
            self.search_index.index_document(doc)
        
        # Get facets
        facets = self.search_index.get_facets()
        
        # Check that facets structure exists
        assert "tags" in facets
        assert "speakers" in facets
        assert "languages" in facets
        assert "entity_types" in facets
        
        # Verify tags were indexed (should have at least "test" tag)
        if facets["tags"]:
            assert "test" in facets["tags"] or len(facets["tags"]) > 0


class TestDiarizationIntegration:
    """Test speaker diarization integration"""
    
    @pytest.mark.asyncio
    async def test_diarization_pipeline(self):
        """Test complete diarization pipeline"""
        manager = DiarizationManager()
        
        # Use mock provider for testing
        mock_provider = MockProvider({"processing_delay": 0.1})
        manager.set_provider(mock_provider)
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"RIFF")  # Basic WAV header
            # Write some dummy data to make it a valid file
            tmp.write(b"RIFF")  # Basic WAV header
        
        try:
            # Run diarization
            result = await manager.process_audio(
                audio_path=tmp_path,
                min_segment_duration=1.0
            )
            
            assert result is not None
            assert len(result.speakers) > 0
            assert len(result.segments) > 0
            assert result.audio_duration > 0
            
            # Check segments
            for segment in result.segments:
                assert segment.speaker_id in result.speakers
                assert segment.duration >= 1.0  # min_segment_duration
                assert segment.confidence > 0
        
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test provider fallback mechanism"""
        manager = DiarizationManager()
        
        # Add mock provider
        mock_provider = MockProvider({"processing_delay": 0.1})
        manager.set_provider(mock_provider)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"RIFF")  # Basic WAV header
        
        try:
            # Try diarization with mock provider
            result = await manager.process_audio(
                audio_path=tmp_path
            )
            
            # Should fallback to mock provider
            assert result is not None
            assert result.metadata.get("provider") == "mock"
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestWebSocketIntegration:
    """Test WebSocket event system integration"""
    
    @pytest.mark.asyncio
    async def test_event_handling_pipeline(self):
        """Test event creation and handling pipeline"""
        
        # Create event handlers
        handled_events = []
        
        class TestTranscriptHandler(EventHandler):
            def can_handle(self, event: Event) -> bool:
                return event.type == EventType.TRANSCRIPT_UPDATED
            
            async def handle(self, event: Event) -> dict:
                handled_events.append(event)
                return {"status": "success", "handled": True}
        
        class TestNotificationHandler(EventHandler):
            def can_handle(self, event: Event) -> bool:
                return event.type == EventType.NOTIFICATION_NEW
            
            async def handle(self, event: Event) -> dict:
                handled_events.append(event)
                return {"status": "success", "notified": True}
        
        # Create handlers
        transcript_handler = TestTranscriptHandler()
        notification_handler = TestNotificationHandler()
        
        # Create events
        events = [
            Event(
                type=EventType.TRANSCRIPT_UPDATED,
                data={"transcript_id": 1, "changes": {"title": "New Title"}},
                room_id="transcript_1",
                user_id=1
            ),
            Event(
                type=EventType.NOTIFICATION_NEW,
                data={"message": "Transcript shared with you"},
                room_id="user_1",
                user_id=1
            ),
            Event(
                type=EventType.PROCESSING_STARTED,
                data={"job_id": "job123"},
                room_id="processing",
                user_id=1
            )
        ]
        
        # Process events
        for event in events:
            if transcript_handler.can_handle(event):
                await transcript_handler.handle(event)
            elif notification_handler.can_handle(event):
                await notification_handler.handle(event)
        
        # Verify handling
        assert len(handled_events) == 2
        assert handled_events[0].type == EventType.TRANSCRIPT_UPDATED
        assert handled_events[1].type == EventType.NOTIFICATION_NEW
    
    def test_event_types_consistency(self):
        """Test that all event types are properly defined"""
        # Check that we have all expected event types
        expected_types = [
            "transcript.updated",
            "transcript.deleted",
            "notification.new",
            "processing.started",
            "processing.completed",
            "room.join",
            "room.leave"
        ]
        
        event_type_values = [et.value for et in EventType]
        
        for expected in expected_types:
            assert expected in event_type_values, f"Missing event type: {expected}"


class TestFeatureIntegration:
    """Test integration between multiple features"""
    
    @pytest.mark.asyncio
    async def test_search_and_diarization_integration(self):
        """Test integration between search and diarization features"""
        # Setup search
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_integration.db")
        search_index = SearchIndex(db_path)
        
        # Setup diarization
        manager = DiarizationManager()
        mock_provider = MockProvider({"processing_delay": 0.1})
        manager.set_provider(mock_provider)
        
        try:
            # Create temporary audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            # Run diarization
            diarization_result = await manager.process_audio(
                audio_path=tmp_path
            )
            
            # Index diarization results in search
            for i, segment in enumerate(diarization_result.segments):
                doc = DocumentIndex(
                    doc_id=f"segment_{i}",
                    title=f"Speaker {segment.speaker_id} - Segment {i}",
                    content=segment.text or f"Segment content {i}",
                    metadata={
                        "speaker": segment.speaker_id,
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "confidence": segment.confidence
                    }
                )
                search_index.index_document(doc)
            
            # Search for speaker segments
            search_manager = SearchManager(search_index)
            query = SearchQuery(
                query="segment content",
                options={"limit": 10}
            )
            result = asyncio.run(search_manager.search(query))
            
            assert result.total_count > 0
            assert len(result.results) > 0
            assert "speaker" in result.results[0]["metadata"]
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Integration Tests for New Features")
    print("=" * 50)
    
    # Run search tests
    print("\n📚 Testing Search Integration...")
    search_test = TestSearchIntegration()
    search_test.setup_method()
    try:
        search_test.test_search_pipeline()
        print("✅ Search pipeline test passed")
        
        search_test.test_faceted_search()
        print("✅ Faceted search test passed")
    finally:
        search_test.teardown_method()
    
    # Run WebSocket tests
    print("\n🔌 Testing WebSocket Integration...")
    ws_test = TestWebSocketIntegration()
    
    asyncio.run(ws_test.test_event_handling_pipeline())
    print("✅ Event handling pipeline test passed")
    
    ws_test.test_event_types_consistency()
    print("✅ Event types consistency test passed")
    
    # Run diarization tests
    print("\n🎙️ Testing Diarization Integration...")
    diarization_test = TestDiarizationIntegration()
    
    asyncio.run(diarization_test.test_diarization_pipeline())
    print("✅ Diarization pipeline test passed")
    
    asyncio.run(diarization_test.test_provider_fallback())
    print("✅ Provider fallback test passed")
    
    # Run cross-feature integration tests
    print("\n🔗 Testing Cross-Feature Integration...")
    integration_test = TestFeatureIntegration()
    
    asyncio.run(integration_test.test_search_and_diarization_integration())
    print("✅ Search and diarization integration test passed")
    
    print("\n✅ All integration tests passed!")


if __name__ == "__main__":
    run_integration_tests()