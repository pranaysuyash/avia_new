#!/usr/bin/env python3
"""
Tests for Processing Router and Workflow Engine
Comprehensive test suite for intelligent media processing routing
"""

import pytest
import asyncio
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from processing_router_workflow_engine import (
    ProcessingRouterWorkflowEngine,
    MediaType,
    ContentComplexity,
    ProcessingStrategy,
    ProcessingMode,
    WorkflowPriority,
    WorkflowStatus,
    ContentAnalysis,
    ProcessingRoute,
    ProcessingJob,
    ProcessingResult
)

class TestProcessingRouterWorkflowEngine:
    """Test suite for ProcessingRouterWorkflowEngine"""
    
    @pytest.fixture
    def router(self):
        """Create router instance for testing"""
        return ProcessingRouterWorkflowEngine(max_concurrent_jobs=2)
    
    @pytest.fixture
    def temp_audio_file(self):
        """Create temporary audio file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b"fake audio data" * 1000)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def temp_video_file(self):
        """Create temporary video file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b"fake video data" * 5000)
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def temp_document_file(self):
        """Create temporary document file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"fake pdf data" * 100)
            yield f.name
        os.unlink(f.name)
    
    def test_initialization(self, router):
        """Test router initialization"""
        assert router.max_concurrent_jobs == 2
        assert len(router.processing_routes) > 0
        assert router.active_jobs == {}
        assert router.completed_jobs == {}
        assert router.job_queue == []
        
        # Check default routes exist
        assert "audio_basic" in router.processing_routes
        assert "video_basic" in router.processing_routes
        assert "document_basic" in router.processing_routes
    
    def test_media_type_determination(self, router):
        """Test media type determination from file extensions"""
        assert router._determine_media_type('.mp3') == MediaType.AUDIO
        assert router._determine_media_type('.wav') == MediaType.AUDIO
        assert router._determine_media_type('.mp4') == MediaType.VIDEO
        assert router._determine_media_type('.avi') == MediaType.VIDEO
        assert router._determine_media_type('.jpg') == MediaType.IMAGE
        assert router._determine_media_type('.pdf') == MediaType.DOCUMENT
        assert router._determine_media_type('.xyz') == MediaType.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_content_analysis_audio(self, router, temp_audio_file):
        """Test content analysis for audio files"""
        analysis = await router.analyze_content(temp_audio_file)
        
        assert analysis.media_type == MediaType.AUDIO
        assert analysis.file_size_mb > 0
        assert analysis.complexity in [ContentComplexity.SIMPLE, ContentComplexity.MODERATE, 
                                     ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX]
        assert 0.0 <= analysis.quality_score <= 1.0
        assert len(analysis.processing_requirements) > 0
        assert analysis.estimated_processing_time > 0
        assert 'cpu' in analysis.resource_requirements
        assert 'memory' in analysis.resource_requirements
    
    @pytest.mark.asyncio
    async def test_content_analysis_video(self, router, temp_video_file):
        """Test content analysis for video files"""
        analysis = await router.analyze_content(temp_video_file)
        
        assert analysis.media_type == MediaType.VIDEO
        assert analysis.file_size_mb > 0
        assert analysis.complexity in [ContentComplexity.SIMPLE, ContentComplexity.MODERATE, 
                                     ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX]
        assert 0.0 <= analysis.quality_score <= 1.0
        assert "video_analysis" in analysis.processing_requirements
        assert analysis.estimated_processing_time > 0
    
    @pytest.mark.asyncio
    async def test_content_analysis_document(self, router, temp_document_file):
        """Test content analysis for document files"""
        analysis = await router.analyze_content(temp_document_file)
        
        assert analysis.media_type == MediaType.DOCUMENT
        assert analysis.file_size_mb > 0
        assert "ocr" in analysis.processing_requirements
        assert "text_extraction" in analysis.processing_requirements
    
    @pytest.mark.asyncio
    async def test_content_analysis_nonexistent_file(self, router):
        """Test content analysis with nonexistent file"""
        analysis = await router.analyze_content("/nonexistent/file.mp3")
        
        # Should return fallback analysis
        assert analysis.media_type == MediaType.UNKNOWN
        assert analysis.complexity == ContentComplexity.SIMPLE
        assert analysis.quality_score == 0.5
    
    def test_route_selection_audio_simple(self, router):
        """Test route selection for simple audio content"""
        analysis = ContentAnalysis(
            media_type=MediaType.AUDIO,
            file_size_mb=5.0,
            duration_seconds=60.0,
            complexity=ContentComplexity.SIMPLE,
            quality_score=0.7,
            processing_requirements=["audio_enhancement", "transcription"],
            estimated_processing_time=30.0,
            resource_requirements={'cpu': 1, 'memory': 512}
        )
        
        route = router.select_processing_route(analysis)
        assert route.route_id == "audio_basic"
        assert route.strategy == ProcessingStrategy.BASIC
        assert MediaType.AUDIO in route.media_types
    
    def test_route_selection_audio_complex(self, router):
        """Test route selection for complex audio content"""
        analysis = ContentAnalysis(
            media_type=MediaType.AUDIO,
            file_size_mb=100.0,
            duration_seconds=3600.0,
            complexity=ContentComplexity.COMPLEX,
            quality_score=0.9,
            processing_requirements=["advanced_audio_enhancement", "speaker_diarization"],
            estimated_processing_time=180.0,
            resource_requirements={'cpu': 2, 'memory': 1024}
        )
        
        route = router.select_processing_route(analysis)
        assert route.route_id == "audio_professional"
        assert route.strategy == ProcessingStrategy.PROFESSIONAL
        assert len(route.fallback_routes) > 0
    
    def test_route_selection_video(self, router):
        """Test route selection for video content"""
        analysis = ContentAnalysis(
            media_type=MediaType.VIDEO,
            file_size_mb=200.0,
            duration_seconds=1800.0,
            complexity=ContentComplexity.MODERATE,
            quality_score=0.8,
            processing_requirements=["video_analysis", "transcription"],
            estimated_processing_time=120.0,
            resource_requirements={'cpu': 2, 'memory': 1024}
        )
        
        route = router.select_processing_route(analysis)
        assert route.route_id == "video_basic"
        assert MediaType.VIDEO in route.media_types
    
    def test_route_selection_unknown_media(self, router):
        """Test route selection for unknown media type"""
        analysis = ContentAnalysis(
            media_type=MediaType.UNKNOWN,
            file_size_mb=10.0,
            duration_seconds=0.0,
            complexity=ContentComplexity.SIMPLE,
            quality_score=0.5,
            processing_requirements=["basic_validation"],
            estimated_processing_time=15.0,
            resource_requirements={'cpu': 1, 'memory': 256}
        )
        
        route = router.select_processing_route(analysis)
        # Should get emergency fallback route
        assert "emergency" in route.route_id
        assert route.strategy == ProcessingStrategy.BASIC
    
    @pytest.mark.asyncio
    async def test_process_media_basic(self, router, temp_audio_file):
        """Test basic media processing"""
        job_id = await router.process_media(temp_audio_file)
        
        assert job_id is not None
        assert job_id in router.active_jobs
        
        # Wait for processing to start
        await asyncio.sleep(0.1)
        
        job_status = router.get_job_status(job_id)
        assert job_status is not None
        assert job_status['job_id'] == job_id
        assert job_status['status'] in ['pending', 'running', 'completed']
        
        # Cleanup
        await router.cleanup()
    
    @pytest.mark.asyncio
    async def test_process_media_custom_route(self, router, temp_audio_file):
        """Test media processing with custom route"""
        job_id = await router.process_media(temp_audio_file, custom_route="audio_basic")
        
        assert job_id is not None
        job = router.active_jobs[job_id]
        assert job.selected_route.route_id == "audio_basic"
        
        await router.cleanup()
    
    @pytest.mark.asyncio
    async def test_process_media_priority(self, router, temp_audio_file):
        """Test media processing with priority"""
        job_id = await router.process_media(temp_audio_file, priority=WorkflowPriority.HIGH)
        
        assert job_id is not None
        job = router.active_jobs[job_id]
        assert job.metadata['priority'] == WorkflowPriority.HIGH.value
        
        await router.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, router):
        """Test concurrent processing of multiple files"""
        # Create multiple test files
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(b"audio data" * (100 * (i + 1)))
                test_files.append(f.name)
        
        try:
            # Submit multiple jobs
            job_ids = []
            for test_file in test_files:
                job_id = await router.process_media(test_file)
                job_ids.append(job_id)
            
            assert len(job_ids) == 3
            assert len(router.active_jobs) == 3
            
            # Wait a bit for processing
            await asyncio.sleep(0.5)
            
            # Check that jobs are being processed
            statuses = [router.get_job_status(job_id) for job_id in job_ids]
            assert all(status is not None for status in statuses)
            
        finally:
            # Cleanup test files
            for test_file in test_files:
                try:
                    os.unlink(test_file)
                except:
                    pass
            await router.cleanup()
    
    def test_processing_step_simulation(self, router):
        """Test processing step simulation"""
        # Create mock job
        job = ProcessingJob(
            job_id="test_job",
            input_file="test.mp3",
            content_analysis=ContentAnalysis(
                media_type=MediaType.AUDIO,
                file_size_mb=10.0,
                duration_seconds=120.0,
                complexity=ContentComplexity.SIMPLE,
                quality_score=0.7,
                processing_requirements=["audio_enhancement"],
                estimated_processing_time=30.0,
                resource_requirements={'cpu': 1, 'memory': 512}
            ),
            selected_route=router.processing_routes["audio_basic"]
        )
        
        # Test different processing steps
        result = router._execute_processing_step("audio_enhancement", job)
        assert result['success'] is True
        assert result['step'] == "audio_enhancement"
        
        result = router._execute_processing_step("transcription", job)
        assert result['success'] is True
        assert 'transcript' in result
        
        result = router._execute_processing_step("quality_check", job)
        assert result['success'] is True
        assert 'quality_score' in result
    
    def test_performance_metrics(self, router):
        """Test performance metrics tracking"""
        initial_metrics = router.get_performance_metrics()
        assert initial_metrics['total_jobs'] == 0
        assert initial_metrics['successful_jobs'] == 0
        assert initial_metrics['failed_jobs'] == 0
        assert initial_metrics['active_jobs'] == 0
        
        # Simulate processing results
        success_result = ProcessingResult(job_id="test1", success=True, processing_time=10.0)
        router._update_performance_metrics(success_result)
        
        failure_result = ProcessingResult(job_id="test2", success=False, processing_time=5.0)
        router._update_performance_metrics(failure_result)
        
        updated_metrics = router.get_performance_metrics()
        assert updated_metrics['total_jobs'] == 2
        assert updated_metrics['successful_jobs'] == 1
        assert updated_metrics['failed_jobs'] == 1
        assert updated_metrics['average_processing_time'] == 7.5
    
    def test_complexity_analysis(self, router):
        """Test complexity analysis logic"""
        # Test audio complexity
        complexity = asyncio.run(router._analyze_complexity("test.mp3", MediaType.AUDIO, 5.0))
        assert complexity == ContentComplexity.SIMPLE
        
        complexity = asyncio.run(router._analyze_complexity("test.mp3", MediaType.AUDIO, 100.0))
        assert complexity == ContentComplexity.MODERATE
        
        complexity = asyncio.run(router._analyze_complexity("test.mp3", MediaType.AUDIO, 500.0))
        assert complexity == ContentComplexity.VERY_COMPLEX
        
        # Test video complexity
        complexity = asyncio.run(router._analyze_complexity("test.mp4", MediaType.VIDEO, 30.0))
        assert complexity == ContentComplexity.SIMPLE
        
        complexity = asyncio.run(router._analyze_complexity("test.mp4", MediaType.VIDEO, 2000.0))
        assert complexity == ContentComplexity.VERY_COMPLEX
    
    def test_processing_time_estimation(self, router):
        """Test processing time estimation"""
        # Simple audio
        time_est = router._estimate_processing_time(
            MediaType.AUDIO, ContentComplexity.SIMPLE, 10.0, 60.0
        )
        assert time_est > 0
        
        # Complex video
        time_est_complex = router._estimate_processing_time(
            MediaType.VIDEO, ContentComplexity.VERY_COMPLEX, 500.0, 3600.0
        )
        assert time_est_complex > time_est
    
    def test_resource_requirements_calculation(self, router):
        """Test resource requirements calculation"""
        # Simple audio
        resources = router._calculate_resource_requirements(
            MediaType.AUDIO, ContentComplexity.SIMPLE, 10.0
        )
        assert resources['cpu'] >= 1
        assert resources['memory'] >= 512
        assert resources['disk'] >= 20  # 2x file size
        
        # Complex video
        resources_complex = router._calculate_resource_requirements(
            MediaType.VIDEO, ContentComplexity.VERY_COMPLEX, 500.0
        )
        assert resources_complex['cpu'] > resources['cpu']
        assert resources_complex['memory'] > resources['memory']
        assert resources_complex['gpu'] > 0
    
    def test_emergency_fallback_route(self, router):
        """Test emergency fallback route creation"""
        fallback_route = router._create_emergency_fallback_route(MediaType.AUDIO)
        
        assert fallback_route.route_id == "emergency_audio"
        assert MediaType.AUDIO in fallback_route.media_types
        assert fallback_route.strategy == ProcessingStrategy.BASIC
        assert fallback_route.priority == WorkflowPriority.LOW
        assert len(fallback_route.processing_steps) > 0
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, router):
        """Test quality assessment logic"""
        # Test with different file sizes
        quality_small = await router._assess_quality("small.mp3", MediaType.AUDIO)
        quality_large = await router._assess_quality("large.mp3", MediaType.AUDIO)
        
        # Quality should be between 0 and 1
        assert 0.0 <= quality_small <= 1.0
        assert 0.0 <= quality_large <= 1.0
    
    def test_processing_requirements_determination(self, router):
        """Test processing requirements determination"""
        # Audio requirements
        audio_reqs = router._determine_processing_requirements(
            MediaType.AUDIO, ContentComplexity.SIMPLE, 10.0, 60.0
        )
        assert "format_validation" in audio_reqs
        assert "audio_enhancement" in audio_reqs
        assert "transcription" in audio_reqs
        assert "quality_check" in audio_reqs
        
        # Complex audio requirements
        complex_audio_reqs = router._determine_processing_requirements(
            MediaType.AUDIO, ContentComplexity.COMPLEX, 100.0, 3600.0
        )
        assert "speaker_diarization" in complex_audio_reqs
        assert "advanced_nlp" in complex_audio_reqs
        
        # Video requirements
        video_reqs = router._determine_processing_requirements(
            MediaType.VIDEO, ContentComplexity.MODERATE, 200.0, 1800.0
        )
        assert "video_analysis" in video_reqs
        assert "audio_extraction" in video_reqs
        
        # Document requirements
        doc_reqs = router._determine_processing_requirements(
            MediaType.DOCUMENT, ContentComplexity.SIMPLE, 5.0, 0.0
        )
        assert "ocr" in doc_reqs
        assert "text_extraction" in doc_reqs
    
    @pytest.mark.asyncio
    async def test_media_duration_estimation(self, router, temp_audio_file):
        """Test media duration estimation"""
        duration = await router._get_media_duration(temp_audio_file, MediaType.AUDIO)
        assert duration >= 0.0
        
        # Test with video
        duration_video = await router._get_media_duration("test.mp4", MediaType.VIDEO)
        assert duration_video >= 0.0
        
        # Test with non-media file
        duration_doc = await router._get_media_duration("test.pdf", MediaType.DOCUMENT)
        assert duration_doc == 0.0
    
    def test_job_status_tracking(self, router):
        """Test job status tracking"""
        # Test with non-existent job
        status = router.get_job_status("nonexistent_job")
        assert status is None
        
        # Create a mock job
        job = ProcessingJob(
            job_id="test_job",
            input_file="test.mp3",
            content_analysis=ContentAnalysis(
                media_type=MediaType.AUDIO,
                file_size_mb=10.0,
                duration_seconds=120.0,
                complexity=ContentComplexity.SIMPLE,
                quality_score=0.7,
                processing_requirements=["audio_enhancement"],
                estimated_processing_time=30.0,
                resource_requirements={'cpu': 1, 'memory': 512}
            ),
            selected_route=router.processing_routes["audio_basic"]
        )
        
        router.active_jobs["test_job"] = job
        
        status = router.get_job_status("test_job")
        assert status is not None
        assert status['job_id'] == "test_job"
        assert status['status'] == WorkflowStatus.PENDING.value
        assert status['progress'] == 0.0
        assert status['route'] == "Basic Audio Processing"
    
    @pytest.mark.asyncio
    async def test_cleanup(self, router):
        """Test cleanup functionality"""
        # Add some mock jobs
        job = ProcessingJob(
            job_id="test_job",
            input_file="test.mp3",
            content_analysis=ContentAnalysis(
                media_type=MediaType.AUDIO,
                file_size_mb=10.0,
                duration_seconds=120.0,
                complexity=ContentComplexity.SIMPLE,
                quality_score=0.7,
                processing_requirements=["audio_enhancement"],
                estimated_processing_time=30.0,
                resource_requirements={'cpu': 1, 'memory': 512}
            ),
            selected_route=router.processing_routes["audio_basic"],
            status=WorkflowStatus.RUNNING
        )
        
        router.active_jobs["test_job"] = job
        
        # Cleanup should not raise exceptions
        await router.cleanup()
        
        # Job should be cancelled
        assert job.status == WorkflowStatus.CANCELLED

@pytest.mark.asyncio
async def test_integration_with_media_ingestion():
    """Test integration with MediaIngestionController"""
    # This test would require the actual MediaIngestionController
    # For now, we'll test that the router can work without it
    
    router = ProcessingRouterWorkflowEngine(media_ingestion_controller=None)
    assert router.media_controller is None
    
    # Should still work for basic functionality
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b"test audio data")
        test_file = f.name
    
    try:
        analysis = await router.analyze_content(test_file)
        assert analysis.media_type == MediaType.AUDIO
        
        job_id = await router.process_media(test_file)
        assert job_id is not None
        
    finally:
        os.unlink(test_file)
        await router.cleanup()

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])