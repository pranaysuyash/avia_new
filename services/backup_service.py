#!/usr/bin/env python3
"""
Backup Service
Handles system backups and restoration
"""

import logging
import os
import json
import shutil
import tarfile
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import boto3
from pathlib import Path

from database.connection import DATABASE_URL
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

class BackupService:
    """Service for creating and managing system backups"""
    
    def __init__(self):
        self.backup_dir = os.getenv('BACKUP_DIR', '/tmp/backups')
        self.s3_bucket = os.getenv('BACKUP_S3_BUCKET')
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        
        # Create backup directory
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if self.s3_bucket and os.getenv('AWS_ACCESS_KEY_ID'):
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
    
    async def create_backup(
        self,
        backup_type: str = "full",
        include_files: bool = True,
        compress: bool = True,
        user_id: Optional[int] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create system backup"""
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backup_dir, backup_id)
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Log backup start
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_CREATE,
                action=f"Create {backup_type} backup",
                user_id=user_id,
                username=username,
                details={'backup_id': backup_id, 'type': backup_type}
            )
            
            # Backup components
            components = []
            
            # 1. Database backup
            db_backup_file = await self._backup_database(backup_path)
            if db_backup_file:
                components.append('database')
            
            # 2. Configuration backup
            config_backup_file = await self._backup_configuration(backup_path)
            if config_backup_file:
                components.append('configuration')
            
            # 3. File storage backup (if requested)
            if include_files:
                files_backup_file = await self._backup_files(backup_path, backup_type)
                if files_backup_file:
                    components.append('files')
            
            # 4. Audit logs backup
            audit_backup_file = await self._backup_audit_logs(backup_path)
            if audit_backup_file:
                components.append('audit_logs')
            
            # Create metadata
            metadata = {
                'backup_id': backup_id,
                'created_at': datetime.utcnow().isoformat(),
                'type': backup_type,
                'components': components,
                'created_by': username,
                'version': '1.0'
            }
            
            with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Compress if requested
            final_path = backup_path
            if compress:
                final_path = await self._compress_backup(backup_path)
                shutil.rmtree(backup_path)  # Remove uncompressed version
            
            # Upload to S3 if configured
            s3_location = None
            if self.s3_client:
                s3_location = await self._upload_to_s3(final_path, backup_id)
            
            # Calculate size
            if os.path.isfile(final_path):
                size = os.path.getsize(final_path)
            else:
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(final_path)
                    for filename in filenames
                )
            
            # Log success
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_CREATE,
                action=f"Backup created successfully",
                result="success",
                user_id=user_id,
                username=username,
                details={
                    'backup_id': backup_id,
                    'size_bytes': size,
                    'components': components,
                    's3_location': s3_location
                }
            )
            
            return {
                'backup_id': backup_id,
                'status': 'success',
                'size': size,
                'components': components,
                'location': final_path,
                's3_location': s3_location,
                'created_at': metadata['created_at']
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            
            # Log failure
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_CREATE,
                action=f"Backup failed",
                result="failure",
                user_id=user_id,
                username=username,
                error_message=str(e),
                details={'backup_id': backup_id}
            )
            
            # Cleanup
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            
            return {
                'backup_id': backup_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def _backup_database(self, backup_path: str) -> Optional[str]:
        """Backup database"""
        try:
            db_backup_file = os.path.join(backup_path, 'database.sql')
            
            # Use pg_dump for PostgreSQL
            if 'postgresql' in DATABASE_URL:
                import subprocess
                
                # Parse connection URL
                from urllib.parse import urlparse
                parsed = urlparse(DATABASE_URL)
                
                env = os.environ.copy()
                env['PGPASSWORD'] = parsed.password
                
                cmd = [
                    'pg_dump',
                    '-h', parsed.hostname,
                    '-p', str(parsed.port or 5432),
                    '-U', parsed.username,
                    '-d', parsed.path[1:],  # Remove leading /
                    '-f', db_backup_file,
                    '--no-owner',
                    '--no-privileges'
                ]
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Database backup failed: {result.stderr}")
                    return None
                
                return db_backup_file
            
            else:
                # For other databases, use SQL dump
                engine = create_engine(DATABASE_URL)
                
                with open(db_backup_file, 'w') as f:
                    # Get all tables
                    tables = engine.table_names()
                    
                    for table in tables:
                        # Export table structure
                        f.write(f"-- Table: {table}\n")
                        
                        # Export data
                        result = engine.execute(f"SELECT * FROM {table}")
                        rows = result.fetchall()
                        
                        if rows:
                            columns = result.keys()
                            f.write(f"INSERT INTO {table} ({','.join(columns)}) VALUES\n")
                            
                            for i, row in enumerate(rows):
                                values = [
                                    f"'{str(v).replace('\"', '\"\"')}'" if v is not None else 'NULL'
                                    for v in row
                                ]
                                f.write(f"({','.join(values)})")
                                f.write(',\n' if i < len(rows) - 1 else ';\n\n')
                
                return db_backup_file
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None
    
    async def _backup_configuration(self, backup_path: str) -> Optional[str]:
        """Backup configuration files"""
        try:
            config_dir = os.path.join(backup_path, 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            # Backup environment variables (sanitized)
            env_backup = {}
            sensitive_keys = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']
            
            for key, value in os.environ.items():
                if key.startswith(('APP_', 'API_', 'FEATURE_')):
                    # Mask sensitive values
                    if any(sensitive in key for sensitive in sensitive_keys):
                        env_backup[key] = '***MASKED***'
                    else:
                        env_backup[key] = value
            
            with open(os.path.join(config_dir, 'environment.json'), 'w') as f:
                json.dump(env_backup, f, indent=2)
            
            # Backup other config files if they exist
            config_files = [
                'config.yaml',
                'config.json',
                '.env.example'
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, config_dir)
            
            return config_dir
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return None
    
    async def _backup_files(self, backup_path: str, backup_type: str) -> Optional[str]:
        """Backup file storage"""
        try:
            files_dir = os.path.join(backup_path, 'files')
            os.makedirs(files_dir, exist_ok=True)
            
            storage_path = os.getenv('STORAGE_PATH', '/tmp/storage')
            
            if backup_type == "full":
                # Full backup - copy all files
                if os.path.exists(storage_path):
                    shutil.copytree(storage_path, files_dir, dirs_exist_ok=True)
            
            else:
                # Incremental backup - only recent files
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                for root, dirs, files in os.walk(storage_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Check modification time
                        if os.path.getmtime(file_path) > cutoff_date.timestamp():
                            # Preserve directory structure
                            rel_path = os.path.relpath(file_path, storage_path)
                            dest_path = os.path.join(files_dir, rel_path)
                            
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            shutil.copy2(file_path, dest_path)
            
            return files_dir
            
        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            return None
    
    async def _backup_audit_logs(self, backup_path: str) -> Optional[str]:
        """Backup audit logs"""
        try:
            # Export audit logs
            from services.audit_logging_service import audit_service
            
            logs = audit_service.query_logs(limit=100000)
            
            audit_file = os.path.join(backup_path, 'audit_logs.json')
            with open(audit_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            return audit_file
            
        except Exception as e:
            logger.error(f"Audit logs backup failed: {e}")
            return None
    
    async def _compress_backup(self, backup_path: str) -> str:
        """Compress backup directory"""
        compressed_path = f"{backup_path}.tar.gz"
        
        with tarfile.open(compressed_path, 'w:gz') as tar:
            tar.add(backup_path, arcname=os.path.basename(backup_path))
        
        return compressed_path
    
    async def _upload_to_s3(self, backup_path: str, backup_id: str) -> Optional[str]:
        """Upload backup to S3"""
        if not self.s3_client:
            return None
        
        try:
            # Determine S3 key
            if backup_path.endswith('.tar.gz'):
                s3_key = f"backups/{backup_id}.tar.gz"
            else:
                s3_key = f"backups/{backup_id}/"
            
            # Upload file or directory
            if os.path.isfile(backup_path):
                self.s3_client.upload_file(backup_path, self.s3_bucket, s3_key)
            else:
                # Upload directory
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, backup_path)
                        self.s3_client.upload_file(
                            file_path,
                            self.s3_bucket,
                            f"{s3_key}{rel_path}"
                        )
            
            return f"s3://{self.s3_bucket}/{s3_key}"
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return None
    
    async def restore_backup(
        self,
        backup_id: str,
        components: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restore from backup"""
        try:
            # Log restore start
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_RESTORE,
                action=f"Restore from backup",
                user_id=user_id,
                username=username,
                details={'backup_id': backup_id, 'components': components}
            )
            
            # Find backup
            backup_path = os.path.join(self.backup_dir, backup_id)
            
            # Check if compressed
            if not os.path.exists(backup_path) and os.path.exists(f"{backup_path}.tar.gz"):
                # Extract compressed backup
                with tempfile.TemporaryDirectory() as temp_dir:
                    with tarfile.open(f"{backup_path}.tar.gz", 'r:gz') as tar:
                        tar.extractall(temp_dir)
                    
                    backup_path = os.path.join(temp_dir, backup_id)
                    return await self._perform_restore(
                        backup_path, components, user_id, username
                    )
            
            else:
                return await self._perform_restore(
                    backup_path, components, user_id, username
                )
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            
            # Log failure
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_RESTORE,
                action=f"Restore failed",
                result="failure",
                user_id=user_id,
                username=username,
                error_message=str(e),
                details={'backup_id': backup_id}
            )
            
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _perform_restore(
        self,
        backup_path: str,
        components: Optional[List[str]],
        user_id: Optional[int],
        username: Optional[str]
    ) -> Dict[str, Any]:
        """Perform actual restore"""
        # Read metadata
        metadata_path = os.path.join(backup_path, 'metadata.json')
        if not os.path.exists(metadata_path):
            raise ValueError("Invalid backup: metadata.json not found")
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Determine components to restore
        if not components:
            components = metadata['components']
        
        restored = []
        
        # Restore each component
        if 'database' in components and 'database' in metadata['components']:
            if await self._restore_database(backup_path):
                restored.append('database')
        
        if 'configuration' in components and 'configuration' in metadata['components']:
            if await self._restore_configuration(backup_path):
                restored.append('configuration')
        
        if 'files' in components and 'files' in metadata['components']:
            if await self._restore_files(backup_path):
                restored.append('files')
        
        # Log success
        audit_service.log_event(
            event_type=AuditEventType.BACKUP_RESTORE,
            action=f"Restore completed",
            result="success",
            user_id=user_id,
            username=username,
            details={
                'backup_id': metadata['backup_id'],
                'restored_components': restored
            }
        )
        
        return {
            'status': 'success',
            'restored_components': restored,
            'backup_info': metadata
        }
    
    async def _restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            db_backup_file = os.path.join(backup_path, 'database.sql')
            
            if not os.path.exists(db_backup_file):
                logger.error("Database backup file not found")
                return False
            
            # Use psql for PostgreSQL
            if 'postgresql' in DATABASE_URL:
                import subprocess
                from urllib.parse import urlparse
                
                parsed = urlparse(DATABASE_URL)
                env = os.environ.copy()
                env['PGPASSWORD'] = parsed.password
                
                # Drop and recreate database (be careful!)
                # This is for demo purposes - production should be more careful
                cmd = [
                    'psql',
                    '-h', parsed.hostname,
                    '-p', str(parsed.port or 5432),
                    '-U', parsed.username,
                    '-d', parsed.path[1:],
                    '-f', db_backup_file
                ]
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Database restore failed: {result.stderr}")
                    return False
                
                logger.info("Database restored successfully")
                return True
            
            else:
                # For other databases, use SQLAlchemy
                engine = create_engine(DATABASE_URL)
                
                with open(db_backup_file, 'r') as f:
                    sql_commands = f.read()
                
                # Execute SQL commands
                with engine.begin() as conn:
                    for command in sql_commands.split(';'):
                        if command.strip():
                            conn.execute(text(command))
                
                logger.info("Database restored successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    async def _restore_configuration(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        try:
            config_dir = os.path.join(backup_path, 'config')
            
            if not os.path.exists(config_dir):
                logger.error("Configuration backup not found")
                return False
            
            # Restore configuration files
            config_files = [
                'config.yaml',
                'config.json',
                '.env.example'
            ]
            
            restored_count = 0
            for config_file in config_files:
                backup_file = os.path.join(config_dir, config_file)
                if os.path.exists(backup_file):
                    # Create backup of current config
                    if os.path.exists(config_file):
                        shutil.copy2(config_file, f"{config_file}.backup")
                    
                    # Restore from backup
                    shutil.copy2(backup_file, config_file)
                    restored_count += 1
                    logger.info(f"Restored {config_file}")
            
            # Log environment variables (for reference only)
            env_file = os.path.join(config_dir, 'environment.json')
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_data = json.load(f)
                logger.info(f"Environment variables reference loaded ({len(env_data)} variables)")
            
            logger.info(f"Configuration restored: {restored_count} files")
            return restored_count > 0
            
        except Exception as e:
            logger.error(f"Configuration restore failed: {e}")
            return False
    
    async def _restore_files(self, backup_path: str) -> bool:
        """Restore files from backup"""
        try:
            files_dir = os.path.join(backup_path, 'files')
            
            if not os.path.exists(files_dir):
                logger.info("No files backup found")
                return True  # Not an error if no files to restore
            
            storage_path = os.getenv('STORAGE_PATH', '/tmp/storage')
            
            # Create backup of current files
            if os.path.exists(storage_path):
                backup_storage = f"{storage_path}.backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(storage_path, backup_storage)
                logger.info(f"Current files backed up to {backup_storage}")
            
            # Restore files
            shutil.copytree(files_dir, storage_path, dirs_exist_ok=True)
            
            # Count restored files
            file_count = sum(
                len(files) for _, _, files in os.walk(storage_path)
            )
            
            logger.info(f"Files restored: {file_count} files")
            return True
            
        except Exception as e:
            logger.error(f"Files restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        # List local backups
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            
            # Handle compressed backups
            metadata = None
            if item.endswith('.tar.gz'):
                # Try to extract metadata
                try:
                    with tarfile.open(item_path, 'r:gz') as tar:
                        metadata_member = tar.getmember(
                            f"{item.replace('.tar.gz', '')}/metadata.json"
                        )
                        metadata_file = tar.extractfile(metadata_member)
                        metadata = json.load(metadata_file)
                except Exception:
                    pass
                
                size = os.path.getsize(item_path)
                
            elif os.path.isdir(item_path):
                # Read metadata
                metadata_path = os.path.join(item_path, 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                # Calculate size
                size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, _, filenames in os.walk(item_path)
                    for filename in filenames
                )
            
            else:
                continue
            
            if metadata:
                backups.append({
                    'backup_id': metadata['backup_id'],
                    'created_at': metadata['created_at'],
                    'type': metadata['type'],
                    'components': metadata['components'],
                    'size': size,
                    'location': 'local',
                    'created_by': metadata.get('created_by')
                })
        
        # Sort by creation date
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        removed = 0
        
        for backup in self.list_backups():
            backup_date = datetime.fromisoformat(backup['created_at'])
            
            if backup_date < cutoff_date:
                # Remove backup
                backup_path = os.path.join(self.backup_dir, backup['backup_id'])
                
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                    removed += 1
                
                if os.path.exists(f"{backup_path}.tar.gz"):
                    os.remove(f"{backup_path}.tar.gz")
                    removed += 1
        
        logger.info(f"Cleaned up {removed} old backups")
        return removed

# Global instance
backup_service = BackupService()

def get_backup_service() -> BackupService:
    """Get backup service instance"""
    return backup_service