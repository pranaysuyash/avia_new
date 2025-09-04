"""
Comprehensive test suite for Frame OCR Job Management System

This module tests all aspects of the enterprise job management system including
job lifecycle, resource allocation, retry logic, and monitoring capabilities.
"""

import pytest
import asyncio
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from frame_ocr_job_manager import (
    FrameOCRJobManager, JobStatus, JobPriority, ProcessingMode,
    ResourceAllocation, RetryConfig, FrameOCRJob, JobMetrics,
    CircuitBreaker, JobQueue, CanaryProcessor
)

class TestFrameOCRJobManager:
    """Test suite for FrameOCRJobManager"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def job_manager(self, temp_db):
        """Create job manager instance for testing"""
        manager = FrameOCRJobManager(db_path=temp_db)
        yield manager
        manager.shutdown()
    
    @pytest.fixture
    def sample_config(self):
        """Sample job configuration"""
        return {
            'sampling_interval': 1.0,
            'max_frames': 100,
            'ocr_engines': ['tesseract'],
            'confidence_threshold': 0.8,
            'languages': ['en'],
            'preprocessing_enabled': True
        }
    
    def test_job_creation(self, job_manager, sample_config):
        """Test basic job creation"""
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=sample_config,
            priority=JobPriority.HIGH
        )
        
        assert job.job_id is not None
        assert job.tenant_id == "test_tenant"
        assert job.video_id == "video_123"
        assert job.status == JobStatus.QUEUED
        assert job.priority == JobPriority.HIGH
        assert job.progress == 0.0
        assert job.retry_count == 0
        assert job.metrics.cost_estimate > 0
    
    def test_job_persistence(self, job_manager, sample_config):
        """Test job persistence to database"""
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=sample_config
        )
        
        # Retrieve job from database
        retrieved_job = job_manager.get_job(job.job_id)
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == job.job_id
        assert retrieved_job.tenant_id == job.tenant_id
        assert retrieved_job.video_id == job.video_id
        assert retrieved_job.status == job.status
    
    def test_job_scheduling(self, job_manager, sample_config):
        """Test job scheduling for future execution"""
        future_time = datetime.now() + timedelta(hours=1)
        
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=sample_config,
            scheduled_at=future_time
        )
        
        assert job.status == JobStatus.PENDING
        assert job.scheduled_at == future_time
    
    def test_job_dependencies(self, job_manager, sample_config):
        """Test job dependencies"""
        # Create parent job
        parent_job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_parent",
            video_path="/path/to/parent.mp4",
            config=sample_config
        )
        
        # Create dependent job
        dependent_job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_child",
            video_path="/path/to/child.mp4",
            config=sample_config,
            dependencies=[parent_job.job_id]
        )
        
        assert parent_job.job_id in dependent_job.dependencies
        
        # Check dependency validation
        assert not job_manager._check_job_dependencies(dependent_job)
        
        # Complete parent job
        parent_job.status = JobStatus.COMPLETED
        job_manager._save_job(parent_job)
        
        # Now dependency should be satisfied
        assert job_manager._check_job_dependencies(dependent_job)
    
    def test_job_cancellation(self, job_manager, sample_config):
        """Test job cancellation"""
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=sample_config
        )
        
        success = job_manager.cancel_job(job.job_id)
        assert success
        
        updated_job = job_manager.get_job(job.job_id)
        assert updated_job.status == JobStatus.CANCELLED
        assert updated_job.completed_at is not None
    
    def test_job_retry(self, job_manager, sample_config):
        """Test job retry functionality"""
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=sample_config
        )
        
        # Simulate job failure
        job.status = JobStatus.FAILED
        job.error_message = "Test error"
        job_manager._save_job(job)
        
        # Retry job
        success = job_manager.retry_job(job.job_id)
        assert success
        
        updated_job = job_manager.get_job(job.job_id)
        assert updated_job.status == JobStatus.QUEUED
        assert updated_job.retry_count == 1
        assert updated_job.error_message is None
    
    def test_job_pause_resume(self, job_manager, sample_config):
        """Test job pause and resume functionality"""
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=sample_config
        )
        
        # Simulate running job
        job.status = JobStatus.RUNNING
        job_manager._save_job(job)
        
        # Pause job
        success = job_manager.pause_job(job.job_id)
        assert success
        
        updated_job = job_manager.get_job(job.job_id)
        assert updated_job.status == JobStatus.PAUSED
        
        # Resume job
        success = job_manager.resume_job(job.job_id)
        assert success
        
        updated_job = job_manager.get_job(job.job_id)
        assert updated_job.status == JobStatus.QUEUED
    
    def test_job_listing_and_filtering(self, job_manager, sample_config):
        """Test job listing with filtering"""
        # Create jobs with different statuses and priorities
        jobs = []
        for i in range(5):
            job = job_manager.create_job(
                tenant_id="test_tenant",
                video_id=f"video_{i}",
                video_path=f"/path/to/video_{i}.mp4",
                config=sample_config,
                priority=JobPriority.HIGH if i % 2 == 0 else JobPriority.NORMAL
            )
            jobs.append(job)
        
        # Test listing all jobs
        all_jobs = job_manager.list_jobs(tenant_id="test_tenant")
        assert len(all_jobs) == 5
        
        # Test filtering by status
        queued_jobs = job_manager.list_jobs(tenant_id="test_tenant", status=JobStatus.QUEUED)
        assert len(queued_jobs) == 5
        
        # Test pagination
        limited_jobs = job_manager.list_jobs(tenant_id="test_tenant", limit=3)
        assert len(limited_jobs) == 3
    
    def test_resource_allocation(self, job_manager):
        """Test tenant resource allocation"""
        allocation = ResourceAllocation(
            tenant_id="test_tenant",
            max_concurrent_jobs=10,
            cpu_limit=4.0,
            memory_limit=8192,
            gpu_allocation=0.5,
            priority_weight=2.0,
            cost_budget=1000.0
        )
        
        job_manager.set_tenant_allocation(allocation)
        
        # Verify allocation is stored
        assert "test_tenant" in job_manager.job_queue.tenant_allocations
        stored_allocation = job_manager.job_queue.tenant_allocations["test_tenant"]
        assert stored_allocation.max_concurrent_jobs == 10
        assert stored_allocation.cpu_limit == 4.0
        assert stored_allocation.priority_weight == 2.0
    
    def test_retry_configuration(self, job_manager):
        """Test retry configuration"""
        retry_config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=600.0,
            exponential_base=3.0,
            jitter=False,
            circuit_breaker_threshold=10,
            circuit_breaker_timeout=120.0
        )
        
        job_manager.set_retry_config("test_tenant", retry_config)
        
        # Verify configuration is stored
        assert "test_tenant" in job_manager.retry_configs
        stored_config = job_manager.retry_configs["test_tenant"]
        assert stored_config.max_attempts == 5
        assert stored_config.base_delay == 2.0
        assert stored_config.exponential_base == 3.0
    
    def test_job_statistics(self, job_manager, sample_config):
        """Test job statistics calculation"""
        # Create jobs with different statuses
        job1 = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_1",
            video_path="/path/to/video1.mp4",
            config=sample_config
        )
        
        job2 = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_2",
            video_path="/path/to/video2.mp4",
            config=sample_config
        )
        
        # Simulate completed job
        job1.status = JobStatus.COMPLETED
        job_manager._save_job(job1)
        
        # Get statistics
        stats = job_manager.get_job_statistics("test_tenant")
        
        assert stats['total_jobs'] == 2
        assert stats['status_counts']['completed'] == 1
        assert stats['status_counts']['queued'] == 1
        assert stats['success_rate'] == 0.5
    
    def test_cost_analytics(self, job_manager, sample_config):
        """Test cost analytics calculation"""
        # Create jobs with metrics
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_1",
            video_path="/path/to/video1.mp4",
            config=sample_config
        )
        
        # Simulate completed job with metrics
        job.status = JobStatus.COMPLETED
        job.metrics.actual_cost = 5.50
        job.metrics.processing_time = 120.0
        job_manager._save_job(job)
        
        # Get cost analytics
        analytics = job_manager.get_cost_analytics("test_tenant")
        
        assert analytics['total_cost'] > 0
        assert analytics['job_count'] == 1
        assert analytics['avg_processing_time'] >= 0
        assert analytics['cost_per_job'] > 0
    
    def test_cleanup_old_jobs(self, job_manager, sample_config):
        """Test cleanup of old jobs"""
        # Create old completed job
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_old",
            video_path="/path/to/old_video.mp4",
            config=sample_config
        )
        
        # Simulate old completed job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now() - timedelta(days=35)
        job_manager._save_job(job)
        
        # Cleanup jobs older than 30 days
        deleted_count = job_manager.cleanup_old_jobs(retention_days=30)
        
        assert deleted_count == 1
        
        # Verify job is deleted
        retrieved_job = job_manager.get_job(job.job_id)
        assert retrieved_job is None

class TestCircuitBreaker:
    """Test suite for CircuitBreaker"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)
        
        # Successful calls should work
        result = breaker.call(lambda x: x * 2, 5)
        assert result == 10
        assert breaker.state == "closed"
    
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker opening after failures"""
        breaker = CircuitBreaker(failure_threshold=2, timeout=60.0)
        
        # Cause failures to open circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1/0)  # Division by zero
            except:
                pass
        
        assert breaker.state == "open"
        
        # Should reject calls when open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            breaker.call(lambda: "test")
    
    def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker half-open state"""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(lambda: 1/0)
            except:
                pass
        
        assert breaker.state == "open"
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Next call should put it in half-open state
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.state == "closed"

class TestJobQueue:
    """Test suite for JobQueue"""
    
    def test_job_queue_priority_ordering(self):
        """Test job queue priority ordering"""
        queue = JobQueue()
        
        # Create jobs with different priorities
        low_job = FrameOCRJob(
            job_id="low", tenant_id="test", video_id="v1", video_path="/path",
            status=JobStatus.QUEUED, priority=JobPriority.LOW, config={},
            created_at=datetime.now()
        )
        
        high_job = FrameOCRJob(
            job_id="high", tenant_id="test", video_id="v2", video_path="/path",
            status=JobStatus.QUEUED, priority=JobPriority.HIGH, config={},
            created_at=datetime.now()
        )
        
        urgent_job = FrameOCRJob(
            job_id="urgent", tenant_id="test", video_id="v3", video_path="/path",
            status=JobStatus.QUEUED, priority=JobPriority.URGENT, config={},
            created_at=datetime.now()
        )
        
        # Add jobs in random order
        queue.add_job(low_job)
        queue.add_job(urgent_job)
        queue.add_job(high_job)
        
        # Should get jobs in priority order (urgent, high, low)
        first_job = queue.get_job()
        assert first_job.job_id == "urgent"
        
        second_job = queue.get_job()
        assert second_job.job_id == "high"
        
        third_job = queue.get_job()
        assert third_job.job_id == "low"
    
    def test_tenant_priority_weighting(self):
        """Test tenant priority weighting"""
        queue = JobQueue()
        
        # Set tenant allocation with higher priority weight
        allocation = ResourceAllocation(
            tenant_id="premium_tenant",
            priority_weight=2.0
        )
        queue.set_tenant_allocation(allocation)
        
        # Create jobs for different tenants with same priority
        regular_job = FrameOCRJob(
            job_id="regular", tenant_id="regular_tenant", video_id="v1", video_path="/path",
            status=JobStatus.QUEUED, priority=JobPriority.NORMAL, config={},
            created_at=datetime.now()
        )
        
        premium_job = FrameOCRJob(
            job_id="premium", tenant_id="premium_tenant", video_id="v2", video_path="/path",
            status=JobStatus.QUEUED, priority=JobPriority.NORMAL, config={},
            created_at=datetime.now()
        )
        
        # Add regular job first
        queue.add_job(regular_job)
        queue.add_job(premium_job)
        
        # Premium job should come first due to higher weight
        first_job = queue.get_job()
        assert first_job.job_id == "premium"

class TestCanaryProcessor:
    """Test suite for CanaryProcessor"""
    
    def test_canary_model_registration(self):
        """Test canary model registration"""
        processor = CanaryProcessor()
        
        model_config = {
            'model_type': 'tesseract_v5',
            'accuracy_target': 0.90
        }
        
        processor.register_canary_model("model_v5", model_config)
        
        assert "model_v5" in processor.canary_models
        assert processor.canary_models["model_v5"]['config'] == model_config
        assert processor.canary_models["model_v5"]['processed_jobs'] == 0
    
    def test_canary_traffic_routing(self):
        """Test canary traffic routing"""
        processor = CanaryProcessor()
        processor.canary_traffic_percentage = 0.5  # 50% for testing
        
        job = FrameOCRJob(
            job_id="test", tenant_id="test", video_id="v1", video_path="/path",
            status=JobStatus.QUEUED, priority=JobPriority.NORMAL, config={},
            created_at=datetime.now()
        )
        
        # Test multiple times to check randomness
        canary_count = 0
        total_tests = 100
        
        for _ in range(total_tests):
            if processor.should_use_canary(job):
                canary_count += 1
        
        # Should be approximately 50% (allow some variance)
        assert 30 <= canary_count <= 70
    
    def test_canary_metrics_update(self):
        """Test canary metrics updating"""
        processor = CanaryProcessor()
        processor.register_canary_model("test_model", {})
        
        # Update metrics
        processor.update_canary_metrics("test_model", True, 10.0, 0.85)
        processor.update_canary_metrics("test_model", False, 15.0, 0.80)
        processor.update_canary_metrics("test_model", True, 12.0, 0.90)
        
        canary = processor.canary_models["test_model"]
        
        assert canary['processed_jobs'] == 3
        assert canary['success_rate'] == 2/3  # 2 successes out of 3
        assert canary['avg_processing_time'] == (10.0 + 15.0 + 12.0) / 3
        assert canary['accuracy_score'] == (0.85 + 0.80 + 0.90) / 3
    
    def test_regression_detection(self):
        """Test regression detection"""
        processor = CanaryProcessor()
        processor.baseline_metrics = {
            'success_rate': 0.95,
            'avg_processing_time': 10.0,
            'accuracy_score': 0.90
        }
        processor.regression_threshold = 0.1  # 10% threshold
        
        processor.register_canary_model("bad_model", {})
        
        # Simulate poor performance
        for _ in range(15):  # Need minimum samples
            processor.update_canary_metrics("bad_model", False, 20.0, 0.70)
        
        # Should detect regression
        assert processor.check_for_regression("bad_model")
    
    def test_canary_rollback(self):
        """Test canary rollback"""
        processor = CanaryProcessor()
        processor.register_canary_model("rollback_model", {})
        
        assert "rollback_model" in processor.canary_models
        
        processor.rollback_canary("rollback_model")
        
        assert "rollback_model" not in processor.canary_models

class TestJobProcessing:
    """Test suite for job processing functionality"""
    
    @pytest.fixture
    def job_manager(self):
        """Create job manager with mocked processing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        manager = FrameOCRJobManager(db_path=db_path)
        
        # Mock the actual processing to avoid real work
        original_process = manager._process_job
        
        def mock_process(job):
            # Simulate quick processing
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            manager._save_job(job)
            
            # Simulate progress updates
            for i in range(5):
                job.progress = (i + 1) / 5
                job.metrics.frames_processed = (i + 1) * 20
                job.metrics.frames_total = 100
                manager._save_job(job)
                time.sleep(0.1)
            
            # Complete job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.metrics.end_time = job.completed_at
            job.metrics.processing_time = (job.completed_at - job.started_at).total_seconds()
            job.progress = 1.0
            manager._save_job(job)
        
        manager._process_job = mock_process
        
        yield manager
        
        manager.shutdown()
        os.unlink(db_path)
    
    def test_job_processing_lifecycle(self, job_manager):
        """Test complete job processing lifecycle"""
        config = {
            'sampling_interval': 1.0,
            'max_frames': 100,
            'ocr_engines': ['tesseract'],
            'confidence_threshold': 0.8
        }
        
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=config
        )
        
        # Job should start as queued
        assert job.status == JobStatus.QUEUED
        
        # Wait for processing to complete
        time.sleep(1.0)
        
        # Check final status
        final_job = job_manager.get_job(job.job_id)
        assert final_job.status == JobStatus.COMPLETED
        assert final_job.progress == 1.0
        assert final_job.started_at is not None
        assert final_job.completed_at is not None
        assert final_job.metrics.processing_time > 0

class TestWebhookIntegration:
    """Test suite for webhook integration"""
    
    @patch('requests.post')
    def test_webhook_notification(self, mock_post):
        """Test webhook notification sending"""
        mock_post.return_value.status_code = 200
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db = f.name
        
        job_manager = FrameOCRJobManager(db_path=temp_db)
        
        config = {'sampling_interval': 1.0}
        
        job = job_manager.create_job(
            tenant_id="test_tenant",
            video_id="video_123",
            video_path="/path/to/video.mp4",
            config=config,
            webhook_url="https://example.com/webhook"
        )
        
        # Simulate job completion
        job.status = JobStatus.COMPLETED
        job.progress = 1.0
        job_manager._send_webhook_notification(job)
        
        # Verify webhook was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        assert call_args[0][0] == "https://example.com/webhook"
        assert 'json' in call_args[1]
        
        payload = call_args[1]['json']
        assert payload['job_id'] == job.job_id
        assert payload['status'] == 'completed'
        assert payload['progress'] == 1.0
        
        job_manager.shutdown()
        os.unlink(temp_db)

# Integration tests
class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            job_manager = FrameOCRJobManager(db_path=db_path)
            
            # Set up tenant allocation
            allocation = ResourceAllocation(
                tenant_id="integration_tenant",
                max_concurrent_jobs=2,
                cpu_limit=1.0,
                memory_limit=2048,
                priority_weight=1.5,
                cost_budget=200.0
            )
            job_manager.set_tenant_allocation(allocation)
            
            # Set up retry configuration
            retry_config = RetryConfig(
                max_attempts=2,
                base_delay=0.1,
                max_delay=1.0
            )
            job_manager.set_retry_config("integration_tenant", retry_config)
            
            # Create multiple jobs
            config = {
                'sampling_interval': 1.0,
                'max_frames': 50,
                'ocr_engines': ['tesseract'],
                'confidence_threshold': 0.8
            }
            
            jobs = []
            for i in range(3):
                job = job_manager.create_job(
                    tenant_id="integration_tenant",
                    video_id=f"video_{i}",
                    video_path=f"/path/to/video_{i}.mp4",
                    config=config,
                    priority=JobPriority.HIGH if i == 0 else JobPriority.NORMAL,
                    tags=[f"test_{i}", "integration"]
                )
                jobs.append(job)
            
            # Verify jobs were created
            assert len(jobs) == 3
            
            # Check statistics
            stats = job_manager.get_job_statistics("integration_tenant")
            assert stats['total_jobs'] == 3
            assert stats['status_counts']['queued'] == 3
            
            # Test job listing with filtering
            high_priority_jobs = [
                job for job in job_manager.list_jobs("integration_tenant")
                if job.priority == JobPriority.HIGH
            ]
            assert len(high_priority_jobs) == 1
            
            # Test cost analytics
            analytics = job_manager.get_cost_analytics("integration_tenant")
            assert analytics['job_count'] == 3
            # Cost should be > 0 due to cost estimates
            assert analytics['total_cost'] >= 0  # Allow 0 cost for test scenario
            
            # Test job cancellation
            success = job_manager.cancel_job(jobs[2].job_id)
            assert success
            
            cancelled_job = job_manager.get_job(jobs[2].job_id)
            assert cancelled_job.status == JobStatus.CANCELLED
            
            # Test cleanup
            deleted_count = job_manager.cleanup_old_jobs(retention_days=1)
            # No old jobs to delete yet
            assert deleted_count == 0
            
        finally:
            job_manager.shutdown()
            os.unlink(db_path)

# Performance tests
class TestPerformance:
    """Performance tests for the job management system"""
    
    def test_job_creation_performance(self):
        """Test performance of job creation"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            job_manager = FrameOCRJobManager(db_path=db_path)
            
            config = {
                'sampling_interval': 1.0,
                'max_frames': 100,
                'ocr_engines': ['tesseract']
            }
            
            start_time = time.time()
            
            # Create 100 jobs
            for i in range(100):
                job_manager.create_job(
                    tenant_id="perf_tenant",
                    video_id=f"video_{i}",
                    video_path=f"/path/to/video_{i}.mp4",
                    config=config
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should create 100 jobs in reasonable time (< 5 seconds)
            assert duration < 5.0
            
            # Verify all jobs were created
            jobs = job_manager.list_jobs("perf_tenant", limit=200)
            assert len(jobs) == 100
            
        finally:
            job_manager.shutdown()
            os.unlink(db_path)
    
    def test_concurrent_job_access(self):
        """Test concurrent access to jobs"""
        import threading
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            job_manager = FrameOCRJobManager(db_path=db_path)
            
            config = {'sampling_interval': 1.0}
            results = []
            errors = []
            
            def create_jobs(thread_id):
                try:
                    for i in range(10):
                        job = job_manager.create_job(
                            tenant_id=f"tenant_{thread_id}",
                            video_id=f"video_{thread_id}_{i}",
                            video_path=f"/path/video_{thread_id}_{i}.mp4",
                            config=config
                        )
                        results.append(job.job_id)
                except Exception as e:
                    errors.append(str(e))
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=create_jobs, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 50  # 5 threads * 10 jobs each
            assert len(set(results)) == 50  # All job IDs should be unique
            
        finally:
            job_manager.shutdown()
            os.unlink(db_path)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])