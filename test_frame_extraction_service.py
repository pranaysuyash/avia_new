"""
Comprehensive tests for Advanced Frame Extraction Service

This module provides thorough testing of all frame extraction functionality
including edge cases, error conditions, and performance validation.
"""

import pytest
import cv2
import numpy as np
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from frame_extraction_service import (
    FrameExtractionService, ExtractionConfig, SamplingStrategy,
    FrameQuality, ExtractedFrame, VideoMetadata, FrameQualityMetrics,
    create_extraction_config, extract_frames_from_video, get_video_info
)


class TestVideoMetadata:
    """Test VideoMetadata class"""
    
    def test_video_metadata_creation(self):
        """Test VideoMetadata creation and serialization"""
        metadata = VideoMetadata(
            duration=30.0,
            fps=25.0,
            width=1920,
            height=1080,
            total_frames=750,
            format="mp4",
            codec="h264",
            bitrate=5000000,
            file_size=50000000,
            aspect_ratio=16/9,
            color_space="yuv420p",
            has_audio=True
        )
        
        assert metadata.duration == 30.0
        assert metadata.fps == 25.0
        assert metadata.width == 1920
        assert metadata.height == 1080
        
        # Test serialization
        data_dict = metadata.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict['duration'] == 30.0
        assert data_dict['format'] == "mp4"


class TestFrameQualityMetrics:
    """Test FrameQualityMetrics class"""
    
    def test_quality_metrics_creation(self):
        """Test FrameQualityMetrics creation"""
        metrics = FrameQualityMetrics(
            blur_score=0.8,
            contrast_score=0.7,
            brightness_score=0.6,
            noise_level=0.2,
            sharpness_score=0.9,
            perspective_skew=0.1,
            text_region_density=0.3,
            overall_quality=FrameQuality.GOOD,
            confidence=0.75
        )
        
        assert metrics.blur_score == 0.8
        assert metrics.overall_quality == FrameQuality.GOOD
        assert metrics.confidence == 0.75
        
        # Test serialization
        data_dict = metrics.to_dict()
        assert data_dict['overall_quality'] == 'good'
        assert data_dict['confidence'] == 0.75


class TestExtractionConfig:
    """Test ExtractionConfig class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = ExtractionConfig()
        
        assert config.sampling_strategy == SamplingStrategy.ADAPTIVE
        assert config.time_interval == 1.0
        assert config.max_frames == 1000
        assert config.enable_quality_assessment == True
        
    def test_custom_config(self):
        """Test custom configuration"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=2.0,
            max_frames=50,
            enable_quality_assessment=False
        )
        
        assert config.sampling_strategy == SamplingStrategy.TIME_BASED
        assert config.time_interval == 2.0
        assert config.max_frames == 50
        assert config.enable_quality_assessment == False


class TestFrameExtractionService:
    """Test FrameExtractionService class"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return FrameExtractionService()
    
    @pytest.fixture
    def sample_video(self):
        """Create a sample video for testing"""
        # Create temporary video file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        video_path = temp_file.name
        temp_file.close()
        
        # Create simple test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 10.0, (640, 480))
        
        # Write 50 frames (5 seconds at 10 fps)
        for i in range(50):
            # Create frame with varying content
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add some pattern
            cv2.rectangle(frame, (i*10, i*5), (i*10+100, i*5+100), (255, 255, 255), -1)
            
            # Add text every 10 frames
            if i % 10 == 0:
                cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(frame)
        
        out.release()
        
        yield video_path
        
        # Cleanup
        if os.path.exists(video_path):
            os.unlink(video_path)
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert isinstance(service, FrameExtractionService)
        assert service.config is not None
        assert len(service.supported_formats) > 0
    
    def test_video_validation(self, service, sample_video):
        """Test video file validation"""
        # Valid video
        assert service._validate_video_file(sample_video) == True
        
        # Non-existent file
        assert service._validate_video_file("nonexistent.mp4") == False
        
        # Invalid format
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"not a video")
            tmp_path = tmp.name
        
        try:
            assert service._validate_video_file(tmp_path) == False
        finally:
            os.unlink(tmp_path)
    
    def test_metadata_extraction_opencv(self, service, sample_video):
        """Test metadata extraction using OpenCV fallback"""
        metadata = service._get_metadata_opencv(sample_video)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.width == 640
        assert metadata.height == 480
        assert metadata.fps > 0
        assert metadata.duration > 0
    
    @patch('subprocess.run')
    def test_metadata_extraction_ffprobe(self, mock_run, service, sample_video):
        """Test metadata extraction using FFprobe"""
        # Mock FFprobe output
        mock_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 640,
                    "height": 480,
                    "r_frame_rate": "10/1",
                    "nb_frames": "50"
                }
            ],
            "format": {
                "duration": "5.0",
                "bit_rate": "1000000",
                "size": "1000000",
                "format_name": "mp4"
            }
        }
        
        mock_run.return_value.stdout = json.dumps(mock_output)
        mock_run.return_value.returncode = 0
        
        metadata = service.get_video_metadata(sample_video)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.width == 640
        assert metadata.height == 480
        assert metadata.fps == 10.0
        assert metadata.duration == 5.0
    
    def test_frame_count_estimation(self, service, sample_video):
        """Test frame count estimation for different strategies"""
        config_time = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=1.0,
            max_frames=100
        )
        
        count = service.estimate_frame_count(sample_video, config_time)
        assert isinstance(count, int)
        assert count > 0
        assert count <= config_time.max_frames
    
    def test_cost_estimation(self, service, sample_video):
        """Test processing cost estimation"""
        config = ExtractionConfig(max_frames=20)
        cost_estimate = service.estimate_processing_cost(sample_video, config)
        
        assert isinstance(cost_estimate, dict)
        assert 'estimated_frames' in cost_estimate
        assert 'estimated_processing_time_seconds' in cost_estimate
        assert 'estimated_storage_mb' in cost_estimate
        assert cost_estimate['estimated_frames'] > 0
    
    def test_time_based_extraction(self, service, sample_video):
        """Test time-based frame extraction"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=1.0,
            max_frames=10,
            enable_quality_assessment=True,
            min_quality_threshold=0.1  # Lower threshold for synthetic test video
        )
        
        frames = service.extract_frames(sample_video, config)
        
        assert isinstance(frames, list)
        assert len(frames) > 0
        assert len(frames) <= config.max_frames
        
        # Check frame properties
        for frame in frames:
            assert isinstance(frame, ExtractedFrame)
            assert frame.timestamp >= 0
            assert frame.image_data is not None
            assert isinstance(frame.quality_metrics, FrameQualityMetrics)
            assert "time_interval" in frame.sampling_reason
    
    def test_keyframe_extraction_opencv_fallback(self, service, sample_video):
        """Test keyframe extraction using OpenCV fallback"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.KEYFRAME,
            max_frames=10,
            keyframe_threshold=0.3
        )
        
        # This will use OpenCV fallback since FFmpeg might not be available
        frames = service._extract_keyframes_opencv(sample_video, config, 
                                                 service.get_video_metadata(sample_video))
        
        assert isinstance(frames, list)
        # Should extract some frames even with fallback method
        for frame in frames:
            assert isinstance(frame, ExtractedFrame)
            assert "keyframe" in frame.sampling_reason
    
    def test_scene_change_extraction(self, service, sample_video):
        """Test scene change detection"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.SCENE_CHANGE,
            max_frames=10,
            scene_change_threshold=0.4
        )
        
        metadata = service.get_video_metadata(sample_video)
        frames = service._extract_scene_changes(sample_video, config, metadata)
        
        assert isinstance(frames, list)
        for frame in frames:
            assert isinstance(frame, ExtractedFrame)
            assert "scene_change" in frame.sampling_reason
    
    def test_adaptive_extraction(self, service, sample_video):
        """Test adaptive sampling"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.ADAPTIVE,
            time_interval=1.0,
            max_frames=10,
            adaptive_complexity_threshold=0.5
        )
        
        metadata = service.get_video_metadata(sample_video)
        frames = service._extract_adaptive(sample_video, config, metadata)
        
        assert isinstance(frames, list)
        for frame in frames:
            assert isinstance(frame, ExtractedFrame)
            assert "adaptive" in frame.sampling_reason
    
    def test_hybrid_extraction(self, service, sample_video):
        """Test hybrid sampling approach"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.HYBRID,
            time_interval=2.0,
            max_frames=15
        )
        
        metadata = service.get_video_metadata(sample_video)
        frames = service._extract_hybrid(sample_video, config, metadata)
        
        assert isinstance(frames, list)
        for frame in frames:
            assert isinstance(frame, ExtractedFrame)
            assert "hybrid" in frame.sampling_reason
    
    def test_quality_assessment(self, service):
        """Test frame quality assessment"""
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        quality_metrics = service._assess_frame_quality(frame)
        
        assert isinstance(quality_metrics, FrameQualityMetrics)
        assert 0 <= quality_metrics.blur_score <= 1
        assert 0 <= quality_metrics.contrast_score <= 1
        assert 0 <= quality_metrics.brightness_score <= 1
        assert 0 <= quality_metrics.confidence <= 1
        assert isinstance(quality_metrics.overall_quality, FrameQuality)
    
    def test_quality_filtering(self, service, sample_video):
        """Test quality-based frame filtering"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=0.5,
            max_frames=20,
            enable_quality_assessment=True,
            min_quality_threshold=0.0  # Don't filter initially
        )
        
        frames = service.extract_frames(sample_video, config)
        original_count = len(frames)
        
        # Apply quality filtering
        filtered_frames = service._filter_by_quality(frames, 0.5)
        
        assert len(filtered_frames) <= original_count
        for frame in filtered_frames:
            assert frame.quality_metrics.confidence >= 0.5
    
    def test_preprocessing(self, service, sample_video):
        """Test frame preprocessing"""
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=2.0,
            max_frames=5,
            enable_preprocessing=True,
            enable_perspective_correction=True,
            target_resolution=(320, 240),
            min_quality_threshold=0.1  # Lower threshold for synthetic test video
        )
        
        frames = service.extract_frames(sample_video, config)
        
        assert len(frames) > 0
        
        # Check if frames were resized
        for frame in frames:
            if frame.processing_metadata and frame.processing_metadata.get('resized'):
                height, width = frame.image_data.shape[:2]
                assert width == 320
                assert height == 240
    
    def test_noise_estimation(self, service):
        """Test noise level estimation"""
        # Clean image
        clean_frame = np.ones((100, 100), dtype=np.uint8) * 128
        noise_level_clean = service._estimate_noise_level(clean_frame)
        
        # Noisy image
        noisy_frame = clean_frame + np.random.randint(-50, 50, (100, 100), dtype=np.int16)
        noisy_frame = np.clip(noisy_frame, 0, 255).astype(np.uint8)
        noise_level_noisy = service._estimate_noise_level(noisy_frame)
        
        assert noise_level_noisy > noise_level_clean
        assert 0 <= noise_level_clean <= 1
        assert 0 <= noise_level_noisy <= 1
    
    def test_perspective_skew_detection(self, service):
        """Test perspective skew detection"""
        # Create image with lines
        frame = np.zeros((200, 200), dtype=np.uint8)
        
        # Add horizontal and vertical lines (no skew)
        cv2.line(frame, (0, 100), (200, 100), 255, 2)  # Horizontal
        cv2.line(frame, (100, 0), (100, 200), 255, 2)  # Vertical
        
        skew = service._detect_perspective_skew(frame)
        assert 0 <= skew <= 1
    
    def test_text_density_estimation(self, service):
        """Test text region density estimation"""
        # Create frame with text-like regions
        frame = np.zeros((200, 200), dtype=np.uint8)
        
        # Add some text-like patterns
        cv2.putText(frame, "TEST", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
        
        density = service._estimate_text_density(frame)
        assert 0 <= density <= 1
    
    def test_content_complexity_calculation(self, service):
        """Test content complexity calculation"""
        # Simple frame (low complexity)
        simple_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        complexity_simple = service._calculate_content_complexity(simple_frame)
        
        # Complex frame (high complexity)
        complex_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        complexity_complex = service._calculate_content_complexity(complex_frame)
        
        assert 0 <= complexity_simple <= 1
        assert 0 <= complexity_complex <= 1
        assert complexity_complex > complexity_simple
    
    def test_image_enhancement(self, service):
        """Test image enhancement preprocessing"""
        # Create test image
        original = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)
        enhanced = service._enhance_image(original)
        
        assert enhanced.shape == original.shape
        assert enhanced.dtype == original.dtype
        # Enhanced image should be different from original
        assert not np.array_equal(original, enhanced)
    
    def test_point_ordering(self, service):
        """Test point ordering for perspective correction"""
        # Create test points (rectangle corners)
        points = np.array([[100, 50], [50, 50], [50, 100], [100, 100]])  # Random order
        ordered = service._order_points(points)
        
        assert ordered.shape == (4, 2)
        # Should be ordered as: top-left, top-right, bottom-right, bottom-left
        assert ordered[0][1] <= ordered[2][1]  # Top points have smaller y than bottom
        assert ordered[0][0] <= ordered[1][0]  # Left points have smaller x than right
    
    def test_error_handling(self, service):
        """Test error handling for invalid inputs"""
        # Test with non-existent file
        with pytest.raises(ValueError):
            service.extract_frames("nonexistent_file.mp4")
        
        # Test with invalid configuration
        config = ExtractionConfig(max_frames=0)  # Invalid max_frames
        
        # Should handle gracefully or raise appropriate error
        # The actual behavior depends on implementation details


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_extraction_config(self):
        """Test extraction config creation utility"""
        config = create_extraction_config(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=2.0,
            max_frames=50
        )
        
        assert isinstance(config, ExtractionConfig)
        assert config.sampling_strategy == SamplingStrategy.TIME_BASED
        assert config.time_interval == 2.0
        assert config.max_frames == 50
    
    @pytest.fixture
    def sample_video_for_utils(self):
        """Create sample video for utility function tests"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        video_path = temp_file.name
        temp_file.close()
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 5.0, (320, 240))
        
        for i in range(25):  # 5 seconds at 5 fps
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            out.write(frame)
        
        out.release()
        yield video_path
        
        if os.path.exists(video_path):
            os.unlink(video_path)
    
    def test_extract_frames_from_video_utility(self, sample_video_for_utils):
        """Test convenience function for frame extraction"""
        frames = extract_frames_from_video(
            sample_video_for_utils,
            sampling_strategy=SamplingStrategy.TIME_BASED,
            time_interval=1.0,
            max_frames=10
        )
        
        assert isinstance(frames, list)
        assert len(frames) > 0
        assert all(isinstance(f, ExtractedFrame) for f in frames)
    
    def test_get_video_info_utility(self, sample_video_for_utils):
        """Test video info utility function"""
        info = get_video_info(sample_video_for_utils)
        
        assert isinstance(info, dict)
        assert 'duration' in info
        assert 'fps' in info
        assert 'width' in info
        assert 'height' in info
        assert info['width'] == 320
        assert info['height'] == 240


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def complex_video(self):
        """Create a more complex video for integration testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        video_path = temp_file.name
        temp_file.close()
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 15.0, (800, 600))
        
        # Create 150 frames (10 seconds at 15 fps) with varying content
        for i in range(150):
            frame = np.zeros((600, 800, 3), dtype=np.uint8)
            
            # Background gradient
            for y in range(600):
                intensity = int(255 * (y / 600))
                frame[y, :] = [intensity // 3, intensity // 2, intensity]
            
            # Scene changes every 50 frames
            scene = i // 50
            if scene % 2 == 1:
                frame = cv2.bitwise_not(frame)
            
            # Moving objects
            x = (i * 5) % 800
            y = 300 + int(100 * np.sin(i * 0.1))
            cv2.circle(frame, (x, y), 30, (255, 255, 255), -1)
            
            # Text overlays
            if i % 30 < 15:  # Text appears periodically
                cv2.putText(frame, f"Scene {scene + 1}", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            
            # Add noise to some frames
            if i % 20 < 5:
                noise = np.random.randint(0, 30, frame.shape, dtype=np.uint8)
                frame = cv2.add(frame, noise)
            
            out.write(frame)
        
        out.release()
        yield video_path
        
        if os.path.exists(video_path):
            os.unlink(video_path)
    
    def test_complete_extraction_workflow(self, complex_video):
        """Test complete extraction workflow with all features"""
        service = FrameExtractionService()
        
        # Test metadata extraction
        metadata = service.get_video_metadata(complex_video)
        assert metadata.duration > 0
        assert metadata.width == 800
        assert metadata.height == 600
        
        # Test cost estimation
        config = ExtractionConfig(
            sampling_strategy=SamplingStrategy.HYBRID,
            time_interval=1.0,
            max_frames=50,
            enable_quality_assessment=True,
            enable_preprocessing=True,
            min_quality_threshold=0.3
        )
        
        cost_estimate = service.estimate_processing_cost(complex_video, config)
        assert cost_estimate['estimated_frames'] > 0
        
        # Test frame extraction
        frames = service.extract_frames(complex_video, config)
        
        assert len(frames) > 0
        assert len(frames) <= config.max_frames
        
        # Verify frame properties
        timestamps = [f.timestamp for f in frames]
        assert timestamps == sorted(timestamps)  # Should be in chronological order
        
        # Check quality metrics
        qualities = [f.quality_metrics.confidence for f in frames]
        assert all(q >= config.min_quality_threshold for q in qualities)
        
        # Verify sampling reasons
        reasons = set(f.sampling_reason.split('_')[0] for f in frames)
        assert len(reasons) > 0  # Should have at least one sampling reason
        
        # Test frame saving (if enabled)
        with tempfile.TemporaryDirectory() as temp_dir:
            config.save_frames = True
            config.output_directory = temp_dir
            
            frames_with_save = service.extract_frames(complex_video, config)
            
            # Check if files were created
            saved_files = list(Path(temp_dir).glob("*.jpg"))
            assert len(saved_files) == len(frames_with_save)
    
    def test_performance_benchmarking(self, complex_video):
        """Test performance with different configurations"""
        service = FrameExtractionService()
        
        import time
        
        configs = [
            ("Fast", ExtractionConfig(
                sampling_strategy=SamplingStrategy.TIME_BASED,
                time_interval=2.0,
                max_frames=20,
                enable_quality_assessment=False,
                enable_preprocessing=False
            )),
            ("Balanced", ExtractionConfig(
                sampling_strategy=SamplingStrategy.ADAPTIVE,
                time_interval=1.0,
                max_frames=30,
                enable_quality_assessment=True,
                enable_preprocessing=False,
                min_quality_threshold=0.1  # Lower threshold for synthetic test video
            )),
            ("High Quality", ExtractionConfig(
                sampling_strategy=SamplingStrategy.HYBRID,
                time_interval=0.5,
                max_frames=40,
                enable_quality_assessment=True,
                enable_preprocessing=True,
                min_quality_threshold=0.1  # Lower threshold for synthetic test video
            ))
        ]
        
        results = {}
        
        for config_name, config in configs:
            start_time = time.time()
            frames = service.extract_frames(complex_video, config)
            end_time = time.time()
            
            processing_time = end_time - start_time
            results[config_name] = {
                'frames': len(frames),
                'time': processing_time,
                'fps': len(frames) / processing_time if processing_time > 0 else 0
            }
        
        # Verify that we got reasonable performance
        assert all(result['frames'] > 0 for result in results.values())
        assert all(result['time'] > 0 for result in results.values())
        
        # Fast config should generally be faster than high quality
        if results['Fast']['time'] > 0 and results['High Quality']['time'] > 0:
            assert results['Fast']['fps'] >= results['High Quality']['fps'] * 0.5  # Allow some variance


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])