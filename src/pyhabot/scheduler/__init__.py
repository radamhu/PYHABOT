"""
Scheduler module for PYHABOT.

This module contains the background scheduler that manages periodic scraping
of watch URLs with proper jitter, backoff, and error handling.
"""

from .runner import SchedulerRunner, SchedulerConfig

__all__ = ["SchedulerRunner", "SchedulerConfig"]