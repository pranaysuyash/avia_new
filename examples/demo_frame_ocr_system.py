"""
Frame OCR Indexing System Demo

This demo showcases the comprehensive Frame OCR data models and database
functionality including multi-tenancy, temporal consolidation, and data lineage.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from frame_ocr_models import (
    FrameOCRJob, FrameOCRResult, TextSegment, BoundingBox, OCRJobConfig,
    JobStatus, OCREngine, RegionType, SamplingStrategy,
    ModelValidator, ModelSerializer
)
from frame_ocr_database import FrameOCRDatabase, DatabaseConfig


def demo_data_models():
    """Demonstrate data model functionality"""
    print("=== Frame OCR Data Models Demo ===\n")
    
    # 1. Create OCR Job Configuration
    print("1. Creating OCR Job Configuration...")
    config = OCRJobConfig(
        sampling_strategy=SamplingStrategy.ADAPTIVE,
        sampling_interval=2.0,
        max_frames=500,
        ocr_engines=[OCREngine.TESSERACT, OCREngine.EASYOCR],
        confidence_threshold=0.7,
        languages=["en", "es"],
        preprocessing_enabled=True,
        temporal_consolidation_enabled=True,
        stability_threshold=0.8
    )
    
    print(f"  - Sampling Strategy: {config.sampling_strategy.value}")
    print(f"  - OCR Engines: {[engine.value for engine in config.ocr_engines]}")
    print(f"  - Languages: {config.languages}")
    print(f"  - Estimated cost for 300s video: ${config.estimate_cost(300):.4f}")
    
    # 2. Create OCR Job
    print("\n2. Creating OCR Job...")
    
    # Create temporary video file for demo
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_video.write(b"fake demo video content")
    temp_video.close()
    
    job = FrameOCRJob(
        video_id="demo_video_001",
        video_path=temp_video.name,
        tenant_id="tenant_demo_123",
        user_id="user_demo_456",
        config=config
    )
    
    print(f"  - Job ID: {job.job_id}")
    print(f"  - Video ID: {job.video_id}")
    print(f"  - Status: {job.status.value}")
    print(f"  - Created: {job.created_at}")
    
    # 3. Simulate job lifecycle
    print("\n3. Simulating Job Lifecycle...")
    
    # Start processing
    job.start_processing("processing_node_1")
    print(f"  - Started processing on: {job.processing_node}")
    print(f"  - Status: {job.status.value}")
    
    # Update progress
    job.update_progress(150, 300)
    print(f"  - Progress: {job.progress:.1%} ({job.frames_processed}/{job.total_frames})")
    
    # Add data lineage
    job.add_lineage_entry("frame_extraction", {
        "total_frames": 300,
        "extraction_method": "ffmpeg",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    job.add_lineage_entry("ocr_processing", {
        "engine": "tesseract",
        "preprocessing": True,
        "confidence_threshold": 0.7
    })
    
    print(f"  - Data lineage entries: {len(job.data_lineage.get('operations', []))}")
    
    # Complete job
    job.complete_job(actual_cost=2.45)
    print(f"  - Completed with cost: ${job.actual_cost}")
    print(f"  - Final status: {job.status.value}")
    
    # 4. Create OCR Results with Text Segments
    print("\n4. Creating OCR Results...")
    
    # Create bounding boxes
    bbox1 = BoundingBox(
        x=50, y=400, width=200, height=30,
        confidence=0.92, region_type=RegionType.LOWER_THIRD
    )
    
    bbox2 = BoundingBox(
        x=100, y=50, width=300, height=40,
        confidence=0.88, region_type=RegionType.TITLE
    )
    
    # Create text segments
    segment1 = TextSegment(
        text="Breaking News Alert",
        confidence=0.95,
        language="en",
        bounding_box=bbox1,
        region_classification=RegionType.LOWER_THIRD
    )
    
    segment2 = TextSegment(
        text="Live Coverage",
        confidence=0.89,
        language="en",
        bounding_box=bbox2,
        region_classification=RegionType.TITLE
    )
    
    # Create OCR results
    results = []
    for i, (timestamp, text, segment) in enumerate([
        (10.5, "Breaking News Alert", segment1),
        (15.2, "Live Coverage", segment2),
        (20.8, "Breaking News Alert", segment1),  # Repeated text
    ]):
        result = FrameOCRResult(
            job_id=job.job_id,
            video_id=job.video_id,
            tenant_id=job.tenant_id,
            timestamp=timestamp,
            frame_number=int(timestamp * 30),  # 30 FPS
            text=text,
            confidence=segment.confidence,
            language="en",
            bounding_boxes=[segment.bounding_box] if segment.bounding_box else [],
            text_segments=[segment],
            ocr_engine=OCREngine.TESSERACT,
            preprocessing_applied=True,
            processing_time=0.15
        )
        results.append(result)
        print(f"  - Result {i+1}: '{text}' at {timestamp}s (confidence: {segment.confidence:.2f})")
    
    # 5. Demonstrate temporal consolidation
    print("\n5. Demonstrating Temporal Consolidation...")
    
    # Simulate text appearing multiple times
    repeated_segment = TextSegment(
        text="Breaking News Alert",
        confidence=0.92,
        language="en"
    )
    
    # Update occurrence to simulate temporal tracking
    repeated_segment.update_occurrence(datetime.now(timezone.utc), 0.94)
    repeated_segment.update_occurrence(datetime.now(timezone.utc) + timedelta(seconds=5), 0.91)
    
    print(f"  - Text: '{repeated_segment.text}'")
    print(f"  - Occurrences: {repeated_segment.occurrence_count}")
    print(f"  - Stability Score: {repeated_segment.stability_score:.3f}")
    print(f"  - Average Confidence: {repeated_segment.confidence:.3f}")
    
    # 6. Model Validation
    print("\n6. Model Validation...")
    
    # Validate job
    job_errors = ModelValidator.validate_job(job)
    print(f"  - Job validation errors: {len(job_errors)}")
    if job_errors:
        for error in job_errors:
            print(f"    * {error}")
    
    # Validate results
    for i, result in enumerate(results):
        result_errors = ModelValidator.validate_result(result)
        print(f"  - Result {i+1} validation errors: {len(result_errors)}")
    
    # 7. Serialization
    print("\n7. Serialization Demo...")
    
    # Serialize job to JSON
    job_json = ModelSerializer.serialize_job(job)
    print(f"  - Job JSON size: {len(job_json)} characters")
    
    # Deserialize and verify
    restored_job = ModelSerializer.deserialize_job(job_json)
    print(f"  - Serialization integrity: {job.job_id == restored_job.job_id}")
    
    # Clean up temporary video file
    try:
        os.unlink(temp_video.name)
    except:
        pass
    
    return job, results


def demo_database_operations():
    """Demonstrate database functionality"""
    print("\n=== Database Operations Demo ===\n")
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Create temporary video files for validation
    temp_video1 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_video1.write(b"fake video content for testing")
    temp_video1.close()
    
    temp_video2 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_video2.write(b"fake video content for testing")
    temp_video2.close()
    
    try:
        # Configure database
        config = DatabaseConfig()
        config.db_type = 'sqlite'
        config.db_name = temp_db.name
        
        # Initialize database
        db = FrameOCRDatabase(config)
        print("1. Database initialized successfully")
        
        # Create tenants for multi-tenancy demo
        print("\n2. Creating Tenants...")
        tenant1_id = db.create_tenant("News Corp", {
            "max_jobs": 1000,
            "retention_days": 365,
            "features": ["ocr", "temporal_consolidation"]
        })
        
        tenant2_id = db.create_tenant("Education Inc", {
            "max_jobs": 500,
            "retention_days": 180,
            "features": ["ocr", "multilingual"]
        })
        
        print(f"  - Tenant 1 (News Corp): {tenant1_id}")
        print(f"  - Tenant 2 (Education Inc): {tenant2_id}")
        
        # Create jobs for different tenants
        print("\n3. Creating Jobs for Different Tenants...")
        
        # Job for Tenant 1
        config1 = OCRJobConfig(
            sampling_strategy=SamplingStrategy.KEYFRAME,
            ocr_engines=[OCREngine.TESSERACT, OCREngine.GOOGLE_VISION],
            languages=["en"]
        )
        
        # Create temporary video files for demo
        import tempfile
        temp_video1 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_video1.close()
        temp_video2 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_video2.close()
        
        job1 = FrameOCRJob(
            video_id="news_broadcast_001",
            video_path=temp_video1.name,
            tenant_id=tenant1_id,
            user_id="news_editor_1",
            config=config1
        )
        
        # Job for Tenant 2
        config2 = OCRJobConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            ocr_engines=[OCREngine.EASYOCR],
            languages=["en", "es", "fr"]
        )
        
        job2 = FrameOCRJob(
            video_id="lecture_video_001",
            video_path=temp_video2.name,
            tenant_id=tenant2_id,
            user_id="professor_1",
            config=config2
        )
        
        # Insert jobs
        job1_id = db.insert_job(job1)
        job2_id = db.insert_job(job2)
        
        print(f"  - Job 1 inserted: {job1_id}")
        print(f"  - Job 2 inserted: {job2_id}")
        
        # Test tenant isolation
        print("\n4. Testing Tenant Isolation...")
        
        # Tenant 1 should access their own job
        retrieved_job1 = db.get_job(job1_id, tenant1_id)
        print(f"  - Tenant 1 accessing own job: {'Success' if retrieved_job1 else 'Failed'}")
        
        # Tenant 1 should NOT access Tenant 2's job
        cross_tenant_job = db.get_job(job2_id, tenant1_id)
        print(f"  - Tenant 1 accessing other tenant's job: {'Failed (Good!)' if not cross_tenant_job else 'Success (Bad!)'}")
        
        # Update job statuses
        print("\n5. Updating Job Statuses...")
        
        db.update_job_status(job1_id, tenant1_id, JobStatus.PROCESSING)
        db.update_job_status(job2_id, tenant2_id, JobStatus.COMPLETED)
        
        updated_job1 = db.get_job(job1_id, tenant1_id)
        updated_job2 = db.get_job(job2_id, tenant2_id)
        
        print(f"  - Job 1 status: {updated_job1.status.value}")
        print(f"  - Job 2 status: {updated_job2.status.value}")
        
        # Insert OCR results
        print("\n6. Inserting OCR Results...")
        
        results_data = [
            (job1_id, tenant1_id, "Breaking: Market Update", 5.0, 150),
            (job1_id, tenant1_id, "Stock prices rising", 10.5, 315),
            (job2_id, tenant2_id, "Chapter 1: Introduction", 2.0, 60),
            (job2_id, tenant2_id, "Mathematical Concepts", 15.0, 450),
        ]
        
        for job_id, tenant_id, text, timestamp, frame_num in results_data:
            result = FrameOCRResult(
                job_id=job_id,
                video_id=f"video_for_{job_id}",
                tenant_id=tenant_id,
                timestamp=timestamp,
                frame_number=frame_num,
                text=text,
                confidence=0.85,
                language="en",
                ocr_engine=OCREngine.TESSERACT
            )
            
            result_id = db.insert_result(result)
            print(f"  - Inserted result: {text[:30]}... -> {result_id}")
        
        # Search OCR text
        print("\n7. Searching OCR Text...")
        
        # Search in Tenant 1's data
        search_results1 = db.search_ocr_text(tenant1_id, "Market")
        print(f"  - Tenant 1 search for 'Market': {len(search_results1)} results")
        
        # Search in Tenant 2's data
        search_results2 = db.search_ocr_text(tenant2_id, "Chapter")
        print(f"  - Tenant 2 search for 'Chapter': {len(search_results2)} results")
        
        # Cross-tenant search should return no results
        cross_search = db.search_ocr_text(tenant1_id, "Chapter")
        print(f"  - Tenant 1 search for Tenant 2's content: {len(cross_search)} results")
        
        # Audit logging
        print("\n8. Audit Logging...")
        
        db.log_audit_event(
            tenant_id=tenant1_id,
            user_id="news_editor_1",
            action="SEARCH_OCR",
            resource_type="OCR_RESULTS",
            resource_id="search_query_001",
            details={"query": "Market", "results_count": len(search_results1)}
        )
        
        db.log_audit_event(
            tenant_id=tenant2_id,
            user_id="professor_1",
            action="CREATE_JOB",
            resource_type="OCR_JOB",
            resource_id=job2_id,
            details={"video_id": "lecture_video_001", "config": "multilingual"}
        )
        
        print("  - Audit events logged successfully")
        
        # Temporal consolidation demo
        print("\n9. Temporal Consolidation Demo...")
        
        # This would typically be done by the processing engine
        # Here we simulate the consolidation results
        consolidation_data = {
            "job_id": job1_id,
            "video_id": "news_broadcast_001",
            "tenant_id": tenant1_id,
            "consolidated_segments": [
                {
                    "text": "Breaking News Alert",
                    "occurrences": 5,
                    "stability_score": 0.92,
                    "confidence_avg": 0.89,
                    "time_span": "00:00:10 - 00:01:30"
                },
                {
                    "text": "Market Update",
                    "occurrences": 3,
                    "stability_score": 0.87,
                    "confidence_avg": 0.91,
                    "time_span": "00:00:05 - 00:00:45"
                }
            ]
        }
        
        print(f"  - Consolidated {len(consolidation_data['consolidated_segments'])} text segments")
        for segment in consolidation_data['consolidated_segments']:
            print(f"    * '{segment['text']}': {segment['occurrences']} occurrences, "
                  f"stability: {segment['stability_score']:.2f}")
        
        print("\n10. Database Demo Completed Successfully!")
        
    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
            os.unlink(temp_video1.name)
            os.unlink(temp_video2.name)
        except:
            pass


def demo_advanced_features():
    """Demonstrate advanced features"""
    print("\n=== Advanced Features Demo ===\n")
    
    # 1. Multi-engine OCR configuration
    print("1. Multi-Engine OCR Configuration...")
    
    advanced_config = OCRJobConfig(
        sampling_strategy=SamplingStrategy.HYBRID,
        sampling_interval=0.5,
        max_frames=2000,
        ocr_engines=[
            OCREngine.TESSERACT,
            OCREngine.EASYOCR,
            OCREngine.GOOGLE_VISION
        ],
        confidence_threshold=0.8,
        languages=["en", "es", "fr", "de"],
        preprocessing_enabled=True,
        region_detection_enabled=True,
        temporal_consolidation_enabled=True,
        stability_threshold=0.85,
        cost_limit=50.0,
        priority=8
    )
    
    print(f"  - Engines: {len(advanced_config.ocr_engines)}")
    print(f"  - Languages: {len(advanced_config.languages)}")
    print(f"  - Cost limit: ${advanced_config.cost_limit}")
    print(f"  - Priority: {advanced_config.priority}/10")
    
    # 2. Region-specific text detection
    print("\n2. Region-Specific Text Detection...")
    
    regions = [
        (RegionType.LOWER_THIRD, "Breaking News: Election Results"),
        (RegionType.TITLE, "Presidential Debate 2024"),
        (RegionType.WATERMARK, "NEWS NETWORK"),
        (RegionType.CAPTION, "[Speaking in Spanish]"),
        (RegionType.BANNER, "LIVE FROM WASHINGTON")
    ]
    
    for region_type, text in regions:
        bbox = BoundingBox(
            x=50, y=100, width=300, height=40,
            confidence=0.9, region_type=region_type
        )
        
        segment = TextSegment(
            text=text,
            confidence=0.88,
            region_classification=region_type,
            bounding_box=bbox
        )
        
        print(f"  - {region_type.value}: '{text}' (conf: {segment.confidence:.2f})")
    
    # 3. Cost estimation and optimization
    print("\n3. Cost Estimation and Optimization...")
    
    video_durations = [60, 300, 1800, 3600]  # 1min, 5min, 30min, 1hour
    
    for duration in video_durations:
        cost = advanced_config.estimate_cost(duration)
        frames = min(advanced_config.max_frames, int(duration / advanced_config.sampling_interval))
        
        print(f"  - {duration//60:2d}:{duration%60:02d} video: ${cost:.4f} ({frames} frames)")
    
    # 4. Data lineage tracking
    print("\n4. Data Lineage Tracking...")
    
    job = FrameOCRJob(
        video_id="advanced_demo_video",
        video_path="/path/to/advanced.mp4",
        tenant_id="advanced_tenant",
        user_id="advanced_user",
        config=advanced_config
    )
    
    # Simulate processing pipeline with lineage tracking
    pipeline_steps = [
        ("video_ingestion", {"source": "upload", "format": "mp4", "duration": 300}),
        ("frame_extraction", {"method": "ffmpeg", "fps": 30, "total_frames": 9000}),
        ("frame_sampling", {"strategy": "hybrid", "selected_frames": 600}),
        ("preprocessing", {"resize": True, "denoise": True, "contrast_enhance": True}),
        ("ocr_tesseract", {"version": "5.0", "confidence_threshold": 0.8}),
        ("ocr_easyocr", {"version": "1.6", "gpu_enabled": True}),
        ("ocr_google_vision", {"api_version": "v1", "features": ["text_detection"]}),
        ("result_consolidation", {"merge_strategy": "confidence_weighted"}),
        ("temporal_analysis", {"stability_threshold": 0.85, "min_occurrences": 2}),
        ("quality_assessment", {"final_confidence": 0.91, "coverage": 0.87})
    ]
    
    for step, details in pipeline_steps:
        job.add_lineage_entry(step, details)
        print(f"  - {step}: {len(details)} parameters tracked")
    
    print(f"  - Total lineage entries: {len(job.data_lineage.get('operations', []))}")
    
    # 5. Performance metrics
    print("\n5. Performance Metrics...")
    
    metrics = {
        "processing_time": 45.2,
        "frames_per_second": 13.3,
        "text_detection_rate": 0.78,
        "average_confidence": 0.89,
        "temporal_stability": 0.82,
        "cost_efficiency": 0.94
    }
    
    for metric, value in metrics.items():
        print(f"  - {metric.replace('_', ' ').title()}: {value}")
    
    print("\nAdvanced Features Demo Completed!")


def main():
    """Run the complete Frame OCR system demo"""
    print("Frame OCR Indexing System - Comprehensive Demo")
    print("=" * 50)
    
    try:
        # Run data models demo
        job, results = demo_data_models()
        
        # Run database operations demo
        demo_database_operations()
        
        # Run advanced features demo
        demo_advanced_features()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✓ Comprehensive data models with validation")
        print("✓ Multi-tenant database architecture")
        print("✓ Temporal consolidation and stability tracking")
        print("✓ Data lineage and audit logging")
        print("✓ Multi-engine OCR configuration")
        print("✓ Region-specific text detection")
        print("✓ Cost estimation and optimization")
        print("✓ Serialization and model validation")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()