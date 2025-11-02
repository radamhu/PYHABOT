"""
Global job queue instance management.

This module provides a way to access the global job queue
without creating circular imports.
"""

from typing import Optional
from .job_queue import JobQueue

# Global job queue instance
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    global _job_queue
    if _job_queue is None:
        raise RuntimeError("Job queue not initialized")
    return _job_queue


def set_job_queue(queue: JobQueue):
    """Set the global job queue instance."""
    global _job_queue
    _job_queue = queue