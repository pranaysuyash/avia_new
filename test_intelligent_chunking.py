#!/usr/bin/env python3
"""
Test script for intelligent content chunking and segmentation
Tests Task 37 implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from segmentation.intelligent_chunking import IntelligentChunkingSystem
from segmentation.segment_manager import SegmentManager, SegmentType
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_segmentation():
    """Test basic segmentation functionality"""
    print("🧪 Testing Basic Segmentation...")
    
    # Sample transcript
    transcript = """
    Hello everyone, welcome to today's meeting. My name is John Smith and I'll be your host.
    
    First, let's discuss the quarterly results. Our revenue increased by 15% this quarter.
    The marketing team, led by Sarah Johnson, did an excellent job.
    
    Now, moving on to our next topic. We need to plan for the upcoming product launch.
    The launch is scheduled for December 15th, 2024.
    
    Are there any questions about the timeline? We should also consider the budget implications.
    
    In conclusion, I think we're on track for a successful year. Thank you all for your hard work.
    """
    
    # Sample timestamps
    timestamps = [
        (0.0, 5.0, "Hello everyone, welcome to today's meeting."),
        (5.0, 8.0, "My name is John Smith and I'll be your host."),
        (10.0, 15.0, "First, let's discuss the quarterly results."),
        (15.0, 20.0, "Our revenue increased by 15% this quarter."),
        (20.0, 25.0, "The marketing team, led by Sarah Johnson, did an excellent job."),
        (30.0, 35.0, "Now, moving on to our next topic."),
        (35.0, 40.0, "We need to plan for the upcoming product launch."),
        (40.0, 45.0, "The launch is scheduled for December 15th, 2024."),
        (50.0, 55.0, "Are there any questions about the timeline?"),
        (55.0, 60.0, "We should also consider the budget implications."),
        (65.0, 70.0, "In conclusion, I think we're on track for a successful year."),
        (70.0, 75.0, "Thank you all for your hard work.")
    ]
    
    # Test different segmentation methods
    manager = SegmentManager()
    
    # Test semantic segmentation
    print("  📊 Testing semantic segmentation...")
    semantic_segments = manager.segment_transcript(
        transcript, timestamps, method="semantic"
    )
    print(f"    ✅ Created {len(semantic_segments)} semantic segments")
    
    # Test structural segmentation
    print("  🏗️ Testing structural segmentation...")
    structural_segments = manager.segment_transcript(
        transcript, timestamps, method="structural"
    )
    print(f"    ✅ Created {len(structural_segments)} structural segments")
    
    # Test temporal segmentation
    print("  ⏰ Testing temporal segmentation...")
    temporal_segments = manager.segment_transcript(
        transcript, timestamps, method="temporal"
    )
    print(f"    ✅ Created {len(temporal_segments)} temporal segments")
    
    # Test hybrid segmentation
    print("  🔄 Testing hybrid segmentation...")
    hybrid_segments = manager.segment_transcript(
        transcript, timestamps, speakers=["John Smith", "Sarah Johnson"], method="hybrid"
    )
    print(f"    ✅ Created {len(hybrid_segments)} hybrid segments")
    
    return True

def test_manual_chapters():
    """Test manual chapter creation"""
    print("🧪 Testing Manual Chapter Creation...")
    
    manager = SegmentManager()
    
    # Create manual chapters
    chapters = [
        manager.create_manual_chapter("Introduction", 0.0, "Meeting opening"),
        manager.create_manual_chapter("Quarterly Results", 10.0, "Financial discussion"),
        manager.create_manual_chapter("Product Launch", 30.0, "Planning discussion"),
        manager.create_manual_chapter("Q&A", 50.0, "Questions and answers"),
        manager.create_manual_chapter("Conclusion", 65.0, "Meeting wrap-up")
    ]
    
    print(f"  ✅ Created {len(chapters)} manual chapters")
    
    # Test chapter application
    transcript = "Sample transcript for chapter testing..."
    timestamps = [(0.0, 10.0, "intro"), (10.0, 20.0, "main"), (20.0, 30.0, "end")]
    
    segments_with_chapters = manager.segment_transcript(
        transcript, timestamps, method="hybrid", manual_chapters=chapters
    )
    
    chapter_segments = [seg for seg in segments_with_chapters if seg.type == SegmentType.CHAPTER]
    print(f"  ✅ Applied {len(chapter_segments)} chapters to segments")
    
    return True

def test_export_functionality():
    """Test segment export functionality"""
    print("🧪 Testing Export Functionality...")
    
    manager = SegmentManager()
    
    # Create sample segments
    transcript = "This is a test transcript for export testing."
    timestamps = [(0.0, 5.0, "This is a test"), (5.0, 10.0, "transcript for export testing.")]
    
    segments = manager.segment_transcript(transcript, timestamps, method="hybrid")
    
    # Test different export formats
    formats = ["json", "srt", "vtt", "text"]
    
    for format_type in formats:
        try:
            exported_data = manager.export_segments(segments, format_type)
            print(f"  ✅ Successfully exported to {format_type} format ({len(exported_data)} chars)")
        except Exception as e:
            print(f"  ❌ Failed to export to {format_type}: {e}")
            return False
    
    return True

def test_intelligent_chunking_system():
    """Test the complete intelligent chunking system"""
    print("🧪 Testing Intelligent Chunking System...")
    
    # Mock session state for testing
    class MockSessionState:
        def __init__(self):
            self.data = {}
        
        def get(self, key, default=None):
            return self.data.get(key, default)
        
        def __setitem__(self, key, value):
            self.data[key] = value
        
        def __getitem__(self, key):
            return self.data[key]
        
        def __contains__(self, key):
            return key in self.data
    
    # Mock streamlit session state
    import streamlit as st
    if not hasattr(st, 'session_state'):
        st.session_state = MockSessionState()
    
    # Initialize system
    chunking_system = IntelligentChunkingSystem()
    
    # Test transcript processing
    transcript = """
    Welcome to our presentation. Today we'll cover three main topics.
    
    First, let's talk about our current market position. We've seen significant growth.
    
    Second, our product development roadmap. We have exciting features planned.
    
    Finally, our financial projections for next year. The outlook is positive.
    
    Thank you for your attention. Are there any questions?
    """
    
    timestamps = [
        (0.0, 3.0, "Welcome to our presentation."),
        (3.0, 6.0, "Today we'll cover three main topics."),
        (8.0, 12.0, "First, let's talk about our current market position."),
        (12.0, 15.0, "We've seen significant growth."),
        (17.0, 21.0, "Second, our product development roadmap."),
        (21.0, 24.0, "We have exciting features planned."),
        (26.0, 30.0, "Finally, our financial projections for next year."),
        (30.0, 33.0, "The outlook is positive."),
        (35.0, 38.0, "Thank you for your attention."),
        (38.0, 41.0, "Are there any questions?")
    ]
    
    # Process transcript
    segments = chunking_system.process_transcript(
        transcript=transcript,
        timestamps=timestamps,
        speakers=["Presenter"]
    )
    
    print(f"  ✅ Processed transcript into {len(segments)} segments")
    
    # Test analytics
    analytics = chunking_system.get_segmentation_analytics(segments)
    print(f"  ✅ Generated analytics: {analytics['total_segments']} segments, {analytics['unique_speakers']} speakers")
    
    # Test export
    json_export = chunking_system.export_segments(segments, "json")
    print(f"  ✅ Exported segments to JSON ({len(json_export)} chars)")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Intelligent Content Chunking Tests...")
    print("=" * 60)
    
    tests = [
        test_basic_segmentation,
        test_manual_chapters,
        test_export_functionality,
        test_intelligent_chunking_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED\n")
            else:
                failed += 1
                print("❌ FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED with exception: {e}\n")
    
    print("=" * 60)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Intelligent chunking system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)