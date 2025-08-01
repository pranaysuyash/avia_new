#!/usr/bin/env python3
"""
Final comprehensive integration test
"""

import os
import sys
import asyncio
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_modules():
    """Test all implemented modules"""
    print("🧪 Final Integration Test")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Video Processing
    print("\n1️⃣ Testing Video Processing...")
    try:
        from video_processing import VideoProcessor
        from test_video_processing import create_test_video
        
        processor = VideoProcessor()
        video_path = create_test_video(duration_seconds=2, fps=10)
        
        analysis = processor.analyze_video(
            video_path,
            extract_frames=True,
            detect_scenes=True,
            keyframe_interval=1.0
        )
        
        assert analysis.duration > 0
        assert len(analysis.keyframes) > 0
        
        os.unlink(video_path)
        results['video_processing'] = "✅ PASS"
        
    except Exception as e:
        results['video_processing'] = f"❌ FAIL: {str(e)}"
    
    # Test 2: Content Insights
    print("\n2️⃣ Testing Content Insights...")
    try:
        from content_insights import ContentInsightsAnalyzer
        
        analyzer = ContentInsightsAnalyzer()
        sample_text = "This is a great meeting with positive outcomes and important decisions."
        
        insights = asyncio.run(analyzer.analyze_content(
            transcript=sample_text,
            transcript_id="test_001"
        ))
        
        assert insights.summary.brief
        assert insights.sentiment.overall_sentiment
        
        results['content_insights'] = "✅ PASS"
        
    except Exception as e:
        results['content_insights'] = f"❌ FAIL: {str(e)}"
    
    # Test 3: Export Manager
    print("\n3️⃣ Testing Export Manager...")
    try:
        from export_manager import MultimediaExporter, ExportConfig
        
        temp_dir = tempfile.mkdtemp()
        exporter = MultimediaExporter(temp_dir)
        
        sample_data = {
            'id': 'test_export',
            'title': 'Test Export',
            'transcript': 'Test content for export functionality.',
            'duration': 30.0,
            'language': 'en'
        }
        
        config = ExportConfig(format='json')
        export_path = exporter.export_transcript(sample_data, config)
        
        assert os.path.exists(export_path)
        os.unlink(export_path)
        
        import shutil
        shutil.rmtree(temp_dir)
        
        results['export_manager'] = "✅ PASS"
        
    except Exception as e:
        results['export_manager'] = f"❌ FAIL: {str(e)}"
    
    # Test 4: Search Functionality
    print("\n4️⃣ Testing Search Functionality...")
    try:
        from search.search_manager import SearchManager, SearchQuery
        
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_search.db")
        
        manager = SearchManager(db_path)
        
        # Simple test without actual indexing
        query = SearchQuery(query="test")
        result = asyncio.run(manager.search(query))
        
        assert result.total_count >= 0  # Should not error
        
        import shutil
        shutil.rmtree(temp_dir)
        
        results['search_functionality'] = "✅ PASS"
        
    except Exception as e:
        results['search_functionality'] = f"❌ FAIL: {str(e)}"
    
    # Test 5: WebSocket Events
    print("\n5️⃣ Testing WebSocket Events...")
    try:
        from websocket import EventType, Event, EventHandler
        
        # Test event creation
        event = Event(
            type=EventType.TRANSCRIPT_UPDATED,
            data={"test": "data"},
            room_id="test_room",
            user_id=1
        )
        
        assert event.type == EventType.TRANSCRIPT_UPDATED
        assert event.data["test"] == "data"
        
        results['websocket_events'] = "✅ PASS"
        
    except Exception as e:
        results['websocket_events'] = f"❌ FAIL: {str(e)}"
    
    # Test 6: Speaker Diarization
    print("\n6️⃣ Testing Speaker Diarization...")
    try:
        from speaker_diarization.diarization_manager import DiarizationManager
        from speaker_diarization.providers.mock_provider import MockProvider
        
        manager = DiarizationManager()
        provider = MockProvider({"processing_delay": 0.1})
        manager.set_provider(provider)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"RIFF")  # Minimal WAV header
        
        try:
            result = asyncio.run(manager.process_audio(tmp_path))
            assert len(result.speakers) > 0
            assert len(result.segments) > 0
            
            results['speaker_diarization'] = "✅ PASS"
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        results['speaker_diarization'] = f"❌ FAIL: {str(e)}"
    
    # Test 7: UI Components Import
    print("\n7️⃣ Testing UI Components...")
    try:
        from video_ui import VideoUI
        from content_insights_ui import ContentInsightsUI  
        from export_ui import ExportUI
        from speaker_diarization.diarization_ui import DiarizationUI
        from search.search_ui import SearchUI
        
        # Test instantiation
        video_ui = VideoUI()
        insights_ui = ContentInsightsUI()
        export_ui = ExportUI()
        diarization_ui = DiarizationUI()
        search_ui = SearchUI()
        
        results['ui_components'] = "✅ PASS"
        
    except Exception as e:
        results['ui_components'] = f"❌ FAIL: {str(e)}"
    
    # Results Summary
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        print(f"{test_name.replace('_', ' ').title()}: {result}")
        if result.startswith("✅"):
            passed += 1
    
    print(f"\n🎯 OVERALL SCORE: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Integration is successful.")
    else:
        print("⚠️ Some tests failed. Check implementation details.")
    
    return passed == total


if __name__ == "__main__":
    success = test_all_modules()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Final integration test {'completed successfully' if success else 'had failures'}")