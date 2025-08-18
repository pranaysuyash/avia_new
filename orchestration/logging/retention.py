"""Log retention and rotation policies."""

import asyncio
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class LogRetentionManager:
    """Manages log file retention and rotation policies."""
    
    def __init__(self, log_dir: Path, config: Dict[str, Any]):
        self.log_dir = Path(log_dir)
        self.config = config
        self.retention_days = config.get('retention_days', 30)
        self.max_file_size = config.get('max_file_size_mb', 100) * 1024 * 1024  # Convert to bytes
        self.compress_after_days = config.get('compress_after_days', 7)
        self.rotation_schedule = config.get('rotation_schedule', 'daily')  # daily, weekly, monthly
        
    async def apply_retention_policies(self) -> Dict[str, Any]:
        """Apply all retention policies."""
        results = {
            'rotated_files': [],
            'compressed_files': [],
            'deleted_files': [],
            'errors': []
        }
        
        try:
            # Rotate large files
            rotated = await self._rotate_large_files()
            results['rotated_files'].extend(rotated)
            
            # Compress old files
            compressed = await self._compress_old_files()
            results['compressed_files'].extend(compressed)
            
            # Delete expired files
            deleted = await self._delete_expired_files()
            results['deleted_files'].extend(deleted)
            
        except Exception as e:
            error_msg = f"Error applying retention policies: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            
        return results
        
    async def _rotate_large_files(self) -> List[str]:
        """Rotate files that exceed size limit."""
        rotated_files = []
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                if log_file.stat().st_size > self.max_file_size:
                    rotated_file = await self._rotate_file(log_file)
                    rotated_files.append(str(rotated_file))
                    logger.info(f"Rotated large file: {log_file} -> {rotated_file}")
                    
            except Exception as e:
                logger.error(f"Error rotating file {log_file}: {e}")
                
        return rotated_files
        
    async def _rotate_file(self, log_file: Path) -> Path:
        """Rotate a single log file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_name = f"{log_file.stem}_{timestamp}.log"
        rotated_path = log_file.parent / rotated_name
        
        # Move current file to rotated name
        shutil.move(str(log_file), str(rotated_path))
        
        # Create new empty log file
        log_file.touch()
        
        return rotated_path
        
    async def _compress_old_files(self) -> List[str]:
        """Compress files older than compress_after_days."""
        compressed_files = []
        cutoff_date = datetime.now() - timedelta(days=self.compress_after_days)
        
        # Find log files to compress (not already compressed)
        for log_file in self.log_dir.glob("*.log"):
            try:
                # Skip current active log files
                if self._is_active_log_file(log_file):
                    continue
                    
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    compressed_file = await self._compress_file(log_file)
                    compressed_files.append(str(compressed_file))
                    logger.info(f"Compressed old file: {log_file} -> {compressed_file}")
                    
            except Exception as e:
                logger.error(f"Error compressing file {log_file}: {e}")
                
        return compressed_files
        
    async def _compress_file(self, log_file: Path) -> Path:
        """Compress a single log file."""
        compressed_path = log_file.with_suffix('.log.gz')
        
        with open(log_file, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
        # Remove original file after successful compression
        log_file.unlink()
        
        return compressed_path
        
    async def _delete_expired_files(self) -> List[str]:
        """Delete files older than retention period."""
        deleted_files = []
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # Delete old log files and compressed files
        for pattern in ["*.log", "*.log.gz"]:
            for log_file in self.log_dir.glob(pattern):
                try:
                    # Skip current active log files
                    if pattern == "*.log" and self._is_active_log_file(log_file):
                        continue
                        
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        log_file.unlink()
                        deleted_files.append(str(log_file))
                        logger.info(f"Deleted expired file: {log_file}")
                        
                except Exception as e:
                    logger.error(f"Error deleting file {log_file}: {e}")
                    
        return deleted_files
        
    def _is_active_log_file(self, log_file: Path) -> bool:
        """Check if log file is currently active (being written to)."""
        # Consider files with standard names as active
        active_names = [
            'orchestration.log',
            'errors.log',
            'aggregated.jsonl',
            'access.log',
            'debug.log'
        ]
        return log_file.name in active_names
        
    async def get_retention_stats(self) -> Dict[str, Any]:
        """Get statistics about log retention."""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_type': {
                'active_logs': {'count': 0, 'size': 0},
                'rotated_logs': {'count': 0, 'size': 0},
                'compressed_logs': {'count': 0, 'size': 0}
            },
            'oldest_file': None,
            'newest_file': None
        }
        
        oldest_time = None
        newest_time = None
        
        for pattern in ["*.log", "*.log.gz"]:
            for log_file in self.log_dir.glob(pattern):
                try:
                    file_stat = log_file.stat()
                    file_size = file_stat.st_size
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    stats['total_files'] += 1
                    stats['total_size'] += file_size
                    
                    # Categorize file
                    if log_file.suffix == '.gz':
                        category = 'compressed_logs'
                    elif self._is_active_log_file(log_file):
                        category = 'active_logs'
                    else:
                        category = 'rotated_logs'
                        
                    stats['by_type'][category]['count'] += 1
                    stats['by_type'][category]['size'] += file_size
                    
                    # Track oldest and newest files
                    if oldest_time is None or file_mtime < oldest_time:
                        oldest_time = file_mtime
                        stats['oldest_file'] = {
                            'name': log_file.name,
                            'modified': file_mtime.isoformat(),
                            'size': file_size
                        }
                        
                    if newest_time is None or file_mtime > newest_time:
                        newest_time = file_mtime
                        stats['newest_file'] = {
                            'name': log_file.name,
                            'modified': file_mtime.isoformat(),
                            'size': file_size
                        }
                        
                except Exception as e:
                    logger.error(f"Error getting stats for file {log_file}: {e}")
                    
        return stats
        
    async def schedule_retention_job(self, interval_hours: int = 24) -> None:
        """Schedule periodic retention policy application."""
        logger.info(f"Starting log retention scheduler (interval: {interval_hours} hours)")
        
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
                logger.info("Running scheduled log retention policies")
                results = await self.apply_retention_policies()
                
                # Log summary of retention actions
                summary = (
                    f"Retention completed - "
                    f"Rotated: {len(results['rotated_files'])}, "
                    f"Compressed: {len(results['compressed_files'])}, "
                    f"Deleted: {len(results['deleted_files'])}, "
                    f"Errors: {len(results['errors'])}"
                )
                logger.info(summary)
                
                if results['errors']:
                    for error in results['errors']:
                        logger.error(f"Retention error: {error}")
                        
            except asyncio.CancelledError:
                logger.info("Log retention scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in retention scheduler: {e}")
                # Continue running despite errors