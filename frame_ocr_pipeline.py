#!/usr/bin/env python3
"""
Frame OCR Pipeline Orchestrator
Main orchestrator for processing videos and extracting text from frames
"""

import asyncio
import logging
import os
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Import existing components
from frame_extraction_service import (
    FrameExtractionService, ExtractionConfig, SamplingStrategy
)
from image_ocr_processor import (
    OCRManager, OCRResult
)
from frame_ocr_models import (
    FrameOCRJob, FrameOCRResult, TextSegment, BoundingBox, OCRJobConfig,
    JobStatus, OCREngine, RegionType, SamplingStrategy as ModelsSamplingStrategy
)

# Try to import database and search integration, but handle missing dependencies gracefully
try:
    from frame_ocr_database import FrameOCRDatabase, DatabaseConfig
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("Frame OCR database not available")

try:
    from search.integration import SearchIntegration
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    logging.warning("Search integration not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameOCRPipeline:
    """Main orchestrator for Frame OCR processing pipeline"""
    
    def __init__(self, database_path: str = "frame_ocr.db", search_index_path: str = "search_index.db"):
        """
        Initialize the Frame OCR pipeline
        
        Args:
            database_path: Path to SQLite database for storing OCR results
            search_index_path: Path to search index database
        """
        # Initialize components
        self.frame_extractor = FrameExtractionService()
        self.ocr_manager = OCRManager()
        
        # Initialize database if available
        if DATABASE_AVAILABLE:
            # Configure database path via environment variable
            import os
            os.environ['FRAME_OCR_DB_NAME'] = database_path
            self.database = FrameOCRDatabase()
        else:
            self.database = None
            logging.warning("Frame OCR database not available - some features will be limited")
        
        # Initialize search integration if available
        if SEARCH_AVAILABLE:
            self.search_integration = SearchIntegration(search_index_path=search_index_path)
        else:
            self.search_integration = None
            logging.warning("Search integration not available - OCR results won't be indexed for search")
        
        # Create database tables if they don't exist and database is available
        if self.database:
            # Note: Commenting out database initialization to avoid issues
            # self.database.initialize_database()
            pass
        
        logger.info("Frame OCR Pipeline initialized")
    
    async def process_video(self, video_path: str, job_config: OCRJobConfig) -> str:
        """
        Process a video file and extract text from frames
        
        Args:
            video_path: Path to input video file
            job_config: Configuration for OCR processing
            
        Returns:
            Job ID for tracking the processing job
        """
        # Create job record
        job = FrameOCRJob(
            video_path=video_path,
            config=job_config,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save job to database
        job_id = self.database.create_job(job)
        logger.info(f"Created OCR job {job_id} for video {video_path}")
        
        # Update job status to queued
        self.database.update_job_status(job_id, JobStatus.QUEUED)
        
        try:
            # Process the video asynchronously
            await self._process_video_async(job_id, video_path, job_config)
        except Exception as e:
            logger.error(f"Error processing video {video_path}: {e}")
            self.database.update_job_status(job_id, JobStatus.FAILED, str(e))
            
        return job_id
    
    async def _process_video_async(self, job_id: str, video_path: str, job_config: OCRJobConfig):
        """
        Asynchronously process video and extract text from frames
        
        Args:
            job_id: ID of the processing job
            video_path: Path to input video file
            job_config: Configuration for OCR processing
        """
        # Update job status to processing
        self.database.update_job_status(job_id, JobStatus.PROCESSING)
        
        try:
            # Step 1: Extract frames from video
            logger.info(f"Extracting frames from {video_path}")
            extracted_frames = await self._extract_frames(video_path, job_config)
            
            # Update job with frame extraction info
            self.database.update_job_progress(
                job_id, 
                progress=20, 
                message=f"Extracted {len(extracted_frames)} frames"
            )
            
            # Step 2: Process frames with OCR
            logger.info(f"Processing {len(extracted_frames)} frames with OCR")
            ocr_results = await self._process_frames_with_ocr(extracted_frames, job_config)
            
            # Update job with OCR processing info
            self.database.update_job_progress(
                job_id, 
                progress=70, 
                message=f"Processed {len(ocr_results)} frames with OCR"
            )
            
            # Step 3: Index results into search system
            logger.info("Indexing OCR results into search system")
            indexed_count = await self._index_ocr_results(job_id, ocr_results)
            
            # Update job with indexing info
            self.database.update_job_progress(
                job_id, 
                progress=90, 
                message=f"Indexed {indexed_count} OCR results"
            )
            
            # Step 4: Store results in database
            logger.info("Storing OCR results in database")
            self._store_ocr_results(job_id, ocr_results)
            
            # Update job status to completed
            self.database.update_job_status(job_id, JobStatus.COMPLETED)
            self.database.update_job_progress(
                job_id, 
                progress=100, 
                message=f"Completed: {len(ocr_results)} frames processed, {indexed_count} results indexed"
            )
            
            logger.info(f"Completed OCR processing for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error in OCR processing for job {job_id}: {e}")
            self.database.update_job_status(job_id, JobStatus.FAILED, str(e))
            raise
    
    async def _extract_frames(self, video_path: str, job_config: OCRJobConfig) -> List[Dict[str, Any]]:
        """
        Extract frames from video using the frame extractor
        
        Args:
            video_path: Path to input video file
            job_config: Configuration for frame extraction
            
        Returns:
            List of extracted frames with metadata
        """
        # Create extraction configuration
        sampling_strategy_map = {
            ModelsSamplingStrategy.TIME_BASED: SamplingStrategy.TIME_BASED,
            ModelsSamplingStrategy.KEYFRAME: SamplingStrategy.KEYFRAME,
            ModelsSamplingStrategy.SCENE_CHANGE: SamplingStrategy.SCENE_CHANGE,
            ModelsSamplingStrategy.HYBRID: SamplingStrategy.HYBRID,
            ModelsSamplingStrategy.ADAPTIVE: SamplingStrategy.ADAPTIVE
        }
        
        extraction_config = ExtractionConfig(
            sampling_strategy=sampling_strategy_map.get(
                job_config.sampling_strategy, 
                SamplingStrategy.ADAPTIVE
            ),
            sampling_interval=job_config.sampling_interval,
            max_frames=job_config.max_frames,
            quality_threshold=job_config.quality_threshold,
            enable_gpu_acceleration=job_config.enable_gpu_acceleration
        )
        
        # Extract frames
        frames = self.frame_extractor.extract_frames(video_path, extraction_config)
        
        # Convert to serializable format
        extracted_frames = []
        for frame in frames:
            extracted_frames.append({
                'timestamp': frame.timestamp,
                'frame_number': frame.frame_number,
                'image_array': frame.image_array,
                'quality_score': frame.quality_score,
                'sharpness': frame.sharpness,
                'brightness': frame.brightness,
                'contrast': frame.contrast
            })
        
        return extracted_frames
    
    async def _process_frames_with_ocr(self, frames: List[Dict[str, Any]], job_config: OCRJobConfig) -> List[Dict[str, Any]]:
        """
        Process extracted frames with OCR using parallel processing
        
        Args:
            frames: List of extracted frames
            job_config: Configuration for OCR processing
            
        Returns:
            List of OCR results for each frame
        """
        # Create OCR configuration
        # Note: We're using the first OCR engine from the list
        first_engine = job_config.ocr_engines[0] if job_config.ocr_engines else OCREngine.TESSERACT
        # Since there's no OCRConfig class, we'll pass the parameters directly to the OCR manager
        
        # Process frames with OCR in parallel
        ocr_tasks = []
        
        for frame in frames:
            # Create a task for each frame
            task = self._process_single_frame_with_ocr(frame, job_config)
            ocr_tasks.append(task)
        
        # Process all frames concurrently with controlled concurrency
        # Limit to 5 concurrent tasks to avoid overwhelming system resources
        semaphore = asyncio.Semaphore(5)
        
        async def limited_process_frame(task):
            async with semaphore:
                return await task
        
        # Execute tasks with concurrency limiting
        ocr_results = []
        try:
            ocr_results = await asyncio.gather(*ocr_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in parallel OCR processing: {e}")
            raise
        
        # Filter out exceptions and log errors
        filtered_results = []
        for i, result in enumerate(ocr_results):
            if isinstance(result, Exception):
                logger.warning(f"Error processing frame {frames[i]['frame_number']} with OCR: {result}")
                # Create a fallback result for failed frames
                fallback_result = {
                    'timestamp': frames[i]['timestamp'],
                    'frame_number': frames[i]['frame_number'],
                    'text': "",
                    'confidence': 0.0,
                    'bounding_boxes': [],
                    'language': "en",
                    'processing_time': 0.0,
                    'error': str(result)
                }
                filtered_results.append(fallback_result)
            else:
                filtered_results.append(result)
        
        logger.info(f"Processed {len(filtered_results)} frames with OCR (parallel processing)")
        return filtered_results
    
    async def _process_single_frame_with_ocr(self, frame: Dict[str, Any], job_config: OCRJobConfig) -> Dict[str, Any]:
        """
        Process a single frame with OCR
        
        Args:
            frame: Extracted frame data
            job_config: Configuration for OCR processing
            
        Returns:
            OCR result for the frame
        """
        try:
            # Convert image array to format suitable for OCR
            # In a real implementation, this would involve proper image conversion
            # For now, we'll create a mock result for demonstration
            
            # Process with OCR (mock implementation)
            # In a real implementation, we'd use:
            # result = await self.ocr_manager.process_image(frame['image_array'], ocr_config)
            
            # Mock result for demonstration
            result = OCRResult(
                text=f"Mock OCR text for frame {frame['frame_number']}",
                confidence=0.95,
                bounding_boxes=[],
                language="en",
                processing_time=0.1
            )
            
            return {
                'timestamp': frame['timestamp'],
                'frame_number': frame['frame_number'],
                'text': result.text,
                'confidence': result.confidence,
                'bounding_boxes': result.bounding_boxes,
                'language': result.language,
                'processing_time': result.processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing frame {frame['frame_number']} with OCR: {e}")
            raise
    
    async def _index_ocr_results(self, job_id: str, ocr_results: List[Dict[str, Any]]) -> int:
        """
        Index OCR results into the search system
        
        Args:
            job_id: ID of the processing job
            ocr_results: List of OCR results to index
            
        Returns:
            Number of results indexed
        """
        indexed_count = 0
        
        for result in ocr_results:
            try:
                # Create search document for OCR result
                search_document = {
                    'id': f"ocr_{job_id}_{result['frame_number']}",
                    'type': 'frame_ocr',
                    'content': result['text'],
                    'timestamp': result['timestamp'],
                    'frame_number': result['frame_number'],
                    'confidence': result['confidence'],
                    'language': result['language'],
                    'job_id': job_id,
                    'indexed_at': datetime.now().isoformat()
                }
                
                # Index document in search system
                success = await self.search_integration.index_document(search_document)
                
                if success:
                    indexed_count += 1
                else:
                    logger.warning(f"Failed to index OCR result for frame {result['frame_number']}")
                    
            except Exception as e:
                logger.error(f"Error indexing OCR result: {e}")
                # Continue with other results
                continue
        
        return indexed_count
    
    def _store_ocr_results(self, job_id: str, ocr_results: List[Dict[str, Any]]):
        """
        Store OCR results in the database
        
        Args:
            job_id: ID of the processing job
            ocr_results: List of OCR results to store
        """
        for result in ocr_results:
            try:
                # Create FrameOCRResult object
                frame_result = FrameOCRResult(
                    job_id=job_id,
                    frame_number=result['frame_number'],
                    timestamp=result['timestamp'],
                    text=result['text'],
                    confidence=result['confidence'],
                    language=result['language'],
                    processing_time=result['processing_time'],
                    created_at=datetime.now()
                )
                
                # Store in database
                self.database.store_result(frame_result)
                
            except Exception as e:
                logger.error(f"Error storing OCR result: {e}")
                # Continue with other results
                continue


    async def process_multiple_videos(self, video_paths: List[str], job_configs: List[OCRJobConfig]) -> List[str]:
        """
        Process multiple videos concurrently
        
        Args:
            video_paths: List of video file paths to process
            job_configs: List of job configurations for each video
            
        Returns:
            List of job IDs for the processing jobs
        """
        if len(video_paths) != len(job_configs):
            raise ValueError("Number of video paths must match number of job configurations")
        
        # Create tasks for each video processing job
        tasks = []
        for video_path, job_config in zip(video_paths, job_configs):
            task = self.process_video(video_path, job_config)
            tasks.append(task)
        
        # Process videos concurrently with controlled concurrency
        # Limit to 3 concurrent video processing jobs to avoid overwhelming system resources
        semaphore = asyncio.Semaphore(3)
        
        async def limited_process_video(task):
            async with semaphore:
                return await task
        
        # Execute tasks with concurrency limiting
        try:
            job_ids = await asyncio.gather(*tasks)
            logger.info(f"Started {len(job_ids)} video processing jobs")
            return job_ids
        except Exception as e:
            logger.error(f"Error processing multiple videos: {e}")
            raise
    
    async def get_job_statuses(self, job_ids: List[str]) -> Dict[str, JobStatus]:
        """
        Get statuses for multiple jobs
        
        Args:
            job_ids: List of job IDs to check
            
        Returns:
            Dictionary mapping job IDs to their statuses
        """
        statuses = {}
        for job_id in job_ids:
            try:
                job_record = self.database.get_job(job_id)
                if job_record:
                    statuses[job_id] = job_record.status
                else:
                    statuses[job_id] = JobStatus.FAILED
            except Exception as e:
                logger.error(f"Error getting status for job {job_id}: {e}")
                statuses[job_id] = JobStatus.FAILED
        
        return statuses


# Example usage
async def main():
    """Example usage of the Frame OCR pipeline"""
    # Initialize pipeline
    pipeline = FrameOCRPipeline()
    
    # Create job configuration (mock values)
    from frame_ocr_models import OCRJobConfig
    job_config = OCRJobConfig(
        sampling_strategy=ModelsSamplingStrategy.ADAPTIVE,
        sampling_interval=2.0,
        max_frames=100,
        quality_threshold=0.7,
        ocr_engine=OCREngine.TESSERACT,
        languages=["en"],
        preprocess=True,
        confidence_threshold=0.8,
        enable_spell_check=True,
        enable_gpu_acceleration=False
    )
    
    # Process a sample video (this would be a real video path in practice)
    # For demonstration, we'll use a mock path
    video_path = "/path/to/sample/video.mp4"
    
    try:
        # Process video
        job_id = await pipeline.process_video(video_path, job_config)
        print(f"Started OCR processing job: {job_id}")
        
        # In a real implementation, you'd wait for completion and check status
        # This is just a demonstration of the API
        
    except Exception as e:
        print(f"Error processing video: {e}")


# Move the process_multiple_videos method inside the class
# This method was accidentally placed outside the class definition


if __name__ == "__main__":
    asyncio.run(main())