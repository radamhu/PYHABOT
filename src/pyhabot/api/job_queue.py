"""
In-memory job queue for PYHABOT API.

This module provides a simple async job queue for background tasks
with status tracking and result storage.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from ..logging import get_logger

logger = get_logger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Represents a background job."""
    id: str
    type: str
    params: Dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }


class JobQueue:
    """In-memory job queue with status tracking."""
    
    def __init__(self):
        """Initialize job queue."""
        self.jobs: Dict[str, Job] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start the job queue worker."""
        if self.running:
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("Job queue worker started")
    
    async def shutdown(self):
        """Shutdown the job queue worker."""
        if not self.running:
            return
        
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Job queue worker stopped")
    
    async def enqueue(self, job_type: str, **params) -> str:
        """Enqueue a new job and return its ID."""
        job_id = str(uuid.uuid4())
        job = Job(id=job_id, type=job_type, params=params)
        
        self.jobs[job_id] = job
        await self.queue.put(job)
        
        logger.info(f"Job {job_id} enqueued: {job_type}")
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update job status and optional result/error."""
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Attempted to update non-existent job: {job_id}")
            return
        
        job.status = status
        
        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.now(timezone.utc)
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
        
        logger.info(f"Job {job_id} status updated to: {status.value}")
    
    async def _worker(self):
        """Background worker that processes jobs."""
        logger.info("Job queue worker started processing jobs")
        
        while self.running:
            try:
                # Wait for job with timeout to allow graceful shutdown
                job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                await self.update_job_status(job.id, JobStatus.PROCESSING)
                
                # Process job based on type
                try:
                    result = await self._process_job(job)
                    await self.update_job_status(job.id, JobStatus.COMPLETED, result=result)
                except Exception as e:
                    logger.error(f"Job {job.id} failed: {e}")
                    await self.update_job_status(job.id, JobStatus.FAILED, error=str(e))
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                # Timeout is expected for graceful shutdown
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(0.1)  # Prevent tight error loop
    
    async def _process_job(self, job: Job) -> Dict[str, Any]:
        """Process a specific job based on its type."""
        # Import here to avoid circular imports
        from ..simple_app import SimplePyhabot
        from ..simple_config import SimpleConfig as Config
        
        # This is a placeholder - we'll implement actual job processing
        # when we integrate with the existing services
        if job.type == "rescrape":
            watch_id = job.params.get("watch_id")
            logger.info(f"Processing rescrape job for watch {watch_id}")
            
            # Simulate processing time
            await asyncio.sleep(2)
            
            return {
                "watch_id": watch_id,
                "new_ads": 0,
                "updated_ads": 0,
                "processing_time": 2.0
            }
        else:
            raise ValueError(f"Unknown job type: {job.type}")
    
    async def list_jobs(self, status: Optional[JobStatus] = None) -> List[Job]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self.jobs.values())
        if status:
            jobs = [job for job in jobs if job.status == status]
        return jobs