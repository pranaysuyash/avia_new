"""
Comprehensive Test Suite for Frame OCR Models and Database Schema
"""

import unittest
import tempfile
import os
from datetime import datetime

from frame_ocr_models import (
    FrameOCRJob, FrameOCRResult, TextSegment, BoundingBox, OCRJobConfig,
    JobStatus, OCREngine, RegionType, SamplingStrategy,
    ModelValidator, ModelSerializer
)
from frame_ocr_database import FrameOCRDatabase, DatabaseConfig


class TestBoundingBox(unittest.TestCase):
    """Test BoundingBox data model"""
    
    def test_valid_bounding_box_creation(self):
        """Test creating a valid bounding box"""
        bbox = BoundingBox(
            x=10, y=20, width=100, height=50,
            confidence=0.85, region_type=RegionType.LOWER_THIRD
        )
        
        self.assertEqual(bbox.x, 10)
        self.assertEqual(bbox.y, 20)
        self.assertEqual(bbox.width, 100)
        self.assertEqual(bbox.height, 50)
        self.assertEqual(bbox.confidence, 0.85)
        self.assertEqual(bbox.region_type, RegionType.LOWER_THIRD)
    
    def test_bounding_box_validation(self):
        """Test bounding box validation"""
        # Test negative coordinates
        with self.assertRaises(ValueError):
            BoundingBox(x=-1, y=20, width=100, height=50, confidence=0.8)
        
        # Test zero dimensions
        with self.assertRaises(ValueError):
            BoundingBox(x=10, y=20, width=0, height=50, confidence=0.8)
        
        # Test invalid confidence
        with self.assertRaises(ValueError):
            BoundingBox(x=10, y=20, width=100, height=50, confidence=1.5)


class TestOCRJobConfig(unittest.TestCase):
    """Test OCRJobConfig data model"""
    
    def test_default_config_creation(self):
        """Test creating default OCR job configuration"""
        config = OCRJobConfig()
        
        self.assertEqual(config.sampling_strategy, SamplingStrategy.TIME_BASED)
        self.assertEqual(config.sampling_interval, 1.0)
        self.assertEqual(config.max_frames, 1000)
        self.assertIn(OCREngine.TESSERACT, config.ocr_engines)
        self.assertEqual(config.confidence_threshold, 0.5)
    
    def test_config_validation(self):
        """Test OCR job configuration validation"""
        # Test invalid sampling interval
        with self.assertRaises(ValueError):
            OCRJobConfig(sampling_interval=0)
        
        # Test invalid max frames
        with self.assertRaises(ValueError):
            OCRJobConfig(max_frames=0)


class TestFrameOCRJob(unittest.TestCase):
    """Test FrameOCRJob data model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = OCRJobConfig()
        self.job = FrameOCRJob(
            video_id="test_video_123",
            video_path="/path/to/test.mp4",
            tenant_id="tenant_abc",
            user_id="user_xyz",
            config=self.config
        )
    
    def test_job_creation(self):
        """Test creating an OCR job"""
        self.assertIsNotNone(self.job.job_id)
        self.assertEqual(self.job.video_id, "test_video_123")
        self.assertEqual(self.job.status, JobStatus.PENDING)
        self.assertEqual(self.job.progress, 0.0)
        self.assertEqual(self.job.retry_count, 0)


class TestFrameOCRDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Set up test database"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Configure test database
        self.config = DatabaseConfig()
        self.config.db_type = 'sqlite'
        self.config.db_name = self.temp_db.name
        
        # Initialize database
        self.db = FrameOCRDatabase(self.config)
    
    def tearDown(self):
        """Clean up test database"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_tenant_creation(self):
        """Test tenant creation"""
        tenant_id = self.db.create_tenant("Test Tenant", {"max_jobs": 100})
        self.assertIsNotNone(tenant_id)
        self.assertIsInstance(tenant_id, str)


if __name__ == '__main__':
    unittest.main(verbosity=2)