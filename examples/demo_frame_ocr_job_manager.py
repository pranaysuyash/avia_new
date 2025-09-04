"""
Demo script for Frame OCR Job Management System

This script demonstrates the comprehensive enterprise job management capabilities
including job creation, monitoring, resource allocation, and analytics.
"""

import time
import json
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import logging

from frame_ocr_job_manager import (
    FrameOCRJobManager, JobStatus, JobPriority, ProcessingMode,
    ResourceAllocation, RetryConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_job_summary(job):
    """Print a summary of a job"""
    print(f"Job ID: {job.job_id[:8]}...")
    print(f"  Status: {job.status.value}")
    print(f"  Priority: {job.priority.value}")
    print(f"  Progress: {job.progress:.1%}")
    print(f"  Tenant: {job.tenant_id}")
    print(f"  Video: {job.video_id}")
    if job.error_message:
        print(f"  Error: {job.error_message}")
    if job.metrics:
        print(f"  Cost Estimate: ${job.metrics.cost_estimate:.3f}")
    print()

def demo_basic_job_management():
    """Demonstrate basic job management functionality"""
    print_section("Basic Job Management Demo")
    
    # Initialize job manager
    job_manager = FrameOCRJobManager("demo_jobs.db")
    
    try:
        # Sample configuration
        config = {
            'sampling_interval': 1.0,
            'max_frames': 500,
            'ocr_engines': ['tesseract', 'easyocr'],
            'confidence_threshold': 0.85,
            'languages': ['en', 'es'],
            'preprocessing_enabled': True
        }
        
        print("Creating sample jobs...")
        
        # Create jobs with different priorities
        jobs = []
        
        # High priority job
        job1 = job_manager.create_job(
            tenant_id="demo_tenant_1",
            video_id="urgent_news_video",
            video_path="/media/urgent_news.mp4",
            config=config,
            priority=JobPriority.URGENT,
            tags=["news", "urgent", "live"],
            webhook_url="https://example.com/webhooks/urgent"
        )
        jobs.append(job1)
        print(f"Created urgent job: {job1.job_id}")
        
        # Normal priority job with dependencies
        job2 = job_manager.create_job(
            tenant_id="demo_tenant_1",
            video_id="documentary_part1",
            video_path="/media/documentary_p1.mp4",
            config=config,
            priority=JobPriority.NORMAL,
            tags=["documentary", "educational"]
        )
        jobs.append(job2)
        print(f"Created normal job: {job2.job_id}")
        
        # Low priority job dependent on job2
        job3 = job_manager.create_job(
            tenant_id="demo_tenant_1",
            video_id="documentary_part2",
            video_path="/media/documentary_p2.mp4",
            config=config,
            priority=JobPriority.LOW,
            dependencies=[job2.job_id],
            tags=["documentary", "educational", "sequel"]
        )
        jobs.append(job3)
        print(f"Created dependent job: {job3.job_id}")
        
        # Scheduled job for later processing
        future_time = datetime.now() + timedelta(minutes=5)
        job4 = job_manager.create_job(
            tenant_id="demo_tenant_2",
            video_id="scheduled_content",
            video_path="/media/scheduled.mp4",
            config=config,
            priority=JobPriority.NORMAL,
            scheduled_at=future_time,
            tags=["scheduled", "batch"]
        )
        jobs.append(job4)
        print(f"Created scheduled job: {job4.job_id} (scheduled for {future_time})")
        
        print(f"\nCreated {len(jobs)} jobs successfully!")
        
        # Display job summaries
        print("\nJob Summaries:")
        for job in jobs:
            print_job_summary(job)
        
        return job_manager, jobs
        
    except Exception as e:
        logger.error(f"Error in basic job management demo: {e}")
        job_manager.shutdown()
        raise

def demo_resource_allocation(job_manager):
    """Demonstrate resource allocation and tenant management"""
    print_section("Resource Allocation Demo")
    
    # Set up different tenant allocations
    allocations = [
        ResourceAllocation(
            tenant_id="demo_tenant_1",
            max_concurrent_jobs=5,
            cpu_limit=2.0,
            memory_limit=4096,
            gpu_allocation=0.3,
            priority_weight=2.0,  # Premium tenant
            cost_budget=500.0
        ),
        ResourceAllocation(
            tenant_id="demo_tenant_2",
            max_concurrent_jobs=2,
            cpu_limit=1.0,
            memory_limit=2048,
            gpu_allocation=0.0,
            priority_weight=1.0,  # Standard tenant
            cost_budget=100.0
        ),
        ResourceAllocation(
            tenant_id="demo_tenant_3",
            max_concurrent_jobs=10,
            cpu_limit=4.0,
            memory_limit=8192,
            gpu_allocation=0.8,
            priority_weight=3.0,  # Enterprise tenant
            cost_budget=2000.0
        )
    ]
    
    print("Setting up tenant resource allocations...")
    for allocation in allocations:
        job_manager.set_tenant_allocation(allocation)
        print(f"Tenant {allocation.tenant_id}:")
        print(f"  Max Concurrent Jobs: {allocation.max_concurrent_jobs}")
        print(f"  CPU Limit: {allocation.cpu_limit} cores")
        print(f"  Memory Limit: {allocation.memory_limit} MB")
        print(f"  GPU Allocation: {allocation.gpu_allocation:.1%}")
        print(f"  Priority Weight: {allocation.priority_weight}x")
        print(f"  Monthly Budget: ${allocation.cost_budget}")
        print()
    
    # Set up retry configurations
    print("Configuring retry policies...")
    
    # Aggressive retry for premium tenant
    premium_retry = RetryConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=120.0,
        exponential_base=1.5,
        jitter=True,
        circuit_breaker_threshold=10,
        circuit_breaker_timeout=30.0
    )
    job_manager.set_retry_config("demo_tenant_1", premium_retry)
    print("Premium tenant: Aggressive retry policy (5 attempts, fast recovery)")
    
    # Conservative retry for standard tenant
    standard_retry = RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=300.0,
        exponential_base=2.0,
        jitter=True,
        circuit_breaker_threshold=5,
        circuit_breaker_timeout=60.0
    )
    job_manager.set_retry_config("demo_tenant_2", standard_retry)
    print("Standard tenant: Conservative retry policy (3 attempts, standard recovery)")
    
    # Enterprise retry for enterprise tenant
    enterprise_retry = RetryConfig(
        max_attempts=7,
        base_delay=0.1,
        max_delay=60.0,
        exponential_base=1.2,
        jitter=False,  # Predictable timing for enterprise
        circuit_breaker_threshold=15,
        circuit_breaker_timeout=15.0
    )
    job_manager.set_retry_config("demo_tenant_3", enterprise_retry)
    print("Enterprise tenant: Enterprise retry policy (7 attempts, rapid recovery)")

def demo_job_operations(job_manager, jobs):
    """Demonstrate job operations and lifecycle management"""
    print_section("Job Operations Demo")
    
    if not jobs:
        print("No jobs available for operations demo")
        return
    
    # Demonstrate job status checking
    print("Current job statuses:")
    for job in jobs:
        current_job = job_manager.get_job(job.job_id)
        print(f"Job {job.job_id[:8]}: {current_job.status.value} ({current_job.progress:.1%})")
    
    print("\nDemonstrating job operations...")
    
    # Pause a running job (if any)
    running_jobs = [job for job in jobs if job_manager.get_job(job.job_id).status == JobStatus.RUNNING]
    if running_jobs:
        job_to_pause = running_jobs[0]
        print(f"\nPausing job {job_to_pause.job_id[:8]}...")
        success = job_manager.pause_job(job_to_pause.job_id)
        if success:
            print("Job paused successfully")
            
            # Wait a moment then resume
            time.sleep(2)
            print(f"Resuming job {job_to_pause.job_id[:8]}...")
            success = job_manager.resume_job(job_to_pause.job_id)
            if success:
                print("Job resumed successfully")
    
    # Simulate a job failure and retry
    if len(jobs) > 1:
        job_to_fail = jobs[1]
        print(f"\nSimulating failure for job {job_to_fail.job_id[:8]}...")
        
        # Manually set job as failed (in real scenario, this would happen during processing)
        failed_job = job_manager.get_job(job_to_fail.job_id)
        failed_job.status = JobStatus.FAILED
        failed_job.error_message = "Simulated processing error for demo"
        failed_job.completed_at = datetime.now()
        job_manager._save_job(failed_job)
        
        print("Job marked as failed")
        
        # Retry the job
        print(f"Retrying failed job {job_to_fail.job_id[:8]}...")
        success = job_manager.retry_job(job_to_fail.job_id)
        if success:
            retried_job = job_manager.get_job(job_to_fail.job_id)
            print(f"Job retried successfully (attempt #{retried_job.retry_count})")
    
    # Cancel a job
    if len(jobs) > 2:
        job_to_cancel = jobs[2]
        print(f"\nCancelling job {job_to_cancel.job_id[:8]}...")
        success = job_manager.cancel_job(job_to_cancel.job_id)
        if success:
            print("Job cancelled successfully")

def demo_monitoring_and_analytics(job_manager):
    """Demonstrate monitoring and analytics capabilities"""
    print_section("Monitoring and Analytics Demo")
    
    # Get overall statistics
    print("System-wide Statistics:")
    overall_stats = job_manager.get_job_statistics()
    print(f"Total Jobs: {overall_stats['total_jobs']}")
    print(f"Success Rate: {overall_stats['success_rate']:.1%}")
    print(f"Running Jobs: {overall_stats['running_jobs']}")
    print(f"Queue Size: {overall_stats['queue_size']}")
    print("\nStatus Distribution:")
    for status, count in overall_stats['status_counts'].items():
        print(f"  {status.title()}: {count}")
    
    # Get tenant-specific statistics
    tenants = ["demo_tenant_1", "demo_tenant_2", "demo_tenant_3"]
    
    print("\nTenant-specific Statistics:")
    for tenant in tenants:
        stats = job_manager.get_job_statistics(tenant)
        cost_analytics = job_manager.get_cost_analytics(tenant)
        
        print(f"\n{tenant}:")
        print(f"  Jobs: {stats['total_jobs']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print(f"  Total Cost: ${cost_analytics['total_cost']:.2f}")
        print(f"  Avg Processing Time: {cost_analytics['avg_processing_time']:.1f}s")
        print(f"  Cost per Job: ${cost_analytics['cost_per_job']:.3f}")
    
    # Demonstrate cost analytics with date range
    print("\nCost Analytics (Last 7 days):")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    weekly_analytics = job_manager.get_cost_analytics(
        tenant_id="demo_tenant_1",
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Total Cost: ${weekly_analytics['total_cost']:.2f}")
    print(f"Jobs Processed: {weekly_analytics['job_count']}")
    print(f"Average Processing Time: {weekly_analytics['avg_processing_time']:.1f}s")

def demo_advanced_features(job_manager):
    """Demonstrate advanced features"""
    print_section("Advanced Features Demo")
    
    # Demonstrate processing mode optimization
    print("Processing Mode Optimization:")
    
    modes = [ProcessingMode.PEAK, ProcessingMode.OFF_PEAK, ProcessingMode.BALANCED]
    
    for mode in modes:
        print(f"\nOptimizing for {mode.value} mode...")
        job_manager.optimize_scheduling(mode)
        print(f"Scheduling optimized for {mode.value} processing")
    
    # Demonstrate canary processing
    print("\nCanary Processing Demo:")
    
    canary_processor = job_manager.canary_processor
    
    # Register a canary model
    canary_config = {
        'model_type': 'tesseract_v5_beta',
        'accuracy_target': 0.92,
        'performance_target': 8.0
    }
    
    canary_processor.register_canary_model("tesseract_v5_beta", canary_config)
    print("Registered canary model: tesseract_v5_beta")
    
    # Simulate canary metrics
    print("Simulating canary model performance...")
    for i in range(20):
        success = i % 10 != 0  # 90% success rate
        processing_time = 7.5 + (i % 3) * 0.5  # Variable processing time
        accuracy = 0.91 + (i % 5) * 0.01  # Variable accuracy
        
        canary_processor.update_canary_metrics(
            "tesseract_v5_beta", success, processing_time, accuracy
        )
    
    canary_stats = canary_processor.canary_models["tesseract_v5_beta"]
    print(f"Canary Model Performance:")
    print(f"  Processed Jobs: {canary_stats['processed_jobs']}")
    print(f"  Success Rate: {canary_stats['success_rate']:.1%}")
    print(f"  Avg Processing Time: {canary_stats['avg_processing_time']:.1f}s")
    print(f"  Accuracy Score: {canary_stats['accuracy_score']:.1%}")
    
    # Check for regression
    has_regression = canary_processor.check_for_regression("tesseract_v5_beta")
    print(f"  Regression Detected: {'Yes' if has_regression else 'No'}")
    
    # Demonstrate circuit breaker
    print("\nCircuit Breaker Demo:")
    
    from frame_ocr_job_manager import CircuitBreaker
    
    breaker = CircuitBreaker(failure_threshold=3, timeout=5.0)
    
    print("Testing circuit breaker with failures...")
    
    # Cause failures to open circuit
    for i in range(5):
        try:
            if i < 3:
                # Successful calls
                result = breaker.call(lambda x: x * 2, i)
                print(f"  Call {i+1}: Success (result: {result})")
            else:
                # Failing calls
                breaker.call(lambda: 1/0)
        except Exception as e:
            print(f"  Call {i+1}: Failed ({type(e).__name__})")
    
    print(f"Circuit breaker state: {breaker.state}")

def demo_job_listing_and_filtering(job_manager):
    """Demonstrate job listing and filtering capabilities"""
    print_section("Job Listing and Filtering Demo")
    
    # List all jobs
    all_jobs = job_manager.list_jobs(limit=100)
    print(f"Total jobs in system: {len(all_jobs)}")
    
    # Filter by tenant
    tenant_jobs = job_manager.list_jobs(tenant_id="demo_tenant_1")
    print(f"Jobs for demo_tenant_1: {len(tenant_jobs)}")
    
    # Filter by status
    queued_jobs = job_manager.list_jobs(status=JobStatus.QUEUED)
    print(f"Queued jobs: {len(queued_jobs)}")
    
    completed_jobs = job_manager.list_jobs(status=JobStatus.COMPLETED)
    print(f"Completed jobs: {len(completed_jobs)}")
    
    failed_jobs = job_manager.list_jobs(status=JobStatus.FAILED)
    print(f"Failed jobs: {len(failed_jobs)}")
    
    # Demonstrate pagination
    print("\nPagination Demo:")
    page_size = 5
    page = 1
    
    while True:
        offset = (page - 1) * page_size
        page_jobs = job_manager.list_jobs(limit=page_size, offset=offset)
        
        if not page_jobs:
            break
        
        print(f"Page {page} ({len(page_jobs)} jobs):")
        for job in page_jobs:
            print(f"  {job.job_id[:8]} - {job.video_id} - {job.status.value}")
        
        page += 1
        if page > 3:  # Limit demo to 3 pages
            break

def demo_cleanup_and_maintenance(job_manager):
    """Demonstrate cleanup and maintenance operations"""
    print_section("Cleanup and Maintenance Demo")
    
    # Create some old jobs for cleanup demo
    print("Creating old jobs for cleanup demonstration...")
    
    config = {'sampling_interval': 1.0, 'max_frames': 10}
    
    old_job = job_manager.create_job(
        tenant_id="demo_tenant_cleanup",
        video_id="old_video",
        video_path="/path/to/old_video.mp4",
        config=config
    )
    
    # Simulate old completed job
    old_job.status = JobStatus.COMPLETED
    old_job.completed_at = datetime.now() - timedelta(days=35)  # 35 days old
    job_manager._save_job(old_job)
    
    print(f"Created old job: {old_job.job_id[:8]} (35 days old)")
    
    # Cleanup old jobs
    print("\nCleaning up jobs older than 30 days...")
    deleted_count = job_manager.cleanup_old_jobs(retention_days=30)
    print(f"Deleted {deleted_count} old jobs")
    
    # System health check
    print("\nSystem Health Check:")
    stats = job_manager.get_job_statistics()
    
    health_indicators = {
        "Queue Size": ("Normal" if stats['queue_size'] < 10 else "High", stats['queue_size']),
        "Running Jobs": ("Normal" if stats['running_jobs'] < 20 else "High", stats['running_jobs']),
        "Success Rate": ("Good" if stats['success_rate'] > 0.9 else "Needs Attention", f"{stats['success_rate']:.1%}"),
    }
    
    for indicator, (status, value) in health_indicators.items():
        print(f"  {indicator}: {status} ({value})")

def demo_concurrent_processing():
    """Demonstrate concurrent job processing"""
    print_section("Concurrent Processing Demo")
    
    job_manager = FrameOCRJobManager("demo_concurrent.db")
    
    try:
        config = {
            'sampling_interval': 0.5,
            'max_frames': 50,
            'ocr_engines': ['tesseract']
        }
        
        print("Creating multiple jobs for concurrent processing...")
        
        # Create jobs from multiple threads to simulate concurrent load
        def create_jobs_batch(batch_id, count):
            jobs = []
            for i in range(count):
                job = job_manager.create_job(
                    tenant_id=f"concurrent_tenant_{batch_id}",
                    video_id=f"video_{batch_id}_{i}",
                    video_path=f"/path/to/video_{batch_id}_{i}.mp4",
                    config=config,
                    priority=JobPriority.NORMAL,
                    tags=[f"batch_{batch_id}", "concurrent"]
                )
                jobs.append(job)
            return jobs
        
        # Use thread pool to create jobs concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for batch_id in range(3):
                future = executor.submit(create_jobs_batch, batch_id, 5)
                futures.append(future)
            
            all_jobs = []
            for future in futures:
                batch_jobs = future.result()
                all_jobs.extend(batch_jobs)
        
        print(f"Created {len(all_jobs)} jobs concurrently")
        
        # Monitor job processing
        print("\nMonitoring job processing...")
        
        start_time = time.time()
        processed_count = 0
        
        while processed_count < len(all_jobs) and (time.time() - start_time) < 30:
            current_stats = job_manager.get_job_statistics()
            completed = current_stats['status_counts'].get('completed', 0)
            failed = current_stats['status_counts'].get('failed', 0)
            cancelled = current_stats['status_counts'].get('cancelled', 0)
            
            processed_count = completed + failed + cancelled
            
            print(f"Progress: {processed_count}/{len(all_jobs)} jobs processed "
                  f"(Completed: {completed}, Failed: {failed}, Cancelled: {cancelled})")
            
            if processed_count < len(all_jobs):
                time.sleep(2)
        
        print(f"\nConcurrent processing demo completed in {time.time() - start_time:.1f} seconds")
        
    finally:
        job_manager.shutdown()

def main():
    """Main demo function"""
    print("🎬 Frame OCR Job Management System Demo")
    print("=" * 60)
    print("This demo showcases enterprise-grade job management capabilities")
    print("including distributed processing, resource allocation, and monitoring.")
    
    try:
        # Basic job management
        job_manager, jobs = demo_basic_job_management()
        
        # Resource allocation
        demo_resource_allocation(job_manager)
        
        # Wait a moment for jobs to start processing
        print("\nWaiting for jobs to start processing...")
        time.sleep(3)
        
        # Job operations
        demo_job_operations(job_manager, jobs)
        
        # Monitoring and analytics
        demo_monitoring_and_analytics(job_manager)
        
        # Advanced features
        demo_advanced_features(job_manager)
        
        # Job listing and filtering
        demo_job_listing_and_filtering(job_manager)
        
        # Cleanup and maintenance
        demo_cleanup_and_maintenance(job_manager)
        
        # Final statistics
        print_section("Final System Statistics")
        final_stats = job_manager.get_job_statistics()
        print(f"Total Jobs Created: {final_stats['total_jobs']}")
        print(f"Final Success Rate: {final_stats['success_rate']:.1%}")
        print(f"Jobs Still Running: {final_stats['running_jobs']}")
        
        # Shutdown gracefully
        print("\nShutting down job manager...")
        job_manager.shutdown()
        print("Job manager shutdown complete")
        
        # Concurrent processing demo (separate instance)
        demo_concurrent_processing()
        
        print_section("Demo Complete")
        print("The Frame OCR Job Management System demo has completed successfully!")
        print("Key features demonstrated:")
        print("✓ Enterprise job lifecycle management")
        print("✓ Multi-tenant resource allocation")
        print("✓ Intelligent retry and circuit breaker patterns")
        print("✓ Comprehensive monitoring and analytics")
        print("✓ Advanced scheduling and optimization")
        print("✓ Canary processing and rollback")
        print("✓ Concurrent processing capabilities")
        print("✓ Data cleanup and maintenance")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed with error: {e}")
        raise

if __name__ == "__main__":
    main()