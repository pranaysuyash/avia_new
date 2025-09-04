"""
Demo script for Comprehensive Timestamping System (Fixed Version)

This script demonstrates:
- Word-level timestamp generation using real test files
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
        
        # Use real test data
        self.test_audio_files = [
            "test_audio.wav",
            "processed_ensemble.wav",
            "processed_webrtc.wav",
            "test_data/audio/business_meeting.wav",
            "test_data/audio/educational_lecture.wav"
        ]
        
        # Load real transcript
        try:
            with open("test_data/transcripts/business_meeting.txt", "r") as f:
                self.demo_transcript = f.read().strip()
        except FileNotFoundError:
            # Fallback transcript
            self.demo_transcript = """
            Good morning everyone. This is John Smith, CEO of TechCorp Industries. 
            Today is January 15th, 2024, and we're here in our Seattle headquarters 
            for the quarterly board meeting. We'll be discussing our Q4 results 
            with Sarah Johnson from the finance team and Michael Chen from operations.
            Our revenue for this quarter reached $2.5 million, which represents 
            a 25% increase from last year. We've successfully expanded to 
            New York City and Los Angeles, hiring 150 new employees.
            """
        
        # Store demo data for later use
        self.stored_word_timestamps = []
        self.stored_segments = []
        
        print("🕒 Timestamping System Demo Initialized")
        print(f"Database: {self.ts_system.database_path}")
        print(f"Available test audio files: {len(self.test_audio_files)}")
        print("-" * 60)
    
    def find_available_audio_file(self):
        """Find the first available audio file"""
        for test_file in self.test_audio_files:
            if os.path.exists(test_file):
                return test_file
        return None
    
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
            import traceback
            logger.error(f"Demo error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"❌ Demo failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    
    def demo_word_timestamps(self):
        """Demonstrate word-level timestamp generation"""
        print("📝 DEMO: Word-Level Timestamps")
        print("=" * 40)
        
        try:
            # Find available audio file
            audio_path = self.find_available_audio_file()
            
            if audio_path:
                print(f"🎵 Using audio file: {audio_path}")
            else:
                print("⚠️ No audio files found, using simulation mode")
                audio_path = "simulation_mode"
            
            # Test different timestamping methods
            methods = ["forced_alignment", "vad_based", "ml_based"]
            
            for method in methods:
                print(f"\n🔍 Testing {method} method...")
                
                if audio_path == "simulation_mode":
                    # Create simulated word timestamps
                    word_timestamps = self.create_simulated_word_timestamps()
                    print(f"✅ Generated {len(word_timestamps)} simulated word timestamps")
                else:
                    # Generate real word timestamps
                    word_timestamps = self.ts_system.generate_word_timestamps(
                        audio_path=audio_path,
                        transcript=self.demo_transcript,
                        content_id=f"{self.demo_content_id}_{method}",
                        method=method
                    )
                    
                    if word_timestamps:
                        print(f"✅ Generated {len(word_timestamps)} word timestamps")
                    else:
                        print("❌ No word timestamps generated, creating simulation")
                        word_timestamps = self.create_simulated_word_timestamps()
                
                if word_timestamps:
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
                    
                    # Store the best result for later use
                    if method == "forced_alignment":
                        self.stored_word_timestamps = word_timestamps
                
            print("\n✅ Word timestamp generation demo completed")
            
        except Exception as e:
            logger.error(f"Word timestamp demo error: {e}")
            print(f"❌ Word timestamp demo failed: {e}")
    
    def create_simulated_word_timestamps(self):
        """Create simulated word timestamps for demo purposes with realistic timing"""
        words = self.demo_transcript.split()
        word_timestamps = []
        
        # More realistic speaking parameters
        base_wpm = 150  # Target 150 words per minute
        current_time = 0.0
        
        for i, word in enumerate(words):
            # Clean word
            clean_word = word.strip('.,!?;:')
            
            # More realistic word duration based on syllables and length
            syllable_count = max(1, len(clean_word) // 3)  # Rough syllable estimate
            base_duration = (syllable_count * 0.2) + 0.1  # ~0.2s per syllable + base
            
            # Add natural variation
            variation = (i % 7 - 3) * 0.02  # Small random-like variation
            duration = max(0.1, base_duration + variation)
            
            # Natural pauses based on punctuation and sentence structure
            if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                pause = 0.6 + (i % 3) * 0.1  # Sentence end pause
            elif word.endswith(',') or word.endswith(';'):
                pause = 0.3 + (i % 2) * 0.05  # Clause pause
            elif i > 0 and i % 8 == 0:  # Breathing pause every ~8 words
                pause = 0.4
            else:
                pause = 0.05 + (i % 4) * 0.02  # Small inter-word pause
            
            start_time = current_time
            end_time = current_time + duration
            current_time = end_time + pause
            
            # More realistic confidence distribution
            # Most words should have good confidence, some lower
            base_confidence = 0.88
            if len(clean_word) <= 2:  # Short words often less confident
                confidence_adjustment = -0.15
            elif len(clean_word) >= 8:  # Long words might be less confident
                confidence_adjustment = -0.08
            elif clean_word.lower() in ['the', 'and', 'is', 'are', 'of', 'to']:  # Common words high confidence
                confidence_adjustment = 0.08
            else:
                confidence_adjustment = (i % 11 - 5) * 0.02  # Some variation
            
            confidence = max(0.5, min(0.98, base_confidence + confidence_adjustment))
            
            word_timestamps.append(WordTimestamp(
                word=clean_word,
                start_time=start_time,
                end_time=end_time,
                confidence=confidence
            ))
        
        return word_timestamps
    
    def demo_segment_timestamps(self):
        """Demonstrate segment-level timestamp generation"""
        print("\n📑 DEMO: Segment Timestamps")
        print("=" * 40)
        
        try:
            audio_path = self.find_available_audio_file() or "simulation_mode"
            
            # Test speaker-based segmentation
            print("🎤 Testing speaker-based segmentation...")
            speakers = ["John Smith", "Sarah Johnson", "Michael Chen"]
            
            if audio_path == "simulation_mode":
                speaker_segments = self.create_simulated_segments("speaker", speakers)
            else:
                speaker_segments = self.ts_system.generate_segment_timestamps(
                    audio_path=audio_path,
                    transcript=self.demo_transcript,
                    content_id=f"{self.demo_content_id}_speakers",
                    speakers=speakers
                )
                
                if not speaker_segments:
                    speaker_segments = self.create_simulated_segments("speaker", speakers)
            
            if speaker_segments:
                print(f"✅ Generated {len(speaker_segments)} speaker segments")
                
                for i, segment in enumerate(speaker_segments[:3]):
                    print(f"  {i+1}. {segment.segment_type} ({segment.speaker_id})")
                    print(f"     Time: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
                    print(f"     Content: {segment.content[:50]}...")
                    print(f"     Confidence: {segment.confidence:.2f}")
            
            # Test topic-based segmentation
            print("\n📚 Testing topic-based segmentation...")
            
            if audio_path == "simulation_mode":
                topic_segments = self.create_simulated_segments("topic")
            else:
                topic_segments = self.ts_system.generate_segment_timestamps(
                    audio_path=audio_path,
                    transcript=self.demo_transcript,
                    content_id=f"{self.demo_content_id}_topics"
                )
                
                if not topic_segments:
                    topic_segments = self.create_simulated_segments("topic")
            
            if topic_segments:
                print(f"✅ Generated {len(topic_segments)} topic segments")
                
                for i, segment in enumerate(topic_segments[:3]):
                    print(f"  {i+1}. {segment.segment_type} - {segment.topic}")
                    print(f"     Time: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
                    print(f"     Duration: {segment.duration():.2f}s")
                    print(f"     Content: {segment.content[:50]}...")
                
                # Store for later use
                self.stored_segments = topic_segments
            
            print("\n✅ Segment timestamp generation demo completed")
            
        except Exception as e:
            logger.error(f"Segment timestamp demo error: {e}")
            print(f"❌ Segment timestamp demo failed: {e}")
    
    def create_simulated_segments(self, segment_type, speakers=None):
        """Create simulated segments for demo purposes"""
        sentences = self.demo_transcript.split('.')
        segments = []
        
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            # Estimate duration based on sentence length
            duration = len(sentence.split()) * 0.4  # ~0.4 seconds per word
            
            start_time = current_time
            end_time = current_time + duration
            current_time = end_time + 0.5  # Pause between sentences
            
            if segment_type == "speaker" and speakers:
                speaker_id = speakers[i % len(speakers)]
                topic = None
            else:
                speaker_id = None
                topic = f"Topic {i + 1}"
            
            segment_id = f"{self.demo_content_id}_{segment_type}_{i}"
            
            segments.append(SegmentTimestamp(
                id=segment_id,
                start_time=start_time,
                end_time=end_time,
                segment_type=segment_type,
                content=sentence.strip(),
                speaker_id=speaker_id,
                topic=topic,
                confidence=0.85
            ))
        
        return segments
    
    def demo_time_codes(self):
        """Demonstrate time code generation"""
        print("\n🕐 DEMO: Time Code Generation")
        print("=" * 40)
        
        try:
            # Use simulated segments if we don't have real ones
            if not self.stored_segments:
                self.stored_segments = self.create_simulated_segments("topic")
            
            # Create sample bookmarks
            sample_bookmarks = [
                Bookmark(
                    id="bookmark_1",
                    timestamp=10.5,
                    title="Key Financial Results",
                    description="Discussion of Q4 revenue figures",
                    tags=["finance", "results"]
                ),
                Bookmark(
                    id="bookmark_2",
                    timestamp=25.0,
                    title="Expansion Plans",
                    description="Details about new office locations",
                    tags=["expansion", "growth"]
                )
            ]
            
            # Generate time codes
            time_codes = self.ts_system.create_time_codes(
                content_id=self.demo_content_id,
                segments=self.stored_segments[:3],  # Use first 3 segments
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
            # Use simulated word timestamps if we don't have real ones
            if not self.stored_word_timestamps:
                self.stored_word_timestamps = self.create_simulated_word_timestamps()
            
            # Create clickable transcript
            transcript_segments = self.ts_system.create_clickable_transcript(
                content_id=self.demo_content_id,
                transcript=self.demo_transcript,
                word_timestamps=self.stored_word_timestamps
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
                    "title": "CEO Introduction",
                    "description": "John Smith introduces the quarterly meeting",
                    "tags": ["introduction", "ceo"]
                },
                {
                    "timestamp": 28.0,
                    "title": "Financial Results",
                    "description": "Q4 revenue and growth figures presentation",
                    "tags": ["finance", "results", "q4"]
                },
                {
                    "timestamp": 45.5,
                    "title": "Expansion Update",
                    "description": "New office locations and hiring plans",
                    "tags": ["expansion", "hiring", "growth"]
                },
                {
                    "timestamp": 62.0,
                    "title": "Partnership Discussion",
                    "description": "Microsoft and Google partnership details",
                    "tags": ["partnerships", "microsoft", "google"]
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
            # Use simulated word timestamps if we don't have real ones
            if not self.stored_word_timestamps:
                self.stored_word_timestamps = self.create_simulated_word_timestamps()
            
            print("📈 Generating comprehensive analytics insights...")
            
            # Use the improved quality metrics system
            quality_metrics = self.ts_system.calculate_quality_metrics(
                self.stored_word_timestamps, 
                self.demo_content_id
            )
            
            metrics = quality_metrics['metrics']
            
            print(f"📊 Word-level analytics:")
            print(f"   Total words: {metrics['total_words']}")
            print(f"   Total duration: {metrics['total_duration']:.2f} seconds")
            print(f"   Average confidence: {metrics['avg_confidence']:.3f}")
            print(f"   Words per minute: {metrics['words_per_minute']:.1f}")
            
            # Confidence distribution
            conf_dist = metrics['confidence_distribution']
            total_words = metrics['total_words']
            
            print(f"\n🎯 Confidence distribution:")
            print(f"   High (≥0.9): {conf_dist['high']} words ({conf_dist['high']/total_words*100:.1f}%)")
            print(f"   Medium (0.7-0.9): {conf_dist['medium']} words ({conf_dist['medium']/total_words*100:.1f}%)")
            print(f"   Low (<0.7): {conf_dist['low']} words ({conf_dist['low']/total_words*100:.1f}%)")
            
            # Speaking pattern analysis
            word_durations = [float(w.duration()) for w in self.stored_word_timestamps]
            avg_word_duration = sum(word_durations) / len(word_durations)
            
            print(f"\n🗣️ Speaking pattern analysis:")
            print(f"   Average word duration: {avg_word_duration:.3f} seconds")
            print(f"   Longest word: {max(word_durations):.3f} seconds")
            print(f"   Shortest word: {min(word_durations):.3f} seconds")
            print(f"   Duration consistency: {metrics['duration_consistency']:.3f}")
            
            # Advanced quality metrics
            print(f"\n📈 Advanced quality metrics:")
            print(f"   Precision score: {metrics['precision_score']:.3f}")
            print(f"   Rate score: {metrics['rate_score']:.3f}")
            print(f"   Overall quality components:")
            print(f"     • Confidence: {metrics['avg_confidence']:.3f} (40% weight)")
            print(f"     • Speaking rate: {metrics['rate_score']:.3f} (25% weight)")
            print(f"     • Precision: {metrics['precision_score']:.3f} (20% weight)")
            print(f"     • Consistency: {metrics['duration_consistency']:.3f} (15% weight)")
            
            # Overall quality assessment
            print(f"\n⭐ Overall quality assessment:")
            print(f"   Quality score: {float(quality_metrics['overall_score']):.3f}/1.0")
            print(f"   Quality rating: {quality_metrics['rating']}")
            
            # Detailed recommendations
            print(f"\n💡 Detailed recommendations:")
            if quality_metrics['recommendations']:
                for i, rec in enumerate(quality_metrics['recommendations'], 1):
                    print(f"   {i}. {rec}")
            else:
                print("   ✅ No specific recommendations - quality is good!")
            
            # Quality improvement tips
            print(f"\n🔧 Quality improvement tips:")
            print("   • Use high-quality audio recording equipment")
            print("   • Record in a quiet environment with minimal background noise")
            print("   • Maintain consistent speaking pace (120-180 words per minute)")
            print("   • Ensure clear pronunciation and avoid mumbling")
            print("   • Use proper microphone positioning (6-8 inches from mouth)")
            
            print("\n✅ Analytics and insights demo completed")
            
        except Exception as e:
            import traceback
            logger.error(f"Analytics demo error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
    print("🎬 COMPREHENSIVE TIMESTAMPING SYSTEM DEMO (FIXED)")
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