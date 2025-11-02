"""
FastAPI application for PYHABOT HTTP API.

This module provides the main FastAPI application with CORS middleware,
documentation configuration, and router setup.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..logging import get_logger
from .job_queue import JobQueue
from .job_manager import set_job_queue
from ..adapters.api.watch_api import router as watch_router
from ..adapters.api.job_api import router as job_router
from ..adapters.api.health_api import router as health_router
from ..adapters.api.webhook_api import router as webhook_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting PYHABOT API...")
    job_queue = JobQueue()
    set_job_queue(job_queue)
    logger.info("Job queue initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PYHABOT API...")
    if job_queue:
        await job_queue.shutdown()
    logger.info("API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development")
    is_production = environment == "production"
    
    # Configure documentation URLs
    docs_url = "/api/docs" if is_production else "/docs"
    redoc_url = "/api/redoc" if is_production else "/redoc"
    openapi_url = "/api/openapi.json" if is_production else "/openapi.json"
    
    app = FastAPI(
        title="PYHABOT API",
        description="Async Python bot for monitoring HardverApró classified ads",
        version="1.0.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan
    )
    
    # CORS middleware for Railway deployment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(watch_router)
    app.include_router(job_router)
    app.include_router(health_router)
    app.include_router(webhook_router)
    
    # Swagger UI configuration
    app.swagger_ui_parameters = {
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "operationsSorter": "method",
        "filter": True,
        "tryItOutEnabled": True
    }
    
    return app


# Create app instance
app = create_app()