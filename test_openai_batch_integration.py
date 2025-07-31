#!/usr/bin/env python3
"""
Test suite for OpenAI batch processing integration
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from openai_batch_processor import OpenAIBatchProcessor, OpenAIBatchJob, OpenAIBatchStatus

class TestOpenAIBatchProcessor:
    """Test cases for OpenAI batch processing integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = OpenAIBatchProcessor()
        
        # Create test job
        # Create mock objects to avoid circular imports
        self.test_files = [
            type('MockFile', (), {
                'id': "file1",
                'name': "test1.mp3", 
                'size_bytes': 1024 * 1024,  # 1MB
                'format': "mp3",
                'temp_path': "/tmp/test1.mp3"
            })(),
            type('MockFile', (), {
                'id': "file2",
                'name': "test2.mp3",
                'size_bytes': 2 * 1024 * 1024,  # 2MB
                'format': "mp3", 
                'temp_path': "/tmp/test2.mp3"
            })(),
            type('MockFile', (), {
                'id': "file3",
                'name': "test3.mp3",
                'size_bytes': 1024 * 1024,  # 1MB
                'format': "mp3",
                'temp_path': "/tmp/test3.mp3"
            })()
        ]
        
        self.test_job = type('MockJob', (), {
            'id': "test_job",
            'name': "Test OpenAI Batch Job",
            'files': self.test_files,
            'analysis_mode': "Advanced (OpenAI)"
        })()
    
    def test_can_use_batch_processing_eligible(self):
        """Test batch processing eligibility detection - eligible case"""
        
        # Mock environment variable
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            result = self.processor.can_use_batch_processing(self.test_job)
            assert result is True
    
    def test_can_use_batch_processing_basic_mode(self):
        """Test batch processing eligibility - Basic mode not eligible"""
        
        basic_job = type('MockJob', (), {
            'id': "basic_job",
            'name': "Basic Job", 
            'files': self.test_files,
            'analysis_mode': "Basic (spaCy)"
        })()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            result = self.processor.can_use_batch_processing(basic_job)
            assert result is False
    
    def test_can_use_batch_processing_no_api_key(self):
        """Test batch processing eligibility - No API key"""
        
        with patch.dict(os.environ, {}, clear=True):
            result = self.processor.can_use_batch_processing(self.test_job)
            assert result is False
    
    def test_can_use_batch_processing_too_few_files(self):
        """Test batch processing eligibility - Too few files"""
        
        small_job = type('MockJob', (), {
            'id': "small_job",
            'name': "Small Job",
            'files': self.test_files[:2],  # Only 2 files
            'analysis_mode': "Advanced (OpenAI)"
        })()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            result = self.processor.can_use_batch_processing(small_job)
            assert result is False
    
    def test_can_use_batch_processing_too_large(self):
        """Test batch processing eligibility - Files too large"""
        
        large_files = [
            type('MockFile', (), {
                'id': "large1",
                'name': "large1.mp3",
                'size_bytes': 50 * 1024 * 1024,  # 50MB
                'format': "mp3",
                'temp_path': "/tmp/large1.mp3"
            })(),
            type('MockFile', (), {
                'id': "large2", 
                'name': "large2.mp3",
                'size_bytes': 60 * 1024 * 1024,  # 60MB
                'format': "mp3",
                'temp_path': "/tmp/large2.mp3"
            })(),
            type('MockFile', (), {
                'id': "large3",
                'name': "large3.mp3", 
                'size_bytes': 40 * 1024 * 1024,  # 40MB
                'format': "mp3",
                'temp_path': "/tmp/large3.mp3"
            })()
        ]
        
        large_job = type('MockJob', (), {
            'id': "large_job",
            'name': "Large Job",
            'files': large_files,  # Total > 100MB
            'analysis_mode': "Advanced (OpenAI)"
        })()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            result = self.processor.can_use_batch_processing(large_job)
            assert result is False
    
    @patch('openai_batch_processor.OpenAI')
    def test_prepare_transcription_batch(self, mock_openai_client):
        """Test transcription batch preparation"""
        
        # Mock OpenAI client responses
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        
        # Mock batch creation response
        mock_batch_response = Mock()
        mock_batch_response.id = "batch_123"
        mock_batch_response.status = "validating"
        mock_client.batches.create.return_value = mock_batch_response
        
        # Mock file upload response
        mock_file_response = Mock()
        mock_file_response.id = "file_123"
        mock_client.files.create.return_value = mock_file_response
        
        # Create temporary audio files
        temp_dir = tempfile.mkdtemp()
        audio_files = {}
        
        try:
            for file_obj in self.test_files:
                temp_file = os.path.join(temp_dir, f"{file_obj.id}.mp3")
                with open(temp_file, 'wb') as f:
                    f.write(b"fake audio data")
                audio_files[file_obj.id] = temp_file
            
            # Test batch preparation
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                processor = OpenAIBatchProcessor()
                batch_id = processor.prepare_transcription_batch(self.test_job, audio_files)
            
            assert batch_id == "batch_123"
            assert mock_client.batches.create.called
            assert mock_client.files.create.called
            
            # Verify batch job was tracked
            assert f"transcribe_{self.test_job.id}" in processor.active_batches
            
        finally:
            # Cleanup
            for audio_file in audio_files.values():
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            os.rmdir(temp_dir)
    
    @patch('openai_batch_processor.OpenAI')
    def test_prepare_analysis_batch(self, mock_openai_client):
        """Test analysis batch preparation"""
        
        # Mock OpenAI client responses
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        
        # Mock batch creation response
        mock_batch_response = Mock()
        mock_batch_response.id = "batch_456"
        mock_batch_response.status = "validating"
        mock_client.batches.create.return_value = mock_batch_response
        
        # Mock file upload response
        mock_file_response = Mock()
        mock_file_response.id = "file_456"
        mock_client.files.create.return_value = mock_file_response
        
        # Test transcripts
        transcripts = {
            "file1": "This is the first test transcript",
            "file2": "This is the second test transcript", 
            "file3": "This is the third test transcript"
        }
        
        # Test batch preparation
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            processor = OpenAIBatchProcessor()
            batch_id = processor.prepare_analysis_batch(self.test_job, transcripts)
        
        assert batch_id == "batch_456"
        assert mock_client.batches.create.called
        assert mock_client.files.create.called
        
        # Verify batch job was tracked
        assert f"analyze_{self.test_job.id}" in processor.active_batches
    
    @patch('openai_batch_processor.OpenAI')
    def test_check_batch_status_completed(self, mock_openai_client):
        """Test checking batch status - completed case"""
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        
        # Create test batch job
        batch_job = OpenAIBatchJob(
            batch_id="test_batch",
            job_id="test_job",
            openai_batch_id="batch_123",
            request_type="transcription",
            file_requests={"file1": "custom_1", "file2": "custom_2"},
            status=OpenAIBatchStatus.IN_PROGRESS,
            created_at=datetime.now()
        )
        
        processor = OpenAIBatchProcessor()
        processor.active_batches["test_batch"] = batch_job
        
        # Mock batch status response - completed
        mock_batch_response = Mock()
        mock_batch_response.status = "completed"
        mock_batch_response.output_file_id = "output_123"
        mock_batch_response.errors = None
        mock_client.batches.retrieve.return_value = mock_batch_response
        
        # Mock results download
        mock_file_content = Mock()
        mock_file_content.read.return_value = b'{"custom_id": "custom_1", "response": {"status_code": 200, "body": {"text": "transcript"}}}\n'
        mock_client.files.content.return_value = mock_file_content
        
        # Test status check
        result = processor.check_batch_status("test_batch")
        
        assert result is not None
        assert result.status == OpenAIBatchStatus.COMPLETED
        assert result.completed_at is not None
        assert result.results is not None
    
    def test_process_transcription_results(self):
        """Test processing transcription results from batch"""
        
        # Create test batch job with results
        batch_job = OpenAIBatchJob(
            batch_id="test_batch",
            job_id="test_job", 
            openai_batch_id="batch_123",
            request_type="transcription",
            file_requests={"file1": "custom_1", "file2": "custom_2"},
            status=OpenAIBatchStatus.COMPLETED,
            created_at=datetime.now(),
            results={
                "custom_1": {
                    "response": {
                        "status_code": 200,
                        "body": {"text": "First transcript"}
                    }
                },
                "custom_2": {
                    "response": {
                        "status_code": 200,
                        "body": {"text": "Second transcript"}
                    }
                }
            }
        )
        
        processor = OpenAIBatchProcessor()
        transcripts = processor.process_transcription_results(batch_job)
        
        assert len(transcripts) == 2
        assert transcripts["file1"] == "First transcript"
        assert transcripts["file2"] == "Second transcript"
    
    def test_process_analysis_results(self):
        """Test processing analysis results from batch"""
        
        # Create test batch job with analysis results
        batch_job = OpenAIBatchJob(
            batch_id="test_batch",
            job_id="test_job",
            openai_batch_id="batch_123", 
            request_type="analysis",
            file_requests={"file1": "custom_1"},
            status=OpenAIBatchStatus.COMPLETED,
            created_at=datetime.now(),
            results={
                "custom_1": {
                    "response": {
                        "status_code": 200,
                        "body": {
                            "choices": [{
                                "message": {
                                    "function_call": {
                                        "name": "extract_entities",
                                        "arguments": json.dumps({
                                            "summary": "Test summary",
                                            "persons": ["John Doe"],
                                            "organizations": ["Test Corp"],
                                            "dates": ["2024"],
                                            "locations": ["New York"],
                                            "key_topics": ["testing"]
                                        })
                                    }
                                }
                            }]
                        }
                    }
                }
            }
        )
        
        processor = OpenAIBatchProcessor()
        analyses = processor.process_analysis_results(batch_job)
        
        assert len(analyses) == 1
        entities, summary = analyses["file1"]
        
        assert summary == "Test summary"
        assert entities["PERSON"] == ["John Doe"]
        assert entities["ORG"] == ["Test Corp"]
        assert entities["DATE"] == ["2024"]
        assert entities["GPE"] == ["New York"]
        assert entities["TOPIC"] == ["testing"]
    
    def test_get_batch_cost_estimate(self):
        """Test batch cost estimation"""
        
        processor = OpenAIBatchProcessor()
        cost_estimate = processor.get_batch_cost_estimate(self.test_job)
        
        assert 'standard_cost' in cost_estimate
        assert 'batch_cost' in cost_estimate
        assert 'savings' in cost_estimate
        assert 'savings_percentage' in cost_estimate
        
        assert cost_estimate['batch_cost'] < cost_estimate['standard_cost']
        assert cost_estimate['savings'] > 0
        assert cost_estimate['savings_percentage'] == 50.0  # 50% savings
    
    @patch('openai_batch_processor.OpenAI')
    def test_cancel_batch(self, mock_openai_client):
        """Test cancelling a batch job"""
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_client.return_value = mock_client
        
        # Create test batch job
        batch_job = OpenAIBatchJob(
            batch_id="test_batch",
            job_id="test_job",
            openai_batch_id="batch_123",
            request_type="transcription",
            file_requests={},
            status=OpenAIBatchStatus.IN_PROGRESS,
            created_at=datetime.now()
        )
        
        processor = OpenAIBatchProcessor()
        processor.active_batches["test_batch"] = batch_job
        
        # Test cancellation
        result = processor.cancel_batch("test_batch")
        
        assert result is True
        assert mock_client.batches.cancel.called
        assert batch_job.status == OpenAIBatchStatus.CANCELLING
    
    def test_cleanup_completed_batches(self):
        """Test cleanup of old completed batches"""
        
        processor = OpenAIBatchProcessor()
        
        # Add some test batches
        old_batch = OpenAIBatchJob(
            batch_id="old_batch",
            job_id="old_job",
            openai_batch_id="batch_old",
            request_type="transcription",
            file_requests={},
            status=OpenAIBatchStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        new_batch = OpenAIBatchJob(
            batch_id="new_batch", 
            job_id="new_job",
            openai_batch_id="batch_new",
            request_type="transcription",
            file_requests={},
            status=OpenAIBatchStatus.IN_PROGRESS,
            created_at=datetime.now()
        )
        
        processor.active_batches["old_batch"] = old_batch
        processor.active_batches["new_batch"] = new_batch
        
        # Cleanup with 0 hour max age (should remove completed batch)
        processor.cleanup_completed_batches(max_age_hours=0)
        
        assert "old_batch" not in processor.active_batches
        assert "new_batch" in processor.active_batches

if __name__ == "__main__":
    pytest.main([__file__, "-v"])