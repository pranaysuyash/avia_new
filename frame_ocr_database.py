"""
Frame OCR Database Schema and Management

This module provides comprehensive database schema implementation for the Frame OCR
Indexing System with support for multi-tenancy, temporal consolidation, and data lineage.
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path

from frame_ocr_models import (
    FrameOCRJob, FrameOCRResult, TextSegment, BoundingBox,
    JobStatus, OCREngine, RegionType, ModelValidator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.db_type = os.getenv('FRAME_OCR_DB_TYPE', 'sqlite')
        self.db_host = os.getenv('FRAME_OCR_DB_HOST', 'localhost')
        self.db_port = int(os.getenv('FRAME_OCR_DB_PORT', '5432'))
        self.db_name = os.getenv('FRAME_OCR_DB_NAME', 'frame_ocr.db')
        self.db_user = os.getenv('FRAME_OCR_DB_USER', 'postgres')
        self.db_password = os.getenv('FRAME_OCR_DB_PASSWORD', '')
        self.connection_pool_size = int(os.getenv('FRAME_OCR_DB_POOL_SIZE', '10'))
    
    def get_connection_string(self) -> str:
        """Get database connection string"""
        if self.db_type == 'postgresql':
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            return self.db_name


class FrameOCRDatabase:
    """Database manager for Frame OCR system"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.db_type = self.config.db_type
        self._connection = None
        self._setup_database()
    
    def _setup_database(self):
        """Initialize database schema"""
        logger.info(f"Setting up {self.db_type} database")
        
        if self.db_type == 'postgresql':
            self._setup_postgresql()
        else:
            self._setup_sqlite()
    
    def _setup_sqlite(self):
        """Setup SQLite database"""
        db_path = Path(self.config.db_name)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            self._create_sqlite_tables(cursor)
            self._create_indices(cursor)
            
            conn.commit()
            logger.info("SQLite database setup completed")
    
    def _setup_postgresql(self):
        """Setup PostgreSQL database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create extensions
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
            
            # Create tables
            self._create_postgresql_tables(cursor)
            self._create_indices(cursor)
            
            conn.commit()
            logger.info("PostgreSQL database setup completed")
    
    def _create_sqlite_tables(self, cursor):
        """Create SQLite tables"""
        
        # Tenants table for multi-tenancy
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id TEXT PRIMARY KEY,
                tenant_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings JSON,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Frame OCR Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_ocr_jobs (
                job_id TEXT PRIMARY KEY,
                video_id TEXT NOT NULL,
                video_path TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL,
                config JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                progress REAL DEFAULT 0.0,
                frames_processed INTEGER DEFAULT 0,
                total_frames INTEGER DEFAULT 0,
                error_message TEXT NULL,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                estimated_cost REAL DEFAULT 0.0,
                actual_cost REAL DEFAULT 0.0,
                processing_node TEXT NULL,
                data_lineage JSON DEFAULT '{}',
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Frame OCR Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_ocr_results (
                result_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                frame_number INTEGER NOT NULL,
                text TEXT NOT NULL,
                confidence REAL NOT NULL,
                language TEXT NOT NULL,
                bounding_boxes JSON NULL,
                text_segments JSON NULL,
                ocr_engine TEXT NOT NULL,
                preprocessing_applied BOOLEAN DEFAULT FALSE,
                processing_time REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON DEFAULT '{}',
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Text Segments table for temporal consolidation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS text_segments (
                segment_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                text TEXT NOT NULL,
                confidence REAL NOT NULL,
                language TEXT NOT NULL,
                bounding_box JSON NULL,
                stability_score REAL DEFAULT 0.0,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                region_classification TEXT DEFAULT 'unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Temporal consolidation tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_consolidation (
                consolidation_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                text_hash TEXT NOT NULL,
                consolidated_text TEXT NOT NULL,
                segment_ids JSON NOT NULL,
                stability_score REAL NOT NULL,
                confidence_avg REAL NOT NULL,
                confidence_min REAL NOT NULL,
                confidence_max REAL NOT NULL,
                first_occurrence TIMESTAMP NOT NULL,
                last_occurrence TIMESTAMP NOT NULL,
                occurrence_count INTEGER NOT NULL,
                region_type TEXT DEFAULT 'unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Processing metrics for monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_metrics (
                metric_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON DEFAULT '{}',
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Audit log for compliance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                user_id TEXT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT NULL,
                user_agent TEXT NULL,
                details JSON DEFAULT '{}',
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
    
    def _create_postgresql_tables(self, cursor):
        """Create PostgreSQL tables with advanced features"""
        
        # Tenants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                tenant_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                settings JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Frame OCR Jobs table with partitioning support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_ocr_jobs (
                job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                video_id VARCHAR(255) NOT NULL,
                video_path TEXT NOT NULL,
                tenant_id UUID NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL,
                config JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP WITH TIME ZONE NULL,
                completed_at TIMESTAMP WITH TIME ZONE NULL,
                progress REAL DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 1.0),
                frames_processed INTEGER DEFAULT 0 CHECK (frames_processed >= 0),
                total_frames INTEGER DEFAULT 0 CHECK (total_frames >= 0),
                error_message TEXT NULL,
                retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
                max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0),
                estimated_cost DECIMAL(10,4) DEFAULT 0.0 CHECK (estimated_cost >= 0),
                actual_cost DECIMAL(10,4) DEFAULT 0.0 CHECK (actual_cost >= 0),
                processing_node VARCHAR(255) NULL,
                data_lineage JSONB DEFAULT '{}',
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Frame OCR Results table with full-text search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_ocr_results (
                result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                job_id UUID NOT NULL,
                video_id VARCHAR(255) NOT NULL,
                tenant_id UUID NOT NULL,
                timestamp REAL NOT NULL CHECK (timestamp >= 0),
                frame_number INTEGER NOT NULL CHECK (frame_number >= 0),
                text TEXT NOT NULL,
                confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
                language VARCHAR(10) NOT NULL,
                bounding_boxes JSONB NULL,
                text_segments JSONB NULL,
                ocr_engine VARCHAR(50) NOT NULL,
                preprocessing_applied BOOLEAN DEFAULT FALSE,
                processing_time REAL DEFAULT 0.0 CHECK (processing_time >= 0),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                text_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Text Segments table with temporal tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS text_segments (
                segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                job_id UUID NOT NULL,
                video_id VARCHAR(255) NOT NULL,
                tenant_id UUID NOT NULL,
                text TEXT NOT NULL,
                confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
                language VARCHAR(10) NOT NULL,
                bounding_box JSONB NULL,
                stability_score REAL DEFAULT 0.0 CHECK (stability_score >= 0.0 AND stability_score <= 1.0),
                first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
                last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
                occurrence_count INTEGER DEFAULT 1 CHECK (occurrence_count >= 1),
                region_classification VARCHAR(50) DEFAULT 'unknown',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Temporal consolidation with advanced analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_consolidation (
                consolidation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                job_id UUID NOT NULL,
                video_id VARCHAR(255) NOT NULL,
                tenant_id UUID NOT NULL,
                text_hash VARCHAR(64) NOT NULL,
                consolidated_text TEXT NOT NULL,
                segment_ids JSONB NOT NULL,
                stability_score REAL NOT NULL CHECK (stability_score >= 0.0 AND stability_score <= 1.0),
                confidence_avg REAL NOT NULL CHECK (confidence_avg >= 0.0 AND confidence_avg <= 1.0),
                confidence_min REAL NOT NULL CHECK (confidence_min >= 0.0 AND confidence_min <= 1.0),
                confidence_max REAL NOT NULL CHECK (confidence_max >= 0.0 AND confidence_max <= 1.0),
                first_occurrence TIMESTAMP WITH TIME ZONE NOT NULL,
                last_occurrence TIMESTAMP WITH TIME ZONE NOT NULL,
                occurrence_count INTEGER NOT NULL CHECK (occurrence_count >= 1),
                region_type VARCHAR(50) DEFAULT 'unknown',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Processing metrics with time-series optimization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_metrics (
                metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                job_id UUID NOT NULL,
                tenant_id UUID NOT NULL,
                metric_type VARCHAR(100) NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                FOREIGN KEY (job_id) REFERENCES frame_ocr_jobs(job_id),
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        
        # Comprehensive audit log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                tenant_id UUID NOT NULL,
                user_id VARCHAR(255) NULL,
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(100) NOT NULL,
                resource_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                ip_address INET NULL,
                user_agent TEXT NULL,
                details JSONB DEFAULT '{}',
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
    
    def _create_indices(self, cursor):
        """Create database indices for performance optimization"""
        
        indices = [
            # Jobs table indices
            "CREATE INDEX IF NOT EXISTS idx_jobs_tenant_id ON frame_ocr_jobs(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_video_id ON frame_ocr_jobs(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON frame_ocr_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON frame_ocr_jobs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON frame_ocr_jobs(user_id)",
            
            # Results table indices
            "CREATE INDEX IF NOT EXISTS idx_results_job_id ON frame_ocr_results(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_results_video_id ON frame_ocr_results(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_results_tenant_id ON frame_ocr_results(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_results_timestamp ON frame_ocr_results(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_results_confidence ON frame_ocr_results(confidence)",
            "CREATE INDEX IF NOT EXISTS idx_results_language ON frame_ocr_results(language)",
            "CREATE INDEX IF NOT EXISTS idx_results_ocr_engine ON frame_ocr_results(ocr_engine)",
            
            # Text segments indices
            "CREATE INDEX IF NOT EXISTS idx_segments_job_id ON text_segments(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_segments_video_id ON text_segments(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_segments_tenant_id ON text_segments(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_segments_stability ON text_segments(stability_score)",
            "CREATE INDEX IF NOT EXISTS idx_segments_first_seen ON text_segments(first_seen)",
            "CREATE INDEX IF NOT EXISTS idx_segments_region ON text_segments(region_classification)",
            
            # Temporal consolidation indices
            "CREATE INDEX IF NOT EXISTS idx_consolidation_job_id ON temporal_consolidation(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_consolidation_video_id ON temporal_consolidation(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_consolidation_tenant_id ON temporal_consolidation(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_consolidation_text_hash ON temporal_consolidation(text_hash)",
            "CREATE INDEX IF NOT EXISTS idx_consolidation_stability ON temporal_consolidation(stability_score)",
            
            # Metrics indices
            "CREATE INDEX IF NOT EXISTS idx_metrics_job_id ON processing_metrics(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_tenant_id ON processing_metrics(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_type ON processing_metrics(metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON processing_metrics(timestamp)",
            
            # Audit log indices
            "CREATE INDEX IF NOT EXISTS idx_audit_tenant_id ON audit_log(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id)"
        ]
        
        # PostgreSQL specific indices
        if self.db_type == 'postgresql':
            indices.extend([
                # Full-text search index
                "CREATE INDEX IF NOT EXISTS idx_results_text_search ON frame_ocr_results USING GIN(text_vector)",
                
                # Trigram indices for fuzzy search
                "CREATE INDEX IF NOT EXISTS idx_results_text_trgm ON frame_ocr_results USING GIN(text gin_trgm_ops)",
                
                # JSONB indices
                "CREATE INDEX IF NOT EXISTS idx_jobs_config_gin ON frame_ocr_jobs USING GIN(config)",
                "CREATE INDEX IF NOT EXISTS idx_results_metadata_gin ON frame_ocr_results USING GIN(metadata)",
                "CREATE INDEX IF NOT EXISTS idx_segments_bounding_box_gin ON text_segments USING GIN(bounding_box)",
                
                # Composite indices for common queries
                "CREATE INDEX IF NOT EXISTS idx_results_tenant_video_time ON frame_ocr_results(tenant_id, video_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_tenant_status_created ON frame_ocr_jobs(tenant_id, status, created_at)",
                
                # Partial indices for active data
                "CREATE INDEX IF NOT EXISTS idx_jobs_active ON frame_ocr_jobs(tenant_id, created_at) WHERE status IN ('pending', 'queued', 'processing')",
                "CREATE INDEX IF NOT EXISTS idx_results_high_confidence ON frame_ocr_results(tenant_id, video_id, timestamp) WHERE confidence >= 0.8"
            ])
        else:
            # SQLite specific indices
            indices.extend([
                # Full-text search (SQLite FTS5)
                "CREATE VIRTUAL TABLE IF NOT EXISTS frame_ocr_results_fts USING fts5(text, content='frame_ocr_results', content_rowid='rowid')",
                
                # Composite indices
                "CREATE INDEX IF NOT EXISTS idx_results_tenant_video_time ON frame_ocr_results(tenant_id, video_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_jobs_tenant_status_created ON frame_ocr_jobs(tenant_id, status, created_at)"
            ])
        
        for index_sql in indices:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup"""
        conn = None
        try:
            if self.db_type == 'postgresql':
                conn = psycopg2.connect(
                    host=self.config.db_host,
                    port=self.config.db_port,
                    database=self.config.db_name,
                    user=self.config.db_user,
                    password=self.config.db_password,
                    cursor_factory=RealDictCursor
                )
            else:
                conn = sqlite3.connect(self.config.db_name)
                conn.row_factory = sqlite3.Row
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_tenant(self, tenant_name: str, settings: Dict[str, Any] = None) -> str:
        """Create a new tenant"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO tenants (tenant_name, settings)
                    VALUES (%s, %s)
                    RETURNING tenant_id
                """, (tenant_name, Json(settings or {})))
                tenant_id = cursor.fetchone()['tenant_id']
            else:
                import uuid
                tenant_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO tenants (tenant_id, tenant_name, settings)
                    VALUES (?, ?, ?)
                """, (tenant_id, tenant_name, json.dumps(settings or {})))
            
            conn.commit()
            logger.info(f"Created tenant: {tenant_id}")
            return str(tenant_id)
    
    def insert_job(self, job: FrameOCRJob) -> str:
        """Insert OCR job into database"""
        # Validate job before insertion
        errors = ModelValidator.validate_job(job)
        if errors:
            raise ValueError(f"Job validation failed: {errors}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO frame_ocr_jobs (
                        job_id, video_id, video_path, tenant_id, user_id, status,
                        config, created_at, progress, frames_processed, total_frames,
                        retry_count, max_retries, estimated_cost, data_lineage
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    job.job_id, job.video_id, job.video_path, job.tenant_id,
                    job.user_id, job.status.value, Json(job.config.to_dict()),
                    job.created_at, job.progress, job.frames_processed,
                    job.total_frames, job.retry_count, job.max_retries,
                    job.estimated_cost, Json(job.data_lineage)
                ))
            else:
                cursor.execute("""
                    INSERT INTO frame_ocr_jobs (
                        job_id, video_id, video_path, tenant_id, user_id, status,
                        config, created_at, progress, frames_processed, total_frames,
                        retry_count, max_retries, estimated_cost, data_lineage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.job_id, job.video_id, job.video_path, job.tenant_id,
                    job.user_id, job.status.value, json.dumps(job.config.to_dict()),
                    job.created_at.isoformat(), job.progress, job.frames_processed,
                    job.total_frames, job.retry_count, job.max_retries,
                    job.estimated_cost, json.dumps(job.data_lineage)
                ))
            
            conn.commit()
            logger.info(f"Inserted job: {job.job_id}")
            return job.job_id
    
    def get_job(self, job_id: str, tenant_id: str) -> Optional[FrameOCRJob]:
        """Get OCR job by ID with tenant isolation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM frame_ocr_jobs 
                WHERE job_id = ? AND tenant_id = ?
            """, (job_id, tenant_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Convert row to FrameOCRJob
            job_data = dict(row)
            if self.db_type == 'sqlite':
                job_data['config'] = json.loads(job_data['config'])
                job_data['data_lineage'] = json.loads(job_data['data_lineage'])
                job_data['created_at'] = datetime.fromisoformat(job_data['created_at'])
                if job_data['started_at']:
                    job_data['started_at'] = datetime.fromisoformat(job_data['started_at'])
                if job_data['completed_at']:
                    job_data['completed_at'] = datetime.fromisoformat(job_data['completed_at'])
            
            return FrameOCRJob.from_dict(job_data)
    
    def update_job_status(self, job_id: str, tenant_id: str, status: JobStatus, 
                         error_message: str = None) -> bool:
        """Update job status with tenant isolation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            update_fields = ["status = ?"]
            params = [status.value]
            
            if status == JobStatus.PROCESSING:
                update_fields.append("started_at = ?")
                params.append(datetime.utcnow())
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                update_fields.append("completed_at = ?")
                params.append(datetime.utcnow())
            
            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            params.extend([job_id, tenant_id])
            
            cursor.execute(f"""
                UPDATE frame_ocr_jobs 
                SET {', '.join(update_fields)}
                WHERE job_id = ? AND tenant_id = ?
            """, params)
            
            updated = cursor.rowcount > 0
            conn.commit()
            
            if updated:
                logger.info(f"Updated job {job_id} status to {status.value}")
            
            return updated
    
    def insert_result(self, result: FrameOCRResult) -> str:
        """Insert OCR result into database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO frame_ocr_results (
                        result_id, job_id, video_id, tenant_id, timestamp,
                        frame_number, text, confidence, language, bounding_boxes,
                        text_segments, ocr_engine, preprocessing_applied,
                        processing_time, created_at, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.result_id, result.job_id, result.video_id, result.tenant_id,
                    result.timestamp, result.frame_number, result.text, result.confidence,
                    result.language, Json([bbox.to_dict() for bbox in result.bounding_boxes]),
                    Json([seg.to_dict() for seg in result.text_segments]),
                    result.ocr_engine.value, result.preprocessing_applied,
                    result.processing_time, result.created_at, Json(result.metadata)
                ))
            else:
                cursor.execute("""
                    INSERT INTO frame_ocr_results (
                        result_id, job_id, video_id, tenant_id, timestamp,
                        frame_number, text, confidence, language, bounding_boxes,
                        text_segments, ocr_engine, preprocessing_applied,
                        processing_time, created_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.result_id, result.job_id, result.video_id, result.tenant_id,
                    result.timestamp, result.frame_number, result.text, result.confidence,
                    result.language, json.dumps([bbox.to_dict() for bbox in result.bounding_boxes]),
                    json.dumps([seg.to_dict() for seg in result.text_segments]),
                    result.ocr_engine.value, result.preprocessing_applied,
                    result.processing_time, result.created_at.isoformat(),
                    json.dumps(result.metadata)
                ))
            
            conn.commit()
            logger.info(f"Inserted OCR result: {result.result_id}")
            return result.result_id
    
    def search_ocr_text(self, tenant_id: str, query: str, video_id: str = None,
                       confidence_threshold: float = 0.0, limit: int = 100) -> List[Dict[str, Any]]:
        """Search OCR text with tenant isolation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            base_query = """
                SELECT result_id, job_id, video_id, timestamp, frame_number,
                       text, confidence, language, ocr_engine, created_at
                FROM frame_ocr_results
                WHERE tenant_id = ? AND confidence >= ?
            """
            params = [tenant_id, confidence_threshold]
            
            if video_id:
                base_query += " AND video_id = ?"
                params.append(video_id)
            
            if self.db_type == 'postgresql':
                base_query += " AND text_vector @@ plainto_tsquery('english', ?)"
                params.append(query)
            else:
                base_query += " AND text LIKE ?"
                params.append(f"%{query}%")
            
            base_query += " ORDER BY confidence DESC, timestamp ASC LIMIT ?"
            params.append(limit)
            
            cursor.execute(base_query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Found {len(results)} OCR search results for query: {query}")
            return results
    
    def get_temporal_consolidation(self, job_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Get temporal consolidation results for a job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM temporal_consolidation
                WHERE job_id = ? AND tenant_id = ?
                ORDER BY stability_score DESC, occurrence_count DESC
            """, (job_id, tenant_id))
            
            results = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(results)} temporal consolidation entries")
            return results
    
    def log_audit_event(self, tenant_id: str, user_id: str, action: str,
                       resource_type: str, resource_id: str, details: Dict[str, Any] = None):
        """Log audit event for compliance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO audit_log (tenant_id, user_id, action, resource_type, resource_id, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (tenant_id, user_id, action, resource_type, resource_id, Json(details or {})))
            else:
                import uuid
                audit_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO audit_log (audit_id, tenant_id, user_id, action, resource_type, resource_id, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (audit_id, tenant_id, user_id, action, resource_type, resource_id, json.dumps(details or {})))
            
            conn.commit()
    
    def cleanup_old_data(self, retention_days: int = 90):
        """Clean up old data based on retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean up old completed jobs and their results
            cursor.execute("""
                DELETE FROM frame_ocr_results 
                WHERE job_id IN (
                    SELECT job_id FROM frame_ocr_jobs 
                    WHERE status = 'completed' AND completed_at < ?
                )
            """, (cutoff_date,))
            
            cursor.execute("""
                DELETE FROM frame_ocr_jobs 
                WHERE status = 'completed' AND completed_at < ?
            """, (cutoff_date,))
            
            # Clean up old metrics
            cursor.execute("""
                DELETE FROM processing_metrics 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {retention_days} days")


if __name__ == "__main__":
    # Example usage and testing
    print("Frame OCR Database - Example Usage")
    
    # Initialize database
    config = DatabaseConfig()
    db = FrameOCRDatabase(config)
    
    # Create test tenant
    tenant_id = db.create_tenant("Test Tenant", {"max_jobs": 100})
    print(f"Created tenant: {tenant_id}")
    
    # Test job insertion and retrieval
    from frame_ocr_models import FrameOCRJob, OCRJobConfig
    
    job = FrameOCRJob(
        video_id="test_video_123",
        video_path="/path/to/test.mp4",
        tenant_id=tenant_id,
        user_id="test_user"
    )
    
    job_id = db.insert_job(job)
    retrieved_job = db.get_job(job_id, tenant_id)
    
    print(f"Job insertion test: {job_id == retrieved_job.job_id}")
    
    # Test status update
    success = db.update_job_status(job_id, tenant_id, JobStatus.PROCESSING)
    print(f"Status update test: {success}")
    
    print("Database setup and testing completed successfully")