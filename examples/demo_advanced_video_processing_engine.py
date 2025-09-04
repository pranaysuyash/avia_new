"""
Demo Script for Advanced Video Processing Engine
Task 3: Advanced Media Processing Pipeline

Demonstrates advanced video processing capabilities including scene detection,
keyframe extraction, object recognition, and intelligent B-roll suggestions.
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path
import tempfile
import cv2
import numpy as np
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from advanced_video_processing_engine import (
        AdvancedVideoProcessingEngine, VideoMetadata, SceneInfo, 
        KeyFrame, ObjectDetection, BRollSuggestion, ProcessingStrategy
    )
    ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Advanced Video Processing Engine not available: {e}")
    ENGINE_AVAILABLE = False

def create_demo_video(output_path: str, duration_seconds: int = 30) -> str:
    """Create a demo video for testing"""
    print(f"🎬 Creating demo video: {output_path}")
    
    # Video properties
    fps = 30
    width, height = 640, 480
    total_frames = duration_seconds * fps
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    try:
        for frame_num in range(total_frames):
            # Create different scenes with varying characteristics
            scene_progress = frame_num / total_frames
            
            if scene_progress < 0.3:
                # Scene 1: Static blue background with moving white circle
                frame = np.full((height, width, 3), (255, 100, 100), dtype=np.uint8)  # Light blue
                center_x = int(width * 0.2 + (width * 0.6) * (scene_progress / 0.3))
                cv2.circle(frame, (center_x, height // 2), 30, (255, 255, 255), -1)
                
                # Add some text
                cv2.putText(frame, "Scene 1: Moving Object", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                
            elif scene_progress < 0.6:
                # Scene 2: Dynamic green background with multiple objects
                frame = np.full((height, width, 3), (100, 255, 100), dtype=np.uint8)  # Light green
                
                # Multiple moving objects
                for i in range(3):
                    x = int(width * (0.2 + i * 0.3) + 50 * np.sin(frame_num * 0.1 + i))
                    y = int(height * (0.3 + i * 0.2) + 30 * np.cos(frame_num * 0.1 + i))
                    color = [(255, 0, 0), (0, 255, 0), (0, 0, 255)][i]
                    cv2.circle(frame, (x, y), 20, color, -1)
                
                cv2.putText(frame, "Scene 2: Multiple Objects", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                
            else:
                # Scene 3: Red background with complex patterns
                frame = np.full((height, width, 3), (100, 100, 255), dtype=np.uint8)  # Light red
                
                # Create complex pattern
                for i in range(0, width, 20):
                    for j in range(0, height, 20):
                        if (i + j + frame_num) % 40 < 20:
                            cv2.rectangle(frame, (i, j), (i+10, j+10), (255, 255, 255), -1)
                
                # Add face-like pattern
                face_x, face_y = width // 2, height // 2
                cv2.circle(frame, (face_x, face_y), 60, (255, 255, 255), 2)  # Face outline
                cv2.circle(frame, (face_x - 20, face_y - 10), 5, (0, 0, 0), -1)  # Left eye
                cv2.circle(frame, (face_x + 20, face_y - 10), 5, (0, 0, 0), -1)  # Right eye
                cv2.ellipse(frame, (face_x, face_y + 20), (15, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
                
                cv2.putText(frame, "Scene 3: Complex Pattern + Face", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Add frame number for reference
            cv2.putText(frame, f"Frame: {frame_num}", (width - 150, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Add some noise for realism
            noise = np.random.randint(-20, 20, frame.shape, dtype=np.int16)
            frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            out.write(frame)
        
        print(f"✅ Demo video created successfully: {total_frames} frames, {duration_seconds}s")
        return output_path
        
    finally:
        out.release()

async def demo_metadata_extraction(engine: AdvancedVideoProcessingEngine, video_path: str):
    """Demonstrate video metadata extraction"""
    print("\n" + "="*60)
    print("📋 METADATA EXTRACTION DEMO")
    print("="*60)
    
    start_time = time.time()
    metadata = await engine.get_video_metadata(video_path)
    extraction_time = time.time() - start_time
    
    print(f"⏱️  Extraction time: {extraction_time:.2f}s")
    print(f"📊 Video Metadata:")
    print(f"   Duration: {metadata.duration:.1f}s")
    print(f"   Resolution: {metadata.width}x{metadata.height}")
    print(f"   FPS: {metadata.fps:.2f}")
    print(f"   Total Frames: {metadata.total_frames}")
    print(f"   Codec: {metadata.codec}")
    print(f"   File Size: {metadata.file_size / (1024*1024):.1f} MB")
    print(f"   Aspect Ratio: {metadata.aspect_ratio}")
    print(f"   Has Audio: {metadata.has_audio}")
    print(f"   Quality Score: {metadata.quality_score:.3f}")
    print(f"   Complexity Score: {metadata.complexity_score:.3f}")
    
    return metadata

async def demo_keyframe_extraction(engine: AdvancedVideoProcessingEngine, 
                                 video_path: str, metadata: VideoMetadata):
    """Demonstrate keyframe extraction"""
    print("\n" + "="*60)
    print("🖼️  KEYFRAME EXTRACTION DEMO")
    print("="*60)
    
    start_time = time.time()
    keyframes = engine._extract_keyframes_advanced(video_path, metadata)
    extraction_time = time.time() - start_time
    
    print(f"⏱️  Extraction time: {extraction_time:.2f}s")
    print(f"🎯 Extracted {len(keyframes)} keyframes")
    
    # Show details of first few keyframes
    for i, keyframe in enumerate(keyframes[:5]):
        print(f"\n   Keyframe {i+1}:")
        print(f"     Frame: {keyframe.frame_number}")
        print(f"     Timestamp: {keyframe.timestamp:.2f}s")
        print(f"     Confidence: {keyframe.confidence:.3f}")
        print(f"     Visual Hash: {keyframe.visual_hash[:16]}...")
        print(f"     Objects: {keyframe.objects_detected}")
        
        if keyframe.quality_metrics:
            print(f"     Quality Metrics:")
            for metric, value in keyframe.quality_metrics.items():
                print(f"       {metric}: {value:.3f}")
    
    if len(keyframes) > 5:
        print(f"   ... and {len(keyframes) - 5} more keyframes")
    
    return keyframes

async def demo_scene_detection(engine: AdvancedVideoProcessingEngine, 
                             video_path: str, metadata: VideoMetadata):
    """Demonstrate scene detection"""
    print("\n" + "="*60)
    print("🎬 SCENE DETECTION DEMO")
    print("="*60)
    
    # Test both basic and advanced scene detection
    print("🔍 Running basic scene detection...")
    start_time = time.time()
    basic_scenes = engine._detect_scenes_basic(video_path, metadata)
    basic_time = time.time() - start_time
    
    print("🔍 Running advanced scene detection...")
    start_time = time.time()
    advanced_scenes = engine._detect_scenes_advanced(video_path, metadata)
    advanced_time = time.time() - start_time
    
    print(f"\n📊 Scene Detection Results:")
    print(f"   Basic Detection: {len(basic_scenes)} scenes in {basic_time:.2f}s")
    print(f"   Advanced Detection: {len(advanced_scenes)} scenes in {advanced_time:.2f}s")
    
    # Show advanced scene details
    print(f"\n🎯 Advanced Scene Analysis:")
    for i, scene in enumerate(advanced_scenes):
        duration = scene.end_time - scene.start_time
        print(f"\n   Scene {i+1}:")
        print(f"     Time: {scene.start_time:.1f}s - {scene.end_time:.1f}s ({duration:.1f}s)")
        print(f"     Type: {scene.scene_type.value}")
        print(f"     Confidence: {scene.confidence:.3f}")
        print(f"     Motion Intensity: {scene.motion_intensity:.3f}")
        print(f"     Visual Complexity: {scene.visual_complexity:.3f}")
        if scene.dominant_colors:
            colors_str = ", ".join([f"RGB{color}" for color in scene.dominant_colors[:3]])
            print(f"     Dominant Colors: {colors_str}")
    
    return advanced_scenes

async def demo_object_detection(engine: AdvancedVideoProcessingEngine, 
                              video_path: str, metadata: VideoMetadata):
    """Demonstrate object detection"""
    print("\n" + "="*60)
    print("👁️  OBJECT DETECTION DEMO")
    print("="*60)
    
    # Test both basic and advanced object detection
    print("🔍 Running basic object detection...")
    start_time = time.time()
    basic_objects = engine._detect_objects_basic(video_path, metadata)
    basic_time = time.time() - start_time
    
    print("🔍 Running advanced object detection...")
    start_time = time.time()
    advanced_objects = engine._detect_objects_advanced(video_path, metadata)
    advanced_time = time.time() - start_time
    
    print(f"\n📊 Object Detection Results:")
    print(f"   Basic Detection: {len(basic_objects)} objects in {basic_time:.2f}s")
    print(f"   Advanced Detection: {len(advanced_objects)} objects in {advanced_time:.2f}s")
    
    # Analyze object types
    object_types = {}
    for obj in advanced_objects:
        obj_type = obj.class_name
        if obj_type not in object_types:
            object_types[obj_type] = []
        object_types[obj_type].append(obj)
    
    print(f"\n🎯 Object Analysis:")
    for obj_type, objects in object_types.items():
        print(f"   {obj_type.title()}: {len(objects)} detections")
        
        # Show details of first few detections
        for i, obj in enumerate(objects[:3]):
            print(f"     Detection {i+1}:")
            print(f"       Time: {obj.timestamp:.2f}s")
            print(f"       Confidence: {obj.confidence:.3f}")
            print(f"       Bounding Box: {obj.bbox}")
            if obj.tracking_id:
                print(f"       Tracking ID: {obj.tracking_id}")
        
        if len(objects) > 3:
            print(f"     ... and {len(objects) - 3} more detections")
    
    return advanced_objects

async def demo_broll_suggestions(engine: AdvancedVideoProcessingEngine,
                               keyframes: List[KeyFrame], scenes: List[SceneInfo],
                               objects: List[ObjectDetection], metadata: VideoMetadata):
    """Demonstrate B-roll suggestions"""
    print("\n" + "="*60)
    print("🎬 B-ROLL SUGGESTIONS DEMO")
    print("="*60)
    
    # Create mock content analysis
    from unittest.mock import Mock
    content_analysis = Mock()
    content_analysis.duration_seconds = metadata.duration
    content_analysis.complexity = "moderate"
    
    start_time = time.time()
    suggestions = await engine._generate_intelligent_broll_suggestions(
        keyframes, scenes, objects, content_analysis
    )
    generation_time = time.time() - start_time
    
    print(f"⏱️  Generation time: {generation_time:.2f}s")
    print(f"💡 Generated {len(suggestions)} B-roll suggestions")
    
    # Group suggestions by type
    suggestion_types = {}
    for suggestion in suggestions:
        stype = suggestion.suggestion_type
        if stype not in suggestion_types:
            suggestion_types[stype] = []
        suggestion_types[stype].append(suggestion)
    
    print(f"\n🎯 Suggestion Analysis:")
    for stype, type_suggestions in suggestion_types.items():
        print(f"\n   {stype.replace('_', ' ').title()}: {len(type_suggestions)} suggestions")
        
        # Show details of suggestions
        for i, suggestion in enumerate(type_suggestions):
            print(f"     Suggestion {i+1}:")
            print(f"       Time: {suggestion.timestamp:.1f}s")
            print(f"       Duration: {suggestion.duration:.1f}s")
            print(f"       Confidence: {suggestion.confidence:.3f}")
            print(f"       Priority: {suggestion.priority}")
            print(f"       Description: {suggestion.description}")
            if suggestion.keywords:
                print(f"       Keywords: {', '.join(suggestion.keywords)}")
    
    # Show timeline of suggestions
    print(f"\n📅 B-roll Timeline:")
    sorted_suggestions = sorted(suggestions, key=lambda x: x.timestamp)
    for suggestion in sorted_suggestions:
        print(f"   {suggestion.timestamp:6.1f}s: {suggestion.suggestion_type.replace('_', ' ').title()}")
        print(f"            {suggestion.description}")
    
    return suggestions

async def demo_comprehensive_processing(engine: AdvancedVideoProcessingEngine, video_path: str):
    """Demonstrate comprehensive video processing"""
    print("\n" + "="*60)
    print("🚀 COMPREHENSIVE PROCESSING DEMO")
    print("="*60)
    
    processing_options = {
        'extract_keyframes': True,
        'detect_scenes': True,
        'detect_objects': True,
        'suggest_broll': True,
        'enhance_quality': False  # Skip for demo speed
    }
    
    print("🎬 Starting comprehensive video processing...")
    start_time = time.time()
    
    results = await engine.process_video_comprehensive(video_path, processing_options)
    
    total_time = time.time() - start_time
    
    print(f"\n📊 Comprehensive Processing Results:")
    print(f"   Success: {results['success']}")
    print(f"   Total Processing Time: {total_time:.2f}s")
    print(f"   Strategy Used: {results.get('processing_strategy', 'N/A')}")
    
    if results['success']:
        print(f"   Keyframes: {len(results.get('keyframes', []))}")
        print(f"   Scenes: {len(results.get('scenes', []))}")
        print(f"   Objects: {len(results.get('objects', []))}")
        print(f"   B-roll Suggestions: {len(results.get('broll_suggestions', []))}")
        
        if results.get('errors'):
            print(f"   Warnings: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"     - {error}")
    else:
        print(f"   Error: {results.get('error', 'Unknown error')}")
    
    return results

async def demo_performance_comparison(engine: AdvancedVideoProcessingEngine, video_path: str):
    """Demonstrate performance comparison between strategies"""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE COMPARISON DEMO")
    print("="*60)
    
    strategies = ['basic', 'enhanced', 'professional']
    results = {}
    
    for strategy in strategies:
        print(f"\n🔍 Testing {strategy} strategy...")
        
        options = {
            'extract_keyframes': True,
            'detect_scenes': True,
            'detect_objects': True,
            'suggest_broll': False,  # Skip for speed comparison
            'processing_strategy': strategy
        }
        
        start_time = time.time()
        result = await engine.process_video_comprehensive(video_path, options)
        processing_time = time.time() - start_time
        
        results[strategy] = {
            'time': processing_time,
            'success': result['success'],
            'keyframes': len(result.get('keyframes', [])),
            'scenes': len(result.get('scenes', [])),
            'objects': len(result.get('objects', []))
        }
        
        print(f"   Time: {processing_time:.2f}s")
        print(f"   Results: {results[strategy]['keyframes']} keyframes, "
              f"{results[strategy]['scenes']} scenes, {results[strategy]['objects']} objects")
    
    print(f"\n📊 Performance Summary:")
    print(f"{'Strategy':<12} {'Time (s)':<10} {'Keyframes':<10} {'Scenes':<8} {'Objects':<8}")
    print("-" * 50)
    
    for strategy, data in results.items():
        print(f"{strategy:<12} {data['time']:<10.2f} {data['keyframes']:<10} "
              f"{data['scenes']:<8} {data['objects']:<8}")
    
    return results

def save_demo_results(results: Dict[str, Any], output_file: str):
    """Save demo results to JSON file"""
    print(f"\n💾 Saving demo results to: {output_file}")
    
    # Convert results to JSON-serializable format
    json_results = {}
    
    for key, value in results.items():
        if hasattr(value, '__dict__'):
            # Convert dataclass objects to dictionaries
            json_results[key] = value.__dict__
        elif isinstance(value, list):
            # Convert list of objects
            json_results[key] = []
            for item in value:
                if hasattr(item, '__dict__'):
                    json_results[key].append(item.__dict__)
                else:
                    json_results[key].append(str(item))
        else:
            json_results[key] = str(value)
    
    try:
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        print(f"✅ Results saved successfully")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")

async def main():
    """Main demo function"""
    print("🎬 Advanced Video Processing Engine Demo")
    print("=" * 60)
    
    if not ENGINE_AVAILABLE:
        print("❌ Advanced Video Processing Engine is not available")
        print("   Please ensure all dependencies are installed")
        return
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, "demo_video.mp4")
    results_path = os.path.join(temp_dir, "demo_results.json")
    
    try:
        # Create demo video
        create_demo_video(video_path, duration_seconds=20)
        
        # Initialize engine
        print("\n🚀 Initializing Advanced Video Processing Engine...")
        engine = AdvancedVideoProcessingEngine(temp_dir=temp_dir, max_workers=2)
        
        # Run demos
        demo_results = {}
        
        # 1. Metadata extraction
        metadata = await demo_metadata_extraction(engine, video_path)
        demo_results['metadata'] = metadata
        
        # 2. Keyframe extraction
        keyframes = await demo_keyframe_extraction(engine, video_path, metadata)
        demo_results['keyframes'] = keyframes
        
        # 3. Scene detection
        scenes = await demo_scene_detection(engine, video_path, metadata)
        demo_results['scenes'] = scenes
        
        # 4. Object detection
        objects = await demo_object_detection(engine, video_path, metadata)
        demo_results['objects'] = objects
        
        # 5. B-roll suggestions
        suggestions = await demo_broll_suggestions(engine, keyframes, scenes, objects, metadata)
        demo_results['broll_suggestions'] = suggestions
        
        # 6. Comprehensive processing
        comprehensive_results = await demo_comprehensive_processing(engine, video_path)
        demo_results['comprehensive'] = comprehensive_results
        
        # 7. Performance comparison
        performance_results = await demo_performance_comparison(engine, video_path)
        demo_results['performance'] = performance_results
        
        # Save results
        save_demo_results(demo_results, results_path)
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"📁 Demo files created in: {temp_dir}")
        print(f"🎬 Demo video: {video_path}")
        print(f"📊 Results file: {results_path}")
        
        print(f"\n📈 Summary Statistics:")
        print(f"   Video Duration: {metadata.duration:.1f}s")
        print(f"   Keyframes Extracted: {len(keyframes)}")
        print(f"   Scenes Detected: {len(scenes)}")
        print(f"   Objects Found: {len(objects)}")
        print(f"   B-roll Suggestions: {len(suggestions)}")
        
        # Cleanup engine
        await engine.cleanup()
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Note: In a real scenario, you might want to clean up temp files
        # For demo purposes, we'll leave them for inspection
        print(f"\n📝 Demo files preserved in: {temp_dir}")
        print("   You can inspect the generated video and results")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())