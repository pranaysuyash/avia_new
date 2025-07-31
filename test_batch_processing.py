#!/usr/bin/env python3
"""
Test suite for batch processing functionality
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from batch_processor import BatchProcessor, BatchJob, BatchFile, BatchResults, BatchJobStatus
from batch_export import BatchExporter
import utils

class TestBatchProcessor:
    """Test cases for BatchProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = BatchProcessor(max_concurrent_jobs=1)
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_test_{i}.mp3",
                dir=self.temp_dir,
                delete=False
            )
            temp_file.write(b"fake audio data")
            temp_file.close()
            
            self.test_files.append({
                'name': f'test_file_{i}.mp3',
                'size_bytes': 1024,
                'format': 'mp3',
                'temp_path': temp_file.name
            })
    
    def teardown_method(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        for file_info in self.test_files:
            if os.path.exists(file_info['temp_path']):
                os.remove(file_info['temp_path'])
        
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
        
        # Stop processor
        self.processor.stop_processing()
    
    def test_create_batch_job(self):
        """Test creating a batch job"""
        job_id = self.processor.create_batch_job(
            files=self.test_files,
            analysis_mode="Basic (spaCy)",
            job_name="Test Job"
        )
        
        assert job_id is not None
        assert len(job_id) == 8  # UUID short format
        
        # Check job is in queue
        assert not self.processor.job_queue.empty()
    
    def test_batch_file_creation(self):
        """Test BatchFile dataclass"""
        batch_file = BatchFile(
            id="test123",
            name="test.mp3",
            size_bytes=1024,
            format="mp3",
            temp_path="/tmp/test.mp3"
        )
        
        assert batch_file.id == "test123"
        assert batch_file.name == "test.mp3"
        assert batch_file.status == BatchJobStatus.PENDING
        assert batch_file.progress == 0
    
    def test_batch_job_creation(self):
        """Test BatchJob dataclass"""
        files = [
            BatchFile(id="1", name="test1.mp3", size_bytes=1024, format="mp3", temp_path="/tmp/1"),
            BatchFile(id="2", name="test2.mp3", size_bytes=2048, format="mp3", temp_path="/tmp/2")
        ]
        
        job = BatchJob(
            id="job123",
            name="Test Job",
            files=files,
            analysis_mode="Basic (spaCy)"
        )
        
        assert job.id == "job123"
        assert job.total_files == 2
        assert job.progress_percentage == 0
        assert not job.is_complete
    
    def test_job_progress_calculation(self):
        """Test job progress calculation"""
        files = [
            BatchFile(id="1", name="test1.mp3", size_bytes=1024, format="mp3", temp_path="/tmp/1"),
            BatchFile(id="2", name="test2.mp3", size_bytes=2048, format="mp3", temp_path="/tmp/2")
        ]
        
        job = BatchJob(
            id="job123",
            name="Test Job",
            files=files,
            analysis_mode="Basic (spaCy)"
        )
        
        # Initially 0% progress
        assert job.progress_percentage == 0
        
        # Complete one file
        job.completed_files = 1
        assert job.progress_percentage == 50
        
        # Complete all files
        job.completed_files = 2
        assert job.progress_percentage == 100
    
    @patch('batch_processor.stt.transcribe')
    @patch('batch_processor.ner_basic.extract_entities')
    def test_process_single_file_basic(self, mock_ner, mock_stt):
        """Test processing a single file in basic mode"""
        # Mock responses
        mock_stt.return_value = "This is a test transcript"
        mock_ner.return_value = {"PERSON": ["John Doe"], "ORG": ["Test Corp"]}
        
        # Create test job and file
        batch_file = BatchFile(
            id="test1",
            name="test.mp3",
            size_bytes=1024,
            format="mp3",
            temp_path=self.test_files[0]['temp_path']
        )
        
        job = BatchJob(
            id="job1",
            name="Test Job",
            files=[batch_file],
            analysis_mode="Basic (spaCy)"
        )
        
        # Process file
        result = self.processor._process_single_file(job, batch_file)
        
        # Verify result
        assert isinstance(result, BatchResults)
        assert result.transcript == "This is a test transcript"
        assert result.entities == {"PERSON": ["John Doe"], "ORG": ["Test Corp"]}
        assert result.word_count == 5
        assert batch_file.status == BatchJobStatus.PROCESSING
    
    def test_get_job_status(self):
        """Test getting job status"""
        # Create and add a job
        job_id = self.processor.create_batch_job(
            files=self.test_files,
            analysis_mode="Basic (spaCy)",
            job_name="Test Job"
        )
        
        # Job should not be in status yet (not processed)
        status = self.processor.get_job_status(job_id)
        assert status is None  # Job is in queue, not active or completed
        
        # Test non-existent job
        status = self.processor.get_job_status("nonexistent")
        assert status is None
    
    def test_cancel_job(self):
        """Test cancelling a job"""
        # Create a mock active job
        job = BatchJob(
            id="test_job",
            name="Test Job",
            files=[],
            analysis_mode="Basic (spaCy)"
        )
        job.status = BatchJobStatus.PROCESSING
        
        self.processor.active_jobs["test_job"] = job
        
        # Cancel the job
        result = self.processor.cancel_job("test_job")
        assert result is True
        assert job.status == BatchJobStatus.CANCELLED
        
        # Try to cancel non-existent job
        result = self.processor.cancel_job("nonexistent")
        assert result is False

class TestBatchExporter:
    """Test cases for BatchExporter class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.exporter = BatchExporter()
        
        # Create test job with results
        self.test_job = self._create_test_job()
    
    def _create_test_job(self):
        """Create a test job with sample results"""
        files = [
            BatchFile(
                id="file1",
                name="test1.mp3",
                size_bytes=1024,
                format="mp3",
                temp_path="/tmp/test1.mp3",
                status=BatchJobStatus.COMPLETED,
                processing_time=5.5
            ),
            BatchFile(
                id="file2",
                name="test2.mp3",
                size_bytes=2048,
                format="mp3",
                temp_path="/tmp/test2.mp3",
                status=BatchJobStatus.COMPLETED,
                processing_time=8.2
            )
        ]
        
        job = BatchJob(
            id="test_job",
            name="Test Export Job",
            files=files,
            analysis_mode="Basic (spaCy)",
            status=BatchJobStatus.COMPLETED,
            completed_files=2
        )
        
        # Add results
        job.results = {
            "file1": BatchResults(
                file_id="file1",
                transcript="This is the first test transcript",
                entities={"PERSON": ["Alice"], "ORG": ["Company A"]},
                word_count=7,
                confidence=0.95
            ),
            "file2": BatchResults(
                file_id="file2",
                transcript="This is the second test transcript",
                entities={"PERSON": ["Bob"], "ORG": ["Company B"]},
                word_count=7,
                confidence=0.88
            )
        }
        
        return job
    
    def test_export_json(self):
        """Test JSON export functionality"""
        result = self.exporter._export_json(self.test_job, include_metadata=True)
        
        assert isinstance(result, bytes)
        
        # Parse JSON to verify structure
        json_data = json.loads(result.decode('utf-8'))
        
        assert 'job_info' in json_data
        assert 'results' in json_data
        assert 'export_metadata' in json_data
        
        assert json_data['job_info']['id'] == 'test_job'
        assert json_data['job_info']['name'] == 'Test Export Job'
        assert len(json_data['results']) == 2
    
    def test_export_csv(self):
        """Test CSV export functionality"""
        result = self.exporter._export_csv(self.test_job, include_metadata=True)
        
        assert isinstance(result, bytes)
        
        # Verify CSV content
        csv_content = result.decode('utf-8')
        lines = csv_content.split('\n')
        
        # Should have metadata header lines
        assert '# Batch Processing Results Export' in lines[0]
        assert '# Job ID:,test_job' in lines[1]
        
        # Should have data rows
        assert 'file_id,file_name' in csv_content
        assert 'file1,test1.mp3' in csv_content
        assert 'file2,test2.mp3' in csv_content
    
    def test_export_txt(self):
        """Test text export functionality"""
        result = self.exporter._export_txt(self.test_job, include_metadata=True)
        
        assert isinstance(result, bytes)
        
        # Verify text content
        txt_content = result.decode('utf-8')
        
        assert 'BATCH PROCESSING RESULTS' in txt_content
        assert 'Job ID: test_job' in txt_content
        assert 'FILE 1: test1.mp3' in txt_content
        assert 'FILE 2: test2.mp3' in txt_content
        assert 'This is the first test transcript' in txt_content
        assert 'This is the second test transcript' in txt_content
    
    def test_get_export_filename(self):
        """Test export filename generation"""
        filename = self.exporter.get_export_filename(self.test_job, 'json')
        
        assert filename.startswith('Test_Export_Job_')
        assert filename.endswith('.json')
        assert len(filename.split('_')) >= 4  # Name + timestamp parts
    
    def test_get_export_stats(self):
        """Test export statistics calculation"""
        stats = self.exporter.get_export_stats(self.test_job)
        
        assert stats['total_files'] == 2
        assert stats['completed_files'] == 2
        assert stats['failed_files'] == 0
        assert stats['total_transcripts'] == 2
        assert stats['total_words'] == 14  # 7 + 7
        assert stats['total_entities'] == 4  # 2 + 2
        assert not stats['has_summaries']  # No summaries in test data
        assert 'json' in stats['supported_formats']

class TestBatchIntegration:
    """Integration tests for batch processing system"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.processor = BatchProcessor(max_concurrent_jobs=1)
        self.exporter = BatchExporter()
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        self.processor.stop_processing()
    
    @patch('batch_processor.stt.transcribe')
    @patch('batch_processor.ner_basic.extract_entities')
    def test_full_batch_workflow(self, mock_ner, mock_stt):
        """Test complete batch processing workflow"""
        # Mock processing functions
        mock_stt.return_value = "Test transcript"
        mock_ner.return_value = {"PERSON": ["Test Person"]}
        
        # Create test files
        temp_dir = tempfile.mkdtemp()
        test_files = []
        
        try:
            for i in range(2):
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f"_test_{i}.mp3",
                    dir=temp_dir,
                    delete=False
                )
                temp_file.write(b"fake audio data")
                temp_file.close()
                
                test_files.append({
                    'name': f'test_file_{i}.mp3',
                    'size_bytes': 1024,
                    'format': 'mp3',
                    'temp_path': temp_file.name
                })
            
            # Create batch job
            job_id = self.processor.create_batch_job(
                files=test_files,
                analysis_mode="Basic (spaCy)",
                job_name="Integration Test Job"
            )
            
            assert job_id is not None
            
            # In a real test, you would start processing and wait for completion
            # For this test, we'll just verify the job was created
            assert not self.processor.job_queue.empty()
            
        finally:
            # Clean up
            for file_info in test_files:
                if os.path.exists(file_info['temp_path']):
                    os.remove(file_info['temp_path'])
            os.rmdir(temp_dir)

def test_utils_functions():
    """Test utility functions used by batch processing"""
    
    # Test file size limit
    limit = utils.get_file_size_limit()
    assert isinstance(limit, int)
    assert limit > 0
    
    # Test timestamp generation
    timestamp = utils.get_timestamp()
    assert isinstance(timestamp, str)
    assert len(timestamp) == 15  # YYYYMMDD_HHMMSS format
    
    # Test file size formatting
    formatted = utils.format_file_size(1024)
    assert formatted == "1.0 KB"
    
    formatted = utils.format_file_size(1024 * 1024)
    assert formatted == "1.0 MB"
    
    # Test duration formatting
    formatted = utils.format_duration(30)
    assert formatted == "30.0s"
    
    formatted = utils.format_duration(90)
    assert formatted == "1m 30s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])