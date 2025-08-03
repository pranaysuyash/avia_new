"""
Celery Configuration
Sets up Celery for background task processing
"""

import os
from celery import Celery
from celery.signals import task_prerun, task_postrun
from sqlalchemy.orm import scoped_session
import logging

from api.database import SessionLocal

logger = logging.getLogger(__name__)

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery app
celery_app = Celery(
    "transcription_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["api.tasks"]  # Include task modules
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
    
    # Task routing
    task_routes={
        "api.tasks.process_transcription": {"queue": "transcription"},
        "api.tasks.process_video": {"queue": "video"},
        "api.tasks.cleanup_old_files": {"queue": "maintenance"},
    },
    
    # Task time limits
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    
    # Result backend settings
    result_expires=86400,  # Results expire after 1 day
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-files": {
            "task": "api.tasks.cleanup_old_files",
            "schedule": 86400.0,  # Run daily
            "options": {"queue": "maintenance"}
        },
        "update-storage-stats": {
            "task": "api.tasks.update_storage_stats",
            "schedule": 3600.0,  # Run hourly
            "options": {"queue": "maintenance"}
        },
    },
)

# Database session management for tasks
db_session = scoped_session(SessionLocal)

@task_prerun.connect
def on_task_prerun(sender=None, task_id=None, task=None, *args, **kwargs):
    """Create a new database session before each task"""
    logger.debug(f"Starting task {task.name} [{task_id}]")

@task_postrun.connect
def on_task_postrun(sender=None, task_id=None, task=None, *args, **kwargs):
    """Close the database session after each task"""
    logger.debug(f"Completed task {task.name} [{task_id}]")
    db_session.remove()

# Export the Celery app
__all__ = ["celery_app", "db_session"]