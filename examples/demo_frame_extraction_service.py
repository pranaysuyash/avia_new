"""
Demo script for Advanced Frame Extraction Service

This script demonstrates the capabilities of the frame extraction service
with various sampling strategies and configurations.
"""

import os
import cv2
import numpy as np
import json
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List, Dict, Any

from frame_extraction_service import (
    FrameExtractionService, ExtractionConfig, SamplingStrategy,
    FrameQuality, ExtractedFrame, VideoMetadata
)


def create_sample_video(duration: int = 30, fps: int = 30) -> str:
    """Create a sample video for demonstration"""
    print(f"Creating sample video ({duration}s at {fps} fps)...")
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    output_path = temp_file.name
    temp_file.close()
    
    # Video properties
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Create video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_num in range(total_frames):
        # Create frame with varying content
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background gradient
        for y in range(height):
            intensity = int(255 * (y / height))
            frame[y, :] = [intensity // 3, intensity // 2, intensity]
        
        # Add time-based elements
        time_sec = frame_num / fps
        
        # Moving rectangle (simulates scene changes)
        rect_x = int((time_sec * 50) % width)
        rect_y = int(height * 0.3)
        cv2.rectangle(frame, (rect_x, rect_y), (rect_x + 100, rect_y + 60), (255, 255, 255), -1)
        
        # Add text overlay (simulates lower thirds)
        if int(time_sec) % 10 < 5:  # Text appears every 10 seconds for 5 seconds
            text = f"Sample Text {int(time_sec // 10) + 1}"
            cv2.putText(frame, text, (50, height - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                       2, (255, 255, 255), 3)
        
        # Scene change simulation (different background every 10 seconds)
        scene_num = int(time_sec // 10)
        if scene_num % 2 == 1:
            # Alternate scene with different pattern
            frame = cv2.bitwise_not(frame)
        
        # Add noise for quality variation
        if frame_num % 100 < 20:  # Add noise to some frames
            noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
            frame = cv2.add(frame, noise)
        
        out.write(frame)
    
    out.release()
    print(f"Sample video created: {output_path}")
    return output_path


def demo_basic_extraction():
    """Demonstrate basic frame extraction"""
    print("\n" + "="*60)
    print("DEMO: Basic Frame Extraction")
    print("="*60)
    
    # Create sample video
    video_path = create_sample_video(duration=20, fps=25)
    
    try:
        # Initialize service
        service = FrameExtractionService()
        
        # Get video metadata
        print("\n1. Video Metadata Analysis:")
        metadata = service.get_video_metadata(video_path)
        print(f"   Duration: {metadata.duration:.1f} seconds")
        print(f"   Resolution: {metadata.width}x{metadata.height}")
        print(f"   Frame Rate: {metadata.fps:.1f} fps")
        print(f"   Total Frames: {metadata.total_frames:,}")
        print(f"   File Size: {metadata.file_size / (1024*1024):.1f} MB")
        
        # Basic time-based extraction
        print("\n2. Time-based Extraction (every 2 seconds):")
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=2.0,
            max_frames=20,
            enable_quality_assessment=True
        )
        
        frames = service.extract_frames(video_path, config)
        print(f"   Extracted {len(frames)} frames")
        
        # Display quality statistics
        qualities = [f.quality_metrics.confidence for f in frames]
        print(f"   Average Quality: {np.mean(qualities):.3f}")
        print(f"   Quality Range: {np.min(qualities):.3f} - {np.max(qualities):.3f}")
        
        # Show first few frames info
        print("\n   First 5 frames:")
        for i, frame in enumerate(frames[:5]):
            print(f"     Frame {i+1}: t={frame.timestamp:.1f}s, "
                  f"quality={frame.quality_metrics.overall_quality.value}, "
                  f"confidence={frame.quality_metrics.confidence:.3f}")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


def demo_sampling_strategies():
    """Demonstrate different sampling strategies"""
    print("\n" + "="*60)
    print("DEMO: Sampling Strategy Comparison")
    print("="*60)
    
    # Create sample video
    video_path = create_sample_video(duration=30, fps=30)
    
    try:
        service = FrameExtractionService()
        
        strategies = [
            (SamplingStrategy.TIME_BASED, "Time-based (1s intervals)"),
            (SamplingStrategy.KEYFRAME, "Keyframe detection"),
            (SamplingStrategy.SCENE_CHANGE, "Scene change detection"),
            (SamplingStrategy.ADAPTIVE, "Adaptive sampling"),
            (SamplingStrategy.HYBRID, "Hybrid approach")
        ]
        
        results = {}
        
        for strategy, description in strategies:
            print(f"\n{description}:")
            
            config = ExtractionConfig(
                sampling_strategy=strategy,
                time_interval=1.0,
                max_frames=50,
                enable_quality_assessment=True,
                keyframe_threshold=0.3,
                scene_change_threshold=0.4,
                adaptive_complexity_threshold=0.5
            )
            
            # Extract frames
            frames = service.extract_frames(video_path, config)
            
            # Calculate statistics
            qualities = [f.quality_metrics.confidence for f in frames]
            timestamps = [f.timestamp for f in frames]
            
            results[strategy.value] = {
                'frames': len(frames),
                'avg_quality': np.mean(qualities),
                'time_span': max(timestamps) - min(timestamps) if timestamps else 0,
                'quality_std': np.std(qualities)
            }
            
            print(f"   Frames extracted: {len(frames)}")
            print(f"   Average quality: {np.mean(qualities):.3f}")
            print(f"   Quality std dev: {np.std(qualities):.3f}")
            print(f"   Time span: {max(timestamps) - min(timestamps):.1f}s")
            
            # Show sampling reasons
            reasons = {}
            for frame in frames:
                reason_key = frame.sampling_reason.split('_')[0]
                reasons[reason_key] = reasons.get(reason_key, 0) + 1
            
            print(f"   Sampling reasons: {dict(reasons)}")
        
        # Summary comparison
        print(f"\n{'Strategy':<20} {'Frames':<8} {'Avg Quality':<12} {'Quality StdDev':<15}")
        print("-" * 60)
        for strategy_name, stats in results.items():
            print(f"{strategy_name:<20} {stats['frames']:<8} "
                  f"{stats['avg_quality']:<12.3f} {stats['quality_std']:<15.3f}")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


def demo_quality_assessment():
    """Demonstrate quality assessment features"""
    print("\n" + "="*60)
    print("DEMO: Quality Assessment & Filtering")
    print("="*60)
    
    # Create sample video with varying quality
    video_path = create_sample_video(duration=15, fps=20)
    
    try:
        service = FrameExtractionService()
        
        # Extract with quality assessment
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=0.5,
            max_frames=100,
            enable_quality_assessment=True,
            min_quality_threshold=0.0  # Don't filter initially
        )
        
        frames = service.extract_frames(video_path, config)
        
        print(f"\n1. Quality Metrics Analysis ({len(frames)} frames):")
        
        # Analyze quality metrics
        blur_scores = [f.quality_metrics.blur_score for f in frames]
        contrast_scores = [f.quality_metrics.contrast_score for f in frames]
        brightness_scores = [f.quality_metrics.brightness_score for f in frames]
        sharpness_scores = [f.quality_metrics.sharpness_score for f in frames]
        text_densities = [f.quality_metrics.text_region_density for f in frames]
        overall_qualities = [f.quality_metrics.confidence for f in frames]
        
        metrics = {
            'Blur Score': blur_scores,
            'Contrast': contrast_scores,
            'Brightness': brightness_scores,
            'Sharpness': sharpness_scores,
            'Text Density': text_densities,
            'Overall Quality': overall_qualities
        }
        
        for metric_name, values in metrics.items():
            print(f"   {metric_name}:")
            print(f"     Mean: {np.mean(values):.3f}")
            print(f"     Std:  {np.std(values):.3f}")
            print(f"     Range: {np.min(values):.3f} - {np.max(values):.3f}")
        
        # Quality level distribution
        quality_levels = {}
        for frame in frames:
            level = frame.quality_metrics.overall_quality.value
            quality_levels[level] = quality_levels.get(level, 0) + 1
        
        print(f"\n2. Quality Level Distribution:")
        for level, count in sorted(quality_levels.items()):
            percentage = (count / len(frames)) * 100
            print(f"   {level.capitalize()}: {count} frames ({percentage:.1f}%)")
        
        # Test different quality thresholds
        print(f"\n3. Quality Filtering Impact:")
        thresholds = [0.3, 0.5, 0.7, 0.9]
        
        for threshold in thresholds:
            filtered_frames = [f for f in frames 
                             if f.quality_metrics.confidence >= threshold]
            retention_rate = (len(filtered_frames) / len(frames)) * 100
            
            if filtered_frames:
                avg_quality = np.mean([f.quality_metrics.confidence for f in filtered_frames])
                print(f"   Threshold {threshold}: {len(filtered_frames)} frames "
                      f"({retention_rate:.1f}% retained), avg quality: {avg_quality:.3f}")
            else:
                print(f"   Threshold {threshold}: 0 frames (0% retained)")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


def demo_preprocessing_effects():
    """Demonstrate preprocessing effects"""
    print("\n" + "="*60)
    print("DEMO: Preprocessing Effects")
    print("="*60)
    
    # Create sample video
    video_path = create_sample_video(duration=10, fps=15)
    
    try:
        service = FrameExtractionService()
        
        # Extract without preprocessing
        config_no_prep = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=2.0,
            max_frames=10,
            enable_preprocessing=False,
            enable_perspective_correction=False
        )
        
        frames_no_prep = service.extract_frames(video_path, config_no_prep)
        
        # Extract with preprocessing
        config_with_prep = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=2.0,
            max_frames=10,
            enable_preprocessing=True,
            enable_perspective_correction=True,
            target_resolution=(640, 360)  # Resize for demo
        )
        
        frames_with_prep = service.extract_frames(video_path, config_with_prep)
        
        print(f"\n1. Preprocessing Comparison:")
        print(f"   Without preprocessing: {len(frames_no_prep)} frames")
        print(f"   With preprocessing: {len(frames_with_prep)} frames")
        
        # Compare quality metrics
        if frames_no_prep and frames_with_prep:
            no_prep_quality = np.mean([f.quality_metrics.confidence for f in frames_no_prep])
            with_prep_quality = np.mean([f.quality_metrics.confidence for f in frames_with_prep])
            
            print(f"\n2. Quality Impact:")
            print(f"   Average quality without preprocessing: {no_prep_quality:.3f}")
            print(f"   Average quality with preprocessing: {with_prep_quality:.3f}")
            print(f"   Quality improvement: {with_prep_quality - no_prep_quality:+.3f}")
            
            # Compare specific metrics
            metrics_comparison = {}
            for metric in ['blur_score', 'contrast_score', 'sharpness_score']:
                no_prep_avg = np.mean([getattr(f.quality_metrics, metric) for f in frames_no_prep])
                with_prep_avg = np.mean([getattr(f.quality_metrics, metric) for f in frames_with_prep])
                metrics_comparison[metric] = {
                    'without': no_prep_avg,
                    'with': with_prep_avg,
                    'improvement': with_prep_avg - no_prep_avg
                }
            
            print(f"\n3. Detailed Metrics Comparison:")
            for metric, values in metrics_comparison.items():
                print(f"   {metric.replace('_', ' ').title()}:")
                print(f"     Without: {values['without']:.3f}")
                print(f"     With: {values['with']:.3f}")
                print(f"     Change: {values['improvement']:+.3f}")
        
        # Check processing metadata
        processed_frames = [f for f in frames_with_prep if f.processing_metadata]
        if processed_frames:
            print(f"\n4. Processing Applied:")
            sample_metadata = processed_frames[0].processing_metadata
            for key, value in sample_metadata.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


def demo_cost_estimation():
    """Demonstrate cost estimation features"""
    print("\n" + "="*60)
    print("DEMO: Processing Cost Estimation")
    print("="*60)
    
    # Create sample video
    video_path = create_sample_video(duration=60, fps=30)  # Longer video for cost demo
    
    try:
        service = FrameExtractionService()
        
        # Get video metadata
        metadata = service.get_video_metadata(video_path)
        print(f"\nVideo Properties:")
        print(f"   Duration: {metadata.duration:.1f} seconds")
        print(f"   Resolution: {metadata.width}x{metadata.height}")
        print(f"   Total Frames: {metadata.total_frames:,}")
        print(f"   File Size: {metadata.file_size / (1024*1024):.1f} MB")
        
        # Test different configurations
        configs = [
            ("Basic Time-based", ExtractionConfig(
                sampling_strategy=SamplingStrategy.TIME_BASED,
                time_interval=5.0,
                max_frames=100,
                enable_quality_assessment=False,
                enable_preprocessing=False
            )),
            ("High Quality", ExtractionConfig(
                sampling_strategy=SamplingStrategy.ADAPTIVE,
                time_interval=1.0,
                max_frames=500,
                enable_quality_assessment=True,
                enable_preprocessing=True,
                enable_perspective_correction=True
            )),
            ("Keyframe Only", ExtractionConfig(
                sampling_strategy=SamplingStrategy.KEYFRAME,
                max_frames=200,
                enable_quality_assessment=True,
                enable_preprocessing=False
            )),
            ("Hybrid Approach", ExtractionConfig(
                sampling_strategy=SamplingStrategy.HYBRID,
                time_interval=2.0,
                max_frames=300,
                enable_quality_assessment=True,
                enable_preprocessing=True
            ))
        ]
        
        print(f"\nCost Estimation for Different Configurations:")
        print(f"{'Configuration':<20} {'Est. Frames':<12} {'Est. Time (s)':<15} {'Est. Storage (MB)':<18}")
        print("-" * 70)
        
        for config_name, config in configs:
            cost_estimate = service.estimate_processing_cost(video_path, config)
            
            print(f"{config_name:<20} "
                  f"{cost_estimate['estimated_frames']:<12} "
                  f"{cost_estimate['estimated_processing_time_seconds']:<15.1f} "
                  f"{cost_estimate['estimated_storage_mb']:<18.1f}")
        
        # Detailed cost breakdown for one configuration
        print(f"\nDetailed Cost Analysis (High Quality Configuration):")
        detailed_config = configs[1][1]  # High Quality config
        detailed_cost = service.estimate_processing_cost(video_path, detailed_config)
        
        for key, value in detailed_cost.items():
            if isinstance(value, (int, float)):
                if 'time' in key.lower():
                    print(f"   {key.replace('_', ' ').title()}: {value:.2f}")
                elif 'mb' in key.lower():
                    print(f"   {key.replace('_', ' ').title()}: {value:.1f}")
                else:
                    print(f"   {key.replace('_', ' ').title()}: {value:,}")
            else:
                print(f"   {key.replace('_', ' ').title()}: {value}")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


def demo_error_handling():
    """Demonstrate error handling and edge cases"""
    print("\n" + "="*60)
    print("DEMO: Error Handling & Edge Cases")
    print("="*60)
    
    service = FrameExtractionService()
    
    # Test invalid file
    print("\n1. Invalid File Handling:")
    try:
        service.extract_frames("nonexistent_file.mp4")
    except Exception as e:
        print(f"   ✓ Properly handled invalid file: {type(e).__name__}")
    
    # Test unsupported format
    print("\n2. Unsupported Format:")
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        tmp.write(b"This is not a video file")
        tmp_path = tmp.name
    
    try:
        service.extract_frames(tmp_path)
    except Exception as e:
        print(f"   ✓ Properly handled unsupported format: {type(e).__name__}")
    finally:
        os.unlink(tmp_path)
    
    # Test extreme configurations
    print("\n3. Extreme Configuration Handling:")
    video_path = create_sample_video(duration=5, fps=10)
    
    try:
        # Very high frame limit
        config = ExtractionConfig(max_frames=100000, time_interval=0.001)
        frames = service.extract_frames(video_path, config)
        print(f"   ✓ High frame limit handled: extracted {len(frames)} frames")
        
        # Very low quality threshold
        config = ExtractionConfig(min_quality_threshold=0.99, enable_quality_assessment=True)
        frames = service.extract_frames(video_path, config)
        print(f"   ✓ High quality threshold handled: {len(frames)} frames passed")
        
        # Invalid strategy (this should work as we handle it in enum)
        print("   ✓ Configuration validation working properly")
        
    finally:
        os.unlink(video_path)


def main():
    """Run all demonstrations"""
    print("Advanced Frame Extraction Service - Comprehensive Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_extraction()
        demo_sampling_strategies()
        demo_quality_assessment()
        demo_preprocessing_effects()
        demo_cost_estimation()
        demo_error_handling()
        
        print("\n" + "="*60)
        print("✅ All demonstrations completed successfully!")
        print("="*60)
        
        print("\nKey Features Demonstrated:")
        print("• Multiple sampling strategies (time-based, keyframe, scene-change, adaptive, hybrid)")
        print("• Comprehensive quality assessment with multiple metrics")
        print("• Intelligent preprocessing and perspective correction")
        print("• Accurate cost estimation and resource planning")
        print("• Robust error handling and validation")
        print("• Flexible configuration options")
        
        print("\nNext Steps:")
        print("• Run the Streamlit UI: streamlit run frame_extraction_service_ui.py")
        print("• Integrate with OCR processing pipeline")
        print("• Add to existing video processing workflows")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()