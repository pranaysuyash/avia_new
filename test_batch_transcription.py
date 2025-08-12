#!/usr/bin/env python3
"""
Test suite for Batch Transcription System
"""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
import numpy as np
import wave
import json

from batch_transcription_system import (
    BatchTranscriptionSystem,
    TranscriptionBatch,
    Priority,
    ProcessingStatus,
    WorkerStatus
)


@pytest.fixture
async def batch_system():
    """Create batch transcription system instance"""
    config = {
        'num_workers': 2,
        'max_retries': 2,
        'enable_gpu': False
    }
    system = BatchTranscriptionSystem(config)
    await system.initialize()
    yield system
    await system.shutdown()


@pytest.fixture
def sample_audio_files(tmp_path):
    """Create sample audio files for testing"""
    audio_files = []
    
    for i in range(3):
        # Create a simple WAV file
        filename = tmp_path / f"test_audio_{i}.wav"
        
        # Generate simple audio data
        sample_rate = 16000
        duration = 1  # 1 second
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, sample_rate * duration)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(str(filename), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        audio_files.append(str(filename))
    
    return audio_files


@pytest.mark.asyncio
async def test_create_batch(batch_system, sample_audio_files):
    """Test creating a transcription batch"""
    batch = await batch_system.create_batch(
        name="Test Batch",
        file_paths=sample_audio_files,
        priority=Priority.HIGH,
        config={'language': 'en'}
    )
    
    assert batch is not None
    assert batch.name == "Test Batch"
    assert batch.priority == Priority.HIGH
    assert len(batch.jobs) == len(sample_audio_files)
    assert batch.status == ProcessingStatus.PENDING


@pytest.mark.asyncio
async def test_batch_priority_ordering(batch_system, sample_audio_files):
    """Test that batches are processed by priority"""
    # Create batches with different priorities
    low_batch = await batch_system.create_batch(
        name="Low Priority",
        file_paths=[sample_audio_files[0]],
        priority=Priority.LOW
    )
    
    high_batch = await batch_system.create_batch(
        name="High Priority",
        file_paths=[sample_audio_files[1]],
        priority=Priority.HIGH
    )
    
    medium_batch = await batch_system.create_batch(
        name="Medium Priority",
        file_paths=[sample_audio_files[2]],
        priority=Priority.MEDIUM
    )
    
    # Check queue order
    queue_status = await batch_system.get_queue_status()
    
    # High priority should be first
    assert queue_status['queue'][0]['batch_id'] == high_batch.batch_id
    assert queue_status['queue'][0]['priority'] == 'high'


@pytest.mark.asyncio
async def test_pause_resume_batch(batch_system, sample_audio_files):
    """Test pausing and resuming a batch"""
    batch = await batch_system.create_batch(
        name="Pause Test",
        file_paths=sample_audio_files,
        priority=Priority.MEDIUM
    )
    
    # Start processing
    await batch_system.start_batch(batch.batch_id)
    
    # Pause
    success = await batch_system.pause_batch(batch.batch_id)
    assert success
    
    status = await batch_system.get_batch_status(batch.batch_id)
    assert status.status == ProcessingStatus.PAUSED
    
    # Resume
    success = await batch_system.resume_batch(batch.batch_id)
    assert success
    
    status = await batch_system.get_batch_status(batch.batch_id)
    assert status.status in [ProcessingStatus.PROCESSING, ProcessingStatus.PENDING]


@pytest.mark.asyncio
async def test_cancel_batch(batch_system, sample_audio_files):
    """Test canceling a batch"""
    batch = await batch_system.create_batch(
        name="Cancel Test",
        file_paths=sample_audio_files,
        priority=Priority.LOW
    )
    
    # Cancel batch
    success = await batch_system.cancel_batch(batch.batch_id)
    assert success
    
    status = await batch_system.get_batch_status(batch.batch_id)
    assert status.status == ProcessingStatus.CANCELLED


@pytest.mark.asyncio
async def test_retry_failed_jobs(batch_system):
    """Test retrying failed jobs"""
    # Create a batch with an invalid file to trigger failure
    invalid_file = "/nonexistent/file.wav"
    
    batch = await batch_system.create_batch(
        name="Retry Test",
        file_paths=[invalid_file],
        priority=Priority.MEDIUM
    )
    
    # Process (will fail)
    await batch_system.start_batch(batch.batch_id)
    await asyncio.sleep(1)  # Wait for processing
    
    # Check for failed jobs
    status = await batch_system.get_batch_status(batch.batch_id)
    assert any(job.status == ProcessingStatus.FAILED for job in status.jobs)
    
    # Retry failed jobs
    retried = await batch_system.retry_failed_jobs(batch.batch_id)
    assert retried > 0


@pytest.mark.asyncio
async def test_worker_management(batch_system):
    """Test worker pool management"""
    # Get worker status
    workers = await batch_system.get_worker_status()
    assert len(workers) > 0
    
    # Check worker states
    for worker in workers:
        assert worker['status'] in ['idle', 'processing']
        assert 'jobs_processed' in worker
        assert 'current_job' in worker


@pytest.mark.asyncio
async def test_batch_statistics(batch_system, sample_audio_files):
    """Test batch statistics and monitoring"""
    batch = await batch_system.create_batch(
        name="Stats Test",
        file_paths=sample_audio_files,
        priority=Priority.MEDIUM
    )
    
    # Get statistics
    stats = await batch_system.get_batch_statistics(batch.batch_id)
    
    assert 'total_jobs' in stats
    assert 'completed_jobs' in stats
    assert 'failed_jobs' in stats
    assert 'average_processing_time' in stats
    assert stats['total_jobs'] == len(sample_audio_files)


@pytest.mark.asyncio
async def test_export_results(batch_system, sample_audio_files, tmp_path):
    """Test exporting batch results"""
    batch = await batch_system.create_batch(
        name="Export Test",
        file_paths=sample_audio_files,
        priority=Priority.HIGH
    )
    
    # Export results
    export_formats = ['json', 'csv', 'txt']
    
    for format in export_formats:
        output_file = tmp_path / f"export.{format}"
        exported = await batch_system.export_results(
            batch.batch_id,
            str(output_file),
            format=format
        )
        
        assert exported
        assert output_file.exists()


@pytest.mark.asyncio
async def test_concurrent_batches(batch_system, sample_audio_files):
    """Test processing multiple batches concurrently"""
    batches = []
    
    # Create multiple batches
    for i in range(3):
        batch = await batch_system.create_batch(
            name=f"Concurrent Batch {i}",
            file_paths=[sample_audio_files[i]],
            priority=Priority.MEDIUM
        )
        batches.append(batch)
    
    # Start all batches
    for batch in batches:
        await batch_system.start_batch(batch.batch_id)
    
    # Check that multiple batches are processing
    queue_status = await batch_system.get_queue_status()
    assert queue_status['active_batches'] > 0


@pytest.mark.asyncio
async def test_resource_monitoring(batch_system):
    """Test resource usage monitoring"""
    resources = await batch_system.get_resource_usage()
    
    assert 'cpu_usage' in resources
    assert 'memory_usage' in resources
    assert 'gpu_usage' in resources
    assert 'disk_usage' in resources
    
    # Values should be percentages
    assert 0 <= resources['cpu_usage'] <= 100
    assert 0 <= resources['memory_usage'] <= 100


@pytest.mark.asyncio
async def test_batch_webhooks(batch_system, sample_audio_files):
    """Test webhook notifications for batch events"""
    webhook_url = "http://example.com/webhook"
    
    batch = await batch_system.create_batch(
        name="Webhook Test",
        file_paths=sample_audio_files,
        priority=Priority.HIGH,
        webhook_url=webhook_url
    )
    
    assert batch.webhook_url == webhook_url
    
    # Verify webhook would be called on status changes
    # (In real implementation, would mock HTTP calls)


@pytest.mark.asyncio
async def test_batch_scheduling(batch_system, sample_audio_files):
    """Test scheduled batch processing"""
    from datetime import datetime, timedelta
    
    # Schedule batch for future
    scheduled_time = datetime.now() + timedelta(minutes=5)
    
    batch = await batch_system.create_batch(
        name="Scheduled Batch",
        file_paths=sample_audio_files,
        priority=Priority.LOW,
        scheduled_time=scheduled_time
    )
    
    assert batch.scheduled_time == scheduled_time
    assert batch.status == ProcessingStatus.SCHEDULED


@pytest.mark.asyncio
async def test_batch_dependencies(batch_system, sample_audio_files):
    """Test batch dependencies"""
    # Create parent batch
    parent_batch = await batch_system.create_batch(
        name="Parent Batch",
        file_paths=[sample_audio_files[0]],
        priority=Priority.HIGH
    )
    
    # Create dependent batch
    dependent_batch = await batch_system.create_batch(
        name="Dependent Batch",
        file_paths=[sample_audio_files[1]],
        priority=Priority.HIGH,
        depends_on=[parent_batch.batch_id]
    )
    
    # Dependent should wait for parent
    assert dependent_batch.status == ProcessingStatus.WAITING


@pytest.mark.asyncio
async def test_error_handling(batch_system):
    """Test error handling for various scenarios"""
    
    # Test with empty file list
    with pytest.raises(ValueError):
        await batch_system.create_batch(
            name="Empty Batch",
            file_paths=[],
            priority=Priority.MEDIUM
        )
    
    # Test with invalid priority
    with pytest.raises(ValueError):
        await batch_system.create_batch(
            name="Invalid Priority",
            file_paths=["/test.wav"],
            priority="INVALID"
        )
    
    # Test with non-existent batch ID
    status = await batch_system.get_batch_status("non-existent-id")
    assert status is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])