"""
Automated Backup Scheduler
Handles scheduled backups with cron-like functionality and comprehensive data protection
"""

import asyncio
import logging
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import schedule
import threading
import time

from services.backup_service import backup_service
from api.cache.redis_cache import redis_cache
from api.database import get_db, User, Transcript
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)


class AutomatedBackupScheduler:
    """Manages automated backup scheduling and monitoring"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.backup_history = []
        self.max_history_size = 100
        
        # Configuration
        self.daily_hour = int(os.getenv("BACKUP_DAILY_HOUR", "2"))  # 2 AM
        self.weekly_day = os.getenv("BACKUP_WEEKLY_DAY", "sunday")  # Sunday
        self.monthly_day = int(os.getenv("BACKUP_MONTHLY_DAY", "1"))  # 1st of month
        
        # Notification settings
        self.notify_on_success = os.getenv("BACKUP_NOTIFY_SUCCESS", "false").lower() == "true"
        self.notify_on_failure = os.getenv("BACKUP_NOTIFY_FAILURE", "true").lower() == "true"
        self.notification_webhook = os.getenv("BACKUP_NOTIFICATION_WEBHOOK")
        
        # Setup schedules
        self._setup_schedules()
    
    def _setup_schedules(self):
        """Setup backup schedules"""
        # Daily backup
        schedule.every().day.at(f"{self.daily_hour:02d}:00").do(
            self._run_scheduled_backup, "daily"
        )
        
        # Weekly backup
        getattr(schedule.every(), self.weekly_day.lower()).at(f"{self.daily_hour:02d}:15").do(
            self._run_scheduled_backup, "weekly"
        )
        
        # Monthly backup
        schedule.every().month.at(f"{self.daily_hour:02d}:30").do(
            self._run_scheduled_backup, "monthly"
        )
        
        # Cleanup job - runs daily at 3 AM
        schedule.every().day.at("03:00").do(self._run_cleanup)
        
        logger.info(f"Backup schedules configured: Daily at {self.daily_hour:02d}:00, Weekly on {self.weekly_day}, Monthly on day {self.monthly_day}")
    
    def start(self):
        """Start the backup scheduler"""
        if self.running:
            logger.warning("Backup scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Backup scheduler started")
        
        # Log scheduler start
        audit_service.log_event(
            event_type=AuditEventType.SYSTEM_START,
            action="Backup scheduler started",
            details={
                "daily_hour": self.daily_hour,
                "weekly_day": self.weekly_day,
                "monthly_day": self.monthly_day
            }
        )
    
    def stop(self):
        """Stop the backup scheduler"""
        if not self.running:
            logger.warning("Backup scheduler not running")
            return
        
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Backup scheduler stopped")
        
        # Log scheduler stop
        audit_service.log_event(
            event_type=AuditEventType.SYSTEM_STOP,
            action="Backup scheduler stopped"
        )
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Backup scheduler loop started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _run_scheduled_backup(self, backup_type: str):
        """Run a scheduled backup"""
        logger.info(f"Starting scheduled {backup_type} backup")
        
        try:
            # Run backup asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            backup_result = loop.run_until_complete(
                self.create_comprehensive_backup(backup_type)
            )
            
            loop.close()
            
            # Add to history
            self._add_to_history(backup_result)
            
            # Send notification on success
            if self.notify_on_success:
                asyncio.create_task(self._send_notification(backup_result, success=True))
            
            logger.info(f"Scheduled {backup_type} backup completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled {backup_type} backup failed: {e}")
            
            error_result = {
                "backup_id": f"failed_{backup_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "backup_type": backup_type,
                "status": "failed",
                "error": str(e),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self._add_to_history(error_result)
            
            # Send notification on failure
            if self.notify_on_failure:
                asyncio.create_task(self._send_notification(error_result, success=False))
    
    def _run_cleanup(self):
        """Run cleanup of old backups"""
        try:
            logger.info("Starting backup cleanup")
            
            # Cleanup old local backups
            removed_count = backup_service.cleanup_old_backups()
            
            # Log cleanup
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_CLEANUP,
                action="Backup cleanup completed",
                details={"removed_backups": removed_count}
            )
            
            logger.info(f"Backup cleanup completed: {removed_count} old backups removed")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    async def create_comprehensive_backup(self, backup_type: str = "manual") -> Dict[str, Any]:
        """Create a comprehensive backup including all system data"""
        start_time = datetime.utcnow()
        backup_id = f"{backup_type}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting comprehensive backup: {backup_id}")
        
        backup_result = {
            "backup_id": backup_id,
            "backup_type": backup_type,
            "start_time": start_time.isoformat(),
            "status": "in_progress",
            "components": {},
            "metrics": {}
        }
        
        try:
            # 1. Database backup using existing service
            db_backup = await backup_service.create_backup(
                backup_type=backup_type,
                include_files=True,
                compress=True,
                user_id=None,
                username="system"
            )
            
            backup_result["components"]["database"] = db_backup
            
            # 2. Enhanced Redis backup
            redis_backup = await self._backup_redis_enhanced(backup_id)
            if redis_backup:
                backup_result["components"]["redis"] = redis_backup
            
            # 3. User data backup
            user_data_backup = await self._backup_user_data(backup_id)
            if user_data_backup:
                backup_result["components"]["user_data"] = user_data_backup
            
            # 4. System metrics backup
            metrics_backup = await self._backup_system_metrics(backup_id)
            if metrics_backup:
                backup_result["components"]["system_metrics"] = metrics_backup
            
            # 5. Cache statistics backup
            cache_stats = await self._backup_cache_statistics(backup_id)
            if cache_stats:
                backup_result["components"]["cache_stats"] = cache_stats
            
            # Calculate backup metrics
            end_time = datetime.utcnow()
            backup_result["end_time"] = end_time.isoformat()
            backup_result["duration"] = (end_time - start_time).total_seconds()
            backup_result["status"] = "completed"
            
            # Calculate total size
            total_size = sum(
                comp.get("size", 0) for comp in backup_result["components"].values()
                if isinstance(comp, dict)
            )
            backup_result["total_size"] = total_size
            
            # Generate backup checksum
            backup_result["checksum"] = await self._generate_backup_checksum(backup_result)
            
            logger.info(f"Comprehensive backup completed: {backup_id}")
            
            # Log successful backup
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_CREATE,
                action=f"Comprehensive {backup_type} backup completed",
                result="success",
                details={
                    "backup_id": backup_id,
                    "duration": backup_result["duration"],
                    "total_size": total_size,
                    "components": list(backup_result["components"].keys())
                }
            )
            
            return backup_result
            
        except Exception as e:
            backup_result["status"] = "failed"
            backup_result["error"] = str(e)
            backup_result["end_time"] = datetime.utcnow().isoformat()
            
            logger.error(f"Comprehensive backup failed: {backup_id} - {e}")
            
            # Log failed backup
            audit_service.log_event(
                event_type=AuditEventType.BACKUP_CREATE,
                action=f"Comprehensive {backup_type} backup failed",
                result="failure",
                error_message=str(e),
                details={"backup_id": backup_id}
            )
            
            raise
    
    async def _backup_redis_enhanced(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Enhanced Redis backup with additional metadata"""
        if not redis_cache.is_connected():
            logger.warning("Redis not connected, skipping enhanced backup")
            return None
        
        try:
            # Get Redis info
            redis_info = redis_cache.client.info()
            
            # Export all keys with metadata
            all_data = {
                "backup_id": backup_id,
                "timestamp": datetime.utcnow().isoformat(),
                "redis_info": {
                    "version": redis_info.get("redis_version"),
                    "used_memory": redis_info.get("used_memory"),
                    "total_keys": redis_cache.client.dbsize(),
                    "uptime_seconds": redis_info.get("uptime_in_seconds")
                },
                "keys": []
            }
            
            # Export keys by pattern
            patterns = {
                "transcription": "trans:*",
                "user": "user:*",
                "cache": "cache:*",
                "session": "sess:*"
            }
            
            for pattern_name, pattern in patterns.items():
                keys_data = []
                for key in redis_cache.client.scan_iter(match=pattern):
                    key_str = key.decode() if isinstance(key, bytes) else key
                    key_type = redis_cache.client.type(key).decode()
                    ttl = redis_cache.client.ttl(key)
                    
                    key_info = {
                        "key": key_str,
                        "type": key_type,
                        "ttl": ttl,
                        "size": redis_cache.client.memory_usage(key) if hasattr(redis_cache.client, 'memory_usage') else None
                    }
                    
                    try:
                        if key_type == "string":
                            key_info["value"] = redis_cache.get(key)
                        elif key_type == "hash":
                            key_info["value"] = redis_cache.hgetall(key)
                        # Add other types as needed
                        
                        keys_data.append(key_info)
                    except Exception as e:
                        logger.warning(f"Failed to backup Redis key {key_str}: {e}")
                
                all_data["keys"].extend(keys_data)
            
            # Save to backup location
            backup_dir = Path(os.getenv('BACKUP_DIR', '/tmp/backups'))
            redis_backup_file = backup_dir / f"redis_enhanced_{backup_id}.json"
            
            with open(redis_backup_file, 'w') as f:
                json.dump(all_data, f, indent=2, default=str)
            
            file_size = redis_backup_file.stat().st_size
            
            logger.info(f"Enhanced Redis backup completed: {len(all_data['keys'])} keys, {file_size} bytes")
            
            return {
                "file_path": str(redis_backup_file),
                "keys_count": len(all_data['keys']),
                "size": file_size,
                "redis_version": all_data["redis_info"]["version"],
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Enhanced Redis backup failed: {e}")
            return None
    
    async def _backup_user_data(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Backup user-specific data with privacy considerations"""
        try:
            backup_dir = Path(os.getenv('BACKUP_DIR', '/tmp/backups'))
            user_data_file = backup_dir / f"user_data_{backup_id}.json"
            
            # Get user statistics (no PII)
            db = next(get_db())
            try:
                users_stats = []
                users = db.query(User).all()
                
                for user in users:
                    # Only backup non-sensitive aggregated data
                    user_transcripts = db.query(Transcript).filter(
                        Transcript.user_id == user.id
                    ).all()
                    
                    user_stat = {
                        "user_id": user.id,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "is_active": user.is_active,
                        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                        "transcript_count": len(user_transcripts),
                        "total_duration": sum(t.duration or 0 for t in user_transcripts),
                        "languages_used": list(set(t.language for t in user_transcripts if t.language)),
                        "last_activity": max(
                            [t.created_at for t in user_transcripts if t.created_at],
                            default=user.created_at
                        ).isoformat() if user_transcripts else None
                    }
                    
                    users_stats.append(user_stat)
                
                user_data = {
                    "backup_id": backup_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_users": len(users_stats),
                    "active_users": sum(1 for u in users_stats if u["is_active"]),
                    "users": users_stats
                }
                
                with open(user_data_file, 'w') as f:
                    json.dump(user_data, f, indent=2, default=str)
                
                file_size = user_data_file.stat().st_size
                
                logger.info(f"User data backup completed: {len(users_stats)} users, {file_size} bytes")
                
                return {
                    "file_path": str(user_data_file),
                    "users_count": len(users_stats),
                    "size": file_size,
                    "status": "completed"
                }
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"User data backup failed: {e}")
            return None
    
    async def _backup_system_metrics(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Backup system performance metrics"""
        try:
            import psutil
            
            backup_dir = Path(os.getenv('BACKUP_DIR', '/tmp/backups'))
            metrics_file = backup_dir / f"system_metrics_{backup_id}.json"
            
            # Collect system metrics
            metrics = {
                "backup_id": backup_id,
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": dict(psutil.virtual_memory()._asdict()),
                    "disk": dict(psutil.disk_usage('/')._asdict()),
                    "load_average": os.getloadavg(),
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
                },
                "process": {
                    "pid": os.getpid(),
                    "memory_info": dict(psutil.Process().memory_info()._asdict()),
                    "cpu_percent": psutil.Process().cpu_percent(),
                    "create_time": datetime.fromtimestamp(psutil.Process().create_time()).isoformat(),
                    "num_threads": psutil.Process().num_threads()
                }
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            
            file_size = metrics_file.stat().st_size
            
            logger.info(f"System metrics backup completed: {file_size} bytes")
            
            return {
                "file_path": str(metrics_file),
                "size": file_size,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"System metrics backup failed: {e}")
            return None
    
    async def _backup_cache_statistics(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Backup cache performance statistics"""
        try:
            from services.transcription_service_cached import CachedTranscriptionService
            
            backup_dir = Path(os.getenv('BACKUP_DIR', '/tmp/backups'))
            cache_stats_file = backup_dir / f"cache_stats_{backup_id}.json"
            
            # Get cache statistics
            db = next(get_db())
            try:
                service = CachedTranscriptionService(db)
                cache_stats = service.get_cache_stats()
                
                # Add timestamp and backup info
                cache_data = {
                    "backup_id": backup_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "cache_statistics": cache_stats
                }
                
                with open(cache_stats_file, 'w') as f:
                    json.dump(cache_data, f, indent=2, default=str)
                
                file_size = cache_stats_file.stat().st_size
                
                logger.info(f"Cache statistics backup completed: {file_size} bytes")
                
                return {
                    "file_path": str(cache_stats_file),
                    "size": file_size,
                    "status": "completed"
                }
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Cache statistics backup failed: {e}")
            return None
    
    async def _generate_backup_checksum(self, backup_data: Dict[str, Any]) -> str:
        """Generate a checksum for backup integrity verification"""
        # Create a deterministic string from backup data
        backup_string = json.dumps(backup_data, sort_keys=True, default=str)
        return hashlib.sha256(backup_string.encode()).hexdigest()
    
    async def _send_notification(self, backup_result: Dict[str, Any], success: bool):
        """Send backup notification"""
        try:
            if not self.notification_webhook:
                return
            
            import aiohttp
            
            notification_data = {
                "backup_id": backup_result["backup_id"],
                "backup_type": backup_result["backup_type"],
                "status": "success" if success else "failed",
                "timestamp": backup_result.get("end_time", datetime.utcnow().isoformat()),
                "duration": backup_result.get("duration"),
                "total_size": backup_result.get("total_size"),
                "components": list(backup_result.get("components", {}).keys()),
                "error": backup_result.get("error")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.notification_webhook,
                    json=notification_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        logger.info(f"Backup notification sent successfully")
                    else:
                        logger.warning(f"Backup notification failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Failed to send backup notification: {e}")
    
    def _add_to_history(self, backup_result: Dict[str, Any]):
        """Add backup result to history"""
        self.backup_history.append(backup_result)
        
        # Maintain history size limit
        if len(self.backup_history) > self.max_history_size:
            self.backup_history = self.backup_history[-self.max_history_size:]
    
    def get_backup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent backup history"""
        return self.backup_history[-limit:]
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup scheduler status"""
        recent_backups = self.get_backup_history(5)
        
        return {
            "scheduler_running": self.running,
            "next_daily": schedule.jobs[0].next_run if schedule.jobs else None,
            "recent_backups": len(recent_backups),
            "last_backup": recent_backups[-1] if recent_backups else None,
            "success_rate": sum(1 for b in recent_backups if b.get("status") == "completed") / len(recent_backups) if recent_backups else 0,
            "configuration": {
                "daily_hour": self.daily_hour,
                "weekly_day": self.weekly_day,
                "monthly_day": self.monthly_day,
                "notify_on_success": self.notify_on_success,
                "notify_on_failure": self.notify_on_failure
            }
        }


# Global scheduler instance
automated_backup_scheduler = AutomatedBackupScheduler()