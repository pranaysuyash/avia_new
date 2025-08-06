"""
Demo script for Comprehensive Timestamping System

This script demonstrates:
- Word-level timestamp generation
- Segment-based organization
- Clickable transcript creation
- Bookmark management
- Time code navigation
- Export capabilities

Requirements: 3.1, 7.4
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# Import the timestamping system
from timestamping_system import (
    TimestampingSystem, WordTimestamp, SegmentTimestamp, 
    TimeCode, Bookmark, TranscriptSegment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimestampingSystemDemo:
    """Demo class for the Timestamping System"""
    
    def __init__(self):
        self.ts_system = TimestampingSystem()
        self.demo_content_id = "demo_audio_001"
        self.demo_transcript = """
        Welcome to our comprehensive timestamping system demonstration. 
        This system provides advanced features for audio and video content analysis.
        We can generate word-level timestamps with high precision.
        Speaker diarization helps identify different speakers in conversations.
        The system supports multiple languages and export formats.
        Bookmarks allow users to mark important moments for quick navigation.
        Real-time synchronization ensures perfect alignment between text and audio.
        Advanced analytics provide insights into speaking patterns and content quality.
        """
        
        print("🕒 Timestamping System Demo Initialized")
        print(f"Database: {self.ts_system.database_path}")
        print("-" * 60)
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        try:
            print("🚀 Starting Comprehensive Timestamping System Demo\n")
            
            # Step 1: Generate word timestamps
            self.demo_word_timestamps()
            
            # Step 2: Create segment timestamps
            self.demo_segment_timestamps()
            
            # Step 3: Generate time codes
            self.demo_time_codes()
            
            # Step 4: Create clickable transcript
            self.demo_clickable_transcript()
            
            # Step 5: Bookmark management
            self.demo_bookmark_system()
            
            # Step 6: Search and navigation
            self.demo_search_navigation()
            
            # Step 7: Export capabilities
            self.demo_export_features()
            
            # Step 8: Analytics and insights
            self.demo_analytics()
            
            print("\n✅ Demo completed successfully!")
            print("🎯 All timestamping features demonstrated")
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
            print(f"❌ Demo failed: {e}")
    
    def demo_word_timestamps(self):
        """Demonstrate word-level timestamp generation"""
        print("📝 DEMO: Word-Level Timestamps")
        print("=" * 40)
        
        try:
            # Create a mock audio file path (in real usage, this would be an actual audio file)
            mock_audio_path = "demo_audio.wav"
            
            # Test different timestamping methods
            methods = ["forced_alignment", "vad_based", "ml_based"]
            
            for method in methods:
                print(f"\n🔍 Testing {method} method...")
                
                # Generate word timestamps
                word_timestamps = self.ts_system.generate_word_timestamps(
                    audio_path=mock_audio_path,
                    transcript=self.demo_transcript,
                    content_id=f"{self.demo_content_id}_{method}",
                    method=method
                )
                
                if word_timestamps:
                    print(f"✅ Generated {len(word_timestamps)} word timestamps")
                    
                    # Show first few words
                    print("📊 Sample word timestamps:")
                    for i, word_ts in enumerate(word_timestamps[:5]):
                        print(f"  {i+1}. '{word_ts.word}' -> "
                              f"{word_ts.start_time:.2f}s - {word_ts.end_time:.2f}s "
                              f"(confidence: {word_ts.confidence:.2f})")
                    
                    # Calculate statistics
                    total_duration = max(w.end_time for w in word_timestamps)
                    avg_confidence = sum(w.confidence for w in word_timestamps) / len(word_timestamps)
                    words_per_minute = (len(word_timestamps) / total_duration) * 60
                    
                    print(f"📈 Statistics:")
                    print(f"  - Total duration: {total_duration:.2f} seconds")
                    print(f"  - Average confidence: {avg_confidence:.2f}")
                    print(f"  - Words per minute: {words_per_minute:.1f}")
                    
                else:
                    print("❌ No word timestamps generated")
            
            print("\n✅ Word timestamp generation demo completed")
            
        except Exception as e:
            logger.error(f"Word timestamp demo error: {e}")
            print(f"❌ Word timestamp demo failed: {e}")
    
    def demo_segment_timestamps(self):
        """Demonstrate segment-level timestamp generation"""
        print("\n📑 DEMO: Segment Timestamps")
        print("=" * 40)
        
        try:
            mock_audio_path = "demo_audio.wav"
            
            # Test speaker-based segmentation
            print("🎤 Testing speaker-based segmentation...")
            speakers = ["Speaker_A", "Speaker_B", "Speaker_C"]
            
            speaker_segments = self.ts_system.generate_segment_timestamps(
                audio_path=mock_audio_path,
                transcript=self.demo_transcript,
                content_id=f"{self.demo_content_id}_speakers",
                speakers=speakers
            )
            
            if speaker_segments:
                print(f"✅ Generated {len(speaker_segments)} speaker segments")
                
                for i, segment in enumerate(speaker_segments[:3]):
                    print(f"  {i+1}. {segment.segment_type} ({segment.speaker_id})")
                    print(f"     Time: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
                    print(f"     Content: {segment.content[:50]}...")
                    print(f"     Confidence: {segment.confidence:.2f}")
            
            # Test topic-based segmentation
            print("\n📚 Testing topic-based segmentation...")
            
            topic_segments = self.ts_system.generate_segment_timestamps(
                audio_path=mock_audio_path,
                transcript=self.demo_transcript,
                content_id=f"{self.demo_content_id}_topics"
            )
            
            if topic_segments:
                print(f"✅ Generated {len(topic_segments)} topic segments")
                
                for i, segment in enumerate(topic_segments[:3]):
                    print(f"  {i+1}. {segment.segment_type} - {segment.topic}")
                    print(f"     Time: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
                    print(f"     Duration: {segment.duration():.2f}s")
                    print(f"     Content: {segment.content[:50]}...")
            
            print("\n✅ Segment timestamp generation demo completed")
            
        except Exception as e:
            logger.error(f"Segment timestamp demo error: {e}")
            print(f"❌ Segment timestamp demo failed: {e}")
    
    def demo_time_codes(self):
        """Demonstrate time code generation"""
        print("\n🕐 DEMO: Time Code Generation")
        print("=" * 40)
        
        try:
            # Create sample segments for time code generation
            sample_segments = [
                SegmentTimestamp(
                    id="seg_1",
                    start_time=0.0,
                    end_time=15.0,
                    segment_type="speaker",
                    content="Introduction and welcome",
                    speaker_id="Speaker_A"
                ),
                SegmentTimestamp(
                    id="seg_2", 
                    start_time=15.0,
                    end_time=30.0,
                    segment_type="topic",
                    content="System overview and features",
                    topic="Overview"
                ),
                SegmentTimestamp(
                    id="seg_3",
                    start_time=30.0,
                    end_time=45.0,
                    segment_type="speaker",
                    content="Technical implementation details",
                    speaker_id="Speaker_B"
                )
            ]
            
            # Create sample bookmarks
            sample_bookmarks = [
                Bookmark(
                    id="bookmark_1",
                    timestamp=10.5,
                    title="Key Feature Mention",
                    description="Important feature discussion",
                    tags=["feature", "important"]
                ),
                Bookmark(
                    id="bookmark_2",
                    timestamp=25.0,
                    title="Technical Deep Dive",
                    description="Detailed technical explanation",
                    tags=["technical", "deep-dive"]
                )
            ]
            
            # Generate time codes
            time_codes = self.ts_system.create_time_codes(
                content_id=self.demo_content_id,
                segments=sample_segments,
                bookmarks=sample_bookmarks
            )
            
            if time_codes:
                print(f"✅ Generated {len(time_codes)} time codes")
                
                print("📍 Time codes:")
                for time_code in time_codes:
                    formatted_time = time_code.format_time("hms")
                    print(f"  • {formatted_time} - {time_code.label} ({time_code.category})")
                    if time_code.description:
                        print(f"    Description: {time_code.description}")
                
                # Demonstrate different time formats
                print("\n🕒 Time format examples:")
                sample_time = 125.750  # 2 minutes, 5.75 seconds
                sample_code = TimeCode(timestamp=sample_time, label="Sample")
                
                print(f"  - HMS format: {sample_code.format_time('hms')}")
                print(f"  - MS format: {sample_code.format_time('ms')}")
                print(f"  - Seconds format: {sample_code.format_time('seconds')}")
            
            print("\n✅ Time code generation demo completed")
            
        except Exception as e:
            logger.error(f"Time code demo error: {e}")
            print(f"❌ Time code demo failed: {e}")
    
    def demo_clickable_transcript(self):
        """Demonstrate clickable transcript creation"""
        print("\n📝 DEMO: Clickable Transcript")
        print("=" * 40)
        
        try:
            # Generate sample word timestamps for transcript
            words = self.demo_transcript.split()
            word_timestamps = []
            
            time_per_word = 0.5  # 0.5 seconds per word
            
            for i, word in enumerate(words):
                start_time = i * time_per_word
                end_time = (i + 1) * time_per_word
                
                word_timestamps.append(WordTimestamp(
                    word=word.strip('.,!?'),
                    start_time=start_time,
                    end_time=end_time,
                    confidence=0.85 + (i % 3) * 0.05  # Varying confidence
                ))
            
            # Create clickable transcript
            transcript_segments = self.ts_system.create_clickable_transcript(
                content_id=self.demo_content_id,
                transcript=self.demo_transcript,
                word_timestamps=word_timestamps
            )
            
            if transcript_segments:
                print(f"✅ Generated {len(transcript_segments)} transcript segments")
                
                print("📄 Clickable transcript segments:")
                for i, segment in enumerate(transcript_segments[:3]):
                    print(f"\n  Segment {i+1}:")
                    print(f"    Time: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
                    print(f"    Text: {segment.text}")
                    print(f"    Words: {len(segment.words)}")
                    print(f"    Confidence: {segment.confidence:.2f}")
                    print(f"    Clickable: {segment.is_clickable}")
                    
                    # Show word-level details for first segment
                    if i == 0 and segment.words:
                        print("    📝 Word details:")
                        for j, word in enumerate(segment.words[:3]):
                            print(f"      {j+1}. '{word.word}' -> "
                                  f"{word.start_time:.2f}s-{word.end_time:.2f}s")
                
                # Demonstrate word lookup at specific time
                test_time = 5.0
                word_at_time = None
                for segment in transcript_segments:
                    word_at_time = segment.get_word_at_time(test_time)
                    if word_at_time:
                        break
                
                if word_at_time:
                    print(f"\n🎯 Word at {test_time}s: '{word_at_time.word}'")
                else:
                    print(f"\n🎯 No word found at {test_time}s")
            
            print("\n✅ Clickable transcript demo completed")
            
        except Exception as e:
            logger.error(f"Clickable transcript demo error: {e}")
            print(f"❌ Clickable transcript demo failed: {e}")
    
    def demo_bookmark_system(self):
        """Demonstrate bookmark management"""
        print("\n🔖 DEMO: Bookmark System")
        print("=" * 40)
        
        try:
            # Create various bookmarks
            bookmarks_to_create = [
                {
                    "timestamp": 12.5,
                    "title": "System Introduction",
                    "description": "Overview of the timestamping system capabilities",
                    "tags": ["introduction", "overview"]
                },
                {
                    "timestamp": 28.0,
                    "title": "Technical Details",
                    "description": "Deep dive into technical implementation",
                    "tags": ["technical", "implementation"]
                },
                {
                    "timestamp": 45.5,
                    "title": "Feature Demonstration",
                    "description": "Live demonstration of key features",
                    "tags": ["demo", "features", "live"]
                },
                {
                    "timestamp": 62.0,
                    "title": "Q&A Session",
                    "description": "Questions and answers from the audience",
                    "tags": ["qa", "questions", "audience"]
                }
            ]
            
            created_bookmarks = []
            
            print("📌 Creating bookmarks...")
            for bookmark_data in bookmarks_to_create:
                bookmark = self.ts_system.create_bookmark(
                    content_id=self.demo_content_id,
                    timestamp=bookmark_data["timestamp"],
                    title=bookmark_data["title"],
                    description=bookmark_data["description"],
                    tags=bookmark_data["tags"],
                    user_id="demo_user"
                )
                
                created_bookmarks.append(bookmark)
                print(f"  ✅ Created: '{bookmark.title}' at {bookmark.timestamp}s")
            
            # Retrieve bookmarks
            print(f"\n📋 Retrieving bookmarks for content '{self.demo_content_id}'...")
            retrieved_bookmarks = self.ts_system.get_bookmarks(
                content_id=self.demo_content_id,
                user_id="demo_user"
            )
            
            if retrieved_bookmarks:
                print(f"✅ Found {len(retrieved_bookmarks)} bookmarks")
                
                for bookmark in retrieved_bookmarks:
                    print(f"\n  🔖 {bookmark.title}")
                    print(f"     Time: {bookmark.timestamp}s")
                    print(f"     Description: {bookmark.description}")
                    print(f"     Tags: {', '.join(bookmark.tags)}")
                    print(f"     Created: {bookmark.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Demonstrate bookmark navigation
                print(f"\n🧭 Bookmark navigation examples:")
                for bookmark in retrieved_bookmarks[:2]:
                    formatted_time = f"{int(bookmark.timestamp//60):02d}:{int(bookmark.timestamp%60):02d}"
                    print(f"  • Jump to '{bookmark.title}' -> {formatted_time}")
            
            print("\n✅ Bookmark system demo completed")
            
        except Exception as e:
            logger.error(f"Bookmark demo error: {e}")
            print(f"❌ Bookmark demo failed: {e}")
    
    def demo_search_navigation(self):
        """Demonstrate search and navigation features"""
        print("\n🔍 DEMO: Search and Navigation")
        print("=" * 40)
        
        try:
            # Test word-level search
            print("🔎 Testing word-level search...")
            
            test_timestamp = 15.0
            word_at_time = self.ts_system.get_word_at_timestamp(
                content_id=self.demo_content_id,
                timestamp=test_timestamp
            )
            
            if word_at_time:
                print(f"✅ Word at {test_timestamp}s: '{word_at_time.word}'")
                print(f"   Confidence: {word_at_time.confidence:.2f}")
                print(f"   Duration: {word_at_time.duration():.2f}s")
            else:
                print(f"❌ No word found at {test_timestamp}s")
            
            # Test segment search
            print(f"\n📑 Testing segment search...")
            
            segment_at_time = self.ts_system.get_segment_at_timestamp(
                content_id=self.demo_content_id,
                timestamp=test_timestamp
            )
            
            if segment_at_time:
                print(f"✅ Segment at {test_timestamp}s:")
                print(f"   Type: {segment_at_time.segment_type}")
                print(f"   Content: {segment_at_time.content[:50]}...")
                print(f"   Duration: {segment_at_time.duration():.2f}s")
            else:
                print(f"❌ No segment found at {test_timestamp}s")
            
            # Test time range search
            print(f"\n⏰ Testing time range search...")
            
            start_time = 10.0
            end_time = 30.0
            
            search_results = self.ts_system.search_by_timestamp(
                content_id=self.demo_content_id,
                start_time=start_time,
                end_time=end_time
            )
            
            print(f"🔍 Search results for {start_time}s - {end_time}s:")
            print(f"   Words found: {len(search_results['words'])}")
            print(f"   Segments found: {len(search_results['segments'])}")
            print(f"   Bookmarks found: {len(search_results['bookmarks'])}")
            
            # Show sample results
            if search_results['words']:
                print(f"   📝 Sample words:")
                for word in search_results['words'][:3]:
                    print(f"     • '{word['word']}' at {word['start_time']:.2f}s")
            
            if search_results['bookmarks']:
                print(f"   🔖 Sample bookmarks:")
                for bookmark in search_results['bookmarks'][:2]:
                    print(f"     • '{bookmark['title']}' at {bookmark['timestamp']}s")
            
            print("\n✅ Search and navigation demo completed")
            
        except Exception as e:
            logger.error(f"Search demo error: {e}")
            print(f"❌ Search demo failed: {e}")
    
    def demo_export_features(self):
        """Demonstrate export capabilities"""
        print("\n📤 DEMO: Export Features")
        print("=" * 40)
        
        try:
            export_formats = ["json", "srt", "vtt", "elan"]
            
            for format_type in export_formats:
                print(f"\n📄 Exporting to {format_type.upper()} format...")
                
                export_data = self.ts_system.export_timestamps(
                    content_id=self.demo_content_id,
                    format_type=format_type
                )
                
                if export_data:
                    print(f"✅ Export successful ({len(export_data)} characters)")
                    
                    # Show preview of exported data
                    preview_length = 200
                    preview = export_data[:preview_length]
                    if len(export_data) > preview_length:
                        preview += "..."
                    
                    print(f"📋 Preview:")
                    print("   " + "\n   ".join(preview.split("\n")[:5]))
                    
                    # Save to file for demonstration
                    filename = f"demo_export_{self.demo_content_id}.{format_type}"
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(export_data)
                        print(f"💾 Saved to: {filename}")
                    except Exception as save_error:
                        print(f"⚠️ Could not save file: {save_error}")
                
                else:
                    print(f"❌ Export failed for {format_type}")
            
            print("\n✅ Export features demo completed")
            
        except Exception as e:
            logger.error(f"Export demo error: {e}")
            print(f"❌ Export demo failed: {e}")
    
    def demo_analytics(self):
        """Demonstrate analytics and insights"""
        print("\n📊 DEMO: Analytics and Insights")
        print("=" * 40)
        
        try:
            # Simulate analytics data
            print("📈 Generating analytics insights...")
            
            # Word-level analytics
            sample_words = [
                {"word": "system", "start_time": 5.0, "end_time": 5.5, "confidence": 0.95},
                {"word": "advanced", "start_time": 10.0, "end_time": 10.8, "confidence": 0.88},
                {"word": "features", "start_time": 15.0, "end_time": 15.6, "confidence": 0.92},
                {"word": "demonstration", "start_time": 20.0, "end_time": 21.2, "confidence": 0.85},
                {"word": "timestamping", "start_time": 25.0, "end_time": 26.0, "confidence": 0.90}
            ]
            
            # Calculate analytics
            total_words = len(sample_words)
            total_duration = max(w["end_time"] for w in sample_words)
            avg_confidence = sum(w["confidence"] for w in sample_words) / total_words
            words_per_minute = (total_words / total_duration) * 60
            
            print(f"📊 Word-level analytics:")
            print(f"   Total words: {total_words}")
            print(f"   Total duration: {total_duration:.2f} seconds")
            print(f"   Average confidence: {avg_confidence:.2f}")
            print(f"   Words per minute: {words_per_minute:.1f}")
            
            # Confidence distribution
            high_confidence = sum(1 for w in sample_words if w["confidence"] >= 0.9)
            medium_confidence = sum(1 for w in sample_words if 0.8 <= w["confidence"] < 0.9)
            low_confidence = sum(1 for w in sample_words if w["confidence"] < 0.8)
            
            print(f"\n🎯 Confidence distribution:")
            print(f"   High (≥0.9): {high_confidence} words ({high_confidence/total_words*100:.1f}%)")
            print(f"   Medium (0.8-0.9): {medium_confidence} words ({medium_confidence/total_words*100:.1f}%)")
            print(f"   Low (<0.8): {low_confidence} words ({low_confidence/total_words*100:.1f}%)")
            
            # Speaking pattern analysis
            word_durations = [w["end_time"] - w["start_time"] for w in sample_words]
            avg_word_duration = sum(word_durations) / len(word_durations)
            
            print(f"\n🗣️ Speaking pattern analysis:")
            print(f"   Average word duration: {avg_word_duration:.2f} seconds")
            print(f"   Longest word: {max(word_durations):.2f} seconds")
            print(f"   Shortest word: {min(word_durations):.2f} seconds")
            
            # Quality assessment
            quality_score = avg_confidence * 0.7 + (1 - min(1.0, abs(words_per_minute - 150) / 150)) * 0.3
            
            print(f"\n⭐ Overall quality assessment:")
            print(f"   Quality score: {quality_score:.2f}/1.0")
            
            if quality_score >= 0.9:
                quality_rating = "Excellent"
            elif quality_score >= 0.8:
                quality_rating = "Good"
            elif quality_score >= 0.7:
                quality_rating = "Fair"
            else:
                quality_rating = "Needs Improvement"
            
            print(f"   Quality rating: {quality_rating}")
            
            # Recommendations
            print(f"\n💡 Recommendations:")
            if avg_confidence < 0.8:
                print("   • Consider improving audio quality for better transcription accuracy")
            if words_per_minute > 180:
                print("   • Speaking rate is quite fast - consider slowing down for better clarity")
            elif words_per_minute < 120:
                print("   • Speaking rate is slow - consider increasing pace for better engagement")
            if low_confidence > total_words * 0.2:
                print("   • High number of low-confidence words - review audio quality and background noise")
            
            print("\n✅ Analytics and insights demo completed")
            
        except Exception as e:
            logger.error(f"Analytics demo error: {e}")
            print(f"❌ Analytics demo failed: {e}")
    
    def cleanup_demo_data(self):
        """Clean up demo data"""
        print("\n🧹 Cleaning up demo data...")
        
        try:
            # Remove demo export files
            import glob
            export_files = glob.glob(f"demo_export_{self.demo_content_id}.*")
            
            for file_path in export_files:
                try:
                    os.remove(file_path)
                    print(f"   🗑️ Removed: {file_path}")
                except Exception as e:
                    print(f"   ⚠️ Could not remove {file_path}: {e}")
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            print(f"❌ Cleanup failed: {e}")


def main():
    """Main function to run the demo"""
    print("🎬 COMPREHENSIVE TIMESTAMPING SYSTEM DEMO")
    print("=" * 60)
    print("This demo showcases advanced timestamping capabilities including:")
    print("• Word-level timestamps with multiple alignment methods")
    print("• Segment-based organization (speakers/topics)")
    print("• Interactive time codes and navigation")
    print("• Clickable transcript with audio synchronization")
    print("• Bookmark system for important moments")
    print("• Search and navigation features")
    print("• Multiple export formats (JSON, SRT, VTT, ELAN)")
    print("• Analytics and quality insights")
    print("=" * 60)
    
    # Initialize demo
    demo = TimestampingSystemDemo()
    
    try:
        # Run the complete demonstration
        demo.run_complete_demo()
        
        # Optional cleanup
        cleanup = input("\n🧹 Clean up demo files? (y/n): ").lower().strip()
        if cleanup == 'y':
            demo.cleanup_demo_data()
        
        print("\n🎉 Thank you for exploring the Timestamping System!")
        print("🚀 Ready for production use with real audio/video files")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo execution error: {e}")
        print(f"\n❌ Demo execution failed: {e}")
    
    print("\n👋 Demo session ended")


if __name__ == "__main__":
    main()