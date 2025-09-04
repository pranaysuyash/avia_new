#!/usr/bin/env python3
"""
Intelligent Content Search Demo
Demonstrates visual scene search, audio pattern recognition, and semantic search
"""

import os
import json
import numpy as np
import cv2
from datetime import datetime
import tempfile
from intelligent_content_search import (
    IntelligentContentSearchSystem, VisualScene, AudioPattern
)

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}\n")

def print_scene(scene: VisualScene, index: int):
    """Print a visual scene"""
    print(f"\n📸 Scene #{index}")
    print(f"   Timestamp: {scene.timestamp:.1f}s (frame {scene.frame_number})")
    print(f"   Description: {scene.description}")
    print(f"   Objects: {', '.join(scene.objects)}")
    print(f"   Confidence: {scene.confidence:.1%}")

def print_pattern(pattern: AudioPattern, index: int):
    """Print an audio pattern"""
    pattern_emoji = {
        'music': '🎵',
        'speech': '🗣️',
        'applause': '👏',
        'silence': '🤫',
        'noise': '🔊'
    }
    
    emoji = pattern_emoji.get(pattern.pattern_type, '🔊')
    
    print(f"\n{emoji} Audio Pattern #{index}")
    print(f"   Type: {pattern.pattern_type}")
    print(f"   Time: {pattern.start_time:.1f}s - {pattern.end_time:.1f}s")
    print(f"   Duration: {pattern.end_time - pattern.start_time:.1f}s")
    print(f"   Confidence: {pattern.confidence:.1%}")

def create_mock_video_data():
    """Create mock video data for demonstration"""
    print("🎬 Creating mock video data...")
    
    # Create a simple video file (3 seconds, 30 fps)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_video.close()
    
    out = cv2.VideoWriter(temp_video.name, fourcc, 30.0, (640, 480))
    
    # Generate frames with different scenes
    scenes_data = [
        {"text": "Person walking", "color": (255, 0, 0)},      # Red scene
        {"text": "Car on street", "color": (0, 255, 0)},       # Green scene
        {"text": "Building entrance", "color": (0, 0, 255)}    # Blue scene
    ]
    
    for i in range(90):  # 3 seconds at 30 fps
        scene_idx = i // 30  # Change scene every second
        scene = scenes_data[scene_idx]
        
        # Create frame
        frame = np.full((480, 640, 3), scene["color"], dtype=np.uint8)
        
        # Add text
        cv2.putText(frame, scene["text"], (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(frame, f"Frame {i}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print(f"   ✅ Created mock video: {temp_video.name}")
    
    return temp_video.name

def demo_video_processing():
    """Demonstrate video processing"""
    print_header("Video Processing Demo")
    
    # Initialize system
    search_system = IntelligentContentSearchSystem()
    print("✅ Initialized Intelligent Content Search System")
    
    # Create mock video
    video_path = create_mock_video_data()
    
    try:
        # Process video
        print("\n🔄 Processing video...")
        results = search_system.process_video_file(video_path, sample_interval=0.5)
        
        print(f"\n✅ Processing complete!")
        print(f"   Duration: {results['metadata']['duration']:.1f}s")
        print(f"   FPS: {results['metadata']['fps']}")
        print(f"   Scenes analyzed: {results['metadata']['scenes_analyzed']}")
        print(f"   Audio patterns: {results['metadata']['audio_patterns_found']}")
        
        # Show some scenes
        if results['visual_scenes']:
            print("\n📸 Sample Visual Scenes:")
            for i, scene in enumerate(results['visual_scenes'][:3], 1):
                print_scene(scene, i)
        
        # Show audio patterns
        if results['audio_patterns']:
            print("\n🎵 Audio Patterns Found:")
            for i, pattern in enumerate(results['audio_patterns'][:3], 1):
                print_pattern(pattern, i)
        
        return search_system, video_path
        
    except Exception as e:
        print(f"\n❌ Error processing video: {e}")
        return search_system, None
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)

def demo_visual_search(search_system):
    """Demonstrate visual scene search"""
    print_header("Visual Scene Search Demo")
    
    # Example search queries
    queries = [
        "person walking",
        "car on street",
        "building entrance",
        "red background",
        "someone running"  # Should not find results
    ]
    
    for query in queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        results = search_system.search_visual_scenes(query, top_k=3)
        
        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n   Result #{i}:")
                print(f"   - File: {os.path.basename(result.file_path)}")
                print(f"   - Time: {result.timestamp:.1f}s")
                print(f"   - Description: {result.description}")
                print(f"   - Relevance: {result.relevance_score:.1%}")
        else:
            print("   ❌ No results found")

def demo_audio_pattern_search(search_system):
    """Demonstrate audio pattern search"""
    print_header("Audio Pattern Search Demo")
    
    # Search for different pattern types
    pattern_types = ['music', 'speech', 'silence', None]  # None = all patterns
    
    for pattern_type in pattern_types:
        type_name = pattern_type or "all patterns"
        print(f"\n🔍 Searching for: {type_name}")
        
        results = search_system.search_audio_patterns(pattern_type=pattern_type)
        
        if results:
            print(f"   Found {len(results)} results:")
            
            # Group by pattern type
            pattern_counts = {}
            for result in results:
                # Extract pattern type from description
                ptype = result.description.split()[0]
                pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1
            
            for ptype, count in pattern_counts.items():
                print(f"   - {ptype}: {count} occurrences")
        else:
            print("   ❌ No patterns found")

def demo_timeline_view(search_system, video_path):
    """Demonstrate timeline view"""
    print_header("Video Timeline View Demo")
    
    if not video_path:
        print("❌ No video available for timeline demo")
        return
    
    timeline = search_system.get_video_timeline(video_path)
    
    print(f"📹 Timeline for: {os.path.basename(video_path)}")
    print(f"   Visual events: {len(timeline['visual_events'])}")
    print(f"   Audio events: {len(timeline['audio_events'])}")
    
    # Show combined timeline
    print("\n🎬 Combined Timeline:")
    
    for event in timeline['combined_timeline'][:10]:  # Show first 10 events
        if event['type'] == 'visual':
            print(f"\n   📸 {event['timestamp']:.1f}s - Visual Scene")
            print(f"      Description: {event['description']}")
            if event['objects']:
                print(f"      Objects: {', '.join(event['objects'])}")
        else:  # audio
            print(f"\n   🎵 {event['timestamp']:.1f}s - Audio Pattern")
            print(f"      Type: {event['pattern_type']}")
            print(f"      Duration: {event['end_time'] - event['timestamp']:.1f}s")

def demo_statistics(search_system):
    """Demonstrate system statistics"""
    print_header("System Statistics Demo")
    
    stats = search_system.get_statistics()
    
    print("📊 Content Statistics:")
    print(f"   Total visual scenes: {stats['total_scenes']}")
    print(f"   Total audio patterns: {stats['total_patterns']}")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Total searches: {stats['total_searches']}")
    
    if stats['pattern_distribution']:
        print("\n🎵 Audio Pattern Distribution:")
        for pattern_type, count in stats['pattern_distribution'].items():
            percentage = (count / stats['total_patterns'] * 100) if stats['total_patterns'] > 0 else 0
            print(f"   - {pattern_type}: {count} ({percentage:.1f}%)")

def demo_advanced_search():
    """Demonstrate advanced search scenarios"""
    print_header("Advanced Search Scenarios")
    
    # Initialize a fresh system for this demo
    search_system = IntelligentContentSearchSystem()
    
    # Add diverse content for demonstration
    print("📚 Adding sample content...")
    
    # Add visual scenes with specific scenarios
    scenes = [
        VisualScene(
            scene_id="adv_001",
            file_path="meeting_recording.mp4",
            timestamp=30.5,
            frame_number=915,
            description="Two people shaking hands in conference room",
            objects=["person", "person", "conference table"],
            confidence=0.92,
            embedding=np.random.randn(384).astype(np.float32)
        ),
        VisualScene(
            scene_id="adv_002",
            file_path="security_footage.mp4",
            timestamp=120.3,
            frame_number=3609,
            description="Woman in red dress getting out of black sedan",
            objects=["person", "car", "building"],
            confidence=0.88,
            embedding=np.random.randn(384).astype(np.float32)
        ),
        VisualScene(
            scene_id="adv_003",
            file_path="presentation.mp4",
            timestamp=45.0,
            frame_number=1350,
            description="Person pointing at whiteboard with charts",
            objects=["person", "whiteboard", "chart"],
            confidence=0.85,
            embedding=np.random.randn(384).astype(np.float32)
        )
    ]
    
    for scene in scenes:
        search_system._save_visual_scene(scene)
    
    print("   ✅ Added 3 visual scenes")
    
    # Demonstrate specific searches
    advanced_queries = [
        "woman getting out of car",
        "people meeting in conference room",
        "presentation with charts",
        "red dress black car"
    ]
    
    print("\n🔍 Advanced Search Queries:")
    
    for query in advanced_queries:
        print(f"\n   Query: '{query}'")
        results = search_system.search_visual_scenes(query, top_k=2)
        
        if results:
            best_result = results[0]
            print(f"   ✅ Best match:")
            print(f"      File: {os.path.basename(best_result.file_path)}")
            print(f"      Time: {best_result.timestamp:.1f}s")
            print(f"      Scene: {best_result.description}")
            print(f"      Score: {best_result.relevance_score:.1%}")
        else:
            print("   ❌ No matches found")

def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("🔍 INTELLIGENT CONTENT SEARCH DEMO")
    print("Visual Scene Description & Audio Pattern Recognition")
    print("="*60)
    
    # Run demos
    demos = [
        ("Video Processing", demo_video_processing),
        ("Visual Search", lambda: demo_visual_search(search_system)),
        ("Audio Pattern Search", lambda: demo_audio_pattern_search(search_system)),
        ("Timeline View", lambda: demo_timeline_view(search_system, video_path)),
        ("System Statistics", lambda: demo_statistics(search_system)),
        ("Advanced Search", demo_advanced_search)
    ]
    
    # Process video first to get search system
    search_system, video_path = demo_video_processing()
    
    # Run remaining demos
    for name, demo_func in demos[1:]:
        input(f"\n⏯️  Press Enter to run {name} demo...")
        try:
            demo_func()
            print(f"\n✅ {name} demo completed successfully!")
        except Exception as e:
            print(f"\n❌ Error in {name} demo: {e}")
    
    print("\n" + "="*60)
    print("🎉 All demos completed!")
    print("="*60)

if __name__ == "__main__":
    main()