"""
Task functions for background job processing
"""

import asyncio
import logging
import os
import json
import tempfile
from typing import Dict, Any
from datetime import datetime

from .job_manager import Job, JobManager

logger = logging.getLogger(__name__)


async def export_transcript_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Export transcript to various formats
    
    Expected job.data:
    - transcript_id: ID of transcript to export
    - export_type: 'pdf', 'docx', 'json', 'csv'
    - user_id: User requesting export
    """
    from .workers import ExportWorker
    
    worker = ExportWorker()
    return await worker.execute(job, job_manager)


async def process_media_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Process media files (transcription, analysis)
    
    Expected job.data:
    - file_path: Path to media file
    - processing_type: 'transcription' or 'analysis'
    - language: Language code (optional, defaults to 'en')
    - transcript: Transcript text (for analysis)
    """
    from .workers import ProcessingWorker
    
    worker = ProcessingWorker()
    return await worker.execute(job, job_manager)


async def send_notification_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Send notifications via email, push, or webhook
    
    Expected job.data:
    - type: 'email', 'push', or 'webhook'
    - recipient: Email address (for email)
    - user_id: User ID (for push)
    - url: Webhook URL (for webhook)
    - subject: Email subject
    - body/message: Notification content
    - payload: Webhook payload
    """
    from .workers import NotificationWorker
    
    worker = NotificationWorker()
    return await worker.execute(job, job_manager)


async def cleanup_old_files_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Clean up old files and data
    
    Expected job.data:
    - type: 'temp_files', 'old_jobs', or 'logs'
    - directory: Directory to clean (optional)
    - max_age_hours: Max age for temp files (optional)
    - max_age_days: Max age for jobs (optional)
    - max_size_mb: Max size for logs (optional)
    """
    from .workers import CleanupWorker
    
    worker = CleanupWorker()
    return await worker.execute(job, job_manager)


# Additional specialized task functions

async def generate_report_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Generate analytics reports
    
    Expected job.data:
    - report_type: 'usage', 'performance', 'user_activity'
    - date_range: {'start': '2024-01-01', 'end': '2024-01-31'}
    - format: 'pdf', 'csv', 'json'
    - user_id: User requesting report
    """
    await job_manager.update_progress(job.id, 10, "Initializing report generation")
    
    report_type = job.data.get('report_type')
    date_range = job.data.get('date_range', {})
    format_type = job.data.get('format', 'pdf')
    
    await job_manager.update_progress(job.id, 30, f"Collecting {report_type} data")
    await asyncio.sleep(2)  # Simulate data collection
    
    await job_manager.update_progress(job.id, 60, "Processing report data")
    await asyncio.sleep(3)  # Simulate processing
    
    await job_manager.update_progress(job.id, 90, f"Generating {format_type} report")
    await asyncio.sleep(2)  # Simulate report generation
    
    output_path = f"/tmp/report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
    
    return {
        'report_type': report_type,
        'format': format_type,
        'file_path': output_path,
        'date_range': date_range,
        'generated_at': datetime.utcnow().isoformat(),
        'records_processed': 1250
    }


async def backup_data_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Create data backups
    
    Expected job.data:
    - backup_type: 'full', 'incremental', 'database'
    - destination: 's3', 'local', 'ftp'
    - encryption: boolean
    - compression: boolean
    """
    await job_manager.update_progress(job.id, 5, "Preparing backup")
    
    backup_type = job.data.get('backup_type', 'incremental')
    destination = job.data.get('destination', 'local')
    encryption = job.data.get('encryption', True)
    compression = job.data.get('compression', True)
    
    await job_manager.update_progress(job.id, 20, "Collecting backup data")
    await asyncio.sleep(3)
    
    await job_manager.update_progress(job.id, 50, "Creating backup archive")
    await asyncio.sleep(5)
    
    if compression:
        await job_manager.update_progress(job.id, 70, "Compressing backup")
        await asyncio.sleep(2)
    
    if encryption:
        await job_manager.update_progress(job.id, 85, "Encrypting backup")
        await asyncio.sleep(2)
    
    await job_manager.update_progress(job.id, 95, f"Uploading to {destination}")
    await asyncio.sleep(2)
    
    backup_filename = f"backup_{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    
    return {
        'backup_type': backup_type,
        'destination': destination,
        'filename': backup_filename,
        'size_mb': 245.7,
        'encrypted': encryption,
        'compressed': compression,
        'created_at': datetime.utcnow().isoformat()
    }


async def sync_external_data_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Sync data with external systems
    
    Expected job.data:
    - source: 'api', 'ftp', 'database'
    - endpoint: API endpoint or connection string
    - sync_type: 'full', 'delta'
    - authentication: Auth credentials
    """
    await job_manager.update_progress(job.id, 10, "Connecting to external source")
    
    source = job.data.get('source')
    sync_type = job.data.get('sync_type', 'delta')
    
    await asyncio.sleep(2)  # Simulate connection
    
    await job_manager.update_progress(job.id, 30, "Fetching external data")
    await asyncio.sleep(4)  # Simulate data fetch
    
    await job_manager.update_progress(job.id, 60, "Processing and validating data")
    await asyncio.sleep(3)  # Simulate processing
    
    await job_manager.update_progress(job.id, 80, "Updating local database")
    await asyncio.sleep(2)  # Simulate database updates
    
    await job_manager.update_progress(job.id, 95, "Finalizing sync")
    await asyncio.sleep(1)
    
    return {
        'source': source,
        'sync_type': sync_type,
        'records_synced': 1847,
        'records_updated': 234,
        'records_new': 156,
        'sync_duration_seconds': 12.5,
        'completed_at': datetime.utcnow().isoformat()
    }


async def optimize_database_task(job: Job, job_manager: JobManager) -> Dict[str, Any]:
    """
    Optimize database performance
    
    Expected job.data:
    - operation: 'vacuum', 'reindex', 'analyze', 'cleanup'
    - tables: List of table names (optional)
    """
    await job_manager.update_progress(job.id, 10, "Starting database optimization")
    
    operation = job.data.get('operation', 'analyze')
    tables = job.data.get('tables', [])
    
    if operation == 'vacuum':
        await job_manager.update_progress(job.id, 30, "Running VACUUM operation")
        await asyncio.sleep(8)  # VACUUM can take time
        
    elif operation == 'reindex':
        await job_manager.update_progress(job.id, 40, "Rebuilding indexes")
        await asyncio.sleep(6)
        
    elif operation == 'analyze':
        await job_manager.update_progress(job.id, 50, "Analyzing table statistics")
        await asyncio.sleep(4)
        
    elif operation == 'cleanup':
        await job_manager.update_progress(job.id, 60, "Cleaning up old data")
        await asyncio.sleep(5)
    
    await job_manager.update_progress(job.id, 90, "Finalizing optimization")
    await asyncio.sleep(1)
    
    return {
        'operation': operation,
        'tables_processed': len(tables) if tables else 15,
        'space_freed_mb': 128.4,
        'performance_improvement': '12%',
        'duration_seconds': 19.2,
        'completed_at': datetime.utcnow().isoformat()
    }


# Task registry for easy lookup
TASK_REGISTRY = {
    'export_transcript': export_transcript_task,
    'process_media': process_media_task,
    'send_notification': send_notification_task,
    'cleanup_old_files': cleanup_old_files_task,
    'generate_report': generate_report_task,
    'backup_data': backup_data_task,
    'sync_external_data': sync_external_data_task,
    'optimize_database': optimize_database_task,
}


def get_task_function(task_name: str):
    """Get task function by name"""
    return TASK_REGISTRY.get(task_name)


def list_available_tasks():
    """List all available task names"""
    return list(TASK_REGISTRY.keys())