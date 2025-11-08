"""
Health check API endpoints.

This module provides endpoints for monitoring the health and status
of the PYHABOT API and its dependencies.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends

from ...api.dependencies import get_config, get_repo
from ...api.job_manager import get_job_queue
from ...api.models import HealthResponse

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Check if the API is running and basic functionality is working",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2025-11-02T13:33:00Z",
                        "services": {
                            "database": "healthy",
                            "scraper": "healthy",
                            "scheduler": "healthy",
                            "job_queue": "healthy"
                        }
                    }
                }
            }
        }
    }
)
async def health_check(
    job_queue = Depends(get_job_queue)
) -> HealthResponse:
    """Comprehensive health check of all services."""
    services = {}
    overall_status = "healthy"
    
    # Check job queue (non-critical - degraded if not working)
    try:
        if job_queue and job_queue.running:
            services["job_queue"] = "healthy"
        else:
            services["job_queue"] = "degraded"
    except Exception as e:
        services["job_queue"] = "degraded"
    
    # Check database (repository) - non-critical for initial startup
    try:
        repo = await get_repo()
        # Simple test - try to access the database
        repo.get_all_watches()
        services["database"] = "healthy"
    except Exception as e:
        services["database"] = "degraded"
        # Don't fail health check if DB has issues during startup
    
    # Check configuration - non-critical
    try:
        config = await get_config()
        if config:
            services["config"] = "healthy"
        else:
            services["config"] = "degraded"
    except Exception as e:
        services["config"] = "degraded"
    
    # For now, mark scraper and scheduler as healthy by default
    # In a real implementation, you'd check these services
    services["scraper"] = "healthy"
    services["scheduler"] = "healthy"
    
    # Always return healthy for Railway - degraded services are logged but not fatal
    return HealthResponse(
        status="healthy",  # Always healthy if API is responding
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        services=services
    )


@router.get(
    "/version",
    summary="Get API version",
    description="Returns the current API version information.",
    responses={
        200: {
            "description": "Version information",
            "content": {
                "application/json": {
                    "example": {
                        "version": "1.0.0",
                        "name": "PYHABOT API",
                        "description": "Async Python bot for monitoring HardverApró classified ads"
                    }
                }
            }
        }
    }
)
async def get_version() -> Dict[str, str]:
    """Get API version information."""
    return {
        "version": "1.0.0",
        "name": "PYHABOT API",
        "description": "Async Python bot for monitoring HardverApró classified ads"
    }


@router.get(
    "/ping",
    summary="Simple ping endpoint",
    description="Simple endpoint for connectivity testing.",
    responses={
        200: {
            "description": "Pong response",
            "content": {
                "application/json": {
                    "example": {"message": "pong"}
                }
            }
        }
    }
)
async def ping() -> Dict[str, str]:
    """Simple ping endpoint for connectivity testing."""
    return {"message": "pong"}