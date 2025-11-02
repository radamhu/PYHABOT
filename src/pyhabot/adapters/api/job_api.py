"""
Job management API endpoints.

This module provides endpoints for submitting and tracking background jobs,
such as re-scraping operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.dependencies import get_watch_service
from ...api.job_manager import get_job_queue
from ...api.models import JobResponse, JobStatus
from ...api.exceptions import (
    WatchNotFoundError,
    JobNotFoundError,
    JobProcessingError
)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post(
    "/watches/{watch_id}/rescrape",
    response_model=JobResponse,
    status_code=202,
    summary="Force re-scraping of a watch",
    description="Initiate an immediate re-scraping of the specified watch URL. This is a long-running operation that returns a job ID for tracking.",
    responses={
        202: {"description": "Re-scraping job queued successfully"},
        404: {"description": "Watch not found"},
        503: {"description": "Service temporarily unavailable"}
    }
)
async def submit_rescrape_job(
    watch_id: int,
    watch_service = Depends(get_watch_service),
    job_queue = Depends(get_job_queue)
) -> JobResponse:
    """Submit a re-scraping job for a specific watch."""
    try:
        # Verify watch exists
        watch = watch_service.get_watch(watch_id)
        if not watch:
            raise WatchNotFoundError(watch_id)
        
        # Start job queue if not running
        await job_queue.start()
        
        # Enqueue rescrape job
        job_id = await job_queue.enqueue("rescrape", watch_id=watch_id)
        
        # Get job details
        job = await job_queue.get_job(job_id)
        if not job:
            raise JobProcessingError(job_id, "Failed to create job")
        
        return JobResponse(**job.to_dict())
        
    except (WatchNotFoundError, JobProcessingError):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job status",
    description="Retrieve the current status and results of a specific job.",
    responses={
        200: {"description": "Job status retrieved successfully"},
        404: {"description": "Job not found"}
    }
)
async def get_job_status(
    job_id: str,
    job_queue = Depends(get_job_queue)
) -> JobResponse:
    """Get the status of a specific job."""
    try:
        job = await job_queue.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        
        return JobResponse(**job.to_dict())
        
    except JobNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/",
    response_model=List[JobResponse],
    summary="List all jobs",
    description="Retrieve all jobs in the system, optionally filtered by status.",
    responses={
        200: {"description": "Jobs retrieved successfully"}
    }
)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter jobs by status"),
    job_queue = Depends(get_job_queue)
) -> List[JobResponse]:
    """List all jobs, optionally filtered by status."""
    try:
        jobs = await job_queue.list_jobs(status)
        return [JobResponse(**job.to_dict()) for job in jobs]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{job_id}",
    summary="Cancel a job",
    description="Attempt to cancel a job that is queued or processing. Note: Already completed jobs cannot be cancelled.",
    responses={
        204: {"description": "Job cancelled successfully"},
        404: {"description": "Job not found"},
        409: {"description": "Job cannot be cancelled (already completed)"}
    }
)
async def cancel_job(
    job_id: str,
    job_queue = Depends(get_job_queue)
):
    """Cancel a job if it's still queued or processing."""
    try:
        job = await job_queue.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        
        if job.status in ["completed", "failed"]:
            raise HTTPException(
                status_code=409,
                detail="Job cannot be cancelled - already completed"
            )
        
        # For now, we'll mark it as failed to "cancel" it
        # In a real implementation, you might have more sophisticated cancellation
        await job_queue.update_job_status(
            job_id, 
            "failed", 
            error="Job cancelled by user"
        )
        
        return None  # FastAPI will return 204 No Content
        
    except (JobNotFoundError, HTTPException):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")