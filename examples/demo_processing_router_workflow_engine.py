#!/usr/bin/env python3
"""
Demo: Processing Router and Workflow Engine
Demonstrates intelligent media processing routing and workflow orchestration
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path

from processing_router_workflow_engine import (
    ProcessingRouterWorkflowEngine, 
    MediaType, 
    ContentComplexity,
    ProcessingStrategy,
    WorkflowPriority
)

async def demo_basic_routing():
    """Demonstrate basic routing functionality"""
    print("🎯 Demo: Basic Processing Routing")
    print("=" * 50)
    
    # Initialize router
    router = ProcessingRouterWorkflowEngine(max_concurrent_jobs=3)
    
    # Create test files
    test_files = []
    
    # Audio file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b"fake audio data" * 1000)  # Make it larger for complexity testing
        test_files.append(f.name)
    
    # Video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b"fake video data" * 5000)  # Larger file
        test_files.append(f.name)
    
    # Document file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"fake pdf data" * 100)
        test_files.append(f.name)
    
    try:
        for i, test_file in enumerate(test_files):
            print(f"\n📁 Processing file {i+1}: {Path(test_file).suffix}")
            
            # Analyze content
            analysis = await router.analyze_content(test_file)
            print(f"   📊 Media Type: {analysis.media_type.value}")
            print(f"   📊 Complexity: {analysis.complexity.value}")
            print(f"   📊 File Size: {analysis.file_size_mb:.2f} MB")
            print(f"   📊 Quality Score: {analysis.quality_score:.2f}")
            print(f"   📊 Processing Requirements: {analysis.processing_requirements}")
            
            # Select route
            route = router.select_processing_route(analysis)
            print(f"   🛤️  Selected Route: {route.name}")
            print(f"   🛤️  Strategy: {route.strategy.value}")
            print(f"   🛤️  Processing Steps: {route.processing_steps}")
            print(f"   🛤️  Estimated Duration: {route.estimated_duration}s")
            
            # Start processing
            job_id = await router.process_media(test_file, priority=WorkflowPriority.NORMAL)
            print(f"   ⚙️  Job ID: {job_id}")
    
    finally:
        # Cleanup test files
        for test_file in test_files:
            try:
                os.unlink(test_file)
            except:
                pass
        
        await router.cleanup()

async def demo_concurrent_processing():
    """Demonstrate concurrent processing capabilities"""
    print("\n🔄 Demo: Concurrent Processing")
    print("=" * 50)
    
    router = ProcessingRouterWorkflowEngine(max_concurrent_jobs=3)
    
    # Create multiple test files
    test_files = []
    for i in range(5):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b"audio data" * (1000 * (i + 1)))  # Different sizes
            test_files.append(f.name)
    
    try:
        # Submit all jobs
        job_ids = []
        for i, test_file in enumerate(test_files):
            priority = WorkflowPriority.HIGH if i < 2 else WorkflowPriority.NORMAL
            job_id = await router.process_media(test_file, priority=priority)
            job_ids.append(job_id)
            print(f"📤 Submitted job {i+1}: {job_id} (Priority: {priority.value})")
        
        # Monitor all jobs
        print("\n📈 Monitoring concurrent jobs...")
        completed_jobs = set()
        
        while len(completed_jobs) < len(job_ids):
            for job_id in job_ids:
                if job_id not in completed_jobs:
                    status = router.get_job_status(job_id)
                    if status:
                        print(f"   Job {job_id[:8]}: {status['status']} ({status['progress']:.1%})")
                        if status['status'] in ['completed', 'failed', 'cancelled']:
                            completed_jobs.add(job_id)
            
            if len(completed_jobs) < len(job_ids):
                await asyncio.sleep(2)
        
        # Show final results
        print("\n✅ All jobs completed!")
        metrics = router.get_performance_metrics()
        print(f"📊 Success Rate: {metrics['successful_jobs']}/{metrics['total_jobs']}")
        print(f"📊 Average Processing Time: {metrics['average_processing_time']:.2f}s")
    
    finally:
        # Cleanup
        for test_file in test_files:
            try:
                os.unlink(test_file)
            except:
                pass
        
        await router.cleanup()

async def demo_fallback_strategies():
    """Demonstrate fallback strategies"""
    print("\n🔄 Demo: Fallback Strategies")
    print("=" * 50)
    
    router = ProcessingRouterWorkflowEngine(max_concurrent_jobs=2)
    
    # Create a test file that might trigger fallbacks
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b"complex audio data" * 10000)  # Large file for complex processing
        test_file = f.name
    
    try:
        # Analyze content
        analysis = await router.analyze_content(test_file)
        print(f"📊 Content Analysis:")
        print(f"   Media Type: {analysis.media_type.value}")
        print(f"   Complexity: {analysis.complexity.value}")
        
        # Select route (should select professional route for complex content)
        route = router.select_processing_route(analysis)
        print(f"🛤️  Selected Route: {route.name}")
        print(f"   Fallback Routes: {route.fallback_routes}")
        
        # Process with potential fallbacks
        job_id = await router.process_media(test_file)
        print(f"⚙️  Processing job: {job_id}")
        
        # Monitor for fallback usage
        while True:
            status = router.get_job_status(job_id)
            if status:
                print(f"   Status: {status['status']} ({status['progress']:.1%})")
                
                # Check if fallback was used
                if 'fallback_used' in status.get('results', {}):
                    print(f"🔄 Fallback route used: {status['results']['fallback_used']}")
                
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
            
            await asyncio.sleep(1)
        
        # Show final status
        final_status = router.get_job_status(job_id)
        if final_status and final_status['status'] == 'completed':
            print("✅ Processing completed successfully!")
            if 'fallback_used' in final_status.get('results', {}):
                print(f"   Used fallback: {final_status['results']['fallback_used']}")
        else:
            print("❌ Processing failed")
    
    finally:
        os.unlink(test_file)
        await router.cleanup()

async def demo_custom_routes():
    """Demonstrate custom route selection"""
    print("\n🎯 Demo: Custom Route Selection")
    print("=" * 50)
    
    router = ProcessingRouterWorkflowEngine(max_concurrent_jobs=2)
    
    # Show available routes
    print("📋 Available Processing Routes:")
    for route_id, route in router.processing_routes.items():
        print(f"   {route_id}: {route.name} ({route.strategy.value})")
    
    # Create test file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b"audio data" * 2000)
        test_file = f.name
    
    try:
        # Test automatic route selection
        print(f"\n🤖 Automatic Route Selection:")
        analysis = await router.analyze_content(test_file)
        auto_route = router.select_processing_route(analysis)
        print(f"   Selected: {auto_route.name}")
        
        # Test custom route selection
        print(f"\n👤 Custom Route Selection:")
        custom_route_id = "audio_professional"
        job_id = await router.process_media(test_file, custom_route=custom_route_id)
        print(f"   Using custom route: {custom_route_id}")
        print(f"   Job ID: {job_id}")
        
        # Monitor custom route processing
        while True:
            status = router.get_job_status(job_id)
            if status:
                print(f"   Status: {status['status']} ({status['progress']:.1%})")
                if status['status'] in ['completed', 'failed', 'cancelled']:
                    break
            await asyncio.sleep(1)
        
        print("✅ Custom route processing completed!")
    
    finally:
        os.unlink(test_file)
        await router.cleanup()

async def demo_performance_monitoring():
    """Demonstrate performance monitoring"""
    print("\n📊 Demo: Performance Monitoring")
    print("=" * 50)
    
    router = ProcessingRouterWorkflowEngine(max_concurrent_jobs=2)
    
    # Process several files to generate metrics
    test_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b"audio data" * (500 * (i + 1)))
            test_files.append(f.name)
    
    try:
        job_ids = []
        
        # Submit jobs
        for i, test_file in enumerate(test_files):
            job_id = await router.process_media(test_file)
            job_ids.append(job_id)
            print(f"📤 Submitted job {i+1}: {job_id[:8]}")
        
        # Monitor performance metrics during processing
        print("\n📈 Real-time Performance Metrics:")
        completed = 0
        while completed < len(job_ids):
            metrics = router.get_performance_metrics()
            print(f"   Active Jobs: {metrics['active_jobs']}")
            print(f"   Queued Jobs: {metrics['queued_jobs']}")
            print(f"   Total Processed: {metrics['total_jobs']}")
            print(f"   Success Rate: {metrics['successful_jobs']}/{metrics['total_jobs']}")
            print(f"   Avg Processing Time: {metrics['average_processing_time']:.2f}s")
            print("   " + "-" * 40)
            
            # Check completed jobs
            completed = sum(1 for job_id in job_ids 
                          if router.get_job_status(job_id) and 
                          router.get_job_status(job_id)['status'] in ['completed', 'failed'])
            
            await asyncio.sleep(2)
        
        # Final metrics
        final_metrics = router.get_performance_metrics()
        print("\n📊 Final Performance Summary:")
        print(f"   Total Jobs Processed: {final_metrics['total_jobs']}")
        print(f"   Successful Jobs: {final_metrics['successful_jobs']}")
        print(f"   Failed Jobs: {final_metrics['failed_jobs']}")
        print(f"   Success Rate: {final_metrics['successful_jobs']/final_metrics['total_jobs']*100:.1f}%")
        print(f"   Average Processing Time: {final_metrics['average_processing_time']:.2f}s")
        print(f"   Available Routes: {final_metrics['available_routes']}")
    
    finally:
        # Cleanup
        for test_file in test_files:
            try:
                os.unlink(test_file)
            except:
                pass
        
        await router.cleanup()

async def main():
    """Run all demos"""
    print("🚀 Processing Router and Workflow Engine Demo")
    print("=" * 60)
    
    try:
        await demo_basic_routing()
        await demo_concurrent_processing()
        await demo_fallback_strategies()
        await demo_custom_routes()
        await demo_performance_monitoring()
        
        print("\n🎉 All demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())