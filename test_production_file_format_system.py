#!/usr/bin/env python3
"""
Comprehensive tests for Production File Format System

Tests all major functionality including:
- Media analysis and format detection
- File conversion with multiple codecs
- Cloud storage integration
- Quality metrics and assessment
- Database operations and analytics
- Parallel processing and job management
- Error handling and fallbacks

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sqlite3
import asyncio
import time
import shutil
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from production_file_format_system import (
    ProductionFileFormatSystem,
    MediaAnalyzer,
    FileConverter,
    CloudStorageManager,
    FileFormatDatabase,
    MediaInfo,
    ConversionJob,
    QualityMetrics,
    MediaType,
    AudioCodec,
    VideoCodec,
    ContainerFormat,
    ConversionStatus,
    ConversionPriority,
    QualityLevel,
    CloudProvider
)


class TestProductionFileFormatSystem(unittest.TestCase):
    """Test suite for Production File Format System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_file_format.db")
        self.system = ProductionFileFormatSystem(self.db_path, self.temp_dir)
        
        # Create test media files
        self.test_audio_file = self._create_test_audio_file()
        self.test_video_file = self._create_test_video_file()
    
    def tearDown(self):
        """Clean up test environment"""
        self.system.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_audio_file(self) -> str:
        """Create a test audio file"""
        test_file = os.path.join(self.temp_dir, "test_audio.wav")
        
        # Create a simple WAV file with test data
        with open(test_file, 'wb') as f:
            # WAV header (44 bytes)
            f.write(b'RIFF')
            f.write((1000).to_bytes(4, 'little'))  # File size
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))  # PCM header size
            f.write((1).to_bytes(2, 'little'))   # PCM format
            f.write((1).to_bytes(2, 'little'))   # Mono
            f.write((44100).to_bytes(4, 'little'))  # Sample rate
            f.write((88200).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))   # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((1000).to_bytes(4, 'little'))  # Data size
            
            # Add some sample audio data
            for i in range(500):
                f.write((i % 256).to_bytes(1, 'little'))
                f.write(((i * 2) % 256).to_bytes(1, 'little'))
        
        return test_file
    
    def _create_test_video_file(self) -> str:
        """Create a test video file"""
        test_file = os.path.join(self.temp_dir, "test_video.mp4")
        
        # Create a minimal MP4 file structure
        with open(test_file, 'wb') as f:
            # Minimal MP4 structure for testing
            f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41')
            f.write(b'\x00\x00\x00\x08free')
            f.write(b'\x00\x00\x01\x00mdat')
            # Add some dummy video data
            f.write(b'\x00' * 200)
        
        return test_file
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.system, ProductionFileFormatSystem)
        self.assertIsInstance(self.system.db, FileFormatDatabase)
        self.assertIsInstance(self.system.analyzer, MediaAnalyzer)
        self.assertIsInstance(self.system.converter, FileConverter)
        self.assertIsInstance(self.system.cloud_manager, CloudStorageManager)
        self.assertTrue(self.system.system_active)
        self.assertEqual(len(self.system.processing_queue), 0)
        self.assertEqual(len(self.system.active_jobs), 0)
    
    def test_media_info_dataclass(self):
        """Test MediaInfo dataclass"""
        media_info = MediaInfo(
            file_path="/test/path.mp4",
            file_size=1024000,
            duration=120.5,
            media_type=MediaType.VIDEO,
            container_format=ContainerFormat.MP4,
            video_codec=VideoCodec.H264,
            resolution=(1920, 1080),
            frame_rate=30.0,
            audio_codec=AudioCodec.AAC,
            sample_rate=44100,
            channels=2,
            quality_score=85.5,
            checksum="abc123"
        )
        
        self.assertEqual(media_info.file_path, "/test/path.mp4")
        self.assertEqual(media_info.file_size, 1024000)
        self.assertEqual(media_info.duration, 120.5)
        self.assertEqual(media_info.media_type, MediaType.VIDEO)
        self.assertEqual(media_info.container_format, ContainerFormat.MP4)
        self.assertEqual(media_info.video_codec, VideoCodec.H264)
        self.assertEqual(media_info.resolution, (1920, 1080))
        self.assertEqual(media_info.frame_rate, 30.0)
        self.assertEqual(media_info.audio_codec, AudioCodec.AAC)
        self.assertEqual(media_info.sample_rate, 44100)
        self.assertEqual(media_info.channels, 2)
        self.assertEqual(media_info.quality_score, 85.5)
        self.assertEqual(media_info.checksum, "abc123")
    
    def test_conversion_job_dataclass(self):
        """Test ConversionJob dataclass"""
        source_info = MediaInfo(file_path="/test/source.mp4", file_size=1000)
        
        job = ConversionJob(
            job_id="test_job_123",
            source_path="/test/source.mp4",
            target_path="/test/target.mp4",
            source_info=source_info,
            target_format=ContainerFormat.MP4,
            target_codec=VideoCodec.H265,
            quality_level=QualityLevel.HIGH,
            priority=ConversionPriority.URGENT,
            status=ConversionStatus.PENDING,
            progress=0.0
        )
        
        self.assertEqual(job.job_id, "test_job_123")
        self.assertEqual(job.source_path, "/test/source.mp4")
        self.assertEqual(job.target_path, "/test/target.mp4")
        self.assertEqual(job.source_info, source_info)
        self.assertEqual(job.target_format, ContainerFormat.MP4)
        self.assertEqual(job.target_codec, VideoCodec.H265)
        self.assertEqual(job.quality_level, QualityLevel.HIGH)
        self.assertEqual(job.priority, ConversionPriority.URGENT)
        self.assertEqual(job.status, ConversionStatus.PENDING)
        self.assertEqual(job.progress, 0.0)
        self.assertIsNone(job.error_message)
        self.assertIsInstance(job.created_at, datetime)
    
    def test_quality_metrics_dataclass(self):
        """Test QualityMetrics dataclass"""
        metrics = QualityMetrics(
            vmaf_score=95.5,
            ssim_score=0.98,
            psnr_score=45.2,
            snr_db=65.0,
            overall_score=92.0,
            quality_grade="Excellent",
            issues_detected=["minor_artifacts", "slight_blur"]
        )
        
        self.assertEqual(metrics.vmaf_score, 95.5)
        self.assertEqual(metrics.ssim_score, 0.98)
        self.assertEqual(metrics.psnr_score, 45.2)
        self.assertEqual(metrics.snr_db, 65.0)
        self.assertEqual(metrics.overall_score, 92.0)
        self.assertEqual(metrics.quality_grade, "Excellent")
        self.assertIn("minor_artifacts", metrics.issues_detected)
        self.assertIn("slight_blur", metrics.issues_detected)
    
    def test_media_analyzer_initialization(self):
        """Test MediaAnalyzer initialization"""
        analyzer = MediaAnalyzer()
        self.assertIsInstance(analyzer.ffprobe_available, bool)
        self.assertIsInstance(analyzer.opencv_available, bool)
        self.assertIsInstance(analyzer.librosa_available, bool)
    
    def test_media_analyzer_basic_format_detection(self):
        """Test basic format detection"""
        analyzer = MediaAnalyzer()
        
        # Test audio file analysis
        audio_info = analyzer.analyze_media_file(self.test_audio_file)
        self.assertEqual(audio_info.file_path, self.test_audio_file)
        self.assertGreater(audio_info.file_size, 0)
        self.assertIsNotNone(audio_info.checksum)
        self.assertGreater(audio_info.analysis_time, 0)
        
        # Basic format detection should work
        self.assertIn(audio_info.media_type, [MediaType.AUDIO, MediaType.UNKNOWN])
        
        # Test video file analysis
        video_info = analyzer.analyze_media_file(self.test_video_file)
        self.assertEqual(video_info.file_path, self.test_video_file)
        self.assertGreater(video_info.file_size, 0)
        self.assertIsNotNone(video_info.checksum)
    
    def test_media_analyzer_checksum_calculation(self):
        """Test checksum calculation"""
        analyzer = MediaAnalyzer()
        
        # Create test file with known content
        test_file = os.path.join(self.temp_dir, "checksum_test.txt")
        test_content = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        checksum = analyzer._calculate_checksum(test_file)
        self.assertIsInstance(checksum, str)
        self.assertGreater(len(checksum), 0)
        
        # Same content should produce same checksum
        checksum2 = analyzer._calculate_checksum(test_file)
        self.assertEqual(checksum, checksum2)
    
    def test_media_analyzer_error_handling(self):
        """Test media analyzer error handling"""
        analyzer = MediaAnalyzer()
        
        # Test with non-existent file
        non_existent = "/path/does/not/exist.mp4"
        media_info = analyzer.analyze_media_file(non_existent)
        
        self.assertEqual(media_info.file_path, non_existent)
        self.assertTrue(media_info.is_corrupted)
        self.assertGreater(media_info.analysis_time, 0)
    
    def test_file_converter_initialization(self):
        """Test FileConverter initialization"""
        converter = FileConverter(self.temp_dir)
        self.assertEqual(converter.temp_dir, self.temp_dir)
        self.assertIsInstance(converter.ffmpeg_available, bool)
        self.assertIsInstance(converter.conversion_presets, dict)
        self.assertIn('audio_high_quality', converter.conversion_presets)
        self.assertIn('video_medium_quality', converter.conversion_presets)
    
    def test_file_converter_preset_loading(self):
        """Test conversion preset loading"""
        converter = FileConverter()
        presets = converter.conversion_presets
        
        # Check audio presets
        self.assertIn('audio_high_quality', presets)
        audio_preset = presets['audio_high_quality']
        self.assertIn('codec', audio_preset)
        self.assertIn('bitrate', audio_preset)
        self.assertIn('sample_rate', audio_preset)
        
        # Check video presets
        self.assertIn('video_high_quality', presets)
        video_preset = presets['video_high_quality']
        self.assertIn('video_codec', video_preset)
        self.assertIn('audio_codec', video_preset)
        self.assertIn('crf', video_preset)
    
    def test_file_converter_parameter_preparation(self):
        """Test conversion parameter preparation"""
        converter = FileConverter()
        
        # Create test job
        source_info = MediaInfo(
            file_path=self.test_audio_file,
            file_size=1000,
            media_type=MediaType.AUDIO
        )
        
        job = ConversionJob(
            job_id="test_prep",
            source_path=self.test_audio_file,
            target_path="/test/output.mp3",
            source_info=source_info,
            target_format=ContainerFormat.MP3,
            target_codec=AudioCodec.MP3,
            quality_level=QualityLevel.HIGH,
            priority=ConversionPriority.NORMAL
        )
        
        params = converter._prepare_conversion_params(job)
        self.assertIsInstance(params, dict)
        self.assertIn('codec', params)
        self.assertIn('bitrate', params)
    
    @patch('subprocess.run')
    def test_file_converter_ffmpeg_execution(self, mock_subprocess):
        """Test FFmpeg execution"""
        converter = FileConverter()
        converter.ffmpeg_available = True
        
        # Mock successful conversion
        mock_subprocess.return_value.returncode = 0
        
        source_info = MediaInfo(
            file_path=self.test_audio_file,
            file_size=1000,
            media_type=MediaType.AUDIO
        )
        
        job = ConversionJob(
            job_id="test_exec",
            source_path=self.test_audio_file,
            target_path=os.path.join(self.temp_dir, "output.mp3"),
            source_info=source_info,
            target_format=ContainerFormat.MP3,
            target_codec=AudioCodec.MP3,
            quality_level=QualityLevel.MEDIUM,
            priority=ConversionPriority.NORMAL
        )
        
        # Create dummy output file
        with open(job.target_path, 'w') as f:
            f.write("dummy content")
        
        result = converter.convert_file(job)
        self.assertTrue(result)
        self.assertEqual(job.status, ConversionStatus.COMPLETED)
        self.assertIsNotNone(job.completed_at)
    
    def test_cloud_storage_manager_initialization(self):
        """Test CloudStorageManager initialization"""
        manager = CloudStorageManager()
        
        # Clients may be None if credentials not available
        self.assertIsNotNone(manager)  # Manager should always initialize
    
    def test_cloud_storage_aws_client_init(self):
        """Test AWS client initialization"""
        # Skip if boto3 not available
        try:
            import boto3
            with patch('boto3.client') as mock_boto3_client:
                mock_client = MagicMock()
                mock_boto3_client.return_value = mock_client
                
                manager = CloudStorageManager()
                self.assertEqual(manager.aws_client, mock_client)
        except ImportError:
            self.skipTest("boto3 not available")
    
    def test_file_format_database_initialization(self):
        """Test database initialization"""
        db = FileFormatDatabase(self.db_path)
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check table creation
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check media_files table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media_files'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check conversion_jobs table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversion_jobs'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check quality_assessments table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_assessments'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_database_media_info_storage(self):
        """Test media info storage in database"""
        db = FileFormatDatabase(self.db_path)
        
        media_info = MediaInfo(
            file_path="/test/sample.mp4",
            file_size=1024000,
            media_type=MediaType.VIDEO,
            container_format=ContainerFormat.MP4,
            duration=120.0,
            video_codec=VideoCodec.H264,
            resolution=(1920, 1080),
            quality_score=85.5,
            checksum="abc123def"
        )
        
        file_id = db.store_media_info(media_info)
        self.assertIsInstance(file_id, int)
        self.assertGreater(file_id, 0)
        
        # Verify storage
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM media_files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "/test/sample.mp4")  # file_path
            self.assertEqual(row[3], 1024000)  # file_size
            self.assertEqual(row[5], "video")  # media_type
    
    def test_database_conversion_job_storage(self):
        """Test conversion job storage"""
        db = FileFormatDatabase(self.db_path)
        
        source_info = MediaInfo(file_path="/test/source.mp4", file_size=1000)
        
        job = ConversionJob(
            job_id="test_storage_123",
            source_path="/test/source.mp4",
            target_path="/test/target.mp4",
            source_info=source_info,
            target_format=ContainerFormat.MP4,
            target_codec=VideoCodec.H265,
            quality_level=QualityLevel.HIGH,
            priority=ConversionPriority.HIGH,
            status=ConversionStatus.PENDING,
            conversion_options={"crf": 20}
        )
        
        job_id = db.store_conversion_job(job)
        self.assertIsInstance(job_id, int)
        self.assertGreater(job_id, 0)
        
        # Update job status
        job.status = ConversionStatus.COMPLETED
        job.progress = 100.0
        job.quality_metrics = {"compression_ratio": 0.8}
        
        db.update_conversion_job(job)
        
        # Verify update
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, progress FROM conversion_jobs WHERE job_id = ?", 
                         (job.job_id,))
            row = cursor.fetchone()
            
            self.assertEqual(row[0], "completed")
            self.assertEqual(row[1], 100.0)
    
    def test_database_statistics(self):
        """Test database statistics generation"""
        db = FileFormatDatabase(self.db_path)
        
        # Add some test data
        source_info = MediaInfo(file_path="/test/source.mp4", file_size=1000)
        
        for i in range(5):
            job = ConversionJob(
                job_id=f"stats_test_{i}",
                source_path=f"/test/source_{i}.mp4",
                target_path=f"/test/target_{i}.mp4",
                source_info=source_info,
                target_format=ContainerFormat.MP4,
                target_codec=VideoCodec.H264,
                quality_level=QualityLevel.MEDIUM,
                priority=ConversionPriority.NORMAL,
                status=ConversionStatus.COMPLETED if i < 3 else ConversionStatus.FAILED
            )
            db.store_conversion_job(job)
        
        stats = db.get_conversion_statistics()
        
        self.assertIn('total_jobs', stats)
        self.assertIn('status_breakdown', stats)
        self.assertIn('success_rate', stats)
        self.assertEqual(stats['total_jobs'], 5)
        self.assertEqual(stats['status_breakdown'].get('completed', 0), 3)
        self.assertEqual(stats['status_breakdown'].get('failed', 0), 2)
        self.assertEqual(stats['success_rate'], 60.0)
    
    def test_system_file_analysis(self):
        """Test system file analysis"""
        media_info = self.system.analyze_file(self.test_audio_file)
        
        self.assertIsInstance(media_info, MediaInfo)
        self.assertEqual(media_info.file_path, self.test_audio_file)
        self.assertGreater(media_info.file_size, 0)
        self.assertIsNotNone(media_info.checksum)
        
        # Should be stored in database
        with sqlite3.connect(self.system.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM media_files WHERE file_path = ?", 
                         (self.test_audio_file,))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)
    
    def test_system_conversion_job_creation(self):
        """Test conversion job creation"""
        target_path = os.path.join(self.temp_dir, "converted_audio.mp3")
        
        job = self.system.create_conversion_job(
            source_path=self.test_audio_file,
            target_path=target_path,
            target_format=ContainerFormat.MP3,
            target_codec=AudioCodec.MP3,
            quality_level=QualityLevel.MEDIUM,
            priority=ConversionPriority.HIGH
        )
        
        self.assertIsInstance(job, ConversionJob)
        self.assertEqual(job.source_path, self.test_audio_file)
        self.assertEqual(job.target_path, target_path)
        self.assertEqual(job.target_format, ContainerFormat.MP3)
        self.assertEqual(job.target_codec, AudioCodec.MP3)
        self.assertEqual(job.quality_level, QualityLevel.MEDIUM)
        self.assertEqual(job.priority, ConversionPriority.HIGH)
        self.assertEqual(job.status, ConversionStatus.PENDING)
        
        # Should be in processing queue
        self.assertIn(job, self.system.processing_queue)
    
    def test_system_job_queue_priority(self):
        """Test job queue priority ordering"""
        # Create jobs with different priorities
        jobs = []
        for priority in [ConversionPriority.LOW, ConversionPriority.URGENT, 
                        ConversionPriority.NORMAL, ConversionPriority.HIGH]:
            job = self.system.create_conversion_job(
                source_path=self.test_audio_file,
                target_path=f"/test/output_{priority.value}.mp3",
                target_format=ContainerFormat.MP3,
                target_codec=AudioCodec.MP3,
                priority=priority
            )
            jobs.append(job)
        
        # Check queue ordering (should be URGENT, HIGH, NORMAL, LOW)
        queue_priorities = [job.priority for job in self.system.processing_queue]
        expected_order = [ConversionPriority.URGENT, ConversionPriority.HIGH, 
                         ConversionPriority.NORMAL, ConversionPriority.LOW]
        self.assertEqual(queue_priorities, expected_order)
    
    def test_system_batch_conversion(self):
        """Test batch file conversion"""
        file_specs = [
            {
                'source_path': self.test_audio_file,
                'target_path': os.path.join(self.temp_dir, 'batch1.mp3'),
                'target_format': 'mp3',
                'target_codec': 'mp3',
                'quality_level': 'medium',
                'priority': 'normal'
            },
            {
                'source_path': self.test_video_file,
                'target_path': os.path.join(self.temp_dir, 'batch2.mp4'),
                'target_format': 'mp4',
                'target_codec': 'h264',
                'quality_level': 'high',
                'priority': 'high'
            }
        ]
        
        job_ids = self.system.batch_convert_files(file_specs)
        
        self.assertEqual(len(job_ids), 2)
        for job_id in job_ids:
            self.assertIsInstance(job_id, str)
            job = self.system.get_job_status(job_id)
            self.assertIsNotNone(job)
    
    def test_system_status_reporting(self):
        """Test system status reporting"""
        status = self.system.get_system_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('system_active', status)
        self.assertIn('queue_length', status)
        self.assertIn('active_jobs', status)
        self.assertIn('max_workers', status)
        self.assertIn('ffmpeg_available', status)
        self.assertIn('cloud_providers', status)
        self.assertIn('statistics', status)
        self.assertIn('features', status)
        
        # Check boolean values
        self.assertIsInstance(status['system_active'], bool)
        self.assertIsInstance(status['ffmpeg_available'], bool)
        
        # Check cloud providers
        cloud_providers = status['cloud_providers']
        self.assertIn('aws_s3', cloud_providers)
        self.assertIn('google_cloud', cloud_providers)
        self.assertIn('azure_blob', cloud_providers)
        
        # Check features
        features = status['features']
        self.assertIn('opencv_available', features)
        self.assertIn('librosa_available', features)
        self.assertIn('magic_available', features)
    
    def test_system_job_status_retrieval(self):
        """Test job status retrieval"""
        job = self.system.create_conversion_job(
            source_path=self.test_audio_file,
            target_path=os.path.join(self.temp_dir, "status_test.mp3"),
            target_format=ContainerFormat.MP3,
            target_codec=AudioCodec.MP3
        )
        
        # Test retrieving active job
        retrieved_job = self.system.get_job_status(job.job_id)
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.job_id, job.job_id)
        
        # Test non-existent job
        fake_job = self.system.get_job_status("non_existent_job_id")
        self.assertIsNone(fake_job)
    
    def test_system_processing_start_stop(self):
        """Test processing start and stop"""
        # Initially system should be active
        self.assertTrue(self.system.system_active)
        
        # Start processing (should create thread)
        self.system.start_processing()
        self.assertTrue(self.system.system_active)
        self.assertIsNotNone(self.system.processing_thread)
        
        # Stop processing
        self.system.stop_processing()
        self.assertFalse(self.system.system_active)
    
    def test_error_handling_invalid_file(self):
        """Test error handling with invalid file"""
        with self.assertRaises(Exception):
            self.system.analyze_file("/non/existent/file.mp4")
    
    def test_error_handling_invalid_conversion_params(self):
        """Test error handling with invalid conversion parameters"""
        try:
            # This should handle gracefully
            job = self.system.create_conversion_job(
                source_path=self.test_audio_file,
                target_path="/invalid/path/output.mp3",
                target_format=ContainerFormat.MP3,
                target_codec=AudioCodec.MP3,
                conversion_options={"invalid_option": "invalid_value"}
            )
            # Job should be created but may fail during processing
            self.assertIsNotNone(job)
        except Exception as e:
            # Should not raise exception during job creation
            self.fail(f"Job creation should not fail: {e}")
    
    def test_enum_values(self):
        """Test enum value consistency"""
        # Test MediaType enum
        media_types = [MediaType.AUDIO, MediaType.VIDEO, MediaType.IMAGE, MediaType.UNKNOWN]
        for media_type in media_types:
            self.assertIsInstance(media_type.value, str)
        
        # Test AudioCodec enum
        audio_codecs = [AudioCodec.AAC, AudioCodec.MP3, AudioCodec.FLAC, AudioCodec.PCM]
        for codec in audio_codecs:
            self.assertIsInstance(codec.value, str)
        
        # Test VideoCodec enum
        video_codecs = [VideoCodec.H264, VideoCodec.H265, VideoCodec.AV1, VideoCodec.VP9]
        for codec in video_codecs:
            self.assertIsInstance(codec.value, str)
        
        # Test ConversionStatus enum
        statuses = [ConversionStatus.PENDING, ConversionStatus.IN_PROGRESS, 
                   ConversionStatus.COMPLETED, ConversionStatus.FAILED]
        for status in statuses:
            self.assertIsInstance(status.value, str)
    
    def test_comprehensive_workflow(self):
        """Test comprehensive workflow from analysis to conversion"""
        # 1. Analyze source file
        media_info = self.system.analyze_file(self.test_audio_file)
        self.assertIsNotNone(media_info)
        
        # 2. Create conversion job
        target_path = os.path.join(self.temp_dir, "workflow_test.mp3")
        job = self.system.create_conversion_job(
            source_path=self.test_audio_file,
            target_path=target_path,
            target_format=ContainerFormat.MP3,
            target_codec=AudioCodec.MP3,
            quality_level=QualityLevel.HIGH,
            priority=ConversionPriority.URGENT
        )
        
        # 3. Verify job creation
        self.assertEqual(job.status, ConversionStatus.PENDING)
        self.assertEqual(job.progress, 0.0)
        
        # 4. Check system status
        status = self.system.get_system_status()
        self.assertGreater(status['queue_length'], 0)
        
        # 5. Verify database storage
        retrieved_job = self.system.get_job_status(job.job_id)
        self.assertIsNotNone(retrieved_job)
        
        print(f"✅ Comprehensive workflow test completed successfully")


class TestAsyncFileFormatSystem(unittest.TestCase):
    """Test async functionality"""
    
    def setUp(self):
        """Set up async test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.system = ProductionFileFormatSystem(
            db_path=os.path.join(self.temp_dir, "async_test.db"),
            temp_dir=self.temp_dir
        )
    
    def tearDown(self):
        """Clean up async test environment"""
        self.system.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_cloud_upload_simulation(self):
        """Test cloud upload simulation"""
        manager = CloudStorageManager()
        
        # Create test file
        test_file = os.path.join(self.temp_dir, "cloud_test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content for cloud upload")
        
        # Create mock job
        source_info = MediaInfo(file_path=test_file, file_size=100)
        job = ConversionJob(
            job_id="cloud_test",
            source_path=test_file,
            target_path=test_file,
            source_info=source_info,
            target_format=ContainerFormat.MP4,
            target_codec=VideoCodec.H264,
            quality_level=QualityLevel.MEDIUM,
            priority=ConversionPriority.NORMAL,
            cloud_provider=CloudProvider.LOCAL,
            cloud_bucket="test-bucket",
            cloud_key="test-key.txt"
        )
        
        # Test upload (should handle gracefully without real cloud credentials)
        result = await manager.upload_file(test_file, job)
        # Result depends on whether cloud clients are available
        self.assertIsInstance(result, bool)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production File Format System Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionFileFormatSystem))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestAsyncFileFormatSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


def run_async_tests():
    """Run async tests"""
    async def async_test_runner():
        # Create test instance
        test_instance = TestAsyncFileFormatSystem()
        test_instance.setUp()
        
        try:
            # Run async tests
            await test_instance.test_cloud_upload_simulation()
            
            print("✅ All async file format tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Async file format test failed: {e}")
            return False
        finally:
            test_instance.tearDown()
    
    return asyncio.run(async_test_runner())


if __name__ == "__main__":
    # Run sync tests
    sync_success = run_comprehensive_tests()
    
    # Run async tests
    async_success = run_async_tests()
    
    overall_success = sync_success and async_success
    print(f"\n{'✅' if overall_success else '❌'} Overall test result: {'PASSED' if overall_success else 'FAILED'}")
    
    exit(0 if overall_success else 1)