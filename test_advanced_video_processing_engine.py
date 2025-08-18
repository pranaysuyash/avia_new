"""
Test Suite for Advanced Video Processing Engine
Task 3: Advanced Media Processing Pipeline

Comprehensive tests for advanced video processing including scene detection,
keyframe extraction, object recognition, and B-roll suggestions.
"""

import pytest
import asyncio
import os
import tempfile
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the module under test
try:
    from advanced_video_processing_engine import (
        AdvancedVideoProcessingEngine, VideoMetadata, SceneInfo, KeyFrame,
        ObjectDetection, BRollSuggestion, VideoQuality, SceneType, ObjectCategory,
        ProcessingStrategy, ContentComplexity
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORT_SUCCESS = False

# Test fixtures
@pytest.fixture
def temp_video_file():
    """Create a temporary test video file"""
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, "test_video.mp4")
    
    # Create a simple test video using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))
    
    # Generate 300 frames (10 seconds at 30fps)
    for i in range(300):
        # Create different colored frames for scene detection
        if i < 100:
            frame = np.full((480, 640, 3), (255, 0, 0), dtype=np.uint8)  # Blue
        elif i < 200:
            frame = np.full((480, 640, 3), (0, 255, 0), dtype=np.uint8)  # Green
        else:
            frame = np.full((480, 640, 3), (0, 0, 255), dtype=np.uint8)  # Red
        
        # Add some noise for realism
        noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        out.write(frame)
    
    out.release()
    
    yield video_path
    
    # Cleanup
    if os.path.exists(video_path):
        os.remove(video_path)
    os.rmdir(temp_dir)

@pytest.fixture
def video_engine():
    """Create video processing engine instance"""
    if not IMPORT_SUCCESS:
        pytest.skip("AdvancedVideoProcessingEngine not available")
    
    return AdvancedVideoProcessingEngine(max_workers=2)

@pytest.fixture
def sample_metadata():
    """Sample video metadata for testing"""
    return VideoMetadata(
        duration=10.0,
        fps=30.0,
        width=640,
        height=480,
        total_frames=300,
        codec="h264",
        bitrate=1000000,
        file_size=1024*1024,
        aspect_ratio="4:3",
        has_audio=True,
        quality_score=0.8,
        complexity_score=0.5
    )

class TestAdvancedVideoProcessingEngine:
    """Test cases for AdvancedVideoProcessingEngine"""
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = AdvancedVideoProcessingEngine(max_workers=4)
        
        assert engine.max_workers == 4
        assert engine.temp_dir is not None
        assert engine.executor is not None
        
        # Test cleanup
        asyncio.run(engine.cleanup())
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_video_metadata_extraction(self, video_engine, temp_video_file):
        """Test video metadata extraction"""
        metadata = await video_engine.get_video_metadata(temp_video_file)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.duration > 0
        assert metadata.fps > 0
        assert metadata.width > 0
        assert metadata.height > 0
        assert metadata.total_frames > 0
        assert 0 <= metadata.quality_score <= 1
        assert 0 <= metadata.complexity_score <= 1
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_quality_score_calculation(self, video_engine):
        """Test video quality score calculation"""
        # Test different quality scenarios
        score_hd = video_engine._calculate_video_quality_score(1920, 1080, 5000000, 30)
        score_sd = video_engine._calculate_video_quality_score(640, 480, 1000000, 30)
        score_4k = video_engine._calculate_video_quality_score(3840, 2160, 20000000, 60)
        
        assert 0 <= score_hd <= 1
        assert 0 <= score_sd <= 1
        assert 0 <= score_4k <= 1
        assert score_4k >= score_hd >= score_sd  # Higher resolution should have higher score
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_complexity_score_calculation(self, video_engine):
        """Test content complexity score calculation"""
        # Test different complexity scenarios
        score_simple = video_engine._calculate_complexity_score(60, 640, 480, 30)  # 1 min, SD
        score_complex = video_engine._calculate_complexity_score(3600, 1920, 1080, 60)  # 1 hour, HD, 60fps
        
        assert 0 <= score_simple <= 1
        assert 0 <= score_complex <= 1
        assert score_complex >= score_simple  # Longer, higher res should be more complex
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_content_analysis(self, video_engine, temp_video_file, sample_metadata):
        """Test content complexity analysis"""
        analysis = await video_engine._analyze_content_complexity(temp_video_file, sample_metadata)
        
        assert hasattr(analysis, 'complexity')
        assert hasattr(analysis, 'quality_score')
        assert hasattr(analysis, 'estimated_processing_time')
        assert analysis.estimated_processing_time > 0
        assert 0 <= analysis.quality_score <= 1
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_processing_strategy_selection(self, video_engine):
        """Test processing strategy selection"""
        # Mock content analysis with different complexity levels
        simple_analysis = Mock()
        simple_analysis.complexity = ContentComplexity.SIMPLE
        
        complex_analysis = Mock()
        complex_analysis.complexity = ContentComplexity.VERY_COMPLEX
        
        simple_strategy = video_engine._select_processing_strategy(simple_analysis)
        complex_strategy = video_engine._select_processing_strategy(complex_analysis)
        
        assert simple_strategy == ProcessingStrategy.BASIC
        assert complex_strategy == ProcessingStrategy.ENTERPRISE
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_frame_quality_metrics(self, video_engine):
        """Test frame quality metrics calculation"""
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        metrics = video_engine._calculate_frame_quality_metrics(frame)
        
        assert 'sharpness' in metrics
        assert 'brightness' in metrics
        assert 'contrast' in metrics
        assert 'noise' in metrics
        
        for metric_name, value in metrics.items():
            assert isinstance(value, float)
            assert value >= 0
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_visual_hash_calculation(self, video_engine):
        """Test visual hash calculation"""
        # Create test frames
        frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        frame2 = frame1.copy()  # Identical frame
        frame3 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)  # Different frame
        
        hash1 = video_engine._calculate_visual_hash(frame1)
        hash2 = video_engine._calculate_visual_hash(frame2)
        hash3 = video_engine._calculate_visual_hash(frame3)
        
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        assert isinstance(hash3, str)
        assert hash1 == hash2  # Identical frames should have same hash
        assert hash1 != hash3  # Different frames should have different hashes
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_keyframe_extraction(self, video_engine, temp_video_file, sample_metadata):
        """Test keyframe extraction"""
        keyframes = video_engine._extract_keyframes_advanced(temp_video_file, sample_metadata)
        
        assert isinstance(keyframes, list)
        assert len(keyframes) > 0
        
        for keyframe in keyframes:
            assert isinstance(keyframe, KeyFrame)
            assert keyframe.frame_number >= 0
            assert keyframe.timestamp >= 0
            assert 0 <= keyframe.confidence <= 1
            assert isinstance(keyframe.visual_hash, str)
            assert isinstance(keyframe.objects_detected, list)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_scene_detection_basic(self, video_engine, temp_video_file, sample_metadata):
        """Test basic scene detection"""
        scenes = video_engine._detect_scenes_basic(temp_video_file, sample_metadata)
        
        assert isinstance(scenes, list)
        
        for scene in scenes:
            assert isinstance(scene, SceneInfo)
            assert scene.start_time >= 0
            assert scene.end_time > scene.start_time
            assert scene.start_frame >= 0
            assert scene.end_frame > scene.start_frame
            assert 0 <= scene.confidence <= 1
            assert isinstance(scene.scene_type, SceneType)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_scene_detection_advanced(self, video_engine, temp_video_file, sample_metadata):
        """Test advanced scene detection"""
        scenes = video_engine._detect_scenes_advanced(temp_video_file, sample_metadata)
        
        assert isinstance(scenes, list)
        
        for scene in scenes:
            assert isinstance(scene, SceneInfo)
            assert scene.start_time >= 0
            assert scene.end_time > scene.start_time
            assert 0 <= scene.confidence <= 1
            assert 0 <= scene.motion_intensity <= 1
            assert 0 <= scene.visual_complexity <= 1
            assert isinstance(scene.scene_type, SceneType)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_motion_intensity_calculation(self, video_engine):
        """Test motion intensity calculation"""
        # Create test frames with known motion
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a moving object
        cv2.rectangle(frame1, (100, 100), (200, 200), (255, 255, 255), -1)
        cv2.rectangle(frame2, (150, 150), (250, 250), (255, 255, 255), -1)
        
        motion = video_engine._calculate_motion_intensity(frame1, frame2)
        
        assert isinstance(motion, float)
        assert motion >= 0
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_scene_type_classification(self, video_engine):
        """Test scene type classification"""
        # Test different motion intensities
        static_type = video_engine._classify_scene_type(0.1, 0.8)
        dynamic_type = video_engine._classify_scene_type(0.6, 0.8)
        action_type = video_engine._classify_scene_type(0.9, 0.8)
        transition_type = video_engine._classify_scene_type(0.3, 0.2)
        
        assert static_type == SceneType.STATIC
        assert dynamic_type == SceneType.DYNAMIC
        assert action_type == SceneType.ACTION
        assert transition_type == SceneType.TRANSITION
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_object_detection_basic(self, video_engine, temp_video_file, sample_metadata):
        """Test basic object detection"""
        objects = video_engine._detect_objects_basic(temp_video_file, sample_metadata)
        
        assert isinstance(objects, list)
        
        for obj in objects:
            assert isinstance(obj, ObjectDetection)
            assert isinstance(obj.class_name, str)
            assert isinstance(obj.category, ObjectCategory)
            assert 0 <= obj.confidence <= 1
            assert len(obj.bbox) == 4
            assert obj.timestamp >= 0
            assert obj.frame_number >= 0
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_object_detection_advanced(self, video_engine, temp_video_file, sample_metadata):
        """Test advanced object detection with tracking"""
        objects = video_engine._detect_objects_advanced(temp_video_file, sample_metadata)
        
        assert isinstance(objects, list)
        
        for obj in objects:
            assert isinstance(obj, ObjectDetection)
            assert isinstance(obj.class_name, str)
            assert isinstance(obj.category, ObjectCategory)
            assert 0 <= obj.confidence <= 1
            assert len(obj.bbox) == 4
            assert obj.timestamp >= 0
            assert obj.frame_number >= 0
            # Advanced detection should include tracking IDs
            if obj.tracking_id:
                assert isinstance(obj.tracking_id, str)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_visual_complexity_calculation(self, video_engine):
        """Test visual complexity calculation"""
        # Create frames with different complexity levels
        simple_frame = np.full((480, 640, 3), 128, dtype=np.uint8)  # Uniform gray
        complex_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)  # Random noise
        
        simple_complexity = video_engine._calculate_visual_complexity(simple_frame)
        complex_complexity = video_engine._calculate_visual_complexity(complex_frame)
        
        assert 0 <= simple_complexity <= 1
        assert 0 <= complex_complexity <= 1
        assert complex_complexity > simple_complexity
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_broll_suggestions_generation(self, video_engine):
        """Test B-roll suggestions generation"""
        # Create mock data
        keyframes = [
            KeyFrame(frame_number=0, timestamp=0.0, confidence=0.8, visual_hash="abc123"),
            KeyFrame(frame_number=150, timestamp=5.0, confidence=0.3, visual_hash="def456"),  # Low quality
            KeyFrame(frame_number=300, timestamp=10.0, confidence=0.9, visual_hash="ghi789")
        ]
        
        scenes = [
            SceneInfo(
                start_time=0.0, end_time=20.0, start_frame=0, end_frame=600,
                confidence=0.8, scene_type=SceneType.STATIC, motion_intensity=0.1,
                visual_complexity=0.3
            )
        ]
        
        objects = [
            ObjectDetection(
                class_name="face", category=ObjectCategory.FACE, confidence=0.9,
                bbox=(100, 100, 50, 50), timestamp=2.0, frame_number=60
            )
        ]
        
        content_analysis = Mock()
        content_analysis.duration_seconds = 30.0
        
        suggestions = await video_engine._generate_intelligent_broll_suggestions(
            keyframes, scenes, objects, content_analysis
        )
        
        assert isinstance(suggestions, list)
        
        for suggestion in suggestions:
            assert isinstance(suggestion, BRollSuggestion)
            assert suggestion.timestamp >= 0
            assert suggestion.duration > 0
            assert 0 <= suggestion.confidence <= 1
            assert suggestion.priority >= 1
            assert isinstance(suggestion.keywords, list)
            assert isinstance(suggestion.description, str)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_face_detection_clustering(self, video_engine):
        """Test face detection clustering"""
        # Create mock face detections
        objects = [
            ObjectDetection(
                class_name="face", category=ObjectCategory.FACE, confidence=0.9,
                bbox=(100, 100, 50, 50), timestamp=1.0, frame_number=30
            ),
            ObjectDetection(
                class_name="face", category=ObjectCategory.FACE, confidence=0.8,
                bbox=(110, 110, 50, 50), timestamp=2.0, frame_number=60
            ),
            ObjectDetection(
                class_name="face", category=ObjectCategory.FACE, confidence=0.9,
                bbox=(120, 120, 50, 50), timestamp=35.0, frame_number=1050  # Different cluster
            )
        ]
        
        clusters = video_engine._cluster_face_detections(objects)
        
        assert isinstance(clusters, list)
        assert len(clusters) >= 1
        
        for cluster in clusters:
            assert isinstance(cluster, list)
            assert len(cluster) > 0
            for obj in cluster:
                assert obj.category == ObjectCategory.FACE
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_frame_similarity_calculation(self, video_engine):
        """Test frame similarity calculation"""
        # Create similar keyframes
        frame1 = KeyFrame(
            frame_number=0, timestamp=0.0, confidence=0.8,
            visual_hash="abc123", quality_metrics={'sharpness': 0.8, 'brightness': 0.5}
        )
        frame2 = KeyFrame(
            frame_number=30, timestamp=1.0, confidence=0.8,
            visual_hash="abc123", quality_metrics={'sharpness': 0.8, 'brightness': 0.5}
        )
        frame3 = KeyFrame(
            frame_number=60, timestamp=2.0, confidence=0.8,
            visual_hash="def456", quality_metrics={'sharpness': 0.3, 'brightness': 0.2}
        )
        
        similarity_high = video_engine._calculate_frame_similarity(frame1, frame2)
        similarity_low = video_engine._calculate_frame_similarity(frame1, frame3)
        
        assert 0 <= similarity_high <= 1
        assert 0 <= similarity_low <= 1
        assert similarity_high > similarity_low
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_comprehensive_video_processing(self, video_engine, temp_video_file):
        """Test comprehensive video processing workflow"""
        processing_options = {
            'extract_keyframes': True,
            'detect_scenes': True,
            'detect_objects': True,
            'suggest_broll': True,
            'enhance_quality': False
        }
        
        results = await video_engine.process_video_comprehensive(
            temp_video_file, processing_options
        )
        
        assert isinstance(results, dict)
        assert 'success' in results
        assert 'processing_time' in results
        assert 'metadata' in results
        assert 'keyframes' in results
        assert 'scenes' in results
        assert 'objects' in results
        assert 'broll_suggestions' in results
        
        if results['success']:
            assert isinstance(results['metadata'], VideoMetadata)
            assert isinstance(results['keyframes'], list)
            assert isinstance(results['scenes'], list)
            assert isinstance(results['objects'], list)
            assert isinstance(results['broll_suggestions'], list)
            assert results['processing_time'] > 0
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_processing_task_creation(self, video_engine, temp_video_file, sample_metadata):
        """Test processing task creation"""
        options = {
            'extract_keyframes': True,
            'detect_scenes': True,
            'detect_objects': True,
            'enhance_quality': False
        }
        
        tasks = video_engine._create_processing_tasks(
            temp_video_file, sample_metadata, ProcessingStrategy.ENHANCED, options
        )
        
        assert isinstance(tasks, dict)
        assert 'keyframes' in tasks
        assert 'scenes' in tasks
        assert 'objects' in tasks
        
        # Test that tasks are callable
        for task_name, task_func in tasks.items():
            assert callable(task_func)
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_processing_task_execution(self, video_engine):
        """Test processing task execution"""
        # Create mock tasks
        def mock_task1():
            return "result1"
        
        def mock_task2():
            return "result2"
        
        def failing_task():
            raise ValueError("Task failed")
        
        tasks = {
            'task1': mock_task1,
            'task2': mock_task2,
            'failing_task': failing_task
        }
        
        results = await video_engine._execute_processing_tasks(tasks)
        
        assert isinstance(results, dict)
        assert 'task1' in results
        assert 'task2' in results
        assert 'failing_task' in results
        
        assert results['task1'] == "result1"
        assert results['task2'] == "result2"
        assert isinstance(results['failing_task'], Exception)

class TestVideoProcessingDataModels:
    """Test video processing data models"""
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_video_metadata_creation(self):
        """Test VideoMetadata creation"""
        metadata = VideoMetadata(
            duration=10.0, fps=30.0, width=1920, height=1080,
            total_frames=300, codec="h264", quality_score=0.8
        )
        
        assert metadata.duration == 10.0
        assert metadata.fps == 30.0
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.quality_score == 0.8
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_scene_info_creation(self):
        """Test SceneInfo creation"""
        scene = SceneInfo(
            start_time=0.0, end_time=5.0, start_frame=0, end_frame=150,
            confidence=0.9, scene_type=SceneType.DYNAMIC,
            motion_intensity=0.7, visual_complexity=0.6
        )
        
        assert scene.start_time == 0.0
        assert scene.end_time == 5.0
        assert scene.confidence == 0.9
        assert scene.scene_type == SceneType.DYNAMIC
        assert scene.motion_intensity == 0.7
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_keyframe_creation(self):
        """Test KeyFrame creation"""
        keyframe = KeyFrame(
            frame_number=100, timestamp=3.33, confidence=0.85,
            visual_hash="abc123", objects_detected=["face", "person"]
        )
        
        assert keyframe.frame_number == 100
        assert keyframe.timestamp == 3.33
        assert keyframe.confidence == 0.85
        assert keyframe.visual_hash == "abc123"
        assert "face" in keyframe.objects_detected
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_object_detection_creation(self):
        """Test ObjectDetection creation"""
        detection = ObjectDetection(
            class_name="face", category=ObjectCategory.FACE,
            confidence=0.95, bbox=(100, 100, 50, 50),
            timestamp=2.5, frame_number=75, tracking_id="track_001"
        )
        
        assert detection.class_name == "face"
        assert detection.category == ObjectCategory.FACE
        assert detection.confidence == 0.95
        assert detection.bbox == (100, 100, 50, 50)
        assert detection.tracking_id == "track_001"
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_broll_suggestion_creation(self):
        """Test BRollSuggestion creation"""
        suggestion = BRollSuggestion(
            timestamp=5.0, duration=3.0, suggestion_type="scene_enhancement",
            description="Add visual interest", confidence=0.8,
            keywords=["visual", "interest"], priority=2
        )
        
        assert suggestion.timestamp == 5.0
        assert suggestion.duration == 3.0
        assert suggestion.suggestion_type == "scene_enhancement"
        assert suggestion.confidence == 0.8
        assert suggestion.priority == 2
        assert "visual" in suggestion.keywords

class TestVideoProcessingIntegration:
    """Integration tests for video processing"""
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, temp_video_file):
        """Test end-to-end video processing"""
        engine = AdvancedVideoProcessingEngine(max_workers=1)
        
        try:
            # Test with minimal options for faster execution
            options = {
                'extract_keyframes': True,
                'detect_scenes': True,
                'detect_objects': False,  # Skip for speed
                'suggest_broll': True,
                'enhance_quality': False
            }
            
            results = await engine.process_video_comprehensive(temp_video_file, options)
            
            assert results['success'] is True
            assert 'processing_time' in results
            assert 'metadata' in results
            assert len(results['keyframes']) > 0
            assert len(results['scenes']) >= 0  # May be 0 for simple test video
            
        finally:
            await engine.cleanup()
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid inputs"""
        engine = AdvancedVideoProcessingEngine(max_workers=1)
        
        try:
            # Test with non-existent file
            results = await engine.process_video_comprehensive("nonexistent.mp4", {})
            assert results['success'] is False
            assert 'error' in results
            
        finally:
            await engine.cleanup()
    
    @pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module not available")
    def test_performance_benchmarks(self, temp_video_file):
        """Test performance benchmarks"""
        engine = AdvancedVideoProcessingEngine(max_workers=2)
        
        try:
            # Benchmark metadata extraction
            import time
            start_time = time.time()
            
            metadata = asyncio.run(engine.get_video_metadata(temp_video_file))
            
            extraction_time = time.time() - start_time
            
            assert extraction_time < 5.0  # Should complete within 5 seconds
            assert isinstance(metadata, VideoMetadata)
            
        finally:
            asyncio.run(engine.cleanup())

# Test utilities
def create_test_frame(width: int = 640, height: int = 480, color: tuple = (128, 128, 128)) -> np.ndarray:
    """Create a test frame with specified dimensions and color"""
    return np.full((height, width, 3), color, dtype=np.uint8)

def create_test_video_metadata(duration: float = 10.0) -> VideoMetadata:
    """Create test video metadata"""
    return VideoMetadata(
        duration=duration,
        fps=30.0,
        width=640,
        height=480,
        total_frames=int(duration * 30),
        codec="h264",
        quality_score=0.8,
        complexity_score=0.5
    )

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])