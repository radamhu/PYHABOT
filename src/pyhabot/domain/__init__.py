"""
Domain models and ports for PYHABOT.

This package contains the core business logic, domain models, and port definitions
that define the contracts for external adapters.
"""

from .models import Watch, Advertisement, NotificationTarget
from .ports import ScraperPort, RepoPort, NotifierPort

__all__ = [
    "Watch",
    "Advertisement", 
    "NotificationTarget",
    "ScraperPort",
    "RepoPort",
    "NotifierPort",
]