"""
Simple Frame OCR System Demo

A simplified demo that showcases the core functionality without timezone complications.
"""

import tempfile
import os
from frame_ocr_models import (
    FrameOCRJob, FrameOCRResult, TextSegment, BoundingBox, OCRJobConfig,
    JobStatus, OCREngine, RegionType, SamplingStrategy,
    ModelValidator, ModelSerializer
)
from frame_ocr_database import FrameOCRDatabase, DatabaseConfig


def main():
    """Run a simple demo of the Frame OCR system"""
    print("Frame OCR Indexing System - Simple Demo")
    print("=" * 45)
    
    try:
        # 1. Create OCR Job Configuration
        print("\n1. Creating OCR Job Configuration...")
        config = OCRJobConfig(
            sampling_strategy=SamplingStrategy.TIME_BASED,
            sampling_interval=1.0,
            max_frames=100,
            ocr_engines=[OCREngine.TESSERACT],
            confidence_threshold=0.8,
            languages=["en"]
        )
        print(f"   ✓ Configuration created with {len(config.ocr_engines)} OCR engine(s)")
        
        # 2. Create temporary video file for testing
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_video.close()
        
        # 3. Create OCR Job
        print("\n2. Creating OCR Job...")
        job = FrameOCRJob(
            video_id="demo_video_001",
            video_path=temp_video.name,
            tenant_id="demo_tenant",
            user_id="demo_user",
            config=config
        )
        print(f"   ✓ Job created with ID: {job.job_id}")
        
        # 4. Test job lifecycle
        print("\n3. Testing Job Lifecycle...")
        job.start_processing("demo_node")
        print(f"   ✓ Job started on node: {job.processing_node}")
        
        job.update_progress(50, 100)
        print(f"   ✓ Progress updated: {job.progress:.0%}")
        
        job.complete_job(actual_cost=1.25)
        print(f"   ✓ Job completed with cost: ${job.actual_cost}")
        
        # 5. Create bounding box and text segment
        print("\n4. Creating OCR Results...")
        bbox = BoundingBox(
            x=10, y=20, width=200, height=30,
            confidence=0.9, region_type=RegionType.LOWER_THIRD
        )
        print(f"   ✓ Bounding box created: {bbox.width}x{bbox.height} at ({bbox.x}, {bbox.y})")
        
        segment = TextSegment(
            text="Breaking News Alert",
            confidence=0.95,
            language="en",
            bounding_box=bbox,
            region_classification=RegionType.LOWER_THIRD
        )
        print(f"   ✓ Text segment created: '{segment.text}' (confidence: {segment.confidence})")
        
        # 6. Create OCR result
        result = FrameOCRResult(
            job_id=job.job_id,
            video_id=job.video_id,
            tenant_id=job.tenant_id,
            timestamp=15.5,
            frame_number=465,
            text="Breaking News Alert",
            confidence=0.95,
            language="en",
            bounding_boxes=[bbox],
            text_segments=[segment],
            ocr_engine=OCREngine.TESSERACT
        )
        print(f"   ✓ OCR result created for frame {result.frame_number} at {result.timestamp}s")
        
        # 7. Test database operations
        print("\n5. Testing Database Operations...")
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Configure and initialize database
        db_config = DatabaseConfig()
        db_config.db_type = 'sqlite'
        db_config.db_name = temp_db.name
        
        db = FrameOCRDatabase(db_config)
        print("   ✓ Database initialized")
        
        # Create tenant
        tenant_id = db.create_tenant("Demo Tenant", {"max_jobs": 10})
        print(f"   ✓ Tenant created: {tenant_id}")
        
        # Update job with correct tenant ID
        job.tenant_id = tenant_id
        result.tenant_id = tenant_id
        
        # Insert job
        job_id = db.insert_job(job)
        print(f"   ✓ Job inserted: {job_id}")
        
        # Insert result
        result_id = db.insert_result(result)
        print(f"   ✓ Result inserted: {result_id}")
        
        # Search OCR text
        search_results = db.search_ocr_text(tenant_id, "Breaking")
        print(f"   ✓ Search found {len(search_results)} result(s)")
        
        # 8. Test model validation
        print("\n6. Testing Model Validation...")
        job_errors = ModelValidator.validate_job(job)
        print(f"   ✓ Job validation: {len(job_errors)} error(s)")
        
        result_errors = ModelValidator.validate_result(result)
        print(f"   ✓ Result validation: {len(result_errors)} error(s)")
        
        # 9. Test serialization
        print("\n7. Testing Serialization...")
        job_json = ModelSerializer.serialize_job(job)
        restored_job = ModelSerializer.deserialize_job(job_json)
        print(f"   ✓ Job serialization: {job.job_id == restored_job.job_id}")
        
        result_json = ModelSerializer.serialize_result(result)
        restored_result = ModelSerializer.deserialize_result(result_json)
        print(f"   ✓ Result serialization: {result.result_id == restored_result.result_id}")
        
        print("\n" + "=" * 45)
        print("✓ All tests completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Comprehensive data models with validation")
        print("  • Multi-tenant database architecture")
        print("  • Job lifecycle management")
        print("  • OCR result storage and retrieval")
        print("  • Text search functionality")
        print("  • Model serialization and validation")
        
    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary files
        try:
            os.unlink(temp_video.name)
            os.unlink(temp_db.name)
        except:
            pass


if __name__ == "__main__":
    main()