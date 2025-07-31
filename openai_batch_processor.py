#!/usr/bin/env python3
"""
OpenAI Batch Processing Integration
Leverages OpenAI's native batch processing API for efficient and cost-effective processing
"""

import os
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import openai
from openai import OpenAI

# Import will be done locally to avoid circular imports
import utils

logger = logging.getLogger(__name__)

class OpenAIBatchStatus(Enum):
    """OpenAI batch processing status"""
    VALIDATING = "validating"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"

@dataclass
class OpenAIBatchRequest:
    """Individual request for OpenAI batch processing"""
    custom_id: str
    method: str
    url: str
    body: Dict[str, Any]

@dataclass
class OpenAIBatchJob:
    """OpenAI batch job tracking"""
    batch_id: str
    job_id: str  # Our internal job ID
    openai_batch_id: str  # OpenAI's batch ID
    request_type: str  # "transcription" or "analysis"
    file_requests: Dict[str, str]  # file_id -> custom_id mapping
    status: OpenAIBatchStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = None
    error_message: str = ""

class OpenAIBatchProcessor:
    """Handles OpenAI batch processing integration"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.active_batches: Dict[str, OpenAIBatchJob] = {}
        self.batch_cost_savings = 0.5  # 50% cost reduction with batch API
        
        logger.info("OpenAI Batch Processor initialized")
    
    def can_use_batch_processing(self, job) -> bool:
        """Check if job is eligible for OpenAI batch processing"""
        
        # Batch processing only available for Advanced modes
        if "Advanced" not in job.analysis_mode:
            return False
        
        # Need OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            return False
        
        # Minimum files for batch efficiency (OpenAI recommends 100+ but we'll use 3+)
        if len(job.files) < 3:
            return False
        
        # Check file sizes - batch API has limits
        total_size = sum(f.size_bytes for f in job.files)
        if total_size > 100 * 1024 * 1024:  # 100MB total limit for batch
            return False
        
        return True
    
    def prepare_transcription_batch(self, job, audio_files: Dict[str, str]) -> Optional[str]:
        """Prepare batch transcription requests for OpenAI"""
        
        try:
            requests = []
            file_requests = {}
            
            for file_obj in job.files:
                if file_obj.id not in audio_files:
                    continue
                
                audio_path = audio_files[file_obj.id]
                
                # Read audio file and encode to base64 for batch processing
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                # Create custom ID for tracking
                custom_id = f"transcribe_{job.id}_{file_obj.id}"
                file_requests[file_obj.id] = custom_id
                
                # Create batch request for transcription
                request = OpenAIBatchRequest(
                    custom_id=custom_id,
                    method="POST",
                    url="/v1/audio/transcriptions",
                    body={
                        "model": "whisper-1",
                        "file": audio_data.hex(),  # Hex encoding for batch API
                        "response_format": "json",
                        "language": "en"
                    }
                )
                requests.append(request)
            
            if not requests:
                return None
            
            # Create batch file
            batch_file_path = self._create_batch_file(requests)
            
            # Submit batch to OpenAI
            batch_response = self.client.batches.create(
                input_file_id=self._upload_batch_file(batch_file_path),
                endpoint="/v1/audio/transcriptions",
                completion_window="24h",
                metadata={
                    "job_id": job.id,
                    "type": "transcription",
                    "file_count": str(len(requests))
                }
            )
            
            # Track batch job
            batch_job = OpenAIBatchJob(
                batch_id=f"transcribe_{job.id}",
                job_id=job.id,
                openai_batch_id=batch_response.id,
                request_type="transcription",
                file_requests=file_requests,
                status=OpenAIBatchStatus(batch_response.status),
                created_at=datetime.now()
            )
            
            self.active_batches[batch_job.batch_id] = batch_job
            
            logger.info(f"Created OpenAI transcription batch {batch_response.id} for job {job.id}")
            return batch_response.id
            
        except Exception as e:
            logger.error(f"Failed to create transcription batch: {e}")
            return None
    
    def prepare_analysis_batch(self, job, transcripts: Dict[str, str]) -> Optional[str]:
        """Prepare batch analysis requests for OpenAI GPT"""
        
        try:
            requests = []
            file_requests = {}
            
            for file_obj in job.files:
                if file_obj.id not in transcripts:
                    continue
                
                transcript = transcripts[file_obj.id]
                if not transcript.strip():
                    continue
                
                # Create custom ID for tracking
                custom_id = f"analyze_{job.id}_{file_obj.id}"
                file_requests[file_obj.id] = custom_id
                
                # Create batch request for analysis
                request = OpenAIBatchRequest(
                    custom_id=custom_id,
                    method="POST",
                    url="/v1/chat/completions",
                    body={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at extracting entities and generating summaries from transcripts. Extract key entities and provide a brief summary."
                            },
                            {
                                "role": "user",
                                "content": f"Analyze this transcript and extract entities (persons, organizations, dates, locations) and provide a summary:\n\n{transcript}"
                            }
                        ],
                        "functions": [
                            {
                                "name": "extract_entities",
                                "description": "Extract key entities and generate summary",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "summary": {"type": "string", "description": "Brief content summary"},
                                        "persons": {"type": "array", "items": {"type": "string"}},
                                        "organizations": {"type": "array", "items": {"type": "string"}},
                                        "dates": {"type": "array", "items": {"type": "string"}},
                                        "locations": {"type": "array", "items": {"type": "string"}},
                                        "key_topics": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["summary"]
                                }
                            }
                        ],
                        "function_call": {"name": "extract_entities"}
                    }
                )
                requests.append(request)
            
            if not requests:
                return None
            
            # Create batch file
            batch_file_path = self._create_batch_file(requests)
            
            # Submit batch to OpenAI
            batch_response = self.client.batches.create(
                input_file_id=self._upload_batch_file(batch_file_path),
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={
                    "job_id": job.id,
                    "type": "analysis",
                    "file_count": str(len(requests))
                }
            )
            
            # Track batch job
            batch_job = OpenAIBatchJob(
                batch_id=f"analyze_{job.id}",
                job_id=job.id,
                openai_batch_id=batch_response.id,
                request_type="analysis",
                file_requests=file_requests,
                status=OpenAIBatchStatus(batch_response.status),
                created_at=datetime.now()
            )
            
            self.active_batches[batch_job.batch_id] = batch_job
            
            logger.info(f"Created OpenAI analysis batch {batch_response.id} for job {job.id}")
            return batch_response.id
            
        except Exception as e:
            logger.error(f"Failed to create analysis batch: {e}")
            return None
    
    def _create_batch_file(self, requests: List[OpenAIBatchRequest]) -> str:
        """Create JSONL file for batch processing"""
        
        temp_dir = utils.ensure_temp_directory()
        batch_file_path = os.path.join(temp_dir, f"batch_{utils.get_timestamp()}.jsonl")
        
        with open(batch_file_path, 'w') as f:
            for request in requests:
                batch_line = {
                    "custom_id": request.custom_id,
                    "method": request.method,
                    "url": request.url,
                    "body": request.body
                }
                f.write(json.dumps(batch_line) + '\n')
        
        logger.debug(f"Created batch file: {batch_file_path}")
        return batch_file_path
    
    def _upload_batch_file(self, file_path: str) -> str:
        """Upload batch file to OpenAI"""
        
        with open(file_path, 'rb') as f:
            file_response = self.client.files.create(
                file=f,
                purpose="batch"
            )
        
        # Clean up local file
        utils.cleanup_file(file_path)
        
        logger.debug(f"Uploaded batch file: {file_response.id}")
        return file_response.id
    
    def check_batch_status(self, batch_id: str) -> Optional[OpenAIBatchJob]:
        """Check status of OpenAI batch job"""
        
        if batch_id not in self.active_batches:
            return None
        
        batch_job = self.active_batches[batch_id]
        
        try:
            # Get current status from OpenAI
            batch_response = self.client.batches.retrieve(batch_job.openai_batch_id)
            
            # Update status
            old_status = batch_job.status
            batch_job.status = OpenAIBatchStatus(batch_response.status)
            
            # Check if completed
            if batch_job.status == OpenAIBatchStatus.COMPLETED and old_status != OpenAIBatchStatus.COMPLETED:
                batch_job.completed_at = datetime.now()
                batch_job.results = self._download_batch_results(batch_response.output_file_id)
                logger.info(f"OpenAI batch {batch_id} completed")
            
            # Check if failed
            elif batch_job.status in [OpenAIBatchStatus.FAILED, OpenAIBatchStatus.EXPIRED, OpenAIBatchStatus.CANCELLED]:
                batch_job.error_message = f"Batch {batch_job.status.value}"
                if batch_response.errors:
                    batch_job.error_message += f": {batch_response.errors}"
                logger.error(f"OpenAI batch {batch_id} failed: {batch_job.error_message}")
            
            return batch_job
            
        except Exception as e:
            logger.error(f"Failed to check batch status for {batch_id}: {e}")
            batch_job.status = OpenAIBatchStatus.FAILED
            batch_job.error_message = str(e)
            return batch_job
    
    def _download_batch_results(self, output_file_id: str) -> Dict[str, Any]:
        """Download and parse batch results from OpenAI"""
        
        try:
            # Download results file
            file_response = self.client.files.content(output_file_id)
            results_content = file_response.read().decode('utf-8')
            
            # Parse JSONL results
            results = {}
            for line in results_content.strip().split('\n'):
                if line.strip():
                    result = json.loads(line)
                    custom_id = result.get('custom_id')
                    if custom_id:
                        results[custom_id] = result
            
            logger.debug(f"Downloaded {len(results)} batch results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to download batch results: {e}")
            return {}
    
    def process_transcription_results(self, batch_job: OpenAIBatchJob) -> Dict[str, str]:
        """Process transcription results from OpenAI batch"""
        
        transcripts = {}
        
        if not batch_job.results:
            return transcripts
        
        for file_id, custom_id in batch_job.file_requests.items():
            if custom_id in batch_job.results:
                result = batch_job.results[custom_id]
                
                if result.get('response', {}).get('status_code') == 200:
                    response_body = result['response']['body']
                    transcript = response_body.get('text', '')
                    transcripts[file_id] = transcript
                else:
                    logger.warning(f"Transcription failed for file {file_id}: {result}")
        
        return transcripts
    
    def process_analysis_results(self, batch_job: OpenAIBatchJob) -> Dict[str, Tuple[Dict[str, Any], str]]:
        """Process analysis results from OpenAI batch"""
        
        analyses = {}
        
        if not batch_job.results:
            return analyses
        
        for file_id, custom_id in batch_job.file_requests.items():
            if custom_id in batch_job.results:
                result = batch_job.results[custom_id]
                
                if result.get('response', {}).get('status_code') == 200:
                    response_body = result['response']['body']
                    
                    # Extract function call result
                    message = response_body.get('choices', [{}])[0].get('message', {})
                    function_call = message.get('function_call', {})
                    
                    if function_call and function_call.get('name') == 'extract_entities':
                        try:
                            function_args = json.loads(function_call.get('arguments', '{}'))
                            
                            # Convert to our expected format
                            entities = {
                                'PERSON': function_args.get('persons', []),
                                'ORG': function_args.get('organizations', []),
                                'DATE': function_args.get('dates', []),
                                'GPE': function_args.get('locations', []),
                                'TOPIC': function_args.get('key_topics', [])
                            }
                            
                            summary = function_args.get('summary', '')
                            analyses[file_id] = (entities, summary)
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse analysis result for {file_id}: {e}")
                else:
                    logger.warning(f"Analysis failed for file {file_id}: {result}")
        
        return analyses
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel an OpenAI batch job"""
        
        if batch_id not in self.active_batches:
            return False
        
        batch_job = self.active_batches[batch_id]
        
        try:
            self.client.batches.cancel(batch_job.openai_batch_id)
            batch_job.status = OpenAIBatchStatus.CANCELLING
            logger.info(f"Cancelled OpenAI batch {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel batch {batch_id}: {e}")
            return False
    
    def cleanup_completed_batches(self, max_age_hours: int = 24):
        """Clean up old completed batch jobs"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        batches_to_remove = []
        for batch_id, batch_job in self.active_batches.items():
            if (batch_job.completed_at and batch_job.completed_at < cutoff_time) or \
               (batch_job.status in [OpenAIBatchStatus.COMPLETED, OpenAIBatchStatus.FAILED, OpenAIBatchStatus.CANCELLED]):
                batches_to_remove.append(batch_id)
        
        for batch_id in batches_to_remove:
            del self.active_batches[batch_id]
        
        if batches_to_remove:
            logger.info(f"Cleaned up {len(batches_to_remove)} completed OpenAI batches")
    
    def get_batch_cost_estimate(self, job) -> Dict[str, float]:
        """Estimate cost savings with batch processing"""
        
        # Rough cost estimates (actual costs may vary)
        whisper_cost_per_minute = 0.006  # $0.006 per minute
        gpt_cost_per_1k_tokens = 0.002   # $0.002 per 1K tokens
        
        total_minutes = sum(f.size_bytes / (1024 * 1024) * 0.5 for f in job.files)  # Rough estimate
        total_tokens = sum(len(f.name) * 10 for f in job.files)  # Very rough estimate
        
        standard_cost = (total_minutes * whisper_cost_per_minute) + (total_tokens / 1000 * gpt_cost_per_1k_tokens)
        batch_cost = standard_cost * (1 - self.batch_cost_savings)
        savings = standard_cost - batch_cost
        
        return {
            'standard_cost': standard_cost,
            'batch_cost': batch_cost,
            'savings': savings,
            'savings_percentage': self.batch_cost_savings * 100
        }
    
    def get_all_active_batches(self) -> Dict[str, OpenAIBatchJob]:
        """Get all active OpenAI batch jobs"""
        return self.active_batches.copy()

# Global OpenAI batch processor instance
openai_batch_processor = OpenAIBatchProcessor()