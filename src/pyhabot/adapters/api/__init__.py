"""
API adapters for PYHABOT.

This package contains FastAPI router implementations for different
API endpoints, providing the HTTP interface to domain services.
"""

from .watch_api import router as watch_router
from .job_api import router as job_router
from .health_api import router as health_router

__all__ = ["watch_router", "job_router", "health_router"]