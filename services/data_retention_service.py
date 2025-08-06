"""
Data Retention Service
Manages data lifecycle, retention policies, and automated cleanup
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean, Text

from database.connection import get_db_session_factory
from database.models import Base
import uuid

logger = logging.getLogger(__name__)

class RetentionPolicy(Base):
    __tablename__ = "retention_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_type = Column(String, nullable=False)  # transcripts, audit_logs, user_data, etc.
    retention_days = Column(Integer, nullable=False)
    auto_delete = Column(Boolean, default=False)
    archive_before_delete = Column(Boolean, default=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON, default=dict)

class RetentionJob(Base):
    __tablename__ = "retention_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # cleanup, archive, purge
    status = Column(String, default='pending')  # pending, running, completed, failed
    records_processed = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    records_archived = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)

class DataRetentionService:
    """Service for managing data retention policies and cleanup"""
    
    # Default retention periods (in days)
    DEFAULT_RETENTION_POLICIES = {
        'transcripts': 2555,  # 7 years for business records
        'audit_logs': 2555,   # 7 years for compliance
        'user_data': 2190,    # 6 years for user account data
        'session_logs': 90,   # 3 months for session data
        'temp_files': 7,      # 1 week for temporary files
        'api_logs': 365,      # 1 year for API access logs
        'backups': 90,        # 3 months for backup files
        'exports': 30,        # 1 month for data exports
        'notifications': 180, # 6 months for notifications
        'webhooks': 365       # 1 year for webhook logs
    }
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.db_session_factory()
    
    def initialize_default_policies(self, created_by: str) -> bool:
        """Initialize default retention policies"""
        db = self._get_db()
        try:
            # Check if policies already exist
            existing_count = db.query(RetentionPolicy).count()
            if existing_count > 0:
                logger.info("Retention policies already initialized")
                return True
            
            # Create default policies
            for data_type, retention_days in self.DEFAULT_RETENTION_POLICIES.items():
                policy = RetentionPolicy(
                    data_type=data_type,
                    retention_days=retention_days,
                    auto_delete=data_type in ['temp_files', 'session_logs', 'exports'],
                    archive_before_delete=data_type in ['transcripts', 'audit_logs', 'user_data'],
                    created_by=created_by,
                    extra_data={
                        'default_policy': True,
                        'description': f'Default retention policy for {data_type}'
                    }
                )
                db.add(policy)
            
            db.commit()
            logger.info("Default retention policies created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing retention policies: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_policy(self, data_type: str) -> Optional[RetentionPolicy]:
        """Get retention policy for a data type"""
        db = self._get_db()
        try:
            policy = db.query(RetentionPolicy).filter(
                RetentionPolicy.data_type == data_type,
                RetentionPolicy.is_active == True
            ).first()
            return policy
        finally:
            db.close()
    
    def create_policy(
        self,
        data_type: str,
        retention_days: int,
        created_by: str,
        auto_delete: bool = False,
        archive_before_delete: bool = True,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> RetentionPolicy:
        """Create a new retention policy"""
        db = self._get_db()
        try:
            # Deactivate existing policy for this data type
            existing = db.query(RetentionPolicy).filter(
                RetentionPolicy.data_type == data_type,
                RetentionPolicy.is_active == True
            ).first()
            
            if existing:
                existing.is_active = False
                existing.updated_at = datetime.utcnow()
            
            # Create new policy
            policy = RetentionPolicy(
                data_type=data_type,
                retention_days=retention_days,
                auto_delete=auto_delete,
                archive_before_delete=archive_before_delete,
                created_by=created_by,
                extra_data=extra_data or {}
            )
            
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
            logger.info(f"Created retention policy for {data_type}: {retention_days} days")
            return policy
            
        except Exception as e:
            logger.error(f"Error creating retention policy: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def update_policy(
        self,
        policy_id: str,
        retention_days: Optional[int] = None,
        auto_delete: Optional[bool] = None,
        archive_before_delete: Optional[bool] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing retention policy"""
        db = self._get_db()
        try:
            policy = db.query(RetentionPolicy).filter(
                RetentionPolicy.id == policy_id
            ).first()
            
            if not policy:
                return False
            
            if retention_days is not None:
                policy.retention_days = retention_days
            if auto_delete is not None:
                policy.auto_delete = auto_delete
            if archive_before_delete is not None:
                policy.archive_before_delete = archive_before_delete
            if extra_data is not None:
                policy.extra_data = extra_data
            
            policy.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Updated retention policy {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating retention policy: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_expired_data(self, data_type: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get data that has exceeded retention period"""
        policy = self.get_policy(data_type)
        if not policy:
            logger.warning(f"No retention policy found for {data_type}")
            return []
        
        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
        
        db = self._get_db()
        try:
            # This is a generic approach - in practice, you'd have specific queries for each data type
            if data_type == 'transcripts':
                from database.models import Transcript
                expired = db.query(Transcript).filter(
                    Transcript.created_at < cutoff_date
                ).limit(limit).all()
                
                return [
                    {
                        'id': t.id,
                        'created_at': t.created_at,
                        'size_estimate': len(t.transcription_text or '') if hasattr(t, 'transcription_text') else 0
                    }
                    for t in expired
                ]
            
            elif data_type == 'audit_logs':
                from api.middleware.audit_logging import AuditLog
                expired = db.query(AuditLog).filter(
                    AuditLog.created_at < cutoff_date
                ).limit(limit).all()
                
                return [
                    {
                        'id': log.id,
                        'created_at': log.created_at,
                        'user_id': log.user_id,
                        'action': log.action
                    }
                    for log in expired
                ]
            
            else:
                logger.warning(f"No specific query implemented for data type: {data_type}")
                return []
                
        except Exception as e:
            logger.error(f"Error finding expired data for {data_type}: {e}")
            return []
        finally:
            db.close()
    
    def create_retention_job(
        self,
        policy_id: str,
        job_type: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> RetentionJob:
        """Create a new retention job"""
        db = self._get_db()
        try:
            job = RetentionJob(
                policy_id=policy_id,
                job_type=job_type,
                extra_data=extra_data or {}
            )
            
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Created retention job {job.id} for policy {policy_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error creating retention job: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def execute_cleanup_job(self, job_id: str) -> bool:
        """Execute a cleanup job"""
        db = self._get_db()
        try:
            job = db.query(RetentionJob).filter(RetentionJob.id == job_id).first()
            if not job:
                logger.error(f"Retention job {job_id} not found")
                return False
            
            policy = db.query(RetentionPolicy).filter(
                RetentionPolicy.id == job.policy_id
            ).first()
            
            if not policy:
                logger.error(f"Policy {job.policy_id} not found")
                return False
            
            # Update job status
            job.status = 'running'
            job.started_at = datetime.utcnow()
            db.commit()
            
            # Get expired data
            expired_data = self.get_expired_data(policy.data_type)
            
            records_processed = 0
            records_deleted = 0
            records_archived = 0
            
            try:
                for record in expired_data:
                    records_processed += 1
                    
                    # Archive if required
                    if policy.archive_before_delete:
                        if self._archive_record(policy.data_type, record):
                            records_archived += 1
                    
                    # Delete the record
                    if self._delete_record(policy.data_type, record['id']):
                        records_deleted += 1
                
                # Update job completion
                job.status = 'completed'
                job.records_processed = records_processed
                job.records_deleted = records_deleted
                job.records_archived = records_archived
                job.completed_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(
                    f"Retention job {job_id} completed: "
                    f"processed={records_processed}, deleted={records_deleted}, archived={records_archived}"
                )
                return True
                
            except Exception as e:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
                logger.error(f"Retention job {job_id} failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing retention job {job_id}: {e}")
            return False
        finally:
            db.close()
    
    def _archive_record(self, data_type: str, record: Dict[str, Any]) -> bool:
        """Archive a record before deletion"""
        try:
            # In a real implementation, this would save to long-term storage
            # like S3 Glacier, tape storage, or another archive system
            
            archive_data = {
                'data_type': data_type,
                'record_id': record['id'],
                'archived_at': datetime.utcnow().isoformat(),
                'original_created_at': record.get('created_at', '').isoformat() if isinstance(record.get('created_at'), datetime) else str(record.get('created_at', '')),
                'metadata': record
            }
            
            # For demo purposes, we'll just log the archive operation
            logger.info(f"Archived {data_type} record {record['id']}")
            
            # In production, you would:
            # 1. Serialize the full record data
            # 2. Compress it
            # 3. Upload to archive storage (S3 Glacier, etc.)
            # 4. Store archive location reference
            
            return True
            
        except Exception as e:
            logger.error(f"Error archiving {data_type} record {record['id']}: {e}")
            return False
    
    def _delete_record(self, data_type: str, record_id: str) -> bool:
        """Delete a record from the database"""
        db = self._get_db()
        try:
            if data_type == 'transcripts':
                from database.models import Transcript
                record = db.query(Transcript).filter(
                    Transcript.id == record_id
                ).first()
                if record:
                    db.delete(record)
            
            elif data_type == 'audit_logs':
                from api.middleware.audit_logging import AuditLog
                record = db.query(AuditLog).filter(
                    AuditLog.id == record_id
                ).first()
                if record:
                    db.delete(record)
            
            # Add more data types as needed
            
            db.commit()
            logger.debug(f"Deleted {data_type} record {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {data_type} record {record_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def run_automated_cleanup(self) -> Dict[str, Any]:
        """Run automated cleanup for all policies with auto_delete enabled"""
        db = self._get_db()
        try:
            auto_policies = db.query(RetentionPolicy).filter(
                RetentionPolicy.auto_delete == True,
                RetentionPolicy.is_active == True
            ).all()
            
            results = []
            
            for policy in auto_policies:
                try:
                    # Create and execute cleanup job
                    job = self.create_retention_job(
                        policy_id=policy.id,
                        job_type='automated_cleanup',
                        extra_data={
                            'data_type': policy.data_type,
                            'retention_days': policy.retention_days,
                            'scheduled': True
                        }
                    )
                    
                    success = self.execute_cleanup_job(job.id)
                    
                    results.append({
                        'data_type': policy.data_type,
                        'policy_id': policy.id,
                        'job_id': job.id,
                        'success': success
                    })
                    
                except Exception as e:
                    logger.error(f"Error in automated cleanup for {policy.data_type}: {e}")
                    results.append({
                        'data_type': policy.data_type,
                        'policy_id': policy.id,
                        'success': False,
                        'error': str(e)
                    })
            
            summary = {
                'total_policies': len(auto_policies),
                'successful_jobs': len([r for r in results if r['success']]),
                'failed_jobs': len([r for r in results if not r['success']]),
                'results': results,
                'executed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Automated cleanup completed: {summary['successful_jobs']}/{summary['total_policies']} policies processed successfully"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in automated cleanup: {e}")
            return {
                'total_policies': 0,
                'successful_jobs': 0,
                'failed_jobs': 1,
                'error': str(e),
                'executed_at': datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    
    def get_retention_status(self) -> Dict[str, Any]:
        """Get overall retention status and statistics"""
        db = self._get_db()
        try:
            policies = db.query(RetentionPolicy).filter(
                RetentionPolicy.is_active == True
            ).all()
            
            recent_jobs = db.query(RetentionJob).order_by(
                RetentionJob.created_at.desc()
            ).limit(10).all()
            
            status = {
                'total_policies': len(policies),
                'auto_delete_policies': len([p for p in policies if p.auto_delete]),
                'policies_by_type': {},
                'recent_jobs': [],
                'next_cleanup_estimates': {}
            }
            
            for policy in policies:
                status['policies_by_type'][policy.data_type] = {
                    'retention_days': policy.retention_days,
                    'auto_delete': policy.auto_delete,
                    'archive_before_delete': policy.archive_before_delete
                }
                
                # Estimate next cleanup
                if policy.auto_delete:
                    expired_count = len(self.get_expired_data(policy.data_type, limit=100))
                    status['next_cleanup_estimates'][policy.data_type] = {
                        'estimated_records': expired_count,
                        'policy_id': policy.id
                    }
            
            for job in recent_jobs:
                status['recent_jobs'].append({
                    'id': job.id,
                    'job_type': job.job_type,
                    'status': job.status,
                    'records_processed': job.records_processed,
                    'records_deleted': job.records_deleted,
                    'created_at': job.created_at.isoformat(),
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting retention status: {e}")
            return {'error': str(e)}
        finally:
            db.close()

# Global instance
db_session_factory = get_db_session_factory()
data_retention_service = DataRetentionService(db_session_factory)