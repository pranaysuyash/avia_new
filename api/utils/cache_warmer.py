"""
Cache Warmer
Pre-loads frequently accessed data into Redis cache
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from api.database import get_db, Transcript, User
from api.cache.redis_cache import transcription_cache, redis_cache
from api.config.cache_config import CacheConfig, CacheKeyGenerator
from services.transcription_service_cached import CachedTranscriptionService

logger = logging.getLogger(__name__)


class CacheWarmer:
    """Handles cache warming operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.service = CachedTranscriptionService(db)
        self.batch_size = CacheConfig.WARM_CACHE_BATCH_SIZE
    
    async def warm_popular_transcripts(self, days: int = 7) -> Dict[str, Any]:
        """
        Warm cache with popular transcripts from the last N days
        
        Args:
            days: Number of days to look back for popular transcripts
        
        Returns:
            Statistics about the warming process
        """
        logger.info(f"Starting cache warming for popular transcripts from last {days} days")
        
        # Get popular transcripts
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        popular_transcripts = self.db.query(
            Transcript,
            func.count(Transcript.id).label('access_count')
        ).filter(
            Transcript.last_accessed >= cutoff_date,
            Transcript.content.isnot(None)
        ).group_by(
            Transcript.id
        ).order_by(
            desc('access_count')
        ).limit(self.batch_size * 2).all()
        
        stats = {
            "total_candidates": len(popular_transcripts),
            "warmed": 0,
            "already_cached": 0,
            "failed": 0,
            "total_size_mb": 0
        }
        
        # Process in batches
        for i in range(0, len(popular_transcripts), self.batch_size):
            batch = popular_transcripts[i:i + self.batch_size]
            
            tasks = []
            for transcript, access_count in batch:
                task = self._warm_single_transcript(transcript, stats)
                tasks.append(task)
            
            # Process batch concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Add delay between batches to avoid overloading
            if i + self.batch_size < len(popular_transcripts):
                await asyncio.sleep(1)
        
        logger.info(f"Cache warming completed: {stats}")
        return stats
    
    async def _warm_single_transcript(
        self,
        transcript: Transcript,
        stats: Dict[str, Any]
    ) -> bool:
        """Warm cache for a single transcript"""
        try:
            # Check if already cached
            if transcript.file_hash:
                # Try to get from cache first
                cache_params = {
                    "language": transcript.language,
                    "model": transcript.model_used or "whisper-1"
                }
                
                cached = transcription_cache.get_transcription(
                    transcript.file_hash,
                    cache_params
                )
                
                if cached:
                    stats["already_cached"] += 1
                    return True
            
            # Calculate size
            segments_size = len(str(transcript.segments or [])) / (1024 * 1024)  # MB
            if not CacheConfig.should_cache(segments_size, "transcription"):
                logger.debug(f"Transcript {transcript.id} too large to cache: {segments_size:.2f}MB")
                return False
            
            # Build cache entry
            cache_data = {
                "transcript_id": str(transcript.id),
                "text": transcript.content,
                "segments": transcript.segments or [],
                "language": transcript.language,
                "duration": transcript.duration,
                "created_at": transcript.created_at.isoformat(),
                "file_hash": transcript.file_hash
            }
            
            # Cache it
            if transcript.file_hash:
                cache_params = {
                    "language": transcript.language,
                    "model": transcript.model_used or "whisper-1"
                }
                
                success = transcription_cache.set_transcription(
                    transcript.file_hash,
                    cache_params,
                    cache_data
                )
                
                if success:
                    stats["warmed"] += 1
                    stats["total_size_mb"] += segments_size
                    logger.debug(f"Warmed cache for transcript {transcript.id}")
                    return True
            
            stats["failed"] += 1
            return False
            
        except Exception as e:
            logger.error(f"Failed to warm cache for transcript {transcript.id}: {e}")
            stats["failed"] += 1
            return False
    
    async def warm_user_lists(self, top_users: int = 100) -> Dict[str, Any]:
        """
        Warm cache with transcript lists for most active users
        
        Args:
            top_users: Number of top users to warm cache for
        
        Returns:
            Statistics about the warming process
        """
        logger.info(f"Starting cache warming for top {top_users} users")
        
        # Get most active users
        active_users = self.db.query(
            User.id,
            func.count(Transcript.id).label('transcript_count')
        ).join(
            Transcript, User.id == Transcript.user_id
        ).group_by(
            User.id
        ).order_by(
            desc('transcript_count')
        ).limit(top_users).all()
        
        stats = {
            "total_users": len(active_users),
            "lists_warmed": 0,
            "failed": 0
        }
        
        for user_id, transcript_count in active_users:
            try:
                # Get user's recent transcripts
                transcripts = await self.service.get_user_transcripts(
                    user_id=str(user_id),
                    limit=50,
                    offset=0
                )
                
                if transcripts:
                    stats["lists_warmed"] += 1
                    logger.debug(f"Warmed transcript list for user {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to warm cache for user {user_id}: {e}")
                stats["failed"] += 1
        
        logger.info(f"User list cache warming completed: {stats}")
        return stats
    
    async def warm_cache_on_startup(self) -> Dict[str, Any]:
        """Run all cache warming operations on startup"""
        if not CacheConfig.WARM_CACHE_ON_STARTUP:
            logger.info("Cache warming on startup is disabled")
            return {"status": "skipped"}
        
        logger.info("Starting cache warming on startup")
        
        overall_stats = {
            "started_at": datetime.utcnow().isoformat(),
            "popular_transcripts": {},
            "user_lists": {}
        }
        
        try:
            # Warm popular transcripts
            transcript_stats = await self.warm_popular_transcripts(days=7)
            overall_stats["popular_transcripts"] = transcript_stats
            
            # Warm user lists
            user_stats = await self.warm_user_lists(top_users=50)
            overall_stats["user_lists"] = user_stats
            
            overall_stats["completed_at"] = datetime.utcnow().isoformat()
            overall_stats["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            overall_stats["error"] = str(e)
            overall_stats["status"] = "failed"
        
        return overall_stats
    
    async def analyze_cache_efficiency(self) -> Dict[str, Any]:
        """Analyze cache hit rates and efficiency"""
        if not redis_cache.is_connected():
            return {"error": "Redis not connected"}
        
        try:
            info = redis_cache.client.info()
            
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total_requests = hits + misses
            
            analysis = {
                "total_requests": total_requests,
                "hits": hits,
                "misses": misses,
                "hit_rate": (hits / total_requests * 100) if total_requests > 0 else 0,
                "memory_used": info.get("used_memory_human", "0"),
                "memory_peak": info.get("used_memory_peak_human", "0"),
                "total_keys": redis_cache.client.dbsize(),
                "evicted_keys": info.get("evicted_keys", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
            
            # Get key distribution by type
            key_counts = {}
            for prefix in ["trans:", "user:", "search:", "stats:"]:
                count = 0
                for key in redis_cache.client.scan_iter(match=f"{prefix}*", count=100):
                    count += 1
                key_counts[prefix.rstrip(':')] = count
            
            analysis["key_distribution"] = key_counts
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze cache efficiency: {e}")
            return {"error": str(e)}


async def run_cache_warmer():
    """Run cache warmer as a standalone script"""
    logging.basicConfig(level=logging.INFO)
    
    db = next(get_db())
    warmer = CacheWarmer(db)
    
    try:
        # Run warming
        stats = await warmer.warm_cache_on_startup()
        print(f"Cache warming completed: {stats}")
        
        # Analyze efficiency
        analysis = await warmer.analyze_cache_efficiency()
        print(f"Cache analysis: {analysis}")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_cache_warmer())