"""
PYHABOT API package.

This package provides HTTP API endpoints for interacting with PYHABOT
via FastAPI, including watch management, job tracking, and health checks.
"""

from .main import app
from .job_manager import get_job_queue
from .models import *
from .exceptions import *

__version__ = "1.0.0"