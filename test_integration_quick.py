#!/usr/bin/env python3
"""
Quick integration test for new features
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Quick Integration Test")
print("=" * 50)

# Test 1: WebSocket Events
print("\n1️⃣ Testing WebSocket Events...")
try:
    from websocket import EventType, Event, EventHandler
    
    event = Event(
        type=EventType.TRANSCRIPT_UPDATED,
        data={"transcript_id": 123},
        room_id="test",
        user_id=1
    )
    print(f"✅ Created event: {event.type.value}")
except Exception as e:
    print(f"❌ WebSocket test failed: {e}")

# Test 2: Search Functionality
print("\n2️⃣ Testing Search...")
try:
    from search.search_manager import SearchManager, SearchQuery
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")
        manager = SearchManager(db_path)
        
        # Index a document
        from search.search_index import DocumentIndex
        doc = DocumentIndex(
            doc_id="test1",
            title="Test Document",
            content="This is a test document for integration testing",
            metadata={"category": "test"}
        )
        manager.index.index_document(doc)
        
        # Search for it
        query = SearchQuery(query="test document")
        result = asyncio.run(manager.search(query))
        
        if result.total_count > 0:
            print(f"✅ Search found {result.total_count} results")
        else:
            print("❌ Search returned no results")
            
except Exception as e:
    print(f"❌ Search test failed: {e}")

# Test 3: Speaker Diarization
print("\n3️⃣ Testing Speaker Diarization...")
try:
    from speaker_diarization.diarization_manager import DiarizationManager
    from speaker_diarization.providers.mock_provider import MockProvider
    
    manager = DiarizationManager()
    provider = MockProvider({"processing_delay": 0.1})
    manager.set_provider(provider)
    
    # Test with temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b"RIFF")  # Minimal WAV header
    
    try:
        result = asyncio.run(manager.process_audio(tmp_path))
        print(f"✅ Diarization completed: {len(result.speakers)} speakers, {len(result.segments)} segments")
    finally:
        os.unlink(tmp_path)
        
except Exception as e:
    print(f"❌ Diarization test failed: {e}")

# Test 4: Authentication (if available)
print("\n4️⃣ Testing Authentication...")
try:
    from auth.auth_manager import AuthManager
    from auth.models import UserCreate
    
    print("✅ Authentication modules available")
except ImportError:
    print("⚠️ Authentication requires API server running")

print("\n" + "=" * 50)
print("✅ Quick integration test completed!")